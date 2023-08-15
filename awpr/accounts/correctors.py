# PR2023-03-23
import io
import tempfile
import xlsxwriter

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.files import File

from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect

from django.utils import timezone
from django.utils.decorators import method_decorator

# PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext, gettext_lazy as _, pgettext_lazy
from django.views.generic import View

from accounts import models as acc_mod
from accounts import permits as acc_prm
from accounts import views as acc_view
from awpr import settings as s
from awpr import constants as c

from awpr import functions as af
from awpr import excel as awpr_excel
from awpr import library as awpr_lib

from schools import models as sch_mod

import json
import logging
logger = logging.getLogger(__name__)


########################################################################
# === UserAllowedClusterUploadView ===================================== PR2023-02-26
@method_decorator([login_required], name='dispatch')
class UserAllowedClusterUploadView(View):
    # used in page correctors when schools set allowedcluster in user with role corrector
    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ')
            logger.debug(' ========== UserAllowedClusterUploadView ===============')

        def get_saved_allowedcluster_dict(allowed_cluster_list):
            saved_allowedcluster_dict = {}
            if allowed_cluster_list:
                sql = ''.join((
                    "SELECT id, school_id, department_id, subject_id, name ",
                    "FROM subjects_cluster ",
                    "WHERE id IN (SELECT UNNEST(ARRAY", str(allowed_cluster_list), "::INT[]))"
                ))
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    for row in cursor.fetchall():
                        # row:(1625, 37, 12, 269, 'V6beco')
                        if row[0] not in saved_allowedcluster_dict:
                            saved_allowedcluster_dict[row[0]] = {
                                'cluster_id': row[0],
                                'school_id': row[1],
                                'department_id': row[2],
                                'subject_id': row[3],
                                'name': row[4]
                            }
            return saved_allowedcluster_dict
########################

        msg_list = []
        border_class = None
        update_wrap = {}

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')
            # upload_dict: {'user_pk': 1472, 'mode': 'update', 'allowed_clusters': [1740, 1743]}

            if logging_on:
                logger.debug('    upload_dict:' + str(upload_dict))
# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get permit
            page_name = 'page_corrector'
            has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

            if not has_permit:
                border_class = c.HTMLCLASS_border_bg_invalid
                msg_list.append(acc_prm.err_txt_no_permit()) # default: 'to perform this action')
            else:

                sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                if err_list:
                    border_class = c.HTMLCLASS_border_bg_invalid
                    err_list.append(str(_('You cannot make changes.')))
                    msg_list.extend(err_list)

                elif sel_examyear and sel_school and sel_department:
    # - get variables
                    user_pk = upload_dict.get('user_pk')
                    user_instance = acc_mod.User.objects.get_or_none(pk=user_pk)
                    sel_examyear_instance = acc_prm.get_sel_examyear_from_user_instance(request.user)

    # - create student_row, also when deleting failed, not when deleted ok, in that case student_row is added in delete_student
                    userallowed_instance = acc_prm.get_userallowed_instance(user_instance, sel_examyear_instance)

                    if logging_on:
                        logger.debug('    user_instance:' + str(user_instance))
                        logger.debug('    userallowed_instance: ' + str(userallowed_instance))
                        logger.debug('    sel_school: ' + str(sel_school))
                        if sel_school:
                            logger.debug('    sel_schoolcode: ' + str(sel_school.base.code))
                            logger.debug('    sel_school_pke: ' + str(sel_school.pk))

                    if userallowed_instance:
                        saved_userallowed_cluster_pk_list = acc_prm.get_userallowed_cluster_pk_list(userallowed_instance)
                        if logging_on:
                            logger.debug('    saved_userallowed_cluster_pk_list:' + str(saved_userallowed_cluster_pk_list))

                        saved_allowedcluster_dict = get_saved_allowedcluster_dict(saved_userallowed_cluster_pk_list)
                        if logging_on:
                            logger.debug('    saved_allowedcluster_dict:' + str(saved_allowedcluster_dict))
                        # saved_allowedcluster_dict:{
                        # 1625: {'id': 1625, 'school_id': 37, 'department_id': 12, 'subject_id': 269, 'name': 'V6beco'},
                        # 1601: {'id': 1601, 'school_id': 37, 'department_id': 11, 'subject_id': 239, 'name': 'H5ec'},
                        # 1628: {'id': 1628, 'school_id': 37, 'department_id': 12, 'subject_id': 239, 'name': 'V6ec'},
                        # 1597: {'id': 1597, 'school_id': 37, 'department_id': 11, 'subject_id': 269, 'name': 'H5beco'}}

                        new_allowed_clusters_str = None
                        has_changed = False
                        new_allowed_clusters_list = upload_dict.get('allowed_clusters')
                        if logging_on:
                            logger.debug(' >>>>   new_allowed_clusters_list:' + str(new_allowed_clusters_list))

                        new_allowedcluster_dict = get_saved_allowedcluster_dict(new_allowed_clusters_list)
                        if logging_on:
                            logger.debug(' @@@@   new_allowedcluster_dict:' + str(new_allowedcluster_dict))

                        # loop through new clusters
                        for cluster_id, new_allowedcluster in new_allowedcluster_dict.items():
                            # skip if not this school and department
                            school_id = new_allowedcluster.get('school_id')
                            department_id = new_allowedcluster.get('department_id')

                            if logging_on:
                                logger.debug(' ... new cluster_id:' + str(cluster_id) + ' ' + str(new_allowedcluster.get('name')))
                                logger.debug('      sel_school.pk:' + str(sel_school.pk) + ' ' + str(type(sel_school.pk)))
                                logger.debug('      new school_id:' + str(school_id) + ' ' + str(type(school_id)))
                                logger.debug('      new department_id:' + str(department_id) + ' ' + str(type(department_id)))
                                logger.debug('      new sel_department.pk:' + str(sel_department.pk) + ' ' + str(type(sel_department.pk)))

                            if school_id == sel_school.pk:
                                if logging_on:
                                    logger.debug('      ...  school dep match')
                                if cluster_id not in saved_allowedcluster_dict:
                                    saved_allowedcluster_dict[cluster_id] = new_allowedcluster
                                    has_changed = True

                                    if logging_on:
                                        logger.debug(' ... add cluster_id:' + str(cluster_id))

                                # check if aleady in
                                subject_id = new_allowedcluster.get('subject_id')
                                name = new_allowedcluster.get('name')
                            else:
                                if logging_on:
                                    logger.debug('      >>  no school dep match')

                        # check if clusters are deleted:
                        for cluster_id, saved_allowedcluster in saved_allowedcluster_dict.items():

                            if logging_on:
                                logger.debug(' --- saved cluster_id:' + str(cluster_id) + ' ' + str(saved_allowedcluster.get('name')))

                            school_id = saved_allowedcluster.get('school_id')
                            department_id = saved_allowedcluster.get('department_id')
                            if school_id == sel_school.pk:
                                if logging_on:
                                    logger.debug(' ...  school dep match')
                                if cluster_id not in new_allowedcluster_dict:
                                    saved_allowedcluster_dict[cluster_id] = {'deleted': True}
                                    has_changed = True
                            else:
                                if logging_on:
                                    logger.debug(' >>  no school dep match')
                            if logging_on:
                                logger.debug(' --- del cluster_id:' + str(cluster_id))

                        if logging_on:
                            logger.debug('    has_changed: ' + str(has_changed))

                        # create list
                        if has_changed:
                            saved_allowedcluster_list = []
                            for cluster_id, saved_allowedcluster in saved_allowedcluster_dict.items():
                                if 'deleted' not in saved_allowedcluster:
                                    saved_allowedcluster_list.append(cluster_id)

                            new_allowed_clusters_str = None
                            if saved_allowedcluster_list:
                                saved_allowedcluster_list.sort()
                                new_allowed_clusters_str = json.dumps(saved_allowedcluster_list)

                            setattr(userallowed_instance, 'allowed_clusters', new_allowed_clusters_str)
                            userallowed_instance.save()

                            updated_corrector_rows = acc_view.create_user_rowsNEW(
                                sel_examyear=userallowed_instance.examyear if userallowed_instance else None,
                                request=request,
                                school_correctors_only=True,
                                user_pk=user_pk
                            )

                            if logging_on:
                                logger.debug('    updated_corrector_rows: ' + str(updated_corrector_rows))
                            if updated_corrector_rows:
                                update_wrap['updated_corrector_rows'] = updated_corrector_rows

# - addd msg_html to update_wrap

        if msg_list:
            update_wrap['msg_html'] = acc_prm.msghtml_from_msglist_with_border(msg_list, border_class)
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - ens of UserAllowedClusterUploadView

########################################################################
# === UserUploadView ===================================== PR2023-02-25 PR2023-05-12
@method_decorator([login_required], name='dispatch')
class UserCompensationUploadView(View):

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ')
            logger.debug(' ========== UserCompensationUploadView ===============')

        msg_list = []
        update_wrap = {}

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')
            # upload_dict: {'mode': 'update', 'usercompensation_pk': 609, 'uc_meetings': 1}

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get permit
            has_permit = acc_prm.get_permit_of_this_page('page_corrector', ['crud', 'approve_comp'], request)
            if not has_permit:
                msg_list.append(acc_prm.err_txt_no_permit()) # default: 'to perform this action')
            else:
                updated_rows = []
# - get variables
                usercompensation_pk = upload_dict.get('usercompensation_pk')

# ----- get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_edit, sel_msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if logging_on:
                    logger.debug('    may_edit:       ' + str(may_edit))
                    logger.debug('    sel_msg_list:       ' + str(sel_msg_list))
                    logger.debug('    upload_dict:       ' + str(upload_dict))

                if sel_msg_list:
                    msg_list.extend(sel_msg_list)

                else:
# +++  get existing usercompensation_instance
                    usercompensation_instance = acc_mod.UserCompensation.objects.get_or_none(
                        id=usercompensation_pk
                    )
                    if usercompensation_instance:
                        if logging_on:
                            logger.debug('    usercompensation_instance: ' + str(usercompensation_instance))
# +++ Update usercompensation_instance
                        changes_are_saved, err_lst = \
                            update_usercompensation_instance(
                                instance=usercompensation_instance,
                                upload_dict=upload_dict,
                                request=request
                            )
                        if err_lst:
                            msg_list.extend(err_lst)

# - create usercompensation_rows
                        if changes_are_saved:
                            updated_rows = create_usercompensation_rows(
                                sel_examyear=sel_examyear,
                                sel_department=sel_department,
                                sel_lvlbase=sel_level.base if sel_level else None,
                                request=request)

                update_wrap['updated_usercompensation_rows'] = updated_rows

    # show modmessage when single update
        if msg_list:
            update_wrap['msg_html'] = ''.join((
                "<div class='p-2 ", c.HTMLCLASS_border_bg_invalid, "'>",
                ''.join(msg_list),
                "</div>"))
            if logging_on:
                logger.debug('msg_list:    ' + str(msg_list))


# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UserCompensationUploadView

#######################################################
def update_usercompensation_instance(instance, upload_dict, request):
    # --- update existing and new instance PR2023-02-25 PR2023-04-17 PR2023-07-11

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_usercompensation_instance -------')
        logger.debug('    upload_dict: ' + str(upload_dict))
        logger.debug('    instance:    ' + str(instance))

# ----- get user_lang
    must_calc_comp = False
    changes_are_saved = False

    err_list = []

    if instance:

        is_approved = True if getattr(instance, 'auth1by_id') or \
                              getattr(instance, 'auth2by_id') else False
        is_published = True if getattr(instance, 'published_id') else False

        save_changes = False
        for field, new_value in upload_dict.items():
            if logging_on:
                logger.debug('    field: ' + str(field))
                logger.debug('    is_approved: ' + str(is_approved))
                logger.debug('    is_published: ' + str(is_published))

    # - save changes in fields
            # field 'amount' is updated in download.py update_usercompensation, every time usercompensation_rows are downloaded
            # was: if field in ('amount', 'meetings', 'correction_amount', 'correction_meetings'):

        # - dont update meeting when compensation is already approved or submitted
            if field in ('meetings', 'meetingdate1', 'meetingdate2') and (is_approved or is_published):

                if not err_list: # to prevent double msg (meetings and meetingdate have both value)
                    this_comp_txt = gettext('This compensation')
                    submitted_approved_txt = gettext('Submitted') if is_published else gettext('Approved')
                    change_delete = str(_('Change') if new_value else _('Delete')).lower()
                    err_list.extend((
                        (str(_("%(cpt)s' is already %(publ_appr_cpt)s.")
                            % {'cpt': this_comp_txt, 'publ_appr_cpt': submitted_approved_txt.lower()})),
                        '<br>',
                        gettext("You cannot %(ch_del)s %(cpt)s.")
                            % {'ch_del': change_delete, 'cpt':gettext('this meeting')}
                    ))

            elif field in ('meetings', 'meetingdate1', 'meetingdate2') and (instance.user != request.user):
                if not err_list: # to prevent double msg (meetings and meetingdate have both value)
                    err_list.append(gettext('A meeting can only be entered by the second corrector himself.'))
            else:
                if field in ('meetings', 'correction_amount', 'correction_meetings'):
                    saved_value = getattr(instance, field) or 0
                    if new_value is None:
                        new_value = 0

                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True
                        must_calc_comp = True

                elif field in ('meetingdate1', 'meetingdate2'):
                    saved_value = getattr(instance, field)
                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True

                elif field in ('auth1by', 'auth2by'):
                    # field 'auth1by' contains boolean, replace by requsr.pk when true or None when False
                    #only school can approve meetings
                    if request.user.role == c.ROLE_008_SCHOOL:
                        if new_value:
                            new_auth = acc_mod.User.objects.get_or_none(pk=request.user.pk)
                        else:
                            new_auth = None
                        saved_auth = getattr(instance, field)

                        if new_auth != saved_auth:
                            setattr(instance, field, new_auth)
                            save_changes = True
                    else:
                        err_list.append(gettext("Only the school can approve compensations."))

    # - save changes
        if save_changes:
            if must_calc_comp:
                new_comp = calc_compensation(
                        approvals_sum=getattr(instance, 'amount') or 0,
                        meetings_sum=getattr(instance, 'meetings') or 0,
                        approvals_sum_correction=getattr(instance, 'correction_amount') or 0,
                        meetings_sum_corrections=getattr(instance, 'correction_meetings') or 0,
                    )
                setattr(instance, 'compensation', new_comp)
            try:
                instance.save(request=request)
                changes_are_saved = True
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                err_list.append(acc_prm.errhtml_error_occurred_no_border(e, _('The changes have not been saved.')))

    if logging_on:
        logger.debug('    changes_are_saved: ' + str(changes_are_saved))

    return changes_are_saved, err_list
# - end of update_usercompensation_instance


