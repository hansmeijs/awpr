# PR2021-11-15
from datetime import datetime, timedelta
from random import randint

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

# PR2019-01-04  https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise

# PR2022-02-13 From Django 4 we dont have force_text You Just have to Use force_str Instead of force_text.
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder


from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Frame, Spacer, Image


from accounts import models as acc_mod
from accounts import views as acc_view
from awpr import menus as awpr_menu, excel as grd_exc
from awpr import constants as c
from awpr import settings as s
from awpr import validators as av
from awpr import functions as af
from awpr import downloads as dl
from awpr import library as awpr_lib

from grades import views as grd_vw

from schools import models as sch_mod
from students import models as stud_mod
from students import functions as stud_fnc
from subjects import models as subj_mod
from students import validators as stud_val
from grades import views as gr_vw

from os import path
import io
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
class ResultListView(View):  # PR2021-11-15

    def get(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('  =====  ResultListView ===== ')

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_result'
        params = awpr_menu.get_headerbar_param(request, page)

# - save this page in Usersetting, so at next login this page will open. Used in LoggedIn
        #         # PR2021-06-22 moved to get_headerbar_param

        return render(request, 'results.html', params)


@method_decorator([login_required], name='dispatch')
class GetPresSecrView(View):  # PR2021-11-19

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GetPresSecrView ============= ')

        update_wrap = {}
        messages = []

        # - get permit
        has_permit = af.get_permit_crud_of_this_page('page_result', request)
        if True:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

      # ----- pres_secr_rows, used in results.js
                pres_secr_dict = get_pres_secr_dict(request)

                update_wrap['pres_secr_dict'] = pres_secr_dict
                if logging_on:
                    logger.debug('pres_secr_dict: ' + str(pres_secr_dict))

        # - addd messages to update_wrap
        if len(messages):
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentUploadView



def get_pres_secr_dict(request):  # PR2021-11-18
    # function creates a dict of auth1 and auth2 users
    # also retrieves the selected auth and printdate from schoolsettings

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_pres_secr_dict -----')

# get selected auth and printdatum from schoolsettings
    settings_json = request.user.schoolbase.get_schoolsetting_dict(c.KEY_GRADELIST)
    stored_setting = json.loads(settings_json) if settings_json else {}
    if logging_on:
        logger.debug('stored_setting: ' + str(stored_setting))
        # stored_setting: {'auth1_pk': 120, 'auth2_pk': None, 'printdate': None}

    # auth_dict: {'auth1': [{'pk': 120, 'name': 'jpd'}, {'pk': 116, 'name': 'Hans meijs'}], 'auth2': []}
    sql_keys = {'sb_id': request.user.schoolbase_id, 'c_id': request.user.country_id, 'role': c.ROLE_008_SCHOOL}
    sql_list = ["SELECT au.id, au.last_name,",
                "(POSITION('" + c.USERGROUP_AUTH1_PRES + "' IN au.usergroups) > 0) AS auth1,",
                "(POSITION('" + c.USERGROUP_AUTH2_SECR + "' IN au.usergroups) > 0) AS auth2",

                "FROM accounts_user AS au",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = au.schoolbase_id)",
                "INNER JOIN schools_country AS c ON (c.id = au.country_id)",

                "WHERE sb.id = %(sb_id)s::INT AND c.id = %(c_id)s::INT AND au.role = %(role)s::INT",
                "AND ( (POSITION('" + c.USERGROUP_AUTH1_PRES + "' IN au.usergroups) > 0)",
                "OR (POSITION('" + c.USERGROUP_AUTH2_SECR + "' IN au.usergroups) > 0 ) )"
                "AND au.activated AND au.is_active"
                ]
    sql = ' '.join(sql_list)
    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    auth_dict = {'auth1': [], 'auth2': []}
    for row in rows:
        if logging_on:
            logger.debug('row: ' + str(row))
            # row: {'id': 47, 'last_name': 'Hans', 'auth1': False, 'auth2': True}
        for usergroup in ('auth1', 'auth2'):
            if row.get(usergroup, False):
                last_name = row.get('last_name')
                if last_name:
                    pk_int = row.get('id')
                    a_dict = {'pk': pk_int, 'name': last_name}
                    selected_auth_pk = stored_setting.get(usergroup + '_pk')
                    if selected_auth_pk and selected_auth_pk == pk_int:
                        a_dict['selected'] = True
                    auth_dict[usergroup].append(a_dict)
# add printdate
    print_date = stored_setting.get('printdate')
    if print_date:
        auth_dict['printdate'] = print_date

    return auth_dict
# - -end of get_pres_secr_dict



# end of GetPresSecrView

@method_decorator([login_required], name='dispatch')
class DownloadGradelistView(View):  # PR2021-11-15

    def get(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= DownloadGradelistView ============= ')

        # TODO for uploading Exs with signatures:
        # - give each Ex3 a sequence , print under Ex3 in box
        # - create table mapped_ex3 with field Ex3 sequence and field with all grade_pks of that Ex3
        # when uploading: user types Ex3 number when uploading Ex3,
        # Awp links grades of that Ex3 to the uploaded file
        # in grade table: add column with href to the uploaded Ex3 form

        # function creates, pdf file based on settings in list and usersetting

        response = None

        if request.user and request.user.country and request.user.schoolbase and list:
            upload_dict = json.loads(list) if list != '-' else {}
            if logging_on:
                logger.debug('upload_dict: ' + str(upload_dict))
                # upload_dict: {'mode': 'prelim', 'print_all': False, 'student_pk_list': [8629], 'auth1_pk': 116, 'printdate': '2021-11-18'}
            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)
            sel_lvlbase_pk, sel_sctbase_pk = dl.get_selected_lvlbase_sctbase_from_usersetting(request)
            if logging_on:
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))

            if sel_school and sel_department:

# - save printdate and auth in schoolsetting
                mode =  upload_dict.get('mode')
                is_prelim = mode == 'prelim'
                auth1_pk = upload_dict.get('auth1_pk')
                auth2_pk = upload_dict.get('auth2_pk')
                printdate = upload_dict.get('printdate')
                student_pk_list = upload_dict.get('student_pk_list')

                settings_key = c.KEY_GRADELIST
                new_setting_dict = {
                    'auth1_pk': auth1_pk,
                    'auth2_pk': auth2_pk,
                    'printdate': printdate,
                }

                new_setting_json = json.dumps(new_setting_dict)
                request.user.schoolbase.set_schoolsetting_dict(settings_key, new_setting_json)

# - get library from examyearsetting
                library = awpr_lib.get_library(sel_examyear, ['gradelist'])

