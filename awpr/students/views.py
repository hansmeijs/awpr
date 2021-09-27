# PR2018-09-02
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
from django.utils.translation import activate, pgettext_lazy, ugettext_lazy as _
from django.views.generic import View

from accounts import views as acc_view
from awpr import menus as awpr_menu, excel as grd_exc
from awpr import constants as c
from awpr import settings as s
from awpr import validators as av
from awpr import functions as af
from awpr import downloads as dl

from grades import views as grd_vw

from schools import models as sch_mod
from students import models as stud_mod
from students import functions as stud_fnc
from subjects import models as subj_mod
from students import validators as stud_val

import json

import logging
logger = logging.getLogger(__name__)

# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

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

def create_student_rows(setting_dict, append_dict, student_pk):
    # --- create rows of all students of this examyear / school PR2020-10-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_student_rows -----')

    student_rows = []
    try:
        sel_examyear_pk = setting_dict.get('sel_examyear_pk')
        sel_schoolbase_pk = setting_dict.get('sel_schoolbase_pk')
        sel_depbase_pk = setting_dict.get('sel_depbase_pk')

        sel_lvlbase_pk = None
        if c.KEY_SEL_LVLBASE_PK in setting_dict:
            sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)

        sel_sctbase_pk = None
        if c.KEY_SEL_SCTBASE_PK in setting_dict:
            sel_sctbase_pk = setting_dict.get(c.KEY_SEL_SCTBASE_PK)

        if logging_on:
            logger.debug(' ----- create_student_rows -----')
            logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk))
            logger.debug('sel_schoolbase_pk: ' + str(sel_schoolbase_pk))
            logger.debug('sel_depbase_pk: ' + str(sel_depbase_pk))
            logger.debug('sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
            logger.debug('sel_sctbase_pk: ' + str(sel_sctbase_pk))

        sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk, 'db_id': sel_depbase_pk}
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
            "st.bis_exam, st.partial_exam, st.additional_exam,",

            "st.linked, st.notlinked, st.has_reex, st.has_reex3, st.has_sere, st.withdrawn,",
            "st.grade_ce_avg_text, st.grade_combi_avg_text, st.endgrade_avg_text,",

            "st.result_info, st.result_status, st.tobedeleted,",

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
            "WHERE sch.base_id = %(sb_id)s::INT AND sch.examyear_id = %(ey_id)s::INT AND dep.base_id = %(db_id)s::INT"]

        if sel_lvlbase_pk:
            sql_list.append('AND lvl.base_id = %(lvlbase_id)s::INT')
            sql_keys['lvlbase_id'] = sel_lvlbase_pk
        if sel_sctbase_pk:
            sql_list.append('AND sct.base_id = %(sctbase_id)s::INT')
            sql_keys['sctbase_id'] = sel_sctbase_pk

        if student_pk:
            sql_list.append('AND st.id = %(st_id)s::INT')
            sql_keys['st_id'] = student_pk
        else:
            # PR2021-06-16
            # order by id necessary to make sure that lookup function on client gets the right row
            sql_list.append("ORDER BY st.id")
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            student_rows = af.dictfetchall(cursor)

        if logging_on:
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
        logger.error(getattr(e, 'message', str(e)))

    return student_rows
# --- end of create_student_rows


def get_permit_crud_of_this_page(page, request):
    # --- get crud permit for this page # PR2021-07-18 PR2021-09-05
    has_permit = False
    if page and request.user and request.user.country and request.user.schoolbase:
        permit_list = request.user.permit_list(page)
        if permit_list:
            has_permit = 'permit_crud' in permit_list

    return has_permit





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
        has_permit = get_permit_crud_of_this_page('page_student', request)
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

# +++  Create new student
                    if is_create:
                        student = create_student(sel_school, sel_department,
                            upload_dict, messages, error_list, request, False)  # skip_save = False
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
                            deleted_ok = delete_student(student, updated_rows, messages, error_list, request)

# +++ Update student, also when it is created, not when delete has failed (when deleted ok there is no student)
                        else:
                            idnumber_list, examnumber_list = [], []
                            update_student_instance(student, upload_dict, idnumber_list, examnumber_list, messages, error_list, request, False)  # skip_save = False

# - create student_row, also when deleting failed, not when deleted ok, in that case student_row is added in delete_student
                    if not deleted_ok:
                        setting_dict = {
                            'sel_examyear_pk': sel_school.examyear.pk,
                            'sel_schoolbase_pk': sel_school.base_id,
                            'sel_depbase_pk': sel_department.base_id}
                        student_pk = student.pk if student else None
                        updated_rows = create_student_rows(
                            setting_dict=setting_dict,
                            append_dict=append_dict,
                            student_pk=student_pk
                        )

                update_wrap['updated_student_rows'] = updated_rows
        if len(messages):
            update_wrap['messages'] = messages
            # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))


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
        has_permit = get_permit_crud_of_this_page('page_studsubj', request)
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
                            setting_dict = {
                                'sel_examyear_pk': sel_school.examyear.pk,
                                'sel_schoolbase_pk': sel_school.base_id,
                                'sel_depbase_pk': sel_department.base_id}
                            student_pk = cur_student.pk if cur_student else None
                            updated_rows = create_student_rows(
                                setting_dict=setting_dict,
                                append_dict=append_dict,
                                student_pk=student_pk
                            )

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
                        logger.debug('cur_student.level.base_id: ' + str(cur_student.level.base_id))
                        logger.debug('other_student.level.base_id: ' + str(other_student.level.base_id))

                    if cur_student.department.base_id == other_student.department.base_id:

        # - student can only be biscandidate when the lvlbases are the same (only when not level_req)
                        if cur_student.department.level_req:
                            if cur_student.level.base_id == other_student.level.base_id:
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
                                setattr(cur_exem_grade, 'sesrgrade', other_studsubj.gradelist_segrade)
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


#################################################################################
@method_decorator([login_required], name='dispatch')
class StudentsubjectValidateViewNIU(View):

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= StudentsubjectValidateView ============= ')

        # function validates studentsubject records of this student PR2021-07-10

        update_wrap = {}

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

            if logging_on:
                logger.debug('upload_dict' + str(upload_dict))
                logger.debug('sel_examyear: ' + str(sel_examyear))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))

# +++ validate subjects of one student, used in modal
            student_pk = upload_dict.get('student_pk')
            if student_pk:
                student = stud_mod.Student.objects.get_or_none(
                    id=student_pk,
                    school=sel_school,
                    department=sel_department
                )
                if student:
                    msg_html = stud_val.validate_studentsubjects(student)
                    if msg_html:
                        update_wrap['studsubj_validate_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

# - end of StudentsubjectValidateView



#################################################################################
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

            if logging_on:
                logger.debug('upload_dict' + str(upload_dict))
                logger.debug('sel_examyear: ' + str(sel_examyear))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))

