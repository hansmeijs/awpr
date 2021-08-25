# PR2020-12-03
import tempfile

from django.contrib.auth.decorators import login_required
from django.core.files import File

from django.db.models import Q
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import View

from reportlab.pdfgen.canvas import Canvas

from accounts import views as acc_view

from awpr import constants as c
from awpr import settings as s
from awpr import menus as awpr_menu
from awpr import functions as af
from awpr import downloads as dl

from schools import models as sch_mod
from students import models as stud_mod
from students import views as stud_view
from subjects import models as subj_mod
from grades import validators as grad_val, calc_finalgrade as calc_final
from grades import exfiles as grade_exfiles

import json # PR2018-12-03
# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy


# ========  GRADES  =====================================

@method_decorator([login_required], name='dispatch')
class GradeListView(View):  # PR2020-12-03 PR2021-03-25

    def get(self, request):

# - set headerbar parameters PR2018-08-06
        page = 'page_grade'
        headerbar_param = awpr_menu.get_headerbar_param(request, page)

        return render(request, 'grades.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class GradeDownloadGradeIconsView(View):  # PR2021-04-30

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeDownloadGradeIconsView ============= ')

        download_wrap = {}
        if request.user and request.user.country and request.user.schoolbase:

# - get selected examyear, school and department from usersettings
            # TOD was: sel_examyear, sel_school, sel_department, is_locked, \
                # examyear_published, school_activated, requsr_same_schoolNIU = \
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
            dl.get_selected_ey_school_dep_from_usersetting(request)

# - get selected examperiod, examtype, subject_pk from usersettings
            sel_examperiod, sel_examtype, sel_subject_pk = dl.get_selected_examperiod_examtype_from_usersetting(request)

            if logging_on:
                logger.debug('sel_examperiod: ' + str(sel_examperiod))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))

            grade_note_icon_rows = create_grade_note_icon_rows(
                sel_examyear_pk=sel_examyear.pk,
                sel_schoolbase_pk=sel_school.base_id,
                sel_depbase_pk=sel_department.base_id,
                sel_examperiod=sel_examperiod,
                studsubj_pk=None,
                request=request)
            if grade_note_icon_rows:
                download_wrap['grade_note_icon_rows'] = grade_note_icon_rows
                
            #grade_stat_icon_rows = create_grade_stat_icon_rows(
            #    sel_examyear_pk=sel_examyear.pk,
            #    sel_schoolbase_pk=sel_school.base_id,
           #     sel_depbase_pk=sel_department.base_id,
            #    sel_examperiod=sel_examperiod,
           #     request=request)

            #if grade_stat_icon_rows:
            #    download_wrap['grade_stat_icon_rows'] = grade_stat_icon_rows
        # - return update_wrap
        return HttpResponse(json.dumps(download_wrap, cls=af.LazyEncoder))

# - end of GradeDownloadGradeIconsView


########################################
@method_decorator([login_required], name='dispatch')
class GradeApproveView(View):  # PR2021-01-19

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeApproveView ============= ')
        # function creates, deletes and updates grade records of current studentsubject PR2020-11-21
        update_wrap = {}

        #<PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

            permit_list, requsr_usergroups_list = acc_view.get_userpermit_list('page_grade', req_user)

            is_auth1 = 'auth1' in requsr_usergroups_list
            is_auth2 = 'auth2' in requsr_usergroups_list
            is_auth3 = 'auth3' in requsr_usergroups_list
            # TODO auth4
            msg_dict = {}
            has_permit = False
            requsr_auth = None
            status_index = None
            # msg_err is made on client side. Here: just skip if user has no or multiple functions
            if is_auth1 + is_auth2 + is_auth3 == 1:
                if is_auth1:
                    requsr_auth = 'auth1'
                    status_index = 1
                elif is_auth2:
                    requsr_auth = 'auth2'
                    status_index = 2
                elif is_auth3:
                    requsr_auth = 'auth3'
                    status_index = 3
            if requsr_auth:
                has_permit = 'approve_grade' in permit_list

            if logging_on:
                logger.debug('requsr_auth:  ' + str(requsr_auth))
                logger.debug('has_permit   ' + str(has_permit))

            if has_permit:
    # -  get user_lang
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

    # - get upload_dict from request.POST
                upload_json = request.POST.get('upload', None)
                if upload_json:
                    upload_dict = json.loads(upload_json)

    # - get selected mode. Modes are 'approve' 'submit_test' 'submit_submit', 'reset'
                    mode = upload_dict.get('mode')
                    is_approve = True if mode in ('approve_test', 'approve_submit', 'approve_reset') else False
                    is_submit = True if mode in ('submit_test', 'submit_submit') else False
                    is_reset = True if mode == 'approve_reset' else False
                    is_test = True if mode in ('approve_test', 'submit_test') else False

    # - get status_index (1 = President, 2 = Secretary, 3 = Commissioner)
                    # PR2021-03-27 status_index is taken from requsr_usergroups_list, not from upload_dict
                    #  function may have changed if gradepage is not refreshed in time)
                    #  was: status_index = upload_dict.get('status_index')

                    # get status_bool_at_index from mode, not from upload_dict
                    # was: status_bool_at_index = upload_dict.get('status_bool_at_index')
                    status_bool_at_index = not is_reset

                    if logging_on:
                        logger.debug('upload_dict' + str(upload_dict))
                        logger.debug('mode: ' + str(mode))
                        logger.debug('status_index: ' + str(status_index))
                        logger.debug('status_bool_at_index: ' + str(status_bool_at_index))

    # - get selected examyear, school and department from usersettings
                    sel_examyear, sel_school, sel_department, is_locked, \
                        examyear_published, school_activated, requsr_same_schoolNIU = \
                            dl.get_selected_ey_school_dep_from_usersetting(request)

    # - get selected examperiod from usersetting
                    sel_examperiod = None
                    selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                    if selected_dict:
                        sel_examperiod = selected_dict.get(c.KEY_SEL_EXAMPERIOD)

    # - get selected grade from upload_dict - only if clicked on a grade tblRow
                    grade_pk = upload_dict.get('grade_pk')
                    if logging_on:
                        logger.debug('grade_pk: ' + str(grade_pk))

    # - if  grade_pk has value: get sel_examtype from upload_dict instead of from settings
                    sel_subject_pk = None
                    if grade_pk:
                        sel_examtype = upload_dict.get('examtype')
                    else:

    # - if  grade_pk has no value: get selected examperiod, examtype and subject_pk from usersettings
                        # update usersetting if new values in upload_dict
                        new_examtype = upload_dict.get('examtype')
                        new_subject_pk = upload_dict.get('subject_pk')
                        if new_examtype or new_subject_pk:
                            new_setting_dict = {}
                            if new_examtype:
                                new_setting_dict[c.KEY_SEL_EXAMTYPE] = new_examtype
                            if new_subject_pk:
                                new_setting_dict[c.KEY_SEL_SUBJECT_PK] = new_subject_pk

                            saved_setting_dict = req_user.set_usersetting_from_upload_subdict(c.KEY_SELECTED_PK, new_setting_dict, request)

                            if logging_on:
                                logger.debug('new_examtype: ' + str(new_examtype))
                                logger.debug('new_subject_pk: ' + str(new_subject_pk))
                                logger.debug('saved_setting_dict: ' + str(saved_setting_dict))

                        sel_examperiodNIU, sel_examtype, sel_subject_pk = \
                            dl.get_selected_examperiod_examtype_from_usersetting(request)

                    if logging_on:
                        logger.debug('sel_examtype:   ' + str(sel_examtype))
                        logger.debug('sel_examperiod: ' + str(sel_examperiod))

                    if sel_examyear and sel_school and sel_department and sel_examperiod and sel_examtype:

# +++ get selected grade_rows
                        crit = Q(studentsubject__student__school=sel_school) & \
                               Q(studentsubject__student__department=sel_department) & \
                               Q(examperiod=sel_examperiod)
                        if grade_pk:
                            crit.add(Q(pk=grade_pk), crit.connector)
                        elif sel_subject_pk:
                            crit.add(Q(studentsubject__schemeitem__subject_id=sel_subject_pk), crit.connector)
                        row_count = stud_mod.Grade.objects.filter(crit).count()

                        if logging_on:
                            logger.debug('grade_pk:       ' + str(grade_pk))
                            logger.debug('sel_subject_pk: ' + str(sel_subject_pk))
                            logger.debug('row_count:      ' + str(row_count))

                        grades = stud_mod.Grade.objects.filter(crit).order_by('studentsubject__student__lastname', 'studentsubject__student__firstname')

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

# +++ create new published_instance.
                            # only save it when it is not a test
                            # file_name will be added after creating Ex-form
                            published_instance = None
                            if is_submit and not is_test:
                                now_arr = upload_dict.get('now_arr')
                                published_instance = create_published_instance(sel_examyear, sel_school, sel_department, sel_examtype, sel_examperiod, sel_subject_pk, is_test, now_arr, request)

# +++++ loop through  grades
                            grade_rows = []
                            for grade in grades:
                                if logging_on:
                                    logger.debug('----- grade: ' + str(grade))

                                msg_dict['count'] += 1
                                if is_approve:
                                    approve_grade(grade, sel_examtype, requsr_auth, status_index, is_test, is_reset, msg_dict, request)
                                elif is_submit:
                                    submit_grade(grade, sel_examtype, is_test, published_instance, msg_dict, request)

    # - add update_dict to update_wrap
                                if grade:
                                    append_dict = {}
                                    rows = create_grade_rows(
                                        sel_examyear_pk=sel_examyear.pk,
                                        sel_schoolbase_pk=sel_school.base_id,
                                        sel_depbase_pk=sel_department.base_id,
                                        sel_examperiod=sel_examperiod,
                                        request=request,
                                        append_dict=append_dict,
                                        grade_pk=grade.pk)
                                    if rows:
                                        # PR2021-06-01 debug. Remove key 'note_status', otherwise it will erase not icon when refreshing this row
                                        row = rows[0]
                                        row.pop('note_status')
                                        grade_rows.append(row)
# +++++  end of loop through  grades

                            row_count = len(grade_rows)
                            if logging_on:
                                logger.debug('row_count: ' + str(row_count))
                            if not row_count:
                                msg_dict['count_text'] = str(
                                    _("The selection contains %(val)s.") % {'val': get_grade_text(0)})
                                if logging_on:
                                    logger.debug('msg_dict: ' + str(msg_dict))
                            else:

                                if is_submit and not is_test:
                                    sel_subject = subj_mod.Subject.objects.get_or_none(
                                        pk=sel_subject_pk,
                                        examyear=sel_examyear
                                    )
                                    create_ex2a(
                                        published_instance=published_instance,
                                        sel_examyear=sel_examyear,
                                        sel_school=sel_school,
                                        sel_department=sel_department,
                                        sel_subject=sel_subject,
                                        sel_examperiod=sel_examperiod,
                                        sel_examtype=sel_examtype,
                                        grade_rows=grade_rows,
                                        request=request)

                                    update_wrap['updated_published_rows'] = create_published_rows(
                                        sel_examyear_pk=sel_examyear.pk,
                                        sel_schoolbase_pk=sel_school.base_id,
                                        sel_depbase_pk=sel_department.base_id,
                                        published_pk=published_instance.pk
                                    )

                                update_wrap['updated_grade_rows'] = grade_rows

# - create msg_html with info of rows
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
                                        msg_dict['double_approved_text'] = get_approved_text(double_approved) + str(_(', in a different function'))

                                    if already_approved_by_auth:
                                        msg_dict['already_approved_by_auth_text'] = get_approved_text(already_approved_by_auth)

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
            if logging_on:
                logger.debug('msg_dict:    ' + str(msg_dict))

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of GradeApproveView


def create_published_instance(sel_examyear, sel_school, sel_department, sel_examtype, sel_examperiod, sel_subject_pk, is_test, now_arr, request):  # PR2021-01-21
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

    # PR2021-04-28 get now_formatted from client
    # was:
    #today_iso = today_date.isoformat()
    #now = timezone.now()
    #now_iso = now.isoformat()

    today_date = af.get_date_from_arr(now_arr)

    year_str = str(now_arr[0])
    month_str = ("00" + str(now_arr[1]))[-2:]
    date_str = ("00" + str(now_arr[2]))[-2:]
    hour_str = ("00" + str(now_arr[3]))[-2:]
    minute_str = ("00" +str( now_arr[4]))[-2:]
    now_formatted = ''.join([year_str, "-", month_str, "-", date_str, " ", hour_str, "u", minute_str])

    # TODO add level if it is filtered on those fields
    file_name = ' '.join(('Ex2A', school_code, school_abbrev, depbase_code, examtype_caption, subject_code, now_formatted))
    # skip school_abbrev if total file_name is too long
    if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
        file_name = ' '.join(('Ex2A', school_code, depbase_code, examtype_caption, subject_code, now_formatted))
    # if total file_name is still too long: cut off
    if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
        file_name = file_name[0:c.MAX_LENGTH_FIRSTLASTNAME]
    file_name += '.pdf'

    published_instance = sch_mod.Published(
        school=sel_school,
        department=sel_department,
        examtype=sel_examtype,
        examperiod=sel_examperiod,
        name=file_name,
        datepublished=today_date)
    # Note: filefield 'file' gets value on creating Ex form
    if not is_test:

        # PR2021-08-07 changed to file_dir = 'country/examyear/published/'
        # this one gives path:awpmedia/awpmedia/media/cur/2022/published
        country_abbrev = sel_examyear.country.abbrev.lower()
        examyear_str = str(sel_examyear.code)
        file_dir = '/'.join((country_abbrev, examyear_str, 'exfiles'))
        file_path = '/'.join((file_dir, published_instance.filename))
        file_name = published_instance.name

        published_instance.filename = file_name + '.pdf'
        published_instance.save(request=request)
        logger.debug('published_instance.saved: ' + str(published_instance))

    return published_instance
