# PR2021-07-28
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q

from django.http import HttpResponse
from django.shortcuts import render

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import FormView

from accounts import models as acc_mod
from accounts import views as acc_view
from accounts.tokens import account_activation_token
from accounts.views import PasswordContextMixin
from awpr import menus as awpr_menu
from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import downloads as dl

from grades import excel as grd_exc

from students import models as stud_mod

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

##########################################


def prepare_ex1_file(request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ============= prepare_ex1_file ============= ')

# function sets auth and publish of studentsubject records of current department # PR2021-07-25
    update_wrap = {}
    messages = []
    requsr_auth = None

# - get permit
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

#----------------------------
    #<PERMIT>
    # only users with role > student and perm_edit can change student data
    # only school that is requsr_school can be changed
    #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
    # only if country/examyear/school/student not locked, examyear is published and school is activated

# - get selected mode. Modes are 'approve' 'submit_test' 'submit_submit', 'reset'
                mode = upload_dict.get('mode')
                is_approve = True if mode in ('approve_test', 'approve_submit', 'approve_reset') else False
                is_submit = True if mode in ('submit_test', 'submit_submit') else False
                is_reset = True if mode == 'approve_reset' else False
                is_test = True if mode in ('approve_test', 'submit_test') else False

# - get auth_index (1 = President, 2 = Secretary, 3 = Commissioner)
                # PR2021-03-27 auth_index is taken from requsr_usergroups_list, not from upload_dict
                #  function may have changed if page is not refreshed in time)

                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))
                    logger.debug('mode: ' + str(mode))

                sel_lvlbase_pk, sel_sctbase_pk, sel_subject_pk, sel_student_pk = None, None, None, None
                selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                if selected_dict:
                    sel_lvlbase_pk = selected_dict.get(c.KEY_SEL_LVLBASE_PK)
                    sel_sctbase_pk = selected_dict.get(c.KEY_SEL_SCTBASE_PK)
                    sel_subject_pk = selected_dict.get(c.KEY_SEL_SUBJECT_PK)
                    # TODO filter by cluster
                if logging_on:
                    logger.debug('selected_dict: ' + str(selected_dict))

# +++ get selected subject_rows
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

                msg_dict = {'count': 0,
                            'already_published': 0,
                            'double_approved': 0,
                            'committed': 0,
                            'saved': 0,
                            'reset': 0,
                            'already_approved_by_auth': 0,
                            'auth_missing': 0,
                            'test_is_ok': False
                            }
                if studsubjects is not None:

# create new published_instance. Only save it when it is not a test
                    # file_name will be added after creating Ex-form
                    published_instance = None
                    if is_submit and not is_test:
                        now_arr = upload_dict.get('now_arr')

                        published_instance = create_published_Ex1_instance(
                            sel_school=sel_school,
                            sel_department=sel_department,
                            sel_examperiod=1,
                            is_test=is_test,
                            now_arr=now_arr,
                            request=request)  # PR2021-07-27

                    studsubj_rows = []

# +++++ loop through subjects
                    if studsubjects:
                        for studsubj in studsubjects:
                            if logging_on:
                                logger.debug('----- studsubj: ' + str(studsubj))

                            msg_dict['count'] += 1
                            is_saved = False
                            if is_approve:
                                is_saved = approve_studsubj(studsubj, requsr_auth, is_test, is_reset, msg_dict, request)
                            elif is_submit:
                                is_saved = submit_studsubj(studsubj, is_test, published_instance, msg_dict, request)

# - add rows to studsubj_rows, to be sent back to page
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
# +++++  end of loop through  subjects

                    row_count = msg_dict.get('count', 0)

