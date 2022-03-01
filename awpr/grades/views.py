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
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext_lazy as _
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
from students import functions as stud_fnc
from subjects import models as subj_mod
from subjects import views as subj_vw
from grades import validators as grad_val
from grades import calc_finalgrade as calc_final
from grades import calc_results as calc_res
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
            # may_edit = False when:
            #  - country is locked,
            #  - examyear is not found, not published or locked
            #  - school is not found, not same_school, not activated, or locked
            #  - department is not found, not in user allowed depbase or not in school_depbase
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
            dl.get_selected_ey_school_dep_from_usersetting(request)

# - get selected examperiod, examtype, subject_pk from usersettings
            sel_examperiod, sel_examtype, sel_subjbase_pkNIU = dl.get_selected_experiod_extype_subjbase_from_usersetting(request)

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
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeApproveView ============= ')
        # function creates, deletes and updates grade records of current studentsubject PR2020-11-21
        update_wrap = {}

        #<PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school not locked, examyear is published and school is activated

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

            permit_list, requsr_usergroups_listNIU = acc_view.get_userpermit_list('page_grade', req_user)

            msg_dict = {}

            has_permit = 'permit_approve_grade' in permit_list
            if has_permit:

    # -  get user_lang
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

    # - get upload_dict from request.POST
                upload_json = request.POST.get('upload', None)
                if upload_json:
                    upload_dict = json.loads(upload_json)

                    """
                    upload_dict{'table': 'grade', 'mode': 'approve_save', 'mapid': 'grade_67275', 'field': 'sr_status', 
                                'auth_index': 4, 'auth_bool_at_index': True, 'examtype': 'sr', 'grade_pk': 67275}
                    upload_dict{'table': 'grade', 'mode': 'approve_reset', 'mapid': 'grade_67275',  'field': 'sr_status', 
                                'auth_index': 4, 'auth_bool_at_index': False, 'examtype': 'sr', 'grade_pk': 67275}
                    """

    # - get selected mode. Modes are 'approve' 'submit_test' 'submit_save', 'reset'
                    mode = upload_dict.get('mode')
                    is_approve = True if mode in ('approve_test', 'approve_save', 'approve_reset') else False
                    is_submit = True if mode in ('submit_test', 'submit_save') else False
                    is_reset = True if mode == 'approve_reset' else False
                    is_test = True if mode in ('approve_test', 'submit_test') else False

                    auth_index = upload_dict.get('auth_index')
                    if auth_index:
                        requsr_auth = 'auth' + str(auth_index)

                        # msg_err is made on client side. Here: just skip if user has no or multiple functions

        # - get auth_index (1 = President, 2 = Secretary, 3 = Commissioner, 4 = examinator
                        # PR2021-03-27 auth_index is taken from requsr_usergroups_list, not from upload_dict
                        #  function may have changed if gradepage is not refreshed in time)
                        #  was: auth_index = upload_dict.get('auth_index')
                        # can't do it like this any more. User can have be examinator and pres/secr at the same time
                        # back to upload_dict.get('auth_bool_at_index')

                        # get auth_bool_at_index from mode, not from upload_dict
                        # was: auth_bool_at_index = upload_dict.get('auth_bool_at_index')
                        auth_bool_at_index = not is_reset

                        if logging_on:
                            logger.debug('upload_dict' + str(upload_dict))
                            logger.debug('mode: ' + str(mode))
                            logger.debug('auth_index: ' + str(auth_index))
                            logger.debug('auth_bool_at_index: ' + str(auth_bool_at_index))
                        """
                        upload_dict{'table': 'grade', 'mode': 'approve_save', 'mapid': 'grade_22432', 'field': 'se_status', 'auth_index': 4, 'auth_bool_at_index': True, 'examtype': 'se', 'grade_pk': 22432}
                        """
        # - get selected examyear, school and department from usersettings
                        sel_examyear, sel_school, sel_department, may_edit, err_list = \
                                dl.get_selected_ey_school_dep_from_usersetting(request)
                        if err_list:
                            # TODO change to msg_list
                            msg_dict['error'] = '<br>'.join(err_list)
                        else:
        # - get selected examperiod from usersetting
                            sel_examperiod = None
                            selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                            if selected_dict:
                                sel_examperiod = selected_dict.get(c.KEY_SEL_EXAMPERIOD)

            # - get selected grade from upload_dict - only if clicked on a grade tblRow
                            grade_pk = upload_dict.get('grade_pk')

            # - if  grade_pk has value: get sel_examtype from upload_dict instead of from settings
                            sel_subjbase_pk = None
                            if grade_pk:
                                sel_examtype = upload_dict.get('examtype')
                                # TODO getting sel_examperiod doesnt work properly.
                                # add this line for now to solve it for sr
                                if sel_examtype == 'sr':
                                    sel_examperiod = c.EXAMPERIOD_FIRST
                            else:

            # - if  grade_pk has no value: get selected examperiod, examtype and subject_pk from usersettings
                                # update usersetting if new values in upload_dict
                                new_examtype = upload_dict.get('examtype')
                                new_subjbase_pk = upload_dict.get('subjbase_pk')
                                if new_examtype or new_subjbase_pk:
                                    new_setting_dict = {}
                                    if new_examtype:
                                        new_setting_dict[c.KEY_SEL_EXAMTYPE] = new_examtype
                                    if new_subjbase_pk:
                                        new_setting_dict[c.KEY_SEL_SUBJBASE_PK] = new_subjbase_pk

                                    saved_setting_dict = req_user.set_usersetting_from_upload_subdict(c.KEY_SELECTED_PK, new_setting_dict, request)

                                    if logging_on:
                                        logger.debug('new_examtype: ' + str(new_examtype))
                                        logger.debug('new_subjbase_pk: ' + str(new_subjbase_pk))
                                        logger.debug('saved_setting_dict: ' + str(saved_setting_dict))

                                sel_examperiodNIU, sel_examtype, sel_subject_pk = \
                                    dl.get_selected_experiod_extype_subjbase_from_usersetting(request)

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
                                elif sel_subjbase_pk:
                                    crit.add(Q(studentsubject__schemeitem__subject_base_id=sel_subjbase_pk), crit.connector)
                                row_count = stud_mod.Grade.objects.filter(crit).count()

                                if logging_on:
                                    logger.debug('grade_pk:       ' + str(grade_pk))
                                    logger.debug('sel_subjbase_pk: ' + str(sel_subjbase_pk))
                                    logger.debug('row_count:      ' + str(row_count))

                                grades = stud_mod.Grade.objects.filter(crit).order_by('studentsubject__student__lastname', 'studentsubject__student__firstname')

                                msg_dict = {'count': 0,
                                            'already_published': 0,
                                            'double_approved': 0,
                                            'no_value': 0,
                                            'committed': 0,
                                            'saved': 0,
                                            'reset': 0,
                                            'already_approved': 0,
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
                                            approve_grade(grade, sel_examtype, requsr_auth, auth_index, is_test, is_reset, msg_dict, request)
                                        elif is_submit:
                                            submit_grade(grade, sel_examtype, is_test, published_instance, msg_dict, request)

            # - add update_dict to update_wrap
                                        if grade:
                                            setting_dict = {}
                                            rows = create_grade_rows(
                                                sel_examyear_pk=sel_examyear.pk,
                                                sel_schoolbase_pk=sel_school.base_id,
                                                sel_depbase_pk=sel_department.base_id,
                                                sel_examperiod=sel_examperiod,
                                                setting_dict=setting_dict,
                                                request=request,
                                                grade_pk_list=[grade.pk]
                                            )
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
                                            already_approved = msg_dict.get('already_approved', 0)
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

                                            if already_approved:
                                                msg_dict['already_approved_text'] = get_approved_text(already_approved)

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
        requsr_school = sch_mod.School.objects.get_or_none(
            base=request.user.schoolbase,
            examyear=sel_examyear
        )
        requsr_schoolcode = requsr_school.base.code if requsr_school.base.code else '---'
        # PR2021-08-07 changed to file_dir = 'country/examyear/published/'
        # this one gives path:awpmedia/awpmedia/media/cur/2022/published
        country_abbrev = sel_examyear.country.abbrev.lower()
        examyear_str = str(sel_examyear.code)
        file_dir = '/'.join((country_abbrev, examyear_str, requsr_schoolcode, 'exfiles'))
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
    if count == 1:
        msg_text = _(' - 1 grade is already approved')
    else:
        msg_text = ' - ' + str(count) + str(_(' grades are already approved'))
    return msg_text


def approve_grade(grade, sel_examtype, requsr_auth, auth_index, is_test, is_reset, msg_dict, request):  # PR2021-01-19
    # auth_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- approve_grade -----')
        logger.debug('sel_examtype: ' + str(sel_examtype))
        logger.debug('requsr_auth:  ' + str(requsr_auth))
        logger.debug('is_reset:     ' + str(is_reset))

    if grade and sel_examtype and sel_examtype in ('se', 'sr', 'pe', 'ce'):
        req_user = request.user

# - skip if this grade / examtype is already published
        published = getattr(grade, sel_examtype + '_published')
        if logging_on:
            logger.debug('published:    ' + str(published))

        if published:
            msg_dict['already_published'] += 1
        else:

# skip if this grade has no value - not when deleting approval
            grade_value = getattr(grade, sel_examtype + 'grade')
            score_value = None
            if sel_examtype in ('pe', 'ce'):
                score_value = getattr(grade, sel_examtype + 'score')
            no_value = grade_value is None and score_value is None and not is_reset
            if logging_on:
                logger.debug('no_value:     ' + str(no_value))

            if no_value:
                msg_dict['no_value'] += 1
            else:
                requsr_authby_field = sel_examtype + '_' + requsr_auth + 'by'

# - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved
                auth1by = getattr(grade, sel_examtype + '_auth1by')
                auth2by = getattr(grade, sel_examtype + '_auth2by')
                auth3by = getattr(grade, sel_examtype + '_auth3by')
                auth4by = getattr(grade, sel_examtype + '_auth4by')
                if logging_on:
                    logger.debug('requsr_authby_field: ' + str(requsr_authby_field))
                    logger.debug('auth1by:      ' + str(auth1by))
                    logger.debug('auth2by:      ' + str(auth2by))
                    logger.debug('auth3by:      ' + str(auth3by))
                    logger.debug('auth4by:      ' + str(auth4by))

                double_approved = False
                save_changes = False

# - remove  authby when is_reset
                if is_reset:
                    setattr(grade, requsr_authby_field, None)
                    msg_dict['reset'] += 1
                    save_changes = True
                else:

# - skip if this grade is already approved
                    requsr_authby_value = getattr(grade, requsr_authby_field)
                    requsr_authby_field_already_approved = True if requsr_authby_value else False
                    if logging_on:
                        logger.debug('requsr_authby_field_already_approved: ' + str(requsr_authby_field_already_approved))

                    if requsr_authby_field_already_approved:
                        msg_dict['already_approved'] += 1
                    else:

# - skip if this author (like 'president') has already approved this grade
            # under a different permit (like 'secretary' or 'commissioner')
                        if requsr_auth == 'auth1':
                            double_approved = (auth2by and auth2by == req_user) or (auth3by and auth3by == req_user) or (auth4by and auth4by == req_user)
                        elif requsr_auth == 'auth2':
                            double_approved = (auth1by and auth1by == req_user) or (auth3by and auth3by == req_user) or (auth4by and auth4by == req_user)
                        elif requsr_auth == 'auth3':
                            double_approved = (auth1by and auth1by == req_user) or (auth2by and auth2by == req_user) or (auth4by and auth4by == req_user)
                        elif requsr_auth == 'auth4':
                            double_approved = (auth1by and auth1by == req_user) or (auth2by and auth2by == req_user) or (auth3by and auth3by == req_user)
                        if logging_on:
                            logger.debug('double_approved: ' + str(double_approved))

                        if double_approved:
                            msg_dict['double_approved'] += 1
                        else:
                            setattr(grade, requsr_authby_field, req_user)
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
                        new_status_sum = af.set_status_sum_by_index(saved_status_sum, auth_index, new_value_bool)

                        setattr(grade, sel_examtype + '_status', new_status_sum)

                        if logging_on:
                            logger.debug('is_reset:         ' + str(is_reset))
                            logger.debug('auth_index:     ' + str(auth_index))
                            logger.debug('saved_status_sum: ' + str(saved_status_sum))
                            logger.debug('new_status_sum:   ' + str(new_status_sum))

    # - save changes
                        grade.save(request=request)
# - end of approve_grade


def submit_grade(grade, sel_examtype, is_test, published_instance, msg_dict, request):  # PR2021-01-21
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- submit_grade -----')

    if grade and sel_examtype and sel_examtype in ('se', 'sr', 'pe', 'ce'):

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
                auth4by = getattr(grade, sel_examtype + '_auth4by')
                # TODO dnot checking on auth3by ia only for testing. Must put it back
                # auth_missing = auth1by is None or auth2by is None or auth3by is None
                auth_missing = auth1by is None or auth2by is None
                if logging_on:
                    logger.debug('subject: ' + str(grade.studentsubject.schemeitem.subject.name))
                    logger.debug('auth1by: ' + str(auth1by))
                    logger.debug('auth2by: ' + str(auth2by))
                    logger.debug('auth3by: ' + str(auth3by))
                    logger.debug('auth4by: ' + str(auth4by))
                    logger.debug('auth_missing: ' + str(auth_missing))
                if auth_missing:
                    msg_dict['auth_missing'] += 1
                else:
# - check if all auth are different
                    double_approved = auth1by == auth2by or auth1by == auth3by or auth1by == auth4by or\
                                      auth2by == auth3by or auth2by == auth4by or\
                                      auth3by == auth4by
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

                            auth_index = 4  # c.STATUS_05_SUBMITTED # STATUS_05_SUBMITTED = 32
                            saved_status_sum = getattr(grade, sel_examtype + '_status')
                            new_value_bool = True
                            new_status_sum = af.set_status_sum_by_index(saved_status_sum, auth_index, new_value_bool)

                            if logging_on:
                                logger.debug('saved_status_sum: ' + str(saved_status_sum))
                                logger.debug('auth_index: ' + str(auth_index))
                                logger.debug('new_status_sum: ' + str(new_status_sum))
                                setattr(grade, sel_examtype + '_status', new_status_sum)
# - save changes
                            grade.save(request=request)
# - end of approve_grade

# - end of submit_grade

@method_decorator([login_required], name='dispatch')
class GradeUploadView(View):  # PR2020-12-16 PR2021-01-15 PR2021-12-15 PR2022-01-24

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= GradeUploadView ============= ')
        # function updates grade records of current studentsubject PR2020-11-21
        # adding or deleting grades is done by StudentsubjectSingleUpdateView
        update_wrap = {}
        msg_list = []

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list, requsr_usergroups_listNIU = acc_view.get_userpermit_list('page_grade', request.user)
            has_permit = 'permit_crud' in permit_list

            if logging_on and False:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

        if not has_permit:
            msg_list.append(str(_("You don't have permission to perform this action.")))
        else:

        # - TODO when deleting: return warning when subject grades have values

    # - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

    # - get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not same_school, not activated, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase
                sel_examyear, sel_school, sel_department, may_edit, err_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)
                if err_list:
                    err_list.append(str(_('You cannot make changes.')))
                    msg_list.extend(err_list)
                else:

