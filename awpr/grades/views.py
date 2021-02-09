# PR2020-12-03
from django.contrib.auth.decorators import login_required

from django.db.models import Q
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import View

from django.core.files.storage import default_storage
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.core.files import File

import io
import codecs
import platform
import os

import string
import random

from awpr import functions as f
from awpr import constants as c
from awpr import settings as awpr_settings
from students import validations as v
from awpr import menus as awpr_menu
from awpr import functions as af
from awpr import downloads as dl
from awpr import calc_finalgrade as calc_final

from accounts import models as acc_mod
from schools import models as sch_mod
from students import models as stud_mod
from students import views as stud_view
from subjects import models as subj_mod
from grades import validations as grad_val
from grades import exfiles as grade_exfiles

import json # PR2018-12-03
# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

# ========  Student  =====================================

@method_decorator([login_required], name='dispatch')
class GradeListView(View):  # PR2020-12-03

    def get(self, request):
        #logger.debug('  =====  GradeListView ===== ')
        #logger.debug('request: ' + str(request) + ' Type: ' + str(type(request)))

# - set headerbar parameters PR2018-08-06
        page = 'grades'
        params = awpr_menu.get_headerbar_param(
            request=request,
            page=page
        )

# - save this page in Usersetting, so at next login this page will open. Uses in LoggedIn
        if request.user:
            request.user.set_usersetting_dict('sel_page', {'page': page})

        return render(request, 'grades.html', params)

#FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