# - create msg_html with info of rows
                    msg_html = self.create_msg_list(logging_on, msg_dict, requsr_auth, is_approve, is_test)

                    if row_count:
                        if is_submit and not is_test:
                            self.create_Ex1(
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
                            committed = msg_dict.get('committed', 0)
                            if committed:
                                update_wrap['test_is_ok'] = True

# - add  msg_dict to update_wrap
                    update_wrap['approve_msg_html'] = msg_html

# - return update_wrap
    return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

def create_msg_listXXX(logging_on, msg_dict, requsr_auth, is_approve, is_test):
    if logging_on:
        logger.debug('  ----- create_msg_list -----')
        logger.debug('msg_dict: ' + str(msg_dict))
        logger.debug('is_test: ' + str(is_test))

    count = msg_dict.get('count', 0)
    committed = msg_dict.get('committed', 0)
    saved = msg_dict.get('saved', 0)
    already_published = msg_dict.get('already_published', 0)
    auth_missing = msg_dict.get('auth_missing', 0)
    already_approved_by_auth = msg_dict.get('already_approved_by_auth', 0)
    double_approved = msg_dict.get('double_approved', 0)

    if logging_on:
        logger.debug('.....count: ' + str(count))
        logger.debug('.....committed: ' + str(committed))
        logger.debug('.....already_published: ' + str(already_published))
        logger.debug('.....auth_missing: ' + str(auth_missing))
        logger.debug('.....already_approved_by_auth: ' + str(already_approved_by_auth))
        logger.debug('.....double_approved: ' + str(double_approved))

    if is_approve:
        class_str = 'border_bg_valid' if committed else 'border_bg_invalid'
    else:
        if saved:
            if (is_test and auth_missing) or (is_test and double_approved):
                class_str = 'border_bg_warning'
            else:
                class_str = 'border_bg_valid'
        else:
            class_str = 'border_bg_invalid'

    msg_list = ["<div class='p-2 ", class_str, "'>",
                "<p class='pb-2'>",
                str(_("The selection contains %(val)s.") % {'val': get_subject_text(count)}),
                '</p>']

    if committed < count:
        msg_list.append("<p class='pb-0'>" + str(_("The following subjects will be skipped")) + ':</p><ul>')
        if already_published:
            msg_list.append('<li>' + str(_("%(val)s already submitted") %
                                         {'val': get_subjects_are_text(already_published)}) + ';</li>')
        if auth_missing:
            msg_list.append('<li>' + str(_("%(val)s not completely approved") %
                                         {'val': get_subjects_are_text(auth_missing)}) + ';</li>')
        if already_approved_by_auth:
            msg_list.append('<li>' + get_approved_text(already_approved_by_auth) + ';</li>')
        if double_approved:
            other_function =  str(_('president')) if requsr_auth == 'auth2' else str(_('secretary'))
            msg_list.append(''.join(('<li>', get_subjects_are_text(double_approved), str(_(' already approved by you as ')), other_function, '.<br>',
                            str(_("You cannot approve a subject both as president and as secretary.")), '</li>')))
        msg_list.append('</ul>')

    msg_list.append('<p>')
    if is_test:
        if not committed:
            if is_approve:
                msg_str = _("No subjects will be approved.")
            else:
                msg_str = _("The Ex1 form can not be submitted.")
        elif committed == 1:
            if is_approve:
                msg_str = _("One subject will be approved.")
            else:
                msg_str = _("One subject will be added to the Ex1 form.")
        else:
            if is_approve:
                msg_str = _("%(val)s subjects will be approved.") % {'val': committed}
            else:
                msg_str = _("%(val)s subjects will be added to the Ex1 form.") % {'val': committed}
    else:
        if not saved:
            msg_str = _("The Ex1 form has not been submitted.")
        elif saved == 1:
            msg_str = _("The Ex1 form has been submitted. It contains 1 subject.")
        else:
            msg_str = _("The Ex1 form has been submitted. It contains %(val)s subjects.") %  {'val': saved}

    msg_list.append(str(msg_str))
    msg_list.append('</p>')

    if class_str == 'border_bg_warning':
        msg_list.append('<p><b>')
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

def create_Ex1(published_instance, sel_examyear, sel_school, sel_department, save_to_disk, user_lang):
    #PR2021-07-27
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ============= create_Ex1 ============= ')

# get text from examyearsetting
    settings = af.get_exform_text(sel_examyear, ['exform', 'ex1'])
    if logging_on:
        logger.debug('settings: ' + str(settings))

# +++ get mapped_subject_rows
    subject_row_count, subject_pk_list, subject_code_list, level_pk_list = \
        grd_exc.create_ex1_mapped_subject_rows(sel_examyear, sel_school, sel_department)
    #  subject_pk_dict: {34: 0, 29: 1, ...} ( subject_pk: index)
    #  subject_code_list: ['bw', 'cav', ]
    #  index = row_count

    if logging_on:
        logger.debug('subject_row_count: ' + str(subject_row_count))
        logger.debug('subject_pk_list: ' + str(subject_pk_list))
        logger.debug('subject_code_list: ' + str(subject_code_list))
        logger.debug('level_pk_list: ' + str(level_pk_list))

# -get dict of subjects of these studsubj_rows
    studsubj_rows = grd_exc.create_ex1_rows(sel_examyear, sel_school, sel_department)

    if studsubj_rows:

# - create Ex1 xlsx file
        response = grd_exc.create_ex1_xlsx(
            published_instance=published_instance,
            examyear=sel_examyear,
            school=sel_school,
            department=sel_department,
            settings=settings,
            save_to_disk=save_to_disk,
            subject_pk_list=subject_pk_list,
            subject_code_list=subject_code_list,
            studsubj_rows=studsubj_rows,
            user_lang=user_lang)

# --- end of create_Ex1