# - end of create_published_instance


def get_grade_text(count):
    return _('no grades') if not count else _('1 grade') if count == 1 else str(count) + str(_(' grades'))


def get_grades_are_text(count):
    return _('no grades are') if not count else _('1 grade is') if count == 1 else str(count) + str(_(' grades are'))


def get_approved_text(count):
    msg_text = None
    if count == 1:
        msg_text = _(' - 1 grade is already approved')
    else:
        msg_text = ' - ' + str(count) + str(_(' grades are already approved'))
    return msg_text


def approve_grade(grade, sel_examtype, requsr_auth, status_index, is_test, is_reset, msg_dict, request):  # PR2021-01-19
    # status_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
    logging_on = s.LOGGING_ON
    if logging_on:

        logger.debug('----- approve_grade -----')
        logger.debug('sel_examtype: ' + str(sel_examtype))
        logger.debug('requsr_auth:  ' + str(requsr_auth))
        logger.debug('is_reset:     ' + str(is_reset))

    if grade and sel_examtype and sel_examtype in ('se', 'pe', 'ce'):
        req_user = request.user

# - skip if this grade / examtype is already published
        published = getattr(grade, sel_examtype + '_published')
        if logging_on:
            logger.debug('published:    ' + str(published))

        if published:
            msg_dict['already_published'] += 1
        else:

# skip if this grade has no value
            grade_value = getattr(grade, sel_examtype + 'grade')
            score_value = None
            if sel_examtype in ('pe', 'ce'):
                score_value = getattr(grade, sel_examtype + 'score')
            no_value = grade_value is None and score_value is None
            if logging_on:
                logger.debug('no_value:     ' + str(no_value))

            if no_value:
                msg_dict['no_value'] += 1
            else:
                locked_field = sel_examtype + '_locked'
                requsr_authby_field = sel_examtype + '_' + requsr_auth + 'by'

# - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved
                auth1by = getattr(grade, sel_examtype + '_auth1by')
                auth2by = getattr(grade, sel_examtype + '_auth2by')
                auth3by = getattr(grade, sel_examtype + '_auth3by')
                if logging_on:
                    logger.debug('requsr_authby_field: ' + str(requsr_authby_field))
                    logger.debug('auth1by:      ' + str(auth1by))
                    logger.debug('auth2by:      ' + str(auth2by))
                    logger.debug('auth3by:      ' + str(auth3by))

                double_approved = False
                save_changes = False

# - remove  authby when is_reset
                if is_reset:
                    setattr(grade, requsr_authby_field, None)
                    msg_dict['reset'] += 1

# - make locked false, only if no other approvals
                    # get value of _auth1by again, to catch updated value
                    auth1by = getattr(grade, sel_examtype + '_auth1by')
                    auth2by = getattr(grade, sel_examtype + '_auth2by')
                    auth3by = getattr(grade, sel_examtype + '_auth3by')

                    if auth1by is None and auth2by is None and auth3by is None:
                        setattr(grade, locked_field, False)
                    save_changes = True
                else:

# - skip if this grade is already approved
                    requsr_authby_value = getattr(grade, requsr_authby_field)
                    requsr_authby_field_already_approved = True if requsr_authby_value else False
                    if logging_on:
                        logger.debug('requsr_authby_field_already_approved: ' + str(requsr_authby_field_already_approved))
                    if requsr_authby_field_already_approved:
                        msg_dict['already_approved_by_auth'] += 1
                    else:

# - skip if this author (like 'president') has already approved this grade
            # under a different permit (like 'secretary' or 'commissioner')
                        logger.debug('>>>>>>>>>> requsr_auth: ' + str(requsr_auth))
                        logger.debug('>>>>>>>>>> req_user: ' + str(req_user))
                        logger.debug('>>>>>>>>>> auth1by: ' + str(auth1by))
                        logger.debug('>>>>>>>>>> auth2by: ' + str(auth2by))
                        logger.debug('>>>>>>>>>> auth3by: ' + str(auth3by))
                        if requsr_auth == 'auth1':
                            double_approved = (auth2by and auth2by == req_user) or (auth3by and auth3by == req_user)
                        elif requsr_auth == 'auth2':
                            double_approved = (auth1by and auth1by == req_user) or (auth3by and auth3by == req_user)
                        elif requsr_auth == 'auth3':
                            double_approved = (auth1by and auth1by == req_user) or (auth2by and auth2by == req_user)
                        if logging_on:
                            logger.debug('double_approved: ' + str(double_approved))

                        if double_approved:
                            msg_dict['double_approved'] += 1
                        else:
                            setattr(grade, requsr_authby_field, req_user)
                            # lock grade
                            setattr(grade, locked_field, True)

                            save_changes = True
                            if logging_on:
                                logger.debug('save_changes: ' + str(save_changes))

# - set value of requsr_authby_field
                if save_changes:
                    if is_test:
                        msg_dict['committed'] += 1
                    else:
                        msg_dict['saved'] += 1

                        saved_status_sum = getattr(grade, sel_examtype + '_status')

                        new_value_bool = True if not is_reset else False
                        new_status_sum = af.set_status_sum_by_index(saved_status_sum, status_index, new_value_bool)

                        setattr(grade, sel_examtype + '_status', new_status_sum)

                        if logging_on:
                            logger.debug('is_reset:         ' + str(is_reset))
                            logger.debug('status_index:     ' + str(status_index))
                            logger.debug('saved_status_sum: ' + str(saved_status_sum))
                            logger.debug('new_status_sum:   ' + str(new_status_sum))

    # - save changes
                        grade.save(request=request)
# - end of approve_grade

def submit_grade(grade, sel_examtype, is_test, published_instance, msg_dict, request):  # PR2021-01-21
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- submit_grade -----')

    if grade and sel_examtype and sel_examtype in ('se', 'pe', 'ce'):