@method_decorator([login_required], name='dispatch')
class GradeApproveView(View):  # PR2021-01-19

    def post(self, request):
        logger.debug(' ============= GradeApproveView ============= ')
        # function creates, deletes and updates grade records of current studentsubject PR2020-11-21
        update_wrap = {}

        #<PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated
        has_permit = False
        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user
            # TODO ROLE_32_ADMIN, ROLE_64_SYSTEM is only for testing, must be removed
            if req_user.role in (c.ROLE_08_SCHOOL, c.ROLE_32_ADMIN, c.ROLE_64_SYSTEM):
                has_permit = (req_user.is_perm_auth1 or req_user.is_perm_auth2 or req_user.is_perm_auth3)
            if has_permit:

    # - reset language
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

    # - get upload_dict from request.POST
                upload_json = request.POST.get('upload', None)
                if upload_json:
                    upload_dict = json.loads(upload_json)
                    logger.debug('upload_dict' + str(upload_dict))

    # - get selected mode. Modes are 'approve' 'submit_test' 'submit_submit', 'reset'
                    mode = upload_dict.get('mode')

                    is_approve = True if mode in ('approve_test', 'approve_submit', 'approve_reset') else False
                    is_submit = True if mode in ('submit_test', 'submit_submit') else False
                    is_reset = True if mode == 'approve_reset' else False
                    is_test = True if mode in ('approve_test', 'submit_test') else False
                    logger.debug('mode: ' + str(mode))

    # - get selected examyear, school and department from usersettings
                    sel_examyear, sel_school, sel_department, is_locked, \
                        examyear_published, school_activated, is_requsr_school = \
                            dl.get_selected_examyear_school_dep_from_usersetting(request)

    # - get selected examperiod from usersetting
                    sel_examperiod = None
                    selected_dict = req_user.get_usersetting_dict(c.KEY_SELECTED_PK)
                    if selected_dict:
                        sel_examperiod = selected_dict.get(c.KEY_SEL_EXAMPERIOD)

    # - get selected grade from upload_dict - only if clicked on a grade tblRow
                    grade_pk = upload_dict.get('grade_pk')
                    logger.debug('grade_pk: ' + str(grade_pk))

    # - if  grade_pk has value: get sel_examtype from upload_dict instead of from settings
                    sel_subject_pk = None
                    if grade_pk:
                        sel_examtype = upload_dict.get('examtype')
                        logger.debug('sel_examtype: ' + str(sel_examtype))
                    else:
    # - if  grade_pk has no value: get selected examperiod, examtype and subject_pk from usersettings
                        # update usersetting if new values in upload_dict
                        new_examtype = upload_dict.get('examtype')
                        new_subject_pk = upload_dict.get('subject_pk')
                        logger.debug('new_subject_pk: ' + str(new_subject_pk))
                        if new_examtype or new_subject_pk:
                            new_setting_dict = {}
                            if new_examtype:
                                new_setting_dict[c.KEY_SEL_EXAMTYPE] = new_examtype
                            if new_subject_pk:
                                new_setting_dict[c.KEY_SEL_SUBJECT_PK] = new_subject_pk
                            logger.debug('new_setting_dict: ' + str(new_setting_dict))
                            saved_setting_dict = req_user.set_usersetting_from_upload_subdict(c.KEY_SELECTED_PK, new_setting_dict)
                            logger.debug('saved_setting_dict: ' + str(saved_setting_dict))
                        sel_examperiodNIU, sel_examtype, sel_subject_pk = \
                            dl.get_selected_examperiod_examtype_from_usersetting(request)

                    if sel_examyear and sel_school and sel_department and sel_examperiod and sel_examtype:
                        logger.debug('sel_examperiod: ' + str(sel_examperiod))
    # +++ get selected grade_rows
                        crit = Q(studentsubject__student__school=sel_school) & \
                               Q(studentsubject__student__department=sel_department) & \
                               Q(examperiod=sel_examperiod)
                        if grade_pk:
                            crit.add(Q(pk=grade_pk), crit.connector)
                        elif sel_subject_pk:
                            crit.add(Q(studentsubject__schemeitem__subject_id=sel_subject_pk), crit.connector)
                        row_count = stud_mod.Grade.objects.filter(crit).count()
                        logger.debug('row_count: ' + str(row_count))

                        grades = stud_mod.Grade.objects.filter(crit)
                        msg_dict = {'count': 0,
                                    'already_published': 0,
                                    'double_approved': 0,
                                    'no_value': 0,
                                    'committed': 0,
                                    'saved': 0,
                                    'reset': 0,
                                    'already_approved_by_auth': 0,
                                    'auth_missing': 0,
                                    'test_is_ok': False
                                    }
                        if grades is not None:
       # create new published_instance. Only save it when it is not a test
                            published_instance = None
                            if is_submit and not is_test:
                                published_instance = create_published_instance(sel_school, sel_department, sel_examtype, sel_examperiod, sel_subject_pk, is_test, request)
        # +++++ loop through  grades
                            grade_rows = []
                            logger.debug('grade_rows: ' + str(grade_rows))
                            for grade in grades:
                                logger.debug('grade: ' + str(grade))
                                msg_dict['count'] += 1
                                if is_approve:
                                    approve_grade(grade, sel_examtype, is_test, is_reset, msg_dict, request)
                                elif is_submit:
                                    submit_grade(grade, sel_examtype, is_test, published_instance, msg_dict, request)

    # - add update_dict to update_wrap
                                if grade:
                                    # TODO check value of error_dict
                                    #if error_dict:
                                    #    append_dict['error'] = error_dict
                                    append_dict = {}
                                    rows = create_grade_rows(
                                        sel_examyear_pk=sel_examyear.pk,
                                        sel_schoolbase_pk=sel_school.base_id,
                                        sel_depbase_pk=sel_department.base_id,
                                        append_dict=append_dict,
                                        sel_examperiod=sel_examperiod,
                                        grade_pk=grade.pk)
                                    if rows:
                                        grade_rows.append(rows[0])
        # +++++  end of loop through  grades

                            row_count = len(grade_rows)
                            logger.debug('len: ' + str(len))
                            if not row_count:
                                msg_dict['count_text'] = str(
                                    _("The selection contains %(val)s.") % {'val': get_grade_text(0)})
                                logger.debug('msg_dict: ' + str(msg_dict))
                            else:

                                if is_submit and not is_test:
                                    sel_subject = subj_mod.Subject.objects.get_or_none(
                                        pk=sel_subject_pk,
                                        examyear=sel_examyear
                                    )
                                    create_ex2a(published_instance, sel_examyear, sel_school,
                                                         sel_department, sel_subject, sel_examperiod,
                                                         sel_examtype, grade_rows, request)

                                    update_wrap['updated_published_rows'] = create_published_rows(
                                        sel_examyear_pk=sel_examyear.pk,
                                        sel_schoolbase_pk=sel_school.base_id,
                                        sel_depbase_pk=sel_department.base_id
                                    )

                                update_wrap['updated_grade_rows'] = grade_rows

                                if is_test:
                                    count = msg_dict.get('count', 0)
                                    committed = msg_dict.get('committed', 0)
                                    no_value = msg_dict.get('no_value', 0)
                                    already_published = msg_dict.get('already_published', 0)
                                    auth_missing = msg_dict.get('auth_missing', 0)
                                    already_approved_by_auth = msg_dict.get('already_approved_by_auth', 0)
                                    double_approved = msg_dict.get('double_approved', 0)

                                    msg_dict['count_text'] = _("The selection contains %(val)s.") % \
                                                             {'val': get_grade_text(count)}
                                    if committed:
                                        msg_dict['test_is_ok'] = True

                                    if committed < count:
                                        msg_dict['skip_text'] = _("The following grades will be skipped:")
                                    if already_published:
                                        msg_dict['already_published_text'] = _("  - %(val)s already submitted") % \
                                                                 {'val': get_grades_are_text(already_published)}
                                    if auth_missing:
                                        msg_dict['auth_missing_text'] = _("  - %(val)s not completely approved") % \
                                                                 {'val': get_grades_are_text(auth_missing)}
                                    if no_value:
                                        if no_value == 1:
                                            msg_dict['no_value_text'] = _("  - 1 grade has no value")
                                        else:
                                            msg_dict['no_value_text'] = _("  - %(val)s grades have no value") % {'val': no_value}

                                    if double_approved:
                                        msg_dict['double_approved_text'] = _("  - %(val)s approved multiple times by the same user, in different functions ") % \
                                                                    {'val': get_grades_are_text(double_approved)}
                                    if already_approved_by_auth:
                                        msg_dict['already_approved_by_auth_text'] = _("  - %(val)s already approved") % \
                                                                    {'val': get_grades_are_text(already_approved_by_auth)}
                                    if is_approve:
                                        if not committed:
                                            msg_dict['saved_text'] = _("No grades will be approved.")
                                        elif committed == 1:
                                            msg_dict['saved_text'] = _("One grade will be approved.")
                                        else:
                                            msg_dict['saved_text'] = _("%(val)s grades will be approved.") % \
                                                                 {'val': committed}
                                    elif is_submit:
                                        if is_test:
                                            if not committed:
                                                msg_dict['saved_text'] = _("The Ex2A form can not be submitted.")
                                            elif committed == 1:
                                                msg_dict['saved_text'] = _("One grade will be added to the Ex2A form.")
                                            else:
                                                msg_dict['saved_text'] = _("%(val)s grades will be added to the Ex2A form.") % \
                                                                     {'val': committed}
                                else:
                                    saved = msg_dict.get('saved', 0)
                                    if not saved:
                                        msg_dict['saved_text'] = _("The Ex2A form has not been submitted.")
                                    elif saved == 1:
                                        msg_dict['saved_text'] = _("The Ex2A has been submitted. It contains 1 grade.")
                                    else:
                                        msg_dict['saved_text'] = _("The Ex2A has been submitted. It contains %(val)s grades.") % \
                                                             {'val': saved}

    # - add  msg_dict to update_wrap
                        update_wrap['msg_dict'] = msg_dict

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=f.LazyEncoder))
# --- end of GradeUploadView


