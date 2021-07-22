# PR2018-09-02
from django.contrib.auth.decorators import login_required

from django.db.models.functions import Lower

from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import View

from awpr import menus as awpr_menu
from awpr import constants as c
from awpr import settings as s
from awpr import validators as av
from awpr import functions as af
from awpr import downloads as dl

from grades import views as grd_vw

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

    if logging_on:
        logger.debug(' ----- create_student_rows -----')
        logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk))
        logger.debug('sel_schoolbase_pk: ' + str(sel_schoolbase_pk))
        logger.debug('sel_depbase_pk: ' + str(sel_depbase_pk))

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
        logger.debug('student_rows: ' + str(student_rows))
# - add lastname_firstname_initials to rows
    if student_rows:
        for row in student_rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

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

                sel_country = request.user.country

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
                        studentbase = create_or_get_studentbase(sel_country,
                            upload_dict, messages, error_list, False)  # skip_save = False
                        student = create_student(studentbase, sel_school, sel_department,
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



#################################################################################
@method_decorator([login_required], name='dispatch')
class StudentsubjectValidateView(View):

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= StudentsubjectValidateView ============= ')

        # function validates studentsubject records of current student PR2021-07-10
        update_wrap = {}
        messages = []

# - get permit - no permit necessary

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)

            messages = []
# ----- get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_editNIU, msg_listNIU = \
                dl.get_selected_ey_school_dep_from_usersetting(request)

            if logging_on:
                logger.debug('upload_dict' + str(upload_dict))
                logger.debug('sel_examyear: ' + str(sel_examyear))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))

# - get current student from upload_dict, filter: sel_school, sel_department, student is not locked

            #if len(msg_list):
            #    msg_html = ''
            #    for msg in msg_list:
            #        msg_html += ''.join(( '<p>', str(msg), '</p>'))
            #    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})

            student_pk = upload_dict.get('student_pk')
            student = stud_mod.Student.objects.get_or_none(
                id=student_pk,
                school=sel_school,
                department=sel_department,
                locked=False
            )
            if logging_on:
                logger.debug('student: ' + str(student))

            if student:

# +++ validate subjects of student
                msg_html = stud_val.validate_studentsubjects(student)
                if msg_html:
                    update_wrap['validate_studsubj_html'] = msg_html

            if len(messages):
                update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))