# +++ validate subjects of one student, used in modal
            student_pk = upload_dict.get('student_pk')
            si_dictlist = upload_dict.get('si_dictlist')
            if logging_on:
                logger.debug('student_pk: ' + str(student_pk) + ' ' + str(type(student_pk)))
                logger.debug('si_dictlist: ' + str(si_dictlist))

            if student_pk:
                student = stud_mod.Student.objects.get_or_none(id=student_pk)
                if logging_on:
                    logger.debug('sel_school.pk: ' + str(sel_school.pk))
                    logger.debug('sel_department.pk: ' + str(sel_department.pk))
                    logger.debug('student: ' + str(student))

                if student:
                    msg_html = stud_val.validate_studentsubjects_TEST(student, si_dictlist)
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
        has_permit = get_permit_crud_of_this_page('page_studsubj', request)
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
class StudentsubjectSendEmailExformView(View):  # PR2021-07-26
    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectSendEmailExformView ============= ')

        update_wrap = {}
        msg_list = []
        class_str = 'border_bg_transparent'

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = req_usr.permit_list('page_studsubj')
            if permit_list and req_usr.usergroup_list:
                if 'auth1' in req_usr.usergroup_list or 'auth2' in req_usr.usergroup_list:
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
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if may_edit:
                    try:
            # create _verificationcode and key, store in usersetting, send key to client, set expiration to 30 minutes
                        # get random number between 1,000,000 en 1,999,999, convert to string and get last 6 characters
                        # this way you get string from '000000' thru '999999'
                        # key is sent to client, code must be entered by user
                        # key_code is stored in usersettings, with
                        _verificationcode = str(randint(1000000, 1999999))[-6:]
                        _verificationkey = str(randint(1000000, 1999999))[-6:]
                        update_wrap['verificationkey'] = _verificationkey

                        key_code = '_'.join((_verificationkey, _verificationcode))

                        now = datetime.now() # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
                        expirationtime = now + timedelta(seconds=1800)
                        expirationtime_iso = expirationtime.isoformat()

                        verification_dict = {'form': 'Ex1', 'key_code': key_code, 'expirationtime': expirationtime_iso}
                        acc_view.set_usersetting_dict(c.KEY_VERIFICATIONCODE, verification_dict, request)

                        subject = str(_('AWP-online verificationcode'))
                        from_email = 'AWP-online <noreply@awponline.net>'
                        message = render_to_string('send_verifcode__ex1_email.html', {
                            'user': request.user,
                            'examyear': sel_examyear,
                            'school': sel_school,
                            'department': sel_department,
                            'verificationcode': _verificationcode
                        })

                        # PR2018-04-25 arguments: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
                        mail_count = send_mail(subject, message, from_email, [req_usr.email], fail_silently=False)

                        if logging_on:
                            logger.debug('mail_count: ' + str(mail_count))

                        if not mail_count:
                            class_str = 'border_bg_invalid'
                            msg_list +=  ("<p class='pb-2'>",
                                               str(_('An error occurred')),
                                               str(_('The email has not been sent.')), '</p>')
                        else:
                            # - return message 'We have sent an email to user'
                            class_str = 'border_bg_transparent'
                            msg_list += ("<p class='pb-2'>",
                                         str(_("We have sent an email with a 6 digit verification code to the email address:")),
                                         '<br>', req_usr.email, '<br>',
                                         str(_("Enter the verification code and click 'Submit Ex form' to submit the Ex1 form.")),
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

# - end of StudentsubjectSendEmailExformView


#####################################################################################
@method_decorator([login_required], name='dispatch')
class StudentsubjectApproveOrSubmitEx1View(View):  # PR2021-07-26

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= StudentsubjectApproveOrSubmitEx1View ============= ')

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
                requsr_usergroup_list = req_usr.usergroup_list
                # msg_err is made on client side. Here: just skip if user has no or multiple functions

                if logging_on:
                    logger.debug('requsr_usergroup_list: ' + str(requsr_usergroup_list) + ' ' + str(type(requsr_usergroup_list)))
                    # requsr_usergroup_list: ['admin', 'auth1', 'edit'] <class 'list'>

                is_auth1 = 'auth1' in requsr_usergroup_list
                is_auth2 = 'auth2' in requsr_usergroup_list
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
                if len(msg_list):
                    msg_html = '<br>'.join(msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})

                else:

    # - get selected mode. Modes are 'approve_test', 'approve_submit', 'approve_reset', 'submit_test' 'submit_submit'
                    mode = upload_dict.get('mode')
                    is_approve = True if mode in ('approve_test', 'approve_submit', 'approve_reset') else False
                    is_submit = True if mode in ('submit_test', 'submit_submit') else False
                    is_reset = True if mode == 'approve_reset' else False
                    is_test = True if mode in ('approve_test', 'submit_test') else False

                    if logging_on:
                        logger.debug('upload_dict' + str(upload_dict))
                        logger.debug('mode: ' + str(mode))

# - when mode = submit_submit: check verificationcode.
                    verification_is_ok = True
                    if is_submit and not is_test:
                        verification_is_ok, verif_msg_html = self.check_verifcode_local(upload_dict, request)
                        if verif_msg_html:
                            msg_html = verif_msg_html
                        if verification_is_ok:
                            update_wrap['verification_is_ok'] = True

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
                                logger.debug('selected_dict: ' + str(selected_dict))

# +++ get selected studsubj_rows
                        # TODO exclude published rows?? Yes, but count them when checking. You cannot approve or undo approve or submit when submitted

                        crit = Q(student__school=sel_school) & \
                               Q(student__department=sel_department)
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
                            logger.debug('sel_lvlbase_pk:   ' + str(sel_lvlbase_pk))
                            logger.debug('sel_sctbase_pk:  ' + str(sel_sctbase_pk))
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
                                    'already_approved_by_auth': 0,
                                    'auth_missing': 0,
                                    'test_is_ok': False
                                    }
                        if studsubjects is not None:

# +++ create new published_instance. Only save it when it is not a test
                            # file_name will be added after creating Ex-form
                            published_instance = None
                            published_instance_pk = None
                            if is_submit and not is_test:
                                now_arr = upload_dict.get('now_arr')

                                published_instance = create_published_Ex1_instance(
                                    sel_school=sel_school,
                                    sel_department=sel_department,
                                    sel_examperiod=1,
                                    now_arr=now_arr,
                                    request=request)  # PR2021-07-27
                                if published_instance:
                                    published_instance_pk = published_instance.pk

                            if logging_on:
                                logger.debug('published_instance_pk' + str(published_instance_pk))

                            studsubj_rows = []

# +++++ loop through subjects
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
                                        is_committed, is_saved, is_saved_error = approve_studsubj(studsubj, requsr_auth, is_test, is_reset, count_dict, request)
                                    elif is_submit:
                                        is_committed, is_saved, is_saved_error = submit_studsubj(studsubj, is_test, published_instance, count_dict, request)

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
    # +++++  end of loop through  subjects

                            count_dict['count'] = row_count
                            count_dict['student_count'] = len(student_pk_list)
                            count_dict['student_committed_count'] = len(student_committed_list)
                            count_dict['student_saved_count'] = len(student_saved_list)
                            count_dict['student_saved_error_count'] = len(student_saved_error_list)
                            update_wrap['approve_count_dict'] = count_dict

    # - create msg_html with info of rows
                            msg_html = self.create_msg_list(count_dict, requsr_auth, is_approve, is_test)

# +++++ create Ex1 form
                            if row_count:
                                if is_submit and not is_test:
                                    self.create_Ex1_form(
                                        published_instance=published_instance,
                                        sel_examyear=sel_examyear,
                                        sel_school=sel_school,
                                        sel_department=sel_department,
                                        save_to_disk=True,
                                        request=request,
                                        user_lang=user_lang)

                                    #update_wrap['updated_published_rows'] = create_published_rows(
                                    #    sel_examyear_pk=sel_examyear.pk,
                                    #    sel_schoolbase_pk=sel_school.base_id,
                                    #    sel_depbase_pk=sel_department.base_id,
                                    #    published_pk=published_instance.pk
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

    def create_msg_list(self, count_dict, requsr_auth, is_approve, is_test):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('  ----- create_msg_list -----')
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
        already_approved_by_auth = count_dict.get('already_approved_by_auth', 0)
        double_approved = count_dict.get('double_approved', 0)

        if logging_on:
            logger.debug('.....count: ' + str(count))
            logger.debug('.....committed: ' + str(committed))
            logger.debug('.....already_published: ' + str(already_published))
            logger.debug('.....auth_missing: ' + str(auth_missing))
            logger.debug('.....already_approved_by_auth: ' + str(already_approved_by_auth))
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

