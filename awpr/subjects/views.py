# PR2018-07-20
import io

from django.contrib.auth.decorators import login_required  # PR2018-04-01

from django.utils import timezone
from django.utils.functional import Promise

from timeit import default_timer as timer

# PR2022-02-13 From Django 4 we dont have force_text You Just have to Use force_str Instead of force_text.
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

from django.db import connection
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render

from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext, pgettext_lazy, gettext_lazy as _
from django.views.generic import View
from reportlab.pdfgen.canvas import Canvas

from accounts import views as acc_view
from  accounts import permits as acc_prm

from awpr import settings as s
from awpr import menus as awpr_menu
from awpr import logs as awpr_logs

from subjects import models as subj_mod

from awpr import constants as c
from awpr import functions as af
from awpr import validators as av
from awpr import printpdf

from schools import models as sch_mod
from subjects import models as sbj_mod
from students import models as stud_mod

from grades import views as grade_view
from grades import calc_finalgrade as calc_final
from grades import calc_score as calc_score

import json  # PR2018-10-25
# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


# === Schemeitem =====================================
@method_decorator([login_required], name='dispatch')
class SchemeitemsDownloadView(View):  # PR2019-01-13
    # PR2019-01-17
    def post(self, request):
        # logger.debug(' ============= SchemeitemsDownloadView ============= ')
        # logger.debug('request.POST' + str(request.POST) )

        # request.POST<QueryDict: {'d
        #
        # ep_id': ['11'], 'lvl_id': ['7'], 'sct_id': ['30']}>

        params = {}
        if request.user is not None and request.user.examyear is not None:

        # lookup scheme by dep_id, lvl_id (if required) and sct_id (if required)
            if 'dep_id' in request.POST.keys():
                dep_id_int = int(request.POST['dep_id'])
                examyear = request.user.examyear
                department = sch_mod.Department.objects.filter(id=dep_id_int, examyear=examyear).first()
                if department:
                    dep_abbrev = department.abbrev
                    # logger.debug(dep_abbrev)

                    # lookup level (if required)
                    level = None
                    lvl_abbrev = ''
                    if department.level_req:
                        if 'lvl_id' in request.POST.keys():
                            lvl_id_int = int(request.POST['lvl_id'])
                            level = subj_mod.Level.objects.filter(id=lvl_id_int, examyear=examyear).first()
                            # if level:
                                # lvl_abbrev = level.abbrev
                    # logger.debug(lvl_abbrev)

                    # lookup sector (if required)
                    sector = None
                    if department.sector_req:
                        if 'sct_id' in request.POST.keys():
                            sct_id_int = int(request.POST['sct_id'])
                            sector = subj_mod.Sector.objects.filter(id=sct_id_int, examyear=examyear).first()
                            #if sector:
                                #sct_name = sector.name
                    # logger.debug(sct_name)

                    # lookup scheme by dep_id, lvl_id (if required) and sct_id (if required)
                    scheme = None
                    if level:
                        if sector:
                            logger.debug('filter by department, level and sector')
                            # filter by department, level and sector
                            # if selection contains multiple schemes: skip
                            if subj_mod.Scheme.objects.filter(
                                department=department, level=level, sector=sector
                            ).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(
                                    department=department, level=level, sector=sector
                                ).first()
                        else:
                            logger.debug('filter by department and level')
                            # filter by department and level
                            # if selection contains multiple schemes: skip
                            if subj_mod.Scheme.objects.filter(
                                    department=department, level=level
                            ).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(
                                    department=department, level=level
                                ).first()
                    else:
                        if sector:
                            # logger.debug('filter by department and sector')
                            # filter by department and sector
                            # if selection contains multiple schemes: skip

                            logger.debug('count: ' + str(subj_mod.Scheme.objects.filter(department=department, sector=sector).count()))
                            if subj_mod.Scheme.objects.filter(department=department, sector=sector).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(department=department, sector=sector).first()
                        else:
                            # logger.debug('only by department')
                            # filter only by department
                            # if selection contains multiple schemes: skip
                            if subj_mod.Scheme.objects.filter(department=department).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(department=department).first()

                    if scheme:
                        scheme_list_str = scheme.get_scheme_list_str()
                        params.update({'scheme': scheme_list_str})

                        # make list of all Subjects from this department and examyear (included in dep)
                        schemeitems = subj_mod.Schemeitem.get_schemeitem_list(scheme)
                        params.update({'schemeitems': schemeitems})

                        # make list of all Subjects from this department and examyear (included in dep) #PR2022-05-14
                        depbase_id_str = ';' + str(department.base.id) + ';'
                        subjects = subj_mod.Subject.objects.filter(
                            examyear=department.examyear,
                            depbase_list__contains=depbase_id_str
                        )
                        subject_list = []
                        for subject in subjects:
                            subject_list.append({
                                'subj_id': str(subject.id),
                                'subj_name_nl': subject.name_nl,
                                'subj_abbr': subject.abbrev,
                                'subj_sequ': subject.sequence
                            })
                        params.update({'subjects': subject_list})

                        # make list of all Subjecttypes from this department and examyear (included in dep)
                        # TODO fix
                        #subjecttypes = subj_mod.Subjecttype.get_subjtype_list( department)  # PR2019-01-18 PR2022-05-14
                        #params.update({'subjecttypes': subjecttypes})

                        # make list of all gradetypes
                        """
                        GRADETYPE_OPTIONS = {
                            GRADETYPE_00_NONE:  _('None'),
                            GRADETYPE_01_NUMBER: _('Number'),
                            GRADETYPE_02_CHARACTER: _('Good/Sufficient/Insufficient')
                        }
                        """
                        gradetypes = []
                        for grtp_id, name in c.GRADETYPE_OPTIONS.items():
                            if grtp_id:
                                gradetypes.append({
                                    'grtp_id': grtp_id,
                                    'name': name
                                })
                        params.update({'gradetypes': gradetypes})

        #logger.debug('params')
        # logger.debug(params)
        return HttpResponse(json.dumps(params))


# ========  SubjectListView  ======= # PR2020-09-29  PR2021-03-25
@method_decorator([login_required], name='dispatch')
class SubjectListView(View):

    def get(self, request):
        #logger.debug(" =====  SubjectListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get sel_schoolbase from settings / request when role is insp, admin or system, from req_usr otherwise
        sel_schoolbase, sel_schoolbase_saveNIU = acc_view.get_sel_schoolbase_instance(
            request=request,
            request_item_schoolbase_pk=None,
            allowed_sections_dict={}
        )

        # requsr_same_school = True when selected school is same as requsr_school PR2021-04-27
        # used on entering grades. Users can only enter grades of their own school. Syst, Adm and Insp, Comm can not neter grades
        requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase.pk)

# - get headerbar parameters
        if requsr_same_school:
            page = 'page_studsubj'
            html_page = 'studentsubjects.html'
            param = {'display_school': True, 'display_department': True}
        else:
            page = 'page_subject'
            html_page = 'subjects.html'
            param = {'display_school': True, 'display_department': False}

        params = awpr_menu.get_headerbar_param(request, page, param)

# - save this page in Usersetting, so at next login this page will open.  Used in LoggedIn
        # PR2021-06-22 moved to get_headerbar_param

        return render(request, html_page, params)


def create_subject_rows(request, sel_examyear, sel_schoolbase, sel_depbase, sel_lvlbase,
                        skip_allowedsubjbase_filter=False, skip_notatdayschool=False,
                        cur_dep_only=False, with_ce_only=False, duo_exam_only=False):
    # PR2020-09-29 PR2020-10-30 PR2020-12-02 PR2022-02-07 PR2022-08-21 PR2022-12-19
    # --- create rows of all subjects of this examyear
    # skip_allowedsubjbase_filter is used in userpage: when setting 'allowed_', all subjects must be shown
    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug(' =============== create_subject_rows ============= ')
        logger.debug('    skip_allowedsubjbase_filter: ' + str(skip_allowedsubjbase_filter))
        logger.debug('    skip_notatdayschool: ' + str(skip_notatdayschool))
        logger.debug('    cur_dep_only: ' + str(cur_dep_only))

    # lookup if sel_depbase_pk is in subject.depbases PR2020-12-19
    # use: AND %(depbase_pk)s::INT = ANY(sj.depbases)
    # ANY must be on the right side of =
    # from https://lerner.co.il/2014/05/22/looking-postgresql-arrays/
    # or
    # from https://www.postgresqltutorial.com/postgresql-like/
    # first_name LIKE '%Jen%';

    #PR2022-06-15 debug: new subject has no si yet, will not show, cannot add si.
    # Make separate sql for page Subjects, without si link

    # PR2022-08-21 notatdayschool added: show this subject only when school is evening school or lex school
    # attention: day/evening school shows notatdayschool subjects. Must be filtered out when adding subjects to day student

    subject_rows = []
    if sel_examyear:
        sql_keys = {'ey_id': sel_examyear.pk}

# create list subject_id with the following filter:
        # - this examyear,
        # - sel_depbase_pk and allowed_depbase
        # - sel_lvlbase_pk and allowed_lvlbase
        # - allowed_subjbase
        # - if duo_exam_only: and not ete_exam
        # - if not evelex school: skip subjects with filter_notatdayschool

        sub_sql_list = ["SELECT si.subject_id",
            "FROM subjects_schemeitem AS si",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
            "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",

            "WHERE subj.examyear_id = %(ey_id)s::INT"
            ]
        if duo_exam_only:
            sub_sql_list.append("AND NOT si.ete_exam")

        if with_ce_only:
            sub_sql_list.append("AND si.weight_ce > 0")

        if not skip_notatdayschool:
            sub_sql_list.append("AND NOT si.notatdayschool")

        # note: don't filter on sel_subjbase_pk, must be able to change within allowed

        #    )

    # --- filter on usersetting and allowed
        # PR2023-05-20 cahnged to get_sqlclause_allowed_v2
        # was:
            #sql_clause = acc_view.get_userallowed_for_subjects_studsubj(
            #    sel_examyear=sel_examyear,
            #    sel_schoolbase=sel_schoolbase,
            #    sel_depbase=sel_depbase,
            #    sel_lvlbase=sel_lvlbase,
            #    request=request,
            #    skip_allowedsubjbase_filter=skip_allowedsubjbase_filter
            #)
            #if sql_clause:
            #    sub_sql_list.append("AND " + sql_clause)

        sql_clause = acc_prm.get_sqlclause_allowed_v2(
            table='subject',
            sel_schoolbase_pk=sel_schoolbase.pk if sel_schoolbase else None,
            sel_depbase_pk=sel_depbase.pk if sel_depbase else None,
            sel_lvlbase_pk=sel_lvlbase.pk if sel_lvlbase else None,
            userallowed_sections_dict=acc_prm.get_userallowed_sections_dict_from_request(request),
            return_false_when_no_allowedsubjects=False
        )
        if sql_clause:
            sub_sql_list.append(sql_clause)


        sub_sql_list.append("GROUP BY si.subject_id")

        sub_sql = ' '.join(sub_sql_list)
        if logging_on:
            logger.debug(' <>>  sql_clause: ' + str(sql_clause))
            logger.debug(' <>>  sub_sql: ' + str(sub_sql))

        """
         sql: WITH sub_sql AS ( SELECT si.subject_id FROM subjects_schemeitem AS si 
         INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id) 
         INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id) 
         INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id) 
         LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id) 
         LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id) 
         WHERE subj.examyear_id = %(ey_id)s::INT AND NOT si.notatdayschool 
         AND 
         (
            CONCAT(';', subj.depbases::TEXT, ';') LIKE 1::TEXT 
                AND 
            lvl.base_id IN (   SELECT UNNEST(   ARRAY[4, 5]::INT[]   )   )
        ) 
         AND (sct.base_id = 14::INT) GROUP BY si.subject_id ) 
         
         SELECT subj.id, subj.base_id, subj.examyear_id, CONCAT('subject_', subj.id::TEXT) AS mapid, 
         sb.code, subj.name_nl, subj.name_en, subj.name_pa, subj.sequence, subj.depbases,  
         ey.code AS examyear_code FROM subjects_subject AS subj 
         INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id) 
         INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)  
         INNER JOIN sub_sql ON (sub_sql.subject_id = subj.id) ORDER BY subj.id
        """

        user_line, user_join = '', ''
        if request.user.role in (c.ROLE_032_INSP, c.ROLE_064_ADMIN, c.ROLE_128_SYSTEM):
            user_line = "subj.modifiedby_id, subj.modifiedat, au.last_name AS modby_username,"
            user_join = "LEFT JOIN accounts_user AS au ON (au.id = subj.modifiedby_id)"

        sql_list = ["WITH sub_sql AS (", sub_sql, ")",
                    "SELECT subj.id, subj.base_id, subj.examyear_id,",
                    "CONCAT('subject_', subj.id::TEXT) AS mapid,",
                    "sb.code, subj.name_nl, subj.name_en, subj.name_pa, subj.sequence, subj.depbases,",
                    user_line,
                    "ey.code AS examyear_code",

                    "FROM subjects_subject AS subj",
                    "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",
                    user_join,
                    "INNER JOIN sub_sql ON (sub_sql.subject_id = subj.id)",
                    "ORDER BY subj.id"
                    ]

        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('    sql_keys: ' + str(sql_keys))
            logger.debug('    sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            subject_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('    subject_rows: ' + str(subject_rows))

    return subject_rows
# --- end of create_subject_rows


def create_subjectrows_for_page_subjects(sel_examyear, append_dict, subject_pk=None):
    # PR2022-08-05
    # --- create rows of all subjects of this examyear for page subjects

    # PR2022-06-15 debug: new subject has no si yet, will not show, cannot add si.
    # Make separate sql for page Subjects, without si link

    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug(' =============== create_subjectrows_for_page_subjects ============= ')

    subject_rows = []
    if sel_examyear:
        sql_keys = {'ey_id': sel_examyear.pk}

        sql_list = [
            "SELECT subj.id, subj.base_id, subj.examyear_id,",
            "CONCAT('subject_', subj.id::TEXT) AS mapid,",
            "sb.code, subj.name_nl, subj.name_en, subj.name_pa, subj.sequence, subj.depbases,",
            "subj.modifiedby_id, subj.modifiedat, au.last_name AS modby_username,"
            "ey.code AS examyear_code",

            "FROM subjects_subject AS subj",
            "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = subj.modifiedby_id)"
            "WHERE subj.examyear_id = %(ey_id)s::INT",
        ]
        if subject_pk:
            sql_keys['subj_id'] = subject_pk
            sql_list.append("AND subj.id = %(subj_id)s::INT")

        sql_list.append("ORDER BY subj.id")
        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            subject_rows = af.dictfetchall(cursor)

# - add messages to subject_row, only if subject_pk has value
        if subject_pk and subject_rows and append_dict:
            # when subject_pk has value there is only 1 row
            row = subject_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    return subject_rows
# --- end of create_subjectrows_for_page_subjects


def create_subjectrows_for_page_users(sel_examyear):
    # PR2022-08-05
    # --- create rows of all subjects of this examyear for page subjects

    # PR2022-06-15 debug: new subject has no si yet, will not show, cannot add si.
    # Make separate sql for page Subjects, without si link

    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug(' =============== create_subjectrows_for_page_users ============= ')

    subject_rows = []
    if sel_examyear:
        sql_keys = {'ey_id': sel_examyear.pk}
        sql_list = ["SELECT subj.id, subj.base_id,",
            "subjbase.code, subj.name_nl, subj.sequence,",
            "ARRAY_AGG(DISTINCT dep.base_id) AS depbase_id_arr,",
            "ARRAY_AGG(DISTINCT lvl.base_id) AS lvlbase_id_arr",

            "FROM subjects_schemeitem AS si",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
            "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",

            "WHERE subj.examyear_id = %(ey_id)s::INT",
            "GROUP BY subj.id, subj.base_id, subjbase.code, subj.name_nl, subj.sequence",
            "ORDER BY subj.id"
            ]
        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            subject_rows = af.dictfetchall(cursor)

    return subject_rows
# --- end of create_subjectrows_for_page_users


def create_cluster_rows(request, sel_examyear, sel_schoolbase, sel_depbase,
                        page, cluster_pk_list=None):
    # --- create rows of all clusters of this examyear this department  #
    # PR2022-01-06 PR2022-12-25 PR2023-02-09 PR2023-05-29
    # called by page users, correctors,
    # grades, secretexam, studentsubject, wolf
    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug(' =============== create_cluster_rows ============= ')
        logger.debug('    sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))
        logger.debug('    sel_schoolbase: ' + str(sel_schoolbase) + ' ' + str(type(sel_schoolbase)))
        logger.debug('    sel_depbase: ' + str(sel_depbase) + ' ' + str(type(sel_depbase)))
        logger.debug('    page: ' + str(page))
        logger.debug('    cluster_pk_list: ' + str(cluster_pk_list))
        # pages are: page_studsubj page_grade page: page_corrector, page_user"page_wolf page_secretexam

    # show only this corr when ug = corrector and not auth1, auth2
    requsr_usergroup_list = acc_prm.get_usergroup_list(acc_prm.get_userallowed_instance(request.user, sel_examyear))
    requsr_has_ug_corrector_only = c.USERGROUP_AUTH4_CORR in requsr_usergroup_list \
                                   and c.USERGROUP_AUTH1_PRES not in requsr_usergroup_list \
                                   and c.USERGROUP_AUTH2_SECR not in requsr_usergroup_list
    if logging_on:
        logger.debug('    requsr_usergroup_list: ' + str(requsr_usergroup_list))
        logger.debug('    requsr_has_ug_corrector_only: ' + str(requsr_has_ug_corrector_only))

    cur_dep_only, cur_school_only, allowed_only = False, False, False
    if page == 'page_corrector':
        if request.user.role == c.ROLE_008_SCHOOL:
            # when school uses page_corrector:
            # school can add clusters to allowed_clusters
            # - show only clusters of this school, all departments
            cur_school_only = True
            # school_corrector can only see his allowedclusters
            if requsr_has_ug_corrector_only:
                allowed_only = True

        elif request.user.role == c.ROLE_016_CORR:

            # when role corrector uses page_corrector:

            # when usergroup is only corrector, not chairperon ofr sexcretaru:
            # can only see allowed clusters of all schools and all departmentsf
            # school can add clusters to allowed_clusters
            # - show only clusters of this school, all departments

            # show only this corr when ug = corrector and not auth1, auth2
            if requsr_has_ug_corrector_only:
                allowed_only = True

    elif page == 'page_user':
        cur_school_only = True
    elif page in ('page_studsubj', 'page_grade', 'page_wolf', 'page_secretexam'):
        cur_school_only = True
        cur_dep_only = True
        # show only this corr when ug = corrector and not auth1, auth2
        if requsr_has_ug_corrector_only:
            allowed_only = True


    cluster_rows = []
    if sel_examyear and sel_schoolbase and sel_depbase:
        try:

            sql_keys = {'ey_id': sel_examyear.pk if sel_examyear else None,
                        #'sb_id': sel_schoolbase.pk if sel_schoolbase else None,
                        #'db_id': sel_depbase.pk if sel_depbase else None
                        }
            sql_list = ["SELECT cluster.id, cluster.name, subj.id AS subject_id, subjbase.id AS subjbase_id,",
                        "CONCAT('cluster_', cluster.id::TEXT) AS mapid,",
                        "sch.base_id AS schoolbase_id, dep.base_id AS depbase_id, depbase.code AS depbase_code, dep.sequence AS dep_sequence,",
                        "subjbase.code AS subj_code, subj.name_nl AS subj_name_nl",
                        "FROM subjects_cluster AS cluster",
                        "INNER JOIN subjects_subject AS subj ON (subj.id = cluster.subject_id)",
                        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                        "INNER JOIN schools_school AS sch ON (sch.id = cluster.school_id)",
                        "INNER JOIN schools_department AS dep ON (dep.id = cluster.department_id)",
                        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                        "WHERE subj.examyear_id = %(ey_id)s::INT",
                        "AND sch.examyear_id = %(ey_id)s::INT",
                        #"AND sch.base_id = %(sb_id)s::INT"
                        ]
            if cur_school_only:
                if sel_schoolbase:
                    sel_schoolbase_clause = ''.join(( "AND sch.base_id = ", str(sel_schoolbase.pk), "::INT"))
                else:
                    sel_schoolbase_clause = "AND FALSE"
                sql_list.append(sel_schoolbase_clause)

            if cur_dep_only:
                if sel_depbase:
                    sel_depbase_clause = ''.join(( "AND dep.base_id = ", str(sel_depbase.pk), "::INT"))
                else:
                    sel_depbase_clause = "AND FALSE"
                sql_list.append(sel_depbase_clause)

    # - filter on allowed depbases, levelbase, subjectbases
                # this doesnt work, because table level is missing in sql. Skip it for now
                # TODO add table level in sql
                #sqlclause_allowed_dep_lvl_subj = acc_prm.get_sqlclause_allowed_dep_lvl_subj(
                #    table='cluster',
                #    userallowed_sections_dict=acc_prm.get_userallowed_sections_dict_from_request(request),
                #    sel_schoolbase_pk=sel_schoolbase.pk if sel_schoolbase else None,
                #    sel_depbase_pk=sel_depbase.pk if sel_depbase else None
                #)
                #if sqlclause_allowed_dep_lvl_subj:
                #    sql_list.append(sqlclause_allowed_dep_lvl_subj)

    # - filter on allowed clusters
            if allowed_only:
                userallowed_cluster_pk_list = acc_prm.get_userallowed_cluster_pk_list_from_request(request)

                # PR2024-05-30 filter on examyear_pk added
                allowed_clusters_of_sel_school = acc_prm.get_allowed_clusters_of_sel_school(
                    sel_schoolbase_pk=sel_schoolbase.pk if sel_schoolbase else None,
                    sel_examyear_pk=sel_examyear.pk if sel_examyear else None,
                    allowed_cluster_pk_list=userallowed_cluster_pk_list
                )
                userallowed_cluster_pk_clause = acc_prm.get_sqlclause_allowed_clusters(
                    table='cluster',
                    allowed_clusters_of_sel_school=allowed_clusters_of_sel_school
                )
                if userallowed_cluster_pk_clause:
                    sql_list.append(userallowed_cluster_pk_clause)
                if logging_on:
                    logger.debug('   allowed_clusters_of_sel_school: ' + str(allowed_clusters_of_sel_school))
                    logger.debug('   userallowed_cluster_pk_clause: ' + str(userallowed_cluster_pk_clause))

            if cluster_pk_list:
                sql_list.extend(("AND cluster.id IN (SELECT UNNEST(ARRAY", str(cluster_pk_list), "::INT[]))"))

            sql_list.append("ORDER BY cluster.id")

            if logging_on:
                for sql_txt in sql_list:
                    logger.debug('    > ' + str(sql_txt))

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                cluster_rows = af.dictfetchall(cursor)

                if logging_on:
                    logger.debug('    len(cluster_rows: ' + str(len(cluster_rows) ))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return cluster_rows
# --- end of create_cluster_rows


@method_decorator([login_required], name='dispatch')
class SubjectUploadView(View):  # PR2020-10-01 PR2021-05-14 PR2021-07-18 PR2023-04-14

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= SubjectUploadView ============= ')

        # error_list is attached to updated row, messages is attached to update_wrap
        update_wrap = {}

# - get permit
        has_permit = acc_prm.has_permit( request, 'page_subject', ['permit_crud'])
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

# - get  variables
                subject_pk = upload_dict.get('subject_pk')
                mode = upload_dict.get('mode')
                is_create = (mode == 'create')
                is_delete = (mode == 'delete')

                if logging_on:
                    logger.debug('mode: ' + str(mode))
                    logger.debug('upload_dict' + str(upload_dict))

                updated_rows = []
                error_list = []
                messages = []
                append_dict = {}

                header_txt = _('Add subject') if is_create else _('Delete subject') if is_delete else _('Edit subject')

# - get selected examyear from Usersetting
                # get_selected_examyear_from_usersetting gives error message when:
                # - country is locked
                # - no exam year selected
                # - exam year is locked
                # - (skip check for not published)
                sel_examyear, sel_msg_list = acc_view.get_selected_examyear_from_usersetting(request, True) # allow_not_published = True
                if sel_msg_list:
                    msg_html = '<br>'.join(sel_msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                    if logging_on:
                        logger.debug('messages:   ' + str(messages))
                else:

# ++++ Create new subject:
                    if is_create:
                        subject_instance, error_list = create_subject(sel_examyear, upload_dict, request)
                        if error_list:
                            messages.append(
                                {'header': str(header_txt),
                                 'class': "border_bg_invalid",
                                 'msg_html': '<br>'.join(error_list)}
                            )

                        if subject_instance:
                            append_dict['created'] = True

                    else:

# +++  or get existing subject
                        subject_instance = sbj_mod.Subject.objects.get_or_none(
                            id=subject_pk,
                            examyear=sel_examyear
                        )
                    if logging_on:
                        logger.debug('..... subject_instance: ' + str(subject_instance))

                    if subject_instance:

# ++++ Delete subject
                        if is_delete:
                            deleted_row, err_html = delete_subject_instance(subject_instance, request)
                            if err_html:
                                messages.append(
                                    {'header': str(header_txt),
                                     'class': "border_bg_invalid",
                                     'msg_html': err_html}
                                )
                            elif deleted_row:
                                subject_instance = None
                                updated_rows.append(deleted_row)

                            if logging_on:
                                logger.debug('    deleted_row: ' + str(deleted_row))
                                logger.debug('    err_html: ' + str(err_html))

# +++ Update subject, also when it is created, not when delete has failed (when deleted ok there is no student)
                        else:
                            error_list = update_subject_instance(
                                subject_instance=subject_instance,
                                examyear=sel_examyear,
                                upload_dict=upload_dict,
                                request=request
                            )
                            if error_list:
                                messages.append(
                                    {'header': str(header_txt),
                                     'class': "border_bg_invalid",
                                     'msg_html': '<br>'.join(error_list)}
                                )

# - create subject_row, also when deleting failed (when deleted ok there is no subject, subject_row is made above)
                    # PR2021-089-04 debug. gave error on subject.pk: 'NoneType' object has no attribute 'pk'
                    if subject_instance:
                        updated_rows = create_subjectrows_for_page_subjects(
                            sel_examyear=sel_examyear,
                            append_dict=append_dict,
                            subject_pk=subject_instance.pk
                        )

        # - add messages to subject_row (there is only 1 subject_row
                        update_wrap['updated_subject_rows'] = updated_rows

                if logging_on:
                    logger.debug('..... messages: ' + str(messages))
                    logger.debug('..... error_list: ' + str(error_list))

                if messages:
                    update_wrap['messages'] = messages
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of SubjectUploadView


##########################
@method_decorator([login_required], name='dispatch')
class SubjecttypebaseUploadView(View):  # PR2021-06-29 PR2022-08-06 PR2023-04-13

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= SubjecttypebaseUploadView ============= ')

        # error_list is attached to updated row, messages is attached to update_wrap
        messages = []
        update_wrap = {}

# - get permit
        has_permit = acc_prm.has_permit( request, 'page_subject', ['permit_crud'])
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload')
            if upload_json:
                # upload_dict = {'mapid': 'subjecttypebase_4', 'sjtpbase_pk': 4, 'abbrev': 'w'}
                # upload_dict{'create': True, 'code': 'a', 'name': 'a', 'sequence': 3, 'abbrev': '2'}
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))

# - get  variables
                sjtpbase_pk = upload_dict.get('sjtpbase_pk')
                is_create = upload_dict.get('create', False)
                is_delete = upload_dict.get('delete', False)

                if logging_on:
                    logger.debug('sjtpbase_pk: ' + str(sjtpbase_pk))
                updated_rows = []
                error_list = []
                is_created = False

# ++++ Create new subjecttypebase:
                if is_create:
                    subjecttypebase = create_subjecttypebase(upload_dict, messages, request)
                    if subjecttypebase:
                        is_created = True
                else:

# +++  get existing subjecttypebase
                    subjecttypebase = sbj_mod.Subjecttypebase.objects.get_or_none(
                        pk=sjtpbase_pk
                    )
                if logging_on:
                    logger.debug('subjecttypebase: ' + str(subjecttypebase))

                if subjecttypebase:

# ++++ Delete subjecttypebase
                    if is_delete:
                        header_txt = _("Delete base character")
                        deleted_row, err_html = delete_subjecttypebase(subjecttypebase, request)

                        if err_html:
                            messages.append(
                                {'header': str(header_txt),
                                 'class': "border_bg_invalid",
                                 'msg_html': err_html}
                            )
                        elif deleted_row:
                            subjecttypebase = None
                            updated_rows.append(deleted_row)

                        if logging_on:
                            logger.debug('    deleted_row: ' + str(deleted_row))
                            logger.debug('    msg_html: ' + str(err_html))

# +++ Update subjecttype
                    elif not is_create:
                        update_subjecttypebase_instance(subjecttypebase, upload_dict, error_list, request)

# - create subjecttype_rows
                    if subjecttypebase:
                        updated_rows = create_subjecttypebase_rows(
                            sjtpbase_pk=subjecttypebase.pk
                        )

    # - add error_list to subject_row (there is only 1 subject_row, or none
                    # Note: error_list is attached to updated row, messages is attached to update_wrap
                    # key 'field' is needed to restore old value when updating item
                    # 'messages' is needed when cerating goes wrong, then there is no item
                    # 'created' is needed to add item to data_rows and make tblRow green
                    if updated_rows:
                        if error_list:
                            updated_rows[0]['error'] = error_list
                        if is_created:
                            updated_rows[0]['created'] = True
                update_wrap['updated_subjecttypebase_rows'] = updated_rows

        if messages:
            update_wrap['messages'] = messages
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of SubjecttypebaseUploadView


def create_subjecttypebase(upload_dict, error_list, request):
    # --- create subjecttype # PR2021-06-29
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_subjecttypebase ----- ')

    msg_header = _('Create base character')

    code = upload_dict.get('code')
    name = upload_dict.get('name')
    abbrev = upload_dict.get('abbrev')
    sequence = upload_dict.get('sequence')
    if logging_on:
        logger.debug('name: ' + str(name))

    msg_list = []
    subjecttypebase = None

# - validate code and name. Function checks null, max_len, exists
    msg_html = av.validate_notblank_maxlength(code, c.MAX_LENGTH_04 , _('The code'))
    if msg_html:
        msg_list.append(msg_html)
    msg_html = av.validate_notblank_maxlength(name, c.MAX_LENGTH_NAME, _('The name'))
    if msg_html:
        msg_list.append(msg_html)
    msg_html = av.validate_notblank_maxlength(abbrev, c.MAX_LENGTH_20, _('The abbreviation'))
    if msg_html:
        msg_list.append(msg_html)
    msg_html = av.validate_notblank_maxlength(sequence, None, _('The sequence'))
    if msg_html:
        msg_list.append(msg_html)

# - check if subjecttypebase code, name, abbrev already exists
    msg_html = av.validate_subjecttypebase_code_name_abbrev_exists('code', code)
    if msg_html:
        msg_list.append(msg_html)
    msg_html = av.validate_subjecttypebase_code_name_abbrev_exists('name', name)
    if msg_html:
        msg_list.append(msg_html)
    msg_html = av.validate_subjecttypebase_code_name_abbrev_exists('abbrev', abbrev)
    if msg_html:
        msg_list.append(msg_html)
# - create and save subjecttype
    if len(msg_list) > 0:
        msg_html = '<br>'.join(msg_list)
        error_list.append({'header': str(msg_header), 'class': "border_bg_invalid", 'msg_html': msg_html})
    else:
        try:
            # Don't create base record. Only use the default subjecttypebase records
            subjecttypebase = sbj_mod.Subjecttypebase(
                code=code,
                name=name,
                abbrev=abbrev,
                sequence=sequence
            )
            subjecttypebase.save()

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            caption = _('Base character')
            msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                        str(_("%(cpt)s '%(val)s' could not be created.") % {'cpt': caption, 'val': name})))
            error_list.append({'header': str(msg_header), 'class': 'border_bg_invalid', 'msg_html': msg_html})

    if logging_on:
        logger.debug('subjecttypebase: ' + str(subjecttypebase))
        logger.debug('error_list: ' + str(error_list))

    return subjecttypebase
# - end of create_subjecttypebase


def delete_subjecttypebase(subjecttypebase, request):
    # --- delete subjecttype # PR2021-06-29 PR2022-08-06
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_subjecttypebase ----- ')
        logger.debug('subjecttypebase: ' + str(subjecttypebase))

    msg_html = None
    deleted_row = None

    this_txt = _("Base character '%(tbl)s'") % {'tbl': subjecttypebase.name}

# check if there are students with subjects with this subjecttypebase
    students_with_this_subjecttypebase_exist = stud_mod.Studentsubject.objects.filter(
        schemeitem__subjecttype__base=subjecttypebase
    ).exists()

    if logging_on:
        logger.debug('students_with_this_subjecttypebase_exist: ' + str(students_with_this_subjecttypebase_exist))

    if students_with_this_subjecttypebase_exist:
        deleted_ok = False
        msg_html = ''.join((str(_('There are candidates with subjects with this base character.')), '<br>',
                            str(_("%(cpt)s could not be deleted.") % {'cpt': this_txt})))

    else:
        deleted_row, err_html = sch_mod.delete_instance(
            table='subjecttypebase',
            instance=subjecttypebase,
            request=request,
            this_txt=this_txt
        )
        if err_html:
            msg_html = err_html

    if logging_on:
        logger.debug('deleted_row' + str(deleted_row))
        logger.debug('msg_html' + str(msg_html))

    return deleted_row, msg_html
# - end of delete_subjecttypebase


def update_subjecttypebase_instance(instance, upload_dict, error_list, request):
    # --- update existing and new instance PR2021-06-29
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_subjecttypebase_instance -----')
        logger.debug('upload_dict: ' + str(upload_dict))

    if instance:
        save_changes = False

        msg_header = _('Update base character')

        for field, new_value in upload_dict.items():

            if logging_on:
                logger.debug('field: ' + str(field))
                logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))

# - save changes in field 'code'
            if field in ('code', 'name', 'abbrev'):
                saved_value = getattr(instance, field)
                if new_value != saved_value:
    # - validate abbrev checks null, max_len, exists
                    caption = _('Code') if field == 'code' else _('Abbreviation') if field == 'abbrev' else _('Name')
                    max_length = c.MAX_LENGTH_04 if field == 'code' else c.MAX_LENGTH_20 if field == 'abbrev' else c.MAX_LENGTH_NAME
                    msg_html = av.validate_notblank_maxlength(new_value, max_length, caption)
                    if msg_html is None:
                        msg_html = av.validate_subjecttypebase_code_name_abbrev_exists(field, new_value, instance)
                    if msg_html:
                        # add 'field' in error_list, to put old value back in field
                        # error_list will show mod_messages in RefreshDatarowItem
                        error_list.append({'field': field, 'header': msg_header, 'class': 'border_bg_warning', 'msg_html': msg_html})
                    else:
                        # - save field if changed and no_error
                        setattr(instance, field, new_value)
                        save_changes = True

            elif field == 'sequence':
                msg_html = None
                new_value_int = None

                if new_value:
    # - check if value is positive whole number
                    if not new_value.isdecimal():
                        msg_html = str(_("'%(val)s' is not a valid number.") % {'val': new_value})
                    else:
                        new_value_int = int(new_value)

                if msg_html:
                    # add 'field' in error_list, to put old value back in field
                    # error_list will show mod_messages in RefreshDatarowItem
                    error_list.append({'field': field,'header': msg_header,'class': 'border_bg_warning', 'msg_html': msg_html})
                else:
                    # -note: value can be None
                    saved_value = getattr(instance, field)
                    if new_value_int != saved_value:
                        setattr(instance, field, new_value_int)
                        save_changes = True
# --- end of for loop ---

# +++++ save changes
        if save_changes:
            try:
                instance.save()
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred: ')), '<br><i>', str(e), '</i><br>',
                                    str(_('The changes have not been saved.'))))
                error_list.append({'header': msg_header, 'class': 'border_bg_invalid', 'msg_html': msg_html})
            else:
                pass
# also update modified in scheme, otherwise it is difficult to find out if scheme has been changed
                # awpr_logs.save_to_log(instance, 'u', request)

# - end of update_subjecttypebase_instance



##########################
@method_decorator([login_required], name='dispatch')
class SubjecttypeUploadView(View):  # PR2021-06-23

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= SubjecttypeUploadView ============= ')

        # error_list is attached to updated row, messages is attached to update_wrap
        messages = []
        update_wrap = {}

# - get permit
        has_permit = acc_prm.has_permit( request, 'page_subject', ['permit_crud'])
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                # upload_dict{'scheme_pk': 177,
                #       'sjtp_list': [{'sjtpbase_pk': 5, 'scheme_pk': 177, 'create': True}]}
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))

                msg_header = _('Update character')

# - get selected examyear from Usersetting
                examyear = get_sel_examyear(msg_header, messages, request)

# - exit when no examyear or examyear is locked
                # note: subjects may be changed before publishing, therefore don't exit when examyear.published = False
                if examyear:

# - get scheme instance
                    scheme_pk = upload_dict.get('scheme_pk')
                    scheme = get_scheme_instance(examyear, scheme_pk, messages, msg_header)
                    if logging_on:
                        logger.debug('scheme_pk: ' + str(scheme_pk))
                        logger.debug('scheme:    ' + str(scheme))

                    if scheme:
                        updated_rows = []

# +++++++++++ update subjecttypes of scheme from sjtp_list
                        sjtp_list = upload_dict.get('sjtp_list')
                        if sjtp_list:
                            update_sjtp_list(examyear, scheme, sjtp_list, updated_rows, messages, request)
                        else:
# +++++++++++ update single sjtp
    # - get  variables
                            subjecttype_pk = upload_dict.get('subjecttype_pk')
                            is_delete = upload_dict.get('delete', False)

# if upload_dict does not have sjtp_list: it is single sjtp update - create, delete or update changes

# ++++ Create new subjecttype:
            # is done in sjtp_list
                            error_list = []

# +++  get existing subjecttype
                            subjecttype_instance = sbj_mod.Subjecttype.objects.get_or_none(
                                id=subjecttype_pk,
                                scheme=scheme
                            )
                            if logging_on:
                                logger.debug(' subjecttype_instance: ' + str(subjecttype_instance))
                                logger.debug(' is_delete: ' + str(is_delete))

                            if subjecttype_instance:
# ++++ Delete subjecttype
                                if is_delete:
                                    # delete_subjecttype will also cascade delete schemitem
                                    deleted_row, err_html = delete_subjecttype(subjecttype_instance, request)
                                    if err_html:
                                        messages.append(
                                            {'header': str(_('Delete character')),
                                             'class': 'border_bg_invalid',
                                             'msg_html': err_html}
                                        )
                                    elif deleted_row:
                                        subjecttype_instance = None
                                        updated_rows.append(deleted_row)

                                    if logging_on:
                                        logger.debug('    deleted_row: ' + str(deleted_row))
                                        logger.debug('    msg_html: ' + str(err_html))

# +++ Update subjecttype
                                else:
                                    update_subjecttype_instance(subjecttype_instance, scheme, upload_dict, error_list, request)
            # - create subjecttype_rows
                                    updated_rows = create_subjecttype_rows(
                                        examyear=examyear,
                                        append_dict={},
                                        sjtp_pk=subjecttype_instance.pk
                                    )

            # - add error_list to subject_row (there is only 1 subject_row, or none
                            # Note: error_list is attached to updated row, messages is attached to update_wrap
                            if error_list and updated_rows:
                                row = updated_rows[0]
                                if row:
                                    if error_list:
                                         row['error'] = error_list

                        update_wrap['updated_subjecttype_rows'] = updated_rows
        if len(messages):
            update_wrap['messages'] = messages
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of SubjecttypeUploadView

##########################

@method_decorator([login_required], name='dispatch')
class SchemeUploadView(View):  # PR2021-06-27 PR2023-04-14

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= SchemeUploadView ============= ')

# error_list is attached to updated row, messages is attached to update_wrap
        msg_dictlist = []
        updated_fields = []
        update_wrap = {}

# - get permit
        has_permit = acc_prm.has_permit( request, 'page_subject', ['permit_crud'])
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload')
            if upload_json:
                upload_dict = json.loads(upload_json)

                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))

# - get  variables
                scheme_pk = upload_dict.get('scheme_pk')

                updated_rows = []
                error_list = []

                msg_header = _('Edit subject scheme')

# - get selected examyear from Usersetting
                examyear = get_sel_examyear(msg_header, msg_dictlist, request)

# - exit when no examyear or examyear is locked
                # note: subjects may be changed before publishing, therefore don't exit when examyear.published = False
                if examyear:

# ++++ Create new scheme
                # not in use

# +++  get existing scheme
                    scheme = get_scheme_instance(examyear, scheme_pk, msg_dictlist, msg_header)
                    if logging_on:
                        logger.debug('scheme: ' + str(scheme))

                    if scheme:
# ++++ Delete scheme
                # not in use
# +++ Update scheme
                        update_scheme_instance(scheme, examyear, upload_dict, updated_rows, error_list, request)

# - create scheme_rows
                        updated_rows = create_scheme_rows(
                            examyear=examyear,
                            scheme_pk=scheme.pk
                        )

                        # - add error_list to subject_row (there is only 1 subject_row, or none
                        # Note: error_list is attached to updated row, msg_dictlist is attached to update_wrap
                        # key 'field' is needed to restore old value when updating item
                        # 'msg_dictlist' is needed when cerating goes wrong, then there is no item
                        # 'created' is needed to add item to data_rows and make tblRow green
                        if updated_rows:
                            if error_list:
                                updated_rows[0]['error'] = error_list

                update_wrap['updated_scheme_rows'] = updated_rows

            # - add msg_dictlist to update_wrap, if any
                if len(msg_dictlist):
                    update_wrap['messages'] = msg_dictlist
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of SchemeUploadView


##########################

@method_decorator([login_required], name='dispatch')
class SchemeitemUploadView(View):  # PR2021-06-25 PR2023-04-14

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= SchemeitemUploadView ============= ')

        update_wrap = {}

# - get permit
        has_permit = acc_prm.has_permit( request, 'page_subject', ['permit_crud'])
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                # upload_dict{'scheme_pk': 177, 'si_list': [{'subj_pk': 755, 'sjtp_pk': 200, 'create': True}, {'subj_pk': 759, 'sjtp_pk': 202, 'create': True}]}

                messages = []

# - get  variables
                message_header = _('Edit subject scheme')

                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))

# - get selected examyear from Usersetting
                examyear = get_sel_examyear(message_header, messages, request)

# - exit when no examyear or examyear is locked
                # note: subjects may be changed before publishing, therefore don't exit when examyear.published = False
                if examyear:

# - get scheme instance
                    scheme_pk = upload_dict.get('scheme_pk')
                    scheme = get_scheme_instance(examyear, scheme_pk, messages, message_header)
                    if scheme:
                        updated_rows = []

        # TODO: when creating / deleting  schemeitem: also change envelopsubject record PR2022-10-11
        # TODO: when changing ete_exam, value of all sectors must be changed because sectors cannot have different ete_exam value PR2023-05-04

# +++ update subjects of scheme from si_list
                        si_list = upload_dict.get('si_list')
                        if si_list:
                            update_si_list(examyear, scheme, si_list, updated_rows, messages, request)

# +++ if upload_dict does not have si_list: it is single schemeitem update
                        else:

# +++ update value of a single schemeitem
                            si_pk = upload_dict.get('si_pk')
                            schemeitem = get_schemeitem_instance(scheme, si_pk, logging_on)
                            if schemeitem:
                                update_schemeitem_instance(schemeitem, examyear, upload_dict, updated_rows, request)
       # - create schemeitem_rows

                                updated_rows = create_schemeitem_rows(
                                    sel_examyear=examyear,
                                    append_dict={},
                                    schemeitem_pk=schemeitem.pk,
                                    skip_notatdayschool=True
                                )

                        update_wrap['updated_schemeitem_rows'] = updated_rows

            # - add messages to update_wrap, if any
                if len(messages):
                    update_wrap['messages'] = messages
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of SchemeitemUploadView


def get_sel_examyear(message_header, msg_dictlist, request):
    # --- get selected examyear from usersetting # PR2021-06-26
    # - get selected examyear from Usersetting
    # return None when examyear is locked, give msg_err
    # function is only used for updating subjects etx
    # in SchemeUploadView, SchemeitemUploadView and SubjecttypeUploadView
    selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
    selected_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
    examyear = None
    if selected_examyear_pk:
        examyear = sch_mod.Examyear.objects.get_or_none(
            id=selected_examyear_pk,
            country=request.user.country
        )

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_sel_examyear ----- ')
        logger.debug('examyear: ' + str(examyear))

    # - exit when no examyear or examyear is locked
    # note: subjects may be changed before publishing, therefore don't exit when examyear.published = False
    if examyear is None:
        msg_dictlist.append({'class': "border_bg_warning",
                         'header': str(message_header),
                         'msg_html': str(_('No exam year selected'))})
    elif examyear.locked:
        msg_dictlist.append({'class': "border_bg_warning",
                         'header': str(message_header),
                         'msg_html': str(_("Exam year %(exyr)s is locked.") % {'exyr': str(examyear.code)})})
        examyear = None

    return examyear
# - end of get_sel_examyear


def get_scheme_instance(examyear, scheme_pk, error_list, msg_header):
    # --- get scheme instance # PR2021-06-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_scheme_instance ----- ')
        logger.debug('examyear: ' + str(examyear))
        logger.debug('scheme_pk: ' + str(scheme_pk))

    scheme = None
    if scheme_pk:
        scheme = sbj_mod.Scheme.objects.get_or_none(
            id=scheme_pk,
            department__examyear=examyear
        )
    if logging_on:
        logger.debug('scheme: ' + str(scheme))

    if scheme is None:
        error_list.append({'header': str(msg_header),
                           'class': "border_bg_invalid",
                           'msg_html': str(_('Subject scheme not found.'))})
    return scheme


def get_schemeitem_instance(scheme, si_pk, logging_on):
    # --- get schemeitem instance # PR2021-06-26
    schemeitem = None
    if si_pk:
        schemeitem = sbj_mod.Schemeitem.objects.get_or_none(
            id=si_pk,
            scheme=scheme
        )
    return schemeitem


def get_subjecttypebase_instance(sjtpbase_pk, error_list, message_header, logging_on, request):
    # --- get subjecttypebase instance # PR2021-06-26
    subjecttypebase = None

    if sjtpbase_pk:
        subjecttypebase = sbj_mod.Subjecttypebase.objects.get_or_none(
            id=sjtpbase_pk
        )

    if logging_on:
        logger.debug('subjecttypebase: ' + str(subjecttypebase))

    if subjecttypebase is None:
        error_list.append({'header': str(message_header),
                           'class': "border_bg_invalid",
                           'msg_html': str(_('Base subject type not found.'))})

    return subjecttypebase

#############################


# ========  WOLF  =====================================
@method_decorator([login_required], name='dispatch')
class WolfListView(View):  # PR2022-12-16

    def get(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('  -----  WolfListView -----')

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get sel_schoolbase from settings / request when role is insp, admin or system, from req_usr otherwise
        sel_examyear_instance = acc_view.get_selected_examyear_from_usersetting_short(request)
        userallowed_instance = acc_prm.get_userallowed_instance(request.user, sel_examyear_instance)
        userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
        if logging_on:
            logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))

        sel_schoolbase, sel_schoolbase_saveNIU = acc_view.get_sel_schoolbase_instance(
            request=request,
            request_item_schoolbase_pk=None,
            allowed_sections_dict=userallowed_sections_dict
        )
        if logging_on:
            logger.debug('    sel_schoolbase: ' + str(sel_schoolbase))

# requsr_same_school = True when selected school is same as requsr_school PR2021-04-27
        # used on entering grades. Users can only enter grades of their own school. Syst, Adm and Insp, Comm can not neter grades
        requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase.pk)

# - set headerbar parameters
        # PR2022-08-29 don't show school when user is not same school
        page = 'page_wolf'
        param = {'display_school': True, 'display_department': True}
        params = awpr_menu.get_headerbar_param(request, page, param)

        if logging_on:
            logger.debug('    params: ' + str(params))

# - save this page in Usersetting, so at next login this page will open.  Used in LoggedIn
        #         # PR2021-06-22 moved to get_headerbar_param

        return render(request, 'wolf.html', params)
# - end of WolfListView



#############################


# ========  EXAMS  =====================================
@method_decorator([login_required], name='dispatch')
class ExamListView(View):  # PR2021-04-04 PR2022-12-16

    def get(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('  -----  ExamListView -----')

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get sel_schoolbase from settings / request when role is insp, admin or system, from req_usr otherwise
        sel_examyear_instance = acc_view.get_selected_examyear_from_usersetting_short(request)
        userallowed_instance = acc_prm.get_userallowed_instance(request.user, sel_examyear_instance)
        userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
        if logging_on:
            logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))

        sel_schoolbase, sel_schoolbase_saveNIU = acc_view.get_sel_schoolbase_instance(
            request=request,
            request_item_schoolbase_pk=None,
            allowed_sections_dict=userallowed_sections_dict
        )
        if logging_on:
            logger.debug('    sel_schoolbase: ' + str(sel_schoolbase))

# requsr_same_school = True when selected school is same as requsr_school PR2021-04-27
        # used on entering grades. Users can only enter grades of their own school. Syst, Adm and Insp, Comm can not neter grades
        requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase.pk)

# - set headerbar parameters
        # PR2022-08-29 don't show school when user is not same school
        page = 'page_exams'
        #param = {'display_school': requsr_same_school, 'display_department': True}
        param = {'display_school': True, 'display_department': True}
        params = awpr_menu.get_headerbar_param(request, page, param)

        if logging_on:
            logger.debug('    params: ' + str(params))

# - save this page in Usersetting, so at next login this page will open.  Used in LoggedIn
        #         # PR2021-06-22 moved to get_headerbar_param

        return render(request, 'exams.html', params)
# - end of ExamListView


# ============= ExamUploadView ============= PR2021-04-04
@method_decorator([login_required], name='dispatch')
class ExamUploadView(View):
    # PR2021-04-04 PR2022-05-14 PR2023-05-04 PR2023-06-14
    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamUploadView ============= ')

        req_usr = request.user
        msg_list = []
        border_class = None
        update_wrap = {}

# - reset language
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            if logging_on:
                logger.debug('upload_dict' + str(upload_dict))
            """
            upload_dict{'table': 'duo_exam', 'mode': 'update', 'exam_pk': 495, 'lvlbase_pk': None, 
            'examtype': 'duo', 'subject_pk': 241, 'subject_code': 'Aardrijkskunde', 'examperiod': 1, 
            'version': 'Cariben', 'secret_exam': False}
            """

            mode = upload_dict.get('mode')

# - get permit
            has_permit = False
            if req_usr and req_usr.country:
                permit_list = acc_prm.get_permit_list('page_exams', req_usr)
                if permit_list:
                    # unpublish only allowed when permit_publish_exam
                    if mode == 'undo_published':
                        has_permit = 'permit_publish_exam' in permit_list
                    else:
                        has_permit = 'permit_crud' in permit_list

                if logging_on:
                    logger.debug('    permit_list: ' + str(permit_list))
                    logger.debug('    has_permit: ' + str(has_permit))

            if not has_permit:
                msg_list.append(acc_prm.err_txt_no_permit()) # default: 'to perform this action')
            else:
                append_dict = {}
                updated_exam_pk_list = []
                deleted_row = None

# - get variables from upload_dict
                table = upload_dict.get('table')
                # PR2023-06-14 I didnt know why this was necessary: was to give msg cant change exam of other country
                #   don't get it from usersettings, get it from upload_dict instead
                # subj_examyear_pk = upload_dict.get('examyear_pk')
                depbase_pk = upload_dict.get('depbase_pk')
                lvlbase_pk = upload_dict.get('lvlbase_pk')

                # PR2023-05-04 debug: examperiod can be -1 for all exam periods
                sel_examperiod = upload_dict.get('examperiod')

                exam_pk = upload_dict.get('exam_pk')
                # PR2022-02-20 debug: exam uses subject_pk, not subjbase_pk
                subject_pk = upload_dict.get('subject_pk')

                show_all = upload_dict.get('show_all') or False

# - get selected examyear and from Usersetting
                sel_examyear, sel_schoolNIU, sel_department, sel_level, may_editNIU, msg_listNIU = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(
                        request=request,
                    skip_allowed_filter=True  # PR2023-06-14 debug added:skip_allowed_filter=True
                    )
                if logging_on:
                    logger.debug('    sel_examyear.pk: ' + str(sel_examyear.pk))
                    logger.debug('    sel_department: ' + str(sel_department))

                # note: exams can be changed before publishing examyear, therefore don't filter on examyear.published
                if sel_examyear and sel_department:
       # - get subject
                    subject = subj_mod.Subject.objects.get_or_none(pk=subject_pk)
                    if logging_on:
                        logger.debug('    subject: ' + str(subject))

                    if subject is None:
                        err_txt = gettext('Subject not found.')
                        msg_list.append(acc_prm.msghtml_from_msgtxt_with_border(err_txt, c.HTMLCLASS_border_bg_invalid))

                    elif sel_examyear.pk != subject.examyear_id:
                        err_txt = ''
                        if logging_on:
                            logger.debug('    subj_examyear: ' + str(subject.examyear))

                        if subject.examyear:
                            err_txt += str(_("This exam is created by %(country)s.") % {'country': subject.examyear.country.name}) + '<br>'
                        err_txt += str(_("You cannot make changes in this exam."))
                        msg_list.append(acc_prm.msghtml_from_msgtxt_with_border(err_txt, c.HTMLCLASS_border_bg_invalid))
                    else:

# +++++ Create new instance if is_create
                        if mode == 'create':
                            department = sch_mod.Department.objects.get_or_none(
                                base=sel_department.base,
                                examyear=sel_examyear
                            )
                            level = subj_mod.Level.objects.get_or_none(
                                base_id=lvlbase_pk,
                                examyear=sel_examyear
                            )
                            if logging_on:
                                logger.debug('    department: ' + str(department))
                                logger.debug('    level: ' + str(level))

                            examperiod_int = upload_dict.get('examperiod')
                            ete_exam = (table == 'ete_exam')
                            exam_instance, err_html = create_exam_instance(
                                subject=subject,
                                department=department,
                                level=level,
                                examperiod_int=examperiod_int,
                                ete_exam=ete_exam,
                                request=request
                            )

                            if err_html:
                                msg_list.append(acc_prm.msghtml_from_msgtxt_with_border(err_html, c.HTMLCLASS_border_bg_invalid))
                            elif exam_instance:
                                updated_exam_pk_list.append(exam_instance.pk)
                                append_dict[exam_instance.pk] = {'created': True}

                            if logging_on:
                                logger.debug('    created exam_instance: ' + str(exam_instance))
                                logger.debug('    append_dict: ' + str(append_dict))

                        else:

    # - else: get existing exam instance
                            exam_instance = subj_mod.Exam.objects.get_or_none(
                                id=exam_pk,
                                subject=subject
                            )
                            if not exam_instance:
                                msg_list.append(acc_prm.msghtml_from_msgtxt_with_border(
                                    _("AWP could not find this exam."), c.HTMLCLASS_border_bg_invalid))

                        if logging_on:
                            logger.debug('exam_instance: ' + str(exam_instance))

                        if not msg_list:

# +++++ Delete instance if is_delete
                            if mode == 'delete':
                                if getattr(exam_instance, 'published_id'):
                                    err_txt = '<br>'.join((gettext('This exam is already published.'),
                                                           gettext(
                                                               'You must first remove the publication before you can delete the exam.')))
                                    msg_list.append(
                                        acc_prm.msghtml_from_msgtxt_with_border(err_txt, c.HTMLCLASS_border_bg_transparent))
                                else:
                                    deleted_row, err_html = delete_exam_instance(exam_instance, request)
                                    if err_html:
                                        msg_list.append(acc_prm.msghtml_from_msgtxt_with_border(err_html, c.HTMLCLASS_border_bg_invalid))
                            else:

# +++++ Update instance, also when it is created, not when is_delete
                                err_list = []
                                updated_cegrade_count = update_exam_instance(
                                    request=request,
                                    sel_examyear=sel_examyear,
                                    sel_department=sel_department,
                                    exam_instance=exam_instance,
                                    upload_dict=upload_dict,
                                    error_list=err_list
                                )
                                if logging_on:
                                    logger.debug('---- updated_cegrade_count: ' + str(updated_cegrade_count))

                                if err_list:
                                    err_txt = '<br>'.join(err_list)
                                    msg_list.append(acc_prm.msghtml_from_msgtxt_with_border(err_txt, c.HTMLCLASS_border_bg_invalid))
                                else:
                                    if exam_instance.pk not in updated_exam_pk_list:
                                        updated_exam_pk_list.append(exam_instance.pk)

            # - return message when CE-grades are calculated after entering cesuur or scalelength
                                if updated_cegrade_count:
                                    if updated_cegrade_count == 1:
                                        msg_txt = gettext('1 CE grade has been calculated from the score.')
                                    else:
                                        msg_txt = gettext('%(count)s CE grades have been calculated from the scores.') \
                                                       % {'count': str(updated_cegrade_count)}
                                    msg_list.append(acc_prm.msghtml_from_msgtxt_with_border(msg_txt, c.HTMLCLASS_border_bg_valid))

                        if logging_on:
                            logger.debug('---- exam_instance: ' + str(exam_instance))
                            logger.debug('---- table: ' + str(table))

        # 6. create list of deleted exam
                        if deleted_row:
                            update_wrap['updated_ete_exam_rows'] = [deleted_row]

                        else:
                            # exam_pk_list = [exam_instance.pk] if exam_instance else None
                            if table == 'ete_exam':
                                updated_ete_exam_rows = create_ete_exam_rows(
                                    req_usr=req_usr,
                                    sel_examyear=sel_examyear,
                                    sel_depbase=sel_department.base,
                                    append_dict=append_dict,
                                    show_all=show_all,
                                    exam_pk_list=updated_exam_pk_list
                                )
                                if updated_ete_exam_rows:
                                    update_wrap['updated_ete_exam_rows'] = updated_ete_exam_rows

                            elif table == 'duo_exam':

                                updated_duo_exam_rows = create_duo_exam_rows(
                                    req_usr=request.user,
                                    sel_examyear=sel_examyear,
                                    sel_depbase=sel_department.base,
                                    sel_lvlbase=sel_level.base if sel_level else None,
                                    sel_examperiod=sel_examperiod,
                                    append_dict=append_dict,
                                    exam_pk_list=updated_exam_pk_list
                                )
                                if updated_duo_exam_rows:
                                    update_wrap['updated_duo_exam_rows'] = updated_duo_exam_rows

        if msg_list:
            update_wrap['msg_html'] = acc_prm.msghtml_from_msglist_with_border(msg_list)

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamUploadView


# ============= ExamCopyView ============= PR2022-03-23
@method_decorator([login_required], name='dispatch')
class ExamCopyView(View):

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamCopyView ============= ')

        req_usr = request.user
        update_wrap = {}
        err_html = ''

# - reset language
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

# - add edit permit
        has_permit = False
        if req_usr and req_usr.country:
            permit_list = acc_prm.get_permit_list('page_exams', req_usr)
            if permit_list:
                has_permit = 'permit_crud' in permit_list
            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

        if not has_permit:
            err_html = str(_("You don't have permission to perform this action."))
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))

                error_list = []
                append_dict = {}

# - get variables from upload_dict
                # upload_dict{'table': 'exam', 'mode': 'update', 'field': 'authby', 'auth_index': 2, 'auth_bool_at_index': True, 'exam_pk': 138}

                # don't get it from usersettings, get it from upload_dict instead
                mode = upload_dict.get('mode')
                if mode == 'copy':
                    examyear_pk = upload_dict.get('examyear_pk')
                    exam_pk = upload_dict.get('exam_pk')
                    # PR2022-02-20 debug: exam uses subject_pk, not subjbase_pk
                    subject_pk = upload_dict.get('subject_pk')

    # - check if examyear exists and equals selected examyear from Usersetting
                    selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                    selected_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                    if examyear_pk == selected_examyear_pk:
                        examyear = sch_mod.Examyear.objects.get_or_none(
                            id=examyear_pk,
                            country=req_usr.country
                        )
                        # note: exams can be changed before publishing examyear, therefore don't filter on examyear.published
                        if examyear and not examyear.locked:
        # - get subject
                            subject = subj_mod.Subject.objects.get_or_none(
                                id=subject_pk,
                                examyear=examyear
                            )
                            if logging_on:
                                logger.debug('subject:     ' + str(subject))

                            if subject:
        # - else: get existing exam instance
                                exam = subj_mod.Exam.objects.get_or_none(
                                    id=exam_pk,
                                    subject=subject
                                )
                                if logging_on:
                                    logger.debug('exam: ' + str(exam))
                                if exam:
                                    copy_txt = pgettext_lazy('noun', 'copy')
                                    new_version = ' - '.join((exam.version, str(copy_txt))) if exam.version else str(copy_txt)
                                    new_exam = None
                                    try:
                                        new_exam = subj_mod.Exam(
                                            subject=exam.subject,
                                            department=exam.department,
                                            level=exam.level,
                                            ntermentable=exam.ntermentable,
                                            ete_exam=exam.ete_exam,
                                            examperiod=exam.examperiod,
                                            version=new_version,
                                            has_partex=exam.has_partex,
                                            partex=exam.partex,
                                            amount=exam.amount,
                                            blanks=exam.blanks,
                                            assignment=exam.assignment,
                                            keys=exam.keys,
                                            status=0,
                                            #auth1by, auth1by, auth1by, published, locked
                                            nex_id=exam.nex_id,
                                            scalelength=exam.scalelength,
                                            cesuur=exam.cesuur,
                                            nterm=exam.nterm
                                        )
                                        new_exam.save(request=request)
                                        if logging_on:
                                            logger.debug('new_exam: ' + str(new_exam))

                                    except Exception as e:
                                        # - create error when exam is  not created
                                        logger.error(getattr(e, 'message', str(e)))
                                        err_html = ' '.join((str(_('An error occurred.')), str(_('This exam could not be copied.'))))

                # 6. create list of updated exam
                                    if new_exam:
                                        updated_ete_exam_rows = create_ete_exam_rows(
                                            req_usr=req_usr,
                                            sel_examyear=new_exam.department.examyear,
                                            sel_depbase=new_exam.department.base,
                                            append_dict={'created': True},
                                            exam_pk_list=[new_exam.pk]
                                        )

                                        if updated_ete_exam_rows:
                                            update_wrap['updated_ete_exam_rows'] = updated_ete_exam_rows
        if err_html:
            update_wrap['msg_html'] = err_html
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamCopyView

# ============= ExamCopyNtermenView ============= PR2022-06-02
@method_decorator([login_required], name='dispatch')
class ExamCopyNtermenView(View):

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamCopyNtermenView ============= ')

        req_usr = request.user
        update_wrap = {}
        err_html = ''

# - reset language
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

# - add edit permit
        has_permit = False
        if req_usr and req_usr.country:
            permit_list = acc_prm.get_permit_list('page_exams', req_usr)
            if permit_list:
                has_permit = 'permit_crud' in permit_list
            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

        if not has_permit:
            err_html = acc_prm.err_html_no_permit()  # default: 'to perform this action')
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('    upload_dict' + str(upload_dict))

                log_list = [str(_('Copy N-termentabel')), ' ']

# - get variables from upload_dict
                # upload_dict{'table': 'exam', 'mode': 'update', 'field': 'authby', 'auth_index': 2, 'auth_bool_at_index': True, 'exam_pk': 138}

                # don't get it from usersettings, get it from upload_dict instead
                mode = upload_dict.get('mode')
                if mode == 'copy_ntermen':
                    examyear_pk = upload_dict.get('examyear_pk')
                    if logging_on:
                        logger.debug('    examyear_pk' + str(examyear_pk) + ' ' + str(type(examyear_pk)))

    # - check if examyear exists and equals selected examyear from Usersetting
                    selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                    selected_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                    if logging_on:
                        logger.debug('    selected_examyear_pk: ' + str(selected_examyear_pk) + ' ' + str(type(selected_examyear_pk)))

                    if examyear_pk == selected_examyear_pk:
                        if logging_on:
                            logger.debug('    examyear_pk == selected_examyear_pk')

                        examyear = sch_mod.Examyear.objects.get_or_none(
                            pk=examyear_pk,
                            country=req_usr.country
                        )
                        if logging_on:
                            logger.debug('    examyear' + str(examyear))

                        # note: exams can be changed before publishing examyear, therefore don't filter on examyear.published
                        if examyear and not examyear.locked:
        # - get exams
                            exams = subj_mod.Exam.objects.filter(
                                department__examyear=examyear,
                                ete_exam=False
                            ).order_by('examperiod', 'department__base_id', 'subject__name_nl', 'level__base__code')
                            if logging_on:
                                logger.debug('    exams count' + str(len(exams)))
                            if exams:
                                for exam in exams:
                                    if logging_on:
                                        logger.debug('..... ')
                                        logger.debug('   exam: ' + str(exam))

                                    subject = exam.subject.name_nl if exam.subject.name_nl else '---'
                                    dep_code = exam.department.base.code if exam.department.base.code else '---'

                                    exam_name_list = [dep_code, subject]
                                    if exam.level:
                                        exam_name_list.append(exam.level.base.code)
                                    exam_name_list.append(c.get_examperiod_caption(exam.examperiod))

                                    exam_name = ' '.join(exam_name_list)
                                    if logging_on:
                                        logger.debug('    exam_name: ' + str(exam_name))

                                    log_list.append(' ')
                                    log_list.append(exam_name)

                                    ntermentable = exam.ntermentable

                                    if logging_on:
                                        logger.debug('    ntermentable: ' + str(ntermentable))

                                    if not ntermentable:
                                        log_list.append(''.join(('    ', str(_('This exam is not linked to a CVTE exam.')))))

                                    else:
                                        log_list.append(''.join(('    ', str(_('CVTE exam')), ': ', ntermentable.omschrijving)))

        # - loop through DUO exams
                                        old_scalelength = getattr(exam, 'scalelength')
                                        old_nterm = getattr(exam, 'nterm')
                                        new_scalelength = getattr(ntermentable, 'schaallengte')
                                        new_nterm = getattr(ntermentable, 'n_term')

                                        not_entered_txt = str(_('Not entered')).lower()
                                        old_scalelength_txt = old_scalelength if old_scalelength else not_entered_txt
                                        new_scalelength_txt = new_scalelength if new_scalelength else not_entered_txt
                                        old_nterm_txt = old_nterm if old_nterm else not_entered_txt
                                        new_nterm_txt = new_nterm if new_nterm else not_entered_txt

                                        if logging_on:
                                            logger.debug('    scalelength' + str(exam_name) + ' <> ' + str(new_scalelength))
                                            logger.debug('    nterm' + str(new_nterm) + ' <> ' + str(new_nterm))

                                        if new_scalelength == old_scalelength and new_nterm == old_nterm:
                                            log_list.append(''.join(('       ', str(_('no changes')), ':')))
                                            if old_scalelength:
                                                log_list.append(''.join(('       ', str(_('Scale length')).lower(), ': ',
                                                                      str(old_scalelength_txt))))
                                            if old_nterm:
                                                log_list.append(''.join(('       ', str(_('N-term')), ':    ',
                                                                          str(old_nterm_txt))))

                                        else:
                                            if new_scalelength != old_scalelength:
                                                setattr(exam, 'scalelength', new_scalelength)

                                                log_list.append(' '.join(('    ', str(_('Scale length')).lower(), ': ', str(old_scalelength_txt), '>', str(new_scalelength_txt))))

                                            if new_nterm != old_nterm:
                                                setattr(exam, 'nterm', new_nterm)

                                                log_list.append(' '.join(( '    ', str(_('N-term')), ':    ', str(old_nterm_txt), '>', str(new_nterm_txt))))

                                            exam.save(request=request)

                update_wrap['loglist_copied_ntermen'] = log_list

        if err_html:
            update_wrap['msg_html'] = err_html
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamCopyNtermenView


# ============= ExamLinkExamToGradesView ============= PR2022-05-23
@method_decorator([login_required], name='dispatch')
class ExamLinkExamToGradesView(View):

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamLinkExamToGradesView ============= ')

        req_usr = request.user
        update_wrap = {}
        msg_list = []

# - reset language
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

# - add edit permit
        has_permit = False
        if req_usr and req_usr.country:
            permit_list = acc_prm.get_permit_list('page_exams', req_usr)
            if permit_list:
                has_permit = 'permit_crud' in permit_list
            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

        if not has_permit:
            msg_list.append(acc_prm.err_html_no_permit() ) # default: 'to perform this action')
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('    upload_dict' + str(upload_dict))
                """
                upload_dict{'mode': 'link_exam_to_grades', 'exam_pk': 190, 'examyear_pk': 2, 
                        'subject_pk': 159, 'subj_name_nl': 'Spaanse taal en literatuur', 
                        'is_test': True}
                SXM links DUO exam:
                upload_dict{'mode': 'link_exam_to_grades', 'exam_pk': 190, 'examyear_pk': 2, 
                        'subject_pk': 159, 'is_test': False} 
                SXM links DUO exam:
                upload_dict{'mode': 'link_exam_to_grades', 'exam_pk': 258, 'examyear_pk': 2,
                        'subject_pk': 172, 'subj_name_nl': 'Franse taal', 'is_test': True}
                SXM links ETE exam:
                upload_dict{'mode': 'link_exam_to_grades', 'exam_pk': 30, 'examyear_pk': 1, 
                'subject_pk': 133, 'subj_name_nl': 'Administratie en commercie', 'is_test': True}
                requsr_examyear_pk2
                        
                """

# - get variables from upload_dict
                # upload_dict{'table': 'exam', 'mode': 'update', 'field': 'authby', 'auth_index': 2, 'auth_bool_at_index': True, 'exam_pk': 138}

                # don't get it from usersettings, get it from upload_dict instead
                mode = upload_dict.get('mode')
                if mode == 'link_exam_to_grades':
                    # examyear_pk is the examyear of the selected exam ( = exam.subject.examyear.pk)
                    exam_examyear_pk = upload_dict.get('examyear_pk')
                    exam_pk = upload_dict.get('exam_pk')
                    is_test = upload_dict.get('is_test') or False

                    # PR2022-02-20 debug: exam uses subject_pk, not subjbase_pk
                    subject_pk = upload_dict.get('subject_pk')

                    if logging_on:
                        logger.debug('    is_test: ' + str(is_test))
                        logger.debug('    exam_pk: ' + str(exam_pk))
                        logger.debug('    exam_examyear_pk: ' + str(exam_examyear_pk))
                        logger.debug('    subject_pk: ' + str(subject_pk))

                    # WARNING: let ETE only link CUr grades, and SXM only link Sxm grades

    # - check if examyear exists and equals selected examyear from Usersetting
                    # - exam is linked to subject > examyear > country. Therefore exam is country-specific
                    # - ETE exams are only Cur-exams, can be created or copied by ETE
                    #       therefore SXM must be able to link ETE-Cur exams to grades, filter by ey_code, not by ey_pk
                    # - Cur and SXM can each add their own DUO-exam, because SXM has some DUO exams that CUR doesn't have
                    #       DUO -exams are created or deleted when linking a subject with a ntermen exam

                    requsr_examyear_pk, requsr_depbase_pk = None, None
                    selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                    if selected_dict:
                        requsr_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                        requsr_depbase_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)

                    if logging_on:
                        logger.debug('    requsr_examyear_pk: ' + str(requsr_examyear_pk))

            # get examyear and subjbase of exam.subject
                    # when SXM links ETE exam:
                    # - exam.examyear is CUR exam year
                    # lookup exam_examyear, to get examyear_code

                    exam_examyear = sch_mod.Examyear.objects.get_or_none(pk=exam_examyear_pk)

            # get requsr_examyear_pk
                    requsr_examyear = sch_mod.Examyear.objects.get_or_none(pk=requsr_examyear_pk)

                    # note: exams can be changed before publishing examyear, therefore don't filter on examyear.published
                    if exam_examyear and requsr_examyear and not requsr_examyear.locked:

            # - get selected exam instance
                        sel_exam = subj_mod.Exam.objects.get_or_none(
                            id=exam_pk,
                            subject__examyear=exam_examyear
                        )
                        if sel_exam:
                            if logging_on:
                                logger.debug('    sel_exam: ' + str(sel_exam))

                            sel_exam_subject = sel_exam.subject
                            if logging_on:
                                logger.debug('    sel_exam_subject: ' + str(sel_exam_subject))
                            sel_exam_subjbase = sel_exam_subject.base
                            if logging_on:
                                logger.debug('    sel_exam_subjbase: ' + str(sel_exam_subjbase))
                                logger.debug('    sel_exam_subjbase.code: ' + str(sel_exam_subjbase.code))

                            if sel_exam_subjbase:

            # - get subject  - subject can be from different country when ETE exam > filter on examyear.code, not on examyear.pk
            # get subject of this country
            # - PR2022-07-01 ERROR: spanish went back to ETE because ETE linked SXM grades.
            # Let each country link their own grades
                                # - DON'T: when ETE exam: linked subject is then CUR subject
                                # was: examyear_code=examyear.code
                                this_country_subject = subj_mod.Subject.objects.get_or_none(
                                    base=sel_exam_subjbase,
                                    examyear=requsr_examyear,
                                )
                                if this_country_subject:
                                    if logging_on:
                                        logger.debug('this_country_subject:     ' + str(this_country_subject))
                                        logger.debug('this_country_subject.examyear.pk:     ' + str(this_country_subject.examyear.pk))

                                    ete_duo_exam = str(_('The ETE exam') if sel_exam.ete_exam else _('The CVTE exam'))
                                    # def get_exam_name(ce_exam_id, ete_exam, subj_name_nl, depbase_code, lvl_abbrev, examperiod, version, ntb_omschrijving):
                                    exam_name = get_exam_name(
                                        ce_exam_id=sel_exam.pk,
                                        ete_exam=sel_exam.ete_exam,
                                        subj_name_nl=sel_exam.subject.name_nl,
                                        depbase_code=sel_exam.department.base.code,
                                        lvl_abbrev=sel_exam.level.abbrev if sel_exam.level else '-',
                                        examperiod=sel_exam.examperiod,
                                        examyear=exam_examyear,
                                        version=sel_exam.version,
                                        ntb_omschrijving=sel_exam.ntermentable.omschrijving if sel_exam.ntermentable else None
                                    )
# --- add exam_pk to grades, only when there is only 1 exam for this subject / dep / level / examperiod
                                    # check if subject has only 1 exam takes place in link_exam_to_grades
                                    # PR2023-05-26 debug: must filter on weight_ce>0 becasue of sptl without CE
                                    grd_count, log_list = link_exam_to_grades(
                                        exam_instance=sel_exam,
                                        requsr_examyear_pk=requsr_examyear.pk,
                                        requsr_depbase_pk=requsr_depbase_pk,
                                        exam_name=exam_name,
                                        is_test=is_test,
                                        is_saved_in_loglist=False
                                    )
                                    if grd_count:
                                        if is_test:
                                            msg_list.append(''.join((
                                                "<p>", str(ete_duo_exam), ":</p><ul class='py-0'><li>", exam_name, "'</li></ul>",
                                                "<p>", str(_("will be linked to the corresponding subject")), " ",
                                                str(_("of %(val)s candidates.") % {'val': str(grd_count)}),' ',
                                                str(_("The list of candidates has been downloaded.")), "</p>",
                                                "<p>", str(_("Do you want to continue?")), "</p>"
                                            )))
                                        else:
                                            msg_list.append(''.join((
                                                "<div class='border_bg_valid'><p>", str(ete_duo_exam), ":</p><ul class='py-0'><li>", exam_name, "'</li></ul>",
                                                "<p>", str(_("has been linked to the corresponding subject")), " ",
                                                str(_("of %(val)s candidates.") % {'val': str(grd_count)}), "</p><p>",
                                                str(_("The list of candidates has been downloaded.")), "</p></div>"
                                            )))
                                            update_wrap['response_link_exam_is_saved'] = True

                            # --- return list of students with linked exams
                                    # check if subject has only 1 exam takes place in link_exam_to_grades
                                            grd_countNIU, log_list = link_exam_to_grades(
                                                exam_instance=sel_exam,
                                                requsr_examyear_pk=requsr_examyear.pk,
                                                requsr_depbase_pk=requsr_depbase_pk,
                                                exam_name=exam_name,
                                                is_test=True,
                                                is_saved_in_loglist=True
                                            )

                                    else:
                                        msg_list.append(''.join((
                                            "<p>", str(_('There are no candidates with the exam')), ":</p><ul class='py-0'><li>", exam_name,
                                            "'</li></ul>",
                                        )))

                                    update_wrap['response_link_exam_to_grades_loglist'] = log_list
                                    update_wrap['response_link_exam_has_grades'] = not not grd_count

                                else:
                                    msg_list.append(''.join((
                                        "<div class='p-2 border_bg_invalid'>",
                                        str(_('The exam is not found')),
                                        '</div')))

        if msg_list:
            update_wrap['response_link_exam_to_grades'] = ''.join(msg_list)
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamLinkExamToGradesView

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# ============= ExamUploadDuoExamView =============
@method_decorator([login_required], name='dispatch')
class ExamUploadDuoExamView(View):
    # PR2021-04-07 PR2022-08-28 PR2023-03-20

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamUploadDuoExamView ============= ')

        def delete_duo_exam_instance(exam_pk):  # PR2022-04-09 PR2022-08-28 PR2023-03-20
            logging_on = s.LOGGING_ON
            if logging_on:
                logger.debug(' --- delete_duo_exam_instance --- ')
                logger.debug('    exam_pk: ' + str(exam_pk))

            deleted_row = None
            err_html = None

            exam_inst = subj_mod.Exam.objects.get_or_none(pk=exam_pk)
            if logging_on:
                logger.debug('exam_inst: ' + str(exam_inst))

            if exam_inst:

        # - check if grades connected to this exam_inst
                count_grades = validate_exam_has_grades(exam_inst)
                if logging_on:
                    logger.debug('    count_grades: ' + str(count_grades))

                if count_grades:

                    if count_grades == 1:
                        err_txt = _('There is 1 candidate with this exam.')
                    else:
                        err_txt = _('There are %(count)s candidates with this exam.') % {'count': str(count_grades)}
                    err_html = acc_prm.msghtml_from_msglist_with_border((err_txt, _('This CVTE exam can not be deleted.')))
                else:

                    try:
            # - create deleted_row
                        deleted_row = {'id': exam_inst.pk,
                                       'mapid': 'exam_' + str(exam_inst.pk),
                                       'deleted': True}
                        if logging_on:
                            logger.debug('    deleted_row: ' + str(deleted_row))

            # - delete instance
                        exam_inst.delete(request=request)

                    except Exception as e:
                        deleted_row = None
                        logger.error(getattr(e, 'message', str(e)))
                        err_html = acc_prm.errhtml_error_occurred_with_border(e, _('This CVTE exam can not be deleted.'))

            if logging_on:
                logger.debug('    deleted_row: ' + str(deleted_row))
                logger.debug('    err_html: ' + str(err_html))

            return deleted_row, err_html
    # - end of delete_duo_exam_instance

        req_usr = request.user
        update_wrap = {}
        msg_html = None

# - reset language
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            if logging_on:
                logger.debug('upload_dict' + str(upload_dict))

            mode = upload_dict.get('mode')

# - get permit
            has_permit = False
            if req_usr and req_usr.country:
                permit_list = acc_prm.get_permit_list('page_exams', req_usr)
                if permit_list:
                    has_permit = 'permit_crud' in permit_list
                if logging_on:
                    logger.debug('    permit_list: ' + str(permit_list))
                    logger.debug('    has_permit: ' + str(has_permit))

            if not has_permit:
                msg_html = acc_prm.err_html_no_permit()  # default: 'to perform this action')
            else:

                append_dict = {}
                updated_exam_pk_list = []

# - get variables from upload_dict
                # upload_dict{'table': 'exam', 'mode': 'update', 'field': 'authby', 'auth_index': 2, 'auth_bool_at_index': True, 'exam_pk': 138}
                """
                upload_dict{'mode': 'delete', 'examyear_pk': 1, 'depbase_pk': 1}
                upload_dict{'exam_list': [
                {'subj_id': 226, 'ntb_id': None, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Franse taal', 'exam_id': None, 'ntb_omschrijving': None}, {'subj_id': 229, 'ntb_id': 532, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Wiskunde', 'exam_id': 341, 'ntb_omschrijving': 'GL/TL wiskunde CSE 2023 tijdvak 1'}, {'subj_id': 234, 'ntb_id': None, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Natuurkunde & Scheikunde 1', 'exam_id': 286, 'ntb_omschrijving': None}, {'subj_id': 235, 'ntb_id': None, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Natuurkunde en scheikunde 2', 'exam_id': 293, 'ntb_omschrijving': None}, {'subj_id': 238, 'ntb_id': 539, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Biologie', 'exam_id': 266, 'ntb_omschrijving': 'GL/TL biologie CSE 2023 tijdvak 1'}, {'subj_id': 239, 'ntb_id': None, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Economie', 'exam_id': 277, 'ntb_omschrijving': None}]}
                
                exam_list[
                    {'subj_id': 229, 'ntb_id': None, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Wiskunde', 'exam_id': 341, 'ntb_omschrijving': None},
                    {'subj_id': 234, 'ntb_id': None, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Natuurkunde & Scheikunde 1', 'exam_id': 286, 'ntb_omschrijving': None}, 
                    {'subj_id': 235, 'ntb_id': None, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Natuurkunde en scheikunde 2', 'exam_id': 293, 'ntb_omschrijving': None},
                    {'subj_id': 238, 'ntb_id': 539, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Biologie', 'exam_id': 266, 'ntb_omschrijving': 'GL/TL biologie CSE 2023 tijdvak 1'}, 
                    {'subj_id': 239, 'ntb_id': None, 'dep_pk': 10, 'level_pk': 12, 'subj_name_nl': 'Economie', 'exam_id': 277, 'ntb_omschrijving': None}] <class 'list'>

                """
        # - get examperiod from upload_dict
                examperiod_int = upload_dict.get('examperiod')

                exam_list = upload_dict.get('exam_list')
                if logging_on:
                    logger.debug('    examperiod_int: ' + str(examperiod_int) + ' ' + str(type(examperiod_int)))
                    logger.debug('    exam_list: ' + str(exam_list) + ' ' + str(type(exam_list)))

        # +++++ Delete instance if is_delete
                if mode == 'delete':
                    exam_pk = upload_dict.get('exam_pk')
                    deleted_row, err_html = delete_duo_exam_instance(exam_pk)
                    if err_html:
                        msg_html = err_html
                    if deleted_row:
                        update_wrap['updated_duo_exam_rows'] = [deleted_row]
                else:

                    for exam_dict in exam_list:

                        subj_id = exam_dict.get('subj_id')

            # - get subject_instance and department_instance
                        subject_instance = subj_mod.Subject.objects.get_or_none(id=subj_id)
                        department_instance = sch_mod.Department.objects.get_or_none(id=exam_dict.get('dep_pk'))

                        if logging_on:
                            logger.debug('    subject_instance: ' + str(subject_instance))
                            logger.debug('    department_instance: ' + str(department_instance))

                        if subject_instance and department_instance:

            # - get exam_instance, level_instance and ntermentable_instance
                            # level_instance can be None
                            level_instance = subj_mod.Level.objects.get_or_none(id=exam_dict.get('level_pk'))
                            ntermentable_instance = subj_mod.Ntermentable.objects.get_or_none(id=exam_dict.get('ntb_id'))

                            if logging_on:
                                logger.debug('    level_instance: ' + str(level_instance))
                                logger.debug('    ntermentable_instance: ' + str(ntermentable_instance))

            # get existing exam instance
                            exam_id = exam_dict.get('exam_id')
                            exam_instance = subj_mod.Exam.objects.get_or_none(id=exam_id)
                            if logging_on:
                                logger.debug('    exam_instance: ' + str(exam_instance))

            # - create exam if it does not exist and ntb_id exists
                            # PR 2023-04-21 error: column "none" does not exist
                            # LINE 1: ...ND exam.id IN (SELECT UNNEST(ARRAY[461, 458, 455, None]::INT...
                            # exam_pk_list contains 'None'
                            # cause: when exam_instance is None was stil added to the list
                            # was:
                            # if exam_instance is None and ntermentable_instance is not None:
                            if exam_instance is None:
                                exam_instance, err_html = create_exam_instance(
                                    subject=subject_instance,
                                    department=department_instance,
                                    level=level_instance,
                                    examperiod_int=examperiod_int,
                                    ete_exam=False,
                                    request=request,
                                    version=None,
                                    ntermentable=ntermentable_instance
                                )

                                if logging_on:
                                    logger.debug('    exam_instance: ' + str(exam_instance))
                                    logger.debug('    err_html: ' + str(err_html))

                                if err_html:
                                    msg_html = str(err_html)
                                if exam_instance:
                                    updated_exam_pk_list.append(exam_instance.pk)
                                    append_dict[exam_instance.pk] = {'created': True}
                            else:
                                # update ntermentable in exam_instance
                                    old_ntermentable = getattr(exam_instance, 'ntermentable')

                                    if logging_on:
                                        logger.debug('    old_ntermentable: ' + str(old_ntermentable))
                                        logger.debug('    ntermentable_instance: ' + str(ntermentable_instance))

                                    if ntermentable_instance != old_ntermentable:
                                        setattr(exam_instance, 'ntermentable', ntermentable_instance)
                                        exam_instance.save(request=request)

                                        updated_exam_pk_list.append(exam_instance.pk)

                # - create list of updated exams
                            updated_duo_exam_rows = create_duo_exam_rows(
                                req_usr=request.user,
                                sel_examyear=department_instance.examyear if department_instance else None,
                                sel_depbase=department_instance.base if department_instance else None,
                                sel_lvlbase=level_instance.base if level_instance else None,
                                sel_examperiod=examperiod_int,
                                append_dict=append_dict,
                                exam_pk_list=updated_exam_pk_list
                            )
                            if updated_duo_exam_rows:
                                update_wrap['updated_duo_exam_rows'] = updated_duo_exam_rows

# +++++ create instance
                if mode == 'create':

                    department_pk = upload_dict.get('department_pk')
                    level_pk = upload_dict.get('level_pk')
                    ntermentable_pk = upload_dict.get('ntermentable_pk')
                    # PR2022-04-09 version not in use yet, to be added when multiple exams per level are possible
                    version = upload_dict.get('version')
                    # PR2022-02-20 debug: exam uses subject_pk, not subjbase_pk
                    # warning: it uses CUR subject, make sure SXM connects the exam correctly
                    subject_pk = upload_dict.get('subject_pk')

                    if logging_on:
                        logger.debug('department_pk' + str(department_pk))
                        logger.debug('level_pk' + str(level_pk))
                        logger.debug('version' + str(version))
                        logger.debug('ntermentable_pk' + str(ntermentable_pk))

    # lookup ntermentable
                    ntermentable, examyear, examperiod_int, nex_id = None, None, None, None
                    if ntermentable_pk:
                        ntermentable = subj_mod.Ntermentable.objects.get_or_none(
                            pk=ntermentable_pk
                        )
                        if logging_on:
                            logger.debug('ntermentable' + str(ntermentable))
                        if ntermentable:
                            nex_id = ntermentable.nex_id
                            examperiod_int = ntermentable.tijdvak
                            if logging_on:
                                logger.debug('nex_id' + str(nex_id) + ' ' + str(type(nex_id)))

    # - check if examyear exists and equals selected examyear from Usersetting
                    # ntermentable has no fiels examyear - get it from nexid
                            if nex_id:
                                nex_id_str = str(nex_id)
                                if len(nex_id_str) > 1:
                                    year_str = nex_id_str[:2]
                                    examyear_pk = 2000 + int(year_str)

                                    examyear = sch_mod.Examyear.objects.get_or_none(
                                        code=examyear_pk,
                                        country=req_usr.country
                                    )
                                    if logging_on:
                                        logger.debug('examyear:       ' + str(examyear))

                    selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                    selected_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)

                    if logging_on:
                        logger.debug('nex_id:       ' + str(nex_id) + ' ' + str(type(nex_id)))
                        logger.debug('selected_examyear_pk:  ' + str(selected_examyear_pk) + ' ' + str(type(selected_examyear_pk)))

                    if examyear and examyear.pk == selected_examyear_pk and not examyear.locked:
    # - get subject
                        subject = subj_mod.Subject.objects.get_or_none(id=subject_pk, examyear=examyear)
                        department = sch_mod.Department.objects.get_or_none(pk=department_pk, examyear=examyear)
                        level = subj_mod.Level.objects.get_or_none(pk=level_pk, examyear=examyear)

                        if logging_on:
                            logger.debug('subject:        ' + str(subject))
                            logger.debug('department:     ' + str(department))
                            logger.debug('level:          ' + str(level))
                            logger.debug('examperiod_int: ' + str(examperiod_int))

    # +++++ Create new instance if is_create:
                        ete_exam = False
                        exam, msg_err = create_exam_instance(subject, department, level,
                                                             examperiod_int, ete_exam, request, version, ntermentable)
                        if msg_err:
                            msg_html = str(msg_err)
                        elif exam:
                            if logging_on:
                                logger.debug('created exam: ' + str(exam))
                                logger.debug('append_dict: ' + str(append_dict))

    # TODO link grades to this exam

        if msg_html:
            update_wrap['msg_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamUploadDuoExamView


def validate_exam_has_grades(exam_instance): # PR2022-04-09
    count_grades = 0

# - check if any grades are connected to this exam
    sql_keys = {'exam_id': exam_instance.pk}
    sql_list = [
        "SELECT COUNT(grd.ce_exam_id)",
        "FROM students_grade AS grd",
        "WHERE grd.ce_exam_id = %(exam_id)s::INT",
    ]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = cursor.fetchall()
        # rows: [(0,)]
        if rows:
            count_grades = rows[0][0]
    return count_grades


@method_decorator([login_required], name='dispatch')
class ExamApproveOrPublishExamView(View):  # PR2021-04-04 PR2022-01-31 PR2022-02-23  PR2023-04-16

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamApproveOrPublishExamView ============= ')

# function sets auth and publish of exam records - submitting grade_exams happens in ExamApproveOrSubmitWolfView
        update_wrap = {}
        requsr_auth = None
        msg_html = None

# - get permit
        # <PERMIT>
        # only users with role = admin and perm_approve_exam or publish_exam can approve or submit
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated

        has_permit_approve, has_permit_publish = False, False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.is_role_admin and req_usr.schoolbase:

            permit_list = acc_prm.get_permit_list('page_exams', req_usr)

            if permit_list:
                # msg_err is made on client side. Here: just skip if user has no or multiple functions

                # PR2023-02-03 was: was: requsr_usergroup_list = req_usr.usergroup_list
                requsr_usergroup_list = acc_prm.get_usergroup_list_from_user_instance(req_usr)
                is_auth1 = 'auth1' in requsr_usergroup_list
                is_auth2 = 'auth2' in requsr_usergroup_list
                if is_auth1 + is_auth2 == 1:
                    if is_auth1:
                        requsr_auth = 'auth1'
                    elif is_auth2:
                        requsr_auth = 'auth2'
                if requsr_auth:
                    has_permit_approve = 'permit_approve_exam' in permit_list
                    has_permit_publish = 'permit_publish_exam' in permit_list

                if logging_on:
                    logger.debug('permit_list: ' + str(permit_list))

        if has_permit_approve or has_permit_publish:

# -  get user_lang
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

# ----- get selected examyear and department from usersettings
                requsr_examyear, requsr_department, sel_schoolNIU, sel_examperiod = \
                    acc_view.get_selected_examyear_examperiod_dep_school_from_usersetting(request)
                msg_list = acc_view.message_examyear_missing_notpublished_locked(requsr_examyear)

                if msg_list:
                    msg_html = ''.join(("<div class='p-2 border_bg_warning'>", '<br>'.join(msg_list), '</>'))
                else:

# - get selected mode. Modes are 'approve_test' 'approve_save' 'approve_reset' 'submit_test' 'submit_save' 'publish_test' 'publish_submit'
                    mode = upload_dict.get('mode')
                    is_approve = True if 'approve_' in mode else False
                    is_submit = True if 'submit_' in mode else False
                    is_reset = True if '_reset' in mode else False
                    is_test = True if '_test' in mode else False

                    if logging_on:
                        logger.debug('upload_dict' + str(upload_dict))
                        logger.debug('mode: ' + str(mode))
                        logger.debug('is_approve: ' + str(is_approve))
                        logger.debug('is_submit: ' + str(is_submit))
                        logger.debug('is_test: ' + str(is_test))

# - when mode = submit_submit: check verificationcode.
                    verification_is_ok = True
                    if is_submit and not is_test:
                        verification_is_ok, verif_msg_html = af.check_verifcode_local(upload_dict, request)
                        if verif_msg_html:
                            msg_html = verif_msg_html
                        if verification_is_ok:
                            update_wrap['verification_is_ok'] = True

                    if verification_is_ok:
                        # also filter on sel_lvlbase_pk, sel_subjbase_pk when is_submit
                        sel_lvlbase_pk, sel_subjbase_pk = None, None
                        selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                        if selected_dict:
                            sel_lvlbase_pk = selected_dict.get(c.KEY_SEL_LVLBASE_PK)
                            # PR2024-03-31 deprecated: sel_subject_pk = selected_dict.get(c.KEY_SEL_SUBJECT_PK)
                            sel_subjbase_pk = selected_dict.get(c.KEY_SEL_SUBJBASE_PK)
                        if logging_on:
                            logger.debug('selected_dict: ' + str(selected_dict))

# +++ get selected exam_rows
                        # exclude published rows??
                        # when published_id has value it means that admin has published the exam, so it is visible for the schools.
                        # submitting the exams by schools happens with grade.ce_exam_published_id, because answers are stored in grade

                        crit = Q(subject__examyear=requsr_examyear) & \
                               Q(department=requsr_department) & \
                               Q(ete_exam=True) & \
                               Q(examperiod=sel_examperiod)

                        # examperiod=12 means both first and second examperiod are selected Not in use any more
                        #if sel_examperiod in (1, 2, 3):
                        #    crit.add(Q(examperiod=sel_examperiod), crit.connector)

                        # PR2023-05-16 debug call Pien van Dijk: cannot publish vwo exam
                        # cause: sel_lvlbase_pk has stil value
                        # solved by adding if requsr_department.level_req
                        # was: if sel_lvlbase_pk:
                        if requsr_department.level_req and sel_lvlbase_pk:
                            crit.add(Q(level__base_id=sel_lvlbase_pk), crit.connector)
                        if sel_subjbase_pk:
                            crit.add(Q(subject__base_id=sel_subjbase_pk), crit.connector)

                        exams = subj_mod.Exam.objects.filter(crit).order_by('subject__base__code')

                        if logging_on:
                            logger.debug('sel_examperiod:  ' + str(sel_examperiod))
                            logger.debug('requsr_department:  ' + str(requsr_department))
                            logger.debug('sel_lvlbase_pk:   ' + str(sel_lvlbase_pk))
                            logger.debug('sel_subjbase_pk: ' + str(sel_subjbase_pk))

                            row_count = subj_mod.Exam.objects.filter(crit).count()
                            logger.debug('row_count:      ' + str(row_count))

                        updated_exam_pk_list = []
                        count_dict = {'count': 0,
                                    'already_published': 0,
                                    'has_blanks': 0,
                                    'double_approved': 0,
                                    'committed': 0,
                                    'saved': 0,
                                    'saved_error': 0,
                                    'reset': 0,
                                    'already_approved': 0,
                                    'auth_missing': 0,
                                    'test_is_ok': False,
                                    'updated_grd_count': 0
                                    }
                        if exams is not None:

# +++++ loop through exams
                            if exams:
                                for exam_instance in exams:
                                    if is_approve:
                                        approve_exam(exam_instance, requsr_auth, is_test, is_reset, count_dict, updated_exam_pk_list, request)

                                    elif is_submit:

        # +++ create new published_instance for each exam. Only save it when it is not a test
                                        # file_name will be added after creating exam-form
                                        published_instance = None
                                        published_instance_pk = None

                                        if not is_test:
                                            now_arr = upload_dict.get('now_arr')
                                            published_instance = create_exam_published_instance(
                                                exam=exam_instance,
                                                now_arr=now_arr,
                                                request=request)  # PR2021-07-27
                                            if published_instance:
                                                published_instance_pk = published_instance.pk

                                            if logging_on:
                                                logger.debug('published_instance_pk' + str(published_instance_pk))

        # --- put published_id in exam
                                        update_exam_in_grades = publish_exam(
                                            request=request,
                                            exam_instance=exam_instance,
                                            published_instance=published_instance,
                                            is_test=is_test,
                                            count_dict=count_dict,
                                            updated_exam_pk_list=updated_exam_pk_list)

        # --- and add exam_pk to grades when published, only when there is only 1 exam for this subject / dep / level / examperiod
                                        if update_exam_in_grades:  # is_publish_exam and not is_test:

                                            exam_name = get_exam_name(
                                                ce_exam_id=exam_instance.pk,
                                                ete_exam=exam_instance.ete_exam,
                                                subj_name_nl=exam_instance.subject.name_nl,
                                                depbase_code=exam_instance.department.base.code,
                                                lvl_abbrev=exam_instance.level.abbrev if exam_instance.level else '-',
                                                examperiod=exam_instance.examperiod,
                                                examyear=exam_instance.subject.examyear,
                                                version=exam_instance.version,
                                                ntb_omschrijving=exam_instance.ntermentable.omschrijving if exam_instance.ntermentable else None
                                            )

                                            # check if subject has only 1 exam takes place in link_exam_to_grades
                                            grd_count, log_list = link_exam_to_grades(
                                                exam_instance=exam_instance,
                                                requsr_examyear_pk=requsr_examyear.pk,
                                                requsr_depbase_pk=requsr_department.base.pk,
                                                exam_name=exam_name,
                                                is_test=is_test,
                                                is_saved_in_loglist=not is_test
                                            )

                                            if grd_count:
                                                count_dict['updated_grd_count'] += grd_count

                                # - add rows to exam_rows, to be sent back to page
                                    # to increase speed, dont create return rows but refresh page after finishing this request

        # +++++  end of loop through  exams
                                #update_wrap['approve_count_dict'] = count_dict

                        # recalc score of grade-exams when exam has changed and there are grade-exams PR2022-05-22
                                grade_view.recalc_grade_ce_exam_score(updated_exam_pk_list)

# - create msg_html with info of rows
                        msg_html = create_exam_approve_publish_msg_list(
                            req_usr=req_usr,
                            count_dict=count_dict,
                            requsr_auth=requsr_auth,
                            is_approve=is_approve,
                            is_test=is_test
                        )

        # get updated_rows
                        if not is_test and updated_exam_pk_list:
                            rows = create_ete_exam_rows(
                                req_usr=req_usr,
                                sel_examyear=requsr_examyear,
                                sel_depbase=requsr_department.base,
                                append_dict={},
                                exam_pk_list=updated_exam_pk_list)
                            if rows:
                                update_wrap['updated_ete_exam_rows'] = rows

                        if is_test:
                            committed = count_dict.get('committed', 0)
                            if committed:
                                update_wrap['test_is_ok'] = True

# - add  msg_html to update_wrap
        update_wrap['approve_msg_html'] = msg_html

        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamApproveOrPublishExamView


@method_decorator([login_required], name='dispatch')
class ExamApproveOrSubmitWolfView(View):
    # PR2021-04-04 PR2022-03-11 PR2022-04-26 PR2022-05-06 PR2023-04-30 PR2024-06-30

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamApproveOrSubmitWolfView ============= ')

# function sets ce_published_id of grade records
        update_wrap = {}
        approve_msg_html = None
        msg_list = []
        border_class = None
        req_usr = request.user
        test_is_ok = False
        saved_is_ok = False
        has_tobesubmitted_eteexams = False
        is_single_approve = False

# -  get user_lang
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            if logging_on:
                logger.debug('upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'form': 'grade_exam', 'now_arr': [2022, 4, 26, 7, 9], 'mode': 'submit_test'}
            upload_dict: {'auth_index': 1, 'form': 'grade_exam', 'now_arr': [2023, 4, 30, 11, 40], 'mode': 'approve_test'}
            """

            # - get selected mode. Modes are 'approve_test', 'approve_reset', 'approve_save', 'submit_test', 'submit_save'
            mode = upload_dict.get('mode')
            auth_index = upload_dict.get('auth_index')
            # when approvingsingle grade_exam: grade_pk has value PR2023-05-26
            sel_grade_pk = upload_dict.get('grade_pk')
            if sel_grade_pk:
                is_single_approve = True

            is_approve = True if 'approve' in mode else False
            is_submit = True if 'submit' in mode else False
            is_reset = True if 'reset' in mode else False
            is_test = True if 'test' in mode else False

            if logging_on:
                logger.debug('    mode: ' + str(mode))

# -  get permit, must come after get upload_dict
            has_permit_approve = acc_prm.get_permit_of_this_page('page_wolf', 'approve_exam', request)
            has_permit_submit = acc_prm.get_permit_of_this_page('page_wolf', 'submit_exam', request)
            if logging_on:
                logger.debug('     has_permit_approve: ' + str(has_permit_approve))
                logger.debug('     has_permit_submit: ' + str(has_permit_submit))
                logger.debug('     is_approve: ' + str(is_approve))
                logger.debug('     is_submit: ' + str(is_submit))
                logger.debug('     is_reset: ' + str(is_reset))
                logger.debug('     is_test: ' + str(is_test))

            if not has_permit_approve and not has_permit_submit:
                border_class = c.HTMLCLASS_border_bg_invalid

                action_txt = gettext('to submit Wolf exams') if is_submit else gettext('to approve Wolf exams')
                msg_list.append(acc_prm.err_txt_no_permit(action_txt))
                approve_msg_html = acc_prm.err_txt_no_permit(action_txt)
                if logging_on:
                    logger.debug('    msg_list: ' + str(msg_list))

            elif auth_index in (1, 2, 3):
                requsr_auth = 'auth' + str(auth_index)
                if logging_on:
                    logger.debug('     requsr_auth: ' + str(requsr_auth))

 # - get grade_pk. It only has value when a single grade is approved
                # not necessary. Single grade exams are approved in GradeUploadView.update_grade_instance, field 'auth_index'

# - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request=request)

# - check if user is same_school
                is_role_same_school = req_usr.is_role_school and sel_school and req_usr.schoolbase and req_usr.schoolbase.pk == sel_school.base_id

                if err_list:
                    border_class = c.HTMLCLASS_border_bg_invalid
                    msg_list.append(err_list)
                elif not is_role_same_school:
                    # TODO enable admin to enter secret exams
                    pass

                elif (is_approve and has_permit_approve) or (is_submit and has_permit_submit):

                    if logging_on:
                        logger.debug('     req_usr.schoolbase:  ' + str(req_usr.schoolbase.code))
                        logger.debug('     is_role_same_school: ' + str(is_role_same_school))

# PR2024-05-06 debug: cannot approve Wolf, because sel_custer not allowed
                    # PR2023-05-28 debug: must filter only allowed_clusters of selected school
                    # PR2024-05-30 debug: also filter on examyear
                    # get saved settings
                    selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)

                    # get_allowed_sections
                    requsr_userallowed_instance = acc_prm.get_userallowed_instance(request.user, sel_examyear)
                    userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(requsr_userallowed_instance)

# - get saved_subjbase_pk from usersetting and check if it is in allowed_subjbase of sel_dep

                    userallowed_schoolbase_dict, userallowed_depbases_pk_arr = \
                        acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(
                           userallowed_sections_dict=userallowed_sections_dict,
                           sel_schoolbase_pk=sel_school.base_id if sel_school else None
                        )

                    userallowed_depbase_dict, userallowed_lvlbase_pk_arr = \
                        acc_prm.get_userallowed_depbase_dict_lvlbases_pk_arr(
                           allowed_schoolbase_dict=userallowed_schoolbase_dict,
                           sel_depbase_pk=sel_department.base_id if sel_department else None
                        )

                    userallowed_subjbase_pk_list = \
                        acc_prm.get_userallowed_subjbase_arr(
                           allowed_depbase_dict=userallowed_depbase_dict,
                           allowed_lvlbase_pk_arr=userallowed_lvlbase_pk_arr,
                           sel_lvlbase_pk=sel_level.base_id if sel_level else None
                        )

                    sel_subjbase_pk = None
                    saved_subjbase_pk = selected_pk_dict.get(c.KEY_SEL_SUBJBASE_PK)
                    if saved_subjbase_pk:
                        if not userallowed_subjbase_pk_list or \
                                saved_subjbase_pk in userallowed_subjbase_pk_list:
                            sel_subjbase_pk = saved_subjbase_pk

# - get saved_cluster_pk from usersetting and check if it is in allowed_clusters of sel_school
                    sel_cluster_pk = None
                    allowed_clusters_of_sel_school = acc_prm.get_allowed_clusters_of_sel_school(
                        sel_schoolbase_pk=sel_school.base_id,
                        sel_examyear_pk=sel_examyear.pk,
                        allowed_cluster_pk_list=acc_prm.get_userallowed_cluster_pk_list(requsr_userallowed_instance)
                    )
                    saved_cluster_pk = selected_pk_dict.get(c.KEY_SEL_CLUSTER_PK)
                    if saved_cluster_pk:
                        if not allowed_clusters_of_sel_school or \
                                saved_cluster_pk in allowed_clusters_of_sel_school:
                            sel_cluster_pk = saved_cluster_pk

                    if logging_on:
                        logger.debug('     saved_cluster_pk:  ' + str(saved_cluster_pk))
                        logger.debug('     allowed_clusters_of_sel_school:  ' + str(allowed_clusters_of_sel_school))
                        logger.debug('     sel_cluster_pk:  ' + str(sel_cluster_pk))

# - get selected examperiod from usersetting, only first and second examperiod
                    # PR2024-06-30 WOlf is only used in exameriod 1
                    sel_examperiod = c.EXAMPERIOD_FIRST
                    # was:
                    #   saved_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
                    #   sel_examperiod = saved_examperiod if saved_examperiod in (1, 2) else None

                    # +++ get selected grade_exam_rows
                    # exclude published rows:
                    #  - when published_id has value it means that admin has published the exam, so it is visible for the schools.
                    #  - submitting the exams by schools happens with grade.ce_exam_published_id, because answers are stored in grade

                    grade_exam_rows = get_approve_grade_exam_rows(
                        sel_examyear=sel_examyear,
                        sel_school=sel_school,
                        sel_department=sel_department,
                        sel_level=sel_level,
                        sel_examperiod=sel_examperiod,
                        is_submit=is_submit,
                        request=request,
                        sel_subjbase_pk=sel_subjbase_pk,
                        sel_cluster_pk=sel_cluster_pk,
                        sel_grade_pk=sel_grade_pk
                    )
                    if logging_on:
                        logger.debug('     sel_examperiod:      ' + str(sel_examperiod))
                        logger.debug('     sel_subjbase_pk:      ' + str(sel_subjbase_pk))
                        logger.debug('     row_count:      ' + str(len(grade_exam_rows)))

                    # grade_exams_tobe_updated_list contains list of tuples with (grade_pk, exam_pk)

                    grade_exams_tobe_updated_list = []
                    count_dict, total_dict = {}, {}
                    published_pk = None
                    err_html = None

                    if grade_exam_rows:

# +++ create new published_instance.
                        # only save it when it is not a test. PR2023-05-01 added:  and not is_reset:
                        # no file will be attached when submitting grade_exam. Published_id is only needed to indicate that exam is submitted and keep date submission

                        if not is_approve and not is_test and not is_reset:
                            now_arr = upload_dict.get('now_arr')
                            published_instance = grade_view.create_published_instance(
                                sel_examyear=sel_examyear,
                                sel_school=sel_school,
                                sel_department=sel_department,
                                sel_level=sel_level,
                                sel_examtype='ce',
                                sel_examperiod=sel_examperiod,
                                is_test=is_test,
                                ex_form='wolf',
                                now_arr=now_arr,
                                request=request
                            )
                            if published_instance:
                                published_pk = published_instance.pk

                        if logging_on:
                            logger.debug('published_pk: ' + str(published_pk))

# +++++++++++++++++ loop through grade_exam_rows
                        for grade_exam_dict in grade_exam_rows:
                            approve_grade_exam(
                                request=request,
                                grade_exam_dict=grade_exam_dict,
                                requsr_auth=requsr_auth,
                                is_submit=is_submit,
                                is_reset=is_reset,
                                is_test=is_test,
                                count_dict=count_dict,
                                total_dict=total_dict,
                                grade_exams_tobe_updated_list=grade_exams_tobe_updated_list
                            )
# +++++++++++++++++ end of loop through grade_exam_rows

                    if logging_on:
                        logger.debug('grade_exams_tobe_updated_list: ' + str(grade_exams_tobe_updated_list))

# when is_submit: check if all grade_exams of each ete_exam are ok - if not: skip submit grade_exams
                    tobe_submitted_ete_exams = []
                    if is_submit:
                        if logging_on:
                            logger.debug('............ count_dict: ' + str(count_dict))
                            logger.debug('............ total_dict: ' + str(total_dict))
                        """
                        count_dict: {
                            51: {'exam_id': 51, 'exam_name': 'Engelse taal - TKL', 'count': 31, 'has_blanks': 31}, 
                            49: {'exam_id': 49, 'exam_name': 'Engelse taal - PBL', 'count': 33, 'has_blanks': 30, 'committed': 3}, 
                            'total_ok': 3}
                        count_dict: {
                            272: {'exam_id': 272, 'exam_name': 'Administratie & Commercie - PBL - Versie BLAUW', 'count': 1, 'saved': 1}, 
                            282: {'exam_id': 282, 'exam_name': 'Administratie & Commercie - PBL - Versie ROOD', 'count': 1, 'saved': 1}, 
                            294: {'exam_id': 294, 'exam_name': 'Zorg & Welzijn intrasectoraal - PBL - Versie ROOD', 'count': 10, 'has_blanks': 10},
                            274: {'exam_id': 274, 'exam_name': 'Zorg & Welzijn intrasectoraal - PBL - Versie BLAUW', 'count': 10, 'has_blanks': 10}}

                        """
                        for exam_dict in count_dict.values():
                            # exam_dict has key 'total_ok' that is an integer
                            if isinstance(exam_dict, dict):
                                exam_id = exam_dict.get('exam_id')
                                count = exam_dict.get('count', 0) or 0
                                committed = exam_dict.get('committed', 0) or 0
                                tobesaved = exam_dict.get('tobesaved', 0) or 0
                                already_submitted = exam_dict.get('already_submitted', 0) or 0
                                not_fully_approved = exam_dict.get('not_fully_approved', 0) or 0

                                is_tobe_submitted = False
                                if is_test:
                                    if committed and committed + already_submitted == count:
                                        is_tobe_submitted = True
                                else:
                                    if tobesaved and tobesaved + already_submitted == count:
                                        is_tobe_submitted = True

                                if is_tobe_submitted:
                                    if exam_id and exam_dict not in tobe_submitted_ete_exams:
                                        tobe_submitted_ete_exams.append(exam_id)
                                        exam_dict['tobe_submitted'] = True
                                        has_tobesubmitted_eteexams = True

                                if logging_on:
                                    logger.debug('  >> exam_dict: ' + str(exam_dict))
                                    logger.debug('     count: ' + str(count))
                                    logger.debug('     committed: ' + str(committed))
                                    logger.debug('     tobesaved: ' + str(tobesaved))
                                    logger.debug('     already_submitted: ' + str(already_submitted))
                                    logger.debug('     not_fully_approved: ' + str(not_fully_approved))
                                    logger.debug('     is_tobe_submitted: ' + str(is_tobe_submitted))
                                    logger.debug('     has_tobesubmitted_eteexams: ' + str(has_tobesubmitted_eteexams))

                        if logging_on:
                            logger.debug('............ tobe_submitted_ete_exams: ' + str(tobe_submitted_ete_exams))
                            """
                            tobe_submitted_ete_exams: [49]
                            """

                    has_error = False
                    updated_grade_pk_list = []

                    if logging_on:
                        logger.debug('    grade_exams_tobe_updated_list: ' + str(grade_exams_tobe_updated_list))

                    if not is_test and grade_exams_tobe_updated_list:
    #  - approve grade_exams
                        if not is_submit:
                            err_html, updated_grade_pk_list = batch_approve_grade_exam_rows(
                                request=request,
                                requsr_auth=requsr_auth,
                                is_reset=is_reset,
                                grade_exams_tobe_updated_list=grade_exams_tobe_updated_list
                            )
                            if err_html:
                                has_error = True
                            else:
                                saved_is_ok = True
    #  - submit grade_exams
                        elif is_submit:
                            # PR2022-06-07 DON'T copy Wolf scores to grade score !!!
                            err_html, updated_grade_pk_list = batch_submit_grade_exam_rows(
                               req_usr=req_usr,
                               is_reset=is_reset,
                                published_pk=published_pk,
                                grade_exams_tobe_updated_list=grade_exams_tobe_updated_list,
                                tobe_submitted_ete_exams=tobe_submitted_ete_exams
                            )
                            if err_html:
                                has_error = True
                            else:
                                saved_is_ok = True

                    if not is_test:
                        # PR2023-05-26 debug: alway add sel_grade_pk when approving single exam,
                        # to return rows if it is not updates because of error
                        err_field = None
                        if sel_grade_pk and sel_grade_pk not in updated_grade_pk_list:
                            err_field = 'status'
                            updated_grade_pk_list.append(sel_grade_pk)

                        if logging_on:
                            logger.debug('    sel_grade_pk: ' + str(sel_grade_pk))
                            logger.debug('    updated_grade_pk_list: ' + str(updated_grade_pk_list))

                        if updated_grade_pk_list:
                            rows = grade_view.create_grade_with_exam_rows(
                                sel_examyear=sel_examyear,
                                sel_schoolbase=sel_school.base if sel_school else None,
                                sel_depbase=sel_department.base if sel_department else None,
                                sel_lvlbase=sel_level.base if sel_level else None,
                                sel_examperiod=sel_examperiod,
                                ete_exams_only=False,
                                request=request,
                                grade_pk_list=updated_grade_pk_list
                            )

                            if rows:
                                # add err_field when approning single has error - better use append_dict, but let is stay for now
                                if is_single_approve and err_field:
                                    row = rows[0]
                                    if row:
                                        if logging_on:
                                            logger.debug('    row: ' + str(row))
                                        if 'err_fields' not in row:
                                            row['err_fields'] = []
                                        row['err_fields'].append(err_field)

                                update_wrap['updated_grade_rows'] = rows

    # first get total_ok from count_dict and delete key before sorting
                    total_ok = 0
                    if 'total_ok' in count_dict:
                        total_ok = count_dict.pop('total_ok')

                    if has_error:
                        update_wrap['error'] = True

                    update_wrap['total'] = total_dict


    # convert dict to sorted dictlist
                    count_list = list(count_dict.values())
                    # count_list: [{'exam_id': 49, 'exam_name': 'Engelse taal - PBL', 'count': 3, 'committed': 3, 'tobe_submitted': True ]

    # sort list to sorted dictlist
                    # PR2021-11-15 from https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
                    count_dictlist_sorted = sorted(count_list, key=lambda d: d['exam_name'])

                    if logging_on:
                        logger.debug('count_dictlist_sorted: ' + str(count_dictlist_sorted))

    # - create approve_msg_html with info of rows
                    if not is_single_approve:
                        approve_msg_html = create_grade_exam_approve_submit_msg_list(
                            req_usr=req_usr,
                            requsr_auth=requsr_auth,
                            count_list=count_dictlist_sorted,
                            is_submit=is_submit,
                            is_test=is_test,
                            is_reset=is_reset,
                            has_error=has_error,
                            err_html=err_html
                        )
                    else:
                        approve_msg_html = create_grade_exam_single_approve_msg_list(
                            req_usr=req_usr,
                            requsr_auth=requsr_auth,
                            count_list=count_dictlist_sorted,
                            is_submit=is_submit,
                            is_test=is_test,
                            is_reset=is_reset,
                            has_error=has_error,
                            err_html=err_html
                        )

                    if total_ok:
                        if is_test:
                            if is_submit:
                                test_is_ok = has_tobesubmitted_eteexams
                            else:
                               test_is_ok = True

                    if logging_on:
                        logger.debug('    total_ok: ' + str(total_ok))
                        logger.debug('    is_test: ' + str(is_test))
                        logger.debug('    is_submit: ' + str(is_submit))
                        logger.debug('    has_tobesubmitted_eteexams: ' + str(has_tobesubmitted_eteexams))
                        logger.debug('    test_is_ok: ' + str(test_is_ok))

        if test_is_ok:
            update_wrap['test_is_ok'] = True
        if saved_is_ok:
            update_wrap['saved_is_ok'] = True

        update_wrap['has_tobesubmitted_eteexams'] = has_tobesubmitted_eteexams

        if logging_on:
            logger.debug('    msg_list: ' + str(msg_list))

        if border_class:
            update_wrap['border_class'] = border_class

# - add  msg_html to update_wrap
        if approve_msg_html:
            if is_single_approve:
            # msg_list messages are shown in mod_message, when there is a single approve
                update_wrap['msg_html'] = acc_prm.msghtml_from_msglist_with_border([approve_msg_html], border_class)
            else:
        # approve_msg_html messages are shown in form mod_approve
                update_wrap['approve_msg_html'] = acc_prm.msghtml_from_msglist_with_border([approve_msg_html], border_class)

        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamApproveOrSubmitWolfView


def batch_approve_grade_exam_rows(request, requsr_auth, is_reset, grade_exams_tobe_updated_list):
    #PR2020-04-25 PR2023-05-16
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- batch_approve_grade_exam_rows -----')
        logger.debug('    grade_exams_tobe_updated_list:    ' + str(grade_exams_tobe_updated_list))
        logger.debug('    requsr_auth:    ' + str(requsr_auth))
        logger.debug('    is_reset:    ' + str(is_reset))
        # grade_exams_tobe_updated_list: [[22961, 146], [21701, 146], [22980, 146]]

    # grade_exams_tobe_updated_list contains list of tuples with (grade_pk, exam_pk)
    grade_exam_pk_tobe_updated = []
    if grade_exams_tobe_updated_list:
        for row in grade_exams_tobe_updated_list:
            grade_exam_pk_tobe_updated.append(row[0])

    updated_grade_exam_pk_list = []
    err_html = None

    if grade_exam_pk_tobe_updated and requsr_auth and request.user:
        # sql_keys = {'ey_id': school.examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}

        # dont update modified field when approving.

        # grade_exam_pk_tobe_updated: [22961, 21701, 22980, ...]

        try:
            new_auth_id = 'NULL' if is_reset else str(request.user.pk)
            auth_field = ''.join(("ce_exam_", requsr_auth, 'by_id'))

            sql = ''.join((
                "UPDATE students_grade",
                " SET ", auth_field, "=", new_auth_id,
                " WHERE id IN (SELECT UNNEST(ARRAY", str(grade_exam_pk_tobe_updated), "::INT[]))",
                " RETURNING id, studentsubject_id;"
            ))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()

                for row in rows:
                    updated_grade_exam_pk_list.append(row[0])
                    if logging_on:
                        logger.debug('............. row: ' + str(row))
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            err_txt = _('No approvals have been removed.') if is_reset else _('No exams have been approved.')
            err_html = acc_prm.errhtml_error_occurred_no_border(e, err_txt)

    if logging_on:
        logger.debug('updated_grade_exam_pk_list:' + str(updated_grade_exam_pk_list))

    return err_html, updated_grade_exam_pk_list
# - end of batch_approve_grade_exam_rows


def batch_submit_grade_exam_rows(req_usr, published_pk, is_reset, grade_exams_tobe_updated_list, tobe_submitted_ete_exams):
    #PR2020-05-06 PR2023-05-16
    # GOES WRONG WHEN SCHOOL HAVE ENTERED ce-grades already:
    # PR2022-06-07 >>>>>> DON'T copy Wolf scores to grade score !!! <<<<<<<<

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- batch_submit_grade_exam_rows -----')
        logger.debug('    grade_exams_tobe_updated_list:    ' + str(grade_exams_tobe_updated_list))
        logger.debug('    tobe_submitted_ete_exams:    ' + str(tobe_submitted_ete_exams))

        # grade_exams_tobe_updated_list: [[22961, 146], [21701, 146], [22980, 146]]


    # grade_exams_tobe_updated_list contains list of tuples with (grade_pk, exam_pk)
    # skip garde_exams when exam_pk not in tobe_submitted_ete_exams

    grade_exams_tobe_updated = []
    if grade_exams_tobe_updated_list:
        for row in grade_exams_tobe_updated_list:
            if row[1] in tobe_submitted_ete_exams:
                grade_exams_tobe_updated.append(row[0])

    if logging_on:
        logger.debug(' ----- batch_submit_grade_exam_rows -----')
        logger.debug('    grade_exams_tobe_updated:    ' + str(grade_exams_tobe_updated))
    updated_grade_exam_pk_list = []

    # tobe_submitted_ete_exams: [[22961, 146], [21701, 146], [22980, 146]]
    # grade_exams_tobe_updated_list: [[22961, 146], [21701, 146], [22980, 146]]
    err_html = None
    try:
        published_pk_str = 'NULL' if is_reset else str(published_pk)

        # TODO make separate sql for copying score to ce_score, filter out the (partially) approved scores
        # solve by removing approved, filter out published
        """
        ce_status = 
        ce_auth1by_id = NULL, ce_auth2by_id = NULL, ce_auth3by_id = NULL, ce_auth4by_id = NULL
        ce_published_id =
        ce_blocked = 
        """

        sql = ''.join((
            "UPDATE students_grade",
            " SET ce_exam_published_id=", published_pk_str, "::INT",
            " WHERE id IN (SELECT UNNEST(ARRAY", str(grade_exams_tobe_updated), "::INT[]))",
            " RETURNING id, studentsubject_id;"
        ))

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

            for row in rows:
                updated_grade_exam_pk_list.append(row[0])
                if logging_on:
                    logger.debug('............. row: ' + str(row))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        err_txt = _('No submissions have been removed.') if is_reset else _('No exams have been submitted.')
        err_html = acc_prm.errhtml_error_occurred_no_border(e, err_txt)

    if logging_on:
        logger.debug('updated_grade_exam_pk_list:' + str(updated_grade_exam_pk_list))
    return err_html, updated_grade_exam_pk_list
# - end of batch_submit_grade_exam_rows


def create_exam_approve_publish_msg_list(req_usr, count_dict, requsr_auth, is_approve, is_test, is_grade_exam=False):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  ----- create_exam_approve_publish_msg_list -----')
        logger.debug('count_dict: ' + str(count_dict))
        logger.debug('is_test: ' + str(is_test))

    exam_count = count_dict.get('count', 0)
    committed = count_dict.get('committed', 0)
    saved = count_dict.get('saved', 0)
    saved_error = count_dict.get('saved_error', 0)
    already_published = count_dict.get('already_published', 0)
    has_blanks = count_dict.get('has_blanks', 0)
    auth_missing = count_dict.get('auth_missing', 0)
    already_approved = count_dict.get('already_approved', 0)
    double_approved = count_dict.get('double_approved', 0)

    if logging_on:
        logger.debug('.....exam_count: ' + str(exam_count))
        logger.debug('.....committed: ' + str(committed))
        logger.debug('.....already_published: ' + str(already_published))
        logger.debug('.....auth_missing: ' + str(auth_missing))
        logger.debug('.....already_approved: ' + str(already_approved))
        logger.debug('.....double_approved: ' + str(double_approved))

# -  get user_lang
    user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
    activate(user_lang)

    show_warning_msg = False
    show_msg_first_approve_by_pres_secr = False
    if is_test:
        if is_approve:
            class_str = 'border_bg_valid' if committed else 'border_bg_invalid'
        else:
            if committed:
                if (is_test and auth_missing) or (is_test and double_approved):
                    class_str = 'border_bg_warning'
                else:
                    class_str = 'border_bg_valid'
            else:
                class_str = 'border_bg_invalid'
    else:
        if saved_error:
            class_str = 'border_bg_invalid'
        elif saved:
            class_str = 'border_bg_valid'
        else:
            class_str = 'border_bg_transparent'

# - create first line with 'The selection contains 4 exams'
    msg_list = ["<div class='p-2 ", class_str, "'>"]
    if is_test:
        msg_list.append(''.join(("<p class='pb-2'>",
                                 str(_("The selection contains %(val)s.") % {'val': get_exam_count_text(exam_count)}),
                                 '</p>')))

# - if any exams skipped: create lines 'The following exams will be skipped' plus the reason
    if is_test and committed < exam_count:
        msg_list.append("<p class='pb-0'>" + str(_("The following exams %(willbe)s skipped")
                                                 % {'willbe': get_willbe_or_are_txt(is_test, exam_count)}) + ':</p><ul>')
        if already_published:
            msg_list.append('<li>' + str(_("%(val)s already published") %
                                             {'val': get_exams_are_text(already_published)}) + ';</li>')
        if has_blanks:
            msg_list.append('<li>' + str(_("%(val)s blank questions") %
                                         {'val': get_exams_have_text(has_blanks)}) + ';</li>')
        if auth_missing:
            msg_list.append('<li>' + str(_("%(val)s not fully approved") %
                                         {'val': get_exams_are_text(auth_missing)}) + ';</li>')
            show_msg_first_approve_by_pres_secr = True
        if already_approved:
            msg_list.append('<li>' + get_exams_are_text(already_approved) + str(
                _(' already approved')) + ';</li>')
        if double_approved:
            other_function = str(_('chairperson')) if requsr_auth == 'auth2' else str(_('secretary'))
            msg_list.append(''.join(('<li>', get_exams_are_text(double_approved),
                                     str(_(' already approved by you as ')), other_function, '.<br>',
                                     str(_("You cannot approve an exam both as chairperson and as secretary.")),
                                     '</li>')))
        msg_list.append('</ul>')

# - line with text how many exams will be approved / submitted
    msg_list.append('<p>')
    if is_test:
        if is_approve:
            if not committed:
                msg_str = _("No exams will be approved.")
            else:
                msg_str = ' '.join((
                    get_exam_count_text(committed),
                    get_will_be_text(committed),
                    gettext('approved') + '.'
                ))
        else:
            if not committed:
                if is_approve:
                    msg_str = _("No exams will be published.")
                else:
                    msg_str = _("The exams cannot be published.")
            else:
                approve_txt = (gettext('approved') if is_approve else gettext('published')) + '.'
                msg_str = ' '.join((
                    get_exam_count_text(committed).capitalize(),
                    get_will_be_text(committed), approve_txt))
    else:
        subject_error_count_txt = get_exams_are_text(saved_error)

        # - line with text how many exams have been approved / submitted
        if is_approve:
            not_str = '' if saved else str(_('not')) + ' '
            msg_str = ''
            if not saved and not saved_error:
                msg_str = str(_("No exams have been approved."))
            else:
                if saved:
                    msg_str = str(_("%(exams)s %(havehasbeen)s approved.")
                                  % {'exams': get_exam_count_text(saved),
                                     'havehasbeen': get_have_has_been_txt(saved)})
                else:
                    msg_str = str(_("No exams have been approved."))
                if saved_error:
                    if msg_str:
                        msg_str += '<br>'
                    msg_str += str(
                        _("%(subj)s %(could)s not be approved because an error occurred.")
                        % {'subj': subject_error_count_txt, 'could': get_could_txt(saved_error)})

        else:
            not_str = '' if saved else str(_('not')) + ' '
            msg_str = str(_("The exams have %(not)s been published.") % {'not': not_str})
            if saved:
                msg_str += '<br>' + str(_("It contains %(exam)s.") % {'exam': get_exam_count_text(saved)})
    msg_list.append(str(msg_str))
    msg_list.append('</p>')

    # - warning if any exams are not fully approved
    if show_warning_msg and not is_approve:
        msg_list.append("<p class='pt-2'><b>")
        msg_list.append(str(_('WARNING')))
        msg_list.append(':</b> ')
        msg_list.append(str(_('There are exams that are not fully approved.')))
        msg_list.append(' ')

        msg_list.append(str(_('They will not be published.')))

        msg_list.append(' ')
        msg_list.append(str(_('Are you sure you want to continue?')))
        msg_list.append('</p>')

    # - add line 'both chairperson and secretary must first approve all exams before you can submit the Ex form
    if show_msg_first_approve_by_pres_secr:
        msg_txt = ''.join(('<p>', str(_(
            'The chairperson and the secretary must approve the exams before you can publish them.')),
                           '</p>'))

# - line with text how many  subjects of stuidents have been linked to exams
    if not is_test and not is_approve:
        if count_dict['updated_grd_count']:
            if count_dict['updated_grd_count'] == 1:
                msg_str = _("The exam has been linked to 1 subject of a candidate.")
            else:
                msg_str = _("The exams have been linked to %(count)s subjects of candidates.") % {'count': count_dict['updated_grd_count']}
            msg_txt = ''.join(('<p>', str(msg_str), '</p>'))
            msg_list.append(msg_txt)

    msg_list.append('</div>')

    msg_html = ''.join(msg_list)
    return msg_html
# - end of create_exam_approve_publish_msg_list


def create_grade_exam_approve_submit_msg_list(req_usr, requsr_auth, count_list,
                                              is_submit, is_test, is_reset, has_error, err_html):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('  ----- create_grade_exam_approve_submit_msg_list -----')
        logger.debug('     count_list: ' + str(count_list))
        logger.debug('     is_test: ' + str(is_test))
        logger.debug('     is_reset: ' + str(is_reset))
        logger.debug('     has_error: ' + str(has_error))
        logger.debug('     err_html: ' + str(err_html))
        """
        count_list: [
        {'exam_id': 49, 'exam_name': 'Engelse taal - PBL', 
        'count': 33, 'has_blanks': 30, 
        'saved': 1, 
        'already_approved': 2}, 
        {'exam_id': 51, 'exam_name': 'Engelse taal - TKL', 
        'count': 31, 'has_blanks': 31}]
    
        count_list: [
            {'exam_id': 54, 'exam_name': 'Spaanse taal - TKL', 'count': 46, 'already_submitted': 46}, 
            {'exam_id': 46, 'exam_name': 'Papiamentu - PBL', 'count': 30, 'already_submitted': 30}, 
            {'exam_id': 39, 'exam_name': 'Mens en maatschappij 2 - PKL', 'count': 27, 'already_submitted': 27}, 
            {'exam_id': 50, 'exam_name': 'Engelse taal - PKL', 'count': 39, 'already_submitted': 39}, 
            {'exam_id': 36, 'exam_name': 'Economie - PBL', 'count': 13, 'already_submitted': 13}, 
            {'exam_id': 51, 'exam_name': 'Engelse taal - TKL', 'count': 46, 'already_submitted': 46}, 
            {'exam_id': 37, 'exam_name': 'Economie - PKL', 'count': 12, 'already_submitted': 12}, 
            {'exam_id': 75, 'exam_name': 'Wiskunde - PBL', 'count': 13, 'already_submitted': 13}, 
            {'exam_id': 48, 'exam_name': 'Papiamentu - TKL', 'count': 46, 'already_submitted': 46}, 
    
        """

# -  get user_lang
    user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
    activate(user_lang)

    msg_list = []
    exam_name_list = []

    requsr_function = c.USERGROUP_CAPTION.get(requsr_auth) or '-'

# - get totals
    total_exam_count = len(count_list)

    # total_grade_exam_count = 0
    # for count_dict in count_list:
    #    total_grade_exam_count += count_dict.get('count', 0) or 0

    msg_list.append(''.join(("<p class='pb-0'>",
        str(_("The selection contains %(count)s") % {'count': get_exam_count_text(total_exam_count)}),
        ':</p>' if total_exam_count else '.</p>')))

# +++ loop through exams
    if count_list:
        for count_dict in count_list:
            msg_list.append("<div class='mx-2 mt-0 p-0'>")

        # write examname in bold letters
            exam_name = count_dict.get('exam_name', '-') or '-'
            msg_list.append("<b>" + exam_name + "</b>")
            msg_list.append("<div class='mx-2 mt-0 p-0'>")

# +++ if is test
            if is_test:
    # count candidates
                # grade_exam_count cannot be zero because of INNER JOIN ce_exam exam_id
                grade_exam_count = count_dict.get('count') or 0
                already_submitted_count = count_dict.get('already_submitted') or 0

                if grade_exam_count and grade_exam_count == already_submitted_count:
                    msg_list.append(''.join(("<div class='pl-2'>", str(_("This exam is already submitted.")), '</div>')))

                else:
                    msg_list.append(''.join(("<div class='pl-2'>",
                                             str(_("There %(is_are)s %(count)s with this exam.") % {
                                                 'is_are' : get_is_are_txt(grade_exam_count),
                                                 'count': get_candidates_count_text(grade_exam_count)}),
                                             '</div>')))

        # count exams with blanks - should not be possible
                    no_questions_count = count_dict.get('no_questions')
                    blank_questions_count = count_dict.get('blank_questions')
                    if no_questions_count or blank_questions_count :
                        blank_no = str(pgettext_lazy('geen', 'no') if no_questions_count else _('blank'))
                        msg_list.append(' '.join(("<div class='pl-2 border_bg_invalid'>",
                                                str(_('This exam has errors.')),
                                                str(_('Please contact the Division of Examinations.')), '</div>')))
                    else:

        # count grade_exam is already submitted
                        already_published_count = count_dict.get('already_published')
                        if already_published_count:
                            msg_list.append(''.join(("<div class='pl-2'>",
                                                     str(_("%(count)s %(is_are)s already submitted.") % {
                                                         'is_are': get_is_are_txt(already_published_count),
                                                         'count': get_exam_count_text(already_published_count)}),
                                                     '</div>')))

        # count exams with blanks
                        grade_blanks_count = count_dict.get('has_blanks')
                        if grade_blanks_count:
                            msg_list.append(''.join(("<div class='pl-2'>",
                                                     str(_("%(count)s %(has_have)s blank questions.") % {
                                                         'has_have': get_has_have_txt(grade_blanks_count),
                                                         'count': get_exam_count_text(grade_blanks_count)}),
                                                     '</div>')))

                        not_fully_approved_count = count_dict.get('not_fully_approved')
                        if logging_on:
                            logger.debug('  >>>>>>>   count_dict: ' + str(count_dict))
                            logger.debug('     not_fully_approved_count: ' + str(not_fully_approved_count))

                        if not_fully_approved_count:
                            msg_list.append(''.join(("<div class='pl-2'>",
                                                     str(_("%(count)s %(is_are)s not fully approved.") % {
                                                         'is_are': get_is_are_txt(not_fully_approved_count),
                                                         'count': get_exam_count_text(not_fully_approved_count)}),
                                                     '</div>')))



        # count exams double_approved
                        grade_double_approved_count = count_dict.get('double_approved')
                        if grade_double_approved_count:
                            msg_list.append(''.join(("<div class='pl-2'>",
                                                     str(_("%(count)s %(is_are)s already approved by you in a different function.") % {
                                                     'is_are' : get_is_are_txt(grade_double_approved_count),
                                                         'count': get_exam_count_text(grade_double_approved_count)}),
                                                     '</div>')))
        # count exams already_approved
                        grade_already_approved_count = count_dict.get('already_approved')
                        if grade_already_approved_count:
                            msg_list.append(''.join(("<div class='pl-2'>",
                                                     str(_("%(count)s %(is_are)s already approved by the %(auth)s.") % {
                                                     'is_are' : get_is_are_txt(grade_already_approved_count),
                                                         'count': get_exam_count_text(grade_already_approved_count),
                                                         'auth': requsr_function.lower()
                                                     }),
                                                     '</div>')))
        # count exams already_approved by different_user (only when reset, also when single_approve)
                        approved_by_diff_user_count = count_dict.get('approved_by_diff_user')
                        if logging_on:
                            logger.debug('     approved_by_diff_user_count: ' + str(approved_by_diff_user_count))

                        if approved_by_diff_user_count:

                            auth = str(c.MAILBOX_USERGROUPS[requsr_auth])

                            msg_list.append(''.join(("<div class='pl-2'>",
                                                     str(_("%(count)s %(is_are)s approved by a different %(auth)s.") % {
                                                     'is_are' : get_is_are_txt(approved_by_diff_user_count),
                                                         'count': get_exam_count_text(approved_by_diff_user_count),
                                                         'auth': auth.lower()
                                                     }),
                                                     "<br>",
                                                     gettext("Only the %(auth)s who has approved %(cpt)s can remove this approval."),
                                                     '</div>')
                                                    ))

                        if logging_on:
                            logger.debug('     msg_list: ' + str(msg_list))

        # count committed exams
                        if not is_submit:
                            grade_committed_count = count_dict.get('committed')
                            if grade_committed_count:
                                will_be_approved_txt = str(_("%(count)s %(will_be)s approved by the %(auth)s.") % {
                                                     'will_be' : get_will_be_text(grade_committed_count),
                                                         'count': get_exam_count_text(grade_committed_count),
                                                         'auth': requsr_function.lower()})
                                msg_list.append(''.join(("<div class='pl-2 border_bg_valid'>", will_be_approved_txt, '</div>')))
                            else:
                                msg_list.append(''.join(("<div class='pl-2'>",
                                                         gettext('No approvals will be removed.' if is_reset else 'No exams will be approved.'),
                                                         '</div>')))
                        else:
                            tobe_submitted = count_dict.get('tobe_submitted', False) or False
                            will_be_txt = pgettext_lazy('singular', 'will be') if tobe_submitted else pgettext_lazy('singular', 'will not be')
                            will_be_submitted_txt = str(_('This exam %(will_be)s submitted.') % {'will_be': str(will_be_txt)})
                            border_class = 'border_bg_valid' if tobe_submitted else ''
                            msg_list.append(''.join(("<div class='pl-2 ", border_class, "'>", will_be_submitted_txt, '</div>')))

    # +++ if is not a test
            else:
                if not is_submit:
                    grade_saved_count = count_dict.get('saved')
                    # Note: after approving, a message is only displayed when there is an error. De modal closes otherwise
                    if grade_saved_count:
                        if has_error:
                            none_approved_txt = gettext('No approvals have been removed.') if is_reset else gettext('No exams have been approved.')
                            has_been_approved_txt = ' '.join((str(_('An error occurred.')), none_approved_txt))
                            msg_list.append(''.join(("<div class='pl-2 border_bg_invalid'>", has_been_approved_txt, '</div>')))
                        else:
                            has_been_approved_txt = str(_("%(count)s %(will_be)s approved by the %(auth)s.") % {
                                'will_be': get_have_has_been_txt(grade_saved_count),
                                'count': get_exam_count_text(grade_saved_count),
                                'auth': requsr_function.lower()})
                            msg_list.append(''.join(("<div class='pl-2 border_bg_valid'>",
                                                     has_been_approved_txt, '</div>')))
                    else:
                        msg_list.append(''.join(("<div class='pl-2'>",
                                                 gettext('No approvals have been removed.') if is_reset else gettext(
                                                     'No exams have been approved.')
                                                 , '</div>')))

                else:
                    # Note: after approving, a message is only displayed when there is an error. De modal closes otherwise
                    is_submitted = count_dict.get('saved', False) or False
                    if is_submitted:
                        if has_error:
                            err_txt = str(_('An error occurred.'))
                            has_been_submitted_txt = str(_("This exam %(has_been)s submitted.") % {'has_been': str(_('has not been'))})
                            msg_list.append(''.join(("<div class='pl-2 border_bg_invalid'>", err_txt, ' ', has_been_submitted_txt, '</div>')))
                        else:
                            has_been_submitted_txt = str(_("This exam %(has_been)s submitted.") % {'has_been': str(_('has been'))})
                            # copied_txt = str(_('The scores have been copied to the CE score.'))
                            msg_list.append(' '.join(("<div class='pl-2 border_bg_valid'>", has_been_submitted_txt, '</div>')))
                    else:
                        has_been_submitted_txt = str(_("This exam %(has_been)s submitted.") % {'has_been': str(_('has not been'))})
                        msg_list.append(''.join(("<div class='pl-2'>", has_been_submitted_txt, '</div>')))

            msg_list.append("</div>")
            msg_list.append("</div>")
# +++ end of loop through exams

    if total_exam_count:
        msg_list.append('<ul>')
        for exam_name in exam_name_list:
            msg_list.append('<li>' + exam_name + '</li>')
            msg_list.append(''.join(("<p class='pl-5'>",
                                 str(_("The selection contains %(count)s") % {
                                     'count': get_candidates_count_text(len(exam_name_list))}),
                                 ':</p>' if total_exam_count else '.</p>')))

        msg_list.append("</ul>")

    if err_html:
        msg_list.append(acc_prm.msghtml_from_msglist_with_border(err_html, c.HTMLCLASS_border_bg_invalid))

    class_str = 'border_bg_transparent'
    msg_list.insert(0, "<div class='p-2 " + class_str + "'>")
    msg_list.append("</div>")

    msg_html = ''.join(msg_list)

    return msg_html
# - end of create_grade_exam_approve_submit_msg_list

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def create_grade_exam_single_approve_msg_list(req_usr, requsr_auth, count_list,
                                              is_submit, is_test, is_reset, has_error, err_html):
    # PR203-05-26 creates msg_html for mod_message when aaproving / resetting single exam
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  ----- create_grade_exam_single_approve_msg_list -----')
        logger.debug('     count_list: ' + str(count_list))

    # -  get user_lang
    #user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
    #activate(user_lang)

    msg_list = []

    # +++ loop through exams - tehre is only 1
    if count_list:
        count_dict = count_list[0]
        requsr_function = c.USERGROUP_CAPTION.get(requsr_auth) or '-'

        # +++ if is test -- there is no test mode in sinlge approve

        this_exam_txt = _('This exam')

        if count_dict.get('already_submitted'):
            msg_list.append(
                ''.join(("<div class='pl-2'>", str(_("This exam is already submitted.")), '</div>')))
        else:
            # count exams with blanks - should not be possible
            if count_dict.get('no_questions') or count_dict.get('blank_questions'):
                msg_list.append(' '.join(("<div class='pl-2 border_bg_invalid'>",
                                          str(_('This exam has errors.')),
                                          str(_('Please contact the Division of Examinations.')), '</div>')))
            else:
                # count grade_exam is already submitted
                already_published_count = count_dict.get('already_published')
                if already_published_count:
                    msg_list.append(''.join(("<div class='pl-2'>",
                                             str(_("%(count)s %(is_are)s already submitted.") % {
                                                 'is_are': _('is'),
                                                 'count': this_exam_txt}),
                                             '</div>')))

                if logging_on:
                    logger.debug('     already_published_count: ' + str(already_published_count))

                # count exams with blanks
                grade_blanks_count = count_dict.get('has_blanks')
                if grade_blanks_count:
                    msg_list.append(''.join(("<div class='pl-2'>",
                                             str(_("%(count)s %(has_have)s blank questions.") % {
                                                 'has_have': _('has'),
                                                 'count': this_exam_txt}),
                                             '</div>')))

                if logging_on:
                    logger.debug('     grade_blanks_count: ' + str(grade_blanks_count))

        # count exams double_approved
                if count_dict.get('double_approved'):
                    msg_list.append(''.join(("<div class='pl-2'>",
                                             str(_(
                                                 "%(count)s %(is_are)s already approved by you in a different function.") % {
                                                     'is_are': _('is'),
                                                     'count': this_exam_txt}),
                                             '</div>')))

                # count exams already_approved by different_user (only when reset, also when single_approve)
                if count_dict.get('approved_by_diff_user'):
                    msg_list.extend((
                        "<div class='pl-2'>",
                        str(_("%(count)s %(is_are)s approved by a different %(auth)s.")
                            % {'is_are': _('is'), 'count': this_exam_txt, 'auth': requsr_function.lower()}),
                       "<br>",
                        str(_("Only the %(auth)s who has approved %(cpt)s can remove this approval.")
                            % {'auth': requsr_function.lower(), 'cpt': this_exam_txt.lower()}),
                       '</div>'
                    ))

                if logging_on:
                    logger.debug('     msg_list: ' + str(msg_list))

    # +++ end of loop through exams

    class_str = 'border_bg_invalid'
    if msg_list:
        msg_list.insert(0, "<div class='p-2 " + class_str + "'>")
        msg_list.append("</div>")

    msg_html = ''.join(msg_list)

    return msg_html
# - end of create_grade_exam_single_approve_msg_list


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def approve_exam(exam, requsr_auth, is_test, is_reset, count_dict, updated_exam_pk_list, request):
    # PR2022-01-31
    # auth_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- approve_exam -----')
        logger.debug('requsr_auth:  ' + str(requsr_auth))
        logger.debug('is_reset:     ' + str(is_reset))

    if exam:
        req_usr = request.user

        count_dict['count'] += 1

# - skip if this studsubj is already published
        is_published = True if getattr(exam, 'published') else False
        if logging_on:
            logger.debug('published:    ' + str(is_published))

        if is_published:
            count_dict['already_published'] += 1
        else:
            no_questions = False if getattr(exam, 'amount') else True
            has_blank_questions = True if getattr(exam, 'blanks') else False
            # dont skip this when is_reset
            if not is_reset and (no_questions or has_blank_questions):
                count_dict['has_blanks'] += 1
            else:
                requsr_authby_field = requsr_auth + 'by'
                requsr_authby_value = getattr(exam, requsr_authby_field)

    # - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved
                auth1by = getattr(exam, 'auth1by')
                auth2by = getattr(exam, 'auth2by')
                if logging_on:
                    logger.debug('requsr_authby_field: ' + str(requsr_authby_field))
                    logger.debug('auth1by:      ' + str(auth1by))
                    logger.debug('auth2by:      ' + str(auth2by))

                save_changes = False


    # - remove authby when is_reset
                if is_reset:
                    if requsr_authby_value:
                        setattr(exam, requsr_authby_field, None)
                        count_dict['reset'] += 1
                        save_changes = True
                        if exam.pk not in updated_exam_pk_list:
                            updated_exam_pk_list.append(exam.pk)
                else:

    # - skip if this exam is already approved
                    if requsr_authby_value:
                        count_dict['already_approved'] += 1
                    else:

    # - skip if this author (like 'chairperson') has already approved this studsubj
            # under a different permit (like 'secretary' or 'corrector')

                        double_approved = False
                        if requsr_auth == 'auth1':
                            double_approved = True if auth2by and auth2by == req_usr else False
                        elif requsr_auth == 'auth2':
                            double_approved = True if auth1by and auth1by == req_usr else False

                        if double_approved:
                            count_dict['double_approved'] += 1
                        else:
                            setattr(exam, requsr_authby_field, req_usr)

                            save_changes = True
                            if logging_on:
                                logger.debug('save_changes: ' + str(save_changes))

                        if logging_on:
                            logger.debug('     double_approved:     ' + str(double_approved))
                            logger.debug('     requsr_authby_value: ' + str(requsr_authby_value))
                            logger.debug('     auth1by:             ' + str(auth1by))
                            logger.debug('     auth2by:             ' + str(auth2by))

    # - set value of requsr_authby_field
                if save_changes:
                    if exam.pk not in updated_exam_pk_list:
                        updated_exam_pk_list.append(exam.pk)

                    if is_test:
                        count_dict['committed'] += 1
                    else:
    # - save changes
                        try:
                            exam.save(request=request)
                            count_dict['saved'] += 1
                        except Exception as e:
                            logger.error(getattr(e, 'message', str(e)))
                            count_dict['saved_error'] += 1

    if logging_on:
        logger.debug('count_dict: ' + str(count_dict))
# - end of approve_exam


# def get_approve_grade_exam_rows(examyear, school, department, examperiod, request):  #PR2022-03-11

def get_approve_grade_exam_rows(sel_examyear, sel_school, sel_department, sel_level, sel_examperiod, is_submit, request,
                                  sel_subjbase_pk=None, sel_cluster_pk=None, sel_grade_pk=None):
    # PR2022-04-25 PR2022-06-01 PR2023-04-30 PR2023-05-16 PR2023-05-26
    # not anymore: approving single grade_exam happens in UploadGrade
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('  ---- get_approve_grade_exam_rows -----')
        logger.debug('     sel_examperiod: ' + str(sel_examperiod))
        logger.debug('     sel_subjbase_pk: ' + str(sel_subjbase_pk))
        logger.debug('     sel_cluster_pk: ' + str(sel_cluster_pk))

        logger.debug('     sel_examyear:        ' + str(sel_examyear))
        logger.debug('     sel_school:          ' + str(sel_school.name))
        logger.debug('     sel_department:      ' + str(sel_department.name))
        logger.debug('     sel_level:   ' + str(sel_level))

    # Note: exams must also be assigned to students of SXM. Therefore don't filter on examyer.pk but on examyear.code
    # it doesnt matter here because it doesnt filter on exam

    #PR2023-05-26 debug Radulphus sptl zonder ce is als in list
    # must filter on CE > 0

    grade_exam_rows = []

    try:
        if sel_examyear and sel_school and sel_department and sel_examperiod:
            #sql_keys = {'ey_id': sel_examyear.pk, 'school_id': sel_school.pk, 'dep_id': sel_department.pk, 'experiod': sel_examperiod}
            sql_list = ["SELECT grd.id AS grade_id, grd.examperiod, grd.ce_exam_blanks, grd.ce_exam_result,",
                        "grd.ce_exam_auth1by_id, grd.ce_exam_auth2by_id, grd.ce_exam_auth3by_id,",
                        "grd.ce_exam_published_id, grd.ce_exam_blocked,",

                        "depbase.code AS dep_code, lvlbase.code AS lvl_code,",
                        "ce_exam.id, ce_exam.version AS ceex_exam_version,",
                        "ce_exam.amount, ce_exam.blanks,",
                        "subj.name_nl AS ceex_subj_name_nl, subjbase.code AS ceex_subj_code,",

                        "CONCAT(subj.name_nl,",
                        "CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' - ', lvl.abbrev) END,",
                        "CASE WHEN ce_exam.version IS NULL OR ce_exam.version = '' THEN NULL ELSE CONCAT(' - ', ce_exam.version) END ) AS exam_name",

                        "FROM students_grade AS grd",
                        "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                        "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
                        "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
                        #PR2022-06-01 debug: was INNER JOIN subjects_levelbase, returns no rows in Havo/Vwo
                        "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                        # was: "LEFT JOIN subjects_exam AS ce_exam ON (ce_exam.id = grd.ce_exam_id)",
                        "INNER JOIN subjects_exam AS ce_exam ON (ce_exam.id = grd.ce_exam_id)",

                        "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                        "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                        "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                        "WHERE school.id =", str(sel_school.pk), "::INT AND dep.id =", str(sel_department.pk), "::INT",
                        "AND ey.id =", str(sel_examyear.pk), "::INT",
                        "AND grd.examperiod =", str(sel_examperiod), "::INT",
                        "AND ce_exam.ete_exam",

                        "AND NOT stud.deleted AND NOT stud.tobedeleted",
                        "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted",
                        "AND NOT grd.deleted AND NOT grd.tobedeleted",

                        "AND si.weight_ce > 0"
                        ]

            if sel_grade_pk:
                sql_list.extend(("AND grd.id =", str(sel_grade_pk), "::INT"))

            if sel_subjbase_pk:
                sql_list.extend(("AND subj.base_id =", str(sel_subjbase_pk), "::INT"))

            # PR2023-05-16 debug. don't filter on cluster when submitting exams
            if not is_submit:
                if sel_cluster_pk:
                    sql_list.extend(("AND studsubj.cluster_id =", str(sel_cluster_pk), "::INT"))

    # - get allowed_sections_dict from request
            userallowed_instance = acc_prm.get_userallowed_instance_from_request(request)
            userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)

            sql_clause = acc_prm.get_sqlclause_allowed_v2(
                table='grade',
                sel_schoolbase_pk=sel_school.base.pk if sel_school else None,
                sel_depbase_pk=sel_department.base.pk if sel_department else None,
                sel_lvlbase_pk=sel_level.base.pk if sel_level else None,
                userallowed_sections_dict=userallowed_sections_dict,
                return_false_when_no_allowedsubjects=False
            )
            if sql_clause:
                sql_list.append(sql_clause)

            if logging_on:
                logger.debug('sql_clause: ' + str(sql_clause))

            userallowed_cluster_pk_list=acc_prm.get_userallowed_cluster_pk_list(userallowed_instance)

            # PR2024-05-30 filter on examyear_pk added
            allowed_clusters_of_sel_school = acc_prm.get_allowed_clusters_of_sel_school(
                sel_schoolbase_pk=sel_school.base_id if sel_school else None,
                sel_examyear_pk=sel_school.examyear_id if sel_school else None,
                allowed_cluster_pk_list=userallowed_cluster_pk_list
            )
            sqlclause_allowed_clusters = acc_prm.get_sqlclause_allowed_clusters(
                table="studsubj",
                allowed_clusters_of_sel_school=allowed_clusters_of_sel_school
            )
            if sqlclause_allowed_clusters:
                sql_list.append(sqlclause_allowed_clusters)

            if logging_on:
                logger.debug('sqlclause_allowed_clusters: ' + str(sqlclause_allowed_clusters))

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)
                grade_exam_rows = af.dictfetchall(cursor)

                if logging_on:
                    logger.debug('sql_list: ')
                    for sql_txt in sql_list:
                        logger.debug('  > ' + str(sql_txt))

                    #for conn_query in connection.queries:
                    #    logger.debug('conn_query: ' + str(conn_query))

                if logging_on:
                    logger.debug('grade_exam_rows: ' + str(len(grade_exam_rows)))
                    #for row in grade_exam_rows:
                    #    logger.debug('row: ' + str(row))

                    logger.debug('---------------- ')

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return grade_exam_rows
# end of get_approve_grade_exam_rows


def approve_grade_exam(request, grade_exam_dict, requsr_auth, is_submit, is_reset, is_test,
                       count_dict, total_dict, grade_exams_tobe_updated_list):
    # PR2022-04-25 PR2022-05-06
    # auth_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise

    # PR2023-05-26 msg_list is used for single approve
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('---- approve_grade_exam -----')

    """
    grade_exam_dict: 
        {'grade_id': 22442, 'examperiod': 1, 'ce_exam_blanks': None, 
        'ce_exam_result': '0;26#1|1;2|2;1|3;b|4;a|5;1|6;1|7;1|8;1|9;1|10;1|11;1|12;1|13;a|14;1|15;a|16;1|17;1|18;1|19;1|20;1|21;a|22;a|23;a|24;1|25;1|26;x', 
        'ce_exam_auth1by_id': 719, 'ce_exam_auth2by_id': 498, 
        'ce_exam_published_id': None, 'ce_exam_blocked': False, 
        'dep_code': 'Vsbo', 'lvl_code': 'PBL', 'exam_id': 49, 'ceex_exam_version': 'Versie BLAUW',
        'amount': 26, 'blanks': None, 
        'ceex_subj_name_nl': 'Engelse taal', 
        'ceex_subj_code': 'en'}
    """
    if grade_exam_dict:
        requsr = request.user
        save_changes = False

        exam_id = grade_exam_dict.get('exam_id')

        if exam_id not in count_dict:
            count_dict[exam_id] = {
                'exam_id': grade_exam_dict.get('exam_id'),
                'exam_name': grade_exam_dict.get('exam_name'),
                'count': 0
            }
        exam_dict = count_dict[exam_id]

        af.add_one_to_count_dict(exam_dict, 'count')

# - skip if this student has no exam
        # because of INNER JOIN ce_exam exam_id has always a value
        # was: no_exam = not grade_exam_dict.get('exam_id')

        no_questions = not grade_exam_dict.get('amount')
        has_blank_questions = True if grade_exam_dict.get('blanks') else False
        already_submitted = True if grade_exam_dict.get('ce_exam_published_id') else False

        # requsr_auth: auth3
        # requsr_authby_field: ce_exam_auth3by_id
        # requsr_authby_value: 904
        requsr_authby_field = 'ce_exam_' + requsr_auth + 'by_id'
        requsr_authby_value = grade_exam_dict.get(requsr_authby_field)

        if logging_on:
            logger.debug('    requsr_auth: ' + str(requsr_auth))
            logger.debug('    requsr_authby_field: ' + str(requsr_authby_field))
            logger.debug('    requsr_authby_value: ' + str(requsr_authby_value))

            logger.debug('     grade_id:     ' + str(grade_exam_dict.get('grade_id')))
            logger.debug('     no_questions:     ' + str(no_questions))
            logger.debug('     blank_quest:      ' + str(has_blank_questions))
            logger.debug('     already_submitted:     ' + str(already_submitted))

# - remove authby when is_reset
        if is_reset:
            if already_submitted:
                af.add_one_to_count_dict(exam_dict, 'already_submitted')
            else:
                if requsr_authby_value:
                    if requsr_authby_value != requsr.pk:
                        af.add_one_to_count_dict(exam_dict, 'approved_by_diff_user')
                    else:
                        af.add_one_to_count_dict(total_dict, 'reset')
                        save_changes = True
        else:

    # - skip if ete_exam has no questions
            if no_questions:
                af.add_one_to_count_dict(exam_dict, 'no_questions')

    # - skip if ete_exam has blank questions
            elif has_blank_questions:
                af.add_one_to_count_dict(exam_dict, 'blank_questions')

    # - skip if this grade_exam is already submitted
            elif already_submitted:
                af.add_one_to_count_dict(exam_dict, 'already_submitted')

            else:
                has_result = True if grade_exam_dict.get('ce_exam_result') else False
                has_blank_answers = True if grade_exam_dict.get('ce_exam_blanks') else False
                if logging_on:
                    logger.debug('     has_result:     ' + str(has_result))
                    logger.debug('     blank_answers:     ' + str(has_blank_answers))

        # skip if this grade_exam has_blanks or result is empty - not when is_reset
                if not has_result or has_blank_answers:
                    af.add_one_to_count_dict(exam_dict, 'has_blanks')
                else:

                    auth1by_id = grade_exam_dict.get('ce_exam_auth1by_id')
                    auth2by_id = grade_exam_dict.get('ce_exam_auth2by_id')
                    auth3by_id = grade_exam_dict.get('ce_exam_auth3by_id')
                    if logging_on:
                        logger.debug('     auth1by_id:     ' + str(auth1by_id))
                        logger.debug('     auth2by_id:     ' + str(auth2by_id))
                        logger.debug('     auth3by_id:     ' + str(auth3by_id))

        # - skip if this grade_exam is double_approved
            # double_approved means: this auth has already approved other auth - is not allowed to approve as auth1 and auth2
                    # PR2023-04-10 debug. there are se-grades with approval of corrector. To prevent double approval notcie, skip corrector in se grade
                    double_approved = (requsr_auth == 'auth1' and auth2by_id and auth2by_id == requsr.pk) or \
                                        (requsr_auth == 'auth2' and auth1by_id and auth1by_id == requsr.pk)
                    if logging_on:
                        logger.debug('     double_approved:     ' + str(double_approved))

        # - skip if this grade_exam is double_approved - not when is_reset
                    if double_approved:
                        af.add_one_to_count_dict(exam_dict, 'double_approved')
                    else:
                        is_fully_approved = auth1by_id is not None and auth2by_id is not None and auth3by_id is not None

                        if logging_on:
                            logger.debug('     fully_approved:     ' + str(is_fully_approved))
                            logger.debug('     already_approved:     ' + str(not is_submit and not is_reset and requsr_authby_value))

        # - when is_approve: skip if this exam is already approved - only in approve mode, not when is_reset
                        if not is_submit and requsr_authby_value:
                            af.add_one_to_count_dict(exam_dict, 'already_approved')
                            af.add_one_to_count_dict(total_dict, 'already_approved')

        # - when is_submit: skip if this grade_exam is not fully_approved - is_reset is not applicable when is_submit
                        elif is_submit and not is_fully_approved:
                            af.add_one_to_count_dict(exam_dict, 'not_fully_approved')

                        else:
                            save_changes = True

                        if logging_on:
                            logger.debug('  ????   is_submit and not is_fully_approved:     ' + str(is_submit and not is_fully_approved))
# - if no errors found: add grade_pk and new_auth_id to grade_exams_tobe_updated_list
        if save_changes:
            grade_pk = grade_exam_dict.get('grade_id')
            exam_pk = grade_exam_dict.get('exam_id')
            if grade_pk not in grade_exams_tobe_updated_list:

# - add grade_pk to tobe_updated_list
                grade_exams_tobe_updated_list.append((grade_pk, exam_pk))

# - if save_changes: add to 'committed' if is_test, to 'tobesaved' if is_save
                key_str = 'committed' if is_test else 'tobesaved'
                af.add_one_to_count_dict(exam_dict, key_str)
                af.add_one_to_count_dict(total_dict, key_str)

    if logging_on:
        logger.debug('     count_dict:      ' + str(count_dict))
        logger.debug('     total_dict:      ' + str(total_dict))

# - end of approve_grade_exam


def publish_exam(request, exam_instance, published_instance, is_test, count_dict, updated_exam_pk_list):
    # PR2022-02-23 PR2022-04-20
    # function puts published in exam and set flag update_exam_in_grades when saved
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- publish_exam -----')

    update_exam_in_grades = False
    if exam_instance:
        count_dict['count'] += 1

# - check if this exam is already published
        published = getattr(exam_instance, 'published')
        if logging_on:
            logger.debug('published: ' + str(published))

        if published:
            count_dict['already_published'] += 1
        else:

# - check if this exam / examtype is approved by all auth
            auth1by = getattr(exam_instance, 'auth1by')
            auth2by = getattr(exam_instance, 'auth2by')
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
# - set value of published_instance and examtype_status field
                    if is_test:
                        count_dict['committed'] += 1
                    else:

                        update_exam_in_grades = False
                        try:
# - put published_id in field published
                            setattr(exam_instance, 'published', published_instance)
# - save changes
                            exam_instance.save(request=request)
                            count_dict['saved'] += 1

                            update_exam_in_grades = True
                            updated_exam_pk_list.append(exam_instance.pk)

                        except Exception as e:
                            logger.error(getattr(e, 'message', str(e)))
                            count_dict['saved_error'] += 1

    return update_exam_in_grades
# - end of publish_exam

"""
def submit_grade_exam(grade_exam_instance, is_test, published_instance, count_dict, request):  # PR2022-02-04
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- submit_grade_exam -----')

    updated_grd_count = 0
    if exam:
        count_dict['count'] += 1

# - check if this exam is already published
        published = getattr(exam, 'published')
        if logging_on:
            logger.debug('published: ' + str(published))

        if published:
            count_dict['already_published'] += 1
        else:

# - check if this exam / examtype is approved by all auth
            auth1by = getattr(exam, 'auth1by')
            auth2by = getattr(exam, 'auth2by')
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
# - set value of published_instance and examtype_status field
                    if is_test:
                        count_dict['committed'] += 1
                    else:

                        update_exam_in_grades = False
                        try:
# - put published_id in field published
                            setattr(exam, 'published', published_instance)
# - save changes
                            exam.save(request=request)
                            count_dict['saved'] += 1
                            update_exam_in_grades = True
                        except Exception as e:
                            logger.error(getattr(e, 'message', str(e)))
                            count_dict['saved_error'] += 1

# --- add exam_pk to grades when published
                        if update_exam_in_grades:  # is_publish_exam and not is_test:
# - skip when there are more than 1 exam for this subject / dep / level / examperiod

                            crit = Q(subject=exam.subject) & \
                                   Q(department=exam.department)
                            if exam.examperiod in (1, 2):
                                crit.add(Q(examperiod=exam.examperiod), crit.connector)
                            else:
                                crit.add(Q(examperiod__lte=2), crit.connector)
                            if exam.level:
                                crit.add(Q(level=exam.level), crit.connector)

                            count_exams = subj_mod.Exam.objects.filter(crit).count()
                            if count_exams == 1:
                                grd_count = link_exam_to_grades(exam)
                                if grd_count:
                                    count_dict['updated_grd_count'] += grd_count
# - end of submit_grade_exam
    """

def create_exam_published_instance(exam, now_arr, request):  # PR2022-02-23
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_exam_published_instance -----')
        logger.debug('request.user: ' + str(request.user))

    # create new published_instance and save it when it is not a test (this function is only called when it is not a test)
    # filename is added after creating file in create_ex1_xlsx
    subjbase_code = exam.subject.base.code
    depbase_code = exam.department.base.code
    lvlbase_code = ''
    if exam.level:
        lvlbase_code = exam.level.base.code
    examperiod = exam.examperiod

    # examtype used to store 'ete' or 'duo' exam

    # to be used when submitting Ex4 form
    examtype_caption = ''
    exform = 'Exam'

    if examperiod == 1:
        examtype_caption = 'ce'
    elif examperiod == 2:
        examtype_caption = 'her'
    elif examperiod == 12:
        examtype_caption = 'ce her'

    today_date = af.get_date_from_arr(now_arr)

    year_str = str(now_arr[0])
    month_str = ("00" + str(now_arr[1]))[-2:]
    date_str = ("00" + str(now_arr[2]))[-2:]
    hour_str = ("00" + str(now_arr[3]))[-2:]
    minute_str = ("00" +str( now_arr[4]))[-2:]
    now_formatted = ''.join([year_str, "-", month_str, "-", date_str, " ", hour_str, "u", minute_str])

    file_name = ' '.join((exform, examtype_caption, depbase_code, lvlbase_code + subjbase_code, now_formatted))
    # if total file_name is still too long: cut off
    if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
        file_name = file_name[0:c.MAX_LENGTH_FIRSTLASTNAME]
    # PR2022-08-24 Pien van Dijk: cannot publish. Error: 'expected string or bytes-like object'
    # Is caused by 'modifiedat=timezone.now', must be 'modifiedat=timezone.now()'
    # changed from sch_mod.Published.objects.create() to sch_mod.Published() plus save(request=request)
    published_instance = sch_mod.Published(
        school=None,
        department=exam.department,
        examtype=examtype_caption,
        examperiod=exam.examperiod,
        name=file_name,
        datepublished=today_date
    )
    # Note: filefield 'file' gets value on creating Ex form

    published_instance.filename = file_name + '.pdf'
    # PR2021-09-06 debug: request.user is not saved in instance.save, don't know why
    published_instance.save(request=request)

    if logging_on:
        logger.debug(' request.user: ' + str(request.user))
        logger.debug('published_instance.saved: ' + str(published_instance))
        logger.debug('published_instance.pk: ' + str(published_instance.pk))
        logger.debug('published_instance.modifiedby: ' + str(published_instance.modifiedby))

    return published_instance
# - end of create_exam_published_instance


def create_grade_exam_submitted_instance(sel_school, department, examperiod, now_arr, request):  # PR2022-03-11

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_grade_exam_submitted_instance -----')
        logger.debug('request.user: ' + str(request.user))

    # create new published_instance and save it when it is not a test (this function is only called when it is not a test)
    # filename is added after creating file in create_ex1_xlsx

    depbase_code = department.base.code
    lvlbase_code = ''
    #if exam.level:
    #    lvlbase_code = exam.level.base.code

    # examtype used to store 'ete' or 'duo' exam

    # to be used when submitting Ex4 form
    examtype_caption = ''
    exform = 'Exam'
    published_instance = None

    if examperiod in (1, 2):
        if examperiod == 1:
            examtype_caption = 'ce'
        elif examperiod == 2:
            examtype_caption = 'her'


        today_date = af.get_date_from_arr(now_arr)

        year_str = str(now_arr[0])
        month_str = ("00" + str(now_arr[1]))[-2:]
        date_str = ("00" + str(now_arr[2]))[-2:]
        hour_str = ("00" + str(now_arr[3]))[-2:]
        minute_str = ("00" +str( now_arr[4]))[-2:]
        now_formatted = ''.join([year_str, "-", month_str, "-", date_str, " ", hour_str, "u", minute_str])

        file_name = ' '.join((exform, examtype_caption, depbase_code, lvlbase_code + now_formatted))
        # if total file_name is still too long: cut off
        if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
            file_name = file_name[0:c.MAX_LENGTH_FIRSTLASTNAME]

        published_instance = sch_mod.Published(
            school=None,
            department=department,
            examtype=examtype_caption,
            examperiod=examperiod,
            name=file_name,
            datepublished=today_date
        )
        # Note: filefield 'file' gets value on creating Ex form

        published_instance.filename = file_name + '.pdf'
        # PR2021-09-06 debug: request.user is not saved in instance.save, don't know why
        published_instance.save(request=request)

        if logging_on:
            logger.debug(' request.user: ' + str(request.user))
            logger.debug('published_instance.saved: ' + str(published_instance))
            logger.debug('published_instance.pk: ' + str(published_instance.pk))
            logger.debug('published_instance.modifiedby: ' + str(published_instance.modifiedby))

    return published_instance
# - end of create_grade_exam_submitted_instance


def get_exam_name(ce_exam_id, ete_exam, subj_name_nl, depbase_code, lvl_abbrev, examperiod, examyear, version, ntb_omschrijving):
    # PR2022-06-22 PR2022-08-28 PR2023-05-11

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_exam_name -----')
        logger.debug('    ete_exam: ' + str(ete_exam))
        logger.debug('    ce_exam_id: ' + str(ce_exam_id))
        logger.debug('    subj_name_nl: ' + str(subj_name_nl))
        logger.debug('    depbase_code: ' + str(depbase_code))
        logger.debug('    lvl_abbrev: ' + str(lvl_abbrev))
        logger.debug('    examperiod: ' + str(examperiod))
        logger.debug('    examyear: ' + str(examyear))
        logger.debug('    version: ' + str(version))
        logger.debug('    ntb_omschrijving: ' + str(ntb_omschrijving))

    exam_name = None
    if ce_exam_id:
        exam_name = 'ETE' if ete_exam else 'CVTE'

        if ete_exam:
            if depbase_code:
                exam_name += ' ' + depbase_code
            if lvl_abbrev:
                exam_name += ' ' + lvl_abbrev
            if subj_name_nl:
                exam_name += ' ' + subj_name_nl
            if version:
                exam_name += ' ' + version
            if examperiod:
                exam_name += ' tijdvak ' + str(examperiod)
            exam_name += ' - ' + str(examyear.code)
        else:
        # add 'Vsbo' when lvl_abbrev has value (Havo Vwo is included in DUO mname
            if depbase_code:
                exam_name += ' ' + depbase_code
            if ntb_omschrijving:
                exam_name += ' ' + ntb_omschrijving
            else:
                # used for extra duo exams without link to ntermen table
                if lvl_abbrev:
                    exam_name += ' ' + lvl_abbrev
                if subj_name_nl:
                    exam_name += ' ' + subj_name_nl

                if version:
                    exam_name += ' ' + version
                if examperiod:
                    exam_name += ' tijdvak ' + str(examperiod)

                exam_name += ' - ' + str(examyear.code)
    if logging_on:
        logger.debug('    exam_name: ' + str(exam_name))

    return exam_name
# - end of get_exam_name


def link_exam_to_grades(exam_instance, requsr_examyear_pk, requsr_depbase_pk, exam_name, is_test, is_saved_in_loglist):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --- link_exam_to_grades --- ')

    # Note: ETE exams must also be assigned to students of SXM.
    #       but SXM can have his own DUO exams
    # - Don't filter on examyear.pk but on examyear.code

    # PR2022-06-02 tel Lavern SMAC: has sp DUO
    # solved by:
    # - SXM can also create exams in exam page
    # - CUR can assign exams to SXM, don't  override (skip when ce_exam_id has value
    # - SXM can only assign exams to SXM, may override

    updated_grd_count = 0

    log_list = []
    if exam_instance.examperiod in (1, 2, 3):

        # - skip when there is more than 1 exam for this subject / dep / level / examperiod
        # TODO: in SXM subject may have ETE exams (ey=cur) and DUO examns (ey=sxm) How to deal with this?
        crit = Q(subject=exam_instance.subject) & \
               Q(department=exam_instance.department) & \
               Q(examperiod=exam_instance.examperiod)
        if exam_instance.level:
            crit.add(Q(level=exam_instance.level), crit.connector)

        count_exams = subj_mod.Exam.objects.filter(crit).count()
        if logging_on:
            logger.debug('    count_exams:     ' + str(count_exams))

    # skip if there are multiple exams
        if count_exams == 1:
            # PR2022-06-14 link only grade from own country > filter on subject_pk instead of subjectbase_pk
            # Was: also add exam to students of SXM, therefore use subjbase and examyear instead of subject
            subjbase_pk = exam_instance.subject.base_id
            lvlbase_pk = exam_instance.level.base_id if exam_instance.level else None
            examperiod = exam_instance.examperiod
            ce_exam_pk = exam_instance.pk

            if logging_on:
                logger.debug('    exam.subj.name_nl: ' + str(exam_instance.subject.name_nl))
                logger.debug('    requsr_examyear_pk:    ' + str(requsr_examyear_pk))
                logger.debug('    lvlbase_pk:     ' + str(lvlbase_pk))
                logger.debug('    examperiod:     ' + str(examperiod))
                logger.debug('    ce_exam_pk:     ' + str(ce_exam_pk))
                logger.debug('    is_test:        ' + str(is_test))

            try:
                sql_keys = {'ey_pk': requsr_examyear_pk, 'db_pk': requsr_depbase_pk, 'lb_pk': lvlbase_pk,
                            'subjbase_pk': subjbase_pk, 'ep': examperiod,  'ce_exam_pk': ce_exam_pk}

                # when may_override = True it will replace existing ce_exams with the new ones,
                # if False it will skip existing ce_exams
                # PR2022-06-14 don not override. Was: may_override_clause = "AND grd.ce_exam_id IS NULL" if not may_override else ""
                # only get student from users own country
                if not is_test:
                    sub_sql_list = ["SELECT grd.id AS grd_id"]
                else:
                    sub_sql_list = ["SELECT CONCAT_WS (' ', schoolbase.code, school.name),",
                                    "CONCAT_WS (' ', '   ', stud.prefix, CONCAT(stud.lastname, ','), stud.firstname),",
                                    "grd.ce_exam_id, exam.ete_exam, subj.name_nl, depbase.code, dep.level_req,",
                                    "lvlbase.code, exam.version, ntb.omschrijving"
                                    ]

                sub_sql_list.extend([
                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                    "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                    "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                    "INNER JOIN schools_schoolbase AS schoolbase ON (schoolbase.id = school.base_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                    "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                    "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                    "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id )",

                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                    "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                    "LEFT JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id)",
                    "LEFT JOIN subjects_ntermentable AS ntb ON (ntb.id = exam.ntermentable_id)",

                    "WHERE dep.base_id = %(db_pk)s::INT",
                    "AND subj.base_id = %(subjbase_pk)s::INT",
                    "AND grd.examperiod = %(ep)s::INT",
# override linked exams allowed
                    # "AND grd.ce_exam_id IS NULL",

# PR2023-05-26 debug: must filter on weight_ce>0 because of sptl without CE
                    #TODO test
                    # "AND si.weight_ce > 0",

# this_country_only
                    "AND ey.id = %(ey_pk)s::INT"
                ])

# lvlbase_clause
                if lvlbase_pk:
                    sub_sql_list.append("AND lvl.base_id = %(lb_pk)s::INT")

                sub_sql_list.extend((
                    "AND NOT stud.deleted AND NOT stud.tobedeleted",
                    "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted",
                    "AND NOT grd.deleted AND NOT grd.tobedeleted"
                ))
                if is_test:
                    sub_sql_list.append("ORDER BY schoolbase.code, dep.sequence, lvl.sequence, stud.lastname, stud.firstname")

                sub_sql = ' '.join(sub_sql_list)

                if is_test:
                    with connection.cursor() as cursor:
                        cursor.execute(sub_sql, sql_keys)
                        rows = cursor.fetchall()

                        if rows:
                            updated_grd_count = len(rows)
                            ete_duo_cpt = _('ETE exam') if exam_instance.ete_exam else _('CVTE exam')
                            willbe_hasbeen = pgettext_lazy('singular', 'has been') if is_saved_in_loglist else pgettext_lazy('singular', 'will be')
                            log_list.append(str(_('This %(cpt)s %(wbhb)s linked to the following %(cnt)s subjects of candidates:') \
                                                %{'cpt': ete_duo_cpt, 'wbhb': willbe_hasbeen, 'cnt': updated_grd_count}))
                            log_list.append(c.STRING_SINGLELINE_80)
                            log_list.append(exam_name)
                            log_list.append(c.STRING_SINGLELINE_80)
                            for row in rows:
                                # add school line
                                if row[0] not in log_list:  # row[0] = schoolbase.code, school.name
                                    log_list.append(row[0])

                                # add line with student and subject / exam if already linked
                                exam_name = ''
                                if row[2]:  # row[2] = grd.ce_exam_id
                                    #if row[3]:  # ete_exam
                                    #    exam_name = ' '.join(('ETE', row[4], row[5]))  # subj_name_nl, depbase_code
                                    #    if row[6]:  # level_req
                                    #        exam_name += (row[7] if row[7] else '-') # lvlbase_code'
                                    #    if row[8]:
                                    #        exam_name += ' ' + row[8]  # version
                                    # else:
                                    #    exam_name = ' '.join(('DUO', row[9] if row[9] else '-'))   # omschrijving

                                    exam_name = get_exam_name(
                                        ce_exam_id=row[2], # row[2] = grd.ce_exam_id - only used to return blank when no ce_exam_id
                                        ete_exam=row[3], # row[3] = ete_exam
                                        subj_name_nl=row[4], # row[4] = subj.name_nl
                                        depbase_code=row[5], # row[5] = depbase.code,
                                        lvl_abbrev=(row[7] if row[7] else '-'), # row[7] = lvlbase.code
                                        examperiod=examperiod,
                                        examyear=exam_instance.subject.examyear,
                                        version=row[8], # row[8] = exam.version,
                                        ntb_omschrijving=row[9] # row[9] = ntb.omschrijving"
                                    )

                                log_list.append(c.STRING_SPACE_05.join(((row[1] + c.STRING_SPACE_40)[:40], exam_name)))
                else:
                    sql_list = [
                        "WITH sub_sql AS (", sub_sql, " )",

                        "UPDATE students_grade",
                        "SET ce_exam_id = %(ce_exam_pk)s::INT",
                        "FROM sub_sql",
                        "WHERE id = sub_sql.grd_id",
                        "RETURNING id;"
                    ]

                    sql = ' '.join(sql_list)

                    with connection.cursor() as cursor:
                        cursor.execute(sql, sql_keys)
                        rows = cursor.fetchall()

                        if rows:
                            updated_grd_count = len(rows)
                            if logging_on:
                                logger.debug('updated_grd_count: ' + str(updated_grd_count))

                    # for testing only:
                    if logging_on and False:
                        for qr in connection.queries:
                            logger.debug('-----------------------------------------------------------------------------')
                            logger.debug(str(qr))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug(' >>> updated_grd_count: ' + str(updated_grd_count))
        for row in log_list:
            logger.debug(' >>> log_list row: ' + str(row))

    return updated_grd_count, log_list
# end of link_exam_to_grades


def create_exam_instance(subject, department, level, examperiod_int, ete_exam, request, version=None, ntermentable=None):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --- create_exam_instance --- ')
        logger.debug('    subject: ' + str(subject))
        logger.debug('    department: ' + str(department))
        logger.debug('    level: ' + str(level))
        logger.debug('    version: ' + str(version))
        logger.debug('    examperiod_int: ' + str(examperiod_int))

    exam = None
    err_html = None
# - create exam
    try:
        if department.level_req and level is None:
            err_html = _('The learning path cannot be blank.')
        else:
            #a = 1 / 0 # to create error
            exam = subj_mod.Exam(
                subject=subject,
                department=department,
                level=level,
                examperiod=examperiod_int,
                ete_exam=ete_exam
                # NIU was: (null not allowed): examtype=examtype
            )
            # only used when creating duo-exam
            if ntermentable:
                exam.ntermentable = ntermentable
            if version:
                exam.version = version

            exam.save(request=request)
            if logging_on:
                logger.debug('    exam: ' + str(exam))

    except Exception as e:
# - create error when exam is not created PR2023-03-20
        logger.error(getattr(e, 'message', str(e)))
        err_html = acc_prm.errhtml_error_occurred_with_border(e, _('The exam could not be created.'))

    return exam, err_html
# - end of create_exam_instance


def delete_exam_instance(instance, request):  #  PR2021-04-05 PR2022-01-22 PR2022-08-23 PR2023-03-20

    deleted_row = {'id': instance.pk,
                    'mapid': 'exam_' + str(instance.pk),
                    'deleted': True}

    err_txt = None
    try:
        instance.delete(request=request)
    except Exception as e:
        deleted_row = None
        logger.error(getattr(e, 'message', str(e)))
        err_txt = acc_prm. errhtml_error_occurred_no_border(e, _('This exam could not be deleted.'))
    return deleted_row, err_txt
# - end of delete_exam_instance


def update_exam_instance(request, sel_examyear, sel_department, exam_instance, upload_dict, error_list):
    # PR2021-04-05 PR2022-01-24 PR2022-05-06 PR2022-05-22
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --------- update_exam_instance -------------')
        logger.debug('     upload_dict: ' + str(upload_dict))
        # upload_dict: {'table': 'exam', 'mode': 'update', 'examyear_pk': 1, 'depbase_pk': 1, 'lvlbase_pk': 13,
        # 'exam_pk': 138, 'subject_pk': 2137, 'field': 'authby', 'auth_index': 2, 'auth_bool_at_index': True}

    updated_cegrade_count = 0
    if exam_instance:
        save_changes = False
        calc_amount_and_scalelength = False
        calc_cegrade_from_exam_score = False

        for field, new_value in upload_dict.items():
# --- skip fields that don't contain new values
            if field in ('mode', 'examyear_pk', 'subject_pk', 'exam_pk', 'examtype'):
                pass

            elif field == 'lvlbase_pk':
                db_field = 'level'
                if logging_on:
                    logger.debug('     field: ' + str(field))
                    logger.debug('     new_value: ' + str(new_value))

                new_level = subj_mod.Level.objects.get_or_none(
                    base_id=new_value,
                    examyear=sel_examyear
                )
                if logging_on:
                    logger.debug('     new_level: ' + str(new_level))

                old_level = getattr(exam_instance, db_field)
                if logging_on:
                    logger.debug('     old_level: ' + str(old_level))

                if new_level != old_level:
                    setattr(exam_instance, db_field, new_level)
                    save_changes = True
                    calc_cegrade_from_exam_score = True

            elif field in ('amount', 'blanks'):
                # these are calculated fields and will be calculated in calc_amount_and_scalelength
                pass

            elif field == 'nterm':
                # only in DUO exams the nterm can be entered
                is_ete_exam = getattr(exam_instance, 'ete_exam', False)

                if logging_on:
                    logger.debug('     is_ete_exam: ' + str(is_ete_exam))

                if not is_ete_exam:
                    # save None instead of  '' or 0
                    if not new_value:
                        new_value = None

                    # - get_grade_number_from_input_str returns None when new_value has no value, without msg_err
                    new_value_str, err_list = calc_score.get_nterm_number_from_input_str(new_value)

                    if err_list:
                        error_list.extend(err_list)
                    else:
                        old_value = getattr(exam_instance, field)
                        if new_value_str != old_value:
                            setattr(exam_instance, field, new_value_str)
                            save_changes = True
                            calc_cegrade_from_exam_score = True

            elif field == 'scalelength':
                # only in DUO exams the scalelength can be entered
                is_ete_exam = getattr(exam_instance, 'ete_exam', False)

                if not is_ete_exam:
                    # save None instead of  '' or 0
                    if not new_value:
                        new_value = None

                    # - get_score_from_inputscore returns None when new_value has no value, without msg_err
                    new_value_int, new_value_str, err_list = calc_final.get_score_from_inputscore(new_value)

                    if err_list:
                        error_list.extend(err_list)
                    else:
                        # check if new_value_str gves valid integer is done in get_score_from_inputscore
                        # new_value_int = int(new_value_str) if new_value_str else None

                        old_value = getattr(exam_instance, field)

                        if new_value_int != old_value:
                            setattr(exam_instance, field, new_value_int)
                            save_changes = True
                            calc_cegrade_from_exam_score = True

                        if logging_on:
                            logger.debug('     field:        ' + str(field))
                            logger.debug('     new_value:    ' + str(new_value) + ' ' + str(type(new_value)))
                            logger.debug('     old_value:    ' + str(old_value) + ' ' + str(type(old_value)))
                            logger.debug('     save_changes: ' + str(save_changes))

            elif field == 'cesuur':
                # save None instead of  '' or 0
                if not new_value:
                    new_value = None
                max_score = getattr(exam_instance, 'scalelength')
                # - get_score_from_inputscore returns None when new_value has no value, without msg_err
                new_value_int, new_value_str, err_list = calc_final.get_score_from_inputscore(new_value, max_score)
                if err_list:
                    error_list.extend(err_list)
                else:
                    # new_value_int = int(new_value_str) if new_value_str else None
                    old_value = getattr(exam_instance, field)
                    if new_value_int != old_value:
                        setattr(exam_instance, field, new_value_int)
                        save_changes = True
                        calc_cegrade_from_exam_score = True

                    if logging_on:
                        logger.debug('     field:        ' + str(field))
                        logger.debug('     new_value_int:    ' + str(new_value_int) + ' ' + str(type(new_value_int)))
                        logger.debug('     old_value:    ' + str(old_value) + ' ' + str(type(old_value)))
                        logger.debug('     save_changes: ' + str(save_changes))

            # PR2023-05-04 debug: when 'all exam periods' is selected examperiod = -1.
            # Gives error: relation "subjects_exam" violates check constraint "subjects_exam_examperiod_check"
            # solved by removing field 'examperiod'
            # examperiod cannot be changed
            # was: elif field in ('partex', 'assignment', 'keys', 'version', 'examperiod', 'nex_id'):
            elif field in ('partex', 'assignment', 'keys', 'version', 'nex_id'):
                # save None instead of  '' or 0
                if not new_value:
                    new_value = None
                old_value = getattr(exam_instance, field)

                # always calculate and save result, to be on the safe side. Was: if new_value != saved_value:
                setattr(exam_instance, field, new_value)
                save_changes = True
                if field in ('partex', 'assignment', 'keys'):
                    calc_amount_and_scalelength = True

            elif field in ('secret_exam', 'has_errata'):
                if not new_value:
                    new_value = False

                if logging_on:
                    logger.debug('field: ' + str(field))
                    logger.debug('new_value: ' + str(new_value))

                old_value = getattr(exam_instance, field, False)
                if new_value != old_value:
                    setattr(exam_instance, field, new_value)
                    save_changes = True
                    logger.debug('save_changes: ' + str(save_changes))

            elif field == 'has_partex':
                if not new_value:
                    new_value = False
                old_value = getattr(exam_instance, field, False)
                if new_value != old_value:
                    setattr(exam_instance, field, new_value)
                    save_changes = True
                    calc_amount_and_scalelength = True

            elif field == 'auth_index':
                auth_index = upload_dict.get(field)
                auth_bool_at_index = upload_dict.get('auth_bool_at_index', False)
                authby = 'auth1by' if auth_index == 1 else 'auth2by' if auth_index == 2 else None
                if logging_on:
                    logger.debug('auth_index: ' + str(auth_index))
                    logger.debug('auth_bool_at_index: ' + str(auth_bool_at_index))
                    logger.debug('authby: ' + str(authby))

                if authby:

         # - check other authorization, to check if it is the same user. Only when auth is set to True
                    authby_other_field = 'auth2by' if authby == 'auth1by' else 'auth1by'
                    other_authby_value = getattr(exam_instance, authby_other_field)
                    if logging_on:
                        logger.debug('  authby_other_field:    ' + str(authby_other_field))
                        logger.debug('  other_authby_value: ' + str(other_authby_value))
                        logger.debug('  request.user: ' + str(request.user) )

                    if auth_bool_at_index and other_authby_value and other_authby_value == request.user:
                        error_list.extend((
                            gettext('You already have approved %(cpt)s in a different function.') % {'cpt': gettext('This exam').lower()},
                            gettext('You cannot approve %(cpt)s in multiple functions.') % {'cpt': gettext('an exam')}
                        ))
                        if logging_on:
                            logger.debug('  err_same_user')

                    else:
                        new_value = request.user if auth_bool_at_index else None
                        if logging_on:
                            logger.debug('new_value: ' + str(auth_index))

                        setattr(exam_instance, authby, new_value)
                        save_changes = True

            elif field == 'published':
                # can only remove published. ALso remove auth1, auth2. PR2022-05-21
                setattr(exam_instance, field, None)
                setattr(exam_instance, 'auth1by', None)
                setattr(exam_instance, 'auth2by', None)
                setattr(exam_instance, 'auth3by', None)
                save_changes = True

            elif field == 'envelopbundle_pk':
                db_field = 'envelopbundle'

                new_instance = subj_mod.Envelopbundle.objects.get_or_none(pk=new_value)
                old_instance = getattr(exam_instance, db_field)

                if logging_on:
                    logger.debug('     field:        ' + str(field))
                    logger.debug('     new_instance:    ' + str(new_instance) + ' ' + str(type(new_instance)))
                    logger.debug('     old_instance:    ' + str(old_instance) + ' ' + str(type(old_instance)))

                if new_instance != old_instance:
                    setattr(exam_instance, db_field, new_instance)
                    setattr(exam_instance, 'evl_modifiedby', request.user)
                    setattr(exam_instance, 'evl_modifiedat', timezone.now())
                    save_changes = True

                if logging_on:
                    logger.debug('     save_changes: ' + str(save_changes))

            elif field == 'datum':
    # new_value has format of date-iso, Excel ordinal format is already converted
                saved_dateobj = getattr(exam_instance, field)

                new_dateobj = af.get_date_from_ISO(new_value)

                if new_dateobj != saved_dateobj:
                    if logging_on:
                        logger.debug('birthdate saved: ' + str(saved_dateobj) + ' ' + str(type(saved_dateobj)))
                        logger.debug('birthdate new  : ' + str(new_dateobj) + ' ' + str(type(new_dateobj)))

                    setattr(exam_instance, field, new_value)
                    save_changes = True

            elif field in ('begintijd', 'eindtijd'):
                if logging_on:
                    logger.debug('field: ' + str(field))
                    logger.debug('new_value: ' + str(new_value))

                old_value = getattr(exam_instance, field, False)
                if new_value != old_value:
                    setattr(exam_instance, field, new_value)
                    save_changes = True
                    logger.debug('save_changes: ' + str(save_changes))

# - save exam_instance
        if save_changes:
            try:
                exam_instance.save(request=request)
                if logging_on:
                    logger.debug('     exam_instance saved: ' + str(exam_instance))

# - calculate amount and scalelength
                # error: conversion from NoneType to Decimal is not supported
                if calc_amount_and_scalelength:
                    total_amount, total_maxscore, total_blanks, total_keys_missing, has_changed = \
                        grade_view.calc_amount_and_scalelength_of_assignment(exam_instance)
                    if logging_on:
                        logger.debug('     total_amount:  ' + str(total_amount)  + ' ' + str(type(total_amount)))
                        logger.debug('     total_maxscore: ' + str(total_maxscore) + ' ' + str(type(total_maxscore)))
                        logger.debug('     total_blanks:   ' + str(total_blanks) + ' ' + str(type(total_blanks)))
                        logger.debug('     total_keys_missing:   ' + str(total_keys_missing) + ' ' + str(type(total_keys_missing)))
                        logger.debug('     has_changed:    ' + str(has_changed) + ' ' + str(type(has_changed)))

                    if has_changed:
                        setattr(exam_instance, 'amount', total_amount)
                        setattr(exam_instance, 'scalelength', total_maxscore)
                        setattr(exam_instance, 'blanks', total_blanks)
                        exam_instance.save(request=request)

# calculate cegrade when scalelength, nterm or  cesuur has changed
                if calc_cegrade_from_exam_score:

                    #starttime = timer()
                    #updated_cegrade_count, updated_cegrade_listNIU, updated_student_pk_listNIU = \
                    #    calc_score.batch_update_finalgrade(
                    #   department_instance=sel_department,
                    #    exam_instance=exam_instance
                    #)
                    #if logging_on:
                    #    elapsed_seconds = int(1000 * (timer() - starttime)) / 1000
                    #    logger.debug('     elapsed_seconds: ' + str(elapsed_seconds))

                    starttime = timer()
                    updated_cegrade_list, updated_student_pk_list = \
                        calc_final.batch_update_finalgrade_v2(
                            req_user=request.user,
                            ce_exam_pk=exam_instance.pk
                        )
                    updated_cegrade_count = len(updated_cegrade_list)
                    if logging_on:
                        elapsed_seconds = int(1000 * (timer() - starttime)) / 1000
                        logger.debug('     elapsed_seconds: ' + str(elapsed_seconds))
                        logger.debug('     updated_cegrade_count: ' + str(updated_cegrade_count))
                        logger.debug('     updated_cegrade_list: ' + str(updated_cegrade_list))
                        logger.debug('     updated_student_pk_list: ' + str(updated_student_pk_list))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                # error: conversion from NoneType to Decimal is not supported
                #msg_err = ''.join((str(_('An error occurred.')), str(_('This exam could not be updated.'))))
                #error_list.append(msg_err)

                err_html = acc_prm.errhtml_error_occurred_no_border(e, _('This exam could not be updated.'))
                error_list.append(err_html)

    return updated_cegrade_count
# - end of update_exam_instance
#####################


def create_all_exam_rows(req_usr, sel_examyear, sel_depbase, sel_examperiod, append_dict, setting_dict=None, exam_pk_list=None):
    # PR2022-06-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_all_exam_rows ============= ')
        logger.debug('    sel_examyear: ' + str(sel_examyear))
        logger.debug('    sel_examyear.code: ' + str(sel_examyear.code))
        logger.debug('    sel_examyear.pk: ' + str(sel_examyear.pk))
        logger.debug('    sel_depbase: ' + str(sel_depbase))
        logger.debug('    sel_examperiod: ' + str(sel_examperiod))
        logger.debug('    exam_pk_list: ' + str(exam_pk_list))

    # PR2022-05-13 debug: Raymond Romney MPC: cannot open exam.
    # cause: exams were filtered by examyear.pk, SXM has different examyear.pk from CUR
    # solved by: filter by examyear.code instead of examyear.pk

    # PR2022-06-02 tel Lavern SMAC: has sp DUO
    # try solving by filtering on examyear.pk when ETE/DOE logs in

    # PR2022-06-23 only used in page Grades
    # --- creates rows with exams that:
    #       - show all exam.ete_exams (filter on sel_examyear.code) (only cur can create ete-exams)
    #       - show only DUO exams of this country (filter on sel_examyear.pk)
    #       - this depbase.id
    #       - this exam_period
    # dont show ETE exam when this subject has also a DUO exam of this country

    """
    In grade page: grade can be linked to the following exam:
    // - only when exam has same subjbase_pk and lvlbase_id as grade, (filter same ey, depbase is in sql)
    //  - also filter examperiod
    // PR2022-05-18 debug Mireille Peterson exam not showing
    //  - cause: sxm has different subj_pk, use subjbase_pk instead
    """

    all_exam_rows = []
    try:
        depbase_pk = sel_depbase.pk if sel_depbase else None
        examyear_pk = sel_examyear.pk if sel_examyear else None
        examyear_code = sel_examyear.code if sel_examyear else None

        # filte only exams of curacao if is_cur, including cur and sxm examsn if is_sxm
        is_sxm = sel_examyear.country.abbrev.lower() == 'sxm'
        examyear_clause = ''.join(("AND ey.code = ", str(examyear_code), "::INT")) \
                            if is_sxm else ''.join(("AND ey.id = ", str(examyear_pk), "::INT"))

        # when school: only ETE published exams (DUO exams are not published)
        sql_keys = {'depbase_id': sel_depbase.pk if sel_depbase else None,
                    'ep': sel_examperiod,
                    'ey_code': sel_examyear.code if sel_examyear else None,
                    'ey_pk': sel_examyear.pk if sel_examyear else None
                    }
        # PR2023-05-10 debug: excluding exam when subject has also duo examn is not working as subquery,
        # when PBL/PKL have ETE and TKL has duo exam, like biology.

        # PR2023-05-11 this one works
        # this subquery gives all subj / dep / lvl combinations with duo exams (of this country / examyear)
        # PR2023-05-28 exam.examperiod added
        # PR2023-05-28 debug: checks only within own country, muste use depbase etc instad ofdep, but only when sxm
        # different approach: create list of exam_pks that have cvte exams in own country, this examperiod
        duo_exams_sql = ' '.join((
            "SELECT dep.base_id AS depbase_id, lvl.base_id AS lvlbase_id, subj.base_id AS subjbase_id, ",
            "ey.code AS ey_code, exam.examperiod ",
            "FROM subjects_exam AS exam",
            "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
            "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

            "WHERE NOT exam.ete_exam",
            "AND dep.base_id = ", str(depbase_pk) , "::INT",
            "AND ey.id = ", str(examyear_pk), "::INT",
            "AND exam.examperiod = ", str(sel_examperiod), "::INT",

            "GROUP BY dep.base_id, lvl.base_id, subj.base_id, ey.code, exam.examperiod "

        ))
        sql_list = [
            "WITH duo_exams AS (", duo_exams_sql, ")",
            "SELECT exam.id, exam.subject_id AS subj_id, subj.base_id AS subjbase_id, subj.examyear_id AS subj_examyear_id,",
            "CONCAT('exam_', exam.id::TEXT) AS mapid,",

            "CONCAT('N', ntb.id, 'D', dep.id, 'S', subj.id, 'L', lvl.id) AS ndsl_pk,",
            "exam.examperiod, exam.department_id AS dep_id, depbase.id AS depbase_id, depbase.code AS depbase_code, dep.sequence AS dep_sequence,",
            "exam.level_id AS lvl_id, lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev, lvl.sequence AS lvl_sequence,",
            "exam.ete_exam, exam.version, exam.nex_id, exam.scalelength, exam.nterm, exam.secret_exam,",

            "sb.code AS subjbase_code, subj.name_nl AS subj_name_nl, subj.name_en AS subj_name_en, subj.name_pa AS subj_name_pa,",

            "ey.id AS ey_id, ey.code AS ey_code, ey.locked AS ey_locked,",

            "ntb.id AS ntb_id, ntb.nex_id AS ntb_nex_id, ntb.leerweg AS ntb_leerweg,",
            "ntb.tijdvak AS ntb_tijdvak, ntb.omschrijving AS ntb_omschrijving, ntb.schaallengte AS ntb_schaallengte, ntb.n_term AS ntb_nterm,",
            "ntb.datum AS ntb_datum,"
            
            "(dex.depbase_id IS NOT NULL) AS has_duo_exams,",
    
            "exam.status, exam.auth1by_id, exam.auth2by_id, exam.published_id, exam.locked, exam.modifiedat,",
            "au.last_name AS modby_username,",

            "auth1.last_name AS auth1_usr, auth2.last_name AS auth2_usr, publ.modifiedat AS publ_modat",

            "FROM subjects_exam AS exam",
            "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
            "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

            "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

            "LEFT JOIN subjects_ntermentable AS ntb ON (ntb.id = exam.ntermentable_id)",

           "LEFT JOIN duo_exams AS dex ON (dex.depbase_id = dep.base_id ",
                                            "AND dex.lvlbase_id = lvl.base_id",
                                            "AND dex.subjbase_id = subj.base_id",
                                            "AND dex.ey_code = ey.code",
                                            "AND dex.examperiod = exam.examperiod)",

            "LEFT JOIN accounts_user AS auth1 ON (auth1.id = exam.auth1by_id)",
            "LEFT JOIN accounts_user AS auth2 ON (auth2.id = exam.auth2by_id)",
            "LEFT JOIN schools_published AS publ ON (publ.id = exam.published_id)",

            "LEFT JOIN accounts_user AS au ON (au.id = exam.modifiedby_id)",

            "WHERE depbase.id = %(depbase_id)s::INT",

            # skip ETE exam when this country has also duo exams
            "AND ( (dex.depbase_id IS NULL) OR (dex.depbase_id IS NOT NULL AND NOT exam.ete_exam)  ) ",

            # examyear_clause,
            # - only show DUO exams of this country (filter on ey.id when NOT ete_exam)
            # - show ETE exams of all countries (filter on ey.code when ete_exam)
            # - but don't show ETE exam when there is also a DUO exam of this country
            #   (sxm has en and sp DUO exam, cur has ETE exam en and sp)
            # dex.subject_id has only value when subj/dep/lvl has duo exams
            # "AND ((exam.ete_exam AND ey.code = %(ey_code)s::INT AND dex.subject_id IS NULL)",
            #        "OR (NOT exam.ete_exam AND ey.id = %(ey_pk)s::INT))"
            "AND ((exam.ete_exam AND ey.code = %(ey_code)s::INT)",
                    "OR (NOT exam.ete_exam AND ey.id = %(ey_pk)s::INT))"

           "AND ((exam.ete_exam AND ey.code = %(ey_code)s::INT)",
            "OR (NOT exam.ete_exam AND ey.id = %(ey_pk)s::INT))"

        ]

    # when school: only ETE published exams (DUO exams are not published)
        if req_usr.role == c.ROLE_008_SCHOOL:
            sql_list.append("AND (exam.published_id IS NOT NULL OR NOT exam.ete_exam)")

        if exam_pk_list:
            sql_keys['pk_arr'] = exam_pk_list
            sql_list.append("AND exam.id IN ( SELECT UNNEST( %(pk_arr)s::INT[]))")

        elif setting_dict:
            sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)
            if sel_lvlbase_pk:
                sql_keys['lvlbase_pk'] = sel_lvlbase_pk
                sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

            if logging_on:
                logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))

        sql_list.append("ORDER BY exam.id")

        sql = ' '.join(sql_list)
        if logging_on and False:
            logger.debug('    sql_keys: ' + str(sql_keys))
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            all_exam_rows = af.dictfetchall(cursor)

            if logging_on and False:
                for conn_query in connection.queries:
                    sql_str = conn_query.get('sql')
                    if sql_str and "SELECT exam.id, exam.subject_id" in sql_str:
                        logger.debug('conn_query: ' + str(conn_query))

            if all_exam_rows:
                if logging_on:
                    logger.debug('count: ' + str(len(all_exam_rows)))

                for row in all_exam_rows:
                    exam_id = row.get('id')
                    if logging_on:
                        logger.debug( ' '.join(('  >',
                                    str(exam_id),
                                    str(row.get('subj_name_nl')),
                                     str(row.get('depbase_code')),
                                     str(row.get('lvl_abbrev')),
                                     str(row.get('level_id')),
                                     str(row.get('has_duo_exams'))
                                                )))

                    row['exam_name'] = get_exam_name(
                        ce_exam_id=exam_id,
                        ete_exam=row.get('ete_exam'),
                        subj_name_nl=row.get('subj_name_nl'),
                        depbase_code=row.get('depbase_code'),
                        lvl_abbrev=row.get('lvl_abbrev'),
                        examperiod=row.get('examperiod'),
                        examyear=sel_examyear,
                        version=row.get('version'),
                        ntb_omschrijving=row.get('ntb_omschrijving')
                    )

    # - add messages to first exam_row, only when exam_pk exists
            if exam_pk_list and len(exam_pk_list) == 1 and all_exam_rows:
                # when exam_pk has value there is only 1 row
                row = all_exam_rows[0]
                if row:
                    for key, value in append_dict.items():
                        row[key] = value

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
    return all_exam_rows
# --- end of create_all_exam_rows


def create_ete_exam_rows(req_usr, sel_examyear, sel_depbase, append_dict, setting_dict=None, show_all=False, exam_pk_list=None):
    # --- create rows of all exams of this examyear  PR2021-04-05  PR2022-01-23 PR2022-02-23 PR2022-05-13  PR2022-06-02
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_ete_exam_rows ============= ')
        logger.debug('    sel_examyear: ' + str(sel_examyear))
        logger.debug('    sel_depbase: ' + str(sel_depbase))
        logger.debug('    show_all: ' + str(show_all))
        logger.debug('    exam_pk_list: ' + str(exam_pk_list))
        logger.debug('    append_dict: ' + str(append_dict))

    # PR2022-05-13 debug: Raymond Romney MPC: cannot open exam.
    # cause: exams were filtered by examyear.pk, SXM has different examyear.pk from CUR
    # solved by: filter by examyear.code instead of examyear.pk

    # PR2022-06-02 tel Lavern SMAC: has sp DUO
    # try solving by filtering on examyear.pk when ETE/DOE logs in

    # - when user is school: only show published exams

    # PR2022-06-23
    # --- creates rows with exams that:
    # - are exam.ete_exam
    # - this department
    # - this examyear_code i.e Sxm also sees Cur ETE exams
    # - if not role = admin:
    #       - only shows published ETE exams

    selected_depbase = sel_depbase if not show_all else None

    sel_depbase_pk = sel_depbase.pk if sel_depbase else 0
    sel_ey_code = sel_examyear.code if sel_examyear else 0

    sql_keys = {'ey_code': sel_ey_code, 'depbase_id': sel_depbase_pk}

    sql_list = [
        "SELECT ex.id, ex.subject_id AS subj_id, subj.base_id AS subjbase_id, subj.examyear_id AS subj_examyear_id,",
        "CONCAT('exam_', ex.id::TEXT) AS mapid,",
        "CONCAT(subj.name_nl,",
            "CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' - ', lvl.abbrev) END,",
            "CASE WHEN ex.version IS NULL OR ex.version = '' THEN NULL ELSE CONCAT(' - ', ex.version) END ) AS exam_name,",

        "ex.ete_exam, ex.examperiod, ex.department_id, depbase.id AS depbase_id, depbase.code AS depbase_code, dep.sequence AS dep_sequence,",
        "ex.level_id, lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev, lvl.sequence AS lvl_sequence,",
        "ex.version, ex.has_partex, ex.partex, ex.assignment, ex.keys, ex.amount, ex.blanks,",
        "ex.nex_id, ex.scalelength, ex.cesuur, ex.nterm, ex.secret_exam,",
        "ex.datum, ex.begintijd, ex.eindtijd, ex.has_errata, ex.subject_color,",

        "ex.status, ex.auth1by_id, ex.auth2by_id, ex.published_id, ex.locked, ex.modifiedat,",

        "ex.cesuur_auth1by_id, ex.cesuur_auth2by_id, ex.cesuur_published_id,",

        "sb.code AS subjbase_code, subj.name_nl AS subj_name_nl, subj.name_en AS subj_name_en, subj.name_pa AS subj_name_pa,",
        "bundle.id AS bundle_id, bundle.name AS bundle_name,"
        "ey.id AS ey_id, ey.code AS ey_code, ey.locked AS ey_locked,",
        "au.last_name AS modby_username,",

        "auth1.last_name AS auth1_usr, auth2.last_name AS auth2_usr, publ.modifiedat AS publ_modat",

        "FROM subjects_exam AS ex",
        "INNER JOIN subjects_subject AS subj ON (subj.id = ex.subject_id)",
        "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

        "INNER JOIN schools_department AS dep ON (dep.id = ex.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = ex.level_id)",
        "LEFT JOIN subjects_envelopbundle AS bundle ON (bundle.id = ex.envelopbundle_id)",

        "LEFT JOIN accounts_user AS auth1 ON (auth1.id = ex.auth1by_id)",
        "LEFT JOIN accounts_user AS auth2 ON (auth2.id = ex.auth2by_id)",
        "LEFT JOIN schools_published AS publ ON (publ.id = ex.published_id)",

        "LEFT JOIN accounts_user AS au ON (au.id = ex.modifiedby_id)",
        "WHERE ex.ete_exam",
        "AND ey.code = %(ey_code)s::INT",
    ]


# - only show exams that are published when user is not role_admin
    if not req_usr.is_role_admin:
        sql_list.append("AND ex.published_id IS NOT NULL")

# skip other filters when exam_pk_list has value

    if exam_pk_list:
        sql_keys['pk_arr'] = exam_pk_list
        sql_list.append("AND ex.id IN (SELECT UNNEST( %(pk_arr)s::INT[]))")

    elif not show_all:
        if sel_depbase_pk:
            # PR2022-08-11 show ete_exams of all deps in page orderlist
            sql_list.append("AND depbase.id = %(depbase_id)s::INT")

        if setting_dict:
            sel_examperiod = setting_dict.get(c.KEY_SEL_EXAMPERIOD)
            if sel_examperiod in (1, 2, 3):
                sql_keys['ep'] = sel_examperiod
                sql_list.append("AND (ex.examperiod = %(ep)s::INT)")

            sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)
            if sel_lvlbase_pk:
                sql_keys['lvlbase_pk'] = sel_lvlbase_pk
                sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

    sql_list.append("ORDER BY ex.id")

    sql = ' '.join(sql_list)
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))
        logger.debug('sql: ' + str(sql))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        ete_exam_rows = af.dictfetchall(cursor)

# - add messages to exam_row
    if ete_exam_rows and exam_pk_list and append_dict:
        # append_dict has keys with exam_pk
        # append_dict: {506: {'created': True}}
        for row in ete_exam_rows:
            exam_pk = row.get('id')
            if exam_pk in append_dict:
                app_dict = append_dict[exam_pk]
                for key, value in app_dict.items():
                    row[key] = value

    return ete_exam_rows
# --- end of create_ete_exam_rows


def create_duo_exam_rows(req_usr, sel_examyear, sel_depbase, sel_lvlbase, sel_examperiod, append_dict, exam_pk_list=None):
    # PR2022-04-06 PR2022-06-02
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_duo_exam_rows ============= ')
        logger.debug('    sel_examyear: ' + str(sel_examyear))
        logger.debug('    sel_depbase: ' + str(sel_depbase))
        logger.debug('    sel_lvlbase: ' + str(sel_lvlbase))
        logger.debug('    sel_examperiod: ' + str(sel_examperiod))
        logger.debug('    exam_pk_list: ' + str(exam_pk_list) + ' ' + str(type(exam_pk_list)))
        logger.debug('    append_dict: ' + str(append_dict))

    # PR2022-05-13 debug: Raymond Romney MPC: cannot open exam.
    # cause: exams were filtered by examyear.pk, SXM has different examyear.pk from CUR
    # solved by: filter by examyear.code instead of examyear.pk

    # PR2022-06-02 tel Lavern SMAC: has sp DUO
    # try solving by filtering on examyear.pk when ETE/DOE logs in

    # PR2022-06-23
    # --- creates rows with exams that:
    # - are not exam.ete_exam
    # - this department
    # - when role = school:
    #       - this examyear_code i.e both exams of Cur and Sxm are showing
    # - when role = admin:
    #       - this examyear_pk i.e only exams of Cur or Sxm are showing

    # PR 2023-04-21 error: column "none" does not exist
    # LINE 1: ...ND exam.id IN (SELECT UNNEST(ARRAY[461, 458, 455, None]::INT...
    # exam_pk_list contains 'None'

    duo_exam_rows = []
    if sel_examyear and sel_depbase and sel_examperiod:
        sql_list = [
            "SELECT exam.id, exam.subject_id AS subj_id, subj.base_id AS subjbase_id, subj.examyear_id AS subj_examyear_id,",
            "CONCAT('exam_', exam.id::TEXT) AS mapid,",

            #"CONCAT(subj.name_nl,",
            #"CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' - ', lvl.abbrev) END,",
            #"CASE WHEN exam.version IS NULL OR exam.version = '' THEN NULL ELSE CONCAT(' - ', exam.version) END ) AS exam_name,",

            "CONCAT('N', ntb.id, 'D', dep.id, 'S', subj.id, 'L', lvl.id) AS ndsl_pk,",
            "exam.examperiod, exam.department_id AS dep_id, depbase.id AS depbase_id, depbase.code AS depbase_code,",
            "exam.level_id AS lvl_id, lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev,",
            "exam.version, exam.nex_id, exam.scalelength, exam.nterm, exam.ete_exam, exam.secret_exam,",

            "sb.code AS subjbase_code, subj.name_nl AS subj_name_nl, subj.name_en AS subj_name_en, subj.name_pa AS subj_name_pa,",

            "ey.id AS ey_id, ey.code AS ey_code, ey.locked AS ey_locked,",

            "ntb.id AS ntb_id, ntb.nex_id AS ntb_nex_id, ntb.leerweg AS ntb_leerweg,",
            "ntb.tijdvak AS ntb_tijdvak, ntb.omschrijving AS ntb_omschrijving, ntb.schaallengte AS ntb_schaallengte, ntb.n_term AS ntb_nterm,",
            "ntb.datum AS ntb_datum,"
    
            "exam.status, exam.auth1by_id, exam.auth2by_id, exam.published_id, exam.locked, exam.modifiedat,",
            "au.last_name AS modby_username,",

            "auth1.last_name AS auth1_usr, auth2.last_name AS auth2_usr, publ.modifiedat AS publ_modat",

            "FROM subjects_exam AS exam",
            "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
            "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

            "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

            "LEFT JOIN subjects_ntermentable AS ntb ON (ntb.id = exam.ntermentable_id)",

            "LEFT JOIN accounts_user AS auth1 ON (auth1.id = exam.auth1by_id)",
            "LEFT JOIN accounts_user AS auth2 ON (auth2.id = exam.auth2by_id)",
            "LEFT JOIN schools_published AS publ ON (publ.id = exam.published_id)",

            "LEFT JOIN accounts_user AS au ON (au.id = exam.modifiedby_id)",

            "WHERE NOT exam.ete_exam AND depbase.id = " + str(sel_depbase.pk) + "::INT",
        ]

        # show all when sel_examperiod = -1 or None PR2023-04-02
        if sel_examperiod in (c.EXAMPERIOD_FIRST, c.EXAMPERIOD_SECOND, c.EXAMPERIOD_THIRD):
            sql_list.append(''.join(("AND exam.examperiod=", str(sel_examperiod), "::INT")))

        if req_usr.role == c.ROLE_008_SCHOOL:
            sql_list.append(''.join(("AND ey.code = ", str(sel_examyear.code), "::INT")))
        else:
            sql_list.append(''.join(("AND ey.id = ", str(sel_examyear.pk), "::INT")))

        if exam_pk_list:
            sql_list.append(''.join(("AND exam.id IN (SELECT UNNEST(ARRAY", str(exam_pk_list), "::INT[]))")))

        if sel_lvlbase:
            sql_list.append(''.join(("AND lvl.base_id = ", str(sel_lvlbase.pk), "::INT")))

        sql_list.append("ORDER BY exam.id")

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql)
            duo_exam_rows = af.dictfetchall(cursor)
            if duo_exam_rows:
                for row in duo_exam_rows:
                    exam_pk = row.get('id')
                    row['exam_name'] = get_exam_name(
                        ce_exam_id=exam_pk,
                        ete_exam=row.get('ete_exam'),
                        subj_name_nl=row.get('subj_name_nl'),
                        depbase_code=row.get('depbase_code'),
                        lvl_abbrev=row.get('lvl_abbrev'),
                        examperiod=row.get('examperiod'),
                        examyear=sel_examyear,
                        version=row.get('version'),
                        ntb_omschrijving=row.get('ntb_omschrijving')
                    )

# - add messages to exam_rows, only when student_pk or grade_pk_list have value PR2023-03-20
                if append_dict and exam_pk_list:
                    if logging_on:
                        logger.debug('......... ')
                        logger.debug('append_dict: ' + str(append_dict))

                    exam_append_dict = append_dict.get(exam_pk)
                    if exam_append_dict:
                        for key, value in exam_append_dict.items():
                            row[key] = value

    if logging_on:
        logger.debug('duo_exam_rows: ' + str(duo_exam_rows))

    return duo_exam_rows
# --- end of create_duo_exam_rows


def create_duo_or_ete_subject_rows(sel_examyear, sel_depbase, sel_lvlbase, create_duo_rows):
    # PR2022-02-23 PR2022-06-23 PR2023-03-18
    # --- create rows with subjects that:
    # - are not si.ete_exam (set in schemeitem, can be different in Cur and Sxm)
    # - have si.weight_ce > 0"
    # - this examyear_pk, this means that only subjects of Cur or Sxm are showing
    # - this department
    # - sel_lvlbase, if sel_lvlbase has value

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_duo_or_ete_subject_rows ============= ')
        logger.debug('    sel_examyear: ' + str(sel_examyear))
        logger.debug('    sel_depbase: ' + str(sel_depbase))
        logger.debug('    sel_lvlbase: ' + str(sel_lvlbase))

    duo_subject_rows=[]

    if sel_examyear and sel_depbase:
        sql_list = [
            "SELECT subj.id, subj.base_id AS subjbase_id,",
            "sb.code, subj.name_nl,",
            "lvl.id AS lvl_id, lvl.abbrev AS lvl_abbrev, lvl.base_id AS lvlbase_id,",
            "dep.id AS dep_id, depbase.id AS depbase_id, depbase.code AS depbase_code",

            "FROM subjects_schemeitem AS si",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
            "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

            "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",

            # PR2022-05-19 added: AND si.weight_ce > 0", because subjects without CE were showing
            "WHERE si.weight_ce > 0",

            # PR2023-05-05 added: return either ete or duo subjects
            # Note: in not all sectors have same ete_exam value, subjects appears both in ETE and DUO subjects
            "AND NOT si.ete_exam" if create_duo_rows else "AND si.ete_exam",

            ''.join(("AND ey.id=", str(sel_examyear.pk), "::INT")),
            ''.join(("AND depbase.id=", str(sel_depbase.pk), "::INT"))
        ]

        if sel_lvlbase:
            sql_list.append(''.join(("AND lvl.base_id=", str(sel_lvlbase.pk), "::INT")))

        sql_list.append("GROUP BY subj.id, subj.base_id, sb.code, subj.name_nl, lvl.id, lvl.abbrev, dep.id, depbase.id, depbase.code")

        if logging_on:
            for sql_txt in sql_list:
                logger.debug(' > ' + str(sql_txt))

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql)
            duo_subject_rows = af.dictfetchall(cursor)

        if logging_on:
            for row in duo_subject_rows:
                logger.debug(' row: ' + str(row))

    return duo_subject_rows
# --- end of create_duo_or_ete_subject_rows


def create_ntermentable_rows(sel_examyear, sel_depbase, setting_dict):
    # --- create rows of all exams of this examyear  PR2021-04-05  PR2022-01-23 PR2022-02-23 PR2022-12-16
    logging_on = False  #  s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_ntermentable_rows ============= ')
    # sty_id 1 = vwo, 2 = havo, 3 = vmbo
    sty_id = None
    if sel_depbase and sel_depbase.code:
        sel_depbase_code_lower = sel_depbase.code.lower()
        if sel_depbase_code_lower == 'vsbo':
            sty_id = 3
        elif sel_depbase_code_lower == 'havo':
            sty_id = 2
        elif sel_depbase_code_lower == 'vwo':
            sty_id = 1
    # - only show published exams when user is school
    # PR2023-05-05 debug: ntermentable rows are shown double bexcause its is filtered by ey_code instead of ey_pk
    # was: sql_keys = {'ey_code': sel_examyear.code, 'sty_id': sty_id}
    sql_keys = {'ey_pk': sel_examyear.pk, 'sty_id': sty_id}


    sql_list = [
        "SELECT nt.id, nt.nex_id, nt.sty_id, nt.opl_code, nt.leerweg, nt.ext_code, nt.tijdvak,"
        "nt.omschrijving, nt.schaallengte, nt.n_term, nt.afnamevakid, nt.extra_vakcodes_tbv_wolf,",
        "nt.datum, nt.begintijd, nt.eindtijd",

        "FROM subjects_ntermentable AS nt",
        "INNER JOIN schools_examyear AS ey ON (ey.id = nt.examyear_id)",
        # was: "WHERE ey.code = %(ey_code)s::INT AND nt.sty_id = %(sty_id)s::INT"
        "WHERE ey.id = %(ey_pk)s::INT AND nt.sty_id = %(sty_id)s::INT"
    ]
    if setting_dict:
        sel_examperiod = setting_dict.get(c.KEY_SEL_EXAMPERIOD)
        if sel_examperiod == 1:
            sql_list.append("AND nt.tijdvak = 1")
        elif sel_examperiod == 2:
            sql_list.append("AND (nt.tijdvak = 2 OR nt.tijdvak = 3)")

        sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)
        if sel_lvlbase_pk:
            sel_lvlbase_code = setting_dict.get('sel_lvlbase_code')
            if sel_lvlbase_code == 'TKL':
                sql_list.append("AND nt.leerweg = 'GL/TL'")
            elif sel_lvlbase_code == 'PKL':
                sql_list.append("AND nt.leerweg = 'KB'")
            elif sel_lvlbase_code == 'PBL':
                sql_list.append("AND nt.leerweg = 'BB'")

    sql_list.append("ORDER BY nt.id")
    sql = ' '.join(sql_list)
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        ntermentable_rows = af.dictfetchall(cursor)

    return ntermentable_rows
# --- end of create_ete_exam_rows


def calc_total():
    # --- creates possible sums of list with max_scores and occurrencies
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== calc_total ============= ')

    maxscore_list = [(18, 2), (34, 1), (27, 4)]
    if logging_on:
        logger.debug('maxscore_list: ' + str(maxscore_list))

    # use list to get reference instead of value
    used_score_str = ""
    total_score_dict = {}
    total_score = 0
    list_index = len(maxscore_list) -1

    calc_recursive(maxscore_list, total_score_dict, used_score_str, total_score, list_index)


    if logging_on:
        logger.debug('total_score_list: ' + str(total_score_dict))

    return total_score_dict
# --- end of calc_total


def calc_recursive(maxscore_list, total_score_dict, used_score_str, total_score, list_index):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calc_recursive  ----- list_index: ' + str(list_index))
        logger.debug('total_score: ' + str(total_score))
        logger.debug('used_score_str: ' + str(used_score_str))

    if list_index >= 0:
        tuple_at_index = maxscore_list[list_index]
        max_score = tuple_at_index[0]
        occurrencies = tuple_at_index[1]
        if logging_on:
            logger.debug('     max_score: ' + str(max_score) + ' occurrencies: ' + str(occurrencies))

        new_listindex = list_index - 1
        this_used_score_str = used_score_str
        # loop through number of occurrencies
        for multiplier in range(0, occurrencies + 1, 1):  # range(start_value, end_value, step), end_value is not included!
            new_total_score = total_score + max_score * multiplier
            if multiplier:
                new_used_score_str = ';'.join((this_used_score_str, str(max_score)))
            else:
                new_used_score_str = this_used_score_str
            if logging_on:
                logger.debug('..... for multiplier = ' + str(multiplier))
                logger.debug('     new_total_score: ' + str(new_total_score))

            calc_recursive(maxscore_list, total_score_dict, new_used_score_str, new_total_score, new_listindex)

            if logging_on:
                logger.debug('..... end of for multiplier = ' + str(multiplier))
    else:
        if total_score:
            used_score_arr = []
            if used_score_str:
                used_score_str = used_score_str[1:]
                arr = used_score_str.split(';')
                if len(arr):
                    for score_str in arr:
                        used_score_arr.append(int(score_str))
                    used_score_arr.sort()

            total_score_dict[total_score] = used_score_arr

        if logging_on:
            logger.debug('     end of recurrencies ')
            logger.debug('     total_score_dict: ' + str(total_score_dict))
            logger.debug('-----  end of calc_recursive')
# - end of calc_recursive


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def delete_subject_instance(subject_instance, request):
    # --- delete subject # PR2021-05-14 PR2021-07-18 PR2022-02-16 PR2022-08-05

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_subject_instance ----- ')
        logger.debug('subject_instance: ' + str(subject_instance))

    deleted_row = None
    msg_html = None

    base_pk = subject_instance.base.pk

    this_txt = _("Subject '%(tbl)s'") % {'tbl': subject_instance.name_nl}

# - check if there are students with this subject
    students_with_this_subject_exist = stud_mod.Studentsubject.objects.filter(
        schemeitem__subject=subject_instance
    ).exists()
    if logging_on:
        logger.debug('students_with_this_subject_exist: ' + str(students_with_this_subject_exist))

    if students_with_this_subject_exist:
        msg_html = '<br>'.join((
            str(_('There are candidates with this subject.')),
            str(_("%(cpt)s could not be deleted.") % {'cpt': this_txt})
        ))

    else:
        # delete subject will also cascade delete Schemeitem, Exam and Cluster
        deleted_row, err_html = sch_mod.delete_instance(
            table='subject',
            instance=subject_instance,
            request=request,
            this_txt=this_txt
        )
        if err_html:
            msg_html = err_html
        else:

    # - check if this subject also exists in other examyears.
            subject_exists = subj_mod.Subject.objects.filter(
                base_id=base_pk
            ).exists()
    # If not: delete also subject_base
            if not subject_exists:
                subject_base = subj_mod.Subjectbase.objects.get_or_none(
                    id=base_pk
                )
                if subject_base:
                    subject_base.delete()

    if logging_on:
        logger.debug('deleted_row' + str(deleted_row))
        logger.debug('msg_html' + str(msg_html))

    return deleted_row, msg_html
# - end of delete_subject_instance


def create_subject(examyear, upload_dict, request):
    # --- create subject # PR2019-07-30 PR2020-10-11 PR2021-05-13 PR2021-06-22 PR2022-08-14
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_subject ----- ')
        logger.debug('examyear: ' + str(examyear))
        logger.debug('upload_dict: ' + str(upload_dict))

    subject_instance = None
    error_list = []

    if examyear:

# - get values
        code = upload_dict.get('code')
        name_nl = upload_dict.get ('name_nl')

        sequence = upload_dict.get ('sequence', 9999)
        depbases = upload_dict.get('depbases')
        if logging_on:
            logger.debug('code: ' + str(code))
            logger.debug('name_nl: ' + str(name_nl))
            logger.debug('sequence: ' + str(sequence))
            logger.debug('depbases: ' + str(depbases) + str(type(depbases)))

# - validate code and name. Function checks null, max_len, exists
        msg_err = av.validate_notblank_maxlength(code, c.MAX_LENGTH_SCHOOLCODE, _('The abbreviation'))
        if msg_err:
            error_list.append(msg_err)

        msg_err = av.validate_notblank_maxlength(name_nl, c.MAX_LENGTH_NAME, _('The name in Dutch'))
        if msg_err:
            error_list.append(msg_err)

# - check if subject code already exists
        msg_err = av.validate_subject_code_exists(code)
        if msg_err:
            error_list.append(msg_err)

# - check if subject name already exists
        msg_err = av.validate_subject_name_exists(
            field='name_nl',
            new_value=name_nl,
            examyear=examyear
        )
        if msg_err:
            error_list.append(msg_err)

# - create and save subject
        if not error_list:
            try:
                # First create base record. base.id is used in Subject. Create also saves new record
                base = sbj_mod.Subjectbase.objects.create(
                    code=code
                )
# - create and save subject
                subject_instance = sbj_mod.Subject(
                    base=base,
                    examyear=examyear,
                    name_nl=name_nl,
                    sequence=sequence,
                    depbases=depbases
                )
                subject_instance.save(request=request)

            except Exception as e:
                subject_instance = None
                logger.error(getattr(e, 'message', str(e)))

                error_list.append(''.join((
                    str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                    str(_("%(cpt)s '%(val)s' could not be added.") % {'cpt': _('Subject'), 'val': name_nl})
                )))

    if logging_on:
        logger.debug('subject_instance: ' + str(subject_instance))
        logger.debug('error_list: ' + str(error_list))

    return subject_instance, error_list
# - end of create_subject


def update_subject_instance(subject_instance, examyear, upload_dict, request):
    # --- update existing and new instance PR2019-06-06 PR2021-05-10
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_subject_instance -----')
        logger.debug('upload_dict: ' + str(upload_dict))

    error_list = []
    if subject_instance:
        save_changes = False
        save_changes_in_base = False

        for field, new_value in upload_dict.items():
            if field in ('code', 'name_nl', 'name_en', 'name_pa', 'depbases', 'sequence'):
                if logging_on:
                    logger.debug('field: ' + str(field))
                    logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))

    # - save changes in field 'code'
                if field == 'code':
                    base = subject_instance.base
                    saved_value = getattr(base, field)
                    if logging_on:
                        logger.debug('saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))

                    if new_value != saved_value:
                        if logging_on:
                            logger.debug('new_value != saved_value')
        # - validate abbrev checks null, max_len, exists
                        #  msg_err = { 'field': 'code', msg_list: [text1, text2] }, (for use in imput modals)
                        msg_html = av.validate_subject_code_exists(
                            code=new_value,
                            cur_subject=subject_instance
                        )
                        if msg_html:
                            error_list.append(msg_html)
                        else:
         # - save field if changed and no_error
                            setattr(base, field, new_value)
                            save_changes_in_base = True

    # - save changes in field 'name_nl'
                elif field in ('name_nl', 'name_en', 'name_pa'):
                    saved_value = getattr(subject_instance, field)

                    caption = _('Subject name in Papiamentu') if field == 'name_pa' \
                        else _('Subject name in English') if field == 'name_en' \
                        else _('Subject name in Dutch')
                    blank_allowed = (field in ('name_en', 'name_pa'))

                    msg_err = av.validate_notblank_maxlength(
                        value=new_value,
                        max_length=c.MAX_LENGTH_NAME,
                        caption=caption,
                        blank_allowed=blank_allowed
                    )

                    if msg_err:
                        error_list.append(msg_err)
                    else:

                        if new_value != saved_value:
            # - validate exists
                            # PR2022-09-06 Pien v Dijk: cannot delete subj name, error: Naam van het vak in het Papiaments 'None' komt al voor.
                            # solved by adding: if new_value is not None:
                            msg_html = None
                            if new_value is not None:
                                msg_html = av.validate_subject_name_exists(
                                    field=field,
                                    new_value=new_value,
                                    examyear=examyear,
                                    cur_subject=subject_instance
                                )
                            if msg_html:
                                error_list.append(msg_html)
                            else:
                                # - save field if changed and no_error
                                setattr(subject_instance, field, new_value)
                                save_changes = True

    # - save changes in depbases
                elif field == 'depbases':
                    saved_value = getattr(subject_instance, field)
                    uploaded_field_arr = new_value.split(';') if new_value else []

                    checked_field_arr = []
                    checked_field_str = None
                    if uploaded_field_arr:
                        for base_pk_str in uploaded_field_arr:
                            base_pk_int = int(base_pk_str)
                            base_instance = sch_mod.Department.objects.get_or_none(
                                base=base_pk_int,
                                examyear=examyear
                            )
                            if base_instance:
                                checked_field_arr.append(base_pk_str)

                        if checked_field_arr:
                            checked_field_arr.sort()
                            checked_field_str = ';'.join(checked_field_arr)
                    if checked_field_str != saved_value:
                        setattr(subject_instance, field, new_value)
                        save_changes = True

    # - save changes in sequence
                elif field == 'sequence':
                    saved_value = getattr(subject_instance, field)
                    if new_value != saved_value:
                        setattr(subject_instance, field, new_value)
                        save_changes = True
# --- end of for loop ---

# 5. save changes
        if save_changes or save_changes_in_base:
            try:
                if save_changes_in_base:
                    # also save instance when base has changed, to update modifiedat and modifiedby
                    subject_instance.base.save()
                subject_instance.save(request=request)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred')), ':<br>&emsp;<i>', str(e), '</i><br>',
                                    str(_('The changes have not been saved.'))))
                error_list.append(msg_html)

    return error_list
# - end of update_subject_instance

# >>>>>>>  SCHEMEITEM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def create_schemeitem(examyear, scheme, subj_pk, sjtp_pk, messages, request):
    # --- create schemeitem # PR2021-06-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_schemeitem ----- ')

    schemeitem = None

    has_error = False
    message_header = str(_('Create subject scheme subject'))
    subject = subj_mod.Subject.objects.get_or_none(
        pk=subj_pk,
        examyear=examyear
    )
    if subject is None:
        has_error = True
        messages.append({'class': "border_bg_invalid",
                         'header': message_header,
                         'msg_list': [str(_('Subject not found.'))]})

    subjecttype = subj_mod.Subjecttype.objects.get_or_none(
        pk=sjtp_pk,
        scheme=scheme
    )
    if subjecttype is None:
        has_error = True
        messages.append({'header': message_header,
                         'class': "border_bg_invalid",
                         'msg_html': str(_('Subject type not found.'))})
    if not has_error:
# - create and save schemeitem
        try:
            schemeitem = sbj_mod.Schemeitem(
                scheme=scheme,
                subject = subject,
                subjecttype = subjecttype
            )
            schemeitem.save(request=request)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            msg_html = [': '.join((str(_('An error occurred')),str(e))),
                        str(_("Subject scheme subject '%(val)s' could not be created.") % {'val': subject.name_nl})]

            messages.append(
                {'class': "border_bg_invalid", 'header': message_header, 'msg_html': msg_html})

    if logging_on:
        logger.debug('schemeitem: ' + str(schemeitem))
        logger.debug('messages: ' + str(messages))

    return schemeitem

# - end of create_schemeitem


def delete_schemeitem(schemeitem_instance, request):
    # --- delete schemeitem # PR2021-06-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_schemeitem ----- ')
        logger.debug('schemeitem_instance: ' + str(schemeitem_instance))

    deleted_row = None
    msg_html = None

    this_txt = _("Subject '%(tbl)s' of subject scheme '%(tbl)s'") % {'tbl': schemeitem_instance.subject.name_nl}

# check if there are students with subjects with this schemeitem
    students_with_this_schemeitem_exist = stud_mod.Studentsubject.objects.filter(
        schemeitem=schemeitem_instance
    ).exists()
    if logging_on:
        logger.debug('students_with_this_schemeitem_exist: ' + str(students_with_this_schemeitem_exist))

    if students_with_this_schemeitem_exist:
        msg_html = '<br>'.join((
            str(_('There are candidates with subjects with this schemeitem.')),
            str(_("%(cpt)s could not be deleted.") % {'cpt': this_txt})
        ))

    else:
        # delete schemeitem will also cascade delete Packageitem (not in use yet)
        deleted_row, err_html = sch_mod.delete_instance(
            table='schemeitem',
            instance=schemeitem_instance,
            request=request,
            this_txt=this_txt
        )
        if err_html:
            msg_html = err_html

    if logging_on:
        logger.debug('deleted_row' + str(deleted_row))
        logger.debug('msg_html' + str(msg_html))

    return deleted_row, msg_html
# - end of delete_schemeitem


def update_si_list(examyear, scheme, si_list, updated_rows, messages, request):
    # --- add or delete schemeitem # PR2021-06-26 PR2022-08-07
    # si_list is created when adding or deleting si in mod_schemeitem
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_si_list ----- ')
        logger.debug('si_list: ' + str(si_list))

# ++++ loop through list of schemeitems:
    for si_dict in si_list:
        schemeitem_instance = None
        is_create = si_dict.get('create')
        is_delete = si_dict.get('delete')

        append_dict = {}

# ++++ Create new schemeitem:
        if is_create:
            subj_pk = si_dict.get('subj_pk')
            sjtp_pk = si_dict.get('sjtp_pk')
            schemeitem_instance = create_schemeitem(examyear, scheme, subj_pk, sjtp_pk, messages, request)
            if schemeitem_instance:
                append_dict['created'] = True

# ++++ Delete schemeitem
        elif is_delete:

# +++  get schemeitem:
            si_pk = si_dict.get('si_pk')
            schemeitem_instance = sbj_mod.Schemeitem.objects.get_or_none(
                id=si_pk,
                scheme=scheme
            )
            if logging_on:
                logger.debug('..... schemeitem_instance: ' + str(schemeitem_instance))

            if schemeitem_instance:
                deleted_row, err_html = delete_schemeitem(schemeitem_instance, request)
                if err_html:
                    header_txt = _("Delete subject from subject scheme")
                    messages.append(
                        {'header': str(header_txt),
                         'class': "border_bg_invalid",
                         'msg_html': err_html}
                    )
                elif deleted_row:
                    schemeitem_instance = None
                    updated_rows.append(deleted_row)

                if logging_on:
                    logger.debug('    deleted_row: ' + str(deleted_row))
                    logger.debug('    err_html: ' + str(err_html))


# - create schemeitem_rows[0], also when deleting failed (when deleted ok there is no subject, subject_row is made above)
        if schemeitem_instance:
            schemeitem_rows = create_schemeitem_rows(
                sel_examyear=examyear,
                append_dict=append_dict,
                schemeitem_pk=schemeitem_instance.pk,
                skip_notatdayschool=True
            )
            if schemeitem_rows:
                updated_rows.append(schemeitem_rows[0])
# - end of update_si_list


def update_schemeitem_instance(instance, examyear, upload_dict, updated_rows, request):
    # --- update existing and new instance PR2021-06-26
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_schemeitem_instance -----')
        logger.debug('upload_dict: ' + str(upload_dict))
    error_list = []
    if instance:
        save_changes = False
        msg_header_txt = _("Edit subject of subject scheme")
        # TODO when no_ce_years has changed after school have entered grades, recalc endgrade should be run on all grades
        # probably also when other fields have changed ('gradetype', 'weight_se', 'weight_ce')
        for field, new_value in upload_dict.items():

            if logging_on:
                logger.debug('field: ' + str(field))
            if field in ('gradetype', 'weight_se', 'weight_ce', 'multiplier', 'is_mandatory', 'is_mand_subj', 'is_combi',
                         'extra_count_allowed', 'extra_nocount_allowed',
                         'has_practexam', 'is_core_subject', 'is_mvt', 'is_wisk',
                         'studyloadhours', 'notatdayschool',
                         # not in use: "rule_final_vsbo", "rule_finalvsbo_notatevlex",
                         # not in use: "rule_final_havovwo", "rule_finalhavovwo_notatevlex",
                         "rule_avg_pece_sufficient", "rule_avg_pece_notatevlex",
                         "rule_grade_sufficient", "rule_gradesuff_notatevlex",
                         "rule_core_sufficient", "rule_core_notatevlex",

                         'ete_exam', 'otherlang',
                         'sr_allowed', 'no_ce_years', 'thumb_rule'):

                saved_value = getattr(instance, field)
                if logging_on:
                    logger.debug('    field: ' + str(field))
                    logger.debug('    new_value: <' + str(new_value) + '> ' + str(type(new_value)))
                    logger.debug('    saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))

                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True
                    # TODO 2022-09-13
                    # PR2022-09-13 mail Nancy Josephina ATC doesn't get final grade in MVT combination suject
                    # caused by CE=1 and is_combi.
                    # set CE=0 when is_combi is set to True
                    #if field == 'is_combi' and new_value:
                    #    setattr(instance,  'weight_ce', 0)

                    # PR2023-09-06 TODO
                    """
                    PR2023-09-06 debug email from Pien vaDijk ETE:
                    Bij de kruiscontrole van de Ex.1-formulieren en de bestellijsten is het volgende opgevallen:
                    Wanneer er een nieuw Ex.-1 formulier ingediend wordt, die de oude moet vervangen, 
                    dan worden de aantallen die veranderd zijn op het nieuwe ex.1-formulier niet aangepast op de bestellijst. 
                    Op de bestellijsten blijven de oude getallen staan:
                    Enkele voorbeelden:
                    •	Skaih op Ex1 staan 11 leerlingen voor Spaans, op de bestellijst staan 4 leerlingen voor Spaans. 
                    
                    answer:                    
                    Ik denk dat er het volgende aan de hand is:
                    De keuze of een vak een ETE of CVTE examen heeft wordt bepaald in het vakschema. 
                    Voor elke afdeling / leerweg / sector / karakter is er een regel.
                    Zoals je ziet in onderstaande afbeelding staat er bij de regels met karakter ‘Overig vak’ geen vinkje bij ETE examen.
                    De kandidaten die Spaans hebben met karakter ‘Overig vak’ komen daarom in de bestellijst bij de CVTE examens terecht.
                    Ik neem aan dat het nooit zal voorkomen dat er binnen een afdeling/leerweg/sector combinatie zowel ETE als CVTEexamens worden afgenomen.
                    Als dat het geval is zou ik een functie kunnen toevoegen die de gekozen optie ETE of CVTE 
                    automatisch bij alle karakters invult of weghaalt.
                    """
                    if field == 'ete_exam':
                        #update_eteexam_in_other_sectors(instance)
                        pass

                    # PR 2022-09-25 TODO to be solved: group by si.ete_exam and si.otherlang goes wrong when sectors of one level have different otherlang PR2022-08-13
                    # when changing otherlang in schemeitem, also change otherlang in other sectors
                    if field == 'otherlang':
                        #update_otherlang_in_other_sectors(instance)
                        pass

                    if logging_on:
                        logger.debug('save_changes: ' + str(save_changes))
# --- end of for loop ---

# +++++ save changes
        if save_changes:
            try:
                instance.save(request=request)
                if logging_on:
                    otherlang = getattr(instance, 'otherlang')
                    logger.debug('    instance: ' + str(instance))
                    logger.debug('    otherlang: ' + str(otherlang))
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred: ')), '<br><i>', str(e), '</i><br>',
                            str(_('The changes have not been saved.'))))
                error_list.append({'header': msg_header_txt, 'class': "border_bg_invalid", 'msg_html': msg_html})

# - end of update_schemeitem_instance

# >>>>>>>>  SCHEME >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def update_scheme_instance(instance, examyear, upload_dict, updated_rows, error_list, request):
    # --- update existing and new instance PR2021-06-27 PR2021-11-28 PR2022-08-01
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_scheme_instance -----')
        logger.debug('upload_dict: ' + str(upload_dict))

    if instance:
        save_changes_in_base = False
        save_changes = False

        msg_header_txt = _('Edit subject scheme')

        for field, new_value in upload_dict.items():

            if logging_on:
                logger.debug('field: ' + str(field))
                logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))

# - save changes in field 'name'
            if field == 'name':
                saved_value = getattr(instance, field)
                if new_value != saved_value:
                    # - validate abbrev checks null, max_len, exists
                    has_error = av.validate_scheme_name_exists(new_value, examyear, error_list, instance)
                    if not has_error:
                        # - save field if changed and no_error
                        setattr(instance, field, new_value)
                        save_changes = True

            elif field in ('rule_avg_pece_sufficient', 'rule_avg_pece_notatevlex',
                            'rule_core_sufficient', 'rule_core_notatevlex'):
                saved_value = getattr(instance, field)
                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

            elif field in ('min_studyloadhours', 'min_subjects', 'max_subjects', 'min_mvt', 'max_mvt',
                           'min_wisk', 'max_wisk', 'min_combi', 'max_combi', 'max_reex'):
                msg_html = None
                new_value_int = None

                if logging_on:
                    logger.debug('..........field: ' + str(field))

                if new_value:
                    # - check if value is positive whole number
                    if not new_value.isdecimal():
                        msg_html = str(_("'%(val)s' is not a valid number.") % {'val': new_value})
                    else:
                        new_value_int = int(new_value)
                        if logging_on:
                            logger.debug('new_value_int: <' + str(new_value_int) + '> ' + str(type(new_value_int)))

                        if field in ('min_subjects', 'min_mvt', 'min_wisk', 'min_combi'):
                            max_field = 'max_mvt' if field == 'min_mvt' else 'max_wisk' if field == 'min_wisk' else 'max_combi' if field == 'min_combi' else 'max_subjects'
                            max_subjects = getattr(instance, max_field)

                            if logging_on:
                                logger.debug('max_subjects: <' + str(max_subjects) + '> ' + str(type(max_subjects)))

                            if max_subjects and new_value_int > max_subjects:
                                msg_html = str(
                                    _("Minimum number of subjects cannot be greater than maximum (%(val)s).") % {
                                        'val': max_subjects})

                        elif field in ('max_subjects', 'max_mvt', 'max_wisk', 'max_combi'):
                            min_field = 'min_mvt' if field == 'max_mvt' else 'min_wisk' if field == 'max_wisk' else 'min_combi' if field == 'max_combi' else 'min_subjects'
                            min_subjects = getattr(instance, min_field)

                            if logging_on:
                                logger.debug('min_subjects: <' + str(min_subjects) + '> ' + str(type(min_subjects)))

                            if min_subjects and new_value_int < min_subjects:
                                msg_html = str(
                                    _("Maximum number of subjects cannot be fewer than minimum (%(val)s).") % {
                                        'val': min_subjects})
                        elif field == 'max_reex':
                            if not new_value_int:
                                msg_html = str(_('%(cpt)s cannot be blank.') % {'cpt': _("Maximum number of re-examinations")})
                            elif new_value_int < 0:
                                msg_html = str(_("Maximum number of re-examinations must be a positive whole number."))
                        elif field == 'min_studyloadhours':
                            if new_value_int < 0:
                                msg_html = str(_("Minimum studyload hours must be a positive whole number."))
                if msg_html:
                    msg_dict = {'field': field,
                                'header': msg_header_txt,
                                'class': 'border_bg_warning',
                                'msg_html': msg_html}
                    error_list.append(msg_dict)
                else:
                    # -note: value can be None, not when max_reex
                    saved_value = getattr(instance, field)
                    if logging_on:
                        logger.debug('saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))
                    if new_value_int != saved_value:
                        setattr(instance, field, new_value_int)
                        save_changes = True
                    if logging_on:
                        logger.debug('..........save_changes: ' + str(save_changes))
        # --- end of for loop ---

        # 5. save changes
        if save_changes or save_changes_in_base:
            try:
                if save_changes_in_base:
                    # also save instance when base has changed, to update modifiedat and modifiedby
                    instance.base.save()
                instance.save(request=request)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred: ')), str(e), '<br>',
                                    str(_('The changes have not been saved.'))))
                error_list.append({'header': msg_header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html})
            else:
# - create schemeitem_rows[0]
                scheme_rows = create_scheme_rows(
                    examyear=examyear,
                    scheme_pk=instance.pk
                )
                if scheme_rows:
                    updated_rows.append(scheme_rows[0])

# - end of update_scheme_instance




# >>>>>>>  SUBJECTTYPE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def update_sjtp_list(examyear, scheme, sjtp_list, updated_rows, messages, request):
    # --- update_sjtp_list # PR2021-06-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_sjtp_list ----- ')
        logger.debug('sjtp_list: ' + str(sjtp_list))

    header_txt = _('Update character')
# ++++ loop through list of subjecttypes:
    for sjtp_dict in sjtp_list:
        subjecttype_instance = None
        append_dict = {}
        is_create = sjtp_dict.get('create')
        is_delete = sjtp_dict.get('delete')

        if is_create:
            sjtpbase_pk = sjtp_dict.get('sjtpbase_pk')
            subjecttype_instance = create_subjecttype(sjtpbase_pk, scheme, sjtp_dict, messages, header_txt, request)
            if subjecttype_instance:
                append_dict['created'] = True

        elif is_delete:

# ++++ Delete subjecttype
# - get existing subjecttype
            sjtp_pk = sjtp_dict.get('sjtp_pk')
            subjecttype_instance = sbj_mod.Subjecttype.objects.get_or_none(
                id=sjtp_pk,
                scheme=scheme
            )
            # delete_subjecttype will set subjecttype to None if deleted_ok
            deleted_row, err_html = delete_subjecttype(subjecttype_instance, request)
            if err_html:
                messages.append(
                    {'header': str(header_txt),
                     'class': "border_bg_invalid",
                     'msg_html': err_html}
                )
            elif deleted_row:
                subjecttype_instance = None
                updated_rows.append(deleted_row)

            if logging_on:
                logger.debug('    deleted_row: ' + str(deleted_row))
                logger.debug('    msg_html: ' + str(err_html))

        if logging_on:
            logger.debug('subjecttype_instance: ' + str(subjecttype_instance))

# - create schemeitem_rows[0], also when deleting failed (when deleted ok there is no subject, subject_row is made above)
        if subjecttype_instance:
            subjecttype_rows = create_subjecttype_rows(
                examyear=examyear,
                append_dict={},
                sjtp_pk=subjecttype_instance.pk,
                cur_dep_only=False
            )
            if logging_on:
                logger.debug('subjecttype_rows: ' + str(subjecttype_rows))

# - messages will be attached to update_wrap, not to updated_rows
            if subjecttype_rows:
                updated_rows.extend(subjecttype_rows)
                if logging_on:
                    logger.debug('updated_rows: ' + str(updated_rows))
# ++++ end of loop

# - end of update_sjtp_list


def create_subjecttype(sjtpbase_pk, scheme, upload_dict, messages, msg_header, request):
    # --- create subjecttype # PR2021-06-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_subjecttype ----- ')

    subjecttype = None
    sjtpbase = None
    msg_header = _('Create character')

    if scheme:
# - get sjtpbase
        sjtpbase = get_subjecttypebase_instance(sjtpbase_pk, messages,
                                        msg_header, logging_on, request)
        if sjtpbase is None:
            msg_html = str(_("Base character not found."))
            msg_dict = {'header': str(msg_header), 'class': 'border_bg_invalid', 'msg_html': msg_html}
            messages.append(msg_dict)
        else:
    # - get values
                name = upload_dict.get ('name')
                if logging_on:
                    logger.debug('name: ' + str(name))

                msg_list = []
                has_error = False
        # - validate code and name. Function checks null, max_len, exists
                msg_html = av.validate_notblank_maxlength(name, c.MAX_LENGTH_NAME, _('The name'))
                if msg_html:
                    msg_list.append(msg_html)

        # - check if subjecttype name already exists

                msg_html = av.validate_subjecttype_name_abbrev_exists('name', name, scheme, subjecttype)
                if msg_html:
                    msg_list.append(msg_html)

        # - create and save subjecttype
                if len(msg_list) > 0:
                    msg_html = '<br>'.join(msg_list)
                    messages.append({'header': str(msg_header), 'class': "border_bg_invalid", 'msg_html': msg_html})
                else:
                    try:
                        # Don't create base record. Only use the default base records
                        subjecttype = sbj_mod.Subjecttype(
                            base=sjtpbase,
                            scheme=scheme,
                            name=name
                        )
                        subjecttype.save(request=request)

                    except Exception as e:
                        logger.error(getattr(e, 'message', str(e)))
                        caption = _('Character')
                        msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                                    str(_("%(cpt)s '%(val)s' could not be created.") % {'cpt': caption, 'val': name})))
                        messages.append({'header': str(msg_header), 'class': 'border_bg_invalid', 'msg_html': msg_html})

    if logging_on:
        logger.debug('subjecttype: ' + str(subjecttype))
        logger.debug('messages: ' + str(messages))

    return subjecttype
# - end of create_subjecttype


def delete_subjecttype(subjecttype_instance, request):
    # --- delete subjecttype # PR2021-06-23 PR2021-07-13 PR2022-08-06
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_subjecttype ----- ')
        logger.debug('subjecttype_instance: ' + str(subjecttype_instance))

    deleted_row = None
    msg_html = None
    this_txt = _("Character '%(tbl)s'") % {'tbl': subjecttype_instance.name}

# check if there are students with subjects with this subjecttype
    students_with_this_subjecttype_exist = stud_mod.Studentsubject.objects.filter(
        schemeitem__subjecttype=subjecttype_instance
    ).exists()

    if logging_on:
        logger.debug('students_with_this_subjecttype_exist: ' + str(students_with_this_subjecttype_exist))

    if students_with_this_subjecttype_exist:
        msg_html = ''.join((str(_('There are candidates with subjects with this character.')), '<br>',
                            str(_("%(cpt)s could not be deleted.") % {'cpt': this_txt})))

    else:
        deleted_row, err_html = sch_mod.delete_instance(
            table='subjecttype',
            instance=subjecttype_instance,
            request=request,
            this_txt=this_txt
        )
        if err_html:
            msg_html = err_html

    # - check if this subjecttype base has other child subjecttypes, delet if none found
        # PR2021-06-27 debug: Don't delete base subjecttypes without children: they may be used another time

    if logging_on:
        logger.debug('deleted_row' + str(deleted_row))
        logger.debug('msg_html' + str(msg_html))

    return deleted_row, msg_html
# - end of delete_subjecttype


def update_subjecttype_instance(instance, scheme, upload_dict, error_list, request):
    # --- update existing and new instance PR2021-06-23
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_subjecttype_instance -----')
        logger.debug('upload_dict: ' + str(upload_dict))

    if instance:
        save_changes_in_base = False
        save_changes = False

        msg_header = _('Update character')

        for field, new_value in upload_dict.items():

            if logging_on:
                logger.debug('field: ' + str(field))
                logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))

# - save changes in field 'code'
            if field == 'sjtpbase_pk':
                base = None
                if new_value:
                    base = sbj_mod.Subjecttypebase.objects.get_or_none(
                        id=new_value
                    )
                if logging_on:
                    logger.debug('new_subjecttypebase: ' + str(base) + ' ' + str(type(base)))

                if base.pk != instance.base.pk:
                    if logging_on:
                        logger.debug('new_value != saved_value')
    # - validate abbrev checks null, max_len, exists
                    #  msg_err = { 'field': 'code', msg_list: [text1, text2] }, (for use in imput modals)
     # - save field if changed and no_error
                    setattr(base, field, new_value)
                    save_changes_in_base = True

# - save changes in field 'name'
            elif field in ('name', 'abbrev'):
                saved_value = getattr(instance, field)
                if new_value != saved_value:
    # - validate abbrev checks null, max_len, exists
                    msg_html = av.validate_subjecttype_name_abbrev_exists(field, new_value, scheme, instance)
                    if msg_html:
                        # add 'field' in error_list, to put old value back in field
                        # error_list will show mod_messages in RefreshDatarowItem
                        error_list.append({'field': field, 'header': msg_header, 'class': 'border_bg_warning', 'msg_html': msg_html})
                    else:
                        # - save field if changed and no_error
                        setattr(instance, field, new_value)
                        save_changes = True

            elif field in ('min_subjects', 'max_subjects',
                           'min_extra_nocount', 'max_extra_nocount',
                           'min_extra_counts', 'max_extra_counts'
                           ):
                msg_html = None

                if logging_on:
                    logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))
                    logger.debug('new_value.isdecimal: ' + str(new_value.isdecimal()))

# - check if value is positive whole number
                if new_value == '':
                    new_value = None

                if new_value is not None:
                    if not new_value.isdecimal():
                        msg_html = str(_("'%(val)s' is not a valid number.") % {'val': new_value})
                    else:
                        # TODO simplify code, also check for min max subjects when checking min_extra_nocount etc
                        new_value = int(new_value)
                        if field == 'min_subjects':
                            max_subjects = getattr(instance, 'max_subjects')
                            if max_subjects is not None and new_value > max_subjects:
                                msg_html = str(_("Minimum number of %(cpt)s cannot be greater than maximum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': max_subjects})
                        elif field == 'max_subjects':
                            min_subjects = getattr(instance, 'min_subjects')
                            if min_subjects is not None and new_value < min_subjects:
                                msg_html = str(_("Maximum number of %(cpt)s cannot be fewer than minimum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': min_subjects})

                        elif field == 'min_extra_nocount':
                            max_extra_nocount = getattr(instance, 'max_extra_nocount')
                            if max_extra_nocount is not None and new_value > max_extra_nocount:
                                msg_html = str(_("Minimum number of %(cpt)s cannot be greater than maximum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': max_extra_nocount})
                        elif field == 'max_extra_nocount':
                            min_extra_nocount = getattr(instance, 'min_extra_nocount')
                            if min_extra_nocount is not None and new_value < min_extra_nocount:
                                msg_html = str(_("Maximum number of %(cpt)s cannot be fewer than minimum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': min_extra_nocount})

                        elif field == 'min_extra_counts':
                            max_extra_counts = getattr(instance, 'max_extra_counts')
                            if max_extra_counts is not None and new_value > max_extra_counts:
                                msg_html = str(_("Minimum number of %(cpt)s cannot be greater than maximum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': max_extra_counts})
                        elif field == 'max_extra_counts':
                            min_extra_counts = getattr(instance, 'min_extra_counts')
                            if min_extra_counts is not None and new_value < min_extra_counts:
                                msg_html = str(_("Maximum number of %(cpt)s cannot be fewer than minimum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': min_extra_counts})

                if msg_html:
                    if logging_on:
                        logger.debug('msg_html: <' + str(msg_html) + '> ' + str(type(msg_html)))
                    # add 'field' in error_list, to put old value back in field
                    # error_list will show mod_messages in RefreshDatarowItem
                    error_list.append({'field': field,'header': msg_header,'class': 'border_bg_warning', 'msg_html': msg_html})
                else:
                    # -note: value can be None
                    saved_value = getattr(instance, field)
                    if logging_on:
                        logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))
                        logger.debug('saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))
                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True

            elif field == 'has_pws':
                saved_value = getattr(instance, field)
                if logging_on:
                    logger.debug('field: ' + str(field))
                    logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))
                    logger.debug('saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))

                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# --- end of for loop ---

# +++++ save changes
        if save_changes or save_changes_in_base:
            try:
                if save_changes_in_base:
                    # also save instance when base has changed, to update modifiedat and modifiedby
                    instance.base.save()
                instance.save(request=request)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred: ')), '<br><i>', str(e), '</i><br>',
                                    str(_('The changes have not been saved.'))))
                error_list.append({'header': msg_header, 'class': 'border_bg_invalid', 'msg_html': msg_html})
            else:
# also update modified in scheme, otherwise it is difficult to find out if scheme has been changed
                try:
                    scheme = instance.scheme
                    scheme.save(request=request)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                # awpr_logs.save_to_log(instance, 'u', request)

# - end of update_subjecttype_instance


def create_subjecttype_rows(examyear, append_dict, scheme_pk=None, depbase=None, cur_dep_only=False, sjtp_pk=None,  orderby_sequence=False):
    # --- create rows of all subjecttypes of this examyear / country  PR2021-06-24
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_subjecttype_rows ============= ')
        logger.debug('cur_dep_only: ' + str(cur_dep_only))
        logger.debug('examyear: ' + str(examyear))
        logger.debug('scheme_pk: ' + str(scheme_pk))
        logger.debug('depbase: ' + str(depbase))
        logger.debug('sjtp_pk: ' + str(sjtp_pk))

    subjecttype_rows =[]
    if examyear:
        sql_keys = {'ey_id': examyear.pk}
        sql_list = ["SELECT sjtp.id, sjtp.base_id, CONCAT('subjecttype_', sjtp.id::TEXT) AS mapid,",
            "sjtpbase.id AS sjtpbase_id, sjtpbase.code AS sjtpbase_code, sjtpbase.name AS sjtpbase_name,",
            "sjtpbase.sequence AS sjtpbase_sequence, sjtp.name, sjtp.abbrev,",
            "sjtp.min_subjects, sjtp.max_subjects, sjtp.min_extra_nocount, sjtp.max_extra_nocount,",
            "sjtp.min_extra_counts, sjtp.max_extra_counts, sjtp.has_pws,",
            "lvl.id AS lvl_id, lvl.abbrev AS lvl_abbrev, sct.id AS sct_id, sct.abbrev AS sct_abbrev,",
            "dep.base_id AS depbase_id, lvl.base_id AS lvlbase_id, sct.base_id AS sctbase_id,",
            "ey.code AS ey_code,",
            "dep.id AS department_id, depbase.code AS depbase_code, scheme.id AS scheme_id, scheme.name AS scheme_name,",
            "sjtp.modifiedby_id, sjtp.modifiedat, au.last_name AS modby_username",

            "FROM subjects_subjecttype AS sjtp",
            "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = sjtp.base_id)",
            "INNER JOIN subjects_scheme AS scheme ON (scheme.id = sjtp.scheme_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",

            "LEFT JOIN accounts_user AS au ON (au.id = sjtp.modifiedby_id)",

            "WHERE ey.id = %(ey_id)s::INT"]

        if sjtp_pk:
            sql_keys['sjtp_pk'] = sjtp_pk
            sql_list.append("AND sjtp.id = %(sjtp_pk)s::INT")

        elif scheme_pk:
            sql_keys['scheme_pk'] = scheme_pk
            sql_list.append("AND scheme.id = %(scheme_pk)s::INT")

        elif cur_dep_only:
            # TODO improve code
            depbase_lookup = None
            if depbase:
                department = sch_mod.Department.objects.get_or_none(examyear=examyear, base=depbase)
                if department:
                    depbase_lookup = ''.join( ('%;', str(depbase.pk), ';%') )
            if logging_on:
                logger.debug('depbase_lookup: ' + str(depbase_lookup))

            if depbase_lookup:
                sql_keys['depbase_pk'] = depbase_lookup
                sql_list.append("AND CONCAT(';', sct.depbases::TEXT, ';') LIKE %(depbase_pk)s::TEXT")
            else:
                sql_list.append("AND FALSE")

        #if orderby_sequence:
        #    sql_list.append("ORDER BY sjtpbase.sequence")

        sql_list.append("ORDER BY sjtp.id")

        sql = ' '.join(sql_list)
        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            subjecttype_rows = af.dictfetchall(cursor)

    # - add messages to student_row
        if sjtp_pk and subjecttype_rows and append_dict:
            # when student_pk has value there is only 1 row
            row = subjecttype_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value


    return subjecttype_rows
# --- end of create_subjecttype_rows


def create_subjecttypebase_rows(sjtpbase_pk=None):
    # --- create rows of all subjecttypes of this examyear / country  PR2021-06-22
    #logger.debug(' =============== create_subjecttypebase_rows ============= ')
    rows =[]

    sql_keys = {}

    sql_list = ["SELECT sjtbase.id, CONCAT('subjecttypebase_', sjtbase.id::TEXT) AS mapid,",
        "sjtbase.code, sjtbase.name, sjtbase.abbrev, sjtbase.sequence",
        "FROM subjects_subjecttypebase AS sjtbase"]

    if sjtpbase_pk:
        sql_keys['sjtpbase_pk'] = sjtpbase_pk
        sql_list.append("WHERE sjtbase.id = %(sjtpbase_pk)s::INT")

    sql_list.append("ORDER BY sjtbase.id")

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    return rows
# --- end of create_subjecttypebase_rows




# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


def create_scheme_rows(examyear, scheme_pk=None, cur_dep_only=False, depbase=None):
    # --- create rows of all schemes of this examyear PR2020-11-16 PR2021-06-24 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_scheme_rows ============= ')
        logger.debug('cur_dep_only: ' + str(cur_dep_only))
        logger.debug('scheme_pk: ' + str(scheme_pk))

    scheme_rows = []
    if examyear:
        sql_keys = {'ey_id': examyear.pk}
        sql_list = ["SELECT scheme.id, scheme.department_id, scheme.level_id, scheme.sector_id,",
            "CONCAT('scheme_', scheme.id::TEXT) AS mapid, scheme.name,",
            "scheme.min_studyloadhours, scheme.min_subjects, scheme.max_subjects,",
            "scheme.min_mvt, scheme.max_mvt, scheme.min_wisk, scheme.max_wisk,",
            "scheme.min_combi, scheme.max_combi, scheme.max_reex,",

            "scheme.rule_avg_pece_sufficient, scheme.rule_avg_pece_notatevlex,",
            "scheme.rule_core_sufficient, scheme.rule_core_notatevlex,",

            "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ey.code AS ey_code,",
            "dep.base_id AS depbase_id, lvl.base_id AS lvlbase_id, sct.base_id AS sctbase_id,",
            "depbase.code AS depbase_code,"
            "scheme.modifiedby_id, scheme.modifiedat,",
            "au.last_name AS modby_username",

            "FROM subjects_scheme AS scheme",
            "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = scheme.modifiedby_id)",

            "WHERE dep.examyear_id = %(ey_id)s::INT"]

        if scheme_pk:
            sql_keys['scheme_id'] = scheme_pk
            sql_list.append('AND scheme.id = %(scheme_id)s::INT')
        elif cur_dep_only:
            if depbase:
                sql_keys['db_id'] = depbase.pk
                sql_list.append('AND dep.base_id = %(db_id)s::INT')
            else:
                sql_list.append("AND FALSE")

        sql_list.append("ORDER BY scheme.id")

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

    return rows
# --- end of create_scheme_rows


def create_schemeitem_rows(sel_examyear, append_dict, schemeitem_pk=None, scheme_pk=None,
                           cur_dep_only=False, depbase=None, skip_notatdayschool=False,
                           orderby_name=False, orderby_sjtpbase_sequence=False):
    # --- create rows of all schemeitems of this examyear PR2020-11-17 PR2021-07-01 PR2022-08-21

    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug(' =============== create_schemeitem_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))
        logger.debug('schemeitem: ' + str(schemeitem_pk) + ' ' + str(type(schemeitem_pk)))
        logger.debug('depbase: ' + str(depbase) + ' ' + str(type(depbase)))

    schemeitem_rows = []
    try:
        if sel_examyear :
            sql_keys = {'ey_id': sel_examyear.pk}
            sql_list = ["SELECT si.id, si.scheme_id, scheme.department_id, scheme.level_id, scheme.sector_id,",
                "CONCAT('schemeitem_', si.id::TEXT) AS mapid,",
                "si.subject_id AS subj_id, subj.name_nl AS subj_name_nl, subjbase.id AS subjbase_id, subjbase.code AS subj_code,",
                "sjtpbase.code AS sjtpbase_code, sjtpbase.sequence AS sjtpbase_sequence,",
                "sjtp.id AS sjtp_id, sjtp.name AS sjtp_name, sjtp.abbrev AS sjtp_abbrev,",
                "sjtp.has_prac AS sjtp_has_prac, sjtp.has_pws AS sjtp_has_pws,",
                "sjtp.min_subjects AS sjtp_min_subjects, sjtp.max_subjects AS sjtp_max_subjects, ",
                "scheme.name AS scheme_name, scheme.fields AS scheme_fields,",
                "depbase.id AS depbase_id, depbase.code AS depbase_code,",
                "lvl.base_id AS lvlbase_id, sct.base_id AS sctbase_id,",
                "lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",

                "ey.code, ey.no_practexam AS ey_no_practexam, ey.sr_allowed AS ey_sr_allowed,"
                "ey.no_centralexam AS ey_no_centralexam, ey.no_thirdperiod AS ey_no_thirdperiod,",

                "si.gradetype, si.weight_se, si.weight_ce, si.multiplier, si.ete_exam, si.otherlang,",
                "si.is_mandatory, si.is_mand_subj_id,",
                "si.is_combi, si.extra_count_allowed, si.extra_nocount_allowed,",
                "si.has_practexam, si.is_core_subject, si.is_mvt, si.is_wisk,",

                "si.rule_grade_sufficient, si.rule_gradesuff_notatevlex,",
                "si.sr_allowed AS si_sr_allowed, si.no_ce_years, si.thumb_rule,",

                "si.studyloadhours, si.notatdayschool,",

                "si.modifiedby_id, si.modifiedat,",
                "au.last_name AS modby_username",

                "FROM subjects_schemeitem AS si",
                "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                "INNER JOIN subjects_subjecttype AS sjtp ON (sjtp.id = si.subjecttype_id)",
                "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = sjtp.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",
                "LEFT JOIN accounts_user AS au ON (au.id = si.modifiedby_id)",

                "WHERE dep.examyear_id = %(ey_id)s::INT"]

            if schemeitem_pk:
                # when schemeitem_pk has value: skip other filters
                sql_keys['si_pk'] = schemeitem_pk
                sql_list.append('AND si.id = %(si_pk)s::INT')

            elif scheme_pk:
                sql_keys['scheme_pk'] = scheme_pk
                sql_list.append("AND scheme.id = %(scheme_pk)s::INT")

            elif cur_dep_only:
                if depbase:
                    sql_keys['depbase_pk'] = depbase.pk
                    sql_list.append('AND depbase.id = %(depbase_pk)s::INT')
                else:
                    sql_list.append("AND FALSE")

            if not skip_notatdayschool:
                sql_list.append("AND NOT si.notatdayschool")

            if orderby_name:
                sql_list.append('ORDER BY LOWER(scheme.name), LOWER(subj.name_nl)')
            elif orderby_sjtpbase_sequence:
                sql_list.append('ORDER BY sjtpbase.sequence')
            else:
                sql_list.append('ORDER BY si.id')

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('orderby_name: ' + str(orderby_name) )
                logger.debug('orderby_sjtpbase_sequence: ' + str(orderby_sjtpbase_sequence) )
                logger.debug('sql_keys: ' + str(sql_keys) )
                logger.debug('sql: ' + str(sql) )

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                schemeitem_rows = af.dictfetchall(cursor)

# - add messages to schemeitem_row, only if subject_pk has value
            if schemeitem_pk and schemeitem_rows and append_dict:
                # when schemeitem_pk has value there is only 1 row
                row = schemeitem_rows[0]
                if row:
                    for key, value in append_dict.items():
                        row[key] = value


    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('schemeitem_rows: ' + str(schemeitem_rows))

    return schemeitem_rows
# --- end of create_schemeitem_rows

#################

def get_scheme_si_dict(examyear_pk, depbase_pk, scheme_pk=None, schemeitem_pk=None):
    # PR2021-12-13 PR2024-05-31
    # --- create dict with all schemitems of this examyear, this department
    # used to validate studsubj and grades, not to make changes
    # lookup key = schemeitem_pk

    # called by:
    #   GradeUploadView,
    #   StudentsubjectApproveSingleView,
    #   StudentsubjectMultipleUploadView,
    #   StudentsubjectSingleUpdateView

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== get_scheme_si_dict ============= ')
        logger.debug('    examyear_pk:   ' + str(examyear_pk) + ' ' + str(type(examyear_pk)))
        logger.debug('    depbase_pk:    ' + str(depbase_pk) + ' ' + str(type(depbase_pk)))
        logger.debug('    scheme_pk:     ' + str(scheme_pk) + ' ' + str(type(scheme_pk)))
        logger.debug('    schemeitem_pk: ' + str(schemeitem_pk) + ' ' + str(type(schemeitem_pk)))

    schemeitem_dict = {}
    try:
        if examyear_pk and depbase_pk:
            sql_keys = {'ey_id': examyear_pk, 'depbase_pk': depbase_pk}
            sql_list = ["SELECT si.id, subj.name_nl AS subj_name_nl, subjbase.code AS subj_code,",
                "sjtpbase.code AS sjtpbase_code,",

                "scheme.name AS scheme_name, scheme.max_reex AS scheme_max_reex,",
                # TODO check if these will be used
                #"scheme.min_subjects AS sch_min_subjects, scheme.max_subjects AS sch_max_subjects,",
                #"scheme.min_extra_nocount AS sch_min_extra_nocount, scheme.max_extra_nocount AS sch_max_extra_nocount,",
                #"scheme.min_extra_counts AS sch_min_extra_counts, scheme.max_extra_counts AS sch_max_extra_counts,",

                "sjtp.name AS sjtp_name, sjtp.abbrev AS sjtp_abbrev,",

                # PR2024-05-18
                # has_prac only enables the has_practexam option of a schemeitem.
                # schemeitem.has_pws is deprecated, use subjecttype.has_pws instead
                # has_pws = has profielwerkstuk or sectorwerkstuk
                "sjtp.has_prac AS sjtp_has_prac, sjtp.has_pws AS sjtp_has_pws,",

                # TODO check if these will be used
                #"sjtp.min_subjects AS sjtp_min_subjects, sjtp.max_subjects AS sjtp_max_subjects,",
                #"sjtp.min_extra_nocount AS sjtp_min_extra_nocount, sjtp.max_extra_nocount AS sjtp_max_extra_nocount,",
                #"sjtp.min_extra_counts AS sjtp_min_extra_counts, sjtp.max_extra_counts AS sjtp_max_extra_counts,",

                # PR2024-05-18 was:
                #   "ey.code AS ey_code, ey.no_practexam AS ey_no_practexam, ey.sr_allowed AS ey_sr_allowed,"
                "ey.code AS ey_code,",

                # PR2024-05-18 was:
                #   "ey.no_centralexam AS ey_no_centralexam, ey.no_thirdperiod AS ey_no_thirdperiod,",
                "ey.no_centralexam, ey.no_thirdperiod,",

                # PR2024-05-18 replaced by "(ey.sr_allowed AND si.sr_allowed) AS sr_allowed",
                # was: "ey.sr_allowed AS ey_sr_allowed, si.sr_allowed AS si_sr_allowed,",
                "(ey.sr_allowed AND si.sr_allowed) AS sr_allowed,",

                # PR2024-05-18 include ey.no_practexam
                # TODO remove ey_no_practexam and si_has_practexam
                "ey.no_practexam AS ey_no_practexam, si.has_practexam AS si_has_practexam,",
                "(NOT ey.no_practexam AND si.has_practexam) AS has_practex,",

                "depbase.code AS depbase_code, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",
                "dep.level_req, dep.sector_req, dep.has_profiel,",
                "si.ete_exam, si.otherlang,",
                "si.gradetype, si.weight_se, si.weight_ce, si.multiplier,",
                "si.is_mandatory, si.is_mand_subj_id,",
                "si.is_combi, si.extra_count_allowed, si.extra_nocount_allowed,",
                "si.has_practexam, si.is_core_subject, si.is_mvt, si.is_wisk,",

                "si.rule_grade_sufficient, si.rule_gradesuff_notatevlex, si.no_ce_years,",
                "si.thumb_rule AS thumb_rule_allowed",

                "FROM subjects_schemeitem AS si",
                "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                "INNER JOIN subjects_subjecttype AS sjtp ON (sjtp.id = si.subjecttype_id)",
                "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = sjtp.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",

                "WHERE dep.examyear_id = %(ey_id)s::INT",
                "AND depbase.id = %(depbase_pk)s::INT"
                ]
            if schemeitem_pk:
                sql_keys['si_id'] = schemeitem_pk
                sql_list.append("AND si.id = %(si_id)s::INT")
            elif scheme_pk:
                sql_keys['schm.id'] = scheme_pk
                sql_list.append("AND scheme.id = %(schm.id)s::INT")
            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = af.dictfetchall(cursor)

            for row in rows:
                si_pk = row.get('id')
                if si_pk:
                    schemeitem_dict[si_pk] = row

                if logging_on:
                    logger.debug('row: ' + str(row))

        if logging_on:
            logger.debug('schemeitem_dict: ' + str(schemeitem_dict))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return schemeitem_dict
# --- end of get_scheme_si_dict


###################

@method_decorator([login_required], name='dispatch')
class ExamDownloadExamView(View):  # PR2021-05-06

    def get(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('===== ExamDownloadExamView ===== ')
            logger.debug('list: ' + str(list) + ' ' + str(type(list)))

        # function creates, Exam pdf file

        response = None
        exam_pk = None
        #try:

        if request.user and request.user.country and request.user.schoolbase:
            req_usr = request.user

# - reset language
            # PR2021-05-08 debug: without activate text will not be translated
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get order_pk_list from parameter 'list
            if list:
                # list: 10 <class 'str'>
                exam_pk = int(list)

                #list_dict = json.loads(list)
                #logger.debug('list_dict: ' + str(list_dict))

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

            if logging_on:
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))
                logger.debug('exam_pk: ' + str(exam_pk))

            if sel_examyear and exam_pk:
                sel_exam_instance = subj_mod.Exam.objects.get_or_none(
                    pk=exam_pk,
                    subject__examyear=sel_examyear)
                if logging_on:
                    logger.debug('sel_exam_instance: ' + str(sel_exam_instance))

                if sel_exam_instance:
                    # ---  create file Name and worksheet Name

                    file_name = ' '.join(( str(_('Exam')),
                        c.EXAMPERIOD_CAPTION.get(sel_exam_instance.examperiod, ''),
                        sel_exam_instance.subject.name_nl,
                        sel_exam_instance.department.base.code
                    ))
                    if sel_exam_instance.level:
                        file_name += ' ' + sel_exam_instance.level.base.code
                    if sel_exam_instance.version:
                        file_name += ' ' + sel_exam_instance.version

                    today_formatted = af.format_DMY_from_dte(af.get_today_dateobj(), user_lang)
                    file_name += ' dd ' + today_formatted + '.pdf'

                    # create the HttpResponse object ...
                    response = HttpResponse(
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = "attachment; filename=" + file_name

                    # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

                    # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                    #temp_file = tempfile.TemporaryFile()
                    # canvas = Canvas(temp_file)

                    buffer = io.BytesIO()
                    canvas = Canvas(buffer)

                    printpdf.draw_exam(canvas, sel_exam_instance, sel_examyear, user_lang)

                    if logging_on:
                        logger.debug('end of draw_exam')

                    canvas.showPage()
                    canvas.save()

                    pdf = buffer.getvalue()
                    # pdf_file = File(temp_file)

                    # was: buffer.close()

                    response = HttpResponse(content_type='application/pdf')
                    #response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'
                    #response['Content-Disposition'] = 'inline; filename="testpdf.pdf"'
                    response['Content-Disposition'] = "inline; filename=" + file_name

                    response.write(pdf)

        #except Exception as e:
       #     logger.error(getattr(e, 'message', str(e)))
       #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of ExamDownloadExamView


@method_decorator([login_required], name='dispatch')
class ExamDownloadWolfView(View):  # PR2022-01-29
    #PR2023 debug Yolande v Erven Ancilla Domini: scalelength op download is 112, in exam 1s 113. How come?
    def get(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('===== ExamDownloadWolfView ===== ')
            logger.debug('list: ' + str(list) + ' ' + str(type(list)))

        # function creates, Exam pdf file with answers

        response = None
        grade_pk = None
        #try:

        if request.user and request.user.country and request.user.schoolbase:
            req_usr = request.user

# - reset language
            # PR2021-05-08 debug: without activate text will not be translated
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get order_pk_list from parameter 'list
            if list:
                # list: 10 <class 'str'>
                grade_pk = int(list)

                #list_dict = json.loads(list)
                #logger.debug('list_dict: ' + str(list_dict))

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

            if logging_on:
                logger.debug('    sel_school: ' + str(sel_school))
                logger.debug('    sel_department: ' + str(sel_department))
                logger.debug('    grade_pk: ' + str(grade_pk))

            if sel_examyear and grade_pk:

                sel_grade_instance = stud_mod.Grade.objects.get_or_none(
                    pk=grade_pk,
                    studentsubject__student__school__base_id=sel_school.base_id)
                if logging_on:
                    logger.debug('sel_grade_instance: ' + str(sel_grade_instance))

                # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3
                sel_ce_exam_instance = None
                if sel_grade_instance:
                    sel_ce_exam_instance = sel_grade_instance.ce_exam
                if logging_on:
                    logger.debug('sel_ce_exam_instance: ' + str(sel_ce_exam_instance))

                # dont print grade_exam when exam is not published (can happen when ETE has tuned of 'published' PR2022-05-22
                if sel_ce_exam_instance and sel_ce_exam_instance.published is not None:

                    student_name = sel_grade_instance.studentsubject.student.fullnamewithinitials

                    if logging_on:
                        logger.debug('    student_name: ' + str(student_name))
                        logger.debug('    scalelength: ' + str(sel_ce_exam_instance.scalelength))

                    file_name = ' '.join(( str(_('Exam')),
                        c.EXAMPERIOD_CAPTION.get(sel_ce_exam_instance.examperiod, ''),
                        sel_ce_exam_instance.subject.name_nl,
                        sel_ce_exam_instance.department.base.code
                    ))
                    if sel_ce_exam_instance.level:
                        file_name += ' ' + sel_ce_exam_instance.level.base.code
                    if sel_ce_exam_instance.version:
                        file_name += ' ' + sel_ce_exam_instance.version
                    if student_name:
                        file_name += ' ' + student_name

                    today_formatted = af.format_DMY_from_dte(af.get_today_dateobj(), user_lang)
                    file_name += ' dd ' + today_formatted + '.pdf'

                    # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                    #temp_file = tempfile.TemporaryFile()
                    # canvas = Canvas(temp_file)

                    buffer = io.BytesIO()
                    canvas = Canvas(buffer)

                    # Start writing the PDF here
                    printpdf.draw_grade_exam(canvas, sel_grade_instance, sel_ce_exam_instance, sel_examyear, user_lang)

                    if logging_on:
                        logger.debug('end of draw_exam')

                    canvas.showPage()
                    canvas.save()

                    pdf = buffer.getvalue()
                    # pdf_file = File(temp_file)

                    # was: buffer.close()

                    response = HttpResponse(content_type='application/pdf')
                    # response['Content-Disposition'] = "inline; filename=" + file_name
                    response['Content-Disposition'] = "inline; filename='examen.pdf'"
                    #response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

                    response.write(pdf)

        #except Exception as e:
       #     logger.error(getattr(e, 'message', str(e)))
       #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of ExamDownloadWolfView


@method_decorator([login_required], name='dispatch')
class ExamDownloadConversionView(View):  # PR2022-05-08

    def get(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('===== ExamDownloadConversionView ===== ')
            logger.debug('list: ' + str(list) + ' ' + str(type(list)))

        # function creates, Conversion table pdf file

        response = None
        exam_pk = None
        #try:

        if request.user and request.user.country and request.user.schoolbase:
            req_usr = request.user

# - reset language
            # PR2021-05-08 debug: without activate text will not be translated
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get exam_pk_list from parameter 'list
            if list:
                # list: 117 <class 'str'>
                exam_pk = int(list)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

            if logging_on:
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))
                logger.debug('exam_pk: ' + str(exam_pk))
                logger.debug('sel_examyear.code: ' + str(sel_examyear.code))

            if sel_examyear and exam_pk:
                sel_exam_instance = subj_mod.Exam.objects.get_or_none(
                    pk=exam_pk,
                    subject__examyear__code=sel_examyear.code)
                if logging_on:
                    logger.debug('sel_exam_instance: ' + str(sel_exam_instance))

                # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

                # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                #temp_file = tempfile.TemporaryFile()
                # canvas = Canvas(temp_file)

                buffer = io.BytesIO()
                canvas = Canvas(buffer)

                # Start writing the PDF here
                printpdf.draw_conversion_table(canvas, sel_exam_instance, sel_examyear, user_lang)

                if logging_on:
                    logger.debug('end of draw_exam')

                canvas.showPage()
                canvas.save()

                pdf = buffer.getvalue()

                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="omzettingstabel.pdf"'
                #response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

                response.write(pdf)

        #except Exception as e:
       #     logger.error(getattr(e, 'message', str(e)))
       #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of ExamDownloadConversionView



@method_decorator([login_required], name='dispatch')
class ExamDownloadExamJsonView(View):  # PR2021-05-06 PR2023-05-18

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('===== ExamDownloadExamJsonView ===== ')

        def get_exam_rows(sel_examyear_code, sel_examperiod, sel_department, sel_lvlbase_pk, sel_subject_pk, request):
            # --- create exam rows that have students with results, also SXM of this examyear PR2022-05-03

            logging_on = s.LOGGING_ON
            if logging_on:
                logger.debug(' ----- get_exam_rows -----')
                logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
                logger.debug('    sel_subject_pk: ' + str(sel_subject_pk))

            # - only grades with ete exams are visible
            # - only exams that are published are visible
            # - only ce_exams that are submitted have results shown
            # - group by exam and school

            exam_rows = []
            req_usr = request.user
            if req_usr.role == c.ROLE_064_ADMIN:

                sel_depbase_pk = sel_department.base_id if sel_department else None

                sql_keys = {'ey_code': sel_examyear_code, 'depbase_id': sel_depbase_pk, 'experiod': sel_examperiod}

                if sel_lvlbase_pk:
                    sql_keys['lvlbase_pk'] = sel_lvlbase_pk

                sel_subjbase_pk = None
                if sel_subject_pk:
                    subject = subj_mod.Subject.objects.get_or_none(pk=sel_subject_pk)
                    if subject:
                        sel_subjbase_pk = subject.base.pk

                if logging_on:
                    logger.debug('    sel_subjbase_pk: ' + str(sel_subjbase_pk))

                if sel_subjbase_pk:
                    sql_keys['sjb_pk'] = sel_subjbase_pk

                sub_sql_list = ["SELECT exam.id",

                            "FROM students_grade AS grd",
                            "INNER JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id)",
                            "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                            "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",

                            "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

                            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                            "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                            "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

                            "WHERE ey.code = %(ey_code)s::INT",
                            "AND exam.ete_exam",
                            "AND grd.examperiod = %(experiod)s::INT",
                            "AND dep.base_id = %(depbase_id)s::INT",

                            "AND exam.published_id IS NOT NULL",
                            "AND grd.ce_exam_published_id IS NOT NULL",

                            "AND grd.ce_exam_score IS NOT NULL",

                            "AND NOT stud.deleted AND NOT stud.tobedeleted",
                            "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted",
                            "AND NOT grd.deleted AND NOT grd.tobedeleted"
                            ]

                if sel_lvlbase_pk:
                    sub_sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

                if sel_subjbase_pk:
                    sub_sql_list.append("AND subj.base_id = %(sjb_pk)s::INT")

                sub_sql_list.append("GROUP BY exam.id")

                sub_sql = ' '.join(sub_sql_list)

                sql_list = ["WITH grade_exams AS (" + sub_sql + ")",
                            "SELECT exam.id AS exam_id,",
                            "depbase.code AS depbase_code, lvl.abbrev AS lvl_abbrev,",
                            "subjbase.code AS subj_code, subj.name_nl AS subj_name_nl,",

                            "exam.examperiod, exam.version, exam.amount, exam.scalelength,",
                            "exam.partex, exam.assignment, exam.keys",

                            "FROM subjects_exam AS exam",

                            "INNER JOIN grade_exams ON (grade_exams.id = exam.id)",

                            "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                            "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
                            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                            "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",

                            "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

                            "WHERE ey.code = %(ey_code)s::INT",
                            "AND exam.ete_exam",
                            "AND exam.examperiod = %(experiod)s::INT",
                            "AND dep.base_id = %(depbase_id)s::INT",
                            # "AND exam.published_id IS NOT NULL",

                            "AND exam.scalelength IS NOT NULL AND exam.scalelength > 0 ",
                            ]

                if sel_lvlbase_pk:
                    sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

                if sel_subjbase_pk:
                    sql_list.append("AND subj.base_id = %(sjb_pk)s::INT")

                sql = ' '.join(sql_list)

                with connection.cursor() as cursor:
                    cursor.execute(sql, sql_keys)
                    exam_rows = af.dictfetchall(cursor)

                if logging_on:
                    logger.debug('sql_keys: ' + str(sql_keys))

                if exam_rows :
                    if logging_on:
                        logger.debug('len(exam_rows): ' + str(len(exam_rows)))
                        for row in exam_rows:
                            logger.debug('XXXXXXXXXXX row: ' + str(row))

                """

                row: {'exam_id': 117, 'depbase_code': 'Vsbo', 'lvl_abbrev': 'PBL', 
                    'subj_code': 'bw', 'subj_name_nl': 'Bouw', 
                    'examperiod': 1, 'version': 'Versie BLAUW', 
                    'amount': 39, 'scalelength': 96, 
                    'partex': '1;1;4;20;Praktijkexamen onderdeel A#3;1;8;12;Minitoets 1 BLAUW onderdeel A#4;1;3;22;Praktijkexamen onderdeel B#6;1;7;7;Minitoets 2 BLAUW onderdeel B#7;1;1;9;Praktijkexamen onderdeel C#9;1;7;8;Minitoets 3 BLAUW onderdeel C#10;1;1;10;Praktijkexamen onderdeel D#12;1;8;8;Minitoets 4 BLAUW onderdeel D', 
                    'assignment': '1;4;20|1;;6;|2;;4;|3;;4;|4;;6;#3;8;12|1;D;3;|2;C;2;|3;C;;|4;;1;|5;;1;|6;;1;|7;D;;|8;;2;#4;3;22|1;;6;|2;;6;|3;;10;#6;7;7|1;;1;|2;D;;|3;;1;|4;;1;|5;;1;|6;D;;|7;;1;#7;1;9|1;;9;#9;7;8|1;C;;|2;;1;|3;;1;|4;D;;|5;;2;|6;D;;|7;;1;#10;1;10|1;;10;#12;8;8|1;D;;|2;D;;|3;C;;|4;;1;|5;;1;|6;D;;|7;D;;|8;;1;', 
                    'keys': '1#3|1;ac|2;b|3;ab|7;d#4#6|2;b|6;b#7#9|1;b|4;c|6;a#10#12|1;a|2;b|3;a|6;d|7;d'}
                """
            return exam_rows

        def get_grade_exam_result_rows(sel_examyear_code, sel_examperiod, selected_pk_dict, request):
            # --- create grade exam rows of all students with results, also SXM of this examyear PR2022-04-27

            logging_on = False  # s.LOGGING_ON
            if logging_on:
                logger.debug(' ----- get_grade_exam_result_rows -----')
                logger.debug('selected_pk_dict: ' + str(selected_pk_dict))

            # - only grades with ete exams are visible
            # - only ce_exams that are submitted have results shown
            # - group by exam and school

            result_rows_dict = {}

            req_usr = request.user
            if req_usr.role == c.ROLE_064_ADMIN:
                sel_depbase_pk = selected_pk_dict.get(c.KEY_SEL_DEPBASE_PK)

                sql_keys = {'ey_code': sel_examyear_code, 'depbase_id': sel_depbase_pk, 'experiod': sel_examperiod}

                sql_list = ["SELECT exam.id AS exam_id, schoolbase.code AS school_code, stud.examnumber, grd.ce_exam_result",

                            "FROM students_grade AS grd",

                            "INNER JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id)",
                            "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                            "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

                            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                            "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                            "INNER JOIN schools_schoolbase AS schoolbase ON (schoolbase.id =school.base_id)",
                            "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

                            "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                            "WHERE ey.code = %(ey_code)s::INT",
                            "AND exam.ete_exam",
                            "AND grd.examperiod = %(experiod)s::INT",
                            "AND dep.base_id = %(depbase_id)s::INT",
                            "AND exam.published_id IS NOT NULL",
                            "AND grd.ce_exam_published_id IS NOT NULL",

                            "AND grd.ce_exam_score IS NOT NULL",
                            "AND exam.scalelength IS NOT NULL AND exam.scalelength > 0 ",

                            "AND NOT stud.deleted AND NOT stud.tobedeleted",
                            "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted",
                            "AND NOT grd.deleted AND NOT grd.tobedeleted"
                            ]

                sel_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)
                if sel_lvlbase_pk:
                    sql_keys['lvlbase_pk'] = sel_lvlbase_pk
                    sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

                sel_subjbase_pk = None
                # get sel_subjbase_pk from sel_subject_pk TODO deprecate, replace filter on sel_subject_pk by sel_subjbase_pk
                sel_subject_pk = selected_pk_dict.get(c.KEY_SEL_SUBJECT_PK)
                if sel_subject_pk:
                    subject = subj_mod.Subject.objects.get_or_none(pk=sel_subject_pk)
                    if subject and subject.base.pk:
                        sel_subjbase_pk = subject.base.pk
                    else:
                        sel_subjbase_pk = selected_pk_dict.get(c.KEY_SEL_SUBJBASE_PK)

                if sel_subjbase_pk:
                    sql_keys['sjb_pk'] = sel_subjbase_pk
                    sql_list.append("AND subj.base_id = %(sjb_pk)s::INT")

                sql = ' '.join(sql_list)

                with connection.cursor() as cursor:
                    cursor.execute(sql, sql_keys)
                    result_rows = af.dictfetchall(cursor)

                if logging_on:
                    logger.debug('sql_keys: ' + str(sql_keys))

                if result_rows:
                    for row in result_rows:
                        exam_id = row.get('exam_id')
                        if exam_id not in result_rows_dict:
                            result_rows_dict[exam_id] = []

                        result_rows_dict[exam_id].append(row)

                if logging_on:
                    logger.debug('result_rows_dict: ' + str(result_rows_dict))
                """
                result_rows_dict: {
                    45: [{'exam_id': 45, 'school_code': 'CUR03', 'ce_exam_result': '0;37#1|1;1|2;1|3;1|4;1|5;1|6;a|7;1|8;1|9;a|10;1|11;a|12;a|13;a|14;1|15;1|16;a|17;1|18;1|19;1|20;a|21;1|22;a|23;a|24;1|25;a|26;a|27;1|28;1|29;1|30;1|31;1|32;a|33;1|34;1|35;1|36;a|37;x'}], 
                    49: [{'exam_id': 49, 'school_code': 'CUR03', 'ce_exam_result': '0;26#1|1;1|2;1|3;a|4;a|5;1|6;1|7;1|8;1|9;1|10;1|11;1|12;1|13;a|14;1|15;d|16;1|17;1|18;1|19;1|20;1|21;a|22;a|23;a|24;1|25;1|26;x'}, 
                         {'exam_id': 49, 'school_code': 'CUR03', 'ce_exam_result': '0;26#1|1;2|2;1|3;b|4;a|5;1|6;1|7;1|8;1|9;1|10;1|11;1|12;1|13;a|14;1|15;a|16;1|17;1|18;1|19;1|20;1|21;a|22;a|23;a|24;1|25;1|26;x'}, 
                         {'exam_id': 49, 'school_code': 'CUR03', 'ce_exam_result': '0;26#1|1;1|2;1|3;b|4;c|5;1|6;1|7;1|8;1|9;1|10;1|11;1|12;1|13;c|14;1|15;a|16;1|17;1|18;1|19;1|20;1|21;c|22;a|23;c|24;1|25;1|26;1'}, 
                         {'exam_id': 49, 'school_code': 'CUR03', 'ce_exam_result': '0;26#1|1;1|2;1|3;b|4;b|5;1|6;1|7;1|8;1|9;1|10;1|11;1|12;1|13;a|14;1|15;a|16;1|17;1|18;1|19;1|20;1|21;a|22;a|23;a|24;1|25;1|26;x'}], 
                    117: [{'exam_id': 117, 'school_code': 'CUR03', 'ce_exam_result': '0;39#1|1;2|2;1|3;3|4;4#3|1;a|2;b|3;a|4;1|5;1|6;1|7;b|8;1#4|1;4|2;2|3;6#6|1;1|2;a|3;x|4;x|5;x|6;a|7;1#7|1;7#9|1;a|2;1|3;1|4;a|5;1|6;a|7;x#10|1;7#12|1;d|2;a|3;a|4;1|5;1|6;b|7;a|8;1'}, 
                          {'exam_id': 117, 'school_code': 'CUR03', 'ce_exam_result': '0;39#1|1;2|2;3|3;4|4;5#3|1;a|2;b|3;b|4;0|5;1|6;x|7;x|8;x#4|1;1|2;1|3;1#6|1;1|2;a|3;1|4;1|5;1|6;a|7;x#7|1;1#9|1;a|2;1|3;1|4;a|5;x|6;c|7;1#10|1;6#12|1;a|2;a|3;a|4;1|5;1|6;a|7;a|8;1'}]}    
                """
            return result_rows_dict

        def get_exam_partex_dict_from_row(row): # PR2022-05-03
            # this function converts the saved 'partex' into a dict
            exam_partex = row.get('partex')
            exam_partex_dict = {}
            if exam_partex:
                exam_partex_arr = exam_partex.split('#')

                for exam_partex_arr_item in exam_partex_arr:
                    partex_arr = exam_partex_arr_item.split(';')
                    if len(partex_arr):
                        partex_pk_int = int(partex_arr[0])
                        exam_partex_dict[partex_pk_int] = {
                            'pk': partex_pk_int,
                            'tijdvak': int(partex_arr[1]),
                            'aantal vragen': int(partex_arr[2]),
                            'schaallengte': int(partex_arr[3]),
                            'naam': partex_arr[4]
                        }
            return exam_partex_dict

        def get_exam_assignment_dict_from_row(row):  # PR2022-05-03
            # this function converts the saved 'assignment' into a dict
            assignment_dict = {}
            assignment = row.get('assignment')
            if assignment:
                assignment_array = assignment.split('#')
                for assign_partex in assignment_array:
                    assign_partex_arr = assign_partex.split('|')
                    assign_partex_info = assign_partex_arr[0]
                    assign_partex_info_arr = assign_partex_info.split(';')
                    assign_partex_pk = int(assign_partex_info_arr[0]) if assign_partex_info_arr[0] else None

                    """
                    assign_partex_arr: ['1;4;48', '1;;20;', '2;;15;', '3;;8;', '4;;5;'] <class 'list'>
                    assign_partex_info: '1;4;48'
                    assign_partex_info_arr: ['1', '4', '48']
                    assign_partex_pk: 1 <class 'int'>
                    """

                    partex_dict = {}
                    for i, qa in enumerate(assign_partex_arr):
                        # skip first item, assign_partex_arr[0] already retrieved above
                        if i:
                            qa_arr = qa.split(';')

                            if len(qa_arr) == 4:
                                # qa_arr: ['1', 'C', '', ''] <class 'list'>
                                #       | q_number ; max_char ; max_score ; min_score |
                                q_nr = int(qa_arr[0])
                                partex_dict[q_nr] = {
                                    'max_char': qa_arr[1] if qa_arr[1] else '',
                                    'max_score': int(qa_arr[2]) if qa_arr[2] else '',
                                    'min_score': int(qa_arr[3]) if qa_arr[3] else ''
                                }

                    assignment_dict[assign_partex_pk] = partex_dict
                    """
                    assignment_dict: {1: {1: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 
                                          2: {'max_char': 'C', 'max_score': '', 'min_score': ''},  
                    """
            return assignment_dict

        def get_exam_keys_dict_from_row(row):  # PR2022-05-03
            # this function converts the saved 'keys' into a dict
            keys_dict = {}
            keys = row.get('keys')
            if keys:
                for keys_partex in keys.split('#'):
                    keys_partex_arr = keys_partex.split('|')
                    keys_partex_pk = int(keys_partex_arr[0]) if keys_partex_arr[0] else None
                    if keys_partex_pk:
                        for i, qk in enumerate(keys_partex_arr):
                            if i:
                                qk_arr = qk.split(';')
                                if len(qk_arr) == 2:
                                    qk_nr = int(qk_arr[0])
                                    if keys_partex_pk not in keys_dict:
                                        keys_dict[keys_partex_pk] = {}
                                    keys_dict[keys_partex_pk][qk_nr] = qk_arr[1] if qk_arr[1] else ''
            """
            keys_dict: {
                1: {1: 'a', 2: 'ab', 3: 'c', 4: 'b', 6: 'c', 7: 'a'}, 
                2: {1: 'b', 2: 'bd', 3: 'a', 4: 'c', 5: 'b', 8: 'c'}, 
                3: {2: 'd', 4: 'c', 5: 'b', 6: 'a', 7: 'c', 9: 'a', 10: 'a'}, 
                4: {2: 'c', 4: 'b', 5: 'c', 6: 'b', 7: 'c', 9: 'b'}, 
                5: {1: 'c', 2: 'c', 4: 'c', 6: 'c', 7: 'c'}, 
                6: {1: 'a', 2: 'd', 4: 'a', 6: 'b', 8: 'c'}
            }
            """
            return keys_dict

        def get_exam_result_dict(result_row):  # PR2022-03-16
            # this function converts the saved 'ce_exam_result' into a dict
            logging_on = False  # s.LOGGING_ON

            exam_result_dict = {}
            exam_result = result_row.get('ce_exam_result')
            """
            result_row: {
                'exam_id': 117, 
                'schoolbase_code': 'CUR03', 
                'ce_exam_blanks': None, 
                'ce_exam_result': '0;39#1|1;2|2;3|3;4|4;5#3|1;a|2;b|3;b|4;0|5;1|6;x|7;x|8;x#4|1;1|2;1|3;1#6|1;1|2;a|3;1|4;1|5;1|6;a|7;x#7|1;1#9|1;a|2;1|3;1|4;a|5;x|6;c|7;1#10|1;6#12|1;a|2;a|3;a|4;1|5;1|6;a|7;a|8;1', 
                'pegrade': None}
            """

            if exam_result:

                if logging_on:
                    logger.debug(' ')
                    logger.debug(' ----- get_exam_result_dict -----')
                    logger.debug('exam_result: ' + str(exam_result))
                """
                school_code: CUR01
                grade.ce_exam_result: 0;35#2|1;b|2;x|3;d|4;a|5;x|6;2|7;1|8;b|9;1#4|1;0|2;a|3;1|4;c|5;b|6;a|7;b|8;1|9;a|10;0#6|1;b|2;a|3;1|4;a|5;1|6;x|7;1|8;a|9;2|10;1#7|1;5|2;2|3;1#8|1;12#9|1;15#10|1;5
                """

                exam_result_array = exam_result.split('#')
                if logging_on:
                    logger.debug('exam_result_array: ' + str(exam_result_array))
                """
                result_array: ['0;35', '2|1;b|2;x|3;d|4;a|5;x|6;2|7;1|8;b|9;1', '4|1;0|2;a|3;1|4;c|5;b|6;a|7;b|8;1|9;a|10;0', '6|1;b|2;a|3;1|4;a|5;1|6;x|7;1|8;a|9;2|10;1', '7|1;5|2;2|3;1', '8|1;12', '9|1;15', '10|1;5']
                """
                for i, exam_result_str in enumerate(exam_result_array):
                    if logging_on:
                        logger.debug('exam_result_str: ' + str(exam_result_str))
                    if not i:
                        result_info_arr = exam_result_str.split(';')
                        result_info_blanks = int(result_info_arr[0]) if result_info_arr[0] else None
                        result_info_amount = int(result_info_arr[1]) if result_info_arr[1] else None
                        if logging_on:
                            logger.debug('result_info_blanks: ' + str(result_info_blanks) + ' ' + str(type(result_info_blanks)))
                            logger.debug('result_info_amount: ' + str(result_info_amount) + ' ' + str(type(result_info_amount)))

                        exam_result_dict['blanks'] = result_info_blanks
                        exam_result_dict['amount'] = result_info_amount

                    else:
                        """
                        exam_result_str = '2|1;b|2;x|3;d|4;a|5;x|6;2|7;1|8;b|9;1',
                        """
                        result_arr = exam_result_str.split('|')
                        partex_pk = int(result_arr[0]) if result_arr[0] else None

                        if logging_on:
                            logger.debug('result_arr: ' + str(result_arr))
                            logger.debug('partex_pk: ' + str(partex_pk))
                        """
                        result_arr: ['2', '1;b', '2;x', '3;d', '4;a', '5;x', '6;2', '7;1', '8;b', '9;1']
                        partex_pk: 2
                        """
                        partex_dict = {}
                        for i, qa in enumerate(result_arr):
                            if logging_on:
                                logger.debug('qa: ' + str(qa))
                            """
                            qa: 2;x
                            """
                            # skip first item, result_arr[0] already retrieved above
                            if i:
                                qa_arr = qa.split(';')
                                q_nr = int(qa_arr[0])
                                value = qa_arr[1]
                                partex_dict[q_nr] = value

                        exam_result_dict[partex_pk] = partex_dict
            if logging_on:
                logger.debug('>>> exam_result_dict: ' + str(exam_result_dict) + ' ' + str(type(exam_result_dict)))

            """
            exam_result_dict: {
                'blanks': 0, 'amount': 35, 
                2: {1: 'b', 2: 'x', 3: 'd', 4: 'a', 5: 'x', 6: '2', 7: '1', 8: 'b', 9: '1'}, 
                4: {1: '0', 2: 'a', 3: '1', 4: 'c', 5: 'b', 6: 'a', 7: 'b', 8: '1', 9: 'a', 10: '0'}, 
                6: {1: 'b', 2: 'a', 3: '1', 4: 'a', 5: '1', 6: 'x', 7: '1', 8: 'a', 9: '2', 10: '1'}, 
                7: {1: '5', 2: '2', 3: '1'}, 8: {1: '12'}, 9: {1: '15'}, 10: {1: '5'}}
            """

            return exam_result_dict

        def get_answers_list(result_rows, exam_partex_dict, exam_assignment_dict, exam_keys_dict):
            # - create dict with answers PR2021-05-08  PR2021-05-24 PR2022-03-16  PR2022-05-02

            logging_on = False  # s.LOGGING_ON
            if logging_on:
                logger.debug(' ----- get_answers_list -----')

            answer_list = []

            if result_rows:
                for result_row in result_rows:
                    exam_result_dict = get_exam_result_dict(result_row)
                    school_code = result_row.get('school_code') or '-'
                    exam_number = result_row.get('examnumber') or '-'
                    if logging_on:
                        logger.debug('>>> result_row: ' + str(result_row))
                        logger.debug('>>> exam_result_dict: ' + str(exam_result_dict))
                        logger.debug('>>> school_code: ' + str(school_code))
                    """
                    result_row: {
                        'exam_id': 45, 'schoolbase_code': 'CUR03', 
                        'ce_exam_result': '0;37#1|1;1|2;1|3;1|4;1|5;1|6;a|7;1|8;1|9;a|10;1|11;a|12;a|13;a|14;1|15;1|16;a|17;1|18;1|19;1|20;a|21;1|22;a|23;a|24;1|25;a|26;a|27;1|28;1|29;1|30;1|31;1|32;a|33;1|34;1|35;1|36;a|37;x'
                        }

                    exam_result_dict: {
                        'blanks': 0, 'amount': 35, 
                        2: {1: 'b', 2: 'x', 3: 'd', 4: 'a', 5: 'x', 6: '2', 7: '1', 8: 'b', 9: '1'}, 
                        4: {1: '0', 2: 'a', 3: '1', 4: 'c', 5: 'b', 6: 'a', 7: 'b', 8: '1', 9: 'a', 10: '0'}, 
                        6: {1: 'b', 2: 'a', 3: '1', 4: 'a', 5: '1', 6: 'x', 7: '1', 8: 'a', 9: '2', 10: '1'}, 
                        7: {1: '5', 2: '2', 3: '1'}, 8: {1: '12'}, 9: {1: '15'}, 10: {1: '5'}}
                    """

                    if exam_result_dict:
                        result_dict = {}
                        score_dict = {}

                        if logging_on:
                            logger.debug(' ----- get_answers_list -----')
                            logger.debug('exam_result_dict: ' + str(exam_result_dict))
                        """
                        exam_partex_dict: {1: {'pk': 1, 'tijdvak': 1, 'aantal vragen': 44, 'maximum score': 61, 'naam': 'Deelexamen 1'}}
                        """
                        for partex_pk, partex_dict in exam_partex_dict.items():
                            partex_assignment_dict = exam_assignment_dict.get(partex_pk)
                            partex_keys_dict = exam_keys_dict.get(partex_pk)
                            partex_amount = partex_dict.get('aantal vragen')
                            if logging_on:
                                logger.debug('............ ')
                                logger.debug('partex_amount: ' + str(partex_amount) + ' ' + str(type(partex_amount)))

                            # lookup partex_pk in exam_result_dict
                            # only the partex that the stuednet has dome are in exam_result_dict
                            partex_result_dict = exam_result_dict.get(partex_pk)
                            if logging_on:
                                logger.debug('partex_result_dict: ' + str(partex_result_dict))

                            """
                            partex_result_dict: {1: 'b', 2: 'x', 3: 'd', 4: 'a', 5: 'x', 6: '2', 7: '1', 8: 'b', 9: '1'} 
                            partex_result_dict: {1: '5', 2: '2', 3: '1'}
                            """
                            a_list = []

                            # score_list doesnt have to be added to json
                            # was:
                            score_list = []

                            if partex_result_dict:
                                for q_number in range(1, partex_amount + 1):  # range(start_value, end_value, step), end_value is not included!
                                    value_int = 0
                                    score_int = 0
                                    if q_number in partex_result_dict:
                                        value_str = partex_result_dict.get(q_number)
                                        if logging_on:
                                            logger.debug('q_number: ' + str(q_number) + ' ' + str(type(q_number)))
                                            logger.debug('     value_str: ' + str(value_str) + ' ' + str(type(value_str)))
                                        if value_str:
                                            is_multiple_choice = True if not value_str.isnumeric() else False
                                            if is_multiple_choice:
                                                value_lc = value_str.lower()
                                                if value_lc == 'x':
                                                    value_int = -1
                                                else:
                                                    asc_code = ord(value_lc)
                                                    value_int = asc_code - 96

                                                    if logging_on:
                                                        logger.debug('     value_lc: ' + str(value_lc) + ' ' + str(type(value_lc)))
                                                        logger.debug('     asc_code: ' + str(asc_code) + ' ' + str(type(asc_code)))
                                                        logger.debug('     value_int: ' + str(value_int) + ' ' + str(type(value_int)))

                                            # check if answer is correct
                                                    # partex_keys_dict: {1: 'a', 2: 'd', 4: 'a', 6: 'b', 8: 'c'} <class 'dict'>
                                                    keys = partex_keys_dict.get(q_number)
                                                    if logging_on:
                                                        logger.debug('..... partex_keys_dict: ' + str(partex_keys_dict))
                                                        logger.debug('..... keys: ' + str(keys) + ' ' + str(type(keys)))
                                                        logger.debug('..... partex_assignment_dict: ' + str(partex_assignment_dict))

                                                    if keys and value_lc in keys:
                                                        # lookup score in partex_assignment_dict
                                                        # partex_assignment_dict: {1: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 2: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 3: {'max_char': '', 'max_score': 1, 'min_score': ''}, 4: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 5: {'max_char': '', 'max_score': 1, 'min_score': ''}, 6: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 7: {'max_char': '', 'max_score': 1, 'min_score': ''}, 8: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 9: {'max_char': '', 'max_score': 2, 'min_score': ''}, 10: {'max_char': '', 'max_score': 1, 'min_score': ''}}
                                                        max_score = None
                                                        q_assignment = partex_assignment_dict.get(q_number)
                                                        if q_assignment:
                                                            max_score = q_assignment.get('max_score')
                                                        if logging_on:
                                                            logger.debug('..... q_assignment: ' + str(q_assignment) + ' ' + str(type(q_assignment)))
                                                            logger.debug('..... max_score: ' + str(max_score) + ' ' + str(type(max_score)))
                                                        score_int = max_score if max_score else 1
                                            else:
                                                value_int = int(value_str)
                                                score_int = value_int
                                                if logging_on:
                                                    logger.debug('     value_int: ' + str(value_int) + ' ' + str(type(value_int)))
                                                    logger.debug('     score_int: ' + str(score_int) + ' ' + str(type(score_int)))
                                    a_list.append(value_int)

                                    # score_list doesnt have to be added to json
                                    # was:
                                    score_list.append(score_int)
                            if logging_on:
                                logger.debug( '..... a_list: ' + str(a_list) + ' ' + str(type(a_list)))

                            if a_list:
                                result_dict[partex_pk] = a_list

                            # score_list doesnt have to be added to json
                            # was:
                            if score_list:
                                score_dict[partex_pk] = score_list

                        if logging_on:
                            logger.debug('result_dict: ' + str(result_dict) + ' ' + str(type(result_dict)))
                            logger.debug('score_dict: ' + str(score_dict) + ' ' + str(type(score_dict)))
                        """
                        result_dict: {1: [2, 3, 4, 5], 3: [1, 2, 2, 0, 1, -1, -1, -1], 4: [1, 1, 1], 6: [1, 1, 1, 1, 1, 1, -1], 7: [1], 9: [1, 1, 1, 1, -1, 3, 1], 10: [6], 12: [1, 1, 1, 1, 1, 1, 1, 1]}
                        score_dict:  {1: [2, 3, 4, 5], 3: [3, 2, 1, 0, 1, 0, 0, 0],    4: [1, 1, 1], 6: [1, 0, 1, 1, 1, 0, 0],  7: [1], 9: [0, 1, 1, 0, 0, 0, 1], 10: [6], 12: [1, 0, 1, 1, 1, 0, 0, 1]}
                        """
                        answer_list.append({'school': school_code, 'exnr': exam_number, 'responses': result_dict, 'score': score_dict} )
                        #answer_list.append({'school': school_code, 'exnr': exam_number, 'responses': result_dict})

            return answer_list
        # - end of get_answers_list

        response = None
        if request.user and request.user.country and request.user.schoolbase:
            req_usr = request.user

# - reset language
            user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear and from Usersetting
            selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
            sel_examyear, sel_department, sel_examperiod, sel_lvlbase_pk, sel_subject_pk = \
                acc_view.get_selected_ey_ep_dep_lvl_subj_from_usersetting(request, selected_pk_dict)

# - get selected examyear and examperiod from usersettings

            if logging_on:
                logger.debug('    sel_examyear: ' + str(sel_examyear))
                logger.debug('    sel_examperiod: ' + str(sel_examperiod))
                logger.debug('    sel_department: ' + str(sel_department))
                logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
                logger.debug('    sel_subject_pk: ' + str(sel_subject_pk))
            if sel_examperiod not in (c.EXAMPERIOD_FIRST, c.EXAMPERIOD_SECOND, c.EXAMPERIOD_THIRD):
                sel_examperiod = c.EXAMPERIOD_FIRST
                # save examperiod in usersettings
                new_setting_dict = {'sel_examperiod': sel_examperiod }
                acc_view.set_usersetting_from_upload_subdict(c.KEY_SELECTED_PK , new_setting_dict, request)

            examyear_txt = str(sel_examyear.code)
            examperiod_txt = c.get_examperiod_caption(sel_examperiod)

            ey_txt = examyear_txt + ' tv' + str(sel_examperiod)
            dep_txt = ''
            lvl_txt = ''
            subj_txt = ''

            examens_dict = {}
            if sel_examperiod in (1, 2):
                examenlijst = []

                exam_rows = get_exam_rows(sel_examyear.code, sel_examperiod, sel_department, sel_lvlbase_pk, sel_subject_pk, request)
                if logging_on:
                    logger.debug('exam_rows: ' + str(exam_rows))

                result_rows_dict = get_grade_exam_result_rows(sel_examyear.code, sel_examperiod,
                                           selected_pk_dict, request)

                if logging_on:
                    logger.debug('result_rows_dict: ' + str(result_rows_dict))

                for exam_row in exam_rows:
                    exam_dict = {}

                    exam_partex_dict = get_exam_partex_dict_from_row(exam_row)
                    exam_assignment_dict = get_exam_assignment_dict_from_row(exam_row)
                    exam_keys_dict = get_exam_keys_dict_from_row(exam_row)

                    assignment_list, partex_count, partex_schaallengte = \
                        get_assignment_list(exam_partex_dict, exam_assignment_dict, exam_keys_dict)

                    exam_id = exam_row.get('exam_id')
                    result_row = result_rows_dict.get(exam_id)

                    answers_list = get_answers_list(result_row, exam_partex_dict, exam_assignment_dict,
                                                    exam_keys_dict)

                    if logging_on:
                        logger.debug('result_row: ' + str(result_row))
                        logger.debug('answers_list: ' + str(answers_list))

                    subj_code = exam_row.get('subj_code') or '-'
                    exam_dict['code'] = subj_code
                    if not subj_txt:
                        subj_txt = ' ' + subj_code
                    elif ' ' + subj_code not in subj_txt:
                        subj_txt += ' ' + subj_code

                    exam_dict['vak'] = exam_row.get('subj_name_nl') or '-'

            # - create string with department abbrev
                    depbase_code = exam_row.get('depbase_code') or '-'
                    exam_dict['afdeling'] = depbase_code
                    if not dep_txt:
                        dep_txt = ' ' + depbase_code
                    elif ' ' + depbase_code not in dep_txt:
                        dep_txt += ' ' + depbase_code

                    if exam_row.get('version'):
                        exam_dict['versie'] =  exam_row.get('version')

            # - create string with level abbrevs
                    lvl_abbrev = exam_row.get('lvl_abbrev')
                    if lvl_abbrev:
                        exam_dict['leerweg'] = lvl_abbrev
                        if not lvl_txt:
                            lvl_txt = ' ' + lvl_abbrev
                        elif ' ' + lvl_abbrev not in lvl_txt:
                            lvl_txt += ' ' + lvl_abbrev

                    exam_dict['aantal vragen'] = exam_row.get('amount') or 0
                    exam_dict['schaallengte'] = exam_row.get('scalelength') or 0

                    exam_dict['deelexamens'] = assignment_list
                    exam_dict['kandidaten'] = answers_list

                    examenlijst.append(exam_dict)

                examens_dict = {
                    'examenjaar': examyear_txt,
                    'tijdvak': examperiod_txt,
                    'examens': examenlijst
                }

            file_name = ''.join(('Examenresultaten ', ey_txt, dep_txt , lvl_txt , subj_txt, '.json'))
            if logging_on:
                logger.debug('file_name: ' + str(file_name))

            response = HttpResponse(json.dumps(examens_dict), content_type="application/json")
            response['Content-Disposition'] = "exam_dict; filename=" + file_name + ""
            #response['Content-Disposition'] = 'inline; filename="testjson.pdf"'

        # except Exception as e:
        #     logger.error(getattr(e, 'message', str(e)))
        #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        #return JsonResponse({'test': 'json'})

# - end of ExamDownloadExamJsonView


@method_decorator([login_required], name='dispatch')
class ExamCopyWolfScoresView(View):  # PR2023-05-18

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamCopyWolfScoresView ============= ')

        def get_sub_sql(is_test):

            if logging_on:
                logger.debug('  ----- get_sub_sql -----')
                logger.debug('    sel_level: ' + str(sel_level))
                logger.debug('    sel_subject_pk: ' + str(sel_subject_pk))

            # see https://wiki.postgresql.org/wiki/Is_distinct_from
            sub_sql_list = ["SELECT grd.id AS grade_id, subj.id AS subject_id, subj.name_nl AS subject_name, exam.level_id, ",
                            "(grd.cescore IS DISTINCT FROM grd.ce_exam_score) AS change, ",
                            "(grd.cescore IS NOT NULL AND grd.cescore IS DISTINCT FROM grd.ce_exam_score) AS diff, ",
                            "(grd.cescore IS NOT NULL AND grd.cescore IS NOT DISTINCT FROM grd.ce_exam_score) AS same, ",

                            "(grd.ce_auth1by_id IS NOT NULL OR grd.ce_auth2by_id IS NOT NULL OR ",
                            "grd.ce_auth3by_id IS NOT NULL OR grd.ce_auth4by_id IS NOT NULL OR ",
                            "grd.ce_published_id IS NOT NULL) AS appr "

                            #"stud.lastname, stud.firstname, grd.cescore, grd.ce_exam_score "

                            "FROM students_grade AS grd ",
                            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id) ",
                            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id) ",
                            "INNER JOIN schools_school AS school ON (school.id = stud.school_id) ",
                            "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id) ",
                            "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id) ",

            # grade must have exam
                            "INNER JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id) ",
                            "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id) ",

                            "WHERE stud.school_id=", str(sel_school.pk), "::INT ",
                            "AND stud.department_id=", str(sel_department.pk), "::INT ",
                            "AND grd.examperiod=", str(sel_examperiod), "::INT ",

            # filter on wolf score has value
                            "AND grd.ce_exam_score IS NOT NULL ",

            # grdae, subj and stud may not be deleted or tobedeleted must be published
                            "AND NOT stud.deleted AND NOT stud.tobedeleted",
                            "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted",
                            "AND NOT grd.deleted AND NOT grd.tobedeleted",

            # exam must be published
                            "AND grd.ce_exam_published_id IS NOT NULL "
                            ]

            # set this filter only when updating
            if not is_test:
                # skip when grade score is (partly) approved or published
                sub_sql_list.extend(("AND grd.ce_auth1by_id IS NULL AND grd.ce_auth2by_id IS NULL ",
                                    "AND grd.ce_auth3by_id IS NULL AND grd.ce_auth4by_id IS NULL ",
                                    "AND grd.ce_published_id IS NULL ",
                # skip when wolf score and grade score are the same
                                     "AND grd.cescore IS DISTINCT FROM grd.ce_exam_score "
                                     ))

            if sel_department.level_req and sel_level:
                sub_sql_list.extend(("AND stud.level_id=", str(sel_level.pk), "::INT "))

            if sel_subject_pk:
                # PR2023-05-19 debug: don't filter on exam.subject_id, it can be differentt from  studsubj.scheeitem.subject_id
                # filter on sel_subjbase_pk instead.
                # was: sub_sql_list.extend(("AND exam.subject_id=", str(sel_subject_pk), "::INT "))
                sel_subject = subj_mod.Subject.objects.get_or_none(pk=sel_subject_pk)
                if logging_on:
                    logger.debug('    sel_subject: ' + str(sel_subject))
                if sel_subject:
                    sub_sql_list.extend(("AND subj.base_id=", str(sel_subject.base_id), "::INT "))

            sql_clause = acc_prm.get_sqlclause_allowed_v2(
                table='grade',
                sel_schoolbase_pk=sel_school.base.pk if sel_school else None,
                sel_depbase_pk=sel_department.base.pk if sel_department else None,
                sel_lvlbase_pk=sel_level.base.pk if sel_level else None,
                userallowed_sections_dict=acc_prm.get_userallowed_sections_dict_from_request(request),
                return_false_when_no_allowedsubjects=False
            )
            if sql_clause:
                sub_sql_list.append(sql_clause)

            return ' '.join(sub_sql_list)

        def test_scores():
            updated_list_sorted = []
            total_change = 0
            level_pk_list = []
            try:
                updated_dict = {}
                sub_sql = get_sub_sql(True)  # True: is_test
                with connection.cursor() as cursor:
                    cursor.execute(sub_sql)

                    for row in af.dictfetchall(cursor):
                        if logging_on and False:
                            logger.debug(' row: ' + str(row))

                        subject_id = row.get('subject_id')
                        if subject_id not in updated_dict:
                            updated_dict[subject_id] = {
                                'subject': row.get('subject_name') or '---',
                                'count': 0, 'change': 0, 'diff': 0, 'same': 0, 'appr': 0}
                        subject_dict = updated_dict[subject_id]
                        subject_dict['count'] += 1

                        if row.get('appr'):
                            subject_dict['appr'] += 1
                        elif row.get('same'):
                            subject_dict['same'] += 1
                        elif row.get('change'):
                            subject_dict['change'] += 1
                            total_change += 1
                            if row.get('diff'):
                                subject_dict['diff'] += 1

                        level_id = row.get('level_id')
                        if level_id not in level_pk_list:
                            level_pk_list.append(level_id)

                # convert dict to list
                updated_list = list(updated_dict.values())
                if logging_on and False:
                    for updated_row in updated_list:
                        logger.error('updated_row: ' + str(updated_row))
                # sort list to sorted dictlist
                # PR2021-11-15 from https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
                updated_list_sorted = sorted(updated_list, key=lambda d: d['subject'])

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

            if logging_on and False:
                logger.debug(' total_change: ' + str(total_change))
                for row in updated_list_sorted:
                    logger.debug(' row: ' + str(row))

            return updated_list_sorted, total_change, level_pk_list

        def copy_scores(request, sel_school, sel_department, sel_level, sel_examperiod, sel_subject_pk):
            # PR2022-05-15 field pescore was temporary used to store ce_exam_score
            # move value of pescore to field ce_exam_score, set pescore = null

            if logging_on:
                logger.debug('    sel_school: ' + str(sel_school))
                logger.debug('    sel_department: ' + str(sel_department))
                logger.debug('    sel_level: ' + str(sel_level))
                logger.debug('    sel_examperiod: ' + str(sel_examperiod))
                logger.debug('    sel_subject_pk: ' + str(sel_subject_pk))

            sub_sql = get_sub_sql(False)  # False: not is_test

            updated_grade_pk_list = []

            try:
                modifiedby_pk_str = str(request.user.pk)
                modifiedat_str = str(timezone.now())

                sql_list = [
                    "WITH sub_sql AS (", sub_sql, ")",
                    "UPDATE students_grade AS grade",
                    "SET cescore = ce_exam_score,",
                    "modifiedby_id=", modifiedby_pk_str, ", modifiedat='", modifiedat_str, "' ",

                    "FROM sub_sql",
                    "WHERE grade.id = sub_sql.grade_id",
                    "RETURNING grade.id"
                ]
                sql = ' '.join(sql_list)

                if logging_on and False:
                    for txt in sql_list:
                        logger.debug(' > ' + str(txt))

                with connection.cursor() as cursor:
                    cursor.execute(sql)

                    rows = cursor.fetchall()
                    if rows:
                        for row in rows:
                            updated_grade_pk_list.append(row[0])

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

            return updated_grade_pk_list

        def create_test_msg_list(updated_list_sorted, level_pk_list):

            if logging_on:
                logger.debug('  ----- create_test_msg_list -----')

            msg_list = []

            # - get number of subjects
            total_subject_count = len(updated_list_sorted)

            # get list of levels
            level_abbrev_list = []
            if level_pk_list:
                for level_pk in level_pk_list:
                    level = subj_mod.Level.objects.get_or_none(pk=level_pk)
                    if level:
                        level_abbrev_list.append(level.abbrev)

            level_abbrev_str = ''
            if level_abbrev_list:
                if len(level_abbrev_list) == 1:
                    level_abbrev_str = gettext(' in the learning path ')
                else:
                    level_abbrev_str = gettext(' in the learning paths ')
                level_abbrev_list_sorted = sorted(level_abbrev_list)
                level_abbrev_str += ', '.join(level_abbrev_list_sorted)

            if total_subject_count:
                msg_txt = gettext("The selection contains %(count)s") % {'count': get_subjects_count_text(total_subject_count, True)}
            else:
                msg_txt = gettext("The selection contains no submitted Wolf scores")

            msg_list.append(''.join(("<p class='pb-0'>", msg_txt, level_abbrev_str, ':</p>' if total_subject_count else '.</p>')))
            # +++ loop through exams
            if total_subject_count:
                for update_dict in updated_list_sorted:
                    msg_list.append("<div class='mx-2 mt-0 p-0'>")

                    # write examname in bold letters
                    subject_name = update_dict.get('subject', '-') or '-'
                    msg_list.append("<b>" + subject_name + "</b>")
                    msg_list.append("<div class='mx-2 mt-0 p-0'>")

                    # count candidates
                    # grade_exam_count cannot be zero because of INNER JOIN ce_exam exam_id
                    grade_exam_count = update_dict.get('count') or 0
                    change_count = update_dict.get('change') or 0
                    diff_count = update_dict.get('diff') or 0
                    same_count = update_dict.get('same') or 0
                    appr_count = update_dict.get('appr') or 0

                    msg_list.append(''.join(("<div class='pl-2'>",
                                             str(_("There %(is_are)s %(count)s with this exam and submitted Wolf scores.") % {
                                                 'is_are': get_is_are_txt(grade_exam_count),
                                                 'count': get_candidates_count_text(grade_exam_count)}),
                                             '</div>')))

                    if appr_count:
                        score_count = ' '.join(
                            (str(appr_count), gettext('CE scores are'))) if appr_count > 1 else gettext(
                            '1 CE score is')
                        same_txt = gettext('CE scores are') if appr_count > 1 else gettext('1 CE score is')
                        willbe_txt = pgettext_lazy('plural', 'will be') if appr_count > 1 else pgettext_lazy('singular',
                                                                                                             'will be')
                        msg_list.append(''.join(("<div class='pl-2'>",
                                                 str(_(
                                                     "%(count)s already approved and %(willbe)s skipped.") % {
                                                         'count': score_count, 'same': same_txt,
                                                         'willbe': str(willbe_txt)}),
                                                 '</div>')))

                    if same_count:
                        score_count = ' '.join((str(same_count), gettext('Wolf scores are'))) if same_count > 1 else gettext('1 Wolf score is')
                        same_txt = gettext('CE scores') if same_count > 1 else gettext('CE score')
                        willbe_txt = pgettext_lazy('plural', 'will be') if same_count > 1 else pgettext_lazy('singular', 'will be')
                        msg_list.append(''.join(("<div class='pl-2'>",
                                                 str(_("%(count)s the same as the %(same)s in the page 'Grades' and %(willbe)s skipped.") % {
                                                     'count': score_count, 'same': same_txt, 'willbe': str(willbe_txt)}),
                                                 '</div>')))

                    changed_count_txt = gettext('No scores will be') if not change_count else \
                                        gettext('1 score will be') if change_count == 1 else \
                                        ' '.join((str(change_count), gettext('scores will be')))
                    border_class = ' border_bg_valid' if change_count else ''
                    msg_list.append(''.join(("<div class='pl-2", border_class, "'>",
                                             str(_("%(count)s copied to the CE score in the page 'Grades'.") % {
                                                 'count': changed_count_txt}),
                                             '</div>')))

                    if diff_count:
                        score_count = ' '.join((str(diff_count), gettext('CE scores have'))) if diff_count > 1 else gettext('1 CE score has')
                        willbe_txt = pgettext_lazy('plural', 'will be') if diff_count > 1 else pgettext_lazy('singular', 'will be')
                        msg_list.append(''.join(("<div class='pl-2 border_bg_warning'><b>", gettext('ATTENTION'), '</b>: ',
                                                 gettext("%(count)s a different value in the page 'Grades' and %(willbe)s overwritten.") % {
                                                     'count': score_count, 'willbe': willbe_txt},
                                                 '</div>')))

                    msg_list.append("</div>")
                    msg_list.append("</div>")
            # +++ end of loop through exams

            class_str = 'border_bg_transparent'
            msg_list.insert(0, "<div class='p-2 " + class_str + "'>")
            msg_list.append("</div>")

            msg_html = ''.join(msg_list)

            return msg_html

        def create_updated_msg_list(updated_score_count):
            if logging_on:
                logger.debug('  ----- create_updated_msg_list -----')

            msg_list = ["<div class='p-2 border_bg_transparent'>"]

            score_count = gettext('No Wolf scores have been') if not updated_score_count else \
                gettext('1 Wolf score has been')  if updated_score_count == 1 else \
                ' '.join((str(updated_score_count), gettext('Wolf scores have been')))

            border_class = ' border_bg_valid' if updated_score_count else ''
            msg_list.append(''.join(("<div class='pl-2", border_class, "'>",
                                     gettext("%(count)s copied to the CE score in the page 'Grades'.") % {
                                         'count': score_count},
                                     '</div>')))
            msg_list.append("</div>")

            msg_html = ''.join(msg_list)

            return msg_html
######################

        req_usr = request.user
        msg_html = None
        update_wrap = {}

# - reset language
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            if logging_on:
                logger.debug('upload_dict' + str(upload_dict))

# - get permit
            has_permit = acc_prm.get_permit_of_this_page('page_wolf', 'submit_exam', request)

            if not has_permit:
                msg_html = acc_prm.err_html_no_permit()  # default: 'to perform this action')
            else:

    # - get exam_pk from upload_dict
                mode = upload_dict.get('mode')

    # - get selected examyear etc from Usersetting
                sel_examyear, sel_school, sel_department, sel_level, may_editNIU, msg_listNIU = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD) if selected_pk_dict else None
                sel_subject_pk = selected_pk_dict.get(c.KEY_SEL_SUBJECT_PK) if selected_pk_dict else None

                # note: exams can be changed before publishing examyear, therefore don't filter on examyear.published
                if mode and sel_examyear and sel_school and sel_department and sel_examperiod in (1, 2, 3):

                    if logging_on:
                        logger.debug('    sel_level: ' + str(sel_level))

        # if no sel_level: get array of allowed levels
                    #allowed_lvlbase_pk_arr, allowed_subjbases_arr = [], []
                    #if (sel_department.level_req and sel_level is None) or (sel_subject_pk is None):
                    #    requsr_allowed_sections_dict = acc_prm.get_userallowed_sections_dict_from_request(request)
                    #    allowed_schoolbase_dict, allowed_depbases_pk_arr = \
                    #        acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(
                    #            userallowed_sections_dict=requsr_allowed_sections_dict,
                    #            sel_schoolbase_pk=sel_school.base.pk
                    #        )
                    #    allowed_depbase_dict, allowed_lvlbase_pk_arr = acc_prm.get_userallowed_depbase_dict_lvlbases_pk_arr(
                    #        allowed_schoolbase_dict=allowed_schoolbase_dict,
                    #        sel_depbase_pk=sel_department.base.pk
                    #    )
                    #    sel_level_base_pk = sel_level.base.pk if sel_level else None
                    #    allowed_subjbases_arr = acc_prm.get_userallowed_subjbase_arr(allowed_depbase_dict, allowed_lvlbase_pk_arr, sel_level_base_pk)

                    if mode == 'is_test':
                        updated_list_sorted, total_change, level_pk_list = test_scores()
                        msg_html = create_test_msg_list(updated_list_sorted, level_pk_list)
                        update_wrap['total_change'] = total_change

                    elif mode == 'update_scores':
                        updated_grade_pk_list = copy_scores(request, sel_school, sel_department, sel_level, sel_examperiod, sel_subject_pk)
                        if updated_grade_pk_list:
                            calc_score.batch_update_finalgrade(
                                department_instance=sel_department,
                                grade_pk_list=updated_grade_pk_list
                        )

                        msg_html = create_updated_msg_list(len(updated_grade_pk_list))


        if msg_html:
            update_wrap['approve_msg_html'] = msg_html

        # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

# - end of ExamCopyWolfScoresView





def get_assignment_list(exam_partex_dict, exam_assignment_dict, exam_keys_dict):
    # - create list with assignments PR2021-05-08 PR2021-05-24 PR2022-03-15

    logging_on = False  # s.LOGGING_ON

    """        
    exam.partex: 1;1;3;0;Praktijkexamen onderdeel A#2;1;8;9;Minitoets 1 ROOD onderdeel A#3;1;8;9;Minitoets 1 BLAUW onderdeel A#4;1;4;0;Praktijkexamen onderdeel B#5;1;6;7;Minitoets 2 ROOD onderdeel B#6;1;6;7;Minitoets 2 BLAUW onderdeel B#7;1;8;8;Minitoets 3 ROOD onderdeel C#8;1;8;8;Minitoets 3 BLAUW onderdeel C#9;1;6;6;Minitoets 4 BLAUW onderdeel D#10;1;6;6;Minitoets 4 ROOD onderdeel D

    format of exam.partex is:
        partex are divided by "#"
            each item of partex contains: partex_pk ; partex_examperiod ; partex_amount ; max_score ; partex_name #

    exam_partex_dict: {1: {'pk': 1, 'tijdvak': 2, 'aantal vragen': 4, 'maximum score': 48, 'naam': 'praktijkexamen onderdeel A'}, 
                       2: {'pk': 2, 'tijdvak': 2, 'aantal vragen': 1, 'maximum score': 27, 'naam': 'Praktijkexamen onderdeel B'}, 
                       3: {'pk': 3, 'tijdvak': 2, 'aantal vragen': 5, 'maximum score': 57, 'naam': 'Praktijkexamen onderdeel C'}}
    """

    return_dict = {}

    """
    grade_dict.ce_exam_result = "1;3;0|1;;;|2;;;|3;;4;#2;2;4|1;C;;|2;D;3;"
    format of ce_exam_result_str is:
     - partal exams are separated with #
     - partex = "2;2;4|1;C;;|2;D;3;"
     first array between | contains partex info (blanks;total_amount), others contain answers info
     #  | partex_pk |
        | q_number ; char ; score ; blank |
    """

    """
    exam.assignment: 1;4;24|1;;10;|2;;4;|3;;4;|4;;6;#2;9;9|1;D;;|2;D;;|3;;1;|4;;1;|5;D;;|6;D;;|7;;1;|8;D;;|9;C;;#3;9;9|1;D;;|2;D;;|3;;1;|4;;1;|5;D;;|6;D;;|7;;1;|8;D;;|9;C;;#4;4;28|1;;6;|2;;6;|3;;6;|4;;10;#5;9;10|1;D;;|2;;1;|3;D;;|4;;2;|5;D;;|6;;1;|7;D;;|8;D;;|9;D;;#6;9;10|1;D;;|2;;1;|3;D;;|4;;2;|5;D;;|6;;1;|7;D;;|8;D;;|9;D;;#7;3;20|1;;10;|2;;6;|3;;4;#8;9;9|1;D;;|2;;1;|3;;1;|4;;1;|5;D;;|6;;1;|7;D;;|8;D;;|9;D;;#9;9;9|1;D;;|2;;1;|3;;1;|4;;1;|5;D;;|6;;1;|7;D;;|8;D;;|9;D;;#10;2;16|1;;10;|2;;6;#11;10;10|1;;1;|2;;1;|3;D;;|4;;1;|5;D;;|6;;1;|7;D;;|8;D;;|9;D;;|10;;1;#12;10;10|1;;1;|2;;1;|3;D;;|4;;1;|5;D;;|6;;1;|7;D;;|8;D;;|9;D;;|10;;1;

    format of assignment_str is:
        partex are divided by "#"
            first item of partex contains partex info: partex_pk ; partex_amount ; max_score |
            other items =  | q_number ; max_char ; max_score ; min_score |

    format of keys_str is:
        partex are divided by "#"
            first item of partex contains partex_pk
            other items =  | q_number ; keys |
    """

    partex_count = 0
    partex_schaallengte = None

    for partex_pk, partex_dict in exam_partex_dict.items():
        partex_assignment_dict = exam_assignment_dict.get(partex_pk)
        partex_keys_dict = exam_keys_dict.get(partex_pk)
        partex_amount = partex_dict.get('aantal vragen')

        partex_count += 1
        partex_schaallengte = partex_dict.get('schaallengte') if partex_count == 1 else None

        partex_assignment_list = []
        if logging_on and False:
            logger.debug('---------------- partex_pk: ' + str(partex_pk) + ' ' + str(type(partex_pk)))
            logger.debug('partex_amount: ' + str(partex_amount) + ' ' + str(type(partex_amount)))
            logger.debug('partex_dict: ' + str(partex_dict) + ' ' + str(type(partex_dict)))

            logger.debug('partex_keys_dict: ' + str(partex_keys_dict) + ' ' + str(type(partex_keys_dict)))
        if logging_on:
            logger.debug('---------------- partex_count: ' + str(partex_count) + ' ' + str(type(partex_count)))
            logger.debug('---------------- partex_schaallengte: ' + str(partex_schaallengte) + ' ' + str(type(partex_schaallengte)))
        """
        partex_pk: 1 <class 'int'>
        partex_dict: {'pk': 1, 'tijdvak': 1, 'aantal vragen': 44, 'maximum score': 61, 'naam': 'Deelexamen 1'} <class 'dict'>
        partex_assignment_dict: {1: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 2: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 3: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 4: {'max_char': '', 'max_score': 1, 'min_score': ''}, 5: {'max_char': '', 'max_score': 2, 'min_score': ''}, 6: {'max_char': '', 'max_score': 2, 'min_score': ''}, 7: {'max_char': '', 'max_score': 1, 'min_score': ''}, 8: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 9: {'max_char': '', 'max_score': 2, 'min_score': ''}, 10: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 11: {'max_char': '', 'max_score': 2, 'min_score': ''}, 12: {'max_char': '', 'max_score': 2, 'min_score': ''}, 13: {'max_char': '', 'max_score': 2, 'min_score': ''}, 14: {'max_char': '', 'max_score': 1, 'min_score': ''}, 15: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 16: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 17: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 18: {'max_char': '', 'max_score': 2, 'min_score': ''}, 19: {'max_char': '', 'max_score': 2, 'min_score': ''}, 20: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 21: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 22: {'max_char': '', 'max_score': 1, 'min_score': ''}, 23: {'max_char': 'C', 'max_score': '', 'min_score': ''}, 24: {'max_char': '', 'max_score': 2, 'min_score': ''}, 25: {'max_char': '', 'max_score': 1, 'min_score': ''}, 26: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 27: {'max_char': '', 'max_score': 1, 'min_score': ''}, 28: {'max_char': '', 'max_score': 2, 'min_score': ''}, 29: {'max_char': '', 'max_score': 1, 'min_score': ''}, 30: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 31: {'max_char': '', 'max_score': 2, 'min_score': ''}, 32: {'max_char': '', 'max_score': 2, 'min_score': ''}, 33: {'max_char': '', 'max_score': 2, 'min_score': ''}, 34: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 35: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 36: {'max_char': '', 'max_score': 2, 'min_score': ''}, 37: {'max_char': '', 'max_score': 1, 'min_score': ''}, 38: {'max_char': '', 'max_score': 2, 'min_score': ''}, 39: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 40: {'max_char': '', 'max_score': 2, 'min_score': ''}, 41: {'max_char': '', 'max_score': 1, 'min_score': ''}, 42: {'max_char': '', 'max_score': 1, 'min_score': ''}, 43: {'max_char': 'D', 'max_score': '', 'min_score': ''}, 44: {'max_char': '', 'max_score': 2, 'min_score': ''}} <class 'dict'>
        partex_keys_dict: {1: 'a', 2: 'ab', 3: 'c', 4: 'b', 6: 'c', 7: 'a'}

        """
        for q_number in range(1, partex_amount + 1):  # range(start_value, end_value, step), end_value is not included!
            q_dict = {'nr': q_number}
            if logging_on:
                logger.debug('      q_number: ' + str(q_number) + ' ' + str(type(q_number)))

            if q_number in partex_assignment_dict:
                max_score = af.get_dict_value(partex_assignment_dict, (q_number, 'max_score'), '')
                max_score_int = int(max_score) if max_score else 0
                max_char = af.get_dict_value(partex_assignment_dict, (q_number, 'max_char'), '')
                is_multiple_choice = True if max_char else False

                if is_multiple_choice:
                    # alternatives = number of choices: max_char = C --> alternatives = 3
                    asc_code = ord(max_char.lower())
                    alternatives = asc_code - 96
                    if logging_on:
                        logger.debug('alternatives: ' + str(alternatives) + ' ' + str(type(alternatives)))

                    q_dict['opgavetype'] = 'Meerkeuze'
                    q_dict['alternatieven'] = alternatives
                    q_dict['maximum score'] = max_score_int if max_score_int else 1

                    if partex_keys_dict:
                        keys_str = partex_keys_dict.get(q_number)
                        if logging_on:
                            logger.debug( '             keys_str: ' + str(keys_str) + ' ' + str(type(keys_str)))

                        if keys_str:
                            key_list = list(keys_str)
                            if logging_on:
                                logger.debug('key_list: ' + str(key_list) + ' ' + str(type(key_list)))

                            key_int_list = []
                            for key_str in key_list:
                                if logging_on:
                                    logger.debug('key_str: ' + str(key_str) + ' ' + str(type(key_str)))

                                asc_code = ord(key_str.lower())
                                if logging_on:
                                    logger.debug('asc_code: ' + str(asc_code) + ' ' + str(type(asc_code)))

                                key_int = asc_code - 96
                                if key_int < 1 or key_int > alternatives:
                                    key_int = -1
                                if logging_on:
                                    logger.debug('key_int: ' + str(key_int) + ' ' + str(type(key_int)))
                                key_int_list.append(key_int)
                                if logging_on:
                                    logger.debug('key_int_list: ' + str(key_int_list) + ' ' + str(type(key_int_list)))

                            q_dict['sleutel'] = key_int_list
                else:
                    q_dict['opgavetype'] = 'Open'
                    q_dict['maximum score'] = max_score_int

            partex_assignment_list.append(q_dict)
            if logging_on:
                logger.debug('partex_assignment_list: ' + str(partex_assignment_list) + ' ' + str(type(partex_assignment_list)))
            """
            partex_assignment_list: [{'nr': 1, 'opgavetype': 'Meerkeuze', 'alternatieven': 3, 'sleutel': [2]}, 
                                     {'nr': 2, 'opgavetype': 'Meerkeuze', 'alternatieven': 3, 'sleutel': [3]}, 
                                     {'nr': 3, 'opgavetype': 'Meerkeuze', 'alternatieven': 3, 'sleutel': [3]}, 
                                     {'nr': 4, 'opgavetype': 'Open', 'maximum score': 1}, 
            """
            partex_dict['opgaven'] = partex_assignment_list

        return_dict[partex_pk] = partex_dict
        #assignment_list.append(partex_dict)
        """
        return_dict: { 
            1: {'pk': 1, 'tijdvak': 1, 'aantal vragen': 44, 'maximum score': 61, 'naam': 'Deelexamen 1', 
                'opgaven': [
                    {'nr': 1, 'opgavetype': 'Meerkeuze', 'alternatieven': 3, 'sleutel': [2]}, 
                    {'nr': 2, 'opgavetype': 'Meerkeuze', 'alternatieven': 3, 'sleutel': [3]}, 
                    {'nr': 3, 'opgavetype': 'Meerkeuze', 'alternatieven': 3, 'sleutel': [3]}, 
                    {'nr': 4, 'opgavetype': 'Open', 'maximum score': 1}, 
                    {'nr': 5, 'opgavetype': 'Open', 'maximum score': 2}, 
        """

    return return_dict, partex_count, partex_schaallengte
# - end of get_assignment_list


def get_ce_examresult_rows():
    #PR2022-03-15
    # TODO replace Grade.objects.filter(ce_exam=sel_exam_instance) in get_answers_list
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_ce_examresult_rows -----')

    examyear_pk, school_pk, department_pk, examperiod = None, None, None, None
    sql_keys = {'ey_id': examyear_pk, 'sch_id': school_pk, 'dep_id': department_pk, 'experiod': examperiod}
    sql_list = ["SELECT stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
                "lvl.id AS level_id, lvl.base_id AS levelbase_id, lvl.abbrev AS lvl_abbrev,",
                "subj.id AS subj_id, subjbase.code AS subj_code, subj.name_nl AS subj_name_nl",

                "FROM students_grade AS grd",
                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",

                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "WHERE ey.id = %(ey_id)s::INT",
                "AND school.id = %(sch_id)s::INT",
                "AND dep.id = %(dep_id)s::INT",
                "AND NOT grd.tobedeleted AND NOT grd.deleted AND NOT studsubj.tobedeleted",
                "AND grd.examperiod = %(experiod)s::INT",

                "ORDER BY LOWER(subj.name_nl), LOWER(stud.lastname), LOWER(stud.firstname)"
                ]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        grade_rows = af.dictfetchall(cursor)
# - end of get_ce_examresult_rows


def get_department_codes(sel_exam_instance, examyear):
    # - create string with depbase codes PR2021-05-09
    dep_codes = ''
    depbases = sel_exam_instance.depbases
    if depbases:
        arr = depbases.split(';')
        if arr:
            for pk_str in arr:
                if pk_str:
                    pk_int = int(pk_str)
                    department = sch_mod.Department.objects.get_or_none(
                        base_id=pk_int,
                        examyear=examyear
                    )
                    if department:
                        if dep_codes:
                            dep_codes += ', '
                        dep_codes += department.base.code
    return dep_codes


# NIU, may be used for other instances with depbases
def get_department_abbrevs(sel_exam_instance, examyear):
    # - create string with depbase abbrevs PR2021-05-08
    dep_abbrevs = ''
    depbases = sel_exam_instance.depbases
    if depbases:
        arr = depbases.split(';')
        if arr:
            for pk_str in arr:
                if pk_str:
                    pk_int = int(pk_str)
                    department = sch_mod.Department.objects.get_or_none(
                        base_id=pk_int,
                        examyear=examyear
                    )
                    if department:
                        if dep_abbrevs:
                            dep_abbrevs += ', '
                        dep_abbrevs += department.abbrev
    return dep_abbrevs


def get_level_abbrevs(exam_instance, examyear):
    # - create string with level abbrevs PR2021-05-08
    level_names = ''
    levelbases = exam_instance.levelbases
    if levelbases:
        arr = levelbases.split(';')
        if arr:
            for pk_str in arr:
                if pk_str:
                    pk_int = int(pk_str)
                    level = subj_mod.Level.objects.get_or_none(
                        base_id=pk_int,
                        examyear=examyear
                    )
                    if level:
                        if level_names:
                            level_names += ', '
                        level_names += level.abbrev
    return level_names



def create_department_dictlist(examyear_instance):  # PR2021-09-01 PR2022-10-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_department_dictlist -----')

    # PR2021-08-20 functions creates ordered dictlist of all departments of this exam year of all countries
    # PR2021-09-02 debug: filter on examyear.code returned each depbase twice. Select ey_pk, same depbase is used in Cur and SXM
    # was: NOTE: use examyear.code (integer field) to filter on examyear. This way depbases from SXM and CUR are added to list
    sql_keys = {'ey_pk': examyear_instance.pk}
    sql_list = [
        "SELECT depbase.id AS depbase_id, depbase.code AS depbase_code, dep.name AS dep_name, dep.level_req AS dep_level_req ",

        "FROM schools_department AS dep",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",

        "WHERE ey.id = %(ey_pk)s::INT",
        "ORDER BY dep.sequence"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        dictlist = af.dictfetchall(cursor)

    if logging_on:
        logger.debug('dictlist: ' + str(dictlist))

    return dictlist
# --- end of create_department_dictlist


def create_level_dictlist(examyear_instance):  # PR2021-09-01 PR2022-10-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_level_dictlist -----')

    # PR2021-09-01 functions creates ordered dictlist of all levels of this exam year of all countries
    # also add row with pk = 0 for Havo / Vwo

    # PR2021-09-02 debug: filter on examyear.code returned each depbase twice. Select ey_pk, same depbase is uses in Cur and SXM
    # was: NOTE: use examyear.code (integer field) to filter on examyear. This way lvlbases from SXM and CUR are added to list

    # fields are lvlbase_id, lvlbase_code, lvl_name",
    sql_keys = {'ey_pk': examyear_instance.pk}
    sql_list = [
        "SELECT lvlbase.id AS lvlbase_id, lvlbase.code AS lvlbase_code, lvl.name AS lvl_name ",

        "FROM subjects_level AS lvl",
        "INNER JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = lvl.examyear_id)",

        "WHERE ey.id = %(ey_pk)s::INT",
        "ORDER BY lvl.sequence"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        dictlist = af.dictfetchall(cursor)

    # add row with pk = 0 for Havo / Vwo
    dictlist.append({'lvlbase_id': 0, 'lvlbase_code': '', 'lvl_name': ''})

    if logging_on:
        logger.debug('dictlist: ' + str(dictlist))

    return dictlist
# --- end of create_level_dictlist


def create_schoolbase_dictlist(examyear, request, schoolbase_pk_list = None):
    # PR2021-08-20 PR2021-10-14 PR2022-10-31 PR2023-03-02
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug ('----- create_schoolbase_dictlist -----')

    # PR2021-08-20 functions creates ordered dictlist of all schoolbase_pk, schoolbase_code and school_name
    # - of this exam year, of all countries

    # - country: when req_usr country = cur: include all schools (inluding SXM schools)
    #            when req_usr country = sxm: show only SXM schools

    # - skip schools of other organizations than schools
    # - also add admin organization (ETE, DOE), for extra for ETE, DOE

    # NOTE: use examyear.code (integer field) to filter on examyear. This way schoolbases from SXM and CUR are added to list

    # called by: create_orderlist_xlsx, create_orderlist_per_school_xlsx and OrderlistsPublishView

    if request.user.country.abbrev.lower() == 'sxm':
        show_sxm_schools_only = ''.join(("AND ey.country_id=", str(request.user.country.pk), "::INT "))
    else:
        show_sxm_schools_only = ''

    sql_list = [
        "SELECT sbase.id AS sbase_id, sbase.code AS sbase_code, sch.depbases, sch.otherlang AS sch_otherlang, ",
        "sch.article AS sch_article, sch.name AS sch_name, sch.abbrev AS sch_abbrev, sbase.defaultrole ",

        "FROM schools_school AS sch ",
        "INNER JOIN schools_schoolbase AS sbase ON (sbase.id = sch.base_id) ",
        "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id) ",

        "WHERE ey.code=" + str(examyear.code) + "::INT ",
        "AND (sbase.defaultrole=", str(c.ROLE_008_SCHOOL), "::INT OR sbase.defaultrole=", str(c.ROLE_064_ADMIN), "::INT) ",
        show_sxm_schools_only
        ]

    # - filter on parameter schoolbase_pk_list when it has value
    if schoolbase_pk_list:
        sql_list.append(''.join(("AND sbase.id IN (SELECT UNNEST(ARRAY", str(schoolbase_pk_list), "::INT[])) ")))

    sql_list.append("ORDER BY LOWER(sbase.code);")
    sql = ''.join(sql_list)

    if logging_on:
        logger.debug('    sql: ' + str(sql))

    with connection.cursor() as cursor:
        cursor.execute(sql)
        dictlist = af.dictfetchall(cursor)

    if logging_on:
        logger.debug('schoolbase_dictlist: ' + str(dictlist))
    # schoolbase_dictlist: [
    #   {'sbase_id': 2, 'sbase_code': 'CUR01', 'depbases': '1', 'sch_otherlang': None, 'sch_article': 'de', 'sch_name': 'Ancilla Domini Vsbo', 'sch_abbrev': 'Ancilla Domini', 'defaultrole': 8},
    #   {'sbase_id': 4, 'sbase_code': 'CUR03', 'depbases': '1', 'sch_otherlang': None, 'sch_article': 'de', 'sch_name': 'Juan Pablo Duarte Vsbo', 'sch_abbrev': 'JPD', 'defaultrole': 8}]

    return dictlist
# --- end of create_schoolbase_dictlist


def create_subjectbase_dictlist(examyear):  # PR2021-08-20
    logging_on = False  # s.LOGGING_ON

    # PR2021-08-20 functions creates ordered dictlist of all subjectbase pk and code of this exam year of all countries
    # NOTE: use examyear.code (integer field) to filter on examyear. This way subjects from SXM and CUR are added to list

    sql_keys = {'ey_int': examyear.code}
    sql_list = [
        "SELECT subjbase.id, subjbase.code ",

        "FROM subjects_subject AS subj",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

        "WHERE ey.code = %(ey_int)s::INT",
        "GROUP BY subjbase.id, subjbase.code",
        "ORDER BY LOWER(subjbase.code)"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        subjectbase_dictlist = af.dictfetchall(cursor)

    if logging_on:
        logger.debug ('----- create_subjectbase_dictlist -----')
        logger.debug('subjectbase_dictlist: ' + str(subjectbase_dictlist))

    return subjectbase_dictlist
# --- end of create_subjectbase_dictlist



# from https://github.com/jmcnamara/XlsxWriter/blob/main/xlsxwriter/utility.py PR2021-08-30

def xl_rowcol_to_cell(row, col, row_abs=False, col_abs=False):
    """
    Convert a zero indexed row and column cell reference to a A1 style string.
    Args:
       row:     The cell row.    Int.
       col:     The cell column. Int.
       row_abs: Optional flag to make the row absolute.    Bool.
       col_abs: Optional flag to make the column absolute. Bool.
    Returns:
        A1 style string.
    """
    if row is None or row < 0:
        return None

    if col is None or col < 0:
        return None

    row += 1  # Change to 1-index.
    row_abs = '$' if row_abs else ''

    col_str = xl_col_to_name(col, col_abs)

    return col_str + row_abs + str(row)


def xl_col_to_name(col, col_abs=False):
    """
    Convert a zero indexed column cell reference to a string.
    Args:
       col:     The cell column. Int.
       col_abs: Optional flag to make the column absolute. Bool.
    Returns:
        Column style string.
    """
    col_num = col
    if col_num is None or col_num < 0:
        return None

    col_num += 1  # Change to 1-index.
    col_str = ''
    col_abs = '$' if col_abs else ''

    while col_num:
        # Set remainder from 1 .. 26
        remainder = col_num % 26

        if remainder == 0:
            remainder = 26

        # Convert the remainder to a character.
        col_letter = chr(ord('A') + remainder - 1)

        # Accumulate the column letters, right to left.
        col_str = col_letter + col_str

        # Get the next order of magnitude.
        col_num = int((col_num - 1) / 26)

    return col_abs + col_str
#---------------------------------------


def get_subjects_count_text(count, has_submitted_txt=False):
    #PR2023-05-22


    return ' '.join(filter(None, (
        str(pgettext_lazy('geen', 'no ') if not count else count),
        gettext('submitted') if count == 1 else
        str(pgettext_lazy('ingediende', 'submitted')) if has_submitted_txt else None,
        gettext('Subject').lower() if count == 1 else gettext('Subjects').lower()
    )))


def get_subjects_have_text(count):
    return ' '.join((get_subjects_count_text(count), ' ', get_has_have_txt(count)))


def get_exam_count_text(count):
    exam_str = str(_('exam') if count == 1 else _('exams'))
    count_str = str(pgettext_lazy('geen', 'no ') if not count else count)
    return ' '.join((count_str, exam_str))


def get_exams_are_text(count):
    return ' '.join((get_exam_count_text(count), ' ', get_is_are_txt(count)))


def get_exams_have_text(count):
    return ' '.join((get_exam_count_text(count), ' ', get_has_have_txt(count)))


def get_candidates_count_text(count):
    exam_str = str(_('Candidate') if count == 1 else _('Candidates')).lower()
    count_str = str(pgettext_lazy('geen', 'no') if not count else str(count))
    return ' '.join((count_str, exam_str))


def get_is_are_txt(count):
    return str(pgettext_lazy('singular', 'is') if  count == 1 else pgettext_lazy('plural', 'are'))


def get_will_be_text(count):
    return str(pgettext_lazy('singular', 'will be') if  count == 1 else pgettext_lazy('plural', 'will be'))


def get_willbe_or_are_txt(is_test, count):
    return get_will_be_text(count) if is_test else get_is_are_txt(count)


def get_has_have_txt(count):
    return str(pgettext_lazy('singular', 'has') if count == 1 else pgettext_lazy('plural', 'have'))


def get_could_txt(count):
    return str(pgettext_lazy('singular', 'could') if count == 1 else pgettext_lazy('plural', 'could'))


def get_have_has_been_txt(count):
    return str(pgettext_lazy('singular', 'has been') if count == 1 else pgettext_lazy('plural', 'have been'))