# - check if this grade / examtype is already published
        published = getattr(grade, sel_examtype + '_published')
        if logging_on:
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
            if logging_on:
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
                if logging_on:
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
                    if logging_on:
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

                            status_index = 4  # c.STATUS_05_SUBMITTED # STATUS_05_SUBMITTED = 32
                            saved_status_sum = getattr(grade, sel_examtype + '_status')
                            new_value_bool = True
                            new_status_sum = af.set_status_sum_by_index(saved_status_sum, status_index, new_value_bool)

                            if logging_on:
                                logger.debug('saved_status_sum: ' + str(saved_status_sum))
                                logger.debug('status_index: ' + str(status_index))
                                logger.debug('new_status_sum: ' + str(new_status_sum))
                                setattr(grade, sel_examtype + '_status', new_status_sum)
# - save changes
                            grade.save(request=request)
# - end of approve_grade

# - end of submit_grade

@method_decorator([login_required], name='dispatch')
class GradeUploadView(View):  # PR2020-12-16 PR2021-01-15

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= GradeUploadView ============= ')
        # function creates, deletes and updates grade records of current studentsubject PR2020-11-21
        
        update_wrap = {}
        err_html = ''

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

        has_permit = False
        if request.user and request.user.country and request.user.schoolbase:
            permit_list, requsr_usergroups_listNIU = acc_view.get_userpermit_list('page_grade', request.user)
            has_permit = 'permit_crud' in permit_list

            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('requsr_usergroups_listNIU: ' + str(requsr_usergroups_listNIU))
                logger.debug('has_permit: ' + str(has_permit))

        if not has_permit:
            err_html = _("You don't have permission to perform this action.")
        else:
        # - TODO when deleting: return warning when subject grades have values

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))
# - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)


# - get select
                # ed examperiod and examtype from upload_dict
                # don't get it from usersettings, get it from upload_dict instead
                # was: sel_examperiod, sel_examtype, sel_subject_pkNIU = dl.get_selected_examperiod_examtype_from_usersetting(request)
                mode = upload_dict.get('mode')
                examperiod_int = upload_dict.get('examperiod')
                grade_pk = upload_dict.get('grade_pk')
                return_grades_with_exam = upload_dict.get('return_grades_with_exam', False)

# - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                student = None
                # is_locked: either country, examyear or school is locked
                # sel_department only has value when sel_examyear and sel_school have value
                if not may_edit:
                    err_list = []
                    if not sel_examyear.published:
                        err_list.append(str(_('This examyear is not published yet.')))
                    if sel_examyear.is_locked:
                        err_list.append(str(_('This examyear is locked.')))
                    if not sel_school.activated:
                        err_list.append(str(_('The school has not activated this examyear yet.')))
                    if sel_school.is_locked:
                        err_list.append(str(_('This school is locked.')))
                    if request.user.schoolbase is None or sel_school.base != request.user.schoolbase:
                        err_list.append(str(_('Only users of this school are allowed to make changes.')))
                    if not sel_department:
                        err_list.append(str(_('There is no department selected.')))
                    if err_list:
                        err_list.append(str(_('You cannot make changes.')))
                        err_html = '<br>'.join(err_list)
                else:
                    student_pk = upload_dict.get('student_pk')
                    student = stud_mod.Student.objects.get_or_none(
                        id=student_pk,
                        school=sel_school,
                        department=sel_department,
                        locked=False
                    )
                    if logging_on:
                        logger.debug('student_pk: ' + str(student_pk))
                        logger.debug('sel_school: ' + str(sel_school))
                        logger.debug('sel_department: ' + str(sel_department))
                        logger.debug('student: ' + str(student))
                # TODO msgerr when student is locked
                if student:
                    error_dict = {}

# - get current grade
                    grade = stud_mod.Grade.objects.get_or_none(
                        id=grade_pk,
                        studentsubject__student=student,
                        examperiod=examperiod_int
                    )
                    if logging_on:
                        logger.debug('grade: ' + str(grade))
                    if grade:

# +++ update existing grade - also when grade is created - grade is None when deleted
                        if mode == 'update':
                            update_grade_instance(grade, upload_dict, error_dict, logging_on, request)

# - add update_dict to update_wrap
                        grade_rows = []


                        if return_grades_with_exam:
                            rows = create_grade_with_exam_rows(
                                sel_examyear_pk=sel_examyear.pk,
                                sel_schoolbase_pk=sel_school.base_id,
                                sel_depbase_pk=sel_department.base_id,
                                sel_examperiod=grade.examperiod,
                                request=request,
                                grade_pk=grade.pk
                            )
                        else:
                            # TODO check value of error_dict
                            append_dict = {}
                            if error_dict:
                                append_dict['error'] = error_dict

                            rows = create_grade_rows(
                                sel_examyear_pk=sel_examyear.pk,
                                sel_schoolbase_pk=sel_school.base_id,
                                sel_depbase_pk=sel_department.base_id,
                                sel_examperiod=grade.examperiod,
                                request=request,
                                append_dict=append_dict,
                                grade_pk=grade.pk)
                        if rows:
                            row = rows[0]
                            if row:
                                grade_rows.append(row)
                        if grade_rows:
                            update_wrap['updated_grade_rows'] = grade_rows
        if err_html:
            update_wrap['err_html'] = err_html
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of GradeUploadView


#######################################################
def update_grade_instance(instance, upload_dict, err_dict, logging_on, request):
    # --- update existing grade PR2020-12-16
    # add new values to update_dict (don't reset update_dict, it has values)
    if logging_on:
        logger.debug(' ------- update_grade_instance -------')
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

        if field in ('pescore', 'cescore', 'segrade', 'pegrade', 'cegrade'):

# a. get saved_value
            saved_value = getattr(instance, field)

# - validate new_value
            validated_value, err_msg = grad_val.validate_input_grade(instance, field, new_value, logging_on)

            if err_msg:
                err_dict[field] = err_msg
            else:
# 2. save changes if changed and no_error
                if validated_value != saved_value:
                    setattr(instance, field, validated_value)
                    save_changes = True
                    recalc_finalgrade = True
                else:
                    err_dict[field] = err_msg
            if logging_on:
                logger.debug('field          : ' + str(field))
                logger.debug('new_value      : ' + str(new_value))
                logger.debug('validated_value: ' + str(validated_value) + ' ' + str(type(validated_value)))
                logger.debug('saved_value    : ' + str(saved_value))
                logger.debug('err_msg        : ' + str(err_msg))
                logger.debug('recalc_final   : ' + str(recalc_finalgrade))