# - get upload_dict variables
                    # get examperiod and examtype from upload_dict
                    # don't get it from usersettings, get it from upload_dict instead
                    # was: sel_examperiod, sel_examtype, sel_subject_pkNIU = dl.get_selected_experiod_extype_subjbase_from_usersetting(request)
                    mode = upload_dict.get('mode')

                    grade_pk = upload_dict.get('grade_pk')
                    return_grades_with_exam = upload_dict.get('return_grades_with_exam', False)

                    if logging_on:
                        logger.debug('upload_dict: ' + str(upload_dict))

# - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                    # sel_department only has value when sel_examyear and sel_school have value
                    student_pk = upload_dict.get('student_pk')
                    student = stud_mod.Student.objects.get_or_none(
                        id=student_pk,
                        school=sel_school,
                        department=sel_department
                    )

                    grade = None
                    if student:

# - get current grade
                        grade = stud_mod.Grade.objects.get_or_none(
                            id=grade_pk,
                            studentsubject__student=student
                        )
                    if logging_on:
                        logger.debug('student: ' + str(student))
                        logger.debug('grade: ' + str(grade))

                    if grade:
                        # TODO student_subj_grade_dict is not in use, I think
                        #examperiod_int = grade.examperiod
                        #double_entrieslist = []
                        #studsubj_pk = grade.studentsubject_id
                        #student_subj_grade_dict =  grad_val.get_student_subj_grade_dict(sel_school, sel_department, examperiod_int, examgradetype, double_entrieslist, student_pk, studsubj_pk)

        # - get schemitem_info, separately, instead of getting from grade_instance, should be faster
                        si_pk = grade.studentsubject.schemeitem_id
                        schemeitems_dict = subj_vw.get_scheme_si_dict(
                            examyear_pk=sel_examyear.pk,
                            depbase_pk=sel_department.base_id,
                            schemeitem_pk=si_pk)
                        si_dict = schemeitems_dict.get(si_pk)