#####################################################################################
@method_decorator([login_required], name='dispatch')
class UserCompensationApproveSubmitView(View):  # PR2021-07-26 PR2022-05-30 PR2023-01-10

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UserCompensationApproveSubmitView ============= ')

        def approve_usercomp(usercomp_row, requsr_auth, is_test, is_reset, count_dict, tobe_updated_usercomp_pk_list, tobe_updated_user_pk_list, request):
            # PR2023-07-09
            # auth_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
            #  prefix = 'reex3_'  'reex_'  'subj_'

            # PR2022-12-30 instead of updating each usercomp instance separately, create list of tobesaved usercomp_pk
            # list is created outside this function, when is_saved = True

            logging_on = False  # s.LOGGING_ON
            if logging_on:
                logger.debug('----- approve_usercomp -----')
                logger.debug('    requsr_auth:  ' + str(requsr_auth))
                logger.debug('    is_reset:     ' + str(is_reset))
                logger.debug('    usercomp_row:     ' + str(usercomp_row))

            if usercomp_row:
                req_user = request.user

    # - skip when this usercomp_row is already published
                if usercomp_row.get('published_id'):
                    af.add_one_to_count_dict(count_dict, 'already_published')
                else:
        # auth fields in table Usercompensation are: auth1by_id, auth2by_id
                    auth1by_id = usercomp_row.get('auth1by_id')
                    auth2by_id = usercomp_row.get('auth2by_id')

                    save_changes = False

         # - remove authby when is_reset
                    if is_reset:
                        af.add_one_to_count_dict(count_dict, 'reset')
                        save_changes = True
                    else:

        # - skip if this usercomp_row is already approved
                        requsr_authby_value = auth1by_id if requsr_auth == 'auth1' else auth2by_id if requsr_auth == 'auth2' else None
                        if requsr_authby_value:
                            af.add_one_to_count_dict(count_dict, 'already_approved')
                        else:

        # - skip if this author (like 'chairperson') has already approved this usercomp_row
                            # under a different permit (like 'secretary' or 'corrector')

                            double_approved = False
                            if requsr_auth == 'auth1':
                                double_approved = True if auth2by_id and auth2by_id == req_user.pk else False
                            elif requsr_auth == 'auth2':
                                double_approved = True if auth1by_id and auth1by_id == req_user.pk else False

                            if double_approved:
                                af.add_one_to_count_dict(count_dict, 'double_approved')
                            else:
                                save_changes = True

        # - add usercomp to tobe_updated_usercomp_pk_list, and user_pk to tobe_updated_user_pk_list
                    if save_changes:

                        usercomp_pk = usercomp_row.get('id')
                        if usercomp_pk:
                            tobe_updated_usercomp_pk_list.append(usercomp_pk)

                        user_pk = usercomp_row.get('user_id')
                        if user_pk and user_pk not in tobe_updated_user_pk_list:
                            tobe_updated_user_pk_list.append(user_pk)

        # - add 1 to count_dict committed
                        af.add_one_to_count_dict(count_dict, 'committed')
        # - end of approve_usercomp

        def submit_usercomp(usercomp_row, is_test, count_dict, tobe_updated_usercomp_pk_list, tobe_updated_user_pk_list):
            # PR2021-01-21 PR2021-07-27 PR2022-05-30 PR2022-12-30 PR2023-02-12

            # PR2022-12-30 instead of updating each studsubj instance separately, create list of tobesaved studsubj_pk
            # list is created outside this function, when is_saved = True

            logging_on = False  # s.LOGGING_ON
            if logging_on:
                logger.debug('----- submit_usercomp -----')
                logger.debug('    requsr_auth:  ' + str(requsr_auth))
                logger.debug('    is_test:     ' + str(is_test))
                logger.debug('    count_dict:     ' + str(count_dict))

            if usercomp_row:

    # - skip when this usercomp_row is already published
                if usercomp_row.get('published_id'):
                    af.add_one_to_count_dict(count_dict, 'already_published')
                else:

        # - check if this studsubj / examtype is approved by all auth
                    auth1by_id = usercomp_row.get('auth1by_id')
                    auth2by_id = usercomp_row.get('auth2by_id')
                    auth_missing = auth1by_id is None or auth2by_id is None

                    if auth_missing:
                        af.add_one_to_count_dict(count_dict, 'auth_missing')
                    else:

        # - skip if this author (like 'chairperson') has already approved this usercomp_row
                            # under a different permit (like 'secretary' or 'corrector')

                        double_approved = auth1by_id == auth2by_id
                        if double_approved:
                            af.add_one_to_count_dict(count_dict, 'double_approved')
                        else:

        # - add usercomp to tobe_updated_usercomp_pk_list, and user_pk to tobe_updated_user_pk_list
                            usercomp_pk = usercomp_row.get('id')
                            if usercomp_pk:
                                tobe_updated_usercomp_pk_list.append(usercomp_pk)

                            user_pk = usercomp_row.get('user_id')
                            if user_pk and user_pk not in tobe_updated_user_pk_list:
                                tobe_updated_user_pk_list.append(user_pk)

                            # - add 1 to count_dict committed
                            af.add_one_to_count_dict(count_dict, 'committed')
        # - end of submit_usercomp

        def create_published_usercomp_instance(sel_school, sel_department, sel_level, now_arr, request):
            # PR2023-03-23
            if logging_on:
                logger.debug('----- create_published_usercomp_instance -----')
                logger.debug('     sel_school: ' + str(sel_school))
                logger.debug('     sel_department: ' + str(sel_department))
                logger.debug('     sel_level: ' + str(sel_level))
                logger.debug('     now_arr: ' + str(now_arr))
                logger.debug('     request.user: ' + str(request.user))

            # create new published_instance and save it when it is not a test (this function is only called when it is not a test)
            # filename is added after creating file in create_ex1_xlsx
            depbase_code = sel_department.base.code if sel_department.base.code else '-'
            school_code = sel_school.base.code if sel_school.base.code else '-'
            school_abbrev = sel_school.abbrev if sel_school.abbrev else '-'

            if sel_level and sel_department.level_req and sel_level.abbrev:
                depbase_code += ' ' + sel_level.abbrev

            if logging_on:
                logger.debug('     depbase_code:  ' + str(depbase_code))
                logger.debug('     school_code:   ' + str(school_code))
                logger.debug('     school_abbrev: ' + str(school_abbrev))

            # to be used when submitting form
            exform = gettext('Compensation correctors')

            if logging_on:
                logger.debug('     exform:       ' + str(exform))

            today_date = af.get_date_from_arr(now_arr)
            if logging_on:
                logger.debug('     today_date: ' + str(today_date) + ' ' + str(type(today_date)))

            year_str = str(now_arr[0])
            month_str = ("00" + str(now_arr[1]))[-2:]
            date_str = ("00" + str(now_arr[2]))[-2:]
            hour_str = ("00" + str(now_arr[3]))[-2:]
            minute_str = ("00" + str(now_arr[4]))[-2:]
            now_formatted = ''.join([year_str, "-", month_str, "-", date_str, " ", hour_str, "u", minute_str])

            file_name = ' '.join((exform, school_code, school_abbrev, depbase_code, now_formatted))
            # skip school_abbrev if total file_name is too long
            if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
                file_name = ' '.join((exform, school_code, depbase_code, now_formatted))
            # if total file_name is still too long: cut off
            if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
                file_name = file_name[0:c.MAX_LENGTH_FIRSTLASTNAME]

            if logging_on:
                logger.debug('     file_name: ' + str(file_name))

            published_instance = None
            try:
                # sel_examtype = '-'
                published_instance = sch_mod.Published(
                    school=sel_school,
                    department=sel_department,
                    examperiod=0,
                    name=file_name,
                    datepublished=today_date
                )

                published_instance.filename = file_name + '.xlsx'

                published_instance.save(request=request)

                if logging_on:
                    logger.debug('     published_instance.saved: ' + str(published_instance))
                    logger.debug('     published_instance.pk: ' + str(published_instance.pk))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

            return published_instance
        # - end of create_published_usercomp_instance

        def batch_update_usercomp(usercomp_pk_list, is_submit, is_reset, requsr_auth, req_user, published_pk):
            # PR2023-07-09 PR2023-07-16

            if logging_on:
                logger.debug(' ')
                logger.debug('----- batch_update_usercomp -----')

            updated_usercomp_pk_list = []
            updated_user_pk_list = []
            err_list = []

            try:
                requsr_authby_field = 'published_id' if is_submit else ''.join((requsr_auth, 'by_id'))

        # - remove authby when is_reset
                requsr_authby_value = "NULL" if is_reset else str(published_pk) if is_submit else str(req_user.pk)

                sql_list = ["UPDATE accounts_usercompensation",
                            " SET", requsr_authby_field, "=", requsr_authby_value,
                            " WHERE id IN (SELECT UNNEST(ARRAY", str(usercomp_pk_list), "::INT[]))",
                            " RETURNING id, user_id;"]
                sql = ' '.join(sql_list)

                if logging_on:
                    logger.debug('    sql: ' + str(sql))

                with connection.cursor() as cursor:
                    cursor.execute(sql)

                    rows = cursor.fetchall()
                    if rows:
                        for row in rows:
                            updated_usercomp_pk_list.append(row[0])
                            if row[1] not in updated_user_pk_list:
                                updated_user_pk_list.append(row[1])

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

                action_txt = str(_('submitted') if is_submit else _('approved'))
                cpt = gettext('compensations')
                err_txt = gettext('The %(cpt)s could not be %(action)s.') % {'cpt': cpt, 'action': action_txt}
                err_list = acc_prm.errlist_error_occurred(e, err_txt)

            if logging_on:
                logger.debug('    updated_usercomp_pk_list: ' + str(updated_usercomp_pk_list))
                logger.debug('    updated_user_pk_list: ' + str(updated_user_pk_list))
                logger.debug('    err_list: ' + str(err_list))
            return updated_usercomp_pk_list, updated_user_pk_list, err_list
        # - end of batch_update_usercomp

        def create_approve_msg_list(sel_department, sel_level, count_dict,
                                updated_usercomp_count, updated_user_count, err_list, requsr_auth, is_test):
            # PR2023-07-16
            logging_on = s.LOGGING_ON
            if logging_on:
                logger.debug('  ----- create_msg_list -----')
                logger.debug('    count_dict: ' + str(count_dict))
                logger.debug('    is_test: ' + str(is_test))
                logger.debug('    count_dict: ' + str(count_dict))
                logger.debug('    updated_usercomp_count: ' + str(updated_usercomp_count))
                logger.debug('    err_list: ' + str(err_list))

            count = count_dict.get('count', 0)
            committed = count_dict.get('committed', 0)
            already_published = count_dict.get('already_published', 0)
            all_published = count and already_published == count

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
                logger.debug('.....all_published: ' + str(all_published))

            class_str = 'border_bg_transparent'

            exam_txt = gettext('Exam').lower()
            exams_txt = gettext('Exams').lower()

            corrector_count_txt = af.get_item_count_text(updated_user_count, 'Second corrector', 'Second correctors')

            msg_list = []

            try:
# ++++++++++++++++ is_test +++++++++++++++++++++++++
                if is_test:
                    exam_count_txt = af.get_item_count_text(count, 'Exam', 'Exams')

            # - create  line with 'The selection contains no exams'
                    if not count:
                        msg_list.append(gettext("The selection contains %(val)s.") % {'val': exam_count_txt})
                    else:
            # - create  line with 'The selection contains only the learning path'
                        level_html = ''
                        if sel_department.level_req and sel_level and sel_level.abbrev:
                            level_html = '<br>' + str(
                                _('The selection contains only %(cpt)s of the learning path: %(lvl_abbrev)s.') % {
                                    'cpt': gettext('Second correctors').lower(), 'lvl_abbrev': sel_level.abbrev})

            # - create  line with 'The selection contains 4 the compensation of 39 exams'
                        msg_list.extend(("<div class='pb-2'>",
                                         gettext("The selection contains %(val)s.") %
                                             {'val': exam_count_txt}, ' ',
                                         level_html,
                                         '</div>'))

            # -  create lines 'The compensation of all exams will be approved'
                        if committed == count:
                            class_str = 'border_bg_valid'
                            msg_list.extend(("<div>",
                                             gettext("The compensation of all exams will be approved."),
                                             '</div>'
                                             ))
                        else:
            # - if any subjects skipped: create lines 'De volgende examens worden overgeslagen:' plus the reason
                            willbe_txt = str(pgettext_lazy('plural', 'will be') )
                            msg_list.extend(("<div>",
                                                gettext("The following %(cpt)s %(willbe)s skipped")
                                                    % {'cpt': exams_txt, 'willbe': willbe_txt},
                                                ":</div><ul class='my-0 pb-2'>"
                                             ))
                            if already_published:
                                msg_list.extend(('<li>',
                                                 gettext("%(val)s already submitted")
                                                    % {'val': af.get_items_are_text(already_published, exam_txt, exams_txt, is_test)},
                                                 '</li>'
                                                 ))

                            # not used when is_test
                            #   if auth_missing:

                            if already_approved:
                                msg_list.extend(('<li>',
                                                 af.get_items_are_text(already_approved, exam_txt, exams_txt, False),
                                                 gettext(' already approved'),
                                                 '</li>'))

                            if double_approved:
                                class_str = 'border_bg_invalid'
                                other_function = gettext('chairperson') if requsr_auth == 'auth2' else gettext('secretary')
                                caption = gettext('exam')
                                msg_list.extend(('<li>',
                                                 af.get_items_are_text(double_approved, exam_txt, exams_txt, False),
                                                        gettext(' already approved by you as '), other_function, '.<br>',
                                               gettext("You cannot approve a %(cpt)s both as chairperson and as secretary.") % {'cpt': caption},
                                                 '</li>'
                                                 ))

                            msg_list.append('</ul>')

                    # - line with text how many subjects will be approved
                            if not committed:
                                msg_list.extend(("<div>",
                                                gettext("No %(cpts)s will be approved.") % {'cpts': gettext('compensations')},
                                                 '</div>'
                                                 ))
                            else:
                                class_str = 'border_bg_valid'
                                item_count_text = af.get_item_count_text(committed, 'Exam', 'Exams')
                                will_be_text = af.get_will_be_text(1) # singular
                                msg_list.extend(("<div>",
                                                    gettext('The compensation'), ' ', gettext('of'), ' ',
                                                    item_count_text, ' ', gettext('of'), ' ',
                                                    str(corrector_count_txt), ' ',
                                                    will_be_text, ' ', gettext('approved'), '.',
                                                    '</div>'
                                                ))

    # ++++++++++++++++ not is_test +++++++++++++++++++++++++
                else:
                    if err_list:
                        class_str = 'border_bg_invalid'
                        msg_list.extend(err_list)

                    # - line with text how many exams have been approved
                    elif not updated_usercomp_count:
                        class_str = 'border_bg_invalid'
                        msg_list.append(gettext("No compensations have been approved."))

                    else:
                        class_str = 'border_bg_valid'
                        corrector_count_txt = af.get_item_count_text(updated_user_count, 'Second corrector', 'Second correctors')

                        item_count_text = af.get_item_count_text(updated_usercomp_count, 'Exam', 'Exams')

                        has_been_txt = af.get_have_has_been_txt(1) # singular
                        msg_list.extend((
                            gettext('The compensation'),  ' ', gettext('of'), ' ',
                                    str(item_count_text), ' ', gettext('of'), ' ',
                                           str(corrector_count_txt), ' ',
                                           str(has_been_txt), ' ', gettext('approved'), '.'))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

            #######################################

            msg_html = ''.join((
                "<div class='p-2 ", class_str, "'>",
                ''.join(msg_list),
                '</div>'
            ))
            if logging_on:
                logger.debug('   class_str: ' + str(class_str))
                logger.debug('   msg_list: ' + str(msg_list))
                logger.debug('   msg_html: ' + str(msg_html))

            return msg_html
        # - end of create_approve_msg_list

        def create_submit_msg_list(sel_department, sel_level, count_dict, updated_usercomp_count, updated_user_count, err_list, requsr_auth, is_test, test_has_failed,
                            published_instance_filename, published_instance_file_url):
            # PR2023-07-16
            logging_on = s.LOGGING_ON
            if logging_on:
                logger.debug('  ----- create_submit_msg_list -----')
                logger.debug('    count_dict: ' + str(count_dict))
                logger.debug('    is_test: ' + str(is_test))

            count = count_dict.get('count', 0)

            committed = count_dict.get('committed', 0)
            saved = count_dict.get('saved', 0)
            already_published = count_dict.get('already_published', 0)

            all_published = count and already_published == count

            auth_missing = count_dict.get('auth_missing', 0)
            already_approved = count_dict.get('already_approved', 0)
            double_approved = count_dict.get('double_approved', 0)

            if logging_on:
                logger.debug('    count: ' + str(count))
                logger.debug('    committed: ' + str(committed))
                logger.debug('    already_published: ' + str(already_published))
                logger.debug('    auth_missing: ' + str(auth_missing))
                logger.debug('    already_approved: ' + str(already_approved))
                logger.debug('    double_approved: ' + str(double_approved))
                logger.debug('    all_published: ' + str(all_published))
                logger.debug('    test_has_failed: ' + str(test_has_failed))

            show_msg_first_approve_by_pres_secr = False
            show_msg_request_verifcode = False
            class_str = 'border_bg_invalid' if test_has_failed else 'border_bg_valid' if committed else 'border_bg_transparent'

            exam_txt = gettext('Exam').lower()
            exams_txt = gettext('Exams').lower()

            msg_list = []
            try:

 # ++++++++++++++++ is_test +++++++++++++++++++++++++
                if is_test:

        # - create  line with 'The selection contains only the learning path'
                    level_html = ''
                    if sel_department.level_req and sel_level and sel_level.abbrev:
                        level_html = '<br>' + str(
                            _('The selection contains only %(cpt)s of the learning path: %(lvl_abbrev)s.') % {
                                'cpt': gettext('Second correctors').lower(), 'lvl_abbrev': sel_level.abbrev})

        # - create  line with 'The selection contains 4 candidates with 39 subjects'
                    corrector_count_txt = af.get_item_count_text(updated_user_count, 'Second corrector', 'Second correctors')
                    exam_count_txt = af.get_item_count_text(count, 'Exam', 'Exams')
                    msg_list.extend(("<div class='pb-2'>",
                                     gettext("The selection contains %(val)s.") %
                                     {'val': exam_count_txt}, ' ',
                                     level_html,
                                     '</div>'))

        # - create  line with 'All compensations are already submitted'
                    if all_published:
                        msg_list.extend(("<div>",
                            gettext("All %(cpts)s are already submitted.") % {'cpts': gettext('compensations')},
                            '</div>'
                        ))
                    else:
        # - create  line with '5  are not fully approved'
                        if auth_missing or double_approved:
                            msg_list.append("<ul class='mb-0 pb-2'>")
                        if auth_missing:
                            show_msg_first_approve_by_pres_secr = True
                            msg_list.extend(('<li>',
                                             af.get_items_are_text(auth_missing, 'Compensation', 'compensations', False),
                                                    gettext(" not fully approved."),
                                             '</li>'
                                             ))
                        if double_approved:
                            #class_str = 'border_bg_invalid'
                            other_function = gettext('chairperson') if requsr_auth == 'auth2' else gettext('secretary')
                            caption = gettext('exam')
                            msg_list.extend(('<li>',
                                 af.get_items_are_text(double_approved, exam_txt, exams_txt, False),
                                 gettext(' already approved by you as '), other_function, '.<br>',
                                 gettext("You cannot approve a %(cpt)s both as chairperson and as secretary.") % {
                                     'cpt': caption},
                                 '</li>'
                                 ))

                        if auth_missing or double_approved:
                            msg_list.append('</ul>')

                        if test_has_failed:
                            msg_list.extend(("<div>",
                                 gettext('The %(frm)s form can not be submitted.') % {'frm': gettext('compensations')},
                                 '</div>'
                                 ))
                        else:
                            show_msg_request_verifcode = True
                            class_str = 'border_bg_valid'
                            item_count_text = af.get_item_count_text(committed, 'Exam', 'Exams')
                            will_be_text = af.get_will_be_text(1)  # singular
                            msg_list.extend(("<div>",
                                             gettext('The compensation'), ' ', gettext('of'), ' ',
                                             item_count_text, ' ', gettext('of'), ' ',
                                             str(corrector_count_txt), ' ',
                                             will_be_text, ' ', gettext('submitted'), '.',
                                             '</div>'
                                             ))


        # - add line 'both prseident and secretary must first approve all subjects before you can submit the Ex form
                        if show_msg_first_approve_by_pres_secr:
                            msg_list.extend(("<div class='pt-2'>",
                                             gettext(
                                                 'The chairperson and the secretary must approve all %(cpt)s<br>before you can submit the %(frm)s form.')
                                             % {'cpt': gettext('compensations'), 'frm': gettext('compensations')},
                                             '</div>'
                                             ))

    # ++++++++++++++++ not is_test +++++++++++++++++++++++++
                else:
                    if err_list:
                        class_str = 'border_bg_invalid'
                        msg_list.extend(err_list)

        # - line with text how many exams have been submitted
                    elif not updated_usercomp_count:
                        class_str = 'border_bg_invalid'
                        msg_list.append(gettext("The %(frm)s form has not been submitted.") % {'frm': gettext('compensation')})

                    else:
                        class_str = 'border_bg_valid'

                        msg_list.extend((
                            gettext("The %(frm)s form has been submitted.") % {'frm': gettext('compensations')}, ' ',
                            gettext("Click <a href='%(href)s' class='awp_href' target='_blank'>here</a> to download it.")
                            % {'href': published_instance_file_url},
                            '<br>',
                            gettext("It has been saved in the page 'Archive' as '%(frm)s'.")
                            % {'frm': published_instance_filename},
                        ))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