# - save changes in field 'exam'
        elif field == 'exam_pk':
            db_field = 'exam'
            saved_exam = getattr(instance, db_field)
            if logging_on:
                logger.debug('field: ' + str(field) + ' new_value: ' + str(new_value))
                logger.debug('saved_exam: ' + str(saved_exam) + ' ' + str(type(saved_exam)))
            exam = None
            if new_value:
                exam = subj_mod.Exam.objects.get_or_none(pk=new_value)
            if logging_on:
                logger.debug('exam: ' + str(exam) + ' ' + str(type(exam)))
            save_exam = False
            if exam:
                save_exam = (saved_exam is None) or (exam.pk != saved_exam.pk)
            else:
                save_exam = (saved_exam is not None)
            if save_exam:
                setattr(instance, db_field, exam)
                save_changes = True
                if logging_on:
                    logger.debug('save_exam: ' + str(save_exam) + ' ' + str(type(save_exam)))

# - save changes in field 'assignment'
        elif field == 'answers':
            saved_value = getattr(instance, field)
            if logging_on:
                logger.debug('field: ' + str(field) + ' new_value: ' + str(new_value))
                logger.debug('saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
    # 2. save changes if changed and no_error
            if new_value != saved_value:
                setattr(instance, field, new_value)
                setattr(instance, 'blanks', upload_dict.get('blanks'))
                save_changes = True
                if logging_on:
                    logger.debug('save_changes: ' + str(save_changes))

# - save changes in field 'blanks'
        elif field == 'blanks':
            saved_value = getattr(instance, field)
            # 2. save changes if changed and no_error
            if new_value != saved_value:
                setattr(instance, field, new_value)
                save_changes = True

        # - save changes in fields 'xx_status' and 'xxpublished'
        elif field in ('se_status', 'pe_status', 'ce_status', 'sepublished', 'pepublished', 'cepublished'):
            pass
            # fields are updated in GradeApproveView

# --- end of for loop ---

# 5. save changes`
    if save_changes:
        if recalc_finalgrade:
            calc_final.update_finalgrade(instance, logging_on)

        try:
            instance.save(request=request)
            if logging_on:
                logger.debug('The changes have been saved.')
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            err_msg = _('An error occurred. The changes have not been saved.')
            err_dict['err_update'] = err_msg
            if logging_on:
                logger.debug(err_msg)
# --- end of update_grade_instance


def create_grade_note_icon_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk, sel_examperiod, studsubj_pk, request):

    # --- calculate the note- and status icons to be show in the grade rows  PR2021-04-20
    logger.debug(' ----- create_grade_note_icon_rows -----')

    grade_note_icon_rows = []

    if sel_examyear_pk and sel_schoolbase_pk and sel_depbase_pk and request.user and request.user.schoolbase_id:
        # req_user can only view nots of his wwn organization

        # only role_school and same_school can view grades that are not published, PR2021-04-29
        # by filtering subquery : (intern_schoolbase_id = requsr_sb_id) OR ssn.intern_schoolbase_id IS NULL)
        # filter on exyr, schoolbase, depbase, examperiod is in main query
        requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase_pk)

        sql_keys = {
            'ey_id': sel_examyear_pk,
            'sb_id': sel_schoolbase_pk,
            'db_id': sel_depbase_pk,
            'ex_per': sel_examperiod,
            'requsr_sb_id': request.user.schoolbase_id}

        logger.debug('sql_keys: ' + str(sql_keys))
        logger.debug('requsr_same_school: ' + str(requsr_same_school))

        sql_ssn_list = ["SELECT ssn.studentsubject_id AS studsubj_id, MAX(ssn.note_status) AS max_note_status",
                    "FROM students_studentsubjectnote AS ssn",
                    "WHERE (ssn.intern_schoolbase_id = %(requsr_sb_id)s::INT OR ssn.intern_schoolbase_id IS NULL)",
                    "GROUP BY ssn.studentsubject_id"]
        sql_ssn = ' '.join(sql_ssn_list)

        sql_list = ["SELECT studsubj.id AS studsubj_id,",
                    "CONCAT('grade_', grd.id::TEXT) AS mapid,",
                    "ssn.max_note_status AS note_status",
                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                    "INNER JOIN (", sql_ssn, ") AS ssn ON (ssn.studsubj_id = studsubj.id)",
                    "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
                    "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                    "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
                    "WHERE sch.examyear_id = %(ey_id)s::INT",
                    "AND sch.base_id = %(sb_id)s::INT",
                    "AND dep.base_id = %(db_id)s::INT",
                    "AND grd.examperiod = %(ex_per)s::INT"
                    ]
        if studsubj_pk:
            sql_keys['studsubj_id'] = studsubj_pk
            sql_list.append("AND studsubj.id = %(studsubj_id)s::INT")
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            grade_note_icon_rows = af.dictfetchall(cursor)

    return grade_note_icon_rows
# --- end of create_grade_note_icon_rows