# - create first line with 'The selection contains 4 candidates with 39 subjects'
        msg_list = ["<div class='p-2 ", class_str, "'>"]
        if is_test:
            msg_list.append(''.join(( "<p class='pb-2'>",
                        str(_("The selection contains %(stud)s with %(subj)s.") %
                            {'stud': get_student_count_text(student_count), 'subj': get_subject_count_text(count)}),
                        '</p>')))

# - if any subjects skipped: create lines 'The following subjects will be skipped' plus the reason
        if is_test and committed < count:
            willbe_or_are_txt = pgettext_lazy('plural', 'will be') if is_test else _('are')
            msg_list.append("<p class='pb-0'>" + str(_("The following subjects %(willbe)s skipped")
                                                     % {'willbe': willbe_or_are_txt}) + ':</p><ul>')
            if already_published:
                msg_list.append('<li>' + str(_("%(subj)s already submitted") %
                                             {'subj': get_subjects_are_text(already_published)}) + ';</li>')
            if auth_missing:
                msg_list.append('<li>' + str(_("%(subj)s not fully approved") %
                                             {'subj': get_subjects_are_text(auth_missing)}) + ';</li>')
                show_msg_first_approve_by_pres_secr = True
            if already_approved_by_auth:
                msg_list.append('<li>' + get_subjects_are_text(already_approved_by_auth) + str(_(' already approved')) + ';</li>')
            if double_approved:
                other_function =  str(_('president')) if requsr_auth == 'auth2' else str(_('secretary'))
                msg_list.append(''.join(('<li>', get_subjects_are_text(double_approved),
                                         str(_(' already approved by you as ')), other_function, '.<br>',
                                str(_("You cannot approve a subject both as president and as secretary.")), '</li>')))
            msg_list.append('</ul>')

# - line with text how many subjects will be approved / submitted
        msg_list.append('<p>')
        if is_test:
            if is_approve:
                if not committed:
                    msg_str = _("No subjects will be approved.")
                else:
                    student_count_txt = get_student_count_text(student_committed_count)
                    subject_count_txt = get_subject_count_text(committed)
                    will_be_text = get_will_be_text(committed)
                    approve_txt = _('approved.')
                    msg_str = ' '.join((str(subject_count_txt), str(_('of')),  str(student_count_txt),
                                        str(will_be_text), str(approve_txt)))
            else:
                if not committed:
                    if is_approve:
                        msg_str = _("No subjects will be approved.")
                    else:
                        msg_str = _("The Ex1 form can not be submitted.")
                else:
                    student_count_txt = get_student_count_text(student_committed_count)
                    subject_count_txt = get_subject_count_text(committed)
                    will_be_text = get_will_be_text(committed)
                    approve_txt = _('approved.') if is_approve else _('added to the Ex1 form.')
                    msg_str = ' '.join((str(subject_count_txt), str(_('of')),  str(student_count_txt),
                                        str(will_be_text), str(approve_txt)))
        else:
            student_count_txt = get_student_count_text(student_saved_count)
            subject_count_txt = get_subject_count_text(saved)
            student_saved_error_count_txt = get_student_count_text(student_saved_error_count)
            subject_error_count_txt = get_subject_count_text(saved_error)

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
                msg_str = str(_("The Ex1 form has %(not)s been submitted.") % {'not': not_str})
                if saved:
                    student_count_txt = get_student_count_text(student_saved_count)
                    subject_count_txt = get_subject_count_text(saved)
                    msg_str += '<br>' + str(_("It contains %(subj)s of %(stud)s.")
                                            % {'stud': student_count_txt, 'subj': subject_count_txt})
        msg_list.append(str(msg_str))
        msg_list.append('</p>')

# - warning if any subjects are not fully approved
        if show_warning_msg and not is_approve:
            msg_list.append("<p class='pt-2'><b>")
            msg_list.append(str(_('WARNING')))
            msg_list.append(':</b> ')
            msg_list.append(str(_('There are subjects that are not fully approved.')))
            msg_list.append(' ')
            msg_list.append(str(_('They will not be included in the Ex1 form.')))
            msg_list.append(' ')
            msg_list.append(str(_('Are you sure you want to submit the Ex1 form?')))
            msg_list.append('</p>')

# - add line 'both prseident and secretary must first approve all subjects before you can submit the Ex form
        if show_msg_first_approve_by_pres_secr:
            msg_txt = ''.join(('<p>', str(_('The president and the secretary must approve all subjects before you can submit the Ex1 form.')), '</p>'))
            msg_list.append(msg_txt)

        msg_list.append('</div>')

        msg_html = ''.join(msg_list)
        return msg_html
    # - end of create_submit_msg_list

    def create_Ex1_form(self, published_instance, sel_examyear, sel_school, sel_department, save_to_disk, request, user_lang):
        #PR2021-07-27 PR2021-08-14
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= create_Ex1_form ============= ')

# get text from examyearsettin  g
        settings = af.get_exform_text(sel_examyear, ['exform', 'ex1'])
        #if logging_on:
        #    logger.debug('settings: ' + str(settings))

# +++ create Ex1 xlsx file
        grd_exc.create_ex1_xlsx(
            published_instance=published_instance,
            examyear=sel_examyear,
            school=sel_school,
            department=sel_department,
            settings=settings,
            save_to_disk=save_to_disk,
            request=request,
            user_lang=user_lang)
    # - end of create_Ex1_form

    def check_verifcode_local(self, upload_dict, request ):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('  ----- check_verifcode_local -----')

        _verificationkey = upload_dict.get('verificationkey')
        _verificationcode = upload_dict.get('verificationcode')
        is_ok, is_expired = False, False
        msg_html, msg_txt = None, None
        if _verificationkey and _verificationcode:
            key_code = '_'.join((_verificationkey, _verificationcode))
        # - get saved key_code
            saved_dict = acc_view.get_usersetting_dict(c.KEY_VERIFICATIONCODE, request)
            if logging_on:
                logger.debug('saved_dict: ' + str(saved_dict))

            if saved_dict:
        # - check if code is expired:
                saved_expirationtime = saved_dict.get('expirationtime')
                # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
                now_iso = datetime.now().isoformat()
                if logging_on:
                    logger.debug('saved_expirationtime: ' + str(saved_expirationtime))
                    logger.debug('now_iso: ' + str(now_iso))
                if now_iso > saved_expirationtime:
                    is_expired = True
                    msg_txt = _("The verificationcode has expired.")
                else:
        # - check if code is correct:
                    saved_form = saved_dict.get('form')
                    saved_key_code = saved_dict.get('key_code')
                    if logging_on:
                        logger.debug('saved_form: ' + str(saved_form))
                        logger.debug('saved_key_code: ' + str(saved_key_code))

                    if saved_form == 'Ex1' and key_code == saved_key_code:
                        is_ok = True
                    else:
                        msg_txt = _("The verificationcode you have entered is not correct.")

        # - delete setting when expired or ok
                if is_ok or is_expired:
                    acc_view.set_usersetting_dict(c.KEY_VERIFICATIONCODE, None, request)

        if logging_on:
            logger.debug('is_ok: ' + str(is_ok))
            logger.debug('is_expired: ' + str(is_expired))
        if msg_txt:
            msg_html = ''.join(("<div class='p-2 border_bg_invalid'>",
                                "<p class='pb-2'>",
                                str(msg_txt),
                                '</p>'))

        return is_ok, msg_html
    # - end of check_verifcode_local