#######################################




            msg_html = ''.join((
                "<div class='p-2 ", class_str, "'>",
                ''.join(msg_list),
                '</div>'
            ))
            # - create 'You need a 6 digit verification code' line
            # PR2023-07-12 added: only when is test

            if show_msg_request_verifcode:
                msg_html += ''.join((
                    "<div class='p-2 my-1 ", c.HTMLCLASS_border_bg_transparent, "'>",
                    gettext("You need a 6 digit verification code to submit the %(frm)s form.") % {'frm': gettext('compensations')}, '<br>',
                    gettext(
                        "Click 'Request verification code' and we will send you an email with the verification code."),
                    '<br>',
                    gettext("The verification code expires in 30 minutes."),
                    '</div>'
                ))

            if logging_on:
                logger.debug('   class_str: ' + str(class_str))
                logger.debug('   msg_list: ' + str(msg_list))
                logger.debug('   msg_html: ' + str(msg_html))

            return msg_html
        # - end of create_submit_msg_list

################################
# function sets auth and publish of studentsubject records of current department # PR2021-07-25
        update_wrap = {}
        requsr_auth = None
        msg_html = None

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

        # - get permit
        # <PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated

        has_permit = False
        req_usr = request.user

        if req_usr.country and req_usr.schoolbase:

            permit_list = acc_prm.get_permit_list('page_corrector', req_usr)
            if logging_on:
                logger.debug('    permit_list: ' + str(permit_list))

            if permit_list and 'permit_approve_comp' in permit_list:
                # msg_err is made on client side. Here: just skip if user has no or multiple functions

                # PR2023-02-12 was: requsr_usergroup_list, allowed_sections_dictNIU, allowed_clusters_list, sel_examyear_instance = acc_prm.get_allowedusergrouplist_allowedsectionsdict_allowedclusterlist(req_usr)
                userallowed_instance = acc_prm.get_userallowed_instance_from_user_instance(req_usr)
                requsr_usergroup_list = acc_prm.get_usergroup_list(userallowed_instance)
                if logging_on:
                    logger.debug('    requsr_usergroup_list: ' + str(requsr_usergroup_list))

                is_auth1 = (requsr_usergroup_list and 'auth1' in requsr_usergroup_list)
                is_auth2 = (requsr_usergroup_list and 'auth2' in requsr_usergroup_list)
                if is_auth1 + is_auth2 == 1:
                    if is_auth1:
                        requsr_auth = 'auth1'
                    elif is_auth2:
                        requsr_auth = 'auth2'
                if requsr_auth:
                    has_permit = True

            if logging_on:
                logger.debug('    has_permit:  ' + str(has_permit))

        if not has_permit:
            msg_html = acc_prm.err_html_no_permit()  # default: 'to perform this action')
        else:

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
                # not af.is_allowed_depbase_requsr or not af.is_allowed_depbase_school,

                sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                form_name = upload_dict.get('form') or '---'

# - get selected mode. Modes are 'approve_test', 'approve_save', 'approve_reset', 'submit_test' 'submit_save'
                mode = upload_dict.get('mode')
                is_approve = True if mode in ('approve_test', 'approve_save', 'approve_reset') else False
                is_submit = True if mode in ('submit_test', 'submit_save') else False
                is_reset = True if mode == 'approve_reset' else False
                is_test = True if mode in ('approve_test', 'submit_test') else False

                if logging_on:
                    logger.debug('    upload_dict ' + str(upload_dict))
                    logger.debug('    mode:       ' + str(mode))
                    logger.debug('    is_submit:       ' + str(is_submit))
                    logger.debug('    is_test:       ' + str(is_test))

# - when mode = submit_submit: check verificationcode.
                verification_is_ok = True
                if is_submit and not is_test:
                    upload_dict['form'] = form_name
                    verification_is_ok, verif_msg_html = af.check_verifcode_local(upload_dict, request)
                    if verif_msg_html:
                        msg_html = verif_msg_html
                    if verification_is_ok:
                        update_wrap['verification_is_ok'] = True

                if logging_on:
                    logger.debug('    verif_is_ok: ' + str(verification_is_ok))
                    logger.debug('    msg_html:    ' + str(msg_html))

                if verification_is_ok:
                    #sel_lvlbase_pk, sel_sctbase_pk, sel_subject_pk, sel_cluster_pk, sel_student_pk = None, None, None, None, None
                    # don't filter on sel_sctbase_pk, sel_subject_pk, sel_cluster_pk or allowed when is_submit
                    # PR2023-01-10 may filter on level, so MPC TKL can submit their own Ex1

                    if logging_on:
                        logger.debug('    is_approve: ' + str(is_approve))

# +++ get selected studsubj_rows
                    # PR2023-01-09 new approach:
                    # - include published studsubjects
                    # - include tobedeleted studsubjects
                    # when a subject is set 'tobedeleted', the published info is removed, to show up when submitted

        # when submit: don't filter on sector, subject or cluster
                    # PR2023-02-12 request MPC: must be able to submit per level tkl / pkl/pbl
                    # also filter on level when submitting Ex form

                    usercomp_rows, auth1_list, auth2_list = get_usercomp_rows(sel_examyear.pk, sel_school.base_id, upload_dict, user_lang)

                    if logging_on:
                        logger.debug('    row_count:      ' + str(len(usercomp_rows)))

                    count_dict = {}

                    if usercomp_rows:

# +++ create new published_instance. Only save it when it is not a test
                        # file_name will be added after creating Ex-form
                        published_instance = None
                        published_instance_pk = None
                        published_instance_filename = None
                        if is_submit and not is_test:
                            now_arr = upload_dict.get('now_arr')

                            published_instance = create_published_usercomp_instance(
                                sel_school=sel_school,
                                sel_department=sel_department,
                                sel_level=sel_level,
                                now_arr=now_arr,
                                request=request
                            )
                            if published_instance:
                                published_instance_pk = published_instance.pk
                                published_instance_filename = published_instance.filename

                        if logging_on:
                            logger.debug('    published_instance_pk: ' + str(published_instance_pk))
                            logger.debug('    published_instance_filename: ' + str(published_instance_filename))

                        studsubj_rows = []

                        row_count = 0

                        # PR2022-12-30 instead of updating each studsubj instance separately, create list of tobesaved studsubj_pk
                        # and batch update at the end
                        tobe_updated_usercomp_pk_list = []
                        tobe_updated_user_pk_list = []

# +++++ loop through usercomp_rows +++++
                        for usercomp_row in usercomp_rows:

                            if logging_on and False:
                                logger.debug('............ ')
                                logger.debug('   ' + str(usercomp_row))

                            row_count += 1

                            if is_approve:
                                approve_usercomp(
                                    usercomp_row=usercomp_row,
                                    requsr_auth=requsr_auth,
                                    is_test=is_test,
                                    is_reset=is_reset,
                                    count_dict=count_dict,
                                    tobe_updated_usercomp_pk_list=tobe_updated_usercomp_pk_list,
                                    tobe_updated_user_pk_list=tobe_updated_user_pk_list,
                                    request=request
                                )

                            elif is_submit:
                                submit_usercomp(
                                    usercomp_row=usercomp_row,
                                    is_test=is_test,
                                    count_dict=count_dict,
                                    tobe_updated_usercomp_pk_list=tobe_updated_usercomp_pk_list,
                                    tobe_updated_user_pk_list=tobe_updated_user_pk_list,
                                )

# +++++  end of loop through  studsubjects

                        auth_missing_count = count_dict.get('auth_missing', 0)
                        double_approved_count = count_dict.get('double_approved', 0)

                        test_has_failed = False
                        if is_test:
                            if not row_count:
                                test_has_failed = True
                            elif is_submit and auth_missing_count:
                                test_has_failed = True
                            elif is_submit and double_approved_count:
                                test_has_failed = True
                            elif not tobe_updated_usercomp_pk_list:
                                test_has_failed = True


                        count_dict['count'] = row_count

                        updated_usercomp_pk_list = []
                        updated_user_pk_list = []

                        err_list = []

                        published_instance_file_url = None

                        update_wrap['approve_count_dict'] = count_dict

                        if not test_has_failed:
                            update_wrap['test_is_ok'] = True

# +++++ create compensation form
                        if is_submit and not is_test and row_count:
                    # form may be printed without new approvals - ( or not ? > in that case add if tobe_updated_usercomp_pk_list )
                            save_to_disk = True
                            responseNIU, is_saved_to_disk = create_excomp_xlsx(
                                published_instance=published_instance,
                                sel_examyear=sel_examyear,
                                sel_school=sel_school,
                                save_to_disk=save_to_disk,
                                request=request,
                                user_lang=user_lang
                            )

                            if is_saved_to_disk and published_instance.file:
                                published_instance_file_url = published_instance.file.url


        # +++++ batch save approval / published PR2023-07-09
                        if not is_test and tobe_updated_usercomp_pk_list:
                            updated_usercomp_pk_list, updated_user_pk_list, err_lst = batch_update_usercomp(
                                usercomp_pk_list=tobe_updated_usercomp_pk_list,
                                is_submit=is_submit,
                                is_reset=is_reset,
                                requsr_auth=requsr_auth,
                                req_user=req_usr,
                                published_pk=published_instance_pk
                            )
                            if err_lst:
                                err_list.extend(err_lst)