# +++ update existing grade - also when grade is created - grade is None when deleted
                        if not msg_list and mode == 'update':
                            err_list = update_grade_instance(
                                grade_instance=grade,
                                upload_dict=upload_dict,
                                sel_examyear=sel_examyear,
                                sel_school=sel_school,
                                sel_department=sel_department,
                                student=student,
                                si_dict=si_dict,
                                request=request)
                        if err_list:
                            msg_list.extend(err_list)

        # - add update_dict to update_wrap
                        grade_rows = []
                        if return_grades_with_exam:
                            rows = create_grade_with_exam_rows(
                                sel_examyear_pk=sel_examyear.pk,
                                sel_schoolbase_pk=sel_school.base_id,
                                sel_depbase_pk=sel_department.base_id,
                                sel_examperiod=grade.examperiod,
                                request=request,
                                grade_pk_list=[grade.pk]
                            )
                        else:

                # - err_fields is used when there is an error entering grade, to restore old value on page
                            append_dict = {}
                            if msg_list:
                                 # only one grade is updated, therefore multiple fields are not possible
                                for err_field in ('pescore', 'cescore', 'segrade', 'srgrade', 'pegrade', 'cegrade'):
                                    if err_field in upload_dict:
                                        append_dict['err_fields'] = [err_field]
                                        break

                            setting_dict = {}
                            rows = create_grade_rows(
                                sel_examyear_pk=sel_examyear.pk,
                                sel_schoolbase_pk=sel_school.base_id,
                                sel_depbase_pk=sel_department.base_id,
                                sel_examperiod=grade.examperiod,
                                setting_dict=setting_dict,
                                request=request,
                                append_dict=append_dict,
                                grade_pk_list=[grade.pk]
                            )
                        if rows:
                            row = rows[0]
                            if row:
                                grade_rows.append(row)
                        if grade_rows:
                            update_wrap['updated_grade_rows'] = grade_rows
        if msg_list:
            msg_html = '<br>'.join(msg_list)
            update_wrap['msg_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of GradeUploadView


#######################################################

def update_grade_instance(grade_instance, upload_dict, sel_examyear, sel_school,
                                sel_department, student, si_dict, request):
    # --- update existing grade PR2020-12-16 PR2021-12-13 PR2021-12-25
    # add new values to update_dict (don't reset update_dict, it has values)
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_grade_instance -------')
        logger.debug('upload_dict: ' + str(upload_dict))

    """
    upload_dict: {'mode': 'update', 'mapid': 'grade_67275', 'examperiod': 1, 
                    'grade_pk': 67275, 'student_pk': 9226, 'studsubj_pk': 67836, 
                    'examgradetype': 'segrade', 'segrade': '5,8'}
    """

    err_list = []
    save_changes = False
    recalc_finalgrade = False
    must_recalc_reex_reex03 = False

    for field, new_value in upload_dict.items():

        if logging_on:
            logger.debug('......... field: ' + str(field))
            logger.debug('......... new_value: ' + str(new_value))

        if field in ('pescore', 'cescore', 'segrade', 'srgrade', 'pegrade', 'cegrade'):

# - validate new_value
        # - check if it is allowed to enter this examgradetype this examyear
        # - check if grade is published or authorized
        # - check restrictions in schemeitem

            validated_value, err_lst = grad_val.validate_update_grade(grade_instance, field, new_value, sel_examyear, si_dict)
            if logging_on:
                #logger.debug('new_value:       ' + str(new_value))
                logger.debug('validated_value: ' + str(validated_value) + ' ' + str(type(validated_value)))
                #logger.debug('err_list:        ' + str(err_list))

            if err_lst:
                err_list.extend(err_lst)
            else:
                saved_value = getattr(grade_instance, field)
                if logging_on:
                    logger.debug('saved_value:     ' + str(saved_value) + ' ' + str(type(saved_value)))

# - save changes if changed and no_error
                if validated_value != saved_value:
                    setattr(grade_instance, field, validated_value)
                    save_changes = True
                    recalc_finalgrade = True
                    must_recalc_reex_reex03 = field in ('segrade', 'srgrade', 'pegrade')

# ----- save changes in field 'exam'
        elif field == 'exam_pk':
            # 'pe_exam' is not in use. Let it stay in case they want to introduce pe-exam again
            db_field = 'ce_exam'
            saved_exam = getattr(grade_instance, db_field)
            if logging_on:
                logger.debug('field: ' + str(field) + ' new_value: ' + str(new_value))
                logger.debug('saved_exam: ' + str(saved_exam) + ' ' + str(type(saved_exam)))

            exam = None
            if new_value:
                exam = subj_mod.Exam.objects.get_or_none(pk=new_value)
            if logging_on:
                logger.debug('exam: ' + str(exam) + ' ' + str(type(exam)))

            if exam:
                save_exam = (saved_exam is None) or (exam.pk != saved_exam.pk)
            else:
                save_exam = (saved_exam is not None)
            if save_exam:
                # reset result when exam_pk changes
                setattr(grade_instance, "ce_exam_result", None)
                setattr(grade_instance, db_field, exam)
                save_changes = True
                if logging_on:
                    logger.debug('save_exam: ' + str(save_exam) + ' ' + str(type(save_exam)))

# - save changes in field 'ce_exam_result', 'pe_exam_result'
        elif field in ('ce_exam_result', 'pe_exam_result'):
            saved_value = getattr(grade_instance, field)
            if logging_on:
                logger.debug('field: ' + str(field) + ' new_value: ' + str(new_value))
                logger.debug('saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
    # 2. save changes if changed and no_error
            if new_value != saved_value:
                setattr(grade_instance, field, new_value)
                save_changes = True
                if logging_on:
                    logger.debug('save_changes: ' + str(save_changes))

        # - save changes in fields 'xx_status' and 'xxpublished'
        elif field in ('se_status', 'pe_status', 'ce_status', 'sepublished', 'pepublished', 'cepublished'):
            pass
            # fields are updated in GradeApproveView

        # - save changes in fields 'ce_exam_auth1by' and 'ce_exam_auth2by'
        elif field == 'auth_index':
            auth_index = upload_dict.get(field)
            auth_bool_at_index = upload_dict.get('auth_bool_at_index', False)
            fldName = 'ce_exam_auth1by' if auth_index == 1 else 'ce_exam_auth2by' if auth_index == 2 else None

            if logging_on:
                logger.debug('auth_index: ' + str(auth_index))
                logger.debug('auth_bool_at_index: ' + str(auth_bool_at_index))
                logger.debug('fldName: ' + str(fldName))

            if fldName:
                new_value = request.user if auth_bool_at_index else None
                if logging_on:
                    logger.debug('new_value: ' + str(auth_index))

                setattr(grade_instance, fldName, new_value)
                save_changes = True

# --- end of for loop ---

# +++ if one of the input fields has changed: recalc calculated fields
    if recalc_finalgrade:
        recalc_finalgrade_in_grade_and_save(grade_instance, si_dict, True) # True = skip_save, will be saved furthtr in this function

# 5. save changes`
    if save_changes:

        try:
            grade_instance.save(request=request)

            if logging_on:
                logger.debug('The changes have been saved.')

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            err_list.append(str(_('An error occurred. The changes have not been saved.')))
        else:

# - recalculate gl_sesr, gl_pece, gl_final, gl_use_exem in studsubj record
            # TODO also update these fields when scores are changed or nterm entered
            if must_recalc_reex_reex03:
    # - when field = 'segrade', 'srgrade', 'pegrade': also update and save grades in reex, reex03, if exist
                recalc_finalgrade_in_reex_reex03_grade_and_save(grade_instance, si_dict)
            # TODO add field needs_recalc to student and recalc results only when opening result page, to speed up
            #if recalc_finalgrade:
            #    sql_studsubj_list, sql_student_list = \
            #        update_studsubj_and_recalc_student_result(
            #            sel_examyear, sel_school, sel_department, student)
            #    if sql_studsubj_list:
            #        calc_res.save_studsubj_batch(sql_studsubj_list)
            #
            #    # save calculated fields in student
            #    if sql_student_list:
            #        calc_res.save_student_batch(sql_student_list)

    return err_list
# --- end of update_grade_instance


def update_studsubj_and_recalc_student_result(sel_examyear, sel_school, sel_department, student):
    # PR2022-01-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_studsubj_and_recalc_student_result -------')

# - get_scheme_dict
    scheme_dict = calc_res.get_scheme_dict(sel_examyear, sel_department)

# - get_schemeitems_dict
    schemeitems_dict = calc_res.get_schemeitems_dict(sel_examyear, sel_department)

# - get student_dict
    student_pk_list = [student.pk]
    student_dictlist = calc_res.get_students_with_grades_dictlist(sel_examyear, sel_school, sel_department,
                                                                  None, None, student_pk_list)
    student_dict = student_dictlist[0]

    log_list = []
    sql_studsubj_list = []
    sql_student_list = []
    calc_res.calc_student_result(sel_examyear, sel_department, student_dict, scheme_dict, schemeitems_dict,
                                 log_list, sql_studsubj_list, sql_student_list)

    if logging_on:
        logger.debug('sql_studsubj_list: ' + str(sql_studsubj_list))
        logger.debug('sql_student_list: ' + str(sql_student_list))
    return sql_studsubj_list, sql_student_list
# - end of update_studsubj_and_recalc_student_result


def recalc_finalgrade_in_reex_reex03_grade_and_save(grade_instance, si_dict):  # PR2021-12-28 PR2022-01-05
    # called by:  - update_grade_instance, - update_studsubj
    # when first examperiod:
    #  - check if there is a reex or reex03 grade: if so, recalc final grade in reex or reex03
    #  - only when first examperiod ( is filtered in update_grade_instance)

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- recalc_finalgrade_in_reex_reex03_grade_and_save -----')
        logger.debug('grade_instance: ' + str(grade_instance) + ' ep: ' + str(grade_instance.examperiod))

# - check if there are any reex or reex03 records
    crit = Q(studentsubject=grade_instance.studentsubject) & Q(tobedeleted=False) & \
           (Q(examperiod=c.EXAMPERIOD_FIRST) | Q(examperiod=c.EXAMPERIOD_SECOND) | Q(examperiod=c.EXAMPERIOD_THIRD))
    grades = stud_mod.Grade.objects.filter(crit)

# - recalc final grade in reex or reex03 records
    if grades:
        for updated_grade in grades:
            recalc_finalgrade_in_grade_and_save(updated_grade, si_dict)
            if logging_on:
                logger.debug('.....  updated_grade is saved')
# end of recalc_finalgrade_in_reex_reex03_grade_and_save


def recalc_finalgrade_in_grade_and_save(grade_instance, si_dict, skip_save=False):
    # PR2021-12-13  PR2021-12-24 PR2022-01-05 PR2022-02-15
    # called by:
    #   - update_grade_instance.
    #   - recalc_finalgrade_in_reex_reex03_grade_and_save

    # - gets input values from grade_instance
    # - calls calc_sesr_pece_final_grade to calculate sesr_grade, pece_grade, finalgrade
    # - puts se, sr, sesr, pe in reex and reex03
    # - saves the grade_instance

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('------- recalc_finalgrade_in_grade_and_save -------')

    if grade_instance:
        try:
            is_ep_exemption = (grade_instance.examperiod == c.EXAMPERIOD_EXEMPTION)

            studentsubject = grade_instance.studentsubject
            has_sr = studentsubject.has_sr

            gradetype = si_dict.get('gradetype')
            weight_se = si_dict.get('weight_se')
            weight_ce = si_dict.get('weight_ce')
            has_practexam = si_dict.get('has_practexam')

            se_grade, sr_grade, pe_grade = None, None, None

# --- when second or third examperiod: get se-, sr- and pe_grade from first examperiod,
            if grade_instance.examperiod in (c.EXAMPERIOD_SECOND, c.EXAMPERIOD_THIRD):
        # - get grade of first examperiod
                grade_first_period = stud_mod.Grade.objects.get_or_none(
                    studentsubject=studentsubject,
                    examperiod=c.EXAMPERIOD_FIRST
                )
                if grade_first_period is None:
        # - give error when there are zero or multiple grade rows with first examperiod, should not be possible
                    count_grade_first_period = stud_mod.Grade.objects.filter(
                        studentsubject=studentsubject,
                        examperiod=c.EXAMPERIOD_FIRST
                    ).count()
                    logger.error('ERROR: ' + count_grade_first_period + ' grades found in first examperiod.')
                    logger.error('       subject: ' + str(si_dict.get('subj_code', '---')))
                    logger.error('       student: ' + str(studentsubject.student))
                else:
                    se_grade = grade_first_period.segrade
                    sr_grade = grade_first_period.srgrade
                    pe_grade = grade_first_period.pegrade

                    # put the values of se, sr, pe in reex and reex03
                    setattr(grade_instance, 'segrade', se_grade)
                    setattr(grade_instance, 'srgrade', sr_grade)
                    setattr(grade_instance, 'pegrade', pe_grade)
            else:

# - when first period or exemption: get se, sr and pe grades from grade_instance
                se_grade = grade_instance.segrade
                sr_grade = grade_instance.srgrade
                pe_grade = grade_instance.pegrade

# - get ce_grade always from grade_instance
            ce_grade = grade_instance.cegrade

# - calc sesr pece and final grade
            if logging_on:
                logger.debug(' calc sesr pece and final grade ')
            sesr_grade, pece_grade, finalgrade = \
                calc_final.calc_sesr_pece_final_grade(
                    is_ep_exemption, has_practexam, gradetype, weight_se, weight_ce,
                    has_sr, se_grade, sr_grade, pe_grade, ce_grade)

            setattr(grade_instance, 'sesrgrade', sesr_grade)
            setattr(grade_instance, 'pecegrade', pece_grade)
            setattr(grade_instance, 'finalgrade', finalgrade)

            if not skip_save:
                grade_instance.save()

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# --- end of recalc_finalgrade_in_grade_and_save


def save_se_sr_pe_in_grade_reex_reex03_NIU(studsubj_pk, se_grade, sr_grade, pe_grade):  # PR2021-12-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- save_se_sr_pe_in_grade_reex_reex03_NIU -----')
    # - function puts se_grade, sr_grade and pe_grade from firstperiod grade in grade reex and reex03, if exists
    # - set value to Null when segrade etc is None
    updated_gradepk_list = []
    if studsubj_pk:
        se_grade_str = ''.join(("'", se_grade, "'")) if se_grade else 'NULL'
        sr_grade_str = ''.join(("'", sr_grade, "'")) if sr_grade else 'NULL'
        pe_grade_str = ''.join(("'", pe_grade, "'")) if pe_grade else 'NULL'

        sql_keys = {'ss_id': studsubj_pk}
        sql_list = [
            "UPDATE students_grade AS grade",
            "SET segrade =", se_grade_str, ", srgrade =", sr_grade_str, ", pegrade =", pe_grade_str,
            "FROM students_studentsubject AS studsubj",
            "WHERE grade.studentsubject_id = studsubj.id",
            "AND (grade.examperiod = 2 OR grade.examperiod = 3)",
            "AND NOT grade.tobedeleted",
            "AND studsubj.id = %(ss_id)s::INT",
            "RETURNING grade.id"
        ]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
# return list of updated grades, to calculate final grades
            for row in cursor.fetchall():
                updated_gradepk_list.append(row[0])
        if logging_on:
            logger.debug('updated_gradepk_list: ' + str(updated_gradepk_list))
    return updated_gradepk_list
# - end of save_se_sr_pe_in_grade_reex_reex03_NIU


def create_grade_note_icon_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk, sel_examperiod, studsubj_pk, request):

    # --- calculate the note- and status icons to be show in the grade rows  PR2021-04-20
    logging_on = False  # s.LOGGING_ON
    if logging_on:
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

        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))
            logger.debug('requsr_same_school: ' + str(requsr_same_school))

        sql_ssn_list = ["SELECT ssn.studentsubject_id AS studsubj_id, MAX(ssn.note_status) AS max_note_status",
                    "FROM students_studentsubjectnote AS ssn",
                    "WHERE (ssn.intern_schoolbase_id = %(requsr_sb_id)s::INT OR ssn.intern_schoolbase_id IS NULL)",
                    "GROUP BY ssn.studentsubject_id"]
        sql_ssn = ' '.join(sql_ssn_list)

        sql_list = ["SELECT grd.id, studsubj.id AS studsubj_id,",
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
                    "AND grd.examperiod = %(ex_per)s::INT",
                    "AND NOT grd.tobedeleted",
                    "AND NOT studsubj.tobedeleted",
                    "AND NOT st.tobedeleted"
                    ]
        if studsubj_pk:
            sql_keys['studsubj_id'] = studsubj_pk
            sql_list.append("AND studsubj.id = %(studsubj_id)s::INT")

        sql_list.append('ORDER BY grd.id')

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


