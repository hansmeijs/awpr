# PR2018-09-02
from datetime import datetime, timedelta
from random import randint
from typing import Union, Dict, Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import update_session_auth_hash
from django.contrib.sites.shortcuts import get_current_site

from django.core.mail import send_mail

from django.db.models import Q
from django.db.models.functions import Lower
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import activate, pgettext_lazy, ugettext_lazy as _
from django.views.generic import View

from accounts import models as acc_mod
from accounts import views as acc_view
from accounts.tokens import account_activation_token
from awpr import menus as awpr_menu
from awpr import constants as c
from awpr import settings as s
from awpr import validators as av
from awpr import functions as af
from awpr import downloads as dl

from grades import views as grd_vw
from grades import excel as grd_exc

from schools import models as sch_mod
from students import models as stud_mod
from students import functions as stud_func
from subjects import models as subj_mod
from students import validators as stud_val

import json

import logging
logger = logging.getLogger(__name__)

# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise
from django.utils.encoding import force_text, force_bytes
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

# - save this page in Usersetting, so at next login this page will open.  Used in LoggedIn
         # PR2021-06-22 moved to get_headerbar_param

        return render(request, 'studentsubjects.html', params)


# ========  OrederlistsListView  =======
@method_decorator([login_required], name='dispatch')
class OrederlistsListView(View): # PR2021-07-04

    def get(self, request):
        #logger.debug(" =====  OrederlistsListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_orderlist'
        param = {'display_school': False, 'display_department': False}
        params = awpr_menu.get_headerbar_param(request, page, param)

        return render(request, 'orderlists.html', params)
# - end of OrederlistsListView



#/////////////////////////////////////////////////////////////////

def create_student_rows(setting_dict, append_dict, student_pk):
    # --- create rows of all students of this examyear / school PR2020-10-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_student_rows -----')

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

        "st.lastname, st.firstname, st.prefix, st.gender,",
        "st.idnumber, st.birthdate, st.birthcountry, st.birthcity,",

        "st.classname, st.examnumber, st.regnumber, st.diplomanumber, st.gradelistnumber,",
        "st.has_dyslexie, st.iseveningstudent, st.islexstudent, st.islinked, st.bis_exam,",

        "st.has_reex, st.has_reex3, st.has_sere, st.withdrawn,",
        "st.grade_ce_avg, st.grade_ce_avg_text, st.grade_combi_avg_text, st.endgrade_avg, st.endgrade_avg_text,",

        "st.result, st.resultid_tv01, st.resultid_tv02, st.resultid_tv03, st.resultid_final,",
        "st.result_info, st.result_status, st.locked,",

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
            # PR2021-07-26 was: full_name = lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = get_full_name(last_name, first_name, prefix)
            row['name_first_init'] = get_lastname_firstname_initials(last_name, first_name, prefix)

    # - add messages to student_row
    if student_pk and student_rows:
        # when student_pk has value there is only 1 row
        row = student_rows[0]
        if row:
            for key, value in append_dict.items():
                row[key] = value

    return student_rows
# --- end of create_student_rows


def get_permit_crud_page_student(request):
    # --- get crud permit for page student # PR2021-07-18
    has_permit = False
    if request.user and request.user.country and request.user.schoolbase:
        permit_list = request.user.permit_list('page_student')
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
        has_permit = get_permit_crud_page_student(request)
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

        # - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)

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