def create_published_instance(sel_school, sel_department, sel_examtype, sel_examperiod, sel_subject_pk, is_test, request):  # PR2021-01-21
    #logger.debug('----- create_published_instance -----')
    # create new published_instance and save it when it is not a test
    depbase_code = sel_department.base.code if sel_department.base.code else '-'
    school_code = sel_school.base.code if sel_school.base.code else '-'
    school_abbrev = sel_school.abbrev if sel_school.abbrev else '-'
    #examtype_caption = c.EXAMTYPE_CAPTION[sel_examtype].lower()

    examperiod_str = ''
    if sel_examperiod == 1:
        examperiod_str = '-tv1'
    if sel_examperiod == 2:
        examperiod_str = '-tv2'
    elif sel_examperiod == 3:
        examperiod_str = '-tv3'
    elif sel_examperiod == 4:
        examperiod_str = '-vrst'
    examtype_caption = sel_examtype.upper() + examperiod_str

    subject_code = ''
    if sel_subject_pk:
        subject = subj_mod.Subject.objects.get_or_none(pk=sel_subject_pk)
        if subject:
            subject_code = subject.base.code

    today_date = af.get_today_dateobj()
    today_iso = today_date.isoformat()

    # TODO add level if it is filtered on those fields
    name = ' '.join(('Ex2A', school_code, depbase_code, school_abbrev, examtype_caption, subject_code, today_iso))
    # skip schoolname if total name is too long
    if len(name) > c.MAX_LENGTH_FIRSTLASTNAME:
        name = ' '.join(('Ex2A', school_code, depbase_code, today_iso))

    published_instance = stud_mod.Published(
        school=sel_school,
        department=sel_department,
        examtype=sel_examtype,
        examperiod=sel_examperiod,
        name=name,
        datepublished=today_date)

    if not is_test:
        published_instance.save(request=request)
        logger.debug('published_instance.saved: ' + str(published_instance))

        #file_name = ( ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(24)) ) + '.pdf'
        file_name = ( ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(24)) ) + '.pdf'

        # published_instance.filename = 'published_' + str(published_instance.pk) + '.pdf'
        published_instance.filename = file_name

        published_instance.save(request=request)
    return published_instance
# - end of create_published_instance

def get_grade_text(count):
    return _('no grades') if not count else _('1 grade') if count == 1 else str(count) + str(_(' grades'))


def get_grades_are_text(count):
    return _('no grades are') if not count else _('1 grade is') if count == 1 else str(count) + str(_(' grades are'))


def approve_grade(grade, sel_examtype, is_test, is_reset, msg_dict, request):  # PR2021-01-19
    logger.debug('----- approve_grade -----')
    logger.debug('sel_examtype: ' + str(sel_examtype))
    logger.debug('is_reset: ' + str(is_reset))

    if grade and sel_examtype and sel_examtype in ('se', 'pe', 'ce'):
        req_user = request.user

# - skip if this grade / examtype is already published
        published = getattr(grade, sel_examtype + '_published')
        logger.debug('published: ' + str(published))
        if published:
            msg_dict['already_published'] += 1
        else:

# skip if this grade has no value
            grade_value = getattr(grade, sel_examtype + 'grade')
            score_value = None
            if sel_examtype in ('pe', 'ce'):
                score_value = getattr(grade, sel_examtype + 'score')
            no_value = grade_value is None and score_value is None
            logger.debug('no_value: ' + str(no_value))
            if no_value:
                msg_dict['no_value'] += 1
            else:
                authby_field = None
                if req_user.is_perm_auth1:
                    authby_field = sel_examtype + '_auth1by'
                elif req_user.is_perm_auth2:
                    authby_field = sel_examtype + '_auth2by'
                elif req_user.is_perm_auth3:
                    authby_field = sel_examtype + '_auth3by'
                logger.debug('authby_field: ' + str(authby_field))

# - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved
                auth1by = getattr(grade, sel_examtype + '_auth1by')
                auth2by = getattr(grade, sel_examtype + '_auth2by')
                auth3by = getattr(grade, sel_examtype + '_auth3by')

                double_approved = False
                save_changes = False

# - remove  authby when is_reset
                if is_reset:
                    setattr(grade, authby_field, None)
                    msg_dict['reset'] += 1
                    save_changes = True
                else:

# - skip if this grade is already approved by this auth
                    already_approved_by_auth = req_user.is_perm_auth1 and auth1by or \
                                               req_user.is_perm_auth2 and auth2by or \
                                               req_user.is_perm_auth3 and auth3by
                    logger.debug('already_approved_by_auth: ' + str(already_approved_by_auth))
                    if already_approved_by_auth:
                        msg_dict['already_approved_by_auth'] += 1
                    else:

# - skip if this author (like 'president') has already approved this grade
            # under a different permit (like 'secretary' or 'commissioner')
                        if req_user.is_perm_auth1:
                            double_approved = (auth2by and auth2by == req_user) or (auth3by and auth3by == req_user)
                        elif req_user.is_perm_auth2:
                            double_approved = (auth1by and auth1by == req_user) or (auth3by and auth3by == req_user)
                        elif req_user.is_perm_auth3:
                            double_approved = (auth1by and auth1by == req_user) or (auth2by and auth2by == req_user)

                        logger.debug('double_approved: ' + str(double_approved))
                        if double_approved:
                            msg_dict['double_approved'] += 1
                        else:
                            setattr(grade, authby_field, req_user)
                            save_changes = True
                            logger.debug('save_changes: ' + str(save_changes))

# - set value of authby_field
                if save_changes:
                    if is_test:
                        msg_dict['committed'] += 1
                    else:
                        msg_dict['saved'] += 1

                        status_index = 1 if req_user.is_perm_auth1 else \
                            2 if req_user.is_perm_auth2 else \
                            3 if req_user.is_perm_auth3 else None
                        logger.debug('status_index: ' + str(status_index))
                        logger.debug('is_reset: ' + str(is_reset))

                        saved_status_sum = getattr(grade, sel_examtype + '_status')
                        logger.debug('saved_status_sum: ' + str(saved_status_sum))

                        new_value_bool = True if not is_reset else False
                        new_status_sum = set_status_sum_by_index(saved_status_sum, status_index, new_value_bool)
                        logger.debug('new_status_sum: ' + str(new_status_sum))
                        setattr(grade, sel_examtype + '_status', new_status_sum)

    # - save changes
                        grade.save(request=request)
# - end of approve_grade

def submit_grade(grade, sel_examtype, is_test, published_instance, msg_dict, request):  # PR2021-01-21
    logger.debug('----- submit_grade -----')

    if grade and sel_examtype and sel_examtype in ('se', 'pe', 'ce'):

# - check if this grade / examtype is already published
        published = getattr(grade, sel_examtype + '_published')
        logger.debug('published: ' + str(published))
        if published:
            msg_dict['already_published'] += 1
        else:

# skip if this grade has no value
            grade_value = getattr(grade, sel_examtype + 'grade')
            score_value = None
            if sel_examtype in ('pe', 'ce'):
                score_value = getattr(grade, sel_examtype + 'score')
            no_value = grade_value is None and score_value is None
            logger.debug('no_value: ' + str(no_value))
            if no_value:
                msg_dict['no_value'] += 1
            else:

# - check if this grade / examtype is approved by all auth
                auth1by = getattr(grade, sel_examtype + '_auth1by')
                auth2by = getattr(grade, sel_examtype + '_auth2by')
                auth3by = getattr(grade, sel_examtype + '_auth3by')
                # TODO dnot checking on auth3by ia only for testing. Must put it back
                # auth_missing = auth1by is None or auth2by is None or auth3by is None
                auth_missing = auth1by is None or auth2by is None
                logger.debug('subject: ' + str(grade.studentsubject.schemeitem.subject.name))
                logger.debug('auth1by: ' + str(auth1by))
                logger.debug('auth2by: ' + str(auth2by))
                logger.debug('auth3by: ' + str(auth3by))
                logger.debug('auth_missing: ' + str(auth_missing))
                if auth_missing:
                    msg_dict['auth_missing'] += 1
                else:
# - check if all auth are different
                    double_approved = auth1by == auth2by or auth1by == auth3by or auth2by == auth3by
                    logger.debug('double_approved: ' + str(double_approved))
                    if double_approved and not auth_missing:
                        msg_dict['double_approved'] += 1
                    else:
# - set value of published_instance and exatmtype_status field
                        if is_test:
                            msg_dict['committed'] += 1
                        else:
                            msg_dict['saved'] += 1
                            setattr(grade, sel_examtype + '_published', published_instance)

                            status_index = 4 # c.STATUS_04_SUBMITTED # STATUS_04_SUBMITTED = 16
                            saved_status_sum = getattr(grade, sel_examtype + '_status')
                            new_value_bool = True
                            new_status_sum = set_status_sum_by_index(saved_status_sum, status_index, new_value_bool)

                            logger.debug('saved_status_sum: ' + str(saved_status_sum))
                            logger.debug('status_index: ' + str(status_index))
                            logger.debug('new_status_sum: ' + str(new_status_sum))
                            setattr(grade, sel_examtype + '_status', new_status_sum)
# - save changes
                            grade.save(request=request)
# - end of approve_grade

# - end of submit_grade

#FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF


@method_decorator([login_required], name='dispatch')
class GradeUploadView(View):  # PR2020-12-16 PR2021-01-15

    def post(self, request):
        #logger.debug(' ============= GradeUploadView ============= ')
        # function creates, deletes and updates grade records of current studentsubject PR2020-11-21
        update_wrap = {}

        #<PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated
        has_permit = False
        if request.user and request.user.country and request.user.schoolbase:
            has_permit = (request.user.role > c.ROLE_02_STUDENT and request.user.is_perm_edit)
        if has_permit:

        # - TODO when deleting: return warning when subject grades have values

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                #logger.debug('upload_dict' + str(upload_dict))

# - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, is_locked, \
                examyear_published, school_activated, is_requsr_school = \
                    dl.get_selected_examyear_school_dep_from_usersetting(request)
# - get selected examperiod and examtype from usersettings
                sel_examperiod, sel_examtype, sel_subject_pkNIU = \
                    dl.get_selected_examperiod_examtype_from_usersetting(request)

# - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                student = None
                # TODO may_edit is not activated for testing:
                #  may_edit = examyear_published and school_activated and is_requsr_school and sel_department and not is_locked
                # sel_department only has value when sel_examyear and sel_school have value
                may_edit = sel_department and not is_locked
                #logger.debug('may_edit: ' + str(may_edit))
                if may_edit:
                    student_pk = upload_dict.get('student_pk')
                    student = stud_mod.Student.objects.get_or_none(
                        id=student_pk,
                        school=sel_school,
                        department=sel_department,
                        locked=False
                    )
                if student:
# - get current studentsubject
                    studsubj_pk = upload_dict.get('studsubj_pk')
                    studentsubject = stud_mod.Studentsubject.objects.get_or_none(
                        id=studsubj_pk,
                        student=student
                    )
                    #logger.debug('studentsubject: ' + str(studentsubject))

                    append_dict = {}
                    error_dict = {}
# - get current grade - when mode is 'create': studsubj is None. It will be created at "elif mode == 'create'"
                    examperiod_int = upload_dict.get('examperiod')
                    grade_pk = upload_dict.get('grade_pk')
                    grade = None
                    if studentsubject:
                        grade = stud_mod.Grade.objects.get_or_none(
                            id=grade_pk,
                            studentsubject =studentsubject,
                            examperiod=examperiod_int
                        )
                    #logger.debug('examperiod_int: ' + str(examperiod_int))
                    #logger.debug('grade_pk: ' + str(grade_pk))
                    #logger.debug('grade: ' + str(grade))

# +++ update existing grade - also when grade is created - grade is None when deleted
                    mode = upload_dict.get('mode')
                    #logger.debug('mode: ' + str(mode))
                    if grade and mode == 'update':
                        update_grade(grade, upload_dict, error_dict, request)

# - add update_dict to update_wrap
                    grade_rows = []
                    if grade:
                        # TODO check value of error_dict
                        if error_dict:
                            append_dict['error'] = error_dict
                        rows = create_grade_rows(
                            sel_examyear_pk=sel_examyear.pk,
                            sel_schoolbase_pk=sel_school.base_id,
                            sel_depbase_pk=sel_department.base_id,
                            sel_examperiod=sel_examperiod,
                            append_dict=append_dict,
                            grade_pk=grade.pk)
                        if rows:
                            row = rows[0]
                            if row:
                                grade_rows.append(row)
                    if grade_rows:
                        update_wrap['updated_grade_rows'] = grade_rows

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=f.LazyEncoder))
# --- end of GradeUploadView


#######################################################
def update_grade(instance, upload_dict, err_dict, request):
    # --- update existing grade PR2020-12-16
    # add new values to update_dict (don't reset update_dict, it has values)
    #logger.debug(' ------- update_grade -------')
    #logger.debug('upload_dict' + str(upload_dict))
    # upload_dict{'id': {'pk': 6, 'table': 'grade', 'student_pk': 5, 'studsubj_pk': 10, 'examperiod': 1,
    #                   'mode': 'update', 'mapid': 'grade_6'},
    #             'segrade': 'ww'}

    # FIELDS_GRADE =('studentsubject', 'examperiod', 'pescore', 'cescore',
    #                  'segrade', 'pegrade', 'cegrade', 'pecegrade', 'finalgrade',
    #                  'sepublished', 'pepublished', 'cepublished',
    #                  'modifiedby', 'modifiedat')

    save_changes = False
    recalc_finalgrade = False
    for field, new_value in upload_dict.items():
        if field in ('pescore', 'cescore', 'segrade', 'pegrade', 'cegrade', 'pecegrade'):