def create_grade_stat_icon_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk, sel_examperiod, request):
    # --- calculate the note- and status icons to be show in the grade rows  PR2021-05-01
    #logger.debug(' ----- create_grade_stat_icon_rows -----')

    grade_stat_icon_rows = []

    if sel_examyear_pk and sel_schoolbase_pk and sel_depbase_pk and request.user and request.user.schoolbase_id:
        # req_user can only view nots of his wwn organization

        # only role_school and same_school can view grades that are not published, PR2021-04-29
        requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase_pk)
        sql_keys = {
            'ey_id': sel_examyear_pk,
            'sb_id': sel_schoolbase_pk,
            'db_id': sel_depbase_pk,
            'ex_per': sel_examperiod,
            'requsr_sb_id': request.user.schoolbase_id}

        #logger.debug('sql_keys: ' + str(sql_keys))
        #logger.debug('requsr_same_school: ' + str(requsr_same_school))

        if requsr_same_school:
            grades = "segrade, srgrade, sesrgrade, cescore, cegrade, pescore, pegrade, pecegrade,"
            final_grade = "grd.finalgrade AS finalgrade,"
            status = "se_status, sr_status, pe_status, ce_status,"
        else:
            grades = ' '.join([
                "CASE WHEN grd.se_published_id IS NOT NULL THEN grd.segrade ELSE NULL END AS segrade,",
                "CASE WHEN grd.sr_published_id IS NOT NULL THEN grd.srgrade ELSE NULL END AS srgrade,",
                "CASE WHEN grd.sr_published_id IS NOT NULL THEN grd.sesrgrade ELSE NULL END AS sesrgrade,",

                "CASE WHEN grd.ce_published_id IS NOT NULL THEN grd.cescore ELSE NULL END AS cescore,",
                "CASE WHEN grd.ce_published_id IS NOT NULL THEN grd.cegrade ELSE NULL END AS cegrade,",

                "CASE WHEN grd.pe_published_id IS NOT NULL THEN grd.pescore ELSE NULL END AS pescore,",
                "CASE WHEN grd.pe_published_id IS NOT NULL THEN grd.pegrade ELSE NULL END AS pegrade,",
                "CASE WHEN grd.pe_published_id IS NOT NULL THEN grd.pecegrade ELSE NULL END AS pecegrade,"
            ])

            # check is to determine if final_grade must be shown. Check is True when weight = 0 or not has_practexam
            final_check_se = '(CASE WHEN si.weight_se > 0 THEN (CASE WHEN grd.se_published_id IS NOT NULL THEN TRUE ELSE FALSE END) ELSE TRUE END)'
            final_check_ce = '(CASE WHEN si.weight_ce > 0 THEN (CASE WHEN grd.ce_published_id IS NOT NULL THEN TRUE ELSE FALSE END) ELSE TRUE END)'
            final_check_pe = '(CASE WHEN si.has_practexam THEN (CASE WHEN grd.pe_published_id IS NOT NULL THEN TRUE ELSE FALSE END) ELSE TRUE END)'

            final_grade = "CASE WHEN " + final_check_se +  " AND " + final_check_ce + "  AND " + final_check_pe + " THEN grd.finalgrade ELSE NULL END AS finalgrade,"

            status = ' '.join([
                "CASE WHEN grd.se_published_id IS NOT NULL THEN grd.se_status ELSE NULL END AS se_status,",
                "CASE WHEN grd.sr_published_id IS NOT NULL THEN grd.sr_status ELSE NULL END AS sr_status,",
                "CASE WHEN grd.pe_published_id IS NOT NULL THEN grd.pe_status ELSE NULL END AS pe_status,",
                "CASE WHEN grd.ce_published_id IS NOT NULL THEN grd.ce_status ELSE NULL END AS ce_status,"
            ])

        sql_list = [
            "SELECT grd.id, grd.studentsubject_id AS studsubj_id, grd.examperiod,",
            grades, final_grade, status,
            "grd.se_blocked, grd.sr_blocked, grd.pe_blocked, grd.ce_blocked,",
            "si.weight_se, si.weight_ce",
            "FROM students_grade AS grd",
            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
            "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
            "WHERE grd.examperiod = %(ex_per)s::INT",
        ]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            grade_stat_icon_rows = af.dictfetchall(cursor)

    return grade_stat_icon_rows
# --- end of create_grade_stat_icon_rows


def create_grade_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk, sel_examperiod, request, append_dict=None,
                       sel_subject_pk=None, grade_pk=None, auth_dict=None):
    # --- create grade rows of all students of this examyear / school PR2020-12-14

    # note: don't forget to filter deleted = false!! PR2021-03-15
    # grades that are not published are only visible when 'same_school'
    # note_icon is downloaded in separate call

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_grade_rows -----')

    # - only requsr of the same school  can view grades that are not published, PR2021-04-29
    # - also commissioner .TODO: add school to commissioner permit
    requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase_pk)
    requsr_commissioner = (request.user.role == c.ROLE_016_COMM)

    #  add_auth_list is used in Ex form to add name of auth
    add_auth_list = True if auth_dict is not None else False

    sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk,
                'depbase_id': sel_depbase_pk, 'experiod': sel_examperiod}

    # - only when requsr_same_school the not-published grades are visible
    # - also the commissioner
    if requsr_same_school or requsr_commissioner:
        grades = "segrade, srgrade, sesrgrade, cescore, cegrade, pescore, pegrade, pecegrade,"
        final_grade = "grd.finalgrade AS finalgrade,"
        status = "se_status, sr_status, pe_status, ce_status,"
    else:
        grades = ' '.join([
            "CASE WHEN grd.se_published_id IS NOT NULL THEN grd.segrade ELSE NULL END AS segrade,",
            "CASE WHEN grd.sr_published_id IS NOT NULL THEN grd.srgrade ELSE NULL END AS srgrade,",
            "CASE WHEN grd.sr_published_id IS NOT NULL THEN grd.sesrgrade ELSE NULL END AS sesrgrade,",

            "CASE WHEN grd.ce_published_id IS NOT NULL THEN grd.cescore ELSE NULL END AS cescore,",
            "CASE WHEN grd.ce_published_id IS NOT NULL THEN grd.cegrade ELSE NULL END AS cegrade,",

            "CASE WHEN grd.pe_published_id IS NOT NULL THEN grd.pescore ELSE NULL END AS pescore,",
            "CASE WHEN grd.pe_published_id IS NOT NULL THEN grd.pegrade ELSE NULL END AS pegrade,",
            "CASE WHEN grd.pe_published_id IS NOT NULL THEN grd.pecegrade ELSE NULL END AS pecegrade,"
        ])

        # check is to determine if final_grade must be shown. Check is True when weight = 0 or not has_practexam
        final_check_se = '(CASE WHEN si.weight_se > 0 THEN (CASE WHEN grd.se_published_id IS NOT NULL THEN TRUE ELSE FALSE END) ELSE TRUE END)'
        final_check_ce = '(CASE WHEN si.weight_ce > 0 THEN (CASE WHEN grd.ce_published_id IS NOT NULL THEN TRUE ELSE FALSE END) ELSE TRUE END)'
        final_check_pe = '(CASE WHEN si.has_practexam THEN (CASE WHEN grd.pe_published_id IS NOT NULL THEN TRUE ELSE FALSE END) ELSE TRUE END)'

        final_grade = "CASE WHEN " + final_check_se + " AND " + final_check_ce + "  AND " + final_check_pe + " THEN grd.finalgrade ELSE NULL END AS finalgrade,"

        status = ' '.join([
            "CASE WHEN grd.se_published_id IS NOT NULL THEN grd.se_status ELSE NULL END AS se_status,",
            "CASE WHEN grd.sr_published_id IS NOT NULL THEN grd.sr_status ELSE NULL END AS sr_status,",
            "CASE WHEN grd.pe_published_id IS NOT NULL THEN grd.pe_status ELSE NULL END AS pe_status,",
            "CASE WHEN grd.ce_published_id IS NOT NULL THEN grd.ce_status ELSE NULL END AS ce_status,"
        ])

    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    sql_list = ["SELECT grd.id, studsubj.id AS studsubj_id, studsubj.schemeitem_id, studsubj.cluster_id,",
                "CONCAT('grade_', grd.id::TEXT) AS mapid,",
                "stud.id AS student_id, stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
                "stud.level_id AS lvl_id, lvl.abbrev AS lvl_abbrev, stud.sector_id AS sct_id, sct.abbrev AS sct_abbrev,",
                "stud.iseveningstudent, ey.locked AS ey_locked, school.locked AS school_locked, stud.locked AS stud_locked,",
                "school.islexschool,",

                grades, final_grade, status,
                "grd.examperiod,",
                "grd.se_auth1by_id, grd.se_auth2by_id, grd.se_auth3by_id, grd.se_published_id, grd.se_blocked,",
                "grd.sr_auth1by_id, grd.sr_auth2by_id, grd.sr_auth3by_id, grd.sr_published_id, grd.sr_blocked,",
                "grd.pe_auth1by_id, grd.pe_auth2by_id, grd.pe_auth3by_id, grd.pe_published_id, grd.pe_blocked,",
                "grd.ce_auth1by_id, grd.ce_auth2by_id, grd.ce_auth3by_id, grd.ce_published_id, grd.ce_blocked,",

                "si.subject_id, si.subjecttype_id,",
                "si.gradetype, si.weight_se, si.weight_ce, si.is_mandatory, si.is_mand_subj_id, si.is_combi, si.extra_count_allowed,",
                "si.extra_nocount_allowed, si.elective_combi_allowed, si.has_practexam, si.has_pws,",
                "si.is_core_subject, si.is_mvt, si.reex_se_allowed, si.max_reex, si.no_thirdperiod, si.no_exemption_ce,",

                "subj.name AS subj_name, subjbase.code AS subj_code,",
                "NULL AS note_status", # will be filled in after downloading note_status

                "FROM students_grade AS grd",
                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",

                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",

                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "WHERE ey.id = %(ey_id)s::INT",
                "AND school.base_id = %(sb_id)s::INT",
                "AND dep.base_id = %(depbase_id)s::INT",
                "AND NOT grd.tobedeleted",
                "AND NOT studsubj.tobedeleted",

                "AND grd.examperiod = %(experiod)s::INT"
                ]

    if logging_on:
        logger.debug('grade_pk: ' + str(grade_pk))

    # show grades that are not published only when requsr_same_school PR2021-04-29
    if grade_pk:
        # when grade_pk has value: skip other filters
        sql_keys['grade_id'] = grade_pk
        sql_list.append('AND grd.id = %(grade_id)s::INT')
    elif sel_subject_pk:
        sql_keys['subj_id'] = sel_subject_pk
        sql_list.append('AND si.subject_id = %(subj_id)s::INT')
        sql_list.append('ORDER BY LOWER(stud.lastname), LOWER(stud.firstname)')
    else:
        sql_list.append('ORDER BY LOWER(stud.lastname), LOWER(stud.firstname), subjbase.code')
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        grade_rows = af.dictfetchall(cursor)

    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