# - create msg_html with info of rows

                        if is_test:
                            updated_usercomp_count = len(tobe_updated_usercomp_pk_list)
                            updated_user_count = len(tobe_updated_user_pk_list)
                        else:
                            updated_usercomp_count = len(updated_usercomp_pk_list)
                            updated_user_count = len(updated_user_pk_list)

                        if is_approve:

                            msg_html = create_approve_msg_list(
                                sel_department=sel_department,
                                sel_level=sel_level,
                                count_dict=count_dict,
                                updated_usercomp_count=updated_usercomp_count,
                                updated_user_count=updated_user_count,
                                err_list=err_list,
                                requsr_auth=requsr_auth,
                                is_test=is_test
                            )
                        else:
                            msg_html = create_submit_msg_list(
                                sel_department=sel_department,
                                sel_level=sel_level,
                                count_dict=count_dict,
                                updated_usercomp_count=updated_usercomp_count,
                                updated_user_count=updated_user_count,
                                err_list=err_list,
                                requsr_auth=requsr_auth,
                                is_test=is_test,
                                test_has_failed=test_has_failed,
                                published_instance_filename=published_instance_filename,
                                published_instance_file_url=published_instance_file_url
                            )


                                # PR2022-12-30 instead of updating each studsubj instance separately, create list of tobesaved studsubj_pk
                                # list is created outside this function, when is_saved = True

                            if logging_on:
                                logger.debug('    updated_usercomp_pk_list: ' + str(updated_usercomp_pk_list))

        # - add rows to studsubj_rows, to be sent back to page
                        # to increase speed, dont create return rows but refresh page after finishing this request

                        if updated_usercomp_pk_list:
                            updated_usercompensation_rows = create_usercompensation_rows(
                                sel_examyear=sel_examyear,
                                sel_department=sel_department,
                                sel_lvlbase=None,
                                request=request,
                                updated_usercomp_pk_list=updated_usercomp_pk_list
                            )
                            if updated_usercompensation_rows:
                                update_wrap['updated_usercompensation_rows'] = updated_usercompensation_rows

                        if logging_on:
                            logger.debug('    studsubj_rows: ' + str(studsubj_rows))

                        #if (studsubj_rows):
                        #    update_wrap['updated_studsubj_approve_rows'] = studsubj_rows


    # - add  msg_html to update_wrap (this one triggers MASS_UpdateFromResponse in page studsubjcts
        update_wrap['approve_msg_html'] = msg_html

     # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
    # - end of  StudentsubjectApproveOrSubmitEx1Ex4View.post

    def save_approved_in_studsubj(self, studsubj_pk_list, is_reset, prefix, requsr_auth, req_user):
        # PR2023-01-10

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug('----- save_approved_in_studsubj -----')

        saved_studsubj_pk_list = []
        err_html = None
        try:
            requsr_authby_field = ''.join((prefix, requsr_auth, 'by_id'))

            #   was: setattr(studsubj, requsr_authby_field, req_user)
            # - remove authby when is_reset
            requsr_authby_value = "NULL" if is_reset else str(req_user.pk)

            sql_keys = {'requsr_pk': req_user.pk, 'sb_arr': studsubj_pk_list}

            sql_list = ["UPDATE students_studentsubject AS studsubj ",
                        "SET", requsr_authby_field, "=", requsr_authby_value,
                        "WHERE studsubj.id IN (SELECT UNNEST(%(sb_arr)s::INT[]))",
                        "AND studsubj.deleted = FALSE",
                        "RETURNING id;"]

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('    sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)

                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        saved_studsubj_pk_list.append(row[0])

            if logging_on:
                logger.debug('    saved_studsubj_pk_list: ' + str(saved_studsubj_pk_list))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            err_html = ''.join((
                str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                str(_('The subjects could not be approved.'))
            ))

        if logging_on:
            logger.debug('    err_html: ' + str(err_html))

        return saved_studsubj_pk_list, err_html
# - end of save_approved_in_studsubj

    def save_published_in_studsubj(self, studsubj_pk_list, prefix, published_pk):
        # PR2022-12-31 PR2023-01-10

        """
        # when is_approve:
        #   requsr_authby_field = prefix + requsr_auth + 'by'
        #   # PR2022-12-30 was: setattr(studsubj, requsr_authby_field, req_user)

        # submit:
            published = getattr(studsubj, prefix + 'published')
            put published_id in field subj_published:
        #    setattr(studsubj, prefix + 'published', published_instance)
        # -
        """

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug('----- save_published_in_studsubj -----')

        saved_studsubj_pk_list = []
        err_html = None

        try:
            published_field = prefix + 'published_id'
            sql_keys = {'publ_pk': published_pk, 'sb_arr': studsubj_pk_list}

            sql_list = ["UPDATE students_studentsubject AS studsubj",
                        "SET", published_field, "= %(publ_pk)s::INT,",
                        "deleted=tobedeleted, tobedeleted=FALSE, tobechanged=FALSE,",
                        "prev_auth1by_id=NULL, prev_auth2by_id=NULL, prev_published_id=NULL",
                        "WHERE studsubj.id IN (SELECT UNNEST(%(sb_arr)s::INT[]))",
                        "AND studsubj.deleted = FALSE",

                        "RETURNING id;"]

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        saved_studsubj_pk_list.append(row[0])

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            err_html = ''.join((
                str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                str(_('The subjects could not be approved.'))
            ))

        if logging_on:
            logger.debug('    saved_studsubj_pk_list: ' + str(saved_studsubj_pk_list))

        return saved_studsubj_pk_list, err_html

    # - end of save_published_in_studsubj

    def create_usercomp_form(self, published_instance, sel_examyear, sel_school, sel_department, sel_level,
                                    save_to_disk, request, user_lang):
        #PR2021-07-27 PR2021-08-14
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= create_usercomp_form ============= ')
            logger.debug('    sel_level: ' + str(sel_level))
            logger.debug('    save_to_disk: ' + str(save_to_disk))

# +++ create Ex_compensation form

        response, is_saved_to_disk = create_excomp_xlsx(
            published_instance=published_instance,
            sel_examyear=sel_examyear,
            sel_school=sel_school,
            save_to_disk=save_to_disk,
            request=request,
            user_lang=user_lang
        )

        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= end of create_usercomp_form ============= ')
# --- end of create_usercomp_form


#################################################################################
@method_decorator([login_required], name='dispatch')
class UserCompensationApproveSingleView(View):  # PR2021-07-25 PR2023-02-18 PR2023-04-16

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UserCompensationApproveSingleView ============= ')

        update_wrap = {}
        msg_list = []

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = acc_prm.get_permit_of_this_page('page_corrector', 'approve_comp', request)

        if not has_permit:
            msg_list.append(acc_prm.err_txt_no_permit())  # default: 'to perform this action')
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('    upload_dict: ' + str(upload_dict))
                #  upload_dict: {'table': 'usercompensation', 'usercompensation_list': [{'usercompensation_pk': 916, 'auth2by': True}]}
                # upload_dict: {'table': 'usercompensation', 'usercompensation_list': [{'usercompensation_pk': 1089, 'auth2by': False}]}
# ----- get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_editNIU, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                if err_list:
                    msg_list.extend(err_list)
                    msg_list.append(acc_prm.err_txt_cannot_make_changes())
                else:

# - get list of usercompensation_pk's  from upload_dict
                    usercompensation_list = upload_dict.get('usercompensation_list') or []
                    # 'usercompensation_list': [{'usercompensation_pk': 916, 'auth2by': True}]

                    if usercompensation_list:
                        updated_usercompensation_rows = []
                        updated_usercomp_pk_list = []
# -------------------------------------------------
# - loop through list of uploaded studentsubjects
                        for usercompensation_dict in usercompensation_list:

                            append_dict = {}
                            error_dict = {}
                            usercompensation_pk = usercompensation_dict.get('usercompensation_pk')

# - get current usercomp_instance
                            usercomp_instance = acc_mod.UserCompensation.objects.get_or_none(
                                id=usercompensation_pk
                            )
                            if logging_on:
                                logger.debug('---------- ')
                                logger.debug('    usercomp_instance: ' + str(usercomp_instance))

                            if usercomp_instance:
# +++ update usercompensation instance

                                changes_are_saved, err_lst = \
                                    update_usercompensation_instance(usercomp_instance, usercompensation_dict, request)

                                if err_lst:
                                    msg_list.extend(err_lst)

                                if changes_are_saved and usercomp_instance:
                                    updated_usercomp_pk_list.append(usercomp_instance.pk)


# - end of loop
# -------------------------------------------------

                        if updated_usercomp_pk_list:
                            updated_usercompensation_rows = create_usercompensation_rows(
                                sel_examyear=sel_examyear,
                                sel_department=sel_department,
                                sel_lvlbase=None,
                                request=request,
                                updated_usercomp_pk_list=updated_usercomp_pk_list
                            )
                            if updated_usercompensation_rows:
                                update_wrap['updated_usercompensation_rows'] = updated_usercompensation_rows

        if msg_list:
            update_wrap['msg_html'] = acc_prm.msghtml_from_msglist_with_border(msg_list, c.HTMLCLASS_border_bg_invalid)

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UserCompensationApproveSingleView


@method_decorator([login_required], name='dispatch')
class UserCompensationDownloadExcompView(View):  # PR2023-07-09

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= UserCompensationDownloadExcompView ============= ')

    # - function creates, Ex1 xlsx file based on settings in usersetting
        response = None

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

    # - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

    # - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

            if logging_on:
                logger.debug('    sel_examyear: ' + str(sel_examyear))
                logger.debug('    sel_school: ' + str(sel_school))

            if sel_examyear and sel_school:

    # +++ create create_excomp_xlsx
                save_to_disk = False
                # just to prevent PyCharm warning on published_instance=published_instance
                # published_instance = None  # sch_mod.School.objects.get_or_none(pk=None)
                response, is_saved_to_disk = create_excomp_xlsx(
                    published_instance=None,
                    sel_examyear=sel_examyear,
                    sel_school=sel_school,
                    save_to_disk=save_to_disk,
                    request=request,
                    user_lang=user_lang
                )

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of UserCompensationDownloadExcompView



@method_decorator([login_required], name='dispatch')
class UserCompensationDownloadPaymentView(View):  # PR2023-07-20

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= UserCompensationDownloadPaymentView ============= ')

        ##################
        def get_usercomp_rows_all_schools(sel_examyear, user_lang):
            # PR2023-07-09 like in UserCompensationDownloadExcompView, but without filter schools
            # PR2023-08-15 filter on requsr when his usergroups contains corrector
            logging_on = s.LOGGING_ON
            if logging_on:
                logger.debug(' ----- get_usercomp_rows_all_schools -----')

            usercomp_rows = []

            try:
                sql = ''.join((
                    "SELECT uc.id, uc.user_id, CONCAT('usercomp_', uc.id::TEXT) AS mapid,",
                    "au.last_name, ",
                    "uc_school.base_id AS uc_schoolbase_id, uc_school.abbrev AS uc_school_abbrev, uc_schoolbase.code AS uc_sb_code,",
                    "depbase.code AS uc_depbase_code, lvlbase.code AS uc_lvlbase_code,",
                    "exam.version AS exam_version, exam.examperiod,",

                    "subj.name_nl AS subj_name_nl, subjbase.code AS subjbase_code,",

                    "uc.amount AS uc_amount, uc.meetings AS uc_meetings,",
                    "uc.correction_amount AS uc_corr_amount, uc.correction_meetings AS uc_corr_meetings, ",
                    "uc.compensation / 100 AS uc_compensation, ",
                    "uc.meetingdate1 AS uc_meetingdate1, uc.meetingdate2 AS uc_meetingdate2, ",
                    "publ.datepublished AS uc_datepublished "
                    
                    "FROM accounts_usercompensation AS uc ",

                    "INNER JOIN accounts_user AS au ON (au.id = uc.user_id) ",

                    "INNER JOIN subjects_exam AS exam ON (exam.id = uc.exam_id) ",

                    "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id) ",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id) ",

                    "INNER JOIN schools_school AS uc_school ON (uc_school.id = uc.school_id) ",
                    "INNER JOIN schools_schoolbase AS uc_schoolbase ON (uc_schoolbase.id = uc_school.base_id) ",

                    "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id) ",
                    "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id) ",

                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id) ",
                    "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id) ",

                    "LEFT JOIN schools_published AS publ ON (publ.id = uc.published_id) ",

                    "WHERE uc_school.examyear_id=", str(sel_examyear.pk), "::INT ",
                    "AND au.role=", str(c.ROLE_016_CORR), "::INT ",

                    "ORDER BY LOWER(au.last_name), LOWER(uc_schoolbase.code), LOWER(subjbase.code), dep.sequence, lvl.sequence, LOWER(exam.version), exam.examperiod"
                ))

                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    usercomp_rows = af.dictfetchall(cursor)

                    for row in usercomp_rows:

                        uc_meetingdate1 = row.get('uc_meetingdate1')
                        uc_meetingdate2 = row.get('uc_meetingdate2')
                        uc_meetingdates = None
                        if uc_meetingdate1 or uc_meetingdate2:
                            if uc_meetingdate1 and uc_meetingdate2:
                                # sort dates
                                uc_meetingdate_list = [uc_meetingdate1, uc_meetingdate2]
                                uc_meetingdate_list.sort()
                                uc_meetingdates = ', '.join(filter(None, (
                                    af.format_DMY_from_dte(uc_meetingdate_list[0], user_lang, True, True),
                                    # month_abbrev=True, skip_year=True
                                    af.format_DMY_from_dte(uc_meetingdate_list[1], user_lang, True, True)
                                # month_abbrev=True, skip_year=True
                                )))
                            else:
                                uc_meetingdate = uc_meetingdate1 if uc_meetingdate1 else uc_meetingdate2 if uc_meetingdate2 else None
                                uc_meetingdates = af.format_DMY_from_dte(uc_meetingdate, user_lang, True,
                                                                         True)  # month_abbrev=True, skip_year=True

                        row['uc_meetingdates'] = uc_meetingdates

                        row['datepublished'] = af.format_DMY_from_dte(row.get('uc_datepublished'), user_lang, True, False) # month_abbrev=True, skip_year=False

                        if logging_on:
                            logger.debug('    row: ' + str(row))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))


            return usercomp_rows

        def get_payment_rows(sel_examyear):
            # PR2023-07-21

            logging_on = False  # s.LOGGING_ON
            if logging_on:
                logger.debug(' ----- get_payment_rows -----')
            rows = []
            try:
                subsub_sql = ''.join((
                    "SELECT uc.user_id, ",
                    "CASE WHEN uc.amount > 0 THEN 1 ELSE 0 END AS uc_exam_count, "
                    "CASE WHEN uc.amount > 0 AND published_id IS NOT NULL THEN 1 ELSE 0 END AS uc_published_count, "
                    "uc.amount + uc.correction_amount AS uc_amount_plus_corr, ",
                    "uc.meetings + uc.correction_meetings AS uc_meetings_plus_corr, ",
                    "uc.compensation AS uc_compensation ",

                    "FROM accounts_usercompensation AS uc ",
                    "INNER JOIN schools_school AS school ON (school.id = uc.school_id) ",

                    "WHERE school.examyear_id=", str(sel_examyear.pk), "::INT ",
                ))

                sub_sql = ''.join((
                    "WITH uc AS (", subsub_sql, ")",
                    "SELECT uc.user_id, ",
                    "SUM(uc.uc_exam_count) AS exam_count, ",
                    "SUM(uc.uc_published_count) AS published_count, ",

                    "SUM(uc.uc_amount_plus_corr) AS sum_amount, ",
                    "SUM(uc.uc_meetings_plus_corr) AS sum_meetings, ",
                    "SUM(uc.uc_compensation) / 100 AS sum_compensation ",

                    "FROM uc ",
                    "GROUP BY uc.user_id"
                ))

                sql_list = [
                    "WITH uc AS (", sub_sql, ") ",
                    "SELECT au.id, au.last_name, ud.idnumber, ud.cribnumber, ud.bankname, ud.bankaccount, ud.beneficiary, ",
                    "uc.exam_count, uc.published_count, ",
                    "CASE WHEN uc.published_count = 0 THEN  0 ELSE ",
                        "CASE WHEN uc.published_count < uc.exam_count THEN 1 ELSE 2 ",
                            "END END AS published_status, ",
                    "sum_amount, sum_meetings, sum_compensation ",

                    "FROM accounts_user AS au ",
                    "INNER JOIN uc ON (uc.user_id = au.id) ",
                    "INNER JOIN accounts_userdata AS ud ON (ud.user_id = au.id) ",

                    "WHERE au.role=", str(c.ROLE_016_CORR), "::INT ",

                    "ORDER BY LOWER(au.last_name);"
                    ]
                sql = ''.join(sql_list)

                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    rows = af.dictfetchall(cursor)
                    if logging_on and False:
                        for row in rows:
                            logger.debug('  row ' + str(row))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

            return rows

##################

    # - function creates, Ex1 xlsx file based on settings in usersetting
        response = None
        req_usr = request.user
        msg_list = []

    # - reset language
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)
        permit_list = acc_prm.get_permit_list('page_corrector', req_usr)
        if logging_on:
            logger.debug('    permit_list: ' + str(permit_list))

    # - get permit
        has_permit = acc_prm.has_permit( request, 'page_corrector', ['permit_pay_comp'])
        if logging_on:
            logger.debug('    has_permit: ' + str(has_permit))
        if not has_permit:
            msg_list.append(str(_("You don't have permission to perform this action.")))
        else:

    # - get selected examyear from usersettings,
            # - checks if country is locked and if examyear is missing, not published or locked
            # - skip allow_not_published when req_usr is admin (ETE) or system
            sel_examyear, err_lst = acc_view.get_selected_examyear_from_usersetting(request)

            if logging_on:
                logger.debug('    sel_examyear: ' + str(sel_examyear))
            if err_lst:
                border_class = c.HTMLCLASS_border_bg_invalid
                msg_list.extend(err_lst)
            elif sel_examyear:

                payment_rows = get_payment_rows(sel_examyear)
                usercomp_rows = get_usercomp_rows_all_schools(sel_examyear, user_lang)

                if logging_on:
                    logger.debug('payment_rows: ' + str(payment_rows))

    # +++ create ex1_xlsx
                save_to_disk = False
                # just to prevent PyCharm warning on published_instance=published_instance
                # published_instance = None  # sch_mod.School.objects.get_or_none(pk=None)
                response, is_saved_to_disk = create_payment_xlsx(
                    published_instance=None,
                    sel_examyear=sel_examyear,
                    payment_rows=payment_rows,
                    usercomp_rows=usercomp_rows,
                    save_to_disk=save_to_disk,
                    request=request,
                    user_lang=user_lang
                )

        if logging_on:
            logger.debug('    response: ' + str(response))

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of UserCompensationDownloadPaymentView


@method_decorator([login_required], name='dispatch')
class UserCompensationDownloadInvoiceView(View):  # PR2023-08-15

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= UserCompensationDownloadInvoiceView ============= ')

        response = None
        req_usr = request.user
        msg_list = []

    # - reset language
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

    # - get permit
        has_permit = acc_prm.has_permit( request, 'page_corrector', ['view_invoice'])
        if not has_permit:
            msg_list.append(str(_("You don't have permission to perform this action.")))
        else:
            pass

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of UserCompensationDownloadInvoiceView

########################################################################
# === UserdataUploadView ===================================== PR2023-07-20
@method_decorator([login_required], name='dispatch')
class UserdataUploadView(View):

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ')
            logger.debug(' ========== UserdataUploadView ===============')

        def update_userdata_instance(instance, upload_dict, request):

            if logging_on:
                logger.debug(' ------- update_userdata_instance -------')
                logger.debug('    upload_dict: ' + str(upload_dict))
                logger.debug('    instance:    ' + str(instance))

            changes_are_saved = False
            err_list = []

            if instance:
                save_changes = False
                for field, new_value in upload_dict.items():
                    if logging_on:
                        logger.debug('    field: ' + str(field))

                    if field in (('idnumber', 'cribnumber', 'bankname', 'bankaccount', 'beneficiary')):
                        saved_value = getattr(instance, field)

                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True


                # - save changes
                if save_changes:
                    try:
                        instance.save(request=request)
                        changes_are_saved = True
                    except Exception as e:
                        logger.error(getattr(e, 'message', str(e)))
                        err_list.append(
                            acc_prm.errhtml_error_occurred_no_border(e, _('The changes have not been saved.')))

            return changes_are_saved, err_list
        # - end of update_userdata_instance

        msg_list = []
        update_wrap = {}

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')
            # upload_dict: {'mode': 'update', 'usercompensation_pk': 609, 'uc_meetings': 1}

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get permit - only requsr can make changes on his own userdata record
            user_pk = upload_dict.get('user_id')
            has_permit = user_pk and user_pk == request.user.pk

            if logging_on:
                logger.debug('    upload_dict: ' + str(upload_dict))
                logger.debug('    user_pk:    ' + str(user_pk))
                logger.debug('    has_permit:    ' + str(has_permit))

            if not has_permit:
                msg_list.append(acc_prm.err_txt_no_permit()) # default: 'to perform this action')
            else:
                updated_rows = []