# +++ get grade_dictlist
                student_list = get_grade_dictlist(sel_examyear, sel_school, sel_department, sel_lvlbase_pk, sel_sctbase_pk,
                                                  student_pk_list)

 # +++ get name of president and secretary
                # auth_dict = get_pres_secr_dict(request)

                # - get arial font
                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'arial.ttf'
                    ttfFile = TTFont('Arial', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                # - get Palace_Script_MT font - for testing - it works 2021-10-14
                """
                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'Palace_Script_MT.ttf'
                    ttfFile = TTFont('Palace_Script_MT', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))
                """
                # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

                # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                # temp_file = tempfile.TemporaryFile()
                # canvas = Canvas(temp_file)

                buffer = io.BytesIO()
                canvas = Canvas(buffer)

                for student_dict in student_list:
                    draw_gradelist(canvas, library, student_dict, is_prelim, auth1_pk, auth2_pk, printdate, request)
                    canvas.showPage()

                canvas.save()
                pdf = buffer.getvalue()
                # pdf_file = File(temp_file)

                # was: buffer.close()

                """
                # TODO as test try to save file in
                studsubjnote = stud_mod.Studentsubjectnote.objects.get_or_none(pk=47)
                content_type='application/pdf'
                file_name = 'test_try.pdf'
                if studsubjnote and pdf_file:
                    instance = stud_mod.Noteattachment(
                        studentsubjectnote=studsubjnote,
                        contenttype=content_type,
                        filename=file_name,
                        file=pdf_file)
                    instance.save()
                    logger.debug('instance.saved: ' + str(instance))
                # gives error: 'bytes' object has no attribute '_committed'
                """

                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="testpdf.pdf"'
                # response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

                response.write(pdf)

        # except Exception as e:
        #     logger.error(getattr(e, 'message', str(e)))
        #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    # - end of DownloadEx3View


def get_grade_dictlist(examyear, school, department, sel_lvlbase_pk, sel_sctbase_pk, student_pk_list):  # PR2021-11-19

    # NOTE: don't forget to filter deleted = false!! PR2021-03-15
    # grades that are not published are only visible when 'same_school'

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_grade_dictlist -----')
        logger.debug('student_pk_list: ' + str(student_pk_list))

    # upload_dict: {'subject_list': [2206, 2165, 2166], 'sel_layout': 'level', 'level_list': [86, 85]}

    # values of sel_layout are:"none", "level", "class", "cluster"
    # "none" or None: all students of subject on one form
    # "level:" seperate form for each leeerweg
    #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
    #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk,
                'student_pk_arr': student_pk_list}
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    grade_dictlist_sorted = []
    grade_dict = {}

    sql_list = ["SELECT studsubj.id AS studsubj_id, stud.id AS stud_id,",
                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, stud.gender, stud.idnumber,",
                "stud.birthdate, stud.birthcountry, stud.birthcity,"
                "stud.grade_ce_avg, stud.grade_combi_avg, stud.grade_final_avg, stud.result_status,",

                "school.name AS school_name, school.article AS school_article, school.islexschool,",
                "sb.code AS school_code, depbase.code AS depbase_code, lvlbase.code AS lvlbase_code,"
                "ey.code::TEXT AS examyear_txt, c.name AS country,"
                "dep.name AS dep_name, dep.abbrev AS dep_abbrev, dep.level_req, dep.has_profiel,"
                "lvl.name AS lvl_name, sct.name AS sct_name,"
                "cl.name AS cluster_name, stud.classname,",
                "studsubj.gradelist_sesrgrade, studsubj.gradelist_pecegrade, studsubj.gradelist_finalgrade,",
                "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.gradelist_use_exem,",

                "studsubj.pws_title, studsubj.pws_subjects,",

                "si.is_combi, (sjtpbase.code = 'stg')::BOOLEAN AS is_stg, (sjtpbase.code = 'wst')::BOOLEAN AS is_wst,",
                "subj.id AS subj_id, subj.name AS subj_name,",
                "sjtp.name AS sjtp_name, ",
                "sjtpbase.sequence AS sjtpbase_sequence, sjtpbase.code AS sjtpbase_code",

                "FROM students_studentsubject AS studsubj",
                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "INNER JOIN schools_country AS c ON (c.id = ey.country_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                #"INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "INNER JOIN subjects_subjecttype AS sjtp ON (sjtp.id = si.subjecttype_id)",
                "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = sjtp.base_id)",

                "LEFT JOIN subjects_cluster AS cl ON (cl.id = studsubj.cluster_id)",

                "WHERE ey.id = %(ey_id)s::INT AND school.id = %(sch_id)s::INT AND dep.id = %(dep_id)s::INT",
                "AND NOT studsubj.tobedeleted"
                ]

    if student_pk_list:
        sql_keys['student_pk_arr'] = student_pk_list
        sql_list.append("AND stud.id IN ( SELECT UNNEST( %(student_pk_arr)s::INT[]))")
    else:
        if sel_lvlbase_pk:
            sql_keys['lvlbase_pk'] = sel_lvlbase_pk
            sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")
        if sel_sctbase_pk:
            sql_keys['sctbase_pk'] = sel_sctbase_pk
            sql_list.append("AND sct.base_id = %(sctbase_pk)s::INT")

    sql_list.append("ORDER BY subj.sequence")

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        grade_rows = af.dictfetchall(cursor)

    # - add full name to rows, and array of id's of auth
    if grade_rows:
        for row in grade_rows:
            stud_id = row.get('stud_id')

            logger.debug('row: ' + str(row))

            if stud_id not in grade_dict:
                full_name = stud_fnc.get_full_name(row.get('lastname'), row.get('firstname'), row.get('prefix'))

                birth_date = row.get('birthdate', '')
                birth_date_formatted = af.format_DMY_from_dte(birth_date, 'nl', False)  # month_abbrev = False

                birth_country = row.get('birthcountry', '') or ''
                birth_city = row.get('birthcity') or ''
                birth_place = ', '.join((birth_city, birth_country))

                grade_dict[stud_id] = {
                    'country': row.get('country'),
                    'examyear_txt': row.get('examyear_txt'),

                    'school_name': row.get('school_name'),
                    'school_article':  row.get('school_article'),
                    'school_code':  row.get('school_code'),
                    'islexschool':  row.get('islexschool', False),

                    'dep_name':  row.get('dep_name'),
                    'depbase_code':  row.get('depbase_code'),
                    'dep_abbrev':  row.get('dep_abbrev'),

                    'lvl_name':  row.get('lvl_name'),
                    'lvlbase_code':  row.get('lvlbase_code'),
                    'level_req':  row.get('level_req', False),

                    'sct_name':  row.get('sct_name'),
                    'has_profiel':  row.get('has_profiel', False),

                    'fullname': full_name,
                    'idnumber': row.get('idnumber'),
                    'gender': row.get('gender'),
                    'birthdate': birth_date_formatted,
                    'birthplace': birth_place,
                    'regnumber':  row.get('regnumber'),
                    'examnumber':  row.get('examnumber'),
                    'classname':  row.get('classname'),
                    'cluster_name':  row.get('cluster_name'),

                    'ce_avg': row.get('grade_ce_avg_text'),
                    'combi_avg':  row.get('grade_combi_avg'),
                    'finalgrade_avg':  row.get('grade_final_avg'),
                    'result_status':  row.get('result_status'),
                }

