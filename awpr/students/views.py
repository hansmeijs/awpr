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
from django.utils.translation import activate, pgettext_lazy, gettext_lazy as _
from django.views.generic import View

from accounts import views as acc_view
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
class StudentListView(View):  # PR2018-09-02 PR2020-10-27 PR2021-03-25

    def get(self, request):
        #logger.debug('  =====  StudentListView ===== ')

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_student'
        params = awpr_menu.get_headerbar_param(request, page)

# - save this page in Usersetting, so at next login this page will open. Used in LoggedIn
        #         # PR2021-06-22 moved to get_headerbar_param

        return render(request, 'students.html', params)


# ========  StudentsubjectListView  =======
@method_decorator([login_required], name='dispatch')
class StudentsubjectListView(View): # PR2020-09-29 PR2021-03-25

    def get(self, request):
        #logger.debug(" =====  StudentsubjectListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_studsubj'
        params = awpr_menu.get_headerbar_param(request, page)
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
def create_student_rows(sel_examyear, sel_schoolbase, sel_depbase, append_dict,
                        student_pk=None, sel_lvlbase_pk=None, sel_sctbase_pk=None):
    # --- create rows of all students of this examyear / school PR2020-10-27 PR2022-01-03 PR2022-02-15
    # - show only students that are not tobedeleted
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_student_rows -----')

    student_rows = []
    error_dict = {} # PR2021-11-17 new way of err msg, like in TSA

    if sel_examyear and sel_schoolbase and sel_depbase:
        try:

            if logging_on:
                logger.debug(' ----- create_student_rows -----')
                logger.debug('sel_examyear: ' + str(sel_examyear))
                logger.debug('sel_schoolbase: ' + str(sel_schoolbase))
                logger.debug('sel_depbase: ' + str(sel_depbase))
                logger.debug('sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
                logger.debug('sel_sctbase_pk: ' + str(sel_sctbase_pk))

            sql_keys = {'ey_id': sel_examyear.pk, 'sb_id': sel_schoolbase.pk, 'db_id': sel_depbase.pk}
            sql_list = ["SELECT st.id, st.base_id, st.school_id AS s_id,",
                "sch.locked AS s_locked, ey.locked AS ey_locked, ",
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
                "st.has_dyslexie, st.iseveningstudent, st.islexstudent,",
                "st.bis_exam, st.partial_exam,",

                "st.linked, st.notlinked, st.sr_count, st.reex_count, st.reex03_count, st.withdrawn,",
                "st.gl_ce_avg, st.gl_combi_avg, st.gl_final_avg,",

                "st.result, st.result_status, st.result_info, st.tobedeleted,",

                "st.modifiedby_id, st.modifiedat,",
                "SUBSTRING(au.username, 7) AS modby_username",

                "FROM students_student AS st",
                "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                "LEFT JOIN schools_department AS dep ON (dep.id = st.department_id)",
                "INNER JOIN schools_departmentbase AS db ON (db.id = dep.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
                "LEFT JOIN subjects_scheme AS scheme ON (scheme.id = st.scheme_id)",
                "LEFT JOIN accounts_user AS au ON (au.id = st.modifiedby_id)",
                "WHERE sch.base_id = %(sb_id)s::INT",
                        "AND sch.examyear_id = %(ey_id)s::INT",
                        "AND dep.base_id = %(db_id)s::INT",
                        "AND NOT st.tobedeleted"]

            if sel_lvlbase_pk:
                sql_list.append('AND lvl.base_id = %(lvlbase_id)s::INT')
                sql_keys['lvlbase_id'] = sel_lvlbase_pk
            if sel_sctbase_pk:
                sql_list.append('AND sct.base_id = %(sctbase_id)s::INT')
                sql_keys['sctbase_id'] = sel_sctbase_pk

            if student_pk:
                sql_list.append('AND st.id = %(st_id)s::INT')
                sql_keys['st_id'] = student_pk

            # order by id necessary to make sure that lookup function on client gets the right row
            sql_list.append("ORDER BY st.id")

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                student_rows = af.dictfetchall(cursor)

            if logging_on and False:
                logger.debug('student_rows: ' + str(student_rows))
                # logger.debug('connection.queries: ' + str(connection.queries))

        # - add lastname_firstname_initials to rows
            if student_rows:
                for row in student_rows:
                    first_name = row.get('firstname')
                    last_name = row.get('lastname')
                    prefix = row.get('prefix')
                    row['name_first_init'] = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)

            # - add messages to student_row
            if student_pk and student_rows:
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
                str(_('An error occurred')) + ':',
                '&emsp;<i>' + str(e) + '</i>'
            ))
            error_dict = {'class': 'border_bg_invalid', 'msg_html': msg_html}

    return student_rows, error_dict
# --- end of create_student_rows



#/////////////////////////////////////////////////////////////////
def create_results_per_school_rows(request, sel_examyear, sel_schoolbase):
    # --- create rows of all students of this examyear / school PR2020-10-27 PR2022-01-03 PR2022-02-15
    # - show only students that are not tobedeleted
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_results_per_school_rows -----')

    student_rows = []
    error_dict = {} # PR2021-11-17 new way of err msg, like in TSA

    if sel_examyear:
        try:

            if logging_on:
                logger.debug('sel_examyear: ' + str(sel_examyear))
                logger.debug('sel_schoolbase: ' + str(sel_schoolbase))
                logger.debug('sel_schoolbase.pk: ' + str(sel_schoolbase.pk))

            sql_keys = {'ey_id': sel_examyear.pk, 'sb_id': sel_schoolbase.pk}
            if logging_on:
                logger.debug('sql_keys: ' + str(sql_keys))

            sql_list = ["SELECT db.code AS db_code, lvlbase.code AS lvl_code, sch.name as sch_name, sb.code as sb_code,",
                #"sctbase.code as sct_code, ",

                "SUM((st.gender = 'M')::INT) AS m,",
                "SUM((st.gender = 'V')::INT) AS v,",
                "SUM(1) AS t,",
        # first exam period
                    "SUM((st.gender = 'M' AND st.ep01_result = 0)::INT) AS ep1_m_nores,",
                    "SUM((st.gender = 'V' AND st.ep01_result = 0)::INT) AS ep1_v_nores,",
                    "SUM((st.ep01_result = 0)::INT) AS ep1_t_nores,",

                    "SUM((st.gender = 'M' AND st.ep01_result = 1)::INT) AS ep1_m_pass,",
                    "SUM((st.gender = 'V' AND st.ep01_result = 1)::INT) AS ep1_v_pass,",
                    "SUM((st.ep01_result = 1)::INT) AS ep1_t_pass,",

                    "SUM((st.gender = 'M' AND st.ep01_result = 2)::INT) AS ep1_m_fail,",
                    "SUM((st.gender = 'V' AND st.ep01_result = 2)::INT) AS ep1_v_fail,",
                    "SUM((st.ep01_result = 2)::INT) AS ep1_t_fail,",

                    "SUM((st.gender = 'M' AND st.ep01_result = 3)::INT) AS ep1_m_reex,",
                    "SUM((st.gender = 'V' AND st.ep01_result = 3)::INT) AS ep1_v_reex,",
                    "SUM((st.ep01_result = 3)::INT) AS ep1_t_reex,",

                    "SUM((st.gender = 'M' AND st.ep01_result = 4)::INT) AS ep1_m_wdr,",
                    "SUM((st.gender = 'V' AND st.ep01_result = 4)::INT) AS ep1_v_wdr,",
                    "SUM((st.ep01_result = 4)::INT) AS ep1_t_wdr,",
            # grade improvemenet
                    "SUM((st.gender = 'M' AND st.ep01_result = 1 AND st.reex_count > 0)::INT) AS ep1_m_gimp,",
                    "SUM((st.gender = 'V' AND st.ep01_result = 1 AND st.reex_count > 0)::INT) AS ep1_v_gimp,",
                    "SUM((st.ep01_result = 1 AND st.reex_count > 0)::INT) AS ep1_t_gimp,",
            # re-examination
                    "SUM((st.gender = 'M' AND st.ep01_result = 2 AND st.reex_count > 0)::INT) AS ep1_m_reex,",
                    "SUM((st.gender = 'V' AND st.ep01_result = 2 AND st.reex_count > 0)::INT) AS ep1_v_reex,",
                    "SUM((st.ep01_result = 2 AND st.reex_count > 0)::INT) AS ep1_t_reex,",

   # second exam period
            "SUM((st.gender = 'M' AND st.ep02_result = 0)::INT) AS ep2_m_nores,",
            "SUM((st.gender = 'V' AND st.ep02_result = 0)::INT) AS ep2_v_nores,",
            "SUM((st.ep02_result = 0)::INT) AS ep2_t_nores,",

            "SUM((st.gender = 'M' AND st.ep02_result = 1)::INT) AS ep2_m_pass,",
            "SUM((st.gender = 'V' AND st.ep02_result = 1)::INT) AS ep2_v_pass,",
            "SUM((st.ep02_result = 1)::INT) AS ep2_t_pass,",

            "SUM((st.gender = 'M' AND st.ep02_result = 2)::INT) AS ep2_m_fail,",
            "SUM((st.gender = 'V' AND st.ep02_result = 2)::INT) AS ep2_v_fail,",
            "SUM((st.ep02_result = 2)::INT) AS ep2_t_fail,",

            "SUM((st.gender = 'M' AND st.ep02_result = 3)::INT) AS ep2_m_reex,",
            "SUM((st.gender = 'V' AND st.ep02_result = 3)::INT) AS ep2_v_reex,",
            "SUM((st.ep02_result = 3)::INT) AS ep2_t_reex,",

            "SUM((st.gender = 'M' AND st.ep02_result = 4)::INT) AS ep2_m_wdr,",
            "SUM((st.gender = 'V' AND st.ep02_result = 4)::INT) AS ep2_v_wdr,",
            "SUM((st.ep02_result = 4)::INT) AS ep2_t_wdr,",

        # final results
            "SUM((st.gender = 'M' AND st.result = 0)::INT) AS m_nores,",
            "SUM((st.gender = 'V' AND st.result = 0)::INT) AS v_nores,",
            "SUM((st.result = 0)::INT) AS t_nores,",

            "SUM((st.gender = 'M' AND st.result = 1)::INT) AS m_pass,",
            "SUM((st.gender = 'V' AND st.result = 1)::INT) AS v_pass,",
            "SUM((st.result = 1)::INT) AS t_pass,",

            "SUM((st.gender = 'M' AND st.result = 2)::INT) AS m_fail,",
            "SUM((st.gender = 'V' AND st.result = 2)::INT) AS v_fail,",
            "SUM((st.result = 2)::INT) AS t_fail,",

            "SUM((st.gender = 'M' AND st.result = 3)::INT) AS m_reex,",
            "SUM((st.gender = 'V' AND st.result = 3)::INT) AS v_reex,",
            "SUM((st.result = 3)::INT) AS t_reex,",

            "SUM((st.gender = 'M' AND st.result = 4)::INT) AS m_wdr,",
            "SUM((st.gender = 'V' AND st.result = 4)::INT) AS v_wdr,",
            "SUM((st.result = 4)::INT) AS t_wdr",

                "FROM students_student AS st",
                "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
                "INNER JOIN schools_departmentbase AS db ON (db.id = dep.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
                "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",
                #"INNER JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
                #"INNER JOIN subjects_sectorbase AS sctbase ON (sctbase.id = sct.base_id)",
                "WHERE sch.examyear_id = %(ey_id)s::INT",
                "AND NOT st.tobedeleted"]

            if request.user.is_role_school:
                sql_keys['sb_id'] = sel_schoolbase.pk if sel_schoolbase else None
                sql_list.append('AND sb.id = %(sb_id)s::INT')

            # order by id necessary to make sure that lookup function on client gets the right row
            sql_list.append("GROUP BY dep.sequence, lvl.sequence, db.code, lvlbase.code, sb.code, sch.name")
            sql_list.append("ORDER BY dep.sequence, lvl.sequence, sb.code")

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                student_rows = af.dictfetchall(cursor)

            if logging_on:
                logger.debug('student_rows: ' + str(student_rows))
                #logger.debug('connection.queries: ' + str(connection.queries))

        except Exception as e:
            # - return msg_err when instance not created
            #  msg format: [ { class: "border_bg_invalid", header: 'Update this', msg_html: "An eror occurred." }]
            logger.error(getattr(e, 'message', str(e)))
            # &emsp; add 4 'hard' spaces
            msg_html = '<br>'.join((
                str(_('An error occurred')) + ':',
                '&emsp;<i>' + str(e) + '</i>'
            ))
            error_dict = {'class': 'border_bg_invalid', 'msg_html': msg_html}

    return student_rows, error_dict
# --- end of create_student_rows


@method_decorator([login_required], name='dispatch')
class ClusterUploadView(View):  # PR2022-01-06

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ClusterUploadView ============= ')

        update_wrap = {}
        msg_list = []