# - get variables
                userdata_pk = upload_dict.get('userdata_id')

# +++  get existing usercompensation_instance
                userdata_instance = acc_mod.Userdata.objects.get_or_none(pk=userdata_pk)
                if userdata_instance:
                    if logging_on:
                        logger.debug('    userdata_instance: ' + str(userdata_instance))
# +++ Update usercompensation_instance
                    changes_are_saved, err_lst = \
                        update_userdata_instance(
                            instance=userdata_instance,
                            upload_dict=upload_dict,
                            request=request
                        )
                    if err_lst:
                        msg_list.extend(err_lst)

# - create userdata_rows
                    if changes_are_saved:
                        updated_pk_list = [userdata_pk]
                        updated_rows = create_userdata_rows(request=request, updated_pk_list=updated_pk_list)
                        update_wrap['updated_userdata_rows'] = updated_rows

    # show modmessage when single update
        if msg_list:
            update_wrap['msg_html'] = ''.join((
                "<div class='p-2 ", c.HTMLCLASS_border_bg_invalid, "'>",
                ''.join(msg_list),
                "</div>"))
            if logging_on:
                logger.debug('msg_list:    ' + str(msg_list))

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UserdataUploadView

#######################################################


def get_usercomp_rows(sel_examyear_pk, sel_schoolbase_pk, upload_dict, user_lang):
    # PR2023-07-09

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_usercomp_rows -----')

    # don't use selected_pk values, but get them from upload_dict
    sel_dep_level_req = upload_dict.get('sel_dep_level_req') or False
    sel_depbase_pk = upload_dict.get('sel_depbase_pk')
    sel_lvlbase_pk = upload_dict.get('sel_lvlbase_pk')

    usercomp_rows = []
    auth1_list, auth2_list = [], []

    try:
        sql_list = [
            "SELECT uc.id, uc.user_id, CONCAT('usercomp_', uc.id::TEXT) AS mapid,",
            "au.last_name, ",
            "uc_school.base_id AS uc_schoolbase_id, uc_school.abbrev AS uc_school_abbrev, uc_schoolbase.code AS sb_code,",
            "depbase.code AS uc_depbase_code, lvlbase.code AS uc_lvlbase_code,",
            "exam.version AS exam_version, exam.examperiod,",

            "subj.name_nl AS subj_name_nl, subjbase.code AS subjbase_code,",

            "uc.amount AS uc_amount, uc.meetings AS uc_meetings,",
            "uc.correction_amount AS uc_corr_amount, uc.correction_meetings AS uc_corr_meetings, ",
            "CASE WHEN uc.compensation IS NULL THEN NULL  ELSE uc.compensation / 100 END AS uc_compensation, ",
            "uc.meetingdate1 AS uc_meetingdate1, uc.meetingdate2 AS uc_meetingdate2, ",
            "uc.auth1by_id, uc.auth2by_id, uc.published_id, ",
            "auth1.last_name AS auth1_name, auth2.last_name AS auth2_name ",

            "FROM accounts_usercompensation AS uc ",

            "INNER JOIN accounts_user AS au ON (au.id = uc.user_id) ",

            "INNER JOIN subjects_exam AS exam ON (exam.id = uc.exam_id) ",

            "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id) ",
            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id) ",

            "INNER JOIN schools_school AS uc_school ON (uc_school.id = uc.school_id) ",
            "INNER JOIN schools_schoolbase AS uc_schoolbase ON (uc_schoolbase.id = uc_school.base_id) ",

            "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id) ",
            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id) ",

            "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id) ",
            "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id) ",

            "LEFT JOIN accounts_user AS auth1 ON (auth1.id = uc.auth1by_id)",
            "LEFT JOIN accounts_user AS auth2 ON (auth2.id = uc.auth2by_id)",

            "WHERE uc_school.examyear_id=", str(sel_examyear_pk), "::INT ",
            "AND uc_school.base_id=", str(sel_schoolbase_pk), "::INT "
            ]

        # don't use selected_pk values, but get them from upload_dict
        # dont filter on dep when creating excomp form
        if sel_depbase_pk:
            sql_list.append(''.join(("AND dep.base_id=", str(sel_depbase_pk), "::INT ")))

        # PR2023-02-19 debug: VWO didnt show records, because of filter sel_lvlbase_pk=5
        # solved bij adding: if sel_dep_level_req

        if sel_dep_level_req and sel_lvlbase_pk:
            sql_list.append(''.join(("AND lvl.base_id=", str(sel_lvlbase_pk), "::INT ")))

        if logging_on :
            for sql_txt in sql_list:
                logger.debug('  > ' + str(sql_txt))

        sql_list.append("ORDER BY LOWER(au.last_name), LOWER(subjbase.code), dep.sequence, lvl.sequence, LOWER(exam.version), exam.examperiod")

        sql = ''.join(sql_list)
        with connection.cursor() as cursor:
            cursor.execute(sql)
            usercomp_rows = af.dictfetchall(cursor)

            for row in usercomp_rows:
                #PR2023-07-11 calc subtotal: compensation without correction
                uc_comp_subtotal = calc_compensation(
                        approvals_sum=row.get('uc_amount') or 0,
                        meetings_sum=row.get('uc_meetings') or 0,
                        approvals_sum_correction=0,
                        meetings_sum_corrections=0,
                    )
                row['uc_comp_subtotal'] = Decimal(uc_comp_subtotal) / Decimal('100')

                uc_meetingdate1 = row.get('uc_meetingdate1')
                uc_meetingdate2 = row.get('uc_meetingdate2')
                uc_meetingdates = None
                if uc_meetingdate1 or uc_meetingdate2:
                    if uc_meetingdate1 and uc_meetingdate2:
                        # sort dates
                        uc_meetingdate_list = [uc_meetingdate1, uc_meetingdate2]
                        uc_meetingdate_list.sort()
                        uc_meetingdates = ', '.join(filter(None, (
                            af.format_DMY_from_dte(uc_meetingdate_list[0], user_lang, True, True), # month_abbrev=True, skip_year=True
                            af.format_DMY_from_dte(uc_meetingdate_list[1], user_lang, True, True) # month_abbrev=True, skip_year=True
                        )))
                    else:
                        uc_meetingdate = uc_meetingdate1 if uc_meetingdate1 else uc_meetingdate2 if uc_meetingdate2 else None
                        uc_meetingdates = af.format_DMY_from_dte(uc_meetingdate, user_lang, True, True) # month_abbrev=True, skip_year=True

                row['uc_meetingdates'] = uc_meetingdates

                uc_auth1_name = row.get('auth1_name')
                uc_auth2_name = row.get('auth2_name')
                if uc_auth1_name and uc_auth1_name not in auth1_list:
                    auth1_list.append(uc_auth1_name)
                if uc_auth2_name and uc_auth2_name not in auth2_list:
                    auth2_list.append(uc_auth2_name)

                if logging_on:
                    logger.debug('    row: ' + str(row))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if auth1_list:
        auth1_list.sort()
    if auth2_list:
        auth2_list.sort()
    if logging_on:
        logger.debug('    auth1_list: ' + str(auth1_list))
        logger.debug('    auth2_list: ' + str(auth2_list))

    return usercomp_rows, auth1_list, auth2_list

##################################################################################

def create_corrector_rows(sel_examyear, sel_schoolbase, sel_depbase, sel_lvlbase, request):
    # --- create list of users with role = corrector and usergroup auth4
    # - filter on allowed school and allowed dep

    # note: admin of role correctors uses table 'users' to add or change correctors
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' =============== create_corrector_rows ============= ')

    corrector_rows = []
    if request.user.country and sel_schoolbase and sel_examyear:

        corrector_rows = acc_view.create_user_rowsNEW(
            sel_examyear=sel_examyear if sel_examyear else None,
            request=request,
            school_correctors_only=True
            #this_depbase_pk_only=sel_depbase.pk if sel_depbase else None
        )

           # userallowed_sections_dict = json.loads(allowed_sections_str)
           # logger.debug(' userallowed_sections_dict ' + str(userallowed_sections_dict))
           # if str(sel_schoolbase.pk) in userallowed_sections_dict:
           #     logger.debug('>>  sel_schoolbase.pk ' + str(sel_schoolbase.pk))
           #     userallowed_school_dict = userallowed_sections_dict.get(str(sel_schoolbase.pk))
           #     logger.debug('>>  userallowed_school_dict ' + str(userallowed_school_dict))

        if logging_on:
            if corrector_rows:
                for row in corrector_rows:
                    logger.debug(' row ' + str(row))

    return corrector_rows


def create_usercompensation_rows(sel_examyear, sel_department, sel_lvlbase, request, updated_usercomp_pk_list=None):
    # --- create list of all correctors of this school, or  PR2023-02-19 PR2023-05-13
    # when a school opens this recordset, only users with uc of the school must be schown
    # when opened by role corrector: show all users, also without uc
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_usercompensation_rows ============= ')
        logger.debug('    request.user.role: ' + str(request.user.role))
        logger.debug('    request.user.schoolbase.pk: ' + str(request.user.schoolbase.pk))

    usercompensation_rows = []
    if sel_examyear:
        try:
            requsr_usergroup_list = acc_prm.get_usergroup_list_from_user_instance(request.user)

            auth4_in_requsr_usergroups = 'auth4' in requsr_usergroup_list if requsr_usergroup_list else False
            auth1_or_auth2_in_requsr_usergroups = 'auth1' in requsr_usergroup_list or 'auth2' in requsr_usergroup_list if requsr_usergroup_list else False
            # when role = school:
            #  - when uergroup has auth1 or auth2: show all usercompensaations from this school
            #  - when uergroup has auth4: schow only usercompensaations from this user
            # when role = corrector:
            #  - when uergroup has auth1 or auth2: show all usercompensaations from all schools
            #  - when uergroup has auth4: schow only usercompensaations from this user, from all schools

            if logging_on:
                logger.debug('    auth1_or_auth2_in_requsr_usergroups: ' + str(auth1_or_auth2_in_requsr_usergroups))

            sql_auth = "SELECT u.id, u.last_name FROM accounts_user AS u"

            sql_sub_list = ["WITH auth1 AS (", sql_auth, "), auth2 AS (", sql_auth, ")",
                        "SELECT uc.id, uc.user_id,",
                        "CONCAT('usercomp_', uc.id::TEXT) AS mapid,",

                        "uc_school.base_id AS uc_schoolbase_id, uc_school.abbrev AS uc_school_abbrev, uc_schoolbase.code AS sb_code,",
                        "depbase.id AS uc_depbase_id, lvlbase.id AS uc_lvlbase_id,",
                        "depbase.code AS uc_depbase_code, lvlbase.code AS uc_lvlbase_code,",
                        "exam.version AS exam_version, exam.examperiod AS examperiod,",

                        "subj.name_nl AS subj_name_nl, subjbase.code AS subjbase_code,",

                        "uc.amount AS uc_amount, uc.meetings AS uc_meetings,",
                        "uc.correction_amount AS uc_corr_amount, uc.correction_meetings AS uc_corr_meetings,",
                        "uc.compensation AS uc_compensation,",
                        "uc.meetingdate1 AS uc_meetingdate1, uc.meetingdate2 AS uc_meetingdate2,",
                        "uc.auth1by_id AS uc_auth1by_id, auth1.last_name AS uc_auth1by_usr,",
                        "uc.auth2by_id AS uc_auth2by_id, auth2.last_name AS uc_auth2by_usr,",
                        "uc.published_id AS uc_published_id,",

                        "publ.modifiedat AS uc_publ_modat,"

                        "uc.notes AS uc_notes",

                        "FROM accounts_usercompensation AS uc",

                        "INNER JOIN subjects_exam AS exam ON (exam.id = uc.exam_id)",

                        "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                        "INNER JOIN schools_school AS uc_school ON (uc_school.id = uc.school_id)",
                        "INNER JOIN schools_schoolbase AS uc_schoolbase ON (uc_schoolbase.id = uc_school.base_id)",

                        "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
                        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                        "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",
                        "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                        "LEFT JOIN auth1 ON (auth1.id = uc.auth1by_id)",
                        "LEFT JOIN auth2 ON (auth2.id = uc.auth2by_id)",

                        "LEFT JOIN schools_published AS publ ON (publ.id = uc.published_id)",

                        "WHERE uc_school.examyear_id=", str(sel_examyear.pk), "::INT"
                        ]
            # only show correctors  of this uc_school when role = school
            if request.user.role == c.ROLE_008_SCHOOL:
                sql_sub_list.append(''.join(("AND uc_school.base_id=", str(request.user.schoolbase.pk), "::INT")))

    # filter on selected department
            # dont filter on sel_department.pk and sel_lvlbase, filer on client instead
            #if sel_department:
            #    sql_sub_list.append(''.join(("AND dep.id=", str(sel_department.pk), "::INT")))

            # filter on selected lvlbase, if level_req
            #if sel_department.level_req and sel_lvlbase:
            #    sql_sub_list.append(''.join(("AND lvl.base_id=", str(sel_lvlbase.pk), "::INT")))

            sub_sql = ' '.join(sql_sub_list)

            sql_join_uc = "INNER JOIN" if request.user.role == c.ROLE_008_SCHOOL else "LEFT JOIN"
            if logging_on:
                logger.debug('    sql_join_uc ' + str(sql_join_uc))

            sql_list = ["WITH uc_sub AS (", sub_sql, ")",
                        "SELECT u.id AS u_id, uc_sub.id AS uc_id,",

                        "CONCAT('usercomp_', u.id::TEXT, CASE WHEN uc_sub.id IS NULL THEN NULL ELSE '_' END, uc_sub.id::TEXT) AS mapid,",

                        #"'TEST' AS TEST,",
                        "SUBSTRING(u.username, 7) AS username, u.last_name, u.is_active,",
                       # "ual.examyear_id, ual.allowed_sections,",

                        #"'TEST2' AS TEST2,",
                        "user_sb.code AS user_sb_code,",

                        "uc_sub.uc_depbase_id, uc_sub.uc_lvlbase_id,",

                        "uc_sub.uc_schoolbase_id, uc_sub.uc_school_abbrev, uc_sub.sb_code, uc_sub.uc_depbase_code, uc_sub.uc_lvlbase_code,",
                        "uc_sub.exam_version, uc_sub.examperiod,",
                        "uc_sub.subj_name_nl, uc_sub.subjbase_code,",

                        "uc_sub.uc_amount, uc_sub.uc_meetings, uc_sub.uc_corr_amount, uc_sub.uc_corr_meetings, uc_sub.uc_compensation,",
                        "uc_sub.uc_meetingdate1,uc_sub.uc_meetingdate2,",
                        "uc_sub.uc_auth1by_id, uc_sub.uc_auth1by_usr,",
                        "uc_sub.uc_auth2by_id, uc_sub.uc_auth2by_usr,",

                        "uc_sub.uc_published_id, uc_sub.uc_publ_modat, uc_sub.uc_notes",

                        "FROM accounts_user AS u",
                        "INNER JOIN accounts_userallowed AS ual ON (ual.user_id = u.id)",
                        "INNER JOIN schools_schoolbase AS user_sb ON (user_sb.id = u.schoolbase_id)",

                        sql_join_uc, "uc_sub ON (uc_sub.user_id = u.id)",

                        "WHERE u.is_active",
                        ''.join(("AND ual.examyear_id=", str(sel_examyear.pk), "::INT")),
                        ''.join(("AND (POSITION('", c.USERGROUP_AUTH4_CORR, "' IN ual.usergroups) > 0)")),

                        #''.join((" u.role=", str(c.ROLE_016_CORR), "::INT")),
                        ]
            if updated_usercomp_pk_list:
                sql_list.append(''.join(("AND uc_sub.id IN (SELECT UNNEST(ARRAY", str(updated_usercomp_pk_list), "::INT[]))")))

            # - when req_usr.role = school: only correctors of this school are visible (from role corrector and own school)
            #       - req_usr.role = school and usergroups countains auth4: show only usercomp rows of this school / this req_usr
            #       - req_usr.role = school and usergroups countains auth1 or auth2: show usercomp rows of all schools / all req_usra with role = corrector
            # - when req_usr.role = corrector: only correctors of with role = corrector are shown (exclude correctors that are appointed by school)
            #       - req_usr.role = corrector and usergroups countains auth4: show usercomp rows of all schools / this req_usr
            #       - req_usr.role = corrector and usergroups countains auth1 or auth2: show usercomp rows of all schools / this req_usr.role = correcor

            if request.user.role == c.ROLE_008_SCHOOL:
                # filter is set by inner join on uc_sub and filter uc_school.base_id
                pass
            elif request.user.role == c.ROLE_016_CORR:
                # only show correctors with role=correctors (schools can also appoint correcteord, they are not included)
                sql_list.append(''.join(("AND u.role=", str(c.ROLE_016_CORR), "::INT")))
            else:
                sql_list.append("AND FALSE")

            if not auth1_or_auth2_in_requsr_usergroups:
                if auth4_in_requsr_usergroups:
                    sql_list.append(''.join(("AND u.id=", str(request.user.pk), "::INT")))
                else:
                    sql_list.append("AND FALSE")

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)

                usercompensation_rows = af.dictfetchall(cursor)
            if logging_on :
                for row in usercompensation_rows:
                    logger.debug(' > row: ' + str(row))
                    logger.debug(' > uc_amount: ' + str(row.get('uc_amount')))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('  len  usercompensation_rows: ' + str(len(usercompensation_rows)))

    return usercompensation_rows
