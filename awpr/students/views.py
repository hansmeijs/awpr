# PR2018-09-02
from django.contrib.auth.decorators import login_required

from django.core.mail import send_mail

from django.db.models import Q
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext, pgettext_lazy, gettext_lazy as _
from django.views.generic import View

from accounts import views as acc_view
from accounts import permits as acc_prm

from awpr import menus as awpr_menu, excel as grd_exc
from awpr import constants as c
from awpr import settings as s
from awpr import validators as av
from awpr import functions as af
from awpr import downloads as dl
from awpr import library as awpr_lib

from grades import views as grd_view
from grades import validators as grad_val
from grades import calc_results as calc_res

from subjects import models as subj_mod
from subjects import views as subj_vw
from schools import models as sch_mod
from students import models as stud_mod
from students import functions as stud_fnc
from students import validators as stud_val

from subjects import views as sj_vw


# PR2019-01-04  https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

import json

import logging
logger = logging.getLogger(__name__)


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


# ========  Student  =====================================

@method_decorator([login_required], name='dispatch')
class StudentListView(View):  # PR2018-09-02 PR2020-10-27 PR2021-03-25 PR2023-04-05

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(" =====  StudentListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_student'
        params = awpr_menu.get_headerbar_param(request, page)
        if logging_on:
            logger.debug(" params: " + str(params))

# - save this page in Usersetting, so at next login this page will open. Used in LoggedIn
        # PR2021-06-22 moved to get_headerbar_param

        return render(request, 'students.html', params)


# ========  StudentsubjectListView  =======
@method_decorator([login_required], name='dispatch')
class StudentsubjectListView(View): # PR2020-09-29 PR2021-03-25 PR2022-07-05

    def get(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(" =====  StudentsubjectListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - for btn text 'Proof of Knowledge' or 'Proof of Exemption'
        is_evelex_school = False
        selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        sel_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK) if selected_dict else None
        if request.user:
            sel_school = sch_mod.School.objects.get_or_none(
                base=request.user.schoolbase,
                examyear_id=sel_examyear_pk
            )
            if sel_school:
                is_evelex_school = sel_school.iseveningschool or sel_school.islexschool

        if is_evelex_school:
            pok_pex_str = _('Proof of exemption')
        else:
            pok_pex_str = _('Proof of knowledge')

# - get headerbar parameters
        page = 'page_studsubj'
        param = {'pok_pex': pok_pex_str}
        params = awpr_menu.get_headerbar_param(request, page, param)
        return render(request, 'studentsubjects.html', params)


# ========  OrderlistsListView  =======
@method_decorator([login_required], name='dispatch')
class OrderlistsListView(View): # PR2021-07-04

    def get(self, request):
        #logger.debug(" =====  OrderlistsListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_orderlist'
        param = {'display_school': False, 'display_department': False}
        params = awpr_menu.get_headerbar_param(request, page, param)

        return render(request, 'orderlists.html', params)
# - end of OrderlistsListView


#/////////////////////////////////////////////////////////////////
def create_student_rows(request, sel_examyear, sel_schoolbase, sel_depbase, append_dict, show_deleted=False, student_pk=None):
    # --- create rows of all students of this examyear / school PR2020-10-27 PR2022-01-03 PR2022-02-15  PR2023-01-11
    # - show only students that are not tobedeleted
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- create_student_rows -----')
        logger.debug('    sel_examyear:   ' + str(sel_examyear))
        logger.debug('    sel_schoolbase: ' + str(sel_schoolbase))
        logger.debug('    sel_depbase:    ' + str(sel_depbase))
        logger.debug('    show_deleted:    ' + str(show_deleted))

    sql_keys = {'ey_id': sel_examyear.pk if sel_examyear else None,
                'sb_id': sel_schoolbase.pk if sel_schoolbase else None,
                'db_id': sel_depbase.pk if sel_depbase else None}
    sql_clause_arr = []

    #  sel_schoolbase is already checked on allowed schoolbases in function download_setting / get_settings_schoolbase / get_sel_schoolbase_instance
    #  sel_depbase is already checked on allowed depbases in function download_setting / get_settings_departmentbase / get_sel_depbase_instance

    sel_school = sch_mod.School.objects.get_or_none(
        examyear=sel_examyear,
        base=sel_schoolbase
    )
    sel_department = sch_mod.Department.objects.get_or_none(
        examyear=sel_examyear,
        base=sel_depbase
    )
    level_is_required = sel_department.level_req if sel_department else False

    if logging_on:
        logger.debug(' ----------')
        logger.debug('    sel_school:   ' + str(sel_school))
        logger.debug('    sel_department: ' + str(sel_department))
        logger.debug('    level_is_required:    ' + str(level_is_required))

# - get allowed_sections_dict from userallowed
    allowed_sections_dict = acc_prm.get_userallowed_sections_dict_from_request(request)
    # allowed_sections_dict: {'13': {'1': {'-9': []}, '2': {'-9': []}}} key is schoolbase_pk / depbase_pk / lvlbase_pk

# - get allowed_schoolbase_dict from allowed_sections_dict
    allowed_schoolbase_dict, allowed_depbases_pk_arr = acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(
        userallowed_sections_dict=allowed_sections_dict,
        sel_schoolbase_pk=sel_schoolbase.pk
    )
    # allowed_schoolbase_dict:    {'1': {'-9': []}, '2': {'-9': []}} key is depbase_pk / lvlbase_pk

# - get allowed_depbase_dict from allowed_schoolbase_dict
    allowed_depbase_dict, allowed_lvlbase_pk_arr = acc_prm.get_userallowed_depbase_dict_lvlbases_pk_arr(
        allowed_schoolbase_dict=allowed_schoolbase_dict,
        sel_depbase_pk=sel_depbase.pk if sel_depbase else None
    )
    # allowed_depbase_dict:    {'-9': []}

    if logging_on:
        logger.debug(' ----------')
        logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict))
        logger.debug('    allowed_schoolbase_dict:    ' + str(allowed_schoolbase_dict))
        logger.debug('    allowed_depbase_dict:    ' + str(allowed_depbase_dict))

    sel_lvlbase_pk_arr = []

# - get selected_pk_dict from usersettings
    selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)

    if level_is_required:

# - get saved_lvlbase_pk of req_usr
        saved_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)
        if logging_on:
            logger.debug(' ----------')
            logger.debug('    saved_lvlbase_pk: ' + str(saved_lvlbase_pk) + ' ' + str(type(saved_lvlbase_pk)))

# - filter only the saved_lvlbase_pk if exists and allowed
    # if sel_lvlbase_pk_arr is empty all lvlbases are allowed
        if not saved_lvlbase_pk or saved_lvlbase_pk == '-9':
            if allowed_depbase_dict:
            # if '-9' in allowed_depbase_dict: all levels are allowed, no filter
            # else: add all allowed lvlbase_pk to sel_lvlbase_pk_arr
                if '-9' not in allowed_depbase_dict:
                    for lvlbase_pk_str in allowed_depbase_dict:
                        sel_lvlbase_pk_arr.append(int(lvlbase_pk_str))
            #else:
        # - all lvlbases are allowed if allowed_depbase_dict is empty

        else:
            if allowed_depbase_dict:
                if str(saved_lvlbase_pk) in allowed_depbase_dict or \
                        '-9' in allowed_depbase_dict:
                    sel_lvlbase_pk_arr.append(saved_lvlbase_pk)
            else:
                sel_lvlbase_pk_arr.append(saved_lvlbase_pk)

        if logging_on:
            logger.debug('    sel_lvlbase_pk_arr: ' + str(sel_lvlbase_pk_arr) + ' ' + str(type(sel_lvlbase_pk_arr)))

# - create lvlbase_clause
        lvlbase_clause = None
        if sel_lvlbase_pk_arr:
            if len(sel_lvlbase_pk_arr) == 1:
                sql_keys['lvlbase_pk'] = sel_lvlbase_pk_arr[0]
                lvlbase_clause = "lvl.base_id = %(lvlbase_pk)s::INT"
            else:
                sql_keys['lvlbase_pk_arr'] = sel_lvlbase_pk_arr
                lvlbase_clause = "lvl.base_id IN (SELECT UNNEST(%(lvlbase_pk_arr)s::INT[]))"
            sql_clause_arr.append(lvlbase_clause)

        if logging_on:
            logger.debug('    lvlbase_clause: ' + str(lvlbase_clause))

    #allowed_depbase_dict = acc_view.get_requsr_allowed_lvlbases_dict(
    #    allowed_depbases_dict=allowed_depbases_dict,
    #    sel_depbase_pk=sel_depbase.pk if sel_depbase else None
    #)

    # - get selected sctbase_pk of req_usr
    saved_sctbase_pk = selected_pk_dict.get(c.KEY_SEL_SCTBASE_PK)
    if saved_sctbase_pk and saved_sctbase_pk != -9:
        sql_clause_arr.append(''.join(("(sct.base_id = ", str(saved_sctbase_pk), "::INT)")))

    sql_clause = 'AND ' + ' AND '.join(sql_clause_arr) if sql_clause_arr else ''

    student_rows = []
    error_dict = {} # PR2021-11-17 new way of err msg, like in TSA

    if sel_examyear and sel_schoolbase and sel_depbase:
        try:

            sql_studsubj_agg = "SELECT student_id FROM students_studentsubject WHERE NOT deleted AND subj_published_id IS NOT NULL GROUP BY student_id"

            sql_list = ["WITH studsubj AS (", sql_studsubj_agg, ")",
                "SELECT st.id, st.base_id, st.school_id AS s_id,",
                "school.locked AS s_locked, ey.locked AS ey_locked, ",
                "st.department_id AS dep_id, st.level_id AS lvl_id, st.sector_id AS sct_id, st.scheme_id,",
                "dep.base_id AS depbase_id, lvl.base_id AS lvlbase_id, sct.base_id AS sctbase_id, "
                "dep.abbrev AS dep_abbrev, db.code AS db_code,",
                "dep.level_req AS lvl_req, lvl.abbrev AS lvl_abbrev,",
                "dep.sector_req AS sct_req, sct.abbrev AS sct_abbrev, scheme.name AS scheme_name,",
                "dep.has_profiel AS dep_has_profiel, sct.abbrev AS sct_abbrev,",
                "CONCAT('student_', st.id::TEXT) AS mapid,",

                "CONCAT_WS (' ', st.prefix, CONCAT(st.lastname, ','), st.firstname) AS fullname,",
                "st.lastname, st.firstname, st.prefix, st.gender,",
                "st.idnumber, st.birthdate, st.birthcountry, st.birthcity,",

                "st.classname, st.examnumber, st.regnumber, st.diplomanumber, st.gradelistnumber,",
                "st.extrafacilities, st.iseveningstudent, st.islexstudent,",
                "st.bis_exam, st.partial_exam,",

                "st.linked, st.notlinked, st.sr_count, st.reex_count, st.reex03_count, st.withdrawn,",
                "st.gl_ce_avg, st.gl_combi_avg, st.gl_final_avg,",

                "st.ep01_result, st.ep02_result, st.result, st.result_status, st.result_info, st.deleted, st.tobedeleted,",

                "CASE WHEN studsubj.student_id IS NOT NULL THEN TRUE ELSE FALSE END AS has_submitted_subjects,",

                "st.modifiedby_id, st.modifiedat,",
                "au.last_name AS modby_username",

                "FROM students_student AS st",
                "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "LEFT JOIN schools_department AS dep ON (dep.id = st.department_id)",
                "INNER JOIN schools_departmentbase AS db ON (db.id = dep.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
                "LEFT JOIN subjects_scheme AS scheme ON (scheme.id = st.scheme_id)",
                "LEFT JOIN accounts_user AS au ON (au.id = st.modifiedby_id)",

                "LEFT JOIN studsubj ON (studsubj.student_id = st.id)",

                "WHERE school.examyear_id = %(ey_id)s::INT",
                "AND school.base_id = %(sb_id)s::INT",
                "AND dep.base_id = %(db_id)s::INT",

                # PR2023-01-14 tobedeleted records must also be shown
                # was: "AND NOT st.tobedeleted"

                ]

            #  show deleted students only when SBR 'Show all' is clicked
            if not show_deleted:
                sql_list.append('AND NOT st.deleted')
            if student_pk:
                sql_list.append('AND st.id = %(st_id)s::INT')
                sql_keys['st_id'] = student_pk
            else:
                # sql_clause = acc_view.get_userfilter_allowed_school_dep_lvl_sct(request)
                if logging_on:
                    logger.debug('    sql_clause: ' + str(sql_clause))
                if sql_clause:
                    sql_list.append(sql_clause)

            # order by id necessary to make sure that lookup function on client gets the right row
            sql_list.append("ORDER BY st.id")

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                student_rows = af.dictfetchall(cursor)

            if logging_on:
                logger.debug('    sql: ' + str(sql))
                # logger.debug('    student_rows: ' + str(student_rows))
                # logger.debug('connection.queries: ' + str(connection.queries))

        # - add lastname_firstname_initials to rows
            if student_rows:
                for row in student_rows:
                    first_name = row.get('firstname')
                    last_name = row.get('lastname')
                    prefix = row.get('prefix')
                    row['name_first_init'] = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)

        # - add messages to student_row
            if student_pk and student_rows and append_dict:
                # when student_pk has value there is only 1 row
                row = student_rows[0]
                if row:
                    for key, value in append_dict.items():
                        row[key] = value

        except Exception as e:
            # - return msg_err when instance not created
            #  msg format: [ { class: "border_bg_invalid", header: 'Update this', msg_html: "An eror occurred." }]
            logger.error(getattr(e, 'message', str(e)))
            # &emsp; add 4 'hard' spaces
            msg_html = '<br>'.join((
                str(_('An error occurred while loading list of candidates')) + ':',
                '&emsp;<i>' + str(e) + '</i>'
            ))
            error_dict = {'class': 'border_bg_invalid', 'msg_html': msg_html}

    return student_rows, error_dict
# --- end of create_student_rows


def create_check_birthcountry_rows(sel_examyear, sel_schoolbase, sel_depbase):
    # --- check_birthcountry rows of all students of this examyear / school PR2022-06-20
    # - show only students that are not tobedeleted
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_check_birthcountry_rows -----')

    log_list = []
    msg_html = None
    birthcountry_regex = '%maarten%' if sel_examyear.country.abbrev == 'Sxm' else 'cura%'
    country = 'Sint Maarten' if sel_examyear.country.abbrev == 'Sxm' else 'Curaçao'

    if logging_on:
        logger.debug('birthcountry_regex: ' + str(birthcountry_regex))

    if sel_examyear and sel_schoolbase and sel_depbase:
        try:
            if logging_on:
                logger.debug('sel_examyear: ' + str(sel_examyear))
                logger.debug('sel_schoolbase: ' + str(sel_schoolbase))
                logger.debug('sel_depbase: ' + str(sel_depbase))

            sql_keys = {'ey_id': sel_examyear.pk if sel_examyear else None,
                        'sb_id': sel_schoolbase.pk if sel_schoolbase else None,
                        'db_id': sel_depbase.pk if sel_depbase else None,
                        'regex': birthcountry_regex
                        }
            sql_list = ["SELECT st.lastname, st.firstname, st.prefix,",
                "st.birthcountry, COALESCE(st.birthcity, '-') AS birthcity, st.birthdate",
                "FROM students_student AS st",
                "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                "LEFT JOIN schools_department AS dep ON (dep.id = st.department_id)",

                "WHERE sch.base_id = %(sb_id)s::INT",
                "AND sch.examyear_id = %(ey_id)s::INT",
                "AND dep.base_id = %(db_id)s::INT",

                "AND st.birthdate < '2010-10-10'::DATE",
                # PR2022-06-21 debug: got error 'argument formats can't be mixed' when using: " ILIKE '" + birthcountry_regex + "'"
                # solved biij changing to  %(regex)s::TEXT, without apostroph
                # see https://www.psycopg.org/docs/usage.html#passing-parameters-to-sql-queries
                "AND TRIM(st.birthcountry) ILIKE %(regex)s::TEXT", # ILIKE is case insensitive
                #"AND (POSITION('" + birthcountry + "' IN LOWER(st.birthcountry)) > 0)",
                "AND NOT st.tobedeleted",
                "ORDER BY st.lastname, st.firstname"]
            sql = ' '.join(sql_list)
            if logging_on:
                logger.debug('sql: ' + str(sql))

            count_wrong_birthcountry = 0
            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = cursor.fetchall()
                if rows:
                    count_wrong_birthcountry = len(rows)

            if count_wrong_birthcountry:
                count_str = str(_("There is 1 candidate") if count_wrong_birthcountry == 1 else _("There are %(count)s candidates") % {'count': str(count_wrong_birthcountry)})
                is_are_str = str(_('is') if count_wrong_birthcountry == 1 else _('are'))
                this_these_str = str(_("This candidate").lower() if count_wrong_birthcountry == 1 else _('these candidates'))
                msg_html = '<br>'.join(("<p class='p-2 border_bg_warning'>" + count_str + \
                                        str(_(" with country of birth: '%(cpt)s', who %(is_are)s born before October 10, 2010.") % {'cpt': country, 'is_are': is_are_str}),
                    str(_("This is not correct, because before that date, the country was 'Nederlandse Antillen', not '%(cpt)s'.") % {'cpt': country}),
                    str(_("Click 'OK' to change the country of birth of %(this_these)s to 'Nederlandse Antillen' and the place of birth to '%(cpt)s' ") % {'this_these': this_these_str, 'cpt': country}),
                    str(_("The list of candidates, whose country of birth will be changed, has been downloaded.")) + '</p>'
                ))
                log_list.append(str(_("List of candidates, whose country of birth will be changed to 'Nederlandse Antillen'")))
                log_list.append(' ')
                log_list.append(' '.join((
                    (str(_('Candidate')).upper() + c.STRING_SPACE_30)[:30],
                    (str(_('Country of birth')).upper() + c.STRING_SPACE_20)[:20],
                    (str(_('Place of birth')).upper() + c.STRING_SPACE_20)[:20],
                    str(_('Birthdate')).upper()
                )))
                for row in rows:
                    lastname_firstname_initial = stud_fnc.get_lastname_firstname_initials(row[0], row[1], row[2])
                    log_list.append(' '.join((
                        (lastname_firstname_initial + c.STRING_SPACE_30)[:30],
                        (row[3] + c.STRING_SPACE_20)[:20],
                        (row[4] + c.STRING_SPACE_20)[:20],
                        str(row[5])
                    )))
            if logging_on:
                logger.debug('log_list: ' + str(log_list))
                # logger.debug('connection.queries: ' + str(connection.queries))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return log_list, msg_html
# --- end of create_student_rows


def change_birthcountry(sel_examyear, sel_schoolbase, sel_depbase, request):
    # --- change birthcountry in all students of this examyear / school PR2022-06-20
    # - show only students that are not tobedeleted
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- change_birthcountry -----')

    msg_dict = {}

    birthcountry_regex = '%maarten%' if sel_examyear.country.abbrev == 'Sxm' else 'cura%'
    country = 'Sint Maarten' if sel_examyear.country.abbrev == 'Sxm' else 'Curaçao'

    modifiedby_pk_str = str(request.user.pk)
    modifiedat_str = str(timezone.now())

    if logging_on:
        logger.debug('birthcountry_regex: ' + str(birthcountry_regex))

    if sel_examyear and sel_schoolbase and sel_depbase:
        try:
            if logging_on:
                logger.debug('sel_examyear: ' + str(sel_examyear))
                logger.debug('sel_schoolbase: ' + str(sel_schoolbase))
                logger.debug('sel_depbase: ' + str(sel_depbase))

            sql_keys = {'ey_id': sel_examyear.pk if sel_examyear else None,
                        'sb_id': sel_schoolbase.pk if sel_schoolbase else None,
                        'db_id': sel_depbase.pk if sel_depbase else None,
                        'regex': birthcountry_regex
                        }

    # - select students with country 'Sint Maarten' or 'Curacao'
            sub_sql_list = ["SELECT st.id AS stud_id",
                            "FROM students_student AS st",
                            "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                            "LEFT JOIN schools_department AS dep ON (dep.id = st.department_id)",

                            "WHERE sch.base_id = %(sb_id)s::INT",
                            "AND sch.examyear_id = %(ey_id)s::INT",
                            "AND dep.base_id = %(db_id)s::INT",

                            "AND st.birthdate < '2010-10-10'::DATE",
                            "AND TRIM(st.birthcountry) ILIKE %(regex)s::TEXT",  # ILIKE is case insensitive

                            "AND NOT st.tobedeleted"]
            sub_sql = ' '.join(sub_sql_list)
     # - update birthcountry and birthcity in student
            sql_list = [
                "WITH sub_sql AS (", sub_sql, ")",
                "UPDATE students_student AS stud",
                "SET birthcountry = 'Nederlandse Antillen', birthcity = '" + country + "',",
                "modifiedby_id = ", modifiedby_pk_str, ", modifiedat = '", modifiedat_str, "'",

                "FROM sub_sql",
                "WHERE stud.id = sub_sql.stud_id",
                "RETURNING stud.id"
            ]

            sql = ' '.join(sql_list)
            if logging_on:
                logger.debug('sql: ' + str(sql))
            record_count = 0
            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = cursor.fetchall()
                if rows:
                    updated_count = len(rows)
                # logger.debug('connection.queries: ' + str(connection.queries))
            if logging_on:
                logger.debug('rows: ' + str(rows))

            count_str = str(_("1 candidate") if updated_count == 1 else _("%(count)s candidates") % {'count': updated_count})

            class_str = 'border_bg_valid' if updated_count else 'border_bg_invalid'
            msg_html = str(_("The birth country of %(cnt)s have been changed to 'Nederlandse Antillen'.") % {'cnt': count_str})
            msg_dict = {'class': class_str, 'msg_html': msg_html}

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return msg_dict
# --- end of change_birthcountry


#/////////////////////////////////////////////////////////////////
def create_results_per_school_rows(request, sel_examyear, sel_schoolbase):
    # --- create rows of all students of this examyear / school PR2020-10-27 PR2022-01-03 PR2022-02-15
    # - show only students that are not tobedeleted
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_results_per_school_rows -----')

    result_dict = {}
    result_rows = []
    error_dict = {} # PR2021-11-17 new way of err msg, like in TSA

    if sel_examyear:
        try:

            if logging_on:
                logger.debug('sel_examyear: ' + str(sel_examyear))
                logger.debug('sel_schoolbase: ' + str(sel_schoolbase))

            sql_keys = {'ey_id': sel_examyear.pk, 'sb_id': sel_schoolbase.pk}
            if logging_on:
                logger.debug('sql_keys: ' + str(sql_keys))

            subsql_list = ["SELECT st.id AS stud_id,",
                           "(LOWER(st.gender) = 'm')::INT AS m,",
                           "(LOWER(st.gender) = 'v')::INT AS v,",
        # partal exam and tobedeleted are filtered out
        # return withdrawn if result is withdrawn
                "CASE WHEN result = 4 THEN 4 ELSE",
        # return passed if any result is passed, also when reex_count > 0
                    "CASE WHEN st.ep01_result = 1 OR ep02_result = 1 OR result = 1 THEN 1 ELSE",
        # return failed if result is failed
                        "CASE WHEN (result = 2) THEN 2 ELSE",
        # return reex if reex_count > 0
        # return noo result if no reex
                            "CASE WHEN st.reex_count > 0 OR st.reex03_count > 0 THEN 3 ELSE 0 END",
                        "END",
                    "END",
                "END AS resultcalc",
                "FROM students_student AS st",
                "WHERE NOT st.partial_exam",
                "AND NOT st.tobedeleted"]
            sub_sql = ' '.join(subsql_list)

            sql_list = ["WITH subsql AS (" + sub_sql + ")",
                "SELECT db.id AS db_id, db.code AS db_code, dep.name AS dep_name,",
                        "lvlbase.id AS lvlbase_id, lvlbase.code AS lvl_code, lvl.name AS lvl_name,",
                        "sb.id AS sb_id, sch.name as sch_name, sb.code as sb_code,",

                "SUM(subsql.m) AS c_m,",
                "SUM(subsql.v) AS c_v,",
                "COUNT(*) AS c_t,",

                "SUM((subsql.resultcalc = 1 AND subsql.m = 1)::INT) AS r_p_m,",
                "SUM((subsql.resultcalc = 1 AND subsql.v = 1)::INT) AS r_p_v,",
                "SUM((subsql.resultcalc = 1)::INT) AS r_p_t,",

                "SUM((subsql.resultcalc = 2 AND subsql.m = 1)::INT) AS r_f_m,",
                "SUM((subsql.resultcalc = 2 AND subsql.v = 1)::INT) AS r_f_v,",
                "SUM((subsql.resultcalc = 2)::INT) AS r_f_t,",

                "SUM((subsql.resultcalc = 3 AND subsql.m = 1)::INT) AS r_r_m,",
                "SUM((subsql.resultcalc = 3 AND subsql.v = 1)::INT) AS r_r_v,",
                "SUM((subsql.resultcalc = 3)::INT) AS r_r_t,",

                "SUM((subsql.resultcalc = 4 AND subsql.m = 1)::INT) AS r_w_m,",
                "SUM((subsql.resultcalc = 4 AND subsql.v = 1)::INT) AS r_w_v,",
                "SUM((subsql.resultcalc = 4)::INT) AS r_w_t,",

                "SUM((subsql.resultcalc = 0 AND subsql.m = 1)::INT) AS r_n_m,",
                "SUM((subsql.resultcalc = 0 AND subsql.v = 1)::INT) AS r_n_v,",
                "SUM((subsql.resultcalc = 0)::INT) AS r_n_t",

                "FROM students_student AS st",
                "INNER JOIN subsql ON (subsql.stud_id = st.id)",

                "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
                "INNER JOIN schools_departmentbase AS db ON (db.id = dep.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
                "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                "WHERE sch.examyear_id = %(ey_id)s::INT"]

            if request.user.is_role_school:
                sql_keys['sb_id'] = sel_schoolbase.pk if sel_schoolbase else None
                sql_list.append('AND sb.id = %(sb_id)s::INT')

            sql_list.append("GROUP BY db.id, dep.sequence, db.code, dep.name, lvlbase.id, lvl.sequence, lvlbase.code, lvl.name, sb.id, sb.code, sch.name")
            sql_list.append("ORDER BY dep.sequence, lvl.sequence, sb.code")

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                result_rows = af.dictfetchall(cursor)

                if logging_on:
                    for row in result_rows:
                        logger.debug('row: ' + str(row))

        except Exception as e:
            # - return msg_err when instance not created
            #  msg format: [ { class: "border_bg_invalid", header: 'Update this', msg_html: "An eror occurred." }]
            logger.error(getattr(e, 'message', str(e)))
            # &emsp; add 4 'hard' spaces
            msg_html = '<br>'.join((str(_('An error occurred')) + ':','&emsp;<i>' + str(e) + '</i>'))
            error_dict = {'class': 'border_bg_invalid', 'msg_html': msg_html}

    return result_rows, error_dict
# --- end of create_results_per_school_rows


def create_result_dict_per_school(request, sel_examyear, sel_schoolbase):
    # --- create rows of all students of this examyear / school PR2022-06-17
    # - show only students that are not tobedeleted
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_result_dict_per_school -----')

    result_dict = {}

    result_rows, error_dict = create_results_per_school_rows(request, sel_examyear, sel_schoolbase)

    if result_rows:
        for row in result_rows:
            db_id = row.get('db_id') or 0
            lvlbase_id = row.get('lvlbase_id') or 0
            sb_id = row.get('sb_id') or 0

            if db_id not in result_dict:
                result_dict[db_id] = {'db_id': db_id, 'db_code': row.get('db_code'),
                                      'dep_name': row.get('dep_name')}
            db_dict = result_dict[db_id]

            if lvlbase_id not in db_dict:
                db_dict[lvlbase_id] = {'lvlbase_id': lvlbase_id, 'lvl_code': row.get('lvl_code'),
                                   'lvl_name': row.get('lvl_name')}
            lvl_dict = db_dict[lvlbase_id]

            if sb_id not in lvl_dict:
                lvl_dict[sb_id] = row

    if logging_on:
        logger.debug('result_dict: ' + str(result_dict))

    """
    result_dict: 
        {1: {'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 
            4: {'lvlbase_id': 4, 'lvl_code': 'TKL', 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 
                13: {'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvlbase_id': 4, 'lvl_code': 'TKL', 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 'sb_id': 13, 'sch_name': 'Abel Tasman College', 'sb_code': 'CUR13', 'c_m': 4, 'c_v': 6, 'c_t': 10, 'r_p_m': 3, 'r_p_v': 6, 'r_p_t': 9, 'r_f_m': 0, 'r_f_v': 0, 'r_f_t': 0, 'r_r_m': 0, 'r_r_v': 0, 'r_r_t': 0, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0, 'r_n_m': 1, 'r_n_v': 0, 'r_n_t': 1}}}, 
        2: {'db_id': 2, 'db_code': 'Havo', 'dep_name': 'Hoger Algemeen Voortgezet Onderwijs', 
            0: {'lvlbase_id': 0, 'lvl_code': None, 'lvl_name': None, 
                13: {'db_id': 2, 'db_code': 'Havo', 'dep_name': 'Hoger Algemeen Voortgezet Onderwijs', 'lvlbase_id': None, 'lvl_code': None, 'lvl_name': None, 'sb_id': 13, 'sch_name': 'Abel Tasman College', 'sb_code': 'CUR13', 'c_m': 12, 'c_v': 9, 'c_t': 21, 'r_p_m': 7, 'r_p_v': 6, 'r_p_t': 13, 'r_f_m': 0, 'r_f_v': 2, 'r_f_t': 2, 'r_r_m': 5, 'r_r_v': 1, 'r_r_t': 6, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0, 'r_n_m': 0, 'r_n_v': 0, 'r_n_t': 0}}}, 
        3: {'db_id': 3, 'db_code': 'Vwo', 'dep_name': 'Voorbereidend Wetenschappelijk Onderwijs', 
            0: {'lvlbase_id': 0, 'lvl_code': None, 'lvl_name': None, 
                13: {'db_id': 3, 'db_code': 'Vwo', 'dep_name': 'Voorbereidend Wetenschappelijk Onderwijs', 'lvlbase_id': None, 'lvl_code': None, 'lvl_name': None, 'sb_id': 13, 'sch_name': 'Abel Tasman College', 'sb_code': 'CUR13', 'c_m': 2, 'c_v': 5, 'c_t': 7, 'r_p_m': 1, 'r_p_v': 3, 'r_p_t': 4, 'r_f_m': 0, 'r_f_v': 0, 'r_f_t': 0, 'r_r_m': 1, 'r_r_v': 2, 'r_r_t': 3, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0, 'r_n_m': 0, 'r_n_v': 0, 'r_n_t': 0}}}}
    """

    return result_dict, error_dict
# --- end of create_result_dict_per_school
#/////////////////////////////////////////////////////////////////


@method_decorator([login_required], name='dispatch')
class ValidateCompositionView(View):  # PR2022-08-25

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ValidateCompositionView ============= ')

        update_wrap = {}
        msg_list = []

        # - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit, only inspectorate kan set validation
        has_permit = request.user.role == c.ROLE_032_INSP and acc_prm.get_permit_crud_of_this_page('page_studsubj', request)

        if not has_permit:
            msg_txt = gettext("You don't have permission %(cpt)s.") % {'cpt': gettext('to validate the composition of subjects')}
            msg_html = ''.join(("<div class='p-2 border_bg_invalid'>", msg_txt, "</div>"))
        else:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                """
                upload_dict: {
                    'student_pk': 2132,
                    'subj_dispensation': True
                }    
                """
# - get variables
                student_pk = upload_dict.get('student_pk')
                subj_dispensation = upload_dict.get('subj_dispensation') or False

                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))

                updated_rows = []
                error_list = []
                append_dict = {}

# ----- get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not same_school, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase
                #sel_examyear, sel_school, sel_department, sel_level, may_edit, sel_msg_list = \
                #    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(
                #        request=request,
                #        skip_same_school_clause=True
                #    )
                selected_pk_dict = acc_prm.get_selected_pk_dict_of_user_instance(request.user)
                sel_examyear = acc_prm.get_sel_examyear_from_selected_pk_dict(selected_pk_dict)
                sel_schoolbase = acc_prm.get_sel_schoolbase_from_selected_pk_dict(selected_pk_dict)
                sel_depbase = acc_prm.get_sel_depbase_from_selected_pk_dict(selected_pk_dict)
                if logging_on:
                    logger.debug('    student_pk:   ' + str(student_pk))
                    logger.debug('    sel_examyear:   ' + str(sel_examyear))
                    logger.debug('    sel_schoolbase:   ' + str(sel_schoolbase))
                    logger.debug('    sel_depbase:   ' + str(sel_depbase))

# +++  get existing student
                student_instance = stud_mod.Student.objects.get_or_none(
                    id=student_pk,
                    school__examyear=sel_examyear
                    )
                if logging_on:
                    logger.debug('..... student_instance: ' + str(student_instance))

# -  set subj_dispensation
                if student_instance:
                    setattr(student_instance, 'subj_dispensation', subj_dispensation)
                    setattr(student_instance, 'subj_disp_modifiedby', request.user)
                    setattr(student_instance, 'subj_disp_modifiedat', timezone.now())

                    # don't update student modifiedby (don't use 'save(reuqest=request)')
                    student_instance.save()

                    if logging_on:
                        logger.debug('    student_instance.saved:   ' + str(student_instance))

# -  get studsubj_rows of this student, create list of pk's
                    #studsubj_pk_list = []
                    #sql_keys = {'stud_id': student_instance.pk}
                    #sql_list = ["SELECT studsubj.id",
                    #            "FROM students_studentsubject AS studsubj",
                    #            "WHERE studsubj.student_id = %(stud_id)s::INT",
                   #             "AND NOT studsubj.deleted"
                    #            ]
                    #sql = ' '.join(sql_list)

                    #with connection.cursor() as cursor:
                    #    cursor.execute(sql, sql_keys)
                   #     for row in cursor.fetchall():
                    #        studsubj_pk_list.append(row[0])

                    #if logging_on:
                   #     logger.debug('    studsubj_pk_list:   ' + str(studsubj_pk_list))

# -  get studentsubject_rows of this student, return to client
                    updated_studsubj_rows = create_studentsubject_rows(
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_schoolbase,
                        sel_depbase=sel_depbase,
                        append_dict={},
                        request=request,
                        student_pk=student_instance.pk
                    )
                    update_wrap['updated_studsubj_rows'] = updated_studsubj_rows
                    if logging_on:
                        for row in updated_studsubj_rows:
                            logger.debug('    row:   ' + str(row))

        if logging_on:
            logger.debug('    msg_list:   ' + str(msg_list))

# - addd messages to update_wrap
        if msg_list:
            header_txt = gettext("Validate subject composition")
            msg_html = '<br>'.join(msg_list)

            if logging_on:
                logger.debug('    header_txt:   ' + str(header_txt))
                logger.debug('    msg_html:   ' + str(msg_html))
            update_wrap['messages'] = [{'class': "border_bg_invalid", 'header': header_txt, 'msg_html': msg_html}]

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

# - end of ValidateCompositionView


@method_decorator([login_required], name='dispatch')
class ClusterUploadView(View):  # PR2022-01-06

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ClusterUploadView ============= ')