def create_grade_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk, sel_examperiod, setting_dict, request,
                      append_dict=None, grade_pk_list=None, auth_dict=None):
    # --- create grade rows of all students of this examyear / school PR2020-12-14  PR2021-12-03 PR2022-02-09

    # note: don't forget to filter tobedeleted = false!! PR2021-03-15
    # grades that are not published are only visible when 'same_school'
    # note_icon is downloaded in separate call

    # PR2021-12-19
    # - instead of getting usernames of auth with LEFT JOIN for each auth:
    #   create dict with pk and username of all users of this school and lookup in
    username_dict = acc_view.get_username_dict()

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_grade_rows -----')
        logger.debug('     sel_examyear_pk: ' + str(sel_examyear_pk))
        logger.debug('     sel_schoolbase_pk: ' + str(sel_schoolbase_pk))
        logger.debug('     sel_depbase_pk: ' + str(sel_depbase_pk))
        logger.debug('     sel_examperiod: ' + str(sel_examperiod))
        logger.debug('     grade_pk_list: ' + str(grade_pk_list))

    grade_rows = []
    try:
        req_user = request.user
        # - only requsr of the same school can view grades that are not published, PR2021-04-29
        requsr_same_school = (req_user.role == c.ROLE_008_SCHOOL and req_user.schoolbase.pk == sel_schoolbase_pk)

        # - also commissioner .TODO: add school to commissioner permit
        requsr_commissioner = (req_user.role == c.ROLE_016_COMM)

    #  - add_auth_list is used in Ex form to add name of auth
        add_auth_list = True if auth_dict is not None else False

        # sel_examtype not in use
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

        # - check is to determine if final_grade must be shown. Check is True when weight = 0 or not has_practexam
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

        sql_list = ["SELECT grd.id, studsubj.id AS studsubj_id, studsubj.schemeitem_id, cl.id AS cluster_id, cl.name AS cluster_name,",
                    "CONCAT('grade_', grd.id::TEXT) AS mapid,",
                    "stud.id AS student_id, stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
                    "stud.level_id AS lvl_id, lvl.abbrev AS lvl_abbrev, stud.sector_id AS sct_id, sct.abbrev AS sct_abbrev,",
                    "stud.iseveningstudent, ey.locked AS ey_locked, school.locked AS school_locked,",
                    "school.islexschool,",
                    "studsubj.has_exemption, studsubj.has_sr, studsubj.has_reex, studsubj.has_reex03,",

                    grades, final_grade, status,
                    "grd.examperiod,",
                    "grd.se_auth1by_id, grd.se_auth2by_id, grd.se_auth3by_id, grd.se_auth4by_id, grd.se_published_id, grd.se_blocked,",
                    "grd.sr_auth1by_id, grd.sr_auth2by_id, grd.sr_auth3by_id, grd.sr_auth4by_id, grd.sr_published_id, grd.sr_blocked,",
                    "grd.pe_auth1by_id, grd.pe_auth2by_id, grd.pe_auth3by_id, grd.pe_auth4by_id, grd.pe_published_id, grd.pe_blocked,",
                    "grd.ce_auth1by_id, grd.ce_auth2by_id, grd.ce_auth3by_id, grd.ce_auth4by_id, grd.ce_published_id, grd.ce_blocked,",

                    "grd.se_published_id, se_published.modifiedat AS se_publ_modat,",
                    "grd.sr_published_id, sr_published.modifiedat AS sr_publ_modat,",
                    "grd.pe_published_id, pe_published.modifiedat AS pe_publ_modat,",
                    "grd.ce_published_id, ce_published.modifiedat AS ce_publ_modat,",

                    "si.subject_id, si.subjecttype_id,",
                    "si.gradetype, si.weight_se, si.weight_ce, si.is_mandatory, si.is_mand_subj_id, si.is_combi, si.extra_count_allowed,",
                    "si.extra_nocount_allowed, si.has_practexam,",
                    # TODO check if sjtp.has_pws is used. If so: add join with subjecttype
                    # was:  "si.has_pws,",
                    "si.is_core_subject, si.is_mvt, si.sr_allowed, si.max_reex, si.no_thirdperiod, si.no_exemption_ce,",
                    "si.rule_grade_sufficient, si.rule_gradesuff_notatevlex,",

                    "subj.name AS subj_name, subjbase.id AS subjbase_id, subjbase.code AS subj_code,",
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

                    "LEFT JOIN subjects_cluster AS cl ON (cl.id = studsubj.cluster_id)",

                    "LEFT JOIN schools_published AS se_published ON (se_published.id = grd.se_published_id)",
                    "LEFT JOIN schools_published AS sr_published ON (sr_published.id = grd.sr_published_id)",
                    "LEFT JOIN schools_published AS pe_published ON (pe_published.id = grd.pe_published_id)",
                    "LEFT JOIN schools_published AS ce_published ON (ce_published.id = grd.ce_published_id)",

                    "WHERE ey.id = %(ey_id)s::INT AND grd.examperiod = %(experiod)s::INT",
                    "AND school.base_id = %(sb_id)s::INT",
                    "AND dep.base_id = %(depbase_id)s::INT",
                    "AND NOT stud.tobedeleted",
                    "AND NOT studsubj.tobedeleted",
                    "AND NOT grd.tobedeleted",
                    ]