# - end of StudentsubjectValidateView
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

        # TODO === FIXIT === set permit
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

                # TODO === FIXIT === set permit
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
                    # - if published: set deleted=True, so its remains in the Ex1 form
                                    setattr(studsubj, 'deleted', True)
                                    studsubj.save(request=request)
                                    if logging_on:
                                        logger.debug('studsubj.deleted: ' + str(studsubj.deleted))
                                    grades = stud_mod.Grade.objects.filter(studentsubject=studsubj)
                            # also set grades deleted=True
                                    if grades:
                                        for grade in grades:
                                            setattr(grade, 'deleted', True)
                                            grade.save(request=request)
                                            if logging_on:
                                                logger.debug('grade.deleted: ' + str(grade.deleted))
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
                            setting_dict = {
                                'sel_examyear_pk': sel_school.examyear.pk,
                                'sel_schoolbase_pk': sel_school.base_id,
                                'sel_depbase_pk': sel_department.base_id
                            }
                            rows = create_studentsubject_rows(
                                setting_dict= setting_dict,
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
                            update_wrap['validate_studsubj_html'] = msg_html
        if len(messages):
            update_wrap['messages'] = messages
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of StudentsubjectUploadView


#######################################################
def update_studsubj(instance, upload_dict, msg_dict, request):
    # --- update existing and new instance PR2019-06-06
    # add new values to update_dict (don't reset update_dict, it has values)
    logger.debug(' ------- update_studsubj -------')
    logger.debug('upload_dict' + str(upload_dict))

    # FIELDS_STUDENTSUBJECT = ('student', 'schemeitem', 'cluster', 'is_extra_nocount','is_extra_counts', 'is_elective_combi',
    #                          'pws_title','pws_subjects', 'has_exemption', 'has_reex', 'has_reex03', 'has_pok', 'pok_status',
    #                          'modifiedby', 'modifiedat')

    #
    # FIELDS_STUDENTSUBJECT = ( student, schemeitem, cluster,
    #   is_extra_nocount, is_extra_counts, is_elective_combi, pws_title, pws_subjects,
    #   has_exemption, has_reex, has_reex03, has_pok,
    #   subj_auth1by, subj_auth2by, subjpublished, exem_auth1by, exem_auth2by, exemppublished,
    #   reex_auth1by, reex_auth2by, reexpublished, reex3_auth1by, reex3_auth2by, reex3published,
    #   pok_auth1by, pok_auth2by, pokpublished,
    #   deleted, 'modifiedby', 'modifiedat')


    # upload_dict{'mode': 'update', 'studsubj_id': 10, 'schemeitem_id': 201, 'stud_id': 29,
    #                   'is_extra_nocount': False, 'is_extra_counts': False, 'is_elective_combi': False,
    #                   'pws_title': 'oo', 'pws_subjects': 'pp'}
    save_changes = False
    for field, new_value in upload_dict.items():
# a. get new_value and saved_value

        #logger.debug('field: ' + str(field) + ' new_value: ' + str(new_value))

# 2. save changes in field 'name', 'abbrev'
        if field in ['pws_title', 'pws_subjects']:
            saved_value = getattr(instance, field)
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

# 3. save changes in fields 'namefirst', 'namelast'
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

        elif field in ('subj_auth1by', 'subj_auth2by', 'exem_auth1by', 'exem_auth2by',
                       'reex_auth1by', 'reex_auth2by', 'reex3_auth1by', 'reex3_auth2by',
                       'pok_auth1by', 'pok_auth2by'):
            logger.debug('field: ' + str(field) )
            logger.debug('new_value: ' + str(new_value))

            prefix, suffix  = field.split('_')
            logger.debug('prefix: ' + str(prefix) )
            logger.debug('suffix: ' + str(suffix) )

# - check if instance is published. Authorization of published instances cannot be changed.
            err_published, err_same_user = False, False
            fld_published = prefix + '_published'
            item_published = getattr(instance, fld_published)
            if item_published:
                err_published = True
# - check other authorization, to check if it is the same user. Only when auth is set to True
            elif new_value:
                suffix_other = 'auth2by' if suffix == 'auth1by' else 'auth1by'
                fld_other = prefix + '_' + suffix_other
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
            logger.debug('The changes have been saved' + str(instance))
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

                    if studsubjnote and file:
                        instance = stud_mod.Noteattachment(
                            studentsubjectnote=studsubjnote,
                            contenttype=file_type,
                            filename=file_name,
                            file=file)

                        if logging_on:
                            logger.debug('instance: ' + str(instance))
                        instance.save()
                        if logging_on:
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

                #=========================








                """
# - also set emplhour.hasnote = True, save emplhour and update last_emplhour_updated PR2020-10-26
                    #emplhour.hasnote = True
                    #emplhour.save(request=request, last_emplhour_updated=True)

# 6. create list of updated emplhour_row
                    filter_dict = {'eplh_update_list': [emplhour.pk]}
                    emplhour_rows = d.create_emplhour_rows(filter_dict, request, None, False)
                    if emplhour_rows:
                        update_wrap['emplhour_updates'] = emplhour_rows

# - also get emplhournote (roster page)
                    emplhournote_rows = d.create_emplhournote_rows(
                        period_dict=filter_dict,
                        last_emplhour_check=None,
                        request=request)
                    if emplhournote_rows:
                        update_wrap['emplhournote_updates'] = emplhournote_rows
                """
# 9. return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=LazyEncoder))


@method_decorator([login_required], name='dispatch')
class StudentImportView(View):  # PR2020-10-01

    def get(self, request):
        logger.debug(' ============= StudentImportView ============= ')
        param = {}
        has_permit = False
        if request.user is not None and request.user.country is not None and request.user.schoolbase is not None:
            has_permit = True  # (request.user.is_perm_planner or request.user.is_perm_hrman)
        if has_permit:
            # coldef_list = [{'tsaKey': 'student', 'caption': _('Company name')},
            #                      {'tsaKey': 'ordername', 'caption': _('Order name')},
            #                      {'tsaKey': 'orderdatefirst', 'caption': _('First date order')},
            #                      {'tsaKey': 'orderdatelast', 'caption': _('Last date order')} ]

            # get coldef_list  and caption
            coldef_list = c.COLDEF_SUBJECT
            captions_dict = c.CAPTION_IMPORT

            # get stored setting from Schoolsetting
            stored_setting = request.user.schoolbase.get_schoolsetting_dict(c.KEY_IMPORT_SUBJECT)

            logger.debug('coldef_list: ' + str(coldef_list))
            logger.debug('captions_dict: ' + str(captions_dict))
            logger.debug('stored_setting: ' + str(stored_setting))

            # don't replace keyvalue when new_setting[key] = ''
            self.has_header = True
            self.worksheetname = ''
            self.codecalc = 'linked'
            if 'has_header' in stored_setting:
                self.has_header = False if Lower(stored_setting['has_header']) == 'false' else True
            if 'worksheetname' in stored_setting:
                self.worksheetname = stored_setting['worksheetname']
            if 'codecalc' in stored_setting:
                self.codecalc = stored_setting['codecalc']

            if 'coldefs' in stored_setting:
                stored_coldefs = stored_setting['coldefs']
                # skip if stored_coldefs does not exist
                if stored_coldefs:
                    # loop through coldef_list
                    for coldef in coldef_list:
                        # coldef = {'tsaKey': 'student', 'caption': 'Cliënt'}
                        # get fieldname from coldef
                        fieldname = coldef.get('tsaKey')
                        # logger.debug('fieldname: ' + str(fieldname))

                        if fieldname:  # fieldname should always be present
                            # check if fieldname exists in stored_coldefs
                            if fieldname in stored_coldefs:
                                # if so, add Excel name with key 'excKey' to coldef
                                coldef['excKey'] = stored_coldefs[fieldname]
                                # logger.debug('stored_coldefs[fieldname]: ' + str(stored_coldefs[fieldname]))

            coldefs_dict = {
                'worksheetname': self.worksheetname,
                'has_header': self.has_header,
                'codecalc': self.codecalc,
                'coldefs': coldef_list
            }
            coldefs_json = json.dumps(coldefs_dict, cls=LazyEncoder)

            captions = json.dumps(captions_dict, cls=LazyEncoder)

            param = awpr_menu.get_headerbar_param(request, 'studentimport', {'captions': captions, 'setting': coldefs_json})

        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_student.html', param)


@method_decorator([login_required], name='dispatch')
class StudentImportUploadSetting(View):  # PR2019-03-10
    # function updates mapped fields, no_header and worksheetname in table Companysetting
    def post(self, request, *args, **kwargs):
        # logger.debug(' ============= StudentImportUploadSetting ============= ')
        # logger.debug('request.POST' + str(request.POST) )
        schoolsetting_dict = {}
        has_permit = False
        if request.user is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_group_system)
        if has_permit:
            if request.POST['upload']:
                new_setting_json = request.POST['upload']
                # new_setting is in json format, no need for json.loads and json.dumps
                # logger.debug('new_setting_json' + str(new_setting_json))

                new_setting_dict = json.loads(request.POST['upload'])
                settings_key = c.KEY_IMPORT_SUBJECT

                new_worksheetname = ''
                new_has_header = True
                new_code_calc = ''
                new_coldefs = {}

                stored_json = request.user.schoolbase.get_schoolsetting_dict(settings_key)
                if stored_json:
                    stored_setting = json.loads(stored_json)
                    # logger.debug('stored_setting: ' + str(stored_setting))
                    if stored_setting:
                        new_has_header = stored_setting.get('has_header', True)
                        new_worksheetname = stored_setting.get('worksheetname', '')
                        new_code_calc = stored_setting.get('codecalc', '')
                        new_coldefs = stored_setting.get('coldefs', {})

                if new_setting_json:
                    new_setting = json.loads(new_setting_json)
                    # logger.debug('new_setting' + str(new_setting))
                    if new_setting:
                        if 'worksheetname' in new_setting:
                            new_worksheetname = new_setting.get('worksheetname', '')
                        if 'has_header' in new_setting:
                            new_has_header = new_setting.get('has_header', True)
                        if 'coldefs' in new_setting:
                            new_coldefs = new_setting.get('coldefs', {})
                    # logger.debug('new_code_calc' + str(new_code_calc))
                new_setting = {'worksheetname': new_worksheetname,
                               'has_header': new_has_header,
                               'codecalc': new_code_calc,
                               'coldefs': new_coldefs}
                new_setting_json = json.dumps(new_setting)

                request.user.schoolbase.set_schoolsetting_dict(settings_key, new_setting_json)

        return HttpResponse(json.dumps(schoolsetting_dict, cls=LazyEncoder))