######## private functions #################

        def create_cluster(subject, cluster_pk, cluster_name):
            # --- create cluster # PR2022-01-06 PR2022-12-23
            if logging_on:
                logger.debug(' ----- create_cluster -----')

            err_list = []
            new_cluster_pk = None
            if sel_school and sel_department and subject:
                # - get value of 'cluster_name'
                new_value = cluster_name.strip() if cluster_name else None
                if logging_on:
                    logger.debug('new_value: ' + str(new_value))

                try:
                    # - validate length of cluster name
                    msg_err = av.validate_notblank_maxlength(new_value, c.MAX_LENGTH_KEY, _('The cluster name'))
                    if msg_err:
                        err_list.append(msg_err)
                    else:
                        # - validate if cluster already exists
                        name_exists = subj_mod.Cluster.objects.filter(
                            school=sel_school,
                            department=sel_department,
                            name__iexact=new_value
                        )
                        if name_exists:
                            err_list.append(str(_("%(cpt)s '%(val)s' already exists.") \
                                                % {'cpt': _('Cluster name'), 'val': new_value}))
                        else:
                            # - create and save cluster
                            cluster = subj_mod.Cluster(
                                school=sel_school,
                                department=sel_department,
                                subject=subject,
                                name=new_value
                            )
                            cluster.save(request=request)

                            if cluster and cluster.pk:
                                new_cluster_pk = cluster.pk
                                #  mapped_cluster_pk_dict: {'new_1': 296}
                                mapped_cluster_pk_dict[cluster_pk] = new_cluster_pk
                            if logging_on:
                                logger.debug('new cluster: ' + str(cluster))

                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))
                    err_list.append(str(_('An error occurred.')))
                    err_list.append(
                        str(_("%(cpt)s '%(val)s' could not be added.") % {'cpt': str(_('Cluster')),
                                                                          'val': new_value}))

            return err_list, new_cluster_pk
        # - end of create_cluster

        def delete_cluster_instance(cluster_instance):
            # --- delete cluster # PR2022-01-06  PR2022-08-08 PR2022-12-24
            if logging_on:
                logger.debug(' ----- delete_cluster_instance -----')
                logger.debug('    cluster_instance: ' + str(cluster_instance))

            msg_html = None
            this_txt = _("Cluster '%(val)s' ") % {'val': cluster_instance.name}

            updated_studsubj_pk_list = []

    # - create list of studsubj_pk with thos cluster, to update the stdsubj rows in client
            if cluster_instance:
                try:
                    sql_dict = {'cl_id': cluster_instance.pk}
                    sql = "SELECT id FROM students_studentsubject WHERE cluster_id = %(cl_id)s::INT"

                    with connection.cursor() as cursor:
                        cursor.execute(sql, sql_dict)
                        for row in cursor.fetchall():
                            updated_studsubj_pk_list.append(row[0])

                except Exception as e:
                    if logging_on:
                        logger.error(getattr(e, 'message', str(e)))

                if logging_on:
                    logger.debug('XXXXXXXXXXXX updated_studsubj_pk_list: ' + str(updated_studsubj_pk_list))

            deleted_row, err_html = sch_mod.delete_instance(
                table='cluster',
                instance=cluster_instance,
                request=request,
                this_txt=this_txt
            )
            if err_html:
                msg_html = err_html

            if logging_on:
                logger.debug('    deleted_row: ' + str(deleted_row))
                logger.debug('    msg_html: ' + str(msg_html))

            return deleted_row, updated_studsubj_pk_list, msg_html
        # - end of delete_cluster_instance

        def update_cluster_instance(cluster_instance, cluster_dict):
            # --- update existing cluster name PR2022-01-10
            logging_on = s.LOGGING_ON
            if logging_on:
                logger.debug(' ----- update_cluster_instance -----')

            err_list = []
            updated_cluster_pk = None
            if cluster_instance:
                try:
                    field = 'name'

        # - get value of 'cluster_name'
                    cluster_name = cluster_dict.get('cluster_name')
                    new_value = cluster_name.strip() if cluster_name else None

        # - get saved value of cluster name
                    saved_value = getattr(cluster_instance, field)

                    if new_value != saved_value:

        # - validate length of cluster name
                        msg_err = av.validate_notblank_maxlength(new_value, c.MAX_LENGTH_KEY, _('The cluster name'))
                        if msg_err:
                            err_list.append(msg_err)
                        else:

        # - validate if cluster already exists
                            name_exists = subj_mod.Cluster.objects.filter(
                                school=sel_school,
                                department=sel_department,
                                name__iexact=new_value
                            )
                            if name_exists:
                                err_list.append(str(_("%(cpt)s '%(val)s' already exists.") \
                                                    % {'cpt': _('Cluster name'), 'val': new_value}))
                            else:

        # - save changes
                                setattr(cluster_instance, field, new_value)
                                cluster_instance.save(request=request)
                                updated_cluster_pk = cluster_instance.pk
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                    err_list.append(''.join((str(_('An error occurred')), ' (', str(e), ').')))
                    err_list.append(str(_("%(cpt)s have not been saved.") % {'cpt': _('The changes')}))

            if logging_on:
                logger.debug('    updated_cluster_pk: ' + str(updated_cluster_pk))
            return err_list, updated_cluster_pk
        # - end of update_cluster_instance

        def loop_cluster_list(sel_school, sel_department, cluster_list, mapped_cluster_pk_dict):
            logging_on = s.LOGGING_ON
            if logging_on:
                if logging_on:
                    logger.debug(' +++++ loop_cluster_list  +++++')

            err_list = []
            created_cluster_pk_arr = []
            updated_cluster_pk_arr = []
            deleted_cluster_rows = []
            updated_studsubj_pk_list = []

            for cluster_dict in cluster_list:
                if logging_on:
                    logger.debug('     ..... cluster_dict: ' + str(cluster_dict))
                    # 'cluster_dict': {'cluster_pk': 'new_1', 'cluster_name': 'spdltl - 1', 'subject_pk': 220, 'mode': 'create'}

                # note: cluster_upload uses subject_pk, not subjbase_pk

                subject_pk = cluster_dict.get('subject_pk')
                subject = subj_mod.Subject.objects.get_or_none(
                    pk=subject_pk
                )
                if subject:
                    cluster_pk = cluster_dict.get('cluster_pk')

                    mode = cluster_dict.get('mode')
                    is_create = mode == 'create'
                    is_delete = mode == 'delete'

                    if logging_on:
                        logger.debug('    mode: ' + str(mode))
                        logger.debug('    cluster_pk: ' + str(cluster_pk))

        # +++  Create new cluster
                    if is_create:
                        cluster_name = cluster_dict.get('cluster_name')
                        err_lst, new_cluster_pk = create_cluster(
                            subject=subject,
                            cluster_pk=cluster_pk,
                            cluster_name=cluster_name
                        )
                        if err_lst:
                            err_list.extend(err_lst)
                        if new_cluster_pk:
                            created_cluster_pk_arr.append(new_cluster_pk)
                        if logging_on:
                            logger.debug('     new_cluster_pk: ' + str(new_cluster_pk))
                            logger.debug('     created_cluster_pk_arr: ' + str(created_cluster_pk_arr))
                            logger.debug('     mapped_cluster_pk_dict: ' + str(mapped_cluster_pk_dict))

        # +++  or get existing cluster
                    # filter out 'new_1', should not happen
                    elif isinstance(cluster_pk, int):
                        cluster_instance = subj_mod.Cluster.objects.get_or_none(
                            pk=cluster_pk,
                            school=sel_school,
                            department=sel_department
                        )
                        if logging_on:
                            logger.debug('    cluster_instance: ' + str(cluster_instance))

                        if cluster_instance:
        # +++ Delete cluster
                            if is_delete:
                                messages = []
                                deleted_row, studsubj_pk_list, err_html = delete_cluster_instance(cluster_instance)
                                if logging_on:
                                    logger.debug('    deleted_row: ' + str(deleted_row))
                                    logger.debug('    msg_html: ' + str(err_html))

                                if err_html:
                                    messages.append(
                                        {'header': str(_("Delete cluster")),
                                         'class': "border_bg_invalid",
                                         'msg_html': err_html}
                                    )

                                    err_list.append(err_html)
                                elif deleted_row:
                                    deleted_cluster_rows.append(deleted_row)
                                    if studsubj_pk_list:
                                        updated_studsubj_pk_list.extend(studsubj_pk_list)


        # +++ Update cluster, not when it is created, not when delete has failed (when deleted ok there is no cluster)
                            else:
                                err_lst, updated_cluster_pk = update_cluster_instance(
                                    cluster_instance=cluster_instance,
                                    cluster_dict=cluster_dict
                                )
                                if err_lst:
                                    err_list.extend(err_lst)
                                if updated_cluster_pk:
                                    updated_cluster_pk_arr.append(updated_cluster_pk)
            if logging_on:
                logger.debug('    created_cluster_pk_arr: ' + str(created_cluster_pk_arr))
                logger.debug('    updated_cluster_pk_arr: ' + str(updated_cluster_pk_arr))
                logger.debug('    deleted_cluster_rows: ' + str(deleted_cluster_rows))

            return err_list, created_cluster_pk_arr, updated_cluster_pk_arr, deleted_cluster_rows, updated_studsubj_pk_list
        # - end of loop_cluster_list

######## end of private functions #################

        update_wrap = {}
        msg_list = []

# - get permit
        has_permit = acc_prm.get_permit_crud_of_this_page('page_studsubj', request)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                """
                upload_dict: {
                    'subject_pk': 2132, 'subject_name': 'Zorg en Welzijn Intrasectoraal',
                    'cluster_list': [
                        {'cluster_pk': 210, 'cluster_name': 'zwi - 222', 'subjbase_pk': 445, 'mode': 'update'}, 
                        {'cluster_pk': 'new_1', 'cluster_name': 'zwi - 6', 'subjbase_pk': 445, 'mode': 'create'}], 
                    'studsubj_list': [
                        {'studsubj_pk': 68838, 'cluster_pk': 'new_1'}, 
                        {'studsubj_pk': 68862, 'cluster_pk': 'new_1'}, 
                        {'studsubj_pk': 68886, 'cluster_pk': 'new_1'}]}    
                """
# - get variables
                cluster_list = upload_dict.get('cluster_list')
                studsubj_list = upload_dict.get('studsubj_list')

                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))

                append_dict = {}

# ----- get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not same_school, not activated, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase

                sel_examyear, sel_school, sel_department, sel_level, may_edit, sel_msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if logging_on:
                    logger.debug('    sel_examyear:   ' + str(sel_examyear))
                    logger.debug('    sel_school:     ' + str(sel_school))
                    logger.debug('    sel_department: ' + str(sel_department))
                    logger.debug('    sel_level:      ' + str(sel_level))
                    logger.debug('    may_edit:       ' + str(may_edit))
                    logger.debug('    sel_msg_list:   ' + str(sel_msg_list))
                    logger.debug('    cluster_list:   ' + str(cluster_list))
                    logger.debug('    studsubj_list:  ' + str(studsubj_list))

                if sel_msg_list:
                    msg_list.extend(sel_msg_list)
                else:
                    sel_schoolbase = sel_school.base if sel_school else None
                    sel_depbase = sel_department.base if sel_department else None

                    mapped_cluster_pk_dict = {}

                    updated_cluster_pk_list = []
                    updated_studsubj_pk_list = []
                    updated_cluster_pk_arr = []

                    if cluster_list:

                        updated_cluster_rows = []
                        err_list, created_cluster_pk_arr, updated_cluster_pk_arr, deleted_cluster_rows, \
                            updated_studsubj_pk_arr = \
                                loop_cluster_list(
                                    sel_school=sel_school,
                                    sel_department=sel_department,
                                    cluster_list=cluster_list,
                                    mapped_cluster_pk_dict=mapped_cluster_pk_dict
                                )
                        if err_list:
                            msg_list.extend(err_list)

                        if updated_cluster_pk_arr:
                            updated_cluster_pk_list.extend(updated_cluster_pk_arr)

                        if updated_studsubj_pk_arr:
                            updated_studsubj_pk_list.extend(updated_studsubj_pk_arr)

                        if logging_on:
                            logger.debug('    created_cluster_pk_arr:  ' + str(created_cluster_pk_arr))
                            logger.debug('    updated_cluster_pk_arr:   ' + str(updated_cluster_pk_arr))
                            logger.debug('    deleted_cluster_rows:   ' + str(deleted_cluster_rows))
                            logger.debug('    updated_studsubj_pk_arr:   ' + str(updated_studsubj_pk_arr))

                        if created_cluster_pk_arr or updated_cluster_pk_arr:
                            # add created pk's to updated ar,, to get cluster_rows in one batch
                            updated_cluster_pk_arr.extend(created_cluster_pk_arr)

                            updated_cluster_rows = sj_vw.create_cluster_rows(
                                request=request,
                                sel_examyear=sel_examyear,
                                sel_schoolbase=sel_schoolbase,
                                sel_depbase=sel_depbase,
                                cur_dep_only=True,
                                allowed_only=False,
                                cluster_pk_list=updated_cluster_pk_arr
                            )

                            if updated_cluster_rows:
                # - add key 'created' to created rows, used in client to add to table Clustres
                                for row in updated_cluster_rows:
                                    if row.get('id') in created_cluster_pk_arr:
                                        row['created'] = True

            # - add deleted cluster_rows to updated_cluster_rows
                        # since seleted cluster does not exist any more, add info of deleted_cluster_rows directly to  updated_cluster_rows
                        if deleted_cluster_rows:
                            updated_cluster_rows.extend(deleted_cluster_rows)

            # - add updated_cluster_rows to update_wrap
                        if updated_cluster_rows:
                            update_wrap['updated_cluster_rows'] = updated_cluster_rows

                    if studsubj_list:
                        err_list, studsubj_pk_list = loop_studsubj_list(studsubj_list, mapped_cluster_pk_dict, request)
                        if err_list:
                            msg_list.extend(err_list)
                        if studsubj_pk_list:
                            updated_studsubj_pk_list.extend(studsubj_pk_list )
                        if logging_on:
                            logger.debug('studsubj_pk_list: ' + str(studsubj_pk_list))

                    if updated_studsubj_pk_list or updated_cluster_pk_arr:
                        studsubj_rows = create_studentsubject_rows(
                            sel_examyear=sel_examyear,
                            sel_schoolbase=sel_schoolbase,
                            sel_depbase=sel_depbase,
                            append_dict=append_dict,
                            request=request,
                            requsr_same_school=True,  # check for same_school is included in may_edit
                            studsubj_pk_list=updated_studsubj_pk_list,
                            cluster_pk_list=updated_cluster_pk_arr
                        )

                        if studsubj_rows:
                            update_wrap['updated_studsubj_rows'] = studsubj_rows

        # - addd messages to update_wrap
        if msg_list:
            update_wrap['messages'] = [{'class': "border_bg_invalid", 'msg_html': '<br>'.join(msg_list)}]

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of ClusterUploadView