# a. get saved_value
            saved_value = getattr(instance, field)

            #logger.debug('field: ' + str(field))
            #logger.debug('new_value: ' + str(new_value))
            #logger.debug('saved_value: ' + str(saved_value))

# - validate new_value
            input_number, validated_value, msg_err = grad_val.validate_input_grade(instance, field, new_value)
            #logger.debug('input_number: ' + str(input_number) + ' ' + str(type(input_number)))
            #logger.debug('validated_value: ' + str(validated_value) + ' ' + str(type(validated_value)))
            #logger.debug('msg_err: ' + str(msg_err))
            if msg_err:
                err_dict[field] = msg_err
            else:
# 2. save changes
                if validated_value != saved_value:
                    # c. save field if changed and no_error
                    setattr(instance, field, validated_value)
                    save_changes = True
                    recalc_finalgrade = True
                else:
                    err_dict[field] = msg_err

# - save changes in fields 'se_status', 'pe_status', 'ce_status'
        elif field in ('se_status', 'pe_status', 'ce_status'):
            pass
            # fields are updated in GradeApproveView

# 3. save changes in fields 'namefirst', 'namelast'
        elif field in ('sepublished', 'pepublished', 'cepublished'):
            pass
            # fields are updated in GradeApproveView

# --- end of for loop ---

# 5. save changes`
    if save_changes:
        if recalc_finalgrade:
            calc_final.calc_final_grade(instance)

        instance.save(request=request)
        #logger.debug('The changes have been saved' + str(instance))
        """
        try:
            instance.save(request=request)
            logger.debug('The changes have been saved' + str(instance))
        except:
            err_dict['err_update'] = _('An error occurred. The changes have not been saved.')
        """
# --- end of update_grade


def create_grade_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk, sel_examperiod, append_dict=None,
                       sel_subject_pk=None, grade_pk=None):
    # --- create rows of all students of this examyear / school PR2020-12-14
    #logger.debug(' ----- create_grade_rows -----')

    sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk, 'depbase_id': sel_depbase_pk, 'experiod': sel_examperiod}
    #logger.debug('sql_keys: ' + str(sql_keys))

    sql_list = ["SELECT grade.id,  studsubj.id AS studsubj_id, studsubj.schemeitem_id, studsubj.cluster_id,",
        "CONCAT('grade_', grade.id::TEXT) AS mapid, 'grade' AS table,",

        "stud.id AS student_id, stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
        "stud.iseveningstudent, ey.locked AS ey_locked, school.locked AS school_locked, stud.locked AS stud_locked,",
        "school.islexschool,",
        "ey.no_practexam, ey.no_centralexam, ey.combi_reex_allowed, ey.no_exemption_ce, ey.no_thirdperiod,",
        "grade.examperiod, grade.pescore, grade.cescore, grade.segrade, grade.pegrade, grade.cegrade,",
        "grade.pecegrade, grade.finalgrade,",

        "se_status, se_auth1by_id, grade.se_auth2by_id, grade.se_auth3by_id, grade.se_published_id,",
        "pe_status, pe_auth1by_id, grade.pe_auth2by_id, grade.pe_auth3by_id, grade.pe_published_id,",
        "ce_status, ce_auth1by_id, grade.ce_auth2by_id, grade.ce_auth3by_id, grade.ce_published_id,",

        "norm.scalelength_ce, norm.scalelength_reex, norm.scalelength_pe,",
        "si.subject_id, si.subjecttype_id, si.gradetype,",
        "si.gradetype, si.weight_se, si.weight_ce, si.is_mandatory, si.is_combi, si.extra_count_allowed,",
        "si.extra_nocount_allowed, si.elective_combi_allowed, si.has_practexam,",
        "subj.name AS subj_name, subjbase.code AS subj_code",

        "FROM students_grade AS grade",
        "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grade.studentsubject_id)",

        "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
        "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
        "LEFT JOIN subjects_norm AS norm ON (norm.id = si.norm_id)",
        "WHERE ey.id = %(ey_id)s::INT",
        "AND school.base_id = %(sb_id)s::INT",
        "AND dep.base_id = %(depbase_id)s::INT",
        "AND grade.examperiod = %(experiod)s::INT"
        ]

    #logger.debug('grade_pk: ' + str(grade_pk))
    #logger.debug('student_pk: ' + str(student_pk))
    #logger.debug('subject_pk: ' + str(subject_pk))
    if grade_pk:
        # when grade_pk has value: skip other filters
        sql_keys['grade_id'] = grade_pk
        sql_list.append('AND grade.id = %(grade_id)s::INT')
    elif sel_subject_pk:
        sql_keys['subj_id'] = sel_subject_pk
        sql_list.append('AND si.subject_id = %(subj_id)s::INT')
        sql_list.append('ORDER BY LOWER(stud.lastname), LOWER(stud.firstname)')
    else:
        sql_list.append('ORDER BY LOWER(stud.lastname), LOWER(stud.firstname), subjbase.code')
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        grade_rows = sch_mod.dictfetchall(cursor)