# --- end of StudentImportUploadSetting

@method_decorator([login_required], name='dispatch')
class StudentImportUploadData(View):  # PR2018-12-04 PR2019-08-05 PR2020-06-04

    def post(self, request):
        logger.debug(' ========================== StudentImportUploadData ========================== ')
        params = {}
        has_permit = False
        is_not_locked = False
        if request.user is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_group_system)
            # TODO change request.user.examyear to sel_examyear
            is_not_locked = not request.user.examyear.locked

        if is_not_locked and has_permit:
            # - Reset language
            # PR2019-03-15 Debug: language gets lost, get request.user.lang again
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                params = import_students(upload_dict, user_lang, request)

        return HttpResponse(json.dumps(params, cls=LazyEncoder))


# --- end of StudentImportUploadData

def import_students(upload_dict, user_lang, request):
    logger.debug(' -----  import_students ----- ')
    logger.debug('upload_dict: ' + str(upload_dict))
    # - get is_test, codecalc, dateformat, awpKey_list
    is_test = upload_dict.get('test', False)
    awpKey_list = upload_dict.get('awpKey_list')
    dateformat = upload_dict.get('dateformat', '')

    params = {}
    if awpKey_list:
        # - get lookup_field
        # lookup_field is field that determines if student alreay exist.
        # check if one of the fields 'payrollcode', 'identifier' or 'code' exists
        # first in the list is lookup_field
        lookup_field = 'code'

        # - get upload_dict from request.POST
        student_list = upload_dict.get('students')
        if student_list:

            today_dte = af.get_today_dateobj()
            today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
            double_line_str = '=' * 80
            indent_str = ' ' * 5
            space_str = ' ' * 30
            logfile = []
            logfile.append(double_line_str)
            logfile.append('  ' + str(request.user.schoolbase.code) + '  -  ' +
                           str(_('Import students')) + ' ' + str(_('date')) + ': ' + str(today_formatted))
            logfile.append(double_line_str)

            if lookup_field is None:
                info_txt = str(_('There is no field given to lookup candidates. Candidates cannot be uploaded.'))
                logfile.append(indent_str + info_txt)
            else:
                if is_test:
                    info_txt = str(_("This is a test. The candidate data are not saved."))
                else:
                    info_txt = str(_("The candidate data are saved."))
                logfile.append(indent_str + info_txt)
                lookup_caption = str(get_field_caption('student', lookup_field))
                info_txt = str(_("Candidates are looked up by the field: '%(fld)s'.") % {'fld': lookup_caption})
                logfile.append(indent_str + info_txt)
                # if dateformat:
                #    info_txt = str(_("The date format is: '%(fld)s'.") % {'fld': dateformat})
                #    logfile.append(indent_str + info_txt)
                update_list = []
                for student_dict in student_list:
                    # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html

                    update_dict = upload_student(student_list, student_dict, lookup_field,
                                                 awpKey_list, is_test, dateformat, indent_str, space_str, logfile,
                                                 request)
                    # json_dumps_err_list = json.dumps(msg_list, cls=f.LazyEncoder)
                    if update_dict:  # 'Any' returns True if any element of the iterable is true.
                        update_list.append(update_dict)

                if update_list:  # 'Any' returns True if any element of the iterable is true.
                    params['student_list'] = update_list
            if logfile:  # 'Any' returns True if any element of the iterable is true.
                params['logfile'] = logfile
                # params.append(new_student)
    return params