# - add full name to rows, and array of id's of auth
    if grade_rows:
        # create auth_dict, with lists of each auth
        auth_fields = ('se_auth1by_id', 'se_auth2by_id', 'se_auth3by_id',
                          'sr_auth1by_id', 'sr_auth2by_id', 'sr_auth3by_id',
                          'pe_auth1by_id', 'pe_auth2by_id', 'pe_auth3by_id',
                          'ce_auth1by_id', 'ce_auth2by_id', 'ce_auth3by_id')

        for row in grade_rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            # if auth_id: add to list
            if add_auth_list:
                for field in auth_fields:
                    auth_id = row.get(field)
                    if auth_id:
                        if field not in auth_dict:
                            auth_dict[field] = [auth_id]
                        else:
                            auth_arr = auth_dict.get(field)
                            if auth_id not in auth_arr:
                                auth_arr.append(auth_id)

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

###########################################


def create_grade_with_exam_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk, sel_examperiod, request, grade_pk=None):
    # --- create grade rows of all students of this examyear / school PR2020-12-14

    # note: don't forget to filter deleted = false!! PR2021-03-15
    # grades that are not published are only visible when 'same_school'
    # note_icon is downloaded in separate call

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_grade_with_exam_rows -----')

    # - only requsr of the same school  can view grades that are not published, PR2021-04-29
    # - also commissioner .TODO: add school to commissioner permit
    requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase_pk)

    sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk,
                'depbase_id': sel_depbase_pk, 'experiod': sel_examperiod}

    # - only when requsr_same_school the not-published grades are visible


    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    sub_list = ["SELECT exam.id, ",
                "CONCAT(subjbase.code,",
                "CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' - ', lvl.abbrev) END,",
                "CASE WHEN exam.version IS NULL THEN NULL ELSE CONCAT(' - ', exam.version) END ) AS exam_name, exam.amount",

                "FROM subjects_exam AS exam",
                "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)"
                ]
    sub_exam = ' '.join(sub_list)


    sql_list = ["SELECT grd.id, CONCAT('grade_', grd.id::TEXT) AS mapid,",
                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
                "stud.id AS student_id, stud.lastname, stud.firstname, stud.prefix,",
                "lvl.id AS level_id, lvl.base_id AS levelbase_id, lvl.abbrev AS lvl_abbrev,",
                "subj.id AS subj_id, subjbase.code AS subj_code, subj.name AS subj_name,",
                "studsubj.id AS studsubj_id, sub_exam.exam_name, sub_exam.amount,",
                "grd.exam_id, grd.answers, grd.blanks, grd.answers_published_id",

                "FROM students_grade AS grd",
                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                "LEFT JOIN (", sub_exam, ") AS sub_exam ON (sub_exam.id = grd.exam_id)",

                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",

                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "WHERE ey.id = %(ey_id)s::INT",
                "AND school.base_id = %(sb_id)s::INT",
                "AND dep.base_id = %(depbase_id)s::INT",
                "AND si.ete_exam",
                "AND NOT grd.tobedeleted AND NOT studsubj.tobedeleted",

                "AND grd.examperiod = %(experiod)s::INT"
                ]
    if grade_pk:
        # when grade_pk has value: skip other filters
        sql_keys['grade_id'] = grade_pk
        sql_list.append('AND grd.id = %(grade_id)s::INT')
    else:
    # show grades that are not published only when requsr_same_school PR2021-04-29
        sql_list.append('ORDER BY LOWER(stud.lastname), LOWER(stud.firstname), subjbase.code')
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        grade_rows = af.dictfetchall(cursor)

    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))
        logger.debug('sql: ' + str(sql))

# - add full name to rows, and array of id's of auth
    if grade_rows:
        for row in grade_rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = stud_view.lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

    return grade_rows
# --- end of create_grade_with_exam_rows


###############################################