# --- end of StudentsubjectApproveOrSubmitEx1View


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
        messages = []

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = req_usr.permit_list('page_studsubj')
            if permit_list:
                has_permit = 'permit_approve_subject' in permit_list
            if logging_on:
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

                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)
                if len(msg_list):
                    msg_html = '<br>'.join(msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})

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
                                logger.debug('     student_pk: ' + str(student_pk))
                                logger.debug('     studsubj_pk: ' + str(studsubj_pk))

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

# - update studsubj
                            if student and studsubj:
                                if logging_on:
                                    logger.debug('studsubj: ' + str(studsubj))
                                update_studsubj(studsubj, studsubj_dict, error_dict, request)

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
                                rows = create_studentsubject_rows(
                                    examyear=sel_examyear,
                                    schoolbase=sel_school.base,
                                    depbase=sel_department.base,
                                    requsr_same_school=True,  # check for same_school is included in may_edit
                                    setting_dict={},
                                    append_dict=append_dict,
                                    student_pk=student.pk,
                                    studsubj_pk=studsubj.pk
                                )
                                if rows:
                                    studsubj_row = rows[0]
                                    if studsubj_row:
                                        studsubj_rows.append(studsubj_row)
# - end of loop
# -------------------------------------------------
                        if studsubj_rows:
                            update_wrap['updated_studsubj_approve_rows'] = studsubj_rows

        if len(messages):
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

def get_subject_count_text(count):
    if not count:
        msg_text = str(_('no subjects'))
    elif count == 1:
        msg_text = str(_('1 subject'))
    else:
        msg_text = ' '.join((str(count), str(_('subjects'))))
    return msg_text


def get_subjects_are_text(count):
    if not count:
        msg_text = str(_('no subjects are'))
    elif count == 1:
        msg_text = str(_('1 subject is'))
    else:
        msg_text = str(count) + str(_(' subjects are'))
    return msg_text


def approve_studsubj(studsubj, requsr_auth, is_test, is_reset, count_dict, request):
    # PR2021-07-26
    # status_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- approve_studsubj -----')
        logger.debug('requsr_auth:  ' + str(requsr_auth))
        logger.debug('is_reset:     ' + str(is_reset))

    is_committed = False
    is_saved = False
    is_saved_error = False
    if studsubj:
        req_user = request.user

# - skip if this studsubj is already published
        published = getattr(studsubj, 'subj_published')
        if logging_on:
            logger.debug('published:    ' + str(published))

        if published:
            count_dict['already_published'] += 1
        else:
            requsr_authby_field = 'subj_' + requsr_auth + 'by'

# - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved
            auth1by = getattr(studsubj, 'subj_auth1by')
            auth2by = getattr(studsubj, 'subj_auth2by')
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
                    count_dict['already_approved_by_auth'] += 1
                else:

# - skip if this author (like 'president') has already approved this studsubj
        # under a different permit (like 'secretary' or 'commissioner')
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


def submit_studsubj(studsubj, is_test, published_instance, count_dict, request):  # PR2021-01-21 PR2021-07-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- submit_studsubj -----')

    is_committed = False
    is_saved = False
    is_saved_error = False

    if studsubj:

# - check if this studsubj is already published
        published = getattr(studsubj, 'subj_published')
        if logging_on:
            logger.debug('subj_published: ' + str(published))
        if published:
            count_dict['already_published'] += 1
        else:

# - check if this studsubj / examtype is approved by all auth
            auth1by = getattr(studsubj, 'subj_auth1by')
            auth2by = getattr(studsubj, 'subj_auth2by')
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
                            setattr(studsubj, 'subj_published', published_instance)
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


def create_published_Ex1_instance(sel_school, sel_department, sel_examperiod, now_arr, request):  # PR2021-07-27
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_published_Ex1_instance -----')
        logger.debug('request.user: ' + str(request.user))

    # create new published_instance and save it when it is not a test (this function is only called when it is not a test)
    # filename is added after creating file in create_ex1_xlsx
    depbase_code = sel_department.base.code if sel_department.base.code else '-'
    school_code = sel_school.base.code if sel_school.base.code else '-'
    school_abbrev = sel_school.abbrev if sel_school.abbrev else '-'

    # to be used when submitting Ex4 form
    examtype_caption = ''
    exform = 'Ex1'
    if sel_examperiod == 1:
        examtype_caption = 'tv1'
    if sel_examperiod == 2:
        examtype_caption = 'tv2'
        exform = 'Ex4'
    elif sel_examperiod == 3:
        examtype_caption = 'tv3'
        exform = 'Ex4'
    elif sel_examperiod == 4:
        examtype_caption = 'vrst'

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
        examperiod=sel_examperiod,
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
        logger.debug(' request.user: ' + str(request.user))
        logger.debug('published_instance.saved: ' + str(published_instance))
        logger.debug('published_instance.pk: ' + str(published_instance.pk))
        logger.debug('published_instance.modifiedby: ' + str(published_instance.modifiedby))

    return published_instance
# - end of create_published_Ex1_instance


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
class StudentsubjectUploadView(View):  # PR2020-11-20 PR2021-08-17

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

                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))
                    logger.debug('sel_examyear: ' + str(sel_examyear))
                    logger.debug('sel_school: ' + str(sel_school))
                    logger.debug('sel_department: ' + str(sel_department))

# - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                student = None

                if len(msg_list):
                    msg_html = '<br>'.join(msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                elif may_edit:
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

# - get list of studentsubjects from upload_dict
                studsubj_list = None
                if student:
                    studsubj_list = upload_dict.get('studsubj_list')
                if studsubj_list:
                    studsubj_rows = []

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
                        error_dict = {}

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
                            # if published: don't delete, but set deleted=True, so its remains in the Ex1 form
                            #               also set grades 'deleted=True
                            # if not published: delete studsubj, grades will be cascade deleted
                            if studsubj:
                                this_text = None
                                if studsubj.schemeitem:
                                    subject = studsubj.schemeitem.subject
                                    if subject and subject.name:
                                        this_text = _("Subject '%(tbl)s' ") % {'tbl': subject.name}

                                if logging_on:
                                    logger.debug('this_text: ' + str(this_text))

                                if studsubj.subj_published or \
                                    studsubj.exem_published or \
                                    studsubj.reex_published or \
                                    studsubj.reex3_published or \
                                    studsubj.pok_published:
                    # - if published: set tobedeleted=True, so its remains in the Ex1 form
                                    setattr(studsubj, 'tobedeleted', True)
                                    studsubj.save(request=request)
                                    if logging_on:
                                        logger.debug('studsubj.tobedeleted: ' + str(studsubj.tobedeleted))
                                    grades = stud_mod.Grade.objects.filter(studentsubject=studsubj)
                            # also set grades tobedeleted=True
                                    if grades:
                                        for grade in grades:
                                            setattr(grade, 'tobedeleted', True)
                                            grade.save(request=request)
                                            if logging_on:
                                                logger.debug('grade.tobedeleted: ' + str(grade.tobedeleted))
                                else:
                    # - if not yet published: delete Grades, Studentsubjectnote, Noteattachment will also be deleted with cascade_delete
                                    err_list = []  # TODO
                                    deleted_ok = sch_mod.delete_instance(studsubj, messages, err_list, request, this_text)
                                    if logging_on:
                                        logger.debug('deleted_ok: ' + str(deleted_ok))
                                    if deleted_ok:
                                        # - add deleted_row to studsubj_rows
                                        studsubj_rows.append({'stud_id': student.pk,
                                                              'studsubj_id': studsubj_pk,
                                                             'mapid': 'studsubj_' + str(student.pk) + '_' + str(studsubj_pk),
                                                             'deleted': True})
                                        studsubj = None

                                        if logging_on:
                                            logger.debug('deleted_row: ' + str(studsubj_rows))

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
                            if logging_on:
                                logger.debug('studsubj and mode: ' + str(studsubj))
                            update_studsubj(studsubj, studsubj_dict, error_dict, request)

# - add update_dict to update_wrap
                        if studsubj:
                            # TODO check value of error_dict
                            if error_dict:
                                append_dict['error'] = error_dict
                            rows = create_studentsubject_rows(
                                examyear=sel_examyear,
                                schoolbase=sel_school.base,
                                depbase=sel_department.base,
                                requsr_same_school=True,  # check for same_school is included in may_edit
                                setting_dict={},
                                append_dict=append_dict,
                                student_pk=student.pk,
                                studsubj_pk=studsubj.pk
                            )
                            if logging_on:
                                logger.debug('error_dict: ' + str(error_dict))
                                logger.debug('rows: ' + str(rows))

                            if rows:
                                studsubj_row = rows[0]
                                if studsubj_row:
                                    studsubj_rows.append(studsubj_row)
# - end of loop
# -------------------------------------------------
                    if logging_on:
                        logger.debug('studsubj_rows: ' + str(studsubj_rows))

                    if studsubj_rows:
                        update_wrap['updated_MSTUDSUBJ_rows'] = studsubj_rows

# +++ validate subjects of student
                        # no message necessary, done by test before saving
                        #msg_html = stud_val.validate_studentsubjects(student)
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

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                    # upload_dict: {'student_pk': 8470, 'studsubj_pk': 61203, 'has_exemption': True}
                # requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase_pk)

# ----- get selected examyear, school and department from usersettings
                # check requsr_same_school is part of get_selected_ey_school_dep_from_usersetting
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))
                    logger.debug('sel_examyear: ' + str(sel_examyear))
                    logger.debug('sel_school: ' + str(sel_school))
                    logger.debug('sel_department: ' + str(sel_department))

# - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                student = None
                if len(msg_list):
                    msg_html = '<br>'.join(msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                elif may_edit:
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

                    msg_dict = {}
                    update_studsubj(studsubj, upload_dict, msg_dict, request)

# - add update_dict to update_wrap
                    # TODO check value of msg_dict
                    #  msg_dict['err_' + field] = str(_("Title and subjects only allowed in subjects with character 'Werkstuk'."))
                    #  msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')
                    msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')
                    append_dict = {}
                    if msg_dict:
                        append_dict['error'] = msg_dict
                    studsubj_rows = create_studentsubject_rows(
                        examyear=sel_examyear,
                        schoolbase=sel_school.base,
                        depbase=sel_department.base,
                        requsr_same_school=True,  # check for same_school is included in may_edit
                        setting_dict={},
                        append_dict=append_dict,
                        student_pk=student.pk,
                        studsubj_pk=studsubj.pk
                    )
                    if logging_on:
                        logger.debug('msg_dict: ' + str(msg_dict))
                        logger.debug('studsubj_rows: ' + str(studsubj_rows))

                    if studsubj_rows:
                        update_wrap['updated_studsubj_rows'] = studsubj_rows

        if len(messages):
            update_wrap['messages'] = messages
        if logging_on:
            logger.debug('update_wrap: ' + str(update_wrap))

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentsubjectSingleUpdateView


#######################################################
def update_studsubj(instance, upload_dict, msg_dict, request):
    # --- update existing and new instance PR2019-06-06
    # add new values to update_dict (don't reset update_dict, it has values)
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_studsubj -------')
        logger.debug('upload_dict' + str(upload_dict))
        # upload_dict{'mode': 'update', 'studsubj_pk': 26993, 'schemeitem_pk': 2033, 'subj_auth2by': 48}

    save_changes = False
    for field, new_value in upload_dict.items():
# a. get new_value and saved_value

        if logging_on:
            logger.debug('field: ' + str(field) + ' new_value: ' + str(new_value))

# +++ save changes in instance fields
        if field in ['pws_title', 'pws_subjects']:
            # only allowed when schemeitem has_pws = True
            if not instance.schemeitem.has_pws:
                msg_dict['err_' + field] = str(_("Title and subjects are not allowed in this subject."))
            else:
                saved_value = getattr(instance, field)
                if logging_on:
                    logger.debug('saved_value: ' + str(saved_value))
                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

        elif field in ['is_extra_nocount','is_extra_counts', 'is_elective_combi']:
            saved_value = getattr(instance, field)
            if logging_on:
                logger.debug('saved_value: ' + str(saved_value))

            if new_value != saved_value:
                setattr(instance, field, new_value)
                save_changes = True

        elif field in ['has_exemption', 'has_reex', 'has_reex03']:
            saved_value = getattr(instance, field)
            if logging_on:
                logger.debug('saved_value: ' + str(saved_value))

            if new_value != saved_value:
                setattr(instance, field, new_value)
                save_changes = True
                exam_period = None
                if field =='has_exemption':
                    exam_period = c.EXAMPERIOD_EXEMPTION
                elif field =='has_reex':
                    exam_period = c.EXAMPERIOD_SECOND
                elif field =='has_reex03':
                    exam_period = c.EXAMPERIOD_SECOND

       # - check if grade of this exam_period exists
                grade = stud_mod.Grade.objects.filter(studentsubject=instance, examperiod=exam_period).first()
                if grade:
                    if new_value:
       # - if it exists while old has_exemption etc. was False: it must be deleted row. Undelete
                        setattr(grade, 'deleted', False)
                    else:
       # - when new has_exemption etc. is False: delete row by setting deleted=True and reset all fields
                        setattr(grade, 'deleted', True)
                        for fld in ('pescore', 'cescore', 'segrade', 'pegrade', 'cegrade', 'pecegrade', 'finalgrade',
                                    'sepublished', 'pepublished', 'cepublished'):
                            setattr(grade, fld, None)
                        for fld in ('seauth', 'peauth', 'ceauth', 'status'):
                            setattr(grade, fld, 0)
                        grade.save(request=request)
                elif new_value:
       # - if it does not exist and new has_exemption etc. is True: create new grade row
                    grade = stud_mod.Grade(
                        studentsubject=instance,
                        examperiod=exam_period)
                    grade.save(request=request)
                if grade:
                    grade.save(request=request)


        #   subj_auth1by, subj_auth2by, subjpublished, exem_auth1by, exem_auth2by, exemppublished,
        #   reex_auth1by, reex_auth2by, reexpublished, reex3_auth1by, reex3_auth2by, reex3published,
        #   pok_auth1by, pok_auth2by, pokpublished,

        #elif field in ('subj_auth1by', 'subj_auth2by', 'exem_auth1by', 'exem_auth2by',
        #               'reex_auth1by', 'reex_auth2by', 'reex3_auth1by', 'reex3_auth2by',
        #               'pok_auth1by', 'pok_auth2by'):
        elif '_auth' in field:
            prefix, authby = field.split('_')
            if logging_on:
                logger.debug('field: ' + str(field) )
                logger.debug('new_value: ' + str(new_value))

                logger.debug('prefix: ' + str(prefix) )
                logger.debug('authby: ' + str(authby) )

# - check if instance is published. Authorization of published instances cannot be changed.
            err_published, err_same_user = False, False
            fld_published = prefix + '_published'
            item_published = getattr(instance, fld_published)
            if item_published:
                err_published = True
# - check other authorization, to check if it is the same user. Only when auth is set to True
            elif new_value:
                authby_other = 'auth2by' if authby == 'auth1by' else 'auth1by'
                fld_other = prefix + '_' + authby_other
                other_authby = getattr(instance, fld_other)

                if logging_on:
                    logger.debug('other_authby: ' + str(other_authby) )
                    logger.debug('request.user: ' + str(request.user) )

                if other_authby and other_authby == request.user:
                    err_same_user = True
            if not err_published and not err_same_user:
                if new_value:
                    setattr(instance, field, request.user)
                else:
                    setattr(instance, field, None)
                save_changes = True

            #msg_dict['err_' + prefix] = _('This item is published. You cannot change its authorization.')
            # msg_dict['err_' + prefix] = _('The same user cannot authorize both as chairman and secretary.')
    # --- end of for loop ---

# 5. save changes`
    if save_changes:
        try:
            instance.save(request=request)
            if logging_on:
                logger.debug('The changes have been saved: ' + str(instance))
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')
# --- end of update_studsubj



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
                        country_abbrev = sel_examyear.country.abbrev.lower()
                        examyear_str = str(sel_examyear.code)
                        file_dir = '/'.join((country_abbrev, examyear_str, 'attachment'))
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

                    grade_note_icon_rows = grd_vw.create_grade_note_icon_rows(
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
def delete_student(student, student_rows, msg_list, error_list, request):
    # --- delete student # PR2021-07-18

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_subject ----- ')
        logger.debug('student: ' + str(student))

    deleted_ok = False

# - create student_row - to be returned after successfull delete
    student_row = {'id': student.pk,
                   'mapid': 'student_' + str(student.pk),
                   'deleted': True}
    base_pk = student.base.pk

    this_txt = _("Candidate '%(tbl)s' ") % {'tbl': student.fullname}
    header_txt = _("Delete candidate")

# - check if student has approved or submitted subjects PR2021-08-21
    has_error, ey_locked, sch_locked, published, approved = stud_val.validate_studsubj_appr_subm_locked(student)
    if has_error or ey_locked or sch_locked or published or approved:
        msg_txt1 = ''
        msg_txt2 = _("%(cpt)s could not be deleted.") % {'cpt': this_txt}
        class_str = "border_bg_invalid"
        if has_error:
            msg_txt1 = _('An error occurred while checking the subjects.')
        elif ey_locked:
            msg_txt1 = _('This exam year is locked.')
        elif sch_locked:
            msg_txt1 = _('This school is locked.')
        elif published:
            msg_txt1 = _('This candidate has submitted subjects.')
            msg_txt2 = ''.join((str(_("You can delete this candidate, but you will have to submit the changes in a new Ex1 form.")),
                                '<br><b>', str(_('Please note')), '</b>:<br>',
                        str(_("Don't submit a new Ex1 form till the start of the exams. In this way all changes can be submitted in one additional Ex1 form."))))
            class_str = "border_bg_warning"
        elif approved:
            msg_txt1 = _('This candidate has approved subjects.')
            msg_txt2 = _("Remove the approval of the subjects and then try again.")
            class_str = "border_bg_warning"
        msg_html = '<br>'.join((str(msg_txt1), str(msg_txt2)))
        msg_list.append({'header': str(header_txt), 'class': class_str, 'msg_html': msg_html})

    else:
        deleted_ok = sch_mod.delete_instance(student, msg_list, error_list, request, this_txt, header_txt)

    if logging_on:
        logger.debug('msg_list: ' + str(msg_list))
    if deleted_ok:
# - add deleted_row to subject_rows
        student_rows.append(student_row)

# - check if this student also exists in other examyears.
        students_exist = stud_mod.Student.objects.filter(base_id=base_pk).exists()
# - If not: delete also subject_base
        if not students_exist:
            student_base = stud_mod.Studentbase.objects.get_or_none(id=base_pk)
            if student_base:
                student_base.delete()

    if logging_on:
        logger.debug('student_rows' + str(student_rows))
        logger.debug('msg_list' + str(msg_list))

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
    # save studentbase beyond, to prevent studentbases without student
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
            msg_list.append(msg_err)

        msg_err = av.validate_notblank_maxlength(lastname_stripped, c.MAX_LENGTH_FIRSTLASTNAME, _('The last name'))
        if msg_err:
            has_error = True
            msg_list.append(msg_err)

        msg_err = av.validate_notblank_maxlength(firstname_stripped, c.MAX_LENGTH_FIRSTLASTNAME, _('The first name'))
        if msg_err:
            has_error = True
            msg_list.append(msg_err)

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
            messages.append({'header': _('Add candidate'), 'class': "border_bg_invalid", 'msg_html': msg_html})
            error_list.extend(msg_list)
            if logging_on:
                logger.debug('msg_list: ' + str(msg_list))
        else:

# - make iseveningstudent / islexstudent true when iseveningschool / islexschool, not when also isdayschool
            # PR 2021-09-08 debug tel Lionel Mongen CAL: validation still chekcs for required subjects
            # reason: CAL iseveningschool, but styudents were not set iseveningstudent
            # also solved by checking validation on iseveningstudent only when school is both dayschool and evveningschool,
            # check on eveningschool when only eveningschool
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
def update_student_instance(instance, upload_dict, idnumber_list, examnumber_list, msg_list, error_list, request, skip_save):
    # --- update existing and new instance PR2019-06-06 PR2021-07-19

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_student_instance -------')
        logger.debug('upload_dict: ' + str(upload_dict))
        logger.debug('instance:    ' + str(instance))
        instance_pk = instance.pk if instance else 'None'
        logger.debug('instance.pk: ' + str(instance_pk))

    changes_are_saved = False
    save_error = False
    field_error = False

    if instance:
        student_name = ' '.join([instance.firstname, instance.lastname])

        save_changes = False
        update_scheme = False
        recalc_regnumber = False

        for field, new_value in upload_dict.items():
            try:
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
                elif field in ('bis_exam', 'has_dyslexie', 'iseveningstudent', 'islexstudent'):
                    saved_value = getattr(instance, field)
                    if new_value is None:
                        new_value = False
                    # PR2021-08-29 debug: when importing value can be 'x'. Convert to True when not a boolean
                    elif not isinstance(new_value, bool):
                        new_value = True

                    if new_value != saved_value:
                        if logging_on:
                            logger.debug('saved ' + str(field) + ': ' + str(saved_value) + ' ' + str(type(saved_value)))
                            logger.debug('new   ' + str(field) + ': ' + str(new_value) + ' ' + str(type(new_value)))

                        setattr(instance, field, new_value)
                        save_changes = True

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                logger.error('field: ' + str(field) + ' new_value: ' + str(new_value) + ' ' + str(type(new_value)))

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

            if logging_on:
                logger.debug('department: ' + str(department))
                logger.debug('level:      ' + str(level))
                logger.debug('sector:     ' + str(sector))
                logger.debug('scheme:     ' + str(scheme))

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
                depbase =  getattr(department, 'base')

            level = getattr(instance, 'level')
            if level:
                levelbase =  getattr(level, 'base')

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
            new_regnumber = stud_fnc.calc_regnumber(school_code, gender, examyear_code, examnumber, depbase, levelbase)

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

    if logging_on:
        logger.debug('changes_are_saved: ' + str(changes_are_saved))
        logger.debug('field_error: ' + str(field_error))
        logger.debug('error_list: ' + str(error_list))
    return changes_are_saved, save_error, field_error
# - end of update_student_instance


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def update_scheme_in_studsubj(student, request):
    # --- update_scheme_in_studsubj # PR2021-03-13
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_scheme_in_studsubj ----- ')
        logger.debug('student: ' + str(student))

    if student:
        # - update scheme in student, also remove if necessary
        new_scheme = subj_mod.Scheme.objects.get_or_none(
            department=student.department,
            level=student.level,
            sector=student.sector)
        setattr(student, 'scheme', new_scheme)

        if logging_on:
            logger.debug('new_scheme: ' + str(new_scheme))

    # - loop through studsubj of this student
        studsubjects = stud_mod.Studentsubject.objects.filter(
            student=student
        )
        for studsubj in studsubjects:
            if new_scheme is None:
                # delete studsubj when no scheme
                # check if studsubj is submitted, set tobedeleted = True if submitted
                set_studsubj_tobedeleted_or_tobechanged(studsubj, True, None, request)  # True = tobedeleted
            else:
                old_subject = studsubj.schemeitem.subject
                old_subjecttype = studsubj.schemeitem.subjecttype

        # skip when studsub scheme equals new_scheme
                if studsubj.schemeitem.scheme != new_scheme:
         # check how many times this subject occurs in new scheme
                    count_subject_in_newscheme = subj_mod.Schemeitem.objects.filter(
                        scheme=new_scheme,
                        subject=old_subject
                        ).count()
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


def set_studsubj_tobedeleted_or_tobechanged(studsubj, tobedeleted, new_schemeitem, request):  # PR2021-08-23
    # delete studsubj when no scheme
    # check if studsubj is submitted, set delete = True if submitted
    subj_published = getattr(studsubj, 'subj_published')

    if tobedeleted:
        field = 'tobedeleted'
        if subj_published is None:
            studsubj.delete(request=request)
    else:
        field = 'tobechanged'
        setattr(studsubj, 'schemeitem', new_schemeitem)

    if subj_published:
        setattr(studsubj, field, True)
        setattr(studsubj,'prev_auth1by', getattr(studsubj, 'subj_auth1by'))
        setattr(studsubj,'prev_auth2by', getattr(studsubj, 'subj_auth2by'))
        setattr(studsubj,'prev_published', subj_published)

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

def create_studentsubject_rows(examyear, schoolbase, depbase, requsr_same_school, setting_dict, append_dict, student_pk=None, studsubj_pk=None):
    # --- create rows of all students of this examyear / school PR2020-10-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_studentsubject_rows ============= ')
        logger.debug('student_pk: ' + str(student_pk))
        logger.debug('studsubj_pk: ' + str(studsubj_pk))
        logger.debug('setting_dict: ' + str(setting_dict))
        logger.debug('append_dict: ' + str(append_dict))
    rows = []
    try:
        # create list of students of this school / examyear, possibly with filter student_pk or studsubj_pk
        # with left join of studentsubjects with deleted=False
        # when role is other than school: only when submitted, don't show students without submitted subjects
        sel_examyear_pk = examyear.pk if examyear else None
        sel_schoolbase_pk = schoolbase.pk if schoolbase else None
        sel_depbase_pk = depbase.pk if depbase else None

        # dont show studnets without subject on other users than sameschool
        left_or_inner_join = "LEFT JOIN" if requsr_same_school else "INNER JOIN"

        sel_lvlbase_pk = None
        if c.KEY_SEL_LVLBASE_PK in setting_dict:
            sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)

        sel_sctbase_pk = None
        if c.KEY_SEL_SCTBASE_PK in setting_dict:
            sel_sctbase_pk = setting_dict.get(c.KEY_SEL_SCTBASE_PK)

        sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk, 'db_id': sel_depbase_pk}
        sql_studsubj_list = ["SELECT studsubj.id AS studsubj_id, studsubj.student_id,",
            "studsubj.cluster_id, si.id AS schemeitem_id, si.scheme_id AS scheme_id,",
            "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_elective_combi,",
            "studsubj.pws_title, studsubj.pws_subjects,",
            "studsubj.has_exemption, studsubj.has_reex, studsubj.has_reex03, studsubj.pok_validthru,",
            "si.subject_id, si.subjecttype_id, si.gradetype,",
            "subjbase.code AS subj_code, subj.name AS subj_name,",
            "si.weight_se AS si_se, si.weight_ce AS si_ce,",
            "si.is_mandatory, si.is_mand_subj_id, si.is_combi, si.extra_count_allowed, si.extra_nocount_allowed,",
            "si.elective_combi_allowed, si.has_practexam,",

            "sjt.id AS sjtp_id, sjt.abbrev AS sjtp_abbrev, sjt.has_prac AS sjtp_has_prac, sjt.has_pws AS sjtp_has_pws,",
            "sjtbase.sequence AS sjtbase_sequence,",

            "studsubj.subj_auth1by_id AS subj_auth1_id, subj_auth1.last_name AS subj_auth1_usr,",
            "studsubj.subj_auth2by_id AS subj_auth2_id, subj_auth2.last_name AS subj_auth2_usr,",
            "studsubj.subj_published_id AS subj_publ_id, subj_published.modifiedat AS subj_publ_modat,",

            "studsubj.exem_auth1by_id AS exem_auth1_id, exem_auth1.last_name AS exem_auth1_usr,",
            "studsubj.exem_auth2by_id AS exem_auth2_id, exem_auth2.last_name AS exem_auth2_usr,",
            "studsubj.exem_published_id AS exem_publ_id, exem_published.modifiedat AS exem_publ_modat,",

            "studsubj.reex_auth1by_id AS reex_auth1_id, reex_auth1.last_name AS reex_auth1_usr,",
            "studsubj.reex_auth2by_id AS reex_auth2_id, reex_auth2.last_name AS reex_auth2_usr,",
            "studsubj.reex_published_id AS reex_publ_id, reex_published.modifiedat AS reex_publ_modat,",

            "studsubj.reex3_auth1by_id AS reex3_auth1_id, reex3_auth1.last_name AS reex3_auth1_usr,",
            "studsubj.reex3_auth2by_id AS reex3_auth2_id, reex3_auth2.last_name AS reex3_auth2_usr,",
            "studsubj.reex3_published_id AS reex3_publ_id, reex3_published.modifiedat AS reex3_publ_modat,",

            "studsubj.pok_auth1by_id AS pok_auth1_id, pok_auth1.last_name AS pok_auth1_usr,",
            "studsubj.pok_auth2by_id AS pok_auth2_id, pok_auth2.last_name AS pok_auth2_usr,",
            "studsubj.pok_published_id AS pok_publ_id, pok_published.modifiedat AS pok_publ_modat,",

            "studsubj.tobedeleted, studsubj.modifiedby_id, studsubj.modifiedat,",
            "SUBSTRING(au.username, 7) AS modby_username",

            "FROM students_studentsubject AS studsubj",
            "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
            "LEFT JOIN subjects_subjecttype AS sjt ON (sjt.id = si.subjecttype_id)",
            "INNER JOIN subjects_subjecttypebase AS sjtbase ON (sjtbase.id = sjt.base_id)",

            "LEFT JOIN accounts_user AS au ON (au.id = studsubj.modifiedby_id)",

            "LEFT JOIN accounts_user AS subj_auth1 ON (subj_auth1.id = studsubj.subj_auth1by_id)",
            "LEFT JOIN accounts_user AS subj_auth2 ON (subj_auth2.id = studsubj.subj_auth2by_id)",
            "LEFT JOIN schools_published AS subj_published ON (subj_published.id = studsubj.subj_published_id)",

            "LEFT JOIN accounts_user AS exem_auth1 ON (exem_auth1.id = studsubj.exem_auth1by_id)",
            "LEFT JOIN accounts_user AS exem_auth2 ON (exem_auth2.id = studsubj.exem_auth2by_id)",
            "LEFT JOIN schools_published AS exem_published ON (exem_published.id = studsubj.exem_published_id)",

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

        # only show published subject for other users than sameschool
        if not requsr_same_school:
            # PR2021-09-04 debug: examyear before 2022 have no subj_published_id. SHow them to others anyway
            if examyear is None or examyear.code >= 2022:
                sql_studsubj_list.append("AND studsubj.subj_published_id IS NOT NULL")

        sql_studsubjects = ' '.join(sql_studsubj_list)

        sql_list = ["WITH studsubj AS (" + sql_studsubjects + ")",
            "SELECT st.id AS stud_id, studsubj.studsubj_id, studsubj.schemeitem_id, studsubj.cluster_id,",
            "CONCAT('studsubj_', st.id::TEXT, '_', studsubj.studsubj_id::TEXT) AS mapid, 'studsubj' AS table,",
            "st.lastname, st.firstname, st.prefix, st.examnumber,",
            "st.scheme_id, st.iseveningstudent, st.tobedeleted, st.has_reex, st.bis_exam, st.withdrawn,",
            "studsubj.subject_id AS subj_id, studsubj.subj_code, studsubj.subj_name,",
            "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",

            "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_elective_combi,",
            "studsubj.pws_title, studsubj.pws_subjects,",
            "studsubj.has_exemption, studsubj.has_reex, studsubj.has_reex03, studsubj.pok_validthru,",

            "studsubj.is_mandatory, studsubj.is_mand_subj_id, studsubj.is_combi,",
            "studsubj.extra_count_allowed, studsubj.extra_nocount_allowed, studsubj.elective_combi_allowed,",
            "studsubj.sjtp_id, studsubj.sjtp_abbrev, studsubj.sjtp_has_prac, studsubj.sjtp_has_pws,",

            "studsubj.subj_auth1_id, studsubj.subj_auth1_usr,",
            "studsubj.subj_auth2_id, studsubj.subj_auth2_usr,",
            "studsubj.subj_publ_id, studsubj.subj_publ_modat,",

            "studsubj.exem_auth1_id, studsubj.exem_auth1_usr,",
            "studsubj.exem_auth2_id, studsubj.exem_auth2_usr,",
            "studsubj.exem_publ_id, studsubj.exem_publ_modat,",

            "studsubj.reex_auth1_id, studsubj.reex_auth1_usr,",
            "studsubj.reex_auth2_id, studsubj.reex_auth2_usr,",
            "studsubj.reex_publ_id, studsubj.reex_publ_modat,",

            "studsubj.reex3_auth1_id, studsubj.reex3_auth1_usr,",
            "studsubj.reex3_auth2_id, studsubj.reex3_auth2_usr,",
            "studsubj.reex3_publ_id, studsubj.reex3_publ_modat,",

            "studsubj.pok_auth1_id, studsubj.pok_auth1_usr,",
            "studsubj.pok_auth2_id, studsubj.pok_auth2_usr,",
            "studsubj.pok_publ_id, studsubj.pok_publ_modat,",

            "studsubj.tobedeleted, studsubj.modifiedat, studsubj.modby_username",

            "FROM students_student AS st",
            left_or_inner_join, "studsubj ON (studsubj.student_id = st.id)",
            "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
            "LEFT JOIN subjects_scheme AS scheme ON (scheme.id = st.scheme_id)",
            "LEFT JOIN subjects_package AS package ON (package.id = st.package_id)",
            "WHERE school.base_id = %(sb_id)s::INT AND school.examyear_id = %(ey_id)s::INT AND dep.base_id = %(db_id)s::INT"
            ]

        if sel_lvlbase_pk:
            sql_list.append('AND lvl.base_id = %(lvlbase_id)s::INT')
            sql_keys['lvlbase_id'] = sel_lvlbase_pk
        if sel_sctbase_pk:
            sql_list.append('AND sct.base_id = %(sctbase_id)s::INT')
            sql_keys['sctbase_id'] = sel_sctbase_pk
        if studsubj_pk:
            sql_list.append('AND studsubj.studsubj_id = %(studsubj_id)s::INT')
            sql_keys['studsubj_id'] = studsubj_pk
        if student_pk:
            sql_keys['st_id'] = student_pk
            sql_list.append('AND st.id = %(st_id)s::INT')

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
            if logging_on:
                logger.debug('row: ' + str(row))
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

    # - add messages to all studsubj_rows, only when student_pk or studsubj_pk have value
            if student_pk or studsubj_pk:
                if rows:
                    for row in rows:
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
            sel_examyear_instance = af.get_selected_examyear_from_usersetting(request)
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
def create_orderlist_rows(sel_examyear_code, request):
    # --- create rows of all schools with published subjects PR2021-08-18
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== students.view create_orderlist_rows ============= ')
        logger.debug('sel_examyear_code: ' + str(sel_examyear_code) + ' ' + str(type(sel_examyear_code)))

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

    requsr_country_pk = request.user.country.pk
    is_curacao = request.user.country.abbrev.lower() == 'cur'
    show_sxm_only = "AND ey.country_id = %(requsr_country_pk)s::INT" if not is_curacao else ''

    sel_exam_period = 1
    sql_keys = {'ey_code_int': sel_examyear_code,
                'ex_period_int': sel_exam_period,
                'default_role': c.ROLE_008_SCHOOL,
                'requsr_country_pk': requsr_country_pk}

    sql_sublist = ["SELECT st.school_id AS school_id, publ.id AS subj_published_id, count(*) AS publ_count,",
        "publ.datepublished, publ.examperiod",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",

        "INNER JOIN schools_published AS publ ON (publ.id = studsubj.subj_published_id)",
        "WHERE publ.examperiod = %(ex_period_int)s::INT",
        "AND NOT studsubj.tobedeleted",

        "GROUP BY st.school_id, publ.id, publ.datepublished, publ.examperiod"
    ]
    sub_sql = ' '.join(sql_sublist)

    total_sublist = ["SELECT st.school_id AS school_id, count(*) AS total",
        "FROM students_studentsubject AS studsubj",
        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "WHERE NOT studsubj.tobedeleted",
        "GROUP BY st.school_id"
    ]
    total_sql = ' '.join(total_sublist)

    total_students_sublist = ["SELECT st.school_id, count(*) AS total_students",
        "FROM students_student AS st",
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
        "ORDER BY LOWER(schbase.code)"
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