# --- filter on usersetting
        sel_lvlbase_pk, sel_subjbase_pk, sel_cluster_pk, sel_student_pk = None, None, None, None
        if setting_dict:
            sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)
            sel_subjbase_pk = setting_dict.get(c.KEY_SEL_SUBJBASE_PK)
            sel_cluster_pk = setting_dict.get(c.KEY_SEL_CLUSTER_PK)
            sel_student_pk = setting_dict.get(c.KEY_SEL_STUDENT_PK)

        if grade_pk_list:
            # when grade_pk_list has value: skip subject filter
            sql_keys['grade_pk_arr'] = grade_pk_list
            sql_list.append("AND grd.id IN ( SELECT UNNEST( %(grade_pk_arr)s::INT[]))")
        else:
            if sel_lvlbase_pk:
                sql_keys['lvlbase_pk'] = sel_lvlbase_pk
                sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

            if sel_subjbase_pk:
                sql_keys['subjbase_pk'] = sel_subjbase_pk
                sql_list.append("AND subj.base_id = %(subjbase_pk)s::INT")

            if sel_cluster_pk:
                sql_keys['cluster_pk'] = sel_cluster_pk
                sql_list.append("AND studsubj.cluster_id = %(cluster_pk)s::INT")

            if sel_student_pk:
                sql_keys['student_pk'] = sel_student_pk
                sql_list.append("AND stud.id = %(student_pk)s::INT")