def lookup_student(studentbase, request):  # PR2019-12-17 PR2020-10-20
    #logger.debug('----------- lookup_student ----------- ')

    student = None
    multiple_students_found = False

# - search student by studentbase and request.user.examyear  # TODO change request.user.examyear to sel_examyear
    if studentbase:
        # check if student exists multiple times
        # TODO change request.user.examyear to sel_examyear
        row_count = stud_mod.Student.objects.filter(base=studentbase, examyear=request.user.examyear).count()
        if row_count > 1:
            multiple_students_found = True
        elif row_count == 1:
            # get student when only one found
            # TODO change request.user.examyear to sel_examyear
            student = stud_mod.Student.objects.get_or_none(base=studentbase, examyear=request.user.examyear)

    return student, multiple_students_found



def get_field_caption(table, field):
    caption = ''
    if table == 'student':
        if field == 'code':
            caption = _('Abbreviation')
        elif field == 'name':
            caption = _('Student name')
        elif field == 'sequence':
            caption = _('Sequence')
        elif field == 'depbases':
            caption = _('Departments')
    return caption


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
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_studentbase ----- ')
        logger.debug('upload_dict: ' + str(upload_dict))

    studentbase = None

# - get value of 'studentbase_pk'
    studentbase_pk = upload_dict.get('studentbase_pk')

# - create studentbase
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
# - end of create_studentbase


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_student(studentbase, school, department, upload_dict, messages, error_list, request, skip_save):
    # --- create student # PR2019-07-30 PR2020-10-11  PR2020-12-14 PR2021-06-15
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_student ----- ')
        logger.debug('studentbase: ' + str(not not studentbase))
        logger.debug('studentbase.country: ' + str(studentbase.country))
        logger.debug('studentbase.pk: ' + str(studentbase.pk))
        logger.debug('school: ' + str(school))

    student = None
    if studentbase and school:

# - get value of 'lastname', 'firstname', 'ID-number'
        last_name = upload_dict.get('lastname')
        first_name = upload_dict.get('firstname')
        id_number = upload_dict.get('idnumber')

        if logging_on:
            logger.debug('idnumber: ' + str(id_number))
            logger.debug('lastname: ' + str(last_name))
            logger.debug('firstname: ' + str(first_name))

        msg_list = []
        msg_err = av.validate_notblank_maxlength(last_name, c.MAX_LENGTH_FIRSTLASTNAME, _('The last name'))
        if msg_err:
            msg_list.append(msg_err)
        msg_err = av.validate_notblank_maxlength(first_name, c.MAX_LENGTH_FIRSTLASTNAME, _('The first name'))
        if msg_err:
            msg_list.append(msg_err)
        msg_err = av.validate_notblank_maxlength(id_number, c.MAX_LENGTH_IDNUMBER, _('The ID-number'))
        if msg_err:
            msg_list.append(msg_err)
        #TODO validate if student already exists
        if len(msg_list) > 0:
            #  messages is list of dicts with format: {'field': fldName, header': header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html}
            msg_html = '<br>'.join(msg_list)
            messages.append({'class': "alert-danger", 'msg_html': msg_html})
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
            if logging_on:
                logger.debug('field:     ' + str(field))
                logger.debug('new_value: ' + str(new_value) + ' ' + str(type(new_value)))
            try:
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
                                            caption = _('ID-number')
                                        break

                            if idnumber_list and new_value in idnumber_list:
                                has_error = True
                                caption = _('ID-number')
                            else:
                                # add new_value to idnumber_list if it doesn't exist yet
                                idnumber_list.append(new_value)

                        elif field == 'examnumber':
                # when updating single student, examnumber_list is not filled yet. in that case: get examnumber_list
                            if not examnumber_list:
                                examnumber_list = stud_val.get_examnumberlist_from_database(
                                    instance.school, instance.department)
                # check if new_value already exists in examnumber_list
                            if examnumber_list and new_value in examnumber_list:
                                has_error = True
                                caption = _('Exam number')
                            else:
                # add new_value to examnumber_list if it doesn't exist yet
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

    # 2. save changes in text fields
                elif field in ('prefix', 'birthdate', 'birthcountry', 'birthcity', 'classname', 'diplomanumber', 'gradelistnumber'):
                    saved_value = getattr(instance, field)

            # 2. convert gender: take first character, make upper case,
                    #  this comes before new_value != saved_value

                    if logging_on:
                        logger.debug('field:     ' + str(field))
                        logger.debug('new_value: ' + str(new_value) + ' ' + str(type(new_value)))
                        logger.debug('saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))

                    if isinstance(new_value, int):
                        new_value = str(new_value)

                    if new_value != saved_value:
                        has_error = False
                        caption = ''

        # validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                        if has_error:
                            err_txt = _("%(cpt)s '%(val)s' already exists.") \
                                      % {'cpt': str(caption), 'val': new_value}
                            error_list.append(err_txt)
                            msg_list.append({'class': "border_bg_warning", 'msg_html': err_txt})
                        else:
                            setattr(instance, field, new_value)
                            save_changes = True
                            if logging_on:
                                logger.debug('setattr(instance, field, new_value: ' + str(new_value))

    # 3. save changes in department, level or sector
                # department cannot be changed
                elif field in ('level', 'sector'):

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

            except Exception as e:
                err_txt1 = str(_('An error occurred'))
                err_txt2 = str(e)
                err_txt3 = str(_("The changes of '%(val)s' have not been saved.") % {'val': field})
                error_list.append(''.join((err_txt1, ' (', err_txt2, ') ', err_txt3)))

                msg_html = ''.join((err_txt1, ': ', '<br><i>', err_txt2, '</i><br>', err_txt3))
                msg_dict = {'header': str(_('Save changes')), 'class': 'border_bg_invalid', 'msg_html': msg_html}
                msg_list.append(msg_dict)

                logger.error(getattr(e, 'message', str(e)))

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
            new_regnumber = stud_func.calc_regnumber(school_code, gender, examyear_code, examnumber, depbase, levelbase)

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
    logger.debug(' ----- update_scheme_in_studsubj ----- ')

    # - update scheme in student, also remove if necessary
    new_scheme = subj_mod.Scheme.objects.get_or_none(
        department=student.department,
        level=student.level,
        sector=student.sector)
    setattr(student, 'scheme', new_scheme)

# - loop through studsubj of this student
    studsubjects = stud_mod.Studentsubject.objects.filter(student=student)
    for studsubj in studsubjects:
        if new_scheme is None:
            # delete studsub when no scheme
            studsubj.delete(request=request)
        else:
            # skip when studsub scheme equals new_scheme
            if studsubj.schemeitem.scheme != new_scheme:
                # check how many times this subjject occurs in new scheme
                count_subject_in_newscheme = subj_mod.Schemeitem.objects.filter(
                    scheme=new_scheme,
                    subject=studsubj.schemeitem.subject
                    ).count()
                if not count_subject_in_newscheme:
                    # delete studsub when subject does not exist in new_scheme
                    studsubj.delete(request=request)
                elif count_subject_in_newscheme == 1:
                    # if subject occurs only once in mew_scheme: replace schemeitem by new schemeitem
                    new_schemeitem = subj_mod.Schemeitem.objects.get_or_none(
                        scheme=new_scheme,
                        subject=studsubj.schemeitem.subject
                    )
                    if new_schemeitem:
                        studsubj.schemeitem = new_schemeitem
                        studsubj.save(request=request)
                else:
                    # if subject occurs multiple times in mew_scheme: check if one exist with same subjecttype
                    new_schemeitem = subj_mod.Schemeitem.objects.get_or_none(
                        scheme=new_scheme,
                        subject=studsubj.schemeitem.subject,
                        subjecttype=studsubj.schemeitem.subjecttype
                    )
                    if new_schemeitem:
                        studsubj.schemeitem = new_schemeitem
                        studsubj.save(request=request)
                    else:
                        # if no schemeitem exist with same subjecttype: get schemeitem with lowest sequence
                        new_schemeitem = subj_mod.Schemeitem.objects.get_or_none(
                            scheme=new_scheme,
                            subject=studsubj.schemeitem.subject
                        ).order_by('sequence').first()
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
                if studsubj.deleted:
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

# - create and save Studentsubject
        if not msg_err:
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
                logger.error(getattr(e, 'message', str(e)))

                # error_list not in use when using modal form, message is displayed in modmesasges
                err_01 = str(_('An error occurred:'))
                err_02 = str(e)
                err_03 = str(_("%(cpt)s '%(val)s' could not be added.") % {'cpt': str(_('Subject')), 'val': subject_name})
                error_list.extend((err_01, err_02, err_03))

                # this one closes modal and shows modmessage with msg_html
                msg_html = '<br>'.join((err_01, '<i>' + err_02 + '</i>', err_03))
                messages.append({'class': "alert-danger", 'msg_html': msg_html})

    return studsubj
# - end of create_studsubj


#/////////////////////////////////////////////////////////////////

def create_studentsubject_rows(setting_dict, append_dict, student_pk=None, studsubj_pk=None):
    # --- create rows of all students of this examyear / school PR2020-10-27
    #logger.debug(' =============== create_student_rows ============= ')
    #logger.debug('append_dict: ' + str(append_dict))
    #logger.debug('setting_dict: ' + str(setting_dict))
    # create list of students of this school / examyear, possibly with filter student_pk or studsubj_pk
    # with left join of studentsubjects with deleted=False
    sel_examyear_pk = af.get_dict_value(setting_dict, ('sel_examyear_pk',))
    sel_schoolbase_pk = af.get_dict_value(setting_dict, ('sel_schoolbase_pk',))
    sel_depbase_pk = af.get_dict_value(setting_dict, ('sel_depbase_pk',))
    #logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk))
    #logger.debug('sel_schoolbase_pk: ' + str(sel_schoolbase_pk))
    #logger.debug('sel_depbase_pk: ' + str(sel_depbase_pk))

    sql_studsubj_list = ["SELECT studsubj.id AS studsubj_id, studsubj.student_id,",
        "studsubj.cluster_id, si.id AS schemeitem_id, si.scheme_id AS scheme_id,",
        "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_elective_combi,",
        "studsubj.pws_title, studsubj.pws_subjects,",
        "studsubj.has_exemption, studsubj.has_reex, studsubj.has_reex03, studsubj.has_pok,",
        "si.subject_id, si.subjecttype_id, si.gradetype,",
        "subjbase.code AS subj_code, subj.name AS subj_name,",
        "si.weight_se AS si_se, si.weight_ce AS si_ce,",
        "si.is_mandatory, si.is_combi, si.extra_count_allowed, si.extra_nocount_allowed,",
        "si.elective_combi_allowed, si.has_practexam,",

        "sjt.id AS sjtp_id, sjt.abbrev AS sjtp_abbrev, sjt.has_prac AS sjtp_has_prac, sjt.has_pws AS sjtp_has_pws,",
        "sjtbase.sequence AS sjtbase_sequence,",

        "studsubj.subj_auth1by_id AS subj_auth1_id, SUBSTRING(subj_auth1.username, 7) AS subj_auth1_usr, subj_auth1.modified_at AS subj_auth1_modat,",
        "studsubj.subj_auth2by_id AS subj_auth2_id, SUBSTRING(subj_auth2.username, 7) AS subj_auth2_usr, subj_auth2.modified_at AS subj_auth2_modat,",
        "studsubj.subj_published_id AS subj_publ_id, subj_published.modifiedat AS subj_publ_modat,",

        "studsubj.exem_auth1by_id AS exem_auth1_id, SUBSTRING(exem_auth1.username, 7) AS exem_auth1_usr, exem_auth1.modified_at AS exem_auth1_modat,",
        "studsubj.exem_auth2by_id AS exem_auth2_id, SUBSTRING(exem_auth2.username, 7) AS exem_auth2_usr, exem_auth2.modified_at AS exem_auth2_modat,",
        "studsubj.exem_published_id AS exem_publ_id, exem_published.modifiedat AS exem_publ_modat,",

        "studsubj.reex_auth1by_id AS reex_auth1_id, SUBSTRING(reex_auth1.username, 7) AS reex_auth1_usr, reex_auth1.modified_at AS reex_auth1_modat,",
        "studsubj.reex_auth2by_id AS reex_auth2_id, SUBSTRING(reex_auth2.username, 7) AS reex_auth2_usr, reex_auth2.modified_at AS reex_auth2_modat,",
        "studsubj.reex_published_id AS reex_publ_id, reex_published.modifiedat AS reex_publ_modat,",

        "studsubj.reex3_auth1by_id AS reex3_auth1_id, SUBSTRING(reex3_auth1.username, 7) AS reex3_auth1_usr, reex3_auth1.modified_at AS reex3_auth1_modat,",
        "studsubj.reex3_auth2by_id AS reex3_auth2_id, SUBSTRING(reex3_auth2.username, 7) AS reex3_auth2_usr, reex3_auth2.modified_at AS reex3_auth2_modat,",
        "studsubj.reex3_published_id AS reex3_publ_id, reex3_published.modifiedat AS reex3_publ_modat,",

        "studsubj.pok_auth1by_id AS pok_auth1_id, SUBSTRING(pok_auth1.username, 7) AS pok_auth1_usr, pok_auth1.modified_at AS pok_auth1_modat,",
        "studsubj.pok_auth2by_id AS pok_auth2_id, SUBSTRING(pok_auth2.username, 7) AS pok_auth2_usr, pok_auth2.modified_at AS pok_auth2_modat,",
        "studsubj.pok_published_id AS pok_publ_id, pok_published.modifiedat AS pok_publ_modat,",

        "studsubj.deleted, studsubj.modifiedby_id, studsubj.modifiedat,",
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

        "WHERE NOT studsubj.deleted"]
    sql_studsubjects = ' '.join(sql_studsubj_list)

    sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk, 'db_id': sel_depbase_pk}

    sql_list = ["SELECT studsubj.studsubj_id, studsubj.schemeitem_id, studsubj.cluster_id,",
        "CONCAT('studsubj_', st.id::TEXT, '_', studsubj.studsubj_id::TEXT) AS mapid, 'studsubj' AS table,",
        "st.id AS stud_id, st.lastname, st.firstname, st.prefix, st.examnumber,",
        "st.scheme_id, st.iseveningstudent, st.locked, st.has_reex, st.bis_exam, st.withdrawn,",
        "studsubj.subject_id AS subj_id, studsubj.subj_code, studsubj.subj_name,",
        "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",

        "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_elective_combi,",
        "studsubj.pws_title, studsubj.pws_subjects,",
        "studsubj.has_exemption, studsubj.has_reex, studsubj.has_reex03, studsubj.has_pok,",

        "studsubj.is_mandatory, studsubj.is_combi, studsubj.extra_count_allowed, studsubj.extra_nocount_allowed, studsubj.elective_combi_allowed,",
        "studsubj.sjtp_id, studsubj.sjtp_abbrev, studsubj.sjtp_has_prac, studsubj.sjtp_has_pws,",

        "studsubj.subj_auth1_id, studsubj.subj_auth1_usr, studsubj.subj_auth1_modat,",
        "studsubj.subj_auth2_id, studsubj.subj_auth2_usr, studsubj.subj_auth2_modat,",
        "studsubj.subj_publ_id, studsubj.subj_publ_modat,",

        "studsubj.exem_auth1_id, studsubj.exem_auth1_usr, studsubj.exem_auth1_modat,",
        "studsubj.exem_auth2_id, studsubj.exem_auth2_usr, studsubj.exem_auth2_modat,",
        "studsubj.exem_publ_id, studsubj.exem_publ_modat,",

        "studsubj.reex_auth1_id, studsubj.reex_auth1_usr, studsubj.reex_auth1_modat,",
        "studsubj.reex_auth2_id, studsubj.reex_auth2_usr, studsubj.reex_auth2_modat,",
        "studsubj.reex_publ_id, studsubj.reex_publ_modat,",

        "studsubj.reex3_auth1_id, studsubj.reex3_auth1_usr, studsubj.reex3_auth1_modat,",
        "studsubj.reex3_auth2_id, studsubj.reex3_auth2_usr, studsubj.reex3_auth2_modat,",
        "studsubj.reex3_publ_id, studsubj.reex3_publ_modat,",

        "studsubj.pok_auth1_id, studsubj.pok_auth1_usr, studsubj.pok_auth1_modat,",
        "studsubj.pok_auth2_id, studsubj.pok_auth2_usr, studsubj.pok_auth2_modat,",
        "studsubj.pok_publ_id, studsubj.pok_publ_modat,",

        "studsubj.deleted, studsubj.modifiedat, studsubj.modby_username",
        "FROM students_student AS st",
        "LEFT JOIN (" + sql_studsubjects + ") AS studsubj ON (studsubj.student_id = st.id)",
        "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
        "LEFT JOIN subjects_scheme AS scheme ON (scheme.id = st.scheme_id)",
        "LEFT JOIN subjects_package AS package ON (package.id = st.package_id)",
        "WHERE school.base_id = %(sb_id)s::INT AND school.examyear_id = %(ey_id)s::INT AND dep.base_id = %(db_id)s::INT"]

    if studsubj_pk:
        sql_list.append('AND studsubj.studsubj_id = %(studsubj_id)s::INT')
        sql_keys['studsubj_id'] = studsubj_pk
    elif student_pk:
        sql_keys['st_id'] = student_pk
        sql_list.append('AND st.id = %(st_id)s::INT')
        sql_list.append('ORDER BY studsubj.subj_code')
    else:
        sql_list.append('ORDER BY LOWER(st.lastname), LOWER(st.firstname), studsubj.subj_code')
    sql = ' '.join(sql_list)

    #logger.debug('sql: ' + str(sql))
    newcursor = connection.cursor()
    newcursor.execute(sql, sql_keys)
    student_rows = af.dictfetchall(newcursor)