# - add subjecttype dict
            student_dict = grade_dict.get(stud_id)
            if student_dict:
                # put combi subjects in dict with key: 'combi', others in dict with key: subjecttype_id
                # werkstuk Havo/Vwo is combi subject, is added to list of combi subjects
                # werkstuk Vsbo TKL is not a combi subject, it is added with key 'wst', grade is shown in draw_wst
                # stage it is added with key 'stg', grade is shown in draw_stg
                is_combi = row.get('is_combi', False)
                if is_combi:
                    sjtp_sequence = 'combi'
                elif row.get('is_wst', False):
                    sjtp_sequence = 'wst'
                elif row.get('is_stg', False):
                    sjtp_sequence = 'stg'
                else:
                    sjtp_sequence = row.get('sjtpbase_sequence', 9999)

                if sjtp_sequence not in student_dict:
                    student_dict[sjtp_sequence] = {
                        'sjtp_name':  row.get('sjtp_name', '') if not is_combi else ''
                    }

                sjtp_dict = student_dict.get(sjtp_sequence)
                subj_id = row.get('subj_id')
                if subj_id not in sjtp_dict:
                    sjtp_dict[subj_id] = {
                        'sjtp_code':  row.get('sjtpbase_code'),
                        'subj_name':  row.get('subj_name'),
                        'segrade':  row.get('gradelist_sesrgrade'),
                        'pecegrade':  row.get('gradelist_pecegrade'),
                        'finalgrade':  row.get('gradelist_finalgrade'),
                    }
                subj_dict = sjtp_dict[subj_id]
                logger.debug('?############ row: ' + str(row))
                logger.debug('?????????? sjtp_dict[' + str(subj_id) + ']: ' + str(sjtp_dict[subj_id]))
# - add  pws_title and pws_subjects to subj_dict
                pws_title = row.get('pws_title')
                if pws_title:
                    subj_dict['pws_title'] = pws_title
                pws_subjects = row.get('pws_subjects')
                if pws_subjects:
                    subj_dict['pws_subjects'] = pws_subjects

# - check if studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.gradelist_use_exem is True
                # if so: add 'has_extra_nocount' = True to student-dict
                # used to add foornote in gradelist
                if row.get('is_extra_nocount', False):
                    subj_dict['is_extra_nocount'] = True
                    student_dict['has_extra_nocount'] = True
                if row.get('is_extra_counts', False):
                    subj_dict['is_extra_counts'] = True
                    student_dict['has_extra_counts'] = True
                if row.get('gradelist_use_exem', False):
                    subj_dict['grlst_use_exem'] = True
                    student_dict['has_use_exem'] = True

# convert dict to sorted dictlist
        grade_list = list(grade_dict.values())

# sort list to sorted dictlist
        # PR2021-11-15 from https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
        grade_dictlist_sorted = sorted(grade_list, key=lambda d: d['fullname'])

    #if logging_on:
        #for row in grade_dictlist_sorted:
            #logger.debug('row: ' + str(row))

    return grade_dictlist_sorted
# - end of get_grade_dictlist