def loop_studsubj_list(studsubj_list, mapped_cluster_pk_dict, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- loop_studsubj_list  -----')
        logger.debug('studsubj_list: ' + str(studsubj_list))
        logger.debug('mapped_cluster_pk_dict: ' + str(mapped_cluster_pk_dict))

    err_list = []
    updated_studsubj_list = []
    """
    'studsubj_list': [
        {'studsubj_pk': 68838, 'cluster_pk': 'new_1'},
        {'studsubj_pk': 68862, 'cluster_pk': 'new_1'},
        {'studsubj_pk': 68886, 'cluster_pk': 'new_1'}]}
    """
    if studsubj_list:

        sql_studsubj_list = []
        for studsubj_dict in studsubj_list:
            studsubj_pk = studsubj_dict.get('studsubj_pk')

            if logging_on:
                logger.debug('studsubj_dict: ' + str(studsubj_dict))
                # studsubj_dict: {'studsubj_pk': 45092, 'cluster_pk': 'new_1'}

            if studsubj_pk:
                cluster_pk = studsubj_dict.get('cluster_pk')
                if logging_on:
                    logger.debug('cluster_pk: ' + str(cluster_pk) + ' ' + str(type(cluster_pk)))

        # replace cluster_pk 'new_1' bij saved cluster_pk
                clean_cluster_pk = None
                if isinstance(cluster_pk, int):
                    clean_cluster_pk = cluster_pk
                    if logging_on:
                        logger.debug('isinstance clean_cluster_pk: ' + str(clean_cluster_pk) + ' ' + str(type(clean_cluster_pk)))
                elif cluster_pk in mapped_cluster_pk_dict:
                    clean_cluster_pk = mapped_cluster_pk_dict[cluster_pk]
                    if logging_on:
                        logger.debug('mapped_cluster_pk_dict clean_cluster_pk: ' + str(clean_cluster_pk) + ' ' + str(type(clean_cluster_pk)))

                clean_cluster_str = str(clean_cluster_pk) if clean_cluster_pk else 'NULL'

                sql_studsubj_list.append((str(studsubj_pk), clean_cluster_str))

                if logging_on:
                    logger.debug('clean_cluster_pk: ' + str(clean_cluster_pk) + ' ' + str(type(clean_cluster_pk)))
                    logger.debug('clean_cluster_str: ' + str(clean_cluster_str))
                    logger.debug('sql_studsubj_list: ' + str(sql_studsubj_list))

        # sql_keys = {'ey_id': school.examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}

        """
        # you can define the types by casting the values of the first row:
        CREATE TEMP TABLE lookup (key, val) AS
        VALUES 
            (0::bigint, -99999::int), 
            (1, 100) ;
        """

        modifiedby_pk_str = str(request.user.pk)
        modifiedat_str = str(timezone.now())

    # fields are: [studentsubject_id, cluster_id, modifiedby_id, modifiedat]
        sql_list = ["DROP TABLE IF EXISTS tmp; CREATE TEMP TABLE tmp (ss_id, cl_id) AS VALUES (0::INT, 0::INT)"]

        for row in sql_studsubj_list:
            sql_list.append(''.join((", (", str(row[0]), ', ' , str(row[1]), ")")))
        sql_list.extend((
            "; UPDATE students_studentsubject AS ss",
            "SET cluster_id = tmp.cl_id, modifiedby_id = ", modifiedby_pk_str, ", modifiedat = '", modifiedat_str, "'",
            "FROM tmp",
            "WHERE ss.id = tmp.ss_id",
            "RETURNING ss.id;"
        ))

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            if logging_on:
                logger.debug('rows: ' + str(rows))

            if rows:
                for row in rows:
                    updated_studsubj_list.append(row[0])
    # - end of save_studsubj_batch


    return err_list, updated_studsubj_list
# - end of loop_studsubj_list


@method_decorator([login_required], name='dispatch')
class StudentUploadView(View):  # PR2020-10-01 PR2021-07-18 PR2022-12-27 PR2023-01-16

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= StudentUploadView ============= ')
        messages = []
        update_wrap = {}

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')

# - get permit
            page_name = 'page_result' if mode == 'withdrawn' else 'page_student'
            has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

            if logging_on:
                logger.debug('    has_permit:' + str(has_permit))

            if not has_permit:
                messages.append(
                    {'class': "border_bg_invalid",
                     'msg_html': str(_("You don't have permission to perform this action."))}
                )

            else:

# - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get variables
                student_pk = upload_dict.get('student_pk')
                is_create = mode == 'create'
                is_delete = mode == 'delete_candidate'
                is_restore = mode == 'restore_candidate'

                updated_rows = []
                error_list = []
                messages = []
                append_dict = {}

                header_txt = _('Add candidate') if is_create else _('Delete candidate') if is_delete else _('Edit candidate')

# ----- get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not same_school, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase
                sel_examyear, sel_school, sel_department, sel_level, may_edit, sel_msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if logging_on:
                    logger.debug('    may_edit:       ' + str(may_edit))
                    logger.debug('    sel_msg_list:       ' + str(sel_msg_list))
                    logger.debug('    upload_dict:       ' + str(upload_dict))
                """
                sel_msg_list = msg_list.append(str(_("You don't have permission to view department %(val)s.") % {'val': sel_depbase.code}))
                upload_dict:  {'table': 'student', 'mode': 'create', 'lastname': 'aa', 'firstname': 'aa', 'gender': 'M', 'idnumber': '2000101010', 'level': 6, 'sector': 12}
               
                """
                if sel_msg_list:
                    msg_html = '<br>'.join(sel_msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                    if logging_on:
                        logger.debug('messages:   ' + str(messages))
                else:

# +++  Create new student
                    if is_create:
                        student_instance = None

                        id_number = upload_dict.get('idnumber')
                        last_name = upload_dict.get('lastname')
                        first_name = upload_dict.get('firstname')
                        prefix = upload_dict.get('prefix')
                        lvlbase_pk = upload_dict.get('level')
                        sctbase_pk = upload_dict.get('sector')

                        idnumber_nodots, msg_err_list, birthdate_dteobjNIU = stud_val.get_idnumber_nodots_stripped_lower(
                            id_number)
                        if msg_err_list:
                            error_list.extend(msg_err_list)

                        lastname_stripped, msg_err = stud_val.get_string_convert_type_and_strip(_('Last name'), last_name, True)  # True = blank_not_allowed
                        if msg_err:
                            error_list.append(str(msg_err))

                        firstname_stripped, msg_err = stud_val.get_string_convert_type_and_strip(_('First name'), first_name, True)  # True = blank_not_allowed
                        if msg_err:
                            error_list.append(str(msg_err))

                        prefix_stripped, msg_err = stud_val.get_string_convert_type_and_strip(_('Prefix'), prefix, False)  # False = blank_allowed
                        if msg_err :
                            error_list.append(str(msg_err))

                        full_name = stud_val.get_prefix_lastname_comma_firstname(lastname_stripped, firstname_stripped, prefix_stripped)

                        # - create student record
                        if not error_list:
                            student_instance, error_list = create_student_instance(
                                examyear=sel_examyear,
                                school=sel_school,
                                department=sel_department,
                                idnumber_nodots=idnumber_nodots,
                                lastname_stripped=lastname_stripped,
                                firstname_stripped=firstname_stripped,
                                prefix_stripped=prefix_stripped,
                                full_name=full_name,
                                lvlbase_pk=lvlbase_pk,
                                sctbase_pk=sctbase_pk,
                                request=request,
                                found_is_error=True,
                                skip_save=False
                            )

                        if error_list:
                            messages.append(
                                {'header': str(header_txt),
                                 'class': "border_bg_invalid",
                                 'msg_html': '<br>'.join(error_list)}
                            )
                        if student_instance:
                            append_dict['created'] = True
                    else:

# +++  or get existing student
                        student_instance = stud_mod.Student.objects.get_or_none(
                            id=student_pk,
                            school=sel_school
                        )
                    if logging_on:
                        logger.debug('student_instance: ' + str(student_instance))

                    restored_student_success = False

                    if student_instance:

# +++ Delete student
                        if is_delete:
                            deleted_row, err_html = set_student_instance_tobedeleted(student_instance, request)
                            if err_html:
                                messages.append(
                                    {'header': str(header_txt),
                                     'class': "border_bg_invalid",
                                     'msg_html': err_html}
                                )
                            elif deleted_row:
                                student_instance = None
                                updated_rows.append(deleted_row)

                            if logging_on:
                                logger.debug('    is_delete: ' + str(is_delete))
                                logger.debug('    deleted_row: ' + str(deleted_row))
                                logger.debug('    err_html: ' + str(err_html))

# +++ restore tobedeleted student
                        elif is_restore:
                            restored_student_success, updated_studsubj_rows, msg_html = restore_student_instance(student_instance, request)
                            if msg_html:
                                messages.append(
                                    {'header': str(header_txt),
                                     'class': "border_bg_invalid",
                                     'msg_html': msg_html}
                                )
                            if not restored_student_success:
                                student_instance = None

                            if logging_on:
                                logger.debug('    is_restore: ' + str(is_restore))
                                logger.debug('    restored_student_success: ' + str(restored_student_success))
                                logger.debug('    updated_studsubj_rows: ' + str(updated_studsubj_rows))
                                logger.debug('    msg_html: ' + str(msg_html))

# +++ Update student, also when it is created, not when delete has failed (when deleted ok there is no student)
                        else:
                            err_fields = []
                            idnumber_list = []
                            examnumber_list = []
                            update_student_instance(
                                instance=student_instance,
                                sel_examyear=sel_examyear,
                                sel_school=sel_school,
                                sel_department=sel_department,
                                upload_dict=upload_dict,
                                idnumber_list=idnumber_list,
                                examnumber_list=examnumber_list,
                                diplomanumber_list=[],
                                gradelistnumber_list=[],
                                msg_list=messages,
                                error_list=error_list,
                                err_fields=err_fields,  # err_fields is only used in update student
                                log_list=[], # log_list is only used in upload students
                                request=request,
                                skip_save=False
                            )

# - create student_row, also when deleting failed, not when deleted ok, in that case student_row is added in delete_student
                    if student_instance:
                        updated_rows, error_dictNIU = create_student_rows(
                            request=request,
                            sel_examyear=sel_school.examyear,
                            sel_schoolbase=sel_school.base,
                            sel_depbase=sel_department.base,
                            append_dict=append_dict,
                            student_pk=student_instance.pk)

                        if restored_student_success and updated_rows:
                            for row in updated_rows:
                                row['restored'] = True


                update_wrap['updated_student_rows'] = updated_rows

# - addd messages to update_wrap
        if messages:
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentUploadView


@method_decorator([login_required], name='dispatch')
class ChangeBirthcountryView(View):  # PR2022-06-20

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ChangeBirthcountryView ============= ')

        update_wrap = {}
        messages = []

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')

# - get permit
            page_name = 'page_result' if mode == 'withdrawn' else 'page_student'
            has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

            if has_permit:

# - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# ----- get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_edit, sel_msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if logging_on:
                    logger.debug('sel_examyear:   ' + str(sel_examyear))
                    logger.debug('sel_school:     ' + str(sel_school))
                    logger.debug('sel_department: ' + str(sel_department))
                    logger.debug('may_edit:       ' + str(may_edit))
                    logger.debug('sel_msg_list:       ' + str(sel_msg_list))

                if len(sel_msg_list):
                    msg_html = '<br>'.join(sel_msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                else:
                    msg_dict = change_birthcountry(sel_examyear, sel_school.base, sel_department.base, request)
                    if msg_dict:
                        messages.append(msg_dict)

# - addd messages to update_wrap
        if len(messages):
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentUploadView
# - end of ChangeBirthcountryView

@method_decorator([login_required], name='dispatch')
class StudentMultipleOccurrencesView(View):  # PR2021-09-05

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= StudentMultipleOccurrencesView ============= ')

        # function validates studentsubject records of all students of this dep PR2021-07-10
        # exclude deleted and other country PR2023-01-17
        update_wrap = {}
        multiple_occurrences_list = []

# - get permit - only download list when user has permit_crud
        has_permit = acc_prm.get_permit_crud_of_this_page('page_studsubj', request)
        if has_permit:

# - reset language
            #user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            #activate(user_lang)

            # - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:

    # ----- get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_listNIU = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

    # +++ get dict of multiple_occurrences
                if sel_examyear and sel_school and sel_department and may_edit:
                    multiple_occurrences_list, multiple_occurrences_dict = stud_val.get_multiple_occurrences(sel_examyear, sel_school.base, sel_department.base)

    # +++ link students with the same idnumber , lastname and firstname
                    #if dictlist:
                    #    stud_val.link_students_with_multiple_occurrences(dictlist)
                    if multiple_occurrences_list:
                        update_wrap['multiple_occurrences_dict'] = multiple_occurrences_dict

        update_wrap['multiple_occurrences_list'] = multiple_occurrences_list
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentMultipleOccurrencesView




@method_decorator([login_required], name='dispatch')
class StudentLinkStudentView(View):  # PR2021-09-06

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= StudentLinkStudentView ============= ')

        update_wrap = {}
        messages = []

# - get permit - StudentLinkStudentView is called from page studsubj
        has_permit = acc_prm.get_permit_crud_of_this_page('page_studsubj', request)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                # upload_dict: {'mode': 'tick', 'cur_stud_id': 6259, 'oth_stud_id': 5991, 'table': 'student', 'linked': False}

# - get variables
                mode = upload_dict.get('mode')
                cur_stud_pk = upload_dict.get('cur_stud_id')
                oth_stud_pk = upload_dict.get('oth_stud_id')

                if logging_on:
                    logger.debug('    upload_dict: ' + str(upload_dict))
                    logger.debug('    mode: ' + str(mode))
                    logger.debug('    cur_stud_pk: ' + str(cur_stud_pk))
                    logger.debug('    oth_stud_pk: ' + str(oth_stud_pk))

                updated_rows = []
                append_dict = {}
                error_list = []

# ----- get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not same_school, not activated, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase
                sel_examyear, sel_school, sel_department, sel_level, may_edit, sel_msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if logging_on:
                    logger.debug('    sel_examyear:   ' + str(sel_examyear))
                    logger.debug('    sel_school:     ' + str(sel_school))
                    logger.debug('    sel_department: ' + str(sel_department))
                    logger.debug('    may_edit:       ' + str(may_edit))
                    logger.debug('    sel_msg_list:       ' + str(sel_msg_list))
                    logger.debug('.....')

                if len(sel_msg_list):
                    msg_html = '<br>'.join(sel_msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                else:

                    try:
    # +++  get current student
                        cur_student = stud_mod.Student.objects.get_or_none(
                            id=cur_stud_pk,
                            school=sel_school
                        )

                        if cur_student and oth_stud_pk:
                            other_stud_pk_str = str(oth_stud_pk)
                            if logging_on:
                                logger.debug('    cur_student:   ' + str(cur_student))
                                logger.debug('    other_stud_pk_str:   ' + str(other_stud_pk_str))

                    # get linked_arr and notlinked_arr from cur_student
                            linked_str = getattr(cur_student, 'linked')
                            linked_arr = linked_str.split(';') if linked_str else []
                            # linked_arr: ['5991', '8531']

                            notlinked_str = getattr(cur_student, 'notlinked')
                            notlinked_arr = notlinked_str.split(';') if notlinked_str else []
                            # notlinked_arr: ['8422']

                            if logging_on:
                                logger.debug('    mode: ' + str(mode))
                                logger.debug('    linked_arr: ' + str(linked_arr))
                                logger.debug('    notlinked_arr: ' + str(notlinked_arr))
                                logger.debug('    other_student_islinked: ' + str(other_stud_pk_str in linked_arr))
                                logger.debug('    other_student_notlinked: ' + str(other_stud_pk_str in notlinked_arr))

                # =====  link ============================
                            if mode == 'link':

                                # when clicked on tick: 'linked' = True sets link, 'linked' = False removes link
                                set_linked = upload_dict.get('linked', False)

                                set_student_linked_ok = set_student_linked(
                                    set_linked, linked_arr, notlinked_arr, other_stud_pk_str, cur_student,
                                                request)

                                #  TODO make_student_biscandidate(cur_student, other_student, request)
                                # add exemptions

                                #if set_student_linked_ok:
                                #    set_student_bisexam_and_exemptions(cur_student, other_stud_pk_str)
                # =====  unlink ============================
                            elif mode == 'unlink':

                                # when clicked on cross: 'unlinked' = True sets unlink, 'unlinked' = False removes unlink

                                # unlink if other_student is different from cur_student:
                                #  -  add oth_stud_pk to notlinked charfield, if not exists yet
                                #  -  remove oth_stud_pk from linked charfield, if exists

                                set_notlinked = upload_dict.get('notlinked', False)
                                set_student_notlinked(set_notlinked, linked_arr, notlinked_arr, other_stud_pk_str,
                                                 cur_student, request)


                        # - create student_row, also when deleting failed, not when deleted ok, in that case student_row is added in delete_student
                            #TODO this is not used, check if can be removed
                            student_pk = cur_student.pk if cur_student else None
                            updated_rows, error_dictNIU = create_student_rows(
                                request=request,
                                sel_examyear=sel_school.examyear,
                                sel_schoolbase=sel_school.base,
                                sel_depbase=sel_department.base,
                                append_dict=append_dict,
                                student_pk=student_pk)

                            # bewijs van vrijstelling is valid for 10 years when evening or lex school
                            if sel_school.iseveningschool or sel_school.islexschool:
                                firstinrange_examyear_int = sel_examyear.code - 10 if sel_examyear.code else None
                            else:
                                firstinrange_examyear_int = sel_examyear.code - 1 if sel_examyear.code else None

                            student_idnumber = getattr(cur_student, 'idnumber')
                            student_dict = stud_val.lookup_multiple_occurrences(
                                firstinrange_examyear_int=firstinrange_examyear_int,
                                sel_examyear=sel_examyear,
                                sel_schoolbase=sel_school.base,
                                sel_depbase=sel_department.base,
                                student_idnumber=student_idnumber
                            )
                            update_wrap['updated_multiple_occurrences'] = [student_dict]

                    except Exception as e:
                        logger.error(getattr(e, 'message', str(e)))

        if len(messages):
            update_wrap['messages'] = messages
            # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentLinkStudentView


def set_student_linked(set_linked, linked_arr, notlinked_arr, other_stud_pk_str, cur_student, request):
    # PR2021-09-06 PR2023-01-17

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug(' ----- set_student_linked -----')
        logger.debug('    cur_student: ' + str(cur_student))
        logger.debug('    set_linked: ' + str(set_linked))
        logger.debug('    other_stud_pk_str: ' + str(other_stud_pk_str))
    set_student_linked_ok = False
    if cur_student and other_stud_pk_str:
        try:

            if set_linked:
                # - add oth_stud_pk to linked_arr
                if other_stud_pk_str not in linked_arr:
                    linked_arr.append(other_stud_pk_str)
                    if linked_arr:
                        linked_arr.sort()
                    linked_str = ';'.join(linked_arr)
                    setattr(cur_student, 'linked', linked_str)
                    set_student_linked_ok = True

                    if logging_on:
                        logger.debug(' ----set_linked------')
                        logger.debug('    cur_student.linked: ' + str(cur_student.linked))
                        logger.debug('    cur_student.notlinked: ' + str(cur_student.notlinked))
                        logger.debug('    set_student_linked_ok: ' + str(set_student_linked_ok))


                # - remove all occurrencies of oth_stud_pk from unlinked charfield, if exists
                if notlinked_arr and other_stud_pk_str in notlinked_arr:
                    #  -  note: arr.remove(str) removes only the first occuuerncy
                    #  -  this removes all occurrencies of oth_stud_pk from linked charfield
                    # PR2021-09-17 from: https://note.nkmk.me/en/python-list-comprehension/
                    new_notlinked_arr = [pk_str for pk_str in notlinked_arr if pk_str != other_stud_pk_str]
                    new_notlinked_str = ';'.join(new_notlinked_arr) if new_notlinked_arr else None

                    setattr(cur_student, 'notlinked', new_notlinked_str)

                cur_student.save(request=request)

            else:
                # - remove other_stud_pk from linked_arr
                if linked_arr and other_stud_pk_str in linked_arr:
                    #  -  note: arr.remove(str) removes only the first occuuerncy
                    #  -  this removes all occurrencies of oth_stud_pk from linked charfield
                    # PR2021-09-17 from: https://note.nkmk.me/en/python-list-comprehension/
                    new_linked_arr = [pk_str for pk_str in linked_arr if pk_str != other_stud_pk_str]
                    new_linked_str = ';'.join(new_linked_arr) if new_linked_arr else None

                    setattr(cur_student, 'linked', new_linked_str)

                    cur_student.save(request=request)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug(' ----------')
        logger.debug('    cur_student.linked: ' + str(cur_student.linked))
        logger.debug('    cur_student.notlinked: ' + str(cur_student.notlinked))
        logger.debug('    set_student_linked_ok: ' + str(set_student_linked_ok))

    return set_student_linked_ok

# - end of set_student_linked


def set_student_notlinked(set_notlinked, linked_arr, notlinked_arr, other_stud_pk_str, cur_student, request):
    # PR2021-09-06 PR2023-01-17

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug(' ----- set_student_notlinked -----')

    set_student_notlinked_ok = False
    if cur_student and other_stud_pk_str:

        try:
            # if notlinked: add other_stud_pk_str to notlinked
            if set_notlinked:
                # - add other_stud_pk_str to notlinked, remove linked if necessary
                notlinked_arr.append(other_stud_pk_str)
                notlinked_arr.sort()
                notlinked_str = ';'.join(notlinked_arr)

                setattr(cur_student, 'notlinked', notlinked_str)

                # - remove all occurrencies of oth_stud_pk from linked charfield
                if other_stud_pk_str in linked_arr:
                    # PR2021-09-17 from: https://note.nkmk.me/en/python-list-comprehension/
                    new_linked_arr = [pk_str for pk_str in linked_arr if pk_str != other_stud_pk_str]
                    new_linked_str = ';'.join(new_linked_arr) if new_linked_arr else None

                    setattr(cur_student, 'linked', new_linked_str)
                    logger.debug('new_linked_str: ' + str(new_linked_str))

                    cur_student.save(request=request)
                    set_student_notlinked_ok = True
                else:
                    # dont update modifiedat when only other_student removed from nonlinked field
                    cur_student.save()

            else:
                # if notlinked = False: remove other_stud_pk_str from notlinked
                if other_stud_pk_str in notlinked_arr:
                    #  -  remove all occurrencies of oth_stud_pk from notlinked charfield
                    # PR2021-09-17 from: https://note.nkmk.me/en/python-list-comprehension/
                    new_notlinked_arr = [pk_str for pk_str in notlinked_arr if pk_str != other_stud_pk_str]
                    new_notlinked_str = ';'.join(new_notlinked_arr) if new_notlinked_arr else None

                    setattr(cur_student, 'notlinked', new_notlinked_str)
                    logger.debug('new_linked_str: ' + str(new_notlinked_str))

                    # dont update modifiedat when only other_student removed from nonlinked field
                    cur_student.save()

            if logging_on:
                logger.debug('.............')
                logger.debug('    cur_student:   ' + str(cur_student))
                logger.debug('    cur_student.linked: ' + str(cur_student.linked))
                logger.debug('    cur_student.notlinked: ' + str(cur_student.notlinked))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
    return set_student_notlinked_ok
# - end of set_student_notlinked


@method_decorator([login_required], name='dispatch')
class StudentEnterExemptionsView(View):  # PR203-01-24

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= StudentEnterExemptionsView ============= ')

        update_wrap = {}
        messages = []

        log_list = []

# - get permit - StudentLinkStudentView is called from page studsubj
        has_permit = acc_prm.get_permit_crud_of_this_page('page_studsubj', request)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                # upload_dict: {'mode': 'tick', 'cur_stud_id': 6259, 'oth_stud_id': 5991, 'table': 'student', 'linked': False}

# - get variables
                if logging_on:
                    logger.debug('    upload_dict: ' + str(upload_dict))

                sel_examyear, sel_school, sel_department, sel_level, may_edit, sel_msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if logging_on:
                    logger.debug('    sel_examyear:   ' + str(sel_examyear))
                    logger.debug('    sel_school:     ' + str(sel_school))
                    logger.debug('    sel_department: ' + str(sel_department))
                    logger.debug('.....')

                if len(sel_msg_list):
                    msg_html = '<br>'.join(sel_msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                else:

                    try:
        # +++ get dict of multiple_occurrences

                        if sel_examyear and sel_school and sel_department and may_edit:
                            updated_grade_pk_list = []
        # - create log_list
                            today_dte = af.get_today_dateobj()
                            today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

                            school_name = sel_school.base.code + ' ' + sel_school.name
                            log_list.append(c.STRING_DOUBLELINE_80)
                            log_list.append(str(_('Enter exemptions')) + ' ' + str(_('date')) + ': ' + str(today_formatted))
                            log_list.append(c.STRING_DOUBLELINE_80)

                            log_list.append(c.STRING_SPACE_05 + str(_("School    : %(name)s") % {'name': school_name}))
                            log_list.append(c.STRING_SPACE_05 + str(_("Department: %(dep)s") % {'dep': sel_department.name}))
                            log_list.append(c.STRING_SPACE_05 + str(_("Exam year : %(ey)s") % {'ey': str(sel_examyear.code)}))

                            log_list.append(c.STRING_SPACE_05)

                            linked_students = stud_mod.Student.objects.filter(
                                school=sel_school,
                                department=sel_department,
                                linked__isnull=False,
                                partial_exam=False,
                                deleted=False,
                                tobedeleted=False
                            )
                            if linked_students:
                                append_dict = {}
                                for cur_stud in linked_students:
                                    cur_examyear_code = cur_stud.school.examyear.code
                                    cur_depbase = cur_stud.department.base
                                    cur_depbase_code = cur_depbase.code
                                    cur_lvlbase = cur_stud.level.base
                                    cur_sctbase = cur_stud.sector.base
                                    cur_lvlbase_code = cur_lvlbase.code if cur_lvlbase else ''
                                    cur_sctbase_code = cur_sctbase.code if cur_sctbase else ''

                                    linked_arr = list(map(int, cur_stud.linked.split(';')))

                                    is_evelex = cur_stud.iseveningstudent or cur_stud.islexstudent

                                    curstud_logtxt_added = False

                                    if logging_on:
                                        logger.debug('cur_stud:   ' + str(cur_stud))
                                        logger.debug(' cur_examyear_code:   ' + str(cur_examyear_code))
                                        logger.debug(' cur_depbase:   ' + str(cur_depbase))
                                        logger.debug(' cur_lvlbase:   ' + str(cur_lvlbase))
                                        logger.debug(' linked_arr:   ' + str(linked_arr))
                                        logger.debug(' ..........')

                                    if linked_arr:

                # ++++++ loop through other_students
                                        for other_student_pk in linked_arr:
                                            other_stud = stud_mod.Student.objects.get_or_none(
                                                pk=other_student_pk,
                                                deleted=False,
                                                tobedeleted=False,
                                                partial_exam=False,
                                                result=c.RESULT_FAILED
                                            )
                                            if other_stud:
                                                other_examyear_code = other_stud.school.examyear.code
                                                other_depbase = other_stud.department.base
                                                other_lvlbase = other_stud.level.base
                                                other_sctbase = other_stud.sector.base
                                                other_result_status = other_stud.result_status
                                                other_failed = (other_stud.result == c.RESULT_FAILED)
                                                other_school = other_stud.school.name
                                                other_depbase_code = other_depbase.code
                                                other_lvlbase_code = other_lvlbase.code if other_lvlbase else ''
                                                other_sctbase_code = other_sctbase.code if other_sctbase else ''

                                                if logging_on:
                                                    logger.debug('    other_stud:   ' + str(other_stud))
                                                    logger.debug('    other_examyear_code:   ' + str(other_examyear_code))
                                                    logger.debug('    other_depbase:   ' + str(other_depbase))
                                                    logger.debug('    other_lvlbase:   ' + str(other_lvlbase))
                                                    logger.debug('    other_failed:   ' + str(other_failed))

                # is exam year correct?
                                                valid_years = 10 if is_evelex else 1
                                                examyear_is_correct = (other_examyear_code < cur_examyear_code and
                                                                    other_examyear_code >= cur_examyear_code - valid_years)
                                                if logging_on:
                                                    logger.debug('    examyear_is_correct:   ' + str(examyear_is_correct))

                                                if examyear_is_correct:
                # dep and level correct?
                                                    if other_depbase == cur_depbase and other_lvlbase == cur_lvlbase:

                                                        if logging_on:
                                                            logger.debug('    BINGO:   ')

                # set student bis_exam = True if False
                                                        cur_stud_bis_exam = getattr(cur_stud, 'bis_exam')
                                                        if not cur_stud_bis_exam:
                                                            setattr(cur_stud, 'bis_exam', True)
                                                            cur_stud.save(request=request)

                 # - create log header for this student
                                                        if not curstud_logtxt_added:
                                                            log_list.append(' ')

                                                            log_list.append(''.join((
                                                                cur_stud.fullname,
                                                                ' - ' + cur_depbase_code,
                                                                ' - ' + cur_lvlbase_code if cur_lvlbase else '',
                                                                ' - ' + cur_sctbase_code if cur_sctbase else ''
                                                            )))
                                                            log_list.append(c.STRING_SPACE_05 + str(
                                                                _("The exam of this candidate is %(is_already)s marked as 'bis-exam'.") %
                                                                {'is_already': _(
                                                                    'already') if cur_stud_bis_exam else 'now'}))

                                                            curstud_logtxt_added = True

                                                        log_list.append(''.join((c.STRING_SPACE_05,
                                                                                     (str(other_examyear_code) + c.STRING_SPACE_05)[:5],
                                                                                     other_school,
                                                                                     ' - ' + other_depbase_code,
                                                                                     ' - ' + other_lvlbase_code if other_lvlbase else '',
                                                                                     ' - ' + other_sctbase_code if other_sctbase else ''
                                                                                     ' - ' + other_sctbase_code if other_sctbase else '',
                                                                                     ' - ' + other_result_status if other_result_status else '',
                                                                                     )))

                            # - get subjects with pok of other student
                                                        other_studsubjects = stud_mod.Studentsubject.objects.filter(
                                                            student=other_stud,
                                                            tobedeleted=False,
                                                            deleted=False,
                                                            pok_validthru__isnull=False
                                                        )
                                                        if other_studsubjects is None:
                                                            log_list.append(''.join((c.STRING_SPACE_10,
                                                                                     str(_('This candidate has no Proofs of Knowledge.'))
                                                                                     )))
                                                        else:
                                                            for other_studsubj in other_studsubjects:

                                                                subj_code = other_studsubj.schemeitem.subject.base.code if other_studsubj.schemeitem.subject.base.code else '---'
                                                                pok_sesr = other_studsubj.pok_sesr.replace('.', ',') if other_studsubj.pok_sesr else '-'
                                                                pok_pece = other_studsubj.pok_pece.replace('.', ',')  if other_studsubj.pok_pece else '-'
                                                                pok_final = other_studsubj.pok_final.replace('.', ',')  if other_studsubj.pok_final else '-'

                                                                if logging_on:
                                                                    logger.debug('........ ')
                                                                    logger.debug('    other_studsubj: ' + str(other_studsubj))
                                                                    logger.debug('    other_studsubj: ' + str(other_studsubj.schemeitem.subject.base.code))
                                                                    logger.debug('    other_studsubj pok_validthru: ' + str(other_studsubj.pok_validthru))
                                                                    logger.debug('    other_studsubj pok_final: ' + str(other_studsubj.pok_final))

                                # get corresonding cur_studsubject
                                                                cur_studsubj = stud_mod.Studentsubject.objects.get_or_none(
                                                                    student=cur_stud,
                                                                    schemeitem__subject__base=other_studsubj.schemeitem.subject.base,
                                                                    tobedeleted=False,
                                                                    deleted=False
                                                                )
                                                                if cur_studsubj:

                                                                    if logging_on:
                                                                        logger.debug('    cur_studsubj: ' + str(cur_studsubj))
                                                                        logger.debug('    cur_studsubj: ' + str(cur_studsubj.schemeitem.subject.base.code))
                                                                        logger.debug('    cur_studsubj pok_validthru: ' + str(cur_studsubj.pok_validthru))
                                                                        logger.debug('    cur_studsubj pok_final: ' + str(cur_studsubj.pok_final))

                                                                        logger.debug('    cur_studsubj pk: ' + str(cur_studsubj.pk))

                                                                    grade_logtxt = ''.join((c.STRING_SPACE_10,
                                                                                            (subj_code + c.STRING_SPACE_10)[:8],
                                                                                            's: ', (pok_sesr + c.STRING_SPACE_05)[:5],
                                                                                            'c: ', (pok_pece + c.STRING_SPACE_05)[:5],
                                                                                            'e: ', (pok_final + c.STRING_SPACE_05)[:5]
                                                                                            ))

                                                # check if cur_studsubj has already an exemption grade
                                                                    cur_exem_grade = stud_mod.Grade.objects.filter(
                                                                        studentsubject=cur_studsubj,
                                                                        examperiod=c.EXAMPERIOD_EXEMPTION
                                                                    ).order_by('pk').first()

                                                                    if cur_exem_grade is None:

                                                                        if logging_on:
                                                                            logger.debug('    cur_exem_grade is None')
                                                                        cur_exem_grade = stud_mod.Grade(
                                                                            studentsubject=cur_studsubj,
                                                                            examperiod=c.EXAMPERIOD_EXEMPTION,
                                                                            segrade=other_studsubj.pok_sesr,
                                                                            cegrade=other_studsubj.pok_pece,
                                                                            finalgrade=other_studsubj.pok_final,
                                                                            exemption_imported=True  # PR2023-01-24 added to skip approval
                                                                        )
                                                                        cur_exem_grade.save(request=request)

                                                                        append_dict[cur_exem_grade.pk] = {'created': True}

                                                                        if cur_exem_grade.pk not in updated_grade_pk_list:
                                                                            updated_grade_pk_list.append(cur_exem_grade.pk)

                                                                        grade_logtxt += ''.join((' (', str(_('added')), ')'))

                                                                    else:
                                                                        # check if exemption is alreay submitted
                                                                        if cur_exem_grade.se_published or cur_exem_grade.ce_published:
                                                                            grade_logtxt = ''.join((c.STRING_SPACE_10,
                                                                                                            (subj_code + c.STRING_SPACE_10)[:8],
                                                                                                str(_('is already submitted'))
                                                                                                ))
                                                                        elif other_studsubj.pok_sesr != cur_exem_grade.segrade or \
                                                                            other_studsubj.pok_pece != cur_exem_grade.cegrade or \
                                                                            other_studsubj.pok_final != cur_exem_grade.finalgrade or \
                                                                                cur_exem_grade.tobedeleted or \
                                                                                cur_exem_grade.deleted:

                                                                            if cur_exem_grade.tobedeleted or cur_exem_grade.deleted:

                                                                                if logging_on:
                                                                                    logger.debug('    cur_exem_grade is deleted')
                                                                                setattr(cur_exem_grade, 'tobedeleted', False)
                                                                                setattr(cur_exem_grade, 'deleted', False)

                                                                                grade_logtxt += ''.join((' (', str(_('was deleted')), ')'))

                                                                                append_dict[cur_exem_grade.pk] = {'created': True}
                                                                                if logging_on:
                                                                                    logger.debug('    append_dict: ' + str(append_dict))
                                                                            else:
                                                                                cur_sesr = cur_exem_grade.segrade.replace(
                                                                                    '.',
                                                                                    ',') if cur_exem_grade.segrade else '-'
                                                                                cur_pece = cur_exem_grade.cegrade.replace(
                                                                                    '.',
                                                                                    ',') if cur_exem_grade.cegrade else '-'
                                                                                cur_finalgrade = cur_exem_grade.finalgrade.replace(
                                                                                    '.',
                                                                                    ',') if cur_exem_grade.finalgrade else '-'

                                                                                grade_logtxt += ''.join(
                                                                                    (' (', str(_('was')),
                                                                                     ': s: ', cur_sesr,
                                                                                     ' c: ', cur_pece,
                                                                                     ' e: ', cur_finalgrade,
                                                                                     ')'))
                                                                            setattr(cur_exem_grade, 'segrade', other_studsubj.pok_sesr)
                                                                            setattr(cur_exem_grade, 'cegrade', other_studsubj.pok_pece)
                                                                            setattr(cur_exem_grade, 'finalgrade', other_studsubj.pok_final)

                                                                            setattr(cur_exem_grade, 'exemption_imported', True) # PR2023-01-24 added to skip approval

                                                                            for examtype in ('se', 'ce'):
                                                                                setattr(cur_exem_grade, examtype + '_blocked', False)
                                                                                setattr(cur_exem_grade, examtype + '_published_id', None)
                                                                                setattr(cur_exem_grade, examtype + '_auth1by_id', None)
                                                                                setattr(cur_exem_grade, examtype + '_auth2by_id', None)

                                                                            cur_exem_grade.save(request=request)

                                                                            if cur_exem_grade.pk not in updated_grade_pk_list:
                                                                                updated_grade_pk_list.append(
                                                                                    cur_exem_grade.pk)

                                                                        else:
                                                                            grade_logtxt += ''.join((' (', str(_('is already entered')), ')'))

                                                                    log_list.append(grade_logtxt)

                                                                    if logging_on:
                                                                        logger.debug(' +++cur_segrade: ' + str(cur_exem_grade.segrade))
                                                                        logger.debug('    cur_cegrade: ' + str(cur_exem_grade.cegrade))
                                                                        logger.debug('    cur_exem_grade: ' + str(cur_exem_grade.finalgrade))

                                                                    setattr(cur_studsubj, 'exemption_year', other_examyear_code)
                                                                    setattr(cur_studsubj, 'has_exemption', True)
                                                                    cur_studsubj.save(request=request)

                                                                    if logging_on:
                                                                        logger.debug('    cur_studsubj.has_exemption: ' + str(cur_studsubj.has_exemption))

                    # ++++++ end of loop through other_students

                # has failed?  - is inlcuded in query

                                if logging_on:
                                    logger.debug('  XXXXXXXXXXXX   append_dict: ' + str(append_dict))

                # enter exemptions
                                grade_rows = grd_view.create_grade_rows(
                                    sel_examyear_pk=sel_examyear.pk,
                                    sel_schoolbase_pk=sel_school.base_id,
                                    sel_depbase_pk=sel_department.base_id,
                                    sel_lvlbase_pk=None,
                                    sel_examperiod=c.EXAMPERIOD_EXEMPTION,
                                    request=request,
                                    append_dict=append_dict,
                                    grade_pk_list=updated_grade_pk_list,
                                    remove_note_status=True
                                )
                                if grade_rows:
                                    update_wrap['updated_grade_rows'] = grade_rows

                    except Exception as e:
                        logger.error(getattr(e, 'message', str(e)))

        update_wrap['log_list'] = log_list

        if len(messages):
            update_wrap['messages'] = messages
            # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

# end of StudentEnterExemptionsView


def set_student_bisexam_and_exemptions(cur_student, other_stud_pk_str, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ============= set_student_bisexam_and_exemptions ============= ')
        logger.debug('cur_student.iseveningstudent: ' + str(cur_student.iseveningstudent))
        logger.debug('cur_student.islexstudent: ' + str(cur_student.islexstudent))


    if cur_student and other_stud_pk_str:

        cur_stud_does_partialexam = cur_student.partial_exam
        # is cur_student an evening or lex student?
        cur_stud_is_evelexstudent = cur_student.iseveningstudent or cur_student.islexstudent
        cur_stud_is_bisexam = cur_student.bis_exam

        cur_examyear_code = cur_student.school.examyear.code

        try:

            if cur_stud_does_partialexam:
                # don't add exemptions when student does partial exam
                pass
            else:

# is cur_student an evening or lex student?
# - get other_student
                other_student = stud_mod.Student.objects.get_or_none(
                   pk=int(other_stud_pk_str)
                )
                if other_student:
                    other_examyear_code = other_student.school.examyear.code

                    other_examyear_ok = False

                    if cur_stud_is_evelexstudent:
                    # other_examyear_code must be max ten year less than current examyear
                        if other_examyear_code <= cur_examyear_code - 1 and \
                            other_examyear_code >= cur_examyear_code - 10:
                                other_examyear_ok = True
                    else:
                    # other_examyear_code must be one year less than current examyear
                        if other_examyear_code == cur_examyear_code - 1:
                            other_examyear_ok = True

                    if other_examyear_ok:
                        # set student as bis_exam - not when evelex student
                        if not cur_stud_is_evelexstudent:
                            cur_student.bis_exam = True
                            cur_student.save(request=request)

                        # get list of pok (proof of knowledge)


# is cur_student an evening or lex student?

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))


# end of set_student_bisexam_and_exemptions

def make_student_biscandidate(cur_student, other_student, request):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ============= make_student_biscandidate ============= ')
        logger.debug('cur_student.iseveningstudent: ' + str(cur_student.iseveningstudent))
        logger.debug('cur_student.islexstudent: ' + str(cur_student.islexstudent))

    # TODO how to deal with evening school
    if not cur_student.iseveningstudent and not cur_student.islexstudent:
        try:
            is_biscand = False
            other_student_examyear_int = other_student.school.examyear.code
        # not in chceklist: student can only be biscandidate when he has failed
        # - student can not be biscandidate when he is withdrawn
            if logging_on:
                logger.debug('other_student.withdrawn: ' + str(other_student.withdrawn))
            if not other_student.withdrawn:
        # - student can only be biscandidate when other_student is from previous year
                if logging_on:
                    logger.debug('cur_student.school.examyear.code: ' + str(cur_student.school.examyear.code))
                    logger.debug('other_student_examyear_int: ' + str(other_student_examyear_int))
                if cur_student.school.examyear.code == other_student_examyear_int + 1:
        # - student can only be biscandidate when the depbases are the same
                    if logging_on:
                        logger.debug('cur_student.department.base_id: ' + str(cur_student.department.base_id))
                        logger.debug('other_student.department.base_id: ' + str(other_student.department.base_id))
                        logger.debug('cur_student.department.level_req: ' + str(cur_student.department.level_req))
                        #logger.debug('cur_student.level.base_id: ' + str(cur_student.level.base_id))
                        #logger.debug('other_student.level.base_id: ' + str(other_student.level.base_id))

                    if cur_student.department.base_id == other_student.department.base_id:

        # - student can only be biscandidate when the lvlbases are the same (only when not level_req)
                        if cur_student.department.level_req:
                            if cur_student.level and other_student.level and cur_student.level.base_id == other_student.level.base_id:
                                is_biscand = True
                        else:
                            is_biscand = True
            if logging_on:
                logger.debug('is_biscand: ' + str(is_biscand))
            if is_biscand:
                cur_student.bis_exam = True
                cur_student.save(request=request)

        # get proof of knowledge subjects from other_student
                other_studsubjects = stud_mod.Studentsubject.objects.filter(
                    student=other_student,
                    pok_validthru__isnull=False
                )
        # loop through list of proof of knowledge subjects of other_student
                for other_studsubj in other_studsubjects:
                    other_subjectbase = other_studsubj.schemeitem.subject.base
                    other_subjbase_code = other_studsubj.schemeitem.subject.base.code
                    if logging_on:
                        logger.debug('........................................')
                        logger.debug('other_subject.name_nl: ' + str(other_studsubj.schemeitem.subject.name_nl))
                        logger.debug('other_subjectbase.code: ' + str(other_subjbase_code))
                        logger.debug('other_subjectbase.pk: ' + str(other_subjectbase.pk))

        # lookup same subject in current student
                    cur_studsubj = stud_mod.Studentsubject.objects.get_or_none(
                        student=cur_student,
                        schemeitem__subject__base__code__iexact=other_subjbase_code
                    )
                    if cur_studsubj:
                        cur_subjbase_code = cur_studsubj.schemeitem.subject.base.code
                        if logging_on:
                            if logging_on:
                                logger.debug('cur_subject.name_nl: ' + str(cur_studsubj.schemeitem.subject.name_nl))
                                logger.debug('cur_subjbase_code: ' + str(cur_subjbase_code))
                                logger.debug('cur_subjectbase.pk: ' + str(cur_studsubj.schemeitem.subject.base.pk))

                        if other_subjbase_code.lower() == cur_subjbase_code.lower():
                            if logging_on:
                                logger.debug('>>>> other_subjbase_code.lower() == cur_subjbase_code.lower() ')

                    # create exemption grade if not yet exist
                            cur_exem_grade = stud_mod.Grade.objects.filter(
                                studentsubject=cur_studsubj,
                                examperiod=c.EXAMPERIOD_EXEMPTION
                            ).order_by('pk').first()
                            if logging_on:
                                logger.debug('cur_exem_grade ' + str(cur_exem_grade))

                            if cur_exem_grade is None:
                                cur_exem_grade = stud_mod.Grade.objects.create(
                                    studentsubject=cur_studsubj,
                                    examperiod=c.EXAMPERIOD_EXEMPTION
                                )
                            if logging_on:
                                    logger.debug('cur_exem_grade.created ' + str(cur_exem_grade))
                            if cur_exem_grade:
                                setattr(cur_exem_grade, 'sesrgrade', other_studsubj.gradelist_sesrgrade)
                                setattr(cur_exem_grade, 'pecegrade', other_studsubj.gradelist_pecegrade)
                                setattr(cur_exem_grade, 'finalgrade', other_studsubj.gradelist_finalgrade)
                                cur_exem_grade.save(request=request)
                                if logging_on:
                                    logger.debug('cur_exem_grade.saved ' + str(cur_exem_grade))

            # set pok_validthru = examyear_int + 1
                            pok_validthru = other_student_examyear_int + 1
                            setattr(cur_studsubj, 'pok_validthru', pok_validthru)
                            cur_studsubj.save(request=request)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of make_student_biscandidate


@method_decorator([login_required], name='dispatch')
class StudentsubjectnoteDownloadView(View):  # PR2021-03-15

    def post(self, request):
        logger.debug(' ============= StudentsubjectnoteDownloadView ============= ')
        logger.debug('request.POST: ' + str(request.POST))
        datalists_json = '{}'
        if request.user and request.user.country and request.user.schoolbase:
            if 'upload' in request.POST and request.POST['upload']:
                upload_dict = json.loads(request.POST['upload'])
                datalists = {'studentsubjectnote_rows': create_studentsubjectnote_rows(upload_dict, request) }

                datalists_json = json.dumps(datalists, cls=af.LazyEncoder)

        return HttpResponse(datalists_json)


############################################################################
@method_decorator([login_required], name='dispatch')
class NoteAttachmentDownloadView(View): # PR2021-03-17

    def get(self, request, pk_int):
        logger.debug(' ============= NoteAttachmentDownloadView ============= ')
        logger.debug('pk_int: ' + str(pk_int))
        # download  file from server
        response = None

        if pk_int:
            attachment = stud_mod.Noteattachment.objects.get_or_none(pk=pk_int)
            logger.debug('attachment' + str(attachment))
            if attachment:
                file = attachment.file
                logger.debug('file: ' + str(file) + ' ' + str(type(file)))
                file_url = file.url
                logger.debug('file_url: ' + str(file_url) + ' ' + str(type(file_url)))


        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of DownloadPublishedFile


@method_decorator([login_required], name='dispatch')
class StudentsubjectValidateAllView(View):  # PR2021-07-24

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectValidateAllView ============= ')

        # function validates studentsubject records of all students of this dep PR2021-07-10

        update_wrap = {}

# - get permit - no permit necessary

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get upload_json from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            if logging_on:
                logger.debug('    upload_dict: ' + str(upload_dict))
                # upload_dict: {'studsubj_validate': {'get': True}}

# ----- get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, sel_level, may_editNIU, msg_listNIU = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(
                    request=request,
                    skip_same_school_clause=False
                )
            if logging_on:
                logger.debug('    sel_department: ' + str(sel_department))
                logger.debug('    sel_level: ' + str(sel_level))

# +++ validate subjects of all students of this dep, used to update studsubj table
            # TODO to speed up: get info in 1 request, no msg_text
            crit = Q(school=sel_school) & \
                   Q(department=sel_department) & \
                   Q(deleted=False)

            if sel_level:
                crit.add(Q(level=sel_level), crit.connector)

            students = stud_mod.Student.objects.filter(crit)
            if logging_on:
                logger.debug('    students: ' + str(students))

            if students:
                validate_studsubj_list = []
                for student in students:

                    if logging_on:
                        logger.debug('----student: ' + str(student))

                    # validate_studentsubjects_no_msg returns True when there is an error PR2022-08-25
                    no_error = not stud_val.validate_studentsubjects_no_msg(student, 'nl')

                    if (not student.subj_composition_checked) or \
                            (student.subj_composition_checked and student.subj_composition_ok != no_error):
                        setattr(student, 'subj_composition_checked', True)
                        setattr(student, 'subj_composition_ok', no_error)
                        # dont update modified by
                        student.save()
                        if logging_on:
                            logger.debug('  student.save  no_error: ' + str(no_error))

                    if not no_error:
                        if student.pk not in validate_studsubj_list:
                            validate_studsubj_list.append(student.pk)

                    if logging_on:
                        logger.debug('    no_error: ' + str(no_error))

                if validate_studsubj_list:
                    update_wrap['validate_studsubj_list'] = validate_studsubj_list
        if logging_on:
            logger.debug('    update_wrap: ' + str(update_wrap))
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentsubjectValidateAllView


@method_decorator([login_required], name='dispatch')
class StudentsubjectValidateTestView(View):

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectValidateTestView ============= ')

        # function validates studentsubject records after opening modal, subjects are in list PR2021-08-17 PR2021-08-31
        # Note: don't filter on allowed, it will skip not-allowed subjects and give incorrect validation

        update_wrap = {'is_test': True}

# - get permit - no permit necessary

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)

# ----- get selected examyear, school and department from usersettings
            # PR2022-12-23 debug: don't filter on allowed, it will skip not-allowed subjects and give incorrect validation
            sel_examyear, sel_school, sel_department, sel_level, may_editNIU, msg_listNIU = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(
                    request=request
                )

# +++ validate subjects of one student, used in modal
            student_pk = upload_dict .get('student_pk')
            studsubj_dictlist = upload_dict.get('studsubj_dictlist')

            if logging_on:
                logger.debug('    sel_examyear: ' + str(sel_examyear))
                logger.debug('    sel_school: ' + str(sel_school))
                logger.debug('    sel_department: ' + str(sel_department))
                logger.debug('    student_pk: ' + str(student_pk) + ' ' + str(type(student_pk)))
                logger.debug('    studsubj_dictlist: ' + str(studsubj_dictlist))
            """
            studsubj_dictlist: [
                {'tobecreated': True, 'tobedeleted': False, 'tobechanged': False, 'schemeitem_id': 20635, 'studsubj_id': None, 'subj_id': 2641, 'subj_code': 'ak', 'is_extra_counts': False, 'is_extra_nocount': False}, 
                {'tobecreated': True, 'tobedeleted': False, 'tobechanged': False, 'schemeitem_id': 20231, 'studsubj_id': None, 'subj_id': 2637, 'subj_code': 'sk', 'is_extra_counts': False, 'is_extra_nocount': False}, 
                {'tobecreated': True, 'tobedeleted': False, 'tobechanged': False, 'schemeitem_id': 20420, 'studsubj_id': None, 'subj_id': 2647, 'subj_code': 'asw', 'is_extra_counts': False, 'is_extra_nocount': False}, 
           
            """
            if student_pk:
                student = stud_mod.Student.objects.get_or_none(id=student_pk)
                if logging_on:
                    logger.debug('    sel_school.pk: ' + str(sel_school.pk))
                    logger.debug('    sel_department.pk: ' + str(sel_department.pk))
                    logger.debug('    student: ' + str(student))

                if student:
                    msg_html = stud_val.validate_studentsubjects_TEST(student, studsubj_dictlist, user_lang)
                    if msg_html:
                        update_wrap['studsubj_validate_html'] = msg_html
                        if logging_on:
                            logger.debug('msg_html' + str(msg_html))

        if logging_on:
            logger.debug('update_wrap' + str(update_wrap))
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

# - end of StudentsubjectValidateTestView

#####################################################################################

@method_decorator([login_required], name='dispatch')
class SendEmailVerifcodeView(View):  # PR2021-07-26 PR2022-04-18
    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= SendEmailVerifcodeView ============= ')

        update_wrap = {}

        class_str = 'border_bg_transparent'

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            if logging_on:
                logger.debug('    upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'table': 'grade', 'mode': 'submit_save', 'form': 'ex2', 'verificationcode': '', 'verificationkey': None, 'auth_index': 2, 'now_arr': [2022, 4, 18, 11, 21]}
            upload_dict: {'table': 'studsubj', 'form': 'ex4', 'examperiod': 2, 'now_arr': [2022, 5, 31, 7, 29], 'mode': 'request_verif'}
            upload_dict: {'table': 'grade', 'form': 'ex5', 'auth_index': 2, 'now_arr': [2022, 6, 12, 18, 51]}

            """
# - get permit
            has_permit = False
            req_usr = request.user
            mode = upload_dict.get('mode')
            table = upload_dict.get('table')
            form = upload_dict.get('form')

            if table == 'result':
                sel_page = 'page_result'
            elif table == 'grade':
                sel_page = 'page_grade'
            elif mode in ('publish_exam', 'submit_grade_exam'):
                sel_page = 'page_exams'
            else:
                sel_page ='page_studsubj'
            if logging_on:
                logger.debug('mode: ' + str(mode))
                logger.debug('sel_page: ' + str(sel_page))
            if req_usr and req_usr.country and req_usr.schoolbase:
                permit_list = acc_prm.get_permit_list(sel_page, req_usr)

                requsr_usergroup_list, allowed_sections_dictNIU, allowed_clusters_listNIU, sel_examyear_instanceNIU = acc_prm.get_allowedusergrouplist_allowedsectionsdict_allowedclusterlist(req_usr)

                if permit_list and requsr_usergroup_list:
                    if 'auth1' in requsr_usergroup_list or 'auth2' in requsr_usergroup_list:
                        if table == 'result':
                            has_permit = 'permit_submit_ex5' in permit_list
                        elif table == 'grade':
                            has_permit = 'permit_submit_grade' in permit_list
                        elif mode == 'publish_exam':
                            has_permit = 'permit_publish_exam' in permit_list
                        elif mode == 'submit_grade_exam':
                            has_permit = 'permit_submit_exam' in permit_list
                        else:
                            has_permit = 'permit_approve_subject' in permit_list

                if logging_on:
                    logger.debug('permit_list: ' + str(permit_list))

            if logging_on:
                logger.debug('    mode: ' + str(mode))
                logger.debug('    sel_page: ' + str(sel_page))
                logger.debug('    has_permit: ' + str(has_permit))

            if has_permit:
                if mode == 'publish_exam':
                    formname = 'ete_exam'
                    sel_school, sel_department = None, None
                    sel_examyear, msg_list = acc_view.get_selected_examyear_from_usersetting(request)
                elif mode == 'submit_grade_exam':
                    formname = 'grade_exam'
                    sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                        acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                else:
                    formname = upload_dict.get('form')
                    sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                        acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if not msg_list:
                    try:
            # create _verificationcode and key, store in usersetting, send key to client, set expiration to 30 minutes
                        verif_key, verif_code = af.create_verificationcode(formname, request)
                        update_wrap['verificationkey'] = verif_key


                        if logging_on:
                            logger.debug('    verif_key: ' + str(verif_key))
                            logger.debug('    verif_code: ' + str(verif_code))


                        subject = str(_('AWP-online verificationcode'))
                        from_email = 'AWP-online <noreply@awponline.net>'

                        if mode == 'publish_exam':
                            template_str = 'email_send_verifcode_exam.html'
                        elif mode == 'submit_grade_exam':
                            template_str = 'email_send_verifcode_grade_exam.html'
                        else:
                            template_str = 'send_verifcode_exform_email.html'

                        ex_form = ''
                        if form == 'ex1':
                            ex_form = _('Ex1 form')
                        elif form =='ex2':
                            ex_form = _('Ex2 form')
                        elif form =='ex2a':
                            ex_form = _('Ex2A form')
                        elif form =='ex4':
                            ex_form = _('Ex4 form')
                        elif form =='ex5':
                            ex_form = _('Ex5 form')
                        elif form =='ex4ep3':
                            ex_form = _('Ex4 form 3rd exam period')
                        message = render_to_string(template_str, {
                            'user': request.user,
                            'examyear': sel_examyear,
                            'school': sel_school,
                            'ex_form': ex_form,
                            'department': sel_department,
                            'verificationcode': verif_code
                        })
                        if logging_on:
                            logger.debug('message: ' + str(message))

                        # PR2018-04-25 arguments: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
                        mail_count = send_mail(subject, message, from_email, [req_usr.email], fail_silently=False)
                        if logging_on:
                            logger.debug('mail_count: ' + str(mail_count))

                        if not mail_count:
                            class_str = 'border_bg_invalid'
                            msg_list += ("<p class='pb-2'>",
                                               str(_('An error occurred')),
                                               str(_('The email has not been sent.')), '</p>')
                        else:
                            # - return message 'We have sent an email to user'
                            class_str = 'border_bg_transparent'
                            if mode == 'publish_exam':
                                msg_txt = str(_('Enter the verification code and click the ENTER key to publish the exams.'))
                            else:
                                msg_txt = str(_("Enter the verification code and click 'Submit Ex form' or the ENTER key to submit the Ex form."))

                            msg_list += ("<p class='pb-0'>",
                                         str(_("We have sent an email with a 6 digit verification code to the email address:")), '</p>',
                                         "<p class='px-4 py-0'>", req_usr.email, '</p>',
                                         "<p class='pb-2'>",
                                         msg_txt,
                                         '</p>')

                    except Exception as e:
                        class_str = 'border_bg_invalid'
                        msg_list += ("<p class='pb-2'>",
                                           str(_('An error occurred')),':<br><i>', str(e), '</i><br>',
                                            str(_('The email has not been sent.')),'</p>')

                if msg_list:
                    msg_wrap_start = ["<div class='p-2 ", class_str, "'>"]
                    msg_wrap_end = ['</p>']

                    msg_html = ''.join(msg_wrap_start + msg_list + msg_wrap_end)

                    # - add  msg_dict to update_wrap
                    update_wrap['approve_msg_html'] = msg_html

    # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

# - end of SendEmailVerifcodeView


#####################################################################################
@method_decorator([login_required], name='dispatch')
class StudentsubjectApproveOrSubmitEx1Ex4View(View):  # PR2021-07-26 PR2022-05-30 PR2023-01-10

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectApproveOrSubmitEx1Ex4View ============= ')

################################
        def get_studsubjects(sel_examperiod, sel_school, sel_department, sel_level, is_submit):
            if logging_on:
                logger.debug('    is_submit: ' + str(is_submit))
            # PR2023-02-12
            studsubject_rows = []

            if sel_examperiod == 2:
                auth_clause = "studsubj.reex_auth1by_id AS auth1by_id, studsubj.reex_auth2by_id AS auth2by_id, studsubj.reex_published_id AS published_id,"
            elif sel_examperiod == 3:
                auth_clause = "studsubj.reex3_auth1by_id AS auth1by_id, studsubj.reex3_auth2by_id AS auth2by_id, studsubj.reex3_published_id AS published_id,"
            else:
                auth_clause = "studsubj.subj_auth1by_id AS auth1by_id, studsubj.subj_auth2by_id AS auth2by_id, studsubj.subj_published_id AS published_id,"

            if (sel_examperiod and sel_school and sel_department):
                try:
                    sql_list = [
                        "SELECT stud.id AS stud_id, stud.idnumber AS idnr, stud.examnumber AS exnr, stud.gender,",
                        "stud.lastname AS ln, stud.firstname AS fn, stud.prefix AS pref, stud.classname AS class, ",
                        "stud.level_id, lvl.name AS lvl_name, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ",

                        "CASE WHEN stud.subj_composition_ok OR stud.subj_dispensation",
                        #PR2023-02-17 skip composition check when iseveningstudent, islexstudent or partial_exam
                        "OR stud.iseveningstudent OR stud.islexstudent OR stud.partial_exam",
                        "THEN FALSE ELSE TRUE END AS composition_error,",

                        "stud.regnumber AS regnr, stud.diplomanumber AS dipnr, stud.gradelistnumber AS glnr,",
                        "stud.iseveningstudent AS evest, stud.islexstudent AS lexst,",
                        "stud.bis_exam AS bisst, stud.partial_exam AS partst, stud.withdrawn AS wdr,",

                        "studsubj.id AS studsubj_id, studsubj.tobedeleted AS studsubj_tobedeleted,",

                        auth_clause,
                        "subj.id AS subj_id, subjbase.code AS subj_code",

                        "FROM students_studentsubject AS studsubj",
                        "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                        "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                        "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",

                        "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                        "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                        "WHERE school.id = " + str(sel_school.pk) + "::INT",
                        "AND dep.id = " + str(sel_department.pk) + "::INT",

                        "AND NOT stud.deleted AND NOT studsubj.deleted"
                        ]

                # filter reex subjects when ex4 or ex4ep3
                    if sel_examperiod == 2:
                        sql_list.append("AND stud.has_reex")
                    elif sel_examperiod == 3:
                        sql_list.append("AND stud.has_reex03")

        # - may also filter on level when submitting Ex form
                    # PR2023-02-12 request MPC: must be able to submit per level tkl / pkl/pbl

                    # PR2023-02-19 debug:  VWO didnt show records, because of filter sel_lvlbase_pk=5
                    # solved bij adding: if sel_department.level_req

                    if sel_department.level_req and sel_level:
                        sql_list.append(''.join(("AND (lvl.base_id = ", str(sel_level.base_id), "::INT)")))

        # - other filters are only allowed when approving, not when is_submit
                    if not is_submit:
                        # - get selected values from usersetting selected_dict
                        sel_sctbase_pk, sel_subject_pk, sel_cluster_pk = None, None, None
                        selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                        if selected_dict:
                            sel_sctbase_pk = selected_dict.get(c.KEY_SEL_SCTBASE_PK)
                            sel_subject_pk = selected_dict.get(c.KEY_SEL_SUBJECT_PK)
                            sel_cluster_pk = selected_dict.get(c.KEY_SEL_CLUSTER_PK)

                        if sel_sctbase_pk:
                            sql_list.append(''.join(("AND sct.base_id = ", str(sel_sctbase_pk), "::INT")))

            # - filter on selected subject, not when is_submit TODO to be changed to subjectbase
                        if sel_subject_pk:
                            sql_list.append(''.join(("AND subj.id = ", str(sel_subject_pk), "::INT")))

            # - filter on selected sel_cluster_pk, not when is_submit
                        if sel_cluster_pk and not is_submit:
                            sql_list.append(''.join(("AND (studsubj.cluster_id = ", str(sel_cluster_pk), "::INT)")))

        # - get allowed_sections_dict from request
                    userallowed_sections_dict = acc_prm.get_userallowed_sections_dict_from_request(request)
                    # allowed_sections_dict: {'2': {'1': {'4': [117, 114], '5': [], '-9': [118, 121]}}} <class 'dict'>

        # - filter on allowed depbases, levelbase, subjectbases, not when is_submit PR2023-02-18
                    #TODO when approve: filter on all allowed, when submit: only filter on allowed lvlbase
                    #dont filter on allowed subjects and allowed clusters, but do filter on allowed lvlbases'
                    userallowed_schoolbase_dict, userallowed_depbases_pk_arr = acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(userallowed_sections_dict, sel_school.base_id)
                    allowed_depbase_dict, allowed_lvlbase_pk_arr = acc_prm.get_userallowed_depbase_dict_lvlbases_pk_arr(userallowed_schoolbase_dict, sel_department.base_id)

                    allowed_lvlbase_clause = acc_prm.get_sqlclause_allowed_lvlbase_from_lvlbase_pk_arr(allowed_lvlbase_pk_arr)

                    if logging_on:
                        logger.debug('    allowed_sections_dict: ' + str(userallowed_sections_dict))
                        logger.debug('    userallowed_schoolbase_dict: ' + str(userallowed_schoolbase_dict))
                        logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict))
                        logger.debug('    allowed_lvlbase_pk_arr: ' + str(allowed_lvlbase_pk_arr))
                        logger.debug('    allowed_lvlbase_clause: ' + str(allowed_lvlbase_clause))

                    if allowed_lvlbase_clause:
                        sql_list.append(allowed_lvlbase_clause)

                    if logging_on and False:
                        for sql_txt in sql_list:
                            logger.debug('  > ' + str(sql_txt))

        # - don't filter on allowed clusters PR2023-02-18
                    # PR2022-04-20 tel Bruno New Song: chairperson is also examiner.
                    # must be able to approve all subjects as chairperson.
                    # therefore: don't filter on allowed clusters when requsr is chairperson or secretary

                    sql_list.append("ORDER BY stud.lastname, stud.firstname")

                    sql = ' '.join(sql_list)
                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                        studsubject_rows = af.dictfetchall(cursor)

                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

            return studsubject_rows

################################
# function sets auth and publish of studentsubject records of current department # PR2021-07-25
        update_wrap = {}
        requsr_auth = None
        msg_html = None

# - get permit
        # <PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated

        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = acc_prm.get_permit_list('page_studsubj', req_usr)
            if logging_on:
                logger.debug('    permit_list: ' + str(permit_list))

            if permit_list and 'permit_approve_subject' in permit_list:
                # msg_err is made on client side. Here: just skip if user has no or multiple functions

                # PR2023-02-12 was: requsr_usergroup_list, allowed_sections_dictNIU, allowed_clusters_list, sel_examyear_instance = acc_prm.get_allowedusergrouplist_allowedsectionsdict_allowedclusterlist(req_usr)
                userallowed_instance = acc_prm.get_userallowed_instance_from_user_instance(req_usr)
                requsr_usergroup_list = acc_prm.get_usergroup_list(userallowed_instance)
                if logging_on:
                    logger.debug('    requsr_usergroup_list: ' + str(requsr_usergroup_list))

                is_auth1 = (requsr_usergroup_list and 'auth1' in requsr_usergroup_list)
                is_auth2 = (requsr_usergroup_list and 'auth2' in requsr_usergroup_list)
                if is_auth1 + is_auth2 == 1:
                    if is_auth1:
                        requsr_auth = 'auth1'
                    elif is_auth2:
                        requsr_auth = 'auth2'
                if requsr_auth:
                    has_permit = True

            if logging_on:
                logger.debug('    has_permit approve_subject:  ' + str(has_permit))

        if not has_permit:
            msg_html = "<div class='p-2 border_bg_invalid'>" + str(_("You don't have permission to perform this action.")) + "</div>"

        else:

# -  get user_lang
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

# ----- get selected examyear, school and department from usersettings
                # may_edit = False when:
                # - examyear, schoolbase, school, depbase or department is None
                # - country, examyear or school is locked
                # - not requsr_same_school,
                # - not sel_examyear.published,
                # not af.is_allowed_depbase_requsr or not af.is_allowed_depbase_school,

                sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                # TODO: get sel_examperiod as part from get_selected_ey_school_dep_lvl_from_usersetting
                examperiod = upload_dict.get('examperiod')
                prefix = 'reex3_' if examperiod == 3 else 'reex_' if examperiod == 2 else 'subj_'
                form_name = 'ex4ep3' if examperiod == 3 else 'ex4' if examperiod == 2 else 'ex1'

                if examperiod not in (1, 2, 3):
                    msg_txt = str(_('The exam period is not valid.'))
                    msg_html = ''.join(("<div class='p-2 border_bg_invalid'>", msg_txt, "</div>"))
                    err_list.append(msg_html)

                if err_list:
                    msg_html = '<br>'.join(err_list)
                else:

    # - get selected mode. Modes are 'approve_test', 'approve_save', 'approve_reset', 'submit_test' 'submit_save'
                    mode = upload_dict.get('mode')
                    is_approve = True if mode in ('approve_test', 'approve_save', 'approve_reset') else False
                    is_submit = True if mode in ('submit_test', 'submit_save') else False
                    is_reset = True if mode == 'approve_reset' else False
                    is_test = True if mode in ('approve_test', 'submit_test') else False

                    if logging_on:
                        logger.debug('    upload_dict ' + str(upload_dict))
                        logger.debug('    mode:       ' + str(mode))
                        logger.debug('    examperiod: ' + str(examperiod))
                        logger.debug('    prefix:     ' + str(prefix))
                        logger.debug('    form_name:  ' + str(form_name))

# - when mode = submit_submit: check verificationcode.
                    verification_is_ok = True
                    if is_submit and not is_test:
                        upload_dict['form'] = form_name
                        verification_is_ok, verif_msg_html = af.check_verifcode_local(upload_dict, request)
                        if verif_msg_html:
                            msg_html = verif_msg_html
                        if verification_is_ok:
                            update_wrap['verification_is_ok'] = True

                    if logging_on:
                        logger.debug('    verif_is_ok: ' + str(verification_is_ok))
                        logger.debug('    msg_html:    ' + str(msg_html))

                    if verification_is_ok:
                        #sel_lvlbase_pk, sel_sctbase_pk, sel_subject_pk, sel_cluster_pk, sel_student_pk = None, None, None, None, None
                        # don't filter on sel_sctbase_pk, sel_subject_pk, sel_cluster_pk or allowed when is_submit
                        # PR2023-01-10 may filter on level, so MPC TKL can submit their own Ex1

                        if logging_on:
                            logger.debug('    is_approve: ' + str(is_approve))

# +++ get selected studsubj_rows
                        # PR2023-01-09 new approach:
                        # - include published studsubjects
                        # - include tobedeleted studsubjects
                        # when a subject is set 'tobedeleted', the published info is removed, to show up when submitted

            # when submit: don't filter on sector, subject or cluster
                        # PR2023-02-12 request MPC: must be able to submit per level tkl / pkl/pbl
                        # also filter on level when submitting Ex form

                        studsubjects = get_studsubjects(
                            sel_examperiod=examperiod,
                            sel_school=sel_school,
                            sel_department=sel_department,
                            sel_level=sel_level,
                            is_submit=is_submit
                        )
                        if logging_on:
                            logger.debug('    row_count:      ' + str(len(studsubjects)))

                        count_dict = {'count': 0,
                                      'student_count': 0,
                                      'student_committed_count': 0,
                                      'student_saved_count': 0,
                                      'already_published': 0,
                                      'double_approved': 0,
                                      'studsubj_tobedeleted': 0,
                                      'committed': 0,
                                      'saved': 0,
                                      'saved_error': 0,
                                      'reset': 0,
                                      'already_approved': 0,
                                      'auth_missing': 0
                                      #'test_is_ok': False
                                    }
                        if studsubjects:

# +++ create new published_instance. Only save it when it is not a test
                            # file_name will be added after creating Ex-form
                            published_instance = None
                            published_instance_pk = None
                            published_instance_filename = None
                            if is_submit and not is_test:
                                now_arr = upload_dict.get('now_arr')

                                published_instance = create_published_Ex1_Ex4_instance(
                                    sel_school=sel_school,
                                    sel_department=sel_department,
                                    sel_level=sel_level,
                                    examperiod=examperiod,
                                    now_arr=now_arr,
                                    request=request)
                                if published_instance:
                                    published_instance_pk = published_instance.pk
                                    published_instance_filename = published_instance.filename

                            if logging_on:
                                logger.debug('    published_instance_pk: ' + str(published_instance_pk))
                                logger.debug('    published_instance_filename: ' + str(published_instance_filename))

                            studsubj_rows = []

                            row_count = 0
                            student_pk_list, student_committed_list, student_saved_list, student_saved_error_list = \
                                [],[], [], []
                            student_composition_error_list = []
                            student_composition_error_namelist = []

                            # PR2022-12-30 instead of updating each studsubj instance separately, create list of tobesaved studsubj_pk
                            # and batch update at the end
                            tobesaved_studsubj_pk_list = []

                            # PR2023-01-12 create list of tobedeleted student_pk and batch delete at the end
                            tobedeleted_student_pk_list = []

# +++++ loop through studsubjects +++++
                            for studsubj in studsubjects:

                                if logging_on and False:
                                    logger.debug('............ ')
                                    logger.debug('   ' + str(studsubj))

                                row_count += 1

                                is_committed = False
                                is_saved = False

                                if is_approve:
                                    is_committed, is_saved = approve_studsubj(
                                        studsubj=studsubj,
                                        requsr_auth=requsr_auth,
                                        prefix=prefix,
                                        is_test=is_test,
                                        is_reset=is_reset,
                                        count_dict=count_dict,
                                        request=request
                                    )

                                elif is_submit:
                                    is_committed, is_saved = submit_studsubj(
                                        studsubj=studsubj,
                                        prefix=prefix,
                                        is_test=is_test,
                                        count_dict=count_dict
                                    )

                                if is_saved:
                                    studsubj_pk = studsubj.get('studsubj_id')
                                    if studsubj_pk:
                                        tobesaved_studsubj_pk_list.append(studsubj_pk)

    # - add student_pk to student_pk_list, student_committed_list or student_saved_list
                                # this is used to count the students in msg: '4 students with 39 subjects are added'
                                # after the loop the totals are added to count_dict['student_count'] etc
                                # PR2022-08-25 submit not allowed when subject composition not coorect and no dispensation
                                student_pk = studsubj.get('stud_id')
                                if logging_on and False:
                                    logger.debug('    student_pk: ' + str(student_pk))

                                if student_pk not in student_composition_error_list:
                                    if studsubj.get('composition_error'):
                                        student_composition_error_list.append(student_pk)
                                        student_composition_error_namelist.append(', '.join((studsubj.get('ln', '-'), studsubj.get('fn', '-'))))

                                if student_pk not in student_pk_list:
                                    student_pk_list.append(student_pk)

                                    #if studsubj.student.tobedeleted and student_pk not in tobedeleted_student_pk_list:
                                    if studsubj.get('studsubj_tobedeleted') and student_pk not in tobedeleted_student_pk_list:
                                        tobedeleted_student_pk_list.append(student_pk)

                                if is_committed:
                                    if student_pk not in student_committed_list:
                                        student_committed_list.append(student_pk)
                                if is_saved:
                                    if student_pk not in student_saved_list:
                                        student_saved_list.append(student_pk)

# +++++  end of loop through  studsubjects

                            if logging_on:
                                logger.debug('    tobesaved_studsubj_pk_list: ' + str(tobesaved_studsubj_pk_list))

                            auth_missing_count = count_dict.get('auth_missing', 0)
                            double_approved_count = count_dict.get('double_approved', 0)

                            student_composition_error_count = len(student_composition_error_list)

                            student_committed_count = len(student_committed_list)

                            test_has_failed = False
                            if not row_count:
                                test_has_failed = True

                            elif is_submit and auth_missing_count:
                                test_has_failed = True
                            elif is_submit and double_approved_count:
                                test_has_failed = True

                            elif is_submit and student_composition_error_count:
                                test_has_failed = True

                            elif not student_committed_count:
                                test_has_failed = True

                            count_dict['count'] = row_count
                            count_dict['student_count'] = len(student_pk_list)
                            count_dict['student_composition_error_count'] = student_composition_error_count
                            count_dict['student_committed_count'] = student_committed_count
                            count_dict['student_saved_count'] = len(student_saved_list)

                            if logging_on:
                                logger.debug('    count_dict: ' + str(count_dict))

                            update_wrap['approve_count_dict'] = count_dict

    # - create msg_html with info of rows
                            msg_html = self.create_ex1_ex4_msg_list(
                                sel_department=sel_department,
                                sel_level=sel_level,
                                count_dict=count_dict,
                                requsr_auth=requsr_auth,
                                is_approve=is_approve,
                                is_test=is_test,
                                examperiod=examperiod,
                                published_instance_filename=published_instance_filename,
                                student_composition_error_namelist=student_composition_error_namelist
                            )

# +++++ create Ex1 Ex4 form
                            if row_count:
                                saved_studsubj_pk_list = []
                                if not is_test:
                                    if is_submit:
                                        self.create_ex1_ex4_form(
                                            published_instance=published_instance,
                                            sel_examyear=sel_examyear,
                                            sel_school=sel_school,
                                            sel_department=sel_department,
                                            sel_level=sel_level,
                                            examperiod=examperiod,
                                            prefix=prefix,
                                            save_to_disk=True,
                                            request=request,
                                            user_lang=user_lang
                                        )

# +++++ batch save approval / published PR2023-01-10
                                    if logging_on:
                                        logger.debug('    tobesaved_studsubj_pk_list: ' + str(tobesaved_studsubj_pk_list))

                                    if tobesaved_studsubj_pk_list:
                                        err_html = None
                                        if is_approve:
                                            saved_studsubj_pk_list, err_html = self.save_approved_in_studsubj(tobesaved_studsubj_pk_list, is_reset, 'subj_', requsr_auth, request.user)
                                        elif is_submit:
                                            saved_studsubj_pk_list, err_html = self.save_published_in_studsubj(tobesaved_studsubj_pk_list, 'subj_', published_instance.pk)

                                        if err_html:
                                            msg_html = "<div class='p-2 border_bg_invalid'>" + err_html + "</div>"

                                        if logging_on:
                                            logger.debug('    saved_studsubj_pk_list: ' + str(saved_studsubj_pk_list))

                                    if is_submit and tobedeleted_student_pk_list:
                                        self.set_student_deleted(tobedeleted_student_pk_list, request)

                                # - delete the 'tobedeleted' rows from StudSubject, only after submitting and no test!

                                    # PR2022-12-30 instead of updating each studsubj instance separately, create list of tobesaved studsubj_pk
                                    # list is created outside this function, when is_saved = True

                                # TODO put back 'tobedeleted' functions
                                    #self.delete_tobedeleted_from_studsubj(
                                    #    published_instance=published_instance,
                                    #    sel_examyear=sel_examyear,
                                    #    sel_school=sel_school,
                                    #    sel_department=sel_department,
                                    #    request=request
                                    #)

                                if logging_on:
                                    logger.debug('    saved_studsubj_pk_list: ' + str(saved_studsubj_pk_list))

            # - add rows to studsubj_rows, to be sent back to page
                                # to increase speed, dont create return rows but refresh page after finishing this request
                                if saved_studsubj_pk_list:
                                    studsubj_rows = create_studentsubject_rows(
                                        sel_examyear=sel_examyear,
                                        sel_schoolbase=sel_school.base if sel_school else None,
                                        sel_depbase=sel_department.base if sel_department else None,
                                        append_dict={},
                                        request=request,
                                        requsr_same_school=True, # when requsr_same_school=True, it includes students without studsubjects
                                        studsubj_pk_list=saved_studsubj_pk_list
                                    )

                                if logging_on:
                                    logger.debug('    studsubj_rows: ' + str(studsubj_rows))

                                if (studsubj_rows):
                                    update_wrap['updated_studsubj_approve_rows'] = studsubj_rows

                                if is_test:
                                    if not test_has_failed:
                                        update_wrap['test_is_ok'] = True

    # - add  msg_html to update_wrap (this one triggers MASS_UpdateFromResponse in page studsubjcts
        update_wrap['approve_msg_html'] = msg_html

     # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
    # - end of  StudentsubjectApproveOrSubmitEx1Ex4View.post

    def save_approved_in_studsubj(self, studsubj_pk_list, is_reset, prefix, requsr_auth, req_user):
        # PR2023-01-10

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug('----- save_approved_in_studsubj -----')

        saved_studsubj_pk_list = []
        err_html = None
        try:
            requsr_authby_field = ''.join((prefix, requsr_auth, 'by_id'))

            #   was: setattr(studsubj, requsr_authby_field, req_user)
            # - remove authby when is_reset
            requsr_authby_value = "NULL" if is_reset else str(req_user.pk)

            sql_keys = {'requsr_pk': req_user.pk, 'sb_arr': studsubj_pk_list}

            sql_list = ["UPDATE students_studentsubject AS studsubj ",
                        "SET", requsr_authby_field, "=", requsr_authby_value,
                        "WHERE studsubj.id IN (SELECT UNNEST(%(sb_arr)s::INT[]))",
                        "AND studsubj.deleted = FALSE",
                        "RETURNING id;"]

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('    sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)

                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        saved_studsubj_pk_list.append(row[0])

            if logging_on:
                logger.debug('    saved_studsubj_pk_list: ' + str(saved_studsubj_pk_list))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            err_html = ''.join((
                str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                str(_('The subjects could not be approved.'))
            ))

        if logging_on:
            logger.debug('    err_html: ' + str(err_html))

        return saved_studsubj_pk_list, err_html
# - end of save_approved_in_studsubj

    def set_student_deleted(self, student_pk_list, request):
        # PR2023-01-12

        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug('----- set_student_deleted -----')
            logger.debug('    student_pk_list: ' + str(student_pk_list))

        deleted_student_pk_list = []
        err_html = None

        try:

            modifiedby_pk_str = str(request.user.pk)
            modifiedat_str = str(timezone.now())

            sql_keys = {'st_arr': student_pk_list}

            sql_list = ["UPDATE students_student",
                "SET deleted = TRUE, tobedeleted=FALSE,",

                "modifiedby_id = ", modifiedby_pk_str, ", modifiedat = '", modifiedat_str, "'",
                "WHERE id IN (SELECT UNNEST(%(st_arr)s::INT[]))",

                "RETURNING id;"]

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        deleted_student_pk_list.append(row[0])

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            err_html = ''.join((
                str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                str(_('The subjects could not be approved.'))
            ))

        if logging_on:
            logger.debug('    deleted_student_pk_list: ' + str(deleted_student_pk_list))

        return deleted_student_pk_list, err_html
# - end of set_student_deleted

    def save_published_in_studsubj(self, studsubj_pk_list, prefix, published_pk):
        # PR2022-12-31 PR2023-01-10

        """
        # when is_approve:
        #   requsr_authby_field = prefix + requsr_auth + 'by'
        #   # PR2022-12-30 was: setattr(studsubj, requsr_authby_field, req_user)

        # submit:
            published = getattr(studsubj, prefix + 'published')
            put published_id in field subj_published:
        #    setattr(studsubj, prefix + 'published', published_instance)
        # -
        """

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug('----- save_published_in_studsubj -----')

        saved_studsubj_pk_list = []
        err_html = None

        try:
            published_field = prefix + 'published_id'
            sql_keys = {'publ_pk': published_pk, 'sb_arr': studsubj_pk_list}

            sql_list = ["UPDATE students_studentsubject AS studsubj",
                        "SET", published_field, "= %(publ_pk)s::INT,",
                        "deleted=tobedeleted, tobedeleted=FALSE, tobechanged=FALSE,",
                        "prev_auth1by_id=NULL, prev_auth2by_id=NULL, prev_published_id=NULL",
                        "WHERE studsubj.id IN (SELECT UNNEST(%(sb_arr)s::INT[]))",
                        "AND studsubj.deleted = FALSE",

                        "RETURNING id;"]

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        saved_studsubj_pk_list.append(row[0])

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            err_html = ''.join((
                str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                str(_('The subjects could not be approved.'))
            ))

        if logging_on:
            logger.debug('    saved_studsubj_pk_list: ' + str(saved_studsubj_pk_list))

        return saved_studsubj_pk_list, err_html
    # - end of save_published_in_studsubj

    def delete_tobedeleted_from_studsubj(self, published_instance, sel_examyear, sel_school, sel_department, request):
        # PR2021-09-30
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ----- delete_tobedeleted_from_studsubj -----')

        studentsubjects = stud_mod.Studentsubject.objects.filter(
            subj_published=published_instance,
            student__school__examyear=sel_examyear,
            student__school=sel_school,
            student__department=sel_department,
            tobedeleted=True
        )
        if logging_on:
            logger.debug('studentsubjects: ' + str(studentsubjects))

        if studentsubjects:
            for studsubj in studentsubjects:
                studsubj.delete(request=request)
                if logging_on:
                    logger.debug('deleted _studsubj: ' + str(studsubj))
# - end of  delete_tobedeleted_from_studsubj

    def create_ex1_ex4_msg_list(self, sel_department, sel_level, count_dict, requsr_auth, is_approve, is_test, examperiod, published_instance_filename, student_composition_error_namelist):
        # PR2022-08-25 PR2023-01-15
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ----- create_ex1_ex4_msg_list -----')
            logger.debug('    count_dict: ' + str(count_dict))
            logger.debug('    is_test: ' + str(is_test))

        count = count_dict.get('count', 0)
        student_count = count_dict.get('student_count', 0)
        committed = count_dict.get('committed', 0)
        student_committed_count = count_dict.get('student_committed_count', 0)
        saved = count_dict.get('saved', 0)
        saved_error = count_dict.get('saved_error', 0)
        student_saved_count = count_dict.get('student_saved_count', 0)
        student_saved_error_count = count_dict.get('student_saved_error_count', 0)
        already_published = count_dict.get('already_published', 0)

        all_published = count and already_published == count

        auth_missing = count_dict.get('auth_missing', 0)
        already_approved = count_dict.get('already_approved', 0)
        double_approved = count_dict.get('double_approved', 0)

        studsubj_tobedeleted = count_dict.get('studsubj_tobedeleted', 0)

        student_composition_error_count = count_dict.get('student_composition_error_count', 0)

        if logging_on:
            logger.debug('.....count: ' + str(count))
            logger.debug('.....committed: ' + str(committed))
            logger.debug('.....already_published: ' + str(already_published))
            logger.debug('.....auth_missing: ' + str(auth_missing))
            logger.debug('.....already_approved: ' + str(already_approved))
            logger.debug('.....double_approved: ' + str(double_approved))
            logger.debug('.....double_approved: ' + str(double_approved))
            logger.debug('.....student_composition_error_count: ' + str(student_composition_error_count))

        show_msg_first_approve_by_pres_secr = False

        if is_test:
            if is_approve:
                class_str = 'border_bg_valid' if committed else 'border_bg_invalid'
            else:
                if all_published:
                    class_str = 'border_bg_valid'
                elif student_composition_error_count:
                    class_str = 'border_bg_invalid'
                elif auth_missing or double_approved:
                    class_str = 'border_bg_invalid'
                elif committed:
                    class_str = 'border_bg_valid'
                else:
                    class_str = 'border_bg_invalid'
        else:
            if student_saved_error_count:
               class_str = 'border_bg_invalid'
            elif student_saved_count:
                class_str = 'border_bg_valid'
            else:
                class_str = 'border_bg_transpaprent'
        if logging_on:
            logger.debug('    class_str: ' + str(class_str))

        subjects_txt = _('subjects') if examperiod == 1 else _('re-examinations')
        form_txt = _('Ex1') if examperiod == 1 else _('Ex4')

        level_html = ''
        if sel_level:
            if sel_department.level_req and sel_level.abbrev:
                level_html = '<br>' + str(_('The selection contains only candidates of the learning path: %(lvl_abbrev)s.') % {'lvl_abbrev': sel_level.abbrev})

        tobedeleted_html = ''
        if studsubj_tobedeleted:
            tobedeleted_html = ' ' + str(_('%(subj)s marked to be deleted.') % {'subj': get_subjects_are_text(examperiod, studsubj_tobedeleted)})

# - create first line with 'The selection contains 4 candidates with 39 subjects'
        msg_list = ["<div class='p-2 ", class_str, "'>"]
        if is_test:
            msg_list.append(''.join(( "<p class='pb-2'>",
                        str(_("The selection contains %(stud)s with %(subj)s.") %
                            {'stud': get_student_count_text(student_count), 'subj': get_subject_count_text(examperiod, count)}), ' ',
                            tobedeleted_html,
                            level_html,
                        '</p>')))

# if students with errors in compositiosn: skip other msg
        try:
            composition_error_names_html = ''
            if student_composition_error_namelist:
                student_composition_error_namelist.sort()
                composition_error_names_html = ''.join((
                    "<ul class='my-0'><li>",
                    "</li><li>".join(student_composition_error_namelist),
                    "</li></ul>"
                ))

############## is_approve  #########################
            if is_approve:

    #++++++++++++++++ is_test +++++++++++++++++++++++++
                if is_test:

        # - if any subjects skipped: create lines 'The following subjects will be skipped' plus the reason
                    if committed == count:
                        msg_list.append("<p class='pb-0'>" + str(_("All %(cpt)s will be approved.") % {'cpt': subjects_txt}) + ':</p><ul>')
                    else:
                        willbe_or_are_txt = pgettext_lazy('plural', 'will be') if is_test else _('are')
                        msg_list.append("<p class='pb-0'>" + str(_("The following %(cpt)s %(willbe)s skipped")
                                                                 % {'cpt': subjects_txt, 'willbe': willbe_or_are_txt}) + \
                                        ":</p><ul class='my-0'>")
                        if already_published:
                            msg_list.append('<li>' + str(_("%(val)s already submitted") %
                                                         {'val': get_subjects_are_text(examperiod, already_published)}) + ';</li>')

                            if logging_on:
                                logger.debug('    already_published: ' + str(already_published))

                        if auth_missing:
                            msg_list.append('<li>' + str(_("%(subj)s not fully approved") %
                                                         {'subj': get_subjects_are_text(examperiod, auth_missing)}) + ';</li>')
                            show_msg_first_approve_by_pres_secr = True
                            if logging_on:
                                logger.debug('    auth_missing: ' + str(auth_missing))

                        if already_approved:
                            msg_list.append('<li>' + get_subjects_are_text(examperiod, already_approved) + str(_(' already approved')) + ';</li>')
                            if logging_on:
                                logger.debug('    already_approved: ' + str(already_approved))

                        if double_approved:
                            other_function =  str(_('chairperson')) if requsr_auth == 'auth2' else str(_('secretary'))
                            caption = _('subject') if examperiod == 1 else _('re-examination')
                            msg_list.append(''.join(('<li>', get_subjects_are_text(examperiod, double_approved),
                                                     str(_(' already approved by you as ')), other_function, '.<br>',
                                            str(_("You cannot approve a %(cpt)s both as chairperson and as secretary.") % {'cpt': caption} ), '</li>')))
                            if logging_on:
                                logger.debug('    double_approved: ' + str(double_approved))

                        msg_list.append('</ul>')

            # - line with text how many subjects will be approved / submitted
                        msg_list.append("<p class='pb-2'>")
                        if not committed:
                            msg_str = _("No %(cpt)s will be approved.") % {'cpt': subjects_txt}
                            if logging_on:
                                logger.debug('    is_approve not committed: ' + str(not committed))

                        else:
                            student_count_txt = get_student_count_text(student_committed_count)
                            subject_count_txt = get_subject_count_text(examperiod, committed)
                            will_be_text = get_will_be_text(committed)
                            msg_str = ' '.join((str(subject_count_txt), str(_('of')),  str(student_count_txt),
                                                str(will_be_text), str(_('approved.'))))
                            if logging_on:
                                logger.debug('    is_approve msg_str: ' + str(not msg_str))

                        msg_list.append(str(msg_str))
                        msg_list.append('</p>')

                # - add line 'both prseident and secretary must first approve all subjects before you can submit the Ex form
                        if show_msg_first_approve_by_pres_secr:
                            msg_txt = ''.join(('<div>', str(_('The chairperson and the secretary must approve all %(cpt)s before you can submit the %(frm)s form.') % {'cpt': subjects_txt, 'frm': form_txt}   ), '</div>'))
                            msg_list.append(msg_txt)

                        if student_composition_error_count:
                            is_are_str = str(_('is') if student_composition_error_count == 1 else _('are'))
                            candidates_cpt = str(_('candidate') if student_composition_error_count == 1 else _('candidates'))
                            msg_txt = ''.join(("<p class='pb-0'><b>", str(_("ATTENTION")), '</b>: ',
                                               str(_("There %(is_are)s %(count)s %(cand)s, ")
                                                   % {'count': student_composition_error_count, 'is_are': is_are_str, 'cand': candidates_cpt}),
                                               str(_(" whose subject composition is not correct.")),
                                               composition_error_names_html,
                                               "<p class='pb-0'>",
                                               str(_("Make the necessary corrections in the subject composition or contact the Inspectorate.")),
                                               "</p>"
                                               ))
                            msg_list.append(msg_txt)

                            if logging_on:
                                logger.debug('    msg_txt: ' + str(msg_txt))

    # ++++++++++++++++ not is_test +++++++++++++++++++++++++
                else:

                    # - line with text how many subjects have been approved
                    msg_list.append('<p>')

                    student_count_txt = get_student_count_text(student_saved_count)
                    subject_count_txt = get_subject_count_text(examperiod, saved)
                    student_saved_error_count_txt = get_student_count_text(student_saved_error_count)
                    subject_error_count_txt = get_subject_count_text(examperiod, saved_error)

                    if logging_on:
                        logger.debug('    not is_text: ' + str(not student_count_txt))

                    # - line with text how many subjects have been approved / submitted
                    if not saved and not saved_error:
                        msg_str = str(_("No subjects have been approved."))
                    else:
                        if saved:
                            have_has_been_txt = _('has been') if saved == 1 else _('have been')
                            msg_str = str(_("%(subj)s of %(stud)s %(havehasbeen)s approved.")
                                          % {'subj': subject_count_txt, 'stud': student_count_txt,
                                             'havehasbeen': have_has_been_txt})
                        else:
                            msg_str = str(_("No subjects have been approved."))
                        if saved_error:
                            if msg_str:
                                msg_str += '<br>'
                            could_txt = pgettext_lazy('singular', 'could') if saved_error == 1 else pgettext_lazy(
                                'plural', 'could')
                            msg_str += str(
                                _("%(subj)s of %(stud)s %(could)s not be approved because an error occurred.")
                                % {'subj': subject_error_count_txt, 'stud': student_saved_error_count_txt,
                                   'could': could_txt})

                    msg_list.append(str(msg_str))
                    msg_list.append('</p>')

############## is submit #########################
            else:
                if all_published :
                    msg_str = ''.join((
                        "<p class='pb-2'>",
                       str(_("All subjects are already submitted.")),
                       "</p>"
                    ))
                    msg_list.append(msg_str)

                elif student_composition_error_count:
                    is_are_str = str(_('is') if student_composition_error_count == 1 else _('are'))
                    candidates_cpt = str(_('candidate') if student_composition_error_count == 1 else _('candidates'))
                    msg_str = ''.join((
                        "<p class='pb-0'>",
                       str(_("The Ex1 form cannot be submitted because there %(is_are)s %(count)s %(cand)s, ")
                           % {'count': student_composition_error_count, 'is_are': is_are_str,
                              'cand': candidates_cpt}),
                       str(_(" whose subject composition is not correct.")),
                       composition_error_names_html,
                       "</p><p class='pb-2'>",
                       str(_("Make the necessary corrections in the subject composition or contact the Inspectorate.")),
                       "</p>"
                    ))

                    if logging_on:
                        logger.debug('   msg_str: ' + str(msg_str))
                    msg_list.append(msg_str)

                elif auth_missing or double_approved:
                    if auth_missing + double_approved == 1:
                        subjects_txt = str(_('There is 1 subject'))
                    else:
                        subjects_txt = str(_("There are %(count)s subjects") % {'count': auth_missing + double_approved})

                    approved_txt = ''
                    if auth_missing:
                        if double_approved:
                            approved_txt = str(_("that are not fully approved")), str(_(" or ")), str(_("that are double approved by the same person."))
                        else:
                            if auth_missing == 1:
                                approved_txt = str(_("that is not fully approved"))
                            else:
                                approved_txt = str(_("that are not fully approved"))
                    else:
                        if double_approved:
                            if double_approved == 1:
                                approved_txt = str(_("that is double approved by the same person"))
                            else:
                                approved_txt = str(_("that are double approved by the same person"))

                    msg_txt = ''.join((subjects_txt, ', ', approved_txt, "."))
                    if logging_on:
                        logger.debug('   msg_txt: ' + str(msg_txt))

                    msg_str = ''.join((
                        "<p class='pb-2'>",
                       str(_("The %(frm)s form can not be submitted.") % {'frm': form_txt}),
                        "<br>",
                        msg_txt,
                       "</p><p class='pb-2'>",
                        str(_('The chairperson and the secretary must approve all subjects before you can submit the Ex1 form.')),
                       "</p>"
                    ))

                    if logging_on:
                        logger.debug('   msg_str: ' + str(msg_str))
                    msg_list.append(msg_str)

                else:

                    if is_test and committed < count:

                        if already_published or committed:
                            msg_list.append('<ul>')

                        if already_published:
                            msg_list.append('<li>' + str(_("%(val)s already submitted") % {'val': get_subjects_are_text(examperiod, already_published)}) + ';</li>')

                        if committed:
                            msg_list.append('<li>' + str(_("%(val)s submitted") % {'val': get_subjects_willbe_text(examperiod, committed)}) + ';</li>')

                        if already_published or committed:
                            msg_list.append('</ul>')

                    # - line with text how many subjects will be approved / submitted
                    msg_list.append('<p>')
                    if is_test:
                        if not committed:
                            msg_str = ''.join((
                                '<p>',
                                str(_("The %(frm)s form can not be submitted.") % {'frm': form_txt}),
                                "</p><p>",
                                str(_('The chairperson and the secretary must approve all subjects before you can submit the Ex1 form.')),
                                "</p>"
                            ))
                            msg_list.append(msg_str)
                            if logging_on:
                                logger.debug('   msg_str: ' + str(msg_str))
                            if logging_on:
                                logger.debug('   not is_approve not committed: ' + str(not not committed))
                        else:
                            """
                            msg_list.append('<p>')

                            student_count_txt = get_student_count_text(student_committed_count)
                            subject_count_txt = get_subject_count_text(examperiod, committed)
                            will_be_text = get_will_be_text(committed)
                            approve_txt = _('added to the %(frm)s form.') % {'frm': form_txt}
                            msg_str = ' '.join((str(subject_count_txt), str(_('of')), str(student_count_txt),
                                                str(will_be_text), str(approve_txt)))

                            if logging_on:
                                logger.debug('    not is_approve msg_str: ' + str(not msg_str))

                            msg_list.append('</p>')
                            """
                    else:

                        msg_list.append("<p class='pb-2'>")
                        #student_count_txt = get_student_count_text(student_saved_count)
                        #subject_count_txt = get_subject_count_text(examperiod, saved)
                        #student_saved_error_count_txt = get_student_count_text(student_saved_error_count)
                        #subject_error_count_txt = get_subject_count_text(examperiod, saved_error)

                        # - line with text how many subjects have been approved / submitted

                        not_str = '' if saved else str(_('not')) + ' '
                        msg_str = str(_("The %(frm)s form has %(not)s been submitted.") % {'frm': form_txt, 'not': not_str})
                        if saved:
                            #student_count_txt = get_student_count_text(student_saved_count)
                            #subject_count_txt = get_subject_count_text(examperiod, saved)
                            file_name = published_instance_filename if published_instance_filename else '---'
                            msg_str += ''.join(('<br>',
                                                # PR2023-02-12 dont give number of subjects, because all subjects are added to the Ex form
                                                #str(_("It contains %(subj)s of %(stud)s.") % {'stud': student_count_txt,
                                                #                                              'subj': subject_count_txt}),
                                                #'<br>',
                                                str(_("The %(frm)s form has been saved as '%(val)s'.") % {'frm': form_txt,
                                                                                                          'val': file_name}),
                                                '<br>', str(_("Go to the page 'Archive' to download the file."))
                                                ))

                        msg_list.append(str(msg_str))
                        msg_list.append('</p>')

            if logging_on:
                logger.debug('   msg_list: ' + str(msg_list))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))


#######################################

        msg_list.append('</div>')


        if logging_on:
            logger.debug('   msg_list: ' + str(msg_list))

        msg_html = ''.join(msg_list)

        if logging_on:
            logger.debug('    msg_html: ' + str(msg_html))

        return msg_html
# - end of create_ex1_ex4_msg_list


    def create_ex1_ex4_form(self, published_instance, sel_examyear, sel_school, sel_department, sel_level,
                                    examperiod, prefix, save_to_disk, request, user_lang):
        #PR2021-07-27 PR2021-08-14
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= create_ex1_ex4_form ============= ')
            logger.debug('    examperiod: ' + str(examperiod))
            logger.debug('    sel_level: ' + str(sel_level))
            logger.debug('    save_to_disk: ' + str(save_to_disk))

# +++ create Ex1 xlsx file
        if examperiod == 1:

            # get text from examyearsetting
            settings = awpr_lib.get_library(sel_examyear, ['exform', 'ex1'])
            # if logging_on:
            #    logger.debug('settings: ' + str(settings))

            grd_exc.create_ex1_xlsx(
                published_instance=published_instance,
                examyear=sel_examyear,
                sel_school=sel_school,
                sel_department=sel_department,
                sel_level=sel_level,
                examperiod=examperiod,
                prefix=prefix,
                settings=settings,
                save_to_disk=save_to_disk,
                request=request,
                user_lang=user_lang)

        elif examperiod in (2, 3):
            grd_exc.create_ex4_xlsx(
                published_instance=published_instance,
                examyear=sel_examyear,
                sel_school=sel_school,
                sel_department=sel_department,
                sel_level=sel_level,
                examperiod=examperiod,
                prefix=prefix,
                save_to_disk=save_to_disk,
                request=request,
                user_lang=user_lang)

        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= end of create_ex1_ex4_form ============= ')
# --- end of create_ex1_ex4_form


#################################################################################
@method_decorator([login_required], name='dispatch')
class StudentsubjectApproveSingleView(View):  # PR2021-07-25 PR2023-02-18

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectApproveSingleView ============= ')

# function sets auth and publish of studentsubject records of current department # PR2021-07-25
        update_wrap = {}
        msg_list = []

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = acc_prm.get_permit_list('page_studsubj', req_usr)
            if permit_list:
                has_permit = 'permit_approve_subject' in permit_list

        if not has_permit:
            msg_list.append(str(_("You don't have permission to perform this action.")))
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('    upload_dict: ' + str(upload_dict))

# ----- get selected examyear, school and department from usersettings
                # may_edit = False when:
                # - examyear, schoolbase, school, depbase or department is None
                # - country, examyear or school is locked
                # - not requsr_same_school,
                # - not sel_examyear.published,
                # not af.is_allowed_depbase_requsr or not af.is_allowed_depbase_school,

                sel_examyear, sel_school, sel_department, sel_level, may_editNIU, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                if err_list:
                    msg_list.extend(err_list)
                else:

# check if studsubj is allowed PR2023-02-12
                    userallowed_instance = acc_prm.get_userallowed_instance_from_request(request)
                    if logging_on:
                        logger.debug('    userallowed_instance: ' + str(userallowed_instance))

                    userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
                    if logging_on:
                        logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))

                    userallowed_schoolbase_dict, userallowed_depbases_pk_arr = acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(userallowed_sections_dict, sel_school.base_id)
                    if logging_on:
                        logger.debug('    userallowed_schoolbase_dict: ' + str(userallowed_schoolbase_dict))
                        logger.debug('    userallowed_depbases_pk_arr: ' + str(userallowed_depbases_pk_arr))

                    userallowed_depbase_dict, userallowed_lvlbase_pk_arr = acc_prm.get_userallowed_depbase_dict_lvlbases_pk_arr(userallowed_schoolbase_dict, sel_department.base_id)
                    if logging_on:
                        logger.debug('    userallowed_depbase_dict: ' + str(userallowed_depbase_dict))
                        logger.debug('    userallowed_lvlbase_pk_arr: ' + str(userallowed_lvlbase_pk_arr))

                    sel_lvlbase_pk = sel_level.base_id if sel_level else None
                    userallowed_subjbase_pk_list = acc_prm.get_userallowed_subjbase_arr(userallowed_depbase_dict, sel_lvlbase_pk)

                    userallowed_cluster_pk_list = acc_prm.get_userallowed_cluster_pk_list(userallowed_instance)
                    if logging_on:
                        logger.debug('    userallowed_subjbase_pk_list: ' + str(userallowed_subjbase_pk_list))
                        logger.debug('    userallowed_cluster_pk_list: ' + str(userallowed_cluster_pk_list))

# - get list of studentsubjects from upload_dict
                    studsubj_list = upload_dict.get('studsubj_list')
                    #  'studsubj_list': [{'student_pk': 7959, 'studsubj_pk': 64174, 'subj_auth1by': True}]}
                    if studsubj_list:
                        studsubj_rows = []
# -------------------------------------------------
# - loop through list of uploaded studentsubjects
                        for studsubj_dict in studsubj_list:
                            student_pk = studsubj_dict.get('student_pk')
                            studsubj_pk = studsubj_dict.get('studsubj_pk')

                            append_dict = {}
                            error_dict = {}

# - get current student and studsubj
                            student = stud_mod.Student.objects.get_or_none(
                                id=student_pk,
                                department=sel_department
                            )
                            studsubj = stud_mod.Studentsubject.objects.get_or_none(
                                id=studsubj_pk,
                                student=student
                            )
                            if logging_on:
                                logger.debug('---------- ')
                                logger.debug('    student: ' + str(student))
                                logger.debug('    studsubj: ' + str(studsubj))

                            may_edit = False
                            if student and studsubj:

# +++ check if updating is allowed:
                                may_edit = True
                                if userallowed_cluster_pk_list:
                                    may_edit = False
                                    if studsubj.cluster_id and studsubj.cluster_id in userallowed_cluster_pk_list:
                                        may_edit = True
                                    else:
                                        msg_list.append(
                                            gettext("You don't have permission %(cpt)s.") % {'cpt': gettext('to approve subjects of this cluster')})

# +++ update studsubj
                            if may_edit:
                                si_pk = studsubj.schemeitem_id
                                schemeitems_dict = subj_vw.get_scheme_si_dict(sel_examyear.pk, sel_department.base_id, si_pk)
                                si_dict = schemeitems_dict.get(si_pk)

                                err_list, err_fields = [], []
                                update_studsubj(studsubj, studsubj_dict, si_dict,
                                                sel_examyear, sel_school, sel_department,
                                                err_list, err_fields, request)
                                if logging_on:
                                    logger.debug('>>>>> err_list: ' + str(err_list))
                                    logger.debug('>>>>> err_fields: ' + str(err_fields))

                                if err_list:
                                    msg_list.extend(err_list)
                                if err_fields:
                                    append_dict['err_fields'] = err_fields

                                # TODO check value of error_dict
                                # error_dict = {err_update: "Er is een fout opgetreden. De wijzigingen zijn niet opgeslagen."}
                                if error_dict:
                                    append_dict['error'] = error_dict
                                setting_dict = {
                                    'sel_examyear_pk': sel_school.examyear.pk,
                                    'sel_schoolbase_pk': sel_school.base_id,
                                    'sel_depbase_pk': sel_department.base_id
                                }

                                if logging_on:
                                    logger.debug('studsubj.pk: ' + str(studsubj.pk))
                                studsubj_pk_list = [studsubj.pk] if studsubj.pk else None

                                rows = create_studentsubject_rows(
                                    sel_examyear=sel_examyear,
                                    sel_schoolbase=sel_school.base if sel_school else None,
                                    sel_depbase=sel_department.base if sel_department else None,
                                    append_dict=append_dict,
                                    request=request,
                                    sel_lvlbase=sel_level.base if sel_level else None,
                                    requsr_same_school=True,  # check for same_school is included in may_edit
                                    student_pk=student.pk,
                                    studsubj_pk_list=studsubj_pk_list
                                )
                                if rows:
                                    studsubj_row = rows[0]
                                    if studsubj_row:
                                        studsubj_rows.append(studsubj_row)
# - end of loop
# -------------------------------------------------
                        if studsubj_rows:
                            update_wrap['updated_studsubj_approve_rows'] = studsubj_rows

        if logging_on:
            logger.debug('>>>>> msg_list: ')
            if msg_list:
                for msg in msg_list:
                    logger.debug('msg: ' + str(msg))
        if msg_list:
            messages = []
            msg_html = '<br>'.join(msg_list)
            messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentsubjectApproveSingleView
##################################################################################


def get_student_count_text(student_count):
    if not student_count:
        msg_text = str(_('no candidates'))
    elif student_count == 1:
        msg_text = str(_('1 candidate'))
    else:
        msg_text = ' '.join((str(student_count), str(_('candidates'))))
    return msg_text


def get_will_be_text(count):
    if count == 1:
        msg_text = pgettext_lazy('singular', 'will be')
    else:
        msg_text = pgettext_lazy('plural', 'will be')
    return msg_text


def get_subject_count_text(examperiod, count):
    if not count:
        msg_text = str(_('no subjects')) if examperiod == 1 else str(_('no re-examinations'))
    elif count == 1:
        msg_text = str(_('1 subject'))  if examperiod == 1 else str(_('1 re-examination'))
    else:
        subjects_txt = str(_('subjects')) if examperiod == 1 else str(_('re-examinations'))
        msg_text = ' '.join((str(count), subjects_txt))
    return msg_text


def get_subjects_are_text(examperiod, count):
    if not count:
        msg_text = str(_('no subjects are')) if examperiod == 1 else str(_('no re-examinations are'))
    elif count == 1:
        msg_text = str(_('1 subject is')) if examperiod == 1 else str(_('1 re-examination is'))
    else:
        subjects_txt = str(_('subjects are')) if examperiod == 1 else str(_('re-examinations are'))
        msg_text = ' '.join((str(count), subjects_txt))
    return msg_text


def get_subjects_willbe_text(examperiod, count):
    if not count:
        msg_text = str(_('no subjects will be')) if examperiod == 1 else str(_('no re-examinations will be'))
    elif count == 1:
        msg_text = str(_('1 subject will be')) if examperiod == 1 else str(_('1 re-examination will be'))
    else:
        subjects_txt = str(_('subjects will be')) if examperiod == 1 else str(_('re-examinations will be'))
        msg_text = ' '.join((str(count), subjects_txt))
    return msg_text


def approve_studsubj(studsubj, requsr_auth, prefix, is_test, is_reset, count_dict, request):
    # PR2021-07-26 PR2022-05-30 PR2022-12-30 PR2023-02-12
    # auth_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
    #  prefix = 'reex3_'  'reex_'  'subj_'

    # PR2022-12-30 instead of updating each studsubj instance separately, create list of tobesaved studsubj_pk
    # list is created outside this function, when is_saved = True

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- approve_studsubj -----')
        logger.debug('    requsr_auth:  ' + str(requsr_auth))
        logger.debug('    prefix:  ' + str(prefix))
        logger.debug('    is_reset:     ' + str(is_reset))
        logger.debug('    studsubj:     ' + str(studsubj))

    is_committed = False
    is_saved = False

    if studsubj:
        req_user = request.user

# - skip when this studsubj is already published
        # PR2023-02-12 was: published = getattr(studsubj, prefix + 'published')
        published = True if studsubj.get('published_id') else False
        if logging_on:
            logger.debug('    published:    ' + str(published))

        if studsubj.get('studsubj_tobedeleted'):
            af.add_one_to_count_dict(count_dict, 'studsubj_tobedeleted')

        if published:
            af.add_one_to_count_dict(count_dict, 'already_published')
        else:
            #requsr_authby_field = prefix + requsr_auth + 'by'
            requsr_authby_field = requsr_auth + 'by_id'

# - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved

            # PR2023-02-12 use sql instead of model:
            # field auth1by_id, auth2by_id, published_id contains the value are of
            #   - when axamperiod = 2: studsubj.reex_auth1by_id
            #   - when axamperiod = 3: studsubj.reex3_auth1by_id
            #   - else:                 studsubj.subj_auth1by_id

            #auth1by = getattr(studsubj, prefix +'auth1by')
            #auth2by = getattr(studsubj, prefix +'auth2by')
            auth1by_id = studsubj.get('auth1by_id')
            auth2by_id = studsubj.get('auth2by_id')
            if logging_on:
                logger.debug('    auth1by_id:      ' + str(auth1by_id))
                logger.debug('    auth2by_id:      ' + str(auth2by_id))

            save_changes = False

# - remove authby when is_reset
            if is_reset:
                # PR2022-12-30 was: setattr(studsubj, requsr_authby_field, None)
                af.add_one_to_count_dict(count_dict, 'reset')
                save_changes = True
            else:

# - skip if this studsubj is already approved
                # requsr_authby_value = getattr(studsubj, requsr_authby_field)
                requsr_authby_value = auth1by_id if requsr_auth == 'auth1' else auth2by_id if requsr_auth == 'auth2' else None
                requsr_authby_field_already_approved = True if requsr_authby_value else False
                if logging_on:
                    logger.debug('    requsr_authby_field_already_approved: ' + str(requsr_authby_field_already_approved))

                if requsr_authby_field_already_approved:
                    af.add_one_to_count_dict(count_dict, 'already_approved')
                else:

# - skip if this author (like 'chairperson') has already approved this studsubj
        # under a different permit (like 'secretary' or 'corrector')

                    if logging_on:
                        logger.debug('    > requsr_auth: ' + str(requsr_auth))
                        logger.debug('    > req_user:    ' + str(req_user))
                        logger.debug('    > auth1by_id:     ' + str(auth1by_id))
                        logger.debug('    > auth2by_id:     ' + str(auth2by_id))

                    double_approved = False
                    if requsr_auth == 'auth1':
                        double_approved = True if auth2by_id and auth2by_id == req_user.pk else False
                    elif requsr_auth == 'auth2':
                        double_approved = True if auth1by_id and auth1by_id == req_user.pk else False

                    if logging_on:
                        logger.debug('    double_approved: ' + str(double_approved))

                    if double_approved:
                        af.add_one_to_count_dict(count_dict, 'double_approved')
                    else:
                        # PR2022-12-30 was: setattr(studsubj, requsr_authby_field, req_user)
                        save_changes = True
                        if logging_on:
                            logger.debug('    save_changes: ' + str(save_changes))

# - set value of requsr_authby_field
            if save_changes:
                if is_test:
                    af.add_one_to_count_dict(count_dict, 'committed')
                    is_committed = True
                else:

# - save changes
                    af.add_one_to_count_dict(count_dict, 'saved')
                    is_saved = True

    return is_committed, is_saved
# - end of approve_studsubj


def submit_studsubj(studsubj, prefix, is_test, count_dict):
    # PR2021-01-21 PR2021-07-27 PR2022-05-30 PR2022-12-30 PR2023-02-12

    # PR2022-12-30 instead of updating each studsubj instance separately, create list of tobesaved studsubj_pk
    # list is created outside this function, when is_saved = True

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- submit_studsubj -----')
        logger.debug('     prefix: ' + str(prefix))

    is_committed = False
    is_saved = False

    if studsubj:

# - check if this studsubj is already published
        #published = getattr(studsubj, prefix + 'published')
        published = True if studsubj.get('published_id') else False
        if logging_on:
            logger.debug('     subj_published: ' + str(published))

        if studsubj.get('studsubj_tobedeleted'):
            af.add_one_to_count_dict(count_dict, 'studsubj_tobedeleted')

        if published:
            af.add_one_to_count_dict(count_dict, 'already_published')
        else:

# - check if this studsubj / examtype is approved by all auth
            #auth1by = getattr(studsubj, prefix + 'auth1by')
            #auth2by = getattr(studsubj, prefix + 'auth2by')

            auth1by_id = studsubj.get('auth1by_id')
            auth2by_id = studsubj.get('auth2by_id')
            auth_missing = auth1by_id is None or auth2by_id is None
            if logging_on:
                logger.debug('    auth1by_id:      ' + str(auth1by_id))
                logger.debug('    auth2by_id:      ' + str(auth2by_id))
                logger.debug('    auth_missing: ' + str(auth_missing))

            if auth_missing:
                af.add_one_to_count_dict(count_dict, 'auth_missing')
            else:
# - check if all auth are different
                double_approved = auth1by_id == auth2by_id
                if logging_on:
                    logger.debug('    double_approved: ' + str(double_approved))

                if double_approved and not auth_missing:
                    af.add_one_to_count_dict(count_dict, 'double_approved')
                else:
# - set value of published_instance and exatmtype_status field
                    if is_test:
                        af.add_one_to_count_dict(count_dict, 'committed')
                        is_committed = True
                    else:
                        af.add_one_to_count_dict(count_dict, 'saved')
                        is_saved = True

    return is_committed, is_saved
# - end of submit_studsubj


def create_published_Ex1_Ex4_instance(sel_school, sel_department, sel_level, examperiod, now_arr, request):
    # PR2021-07-27 PR2022-08-21
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_published_Ex1_Ex4_instance -----')
        logger.debug('     sel_school: ' + str(sel_school))
        logger.debug('     sel_department: ' + str(sel_department))
        logger.debug('     sel_level: ' + str(sel_level))
        logger.debug('     examperiod: ' + str(examperiod))
        logger.debug('     now_arr: ' + str(now_arr))
        logger.debug('     request.user: ' + str(request.user))

    # create new published_instance and save it when it is not a test (this function is only called when it is not a test)
    # filename is added after creating file in create_ex1_xlsx
    depbase_code = sel_department.base.code if sel_department.base.code else '-'
    school_code = sel_school.base.code if sel_school.base.code else '-'
    school_abbrev = sel_school.abbrev if sel_school.abbrev else '-'

    if sel_level and sel_department.level_req and sel_level.abbrev:
        depbase_code += ' ' + sel_level.abbrev

    if logging_on:
        logger.debug('     depbase_code:  ' + str(depbase_code))
        logger.debug('     school_code:   ' + str(school_code))
        logger.debug('     school_abbrev: ' + str(school_abbrev))

    # to be used when submitting Ex4 form
    examtype_caption = ''
    exform = 'Ex4 3e tijdvak' if examperiod == 3 else 'Ex4' if examperiod == 2 else 'Ex1' if examperiod == 1 else '-'
    examtype_caption = 'tv3' if examperiod == 3 else 'tv2' if examperiod == 2 else 'tv1' if examperiod == 1 else '-'

    if logging_on:
        logger.debug('     exform:       ' + str(exform))
        logger.debug('     examtype_cpt: ' + str(examtype_caption))

    today_date = af.get_date_from_arr(now_arr)
    if logging_on:
        logger.debug('     today_date: ' + str(today_date) + ' ' + str(type(today_date)))

    year_str = str(now_arr[0])
    month_str = ("00" + str(now_arr[1]))[-2:]
    date_str = ("00" + str(now_arr[2]))[-2:]
    hour_str = ("00" + str(now_arr[3]))[-2:]
    minute_str = ("00" +str( now_arr[4]))[-2:]
    now_formatted = ''.join([year_str, "-", month_str, "-", date_str, " ", hour_str, "u", minute_str])

    file_name = ' '.join((exform, school_code, school_abbrev, depbase_code, examtype_caption, now_formatted))
    # skip school_abbrev if total file_name is too long
    if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
        file_name = ' '.join((exform, school_code, depbase_code, examtype_caption, now_formatted))
    # if total file_name is still too long: cut off
    if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
        file_name = file_name[0:c.MAX_LENGTH_FIRSTLASTNAME]

    if logging_on:
        logger.debug('     file_name: ' + str(file_name))

    published_instance = None
    try:
        #sel_examtype = '-'
        published_instance = sch_mod.Published(
            school=sel_school,
            department=sel_department,
            #examtype=sel_examtype,
            examperiod=examperiod,
            name=file_name,
            datepublished=today_date
        )

        published_instance.filename = file_name + '.xlsx'

        published_instance.save(request=request)

        if logging_on:
            logger.debug('     published_instance.saved: ' + str(published_instance))
            logger.debug('     published_instance.pk: ' + str(published_instance.pk))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return published_instance
# - end of create_published_Ex1_Ex4_instance


#################################################################################

@method_decorator([login_required], name='dispatch')
class StudentsubjectValidateSchemeView(View):  # PR2021-08-28

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectValidateSchemeView ============= ')

        # function checks if schemeitem schemes are the same as the student scheme
        # can only be used by system.
        # Function is added to check and correct schemeitems, because of wrong schemeitems in SMAC students.
        # STiil don't know why those students got the wrong schemeitems
        update_wrap = {}

        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:

            # - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            correct_errors = False
            if upload_json:
                upload_dict = json.loads(upload_json)
                correct_errors = upload_dict.get('correct_errors', False)

            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

            stud_row_count, stud_row_error, student_rows = validate_students_scheme(sel_examyear, correct_errors, request)
            response_dict = {}
            response_dict['stud_row_count'] = stud_row_count
            response_dict['stud_row_error'] = stud_row_error
            response_dict['student_rows'] = student_rows

            studsubj_row_count, studsubj_row_error, studsubj_rows = validate_studsubj_scheme(sel_examyear, correct_errors, request)

            response_dict['studsubj_row_count'] = studsubj_row_count
            response_dict['studsubj_row_error'] = studsubj_row_error
            response_dict['studsubj_rows'] = studsubj_rows

            update_wrap['validate_scheme_response'] = response_dict


# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentsubjectValidateSchemeView


def validate_students_scheme(sel_examyear, correct_errors, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- validate_students_scheme ----- ')
        logger.debug('sel_examyear: ' + str(sel_examyear))
        logger.debug('correct_errors: ' + str(correct_errors))

    row_count, row_error, student_rows = 0, 0, []
    try:
        sql_keys = {'ey_id': sel_examyear.pk}

        sql_list = ["WITH sub_scheme AS (",
                    "SELECT scheme.id AS scheme_id,",
                    "dep.id AS scheme_dep_id, dep.base_id AS scheme_depbase_id,",
                    "lvl.id AS scheme_level_id, lvl.base_id AS scheme_lvlbase_id,",
                    "sct.id AS scheme_sector_id, sct.base_id AS scheme_sctbase_id",
                    "FROM subjects_scheme AS scheme",
                    "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                    "INNER JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
                    "INNER JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)"
            , ")",

                    "SELECT st.id AS student_id, st.lastname, st.firstname, st.school_id AS s_id,",
                    "sbase.code AS school_code, sch.name AS school_name, ",
                    "dep.id AS st_dep_id, dep.base_id AS st_depbase_id, ",
                    "lvl.id AS st_lvl_id, lvl.base_id AS st_lvlbase_id, ",
                    "sct.id AS st_sct_id, sct.base_id AS st_sctbase_id, ",
                    "st.scheme_id AS st_scheme_id, ",
                    "scheme_dep_id, scheme_depbase_id, ",
                    "scheme_dep_id, scheme_depbase_id, ",
                    "scheme_level_id, scheme_lvlbase_id, ",
                    "scheme_sector_id, scheme_sctbase_id ",

                    "FROM students_student AS st",
                    "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                    "INNER JOIN schools_schoolbase AS sbase ON (sbase.id = sch.base_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",

                    "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
                    "INNER JOIN schools_departmentbase AS db ON (db.id = dep.base_id)",
                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
                    "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
                    "LEFT JOIN sub_scheme ON (sub_scheme.scheme_id = st.scheme_id)",
                    "WHERE sch.examyear_id = %(ey_id)s::INT"]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)
            # logger.debug('connection.queries: ' + str(connection.queries))
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if rows:
        for row in rows:
            row_count += 1

            student_id = row.get('student_id')
            student = stud_mod.Student.objects.get_or_none(pk=student_id)
            if student:
                # get scheme, based on value of dep, sct and maybe lvl
                department = student.department
                level = student.level
                sector = student.sector
                student_scheme = student.scheme

                deplvlsct_scheme = None
                if department and sector:
                    if level is None:
                        deplvlsct_scheme = subj_mod.Scheme.objects.filter(
                            department=department,
                            level_id__isnull=True,
                            sector=sector,
                        ).order_by('pk').first()
                    else:
                        deplvlsct_scheme = subj_mod.Scheme.objects.filter(
                            department=department,
                            level_id=level,
                            sector=sector,
                        ).order_by('pk').first()

                err_txt = None
                if deplvlsct_scheme is None:
                    if student_scheme is not None:
                        err_txt = 'Student has scheme ' + str(student_scheme.name) + ', but deplvlsct_scheme not found'
                else:
                    if student_scheme is None:
                        err_txt = 'student_scheme is None, but  deplvlsct_scheme is: ' + str(deplvlsct_scheme.name)
                    elif student_scheme.pk != deplvlsct_scheme.pk:
                        err_txt = 'Student_scheme: ' + str(
                            student_scheme.name) + ' not equal to deplvlsct_scheme: ' + str(deplvlsct_scheme.name)
                if err_txt:
                    row_error += 1
                    if correct_errors:
                        setattr(student, 'scheme', deplvlsct_scheme)
                        student.save(request=request)

                    row_dict = {}
                    row_dict['STUDENT'] = str(student.fullname)
                    row_dict['SCHOOL'] = student.school.name
                    row_dict['ERROR'] = err_txt

                    student_rows.append(row_dict)

    if logging_on:
        logger.debug('row_count:   ' + str(row_count))
        logger.debug('row_error:   ' + str(row_error))
        logger.debug('student_rows: ' + str(student_rows))

    return row_count, row_error, student_rows
# - end of validate_students_scheme


def validate_studsubj_scheme(sel_examyear, correct_errors, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- validate_studsubj_scheme ----- ')
        logger.debug('sel_examyear: ' + str(sel_examyear))
        logger.debug('correct_errors: ' + str(correct_errors))

    row_count, row_error, studsubj_rows = 0, 0, []
    try:
        sql_keys = {'ey_id': sel_examyear.pk}

        sql_list = ["SELECT studsubj.id AS studsubj_id, st.id AS student_id, st.lastname, st.firstname, st.school_id AS s_id,",
                    "sbase.code AS school_code, sch.name AS school_name,",
                    "studsubj.schemeitem_id AS studsubj_si_id, ",
                    "st.scheme_id AS student_scheme_id,",
                    "si_scheme.id AS studsubj_scheme_id, si_scheme.name AS studsubj_scheme_name,",
                    "subjbase.code AS studsubj_subjbase_code",

                    "FROM students_studentsubject AS studsubj",
                    "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
                    "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                    "INNER JOIN schools_schoolbase AS sbase ON (sbase.id = sch.base_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                    "LEFT JOIN subjects_scheme AS stud_scheme ON (stud_scheme.id = st.scheme_id)",

                    "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                    "INNER JOIN subjects_scheme AS si_scheme ON (si_scheme.id = si.scheme_id)",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                    "WHERE sch.examyear_id = %(ey_id)s::INT"]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)
            # logger.debug('connection.queries: ' + str(connection.queries))
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if rows:
        for row in rows:
            row_count += 1
            student_scheme_id = row.get('student_scheme_id')
            studsubj_scheme_id = row.get('studsubj_scheme_id')

            if student_scheme_id and studsubj_scheme_id:
                if student_scheme_id != studsubj_scheme_id:
                    row_error += 1
                    row_dict = {}

                    studsubj_id = row.get('studsubj_id')
                    studsubj = stud_mod.Studentsubject.objects.get_or_none(pk=studsubj_id)

        # - get student
                    if studsubj:
                        student = studsubj.student
                        student_scheme = student.scheme
                        if student_scheme:

        # - first get subject and subjecttype from studsubj_schemeitem
                            current_schemeitem = studsubj.schemeitem
                            current_subject = current_schemeitem.subject
                            current_sjtype = current_schemeitem.subjecttype

                            row_dict['STUDENT'] = str(student.fullname)
                            row_dict['SCHOOL'] = student.school.name
                            row_dict['ERROR'] = 'student scheme is: ' + str(student_scheme.name) + ', studsubj scheme is: ' + str(
                                current_schemeitem.scheme.name)
                            row_dict['CURRENT'] = 'Subject: ' + str(current_subject.name_nl  ) + ', Subjecttype: ' + current_sjtype.abbrev

    # - check if student scheme also has schemeitems with same subject and subjecttype as studsubj_schemeitem
                            new_schemeitem = subj_mod.Schemeitem.objects.filter(
                                scheme=student_scheme,
                                subject=current_subject,
                                subjecttype__base=current_sjtype.base
                            ).order_by('pk').first()
    # - save new_schemeitem if student scheme also has schemeitems with same subject and subjecttype
                            if new_schemeitem:
                                row_dict['new_with_same_sjtype'] = 'subject: ' + str(new_schemeitem.subject.base.code) + ', Subjecttype: ' + new_schemeitem.subjecttype.abbrev
                                if correct_errors:
                                    setattr(studsubj, 'schemeitem', new_schemeitem)
                                    studsubj.save(request=request)
                            else:
    # - check if student scheme has schemeitems with same subject but differenet subjecttype
                                new_schemeitem = subj_mod.Schemeitem.objects.filter(
                                    scheme=student_scheme,
                                    subject=current_subject
                                ).order_by('subjecttype__base__sequence').first()
                                if new_schemeitem:
                                    row_dict['new_with_different_sjtype'] = 'Subject: ' + str(new_schemeitem.subject.base.code) + ', Subjecttype: ' + new_schemeitem.subjecttype.abbrev
                                    setattr(studsubj, 'schemeitem', new_schemeitem)
                                    if correct_errors:
                                        setattr(studsubj, 'schemeitem', new_schemeitem)
                                        studsubj.save(request=request)
                                else:
        # - delete studsubj if new scheme does not have this subject
                                    row_dict['not_in_new_scheme'] = 'Subject ' + str(current_subject.base.code) + ' will be deleted'
                                    if correct_errors:
                                        studsubj.delete(request=request)
                    studsubj_rows.append(row_dict)
    if logging_on:
        logger.debug('row_count:   ' + str(row_count))
        logger.debug('row_error:   ' + str(row_error))
        logger.debug('studsubj_rows: ' + str(studsubj_rows))

    return row_count, row_error, studsubj_rows
# - end of validate_studsubj_scheme
#################################################################################


@method_decorator([login_required], name='dispatch')
class StudentsubjectMultipleUploadView(View):  # PR2020-11-20 PR2021-08-17 PR2021-09-28 PR2022-08-30 PR2023-01-07

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectMultipleUploadView ============= ')

        # function creates, deletes and updates studentsubject records of current student PR2020-11-21
        update_wrap = {}
        messages = []

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = acc_prm.get_permit_list('page_studsubj', req_usr)
            if permit_list:
                has_permit = 'permit_crud' in permit_list
            if logging_on:
                logger.debug('    permit_list: ' + str(permit_list))

        if logging_on:
            logger.debug('    has_permit: ' + str(has_permit))
        if has_permit:

        # - check for double subjects, double subjects are not allowed -> happens in create_studsubj PR2021-07-11
        # - TODO when deleting: return warning when subject grades have values

    # - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

    # - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

    # - get selected examyear, school and department from usersettings
                # may_edit = False when:
                # - examyear, schoolbase, school, depbase or department is None
                # - country, examyear or school is locked
                # - not requsr_same_school,
                # - not sel_examyear.published,
                # not af.is_allowed_depbase_requsr or not af.is_allowed_depbase_school,

                sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if logging_on:
                    logger.debug('    upload_dict' + str(upload_dict))
                    logger.debug('    sel_examyear: ' + str(sel_examyear))
                    logger.debug('    sel_school: ' + str(sel_school))
                    logger.debug('    sel_department: ' + str(sel_department))

    # - get info from upload_dict
                # - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                student_instance = None

                if len(err_list):
                    msg_html = '<br>'.join(err_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                elif may_edit:
                    student_pk = upload_dict.get('student_pk')
                    student_instance = stud_mod.Student.objects.get_or_none(
                        id=student_pk,
                        school=sel_school,
                        department=sel_department
                    )
                if logging_on:
                    logger.debug('    student_instance: ' + str(student_instance))

# - get list of studentsubjects from upload_dict
                studsubj_list = None
                if student_instance:
                    studsubj_list = upload_dict.get('studsubj_list')

                if studsubj_list:

# - get schemitem_info of the scheme of this student, separately, instead of getting t for each subject, should be faster
                    schemeitems_dict = subj_vw.get_scheme_si_dict(sel_examyear.pk, sel_department.base_id, student_instance.scheme_id)

                    # PR2023-02-22 when studsubj is set to 'deleted' instead of 'tobedeleted' (happens when row is not piblished), iit is not included in updated rows.
                    # add it to list 'deleted_rows' and add it to updated_rows at the end.
                    # necessary to remove deleted row from studsubj table
                    deleted_rows = []
                    updated_rows = []
                    updated_rows_append_dict = {}
                    recalc_subj_composition = False

# -------------------------------------------------
# - loop through list of uploaded studentsubjects
                    for studsubj_dict in studsubj_list:
                        # values of mode are: 'delete', 'create', 'update'
                        mode = studsubj_dict.get('mode')
                        studsubj_pk = studsubj_dict.get('studsubj_pk')
                        schemeitem_pk = studsubj_dict.get('schemeitem_pk')

                        if logging_on:
                            logger.debug('---------- loop through list of uploaded studentsubjects ')
                            logger.debug('    mode: ' + str(mode))
                            logger.debug('    studsubj_dict:   ' + str(studsubj_dict))
                            logger.debug('    studsubj_pk:   ' + str(studsubj_pk))
                            logger.debug('    schemeitem_pk: ' + str(schemeitem_pk))

# - get current studsubj - when mode is 'create': studsubj is None. It will be created at "elif mode == 'create'"
                        studsubj = stud_mod.Studentsubject.objects.get_or_none(
                            id=studsubj_pk,
                            student=student_instance
                        )
                        if logging_on:
                            logger.debug('    studsubj: ' + str(studsubj))

                        append_dict = {}
                        deleted_rows = []
# +++ delete studsubj ++++++++++++
                        if mode == 'delete':
                            if studsubj:
                                deleted_row, tobedeleted_studsubj_pk, err_html = delete_studentsubject(
                                    student_instance=student_instance,
                                    studsubj_instance=studsubj,
                                    request=request
                                )
                                if err_html:
                                    messages.append(
                                        {'header': str(_('Delete subject')),
                                         'class': "border_bg_invalid",
                                         'msg_html': err_html}
                                    )

                                # - when studsubj is submitted, tobedeleted is set True, studsubj will be retrieved by updated_rows = create_studentsubject_rows
                                # the key 'tobedeleted' must be added via append_dict

                                elif tobedeleted_studsubj_pk:
                                    append_dict[tobedeleted_studsubj_pk] = {'tobedeleted': True}

                                    studsubj = None
                                    recalc_subj_composition = True

                                # - when studsubj is not yet submitted, deleted is set True, studsubj will NOT be retrieved by updated_rows = create_studentsubject_rows
                                # therefore a dict with the info af the deleted row must be added to updated_rows at the end, to remove the dict from the data_dicts and the tblrow

                                elif deleted_row:
                                    deleted_rows.append(deleted_row)

                                    studsubj = None
                                    recalc_subj_composition = True

                        # +++ create or restore new studentsubject, also create grade of first examperiod
                        elif mode == 'create':
                            schemeitem = subj_mod.Schemeitem.objects.get_or_none(id=schemeitem_pk)
                            error_list = []

                            studsubj, append_key = create_studsubj(student_instance, schemeitem, messages, error_list, request, False)  # False = don't skip_save

                            if logging_on:
                                logger.debug('    studsubj: ' + str(studsubj))
                                logger.debug('    append_key: ' + str(append_key))

                            if studsubj:
                                # PR2023-01-03 was: append_dict['created'] = True
                                #updated_studsubj_pk_list.append(studsubj.pk)
                                #if logging_on:
                                #    logger.debug('    updated_studsubj_pk_list: ' + str(updated_studsubj_pk_list))

                                recalc_subj_composition = True

                                if append_key:  # append_key = 'created' when new or 'updated' when 'restored'
                                    append_dict = {append_key: True}

                            elif error_list:
                                # TODO check if error is displayed correctly PR2021-07-21
                                # yes, but messages html is displayed in msg_box. This one not in use??
                                # PR2023-01-03 was: append_dict['err_create'] = ' '.join(error_list)
                                append_dict = {'err_create': ' '.join(error_list)}
                            if logging_on:
                                logger.debug('    schemeitem: ' + str(schemeitem))
                                logger.debug('    append_dict: ' + str(append_dict))

# +++ update existing studsubj - also when studsubj is created - studsubj is None when deleted
                        if studsubj and mode in ('create', 'update'):
                            si_pk = studsubj.schemeitem_id
                            si_dict = schemeitems_dict.get(si_pk)
                            err_fields = []

                            studsubj_pk_list, recalc_subj_comp = update_studsubj(studsubj, studsubj_dict, si_dict, sel_examyear, sel_school, sel_department, err_list, err_fields, request)
                            #if studsubj_pk_list:
                            #    for studsubj_pk in studsubj_pk_list:
                            #        if studsubj_pk not in updated_studsubj_pk_list:
                            #            updated_studsubj_pk_list.append(studsubj_pk)
                            if recalc_subj_comp:
                                recalc_subj_composition = True

                        if studsubj and append_dict:
                            updated_rows_append_dict[studsubj.pk] = append_dict
# - end of loop
# -------------------------------------------------
                    if recalc_subj_composition:
                        update_student_subj_composition(student_instance)

                    if len(err_list):
                        msg_html = '<br>'.join(err_list)
                        messages.append({'class': "border_bg_invalid", 'msg_html': msg_html})

# - add update_dict to update_wrap

# must update all studsubjects from this student, because the exclamation sign must be updated
                    # in all sudsubjects, not only the updeted ones
                    updated_rows = create_studentsubject_rows(
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_school.base if sel_school else None,
                        sel_depbase=sel_department.base if sel_department else None,
                        append_dict= updated_rows_append_dict,
                        request=request,
                        requsr_same_school=True,  # check for same_school is included in may_edit
                        student_pk=student_instance.pk
                    )
                    #PR2023-01-07 added to update composistion tickmark in all studsubjects of this student
                    for row in updated_rows:
                        row['changed'] = True

                    if deleted_rows:
                        updated_rows.extend(deleted_rows)

                    if logging_on and False:
                        logger.debug('    updated_rows: ' + str(updated_rows))

                    if updated_rows:
                        update_wrap['updated_studsubj_rows'] = updated_rows

# +++ validate subjects of student
                        # no message necessary, done by test before saving
                        #msg_html = stud_val.Fstudent)
                        #if msg_html:
                        #    update_wrap['studsubj_validate_html'] = msg_html
                        #if logging_on:
                        #    logger.debug('msg_html: ' + str(msg_html))

                   # has_error = stud_val.validate_studentsubjects_no_msg(student_instance, user_lang)

                    #update_wrap['subj_error'] = has_error
                    #update_wrap['stud_pk'] = student_instance.pk

        if len(messages):
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of StudentsubjectMultipleUploadView


def delete_studentsubject(student_instance, studsubj_instance, request):
    # PR2021-07-18 PR2022-02-16 PR2022-08-05 PR2023-02-22

    # published fields are: subj_published, exem_published, reex_published, reex3_published, pok_published
    # if published: don't delete, but set 'tobedeleted' = True, so its remains in the Ex1 form
    #       also remove approved and published info
    #       PR2023-02-12 dont have to set grades 'tobedeleted', grdaes of deleted studsubj are fitered out by sql studsubj.tobedeleted=False
    #           only exem, reex and reex03 grades are set tobedeleted when deleteingexem, reex or reex 3
    #           was: also set grades 'tobedeleted'=True
    # if not published: delete studsubj, grades will be cascade deleted

    # PR2022-02-15 studentsubject can always be deleted

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_studentsubject ----- ')
        logger.debug('    studsubj_instance: ' + str(studsubj_instance))

    msg_html = None
    err_html = ''

    this_txt = None
    if studsubj_instance.schemeitem:
        subject = studsubj_instance.schemeitem.subject
        if subject and subject.name_nl:
            this_txt = _("Subject '%(tbl)s' ") % {'tbl': subject.name_nl}

            if logging_on:
                logger.debug('    subject: ' + str(subject))

# - check if studsubj_instance is submitted
    if studsubj_instance.subj_published_id or \
            studsubj_instance.sr_published_id or \
            studsubj_instance.reex_published_id or \
            studsubj_instance.reex3_published_id:
        is_submitted = True
    else:
        is_submitted = False
    if logging_on:
        logger.debug('    is_submitted: ' + str(is_submitted))

# - when studsubj is submitted, tobedeleted is set True, studsubj will be retrieved by updated_rows = create_studentsubject_rows
    # the key 'tobedeleted' must be added via append_dict

# - when studsubj is not yet submitted, deleted is set True, studsubj will NOT be retrieved by updated_rows = create_studentsubject_rows
    # therefore a dict with the info af the deleted row must be added to updated_rows at the end, to remove the dict from the data_dicts and the tblrow

    deleted_row, tobedeleted_studsubj_pk = None, None

    studsubj_instance_pk = studsubj_instance.pk
    map_id = '_'.join(('studsubj', str(student_instance.pk), str(studsubj_instance.pk)))

# - check if studentsubject has submitted grades or school is locked or examyear is locked PR2021-08-21
    # PR2022-02-15 studentsubject can always be deleted

    # PR2022-08-30 MAJOR BUG: student was deleted instead of studsubj,
    # because 'instance=student_instance' instead of 'instance=studsubj_instance'

    # PR2022-12-18 set tobedeleted=True and remove published info instead of deleting record, also in table grades
    # was:
    #   # delete student will also cascade delete Grades
    #   deleted_rowNIU, err_html = sch_mod.delete_instance(
    #       table='studsubj', # used to create mapid in deleted_row
    #       instance=studsubj_instance, # MAJOR BUG was: instance=student_instance
    #       request=request,
    #       this_txt=this_txt)

    try:
        if is_submitted:
            setattr(studsubj_instance, 'tobedeleted', True)

    # - also remove approved and published info, store it in prev_auth1by_id etc
            setattr(studsubj_instance, 'prev_auth1by_id', getattr(studsubj_instance, 'subj_auth1by_id', None))
            setattr(studsubj_instance, 'prev_auth2by_id', getattr(studsubj_instance, 'subj_auth2by_id', None))
            setattr(studsubj_instance, 'prev_published_id', getattr(studsubj_instance, 'subj_published_id', None))

            tobedeleted_studsubj_pk = studsubj_instance.pk

        else:
            setattr(studsubj_instance, 'deleted', True)
            setattr(studsubj_instance, 'tobedeleted', False)

            setattr(studsubj_instance, 'prev_auth1by_id', None)
            setattr(studsubj_instance, 'prev_auth2by_id', None)
            setattr(studsubj_instance, 'prev_published_id',None)

            # - create deleted_row, to be sent back to page
            deleted_row = {'id': studsubj_instance_pk,
                           'mapid': '_'.join(('studsubj', str(student_instance.pk), str(studsubj_instance.pk))),
                           'deleted': True}

        setattr(studsubj_instance, 'subj_auth1by_id', None)
        setattr(studsubj_instance, 'subj_auth2by_id', None)
        setattr(studsubj_instance, 'subj_published_id', None)

        studsubj_instance.save(request=request)

        if logging_on:
            logger.debug('    studsubj_instance: ' + str(studsubj_instance))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

        err_html = ''.join((
            str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
            str(_('%(cpt)s could not be deleted.') % {'cpt': this_txt})
        ))
        # msg_dict = {'header': header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html}

    # grades.tobedeleted and deleted are only used in exem, reex and reex3
    # NIU: err_html = delete_studentsubject_grades(studsubj_instance, this_txt, tobedeleted_row, updated_rows, request)

    if err_html:
        msg_html = err_html

    if logging_on:
        logger.debug('msg_html: ' + str(msg_html))
        logger.debug('deleted_row' + str(deleted_row))

    return deleted_row, tobedeleted_studsubj_pk, msg_html
# - end of delete_studentsubject


def delete_studentsubject_grades(studsubj_instance, this_txt, request):
    logging_on = s.LOGGING_ON
    #PR2023-02-12 dont set grade.tobedeleted.
    # grade.tobedeleted is only used when deleting exem. reex or reex03
    err_html = None
    try:
        grades = stud_mod.Grade.objects.filter(
            studentsubject=studsubj_instance,
            tobedeleted=False
        )

        if logging_on:
            logger.debug('    grades: ' + str(grades))

        modifiedby_pk_str = str(request.user.pk)
        modifiedat_str = str(timezone.now())
        sql_keys = {'studsubj_id': studsubj_instance.pk}

        sql_list = [
            "UPDATE students_grade",
            "SET tobedeleted = TRUE, deleted = TRUE,",
            "modifiedby_id =", modifiedby_pk_str, ", modifiedat = '", modifiedat_str, "'",
            "WHERE students_grade.studentsubject_id = %(studsubj_id)s::INT",
            "RETURNING id;"
        ]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)

            if logging_on:
                rows = cursor.fetchall()
                logger.debug(' grade rows: ' + str(rows))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

        err_html = ''.join((
            str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
            str(_('%(cpt)s could not be deleted.') % {'cpt': this_txt})
        ))
        deleted_row = None
    return err_html
# end of delete_studentsubject_grades

####################################################

@method_decorator([login_required], name='dispatch')
class StudentsubjectSingleUpdateView(View):  # PR2021-09-18 PR2023-04-01

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectSingleUpdateView ============= ')

        # function updates single studentsubject record
        update_wrap = {}

        msg_html = None
        msg_list = []
        err_fields = []
        border_class = None

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            has_permit = acc_prm.get_permit_crud_of_this_page('page_studsubj', request)
        if logging_on:
            logger.debug('    has_permit: ' + str(has_permit))

        if not has_permit:
            border_class = c.HTMLCLASS_border_bg_invalid
            msg_list.append(gettext("You don't have permission %(cpt)s.") % {'cpt': gettext('to perform this action')})
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                    # upload_dict: {'student_pk': 8470, 'studsubj_pk': 61203, 'has_exemption': True}
                # requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase_pk)

# - get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not same_school, not activated, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase
                #  TODO student is tobedeleted or studsubj is tobedeleted

                # check requsr_same_school is part of get_selected_ey_school_dep_lvl_from_usersetting
                sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                if err_list:
                    err_list.append(str(_('You cannot make changes.')))
                    msg_list.extend(err_list)
                    border_class = c.HTMLCLASS_border_bg_invalid
                else:
                    if logging_on:
                        logger.debug('    upload_dict:    ' + str(upload_dict))
                        logger.debug('    sel_examyear:   ' + str(sel_examyear))
                        logger.debug('    sel_school:     ' + str(sel_school))
                        logger.debug('    sel_department: ' + str(sel_department))

# - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                    student_pk = upload_dict.get('student_pk')
                    student_instance = stud_mod.Student.objects.get_or_none(
                        id=student_pk,
                        school=sel_school,
                        department=sel_department
                    )
                    if student_instance.deleted:
                        msg_list.append(gettext("This candidate is deleted."))
                        border_class = c.HTMLCLASS_border_bg_invalid
                    elif student_instance.tobedeleted:
                        msg_list.extend([gettext("This candidate is marked for deletion."), gettext("You cannot make changes.")])
                        border_class = c.HTMLCLASS_border_bg_invalid
                    else:
                        if logging_on:
                            logger.debug('    msg_list: ' + str(msg_list))
                            logger.debug('    may_edit: ' + str(may_edit))
                            logger.debug('    student_instance: ' + str(student_instance))

    # - get studentsubject from upload_dict
                        studsubj_pk = upload_dict.get('studsubj_pk')
                        studsubj = stud_mod.Studentsubject.objects.get_or_none(
                            id=studsubj_pk,
                            student=student_instance
                        )
                        if studsubj:
                            if studsubj.deleted:
                                msg_list.append(gettext("This subject is deleted."))
                                border_class = c.HTMLCLASS_border_bg_invalid
                            elif studsubj.tobedeleted:
                                msg_list.extend([gettext("This subject is marked for deletion."),
                                                 gettext("You cannot make changes.")])
                                border_class = c.HTMLCLASS_border_bg_invalid
                            else:

                                studsubj_pk_list = [studsubj.pk]

                                if logging_on:
                                    logger.debug('    studsubj: ' + str(studsubj))

        # - validate if requsr has allowed_cluster to change this subject - validate allowed levl / subjects not necessary, because only allowed subjects are shown
                                cluster_pk = studsubj.cluster_id
                                userallowed_cluster_pk_list = acc_prm.get_userallowed_cluster_pk_list_from_request(request)
                                is_allowed = acc_prm.validate_userallowed_cluster(userallowed_cluster_pk_list, cluster_pk)
                                if not is_allowed:
                                    msg_list.append(gettext("You don't have permission %(cpt)s.") % {
                                        'cpt': gettext('to make changes in subjects of this cluster')})

                                    # return err_fields, to restore old value on client
                                    for fld_name in upload_dict:
                                        if fld_name in ('cluster_pk', 'pws_title', 'pws_subjects', 'exemption_year', 'is_thumbrule',
                                                     'is_extra_nocount', 'is_extra_countsNIU', 'has_exemption', 'has_reex', 'has_reex03', '_auth'):
                                            err_fields.append(fld_name)

                                    if logging_on:
                                        logger.debug('    err_fields: ' + str(err_fields))
                                else:

        # - get schemitem_info, separately, instead of getting from grade_instance, should be faster
                                    si_pk = studsubj.schemeitem_id
                                    if logging_on:
                                        logger.debug('si_pk: ' + str(si_pk))

                                    schemeitems_dict = subj_vw.get_scheme_si_dict(
                                            examyear_pk=sel_examyear.pk,
                                            depbase_pk=sel_department.base_id,
                                            schemeitem_pk=si_pk
                                        )
                                    si_dict = schemeitems_dict.get(si_pk)

        # +++++  update studentsubject
                                    updated_pk_list, recalc_subj_comp = update_studsubj(
                                        studsubj_instance=studsubj,
                                        upload_dict=upload_dict,
                                        si_dict=si_dict,
                                        sel_examyear=sel_examyear,
                                        sel_school=sel_school,
                                        sel_department=sel_department,
                                        msg_list=msg_list,
                                        err_fields=err_fields,
                                        request=request
                                    )
                                    if updated_pk_list:
                                        studsubj_pk_list.extend(updated_pk_list)

                                    if logging_on:
                                        logger.debug('updated_pk_list: ' + str(updated_pk_list))

                                    if recalc_subj_comp:
                                        update_student_subj_composition(student_instance)

            # - add update_dict to update_wrap
                                # TODO check value of msg_dict
                                #  msg_dict['err_' + field] = str(_("Title and subjects only allowed in subjects with character 'Werkstuk'."))
                                #  msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')
                                append_dict = {}
                                if err_fields:
                                    # PR2023-02-18 note: append_dict has key with studsubj_pk
                                    append_dict[studsubj.pk] = {'err_fields': err_fields}
                                    border_class = c.HTMLCLASS_border_bg_invalid

                                if logging_on:
                                    logger.debug('    append_dict: ' + str(append_dict))

                                # TODO PR2022-12-22 check if sel_lvlbase must get value

                                studsubj_rows = create_studentsubject_rows(
                                    sel_examyear=sel_examyear,
                                    sel_schoolbase=sel_school.base if sel_school else None,
                                    sel_depbase=sel_department.base if sel_department else None,
                                    append_dict=append_dict,
                                    request=request,
                                    requsr_same_school=True,  # check for same_school is included in may_edit
                                    student_pk=student_instance.pk,
                                    studsubj_pk_list=studsubj_pk_list
                                )
                                if studsubj_rows:
                                    update_wrap['updated_studsubj_rows'] = studsubj_rows

        if msg_list:
            update_wrap['msg_html'] = acc_prm.msghtml_from_msglist_with_border(msg_list, border_class)

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentsubjectSingleUpdateView


#######################################################
def update_studsubj(studsubj_instance, upload_dict, si_dict, sel_examyear, sel_school, sel_department,
                    msg_list, err_fields, request):
    # PR2019-06-06 PR2021-12-25 PR2022-04-15 PR2022-06-25 PR2022-08-25
    # --- update existing and new studsubj_instance PR2019-06-06
    # called by StudentsubjectMultipleUploadView, StudentsubjectSingleUpdateView, StudentsubjectApproveSingleView

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_studsubj -------')
        logger.debug('    upload_dict: ' + str(upload_dict))
        """
        upload_dict{'mode': 'update', 'studsubj_pk': 26993, 'schemeitem_pk': 2033, 'subj_auth2by': 48}
        upload_dict: {'student_pk': 9224, 'studsubj_pk': 67818, 'has_reex': False}
        upload_dict: {'student_pk': 9226, 'studsubj_pk': 67836, 'subj_auth2by': True}
        
        when changing schemeitem_pk:
        upload_dict: {
            'mode': 'update', 
            'student_pk': 5231, 'studsubj_pk': 45376, 'schemeitem_pk': 1721, 
            'is_extra_nocount': False, 'is_extra_counts': False, 'pws_title': None, 'pws_subjects': None, 
            'tobedeleted': False}
        """

    save_changes = False
    recalc_finalgrade = False
    recalc_subj_composition = False

    studsubj_pk_list = []
    for field, new_value in upload_dict.items():

# +++ save changes in studsubj_instance fields
        if field == 'schemeitem_pk':
            saved_schemeitem = getattr(studsubj_instance, 'schemeitem')
            new_schemeitem = subj_mod.Schemeitem.objects.get_or_none(pk=new_value)
            if logging_on:
                logger.debug('    saved studsubj_schemeitem: ' + str(saved_schemeitem))
                logger.debug('    new_schemeitem: ' + str(new_schemeitem))

            if new_schemeitem is None:
                msg_list.append(str(_("Subject scheme of this subject is not found.")))

            elif saved_schemeitem:
                if new_schemeitem.pk != saved_schemeitem.pk:
                    setattr(studsubj_instance, 'schemeitem', new_schemeitem)

            # - also remove approved and published info
                    # TODO also from grades??
                    setattr(studsubj_instance, 'prev_auth1by_id', getattr(studsubj_instance, 'subj_auth1by_id', None))
                    setattr(studsubj_instance, 'prev_auth2by_id', getattr(studsubj_instance, 'subj_auth2by_id', None))
                    setattr(studsubj_instance, 'prev_published_id', getattr(studsubj_instance, 'subj_published_id', None))

                    setattr(studsubj_instance, 'subj_auth1by', None)
                    setattr(studsubj_instance, 'subj_auth2by', None)
                    setattr(studsubj_instance, 'subj_published', None)

                    setattr(studsubj_instance, 'tobechanged', True)

                    save_changes = True
                    recalc_finalgrade = True
                    recalc_subj_composition = True

                    if logging_on:
                        logger.debug('>>>>> new_schemeitem save')

        elif field in ['pws_title', 'pws_subjects']:
            # only allowed when subjecttype has_pws = True
            if not studsubj_instance.schemeitem.subjecttype.has_pws:
                if new_value:
                    subj_name = studsubj_instance.schemeitem.subject.name_nl
                    msg_list.append(str(_("Title and subjects are not allowed in subject %(cpt)s.") % {'cpt': subj_name}))
            else:
                err_list = []
                saved_value = getattr(studsubj_instance, field)
                if logging_on:
                    logger.debug('saved_value: ' + str(saved_value))

                if new_value:
                    err_list = stud_val.validate_studsubj_pws_title_subjects_length(field, new_value)
                    if err_list:
                        msg_list.extend(err_list)
                        err_fields.append(field)

                if not err_list:
                    if new_value != saved_value:
                        setattr(studsubj_instance, field, new_value)
                        save_changes = True

        elif field == 'cluster_pk':
            new_cluster = subj_mod.Cluster.objects.get_or_none(pk=new_value)
            saved_cluster = getattr(studsubj_instance, 'cluster')
            if new_cluster != saved_cluster:
                setattr(studsubj_instance, 'cluster', new_cluster)
                save_changes = True

        elif field == 'exemption_year':
            # changing is only allowed when evening or lex student. Is set on client side
            saved_value = getattr(studsubj_instance, field)
            if logging_on:
                logger.debug('field: ' + str(field))
                logger.debug('new_value: ' + str(new_value))
                logger.debug('saved_value: ' + str(saved_value))
            if new_value != saved_value:
                setattr(studsubj_instance, field, new_value)
                save_changes = True
                recalc_finalgrade = True

        elif field == 'is_thumbrule':
            saved_value = getattr(studsubj_instance, field)
            err_list = []
            if new_value:
                err_list = stud_val.validate_thumbrule_allowed(studsubj_instance)
                if err_list:
                    msg_list.extend(err_list)
                    err_fields.append(field)

            if not err_list:
                if logging_on:
                    logger.debug('saved_value: ' + str(saved_value) + str(type(new_value)))
                    logger.debug('new_value: ' + str(new_value) + str(type(new_value)))

                if new_value != saved_value:
                    setattr(studsubj_instance, field, new_value)
                    save_changes = True
        # when combi: apply or remove thumbrule also to other combi subjects
                    if studsubj_instance.schemeitem.is_combi:
                        other_combi_subjects = stud_mod.Studentsubject.objects.filter(
                            student=studsubj_instance.student,
                            schemeitem__is_combi=True,
                            tobedeleted=False
                        ).exclude(pk=studsubj_instance.pk)

                        if other_combi_subjects:
                            for other_combi in other_combi_subjects:
                                setattr(other_combi, field, new_value)
                                other_combi.save(request=request)
                                studsubj_pk_list.append(other_combi.pk)

                            if new_value:
                                set_remove = str(pgettext_lazy('the thumbrule is set to', 'set to'))
                            else:
                                set_remove =str(pgettext_lazy('the thumbrule is removed from', 'removed from'))
                            msg_list.append(
                                str(_('The thumb rule is only applicable to the combination grade, not to individual combi subjects.')))
                            msg_list.append(
                                str(_('Therefore the thumbrule is also %(cpt)s the other combi subjects of this candidate.') %{'cpt': set_remove}))

        elif field in ('is_extra_nocount', 'is_extra_countsNIU'):
            err_list = []
            if new_value:
                err_list = stud_val.validate_extra_nocount_allowed(studsubj_instance)
                if err_list:
                    msg_list.extend(err_list)
                    err_fields.append(field)

            if not err_list:
                saved_value = getattr(studsubj_instance, field)
                if logging_on:
                    logger.debug("new value   of field '" + str(field) + "': " + str(new_value))
                    logger.debug("saved value of field '" + str(field) + "': " + str(saved_value))

                if new_value != saved_value:
                    setattr(studsubj_instance, field, new_value)
                    save_changes = True

        # TODO check or delete has_sr, disabled for now
        elif field == 'has_sr' and False:
            saved_value = getattr(studsubj_instance, field)
# +++++ add or delete re-examination school exam
            # - toggle value of has_sr:
            # - set sr = None
            # - recalc grade (sesr, pece, final)
            # - recalc max_ etc in studsubj
            # - recalc result in student
            if new_value != saved_value:
                err_list = []
    # - get grade of first exam period
                grade_firstperiod = stud_mod.Grade.objects.get_or_none(
                    studentsubject=studsubj_instance,
                    examperiod=c.EXAMPERIOD_FIRST
                )

                if logging_on:
                    logger.debug('grade_firstperiod: ' + str(grade_firstperiod))

                if grade_firstperiod is None:
                    msg_list.append(str(_('An error occurred')))
                    msg_list.append(str(_('Grade record not found')))
                else:
                    recalc_grade_firstperiod = False
    # +++ add re-examination school exam:
                    if new_value:
        # - check if adding sr is allowed
                        err_list = stud_val.validate_studsubj_sr_allowed(si_dict)
                        if err_list:
                            msg_list.extend(err_list)
                        else:
        # - save has_sr
                            setattr(studsubj_instance, field, new_value)
                            save_changes = True
                            recalc_finalgrade = True
                            recalc_grade_firstperiod = True
                    else:
# +++ delete re-examination school exam:
        # - check if deleting sr is allowed
                        # note: a sr can be deleted when it is submitted but does not have an approved grade yet

                        this_item_cpt = str(_('This re-examination school exam'))
                        err_list = grad_val.validate_grade_published_from_gradeinstance(grade_firstperiod, 'sr', this_item_cpt)
                        if err_list:
                            err_list.append(str(_('You cannot delete %(cpt)s.') % {'cpt': this_item_cpt.lower()}))

                        if logging_on:
                            logger.debug('.............. err_list: ' + str(err_list))

                        if err_list:
                            msg_list.extend(err_list)
                        else:
        # - save when new_value != saved_value and no error
                            setattr(studsubj_instance, field, new_value)
                            save_changes = True
                            recalc_finalgrade = True

        # remove value from srgrade, also remove approval and published info
                            setattr(grade_firstperiod, 'srgrade', None)
                            setattr(grade_firstperiod, 'sr_auth1by_id', None)
                            setattr(grade_firstperiod, 'sr_auth2by_id', None)
                            setattr(grade_firstperiod, 'sr_published_id', None)
                            recalc_grade_firstperiod = True

                    if recalc_grade_firstperiod:
        # recalculate sesr, pece, final in all grade_periods
                        grd_view.recalc_finalgrade_in_grade_and_save(grade_firstperiod, si_dict)
                        grade_firstperiod.save()

        # - count 'exemption', 'sr', 'reex', 'reex03', 'is_thumbrule' records of this student an save count in student
                        update_reexcount_etc_in_student(field, studsubj_instance.student_id)

        elif field in ['has_exemption', 'has_reex', 'has_reex03']:
            # upload_dict: {'student_pk': 4432, 'studsubj_pk': 27484, 'has_reex': False}
            # field = 'has_reex', new_value = False

# +++++ add or delete exemption, reex, reex03
            # - toggle value of has_exemption, has_reex or has_reex03
            # - when add: add grade with examperiod = 4, 2 or 3
            # - when reex or reex03: add segrade, srgrade and pegrade in reex grade_instance
            # - when delete: set 'tobedeleted' = True and reset all values of grade
            # - recalc max_ etc in studsubj
            # - recalc result in student

            must_add_delete_exem_reex_reex03 = False

# +++++ add exemption, reex, reex03
            if new_value:

    # - validate if adding reex or reex03 is allowed
                err_list = stud_val.validate_studsubj_add_reex_reex03_allowed(field, si_dict)

                # don't check if the number of re-examinations equals or exceeds the maximum
                #   students that have been sick may do multiple reex
                #   was: if not err_list:
                #           err_list = stud_val.validate_reex_count(studsubj_instance, si_dict)

                if err_list:
                    msg_list.extend(err_list)
                    err_fields.append(field)
                else:
                    saved_value = getattr(studsubj_instance, field)

                    if new_value != saved_value:
                        setattr(studsubj_instance, field, new_value)
                        save_changes = True
                        recalc_finalgrade = True
                        must_add_delete_exem_reex_reex03 = True
                        if logging_on:
                            logger.debug(' add reex, field: ' + str(field) + ' ' + str(new_value))

                        recalc_reex_grade = field in ('has_reex', 'has_reex03')
    # - when setting exemption: fill in previous examyear as exemption_year PR2022-04-15
                        if field == 'has_exemption':
                            previous_exam_year = sel_examyear.code - 1
                            setattr(studsubj_instance, 'exemption_year', previous_exam_year)

            else:

# +++++ delete exemption, sr, reex, reex03
        # - get saved value
                saved_value = getattr(studsubj_instance, field)
                if logging_on:
                    logger.debug(' delete reex, field: ' + str(field))
                    logger.debug(' delete reex, saved_value: ' + str(saved_value))
                    logger.debug(' delete reex, new_value: ' + str(new_value))

        # - save when new_value != saved_value
                if new_value != saved_value:

        # - check if deleting is allowed
                    #  check if grade is authorized, published or blocked
                    err_list = grad_val.validate_exem_sr_reex_reex03_delete_allowed(
                        studsubj_instance=studsubj_instance,
                        field=field
                    )

                    if err_list:
                        msg_list.extend(err_list)
                        err_fields.append(field)
                    else:
        # - set 'has_exemption' or 'has_reex' or 'has_reex03  False
                        setattr(studsubj_instance, field, new_value)
                        save_changes = True
                        recalc_finalgrade = True
                        must_add_delete_exem_reex_reex03 = True
                        if logging_on:
                            logger.debug(' removed reex, field: ' + str(field) + ' new_value: ' + str(new_value))

        # - when deleting exemption: also delete exemption_year PR2022-04-15
                        if field == 'has_exemption':
                            setattr(studsubj_instance, 'exemption_year', None)

# --- add exem, reex, reex03 grade or make grade 'tobedeleted'
            # when adding: also put values of segrade, srgrade and pegrade in new grade_instance
            if must_add_delete_exem_reex_reex03:
                err_list = add_or_delete_grade_exem_reex_reex03( field, studsubj_instance, new_value, request)
                if logging_on:
                    logger.debug('  err_list:     ' + str(err_list))

                if err_list:
                    msg_list.extend(err_list)
                    err_fields.append(field)
        # - count 'exemption', 'sr', 'reex', 'reex03' records of this student an save count in student
                update_reexcount_etc_in_student(field, studsubj_instance.student_id)

        elif '_auth' in field:

            prefix, authby = field.split('_')
            if logging_on:

                logger.debug('  field:     ' + str(field) )
                logger.debug('  new_value: ' + str(new_value))
                logger.debug('  prefix:    ' + str(prefix) )
                logger.debug('  authby:    ' + str(authby) )

# - check if instance is published. Authorization of published instances cannot be changed.
            err_published, err_same_user = False, False
            fld_published = prefix + '_published'
            item_published = getattr(studsubj_instance, fld_published)
            if logging_on:
                logger.debug(str(fld_published) + ': ' + str(item_published))

            if item_published:
                err_published = True
                msg_list.append(str(_('This item is published. You cannot change its authorization.')))

# - check other authorization, to check if it is the same user. Only when auth is set to True
            elif new_value:
                authby_other = 'auth2by' if authby == 'auth1by' else 'auth1by'
                fld_other = prefix + '_' + authby_other
                other_authby = getattr(studsubj_instance, fld_other)
                if logging_on:
                    logger.debug('  fld_other:    ' + str(fld_other))
                    logger.debug('  other_authby: ' + str(other_authby))
                    logger.debug('  request.user: ' + str(request.user) )

                if other_authby and other_authby == request.user:
                    err_same_user = True
                    err_fields.append(field)

                    msg_list.append(str(_('You already have approved this subject in a different function.')))
                    msg_list.append(str(_('You cannot approve a subject in multiple functions.')))

                if logging_on:
                    logger.debug('  err_same_user:    ' + str(err_same_user))

            if not err_published and not err_same_user:
                # value of new_value is True or False, not aurh_id or None
                # use request.user or None as new_value
                if logging_on:
                    logger.debug('new_value: ' + str(new_value) )
                if new_value:
                    setattr(studsubj_instance, field, request.user)
                else:
                    setattr(studsubj_instance, field, None)
                save_changes = True
    # --- end of for loop ---

# 5. save changes`
    if save_changes:
        try:
            studsubj_instance.save(request=request)
            if logging_on:
                logger.debug('The changes have been saved: ' + str(studsubj_instance))
        except Exception as e:
            recalc_subj_composition = False
            logger.error(getattr(e, 'message', str(e)))
            msg_list.append(acc_prm.msghtml_error_occurred_with_border(e, _('The changes have not been saved.')))
        else:

            if logging_on:
                logger.debug('    recalc_finalgrade: ' + str(recalc_finalgrade))
                logger.debug('    studsubj_instance: ' + str(studsubj_instance))

            if recalc_finalgrade:
                grades = stud_mod.Grade.objects.filter(
                    studentsubject=studsubj_instance,
                    tobedeleted=False
                )
                if logging_on:
                    logger.debug('grades: ' + str(grades))

                for grade_instance in grades:
                    if logging_on:
                        logger.debug('grade_instance: ' + str(grade_instance))
                        logger.debug('grade_instance.examperiod: ' + str(grade_instance.examperiod))
                # - recalculate gl_sesr, gl_pece, gl_final, gl_use_exem in studsubj record
                    if grade_instance and grade_instance.examperiod == c.EXAMPERIOD_FIRST:
                        # when first examperiod: also update and save grades in reex, reex03, if exist
                        grd_view.recalc_finalgrade_in_reex_reex03_grade_and_save(grade_instance, si_dict)

                try:
                    student = studsubj_instance.student
                    if logging_on:
                        logger.debug('student: ' + str(student))

                    sql_studsubj_list, sql_student_list = grd_view.update_studsubj_and_recalc_student_result(
                            sel_examyear=sel_examyear,
                            sel_school=sel_school,
                            sel_department=sel_department,
                            student=studsubj_instance.student
                        )
                    if logging_on:
                        logger.debug('sql_studsubj_list: ' + str(sql_studsubj_list))
                        logger.debug('sql_student_list: ' + str(sql_student_list))

                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))


                try:
                    if sql_studsubj_list:
                        calc_res.save_studsubj_batch(sql_studsubj_list)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                try:
                    # save calculated fields in student
                    if sql_student_list:
                        calc_res.save_student_batch(sql_student_list)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('msg_list: ' + str(msg_list))
        logger.debug('  ..... end of update_studsubj .....')
    return studsubj_pk_list, recalc_subj_composition
# --- end of update_studsubj

def update_student_subj_composition(student_instance):
    # PR2022-08-30
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_student_subj_composition -------')
        logger.debug('     student_instance: ' + str(student_instance))


    no_error = not stud_val.validate_studentsubjects_no_msg(student_instance, 'nl')
    if (not student_instance.subj_composition_checked) or \
            (student_instance.subj_composition_checked and student_instance.subj_composition_ok != no_error):
        setattr(student_instance, 'subj_composition_checked', True)
        setattr(student_instance, 'subj_composition_ok', no_error)
        # dont update modified by
        student_instance.save()

    if logging_on:
        logger.debug('     subj_composition_checked: ' + str(student_instance.subj_composition_checked))
        logger.debug('     subj_composition_ok:      ' + str(student_instance.subj_composition_ok))

# --- end of update_student_subj_composition


def add_or_delete_grade_exem_reex_reex03(field, studsubj_instance, new_value, request):  # PR2021-12-15
    # fields are 'has_exemption', 'has_reex', 'has_reex03'
    # when new_value = True: add or undelete grade
    # when new_value = False: make grade 'tobedeleted', remove all values if allowed


    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- add_or_delete_grade_exem_reex_reex03 -------')
        logger.debug('     field: ' + str(field))
    exam_period = None
    if field == 'has_exemption':
        exam_period = c.EXAMPERIOD_EXEMPTION
    elif field == 'has_reex':
        exam_period = c.EXAMPERIOD_SECOND
    elif field == 'has_reex03':
        exam_period = c.EXAMPERIOD_THIRD

    if logging_on:
        logger.debug('     exam_period: ' + str(exam_period))
        logger.debug('     new_value: ' + str(new_value))

    err_list = []

    try:
        save_changes = False

# - check if grade of this exam_period exists
        # Note: don't use get_or_none, returns None when multiple records exists and therefore will add another one
        grade = stud_mod.Grade.objects.filter(
            studentsubject=studsubj_instance,
            examperiod=exam_period
        ).first()

        if logging_on:
            logger.debug('     grade exists: ' + str(grade))

# +++ add or undelete grade
        # when new_value = True: add or undelete grade
        if new_value:
            save_changes = True

            if grade:
                if logging_on:
                    logger.debug('     grade deleted: ' + str(grade.deleted))
        # - if grade exists: it must be deleted row. Undelete

                # TODO PR2023-01-23 replace grade 'tobedeleted' by  grade 'deleted', let 'tobedeleted' stay for now
                setattr(grade, 'tobedeleted', False)
                setattr(grade, 'deleted', False)
                if logging_on:
                    logger.debug('     grade deleted: ' + str(grade.deleted))
            else:
        # - if grade does not exist: create new grade row
                grade = stud_mod.Grade(
                    studentsubject=studsubj_instance,
                    examperiod=exam_period)

                if logging_on:
                    logger.debug('     grade new: ' + str(exam_period))
    # if 2nd or 3rd period: get se sr pe from first period and put them in new grade
            # PR2022-01-05 dont save se, sr, pe in reex reex03 any more
            # PR2022-05-29 changed my mind: due to batch update needs nthosegardes in reex_grade to calc final grade
            # must make sure that values in reex_grade are updated when update them in ep 1
            if exam_period in (c.EXAMPERIOD_SECOND, c.EXAMPERIOD_THIRD):
                found, segrade, srgrade, pegrade = get_se_sr_pe_from_grade_ep1(studsubj_instance)

                if logging_on:
                    logger.debug('     segrade: ' + str(segrade))

                if found:
                    setattr(grade, 'segrade', segrade)
                    setattr(grade, 'srgrade', srgrade)
                    setattr(grade, 'pegrade', pegrade)
                if logging_on:
                    logger.debug('     segrade: ' + str(segrade))
        else:
            if grade:
                if logging_on:
                    logger.debug('     set grade tobedeleted ')

# +++ set grade tobedeleted
    # - when new has_exemption etc. is False: delete row by setting deleted=True and reset all fields
                clear_grade_fields(grade)
                # TODO PR2023-012-12 check difference between grade 'tobedeleted' and grade 'deleted'
                setattr(grade, 'tobedeleted', True)
                setattr(grade, 'deleted', True)
                save_changes = True

                if logging_on:
                    logger.debug('     set grade deleted and tobedeleted : ' + str(grade.deleted))

        if save_changes:
            grade.save(request=request)
            if logging_on:
                logger.debug('    changes in grade are saved ')

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        err_list.append(str(_('An error occurred. The changes have not been saved.')))

    return err_list
# --- end of add_or_delete_grade_exem_reex_reex03


def clear_grade_fields(grade_instance):  # PR2021-12-24
    for fld in ('pescore', 'cescore', 'segrade', 'srgrade', 'sesrgrade',
                'pegrade', 'cegrade', 'pecegrade', 'finalgrade'):
        setattr(grade_instance, fld, None)

    for prefix in ('se', 'sr', 'pe', 'ce'):
        for suffix in ('auth1by_id', 'auth2by_id', 'auth3by_id', 'auth4by_id', 'published_id'):
            fld = '_'.join((prefix, suffix))
            setattr(grade_instance, fld, None)

        fld = '_'.join((prefix, 'status'))
        setattr(grade_instance, fld, 0)

        fld = '_'.join((prefix, 'blocked'))
        setattr(grade_instance, fld, False)

    for prefix in ('pe', 'ce'):
        for suffix in ('exam_id', 'exam_result', 'exam_auth1by_id', 'exam_auth2by_id', 'exam_published_id'):
            fld = '_'.join((prefix, suffix))
            setattr(grade_instance, fld, None)
        fld = '_'.join((prefix, 'blocked'))
        setattr(grade_instance, fld, False)
# - end of clear_grade_fields


def get_se_sr_pe_from_grade_ep1(studentsubject):  # PR2021-12-25 PR2022-05-29
    # functions returns value of se, sr, pe from first period,
    # called when creating grade of 2nd or 3rd period

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_se_sr_pe_from_grade_ep1 -------')
        logger.debug('studentsubject: ' + str(studentsubject))

    segrade, srgrade, pegrade = None, None, None
    found = False

# get grade of first examperiod
    # Note: with .values a dict is returned, not a model instance
    # grade_first_period: {'segrade': '5,7', 'srgrade': None, 'pegrade': '4.3'}
    grades_first_period = stud_mod.Grade.objects.filter(
        studentsubject=studentsubject,
        examperiod=c.EXAMPERIOD_FIRST
    ).values('segrade', 'srgrade', 'pegrade')

    grade_first_period = None
    found, multiple_found = False, False
    if grades_first_period:
        for row in grades_first_period:
            if logging_on:
                logger.debug('row: ' + str(row))

            if not found:
                found = True
                grade_first_period = row
            else:
                multiple_found = True
                break

# - give error when there are zero or multiple grade rows with first examperiod, should not be possible
    if grade_first_period is None:
        logger.error('ERROR: ' + ('multiple' if multiple_found else 'no' ) + ' grades found in first examperiod.')
        logger.error('       studentsubject: ' + str(studentsubject))
        logger.error('       student: ' + str(studentsubject.student))
    else:
        found = True
        segrade = grade_first_period.get('segrade')
        srgrade = grade_first_period.get('srgrade')
        pegrade = grade_first_period.get('pegrade')

    if logging_on:
        logger.debug(' >>> segrade: ' + str(segrade))
        logger.debug(' >>> srgrade: ' + str(srgrade))
        logger.debug(' >>> pegrade: ' + str(pegrade))

    return found, segrade, srgrade, pegrade
# - end of get_se_sr_pe_from_grade_ep1

# NOT IN USE
def copy_grade_fields_from_firstperiod(grade_instance):  # PR2021-12-25
    for fld in ('pescore', 'cescore', 'segrade', 'srgrade', 'sesrgrade',
                'pegrade', 'cegrade', 'pecegrade', 'finalgrade'):

        setattr(grade_instance, fld, None)

    for prefix in ('se', 'sr', 'pe', 'ce'):
        for suffix in ('auth1by_id', 'auth2by_id', 'auth3by_id', 'auth4by_id', 'published_id'):
            fld = '_'.join((prefix, suffix))
            setattr(grade_instance, fld, None)

        fld = '_'.join((prefix, 'status'))
        setattr(grade_instance, fld, 0)

        fld = '_'.join((prefix, 'blocked'))
        setattr(grade_instance, fld, False)

    for prefix in ('pe', 'ce'):
        for suffix in ('exam_id', 'exam_result', 'exam_auth1by_id', 'exam_auth2by_id', 'exam_published_id'):
            fld = '_'.join((prefix, suffix))
            setattr(grade_instance, fld, None)
        fld = '_'.join((prefix, 'blocked'))
        setattr(grade_instance, fld, False)


def update_reexcount_etc_in_student(field, student_pk=None):  # PR2021-12-19 PR2021-12-25 PR2022-06-05
    # values of field are 'has_exemption', 'has_sr', 'has_reex', 'has_reex03'

    # when 'has_exemption', 'has_reex', 'has_reex03': function counts grade records of this student
    # when 'has_sr', 'is_thumbrule': function counts studsubj records with value = True

    #   with filter:
    #   - student_pk
    #   - sel_examperiod
    #   - 'grd.tobedeleted' = False and studsubj.tobedeleted = False
    #   - when has_sr: studsubj.has_sr = True
    #   - when exemption, reex, reex03: no check on has_reex; grade with this ep does not exist when has_reex = False
    # Attention: must count after adding grade or saving tobedeleted = True

    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug('----------- update_reexcount_etc_in_student ----------- ')
        logger.debug('     field: ' + str(field))
        logger.debug('     student_pk: ' + str(student_pk))

    if field in ('has_exemption', 'has_sr', 'has_reex', 'has_reex03', 'is_thumbrule'):
        if True:
       # try:
            examperiod = c.EXAMPERIOD_EXEMPTION if field == 'has_exemption' else \
                         c.EXAMPERIOD_THIRD if field == 'has_reex03' else \
                         c.EXAMPERIOD_SECOND if field == 'has_reex' else \
                         c.EXAMPERIOD_FIRST
            db_field = 'exemption_count' if field == 'has_exemption' else \
                        'reex03_count' if field == 'has_reex03' else \
                        'reex_count' if field == 'has_reex' else \
                        'thumbrule_count' if field == 'is_thumbrule' else \
                        'sr_count'

            if logging_on:
                logger.debug('     examperiod: ' + str(examperiod))
                logger.debug('     db_field: ' + str(db_field))
                logger.debug('     student_pk: ' + str(student_pk))

            sql_keys = {'ep': examperiod}

            sub_sql_list = [
                "SELECT stud.id AS student_id, COUNT(*) AS record_count",

                "FROM students_grade AS grd",
                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",

                "WHERE grd.examperiod = %(ep)s::INT",
                "AND NOT grd.tobedeleted AND NOT grd.deleted AND NOT studsubj.tobedeleted"
            ]
            if field == 'has_sr':
                sub_sql_list.append("AND studsubj.has_sr")
            elif field == 'is_thumbrule':
                sub_sql_list.append("AND studsubj.is_thumbrule")

            sub_sql_list.append( "GROUP BY stud.id")
            sub_sql = ' '.join(sub_sql_list)

            # sub_sql row: {'student_id': 4671, 'count': 4}

            sql_list = ["WITH grades AS (", sub_sql, ")",
                        "UPDATE students_student",
                            "SET ", db_field, " = grades.record_count",
                        "FROM grades",
                        "WHERE grades.student_id = students_student.id"
                      ]

            if student_pk:
                 sql_keys['stud_pk'] = student_pk
                 sql_list.append("AND students_student.id = %(stud_pk)s::INT")

            sql_list.append("RETURNING students_student.id;")

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('     sql_keys: ' + str(sql_keys))
                logger.debug('     sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)

                if logging_on:
                    logger.debug('     cursor.execute: ')
                    for cq in connection.queries:
                        logger.debug('query: ' + str(cq.get('sql')))

                    rows = cursor.fetchall()
                    for row in rows:
                        # row is tuple: (3957, 1)
                        logger.debug('     row: ' + str(row))

                    sql_list = ["SELECT exemption_count, reex_count, reex03_count, thumbrule_count, sr_count, id, lastname, firstname",
                                "FROM students_student",
                                "WHERE exemption_count > 0 OR reex_count > 0 OR reex03_count > 0 OR thumbrule_count > 0 OR sr_count > 0",
                                ]
                    sql = ' '.join(sql_list)
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    for row in rows:
                        logger.debug('     row: ' + str(row))

        #except Exception as e:
        #    logger.error(getattr(e, 'message', str(e)))
# --- end of update_reexcount_etc_in_student


@method_decorator([login_required], name='dispatch')
class StudentsubjectnoteUploadView(View):  # PR2021-01-16

    def post(self, request):
        logging_on = s.LOGGING_ON

        files = request.FILES
        file = files.get('file')
        if logging_on:
            logger.debug(' ============= StudentsubjectnoteUploadView ============= ')
            logger.debug('files: ' + str(files) + ' ' + str(type(files)))
            logger.debug('file: ' + str(file) + ' ' + str(type(file)))

        # function creates, deletes and updates studentsubject records of current student PR2020-11-21
        update_wrap = {}

        #<PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated
        has_permit = False
        if request.user and request.user.country and request.user.schoolbase:
            has_permit = True # (request.user.role > c.ROLE_002_STUDENT and request.user.is_group_edit)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))

                # - get selected examyear, school and department from usersettings
                # was: sel_examyear, sel_school, sel_department, is_locked, \
                #examyear_published, school_activated, is_requsr_school =
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

# - get current grade - when mode is 'create': studsubj is None. It will be created at "elif mode == 'create'"
                examperiod = upload_dict.get('examperiod')
                studsubj_pk = upload_dict.get('studsubj_pk')
                note = upload_dict.get('note')

                file_type = upload_dict.get('file_type')
                file_name = upload_dict.get('file_name')
                file_size = upload_dict.get('file_size')

                studsubj = stud_mod.Studentsubject.objects.get_or_none(
                    id=studsubj_pk,
                    student__school=sel_school,
                    student__department=sel_department
                )

                if logging_on:
                    logger.debug('studsubj: ' + str(studsubj))
                    logger.debug('note: ' + str(note))
                    logger.debug('file_type: ' + str(file_type))
                    logger.debug('file_name: ' + str(file_name))
                    logger.debug('file_size: ' + str(file_size))

# - Create new studsubjnote if is_create:
                # studsubjnote is also called when studsubjnote is_created, save_to_log is called in update_studsubjnote
                if studsubj and (note or file):
                    note_status = upload_dict.get('note_status')

        # if is_internal_note: get schoolbase of request_user, to be put in  intern_schoolbase
                    is_internal_note = upload_dict.get('is_internal_note', False)
                    intern_schoolbase = None
                    if is_internal_note:
                        intern_schoolbase = request.user.schoolbase
                    if logging_on:
                        logger.debug('is_internal_note: ' + str(is_internal_note))
                        logger.debug('intern_schoolbase: ' + str(intern_schoolbase))

                    studsubjnote = stud_mod.Studentsubjectnote(
                        studentsubject=studsubj,
                        note=note,
                        note_status=note_status,
                        intern_schoolbase=intern_schoolbase
                    )
                    if logging_on:
                        logger.debug('studsubjnote.note: ' + str(studsubjnote.note))
                    studsubjnote.save(request=request)

                    if logging_on:
                        logger.debug('studsubjnote.pk: ' + str(studsubjnote.pk))
                        logger.debug('file_type: ' + str(file_type))
                        logger.debug('file_name: ' + str(file_name))
                        logger.debug('file: ' + str(file))

                    # attachments are stored in spaces awpmedia/awpmedia/media/private

# +++ save attachment
                    if studsubjnote and file:
# ---  create file_path
                        # PR2021-08-07 file_dir = 'country/examyear/attachments/'
                        # this one gives path:awpmedia/awpmedia/media/cur/2022/published
                        requsr_school = sch_mod.School.objects.get_or_none(
                            base=request.user.schoolbase,
                            examyear=sel_examyear
                        )
                        requsr_schoolcode = requsr_school.base.code if requsr_school.base.code else '---'
                        country_abbrev = sel_examyear.country.abbrev.lower()
                        examyear_str = str(sel_examyear.code)
                        file_dir = '/'.join((country_abbrev, examyear_str, requsr_schoolcode, 'attachment'))
                        file_path = '/'.join((file_dir, file_name))

                        if logging_on:
                            logger.debug('file_dir: ' + str(file_dir))
                            logger.debug('file_name: ' + str(file_name))
                            logger.debug('filepath: ' + str(file_path))

                        instance = stud_mod.Noteattachment(
                            studentsubjectnote=studsubjnote,
                            contenttype=file_type,
                            filename=file_name,
                        )
                        instance.save()
                        instance.file.save(file_path, file)

                        if logging_on:
                            logger.debug('instance: ' + str(instance))
                            logger.debug('instance.pk: ' + str(instance.pk))

#======================

                    grade_note_icon_rows = grd_view.create_grade_note_icon_rows(
                        sel_examyear_pk=sel_examyear.pk,
                        sel_schoolbase_pk=sel_school.base_id,
                        sel_depbase_pk=sel_department.base_id,
                        sel_examperiod=examperiod,
                        studsubj_pk=studsubj.pk,
                        request=request)
                    if grade_note_icon_rows:
                        update_wrap['grade_note_icon_rows'] = grade_note_icon_rows

# 9. return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=LazyEncoder))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def set_student_instance_tobedeleted(student_instance, request):
    # --- delete student # PR2021-07-18 PR2022-02-16 PR2022-08-05 PR2022-12-27 PR2023-01-16
    # dont delete student when student has submitted subjects, but set tobedeleted
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- set_student_instance_tobedeleted ----- ')
        logger.debug('    student_instance: ' + str(student_instance))

    deleted_row = None
    msg_html = None
    this_txt = _("Candidate '%(tbl)s' ") % {'tbl': student_instance.fullname}

# - check if student has submitted subjects PR2021-08-21 PR2022-05-15
    has_publ_studsubj = stud_mod.Studentsubject.objects.filter(
        student=student_instance,
        subj_published_id__isnull=False
    ).exists()
    if logging_on:
        logger.debug('    has_publ_studsubj: ' + str(has_publ_studsubj))

    if has_publ_studsubj:

# - if student has submitted subjects: mark candidate as 'tobedeleted'
        setattr(student_instance, 'tobedeleted', True)
        student_instance.save(request=request)

    # remove approval and subj_published from studentsubject, add published info to prev_published fields
        updated_studsubj_pk_list, err_html = set_studsubjects_tobedeleted(request, student_instance.pk)
        if err_html:
            msg_html = err_html
        else:
    # mark candidate as 'tobedeleted'
            setattr(student_instance, 'tobedeleted', True)
            student_instance.save(request=request)

    else:
        deleted_row = {'id': student_instance.pk,
                       'mapid': 'student_' + str(student_instance.pk),
                       'deleted': True}
        if logging_on:
            logger.debug('    deleted_row: ' + str(deleted_row))

# - if student doesn't have submitted subjects: mark candidate as 'deleted'
        # also delete studsubj rows (Not necessary, studsub and grades of deletedsudents are filtered out
        err_html = None
        try:
            setattr(student_instance, 'deleted', True)
            setattr(student_instance, 'tobedeleted', False)
            student_instance.save(request=request)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            deleted_row = None

            caption = _('Candidate')
            full_name = stud_fnc.get_full_name(student_instance.lastname, student_instance.firstname, student_instance.prefix)
            err_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                        str(_("%(cpt)s '%(val)s' could not be deleted.") % {'cpt': caption, 'val': full_name})))

        if err_html:
            msg_html = err_html
        if logging_on:
            logger.debug('    deleted_row: ' + str(deleted_row))
            logger.debug('    err_html: ' + str(err_html))

    if logging_on:
        logger.debug('    deleted_row: ' + str(deleted_row))
        logger.debug('    msg_html: ' + str(msg_html))

    return deleted_row, msg_html
# - end of set_student_instance_tobedeleted


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def restore_student_instance(student_instance, request):
    # --- restore student and studsubjects # PR2022-12-28

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- restore_student_instance ----- ')
        logger.debug('    student_instance: ' + str(student_instance))

    restored_student_success = False
    restored_studsubj_pk_list = []
    msg_html = None

    this_txt = _("Candidate '%(tbl)s' ") % {'tbl': student_instance.fullname}

    if student_instance.tobedeleted or student_instance.deleted:

    # resore approval and subj_published from studentsubject, from prev_published fields
        restored_studsubj_pk_list, msg_html = restore_tobedeleted_studsubjects(
            request=request,
            student_pk=student_instance.pk,
            include_deleted=student_instance.deleted,
        )

        if not msg_html:
    # remove 'tobedeleted' from candidate
            try:
                setattr(student_instance, 'tobedeleted', False)
                setattr(student_instance, 'deleted', False)
                student_instance.save(request=request)
                restored_student_success = True

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

                msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                                    str(_("%(cpt)s could not be restored.") % {'cpt':this_txt})))

    if logging_on:
        logger.debug('    restored_student_success: ' + str(restored_student_success))
        logger.debug('    restored_studsubj_pk_list: ' + str(restored_studsubj_pk_list))
        logger.debug('    msg_html: ' + str(msg_html))

    return restored_student_success, restored_studsubj_pk_list , msg_html
# - end of restore_student_instance


def create_or_get_studentbase(country, upload_dict, messages, error_list, skip_save):
    # --- create studentbase  PR2021-07-18
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_or_get_studentbase ----- ')
        logger.debug('upload_dict: ' + str(upload_dict))

    studentbase = None

# - get value of 'studentbase_pk'
    studentbase_pk = upload_dict.get('studentbase_pk')

    try:

# - lookup existing studentbase record
        if studentbase_pk:
            studentbase = stud_mod.Studentbase.objects.get_or_none(pk=studentbase_pk)

# - create studentbase record if it does not exist yet
        if studentbase is None:
            studentbase = stud_mod.Studentbase(
                country=country
        )

# - save studentbase record, only when not is_test
        if not skip_save:
            studentbase.save()

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

        last_name = upload_dict.get('lastname', '')
        first_name = upload_dict.get('firstname', '')
        name = ' '.join((first_name, last_name))
        #  messages is list of dicts with format: {'field': fldName, header': header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html}
        err_01 = str(_('An error occurred:'))
        err_02 = str(e)
        err_03 = str(_("%(cpt)s '%(val)s' could not be added.") % {'cpt': str(_('Candidate')), 'val': name})
        error_list.extend((err_01, err_02, err_03))

        msg_html = '<br>'.join((err_01, '<i>' + err_02 + '</i>', err_03))
        messages.append({'class': "alert-danger", 'msg_html': msg_html})

    if logging_on:
        logger.debug('messages: ' + str(messages))

    return studentbase
# - end of create_or_get_studentbase


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_student_instance(examyear, school, department, idnumber_nodots,
                   lastname_stripped, firstname_stripped, prefix_stripped, full_name,
                    lvlbase_pk, sctbase_pk, request, found_is_error, skip_save):
    # --- create student # PR2019-07-30 PR2020-10-11  PR2020-12-14 PR2021-06-15 PR2022-08-20
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' +++++++++++++++++ create_student +++++++++++++++++ ')
        logger.debug('    school: ' + str(school))
        logger.debug('    department: ' + str(department))

    student = None
    error_list = []
# - create but don't save studentbase
    # save studentbase at the end, to prevent studentbases without student
    studentbase = stud_mod.Studentbase()

    if studentbase and school:
        has_error = False
        error_list = []

        msg_err = av.validate_notblank_maxlength(lastname_stripped, c.MAX_LENGTH_FIRSTLASTNAME, _('The last name'))
        if logging_on:
            logger.debug('    validate_lastname_stripped msg_err: ' + str(msg_err))
        if msg_err:
            has_error = True
            error_list.append(str(msg_err))

        msg_err = av.validate_notblank_maxlength(firstname_stripped, c.MAX_LENGTH_FIRSTLASTNAME, _('The first name'))
        if logging_on:
            logger.debug('    validate_firstname_stripped msg_err: ' + str(msg_err))
        if msg_err:
            has_error = True
            error_list.append(str(msg_err))

# - validate level sector
        msg_lst = av.validate_level_sector_in_student(examyear, school, department, lvlbase_pk, sctbase_pk)
        if logging_on:
            logger.debug('    validate_firstname_stripped msg_lst: ' + str(msg_lst))
        if msg_lst:
            has_error = True
            error_list.extend(msg_lst)

        if not has_error:
# - validate if student already exists
            # either student, not_found or has_error is trueish
            # when importing: dont give error when found, but return found student  error_when_found
            student, not_found, err_str = \
                stud_val.lookup_student_by_idnumber_nodots(
                    school=school,
                    department=department,
                    idnumber_nodots=idnumber_nodots,
                    upload_fullname=full_name,
                    found_is_error=found_is_error
                )
            if err_str:
                has_error = True
                error_list.append(str(err_str))
            if logging_on:
                logger.debug('    lookup_student_by_idnumber_nodots err_list: ' + str(err_str))
                logger.debug('    student: ' + str(student))
                logger.debug('    not_found: ' + str(not_found))
                logger.debug('    has_error: ' + str(has_error))

        if not has_error:

# - make iseveningstudent / islexstudent true when iseveningschool / islexschool, not when also isdayschool
            # PR 2021-09-08 debug tel Lionel Mongen CAL: validation still chekcs for required subjects
            # reason: CAL iseveningschool, but styudents were not set iseveningstudent
            # also solved by checking validation on iseveningstudent only when school is both dayschool and evveningschool,
            # set is_evening_student = True or is_lex_student = True, only when school is not a dayschool (in that case you must select field in mosstudent)
            is_evening_student, is_lex_student = False, False
            if not school.isdayschool:
                is_evening_student = school.iseveningschool
                is_lex_student= school.islexschool

# - save studentbase
            # if studentbase is created but not yet saved: studentbase = True and studentbase.pk = None
            # save studentbase here, to prevent studentbases without student
            if not skip_save and studentbase.pk is None:
               studentbase.save()

            if logging_on:
                logger.debug('    studentbase: ' + str(studentbase))
# - create and save student
            try:
                student = stud_mod.Student(
                    base=studentbase,
                    school=school,
                    department=department,
                    lastname=lastname_stripped,
                    firstname=firstname_stripped,
                    prefix=prefix_stripped,
                    idnumber=idnumber_nodots,
                    iseveningstudent=is_evening_student,
                    islexstudent=is_lex_student
                )
                if logging_on:
                    logger.debug('    student: ' + str(student))
                if not skip_save:
                    student.save(request=request)

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

                error_list.append(''.join((
                    str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                    str(_("%(cpt)s '%(val)s' could not be added.") % {'cpt': _('Candidate'), 'val': full_name})
                )))

    if logging_on:
        student_pk = student.pk if student else 'None'
        logger.debug(' ---student:    ' + str(student))
        logger.debug('    student_pk: ' + str(student_pk))
        logger.debug('    error_list: ' + str(error_list))

    return student, error_list
# - end of create_student


#######################################################
def update_student_instance(instance, sel_examyear, sel_school, sel_department, upload_dict,
                            idnumber_list, examnumber_list, diplomanumber_list, gradelistnumber_list,
                            msg_list, error_list, err_fields, log_list, request, skip_save):
    # --- update existing and new instance PR2019-06-06 PR2021-07-19 PR2022-04-11 PR2022-06-04 PR2022-09-01
    # log_list is only used when uploading students, is None otherwise
    instance_pk = instance.pk if instance else None

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_student_instance -------')
        logger.debug('    upload_dict: ' + str(upload_dict))
        logger.debug('    instance:    ' + str(instance))

    def get_log_txt(caption, new_value, saved_value):
        blank_str = str(_('blank'))
        log_txt = ' = '.join(((caption + c.STRING_SPACE_20)[:20],
                              (str(new_value) if new_value else blank_str)[:20]
                              ))
        if logging_on:
            logger.debug(' ------- get_log_txt -------')
            logger.debug('    caption:     ' + str(caption))
            logger.debug('    new_value:   ' + str(new_value))
            logger.debug('    saved_value: ' + str(saved_value))
            logger.debug('    blank_str:   ' + blank_str)

        if saved_value:
            saved_str = str(saved_value) if saved_value else blank_str
            log_txt += ''.join(('  (', str(_('was')), ': ', saved_str, ')'))
        return log_txt

# ----- get user_lang
    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT

    changes_are_saved = False
    save_error = False
    field_error = False

    # TODO add error fieldname to err_fields, instead of field_error

    if instance:
        save_changes = False
        update_scheme = False
        recalc_regnumber = False
        remove_exemptions = False
        recalc_passed_failed = False
        recalc_subj_composition = False

        for field, new_value in upload_dict.items():
            #try:
            if True:
    # - save changes in fields 'lastname', 'firstname'
                if field in ['lastname', 'firstname']:
                    saved_value = getattr(instance, field)

                    # PR2022-06-29 debug: when value is None it converts it to string 'None'
                    if new_value is not None:
                        if not isinstance(new_value, str):
                            new_value = str(new_value)

                    if new_value != saved_value:
                        if logging_on and False:
                            logger.debug('lastname firstname saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
                            logger.debug('lastname firstname new_value:   ' + str(new_value)+ ' ' + str(type(new_value)))

                        name_first = None
                        name_last = None
                        if field == 'firstname':
                            name_first = new_value
                            name_last = getattr(instance, 'lastname')
                        elif field == 'lastname':
                            name_first = getattr(instance, 'firstname')
                            name_last = new_value
                        # TODO check if student namefirst / namelast combination already exists
                        """
                        field_error = validate_namelast_namefirst(
                            namelast=name_last,
                            namefirst=name_first,
                            company=request.user.company,
                            update_field=field,
                            msg_dict=msg_dict,
                            this_pk=instance.pk)
                        """
                        has_error = False
                        if not has_error:
                            setattr(instance, field, new_value)
                            save_changes = True
                        else:
                            field_error = True

                elif field == 'gender':
                    new_gender = None
                    has_error = False

                    # PR2022-06-29 debug: when value is None it converts it to string 'None'
                    if new_value is not None:
                        if not isinstance(new_value, str):
                            new_value = str(new_value)

                    if new_value:
                        new_gender = new_value[:1].upper()
                        if new_gender == 'F':
                            new_gender = 'V'
                        if new_gender not in ['M', 'V']:
                            has_error = True

                    if has_error:
                        field_error = True
                        err_txt = _("%(cpt)s '%(val)s' is not allowed.") \
                                  % {'cpt': str(_('Gender')), 'val': new_value}
                        error_list.append(err_txt)
                        err_fields.append(field)
                        msg_list.append({'class': "border_bg_warning", 'msg_html': err_txt})
                    else:
                        saved_value = getattr(instance, field)

                        if new_gender != saved_value:
                            if logging_on and False:
                                logger.debug('gender saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
                                logger.debug('gender new_gender:  ' + str(new_gender) + ' ' + str(type(new_gender)))

                            setattr(instance, field, new_gender)
                            save_changes = True
                            recalc_regnumber = True

                elif field == 'idnumber':
                    caption = _('ID-number')
                    err_txt = None
                    class_txt = None

                    # PR2022-06-29 debug: when value is None it converts it to string 'None'
                    if new_value is not None:
                        if not isinstance(new_value, str):
                            new_value = str(new_value)
                    # PR2022-09-01 debug: blank ID number was not giving error, because of 'if new_value'
                    # was:
                    #    if new_value:

            # - remove dots, check if idnumber is correct
                    idnumber_nodots_stripped_lower, msg_err_list, birthdate_dteobj = stud_val.get_idnumber_nodots_stripped_lower(new_value)
                    if msg_err_list:
                        err_txt = ' '.join(msg_err_list)
                        class_txt = c.HTMLCLASS_border_bg_invalid

                    if err_txt is None:
            # check idnumber_already_exists
                        idnumber_already_exists = False
                        idnumber_already_exists_namelist = []

                        # when updating single student, idnumber_list is not filled yet. in that case: get idnumber_list
                        if not idnumber_list:
                            stud_val.get_idnumberlist_from_database(instance.school, idnumber_list)

                        if logging_on :
                            logger.debug('    idnumber_list: ' + str(idnumber_list))

                        if idnumber_list:
                            for row in idnumber_list:
                                # row is a tuple with (id, idnumber, lastname, firstname, prefix), id=0 when instance not saved yet
                                #  (8518, '2000120411', 'Suarez Mendoza', 'Mayra  Alejandra', '')
                                # skip idnumber of this student
                                if instance_pk is None or row[0] != instance_pk:
                                    if row[1] and row[1] == idnumber_nodots_stripped_lower:
                                        idnumber_already_exists = True
                                        idnumber_already_exists_namelist.append(
                                            stud_fnc.get_firstname_prefix_lastname(row[2], row[3], row[4])
                                        )

                        if idnumber_already_exists:
                            class_txt = "border_bg_invalid"
                            err_txt = '<br>'.join((
                                str(_("%(cpt)s '%(val)s' already exists.") % {'cpt': str(caption), 'val': idnumber_nodots_stripped_lower}),
                                str(_("%(cand)s has this ID number.") % {'cand': ', '.join(idnumber_already_exists_namelist)})
                            ))

                        else:
                            # add new_value to idnumber_list if it doesn't exist yet

                            # PR2022-08-22 debug Guribaldi Gouv Lauffer: string index out of range
                            # cause: idnumber_list item is [studenk_pk_int, idnumber_str]
                            # add student_pk as first value, add 0 when new student
                            # was: idnumber_list.append(new_value)

                            if logging_on:
                                logger.debug('    instance_pk: ' + str(instance_pk))
                            if instance_pk is None:
                                idnumber_list.append((0, idnumber_nodots_stripped_lower))
                            if logging_on:
                                logger.debug('    idnumber_list: ' + str(idnumber_list))

                    if err_txt:
                        field_error = True
                        error_list.append(err_txt)
                        err_fields.append(field)
                        msg_list.append({'class': class_txt, 'msg_html': err_txt})
                    else:
                        saved_value = getattr(instance, field)
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True

                elif field == 'examnumber':
                    caption = _('Exam number')
                    err_txt = None
                    class_txt = None

                    # PR2022-06-29 debug: when value is None it converts it to string 'None'
                    if new_value is not None:
                        if not isinstance(new_value, str):
                            new_value = str(new_value)

                    if new_value:
            # check max length
                        new_value = new_value.strip()
                        if len(new_value) > c.MAX_LENGTH_EXAMNUMBER:
                            err_txt = str(_("%(cpt)s '%(val)s' is too long.<br>Maximum %(max)s characters.") \
                                % {'cpt': caption, 'val': new_value, 'max': c.MAX_LENGTH_EXAMNUMBER})
                            class_txt = "border_bg_invalid"

                    if err_txt is None:

            # check examnumber_already_exists
                        examnumber_already_exists = False

                        # PR2022-09-01 Angela Richardson Maris Stella: cannot upload students
                        # error: new_value.lower(): 'NoneType' object has no attribute 'lower'
                        # solved by adding if new_value. new_value is converted sto string above

                        if new_value:
                            # when updating single student, idnumber_list is not filled yet. in that case: get idnumber_list
                            if not examnumber_list:
                                stud_val.get_examnumberlist_from_database(instance.school, instance.department, examnumber_list)

                            if examnumber_list:
                                # examnumber_list:  list of tuples (student_pk, LOWER(examnumber)) [(4445, '201'), (4545, '202'), (4546, '203'), (4547, '204'), (5888, '205'), (4549, '206'), (6016, '207')]
                                 for row in examnumber_list:
                                    # skip exam number of this student
                                    if logging_on:
                                        logger.debug('examnumber_list: ' + str(examnumber_list) + ' ' + str(type(examnumber_list)))
                                        logger.debug('row: ' + str(row) + ' ' + str(type(row)))
                                        logger.debug('row[0]: ' + str(row[0]) + ' ' + str(type(row[0])))
                                        logger.debug('row[1]: ' + str(row[1]) + ' ' + str(type(row[1])))
                                        logger.debug('new_value: ' + str(new_value) + ' ' + str(type(new_value)))

                                    if instance_pk is None or row[0] != instance_pk:
                                        if row[1] and row[1] == new_value.lower():
                                            examnumber_already_exists = True
                                            break

                        if examnumber_already_exists:
                            err_txt = _("%(cpt)s '%(val)s' already exists.")  % {'cpt': str(caption), 'val': new_value}
                            class_txt = "border_bg_warning"
                        else:
            # add new_value to examnumber_list if it doesn't exist yet

                            # PR2022-08-22 debug Guribaldi Gouv Lauffer: string index out of range
                            # cause: examnumber_list item is [studenk_pk_int, examnumber_str]
                            # add student_pk as first value, add 0 when new student
                            # was: examnumber_list.append(new_value)
                            if instance_pk is None:
                                examnumber_list.append((0, new_value))

                        if logging_on and False:
                            logger.debug('    err_txt: ' + str(err_txt))
                            logger.debug(' --------------')

                    if err_txt:
                        field_error = True
                        error_list.append(err_txt)
                        err_fields.append(field)
                        msg_list.append({'class': class_txt, 'msg_html': err_txt})
                    else:
                        saved_value = getattr(instance, field)

                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
                            # TODO to be deprecated
                            recalc_regnumber = True

                elif field in ('diplomanumber', 'gradelistnumber'):
                    caption = str(_('Diploma number')) if field == 'diplomanumber' else str(_('Gradelist number'))
                    err_txt = None
                    class_txt = None

                    # PR2022-06-29 debug: when value is None it converts it to string 'None'
                    if new_value is not None:
                        if not isinstance(new_value, str):
                            new_value = str(new_value)

                    if new_value:
            # - validate length of new_value
                        err_txt = stud_val.validate_length(caption, new_value, c.MAX_LENGTH_EXAMNUMBER, True)  # True = blank_allowed
                        #if err_txt is None:
                            # PR2022-07-04 debug Angela Richardson Maris Stella: cannot enter number, already exists in other level
                            # skip check for double numbers
            # check if new_value already exists in value_list, but skip idnumber of this instance
                            #value_list = diplomanumber_list if field == 'diplomanumber' else gradelistnumber_list

                # when updating single student, value_list is not filled yet. in that case: get diplomanumber_list
                            #if not value_list:
                            #    value_list = stud_val.get_diplomanumberlist_gradelistnumberlist_from_database(field, sel_school)

                            # value_list contains tuples with (id, value), id is needed to skip value of this student
                            #if value_list:
                            #    double_student_id_list = []
                            #    for row in value_list:
                            #        # row is a tuple with (id, value)
                            #        if row[1] == new_value:
                            #            # unsaved instance has id = None
                            #            lookup_id = row[0]
                            #            skip_this_student = False
                            #            saved_id = getattr(instance, 'id')
                            #            if saved_id:
                            #                if saved_id and lookup_id == saved_id:
                            #                    skip_this_student = True
                            #            if not skip_this_student:
                            #                double_student_id_list.append(lookup_id)
                            #
                            #   if double_student_id_list:
                            #        err_txt = _("%(cpt)s '%(val)s' already exists at:") \
                            #                  % {'cpt': str(caption), 'val': new_value}
                            #        class_txt = "border_bg_invalid"
                            #
                            #        for student_id in double_student_id_list:
                            #            stud = stud_mod.Student.objects.get_or_none(pk=student_id)
                            #            if stud:
                            #                full_name = stud_fnc.get_full_name(stud.lastname, stud.firstname, stud.prefix)
                            #                err_txt += '<br> - ' + full_name

                            #if err_txt is None:
                            #    # add new_value to value_list if it doesn't exist yet
                            #    value_list.append(new_value)

            # = put err_txt in error_list
                    if err_txt:
                        field_error = True
                        error_list.append(err_txt)
                        err_fields.append(field)
                        msg_list.append({'class': class_txt, 'msg_html': err_txt})
                    else:
                        saved_value = getattr(instance, field)

                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
                            if log_list is not None:
                                log_list.append(get_log_txt(caption, new_value, saved_value))

    # 2. save changes in birthdate field
                elif field == 'birthdate':
                    # new_value has format of date-iso, Excel ordinal format is already converted
                    saved_dateobj = getattr(instance, field)

                    new_dateobj = af.get_date_from_ISO(new_value)

                    if new_dateobj != saved_dateobj:
                        if logging_on and False:
                            logger.debug('birthdate saved: ' + str(saved_dateobj) + ' ' + str(type(saved_dateobj)))
                            logger.debug('birthdate new  : ' + str(new_dateobj) + ' ' + str(type(new_dateobj)))

                        setattr(instance, field, new_value)
                        save_changes = True

    # 2. save changes in text fields
                elif field in ('prefix', 'birthcountry', 'birthcity', 'classname'):
                    saved_value = getattr(instance, field)

                    # PR2022-06-29 debug: when value is None it converts it to string 'None'
                    if new_value is not None:
                        if not isinstance(new_value, str):
                            new_value = str(new_value)

                    if logging_on and False:
                        logger.debug('field: ' + field + ' saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
                        logger.debug('field: ' + field + ' new_value: ' + str(new_value) + ' ' + str(type(new_value)))

                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True
                        if logging_on and False:
                            logger.debug('save_changes field: ' + field + ' new_value: ' + str(new_value))

    # 3. save changes in department, level or sector
                # department cannot be changed
                # change 'profiel' into 'sector
                elif field in ('level', 'sector', 'profiel'):
                    if field == 'profiel':
                        field = 'sector'

                    #TODO PR2022-07-07 error on CAL and Omega: sector disappears when changing student, then subjects get deleted without deleting grade info
                    if logging_on and False:
                        logger.debug(' >> field: ' + str(field) + ' ' + str(type(field)))
                        logger.debug('    new_value: ' + str(new_value) + ' ' + str(type(new_value)))
                        logger.debug('    old_level: ' + str(getattr(instance, 'level')))
                        logger.debug('    old_sector: ' + str(getattr(instance, 'sector')))
                        logger.debug('    old_scheme: ' + str(getattr(instance, 'scheme')))
                        logger.debug('    old_department: ' + str(getattr(instance, 'department')))

                    new_lvl_or_sct = None
                    school = getattr(instance, 'school')
                    if logging_on and False:
                        logger.debug('    school: ' + str(school) + ' ' + str(type(school)))
                    if school:
                        examyear = getattr(school, 'examyear')
                        if logging_on and False:
                            logger.debug('    examyear: ' + str(examyear) + ' ' + str(type(examyear)))
                        if examyear:
                            if field == 'level':
                                new_lvl_or_sct = subj_mod.Level.objects.get_or_none(
                                    base_id=new_value,
                                    examyear=examyear
                                )
                            elif field == 'sector':
                                new_lvl_or_sct = subj_mod.Sector.objects.get_or_none(
                                    base_id=new_value,
                                    examyear=examyear
                                )

                    saved_lvl_or_sct = getattr(instance, field)
                    if logging_on and False:
                        logger.debug('    new_lvl_or_sct: ' + str(new_lvl_or_sct) + ' ' + str(type(new_lvl_or_sct)))
                        logger.debug('    saved_lvl_or_sct: ' + str(saved_lvl_or_sct) + ' ' + str(type(saved_lvl_or_sct)))

                    # new_value is levelbase_pk or sectorbase_pk
                    if new_lvl_or_sct != saved_lvl_or_sct:
                        if logging_on and False:
                            logger.debug('saved ' + str(field) + ': ' + str(saved_lvl_or_sct) + ' ' + str(type(saved_lvl_or_sct)))
                            logger.debug('new   ' + str(field) + ': ' + str(new_lvl_or_sct) + ' ' + str(type(new_lvl_or_sct)))

                        setattr(instance, field, new_lvl_or_sct)
                        save_changes = True
                        update_scheme = True
                        recalc_subj_composition = True

                        if field == 'level':
                            recalc_regnumber = True

    # - save changes in field 'bis_exam'
                elif field == 'bis_exam':
                    saved_value = getattr(instance, field)
                    if new_value is None:
                        new_value = False
                    # PR2021-08-29 debug: when importing value can be 'x'. Convert to True when not a boolean
                    elif not isinstance(new_value, bool):
                        new_value = True

                    if new_value != saved_value:
                        # check if student has published grades when removing bis_exam
                        # not when it is evening / lex student
                        has_published_exemptions = False
                        if not new_value:
                            is_evelex = False
                            for evelex_field in ('iseveningstudent', 'islexstudent'):
                                if upload_dict.get(evelex_field):
                                    is_evelex = True
                                elif getattr(instance, evelex_field):
                                    is_evelex = True

                            if not is_evelex:
                                has_errorNIU, has_published = stud_val.validate_submitted_locked_grades(
                                    student_pk=instance.pk,
                                    examperiod=c.EXAMPERIOD_EXEMPTION
                                )
                                if has_published:
                                    has_published_exemptions = True
                                    field_error = True
                                    err_txt1 = str(_('This candidate has submitted exemptions.'))
                                    err_txt2 = str(_('The bis-exam cannot be removed.'))
                                    error_list.append(' '.join((err_txt1, err_txt2)))
                                    err_fields.append(field)
                                    msg_list.append({'class': "border_bg_warning", 'msg_html': '<br>'.join((err_txt1, err_txt2))})
                            else:
                                remove_exemptions = True

                        if not has_published_exemptions:
                            setattr(instance, field, new_value)
                            save_changes = True

                elif field == 'withdrawn': # PR2022-06-04
                    if not new_value:
                        new_value = False
                    saved_value = getattr(instance, field) or False
                    if logging_on and False:
                        logger.debug('new_value: ' + str(new_value))
                        logger.debug('saved_value: ' + str(saved_value))
                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True
                        recalc_passed_failed = True

                    # also set result
                        result_index = c.RESULT_WITHDRAWN if new_value else c.RESULT_NORESULT
                        result_status = str(_('Withdrawn')) if new_value else str(_('No result'))
                        setattr(instance, 'result', result_index)
                        setattr(instance, 'result_status', result_status)
                        setattr(instance, 'result_info', None)

    # - save changes in other fields
                elif field in ('iseveningstudent', 'islexstudent', 'partial_exam', 'extrafacilities'):
                    saved_value = getattr(instance, field)
                    if new_value is None:
                        new_value = False
                    # PR2021-08-29 debug: when importing value can be 'x'. Convert to True when not a boolean
                    elif not isinstance(new_value, bool):
                        new_value = True

                    if new_value != saved_value:
                        has_published_exemptions = False
                        # check if student has published grades when removing iseveningstudent', 'islexstudent
                        # not when it is bis_exam
                        if not new_value and field in ('iseveningstudent', 'islexstudent'):
                            is_bisexam = False
                            if upload_dict.get('bis_exam'):
                                is_bisexam = True
                            elif getattr(instance, 'bis_exam'):
                                is_bisexam = True

                            if not is_bisexam:
                                has_errorNIU, has_published = stud_val.validate_submitted_locked_grades(
                                    student_pk=instance.pk,
                                    examperiod=c.EXAMPERIOD_EXEMPTION
                                )
                                if has_published:
                                    has_published_exemptions = True
                                    field_error = True
                                    err_txt1 = str(_('This candidate has submitted exemptions.'))
                                    caption = 'landsexamen candidate' if field == 'islexstudent' else 'evening candidate'
                                    err_txt2 = str(_("The label '%(cpt)s' cannot be removed.") % {'cpt': caption})
                                    error_list.append(' '.join((err_txt1, err_txt2)))
                                    err_fields.append(field)
                                    msg_list.append({'class': "border_bg_warning", 'msg_html': '<br>'.join((err_txt1, err_txt2))})
                                else:
                                    remove_exemptions = True

                        if not has_published_exemptions:
                            setattr(instance, field, new_value)
                            save_changes = True
                            if field in ('iseveningstudent', 'islexstudent', 'partial_exam'):
                                recalc_subj_composition = True

            #except Exception as e:
            #    logger.error(getattr(e, 'message', str(e)))
            #    logger.error('field: ' + str(field) + ' new_value: ' + str(new_value) + ' ' + str(type(new_value)))

# --- end of for loop ---

# - update scheme if level or sector have changed
        if update_scheme:
            department = getattr(instance, 'department')
            level = getattr(instance, 'level')
            sector = getattr(instance, 'sector')
            scheme = subj_mod.Scheme.objects.get_or_none(
                department=department,
                level=level,
                sector=sector)
            setattr(instance, 'scheme', scheme)

            if logging_on and False:
                logger.debug('     dep:    ' + str(department) + ' ' + str(type(department)))
                logger.debug('     new_level:  ' + str(level) + ' ' + str(type(level)))
                logger.debug('     new_sector: ' + str(sector) + ' ' + str(type(sector)))
                logger.debug('     new_scheme: ' + str(scheme) + ' ' + str(type(scheme)))

            if scheme is None:
                msg_arr = []
                if department.level_req:
                    if level is None:
                        msg_arr.append(str(_("The learning path is not entered.")))
                if sector is None:
                    if department.has_profiel:
                        msg_arr.append(str(_("The profile is not entered.")))
                    else:
                        msg_arr.append(str(_("The sector is not entered.")))
                if msg_arr:
                    msg_txt = ' '.join(msg_arr)
                    error_list.append(msg_txt)

    # - update scheme in student instance, also remove scheme if necessary
            # - update scheme in all studsubj of this student
            update_scheme_in_studsubj(instance, request)

# +++ calculate registration number
        if recalc_regnumber:
            school_code, examyear_code, depbase, levelbase, bis_exam = None, None, None, None, False

            school = getattr(instance, 'school')
            if school:
                schoolbase = getattr(school, 'base')
                if schoolbase:
                    school_code = schoolbase.code
                examyear = getattr(school, 'examyear')
                if examyear:
                    examyear_code = examyear.code

            department = getattr(instance, 'department')
            if department:
                depbase = getattr(department, 'base')

            level = getattr(instance, 'level')
            if level:
                levelbase = getattr(level, 'base')

            gender = getattr(instance, 'gender')
            examnumber = getattr(instance, 'examnumber')

    # - create examnumber if it does not yet exist
            if examnumber is None:
                # get highest examnumber + 1
                examnumber = stud_fnc.get_next_examnumber(school, department)
                setattr(instance, 'examnumber', examnumber)
                save_changes = True
                if logging_on:
                    logger.debug('setattr(instance, examnumber, examnumber: ' + str(examnumber))

    # - calc_regnumber
            bis_exam = getattr(instance, 'bis_exam') or False
            depbase_code = depbase.code if depbase else None
            levelbase_code = levelbase.code if levelbase else None

            new_regnumber = stud_fnc.calc_regnumber(
                school_code=school_code,
                gender=gender,
                examyear_str=str(examyear_code),
                examnumber_str=examnumber,
                depbase_code=depbase_code,
                levelbase_code=levelbase_code,
                bis_exam=bis_exam
            )

            if logging_on:
                logger.debug('recalc_regnumber: ')
                logger.debug('level:      ' + str(level))
                logger.debug('gender:     ' + str(gender))
                logger.debug('examnumber:     ' + str(examnumber))
                logger.debug('new_regnumber:     ' + str(new_regnumber))

            saved_value = getattr(instance, 'regnumber')
            if new_regnumber != saved_value:
                setattr(instance, 'regnumber', new_regnumber)
                save_changes = True
                if logging_on:
                    logger.debug('setattr(instance, regnumber, new_regnumber: ' + str(new_regnumber))

# 5. save changes
        if save_changes:

    # update subj_composition_checked and subj_composition_ok when recalc_subj_composition PR2022-08-30
            if recalc_subj_composition:
                # validate_studentsubjects_no_msg returns True when there is an error
                no_error = not stud_val.validate_studentsubjects_no_msg(instance, 'nl')
                if (not instance.subj_composition_checked) or \
                    (instance.subj_composition_checked and instance.subj_composition_ok != no_error):
                    setattr(instance, 'subj_composition_checked', True)
                    setattr(instance, 'subj_composition_ok', no_error)

            try:
                if not skip_save:
                    instance.save(request=request)
                if logging_on:
                    logger.debug('..............skip_save: ' + str(skip_save))
                    logger.debug('after saving: instance.pk: ' + str(instance.pk))
                    logger.debug('after saving: instance.level: ' + str(instance.level))
                    logger.debug('after saving: instance.sector: ' + str(instance.sector))
                    logger.debug('after saving: instance.scheme: ' + str(instance.scheme))
                changes_are_saved = True
            except Exception as e:
                save_error = True
                err_txt1 = str(_('An error occurred'))
                err_txt2 = str(e)
                err_txt3 = str(_("The changes have not been saved."))
                error_list.append(''.join((err_txt1, ': ', err_txt2)))

                msg_html = ''.join((err_txt1, ': ', '<br><i>', err_txt2, '</i><br>',err_txt3))
                msg_dict = {'header': str(_('Save changes')), 'class': 'border_bg_invalid', 'msg_html': msg_html}
                msg_list.append(msg_dict)

                logger.error(getattr(e, 'message', str(e)))

        if instance and changes_are_saved:
            if remove_exemptions:
                if logging_on:
                    logger.debug(' --- remove_exemptions --- ')
                # get exemptions of this student
                # check for published exemptions is already done above.
                # PR2022-04-11 Richard Westerink ATC: eveningstudent may have exemptions.
                # Don't remove exemptions when iseveningstudent or islexstudent
                if not instance.bis_exam and not instance.iseveningstudent and not instance.islexstudent:
                    if student_has_exemptions(instance.pk):
                        recalc_studsubj_and_student = delete_exemptions(instance.pk)
                        # TODO recalc_studsubj_and_student

                        sql_studsubj_list, sql_student_list = \
                            grd_view.update_studsubj_and_recalc_student_result(
                                sel_examyear=sel_examyear,
                                sel_school=sel_school,
                                sel_department=sel_department,
                                student=instance)
                        if sql_studsubj_list:
                            calc_res.save_studsubj_batch(sql_studsubj_list)

                        #if recalc_studsubj_and_student:
                        #    calc_res.calc_student_result(examyear, department, student_dict, scheme_dict,
                        #                                 schemeitems_dict, log_list,
                        #                    sql_studsubj_list, sql_student_list)

            if recalc_passed_failed:
                sel_lvlbase_pk = instance.level.base_id if instance.level else None
                calc_res.calc_batch_student_result(
                    sel_examyear=sel_examyear,
                    sel_school=sel_school,
                    sel_department=sel_department,
                    student_pk_list=[instance.pk],
                    sel_lvlbase_pk=sel_lvlbase_pk,
                    user_lang=user_lang
                )


    if logging_on:
        logger.debug('changes_are_saved: ' + str(changes_are_saved))
        logger.debug('field_error: ' + str(field_error))
        logger.debug('error_list: ' + str(error_list))
        logger.debug('err_fields: ' + str(err_fields))

    return changes_are_saved, save_error, field_error
# - end of update_student_instance


def student_has_exemptions(student_pk):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --- student_has_exemptions --- ')

    # check if student has exemptions

    has_exemptions = False
    if student_pk:
        try:
            # check if exemptions exist
            sql_keys = {'stud_id': student_pk}
            sql_list = [
                "SELECT grd_id",
                "FROM students_grade AS grd",
                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                "WHERE studsubj.student_id = %(stud_id)s::INT)",
                "AND grd.examperiod = ", str(c.EXAMPERIOD_EXEMPTION),
                "LIMIT 1;"
            ]
            sql = ' '.join(sql_list)
            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = cursor.fetchall()
                has_exemptions = len(rows)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return has_exemptions


def delete_exemptions(student_pk):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --- delete_exemptions --- ')

    # check if student has exemptions
    recalc_studsubj_and_student = False
    if student_pk:
        try:
            # check if exemptions exist
            sql_keys = {'stud_id': student_pk}
            sql_list = [
                "DELETE FROM students_grade AS grd",
                "WHERE grd.examperiod = 4",
                "AND EXISTS (SELECT * FROM students_studentsubject AS studsubj",
                "WHERE studsubj.id = grd.studentsubject_id",
                "AND studsubj.student_id = %(stud_id)s::INT)",
                "RETURNING grd.id;"
            ]
            sql = ' '.join(sql_list)
            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                # return list of updated grades, to calculate final grades
                rows = cursor.fetchall()
                if len(rows):
                    recalc_studsubj_and_student = True

                # TODO recalc_studsubj_and_student
            # remove 'has_exemption' and 'exemption_year' from students_studentsubject
            sql_list = ["UPDATE students_studentsubject AS studsubj",
                        "SET has_exemption=False, exemption_year=NULL"
                        "WHERE studsubj.student_id = %(stud_id)s::INT)",
                        ]
            sql = ' '.join(sql_list)
            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)

                for row in cursor.fetchall():
                    logger.debug('row: ' + str(row))


            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                # return list of updated grades, to calculate final grades

                for row in cursor.fetchall():
                    logger.debug('row: ' + str(row))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return recalc_studsubj_and_student


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def update_scheme_in_studsubj(student, request):
    # --- update_scheme_in_studsubj # PR2021-03-13 PR2022-07-10
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_scheme_in_studsubj ----- ')
        logger.debug('     student: ' + str(student))
    # TOD add 'is_test' and log_file before uopdating scheme
    if student:
        # - update scheme in student, also remove if necessary
        new_scheme = subj_mod.Scheme.objects.get_or_none(
            department=student.department,
            level=student.level,
            sector=student.sector)
        setattr(student, 'scheme', new_scheme)

        if logging_on:
            logger.debug('     new_scheme: ' + str(new_scheme))

        # PR2022-05-18 CAL, Omega: all subjects disappear.
        # Cause: tobedeleted is set True. Dont know why yet

        # delete studsubj when no scheme
        # check if studsubj is submitted, set tobedeleted = True if submitted
        # PR2022-05-18 debug: Omega College: grades have disappeared
        # TODO instead of deleting studsubj: prevent making changes PR2022-07-10
        # TODO delete or change exam in grades when changing level

        if new_scheme:
    # - loop through studsubj of this student
            studsubjects = stud_mod.Studentsubject.objects.filter(
                student=student
            )
            for studsubj in studsubjects:
                old_subject = studsubj.schemeitem.subject
                old_subjecttype = studsubj.schemeitem.subjecttype

                if logging_on:
                    logger.debug('....old_subject: ' + str(old_subject))
                    logger.debug('    old_subjecttype: ' + str(old_subjecttype))

        # skip when studsub scheme equals new_scheme
                if studsubj.schemeitem.scheme != new_scheme:
                    save_studsubj = False

            # check id studsubj is already approved or submitted
                    studsubj_is_submitted = studsubj.subj_published is not None
                    studsubj_is_approved = False
                    if not studsubj_is_submitted:
                        studsubj_is_approved = studsubj.subj_auth1by is not None or studsubj.subj_auth2by is not None

        # check how many times this subject occurs in new scheme
                    count_subject_in_newscheme = subj_mod.Schemeitem.objects.filter(
                        scheme=new_scheme,
                        subject=old_subject
                        ).count()
                    if logging_on:
                        logger.debug('    count_subject_in_newscheme: ' + str(count_subject_in_newscheme))

                    if not count_subject_in_newscheme:
        # delete studsub when subject does not exist in new_scheme
                        # check if studsubj is submitted, set tobedeleted = True if submitted
                        # was: set_studsubj_tobedeleted_or_tobechanged(studsubj, True, None, request)  # True = tobedeleted
                        setattr(studsubj, 'tobedeleted', True)
                        save_studsubj = True
                        if logging_on:
                            logger.debug('    count = 0 > set deleted = True')

                    elif count_subject_in_newscheme == 1:
        # if subject occurs only once in new_scheme: replace schemeitem by new schemeitem
                        new_schemeitem = subj_mod.Schemeitem.objects.get_or_none(
                            scheme=new_scheme,
                            subject=old_subject
                        )
                        if new_schemeitem:
                            # change schemeitem in studsubj, set tobechanged = True if submitted
                            # was: set_studsubj_tobedeleted_or_tobechanged(studsubj, False, new_schemeitem, request)  # False = tobechanged
                            setattr(studsubj, 'schemeitem', new_schemeitem)
                            save_studsubj = True

                            if logging_on:
                                logger.debug('    count = 1 > setattr = new_schemeitem')
                                logger.debug('    new_subjecttype: ' + str(new_schemeitem.subjecttype))
                    else:
        # if subject occurs multiple times in new_scheme: check if one exist with same subjecttype
                        new_schemeitem = subj_mod.Schemeitem.objects.get_or_none(
                            scheme=new_scheme,
                            subject=old_subject,
                            subjecttype=old_subjecttype
                        )
                        if new_schemeitem:
                            studsubj.schemeitem = new_schemeitem
                            save_studsubj = True
                        else:
        # if no schemeitem exist with same subjecttype: get schemeitem with lowest sequence
                            new_schemeitem = subj_mod.Schemeitem.objects.filter(
                                scheme=new_scheme,
                                subject=studsubj.schemeitem.subject
                            ).order_by('subjecttype__base__sequence').first()
                            if new_schemeitem:
                                studsubj.schemeitem = new_schemeitem
                                save_studsubj = True
                                if logging_on:
                                    logger.debug('    count = 1 > setattr = new_schemeitem')
                                    logger.debug('    new_subjecttype: ' + str(new_schemeitem.subjecttype))
                    if save_studsubj:
                        studsubj.save(request=request)
# end of update_scheme_in_studsubj


def set_studsubjects_tobedeleted(request, student_pk, set_deleted=False, studsubj_pk=None):
    # PR2021-08-23 PR2022-12-28
    # delete studsubj when no scheme > PR2022-07-10 don't, instead: prevent changes when no scheme
    # check if studsubj is submitted, set tobedeleted = True if submitted
    # called by  update_scheme_in_studsubj 3 times

    # PR2022-05-18 CAL, Omega: all subjects disappear.
    # Cause: tobedeleted is set True. Dont know why yet

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- set_studsubjects_tobedeleted ----- ')
        logger.debug('    student_pk: ' + str(student_pk))
        logger.debug('    studsubj_pk: ' + str(studsubj_pk))

    msg_html = None
    updated_studsubj_pk_list = []

    if student_pk:
        try:
            modifiedby_pk_str = str(request.user.pk)
            modifiedat_str = str(timezone.now())

            # store subj_auth and subj_published info in prev_auth and prev_published fields
            # set subj_auth and subj_published to NULL
            # set tobedeleted= True, update modified

            # when set_deleted = True: set deleted, otherwise: set tobedeleted
            set_deleted_str = "deleted=TRUE, tobedeleted=False, " if set_deleted else "tobedeleted=TRUE, "
            deleted_clause_str = "AND NOT deleted " if set_deleted else "AND NOT tobedeleted AND NOT deleted "

            sql_keys = {'stud_id': student_pk}
            sql_list = ["UPDATE students_studentsubject AS studsubj ",
                        "SET prev_auth1by_id=subj_auth1by_id, ",
                            "prev_auth2by_id=subj_auth2by_id, ",
                            "prev_published_id=subj_published_id, ",
                            "subj_auth1by_id=NULL, subj_auth2by_id=NULL, subj_published_id=NULL, ",
                            set_deleted_str,
                            "modifiedby_id=", modifiedby_pk_str, ", modifiedat='", modifiedat_str, "' ",
                        "WHERE studsubj.student_id = %(stud_id)s::INT ",
                        deleted_clause_str,
                        ]

            if studsubj_pk:
                sql_keys['studsubj_id'] = studsubj_pk
                sql_list.append("AND id = %(studsubj_id)s::INT ")

            sql_list.append("RETURNING studsubj.id;")

            sql = ''.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                updated_rows = cursor.fetchall()
                if updated_rows:
                    for row in updated_rows:
                        updated_studsubj_pk_list.append(row[0])

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                                str(_("%(cpt)s could not be restored.") % {'cpt': _('This candidate')})))

    return updated_studsubj_pk_list, msg_html
# - end of set_studsubjects_tobedeleted


def restore_tobedeleted_studsubjects(request, student_pk, studsubj_pk=None, include_deleted=False):
    # PR2022-12-28 PR2023-01-14

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- restore_tobedeleted_studsubjects ----- ')
        logger.debug('    student_pk: ' + str(student_pk))
        logger.debug('    studsubj_pk: ' + str(studsubj_pk))

    msg_html = None
    updated_studsubj_pk_list = []

    if student_pk:
        try:
            modifiedby_pk_str = str(request.user.pk)
            modifiedat_str = str(timezone.now())

            # restore subj_auth and subj_published info from prev_auth and prev_published fields
            # set tobedeleted= False, update modified

            sql_keys = {'stud_id': student_pk}
            sql_list = ["UPDATE students_studentsubject AS studsubj ",
                        "SET subj_auth1by_id=prev_auth1by_id, ",
                            "subj_auth2by_id=prev_auth2by_id, ",
                            "subj_published_id=prev_published_id, ",
                            "tobedeleted=FALSE, ",
                            "modifiedby_id=", modifiedby_pk_str, ", modifiedat='", modifiedat_str, "' ",
                        "WHERE studsubj.student_id = %(stud_id)s::INT AND tobedeleted ",
                        ]

            if not include_deleted:
                sql_list.append("AND NOT deleted ")

            if studsubj_pk:
                sql_keys['studsubj_id'] = studsubj_pk
                sql_list.append("AND id = %(studsubj_id)s::INT ")

            sql_list.append("RETURNING studsubj.id;")

            sql = ''.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                updated_rows = cursor.fetchall()
                if updated_rows:
                    for row in updated_rows:
                        updated_studsubj_pk_list.append(row[0])

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                                str(_("%(cpt)s could not be restored.") % {'cpt': _('This candidate')})))

    if logging_on:
        logger.debug('    updated_studsubj_pk_list: ' + str(updated_studsubj_pk_list))
        logger.debug('    msg_html: ' + str(msg_html))

    return updated_studsubj_pk_list, msg_html
# end of restore_tobedeleted_studsubjects


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_studsubj(student, schemeitem, messages, error_list, request, skip_save):
    # --- create student subject # PR2020-11-21 PR2021-07-21 PR2023-01-02
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_studsubj ----- ')
        logger.debug('    student: ' + str(student))
        logger.debug('    schemeitem: ' + str(schemeitem))

    has_error = False
    studsubj_instance = None
    append_key = None

    if student and schemeitem:
        subject_name = schemeitem.subject.name_nl if schemeitem.subject and schemeitem.subject.name_nl else '---'

# - check if student already has this subject (should be not more than one)
        studsubj_instance = stud_mod.Studentsubject.objects.filter(
            student=student,
            schemeitem__subject=schemeitem.subject
        ).first()

        if logging_on:
            logger.debug('    subject_name: ' + str(subject_name))
            logger.debug('    studsubj_instance: ' + str(studsubj_instance))

        if studsubj_instance:
# +++ if studsubj is not tobedeleted and not deleted:
            if not studsubj_instance.deleted and not studsubj_instance.tobedeleted:

                if logging_on:
                    logger.debug('    studsubj_instance.tobedeleted: ' + str(studsubj_instance.tobedeleted))
                    logger.debug('    studsubj_instance.deleted: ' + str(studsubj_instance.deleted))

                #has_error = True
                #err_01 = str(_("%(cpt)s '%(val)s' already exists.") % {'cpt': _('Subject'), 'val': subject_name})
                ## error_list not in use when using modal form, message is displayed in modmessages
                #error_list.append(err_01)

                ## this one closes modal and shows modmessage with msg_html
                #msg_dict = {'header': _('Add subject'), 'class': 'border_bg_warning', 'msg_html': err_01}
                #messages.append(msg_dict)

                if schemeitem != studsubj_instance.schemeitem:
                    try:
                        # set schemeitem
                        setattr(studsubj_instance, 'schemeitem', schemeitem)
                        setattr(studsubj_instance, 'tobechanged', True)

                        setattr(studsubj_instance, 'prev_auth1by_id', None)
                        setattr(studsubj_instance, 'prev_auth2by_id', None)
                        setattr(studsubj_instance, 'prev_published_id', None)

                        setattr(studsubj_instance, 'subj_auth1by_id', None)
                        setattr(studsubj_instance, 'subj_auth2by_id', None)
                        setattr(studsubj_instance, 'subj_published_id', None)

                        append_key = 'changed'

                        if not skip_save:
                            studsubj_instance.save(request=request)

                    except Exception as e:
                        has_error = True
                        logger.error(getattr(e, 'message', str(e)))
                        # error_list not in use when using modal form, message is displayed in modmesages
                        err_01 = str(_('An error occurred:'))
                        err_02 = str(e)
                        err_03 = str(_("%(cpt)s '%(val)s' could not be changed.") % {'cpt': str(_('Subject')),
                                                                                   'val': subject_name})
                        error_list.extend((err_01, err_02, err_03))

                        # this one closes modal and shows modmessage with msg_html
                        msg_html = '<br>'.join((err_01, '<i>' + err_02 + '</i>', err_03))
                        messages.append({'class': "alert-danger", 'msg_html': msg_html})

            else:
 # +++ subject is found but is tobedeleted or deleted
                try:
                    if studsubj_instance.deleted:
                        # subject is deleted > remove deleted, remove prev_published, remove published
                        setattr(studsubj_instance, 'deleted', False)
                        setattr(studsubj_instance, 'tobedeleted', False)

                        setattr(studsubj_instance, 'prev_auth1by_id', None)
                        setattr(studsubj_instance, 'prev_auth2by_id', None)
                        setattr(studsubj_instance, 'prev_published_id', None)

                        setattr(studsubj_instance, 'subj_auth1by_id', None)
                        setattr(studsubj_instance, 'subj_auth2by_id', None)
                        setattr(studsubj_instance, 'subj_published_id', None)

                        # set schemeitem
                        setattr(studsubj_instance, 'schemeitem', schemeitem)

                        append_key = 'created'

                    elif studsubj_instance.tobedeleted:
                        if schemeitem == studsubj_instance.schemeitem:
                        # if new studsubj has same schemeitem as tobedeleted one
                        # if studsubject is tobedeleted > restore studsubject: remove tobedeleted, restore published, remove prev_published (should be None already)
                            setattr(studsubj_instance, 'deleted', False)
                            setattr(studsubj_instance, 'tobedeleted', False)

                            setattr(studsubj_instance, 'subj_auth1by_id',getattr(studsubj_instance, 'prev_auth1by_id', None))
                            setattr(studsubj_instance, 'subj_auth2by_id',getattr(studsubj_instance, 'prev_auth2by_id', None))
                            setattr(studsubj_instance, 'subj_published_id',getattr(studsubj_instance, 'prev_published_id', None))

                            setattr(studsubj_instance, 'prev_auth1by_id', None)
                            setattr(studsubj_instance, 'prev_auth2by_id', None)
                            setattr(studsubj_instance, 'prev_published_id', None)

                        else:
                    # if new studsubj has different schemeitem as tobedeleted one:
                    # if studsubject is tobedeleted > remove tobedeleted, set schemeitem, keep prevpublished , remove published (should be None already)

                            setattr(studsubj_instance, 'tobechanged', True)

                            setattr(studsubj_instance, 'deleted', False)
                            setattr(studsubj_instance, 'tobedeleted', False)

                            setattr(studsubj_instance, 'subj_auth1by_id', None)
                            setattr(studsubj_instance, 'subj_auth2by_id', None)
                            setattr(studsubj_instance, 'subj_published_id', None)

                    # set schemeitem
                            setattr(studsubj_instance, 'schemeitem', schemeitem)

                        append_key = 'restored'

                    if not skip_save:
                        studsubj_instance.save(request=request)

        # +++++ also undelete grades
                    # PR2023-02-12 grades are only set tobedeleted or deleted when exem. reex or reex03
                    #  restore previously deleted grades with ep=1
                        crit = Q(studentsubject=studsubj_instance) & \
                               Q(examperiod=c.EXAMPERIOD_FIRST) & \
                               (Q(tobedeleted=True) | Q(deleted=True))
                        grades = stud_mod.Grade.objects.filter(crit)

                        if grades:
                            for grade in grades:
                                setattr(grade, 'tobedeleted', False)
                                setattr(grade, 'deleted', False)
                                if not skip_save:
                                    grade.save(request=request)

                except Exception as e:
                    has_error = True
                    logger.error(getattr(e, 'message', str(e)))
                    # error_list not in use when using modal form, message is displayed in modmesasges
                    err_01 = str(_('An error occurred:'))
                    err_02 = str(e)
                    err_03 = str(_("%(cpt)s '%(val)s' could not be added.") % {'cpt': str(_('Subject')),
                                                                               'val': subject_name})
                    error_list.extend((err_01, err_02, err_03))

                    # this one closes modal and shows modmessage with msg_html
                    msg_html = '<br>'.join((err_01, '<i>' + err_02 + '</i>', err_03))
                    messages.append({'class': "alert-danger", 'msg_html': msg_html})

# +++++ if studsubj_instance is None: create and save Studentsubject
        else:
            try:
                studsubj_instance = stud_mod.Studentsubject(
                    student=student,
                    schemeitem=schemeitem
                )
                if not skip_save:
                    studsubj_instance.save(request=request)

        # - also create grade of first examperiod
                grade = stud_mod.Grade(
                    studentsubject=studsubj_instance,
                    examperiod=c.EXAMPERIOD_FIRST
                )
                if not skip_save:
                    grade.save(request=request)
                append_key = 'created'

            except Exception as e:
                has_error = True
                logger.error(getattr(e, 'message', str(e)))

                # error_list not in use when using modal form, message is displayed in modmesasges
                err_01 = str(_('An error occurred:'))
                err_02 = str(e)
                err_03 = str(_("%(cpt)s '%(val)s' could not be added.") % {'cpt': str(_('Subject')), 'val': subject_name})
                error_list.extend((err_01, err_02, err_03))

                # this one closes modal and shows modmessage with msg_html
                msg_html = '<br>'.join((err_01, '<i>' + err_02 + '</i>', err_03))
                messages.append({'class': "alert-danger", 'msg_html': msg_html})

        if has_error:
            studsubj_instance = None

    if logging_on:
        logger.debug('    studsubj_instance: ' + str(studsubj_instance))
        logger.debug('    append_key: ' + str(append_key))

    return studsubj_instance, append_key
# - end of create_studsubj


#/////////////////////////////////////////////////////////////////

def create_studentsubject_rows(sel_examyear, sel_schoolbase, sel_depbase, append_dict, request,
                               requsr_same_school=False, sel_lvlbase=None, student_pk=None,
                               studsubj_pk_list=None, cluster_pk_list=None):
    # --- create rows of all students of this examyear / school / dep PR2020-10-27 PR2022-01-10 studsubj_pk_list added
    # PR2022-02-15 show only not tobeleted students and studentsubjects
    # PR2022-03-23 cluster_pk_list added, to return studsubj with changed clustername
    # PR2022-12-16 allowed filter renewed
    # PR2023-04-18 Sentry error fixed: syntax error at or near ")" LINE 1: ...cluster_id IN (SELECT UNNEST(ARRAY[1465]::INT[])) ) ORDER BY...
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' =============== create_studentsubject_rows ============= ')
        logger.debug('     student_pk: ' + str(student_pk))
        logger.debug('     sel_schoolbase: ' + str(sel_schoolbase))
        logger.debug('     sel_depbase: ' + str(sel_depbase))
        logger.debug('     sel_lvlbase: ' + str(sel_lvlbase))
        logger.debug('     requsr_same_school: ' + str(requsr_same_school))
        logger.debug('     studsubj_pk_list: ' + str(studsubj_pk_list))
        logger.debug('     append_dict: ' + str(append_dict))
        logger.debug('     cluster_pk_list: ' + str(cluster_pk_list))
        logger.debug('     ......................... ')

    rows = []
    try:
        # create list of students of this school / examyear, possibly with filter student_pk or studsubj_pk
        # with left join of studentsubjects with deleted=False
        # when role is other than school: only when submitted, don't show students without submitted subjects
        sel_examyear_pk = sel_examyear.pk if sel_examyear else None
        sel_schoolbase_pk = sel_schoolbase.pk if sel_schoolbase else None
        sel_depbase_pk = sel_depbase.pk if sel_depbase else None
        sel_lvlbase_pk = sel_lvlbase.pk if sel_lvlbase else None

    # - get selected sctbase_pk of req_usr
        selected_pk_dict = acc_prm.get_selected_pk_dict_of_user_instance(request.user)
        sel_sctbase_pk = selected_pk_dict.get(c.KEY_SEL_SCTBASE_PK) if selected_pk_dict else None

    # - get allowed_sections_dict from request
        userallowed_instance = acc_prm.get_userallowed_instance_from_request(request)

        userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
        if logging_on:
            logger.debug(
                '    allowed_sections_dict: ' + str(userallowed_sections_dict) + ' ' + str(
                    type(userallowed_sections_dict)))
            # allowed_sections_dict: {'2': {'1': {'4': [117, 114], '5': [], '-9': [118, 121]}}} <class 'dict'>

        # dont show students without subject on other users than sameschool
        #PR2022-01-10 also use inner join when studsubj_pk_list has values: only these records must be returned
        #left_or_inner_join = "LEFT JOIN" if requsr_same_school and not studsubj_pk_list else "INNER JOIN"
        left_or_inner_join = "LEFT JOIN"

        sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk, 'db_id': sel_depbase_pk}
        sql_studsubj_list = ["SELECT studsubj.id AS studsubj_id, studsubj.student_id,",
            "cl.id AS cluster_id, cl.name AS cluster_name, si.id AS schemeitem_id, si.scheme_id AS scheme_id,",
            "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_thumbrule,",
            "studsubj.pws_title, studsubj.pws_subjects,",
            "studsubj.has_exemption, studsubj.has_sr, studsubj.has_reex, studsubj.has_reex03, studsubj.exemption_year, studsubj.pok_validthru,",
            "si.subject_id, si.subjecttype_id, si.gradetype,",
            "subjbase.id AS subjbase_id, subjbase.code AS subj_code, subj.name_nl AS subj_name_nl,",
            "si.weight_se, si.weight_ce,",
            "si.is_mandatory, si.is_mand_subj_id, si.is_combi, si.extra_count_allowed, si.extra_nocount_allowed,",
            "si.has_practexam,",

            "sjt.id AS sjtp_id, sjt.abbrev AS sjtp_abbrev, sjt.has_prac AS sjtp_has_prac, sjt.has_pws AS sjtp_has_pws,",
            "sjtbase.sequence AS sjtbase_sequence,",

            "studsubj.subj_auth1by_id, subj_auth1.last_name AS subj_auth1_usr,",
            "studsubj.subj_auth2by_id , subj_auth2.last_name AS subj_auth2_usr,",
            "studsubj.subj_published_id, subj_published.modifiedat AS subj_publ_modat,",

            "studsubj.exem_auth1by_id , exem_auth1.last_name AS exem_auth1_usr,",
            "studsubj.exem_auth2by_id, exem_auth2.last_name AS exem_auth2_usr,",
            "studsubj.exem_published_id, exem_published.modifiedat AS exem_publ_modat,",

            "studsubj.sr_auth1by_id AS sr_auth1by_id, sr_auth1.last_name AS sr_auth1_usr,",
            "studsubj.sr_auth2by_id AS sr_auth2by_id, sr_auth2.last_name AS sr_auth2_usr,",
            "studsubj.sr_published_id, sr_published.modifiedat AS sr_publ_modat,",

            "studsubj.reex_auth1by_id, reex_auth1.last_name AS reex_auth1_usr,",
            "studsubj.reex_auth2by_id, reex_auth2.last_name AS reex_auth2_usr,",
            "studsubj.reex_published_id, reex_published.modifiedat AS reex_publ_modat,",

            "studsubj.reex3_auth1by_id, reex3_auth1.last_name AS reex3_auth1_usr,",
            "studsubj.reex3_auth2by_id, reex3_auth2.last_name AS reex3_auth2_usr,",
            "studsubj.reex3_published_id, reex3_published.modifiedat AS reex3_publ_modat,",

            "studsubj.pok_auth1by_id, pok_auth1.last_name AS pok_auth1_usr,",
            "studsubj.pok_auth2by_id, pok_auth2.last_name AS pok_auth2_usr,",
            "studsubj.pok_published_id, pok_published.modifiedat AS pok_publ_modat,",

            "studsubj.tobedeleted, studsubj.modifiedby_id, studsubj.modifiedat,",
            "au.last_name AS modby_username",

            "FROM students_studentsubject AS studsubj",

            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
            "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
            "LEFT JOIN subjects_subjecttype AS sjt ON (sjt.id = si.subjecttype_id)",
            "INNER JOIN subjects_subjecttypebase AS sjtbase ON (sjtbase.id = sjt.base_id)",

            "LEFT JOIN subjects_cluster AS cl ON (cl.id = studsubj.cluster_id)",

            "LEFT JOIN accounts_user AS au ON (au.id = studsubj.modifiedby_id)",

            "LEFT JOIN accounts_user AS subj_auth1 ON (subj_auth1.id = studsubj.subj_auth1by_id)",
            "LEFT JOIN accounts_user AS subj_auth2 ON (subj_auth2.id = studsubj.subj_auth2by_id)",
            "LEFT JOIN schools_published AS subj_published ON (subj_published.id = studsubj.subj_published_id)",

            "LEFT JOIN accounts_user AS exem_auth1 ON (exem_auth1.id = studsubj.exem_auth1by_id)",
            "LEFT JOIN accounts_user AS exem_auth2 ON (exem_auth2.id = studsubj.exem_auth2by_id)",
            "LEFT JOIN schools_published AS exem_published ON (exem_published.id = studsubj.exem_published_id)",

            "LEFT JOIN accounts_user AS sr_auth1 ON (sr_auth1.id = studsubj.sr_auth1by_id)",
            "LEFT JOIN accounts_user AS sr_auth2 ON (sr_auth2.id = studsubj.sr_auth2by_id)",
            "LEFT JOIN schools_published AS sr_published ON (sr_published.id = studsubj.sr_published_id)",

            "LEFT JOIN accounts_user AS reex_auth1 ON (reex_auth1.id = studsubj.reex_auth1by_id)",
            "LEFT JOIN accounts_user AS reex_auth2 ON (reex_auth2.id = studsubj.reex_auth2by_id)",
            "LEFT JOIN schools_published AS reex_published ON (reex_published.id = studsubj.reex_published_id)",

            "LEFT JOIN accounts_user AS reex3_auth1 ON (reex3_auth1.id = studsubj.reex3_auth1by_id)",
            "LEFT JOIN accounts_user AS reex3_auth2 ON (reex3_auth2.id = studsubj.reex3_auth2by_id)",
            "LEFT JOIN schools_published AS reex3_published ON (reex3_published.id = studsubj.reex3_published_id)",

            "LEFT JOIN accounts_user AS pok_auth1 ON (pok_auth1.id = studsubj.pok_auth1by_id)",
            "LEFT JOIN accounts_user AS pok_auth2 ON (pok_auth2.id = studsubj.pok_auth2by_id)",
            "LEFT JOIN schools_published AS pok_published ON (pok_published.id = studsubj.pok_published_id)",

            "WHERE NOT stud.deleted AND NOT studsubj.deleted"

            # PR2022-12-26 show tobedelted records only when they are not submitted yet
            # "WHERE NOT studsubj.tobedeleted"
            #"WHERE ( NOT studsubj.tobedeleted OR (studsubj.tobedeleted AND studsubj.subj_published_id IS NULL) )"
            ]

        # studsubj are only visible for other users than sameschool when they are published

        # PR0222-09-06 mail Nancy Josephina Insp: cannot validate.
        # must show alls subjects to Insp, also when they are not published
        # added: 'and not request.user.role == c.ROLE_032_INSP:'
        if not requsr_same_school and not request.user.role == c.ROLE_032_INSP:
            # PR2022-12-16 NIU: there are no examyears before 2022
            #   PR2021-09-04 debug: examyears before 2022 have no subj_published_id. Show them to others anyway
            #   if sel_examyear is None or sel_examyear.code >= 2022:
            sql_studsubj_list.append("AND studsubj.subj_published_id IS NOT NULL")

        sql_studsubjects = ' '.join(sql_studsubj_list)

        sql_list = ["WITH studsubj AS (" + sql_studsubjects + ")",
            "SELECT st.id AS stud_id, studsubj.studsubj_id, studsubj.subjbase_id, studsubj.schemeitem_id, studsubj.cluster_id, studsubj.cluster_name,",
            "CONCAT('studsubj_', st.id::TEXT, '_', studsubj.studsubj_id::TEXT) AS mapid, 'studsubj' AS table,",
            "st.lastname, st.firstname, st.prefix, st.examnumber,",
            "st.scheme_id, st.iseveningstudent, st.islexstudent, st.classname, ",
            "st.tobedeleted AS st_tobedeleted, st.reex_count, st.reex03_count, st.bis_exam, st.withdrawn,",

            "st.subj_composition_checked, st.subj_composition_ok, st.subj_dispensation,",

            "studsubj.subject_id AS subj_id, studsubj.subj_code, studsubj.subj_name_nl,",
            "dep.base_id AS depbase_id, dep.abbrev AS dep_abbrev,",
            "lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev,",
            "sct.base_id AS sctbase_id, sct.abbrev AS sct_abbrev,",

            "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_thumbrule,",
            "studsubj.pws_title, studsubj.pws_subjects,",
            "studsubj.has_exemption, studsubj.has_sr, studsubj.has_reex, studsubj.has_reex03, studsubj.exemption_year, studsubj.pok_validthru,",

            "studsubj.is_mandatory, studsubj.is_mand_subj_id, studsubj.is_combi,",
            "studsubj.extra_count_allowed, studsubj.extra_nocount_allowed,",
            "studsubj.sjtp_id, studsubj.sjtp_abbrev, studsubj.sjtp_has_prac, studsubj.sjtp_has_pws,",
            "studsubj.weight_se, studsubj.weight_ce,",
            "studsubj.subj_auth1by_id, studsubj.subj_auth1_usr,",
            "studsubj.subj_auth2by_id, studsubj.subj_auth2_usr,",
            "studsubj.subj_published_id, studsubj.subj_publ_modat,",

            "studsubj.exem_auth1by_id, studsubj.exem_auth1_usr,",
            "studsubj.exem_auth2by_id, studsubj.exem_auth2_usr,",
            "studsubj.exem_published_id, studsubj.exem_publ_modat,",

            "studsubj.sr_auth1by_id, studsubj.sr_auth1_usr,",
            "studsubj.sr_auth2by_id, studsubj.sr_auth2_usr,",
            "studsubj.sr_published_id, studsubj.sr_publ_modat,",

            "studsubj.reex_auth1by_id, studsubj.reex_auth1_usr,",
            "studsubj.reex_auth2by_id, studsubj.reex_auth2_usr,",
            "studsubj.reex_published_id, studsubj.reex_publ_modat,",

            "studsubj.reex3_auth1by_id, studsubj.reex3_auth1_usr,",
            "studsubj.reex3_auth2by_id, studsubj.reex3_auth2_usr,",
            "studsubj.reex3_published_id, studsubj.reex3_publ_modat,",

            "studsubj.pok_auth1by_id, studsubj.pok_auth1_usr,",
            "studsubj.pok_auth2by_id, studsubj.pok_auth2_usr,",
            "studsubj.pok_published_id, studsubj.pok_publ_modat,",

            "studsubj.tobedeleted, studsubj.modifiedat, studsubj.modby_username",

            "FROM students_student AS st",
            left_or_inner_join, "studsubj ON (studsubj.student_id = st.id)",
            "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
            "LEFT JOIN subjects_scheme AS scheme ON (scheme.id = st.scheme_id)",
            "LEFT JOIN subjects_package AS package ON (package.id = st.package_id)",

            "WHERE school.base_id=" + str(sel_schoolbase_pk) + "::INT",
            "AND school.examyear_id=" + str(sel_examyear_pk) + "::INT",
            "AND dep.base_id=" + str(sel_depbase_pk) + "::INT",
            "AND NOT st.deleted"
            ]

        if sel_lvlbase_pk:
            sql_list.append("".join(("AND lvl.base_id=", str(sel_lvlbase_pk), "::INT")))

        if sel_sctbase_pk:
            sql_list.append("".join(("AND sct.base_id=", str(sel_sctbase_pk), "::INT")))

        # filter on sel_student_pk
        if student_pk:
            sql_list.append("".join(("AND st.id=", str(student_pk), "::INT")))

        # also return existing studsubj of updated clusters, to show changed name in table
        # - filter on studsubj_pk_list with ANY clause
        # - PR2022-03-23 see https://stackoverflow.com/questions/34627026/in-vs-any-operator-in-postgresql
        if cluster_pk_list:
            sql_keys['cls_pk_list'] = cluster_pk_list
            if studsubj_pk_list:
                # PR2023-02-18 was:
                #   sql_keys['ss_pk_list'] = studsubj_pk_list
                #   PR2022-12-25 was: sql_list.append("AND ( studsubj.studsubj_id = ANY(%(ss_pk_list)s::INT[]) OR studsubj.cluster_id = ANY(%(cls_pk_list)s::INT[]) )  ")
                #   sql_list.append("AND ( studsubj.studsubj_id IN (SELECT UNNEST(%(ss_pk_list)s::INT[])) OR studsubj.cluster_id IN (SELECT UNNEST(%(cls_pk_list)s::INT[])) )")

                sql_list.append(''.join((
                    "AND (studsubj.studsubj_id IN (SELECT UNNEST(ARRAY", str(studsubj_pk_list), "::INT[])) OR ",
                         "studsubj.cluster_id IN (SELECT UNNEST(ARRAY", str(cluster_pk_list),  "::INT[])) )"
                )))
            else:
                # PR2023-02-18 was:
                #   PR2022-12-26 was: sql_list.append("AND studsubj.cluster_id = ANY(%(cls_pk_list)s::INT[])")
                #   sql_list.append("AND studsubj.cluster_id IN (SELECT UNNEST( %(cls_pk_list)s::INT[]))")
                sql_list.append(
                    ''.join((
                        "AND studsubj.cluster_id IN (SELECT UNNEST(ARRAY", str(cluster_pk_list), "::INT[]))"
                    ))
                )

        elif studsubj_pk_list:
            # PR2023-02-18 was:
            #   sql_keys['ss_pk_list'] = studsubj_pk_list
            #   PR2022-12-25 was: sql_list.append("AND studsubj.studsubj_id = ANY(%(ss_pk_list)s::INT[])")
            #   sql_list.append("AND studsubj.studsubj_id IN (SELECT UNNEST(%(ss_pk_list)s::INT[]))")
            sql_list.append(''.join(("AND studsubj.studsubj_id IN (SELECT UNNEST(ARRAY", str(studsubj_pk_list), "::INT[]))")))

        else:
    # --- filter on usersetting and allowed

            requsr_corrector = (request.user.role == c.ROLE_016_CORR)

            # PR2023-03-27
            # when a corrector has no allowed subjects, must return None.
            # when an examiner has no allowed subjects, must return all subjects.
            return_false_when_no_allowedsubjects = requsr_corrector

            sql_clause = acc_prm.get_sqlclause_allowed_NEW(
                table='studsubj',
                sel_schoolbase_pk=sel_schoolbase_pk,
                sel_depbase_pk=sel_depbase_pk,
                sel_lvlbase_pk=sel_lvlbase_pk,
                userallowed_sections_dict=userallowed_sections_dict,
                return_false_when_no_allowedsubjects=return_false_when_no_allowedsubjects
            )
            if sql_clause:
                sql_list.append(sql_clause)

            if logging_on :
                logger.debug('sql_clause: ' + str(sql_clause))

        sql_list.append('ORDER BY st.id, studsubj.studsubj_id NULLS FIRST;')
        if logging_on and False:
            for sql_str in sql_list:
                logger.debug('  > ' + str(sql_str))

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            #cursor.execute(sql, sql_keys)
            cursor.execute(sql)
            rows = af.dictfetchall(cursor)

        if logging_on and False:
            for q in connection.queries:
                logger.debug('   ' + str(q))

        if logging_on:
            logger.debug('    len rows: ' + str(len(rows)))

    # - full name to rows
        for row in rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

    # - add additional key/value pairs to studsubj_row, from append_dict, with key = studsubj_id
            if append_dict:
                studsubj_append_dict = append_dict.get(row.get('studsubj_id'))
                if studsubj_append_dict:
                    for key, value in studsubj_append_dict.items():
                        row[key] = value

            if logging_on and False:
                logger.debug('row: ' + str(row))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
    return rows
# --- end of create_studentsubject_rows


def create_studentsubjectnote_rows(upload_dict, request):  # PR2021-03-16
    # --- create rows of notes of this studentsubject
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_studentsubjectnote_rows ============= ')
        logger.debug('upload_dict: ' + str(upload_dict))
    # create list of studentsubjectnote of this studentsubject, filter intern_schoolbase
    # to show intern note only to user of the same school/insp: filter intern_schoolbase = requsr.schoolbase or null
    # intern_schoolbase only has value when it is an intern memo.
    # It has the value of the school of the user, NOT the school of the student
    note_rows = []
    if upload_dict:
        studsubj_pk = upload_dict.get('studsubj_pk')
        if studsubj_pk:
            if logging_on:
                logger.debug('studsubj_pk: ' + str(studsubj_pk))
            sel_examyear_instance = af.get_selected_examyear_from_usersetting_without_check(request)
            if sel_examyear_instance:
                sql_keys = {
                    'ss_id': studsubj_pk,
                    'ex_yr': sel_examyear_instance.pk,
                    'req_int_sb_id': request.user.schoolbase_id}
                sql_list = ["SELECT au.id, COALESCE(SUBSTRING (au.username, 7), '') AS name,",
                            "sb.code AS sb_code, sch.abbrev as sch_abbrev ",
                            "FROM accounts_user AS au",
                            "INNER JOIN schools_schoolbase AS sb ON (sb.id = au.schoolbase_id)",
                            "INNER JOIN schools_school AS sch ON (sch.base_id = au.schoolbase_id)",
                            "WHERE sch.examyear_id = %(ex_yr)s::INT"
                            ]

                sql_user = ' '.join(sql_list)
                sql_list = ["SELECT ssn.id, ssn.studentsubject_id, ssn.note, ssn.note_status, ssn.intern_schoolbase_id,",
                            "ssn.modifiedat, au.name AS modifiedby, au.sb_code, au.sch_abbrev",

                            "FROM students_studentsubjectnote AS ssn",
                            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = ssn.studentsubject_id)",
                            "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
                            "LEFT JOIN ( " + sql_user + ") AS au ON (au.id = ssn.modifiedby_id)",
                            "WHERE ssn.studentsubject_id = %(ss_id)s::INT",
                            "AND (ssn.intern_schoolbase_id = %(req_int_sb_id)s::INT OR ssn.intern_schoolbase_id IS NULL)"
                            ]
                sql_list.append("ORDER BY ssn.modifiedat DESC")

                sql = ' '.join(sql_list)
                newcursor = connection.cursor()
                newcursor.execute(sql, sql_keys)
                note_rows = af.dictfetchall(newcursor)
                if note_rows:
                    for note_row in note_rows:
                        ssn_id = note_row.get('id')

                        if logging_on:
                            logger.debug('note_row: ' + str(note_row))
                            logger.debug('ssn_id: ' + str(ssn_id))
                        sql_keys = {'ssn_id': ssn_id}
                        sql_list = [
                            "SELECT nat.id, nat.file, nat.contenttype, nat.studentsubjectnote_id",
                            "FROM students_noteattachment AS nat",
                            "WHERE nat.studentsubjectnote_id = %(ssn_id)s::INT"
                            ]
                        #                         "WHERE nat.studentsubjectnote_id = %(ssn_id)s::INT"
                        sql_list.append("ORDER BY nat.file")
                        sql = ' '.join(sql_list)
                        newcursor.execute(sql, sql_keys)
                        rows = newcursor.fetchall()

                        if logging_on:
                            logger.debug('rows: ' + str(rows))

                        attachments = stud_mod.Noteattachment.objects.filter(
                            studentsubjectnote=ssn_id)
                # get list of attachments
                        nat_rows = []
                        if attachments:
                            for attachment in attachments:
                                file = attachment.file
                                url = file.url
                                nat_rows.append({'id': attachment.pk, 'file_name': str(file), 'url': url})
                        if nat_rows:
                            note_row['attachments'] = nat_rows

    return note_rows
# - end of create_studentsubjectnote_rows


def create_ssnote_attachment_rows(upload_dict, request):  # PR2021-03-17
    # --- create rows of notes of this studentsubject
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_studentsubjectnote_rows ============= ')
        logger.debug('upload_dict: ' + str(upload_dict))
    # create list of studentsubjectnote of this studentsubject, filter intern_schoolbase
    # to show intern note only to user of the same school/insp: filter intern_schoolbase = requsr.schoolbase or null
    note_rows = []
    if upload_dict:
        studsubj_pk =  upload_dict.get('studsubj_pk')
        if studsubj_pk:
            requsr_intern_schoolbase_pk = request.user.schoolbase_id
            if logging_on:
                logger.debug('studsubj_pk: ' + str(studsubj_pk))
                logger.debug('requsr_intern_schoolbase_pk: ' + str(requsr_intern_schoolbase_pk))

            sql_keys = {'ss_id': studsubj_pk, 'int_sb_id': requsr_intern_schoolbase_pk}
            sql_user = "SELECT au.id, COALESCE(SUBSTRING (au.username, 7), '') AS name, sb.code AS sb_code " + \
                            "FROM accounts_user AS au INNER JOIN schools_schoolbase AS sb ON (sb.id = au.schoolbase_id)"

            sql_list = ["SELECT ssn.id, ssn.studentsubject_id, ssn.note, ssn.note_status, ssn.intern_schoolbase_id,",
                        "ssn.modifiedat, au.name AS modifiedby, au.sb_code AS schoolcode",
                        "FROM students_studentsubjectnote AS ssn",
                        "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = ssn.studentsubject_id)",
                        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
                        "LEFT JOIN ( " + sql_user + ") AS au ON (au.id = ssn.modifiedby_id)",
                        "WHERE ssn.studentsubject_id = %(ss_id)s::INT"

                        ]
                        #"AND ( ssn.intern_schoolbase_id IS NULL OR ssn.intern_schoolbase_id = %(int_sb_id)s::INT ) "

            sql_list.append("ORDER BY ssn.modifiedat DESC")

            sql = ' '.join(sql_list)
            newcursor = connection.cursor()
            newcursor.execute(sql, sql_keys)
            note_rows = af.dictfetchall(newcursor)

    return note_rows
# - end of create_studentsubjectnote_rows