# --- filter on allowed
        if req_user.allowed_depbases:
            if ';' in req_user.allowed_depbases:
                sql_keys['db_arr'] = req_user.allowed_depbases.split(';')
                sql_list.append("AND dep.base_id IN ( SELECT UNNEST(%(db_arr)s::INT[]) )")
            else:
                sql_keys['db_pk'] = req_user.allowed_depbases
                sql_list.append("AND dep.base_id = %(db_pk)s::INT")

        if req_user.allowed_levelbases:
            if ';' in req_user.allowed_levelbases:
                sql_keys['lvl_arr'] = req_user.allowed_levelbases.split(';')
                sql_list.append("AND lvl.base_id IN ( SELECT UNNEST(%(lvl_arr)s::INT[]) )")
            else:
                sql_keys['db_pk'] = req_user.allowed_levelbases
                sql_list.append("AND lvl.base_id = %(lvl_pk)s::INT")

        if req_user.allowed_schoolbases:
            if ';' in req_user.allowed_schoolbases:
                sql_keys['schb_arr'] = req_user.allowed_schoolbases.split(';')
                sql_list.append("AND school.base_id IN ( SELECT UNNEST(%(schb_arr)s::INT[]) )")
            else:
                sql_keys['schb_pk'] = req_user.allowed_schoolbases
                sql_list.append("AND school.base_id = %(schb_pk)s::INT")

        acc_view.get_userfilter_subjbase(sql_keys, sql_list, sel_subjbase_pk, request)

        # allowed_clusterbases are not filtered here, instead allow editing in client

        sql_list.append('ORDER BY grd.id')

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            grade_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))
            logger.debug('sql: ' + str(sql))

    # - add full name to rows, and array of id's of auth
        if grade_rows:
            # create auth_dict, with lists of each auth
            #auth_fields = ('se_auth1by_id', 'se_auth2by_id', 'se_auth3by_id', 'se_auth4by_id',
            #                  'sr_auth1by_id', 'sr_auth2by_id', 'sr_auth3by_id', 'sr_auth4by_id',
            #                  'pe_auth1by_id', 'pe_auth2by_id', 'pe_auth3by_id', 'pe_auth4by_id',
            #                  'ce_auth1by_id', 'ce_auth2by_id', 'ce_auth3by_id' 'ce_auth4by_id')

            if logging_on and False:
                logger.debug('---------------- ')
            for row in grade_rows:
                first_name = row.get('firstname')
                last_name = row.get('lastname')
                # PR 2021-12-19
                # instead of adding LEFT JOIN accounts_user to sql
                # create a dict with all users and get user last_name from dict instead
                for ex_type in ('se', 'sr', 'pe', 'ce'):
                    for auth_idx in range(1, 5):
                        field_name = ''.join((ex_type, '_auth', str(auth_idx), 'by_id'))
                        auth_id = row.get(field_name)
                        if auth_id:
                            field_usrname = ''.join((ex_type, '_auth', str(auth_idx), 'by_usr'))
                            usrname = username_dict.get(auth_id, '-')
                            if logging_on:
                                logger.debug('field_usrname: ' + str(field_usrname))
                                logger.debug('usrname: ' + str(usrname))

                            row[field_usrname] = usrname

                prefix = row.get('prefix')
                full_name = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)
                row['fullname'] = full_name if full_name else None

        # - add messages to all studsubj_rows, only when student_pk or studsubj_pk_list have value
                if append_dict and grade_pk_list:
                    for key, value in append_dict.items():
                        row[key] = value

                if logging_on and False:
                    logger.debug('..... ')
                    logger.debug('row: ' + str(row))

            if logging_on:
                logger.debug('---------------- ')

    except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return grade_rows