def create_published_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk, published_pk=None):
    # --- create rows of published records PR2021-01-21
    #logger.debug(' ----- create_grade_rows -----')

    """
    sql_keys = {'ey_id': sel_examyear_pk,
                'sb_id': sel_schoolbase_pk,
                'depbase_id': sel_depbase_pk,
                'mediadir': s.MEDIA_DIR}

    sql_list = ["SELECT publ.id, CONCAT('published_', publ.id::TEXT) AS mapid, 'published' AS table,",
        "publ.name, publ.examtype, publ.examperiod, publ.datepublished, publ.filename,",
        "CONCAT(%(mediadir)s, publ.filename) AS filepath,",
        "sb.code AS sb_code, school.name AS school_name, db.code AS db_code, ey.code AS ey_code",

        "FROM schools_published AS publ",
        "INNER JOIN schools_school AS school ON (school.id = publ.school_id)",
        "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = publ.department_id)",
        "INNER JOIN schools_departmentbase AS db ON (db.id = dep.base_id)",

        "WHERE ey.id = %(ey_id)s::INT",
        "AND school.base_id = %(sb_id)s::INT",
        "AND dep.base_id = %(depbase_id)s::INT",
        "ORDER BY publ.datepublished"
        ]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        published_rows = af.dictfetchall(cursor)
    """
    # can't use sql because of file field
    # +++ get selected grade_rows
    crit = Q(school__base_id=sel_schoolbase_pk) & \
           Q(school__examyear_id=sel_examyear_pk) & \
           Q(department__base_id=sel_depbase_pk)
    # published_pk only has value when called by GradeApproveView. Then it is a created row
    if published_pk:
        crit.add(Q(pk=published_pk), crit.connector)

    rows = sch_mod.Published.objects.filter(crit).order_by('-datepublished')

    published_rows = []
    for row in rows:
        file_name = None
        file_url = None
        if row.file:
            file_name = str(row.file)
            file_url = row.file.url

        dict = {
            'id': row.pk,
            'mapid': 'published_' + str(row.pk),
            'table': 'published',
            'name': row.name,
            'examtype': row.examtype,
            'examperiod': row.examperiod,
            'datepublished': row.datepublished,
            'filename': row.filename,
            'sb_code': row.school.base.code,
            'school_name': row.school.name,
            'db_code': row.department.base.code,
            'ey_code': row.school.examyear.code,
            'file_name': file_name,
            'url': file_url}
        if published_pk:
            dict['created'] = True
        published_rows.append(dict)

    return published_rows
# --- end of create_grade_rows


def create_ex2a(published_instance, sel_examyear, sel_school, sel_department, sel_subject, sel_examperiod, sel_examtype, grade_rows, request):
    logger.debug(' ============= create_ex2a ============= ')
    # --- create ex2a PR2021-01-22

# from https://stackoverflow.com/questions/26274021/simply-save-file-to-folder-in-django
# from https://stackoverflow.com/questions/51139721/django-save-canvas-object-as-a-pdf-file-to-filefield

# maybe this one gives an answer how to save and retrieve pdf from spaces PR2021-03-28
# https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3
    file_path = None
    try:
        # create PDF
        # PR2021-03-17 was:
        #if s.AWS_LOCATION:
            #file_dir = ''.join((s.AWS_LOCATION, '/published/'))
        # this one gave path:awpmedia/awpmedia/media/private/media/private/published
        #if s.AWS_PRIVATE_MEDIA_LOCATION:
        #    # AWS_PRIVATE_MEDIA_LOCATION = 'media/private'
        #    file_dir = ''.join((s.AWS_PRIVATE_MEDIA_LOCATION, '/published/'))
        #else:
        #    # STATICFILES_MEDIA_DIR = os.path.join(BASE_DIR, 'media', 'private', 'published') + '/'
        #    file_dir = s.STATICFILES_MEDIA_DIR

# ---  create file_path
        # PR2021-08-07 changed to file_dir = 'country/examyear/exfiles/'
        # this one gives path:awpmedia/awpmedia/media/cur/2022/exfiles
        country_abbrev = sel_examyear.country.abbrev.lower()
        examyear_str = str(sel_examyear.code)
        file_dir = '/'.join((country_abbrev, examyear_str, 'exfiles'))
        file_path = '/'.join((file_dir, published_instance.filename))
        file_name = published_instance.name

        logger.debug('file_dir: ' + str(file_dir))
        logger.debug('file_name: ' + str(file_name))
        logger.debug('filepath: ' + str(file_path))

        # from https://docs.python.org/3/library/tempfile.html
        temp_file = tempfile.TemporaryFile()

        # was: canvas = Canvas(file_path)
        canvas = Canvas(temp_file)
        canvas.setTitle(file_name)

        grade_exfiles.draw_Ex2A(canvas, sel_examyear, sel_school, sel_department, sel_subject, sel_examperiod, sel_examtype,
                      grade_rows)
        #canvas.drawString(200, 200, 'Examennummer')
        canvas.showPage()
        canvas.save()

        logger.debug('canvas: ' + str(canvas))
        logger.debug('temp_file: ' + str(temp_file))

        if file_path:
            # PR2021-04-28 from: https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3
            # PR2021-04-28 debug decoding error. See https://stackoverflow.com/questions/9233027/unicodedecodeerror-charmap-codec-cant-decode-byte-x-in-position-y-character
            # error: Unicode-objects must be encoded before hashing
            #io_file = codecs.open(filepath, "r", encoding='utf-8', errors='ignore')
            #local_file = open(file_path, encoding="Latin-1", errors="ignore")

            # finally, this one works:   local_file = open(file_path, 'rb')
            # thanks to https://stackoverflow.com/questions/9233027/unicodedecodeerror-charmap-codec-cant-decode-byte-x-in-position-y-character

            # was: local_file = open(file_path, 'rb')
            # was: pdf_file = File(local_file)
            # this works! PR2021-04-29
            pdf_file = File(temp_file)

            published_instance.file.save(file_path, pdf_file)

            logger.debug('file_path: ' + str(file_path))
            # file_path: media/private/published/Ex2A CUR13 ATC Vsbo SE-tv1 cav 2021-04-29 10u11.pdf
            # stored in dir:
            logger.debug('published_instance.file: ' + str(published_instance.file))

# - save form
            published_instance.save(request=request)

    except Exception as e:
       logger.error(getattr(e, 'message', str(e)))
    """
    default fonts in reportlab:
        Courier Courier-Bold Courier-BoldOblique Courier-Oblique 
        Helvetica Helvetica-Bold Helvetica-BoldOblique Helvetica-Oblique 
        Symbol 
        Times-Bold Times-BoldItalic Times-Italic Times-Roman 
        ZapfDingbats 
    """