def draw_gradelist(canvas, library, student_dict, is_prelim, auth1_pk, auth2_pk, printdate, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_gradelist -----')
        logger.debug('auth1_pk: ' + str(auth1_pk) + '' + str(type(auth1_pk)))
        logger.debug('student_dict: ' + str(student_dict))
        """
        student_dict: {
            'examyear_txt': '2021', 'school_name': 'Juan Pablo Duarte Vsbo', 'country': 'Curacao', 'school_article': 'de', 
            'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_abbrev': 'V.S.B.O.', 'level_req': True, 'has_profiel': False, 
            'lvl_name': 'Theoretisch Kadergerichte Leerweg', 'sct_name': 'Zorg & Welzijn', 'cluster_name': None, 'classname': 'T4A', 
            'fullname': 'ANTOINE, Stayci', 'idnumber': None, 'birthdate': '23 juni 2005', 'birthplace': 'Willemstad, Curaçao', 
            'regnumber': None, 'islexschool': False, 'ce_avg': None, 'combi_avg': None, 'endgrade_avg': '7,1', 
            'result_info': 'Geslaagd', 
            'has_extra_nocount': True, 
            'combi': {'sjtp_name': '', 
                2116: {'sjtp_code': 'gmd', 'subj_name': 'Mens en Maatschappij 1', 'segrade': '5,8', 'pecegrade': '---', 'finalgrade': '6'}, 
                2117: {'sjtp_code': 'gmd', 'subj_name': 'Lichamelijke Opvoeding', 'segrade': '6,9', 'pecegrade': '---', 'finalgrade': '7'}, 
                2118: {'sjtp_code': 'gmd', 'subj_name': 'Culturele en Artistieke Vorming', 'segrade': '7,9', 'pecegrade': '---', 'finalgrade': '8'}}, 
            'wst': {'sjtp_name': 'Sectorwerkstuk', 
                2136: {'sjtp_code': 'wst', 'subj_name': 'Sectorwerkstuk', 'segrade': 'G', 'pecegrade': '---', 'finalgrade': 'G', 'pws_title': 'Heterokromia'}}}
            1: {'sjtp_name': 'Gemeenschappelijk deel', 
                2114: {'sjtp_code': 'gmd', 'subj_name': 'Nederlandse taal', 'segrade': '6,6', 'pecegrade': '7,6', 'finalgrade': '7'}, 
                2115: {'sjtp_code': 'gmd', 'subj_name': 'Engelse taal', 'segrade': '8,7', 'pecegrade': '6,8', 'finalgrade': '8'}, 
                2119: {'sjtp_code': 'gmd', 'subj_name': 'Papiamentu', 'segrade': '8,4', 'pecegrade': '---', 'finalgrade': '8'}}, 
            3: {'sjtp_name': 'Overig vak', 
                2121: {'sjtp_code': 'vrd', 'subj_name': 'Spaanse taal', 'segrade': '7,1', 'pecegrade': '8,2', 'finalgrade': '8', 'is_extra_nocount': True}}, 
            2: {'sjtp_name': 'Sectordeel', 
                2124: {'sjtp_code': 'spd', 'subj_name': 'Biologie', 'segrade': '6,3', 'pecegrade': '5,5', 'finalgrade': '6'}, 
                2125: {'sjtp_code': 'spd', 'subj_name': 'Mens en Maatschappij 1, 2', 'segrade': '6,8', 'pecegrade': '---', 'finalgrade': '7'}}, 
            4: {'sjtp_name': 'Sectorprogramma', 
                2132: {'sjtp_code': 'spr', 'subj_name': 'Zorg en Welzijn Intrasectoraal', 'segrade': '7,1', 'pecegrade': '6,7', 'finalgrade': '7'}}, 
        """
    auth1_name = '---'
    if auth1_pk:
        auth1 = acc_mod.User.objects.get_or_none(
            pk=auth1_pk,
            schoolbase=request.user.schoolbase,
            activated=True,
            is_active=True,
            usergroups__contains='auth1'
        )
        if logging_on:
            logger.debug('auth1: ' + str(auth1))
        if auth1:
            auth1_name = auth1.last_name

            if logging_on:
                logger.debug('auth1: ' + str(auth1))
                logger.debug('auth1_name: ' + str(auth1_name))
                logger.debug('auth1.usergroups: ' + str(auth1.usergroups))

    auth2_name = '---'
    if auth2_pk:
        auth2 = acc_mod.User.objects.get_or_none(
            pk=auth2_pk,
            schoolbase=request.user.schoolbase,
            activated=True,
            is_active=True,
            usergroups__contains='auth2'
        )
        if auth2:
            auth2_name = auth2.last_name

    is_lexschool = student_dict.get('islexschool', False)
    has_profiel = student_dict.get('has_profiel', False)
    reg_number = student_dict.get('regnumber')

# - calc regnumber if it is None
    if reg_number is None:
        reg_number = stud_fnc.calc_regnumber(
            school_code=student_dict.get('school_code'),
            gender=student_dict.get('gender'),
            examyear_str=student_dict.get('examyear_txt'),
            examnumber_str=student_dict.get('examnumber'),
            depbase_code=student_dict.get('depbase_code'),
            levelbase_code=student_dict.get('lvlbase_code')
        )

# - set the corners of the rectangle
    # - 72 points = 1 inch   -  1 point = 20 pixels  - 1 mm = 2,8346 points
    # only when prelim gradelist. rectangle is 180 mm wide and 270 mm high, 12 mm from bottom, 15 mm from left
    top, right, bottom, left = 282 * mm, 195 * mm, 12 * mm, 15 * mm
    #width = right - left  # 190 mm
    #height = top - bottom  # 275 mm
    border = [top, right, bottom, left]
    coord = [left, top]
    if logging_on:
        logger.debug('bottom: ' + str(bottom))
        logger.debug('left: ' + str(left))
        logger.debug('coord: ' + str(coord))
        logger.debug('1 * mm: ' + str(1 * mm))
    canvas.setLineWidth(0)
    canvas.setStrokeColorRGB(0.5, 0.5, 0.5)

    col_tab_list = (10, 90, 110, 130, 150, 170, 180)

# - draw border around page
    if is_prelim:
        draw_page_border(canvas, border)

# - draw page header
    draw_gradelist_page_header(canvas, coord, col_tab_list, library, student_dict, is_prelim, is_lexschool)

# - draw column header
    draw_gradelist_colum_header(canvas, coord, col_tab_list, library, is_lexschool)

# - loop through subjecttypes

    # combi, stage and werkstuk have text keys, rest has integer key
    for sequence in range(0, 10):  # range(start_value, end_value, step), end_value is not included!
        # sjtp_dict = {'sjtp_code': 'combi', 'sjtp_name': '', 2168: {'subj_name': 'Culturele en Artistieke Vorming',
        sjtp_dict = student_dict.get(sequence)
        if sjtp_dict:
            draw_gradelist_sjtp_header(canvas, coord, col_tab_list, library, sjtp_dict, student_dict)
            logger.debug('@@@@@ sjtp_dict: ' + str(sjtp_dict))
            for key, subj_dict in sjtp_dict.items():
                logger.debug('@@@@@ subj_dict: ' + str(subj_dict))
                if isinstance(key, int):
                    draw_gradelist_subject_row(canvas, coord, col_tab_list, subj_dict)

# - get combi subjects
    # also check if combi contains werkstuk
    combi_dict = student_dict.get('combi')
    wst_subj_dict = {}

    if combi_dict:
        draw_gradelist_sjtp_header(canvas, coord, col_tab_list, library, combi_dict, student_dict, True)
        for key, subj_dict in combi_dict.items():
            if isinstance(key, int):
                sjtp_code = subj_dict.get('sjtp_code')
                if sjtp_code == 'wst':
                    wst_subj_dict = subj_dict
                    wst_subj_dict['is_combi'] = True

                draw_gradelist_subject_row(canvas, coord, col_tab_list, subj_dict, True)

# - get werkstuk rows
    # if wst not found in combi (in Havo Vwo), lookup with key 'wst' ( in Vsbo)
    if not wst_subj_dict:
        wst_dict = student_dict.get('wst')
        if wst_dict:
            # there can only be one werkstuk
            for key, subj_dict in wst_dict.items():
                if isinstance(key, int):
                    wst_subj_dict = subj_dict
                    wst_subj_dict['is_combi'] = False
                    break
    if wst_subj_dict:
        draw_gradelist_werkstuk_row(canvas, coord, col_tab_list, library, wst_subj_dict, has_profiel)

# - get stage rows
    stg_dict = student_dict.get('stg')
    if stg_dict:
        stg_subj_dict = {}
        # there can only be one stage
        for key, subj_dict in stg_dict.items():
            if isinstance(key, int):
                stg_subj_dict = subj_dict
                break
        if stg_subj_dict:
            draw_gradelist_stage_row(canvas, coord, col_tab_list, stg_subj_dict)

# - draw 'Gemiddelde der cijfers' row
    draw_gradelist_avg_final_row(canvas, coord, col_tab_list, library, student_dict)

# - draw 'Uitslag op grond van de resultaten:' row
    draw_gradelist_result_row(canvas, coord, col_tab_list, library, student_dict)

# - draw page footer
    draw_gradelist_footnote_row(canvas, coord, col_tab_list, library, student_dict, is_lexschool)

# - draw page signatures
    draw_gradelist_signature_row(canvas, border, coord, col_tab_list, library, student_dict, auth1_name, auth2_name, printdate, reg_number)

# - end of draw_gradelist


def draw_page_border(canvas, border):
    # - draw border around page

    #  border = [top, right, bottom, left]
    top, right, bottom, left = border[0], border[1], border[2], border[3]
    width = right - left  # 190 mm
    height = top - bottom  # 275 mm

    canvas.rect(left, bottom, width, height)


    #draw_red_cross(canvas, left, bottom)
# - end of draw_page_border


def draw_gradelist_page_header(canvas, coord, col_tab_list, library, student_dict, is_prelim, is_lexschool):
    # loop through rows of page_header

    examyear_code = student_dict.get('examyear_txt', '---')
    school_name = student_dict.get('school_name', '---')
    school_article = student_dict.get('school_article', '---')
    country = student_dict.get('country', '---')
    dep_abbrev = student_dict.get('dep_abbrev', '---')
    dep_name = student_dict.get('dep_name', '---')

    full_name = student_dict.get('fullname', '---')
    birth_date = student_dict.get('birthdate') or '---'
    birth_place = student_dict.get('birthplace') or '---'
    in_the_examyear_txt = ' '.join((
        library.get('in_the_examyear', '-'),
        examyear_code,
        library.get('attended_the_exam', '-'),
        library.get('het_landsexamen', '-') if is_lexschool else library.get('het_eindexamen', '-'),
        dep_abbrev,
        library.get('conform', '-'),
    ))
    level_req = student_dict.get('level_req', False)
    key_str = 'de_sector' if level_req else 'het_profiel'
    sector_profiel_label = library.get(key_str) or '-'
    leerweg_label = library.get('leerweg') or '-'

    sector_profiel_txt = student_dict.get('sct_name') or '---'
    leerweg_txt = student_dict.get('lvl_name') or '---'

    aan_article_txt = ' '.join((library.get('at_school', '-'), school_article))

    eex_article01 = library.get('eex_article01')
    eex_article02 = library.get('eex_article02')
    eex_article03 = library.get('eex_article03')

    is_prelim = True
    txt_list = [{'txt': library.get('preliminary', '---'), 'font': 'Times-Roman', 'size': 16, 'align': 'c',
         'x': coord[0] + (col_tab_list[0] + col_tab_list[5]) / 2 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, 10, 0, False, None, txt_list, not is_prelim)

    txt_list = [{'txt': dep_name, 'font': 'Times-Bold', 'size': 16, 'align': 'c',
         'x': coord[0] + (col_tab_list[0] + col_tab_list[5]) / 2 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, 10, 0, False, None, txt_list, not is_prelim)

    dont_print_leerweg = not level_req or not is_prelim
    txt_list = [{'txt': leerweg_txt, 'font': 'Times-Bold', 'size': 14, 'align': 'c',
         'x': coord[0] + (col_tab_list[0] + col_tab_list[5]) / 2 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, 10, 0, False, None, txt_list, dont_print_leerweg)

    txt_list = [{'txt': library.get('undersigned', '---'), 'size': 11, 'x': 25 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, 10, 0, False, None, txt_list, not is_prelim)

    txt_list = [{'txt': full_name, 'font': 'Times-Bold', 'size': 14, 'x': 25 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, 10, 0, False, None, txt_list, not is_prelim)

    txt_list = [
        {'txt': library.get('born_on', '---'), 'size': 11, 'x': 25 * mm},
        {'txt': birth_date, 'font': 'Times-Bold', 'size': 11, 'x': 45 * mm},
        {'txt': library.get('born_at', '---'), 'size': 11, 'x': 80 * mm},
        {'txt': birth_place, 'font': 'Times-Bold', 'size': 11, 'x': 87 * mm} ]
    draw_text_one_line(canvas, coord, col_tab_list, 10, 0, False, None, txt_list, not is_prelim)

    txt_list = [{'txt': in_the_examyear_txt, 'size': 11, 'x': 25 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, 6, 0, False, None, txt_list, not is_prelim)

    txt_list = [
        {'txt': sector_profiel_label, 'size': 11, 'x': 25 * mm},
        {'txt': sector_profiel_txt, 'font': 'Times-Bold', 'size': 11, 'x': 45 * mm} ]
    if level_req:
        txt_list.extend([
            {'txt': leerweg_label, 'size': 11, 'x': 95 * mm},
            {'txt': leerweg_txt, 'font': 'Times-Bold', 'size': 11, 'padding': 0, 'x': 115 * mm} ])
    draw_text_one_line(canvas, coord, col_tab_list, 6, 0, False, None, txt_list, not is_prelim)

    txt_list = [
        {'txt': aan_article_txt,'size': 11, 'x': 25 * mm},
        {'txt': school_name, 'font': 'Times-Bold', 'size': 11, 'x': 45 * mm},
        {'txt': library.get('at_country', '-'), 'size': 11, 'x': 135 * mm},
        {'txt': country, 'font': 'Times-Bold', 'size': 11, 'x': 145 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, 6, 0, False, None, txt_list, not is_prelim)

    txt_list = [{'txt': eex_article01, 'x': 25 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, 6, 0, False, None, txt_list, not is_prelim)

    txt_list = [{'txt': eex_article02, 'x': 25 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, 5, 0, False, None, txt_list, not is_prelim)

    if eex_article03:
        txt_list = [{'txt': eex_article03, 'x': 25 * mm}]
        draw_text_one_line(canvas, coord, col_tab_list, 5, 0, False, None, txt_list, not is_prelim)
# - end of draw_gradelist_page_header


def draw_gradelist_colum_header(canvas, coord, col_tab_list, library, is_lexschool):
    #     col_tab_list = (10, 90, 110, 130, 150, 170, 180)

    header_height = 13 * mm

    x = coord[0]
    y = coord[1] - 5 * mm
    coord[1] = y

# - draw horizontal lines above and below column header
    left = coord[0] + col_tab_list[0] * mm
    right = coord[0] + col_tab_list[5] * mm
    canvas.line(left, y, right, y)

    y1 = y - header_height
    canvas.line(left, y1, right, y1)


# - draw vertical lines of columns
    y_top = coord[1]
    y_top_minus = y_top - 5 * mm  # line height - 1 mm
    y_bottom = y_top - header_height

    for index in range(0, len(col_tab_list) - 1):  # range(start_value, end_value, step), end_value is not included!
        line_x = coord[0] + col_tab_list[index] * mm
        y1_mod = y_top_minus if index in (2, 4) else y_top
        canvas.line(line_x, y1_mod, line_x, y_bottom)

# - draw horizontal line  below 'CIjfers voor' and 'Eindcijfers'
    left = coord[0] + col_tab_list[1] * mm
    canvas.line(left, y_top_minus, right, y_top_minus)
    #canvas.setFont('Arial', 8, leading=None)
    #canvas.setFillColor(colors.HexColor("#000000"))

   # line_height = 4 * mm
    #y_txt1 = y - line_height - 1 * mm

    # - draw page header
    col_01_01_key = 'col_01_01_lex' if is_lexschool else 'col_01_01_eex'
    col_01_01_txt = library.get(col_01_01_key, '-')
    txt_list = [
        {'txt': library.get('col_00_00', '-'), 'padding': 4, 'x': x + col_tab_list[0] * mm, 'offset_bottom': 1.25, 'line_height': 5},
        {'txt': library.get('col_01_00', '-'), 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[3]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
        {'txt': library.get('col_03_00', '-'), 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[5]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
        ]
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, False, None, txt_list)
    txt_list = [
        {'txt': col_01_01_txt, 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[2]) / 2 * mm, 'offset_bottom': 1, 'line_height': 5},
        {'txt': library.get('col_02_01', '-'), 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
        {'txt': library.get('col_03_01', '-'), 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
        {'txt': library.get('col_04_01', '-'), 'align': 'c', 'x': x + (col_tab_list[4] + col_tab_list[5]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0}]

    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, False, None, txt_list)
    txt_list = [
        {'txt': library.get('col_01_02', '-'), 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[2]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 3},
        {'txt': library.get('col_02_02', '-'), 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
    ]
    draw_text_one_line(canvas, coord, col_tab_list, 3, 1.25, False, None, txt_list)
# - end of draw_gradelist_colum_header


def draw_gradelist_sjtp_header(canvas, coord, col_tab_list, library, sjtp_dict, student_dict, is_combi=False):
    #     col_tab_list = (10, 90, 110, 130, 150, 170, 180)

    header_height = 5 * mm

    x = coord[0]
    y = coord[1]

# - draw recangle and fill background
    left = x + col_tab_list[0] * mm
    right = coord[0] + col_tab_list[5] * mm
    width = (col_tab_list[5] - col_tab_list[0]) * mm

    y1 = y - header_height

    canvas.setFillColor(colors.HexColor("#f0f0f0"))
    canvas.rect(left, y1, width, header_height, stroke=0, fill=1) # canvas.rect(left, bottom, page_width, height)
    canvas.setFillColor(colors.HexColor("#000000"))

# also draw upper line - otherwise it will be covered by fill rectangle
    canvas.setStrokeColorRGB(.5, .5, .5)
    canvas.line(left, y, right, y)

# - draw sjtp text
    if is_combi:
        sjtp_name = library.get('combi_grade', '---')
    else:
        sjtp_name = sjtp_dict.get('sjtp_name', '---')

    combi_grade, combi_grade_in_letters = get_final_grade(student_dict, 'combi_avg')

    font_str = 'Times-Roman' if is_combi else 'Times-Bold'
    txt_list = [ {'txt': sjtp_name, 'font': font_str, 'padding': 4, 'x': x + col_tab_list[0] * mm}]

    vertical_lines = (0, 3, 4, 5) if is_combi else (0, 5)
    if is_combi:
        txt_list.extend([
            {'txt': combi_grade, 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm},
            {'txt': combi_grade_in_letters, 'align': 'c', 'x': x + (col_tab_list[4] + col_tab_list[5]) / 2 * mm}
        ])

    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_sjtp_header


def draw_gradelist_subject_row(canvas, coord, col_tab_list, subj_dict, is_combi=False):
    #     col_tab_list = (10, 90, 110, 130, 150, 170, 180)

    x = coord[0]
    """
    'PR2020-05-18 Corona:
    ' functie wordt nu ook gebruikt om vrst weer te geven achter vak als Vrijstelling wordt gebruikt in eindcijfer
    ' - bij vrijstelling "(vrst)" achter vak plaatsen, Hier geplaatst, zodat het ook op de cijferlijst terecht komt
    ' - suffix (h) en (h3) niet weergeven op Cijferlijst, wordt bereikt door IsHerTv02 en IsHerTv03 weg te laten uit parameters
    
    'PR2020-05-08 Corona bij vrijstelling "(vrst)" achter vak plaatsen, Hier geplaatst, zodat het ook op de cijferlijst terecht komt
    
    'PR2020-07-10 verzoek Esther: geen Vrst weergeven op LEX cijferlijst als het officieel geen vrst is.
        ' deze berekening wordt te ingewikkeld, dan maar gewoon uischakelen.
        'BewijsVanKennisOK = CalcBewijsVanKennis(strVakText, strSEcijfer, strCEcijfer, strEINDcijfer, _
        '                             lngCijferTypeID, crcSEweging, crcCEweging, _
        '                             booIsCombiOfKeuzeCombi, kv_IsHerVak(), kv_MaxTv())
    If Not pblAfd.IsLandsexamen Then
        strVakText = strVakText & " (Vr)"
    End If
    
    """

    subj_name = subj_dict.get('subj_name', '---')
    if is_combi:
        subj_name += " *"
    if subj_dict.get('is_extra_nocount', False):
        subj_name += " +"
    if subj_dict.get('is_extra_counts', False):
        subj_name += " ++"
    if subj_dict.get('grlst_use_exem', False):
        subj_name += " (vr)"

    finalgrade, finalgrade_in_letters = get_final_grade(subj_dict, 'finalgrade')

# - draw subject_row
    txt_list = [
        {'txt': subj_name, 'font': 'Times-Roman', 'padding': 4, 'x': x + col_tab_list[0] * mm},
        {'txt': subj_dict.get('segrade', '---'), 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[2]) / 2 * mm},
        {'txt': subj_dict.get('pecegrade', '---'), 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm},
        {'txt': finalgrade, 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm},
        {'txt': finalgrade_in_letters, 'align': 'c', 'x': x + (col_tab_list[4] + col_tab_list[5]) / 2 * mm}
    ]

    logger.debug('@@@@@ txt_list: ' + str(txt_list))

    vertical_lines = (0, 1, 2, 3, 4,  5)
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_subject_row


def draw_gradelist_werkstuk_row(canvas, coord, col_tab_list, library, subj_dict, has_profiel):

    x = coord[0]

# - draw subject_row
    # draw grade of werkstuk, only if it is not part of the combi grade
    is_combi = subj_dict.get('is_combi', False)
    if not is_combi:
        label_key = 'pws' if has_profiel else 'sws'
        label_txt = library.get(label_key, '---')
        finalgrade, finalgrade_in_letters = get_final_grade(subj_dict, 'finalgrade')

        txt_list = (
            {'txt': label_txt, 'font': 'Times-Roman', 'padding': 4, 'x': x + col_tab_list[0] * mm},
            {'txt': finalgrade_in_letters, 'align': 'c', 'x': x + (col_tab_list[4] + col_tab_list[5]) / 2 * mm}
        )
        vertical_lines = (0, 3, 4, 5)
        draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)

# - draw subject_row
    # when title has more than 44 char, shift title 22 mm to left
    title_key = 'lbl_title_pws' if has_profiel else 'lbl_title_sws'
    title = library.get(title_key, '---')
    if len(title) > 44:
        pos_x_title = x + (col_tab_list[1] - 20) * mm
    else:
        pos_x_title = x + col_tab_list[1] * mm
    txt_list = (
        {'txt': library.get(title_key, '---'), 'font': 'Times-Roman', 'padding': 4, 'x': x + col_tab_list[0] * mm},
        {'txt': subj_dict.get('pws_title', '---'), 'font': 'Times-Italic', 'padding': 4, 'x': pos_x_title}
    )
    vertical_lines = (0, 5)
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)

    subjects_key = 'lbl_subjects_pws' if has_profiel else 'lbl_subjects_sws'
    txt_list = (
        {'txt': library.get(subjects_key, '---'), 'font': 'Times-Roman', 'padding': 4, 'x': x + col_tab_list[0] * mm},
        {'txt': subj_dict.get('pws_subjects', '---'), 'font': 'Times-Italic', 'padding': 4, 'x': x + col_tab_list[1] * mm}
    )
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_werkstuk_row


def draw_gradelist_stage_row(canvas, coord, col_tab_list, subj_dict):
    finalgrade, finalgrade_in_letters = get_final_grade(subj_dict, 'finalgrade')

    txt_list = [
        {'txt': subj_dict.get('subj_name', '---'), 'font': 'Times-Roman', 'padding': 4, 'x': coord[0] + col_tab_list[0] * mm},
        {'txt': finalgrade_in_letters, 'align': 'c', 'x': coord[0] + (col_tab_list[4] + col_tab_list[5]) / 2 * mm}
    ]
    vertical_lines = (0, 3, 4, 5)
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_stage_row


def draw_gradelist_avg_final_row(canvas, coord, col_tab_list, library, student_dict):
    # draw row 'Gemiddelde der cijfers', only when ce_avg or endgrade_avg have value PR2021-11-16
    # values are stored in student_dict, not in subj_dict
    ce_avg = student_dict.get('ce_avg')
    endgrade_avg = student_dict.get('endgrade_avg')

    if ce_avg or endgrade_avg:
        txt_list = [ {'txt': library.get('avg_grade', '---'), 'font': 'Times-Roman', 'padding': 4, 'x': coord[0] + col_tab_list[0] * mm}]
        if ce_avg:
            txt_list.append({'txt': ce_avg, 'align': 'c', 'x': coord[0] + (col_tab_list[2] + col_tab_list[3]) / 2 * mm})
        if endgrade_avg:
            txt_list.append({'txt': endgrade_avg, 'align': 'c', 'x': coord[0] + (col_tab_list[3] + col_tab_list[4]) / 2 * mm})
        vertical_lines = [0, 3, 5]
        if ce_avg:
            vertical_lines.append(2)
        if endgrade_avg:
            vertical_lines.append(4)

        draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_avg_final_row


def draw_gradelist_result_row(canvas, coord, col_tab_list, library, student_dict):
    label = library.get('result', '---')
    result = student_dict.get('result_status', '---')

    txt_list = [
        {'txt':label, 'font': 'Times-Bold', 'padding': 4, 'x': coord[0] + col_tab_list[0] * mm},
        {'txt': result, 'font': 'Times-Bold', 'padding': 3, 'align': 'r', 'x': coord[0] + col_tab_list[5] * mm}
    ]
    vertical_lines = (0, 5)
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_stage_row


def draw_gradelist_footnote_row(canvas, coord, col_tab_list, library, student_dict, is_lexschool):
    """
    'PR2020-05-08 Corona: voetnoot toegevoegd, overleg Esther, Rubya Nancy 2020-005-08
    'PR2020-07-10 verzoek Esther: geen Vrst weergeven op LEX cijferlijst als het officieel geen vrst is.
    """
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug((' ----- draw_gradelist_footnote_row -----'))
        #logger.debug(('student_dict: ' + str(student_dict)))
        logger.debug('has_extra_nocount: ' + str(student_dict.get('has_extra_nocount', False)))
        logger.debug('has_extra_counts: ' + str(student_dict.get('has_extra_counts', False)))

    # check if student has subjects with is_extra_nocount or is_extra_counts or gradelist_use_exem
    footnote = ''
    if student_dict.get('has_extra_nocount', False):
        footnote += library.get('footnote_extra_nocount') or ''
    if student_dict.get('has_extra_counts', False):
        footnote += library.get('footnote_extra_counts') or ''
    if student_dict.get('has_use_exem', False) and not is_lexschool:
        footnote += library.get('footnote_exem') or ''

    if logging_on:
        logger.debug('footnote: ' + str(footnote))

    if footnote:
        txt_list = [
            {'txt':footnote, 'font': 'Times-Roman',  'size': 8, 'padding': 4, 'x': coord[0] + col_tab_list[0] * mm}
        ]
        if logging_on:
            logger.debug('txt_list: ' + str(txt_list))
        vertical_lines = ()
        draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, False, vertical_lines, txt_list)
# - end of draw_gradelist_footnote_row


def draw_gradelist_signature_row(canvas, border, coord, col_tab_list, library, student_dict, auth1_name, auth2_name, printdate, reg_number):
    """
    'PR2020-05-24 na email correspondentie Esther: 'De voorzitter / directeur' gewijzigd in 'De voorzitter'
    """
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug((' ----- draw_gradelist_signature_row -----'))
        #logger.debug(('student_dict: ' + str(student_dict)))
        logger.debug('auth1_name: ' + str(auth1_name))
        logger.debug('auth2_name: ' + str(auth2_name))
        logger.debug('printdate: ' + str(printdate))


    #border = [top, right, bottom, left]
    bottom = border[2]

# ---  set date today for now - TODO save date in school_settings
    printdate_formatted = None
    if printdate:
        printdate_dte = af.get_date_from_ISO(printdate)
        printdate_formatted = af.format_DMY_from_dte(printdate_dte, 'nl', False)  # False = not month_abbrev
    if not printdate_formatted:
        printdate_formatted = '---'

    x = coord[0]

    txt_list = [
        {'txt': library.get('place', '---'), 'font': 'Times-Roman', 'size': 10, 'padding': 4, 'x': x + col_tab_list[0] * mm},
        {'txt': student_dict.get('country', '---'), 'font': 'Times-Bold', 'size': 10, 'padding': 18, 'x': x + col_tab_list[0] * mm},
        {'txt': library.get('date', '---'), 'font': 'Times-Roman', 'size': 10, 'padding': 4, 'x': x + col_tab_list[1] * mm},
        {'txt': printdate_formatted, 'font': 'Times-Bold', 'size': 10, 'padding': 18, 'x': x + col_tab_list[1] * mm},
    ]
    line_height = 7
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 1.25, False, None, txt_list)

# - draw name of president and secretary
    # - place the text of the name of the president / secretary 40 mm under  the line president / secretary
    # but no lower than maximum

    txt_list = [
        {'txt': auth1_name, 'font': 'Times-Bold', 'size': 10, 'padding': 4,
         'x': x + col_tab_list[0] * mm},
        {'txt': auth2_name, 'font': 'Times-Bold', 'size': 10, 'padding': 4,
         'x': x + col_tab_list[1] * mm},
    ]
    line_height = 30
    pos_y_auth = coord[1] - line_height * mm
    if pos_y_auth < 23 * mm:
        pos_y_auth = 23 * mm
    coord_auth = [coord[0], pos_y_auth]
    draw_text_one_line(canvas, coord_auth, col_tab_list, 0, 1.25, False, None, txt_list)

# - draw label 'president' and 'secretary' under the name
    pos_y_auth_label  = pos_y_auth - 5 * mm
    coord_auth_label = [coord[0], pos_y_auth_label]
    txt_list = [
        {'txt': library.get('president', '---'), 'font': 'Times-Roman', 'size': 10, 'padding': 4,
         'x': x + col_tab_list[0] * mm},
        {'txt': library.get('secretary', '---'), 'font': 'Times-Roman', 'size': 10, 'padding': 4,
         'x': x + col_tab_list[1] * mm},
    ]
    draw_text_one_line(canvas, coord_auth_label, col_tab_list, 0, 1.25, False, None, txt_list)

    if logging_on:
        logger.debug('coord: ' + str(coord))
        logger.debug('coord_auth: ' + str(coord_auth))
        logger.debug('bottom: ' + str(bottom))

# - regnumber and idnumber are just above lower line of rectangle
    id_number = student_dict.get('idnumber') or '---'
    txt_list = [
        {'txt': reg_number, 'font': 'Times-Roman', 'size': 8, 'padding': 4,
         'x': x + col_tab_list[0] * mm},
        {'txt': id_number, 'font': 'Times-Roman', 'size': 8, 'padding': 4,
         'x': x + col_tab_list[1] * mm},
    ]
    coord_regnr = [coord[0], bottom]
    draw_text_one_line(canvas, coord_regnr, col_tab_list, 0, 1.25, False, None, txt_list)
# - end of draw_gradelist_signature_row


def draw_text_one_line(canvas, coord, col_tab_list, line_height, offset_bottom,
                       draw_line_below, vertical_lines, text_list, dont_print=False):
    # function creates one line with text for each item in list PR2021-11-16
    # x-coord[0] is not in use
    # coord[1] decreses with line_height

    # still call this function when dont_print, to keep track of y_pos

    y_pos_line = coord[1] - line_height * mm
    y_pos_txt = y_pos_line + offset_bottom * mm

    if not dont_print:
        for text_dict in text_list:
    # - get info from text_dict
            text = text_dict.get('txt')
            if text:
                font_type = text_dict.get('font', 'Times-Roman')
                font_size = text_dict.get('size', 10)
                font_hexcolor = text_dict.get('color', '#000000')
                text_align = text_dict.get('align', 'l')

                x_pos = text_dict.get('x', 0)

                # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
                canvas.setFont(font_type, font_size, leading=None)
                canvas.setFillColor(colors.HexColor(font_hexcolor))
                if text_align == 'c':
                    x_pos_txt = x_pos
                    canvas.drawCentredString(x_pos_txt, y_pos_txt, text)
                elif text_align == 'r':
                    x_pos_txt = x_pos - text_dict.get('padding', 0) * mm
                    canvas.drawRightString(x_pos_txt, y_pos_txt, text)
                else:
                    x_pos_txt = x_pos + text_dict.get('padding', 0) * mm
                    canvas.drawString(x_pos_txt, y_pos_txt, text)

                #draw_red_cross(canvas, x_pos_txt, y_pos_txt)

        # - draw line at bottom of row
        if draw_line_below:
            canvas.setStrokeColorRGB(.5, .5, .5)
            left = coord[0] + col_tab_list[0] * mm
            right = coord[0] + col_tab_list[5] * mm
            canvas.line(left, y_pos_line, right, y_pos_line)


    # - draw vertical lines of columns
        if vertical_lines:
            canvas.setStrokeColorRGB(.5, .5, .5)
            for index in vertical_lines:
                y_top = coord[1]
                y_bottom = y_pos_line

                line_x = coord[0] + col_tab_list[index] * mm
                canvas.line(line_x, y_top, line_x, y_bottom)

    coord[1] = y_pos_line
# - end of draw_text_one_line


def draw_red_cross(canvas, x, y):
    # draw red cross, for outlining while designing
    canvas.setStrokeColorRGB(1, 0, 0)
    canvas.line(x, y + 5 * mm, x, y - 5 * mm)
    canvas.line(x - 5 * mm, y , x + 5 * mm, y )


def get_final_grade(subj_dict, key_str):
    # PR2021-11-19
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  key_str  -----')
        logger.debug('subj_dict: ' + str(subj_dict))
        logger.debug('key_str: ' + str(key_str))

    finalgrade, finalgrade_in_letters = None, None
    final_grade = subj_dict.get(key_str)

    if logging_on:
        logger.debug('final_grade: ' + str(final_grade))

    if final_grade:
        finalgrade = final_grade.lower()
        finalgrade_in_letters = c.GRADE_IN_LETTERS.get(final_grade)

    if not finalgrade:
        finalgrade = '---'
    if not finalgrade_in_letters:
        finalgrade_in_letters = '---'

    if logging_on:
        logger.debug('finalgrade: ' + str(finalgrade))
        logger.debug('finalgrade_in_letters: ' + str(finalgrade_in_letters))
    return finalgrade, finalgrade_in_letters
# - end of get_final_grade