# --- end of create_grade_rows


def create_grade_with_exam_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk, sel_examperiod,
                                    request, setting_dict=None, grade_pk_list=None):
    # --- create grade rows of all students of this examyear / school PR2020-12-14 PR2022-02-20

    # note: don't forget to filter deleted = false!! PR2021-03-15
    # grades that are not published are only visible when 'same_school'
    # note_icon is downloaded in separate call
    # IMPORTANT: only add field 'keys' when ETE has logged in .
    #   Field 'keys' contains the answers of multiple choice questions,
    #   they may not be downloaded by schools,
    #   to be 100% sure that the answers cannot be retrieved by a school.

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_grade_with_exam_rows -----')
        logger.debug('setting_dict: ' + str(setting_dict))

    # - only requsr of the same school  can view grades that are not published, PR2021-04-29
    # - also commissioner .TODO: add school to commissioner permit

    # - only exams that are published are visible
    # - only ce_exams that are submitted are visible for non - requsr_same_school user > not necessary
    #       > not necessary, because only requsr_same_school can access grade_with_exam_rows

    grade_rows = []

    req_user = request.user
    requsr_same_school = (req_user.role == c.ROLE_008_SCHOOL and req_user.schoolbase.pk == sel_schoolbase_pk)
    if requsr_same_school:
        #examkeys_fields = ""
        #if req_user.role == c.ROLE_064_ADMIN:
        #    # pe_exam not in use: was: examkeys_fields = "ce_exam.keys AS ceex_keys, pe_exam.keys AS peex_keys,"
        #    examkeys_fields = "ce_exam.keys AS ceex_keys,"

        sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk,
                    'depbase_id': sel_depbase_pk, 'experiod': sel_examperiod}

        sub_list = ["SELECT exam.id, subjbase.id AS exam_subjbase_id,",
                    "CONCAT(subjbase.code,",
                    "CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' - ', lvl.abbrev) END,",
                    "CASE WHEN exam.version IS NULL OR exam.version = '' THEN NULL ELSE CONCAT(' - ', exam.version) END ) AS exam_name,",

                    "exam.examperiod, exam.examtype, exam.version, exam.has_partex, exam.partex, exam.amount, exam.blanks, exam.assignment, exam.keys,",
                    "exam.nex_id, exam.scalelength, exam.cesuur, exam.nterm",  #, exam.examdate",

                    "FROM subjects_exam AS exam",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

                    "WHERE exam.published_id IS NOT NULL"
                    ]
        sub_exam = ' '.join(sub_list)

        sql_list = ["SELECT grd.id, CONCAT('grade_', grd.id::TEXT) AS mapid,",
                    "stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
                    "stud.id AS student_id, stud.lastname, stud.firstname, stud.prefix,",
                    "lvl.id AS level_id, lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev,",
                    "subj.id AS subj_id, subjbase.code AS subj_code, subjbase.id AS subjbase_id, subj.name AS subj_name,",
                    "studsubj.id AS studsubj_id, cls.id AS cluster_id, cls.name AS cluster_name,",
                    "grd.examperiod,"
                    # "grd.pe_exam_id, grd.pe_exam_result, grd.pe_exam_auth1by_id, grd.pe_exam_auth2by_id, grd.pe_exam_published_id, grd.pe_exam_blocked,",
                    "grd.ce_exam_id, grd.ce_exam_result, grd.ce_exam_auth1by_id, grd.ce_exam_auth2by_id, grd.ce_exam_published_id, grd.ce_exam_blocked,",

                    "ce_exam.id AS ceex_exam_id, ce_exam.exam_name AS ceex_name,"
                    "ce_exam.exam_subjbase_id AS ceex_exam_subjbase_id,",
                    "ce_exam.examperiod AS ceex_examperiod, ce_exam.examtype AS ceex_examtype,",
                    "ce_exam.version AS ceex_version, ce_exam.amount AS ceex_amount,",
                    "ce_exam.has_partex AS ceex_has_partex, ce_exam.partex AS ceex_partex,",
                    "ce_exam.blanks AS ceex_blanks, ce_exam.assignment AS ceex_assignment,",
                    "ce_exam.nex_id AS ceex_nex_id, ce_exam.scalelength AS ceex_scalelength,",
                    "ce_exam.cesuur AS ceex_cesuur, ce_exam.nterm AS ceex_nterm,",  # ce_exam.examdate AS ceex_examdate,",

                    # examkeys_fields,

                    #"pe_exam.id AS peex_exam_id, pe_exam.exam_name AS peex_name,"
                    #"pe_exam.examperiod AS peex_examperiod, pe_exam.examtype AS peex_examtype,",
                    #"pe_exam.version AS peex_version, pe_exam.amount AS peex_amount,",
                    #"pe_exam.has_partex AS peex_has_partex, pe_exam.partex AS peex_partex,",
                    #"pe_exam.blanks AS peex_blanks, pe_exam.assignment AS peex_assignment,",
                    #"pe_exam.nex_id AS peex_nex_id, pe_exam.scalelength AS peex_scalelength,",
                    #"pe_exam.cesuur AS peex_cesuur, pe_exam.nterm AS peex_nterm,",  # pe_exam.examdate AS peex_examdate,",

                    "auth1.last_name AS ce_exam_auth1_usr, auth2.last_name AS ce_exam_auth2_usr, publ.modifiedat AS ce_exam_publ_modat",

                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                    "LEFT JOIN (", sub_exam, ") AS ce_exam ON (ce_exam.id = grd.ce_exam_id)",
                    #"LEFT JOIN (", sub_exam, ") AS pe_exam ON (pe_exam.id = grd.pe_exam_id)",

                    "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                    "LEFT JOIN subjects_cluster AS cls ON (cls.id = studsubj.cluster_id)",

                    "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                    "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                    "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                    "LEFT JOIN accounts_user AS auth1 ON (auth1.id = grd.ce_exam_auth1by_id)",
                    "LEFT JOIN accounts_user AS auth2 ON (auth2.id = grd.ce_exam_auth2by_id)",
                    "LEFT JOIN schools_published AS publ ON (publ.id = grd.ce_exam_published_id)",

                    "WHERE ey.id = %(ey_id)s::INT",
                    "AND school.base_id = %(sb_id)s::INT",
                    "AND dep.base_id = %(depbase_id)s::INT",
                    "AND si.ete_exam",
                    "AND NOT grd.tobedeleted AND NOT studsubj.tobedeleted AND NOT stud.tobedeleted"
                    ]

        if logging_on:
            logger.debug('grade_pk_list: ' + str(grade_pk_list))

        if grade_pk_list:
            # when grade_pk_list has value: skip subject filter
            sql_keys['grade_pk_arr'] = grade_pk_list
            sql_list.append("AND grd.id IN ( SELECT UNNEST( %(grade_pk_arr)s::INT[]))")

        elif setting_dict:
            sel_examperiod = setting_dict.get(c.KEY_SEL_EXAMPERIOD)
            if sel_examperiod in (1, 2):
                sql_keys['ep'] = sel_examperiod
                sql_list.append("AND grd.examperiod = %(ep)s::INT")

            sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)
            if sel_lvlbase_pk:
                sql_keys['lvlbase_pk'] = sel_lvlbase_pk
                sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

            sel_subjbase_pk = setting_dict.get(c.KEY_SEL_SUBJBASE_PK)
            if sel_subjbase_pk:
                sql_keys['subjbase_pk'] = sel_subjbase_pk
                sql_list.append("AND subj.base_id = %(subjbase_pk)s::INT")

            sel_cluster_pk = setting_dict.get(c.KEY_SEL_CLUSTER_PK)
            if sel_cluster_pk:
                sql_keys['cluster_pk'] = sel_cluster_pk
                sql_list.append("AND studsubj.cluster_id = %(cluster_pk)s::INT")

            sel_student_pk = setting_dict.get(c.KEY_SEL_STUDENT_PK)
            if sel_student_pk:
                sql_keys['student_pk'] = sel_student_pk
                sql_list.append("AND stud.id = %(student_pk)s::INT")

    # show grades that are not published only when requsr_same_school PR2021-04-29

        sql_list.append('ORDER BY grd.id')

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            grade_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))
            logger.debug('sql: ' + str(sql))
            logger.debug('grade_rows: ' + str(grade_rows))

    # - add full name to rows, and array of id's of auth
        if grade_rows:
            for row in grade_rows:
                first_name = row.get('firstname')
                last_name = row.get('lastname')
                prefix = row.get('prefix')
                full_name = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)
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
           Q(school__examyear_id=sel_examyear_pk)
          # Q(department__base_id=sel_depbase_pk)
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
            #'db_code': row.department.base.code,
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
        requsr_school = sch_mod.School.objects.get_or_none(
            base=request.user.schoolbase,
            examyear=sel_examyear
        )
        requsr_schoolcode = requsr_school.base.code if requsr_school.base.code else '---'
        country_abbrev = sel_examyear.country.abbrev.lower()
        examyear_str = str(sel_examyear.code)
        file_dir = '/'.join((country_abbrev, examyear_str, requsr_schoolcode, 'exfiles'))
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

            # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
            published_instance.save(request=request)

            # file_path: media/private/published/Ex2A CUR13 ATC Vsbo SE-tv1 cav 2021-04-29 10u11.pdf
            # stored in dir:

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