# - end of create_usercompensation_rows


def create_userdata_rows(request, updated_pk_list=None):
    # --- create list of userdata row of this user PR2023-07-18

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_userdata_rows ============= ')
        logger.debug('    request.user.role: ' + str(request.user.role))
        logger.debug('    request.user.schoolbase.pk: ' + str(request.user.schoolbase.pk))

    userdata_rows = []
    try:
        sql_list = [
            "SELECT ud.id, ud.user_id, ",
            "CONCAT('userdata_', ud.id::TEXT) AS mapid, ",
            "au.last_name, ud.idnumber, ud.cribnumber, ud.bankname, ud.bankaccount, ud.beneficiary, ",
            "ud.modifiedat, ud.modifiedby_id, modusr.last_name AS modby_name ",

            "FROM accounts_userdata AS ud ",
            "INNER JOIN accounts_user AS au ON (au.id = ud.user_id) ",
            "LEFT JOIN accounts_user AS modusr ON (modusr.id = ud.modifiedby_id) ",
            "WHERE "
            ]
        if updated_pk_list:
            if len(updated_pk_list) == 1:
                sql_list.extend(("ud.id=", str(updated_pk_list[0]), "::INT;"))
            else:
                sql_list.extend(("ud.id IN (SELECT UNNEST(ARRAY", str(updated_pk_list), "::INT[];"))
        else:
            sql_list.extend(("ud.user_id=", str(request.user.pk), "::INT;"))

        sql = ''.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql)
            userdata_rows = af.dictfetchall(cursor)

        if logging_on :
            for row in userdata_rows:
                logger.debug(' > row: ' + str(row))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('  len  userdata_rows: ' + str(len(userdata_rows)))

    return userdata_rows
# - end of create_userdata_rows


def create_usercomp_agg_rows(sel_examyear, sel_department,  sel_lvlbase, request):
    # --- create list of all approvals per correctors per exam and calculate total compensation PR2023-02-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_usercomp_agg_rows ============= ')

    usercompensation_agg_rows = []
    if request.user.country and request.user.schoolbase:
        if request.user.role >= c.ROLE_008_SCHOOL:

            # ATTENTION: sxm may use exams of ETE, therefore don't filter on examyear of exam,
            # this filter is ok: school.examyear_id

            try:
                sql_list = ["SELECT u.id AS u_id, exam.id AS exam_id,",

                            "CONCAT('user_exam_', u.id::TEXT, '_',  exam.id::TEXT) AS mapid,",

                            "SUBSTRING(u.username, 7) AS username, u.last_name, u.is_active,",
                            "user_sb.code AS user_sb_code,",

                            "depbase.id AS uc_depbase_id, depbase.code AS depbase_code,",
                            "lvlbase.id AS uc_lvlbase_id, lvlbase.code AS lvlbase_code,",
                            "exam.version AS exam_version, exam.examperiod AS examperiod,",

                            "subj.name_nl AS subj_name_nl, subjbase.code AS subjbase_code,",

                            "SUM(uc.amount) AS uc_amount, SUM(uc.meetings) AS uc_meetings,",
                            "SUM(uc.correction_amount) AS uc_corr_amount, SUM(uc.correction_meetings) AS uc_corr_meetings,",

                            "SUM(uc.compensation) AS uc_compensation",

                            "FROM accounts_usercompensation AS uc",

                            "INNER JOIN accounts_user AS u ON (u.id = uc.user_id)",
                            "LEFT JOIN schools_schoolbase AS user_sb ON (user_sb.id = u.schoolbase_id)",

                            "INNER JOIN subjects_exam AS exam ON (exam.id = uc.exam_id)",
                            "INNER JOIN schools_school AS school ON (school.id = uc.school_id)",

                            "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                            "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
                            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                            "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",
                            "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                            "WHERE school.examyear_id=" + str(sel_examyear.pk) + "::INT",

                            # for testimg only: "AND u.last_name ILIKE '%%jeska%%'"
                            ]
            # only show correctors of this school when role = school
                if request.user.role == c.ROLE_008_SCHOOL:
                    sql_list.extend(("AND school.base_id=", str(request.user.schoolbase.pk), "::INT"))

            # show only this corr when ug = corrector and not auth1, auth2
                requsr_userallowed_instance = acc_prm.get_userallowed_instance(request.user, sel_examyear)
                requsr_usergroup_list = acc_prm.get_usergroup_list(requsr_userallowed_instance)
                if c.USERGROUP_AUTH4_CORR in requsr_usergroup_list \
                        and c.USERGROUP_AUTH1_PRES not in requsr_usergroup_list \
                        and c.USERGROUP_AUTH1_PRES not in requsr_usergroup_list:
                    sql_list.extend(("AND u.id=", str(request.user.pk), "::INT"))

                sql_list.extend(("GROUP BY u.id, u.username, u.last_name, u.is_active, user_sb.code, exam.id,",
                                 "exam.version, exam.examperiod,",
                                 "depbase.id, depbase.code, lvlbase.id, lvlbase.code, subj.name_nl, subjbase.code"))

                sql = ' '.join(sql_list)

                if logging_on:
                    for txt in sql_list:
                        logger.debug(' > ' + str(txt))

                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    usercompensation_agg_rows = af.dictfetchall(cursor)
                if usercompensation_agg_rows:
                    # add compensation to each row
                    for row in usercompensation_agg_rows:
                        compensation = calc_compensation(
                            approvals_sum=row.get('amount_sum') or 0,
                            meetings_sum=row.get('meetings_sum') or 0,
                            approvals_sum_correction=row.get('corr_amount_sum') or 0,
                            meetings_sum_corrections=row.get('corr_meetings_sum') or 0
                        )
                        #row['compensation'] = compensation

                        if logging_on:
                            logger.debug('   row: ' + str(row))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('   len usercompensation_agg_rows: ' + str(len(usercompensation_agg_rows)))

    return usercompensation_agg_rows
# - end of create_usercomp_agg_rows


def create_bankname_rows(sel_examyear):
    # --- create list of userdata row of this user PR2023-07-20

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_bankname_rows ============= ')
        logger.debug('    sel_examyear: ' + str(sel_examyear))
    bankname_rows = sel_examyear.get_examyearsetting_dict(c.KEY_BANKLIST)

    if logging_on:
        logger.debug(' > bankname_rows: ' + str(bankname_rows) + ' ' + str(type(bankname_rows)) )

    return bankname_rows
# - end of create_bankname_rows


####################################################
def calc_compensation(approvals_sum, meetings_sum, approvals_sum_correction, meetings_sum_corrections):
    # calculate compensation PR2023-02-25
    # values, to be stored in examyear_settings
    first_approval_amount = c.CORRCOMP_FIRST_APPROVAL
    other_approval_amount = c.CORRCOMP_OTHER_APPROVAL
    meeting_amount = c.CORRCOMP_MEETING_COMP
    max_meetings = c.CORRCOMP_MAX_MEETINGS

    total_approvals = approvals_sum + approvals_sum_correction
    total_meetings = meetings_sum + meetings_sum_corrections
    if total_meetings > max_meetings:
        total_meetings = max_meetings

    compensation = 0
    if total_approvals >= 1:
        compensation = first_approval_amount + (other_approval_amount * (total_approvals - 1))
    if total_meetings:
        compensation += meeting_amount * total_meetings

    return compensation