# - add full name to rows
    if grade_rows:
        for row in grade_rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = stud_view.lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

# - add messages to student_row, only when only 1 row added (then studsubj_pk has value)
        if grade_pk and append_dict is not None:
            # when sel_student_pk has value there is only 1 row
            row = grade_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    return grade_rows
# --- end of create_grade_rows


def create_published_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk):
    # --- create rows of published records PR2021-01-21
    #logger.debug(' ----- create_grade_rows -----')

    sql_keys = {'ey_id': sel_examyear_pk,
                'sb_id': sel_schoolbase_pk,
                'depbase_id': sel_depbase_pk,
                'mediadir': awpr_settings.MEDIA_DIR}

    sql_list = ["SELECT publ.id, CONCAT('published_', publ.id::TEXT) AS mapid, 'published' AS table,",
        "publ.name, publ.examtype, publ.examperiod, publ.datepublished, publ.filename,",
        "CONCAT(%(mediadir)s, publ.filename) AS filepath,",
        "sb.code AS sb_code, school.name AS school_name, db.code AS db_code, ey.code AS ey_code",

        "FROM students_published AS publ",
        "INNER JOIN schools_school AS school ON (school.id = publ.school_id)",
        "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = publ.department_id)",
        "INNER JOIN schools_departmentbase AS db ON (db.id = dep.base_id)",

        "WHERE ey.id = %(ey_id)s::INT",
        "AND school.base_id = %(sb_id)s::INT",
        "AND dep.base_id = %(depbase_id)s::INT",
        "AND dep.base_id = %(depbase_id)s::INT",
        "ORDER BY publ.datepublished"
        ]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        published_rows = sch_mod.dictfetchall(cursor)

    return published_rows
# --- end of create_grade_rows


def get_status_list_from_status_sum(status_sum):  # PR2021-01-15
    # status_sum:                            117
    # bin:                             0b1110101
    # binary_str:                        1110101
    # binary_str_extended: 000000000000001110101
    # binary_str_cut:            000000001110101
    # binary_str_reversed:       101011100000000
    # status_list: ['1', '0', '1', '0', '1', '1', '1', '0', '0', '0', '0', '0', '0', '0', '0']

    if status_sum is None:
        status_sum = 0
    binary_str = bin(status_sum)[2:]
    binary_str_extended = '00000000000000' + binary_str
    binary_str_cut = binary_str_extended[-15:]
    binary_str_reversed = binary_str_cut[-1::-1]
    status_list = list(binary_str_reversed)
    return status_list
# --- end of get_status_bool_by_index

def get_status_bool_by_index(status_sum, index):  # PR2021-01-15
    status_list = list(bin(status_sum)[-1:1:-1])
    status_bool = False
    if len(status_list) > index and status_list[index] == '1':
        status_bool = True
    return status_bool
# --- end of get_status_bool_by_index


def set_status_sum_by_index(status_sum, index, new_value_bool):  # PR2021-01-15
    #logger.debug(' =============== set_status_sum_by_index ============= ')
    # bin(status_sum): '0b0010111' <class 'str'>   binary string from int
    # bin(status_sum)[-1:1:-1]: '1110100' <class 'str'>     reversed string from binary string, leave out '0b'
    # status_list: ['1', '1', '1', '0', '1', '0', '0']  convert to list

    #logger.debug('status_sum: ' + str(status_sum))
    #logger.debug('index: ' + str(index))
    #logger.debug('new_value_bool: ' + str(new_value_bool))
# - convert status_sum to status_list
    status_list = list(bin(status_sum)[-1:1:-1])
    #logger.debug('status_list: ' + str(status_list))
# - if index > length of list: extend list with zero's
    length = len(status_list)
    if length <= index:
        for i in range(length, index + 1):
            status_list.append('0')
    #logger.debug('extended status_list: ' + str(status_list))

# - replace binary value at index with '1' if new_value_bool = True, else with '0'
    status_list[index] = '1' if new_value_bool else '0'

    #logger.debug('new status_list: ' + str(status_list))
    new_status_str = ''.join(status_list)
    #logger.debug('new new_status_str: ' + str(new_status_str))
    new_status_str_reversed = new_status_str[::-1]
    #logger.debug('new new_status_str_reversed: ' + str(new_status_str_reversed))
# - convert status_list to new_status_sum
    # PR2021-02-06 from https://stackoverflow.com/questions/8928240/convert-base-2-binary-number-string-to-int
    new_status_sum = int(new_status_str_reversed, 2)
    #logger.debug('new_status_sum: ' + str(new_status_sum))

    return new_status_sum
# --- end of set_status_sum_by_index


def create_ex2a(published_instance, sel_examyear, sel_school, sel_department, sel_subject, sel_examperiod, sel_examtype, grade_rows, request):
    logger.debug(' ============= create_ex2a ============= ')
    # --- create ex2a PR2021-01-22