# - full name to rows
    if student_rows:
        for row in student_rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

# - add messages to student_row, only when only 1 row added (then studsubj_pk has value)
        if studsubj_pk:
            # when student_pk has value there is only 1 row
            row = student_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    return student_rows
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

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
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
                "subj.id AS subj_id, subjbase.code AS subjbase_code, subj.name AS subj_name, subj.etenorm AS subj_etenorm,",
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

                "WHERE NOT studsubj.deleted",
                # "AND studsubj.subj_published_id IS NOT NULL"

                ]
    sub_sql = ' '.join(sql_sublist)

    sql_keys = {'ey_id': sel_examyear_pk}
    sql_list = ["SELECT sch.id AS school_id, schbase.code AS schbase_code, sch.name AS school_name,",
        "sub.dep_id, sub.depbase_code, sub.lvl_id, sub.lvl_abbrev,",
        "sub.subj_id, sub.subjbase_code, sub.subj_name, sub.subj_etenorm,",
        "ARRAY_AGG(DISTINCT sub.subj_published_id) AS subj_published_arr,",
        "sub.lang,",
        "count(*) AS count",

        "FROM (" + sub_sql + ") AS sub",

        "INNER JOIN schools_school AS sch ON (sch.id = sub.school_id)",
        "INNER JOIN schools_schoolbase AS schbase ON (schbase.id = sch.base_id)",

        "GROUP BY sch.id, schbase.code, sch.name, sub.dep_id, sub.depbase_id, sub.depbase_code,",
                "sub.lvl_id, sub.lvl_abbrev, sub.lang, ",
                "sub.subj_id, sub.subjbase_code, sub.subj_name, sub.subj_etenorm",
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