#################################################################################
@method_decorator([login_required], name='dispatch')
class StudentsubjectValidateView(View):

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
                    department=sel_department,
                    locked=False
                )
                if student:
                    msg_html = stud_val.validate_studentsubjects(student)
                    if msg_html:
                        update_wrap['studsubj_validate_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

# - end of StudentsubjectValidateView


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
                        message = render_to_string('submit_ex1_email.html', {
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
                        verification_is_ok, verif_msg_html = self.check_verificationcode(upload_dict, request)
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
                        # TODO exclude published rows?? Yes, but count them when checkign. You cannot approve or undo approve or submit when submitted

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

                        row_count = stud_mod.Studentsubject.objects.filter(crit).count()

                        if logging_on:
                            logger.debug('sel_lvlbase_pk:   ' + str(sel_lvlbase_pk))
                            logger.debug('sel_sctbase_pk:  ' + str(sel_sctbase_pk))
                            logger.debug('sel_subject_pk: ' + str(sel_subject_pk))
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
                                    is_test=is_test,
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
                                    # to increase sppeed, dont create return rows but refreash page after finishing this request
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
                msg_list.append('<li>' + str(_("%(subj)s not completely approved") %
                                             {'subj': get_subjects_are_text(auth_missing)}) + ';</li>')
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

        msg_list.append('</div>')

        msg_html = ''.join(msg_list)

        return msg_html
    # - end of create_submit_msg_list

    def create_Ex1_form(self, published_instance, sel_examyear, sel_school, sel_department, save_to_disk, user_lang):
        #PR2021-07-27 PR2021-08-14
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= create_Ex1_form ============= ')

# get text from examyearsetting
        settings = af.get_exform_text(sel_examyear, ['exform', 'ex1'])
        #if logging_on:
        #    logger.debug('settings: ' + str(settings))

# +++ get mapped_subject_rows
        subject_row_count, subject_pk_list, subject_code_list = \
            grd_exc.create_ex1_mapped_subject_rows(sel_examyear, sel_school, sel_department)
        #  subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
        #  subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]

        if logging_on:
            logger.debug('subject_row_count: ' + str(subject_row_count))
            logger.debug('subject_pk_list: ' + str(subject_pk_list))
            logger.debug('subject_code_list: ' + str(subject_code_list))

# +++ create Ex1 xlsx file
        grd_exc.create_ex1_xlsx(
            published_instance=published_instance,
            examyear=sel_examyear,
            school=sel_school,
            department=sel_department,
            settings=settings,
            save_to_disk=save_to_disk,
            subject_pk_list=subject_pk_list,
            subject_code_list=subject_code_list,
            user_lang=user_lang)
    # - end of create_Ex1_form

    def check_verificationcode(self, upload_dict, request ):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('  ----- check_verificationcode -----')

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
    # - end of check_verificationcode

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


def create_published_Ex1_instance(sel_school, sel_department, sel_examperiod, is_test, now_arr, request):  # PR2021-07-27
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_published_Ex1_instance -----')
    # create new published_instance and save it when it is not a test
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

    published_instance = sch_mod.Published(
        school=sel_school,
        department=sel_department,
        examtype=None,
        examperiod=sel_examperiod,
        name=file_name,
        datepublished=today_date)
    # Note: filefield 'file' gets value on creating Ex form
    if not is_test:
        published_instance.filename = file_name + '.xlsx'
        published_instance.save(request=request)

        if logging_on:
            logger.debug('published_instance.saved: ' + str(published_instance))
            logger.debug('published_instance.pk: ' + str(published_instance.pk))

    return published_instance
# - end of create_published_Ex1_instance



#################################################################################

@method_decorator([login_required], name='dispatch')
class StudentsubjectUploadView(View):  # PR2020-11-20

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

        # TODO === FIXIT === remove has_permit = True
        has_permit = True

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
                    logger.debug('may_edit: ' + str(may_edit))
                    logger.debug('msg_list: ' + str(msg_list))

# - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                student = None
                # TODO : may_edit = examyear_published and school_activated and requsr_same_school and sel_department and not is_locked

                # TODO === FIXIT === remove may_edit = True
                msg_list = []
                may_edit = True

                if len(msg_list):
                    msg_html = '<br>'.join(msg_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                elif may_edit:
                    student_pk = upload_dict.get('student_pk')
                    student = stud_mod.Student.objects.get_or_none(
                        id=student_pk,
                        school=sel_school,
                        department=sel_department,
                        locked=False
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
                                        studsubj_rows.append({'studsubj_id': studsubj_pk,
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
                                setting_dict={},
                                append_dict=append_dict,
                                studsubj_pk=studsubj.pk
                            )
                            if rows:
                                studsubj_row = rows[0]
                                if studsubj_row:
                                    studsubj_rows.append(studsubj_row)
# - end of loop
# -------------------------------------------------
                    if studsubj_rows:
                        update_wrap['updated_studsubj_rows'] = studsubj_rows

# +++ validate subjects of student
                        msg_html = stud_val.validate_studentsubjects(student)
                        if msg_html:
                            update_wrap['studsubj_validate_html'] = msg_html
        if len(messages):
            update_wrap['messages'] = messages
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of StudentsubjectUploadView


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
            saved_value = getattr(instance, field)
            if logging_on:
                logger.debug('saved_value: ' + str(saved_value))
            if new_value != saved_value:
                # TODO
                msg_err = None
                if not msg_err:
                    # c. save field if changed and no_error
                    setattr(instance, field, new_value)
                    save_changes = True
                else:
                    msg_dict['err_' + field] = msg_err

        elif field in ['is_extra_nocount','is_extra_counts', 'is_elective_combi']:
            saved_value = getattr(instance, field)
            logger.debug('saved_value: ' + str(saved_value))
            if new_value != saved_value:
                setattr(instance, field, new_value)
                save_changes = True

        elif field in ['has_exemption', 'has_reex', 'has_reex03']:
            saved_value = getattr(instance, field)
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
       # - when new has_exemption etc. is False: deleted row by setting deleted=True and reset all fields
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
            logger.debug('field: ' + str(field) )
            logger.debug('new_value: ' + str(new_value))

            prefix, authby = field.split('_')
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
            logger.debug('The changes have been saved: ' + str(instance))
        except:
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
    # --- delete subject # PR2021-07-18

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_subject ----- ')
        logger.debug('student: ' + str(student))

    deleted_ok = False

# - create student_row - to be returned after successfull delete
    student_row = {'id': student.pk,
                   'mapid': 'student_' + str(student.pk),
                   'deleted': True}
    base_pk = student.base.pk

    student_name = getattr(student, 'fullname', '---')
    this_txt = _("Candidate '%(tbl)s' ") % {'tbl': student_name}
    header_txt = _("Delete candidate")

# - TODO check if student has submitted subjects
    student_has_submitted_subjects = False
    if student_has_submitted_subjects:
        err_txt1 = str(_('%(cpt)s has submitted subjects.') % {'cpt': this_txt})
        err_txt2 = str(_("%(cpt)s could not be deleted.") % {'cpt': _('This candidate')})
        error_list.append(' '.join((err_txt1, err_txt2)))

        msg_html = '<br>'.join((err_txt1, err_txt2))
        msg_list.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': msg_html})

    else:
        deleted_ok = sch_mod.delete_instance(student, msg_list, error_list, request, this_txt, header_txt)

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
        logger.debug('error_list' + str(error_list))

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
        logger.debug(' ----- create_student ----- ')

# - create but don't save studentbase
    # save studentbase beyond, to prevent studentbases without student
    studentbase = stud_mod.Studentbase(
        country=school.examyear.country
    )

    student = None
    if studentbase and school:

# - get value of 'idnumber', 'lastname', 'firstname', 'prefix'
        id_number = upload_dict.get('idnumber')
        last_name = upload_dict.get('lastname')
        first_name = upload_dict.get('firstname')
        prefix = upload_dict.get('prefix')

        id_number_stripped = id_number.strip() if id_number else ''
        lastname_stripped = last_name.strip() if last_name else ''
        firstname_stripped = first_name.strip() if first_name else ''
        prefix_stripped = prefix.strip() if prefix else ''
        full_name = stud_val.get_prefix_lastname_comma_firstname(lastname_stripped, firstname_stripped, prefix_stripped)

        if logging_on:
            logger.debug('id_number_stripped: ' + str(id_number_stripped))
            logger.debug('lastname_stripped: ' + str(lastname_stripped))
            logger.debug('firstname_stripped: ' + str(firstname_stripped))
            logger.debug('full_name: ' + str(full_name))

        msg_list = []
        msg_err = av.validate_notblank_maxlength(lastname_stripped, c.MAX_LENGTH_FIRSTLASTNAME, _('The last name'))
        if msg_err:
            msg_list.append(msg_err)
        msg_err = av.validate_notblank_maxlength(firstname_stripped, c.MAX_LENGTH_FIRSTLASTNAME, _('The first name'))
        if msg_err:
            msg_list.append(msg_err)
        msg_err = av.validate_notblank_maxlength(id_number_stripped, c.MAX_LENGTH_IDNUMBER, _('The ID-number'))
        if msg_err:
            msg_list.append(msg_err)

# - validate if student already exists
        # either student, is_new_student or has_error is trueish
        is_test, is_import, found_is_error, notfound_is_error = False, False, True, False
        student, is_new_student, has_error = stud_val.lookup_student_by_idnumber(
            school, department, id_number_stripped, full_name, is_test, is_import, msg_list, found_is_error, notfound_is_error)

        if len(msg_list) > 0:
            #  messages is list of dicts with format: {'field': fldName, header': header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html}
            msg_html = '<br>'.join(msg_list)
            messages.append({'header': _('Add candidate'), 'class': "border_bg_invalid", 'msg_html': msg_html})
            error_list.extend(msg_list)
        else:

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
                    department=department
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
        logger.debug('student: ' + str(student))
        logger.debug('messages: ' + str(messages))
        logger.debug('error_list: ' + str(error_list))

    return student

# - end of create_student

#######################################################
def update_student_instance(instance, upload_dict, idnumber_list, examnumber_list, msg_list, error_list, request, skip_save):
    # --- update existing and new instance PR2019-06-06 PR2021-07-19

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_student_instance -------')
        logger.debug('upload_dict' + str(upload_dict))

    if instance:
        student_name = ' '.join([instance.firstname, instance.lastname])

        save_changes = False
        update_scheme = False
        recalc_regnumber = False

        for field, new_value in upload_dict.items():
            #try:
            if True:

    # - save changes in fields 'lastname', 'firstname'
                if field in ['lastname', 'firstname']:
                    saved_value = getattr(instance, field)

                    if isinstance(new_value, int):
                        new_value = str(new_value)

                    if new_value != saved_value:
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
                        has_error = validate_namelast_namefirst(
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

                    if logging_on:
                        logger.debug('new_gender:     ' + str(new_gender))
                        logger.debug('has_error:     ' + str(has_error))

                    if has_error:
                        err_txt = _("%(cpt)s '%(val)s' is not allowed.") \
                                  % {'cpt': str(_('Gender')), 'val': new_value}
                        error_list.append(err_txt)
                        msg_list.append({'class': "border_bg_warning", 'msg_html': err_txt})
                    else:
                        saved_value = getattr(instance, field)
                        if new_gender != saved_value:
                            setattr(instance, field, new_gender)
                            save_changes = True
                            recalc_regnumber = True
                            if logging_on:
                                logger.debug('setattr(instance, field, new_gender: ' + str(new_gender))

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
                                        break

                            if idnumber_list and new_value in idnumber_list:
                                has_error = True
                            else:
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
                        err_txt = _("%(cpt)s '%(val)s' already exists.") \
                                  % {'cpt': str(caption), 'val': new_value}
                        error_list.append(err_txt)
                        msg_list.append({'class': "border_bg_warning", 'msg_html': err_txt})
                    else:
                        saved_value = getattr(instance, field)
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
                            if field == 'examnumber':
                                recalc_regnumber = True
                            if logging_on:
                                logger.debug('setattr(instance, field, new_value: ' + str(new_value))

    # 2. save changes in birthdate field
                elif field == 'birthdate':
                    # new_value has format of Excel field
                    saved_value = getattr(instance, field)
                    if logging_on:
                        logger.debug('field:     ' + str(field))
                        logger.debug('new_value: ' + str(new_value) + ' ' + str(type(new_value)))
                        logger.debug('saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))

                    if isinstance(new_value, int):
                        new_value = str(new_value)

                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True
                        if logging_on:
                            logger.debug('setattr(instance, field, new_value: ' + str(new_value))

    # 2. save changes in text fields
                elif field in ('prefix', 'birthdate', 'birthcountry', 'birthcity', 'classname', 'diplomanumber', 'gradelistnumber'):
                    saved_value = getattr(instance, field)
                    if logging_on:
                        logger.debug('field:     ' + str(field))
                        logger.debug('new_value: ' + str(new_value) + ' ' + str(type(new_value)))
                        logger.debug('saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))

                    if isinstance(new_value, int):
                        new_value = str(new_value)

                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True
                        if logging_on:
                            logger.debug('setattr(instance, field, new_value: ' + str(new_value))

    # 3. save changes in department, level or sector
                # department cannot be changed
                # change 'profiel' into 'sector
                elif field in ('level', 'sector', 'profiel'):
                    if field == 'profiel':
                        field = 'sector'

                    saved_value = getattr(instance, field)
                    if logging_on:
                        logger.debug('field: ' + str(field))
                        logger.debug('new_value: ' + str(new_value) + ' ' + str(type(new_value)))
                        logger.debug('saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
                    # new_value is levelbase_pk or sectorbase_pk
                    if new_value != saved_value:
                        # TODO delete student_subjects that are not in the new scheme
                        examyear = None
                        school = getattr(instance, 'school')
                        if school:
                            examyear = getattr(school, 'examyear')

                        if field == 'level':
                            level_or_sector = subj_mod.Level.objects.get_or_none(
                                base_id=new_value,
                                examyear=examyear
                            )
                            recalc_regnumber = True
                        else:
                            level_or_sector = subj_mod.Sector.objects.get_or_none(
                                base_id=new_value,
                                examyear=examyear
                            )
                        setattr(instance, field, level_or_sector)
                        save_changes = True
                        update_scheme = True

    # - save changes in field 'bis_exam'
                elif field in ('bis_exam','has_dyslexie', 'iseveningstudent', 'islexstudent'):
                    saved_value = getattr(instance, field)
                    if new_value is None:
                        new_value = False
                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True

                    if logging_on:
                        logger.debug('---- field:   ' + str(field))
                        logger.debug('new_value:    ' + str(new_value))
                        logger.debug('saved_value:  ' + str(saved_value))
                        logger.debug('save_changes: ' + str(save_changes))
            """
            except Exception as e:
                err_txt1 = str(_('An error occurred'))
                err_txt2 = str(e)
                err_txt3 = str(_("The changes of '%(val)s' have not been saved.") % {'val': field})
                error_list.append(''.join((err_txt1, ' (', err_txt2, ') ', err_txt3)))

                msg_html = ''.join((err_txt1, ': ', '<br><i>', err_txt2, '</i><br>', err_txt3))
                msg_dict = {'header': str(_('Save changes')), 'class': 'border_bg_invalid', 'msg_html': msg_html}
                msg_list.append(msg_dict)

                logger.error(getattr(e, 'message', str(e)))
            """
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
                examnumber = stud_func.get_next_examnumber(school, department)
                setattr(instance, 'examnumber', examnumber)
                save_changes = True
                if logging_on:
                    logger.debug('setattr(instance, examnumber, examnumber: ' + str(examnumber))
    # - calc_regnumber
            new_regnumber = stud_func.calc_regnumber(school_code, gender, examyear_code, examnumber, depbase, levelbase)

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
        if save_changes and not skip_save:
            try:
                instance.save(request=request)
            except Exception as e:
                err_txt1 = str(_('An error occurred'))
                err_txt2 = str(e)
                err_txt3 = str(_("The changes of '%(val)s' have not been saved.") % {'val': student_name})
                error_list.append(''.join((err_txt1, ' (', err_txt2, ') ', err_txt3)))

                msg_html = ''.join((err_txt1, ': ', '<br><i>', err_txt2, '</i><br>',err_txt3))
                msg_dict = {'header': str(_('Save changes')), 'class': 'border_bg_invalid', 'msg_html': msg_html}
                msg_list.append(msg_dict)

                logger.error(getattr(e, 'message', str(e)))
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
                # TODO check if studsubj is submitted, set delete = True if submitted
                studsubj.delete(request=request)
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
                        # TODO check if studsubj is submitted, set delete = True if submitted
                        studsubj.delete(request=request)
                    elif count_subject_in_newscheme == 1:
        # if subject occurs only once in new_scheme: replace schemeitem by new schemeitem
                        new_schemeitem = subj_mod.Schemeitem.objects.get_or_none(
                            scheme=new_scheme,
                            subject=old_subject
                        )
                        if new_schemeitem:
                            studsubj.schemeitem = new_schemeitem
                            studsubj.save(request=request)
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


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_studsubj(student, schemeitem, messages, error_list, request, skip_save):
    # --- create student subject # PR2020-11-21 PR2021-07-21
    logging_on = s.LOGGING_ON
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

def create_studentsubject_rows(examyear, schoolbase, depbase, setting_dict, append_dict, student_pk=None, studsubj_pk=None):
    # --- create rows of all students of this examyear / school PR2020-10-27
    #logger.debug(' =============== create_student_rows ============= ')
    #logger.debug('append_dict: ' + str(append_dict))
    #logger.debug('setting_dict: ' + str(setting_dict))

    # create list of students of this school / examyear, possibly with filter student_pk or studsubj_pk
    # with left join of studentsubjects with deleted=False
    sel_examyear_pk = examyear.pk if examyear else None
    sel_schoolbase_pk = schoolbase.pk if schoolbase else None
    sel_depbase_pk = depbase.pk if depbase else None

    sel_lvlbase_pk = None
    if c.KEY_SEL_LVLBASE_PK in setting_dict:
        sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)

    sel_sctbase_pk = None
    if c.KEY_SEL_SCTBASE_PK in setting_dict:
        sel_sctbase_pk = setting_dict.get(c.KEY_SEL_SCTBASE_PK)

    sql_studsubj_list = ["SELECT studsubj.id AS studsubj_id, studsubj.student_id,",
        "studsubj.cluster_id, si.id AS schemeitem_id, si.scheme_id AS scheme_id,",
        "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_elective_combi,",
        "studsubj.pws_title, studsubj.pws_subjects,",
        "studsubj.has_exemption, studsubj.has_reex, studsubj.has_reex03, studsubj.has_pok,",
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
    sql_studsubjects = ' '.join(sql_studsubj_list)

    sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk, 'db_id': sel_depbase_pk}

    sql_list = ["WITH studsubj AS (" + sql_studsubjects + ")",
        "SELECT st.id AS stud_id, studsubj.studsubj_id, studsubj.schemeitem_id, studsubj.cluster_id,",
        "CONCAT('studsubj_', st.id::TEXT, '_', studsubj.studsubj_id::TEXT) AS mapid, 'studsubj' AS table,",
        "st.lastname, st.firstname, st.prefix, st.examnumber,",
        "st.scheme_id, st.iseveningstudent, st.locked, st.has_reex, st.bis_exam, st.withdrawn,",
        "studsubj.subject_id AS subj_id, studsubj.subj_code, studsubj.subj_name,",
        "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",

        "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_elective_combi,",
        "studsubj.pws_title, studsubj.pws_subjects,",
        "studsubj.has_exemption, studsubj.has_reex, studsubj.has_reex03, studsubj.has_pok,",

        "studsubj.is_mandatory, studsubj.is_mand_subj_id, studsubj.is_combi, studsubj.extra_count_allowed, studsubj.extra_nocount_allowed, studsubj.elective_combi_allowed,",
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
        "LEFT JOIN studsubj ON (studsubj.student_id = st.id)",
        "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
        "LEFT JOIN subjects_scheme AS scheme ON (scheme.id = st.scheme_id)",
        "LEFT JOIN subjects_package AS package ON (package.id = st.package_id)",
        "WHERE school.base_id = %(sb_id)s::INT AND school.examyear_id = %(ey_id)s::INT AND dep.base_id = %(db_id)s::INT"]

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

    #logger.debug('sql_keys: ' + str(sql_keys) + ' ' + str(type(sql_keys)))
    #logger.debug('sql: ' + str(sql) + ' ' + str(type(sql)))
    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    #logger.debug('rows: ' + str(rows) + ' ' + str(type(rows)))

    #logger.debug('connection.queries: ' + str(connection.queries))

# - full name to rows
    if rows:
        for row in rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

# - add messages to all studsubj_rows, only when student_pk or studsubj_pk have value
        if student_pk or studsubj_pk:
            if rows:
                for row in rows:
                    for key, value in append_dict.items():
                        row[key] = value

    return rows
# --- end of create_studentsubject_rows


def create_studentsubjectnote_rows(upload_dict, request):  # PR2021-03-16
    # --- create rows of notes of this studentsubject
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
    logger.debug(' =============== create_studentsubjectnote_rows ============= ')
    logger.debug('upload_dict: ' + str(upload_dict))
    # create list of studentsubjectnote of this studentsubject, filter intern_schoolbase
    # to show intern note only to user of the same school/insp: filter intern_schoolbase = requsr.schoolbase or null
    note_rows = []
    if upload_dict:
        studsubj_pk =  upload_dict.get('studsubj_pk')
        if studsubj_pk:
            requsr_intern_schoolbase_pk = request.user.schoolbase_id
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


# /////////////////////////////////////////////////////////////////
def create_orderlist_rowsNEW(sel_examyear): # PR2021-08-09
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_orderlist_rowsNEW ============= ')

    #  create nested dict of all schools of CUR and SXM with submitted subjects # PR2021-08-09

    sql_keys = {'ey_code_int': sel_examyear.code}

    sql_list = ["SELECT si.ete_exam,",
                "CASE WHEN subj.otherlang IS NULL OR sch.otherlang IS NULL THEN 'ne' ELSE",
                "CASE WHEN POSITION(sch.otherlang IN subj.otherlang) > 0 THEN sch.otherlang ELSE 'ne' END END AS lang,",
                "dep.base_id AS depbase_id,",
                "lvl.base_id AS lvlbase_id,",
                "sch.base_id AS schoolbase_id,",
                "subj.base_id AS subjbase_id",

               "FROM students_studentsubject AS studsubj",

               "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
               "INNER JOIN subjects_scheme AS sm ON (sm.id = si.scheme_id)",
               "INNER JOIN schools_department AS dep ON (dep.id = sm.department_id)",
               "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

               "LEFT JOIN subjects_level AS lvl ON (lvl.id = sm.level_id)",

               "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
               "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

               "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
               "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
               "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",

               "WHERE ey.code = %(ey_code_int)s::INT",
               "AND NOT studsubj.tobedeleted",
                # TODO FIXIT set filter published
               # "AND studsubj.subj_published_id IS NOT NULL"

               ]
    sql = ' '.join(sql_list)

    # logger.debug('sql: ' + str(sql))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

        examyear_dict = {'total': {}}
        for row in rows:
            exam = 'ete' if row.get('ete_exam', False) else 'duo'
            if exam not in examyear_dict:
                examyear_dict[exam] = {'total': {}}
            exam_dict = examyear_dict[exam]

            lang = row.get('lang', 'ne')
            if lang not in exam_dict:
                exam_dict[lang] = {'total': {}}
            lang_dict = exam_dict[lang]

            depbase_pk = row.get('depbase_id')
            if depbase_pk not in lang_dict:
                lang_dict[depbase_pk] = {'total': {}}
            depbase_dict = lang_dict[depbase_pk]

            # value is '0' when lvlbase_id = None (Havo/Vwo)
            lvlbase_pk = row.get('lvlbase_id', 0)
            if lvlbase_pk not in depbase_dict:
                depbase_dict[lvlbase_pk] = {'total': {}}
            lvlbase_dict = depbase_dict[lvlbase_pk]

            schoolbase_pk = row.get('schoolbase_id')
            if schoolbase_pk not in lvlbase_dict:
                lvlbase_dict[schoolbase_pk] = {}
            schoolbase_dict = lvlbase_dict[schoolbase_pk]

            subjbase_pk = row.get('subjbase_id')
            if subjbase_pk not in schoolbase_dict:
                schoolbase_dict[subjbase_pk] = 1
            else:
                schoolbase_dict[subjbase_pk] += 1

            lvlbase_total = lvlbase_dict.get('total')
            if subjbase_pk not in lvlbase_total:
                lvlbase_total[subjbase_pk] = 1
            else:
                lvlbase_total[subjbase_pk] += 1

            depbase_total = depbase_dict.get('total')
            if subjbase_pk not in depbase_total:
                depbase_total[subjbase_pk] = 1
            else:
                depbase_total[subjbase_pk] += 1

            lang_total = lang_dict.get('total')
            if subjbase_pk not in lang_total:
                lang_total[subjbase_pk] = 1
            else:
                lang_total[subjbase_pk] += 1

            exam_total = exam_dict.get('total')
            if subjbase_pk not in exam_total:
                exam_total[subjbase_pk] = 1
            else:
                exam_total[subjbase_pk] += 1

            examyear_total = examyear_dict.get('total')
            if subjbase_pk not in examyear_total:
                examyear_total[subjbase_pk] = 1
            else:
                examyear_total[subjbase_pk] += 1
        """
        examyear_dict = {
            'total': {133: 175, 134: 175, 135: 175, 136: 175, 137: 175, 138: 175, 141: 141, 142: 101, 146: 31, 156: 102, 149: 37, 140: 74, 153: 74, 175: 74, 154: 33, 155: 73, 143: 7},
            'duo': { 'total': {133: 175, 134: 175, 135: 175, 136: 175, 137: 175, 138: 175, 141: 114, 142: 101, 146: 31, 156: 102, 149: 37, 140: 74, 153: 74, 175: 74, 154: 33, 155: 73, 143: 7},
                'ne': {'total': {133: 175, 134: 175, 135: 175, 136: 175, 137: 175, 141: 114, 142: 101, 146: 31, 156: 102, 149: 37, 140: 74, 153: 74, 175: 74, 154: 33, 155: 73, 143: 7},
                    1: {'total': {133: 175, 134: 175, 135: 175, 136: 175, 137: 175, 141: 114, 142: 101, 146: 31, 156: 102, 149: 37, 140: 74, 153: 74, 175: 74, 154: 33, 155: 73, 143: 7},
                        14: {'total': {133: 41, 134: 41, 135: 41, 136: 41, 137: 41, 141: 41, 142: 41, 146: 18, 156: 41, 149: 23},
                            11: {133: 41, 134: 41, 135: 41, 136: 41, 137: 41, 141: 41, 142: 41, 146: 18, 156: 41, 149: 23}},
                        13: {'total': {133: 61, 134: 61, 135: 61, 136: 61, 137: 61, 140: 34, 153: 34, 156: 61, 175: 34, 142: 27, 146: 13, 149: 14},
                            11: {133: 61, 134: 61, 135: 61, 136: 61, 137: 61, 140: 34, 153: 34, 156: 61, 175: 34, 142: 27, 146: 13, 149: 14}},
                        12: {'total': {133: 73, 134: 73, 135: 73, 136: 73, 137: 73, 141: 73, 142: 33, 154: 33, 155: 73, 140: 40, 153: 40, 175: 40, 143: 7},
                            11: {133: 73, 134: 73, 135: 73, 136: 73, 137: 73, 141: 73, 142: 33, 154: 33, 155: 73, 140: 40, 153: 40, 175: 40, 143: 7}}}},
                'pa': {'total': {138: 175},
                        1: {'total': {138: 175},
                            14: {'total': {138: 41},
                                  11: {138: 41}
                                 },
                            13: {'total': {138: 61},
                                11: {138: 61}
                                 },
                            12: {'total': {138: 73},
                                11: {138: 73}
                                 }
                            }
                       }
            },
            'ete': {'total': {141: 27},
                    'ne': {'total': {141: 27}, 
                    1: {'total': {141: 27}, 
                        13: {'total': {141: 27}, 
                            11: {141: 27}}}}
                    }
             }
        """

        if logging_on:
            logger.debug('examyear_dict: ' + str(examyear_dict))

    return rows


# --- end of create_orderlist_rows


#/////////////////////////////////////////////////////////////////
def create_orderlist_rows(sel_examyear_pk):
    # --- create rows of all schools with submeitted subjects PR2021-07-04
    #logger.debug(' =============== create_orderlist_rows ============= ')
    #logger.debug('append_dict: ' + str(append_dict))
    #logger.debug('setting_dict: ' + str(setting_dict))
    # create list of students of this school / examyear, possibly with filter student_pk or studsubj_pk
    # with left join of studentsubjects with deleted=False

    #logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk))
    #logger.debug('sel_schoolbase_pk: ' + str(sel_schoolbase_pk))
    #logger.debug('sel_depbase_pk: ' + str(sel_depbase_pk))


#CASE WHEN  POSITION(';" + sch.otherlang + ";' IN CONCAT(';', subj.otherlang, ';')) > 0 THEN ELSE END

    """
    "CASE WHEN subj.otherlang IS NULL OR sch.otherlang THEN 'ne' ELSE", 
    "CASE WHEN  POSITION('" + sch.otherlang + "' IN subj.otherlang) > 0 THEN sch.otherlang ELSE 'ne' END",
    "END AS lang,",
    
    """
    sql_keys = {'ey_id': sel_examyear_pk}

    sql_sublist = ["SELECT sch.id AS school_id,",
                "dep.id AS dep_id, dep.base_id AS depbase_id, depbase.code AS depbase_code, lvl.id AS lvl_id, lvl.abbrev AS lvl_abbrev,",
                "studsubj.subj_published_id,",
                "subj.id AS subj_id, subjbase.code AS subjbase_code, subj.name AS subj_name,",
                "si.ete_exam AS si_ete_exam,",
                "CASE WHEN subj.otherlang IS NULL OR sch.otherlang IS NULL THEN 'ne' ELSE",
                "CASE WHEN POSITION(sch.otherlang IN subj.otherlang) > 0 THEN sch.otherlang ELSE 'ne' END END AS lang",

                "FROM students_studentsubject AS studsubj",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_scheme AS sm ON (sm.id = si.scheme_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = sm.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = sm.level_id)",

                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
                "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                "INNER JOIN schools_schoolbase AS schbase ON (schbase.id = sch.base_id)",

                "WHERE NOT studsubj.tobedeleted",
                # "AND studsubj.subj_published_id IS NOT NULL"

                ]
    sub_sql = ' '.join(sql_sublist)

    sql_keys = {'ey_id': sel_examyear_pk}

    sql_list = ["WITH sub AS (" , sub_sql, ")",
        "SELECT sch.id AS school_id, schbase.code AS schbase_code, sch.name AS school_name,",
        "sub.dep_id, sub.depbase_code, sub.lvl_id, sub.lvl_abbrev,",
        "sub.subj_id, sub.subjbase_code, sub.subj_name, sub.si_ete_exam,",
        "ARRAY_AGG(DISTINCT sub.subj_published_id) AS subj_published_arr,",
        "sub.lang,",
        "count(*) AS count",

        "FROM sub",
        "INNER JOIN schools_school AS sch ON (sch.id = sub.school_id)",
        "INNER JOIN schools_schoolbase AS schbase ON (schbase.id = sch.base_id)",

        "GROUP BY sch.id, schbase.code, sch.name, sub.dep_id, sub.depbase_id, sub.depbase_code,",
                "sub.lvl_id, sub.lvl_abbrev, sub.lang, ",
                "sub.subj_id, sub.subjbase_code, sub.subj_name, sub.si_ete_exam",
        "ORDER BY LOWER(schbase.code), sub.depbase_id"
        ]
    sql = ' '.join(sql_list)

    #logger.debug('sql: ' + str(sql))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    return rows
# --- end of create_orderlist_rows


# oooooooooooooo Functions  Student name ooooooooooooooooooooooooooooooooooooooooooooooooooo

def get_full_name(last_name, first_name, prefix):  # PR2021-07-26
    last_name = last_name.strip() + ','   if last_name else ''
    first_name = first_name.strip() if first_name else ''
    prefix = prefix.strip() if prefix else ''
    return ' '.join((prefix, last_name, first_name))

def get_firstname_initials(first_name):  # PR2021-07-26
    firstname_initials = ''
    first_name = first_name.strip() if first_name else ''
    if first_name:
        # strings '', ' ' and '   ' give empty list [] which is False
        firstnames_arr = first_name.split()
        if firstnames_arr:
            skip = False
            for item in firstnames_arr:
                if not skip:
                    firstname_initials += item + ' '  # write first firstname in full
                    skip = True
                else:
                    if item:
                        #PR2017-02-18 VB debug. bij dubbele spatie in voornaam krijg je lege err(x)
                        firstname_initials += item[:1] # write of the next firstnames only the first letter
    return firstname_initials


def get_lastname_firstname_initials(last_name, first_name, prefix): # PR2021-07-26
    firstname_initials = get_firstname_initials(first_name)
    return get_full_name(last_name, firstname_initials, prefix)


# TODO deprecate
def lastname_firstname_initials(last_name, first_name, prefix):
    full_name = last_name.strip()
    firstnames = ''
    if first_name:
        firstnames_arr = first_name.split()
        if len(firstnames_arr) == 0:
            firstnames = first_name.strip()  # 'PR 13 apr 13 Trim toegevoegd
        else:
            skip = False
            for item in firstnames_arr:
                if not skip:
                    firstnames = firstnames + item + ' '  # write first firstname in full
                    skip = True
                else:
                    if item:
                        #PR2017-02-18 VB debug. bij dubbele spatie in voornaam krijg je lege err(x)
                        firstnames = firstnames + item[:1] # write of the next firstnames only the first letter
    if firstnames:
        full_name = full_name + ', ' + firstnames
    if prefix: # put prefix at the front
        full_name = prefix.strip() + ' ' + full_name
    full_name = full_name.strip()
    return full_name

    
def SplitPrefix(name, is_firstname):
    # PR2020-11-15 from AWP PR2016-04-01 aparte functie van gemaakt
    # Functie splits tussenvoegsel voor Achternaam (IsPrefix=True) of achter Voornamen (IsPrefix=False)

    found = False

    remainder = ''
    prefix = ''

    prefixes = ("voor den", "van den", "van der", "van de", "van 't", "de la",
                "del", "den", "der", "dos", "ten", "ter", "van",
                "al", "d'", "da", "de", "do", "el", "l'", "la", "le", "te")


    # search in reverse order of prefix length: check "van den" first,
    # when you check 'van' first, 'van den' will not be reached
    # when booIsPrefix: put space after prefix, but also check "d'" and "l'" without space after prefix
    # when not booIsPrefix: put space before prefix

    prefixes_without_space = ("d'", " l'")

    name_stripped = name.strip()  # 'PR 13 apr 13 Trim toegevoegd
    if name_stripped:
        name_len = len(name_stripped)
        for value in prefixes:
            search_prefix = ' ' + value if is_firstname else value + ' '
            search_len = len(search_prefix)
            if name_len >= search_len:
                if is_firstname:
                    # check for prefix at end of firstname
                    lookup_str = name_stripped[0:search_len]
                else:
                    # check for prefix in front of lastname
                    lookup_str = name_stripped[-name_len]
                if lookup_str == search_prefix:
                    found = True
                    prefix = lookup_str.strip()
                    if is_firstname:
                        remainder = name_stripped[len].strip()
                    else:
                        remainder_len = name_len - search_len
                        remainder = name_stripped[0:remainder_len].strip()
                    break
    # Voornamen met tussenvoegsel erachter
        #van groot naar klein, anders wordt 'van den' niet bereikt, maar 'den' ingevuld

    return found, prefix, remainder # found returns True when name is split
# End of SplitPrefix


# oooooooooooooo End of Functions Student name ooooooooooooooooooooooooooooooooooooooooooooooooooo