# from https://stackoverflow.com/questions/26274021/simply-save-file-to-folder-in-django
# from https://stackoverflow.com/questions/51139721/django-save-canvas-object-as-a-pdf-file-to-filefield

    try:
        # create PDF
        file_path = ''.join((awpr_settings.STATICFILES_MEDIA_DIR, published_instance.filename))
        file_name = published_instance.name

        logger.debug('filepath: ' + str(file_path))
        logger.debug('file_name: ' + str(file_name))

        canvas = Canvas(file_path)

        canvas.setTitle(file_name)

        grade_exfiles.draw_Ex2A(canvas, sel_examyear, sel_school, sel_department, sel_subject, sel_examperiod, sel_examtype,
                      grade_rows)
        #canvas.drawString(200, 200, 'Examennummer')
        canvas.showPage()
        canvas.save()

        logger.debug('canvas: ' + str(canvas))
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    """
    else:
        cur_platform = platform.system()
        logger.debug('cur_platform: ' + str(cur_platform))
        if cur_platform != 'Windows':
            try:
                # change owner to uaw, see if this works
                # PR2021-02-07 fro m https://www.tutorialspoint.com/How-to-change-the-owner-of-a-file-using-Python
                # https://stackoverflow.com/questions/5994840/how-to-change-the-user-and-group-permissions-for-a-directory-by-name
                # module pwd only available on Unix
                import pwd
                import grp
                import os


                uid = pwd.getpwnam('uaw').pw_uid
                logger.debug('uid: ' + str(uid))

                gid = grp.getgrnam('uaw').gr_gid
                logger.debug('gid: ' + str(gid))

                logger.debug('filepath: ' + str(filepath))
                os.chown(filepath, uid, gid)

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
    """
    #io_file = io.open(filename, encoding="utf-8")

    #io_file = codecs.open(filepath, "r", encoding='utf-8', errors='ignore')
    #logger.debug('io_file: ' + str(io_file) + ' ' + str(type(io_file)))
    #f_file = File(io_file)

    #logger.debug('f_file: ' + str(f_file) + ' ' + str(type(f_file)))
    # published_instance.file.save(filepath, f_file)

    # save form
    # published_instance.save(request=request)

    """
    default fonts in reportlab:
        Courier Courier-Bold Courier-BoldOblique Courier-Oblique 
        Helvetica Helvetica-Bold Helvetica-BoldOblique Helvetica-Oblique 
        Symbol 
        Times-Bold Times-BoldItalic Times-Italic Times-Roman 
        ZapfDingbats 
    """
"""
Django: how save bytes object to models.FileField?
You can try: 
    from django.core.files.base import ContentFile 
    file_data = ContentFile(base64.b64decode(fileData)) 
    object.file.save(file_name,  
    
    from django.core.files.base import ContentFile 
    file_data = ContentFile(base64.b64decode(fileData)) 
    object.file.save(file_name, file_data) 
    
    You can use your file_name with an.m3u extension, and you shall have it. 
"""

#/////////////////////////////////////////////////////////////////
"""
def create_grade_rowsXXX(setting_dict, append_dict, student_pk):
    # --- create rows of all students of this examyear / school PR2020-10-27
    # logger.debug(' =============== create_grade_rows ============= ')

    sel_examyear_pk = setting_dict.get('sel_examyear_pk')
    sel_schoolbase_pk = setting_dict.get('sel_schoolbase_pk')
    sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk}

    sql_list = ["SELECT st.id, st.base_id, st.school_id AS s_id,",
        "st.department_id AS dep_id, st.level_id AS lvl_id, st.sector_id AS sct_id, st.scheme_id,",
        "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",
        "CONCAT('student_', st.id::TEXT) AS mapid,",
        "st.lastname, st.firstname, st.prefix, st.gender,",
        "st.idnumber, st.birthdate, st.birthcountry, st.birthcity,",
        "st.classname, st.examnumber, st.regnumber, st.diplomanumber, st.gradelistnumber,",
        "st.iseveningstudent, st.locked, st.has_reex, st.bis_exam, st.withdrawn,",
        "st.modifiedby_id, st.modifiedat,",
        "SUBSTRING(au.username, 7) AS modby_username",
        "FROM students_student AS st",
        "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
        "LEFT JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
        "LEFT JOIN accounts_user AS au ON (au.id = st.modifiedby_id)",
        "WHERE sch.base_id = %(sb_id)s::INT AND sch.examyear_id = %(ey_id)s::INT "]

    if student_pk:
        # when student_pk has value: skip other filters
        sql_list.append('AND st.id = %(st_id)s::INT')
        sql_keys['st_id'] = student_pk
    else:
        sql_list.append('ORDER BY LOWER(st.lastname), LOWER(st.firstname)')
    sql = ' '.join(sql_list)

    newcursor = connection.cursor()
    newcursor.execute(sql, sql_keys)
    student_rows = sch_mod.dictfetchall(newcursor)

# - add lastname_firstname_initials to rows
    if student_rows:
        for row in student_rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = stud_view.lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

    # - add messages to student_row
    if student_pk and student_rows:
        # when student_pk has value there is only 1 row
        row = student_rows[0]
        if row:
            for key, value in append_dict.items():
                row[key] = value

    return student_rows

# --- end of create_grade_rows
"""