# - get permit
        has_permit = af.get_permit_crud_of_this_page('page_studsubj', request)
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
                sel_examyear, sel_school, sel_department, may_edit, sel_msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if logging_on:
                    logger.debug('sel_examyear:   ' + str(sel_examyear))
                    logger.debug('sel_school:     ' + str(sel_school))
                    logger.debug('sel_department: ' + str(sel_department))
                    logger.debug('may_edit:       ' + str(may_edit))
                    logger.debug('sel_msg_list:   ' + str(sel_msg_list))
                    logger.debug('cluster_list:   ' + str(cluster_list))
                    logger.debug('studsubj_list:   ' + str(studsubj_list))

                if sel_msg_list:
                    msg_list.extend(sel_msg_list)
                else:
                    sel_schoolbase = sel_school.base if sel_school else None
                    sel_depbase = sel_department.base if sel_department else None

                    mapped_cluster_pk_dict = {}

                    created_cluster_pk_list = []
                    deleted_cluster_pk_list = []
                    updated_cluster_pk_list = []
                    cluster_pk_list = []

                    if cluster_list:
                        err_list = loop_cluster_list(
                            sel_examyear=sel_examyear,
                            sel_school=sel_school,
                            sel_department=sel_department,
                            cluster_list=cluster_list,
                            mapped_cluster_pk_dict=mapped_cluster_pk_dict,
                            created_cluster_pk_list=created_cluster_pk_list,
                            updated_cluster_pk_list=updated_cluster_pk_list,
                            deleted_cluster_pk_list=deleted_cluster_pk_list,
                            request=request
                        )
                        if err_list:
                            msg_list.extend(err_list)
                        # cluster_pk_list stores cahnged clusters, to update cluster in table with studsubj
                        if updated_cluster_pk_list:
                            cluster_pk_list.extend(updated_cluster_pk_list)
                        if deleted_cluster_pk_list:
                            cluster_pk_list.extend(deleted_cluster_pk_list)

                        if logging_on:
                            logger.debug('created_cluster_pk_list: ' + str(created_cluster_pk_list))
                            logger.debug('deleted_cluster_pk_list: ' + str(deleted_cluster_pk_list))
                            logger.debug('updated_cluster_pk_list: ' + str(updated_cluster_pk_list))
                            logger.debug('mapped_cluster_pk_dict: ' + str(mapped_cluster_pk_dict))
                            logger.debug('cluster_pk_list: ' + str(cluster_pk_list))

                        updated_cluster_rows = []
                        if updated_cluster_pk_list:
                            updated_cluster_rows = sj_vw.create_cluster_rows(
                                request=request,
                                sel_examyear=sel_examyear,
                                sel_schoolbase=sel_schoolbase,
                                sel_depbase=sel_depbase,
                                cur_dep_only=True,
                                allowed_only=False,  # TODO check if value  false is ok
                                cluster_pk_list=updated_cluster_pk_list,
                                add_field_created=False
                            )
                        if created_cluster_pk_list:
                            created_cluster_rows = sj_vw.create_cluster_rows(
                                request=request,
                                sel_examyear=sel_examyear,
                                sel_schoolbase=sel_schoolbase,
                                sel_depbase=sel_depbase,
                                cur_dep_only=True,
                                allowed_only=False,  # TODO check if value  false is ok
                                cluster_pk_list=created_cluster_pk_list,
                                add_field_created=True
                            )
                            if created_cluster_rows:
                                updated_cluster_rows.extend(created_cluster_rows)

                        if deleted_cluster_pk_list:
                            for deleted_cluster_pk in deleted_cluster_pk_list:
                                updated_cluster_rows.append({'id': deleted_cluster_pk, 'deleted': True})
                        if updated_cluster_rows:
                            update_wrap['updated_cluster_rows'] = updated_cluster_rows

                        if logging_on:
                            logger.debug('updated_cluster_rows: ' + str(updated_cluster_rows))

                    studsubj_pk_list = []
                    if studsubj_list:
                        err_list, studsubj_pk_list = loop_studsubj_list(studsubj_list, mapped_cluster_pk_dict, request)
                        if err_list:
                            msg_list.extend(err_list)
                        if logging_on:
                            logger.debug('studsubj_pk_list: ' + str(studsubj_pk_list))

                    if studsubj_pk_list or cluster_pk_list:
                        rows = create_studentsubject_rows(
                            examyear=sel_examyear,
                            schoolbase=sel_schoolbase,
                            depbase=sel_depbase,
                            requsr_same_school=True,  # check for same_school is included in may_edit
                            setting_dict={},
                            append_dict=append_dict,
                            request=request,
                            studsubj_pk_list=studsubj_pk_list,
                            cluster_pk_list=cluster_pk_list
                        )
                        if rows:
                            update_wrap['updated_studsubj_rows'] = rows
                    #if logging_on:
                    #    logger.debug('rows: ' + str(rows))

        # - addd messages to update_wrap
        if msg_list:
            msg_html = '<br>'.join(msg_list)
            update_wrap['msg_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of ClusterUploadView


def loop_cluster_list(sel_examyear, sel_school, sel_department, cluster_list, mapped_cluster_pk_dict,
                      created_cluster_pk_list, updated_cluster_pk_list, deleted_cluster_pk_list, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        if logging_on:
            logger.debug(' ----- loop_cluster_list  -----')
            logger.debug('cluster_list: ' + str(cluster_list))

    err_list = []

    for cluster_dict in cluster_list:
        if logging_on:
            logger.debug('cluster_dict: ' + str(cluster_dict))
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
                logger.debug('mode: ' + str(mode))
                logger.debug('cluster_pk: ' + str(cluster_pk))

    # +++  Create new cluster
            if is_create:
                cluster_name = cluster_dict.get('cluster_name')
                err_lst, new_cluster_pk = create_cluster(sel_school, sel_department, subject, cluster_pk, cluster_name, mapped_cluster_pk_dict, request)
                if err_lst:
                    err_list.extend(err_lst)
                if new_cluster_pk:
                    created_cluster_pk_list.append(new_cluster_pk)
                if logging_on:
                    logger.debug('     new_cluster_pk: ' + str(new_cluster_pk))
                    logger.debug('     updated_cluster_pk_list: ' + str(updated_cluster_pk_list))
                    logger.debug('     mapped_cluster_pk_dict: ' + str(mapped_cluster_pk_dict))

    # +++  or get existing cluster
            # filter out 'new_1', should not happen
            elif isinstance(cluster_pk, int):
                cluster = subj_mod.Cluster.objects.get_or_none(
                    pk=cluster_pk,
                    school=sel_school,
                    department=sel_department
                )
                if logging_on:
                    logger.debug('cluster: ' + str(cluster))

                if cluster:
    # +++ Delete cluster
                    if is_delete:
                        deleted_ok, err_lst, deleted_cluster_pk = delete_cluster(cluster, request)
                        if err_lst:
                            err_list.extend(err_lst)
                        if deleted_cluster_pk:
                            deleted_cluster_pk_list.append(deleted_cluster_pk)

                        if logging_on:
                            logger.debug('deleted_cluster_pk: ' + str(deleted_cluster_pk))
                            logger.debug('deleted_cluster_pk_list: ' + str(deleted_cluster_pk_list))
    # +++ Update cluster, not when it is created, not when delete has failed (when deleted ok there is no cluster)
                    else:
                        err_lst, updated_cluster_pk = update_cluster_instance(sel_school, sel_department, cluster, cluster_dict, request)
                        if err_lst:
                            err_list.extend(err_lst)
                        if updated_cluster_pk:
                            updated_cluster_pk_list.append(updated_cluster_pk)
                        if logging_on:
                            logger.debug('updated_cluster_pk: ' + str(updated_cluster_pk))
                            logger.debug('updated_cluster_pk_list: ' + str(updated_cluster_pk_list))
    return err_list
# - end of loop_cluster_list


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
class StudentUploadView(View):  # PR2020-10-01 PR2021-07-18

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= StudentUploadView ============= ')

        update_wrap = {}
        messages = []

# - get permit
        has_permit = af.get_permit_crud_of_this_page('page_student', request)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

# - get variables
                student_pk = upload_dict.get('student_pk')
                mode = upload_dict.get('mode')
                is_create = mode == 'create'
                is_delete =  mode == 'delete'

                if logging_on:
                    logger.debug('mode: ' + str(mode))
                    logger.debug('upload_dict: ' + str(upload_dict))

                updated_rows = []
                append_dict = {}
                error_list = []

# ----- get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not same_school, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase
                #  - Note: skip check not activated, it will be set True in create_student
                sel_examyear, sel_school, sel_department, may_edit, sel_msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(
                        request=request,
                        skip_check_activated=True
                    )

                if logging_on:
                    logger.debug('sel_examyear:   ' + str(sel_examyear))
                    logger.debug('sel_school:     ' + str(sel_school))
                    logger.debug('sel_department: ' + str(sel_department))
                    logger.debug('may_edit:       ' + str(may_edit))
                    logger.debug('sel_msg_list:       ' + str(sel_msg_list))
                """
                sel_msg_list = msg_list.append(str(_("You don't have permission to view department %(val)s.") % {'val': sel_depbase.code}))
                """
                if len(sel_msg_list):
                    msg_html = '<br>'.join(sel_msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                else:

# +++  Create new student
                    if is_create:
                        err_list = []
                        student = create_student(sel_school, sel_department,
                            upload_dict, messages, err_list, request, False)  # skip_save = False
                        """
                        msg_html = '<br>'.join(msg_list)
                        messages.append({'header': str(_('Add candidate')), 'class': "border_bg_invalid", 'msg_html': msg_html})
                        error_list.extend(msg_list)
                        """
                        if err_list:
                            messages.extend(err_list)

                        if student:
                            append_dict['created'] = True
                    else:

# +++  or get existing student
                        student = stud_mod.Student.objects.get_or_none(
                            id=student_pk,
                            school=sel_school
                        )
                    if logging_on:
                        logger.debug('student: ' + str(student))

                    deleted_ok = False

                    if student:
# +++ Delete student
                        if is_delete:
                            err_list = []
                            deleted_ok = delete_student(student, updated_rows, err_list, request)
                            if err_list:
                                messages.extend(err_list)

# +++ Update student, also when it is created, not when delete has failed (when deleted ok there is no student)
                        else:
                            idnumber_list, examnumber_list = [], []
                            update_student_instance(student, sel_examyear, sel_school, sel_department, upload_dict, idnumber_list, examnumber_list, messages, error_list, request, False)  # skip_save = False

# - create student_row, also when deleting failed, not when deleted ok, in that case student_row is added in delete_student
                    if not deleted_ok:
                        student_pk = student.pk if student else None
                        updated_rows, error_dictNIU = create_student_rows(
                            sel_examyear=sel_school.examyear,
                            sel_schoolbase=sel_school.base,
                            sel_depbase=sel_department.base,
                            append_dict=append_dict,
                            student_pk=student_pk)

                update_wrap['updated_student_rows'] = updated_rows

# - addd messages to update_wrap
        if len(messages):
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentUploadView


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
        has_permit = af.get_permit_crud_of_this_page('page_studsubj', request)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

# - get variables
                mode = upload_dict.get('mode')
                cur_stud_pk = upload_dict.get('cur_stud_id')
                oth_stud_pk = upload_dict.get('oth_stud_id')

                if logging_on:
                    logger.debug('mode: ' + str(mode))
                    logger.debug('cur_stud_pk: ' + str(cur_stud_pk))
                    logger.debug('oth_stud_pk: ' + str(oth_stud_pk))

                updated_rows = []
                append_dict = {}
                error_list = []

# ----- get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not same_school, not activated, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase
                sel_examyear, sel_school, sel_department, may_edit, sel_msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

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
                    try:
    # +++  get current student
                        cur_student = stud_mod.Student.objects.get_or_none(
                            id=cur_stud_pk,
                            school=sel_school
                        )

                        if cur_student and oth_stud_pk:
                            other_stud_pk_str = str(oth_stud_pk)
                            if logging_on:
                                logger.debug('cur_student:   ' + str(cur_student))
                                logger.debug('oth_stud_pk:   ' + str(oth_stud_pk))

                    # get notlinked_arr from notlinked charfield
                            linked_arr, notlinked_arr = [], []
                            linked_str = getattr(cur_student, 'linked')
                            if linked_str:
                                linked_arr = linked_str.split(';')
                            notlinked_str = getattr(cur_student, 'notlinked')
                            if notlinked_str:
                                notlinked_arr = notlinked_str.split(';')

                            cur_student_islinked = (other_stud_pk_str in linked_arr)
                            cur_student_notlinked = (other_stud_pk_str in notlinked_arr)

                            if logging_on:
                                logger.debug('mode: ' + str(mode))
                                logger.debug('other_stud_pk_str: ' + str(other_stud_pk_str))
                                logger.debug('linked_arr: ' + str(linked_arr))
                                logger.debug('notlinked_arr: ' + str(notlinked_arr))
                                logger.debug('cur_student_islinked: ' + str(cur_student_islinked))
                                logger.debug('cur_student_notlinked: ' + str(cur_student_notlinked))

                # =====  link ============================
                            if mode == 'tick':
                                link_other = upload_dict.get('linked')

                                if link_other:
                                    # - add oth_stud_pk to linked_arr
                                    if other_stud_pk_str not in linked_arr:
                                        linked_arr.append(other_stud_pk_str)
                                        linked_str = ';'.join(linked_arr)
                                        setattr(cur_student, 'linked', linked_str)
                                    # - remove all occurrencies of oth_stud_pk from unlinked charfield, if exists
                                    # PR2021-09-17 from: https://note.nkmk.me/en/python-list-comprehension/
                                    notlinked_str = ';'.join(
                                        [pk_str for pk_str in notlinked_arr if pk_str != other_stud_pk_str])
                                    setattr(cur_student, 'notlinked', notlinked_str)

                                elif link_other is not None:
                                    # - remove oth_stud_pk from linked_arr
                                    if other_stud_pk_str in linked_arr:
                                        #  -  remove all occurrencies of oth_stud_pk from linked charfield
                                        # PR2021-09-17 from: https://note.nkmk.me/en/python-list-comprehension/
                                        new_linked_str = None
                                        new_linked_arr = [pk_str for pk_str in linked_arr if
                                                          pk_str != other_stud_pk_str]
                                        if new_linked_arr:
                                            new_linked_str = ';'.join(new_linked_arr)
                                        setattr(cur_student, 'linked', new_linked_str)
                                cur_student.save(request=request)

                            #  TODO make_student_biscandidate(cur_student, other_student, request)

                # =====  unlink ============================
                            elif mode == 'cross':
                                # unlink if other_student is different from cur_student:
                                #  -  add oth_stud_pk to notlinked charfield, if not exists yet
                                #  -  remove oth_stud_pk from linked charfield, if exists

                                notlink_other = upload_dict.get('notlinked')

                    # if notlinked: add other_stud_pk_str to notlinked
                                if notlink_other:
                            # - add other_stud_pk_str to notlinked, remove linked if necessary
                                    notlinked_arr.append(other_stud_pk_str)
                                    notlinked_str = ';'.join(notlinked_arr)
                                    setattr(cur_student, 'notlinked', notlinked_str)

                            # - remove all occurrencies of oth_stud_pk from linked charfield
                                    if other_stud_pk_str in linked_arr:
                                        # PR2021-09-17 from: https://note.nkmk.me/en/python-list-comprehension/
                                        new_linked_str = None
                                        new_linked_arr = [pk_str for pk_str in linked_arr if
                                                          pk_str != other_stud_pk_str]
                                        if new_linked_arr:
                                            new_linked_str = ';'.join(new_linked_arr)
                                        setattr(cur_student, 'linked', new_linked_str)
                                        logger.debug('new_linked_str: ' + str(new_linked_str))

                                        cur_student.save(request=request)
                                    else:
                                        # dont update modifiedat when only other_student removed from nonlinked field
                                        cur_student.save()

                                elif notlink_other is not None:

                            # - if notlink_other: remove other_stud_pk_str from notlinked
                                    if other_stud_pk_str in notlinked_arr:
                                        #  -  remove all occurrencies of oth_stud_pk from notlinked charfield
                                        # PR2021-09-17 from: https://note.nkmk.me/en/python-list-comprehension/
                                        new_notlinked_str = None
                                        new_notlinked_arr = [pk_str for pk_str in notlinked_arr if pk_str != other_stud_pk_str]
                                        if new_notlinked_arr:
                                            new_notlinked_str = ';'.join(new_notlinked_arr)
                                        setattr(cur_student, 'linked', new_notlinked_str)
                                        logger.debug('new_linked_str: ' + str(new_notlinked_str))
                                        # dont update modifiedat when only other_student removed from nonlinked field
                                        cur_student.save()

                            if logging_on:
                                logger.debug('cur_student:   ' + str(cur_student))
                                logger.debug('cur_student.linked: ' + str(cur_student.linked))
                                logger.debug('cur_student.notlinked: ' + str(cur_student.notlinked))

                        # - create student_row, also when deleting failed, not when deleted ok, in that case student_row is added in delete_student
                            #TODO this is not used, check if can be removed
                            student_pk = cur_student.pk if cur_student else None
                            updated_rows, error_dictNIU = create_student_rows(
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
                        logger.debug('other_subject.name: ' + str(other_studsubj.schemeitem.subject.name))
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
                                logger.debug('cur_subject.name: ' + str(cur_studsubj.schemeitem.subject.name))
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
            # upload_dict = json.loads(upload_json)

# ----- get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_editNIU, msg_listNIU = \
                dl.get_selected_ey_school_dep_from_usersetting(request)

# +++ validate subjects of all students of this dep, used to update studsubj table
            # TODO to speed up: get info in 1 request, no msg_text
            students = stud_mod.Student.objects.filter(
                school=sel_school,
                department=sel_department
            )

            if students:
                validate_studsubj_list = []
                for student in students:
                    has_error = stud_val.validate_studentsubjects_no_msg(student)
                    if logging_on:
                        logger.debug('student: ' + str(student))
                        logger.debug('has_error: ' + str(has_error))

                    if has_error:
                        if student.pk not in validate_studsubj_list:
                            validate_studsubj_list.append(student.pk)
                if validate_studsubj_list:
                    update_wrap['validate_studsubj_list'] = validate_studsubj_list

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentsubjectValidateAllView


@method_decorator([login_required], name='dispatch')
class StudentsubjectValidateTestView(View):

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectValidateTestView ============= ')

        # function validates studentsubject records after oepning modal, subject are in list PR2021-08-17 PR2021-08-31

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
            sel_examyear, sel_school, sel_department, may_editNIU, msg_listNIU = \
                dl.get_selected_ey_school_dep_from_usersetting(request)

# +++ validate subjects of one student, used in modal
            student_pk = upload_dict.get('student_pk')
            studsubj_dictlist = upload_dict.get('studsubj_dictlist')

            if logging_on:
                logger.debug('sel_examyear: ' + str(sel_examyear))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))
                logger.debug('student_pk: ' + str(student_pk) + ' ' + str(type(student_pk)))
                logger.debug('studsubj_dictlist: ' + str(studsubj_dictlist))
            """
            studsubj_dictlist: [
                {'tobecreated': False, 'tobedeleted': False, 'tobechanged': False, 'schemeitem_id': 1686, 'studsubj_id': 20701, 'subj_id': 113, 'is_extra_counts': False, 'is_extra_nocount': False}, 
                {'tobecreated': False, 'tobedeleted': False, 'tobechanged': False, 'schemeitem_id': 1688, 'studsubj_id': 20703, 'subj_id': 115, 'is_extra_counts': False, 'is_extra_nocount': False}, 
            """
            if student_pk:
                student = stud_mod.Student.objects.get_or_none(id=student_pk)
                if logging_on:
                    logger.debug('sel_school.pk: ' + str(sel_school.pk))
                    logger.debug('sel_department.pk: ' + str(sel_department.pk))
                    logger.debug('student: ' + str(student))

                if student:
                    msg_html = stud_val.validate_studentsubjects_TEST(student, studsubj_dictlist)
                    if msg_html:
                        update_wrap['studsubj_validate_html'] = msg_html
                        if logging_on:
                            logger.debug('msg_html' + str(msg_html))

        if logging_on:
            logger.debug('update_wrap' + str(update_wrap))
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

# - end of StudentsubjectValidateTestView


@method_decorator([login_required], name='dispatch')
class StudentsubjectMultipleOccurrencesView(View):  # PR2021-09-05

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= StudentsubjectMultipleOccurrencesView ============= ')

        # function validates studentsubject records of all students of this dep PR2021-07-10

        update_wrap = {}

# - get permit - only download list when user has permit_crud
        has_permit = af.get_permit_crud_of_this_page('page_studsubj', request)
        if has_permit:
# - reset language
            #user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            #activate(user_lang)

            # - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:

    # ----- get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, may_edit, msg_listNIU = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

    # +++ validate subjects of all students of this dep, used to update studsubj table
                if sel_examyear and sel_school and sel_department and may_edit:
                    dictlist = stud_val.get_multiple_occurrences(sel_examyear, sel_school.base, sel_department.base)

                    if dictlist:
                        update_wrap['validate_multiple_occurrences'] = dictlist

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentsubjectMultipleOccurrencesView



#####################################################################################

@method_decorator([login_required], name='dispatch')
class SendEmailSubmitExformView(View):  # PR2021-07-26 PR2022-04-18
    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= SendEmailSubmitExformView ============= ')

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
                logger.debug('upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'table': 'grade', 'mode': 'submit_save', 'form': 'ex2', 'verificationcode': '', 'verificationkey': None, 'auth_index': 2, 'now_arr': [2022, 4, 18, 11, 21]}
            upload_dict: {'table': 'studsubj', 'form': 'ex4', 'examperiod': 2, 'now_arr': [2022, 5, 31, 7, 29], 'mode': 'request_verif'}
           
            """
# - get permit
            has_permit = False
            req_usr = request.user
            mode = upload_dict.get('mode')
            table = upload_dict.get('table')
            form = upload_dict.get('form')

            if table == 'grade':
                sel_page = 'page_grade'
            elif mode in ('publish_exam', 'submit_grade_exam'):
                sel_page = 'page_exams'
            else:
                sel_page ='page_studsubj'
            if logging_on:
                logger.debug('mode: ' + str(mode))
                logger.debug('sel_page: ' + str(sel_page))
            if req_usr and req_usr.country and req_usr.schoolbase:
                permit_list = req_usr.permit_list(sel_page)
                if permit_list and req_usr.usergroup_list:
                    if 'auth1' in req_usr.usergroup_list or 'auth2' in req_usr.usergroup_list:
                        if table == 'grade':
                            has_permit = 'permit_submit_grade' in permit_list
                        elif mode == 'publish_exam':
                            has_permit = 'permit_publish_exam' in permit_list
                        elif mode in ('submit_grade_exam'):
                            has_permit = 'permit_submit_exam' in permit_list
                        else:
                            has_permit = 'permit_approve_subject' in permit_list

                if logging_on:
                    logger.debug('permit_list: ' + str(permit_list))

            if logging_on:
                logger.debug('mode: ' + str(mode))
                logger.debug('sel_page: ' + str(sel_page))
                logger.debug('has_permit: ' + str(has_permit))

            if has_permit:
                if mode == 'publish_exam':
                    formname = 'ete_exam'
                    sel_school, sel_department = None, None
                    sel_examyear, may_edit, msg_list = dl.get_selected_examyear_from_usersetting(request)
                elif mode == 'submit_grade_exam':
                    formname = 'grade_exam'
                    sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                        dl.get_selected_ey_school_dep_from_usersetting(request)
                else:
                    formname = upload_dict.get('form')
                    sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                        dl.get_selected_ey_school_dep_from_usersetting(request)

                if may_edit:
                    #try:
                    if True:
            # create _verificationcode and key, store in usersetting, send key to client, set expiration to 30 minutes
                        verif_key, verif_code = af.create_verificationcode(formname, request)
                        update_wrap['verificationkey'] = verif_key

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
                                msg_txt = str(_('Enter the verification code and click the ENTER key to submit the Ex form.'))

                            msg_list += ("<p class='pb-0'>",
                                         str(_("We have sent an email with a 6 digit verification code to the email address:")), '</p>',
                                         "<p class='px-4 py-0'>", req_usr.email, '</p>',
                                         "<p class='pb-2'>",
                                         msg_txt,
                                         '</p>')

                    #except Exception as e:
                    #    class_str = 'border_bg_invalid'
                    #    msg_list += ("<p class='pb-2'>",
                    #                       str(_('An error occurred')),':<br><i>', str(e), '</i><br>',
                    #                        str(_('The email has not been sent.')),'</p>')

                if msg_list:
                    msg_wrap_start = ["<div class='p-2 ", class_str, "'>"]
                    msg_wrap_end = ['</p>']

                    msg_html = ''.join(msg_wrap_start + msg_list + msg_wrap_end)

                    # - add  msg_dict to update_wrap
                    update_wrap['approve_msg_html'] = msg_html

    # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

# - end of SendEmailSubmitExformView


#####################################################################################
@method_decorator([login_required], name='dispatch')
class StudentsubjectApproveOrSubmitEx1Ex4View(View):  # PR2021-07-26 PR2022-05-30

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectApproveOrSubmitEx1Ex4View ============= ')

# function sets auth and publish of studentsubject records of current department # PR2021-07-25
        update_wrap = {}
        messages = []
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
            permit_list = req_usr.permit_list('page_studsubj')
            if permit_list:
                # msg_err is made on client side. Here: just skip if user has no or multiple functions

                requsr_usergroup_list = req_usr.usergroup_list
                is_auth1 = (requsr_usergroup_list and 'auth1' in requsr_usergroup_list)
                is_auth2 = (requsr_usergroup_list and'auth2' in requsr_usergroup_list)
                if is_auth1 + is_auth2 == 1:
                    if is_auth1:
                        requsr_auth = 'auth1'
                    elif is_auth2:
                        requsr_auth = 'auth2'
                if requsr_auth:
                    has_permit = 'permit_approve_subject' in permit_list

            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

        if has_permit:

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
                # - not sel_school.activated,
                # not af.is_allowed_depbase_requsr or not af.is_allowed_depbase_school,

                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                # TODO: get sel_examperiod as part from get_selected_ey_school_dep_from_usersetting
                examperiod = upload_dict.get('examperiod')
                prefix = 'reex3_' if examperiod == 3 else 'reex_' if examperiod == 2 else 'subj_'
                form_name = 'ex4ep3' if examperiod == 3 else  'ex4' if examperiod == 2 else 'ex1'

                if examperiod not in (1, 2, 3):
                    msg_list.append(str(_('The exam period is not valid.')))

                if len(msg_list):
                    msg_html = '<br>'.join(msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                else:

    # - get selected mode. Modes are 'approve_test', 'approve_save', 'approve_reset', 'submit_test' 'submit_save'
                    mode = upload_dict.get('mode')
                    is_approve = True if mode in ('approve_test', 'approve_save', 'approve_reset') else False
                    is_submit = True if mode in ('submit_test', 'submit_save') else False
                    is_reset = True if mode == 'approve_reset' else False
                    is_test = True if mode in ('approve_test', 'submit_test') else False

                    if logging_on:
                        logger.debug('upload_dict ' + str(upload_dict))
                        logger.debug('mode:       ' + str(mode))
                        logger.debug('examperiod: ' + str(examperiod))
                        logger.debug('prefix:     ' + str(prefix))
                        logger.debug('form_name:  ' + str(form_name))

# - when mode = submit_submit: check verificationcode.
                    verification_is_ok = True
                    if is_submit and not is_test:
                        upload_dict['form'] = form_name
                        verification_is_ok, verif_msg_html = subj_vw.check_verifcode_local(upload_dict, request)
                        if verif_msg_html:
                            msg_html = verif_msg_html
                        if verification_is_ok:
                            update_wrap['verification_is_ok'] = True

                    if logging_on:
                        logger.debug('verification_is_ok' + str(verification_is_ok))
                        logger.debug('msg_html' + str(msg_html))

                    if verification_is_ok:
                        sel_lvlbase_pk, sel_sctbase_pk, sel_subject_pk, sel_student_pk = None, None, None, None
                        # don't filter on sel_lvlbase_pk, sel_sctbase_pk, sel_subject_pk when is_submit
                        if is_approve:
                            selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                            if selected_dict:
                                sel_lvlbase_pk = selected_dict.get(c.KEY_SEL_LVLBASE_PK)
                                sel_sctbase_pk = selected_dict.get(c.KEY_SEL_SCTBASE_PK)
                                sel_subject_pk = selected_dict.get(c.KEY_SEL_SUBJECT_PK)
                                # TODO filter by cluster
                        if logging_on:
                            logger.debug('is_approve: ' + str(is_approve))
                            logger.debug('sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
                            logger.debug('sel_sctbase_pk: ' + str(sel_sctbase_pk))
                            logger.debug('sel_subject_pk: ' + str(sel_subject_pk))
                            logger.debug('sel_student_pk: ' + str(sel_student_pk))

# +++ get selected studsubj_rows
                        # TODO exclude published rows?? Yes, but count them when checking. You cannot approve or undo approve or submit when submitted
                        # when a subject is set 'tobedeleted', the published info is removed, to show up when submitted
                        crit = Q(student__school=sel_school) & \
                               Q(student__department=sel_department) & \
                               Q(tobedeleted=False) & \
                               Q(student__tobedeleted=False)
            # filter reex subjects when ex4 or ex4ep3
                        if examperiod == 2:
                            crit.add(Q(has_reex=True), crit.connector)
                        elif examperiod == 3:
                            crit.add(Q(has_reex03=True), crit.connector)

            # when submit: don't filter on level, sector, subject or cluster
                        if not is_submit:
                            if sel_lvlbase_pk:
                                crit.add(Q(student__level__base_id=sel_lvlbase_pk), crit.connector)
                                crit.add(Q(schemeitem__scheme__level__base_id=sel_lvlbase_pk), crit.connector)
                            if sel_sctbase_pk:
                                crit.add(Q(student__sector__base_id=sel_sctbase_pk), crit.connector)
                                crit.add(Q(schemeitem__scheme__sector__base_id=sel_sctbase_pk), crit.connector)
                            if sel_subject_pk:
                                crit.add(Q(schemeitem__subject_id=sel_subject_pk), crit.connector)

                        if logging_on:
                            logger.debug('sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
                            logger.debug('sel_sctbase_pk: ' + str(sel_sctbase_pk))
                            logger.debug('sel_subject_pk: ' + str(sel_subject_pk))

                            row_count = stud_mod.Studentsubject.objects.filter(crit).count()
                            logger.debug('row_count:      ' + str(row_count))

                        studsubjects = stud_mod.Studentsubject.objects.filter(crit).order_by('schemeitem__subject__base__code', 'student__lastname', 'student__firstname')

                        count_dict = {'count': 0,
                                      'student_count': 0,
                                      'student_committed_count': 0,
                                      'student_saved_count': 0,
                                      'already_published': 0,
                                      'double_approved': 0,
                                      'committed': 0,
                                      'saved': 0,
                                      'saved_error': 0,
                                      'reset': 0,
                                      'already_approved': 0,
                                      'auth_missing': 0,
                                      'test_is_ok': False
                                    }
                        if studsubjects is not None:

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
                                    examperiod=examperiod,
                                    now_arr=now_arr,
                                    request=request)
                                if published_instance:
                                    published_instance_pk = published_instance.pk
                                    published_instance_filename = published_instance.filename

                            if logging_on:
                                logger.debug('published_instance_pk' + str(published_instance_pk))
                                logger.debug('published_instance_filename' + str(published_instance_filename))

                            studsubj_rows = []

# +++++ loop through studsubjects
                            row_count = 0
                            student_pk_list, student_committed_list, student_saved_list, student_saved_error_list = \
                                [],[], [], []

                            if studsubjects:
                                for studsubj in studsubjects:
                                    row_count += 1

                                    is_committed = False
                                    is_saved = False
                                    is_saved_error = False

                                    if is_approve:
                                        is_committed, is_saved, is_saved_error = approve_studsubj(studsubj, requsr_auth, prefix, is_test, is_reset, count_dict, request)
                                    elif is_submit:
                                        is_committed, is_saved, is_saved_error = submit_studsubj(studsubj, prefix, is_test, published_instance, count_dict, request)

        # - add student_pk to student_pk_list, student_committed_list or student_saved_list
                                    # this is used to count the students in msg: '4 students with 39 subjects are added'
                                    # after the loop the totals are added to count_dict['student_count'] etc
                                    if studsubj.student_id not in student_pk_list:
                                        student_pk_list.append(studsubj.student_id)
                                    if is_committed:
                                        if studsubj.student_id not in student_committed_list:
                                            student_committed_list.append(studsubj.student_id)
                                    if is_saved:
                                        if studsubj.student_id not in student_saved_list:
                                            student_saved_list.append(studsubj.student_id)
                                    if is_saved_error:
                                        if studsubj.student_id not in student_saved_error_list:
                                            student_saved_error_list.append(studsubj.student_id)

        # - add rows to studsubj_rows, to be sent back to page
                                    # to increase speed, dont create return rows but refresh page after finishing this request
                                    """
                                    if not is_test and is_saved:
                                        rows = create_studentsubject_rows(
                                            examyear=sel_examyear,
                                            schoolbase=sel_school.base,
                                            depbase=sel_department.base,
                                            append_dict={},
                                            student_pk=None,
                                            studsubj_pk=studsubj.pk)
                                        if rows:
                                              studsubj_rows.append(rows[0])
                                    """
    # +++++  end of loop through  studsubjects

                            count_dict['count'] = row_count
                            count_dict['student_count'] = len(student_pk_list)
                            count_dict['student_committed_count'] = len(student_committed_list)
                            count_dict['student_saved_count'] = len(student_saved_list)
                            count_dict['student_saved_error_count'] = len(student_saved_error_list)
                            update_wrap['approve_count_dict'] = count_dict

    # - create msg_html with info of rows
                            msg_html = self.create_ex1_ex4_msg_list(
                                count_dict=count_dict,
                                requsr_auth=requsr_auth,
                                is_approve=is_approve,
                                is_test=is_test,
                                examperiod=examperiod,
                                published_instance_filename=published_instance_filename
                            )

# +++++ create Ex1 Ex4 form
                            if row_count:
                                if is_submit and not is_test:
                                    self.create_ex1_ex4_form(
                                        published_instance=published_instance,
                                        sel_examyear=sel_examyear,
                                        sel_school=sel_school,
                                        sel_department=sel_department,
                                        examperiod=examperiod,
                                        prefix=prefix,
                                        save_to_disk=True,
                                        request=request,
                                        user_lang=user_lang)

                    # - delete the 'tobedeleted' rows from StudSubject, only after submitting and no test!
                                    # TODO put back 'tobedeleted' functions
                                    #self.delete_tobedeleted_from_studsubj(
                                    #    published_instance=published_instance,
                                    #    sel_examyear=sel_examyear,
                                    #    sel_school=sel_school,
                                    #    sel_department=sel_department,
                                    #    request=request
                                    #)

                                if (studsubj_rows):
                                    update_wrap['updated_studsubj_approve_rows'] = studsubj_rows

                                if is_test:
                                    committed = count_dict.get('committed', 0)
                                    if committed:
                                        update_wrap['test_is_ok'] = True

    # - add  msg_html to update_wrap
        update_wrap['approve_msg_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))


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


    def create_ex1_ex4_msg_list(self, count_dict, requsr_auth, is_approve, is_test, examperiod, published_instance_filename):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('  ----- create_ex1_ex4_msg_list -----')
            logger.debug('count_dict: ' + str(count_dict))
            logger.debug('is_test: ' + str(is_test))

        count = count_dict.get('count', 0)
        student_count = count_dict.get('student_count', 0)
        committed = count_dict.get('committed', 0)
        student_committed_count = count_dict.get('student_committed_count', 0)
        saved = count_dict.get('saved', 0)
        saved_error = count_dict.get('saved_error', 0)
        student_saved_count = count_dict.get('student_saved_count', 0)
        student_saved_error_count = count_dict.get('student_saved_error_count', 0)
        already_published = count_dict.get('already_published', 0)
        auth_missing = count_dict.get('auth_missing', 0)
        already_approved = count_dict.get('already_approved', 0)
        double_approved = count_dict.get('double_approved', 0)

        if logging_on:
            logger.debug('.....count: ' + str(count))
            logger.debug('.....committed: ' + str(committed))
            logger.debug('.....already_published: ' + str(already_published))
            logger.debug('.....auth_missing: ' + str(auth_missing))
            logger.debug('.....already_approved: ' + str(already_approved))
            logger.debug('.....double_approved: ' + str(double_approved))

        show_warning_msg = False
        show_msg_first_approve_by_pres_secr = False
        if is_test:
            if is_approve:
                class_str = 'border_bg_valid' if committed else 'border_bg_invalid'
            else:
                if committed:
                    if (is_test and auth_missing) or (is_test and double_approved):
                        class_str = 'border_bg_warning'
                        show_warning_msg = True
                    else:
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

        subjects_txt = _('subjects') if examperiod == 1 else _('re-examinations')
        form_txt = _('Ex1') if examperiod == 1 else _('Ex4')

# - create first line with 'The selection contains 4 candidates with 39 subjects'
        msg_list = ["<div class='p-2 ", class_str, "'>"]
        if is_test:
            msg_list.append(''.join(( "<p class='pb-2'>",
                        str(_("The selection contains %(stud)s with %(subj)s.") %
                            {'stud': get_student_count_text(student_count), 'subj': get_subject_count_text(examperiod, count)}),
                        '</p>')))

# - if any subjects skipped: create lines 'The following subjects will be skipped' plus the reason
        if is_test and committed < count:
            willbe_or_are_txt = pgettext_lazy('plural', 'will be') if is_test else _('are')
            msg_list.append("<p class='pb-0'>" + str(_("The following %(cpt)s %(willbe)s skipped")
                                                     % {'cpt': subjects_txt, 'willbe': willbe_or_are_txt}) + ':</p><ul>')
            if already_published:
                msg_list.append('<li>' + str(_("%(val)s already submitted") %
                                             {'val': get_subjects_are_text(examperiod, already_published)}) + ';</li>')
            if auth_missing:
                msg_list.append('<li>' + str(_("%(subj)s not fully approved") %
                                             {'subj': get_subjects_are_text(examperiod, auth_missing)}) + ';</li>')
                show_msg_first_approve_by_pres_secr = True
            if already_approved:
                msg_list.append('<li>' + get_subjects_are_text(examperiod, already_approved) + str(_(' already approved')) + ';</li>')
            if double_approved:
                other_function =  str(_('chairperson')) if requsr_auth == 'auth2' else str(_('secretary'))
                caption = _('subject') if examperiod == 1 else _('re-examination')
                msg_list.append(''.join(('<li>', get_subjects_are_text(examperiod, double_approved),
                                         str(_(' already approved by you as ')), other_function, '.<br>',
                                str(_("You cannot approve a %(cpt)s both as chairperson and as secretary.") % {'cpt': caption} ), '</li>')))
            msg_list.append('</ul>')

# - line with text how many subjects will be approved / submitted
        msg_list.append('<p>')
        if is_test:
            if is_approve:
                if not committed:
                    msg_str = _("No %(cpt)s will be approved.") % {'cpt': subjects_txt}

                else:
                    student_count_txt = get_student_count_text(student_committed_count)
                    subject_count_txt = get_subject_count_text(examperiod, committed)
                    will_be_text = get_will_be_text(committed)
                    approve_txt = _('approved.')
                    msg_str = ' '.join((str(subject_count_txt), str(_('of')),  str(student_count_txt),
                                        str(will_be_text), str(approve_txt)))
            else:
                if not committed:
                    if is_approve:
                        msg_str = _("No %(cpt)s will be approved.") % {'cpt': subjects_txt}
                    else:
                        msg_str = _("The %(frm)s form can not be submitted.") % {'frm': form_txt}
                else:
                    student_count_txt = get_student_count_text(student_committed_count)
                    subject_count_txt = get_subject_count_text(examperiod, committed)
                    will_be_text = get_will_be_text(committed)
                    approve_txt = _('approved.') if is_approve else _('added to the %(frm)s form.') % {'frm': form_txt}
                    msg_str = ' '.join((str(subject_count_txt), str(_('of')),  str(student_count_txt),
                                        str(will_be_text), str(approve_txt)))
        else:
            student_count_txt = get_student_count_text(student_saved_count)
            subject_count_txt = get_subject_count_text(examperiod, saved)
            student_saved_error_count_txt = get_student_count_text(student_saved_error_count)
            subject_error_count_txt = get_subject_count_text(examperiod, saved_error)

# - line with text how many subjects have been approved / submitted
            if is_approve:
                not_str = '' if saved else str(_('not')) + ' '
                msg_str = ''
                if not saved and not saved_error:
                    msg_str = str(_("No subjects have been approved."))
                else:
                    if saved:
                        have_has_been_txt = _('has been') if saved == 1 else _('have been')
                        msg_str = str(_("%(subj)s of %(stud)s %(havehasbeen)s approved.")
                                                % {'subj': subject_count_txt, 'stud': student_count_txt, 'havehasbeen': have_has_been_txt})
                    else:
                        msg_str = str(_("No subjects have been approved."))
                    if saved_error:
                        if msg_str:
                            msg_str += '<br>'
                        could_txt = pgettext_lazy('singular', 'could') if saved_error == 1 else pgettext_lazy('plural', 'could')
                        msg_str += str(_("%(subj)s of %(stud)s %(could)s not be approved because an error occurred.")
                                                % {'subj': subject_error_count_txt, 'stud': student_saved_error_count_txt, 'could': could_txt})

            else:
                not_str = '' if saved else str(_('not')) + ' '
                msg_str = str(_("The %(frm)s form has %(not)s been submitted.") % {'frm': form_txt, 'not': not_str})
                if saved:
                    student_count_txt = get_student_count_text(student_saved_count)
                    subject_count_txt = get_subject_count_text(examperiod, saved)
                    file_name = published_instance_filename if published_instance_filename else '---'
                    msg_str += ''.join(('<br>',
                        str(_("It contains %(subj)s of %(stud)s.") % {'stud': student_count_txt, 'subj': subject_count_txt}),
                        '<br>', str(_("The %(frm)s form has been saved as '%(val)s'.") % {'frm': form_txt, 'val': file_name}),
                        '<br>', str(_("Go to the page 'Archive' to download the file."))
                    ))

        msg_list.append(str(msg_str))
        msg_list.append('</p>')

# - warning if any subjects are not fully approved
        if show_warning_msg and not is_approve:
            msg_list.append("<div class='pt-2'><b>")
            msg_list.append(str(_('WARNING')))
            msg_list.append(':</b><br>')
            msg_list.append(str(_('There are subjects that are not fully approved.')))
            msg_list.append(' ')
            msg_list.append(str(_('They will not be included in the %(frm)s form.') % {'frm': form_txt}))
            msg_list.append(' ')
            msg_list.append(str(_('Are you sure you want to submit the %(frm)s form?') % {'frm': form_txt}))
            msg_list.append('</div>')

# - add line 'both prseident and secretary must first approve all subjects before you can submit the Ex form
        if show_msg_first_approve_by_pres_secr:
            msg_txt = ''.join(('<div>', str(_('The chairperson and the secretary must approve all %(cpt)s before you can submit the %(frm)s form.') % {'cpt': subjects_txt, 'frm': form_txt}   ), '</div>'))
            msg_list.append(msg_txt)

        msg_list.append('</div>')

        msg_html = ''.join(msg_list)
        return msg_html
# - end of create_ex1_ex4_msg_list


    def create_ex1_ex4_form(self, published_instance, sel_examyear, sel_school, sel_department,
                                    examperiod, prefix, save_to_disk, request, user_lang):
        #PR2021-07-27 PR2021-08-14
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= create_ex1_ex4_form ============= ')
            logger.debug('examperiod: ' + str(examperiod))
            logger.debug('save_to_disk: ' + str(save_to_disk))

# +++ create Ex1 xlsx file
        if examperiod == 1:

            # get text from examyearsetting
            settings = awpr_lib.get_library(sel_examyear, ['exform', 'ex1'])
            # if logging_on:
            #    logger.debug('settings: ' + str(settings))

            grd_exc.create_ex1_xlsx(
                published_instance=published_instance,
                examyear=sel_examyear,
                school=sel_school,
                department=sel_department,
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
                school=sel_school,
                department=sel_department,
                examperiod=examperiod,
                prefix=prefix,
                save_to_disk=save_to_disk,
                request=request,
                user_lang=user_lang)
    # - end of create_ex1_ex4_form

# --- end of StudentsubjectApproveOrSubmitEx1Ex4View


#################################################################################
@method_decorator([login_required], name='dispatch')
class StudentsubjectApproveSingleView(View):  # PR2021-07-25

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectApproveSingleView ============= ')

# function sets auth and publish of studentsubject records of current department # PR2021-07-25
        update_wrap = {}
        msg_list = []

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = req_usr.permit_list('page_studsubj')
            if permit_list:
                has_permit = 'permit_approve_subject' in permit_list
            if logging_on and False:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

# - reset language
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
                # - not sel_school.activated,
                # not af.is_allowed_depbase_requsr or not af.is_allowed_depbase_school,

                sel_examyear, sel_school, sel_department, may_edit, err_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)
                if err_list:
                    msg_list.extend(err_list)
                else:

# - get list of studentsubjects from upload_dict
                    studsubj_list = upload_dict.get('studsubj_list')
                    if studsubj_list:
                        studsubj_rows = []
# -------------------------------------------------
# - loop through list of uploaded studentsubjects
                        for studsubj_dict in studsubj_list:
                            student_pk = studsubj_dict.get('student_pk')
                            studsubj_pk = studsubj_dict.get('studsubj_pk')
                            if logging_on:
                                logger.debug('---------- ')
                                logger.debug('  student_pk: ' + str(student_pk))
                                logger.debug('  studsubj_pk: ' + str(studsubj_pk))

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
                                logger.debug('student: ' + str(student))
                                logger.debug('studsubj: ' + str(studsubj))

# +++ update studsubj
                            if student and studsubj:
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
                                    examyear=sel_examyear,
                                    schoolbase=sel_school.base,
                                    depbase=sel_department.base,
                                    requsr_same_school=True,  # check for same_school is included in may_edit
                                    setting_dict={},
                                    append_dict=append_dict,
                                    request=request,
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


def approve_studsubj(studsubj, requsr_auth, prefix, is_test, is_reset, count_dict, request):
    # PR2021-07-26 PR2022-05-30
    # auth_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
    #  prefix = 'reex3_'  'reex_'  'subj_'
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- approve_studsubj -----')
        logger.debug('requsr_auth:  ' + str(requsr_auth))
        logger.debug('prefix:  ' + str(prefix))
        logger.debug('is_reset:     ' + str(is_reset))

    is_committed = False
    is_saved = False
    is_saved_error = False
    if studsubj:
        req_user = request.user

# - skip if this studsubj is already published
        published = getattr(studsubj, prefix + 'published')
        if logging_on:
            logger.debug('published:    ' + str(published))

        if published:
            count_dict['already_published'] += 1
        else:
            requsr_authby_field = prefix + requsr_auth + 'by'

# - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved
            auth1by = getattr(studsubj, prefix +'auth1by')
            auth2by = getattr(studsubj, prefix +'auth2by')
            if logging_on:
                logger.debug('requsr_authby_field: ' + str(requsr_authby_field))
                logger.debug('auth1by:      ' + str(auth1by))
                logger.debug('auth2by:      ' + str(auth2by))

            save_changes = False

# - remove authby when is_reset
            if is_reset:
                setattr(studsubj, requsr_authby_field, None)
                count_dict['reset'] += 1
                save_changes = True
            else:

# - skip if this studsubj is already approved
                requsr_authby_value = getattr(studsubj, requsr_authby_field)
                requsr_authby_field_already_approved = True if requsr_authby_value else False
                if logging_on:
                    logger.debug('requsr_authby_field_already_approved: ' + str(requsr_authby_field_already_approved))
                if requsr_authby_field_already_approved:
                    count_dict['already_approved'] += 1
                else:

# - skip if this author (like 'chairperson') has already approved this studsubj
        # under a different permit (like 'secretary' or 'corrector')
                    logger.debug('>>> requsr_auth: ' + str(requsr_auth))
                    logger.debug('>>> req_user:    ' + str(req_user))
                    logger.debug('>>> auth1by:     ' + str(auth1by))
                    logger.debug('>>> auth2by:     ' + str(auth2by))

                    double_approved = False
                    if requsr_auth == 'auth1':
                        double_approved = True if auth2by and auth2by == req_user else False
                    elif requsr_auth == 'auth2':
                        double_approved = True if auth1by and auth1by == req_user else False
                    if logging_on:
                        logger.debug('double_approved: ' + str(double_approved))

                    if double_approved:
                        count_dict['double_approved'] += 1
                    else:
                        setattr(studsubj, requsr_authby_field, req_user)

                        save_changes = True
                        if logging_on:
                            logger.debug('save_changes: ' + str(save_changes))

# - set value of requsr_authby_field
            if save_changes:
                if is_test:
                    count_dict['committed'] += 1
                    is_committed = True
                else:
# - save changes
                    try:
                        studsubj.save(request=request)
                        is_saved = True
                        count_dict['saved'] += 1
                    except Exception as e:
                        logger.error(getattr(e, 'message', str(e)))
                        is_saved_error = True
                        count_dict['saved_error'] += 1

    return is_committed, is_saved, is_saved_error
# - end of approve_studsubj


def submit_studsubj(studsubj, prefix, is_test, published_instance, count_dict, request):
    # PR2021-01-21 PR2021-07-27 PR2022-05-30
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- submit_studsubj -----')
        logger.debug('     prefix: ' + str(prefix))

    is_committed = False
    is_saved = False
    is_saved_error = False

    if studsubj:

# - check if this studsubj is already published
        published = getattr(studsubj, prefix + 'published')
        if logging_on:
            logger.debug('     subj_published: ' + str(published))

        if published:
            count_dict['already_published'] += 1
        else:

# - check if this studsubj / examtype is approved by all auth
            auth1by = getattr(studsubj, prefix + 'auth1by')
            auth2by = getattr(studsubj, prefix + 'auth2by')
            auth_missing = auth1by is None or auth2by is None
            if logging_on:
                logger.debug('auth1by: ' + str(auth1by))
                logger.debug('auth2by: ' + str(auth2by))
                logger.debug('auth_missing: ' + str(auth_missing))
            if auth_missing:
                count_dict['auth_missing'] += 1
            else:
# - check if all auth are different
                double_approved = auth1by == auth2by
                if logging_on:
                    logger.debug('double_approved: ' + str(double_approved))
                if double_approved and not auth_missing:
                    count_dict['double_approved'] += 1
                else:
# - set value of published_instance and exatmtype_status field
                    if is_test:
                        count_dict['committed'] += 1
                        is_committed = True
                    else:

                        try:
# - put published_id in field subj_published
                            setattr(studsubj, prefix + 'published', published_instance)
# - save changes
                            studsubj.save(request=request)
                            is_saved = True
                            count_dict['saved'] += 1
                        except Exception as e:
                            logger.error(getattr(e, 'message', str(e)))
                            is_saved_error = True
                            count_dict['saved_error'] += 1

    return is_committed, is_saved, is_saved_error
# - end of submit_studsubj


def create_published_Ex1_Ex4_instance(sel_school, sel_department, examperiod, now_arr, request):  # PR2021-07-27
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_published_Ex1_Ex4_instance -----')
        logger.debug('     request.user: ' + str(request.user))

    # create new published_instance and save it when it is not a test (this function is only called when it is not a test)
    # filename is added after creating file in create_ex1_xlsx
    depbase_code = sel_department.base.code if sel_department.base.code else '-'
    school_code = sel_school.base.code if sel_school.base.code else '-'
    school_abbrev = sel_school.abbrev if sel_school.abbrev else '-'

    # to be used when submitting Ex4 form
    examtype_caption = ''
    exform = 'Ex4 3e tijdvak' if examperiod == 3 else 'Ex4' if examperiod == 2 else 'Ex1' if examperiod == 1 else '-'
    examtype_caption = 'tv3' if examperiod == 3 else 'tv2' if examperiod == 2 else 'tv1' if examperiod == 1 else '-'

    today_date = af.get_date_from_arr(now_arr)

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

    published_instance = sch_mod.Published.objects.create(
        school=sel_school,
        department=sel_department,
        examtype=None,
        examperiod=examperiod,
        name=file_name,
        datepublished=today_date,
        modifiedat=timezone.now,
        modifiedby=request.user
    )
    # Note: filefield 'file' gets value on creating Ex form

    published_instance.filename = file_name + '.xlsx'
    # PR2021-09-06 debug: request.user is not saved in instance.save, don't know why
    published_instance.save(request=request)

    if logging_on:
        logger.debug('     published_instance.saved: ' + str(published_instance))
        logger.debug('     published_instance.pk: ' + str(published_instance.pk))

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

            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)

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
                            row_dict['CURRENT'] = 'Subject: ' + str(current_subject.name) + ', Subjecttype: ' + current_sjtype.abbrev

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
class StudentsubjectUploadView(View):  # PR2020-11-20 PR2021-08-17 PR2021-09-28

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectUploadView ============= ')

        # function creates, deletes and updates studentsubject records of current student PR2020-11-21
        update_wrap = {}
        messages = []

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = req_usr.permit_list('page_studsubj')
            if permit_list:
                has_permit = 'permit_crud' in permit_list
            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

        if has_permit:

        # - check for double subjects, double subjects are not allowed -> happens in create_studsubj PR2021-07-11
        # - TODO when deleting: return warning when subject grades have values

# - reset language
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
                # - not sel_school.activated,
                # not af.is_allowed_depbase_requsr or not af.is_allowed_depbase_school,

                sel_examyear, sel_school, sel_department, may_edit, err_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))
                    logger.debug('sel_examyear: ' + str(sel_examyear))
                    logger.debug('sel_school: ' + str(sel_school))
                    logger.debug('sel_department: ' + str(sel_department))

# - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                student = None

                if len(err_list):
                    msg_html = '<br>'.join(err_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                elif may_edit:
                    student_pk = upload_dict.get('student_pk')
                    student = stud_mod.Student.objects.get_or_none(
                        id=student_pk,
                        school=sel_school,
                        department=sel_department
                    )
                if logging_on:
                    logger.debug('student: ' + str(student))

# - get list of studentsubjects from upload_dict
                studsubj_list = None
                if student:
                    studsubj_list = upload_dict.get('studsubj_list')
                if studsubj_list:

# - get schemitem_info of the scheme of this student, separately, instead of getting t for each subject, should be faster
                    schemeitems_dict = subj_vw.get_scheme_si_dict(sel_examyear.pk, sel_department.base_id, student.scheme_id)

                    updated_rows = []

# -------------------------------------------------
# - loop through list of uploaded studentsubjects
                    for studsubj_dict in studsubj_list:
                        # values of mode are: 'delete', 'create', 'update'
                        mode = studsubj_dict.get('mode')
                        studsubj_pk = studsubj_dict.get('studsubj_pk')
                        schemeitem_pk = studsubj_dict.get('schemeitem_pk')

                        if logging_on:
                            logger.debug('---------- ')
                            logger.debug('studsubj mode: ' + str(mode))
                            logger.debug('studsubj_pk: ' + str(studsubj_pk))
                            logger.debug('schemeitem_pk: ' + str(schemeitem_pk))

                        append_dict = {}

# - get current studsubj - when mode is 'create': studsubj is None. It will be created at "elif mode == 'create'"
                        studsubj = stud_mod.Studentsubject.objects.get_or_none(
                            id=studsubj_pk,
                            student=student
                        )
                        if logging_on:
                            logger.debug('studsubj: ' + str(studsubj))

# +++ delete studsubj ++++++++++++
                        if mode == 'delete':
                            # published fields are: subj_published, exem_published, reex_published, reex3_published, pok_published
                            # if published: don't delete, but set 'tobedeleted' = True, so its remains in the Ex1 form
                            #       also remove approved and published info
                            #       also set grades 'tobedeleted'=True
                            # if not published: delete studsubj, grades will be cascade deleted
                            if studsubj:
                                deleted_ok = delete_studentsubject(student, studsubj, updated_rows, err_list, request)

# +++ create new studentsubject, also create grade of first examperiod
                        elif mode == 'create':
                            schemeitem = subj_mod.Schemeitem.objects.get_or_none(id=schemeitem_pk)
                            error_list = []


                            studsubj = create_studsubj(student, schemeitem, messages, error_list, request, False)  # False = don't skip_save

                            if studsubj:
                                append_dict['created'] = True
                            elif error_list:
                                # TODO check if error is dispalyed correctly PR2021-07-21
                                # yes, but messages html is displayed in msg_box. This one not in use??
                                append_dict['err_create'] = ' '.join(error_list)

                            if logging_on:
                                logger.debug('schemeitem: ' + str(schemeitem))
                                logger.debug('studsubj: ' + str(studsubj))
                                logger.debug('append_dict: ' + str(append_dict))

# +++ update existing studsubj - also when studsubj is created - studsubj is None when deleted
                        if studsubj and mode in ('create', 'update'):
                            si_pk = studsubj.schemeitem_id
                            si_dict = schemeitems_dict.get(si_pk)
                            err_fields = []
                            update_studsubj(studsubj, studsubj_dict, si_dict, sel_examyear, sel_school, sel_department, err_list, err_fields, request)

# - add update_dict to update_wrap
                        if studsubj:

                            studsubj_pk_list = [studsubj.pk] if studsubj.pk else None
                            rows = create_studentsubject_rows(
                                examyear=sel_examyear,
                                schoolbase=sel_school.base,
                                depbase=sel_department.base,
                                requsr_same_school=True,  # check for same_school is included in may_edit
                                setting_dict={},
                                append_dict=append_dict,
                                request=request,
                                student_pk=student.pk,
                                studsubj_pk_list=studsubj_pk_list
                            )
                            if logging_on:
                                logger.debug('rows: ' + str(rows))

                            if rows:
                                studsubj_row = rows[0]
                                if studsubj_row:
                                    updated_rows.append(studsubj_row)
# - end of loop
# -------------------------------------------------
                    if len(err_list):
                        msg_html = '<br>'.join(err_list)
                        messages.append({'class': "border_bg_invalid", 'msg_html': msg_html})

                    if updated_rows:
                        update_wrap['updated_studsubj_rows'] = updated_rows

# +++ validate subjects of student
                        # no message necessary, done by test before saving
                        #msg_html = stud_val.Fstudent)
                        #if msg_html:
                        #    update_wrap['studsubj_validate_html'] = msg_html
                        #if logging_on:
                        #    logger.debug('msg_html: ' + str(msg_html))

                    has_error = stud_val.validate_studentsubjects_no_msg(student)
                    update_wrap['subj_error'] = has_error
                    update_wrap['stud_pk'] = student.pk

        if len(messages):
            update_wrap['messages'] = messages

        if logging_on:
            logger.debug('update_wrap: ' + str(update_wrap))
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of StudentsubjectUploadView


def delete_studentsubject(student, studsubj, updated_rows, err_list, request):
    # --- delete student # PR2021-07-18 PR2022-02-16

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_studentsubject ----- ')
        logger.debug('studsubj: ' + str(studsubj))

    deleted_ok = False

# - create updated_row - to be returned after successfull delete
    updated_row = {'stud_id': student.pk,
                          'studsubj_id': studsubj.pk,
                          'mapid': 'studsubj_' + str(student.pk) + '_' + str(studsubj.pk),
                          'deleted': True}

    this_txt = None
    if studsubj.schemeitem:
        subject = studsubj.schemeitem.subject
        if subject and subject.name:
            this_txt = _("Subject '%(tbl)s' ") % {'tbl': subject.name}

# - check if studentsubject has submitted grades or school is locked or examyear is locked PR2021-08-21
    # PR2022-02-15 studentsubject can always be deleted

    try:
        # delete studentsubject will also cascade delete grades, studentsubjectnote, noteattachment
        deleted_ok = sch_mod.delete_instance(studsubj, [], err_list, request, this_txt)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    else:
# - add deleted_row to updated_rows
        deleted_ok = True
        studsubj = None
        updated_rows.append(updated_row)

    if logging_on:
        logger.debug('deleted_ok: ' + str(deleted_ok))
        logger.debug('updated_rows' + str(updated_rows))
        logger.debug('err_list' + str(err_list))

    return deleted_ok
# - end of delete_studentsubject


####################################################

@method_decorator([login_required], name='dispatch')
class StudentsubjectSingleUpdateView(View):  # PR2021-09-18

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectSingleUpdateView ============= ')

        # function updates single studentsubject record
        update_wrap = {}
        msg_list = []
        err_fields = []

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = req_usr.permit_list('page_studsubj')
            has_permit = 'permit_crud' in permit_list

            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

        if not has_permit:
            msg_list.append(str(_("You don't have permission to perform this action.")))
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

                # check requsr_same_school is part of get_selected_ey_school_dep_from_usersetting
                sel_examyear, sel_school, sel_department, may_edit, err_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)
                if err_list:
                    err_list.append(str(_('You cannot make changes.')))
                    msg_list.extend(err_list)
                else:
                    if logging_on:
                        logger.debug('upload_dict' + str(upload_dict))
                        logger.debug('sel_examyear: ' + str(sel_examyear))
                        logger.debug('sel_school: ' + str(sel_school))
                        logger.debug('sel_department: ' + str(sel_department))

# - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                    student_pk = upload_dict.get('student_pk')
                    student = stud_mod.Student.objects.get_or_none(
                        id=student_pk,
                        school=sel_school,
                        department=sel_department
                    )
                    if logging_on:
                        logger.debug('msg_list: ' + str(msg_list))
                        logger.debug('may_edit: ' + str(may_edit))
                        logger.debug('student: ' + str(student))

# - get studentsubject from upload_dict
                    studsubj_pk = upload_dict.get('studsubj_pk')
                    studsubj = stud_mod.Studentsubject.objects.get_or_none(
                        id=studsubj_pk,
                        student=student
                    )
                    if studsubj:
                        if logging_on:
                            logger.debug('studsubj: ' + str(studsubj))

                        studsubj_pk_list = [studsubj.pk]

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
                        updated_pk_list = update_studsubj(
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

                        if logging_on:
                            logger.debug('updated_pk_list: ' + str(updated_pk_list))

                        if updated_pk_list:
                            studsubj_pk_list.extend(updated_pk_list)

                        if msg_list:
                            update_wrap['msg_list'] = msg_list

# - add update_dict to update_wrap
                        # TODO check value of msg_dict
                        #  msg_dict['err_' + field] = str(_("Title and subjects only allowed in subjects with character 'Werkstuk'."))
                        #  msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')
                        append_dict = {}
                        if err_fields:
                            append_dict['err_fields'] = err_fields

                        studsubj_rows = create_studentsubject_rows(
                            examyear=sel_examyear,
                            schoolbase=sel_school.base,
                            depbase=sel_department.base,
                            requsr_same_school=True,  # check for same_school is included in may_edit
                            setting_dict={},
                            append_dict=append_dict,
                            request=request,
                            student_pk=student.pk,
                            studsubj_pk_list=studsubj_pk_list
                        )
                        if studsubj_rows:
                            update_wrap['updated_studsubj_rows'] = studsubj_rows

        if msg_list:
            msg_html = '<br>'.join(msg_list)
            update_wrap['msg_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentsubjectSingleUpdateView


#######################################################
def update_studsubj(studsubj_instance, upload_dict, si_dict, sel_examyear, sel_school, sel_department,
                    msg_list, err_fields, request):  # PR2019-06-06 PR2021-12-25 PR2022-04-15
    # --- update existing and new studsubj_instance PR2019-06-06
    # called by StudentsubjectUploadView, StudentsubjectSingleUpdateView, StudentsubjectApproveSingleView

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_studsubj -------')
        logger.debug('upload_dict: ' + str(upload_dict))
        # upload_dict{'mode': 'update', 'studsubj_pk': 26993, 'schemeitem_pk': 2033, 'subj_auth2by': 48}
        # upload_dict: {'student_pk': 9224, 'studsubj_pk': 67818, 'has_reex': False}
        # upload_dict: {'student_pk': 9226, 'studsubj_pk': 67836, 'subj_auth2by': True}

    save_changes = False
    recalc_finalgrade = False
    studsubj_pk_list = []
    for field, new_value in upload_dict.items():

# +++ save changes in studsubj_instance fields
        if field in ['schemeitem_pk']:
            saved_schemeitem = getattr(studsubj_instance, 'schemeitem')
            new_schemeitem = subj_mod.Schemeitem.objects.get_or_none(pk=new_value)
            if logging_on:
                logger.debug('saved_schemeitem: ' + str(saved_schemeitem))
                logger.debug('new_schemeitem: ' + str(new_schemeitem))

            if new_schemeitem is None:
                msg_list.append(str(_("Subject scheme of this subject is not found.")))

            elif saved_schemeitem:
                if new_schemeitem.pk != saved_schemeitem.pk:
                    setattr(studsubj_instance, 'schemeitem', new_schemeitem)
            # - also remove approved and published info
                    # TODO also from grades??
                    setattr(studsubj_instance, 'subj_auth1by', None)
                    setattr(studsubj_instance, 'subj_auth2by', None)
                    setattr(studsubj_instance, 'subj_published', None)

                    save_changes = True
                    recalc_finalgrade = True

                    if logging_on:
                        logger.debug('>>>>> new_schemeitem save')

        elif field in ['pws_title', 'pws_subjects']:
            # only allowed when subjecttype has_pws = True
            if not studsubj_instance.schemeitem.subjecttype.has_pws:
                if new_value:
                    subj_name = studsubj_instance.schemeitem.subject.name
                    msg_list.append(str(_("Title and subjects are not allowed in subject %(cpt)s.") % {'cpt': subj_name}))
            else:
                saved_value = getattr(studsubj_instance, field)
                if logging_on:
                    logger.debug('saved_value: ' + str(saved_value))
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
                    logger.debug('saved_value: ' + str(saved_value))

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

                # don't check if the amount of re-examinations equals or exceeds the maximum
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
                    logger.debug(' delete reex, field: ' + str(saved_value))
                    logger.debug(' delete reex, saved_value: ' + str(saved_value))
                    logger.debug(' delete reex, new_value: ' + str(saved_value))

        # - save when new_value != saved_value
                if new_value != saved_value:

        # - check if deleting is allowed
                    #  check if grade is authorized, published or blocked
                    err_list = grad_val.validate_exem_sr_reex_reex03_delete_allowed(studsubj_instance, field)

                    if err_list:
                        msg_list.extend(err_list)
                        err_fields.append(field)
                    else:
        # - set has_exemption etc False
                        setattr(studsubj_instance, field, new_value)
                        save_changes = True
                        recalc_finalgrade = True
                        must_add_delete_exem_reex_reex03 = True
                        if logging_on:
                            logger.debug(' removed reex, field: ' + str(field) + ' ' + str(new_value))

        # - when deleting exemption: also delete exemption_year PR2022-04-15
                        if field == 'has_exemption':
                            setattr(studsubj_instance, 'exemption_year', None)

# --- add exem, reex, reex03 grade or make grade 'tobedeleted'
            # when adding: also pu values of segrade, srgrade and pegrade in new grade_instance
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
            logger.error(getattr(e, 'message', str(e)))
            msg_list.append(str(_('An error occurred. The changes have not been saved.')))
        else:
            if recalc_finalgrade:
                grades = stud_mod.Grade.objects.filter(
                    studentsubject=studsubj_instance,
                    tobedeleted=False
                )
                for grade_instance in grades:
                # - recalculate gl_sesr, gl_pece, gl_final, gl_use_exem in studsubj record
                    if grade_instance.examperiod == c.EXAMPERIOD_FIRST:
                        # when first examperiod: also update and save grades in reex, reex03, if exist
                        grd_view.recalc_finalgrade_in_reex_reex03_grade_and_save(grade_instance, si_dict)

                sql_studsubj_list, sql_student_list = \
                    grd_view.update_studsubj_and_recalc_student_result(
                        sel_examyear, sel_school, sel_department, studsubj_instance.student)
                if sql_studsubj_list:
                    calc_res.save_studsubj_batch(sql_studsubj_list)

                    # save calculated fields in student
                if sql_student_list:
                    calc_res.save_student_batch(sql_student_list)

    if logging_on:
        logger.debug('msg_list: ' + str(msg_list))
        logger.debug('  ..... end of update_studsubj .....')
    return studsubj_pk_list
# --- end of update_studsubj


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
    if True:
    #try:
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
                    logger.debug('     grade tobedeleted: ' + str(grade.tobedeleted))
        # - if grade exists: it must be deleted row. Undelete
                setattr(grade, 'tobedeleted', False)
                if logging_on:
                    logger.debug('     grade tobedeleted: ' + str(grade.tobedeleted))
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
                setattr(grade, 'tobedeleted', True)
                save_changes = True

                if logging_on:
                    logger.debug('     set grade tobedeleted: ' + str(grade.tobedeleted))

        if save_changes:
            grade.save(request=request)
            if logging_on:
                logger.debug('     saved_changes: ')

    #except Exception as e:
    #    logger.error(getattr(e, 'message', str(e)))
    #    err_list.append(str(_('An error occurred. The changes have not been saved.')))

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
                "AND NOT grd.tobedeleted AND NOT studsubj.tobedeleted"
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


def save_result_etc_in_student(student_dict, last_student_ep_dict, result_info_list, sql_student_list):  # PR2021-12-30

    # function saves result and grade info in return list sql_student_values

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------- save_result_etc_in_student ----------- ')
        logger.debug('last_student_ep_dict: ' + str(last_student_ep_dict))
    """
    last_student_ep_dict: {
    'ep': 3, 
    'final': {'sum': -3986, 'cnt': 7, 
            'info': ' ne:- pa:6 en:-(vr) wk:4 mm12:-(vr) ac:-(h3) combi:-', 'avg': None, 
            'result': 'Gemiddeld eindcijfer: - (-/7) '}, 
    'combi': {'sum': -1993, 'cnt': 3, 'info': ' mm1:- cav:-(vr) lo:5', 'final': None, 
            'result': 'Combinatiecijfer: - (-/3) '}, 
    'pece': {'sumX10': -29967, 'cnt': 4, 'info': ' ne:- en:-(vr) wk:3,0 ac:-(h3)', 'avg': None, 
            'result': 'Gemiddeld CE-cijfer: - (-/4) '}, 
    'count': {'c3': 0, 'c4': 1, 'c5': 0, 'c6': 1, 'c7': 0, 'core4': 1, 'core5': 0}, 
    'noin': {'sr': ['ne'], 'ce': ['ne'], 'vr': {'en': ['SE', 'CE'], 'ec': ['SE', 'CE'], 'mm12': ['SE'], 'cav': ['SE']}, 'se': ['mm1'], 'h3': ['ac']}, 
    'failed': {'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.']}, 
    'result_index': 0, 
    'noin_info': ['Vrijstelling: en(SE,CE) ec(SE,CE) mm12(SE) cav(SE) niet ingevuld', 'Schoolexamen: mm1 niet ingevuld', 'Herkansing schoolexamen: ne niet ingevuld', 'Centraal examen: ne niet ingevuld', 'Herexamen 3e tijdvak: ac niet ingevuld']}
    """

    sql_student_values = []
    try:
        student_id = student_dict.get('stud_id')
        gl_ce_avg = af.get_dict_value(last_student_ep_dict, ('pece', 'avg'))
        gl_combi_avg = af.get_dict_value(last_student_ep_dict, ('combi', 'final'))
        gl_final_avg = af.get_dict_value(last_student_ep_dict, ('final', 'avg'))
        result_index = last_student_ep_dict.get('result_index') or 0

        gl_ce_avg_str = ''.join(("'",  str(gl_ce_avg), "'")) if gl_ce_avg else 'NULL'
        gl_combi_avg_str = ''.join(("'",  str(gl_combi_avg), "'")) if gl_combi_avg else 'NULL'
        gl_final_avg_str = ''.join(("'",  str(gl_final_avg), "'")) if gl_final_avg else 'NULL'

        result_index_str = str(result_index) if result_index else '0'
        result_status_str = ''.join(("'", c.RESULT_CAPTION[result_index], "'")) if c.RESULT_CAPTION[result_index] else 'NULL'

        result_info = '|'.join(result_info_list) if result_info_list else None
        result_info_str = ''.join(("'",  result_info, "'")) if result_info else 'NULL'

        e1_ce_avg = af.get_dict_value(last_student_ep_dict, ('pece', 'avg'))
        e1_combi_avg = af.get_dict_value(last_student_ep_dict, ('combi', 'final'))
        e1_final_avg = af.get_dict_value(last_student_ep_dict, ('final', 'avg'))
        e1_result_index_str = str(result_index) if result_index else '0'

        e1_ce_avg_str = ''.join(("'",  str(e1_ce_avg), "'")) if e1_ce_avg else 'NULL'
        e1_combi_avg_str = ''.join(("'",  str(e1_combi_avg), "'")) if e1_combi_avg else 'NULL'
        e1_final_avg_str = ''.join(("'",  str(e1_final_avg), "'")) if e1_final_avg else 'NULL'

        e2_ce_avg = af.get_dict_value(last_student_ep_dict, ('pece', 'avg'))
        e2_combi_avg = af.get_dict_value(last_student_ep_dict, ('combi', 'final'))
        e2_final_avg = af.get_dict_value(last_student_ep_dict, ('final', 'avg'))
        e2_result_index_str = str(result_index) if result_index else '0'

        e2_ce_avg_str = ''.join(("'",  str(e2_ce_avg), "'")) if e2_ce_avg else 'NULL'
        e2_combi_avg_str = ''.join(("'",  str(e2_combi_avg), "'")) if e2_combi_avg else 'NULL'
        e2_final_avg_str = ''.join(("'",  str(e2_final_avg), "'")) if e2_final_avg else 'NULL'

        if logging_on:
            logger.debug('gl_ce_avg_str: ' + str(gl_ce_avg_str))
            logger.debug('gl_combi_avg_str: ' + str(gl_combi_avg_str))
            logger.debug('gl_final_avg_str: ' + str(gl_final_avg_str))

            logger.debug('result_index_str: ' + str(result_index_str))
            logger.debug('result_status_str: ' + str(result_status_str))
            logger.debug('result_info_str: ' + str(result_info_str))
        """
        (3811, NULL, '6', NULL, 0, 'Geen uitslag', "'Uitslag: GEEN UITSLAG|Centraal examen: ne,en,wk,nask1,nask2,ta niet  "ingevuld', 
        0, 0, 0, 0, 0, 
        NULL, '6', NULL, 0, 
        NULL, '6', NULL, 0)
        """

        sql_student_values = [ str(student_id),
            gl_ce_avg_str, gl_combi_avg_str, gl_final_avg_str,
            result_index_str, result_status_str,  result_info_str,
            e1_ce_avg_str, e1_combi_avg_str, e1_final_avg_str, e1_result_index_str,
            e2_ce_avg_str, e2_combi_avg_str, e2_final_avg_str, e2_result_index_str
        ]


        """
        sql_keys = {'stud_id': student_id}
        sql_list = ["UPDATE students_student AS stud",
                    " SET gl_ce_avg = ", gl_ce_avg_str,
                    ", gl_combi_avg = ", gl_combi_avg_str,
                    ", gl_final_avg = ", gl_final_avg_str,
                    ", result = ", str(result_index),
                    ", result_status = ", result_status_str,
                    ", result_info = ", result_info_str,
                    " WHERE stud.id = %(stud_id)s::INT"
                  ]
        sql = ''.join(sql_list)

        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
        """

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return sql_student_values
# --- end of save_result_etc_in_student


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
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

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
def delete_student(student_instance, updated_rows, err_list, request):
    # --- delete student # PR2021-07-18 PR2022-02-16

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_subject ----- ')
        logger.debug('student_instance: ' + str(student_instance))

    deleted_ok = False

# - create updated_row - to be returned after successfull delete
    updated_row = {'id': student_instance.pk,
                   'mapid': 'student_' + str(student_instance.pk),
                   'deleted': True}

    this_txt = _("Candidate '%(tbl)s' ") % {'tbl': student_instance.fullname}
    header_txt = _("Delete candidate")

# - check if student has submitted subjects PR2021-08-21 PR2022-05-15

    has_publ_studsubj = stud_mod.Studentsubject.objects.filter(
        student=student_instance,
        subj_published_id__isnull=False
    ).exists()
    if has_publ_studsubj:
        msg_html = ''.join((
            str(_('This candidate has submitted subjects.')), '<br>',
            str(_('You cannot delete %(cpt)s.') % {'cpt': str(_('This candidate')).lower()})
        ))
        msg_dict = {'header': header_txt, 'class': 'border_bg_warning', 'msg_html': msg_html}
        err_list.append(msg_dict)
    else:

        try:

            # delete student will also cascade delete studsubj, Grades, Studentsubjectnote, Noteattachment
            deleted_ok = sch_mod.delete_instance(student_instance, [], err_list, request, this_txt, header_txt)
            if logging_on:
                logger.debug('deleted_ok: ' + str(deleted_ok))


        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
        else:
    # - add deleted_row to updated_rows
            deleted_ok = True
            updated_rows.append(updated_row)

    # - check if this student also exists in other examyears.
            # PR2022-02-15 deleting student_base not necessary, student will be set tobedeleted
            #students_exist = stud_mod.Student.objects.filter(base_id=base_pk).exists()
        # - If not: delete also subject_base
            #if not students_exist:
            #    student_base = stud_mod.Studentbase.objects.get_or_none(id=base_pk)
            #    if student_base:
            #        student_base.delete()

        if logging_on:
            logger.debug('updated_rows' + str(updated_rows))
            logger.debug('err_list' + str(err_list))

    return deleted_ok
# - end of delete_student


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
def create_student(school, department, upload_dict, messages, error_list, request, skip_save):
    # --- create student # PR2019-07-30 PR2020-10-11  PR2020-12-14 PR2021-06-15
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' +++++++++++++++++ create_student +++++++++++++++++ ')

# - create but don't save studentbase
    # save studentbase at the end, to prevent studentbases without student
    studentbase = stud_mod.Studentbase()

    student = None
    if studentbase and school:

# - get value of 'idnumber', 'lastname', 'firstname', 'prefix'
        id_number = upload_dict.get('idnumber')
        last_name = upload_dict.get('lastname')
        first_name = upload_dict.get('firstname')
        prefix = upload_dict.get('prefix')

        lastname_stripped = last_name.strip() if last_name else ''
        firstname_stripped = first_name.strip() if first_name else ''
        prefix_stripped = prefix.strip() if prefix else ''
        full_name = stud_val.get_prefix_lastname_comma_firstname(lastname_stripped, firstname_stripped, prefix_stripped)

        msg_list = []
        has_error = False

        idnumber_nodots, msg_err, birthdate_dteobjNIU = stud_val.get_idnumber_nodots_stripped_lower(id_number)
        if msg_err:
            has_error = True
            msg_list.append(str(msg_err))

        msg_err = av.validate_notblank_maxlength(lastname_stripped, c.MAX_LENGTH_FIRSTLASTNAME, _('The last name'))
        if msg_err:
            has_error = True
            msg_list.append(str(msg_err))

        msg_err = av.validate_notblank_maxlength(firstname_stripped, c.MAX_LENGTH_FIRSTLASTNAME, _('The first name'))
        if msg_err:
            has_error = True
            msg_list.append(str(msg_err))

        if not has_error:
# - validate if student already exists
            # either student, not_found or has_error is trueish
            student, not_found, has_error = \
                stud_val.lookup_student_by_idnumber_nodots(
                    school=school,
                    department=department,
                    idnumber_nodots=idnumber_nodots,
                    upload_fullname=full_name,
                    error_list=msg_list,
                    found_is_error=True
                )

        if logging_on:
            logger.debug('msg_list: ' + str(msg_list))

        if has_error:
            #  messages is list of dicts with format: {'field': fldName, header': header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html}
            msg_html = '<br>'.join(msg_list)
            messages.append({'header': str(_('Add candidate')), 'class': "border_bg_invalid", 'msg_html': msg_html})
            error_list.extend(msg_list)
            if logging_on:
                logger.debug('msg_list: ' + str(msg_list))
        else:

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

# - create and save student
            try:
                student = stud_mod.Student(
                    base=studentbase,
                    school=school,
                    lastname=last_name,
                    firstname=first_name,
                    idnumber=id_number,
                    department=department,
                    iseveningstudent=is_evening_student,
                    islexstudent=is_lex_student
                )
                if not skip_save:
                    student.save(request=request)

# - also activate school if not activated PR2021-07-20
                    if student:
                        school = student.school
                        if school:
                            activated = getattr(school, 'activated')
                            if not activated:
                                setattr(school, 'activated', True)
                                setattr(school, 'activatedat', timezone.now())
                                # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
                                school.save(request=request)

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

                name = ' '.join([first_name, last_name])
                #  messages is list of dicts with format: {'field': fldName, header': header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html}
                err_01 = str(_('An error occurred:'))
                err_02 = str(e)
                err_03 = str(_("%(cpt)s '%(val)s' could not be added.") % {'cpt': str(_('Candidate')), 'val': name})
                error_list.extend((err_01, err_02, err_03))

                msg_html = '<br>'.join((err_01, '<i>' + err_02 + '</i>', err_03))
                messages.append({'class': "alert-danger", 'msg_html': msg_html})

    if logging_on:
        student_pk = student.pk if student else 'None'
        logger.debug('student:    ' + str(student))
        logger.debug('student_pk: ' + str(student_pk))
        logger.debug('messages:   ' + str(messages))
        logger.debug('error_list: ' + str(error_list))

    return student

# - end of create_student

#######################################################
def update_student_instance(instance, sel_examyear, sel_school, sel_department, upload_dict,
                            idnumber_list, examnumber_list, msg_list, error_list, request, skip_save):
    # --- update existing and new instance PR2019-06-06 PR2021-07-19 PR2022-04-11 PR2022-06-04

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_student_instance -------')
        logger.debug('upload_dict: ' + str(upload_dict))
        logger.debug('instance:    ' + str(instance))
        instance_pk = instance.pk if instance else 'None'
        logger.debug('instance.pk: ' + str(instance_pk))
    """
    upload_dict: {'mode': 'withdrawn', 'table': 'student', 'student_pk': 4053, 'withdrawn': True}
    """
# ----- get user_lang
    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT

    changes_are_saved = False
    save_error = False
    field_error = False

    if instance:
        save_changes = False
        update_scheme = False
        recalc_regnumber = False
        remove_exemptions = False
        recalc_passed_failed = False

        for field, new_value in upload_dict.items():
            #try:
            if True:
    # - save changes in fields 'lastname', 'firstname'
                if field in ['lastname', 'firstname']:
                    saved_value = getattr(instance, field)

                    if isinstance(new_value, int):
                        new_value = str(new_value)

                    if new_value != saved_value:
                        if logging_on:
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

                    if isinstance(new_value, int):
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
                        msg_list.append({'class': "border_bg_warning", 'msg_html': err_txt})
                    else:
                        saved_value = getattr(instance, field)

                        if new_gender != saved_value:
                            if logging_on:
                                logger.debug('gender saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
                                logger.debug('gender new_gender:  ' + str(new_gender) + ' ' + str(type(new_gender)))

                            setattr(instance, field, new_gender)
                            save_changes = True
                            recalc_regnumber = True

                elif field in ('idnumber', 'examnumber'):
                    has_error = False
                    caption = ''

                    if isinstance(new_value, int):
                        new_value = str(new_value)

                    if new_value:
                        if field == 'idnumber':
                            caption = _('ID-number')
                # when updating single student, idnumber_list is not filled yet. in that case: get idnumber_list
                            if not idnumber_list:
                                idnumber_list = stud_val.get_idnumberlist_from_database(instance.school)
                # check if new_value already exists in idnumber_list, but skip idnumber of this instance
                            if idnumber_list:
                                for row in idnumber_list:
                                    # row is a tuple with (id, idnumber)
                                    if row[1] == new_value:
                                        # unsaved instance has id = None
                                        skip_own_idnumber = False
                                        saved_id = getattr(instance, 'id')
                                        if saved_id:
                                            if saved_id and row[0] == saved_id:
                                                skip_own_idnumber = True
                                        if not skip_own_idnumber:
                                            has_error = True
                                            field_error = True
                                        break

                            if not has_error:
                                # add new_value to idnumber_list if it doesn't exist yet
                                idnumber_list.append(new_value)

                        elif field == 'examnumber':
                            caption = _('Exam number')
                # when uploading students: examnumber_list is filled, unless there were no examnumbers
                            if examnumber_list and new_value in examnumber_list:
                                has_error = True
                            else:
                # when updating single student, examnumber_list is not filled. Use validate_examnumber_exists instead
                                has_error = stud_val.validate_examnumber_exists(instance, new_value)

                # add new_value to examnumber_list if it doesn't exist yet
                            if not has_error:
                                examnumber_list.append(new_value)

                # validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                    if has_error:
                        field_error = True
                        err_txt = _("%(cpt)s '%(val)s' already exists.") \
                                  % {'cpt': str(caption), 'val': new_value}
                        error_list.append(err_txt)
                        msg_list.append({'class': "border_bg_warning", 'msg_html': err_txt})
                    else:
                        saved_value = getattr(instance, field)

                        if logging_on and new_value != saved_value:
                            logger.debug(
                                'idnumber examnumber saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
                            logger.debug('idnumber examnumber new_value: ' + str(new_value) + ' ' + str(type(new_value)))

                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
                            if field == 'examnumber':
                                recalc_regnumber = True
                            if logging_on:
                                logger.debug('setattr(instance, field, new_value: ' + str(new_value))

    # 2. save changes in birthdate field
                elif field == 'birthdate':
                    # new_value has format of date-iso, Excel ordinal format is already converted
                    saved_dateobj = getattr(instance, field)

                    new_dateobj = af.get_date_from_ISO(new_value)

                    if new_dateobj != saved_dateobj:
                        if logging_on:
                            logger.debug('birthdate saved: ' + str(saved_dateobj) + ' ' + str(type(saved_dateobj)))
                            logger.debug('birthdate new  : ' + str(new_dateobj) + ' ' + str(type(new_dateobj)))

                        setattr(instance, field, new_value)
                        save_changes = True

    # 2. save changes in text fields
                elif field in ('prefix', 'birthcountry', 'birthcity', 'classname', 'diplomanumber', 'gradelistnumber'):
                    saved_value = getattr(instance, field)

                    if isinstance(new_value, int):
                        new_value = str(new_value)

                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True
                        if logging_on:
                            logger.debug('save_changes field: ' + field + ' new_value: ' + str(new_value))

    # 3. save changes in department, level or sector
                # department cannot be changed
                # change 'profiel' into 'sector
                elif field in ('level', 'sector', 'profiel'):
                    if field == 'profiel':
                        field = 'sector'

                    new_lvl_or_sct = None
                    school = getattr(instance, 'school')
                    if school:
                        examyear = getattr(school, 'examyear')
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

                    # new_value is levelbase_pk or sectorbase_pk
                    if new_lvl_or_sct != saved_lvl_or_sct:
                        if logging_on:
                            logger.debug('saved ' + str(field) + ': ' + str(saved_lvl_or_sct) + ' ' + str(type(saved_lvl_or_sct)))
                            logger.debug('new   ' + str(field) + ': ' + str(new_lvl_or_sct) + ' ' + str(type(new_lvl_or_sct)))

                        setattr(instance, field, new_lvl_or_sct)
                        save_changes = True
                        update_scheme = True

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
                    if logging_on:
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
                elif field in ('iseveningstudent', 'islexstudent', 'partial_exam', 'has_dyslexie'):
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
                                    msg_list.append({'class': "border_bg_warning", 'msg_html': '<br>'.join((err_txt1, err_txt2))})
                                else:
                                    remove_exemptions = True

                        if not has_published_exemptions:
                            setattr(instance, field, new_value)
                            save_changes = True

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

            if logging_on:
                logger.debug('     dep:    ' + str(department) + ' ' + str(type(department)))
                logger.debug('     level:  ' + str(level) + ' ' + str(type(level)))
                logger.debug('     sector: ' + str(sector) + ' ' + str(type(sector)))
                logger.debug('     scheme: ' + str(scheme) + ' ' + str(type(scheme)))

            if scheme is None:
                msg_arr = []
                if department.level_req:
                    if level is None:
                        msg_arr.append(str(_("The 'leerweg' is not entered.")))
                if sector is None:
                    if department.has_profiel:
                        msg_arr.append(str(_("The 'profiel' is not entered.")))
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
            school_code, examyear_code, depbase, levelbase = None, None, None, None

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
            depbase_code = depbase.code if depbase else None
            levelbase_code = levelbase.code if levelbase else None
            new_regnumber = stud_fnc.calc_regnumber(school_code, gender, str(examyear_code), examnumber, depbase_code, levelbase_code)

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
                sel_lvlbase_pk = instance.level.base_id  if instance.level else None
                log_list = calc_res.calc_batch_student_result(
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
    # --- update_scheme_in_studsubj # PR2021-03-13
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_scheme_in_studsubj ----- ')
        logger.debug('     student: ' + str(student))

    if student:
        # - update scheme in student, also remove if necessary
        new_scheme = subj_mod.Scheme.objects.get_or_none(
            department=student.department,
            level=student.level,
            sector=student.sector)
        setattr(student, 'scheme', new_scheme)

        if logging_on:
            logger.debug('     new_scheme: ' + str(new_scheme))

    # - loop through studsubj of this student
        studsubjects = stud_mod.Studentsubject.objects.filter(
            student=student
        )
        for studsubj in studsubjects:
            if new_scheme is None:
                # delete studsubj when no scheme
                # check if studsubj is submitted, set tobedeleted = True if submitted
                #PR2022-05-18 debug: Omega College: grades have disappeared
                set_studsubj_tobedeleted_or_tobechanged(studsubj, True, None, request)  # True = tobedeleted
            else:
                old_subject = studsubj.schemeitem.subject
                old_subjecttype = studsubj.schemeitem.subjecttype

                if logging_on:
                    logger.debug('     old_subject: ' + str(old_subject))
                    logger.debug('     old_subjecttype: ' + str(old_subjecttype))

        # skip when studsub scheme equals new_scheme
                if studsubj.schemeitem.scheme != new_scheme:
        # check how many times this subject occurs in new scheme
                    count_subject_in_newscheme = subj_mod.Schemeitem.objects.filter(
                        scheme=new_scheme,
                        subject=old_subject
                        ).count()
                    if logging_on:
                        logger.debug('     count_subject_in_newscheme: ' + str(count_subject_in_newscheme))

                    if not count_subject_in_newscheme:
        # delete studsub when subject does not exist in new_scheme
                        # check if studsubj is submitted, set tobedeleted = True if submitted
                        set_studsubj_tobedeleted_or_tobechanged(studsubj, True, None, request)  # True = tobedeleted

                    elif count_subject_in_newscheme == 1:
        # if subject occurs only once in new_scheme: replace schemeitem by new schemeitem
                        new_schemeitem = subj_mod.Schemeitem.objects.get_or_none(
                            scheme=new_scheme,
                            subject=old_subject
                        )
                        if new_schemeitem:
                            # change schemeitem in studsubj, set tobechanged = True if submitted
                            set_studsubj_tobedeleted_or_tobechanged(studsubj, False, new_schemeitem, request)  # False = tobechanged
                    else:
        # if subject occurs multiple times in new_scheme: check if one exist with same subjecttype
                        new_schemeitem = subj_mod.Schemeitem.objects.get_or_none(
                            scheme=new_scheme,
                            subject=old_subject,
                            subjecttype=old_subjecttype
                        )
                        if new_schemeitem:
                            studsubj.schemeitem = new_schemeitem
                            studsubj.save(request=request)
                        else:
        # if no schemeitem exist with same subjecttype: get schemeitem with lowest sequence
                            new_schemeitem = subj_mod.Schemeitem.objects.filter(
                                scheme=new_scheme,
                                subject=studsubj.schemeitem.subject
                            ).order_by('subjecttype__base__sequence').first()
                            if new_schemeitem:
                                studsubj.schemeitem = new_schemeitem
                                studsubj.save(request=request)


def set_studsubj_tobedeleted_or_tobechanged(studsubj, tobedeleted, new_schemeitem, request):
    # PR2021-08-23
    # delete studsubj when no scheme
    # check if studsubj is submitted, set delete = True if submitted
    # called by  update_scheme_in_studsubj 3 times

    #PR2022-05-18 CAL, Omega: all subjects disappear.
    # Cause: tobedeleted is set True. Dont know why yet
    subj_published = getattr(studsubj, 'subj_published')

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' >>>>>>>>>>>> ----- set_studsubj_tobedeleted_or_tobechanged ----- ')
        logger.debug('studsubj: ' + str(studsubj))
        logger.debug('tobedeleted: ' + str(tobedeleted))
        logger.debug('new_schemeitem: ' + str(new_schemeitem))

    if tobedeleted:
        field = 'tobedeleted'
        if subj_published is None:
            studsubj.delete(request=request)

            if logging_on:
                logger.debug('studsubj.delete: ' + str(field))
    else:
        field = 'tobechanged'
        setattr(studsubj, 'schemeitem', new_schemeitem)

        if logging_on:
            logger.debug('tobechanged: ' + str(field))

    if subj_published:
        setattr(studsubj, field, True)
        setattr(studsubj,'prev_auth1by', getattr(studsubj, 'subj_auth1by'))
        setattr(studsubj,'prev_auth2by', getattr(studsubj, 'subj_auth2by'))
        setattr(studsubj,'prev_published', subj_published)

        if logging_on:
            logger.debug('if subj_published: ' + str(field))

        studsubj.save(request=request)
# - end of set_studsubj_tobedeleted_or_tobechanged

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_studsubj(student, schemeitem, messages, error_list, request, skip_save):
    # --- create student subject # PR2020-11-21 PR2021-07-21
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_studsubj ----- ')
        logger.debug('student: ' + str(student))
        logger.debug('schemeitem: ' + str(schemeitem))

    has_error = False
    studsubj = None
    if student and schemeitem:
        subject_name = schemeitem.subject.name if schemeitem.subject and schemeitem.subject.name else '---'

# - check if student already has this subject, with same or different schemeitem
        msg_err = None
        studsubjects = stud_mod.Studentsubject.objects.filter(
            student=student,
            schemeitem__subject=schemeitem.subject
        )
        if studsubjects is not None:
            doubles_found = False
            undelete_studsubj = False
            row_count, deleted_count = 0, 0
            for studsubj in studsubjects:
                row_count += 1
                if studsubj.tobedeleted:
                    deleted_count += 1

            if row_count:
    # - doubles_found = True when non-deleted records found:
                if row_count > deleted_count:
                    doubles_found = True
                elif deleted_count > 1:
    # - doubles_found = True when multiple deleted records found:
                    doubles_found = True
                else:
    # - when only 1 deleted found: undelete, also undelete grades
                    undelete_studsubj = True

            if doubles_found:
                has_error = True
                err_01 = str(_("%(cpt)s '%(val)s' already exists.") % {'cpt': _('Subject'), 'val': subject_name})
                # error_list not in use when using modal form, message is displayed in modmesasges
                error_list.append(err_01)

                # this one closes modal and shows modmessage with msg_html
                msg_dict = {'header': _('Add subject'), 'class': 'border_bg_warning', 'msg_html': err_01}
                messages.append(msg_dict)

            elif undelete_studsubj:
                # TODO this undelete feature is not tested yet PR2021-07-11
                deleted_studsubj = stud_mod.Studentsubject.objects.get_or_none(
                    student=student,
                    deleted=True
                )
                if not skip_save:
                    if deleted_studsubj:
                        try:
                            setattr(deleted_studsubj, 'deleted', False)
                            setattr(deleted_studsubj, 'schemeitem', schemeitem)
                            deleted_studsubj.save(request=request)
                            # also undelete grades
                            deleted_grades = stud_mod.Grade.objects.filter(
                                deleted_studsubj=deleted_studsubj,
                                deleted=True
                            )
                            if deleted_grades:
                                for deleted_grade in deleted_grades:
                                    setattr(deleted_grade, 'deleted', False)
                                    deleted_grade.save(request=request)
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

# - create and save Studentsubject
        if not has_error:
            try:
                studsubj = stud_mod.Studentsubject(
                    student=student,
                    schemeitem=schemeitem
                )
                if not skip_save:
                    studsubj.save(request=request)
                # also create grade of first examperiod
                grade = stud_mod.Grade(
                    studentsubject=studsubj,
                    examperiod=c.EXAMPERIOD_FIRST
                )
                if not skip_save:
                    grade.save(request=request)
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
            studsubj = None

    return studsubj
# - end of create_studsubj


#/////////////////////////////////////////////////////////////////

def create_studentsubject_rows(examyear, schoolbase, depbase, requsr_same_school, setting_dict,
                               append_dict, request, student_pk=None, studsubj_pk_list=None, cluster_pk_list=None):
    # --- create rows of all students of this examyear / school PR2020-10-27 PR2022-01-10 studsubj_pk_list added
    # PR2022-02-15 show only not tobeleted students and studentsubjects
    # PR2022-03-23 cluster_pk_list added, to return studsubj with changed clustername
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_studentsubject_rows ============= ')
        logger.debug('student_pk: ' + str(student_pk))
        logger.debug('studsubj_pk_list: ' + str(studsubj_pk_list))
        logger.debug('setting_dict: ' + str(setting_dict))
        logger.debug('append_dict: ' + str(append_dict))
        logger.debug('cluster_pk_list: ' + str(cluster_pk_list))

    rows = []
    try:
        # create list of students of this school / examyear, possibly with filter student_pk or studsubj_pk
        # with left join of studentsubjects with deleted=False
        # when role is other than school: only when submitted, don't show students without submitted subjects
        sel_examyear_pk = examyear.pk if examyear else None
        sel_schoolbase_pk = schoolbase.pk if schoolbase else None
        sel_depbase_pk = depbase.pk if depbase else None

        # dont show students without subject on other users than sameschool
        #PR2022-01-10 also use inner join when studsubj_pk_list has values: only these records must be returned
        left_or_inner_join = "LEFT JOIN" if requsr_same_school and not studsubj_pk_list else "INNER JOIN"

        sel_lvlbase_pk = None
        if c.KEY_SEL_LVLBASE_PK in setting_dict:
            sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)

        sel_sctbase_pk = None
        if c.KEY_SEL_SCTBASE_PK in setting_dict:
            sel_sctbase_pk = setting_dict.get(c.KEY_SEL_SCTBASE_PK)

        sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk, 'db_id': sel_depbase_pk}
        sql_studsubj_list = ["SELECT studsubj.id AS studsubj_id, studsubj.student_id,",
            "cl.id AS cluster_id, cl.name AS cluster_name, si.id AS schemeitem_id, si.scheme_id AS scheme_id,",
            "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_thumbrule,",
            "studsubj.pws_title, studsubj.pws_subjects,",
            "studsubj.has_exemption, studsubj.has_sr, studsubj.has_reex, studsubj.has_reex03, studsubj.exemption_year, studsubj.pok_validthru,",
            "si.subject_id, si.subjecttype_id, si.gradetype,",
            "subjbase.id AS subjbase_id, subjbase.code AS subj_code, subj.name AS subj_name,",
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
            "SUBSTRING(au.username, 7) AS modby_username",

            "FROM students_studentsubject AS studsubj",

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
            "WHERE NOT studsubj.tobedeleted"]

        # studsubj are only visible for other users than sameschool when they are published
        if not requsr_same_school:
            # PR2021-09-04 debug: examyears before 2022 have no subj_published_id. Show them to others anyway
            if examyear is None or examyear.code >= 2022:
                sql_studsubj_list.append("AND studsubj.subj_published_id IS NOT NULL")

        sql_studsubjects = ' '.join(sql_studsubj_list)

        sql_list = ["WITH studsubj AS (" + sql_studsubjects + ")",
            "SELECT st.id AS stud_id, studsubj.studsubj_id, studsubj.subjbase_id, studsubj.schemeitem_id, studsubj.cluster_id, studsubj.cluster_name,",
            "CONCAT('studsubj_', st.id::TEXT, '_', studsubj.studsubj_id::TEXT) AS mapid, 'studsubj' AS table,",
            "st.lastname, st.firstname, st.prefix, st.examnumber,",
            "st.scheme_id, st.iseveningstudent, st.islexstudent, st.classname, ",
            "st.tobedeleted AS st_tobedeleted, st.reex_count, st.reex03_count, st.bis_exam, st.withdrawn,",
            "studsubj.subject_id AS subj_id, studsubj.subj_code, studsubj.subj_name,",
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
            "WHERE school.base_id = %(sb_id)s::INT",
                    "AND school.examyear_id = %(ey_id)s::INT",
                    "AND dep.base_id = %(db_id)s::INT",
                    "AND NOT st.tobedeleted"]

        if sel_lvlbase_pk:
            sql_list.append('AND lvl.base_id = %(lvlbase_id)s::INT')
            sql_keys['lvlbase_id'] = sel_lvlbase_pk
        if sel_sctbase_pk:
            sql_list.append('AND sct.base_id = %(sctbase_id)s::INT')
            sql_keys['sctbase_id'] = sel_sctbase_pk
        if student_pk:
            sql_keys['st_id'] = student_pk
            sql_list.append('AND st.id = %(st_id)s::INT')

        sel_subjbase_pk = None
        if c.KEY_SEL_SUBJBASE_PK in setting_dict:
            sel_subjbase_pk = setting_dict.get(c.KEY_SEL_SUBJBASE_PK)

        acc_view.get_userfilter_allowed_subjbase(
            request=request,
            sql_keys=sql_keys,
            sql_list=sql_list,
            subjbase_pk=sel_subjbase_pk,
            skip_allowed_filter=False,
            table='studsubj'
        )

        # also return existing studsubj of updated clusters, to show changed name in table
        # - filter on studsubj_pk_list with ANY clause
        # - PR2022-03-23 see https://stackoverflow.com/questions/34627026/in-vs-any-operator-in-postgresql
        if cluster_pk_list:
            sql_keys['cls_pk_list'] = cluster_pk_list
            if studsubj_pk_list:
                sql_keys['ss_pk_list'] = studsubj_pk_list
                sql_list.append("AND ( studsubj.studsubj_id = ANY(%(ss_pk_list)s::INT[]) OR studsubj.cluster_id = ANY(%(cls_pk_list)s::INT[]) )  ")
            else:
                sql_list.append("AND studsubj.cluster_id = ANY(%(cls_pk_list)s::INT[])")
        else:
            if studsubj_pk_list:
                sql_keys['ss_pk_list'] = studsubj_pk_list
                sql_list.append("AND studsubj.studsubj_id = ANY(%(ss_pk_list)s::INT[])")

        sql_list.append('ORDER BY st.id, studsubj.studsubj_id NULLS FIRST')

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys) + ' ' + str(type(sql_keys)))
            #logger.debug('sql: ' + str(sql) + ' ' + str(type(sql)))
            #logger.debug('connection.queries: ' + str(connection.queries))

    # - full name to rows
        for row in rows:
            #if logging_on:
            #    logger.debug('row: ' + str(row))
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

    # - add messages to all studsubj_rows, only when student_pk or studsubj_pk_list have value
            if append_dict and student_pk or studsubj_pk_list:
                for key, value in append_dict.items():
                    row[key] = value

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
            sel_examyear_instance = af.get_selected_examyear_instance_from_usersetting(request)
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


#/////////////////////////////////////////////////////////////////
def create_orderlist_rows(request, sel_examyear):
    # --- create rows of all schools with published subjects PR2021-08-18
    # PR2022-02-15 filter also on student.tobedeleted=False
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== students.view create_orderlist_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    # create list of schools of this examyear (CUR and SXM), only where defaultrole = school
    # for sxm: only sxm schools
    # with left join of studentsubjects with deleted=False, group by school_id with count(*)


    #logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk))
    #logger.debug('sel_schoolbase_pk: ' + str(sel_schoolbase_pk))
    #logger.debug('sel_depbase_pk: ' + str(sel_depbase_pk))


#CASE WHEN  POSITION(';" + sch.otherlang + ";' IN CONCAT(';', subj.otherlang, ';')) > 0 THEN ELSE END

    """
    
    "si.ete_exam AS si_ete_exam,",
    CASE WHEN subj.otherlang IS NULL OR sch.otherlang IS NULL  THEN 'ne'   ELSE
    CASE WHEN POSITION(sch.otherlang IN subj.otherlang) > 0 THEN sch.otherlang ELSE 'ne' END END AS lang
    
    or even better with delimiters:
    CASE WHEN subj.otherlang IS NULL OR sch.otherlang IS NULL 
        THEN 
            'ne' 
        ELSE
            CASE WHEN POSITION(';" + sch.otherlang + ";' IN CONCAT(';', subj.otherlang, ';')) > 0 
                THEN 
                ELSE 
            END
    END    
    
    """
    rows = []
    if sel_examyear:

        requsr_country_pk = request.user.country.pk
        is_curacao = request.user.country.abbrev.lower() == 'cur'
        show_sxm_only = "AND ey.country_id = %(requsr_country_pk)s::INT" if not is_curacao else ''

        sel_exam_period = 1
        sql_keys = {'ey_code_int': sel_examyear.code,
                    'ex_period_int': sel_exam_period,
                    'default_role': c.ROLE_008_SCHOOL,
                    'requsr_country_pk': requsr_country_pk}

        sql_sublist = ["SELECT st.school_id AS school_id, publ.id AS subj_published_id, count(*) AS publ_count,",
            "publ.datepublished, publ.examperiod",

            "FROM students_studentsubject AS studsubj",
            "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",

            "INNER JOIN schools_published AS publ ON (publ.id = studsubj.subj_published_id)",
            "WHERE publ.examperiod = %(ex_period_int)s::INT",
            "AND NOT st.tobedeleted AND NOT studsubj.tobedeleted",

            "GROUP BY st.school_id, publ.id, publ.datepublished, publ.examperiod"
        ]
        sub_sql = ' '.join(sql_sublist)

        total_sublist = ["SELECT st.school_id AS school_id, count(*) AS total",
            "FROM students_studentsubject AS studsubj",
            "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
            "WHERE NOT st.tobedeleted AND NOT studsubj.tobedeleted",
            "GROUP BY st.school_id"
        ]
        total_sql = ' '.join(total_sublist)
        # see https://www.postgresqltutorial.com/postgresql-group-by/
        total_students_sublist = ["SELECT st.school_id, count(*) AS total_students",
            "FROM students_student AS st",
            "WHERE NOT st.tobedeleted",
            "GROUP BY st.school_id"
        ]
        total_students_sql = ' '.join(total_students_sublist)

        sql_list = ["WITH sub AS (", sub_sql, "), total AS (", total_sql, "), total_students AS (", total_students_sql, ")",
            "SELECT sch.id AS school_id, schbase.code AS schbase_code, sch.abbrev AS school_abbrev, sub.subj_published_id,",
            "total.total, total_students.total_students, sub.publ_count, sub.datepublished, sub.examperiod",

            "FROM schools_school AS sch",
            "INNER JOIN schools_schoolbase AS schbase ON (schbase.id = sch.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",

            "LEFT JOIN sub ON (sub.school_id = sch.id)",
            "LEFT JOIN total ON (total.school_id = sch.id)",
            "LEFT JOIN total_students ON (total_students.school_id = sch.id)",

            "WHERE schbase.defaultrole = %(default_role)s::INT",
            "AND ey.code = %(ey_code_int)s::INT",
            show_sxm_only,
            "ORDER BY sch.id"
            ]
        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

            for row in rows:
                published_pk = row.get('subj_published_id')
                if published_pk:
        # can't use sql because of file field
                    published = sch_mod.Published.objects.get_or_none(pk=published_pk)
                    if published and published.file:
                        row['file_name'] = str(published.file)
                        row['url'] = published.file.url

    return rows
# --- end of create_orderlist_rows


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_cluster(school, department, subject, cluster_pk, cluster_name, mapped_cluster_pk_dict, request):
    # --- create cluster # PR2022-01-06
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' +++++++++++++++++ create_cluster +++++++++++++++++ ')

    err_list = []
    new_cluster_pk = None
    if school and department and subject:
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
                    school=school,
                    department=department,
                    name__iexact=new_value
                )
                if name_exists:
                    err_list.append(str(_("%(cpt)s '%(val)s' already exists.") \
                                        % {'cpt': _('Cluster name') , 'val': new_value} ))
                else:
# - create and save cluster
                    cluster = subj_mod.Cluster(
                        school=school,
                        department=department,
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
            err_list.append(str(_("%(cpt)s '%(val)s' could not be added.") % {'cpt': str(_('Cluster')), 'val': new_value}))

    return err_list, new_cluster_pk
# - end of create_cluster


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def delete_cluster(cluster, request):
    # --- delete cluster # PR2022-01-06

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_cluster ----- ')
        logger.debug('cluster: ' + str(cluster))

    deleted_ok = False
    err_list = []
    deleted_cluster_pk = None
# - create updated_row - to be returned after successfull delete
    #updated_row = {'id': cluster.pk, 'deleted': True}

    this_txt = ''.join((str(_('Cluster')), " '", cluster.name, "' "))
    header_txt = _("Delete cluster")

# - delete cluster
    error_list = []
    tobedeleted_cluster_pk = cluster.pk
    deleted_ok = sch_mod.delete_instance(cluster, [], error_list, request, this_txt, header_txt)
    if logging_on:
        logger.debug('deleted_ok' + str(deleted_ok))
        logger.debug('error_list' + str(error_list))

    if error_list:
        err_list.extend(error_list)
    if deleted_ok:
        deleted_cluster_pk = tobedeleted_cluster_pk

# - add deleted_row to updated_rows
    #if deleted_ok:
    #    updated_rows.append(updated_row)

# - check if this cluster is used in studsubj
        #  not necessary,  cluster has on_delete=SET_NULL in studsubj

    if logging_on:
        #logger.debug('updated_rows' + str(updated_rows))
        logger.debug('err_list' + str(err_list))

    return deleted_ok, err_list, deleted_cluster_pk
# - end of delete_cluster


def update_cluster_instance(school, department, instance, upload_dict, request):
# --- update existing cluster name PR2022-01-10
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_cluster_instance -------')

    err_list = []
    updated_cluster_pk = None
    if instance:
        try:
            field = 'name'

# - get value of 'cluster_name'
            cluster_name = upload_dict.get('cluster_name')
            new_value = cluster_name.strip() if cluster_name else None

# - save changes in fields 'name'
            saved_value = getattr(instance, field)

            if new_value != saved_value:

# - validate length of cluster name
                msg_err = av.validate_notblank_maxlength(new_value, c.MAX_LENGTH_KEY, _('The cluster name'))
                if msg_err:
                    err_list.append(msg_err)
                else:

# - validate if cluster already exists
                    name_exists = subj_mod.Cluster.objects.filter(
                        school=school,
                        department=department,
                        name__iexact=new_value
                    )
                    if name_exists:
                        err_list.append(str(_("%(cpt)s '%(val)s' already exists.") \
                                            % {'cpt': _('Cluster name'), 'val': new_value}))
                    else:
                        setattr(instance, field, new_value)
                        instance.save(request=request)
                        updated_cluster_pk = instance.pk
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            err_list.append(''.join((str(_('An error occurred')), ' (', str(e), ').')))
            err_list.append(str(_("%(cpt)s have not been saved.") % {'cpt': _('The changes')}))

    if logging_on:
        logger.debug('updated_cluster_pk: ' + str(updated_cluster_pk))
    return err_list, updated_cluster_pk
# - end of update_cluster_instance