def update_usercompensation(sel_examyear, request):
    # --- create list of all correctors, approvals
    # and return dict with key (user_pk, exam_pk, school_pk) and count PR2023-02-24 PR2023-05-14
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_usercompensation ----- ')

    # ++++++++++++++++++++++++++++++++++++++
    def get_approval_count_dict():
        # --- create list of all grades, that are approved by correctors
        # return dict with key (user_id, exam_id, school_id) and value = count PR2023-02-24

        # NOTE: grades that are approved by corrector, but have no exam, are NOT included!
        # NOTE: sxm may use exams of ETE, therefore don't filter on examyear of exam,
        #       filter by examyear_id of grade is ok (correctrs only approve grade of own country): grd.studsubj.stud.school.examyear_id
        # NOTE: it includes approval of deleted students and subjects

        approval_count_dict = {}
        sql_list = [
            "SELECT u.id AS user_id, exam.id AS exam_id, school.id AS school_id, count(*) AS count ",

            "FROM students_grade AS grd",
            "INNER JOIN accounts_user AS u ON (u.id = grd.ce_auth4by_id)",
            "INNER JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id)",

            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
            "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",

            "WHERE school.examyear_id=" + str(sel_examyear.pk) + "::INT",
            # dont filter on auth4, usergroup may have been removed after approving grade, so dont add:
            #  "AND (POSITION('" + c.USERGROUP_AUTH4_CORR + "' IN ual.usergroups) > 0)",

            # include approval of deleted students and subjects, so dont add:
            #   "AND NOT stud.deleted AND NOT studsubj.deleted AND NOT grd.deleted",
        ]

        if request.user.role == c.ROLE_008_SCHOOL:
            requsr_schoolbase_pk = request.user.schoolbase.pk if request.user.schoolbase.pk else 0

            # PR2023-05-14 debug: filter by u.schoolbase_id is not correct,
            # instead must filter bij grd.studsubj.stud.school.base_id
            # was: sql_list.append(''.join(('AND u.schoolbase_id=', str(schoolbase_pk), '::INT')))
            sql_list.append(''.join(('AND school.base_id=', str(requsr_schoolbase_pk), '::INT')))

        sql_list.append("GROUP BY u.id, exam.id, school.id")

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    # 0: user_id, 1: exam_id, 2: school_id, 3: count
                    approval_count_dict[(row[0], row[1], row[2])] = row[3]

        return approval_count_dict
    # - end of get_approval_count_dict

    def get_usercompensation_dict():
        # get rows from usercompensation,
        # create dict with key (user_pk, exam_pk, school_pk) and value = tuple (uc.amount, uc.id) PR2023-02-24

        # ATTENTION: sxm may use exams of ETE, therefore don't filter on examyear of exam,
        # this filter is ok: school.examyear_id

        usercompensation_dict = {}
        sql_list = [
            "SELECT uc.user_id, uc.exam_id, uc.school_id,",
            "uc.id, uc.amount, uc.meetings, uc.correction_amount, uc.correction_meetings",

            "FROM accounts_usercompensation AS uc",
            "INNER JOIN schools_school AS school ON (school.id = uc.school_id)",

            "WHERE school.examyear_id=" + str(sel_examyear.pk) + "::INT",
        ]

        if request.user.role == c.ROLE_008_SCHOOL:
            schoolbase_pk = request.user.schoolbase.pk if request.user.schoolbase.pk else 0
            sql_list.append(''.join(('AND school.base_id=', str(schoolbase_pk), '::INT')))

        sql = ' '.join(sql_list)

        if logging_on and False:
            for txt in sql_list:
                logger.debug(' > ' + str(txt))

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    # key is tuple of (user_id, exam_id, school_id)
                    # value is tuple of (uc_id, uc.amount, uc.meetings, uc.correction_amount, uc.correction_meetings)
                    usercompensation_dict[(row[0], row[1], row[2])] = (row[3], row[4], row[5], row[6], row[7])

        if logging_on:
            logger.debug('    usercompensation_dict: ' + str(usercompensation_dict))

        return usercompensation_dict
    # - end of get_usercompensation

    def create_tobe_lists():
        tobe_updated_list, tobe_added_list = [], []

 # +++++ loop through approval_count_dict +++++
        if approval_count_dict:
            for key_tuple, count_int in approval_count_dict.items():

                # check if record already exists in usercompensation_dict:
                if usercompensation_dict and key_tuple in usercompensation_dict:
                    # usercompensation_dict value is tuple: (uc_id, uc.amount, uc.meetings, uc.correction_amount, uc.correction_meetings)

                    uc_item = usercompensation_dict.get(key_tuple)
                    uc_amount = uc_item[1]

                    # add to tobe_updated_list if count has changed
                    if count_int != uc_amount:
                        uc_id = uc_item[0]
                        uc_meetings = uc_item[2]
                        uc_corr_amount = uc_item[3]
                        uc_corr_meetings = uc_item[4]

                        # calculate compensation

                        # note: when uc_corr_amount or uc_meetings or uc_corr_meetings changes, the new compensation will be stored.
                        # so here yoy only have to recalculate when uc_amount changes

                        total_amount = count_int + uc_corr_amount
                        total_meetings = uc_meetings + uc_corr_meetings
                        if total_meetings > max_meetings:
                            total_meetings = max_meetings

                        compensation = 0
                        if total_amount >= 1:
                            compensation = first_approval_amount + (other_approval_amount * (total_amount - 1))
                        if total_meetings:
                            compensation += meeting_amount * total_meetings
                        # create new tuple with new amount and new compensation
                        new_tuple = (uc_id, count_int, compensation)
                        tobe_updated_list.append(new_tuple)
                else:
                    # add to tobeadded_list if it does not yet exist
                    # PR2023-02-24 debug 'can only concatenate tuple (not "int") to tuple'
                    # was: key_tuple_with_count = key_tuple + count_int

                    compensation = 0
                    if count_int >= 1:
                        compensation = first_approval_amount + (other_approval_amount * (count_int - 1))

                        if logging_on:
                            logger.debug('     compensation ' + str(compensation) + '   f ' + str(
                                first_approval_amount) + '   o ' + str(other_approval_amount))

                    new_tuple = key_tuple + (count_int, compensation)

                    tobe_added_list.append(new_tuple)

        if logging_on:
            logger.debug('     len tobe_added_list ' + str(len(tobe_added_list)))

        # +++++ loop through usercompensation_dict +++++
        # check for deleted approvals
        if usercompensation_dict:
            for key_tuple in usercompensation_dict:
                if approval_count_dict and key_tuple in approval_count_dict:
                    pass
                else:
                    count_int = 0
                    uc_item = usercompensation_dict.get(key_tuple)

                    # add to tobe_updated_list with count = 0
                    uc_id = uc_item[0]
                    uc_meetings = uc_item[2]
                    uc_corr_amount = uc_item[3]
                    uc_corr_meetings = uc_item[4]

                    # calculate compensation
                    total_amount = count_int + uc_corr_amount
                    total_meetings = uc_meetings + uc_corr_meetings
                    if total_meetings > max_meetings:
                        total_meetings = max_meetings

                    # compensation is calculated for 1 school, max meetings is counted for each school
                    compensation = 0
                    if total_amount >= 1:
                        compensation = first_approval_amount + (other_approval_amount * (total_amount - 1))
                    if total_meetings:
                        compensation += meeting_amount * total_meetings

                    # create new tuple with new amount and new compensation
                    new_tuple = (uc_id, count_int, compensation)
                    tobe_updated_list.append(new_tuple)

        if logging_on:
            logger.debug('     len tobe_updated_list ' + str(len(tobe_updated_list)))
        return tobe_updated_list, tobe_added_list
    # - end of create_tobe_lists

    def update_usercompensation_batch(tobe_updated_list):  # PR2023-02-24
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('----------------- save_studsubj_batch  --------------------')
            logger.debug('tobe_updated_list: ' + str(tobe_updated_list))

        if tobe_updated_list:
            # sql_keys = {'ey_id': school.examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}

            """
            # you can define the types by casting the values of the first row:
            CREATE TEMP TABLE lookup (key, val) AS
            VALUES 
                (0::bigint, -99999::int), 
                (1, 100) ;
            """
            try:
                sql_list = ["DROP TABLE IF EXISTS tmp; CREATE TEMP TABLE tmp (",
                            "uc_id, am, comp) AS",
                            "VALUES (0::INT, 0::INT, 0::INT)"]

                for row in tobe_updated_list:
                    sql_item = ', '.join((str(row[0]), str(row[1]), str(row[2])))
                    sql_list.append(''.join((", (", sql_item, ")")))

                sql_list.extend((
                    "; UPDATE accounts_usercompensation AS uc",
                    "SET amount = tmp.am, compensation = tmp.comp",
                    "FROM tmp",
                    "WHERE uc.id = tmp.uc_id",
                    "RETURNING uc.id, uc.amount, uc.compensation;"
                ))

                sql = ' '.join(sql_list)

                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    rows = cursor.fetchall()

                if logging_on:
                    if rows:
                        logger.debug('............................................')
                        for row in rows:
                            logger.debug('row: ' + str(row))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
    # - end of update_usercompensation

    def insert_usercompensation_batch(tobe_added_list):
        #  from https://www.postgresqltutorial.com/postgresql-insert-multiple-rows/
        value_list = []
        value_str = None

        modifiedat_str = ''.join(("'", str(timezone.now()), "'"))
        for tobe_added_tuple in tobe_added_list:
            user_id = tobe_added_tuple[0]
            exam_id = tobe_added_tuple[1]
            school_id = tobe_added_tuple[2]
            count_int = tobe_added_tuple[3]
            compensation = tobe_added_tuple[4]
            join_str = ', '.join((str(user_id), str(exam_id), str(school_id), str(count_int), str(compensation),
                                  "0, 0, 0, FALSE",
                                  modifiedat_str))
            value_list.append(''.join(('(', join_str, ')')))
        if value_list:
            value_str = ', '.join(value_list)

        if value_str:
            sql_list = [
                "INSERT INTO accounts_usercompensation (user_id, exam_id, school_id, amount, compensation,",
                "meetings, correction_amount, correction_meetings, void, modifiedat",
                ") VALUES",
                value_str,
                "RETURNING accounts_usercompensation.id, accounts_usercompensation.amount;"
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()

            if logging_on:
                if rows:
                    logger.debug('............................................')
                    for row in rows:
                        logger.debug('row: ' + str(row))


    # ++++++++++++++++++++++++++++++++++++++

    if request.user.country and request.user.schoolbase and sel_examyear:
        if request.user.role >= c.ROLE_008_SCHOOL:

            try:
                first_approval_amount = c.CORRCOMP_FIRST_APPROVAL
                other_approval_amount = c.CORRCOMP_OTHER_APPROVAL
                meeting_amount = c.CORRCOMP_MEETING_COMP
                max_meetings = c.CORRCOMP_MAX_MEETINGS

                # - get dict with approval_count and dict with usercompensations
                approval_count_dict = get_approval_count_dict()
                if logging_on:
                    logger.debug('    approval_count_dict: ' + str(approval_count_dict))

                usercompensation_dict = get_usercompensation_dict()
                if logging_on:
                    logger.debug('    usercompensation_dict: ' + str(usercompensation_dict))

                tobe_updated_list, tobe_added_list = create_tobe_lists()

                if logging_on:
                    logger.debug('tobe_updated_list: ' + str(tobe_updated_list))
                    logger.debug('tobe_added_list: ' + str(tobe_added_list))

                if tobe_updated_list:
                    update_usercompensation_batch(tobe_updated_list)

                if tobe_added_list:
                    insert_usercompensation_batch(tobe_added_list)

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

# - end of update_usercompensation

#################################################################################


#//////////////////////////////////////////////////////////////////////////////////////////////////////////////
def create_excomp_xlsx(published_instance, sel_examyear, sel_school, save_to_disk, request, user_lang):  # PR2023-07-09

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_excomp_xlsx -----')

    is_saved_to_disk = False

# +++ get mapped_subject_rows    '
    # function gets all subjects of studsubj of this dep, not deleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]
    #subject_row_count, subject_pk_list, subject_code_list = \
    #    create_ex1_Ex4_mapped_subject_rows(examyear, sel_school, sel_department, True)  # is_reex=True

    #if logging_on:
    #    logger.debug('subject_row_count: ' + str(subject_row_count))
    #    logger.debug('subject_pk_list: ' + str(subject_pk_list))
    #    logger.debug('subject_code_list: ' + str(subject_code_list))

# +++ get dict of students with list of studsubj_pk, grouped by level_pk, with totals

    usercomp_rows, auth1_list, auth2_list = get_usercomp_rows(sel_examyear.pk, sel_school.base_id, {}, user_lang)

    response = None

    # - get text from examyearsetting
    settings = awpr_lib.get_library(sel_examyear, ['exform', 'ex1'])

    if settings and usercomp_rows:

        # PR2021-07-28 changed to file_dir = 'published/'
        # this one gives path: awpmedia / awpmedia / media / private / published
        # PR2021-08-06 create different folders for country and examyear
        # this one gives path: awpmedia / awpmedia / media / private / cur / 2022 / published
        # published_instance is None when downloading preliminary Ex1 form

        examyear_str = str(sel_examyear.code)

        file_path = None
        if published_instance:

# ---  create file_path
            # PR2021-08-07 changed to file_dir = 'country/examyear/published/'
            # this one gives path:awpmedia/awpmedia/media/cur/2022/published
            requsr_school = sch_mod.School.objects.get_or_none(
                base=request.user.schoolbase,
                examyear=sel_examyear
            )
            requsr_schoolcode = requsr_school.base.code if requsr_school.base.code else '---'
            country_abbrev = sel_examyear.country.abbrev.lower()
            file_dir = '/'.join((country_abbrev, examyear_str, requsr_schoolcode, 'exfiles'))
            file_path = '/'.join((file_dir, published_instance.filename))
            file_name = published_instance.name

            if logging_on:
                logger.debug('file_dir: ' + str(file_dir))
                logger.debug('file_name: ' + str(file_name))
                logger.debug('filepath: ' + str(file_path))

# ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
        ex_txt = gettext('Compensation correctors')
        title = ' '.join( (ex_txt, str(sel_examyear), sel_school.base.code, today_dte.isoformat() ) )
        file_name = title + ".xlsx"
        worksheet_name = str(_('Compensation'))

# - Create an in-memory output file for the new workbook.
        # from https://docs.python.org/3/library/tempfile.html
        temp_file = tempfile.TemporaryFile()

        output = temp_file if save_to_disk else io.BytesIO()
        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        #  book = xlsxwriter.Workbook(response, {'in_memory': True})
        book = xlsxwriter.Workbook(output)
        sheet = book.add_worksheet(worksheet_name)

        sheet.hide_zero()

# --- create format of workbook
        bold_format = book.add_format({'bold': True})
        bold_blue = book.add_format({'font_color': 'blue', 'bold': True})
        normal_blue = book.add_format({'font_color': 'blue'})

        f_comp_caption = awpr_excel.xl_book_add_format(book, font_size=8)
        f_comp_value = awpr_excel.xl_book_add_format(book,  font_size=8, font_color='blue', h_align='right', num_format='num_dig_2')
        f_exmyear_value  = awpr_excel.xl_book_add_format(book, font_color='blue', font_bold=True)

        row_align_left_blue = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter', 'border': True})
        row_align_center_blue = book.add_format({'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True})
        row_align_right_blue = book.add_format({'font_size': 8, 'font_color': 'blue', 'align': 'right', 'valign': 'vcenter', 'border': True, 'num_format': '#,##0.00'})

        th_merge_bold = book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        th_merge_bold.set_left()
        th_merge_bold.set_bottom()

        th_prelim = book.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        th_align_left = awpr_excel.xl_book_add_format(book, font_size=8, font_bold=True, text_wrap=True, border=True)
        th_align_center = awpr_excel.xl_book_add_format(book, font_size=8, font_bold=True, h_align='center', text_wrap=True, border=True)

        totalrow_align_center = book.add_format({'font_size': 8, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': True})
        totalrow_align_center_num0 = book.add_format({'font_size': 8, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': True, 'num_format': '#,##0'})
        totalrow_align_right_num2 = book.add_format({'font_size': 8, 'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': True, 'num_format': '#,##0.00'})
        totalrow_align_left = book.add_format({'font_size': 8, 'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': True})

        footer_number_format = book.add_format({'bold': True, 'num_format': '#,##0.00'})
        footer_number_format.set_bottom()
        footer_number_format.set_bg_color('#d8d8d8')  # #d8d8d8;  /* light grey 218 218 218 100%

        header_formats = [th_align_left, th_align_center, th_align_center, th_align_left,
                          th_align_left, th_align_center, th_align_center, th_align_center, th_align_center, th_align_center]
        row_formats = [row_align_left_blue, row_align_center_blue, row_align_center_blue, row_align_left_blue,
                       row_align_left_blue, row_align_center_blue, row_align_center_blue, row_align_center_blue, row_align_left_blue, row_align_right_blue]
        totalrow_formats = [totalrow_align_left, totalrow_align_center, totalrow_align_center, totalrow_align_center,
                            totalrow_align_center, totalrow_align_center_num0, totalrow_align_center_num0, totalrow_align_center_num0, totalrow_align_center, totalrow_align_right_num2]

        field_width = [25, 8, 8, 25, 9, 6, 15, 15, 9, 9]
        field_names = ['last_name', 'uc_depbase_code', 'uc_lvlbase_code', 'subj_name_nl',
                       'exam_version', 'examperiod',  'uc_amount', 'uc_meetings', 'uc_meetingdates', 'uc_comp_subtotal']
        field_captions = ['Naam gecommitteerde', 'Afdeling', 'Leerweg', 'Vak',
                           'Versie', 'Tijdvak',  'Aantal goedkeuringen', 'Aantal vergaderingen', 'Vergaderdata', 'Vergoeding']

# --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)
        row_index = 0
# --- title row
        # was: sheet.write(0, 0, str(_('Report')) + ':', bold)
        title_str = gettext('Compensations second correctors')

       # minond_str = gettext('MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT')
        minond_str = gettext('Ministry of Education, Culture, Youth and Sport').upper()
        sheet.write(row_index, 0, minond_str, bold_format)
        row_index += 1
        sheet.write(row_index, 0, title_str, bold_format)

        row_index += 2

        sheet.write(row_index, 0, gettext('School') + ':', bold_format)
        sheet.write(row_index, 1, sel_school.name, bold_blue)
        row_index += 1
        sheet.write(row_index, 0, gettext('Exam year') + ':', bold_format)
        sheet.write(row_index, 1, examyear_str, f_exmyear_value)
        row_index += 2

        col_count = len(field_width)

        if not save_to_disk:
            prelim_txt = gettext('Preliminary Compensation Form Second Correctors').upper()

            sheet.merge_range(row_index, 0, row_index, col_count - 1, prelim_txt, th_prelim)
            row_index += 1

# print compenastion per exam
        row_index += 1
        comp_captions = ( gettext('Compensation first exam'),
                          gettext('Compensation per following exam'),
                          gettext('Compensation per meeting'))
        comp_values = (c.CORRCOMP_FIRST_APPROVAL, c.CORRCOMP_OTHER_APPROVAL, c.CORRCOMP_MEETING_COMP)
        for i, comp_caption in enumerate(comp_captions):
            sheet.write(row_index, 0, comp_caption + ':', f_comp_caption)
            sheet.write(row_index, 1, comp_values[i] / 100, f_comp_value)
            sheet.write(row_index, 2, gettext('ANG'), f_comp_caption)
            row_index += 1

        #if has_published_ex1_rows(examyear, sel_school, sel_department):
        #    exists_txt = str(_('Attention: an Ex1 form has already been submitted. The subjects in that form are not included in this form.'))
        #    sheet.merge_range(row_index, 0, row_index, col_count - 1, exists_txt, th_exists)
        #    row_index += 1


# ---  table header row
        row_index += 1
        #sheet.merge_range(row_index, 0, row_index, col_count - 1, lvl_name, th_level)    first_subject_column = col_count

        for i, field_caption in enumerate(field_captions):
             sheet.write(row_index, i, field_caption, header_formats[i])

        start_row_index = row_index + 1

        for row in usercomp_rows:
            row_index += 1
            for i, field_name in enumerate(field_names):
                exc_format = row_formats[i]
                value = ''
                if isinstance(field_name, int):
                    # in subject column 'field_name' is subject_id
                    #subj_id_list = row.get('subj', [])
                    #if subj_id_list and field_name in subj_id_list:
                    #    value = 'x'

                    subj_nondel_list = row.get('subj_nondel', [])
                    if subj_nondel_list and field_name in subj_nondel_list:
                        value = 'x'
                        # PR2022-03-05 tobedeleted is deprecated. Was:
                        #value = 'o'
                    #subj_del_list = row.get('subj_del', [])
                    #if subj_del_list and field_name in subj_del_list:
                    #    value = 'x'
                    #    exc_format = excomp_formats['row_align_center_red']
                else:
                    value = row.get(field_name, '')
                sheet.write(row_index, i, value, exc_format)
# end of iterate through levels,
# ++++++++++++++++++++++++++++

# ---  table total row
        row_index += 1

        for i, field_name in enumerate(field_names):
            #logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
            value = ''

            if field_name in ('uc_amount', 'uc_meetings', 'uc_comp_subtotal'):

                upper_cell_ref = awpr_excel.xl_rowcol_to_cell(start_row_index, i)  # cell_ref: 10,0 > A11
                lower_cell_ref = awpr_excel.xl_rowcol_to_cell(row_index -1, i)  # cell_ref: 10,0 > A11

                sum_cell_ref = awpr_excel.xl_rowcol_to_cell(row_index, i)  # cell_ref: 10,0 > A11

                formula = ''.join(['=SUM(', upper_cell_ref, ':', lower_cell_ref, ')'])
                sheet.write_formula(sum_cell_ref, formula, totalrow_formats[i])

            elif field_name == 'uc_depbase_code':
                upper_cell_ref = awpr_excel.xl_rowcol_to_cell(start_row_index, i)  # cell_ref: 10,0 > A11
                lower_cell_ref = awpr_excel.xl_rowcol_to_cell(row_index -1, i)  # cell_ref: 10,0 > A11

                sum_cell_ref = awpr_excel.xl_rowcol_to_cell(row_index, i)  # cell_ref: 10,0 > A11

                formula = ''.join(['=SUBTOTAL(3, ', upper_cell_ref, ':', lower_cell_ref, ')'])
                sheet.write_formula(sum_cell_ref, formula, totalrow_formats[i])

            elif field_name == 'last_name':
                sheet.write(row_index, i, gettext('Total'), totalrow_formats[i])

            else:
                sheet.write(row_index, i, ' ', totalrow_formats[i])
                # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')

        first_footnote_row = row_index + 3

# ---  digitally signed by
        # PR2022-05-31 also show signatures on preliminary Ex4 form
        auth_row = first_footnote_row
        if save_to_disk or True:
            sheet.write(auth_row, 0, str(_('Digitally signed by')) + ':')
            auth_row += 2

    # - Chairperson
            sheet.write(auth_row, 0, str(_('Chairperson')) + ':')
            if auth1_list:
                for auth1_name in auth1_list:
                    if auth1_name:
                        sheet.write(auth_row, 1, auth1_name, normal_blue)
                        auth_row += 1
            else:
                auth_row += 1
            auth_row += 1

    # - Secretary
            sheet.write(auth_row, 0, str(_('Secretary')) + ':')
            if auth2_list:
                for auth2_name in auth2_list:
                    if auth2_name:
                        sheet.write(auth_row, 1, auth2_name, normal_blue)
                        auth_row += 1
            else:
                auth_row += 1

            auth_row += 1

    # -  place, date
        sheet.write(auth_row, 0, gettext('Place') + ':')
        sheet.write(auth_row, 1, str(sel_school.examyear.country.name), normal_blue)
        sheet.write(auth_row, 4, gettext('Date') + ':')
        sheet.write(auth_row, 6, today_formatted, normal_blue)

        book.close()

# +++ save file to disk
        if save_to_disk:
            excel_file = File(temp_file)

            published_instance.file.save(file_path, excel_file)

            # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
            published_instance.save(request=request)
            is_saved_to_disk = True

            logger.debug('file_path: ' + str(file_path))
            # file_path: media/private/published/Ex2A CUR13 ATC Vsbo SE-tv1 cav 2021-04-29 10u11.pdf
            # stored in dir:
            logger.debug('published_instance.file: ' + str(published_instance.file))
        else:
    # Rewind the buffer.
            output.seek(0)

        # Set up the Http response.
            response = HttpResponse(
                output,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

            response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    # response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # response['Content-Disposition'] = "attachment; filename=" + file_name
    return response, is_saved_to_disk
# --- end of create_excomp_xlsx


#//////////////////////////////////////////////////////////////////////////////////////////////////////////////
def create_payment_xlsx(published_instance, sel_examyear, payment_rows, usercomp_rows, save_to_disk, request, user_lang):  # PR2023-07-21

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_payment_xlsx -----')

    is_saved_to_disk = False

    response = None

    # - get text from examyearsetting
    # settings = awpr_lib.get_library(sel_examyear, ['exform', 'ex1'])

    if payment_rows:

        # PR2021-07-28 changed to file_dir = 'published/'
        # this one gives path: awpmedia / awpmedia / media / private / published
        # PR2021-08-06 create different folders for country and examyear
        # this one gives path: awpmedia / awpmedia / media / private / cur / 2022 / published
        # published_instance is None when downloading preliminary Ex1 form

        examyear_str = str(sel_examyear.code)

        file_path = None
        if published_instance:

# ---  create file_path
            # PR2021-08-07 changed to file_dir = 'country/examyear/published/'
            # this one gives path:awpmedia/awpmedia/media/cur/2022/published
            requsr_school = sch_mod.School.objects.get_or_none(
                base=request.user.schoolbase,
                examyear=sel_examyear
            )
            requsr_schoolcode = requsr_school.base.code if requsr_school.base.code else '---'
            country_abbrev = sel_examyear.country.abbrev.lower()
            file_dir = '/'.join((country_abbrev, examyear_str, requsr_schoolcode, 'exfiles'))
            file_path = '/'.join((file_dir, published_instance.filename))
            file_name = published_instance.name

            if logging_on:
                logger.debug('file_dir: ' + str(file_dir))
                logger.debug('file_name: ' + str(file_name))
                logger.debug('filepath: ' + str(file_path))

# ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
        title = ' '.join( ('Compensation payment form', str(sel_examyear), 'dd', today_dte.isoformat() ) )
        file_name = title + ".xlsx"

# - Create an in-memory output file for the new workbook.
        # from https://docs.python.org/3/library/tempfile.html
        temp_file = tempfile.TemporaryFile()

        output = temp_file if save_to_disk else io.BytesIO()
        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        #  book = xlsxwriter.Workbook(response, {'in_memory': True})
        book = xlsxwriter.Workbook(output)

        # --- create format of workbook
        bold_format = book.add_format({'bold': True})
        bold_blue = book.add_format({'font_color': 'blue', 'bold': True})
        normal_blue = book.add_format({'font_color': 'blue'})

        f_comp_caption = awpr_excel.xl_book_add_format(book, font_size=8)
        f_comp_value = awpr_excel.xl_book_add_format(book, font_size=8, font_color='blue', h_align='right',
                                                     num_format='num_dig_2')
        f_exmyear_value = awpr_excel.xl_book_add_format(book, font_color='blue', font_bold=True, h_align='right')

        row_align_left_blue = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter', 'border': True})
        row_align_center_blue = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True})
        row_align_center_blue_num0 = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True,
             'num_format': '#,##0'})
        row_align_right_blue_num2 = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'align': 'right', 'valign': 'vcenter', 'border': True,
             'num_format': '#,##0.00'})

        th_prelim = book.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        th_align_left = awpr_excel.xl_book_add_format(book, font_size=8, font_bold=True, v_align='top', text_wrap=True,
                                                      border=True)
        th_align_center = awpr_excel.xl_book_add_format(book, font_size=8, font_bold=True, h_align='center',
                                                        v_align='top', text_wrap=True, border=True)
        th_align_right = awpr_excel.xl_book_add_format(book, font_size=8, font_bold=True, h_align='right',
                                                       v_align='top', text_wrap=True, border=True)

        totalrow_align_center_num0 = awpr_excel.xl_book_add_format(book, font_size=8, font_bold=True, h_align='center',
                                                                   text_wrap=True, border=True, num_format='#,##0')
        totalrow_align_right_num2 = awpr_excel.xl_book_add_format(book, font_size=8, font_bold=True, h_align='right',
                                                                  text_wrap=True, border=True, num_format='#,##0.00')
        totalrow_align_left = awpr_excel.xl_book_add_format(book, font_size=8, font_bold=True, h_align='left',
                                                            text_wrap=True, border=True)

# ++++++++++++++ worksheet payment ++++++++++++++++++++++++++++++++++
        worksheet_name = gettext('Total compensation')
        sheet = book.add_worksheet(worksheet_name)

        sheet.hide_zero()

        header_formats = [th_align_left, th_align_left, th_align_left,
                          th_align_left, th_align_left, th_align_left,
                          th_align_center, th_align_center, th_align_center,
                          th_align_right, th_align_center]
        row_formats = [row_align_left_blue, row_align_left_blue, row_align_left_blue,
                       row_align_left_blue, row_align_left_blue, row_align_left_blue,
                       row_align_center_blue_num0, row_align_center_blue_num0, row_align_center_blue_num0,
                       row_align_right_blue_num2, row_align_center_blue]
        totalrow_formats = [totalrow_align_left, totalrow_align_left, totalrow_align_left,
                            totalrow_align_left, totalrow_align_left, totalrow_align_left,
                            totalrow_align_center_num0, totalrow_align_center_num0, totalrow_align_center_num0,
                            totalrow_align_right_num2, totalrow_align_left]

        field_width = [10, 10, 25, 25, 10, 25, 10, 10, 10, 10, 10]
        field_names = ['idnumber', 'cribnumber', 'last_name', 'bankname', 'bankaccount', 'beneficiary',
                       'exam_count', 'sum_amount', 'sum_meetings', 'sum_compensation', 'published_status']
        field_captions = [gettext('ID number'), gettext('CRIB number'), gettext('Name of Second Corrector'),
                          gettext('Bank'), gettext('Bank account number'), gettext('Name of the account holder'), gettext('Number of different exams'),
                          gettext('Number of approvals'), gettext('Number of meetings'), gettext('Compensation'), gettext('Submitted by school')]

# --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)
        row_index = 0

# --- title row
        title_str = gettext('Compensations second correctors')

        minond_str = gettext('Ministry of Education, Culture, Youth and Sport').upper()
        sheet.write(row_index, 0, minond_str, bold_format)
        row_index += 1
        sheet.write(row_index, 0, title_str, bold_format)

        row_index += 2
        sheet.write(row_index, 0, gettext('Exam year') + ':', bold_format)
        sheet.write(row_index, 1, examyear_str, f_exmyear_value)
        row_index += 2

        col_count = len(field_width)

        if not save_to_disk:
            prelim_txt = gettext('Compensations second correctors').upper()

            sheet.merge_range(row_index, 0, row_index, col_count - 1, prelim_txt, th_prelim)
            row_index += 1

    # print compenastion per exam
        row_index += 1
        comp_captions = ( gettext('Compensation first exam'),
                          gettext('Compensation per following exam'),
                          gettext('Compensation per meeting'))
        comp_values = (c.CORRCOMP_FIRST_APPROVAL, c.CORRCOMP_OTHER_APPROVAL, c.CORRCOMP_MEETING_COMP)
        for i, comp_caption in enumerate(comp_captions):
            sheet.write(row_index, 0, comp_caption + ':', f_comp_caption)
            sheet.write(row_index, 2, comp_values[i] / 100, f_comp_value)
            sheet.write(row_index, 3, gettext('ANG'), f_comp_caption)
            row_index += 1

        #if has_published_ex1_rows(examyear, sel_school, sel_department):
        #    exists_txt = str(_('Attention: an Ex1 form has already been submitted. The subjects in that form are not included in this form.'))
        #    sheet.merge_range(row_index, 0, row_index, col_count - 1, exists_txt, th_exists)
        #    row_index += 1

# ---  table header row
        row_index += 1
        #sheet.merge_range(row_index, 0, row_index, col_count - 1, lvl_name, th_level)    first_subject_column = col_count

        for i, field_caption in enumerate(field_captions):
             sheet.write(row_index, i, field_caption, header_formats[i])

        start_row_index = row_index + 1

        for row in payment_rows:
            row_index += 1
            for i, field_name in enumerate(field_names):
                exc_format = row_formats[i]
                value = ''
                if field_name == 'published_status':

                    status = row.get(field_name)
                    if status == 2:
                        # fully approved
                        value = u"\u2B24"  # large solid circle
                        exc_format = row_align_center_blue

                    elif status == 1:
                        # partly approved
                        value = u"\u2B58"  # large outlined circle

                else:
                    value = row.get(field_name, '')
                sheet.write(row_index, i, value, exc_format)
# end of iterate through levels,


# ---  table total row
        row_index += 1
        #         field_names = ['idnumber', 'cribnumber', 'last_name', 'bankname', 'bankaccount', 'beneficiary',
        #         'exam_count', 'sum_amount', 'sum_meetings', 'sum_compensation']
        for i, field_name in enumerate(field_names):

            if field_name in ('exam_count', 'sum_amount', 'sum_meetings', 'sum_compensation'):

                upper_cell_ref = awpr_excel.xl_rowcol_to_cell(start_row_index, i)  # cell_ref: 10,0 > A11
                lower_cell_ref = awpr_excel.xl_rowcol_to_cell(row_index -1, i)  # cell_ref: 10,0 > A11

                sum_cell_ref = awpr_excel.xl_rowcol_to_cell(row_index, i)  # cell_ref: 10,0 > A11

                formula = ''.join(['=SUM(', upper_cell_ref, ':', lower_cell_ref, ')'])
                sheet.write_formula(sum_cell_ref, formula, totalrow_formats[i])

            elif field_name == 'last_name':
                sheet.write(row_index, i, gettext('Total'), totalrow_formats[i])

            else:
                sheet.write(row_index, i, ' ', totalrow_formats[i])
                # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')

    # -  place, date
        row_index += 2
        sheet.write(row_index, 0, gettext('Date') + ':')
        sheet.write(row_index, 1, today_formatted, normal_blue)

# ++++++++++++++ worksheet compensation details ++++++++++++++++++++++++++++++++++
        sheet = book.add_worksheet(gettext('Compensation details'))

        sheet.hide_zero()

 # --- create format of workbook
        header_formats = [th_align_left, th_align_left, th_align_left, th_align_center, th_align_center, th_align_left,
                          th_align_left, th_align_center, th_align_center, th_align_center, th_align_center, th_align_center, th_align_center,
                          th_align_center, th_align_center]
        row_formats = [row_align_left_blue, row_align_left_blue,row_align_left_blue,row_align_center_blue, row_align_center_blue, row_align_left_blue,
                       row_align_left_blue, row_align_center_blue, row_align_center_blue, row_align_center_blue,
                       row_align_left_blue, row_align_left_blue, row_align_left_blue, row_align_right_blue_num2, row_align_center_blue]
        totalrow_formats = [totalrow_align_left, totalrow_align_left, totalrow_align_left, totalrow_align_center_num0, totalrow_align_center_num0, totalrow_align_center_num0,
                            totalrow_align_center_num0, totalrow_align_center_num0, totalrow_align_center_num0,
                            totalrow_align_center_num0, totalrow_align_center_num0, totalrow_align_center_num0, totalrow_align_center_num0, totalrow_align_right_num2, totalrow_align_center_num0]

        field_width = [25, 8, 12, 8, 8, 25,
                       10, 8, 10, 10, 10,
                       10, 10, 10, 10]
        field_names = ['last_name', 'uc_sb_code', 'uc_school_abbrev', 'uc_depbase_code', 'uc_lvlbase_code', 'subj_name_nl',
                       'exam_version', 'examperiod', 'uc_amount', 'uc_meetings', 'uc_meetingdates',
                       'uc_corr_amount', 'uc_corr_meetings', 'uc_compensation', 'datepublished']
        field_captions = [gettext('Name of Second Corrector'), gettext('School code'), gettext('School'), gettext('Department'), gettext('Learning path'), gettext('Subject'),
                          gettext('Version'), gettext('Exam period'), gettext('Number of approvals'), gettext('Number of meetings'), gettext('Meeting dates'),
                          gettext('Correction of approvals'), gettext('Correction of meetings'),
                          gettext('Compensation'), gettext('Date submitted by school')]

        # --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)
        row_index = 0
        # --- title row
        # was: sheet.write(0, 0, str(_('Report')) + ':', bold)
        title_str = gettext('Compensations second correctors')

        # minond_str = gettext('MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT')
        minond_str = gettext('Ministry of Education, Culture, Youth and Sport').upper()
        sheet.write(row_index, 0, minond_str, bold_format)
        row_index += 1
        sheet.write(row_index, 0, title_str, bold_format)

        row_index += 2

        sheet.write(row_index, 0, gettext('Exam year') + ':', bold_format)
        sheet.write(row_index, 1, examyear_str, f_exmyear_value)
        row_index += 2

        col_count = len(field_width)

        if not save_to_disk:
            prelim_txt = gettext('Compensations second correctors').upper()

            sheet.merge_range(row_index, 0, row_index, col_count - 1, prelim_txt, th_prelim)
            row_index += 1

        # print compenastion per exam
        row_index += 1
        comp_captions = (gettext('Compensation first exam'),
                         gettext('Compensation per following exam'),
                         gettext('Compensation per meeting'))
        comp_values = (c.CORRCOMP_FIRST_APPROVAL, c.CORRCOMP_OTHER_APPROVAL, c.CORRCOMP_MEETING_COMP)
        for i, comp_caption in enumerate(comp_captions):
            sheet.write(row_index, 0, comp_caption + ':', f_comp_caption)
            sheet.write(row_index, 1, comp_values[i] / 100, f_comp_value)
            sheet.write(row_index, 2, gettext('ANG'), f_comp_caption)
            row_index += 1

        # if has_published_ex1_rows(examyear, sel_school, sel_department):
        #    exists_txt = str(_('Attention: an Ex1 form has already been submitted. The subjects in that form are not included in this form.'))
        #    sheet.merge_range(row_index, 0, row_index, col_count - 1, exists_txt, th_exists)
        #    row_index += 1

        # ---  table header row
        row_index += 1
        # sheet.merge_range(row_index, 0, row_index, col_count - 1, lvl_name, th_level)    first_subject_column = col_count

        for i, field_caption in enumerate(field_captions):
            sheet.write(row_index, i, field_caption, header_formats[i])

        start_row_index = row_index + 1

        for row in usercomp_rows:
            row_index += 1
            for i, field_name in enumerate(field_names):
                exc_format = row_formats[i]

                value = row.get(field_name, '')
                sheet.write(row_index, i, value, exc_format)
    # ---  table total row
        row_index += 1

        for i, field_name in enumerate(field_names):
            # logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
            value = ''

            if field_name in ('uc_amount', 'uc_meetings', 'uc_corr_amount', 'uc_corr_meetings', 'uc_compensation'):

                upper_cell_ref = awpr_excel.xl_rowcol_to_cell(start_row_index, i)  # cell_ref: 10,0 > A11
                lower_cell_ref = awpr_excel.xl_rowcol_to_cell(row_index - 1, i)  # cell_ref: 10,0 > A11

                sum_cell_ref = awpr_excel.xl_rowcol_to_cell(row_index, i)  # cell_ref: 10,0 > A11

                formula = ''.join(['=SUM(', upper_cell_ref, ':', lower_cell_ref, ')'])
                sheet.write_formula(sum_cell_ref, formula, totalrow_formats[i])

            elif field_name == 'last_name':
                sheet.write(row_index, i, gettext('Total'), totalrow_formats[i])

            else:
                sheet.write(row_index, i, ' ', totalrow_formats[i])

 # -  place, date
        row_index += 2
        sheet.write(row_index, 0, gettext('Date') + ':')
        sheet.write(row_index, 1, today_formatted, normal_blue)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        book.close()

# +++ save file to disk
        if save_to_disk:
            excel_file = File(temp_file)

            published_instance.file.save(file_path, excel_file)

            # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
            published_instance.save(request=request)
            is_saved_to_disk = True

            logger.debug('file_path: ' + str(file_path))
            # file_path: media/private/published/Ex2A CUR13 ATC Vsbo SE-tv1 cav 2021-04-29 10u11.pdf
            # stored in dir:
            logger.debug('published_instance.file: ' + str(published_instance.file))
        else:
    # Rewind the buffer.
            output.seek(0)

        # Set up the Http response.
            response = HttpResponse(
                output,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

            response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    # response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # response['Content-Disposition'] = "attachment; filename=" + file_name
    return response, is_saved_to_disk
# --- end of create_payment_xlsx

