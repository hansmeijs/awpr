# PR2023-03-23
import io
import tempfile
import xlsxwriter
from django.contrib.auth.decorators import login_required
from django.core.files import File

from django.db import connection
from django.http import HttpResponse

from django.contrib.auth import get_user_model, authenticate
# UserModel = get_user_model()

from django.utils import timezone
from django.utils.decorators import method_decorator


#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext, gettext_lazy as _, pgettext_lazy
from django.views.generic import View

from accounts import models as acc_mod
from accounts import permits as acc_prm
from accounts import views as acc_view
from awpr import settings as s
from awpr import constants as c
from awpr import validators as awpr_val

from awpr import functions as af
from awpr import menus as awpr_menu
from awpr import excel as awpr_excel

from schools import models as sch_mod
from subjects import  models as subj_mod

from datetime import datetime
import pytz
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

        msg_html = None
        update_wrap = {}
        data_has_changed = False

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')
            # upload_dict: {'user_pk': 1472, 'mode': 'update', 'allowed_clusters': [1740, 1743]}

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get permit
            page_name = 'page_corrector'
            has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

            if not has_permit:
                msg_html = acc_prm.err_html_no_permit()  # default: 'to perform this action')
            else:

# - get variables
                user_pk = upload_dict.get('user_pk')
                ual_pk = upload_dict.get('ual_pk')

                updated_rows = []
                error_list = []

                append_dict = {}

# - create student_row, also when deleting failed, not when deleted ok, in that case student_row is added in delete_student
                userallowed_instance = acc_mod.UserAllowed.objects.get_or_none(
                    pk=ual_pk,
                    user_id=user_pk
                )
                if logging_on:
                    logger.debug('    userallowed_instance:' + str(userallowed_instance))

                if userallowed_instance:
                    new_allowed_clusters_str = None
                    new_allowed_clusters_list = upload_dict.get('allowed_clusters')
                    if new_allowed_clusters_list:
                        new_allowed_clusters_list.sort()
                        new_allowed_clusters_str = json.dumps(new_allowed_clusters_list)

                    if logging_on:
                        logger.debug('    new_allowed_clusters_list:' + str(new_allowed_clusters_list) + ' ' + str(
                            type(new_allowed_clusters_list)))
                        logger.debug('    new_allowed_clusters_str:' + str(new_allowed_clusters_str) + ' ' + str(
                            type(new_allowed_clusters_str)))

                    saved_allowed_clusters_str = getattr(userallowed_instance, 'allowed_clusters')

                    if logging_on:
                        logger.debug('    new_allowed_clusters_str: ' + str(new_allowed_clusters_str))
                        logger.debug('    saved_allowed_clusters_str: ' + str(saved_allowed_clusters_str))

                    if new_allowed_clusters_str != saved_allowed_clusters_str:
                        setattr(userallowed_instance, 'allowed_clusters', new_allowed_clusters_str)
                        userallowed_instance.save()

                        updated_corrector_rows = acc_view.create_user_rowsNEW(
                            sel_examyear=userallowed_instance.examyear if userallowed_instance else None,
                            request=request,
                            user_pk=user_pk
                        )

                        if logging_on:
                            logger.debug('    updated_corrector_rows: ' + str(updated_corrector_rows))
                        if updated_corrector_rows:
                            update_wrap['updated_corrector_rows'] = updated_corrector_rows

# - addd msg_html to update_wrap
        if msg_html:
            update_wrap['msg_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - ens of UserAllowedClusterUploadView

########################################################################
# === UserUploadView ===================================== PR2023-02-25
@method_decorator([login_required], name='dispatch')
class UserCompensationUploadView(View):

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ')
            logger.debug(' ========== UserCompensationUploadView ===============')

        msg_html = None
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
            page_name = 'page_corrector'
            has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

            if logging_on:
                logger.debug('    has_permit:' + str(has_permit))

            if not has_permit:
                msg_html = acc_prm.err_html_no_permit()  # default: 'to perform this action')
            else:

# - get variables
                usercompensation_pk = upload_dict.get('usercompensation_pk')

                updated_rows = []
                error_list = []

                append_dict = {}

# ----- get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_edit, sel_msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if logging_on:
                    logger.debug('    may_edit:       ' + str(may_edit))
                    logger.debug('    sel_msg_list:       ' + str(sel_msg_list))
                    logger.debug('    upload_dict:       ' + str(upload_dict))

                if sel_msg_list:
                    msg_html = acc_prm.msghtml_from_msglist_with_border(sel_msg_list)

                else:

# +++  get existing usercompensation_instance
                    usercompensation_instance = acc_mod.UserCompensation.objects.get_or_none(
                        id=usercompensation_pk
                    )

                    if usercompensation_instance:
                        if logging_on:
                            logger.debug('    usercompensation_instance: ' + str(usercompensation_instance))
# +++ Update student, also when it is created, not when delete has failed (when deleted ok there is no student)
                        update_usercompensation_instance(
                            instance=usercompensation_instance,
                            upload_dict=upload_dict,
                            request=request
                        )

# - create student_row, also when deleting failed, not when deleted ok, in that case student_row is added in delete_student
                    if usercompensation_instance:
                        updated_rows = create_usercompensation_rows(sel_examyear, request)

                update_wrap['updated_usercompensation_rows'] = updated_rows

# - addd msg_html to update_wrap
        if msg_html:
            update_wrap['msg_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UserCompensationUploadView

#######################################################
def update_usercompensation_instance(instance, upload_dict, request):
    # --- update existing and new instance PR2023-02-25
    instance_pk = instance.pk if instance else None

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_usercompensation_instance -------')
        logger.debug('    upload_dict: ' + str(upload_dict))
        logger.debug('    instance:    ' + str(instance))

# ----- get user_lang

    changes_are_saved = False
    save_error = False
    field_error = False

    # TODO add error fieldname to err_fields, instead of field_error

    if instance:
        save_changes = False
        for field, new_value in upload_dict.items():

    # - save changes in fields
            if field in ('meetingdate1', 'meetingdate2', 'meetings'):
                saved_value = getattr(instance, field)
                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

            elif field in ('auth1by', 'auth2by'):
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

    if logging_on:
        logger.debug('    changes_are_saved: ' + str(changes_are_saved))

    return changes_are_saved, save_error, field_error
# - end of update_usercompensation_instance


#####################################################################################
@method_decorator([login_required], name='dispatch')
class UserCompensationApproveSubmitView(View):  # PR2021-07-26 PR2022-05-30 PR2023-01-10

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UserCompensationApproveSubmitView ============= ')

################################
        def get_studsubjects(sel_examperiod, sel_school, sel_department, sel_level, is_submit):
            if logging_on:
                logger.debug('    is_submit: ' + str(is_submit))
            # PR2023-02-12
            studsubject_rows = []

            if sel_examperiod == 2:
                auth_clause = "studsubj.reex_auth1by_id AS auth1by_id, studsubj.reex_auth2by_id AS auth2by_id, studsubj.reex_published_id AS published_id,"
            elif sel_examperiod == 3:
                auth_clause = "studsubj.reex3_auth1by_id AS auth1by_id, studsubj.reex3_auth2by_id AS auth2by_id, studsubj.reex3_published_id AS published_id,"
            else:
                auth_clause = "studsubj.subj_auth1by_id AS auth1by_id, studsubj.subj_auth2by_id AS auth2by_id, studsubj.subj_published_id AS published_id,"

            if (sel_examperiod and sel_school and sel_department):
                try:
                    sql_list = [
                        "SELECT stud.id AS stud_id, stud.idnumber AS idnr, stud.examnumber AS exnr, stud.gender,",
                        "stud.lastname AS ln, stud.firstname AS fn, stud.prefix AS pref, stud.classname AS class, ",
                        "stud.level_id, lvl.name AS lvl_name, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ",

                        "CASE WHEN stud.subj_composition_ok OR stud.subj_dispensation",
                        #PR2023-02-17 skip composition check when iseveningstudent, islexstudent or partial_exam
                        "OR stud.iseveningstudent OR stud.islexstudent OR stud.partial_exam",
                        "THEN FALSE ELSE TRUE END AS composition_error,",

                        "stud.regnumber AS regnr, stud.diplomanumber AS dipnr, stud.gradelistnumber AS glnr,",
                        "stud.iseveningstudent AS evest, stud.islexstudent AS lexst,",
                        "stud.bis_exam AS bisst, stud.partial_exam AS partst, stud.withdrawn AS wdr,",

                        "studsubj.id AS studsubj_id, studsubj.tobedeleted AS studsubj_tobedeleted,",

                        auth_clause,
                        "subj.id AS subj_id, subjbase.code AS subj_code",

                        "FROM students_studentsubject AS studsubj",
                        "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                        "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                        "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",

                        "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                        "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                        "WHERE school.id = " + str(sel_school.pk) + "::INT",
                        "AND dep.id = " + str(sel_department.pk) + "::INT",

                        "AND NOT stud.deleted AND NOT studsubj.deleted"
                        ]

                # filter reex subjects when ex4 or ex4ep3
                    if sel_examperiod == 2:
                        sql_list.append("AND stud.has_reex")
                    elif sel_examperiod == 3:
                        sql_list.append("AND stud.has_reex03")

        # - may also filter on level when submitting Ex form
                    # PR2023-02-12 request MPC: must be able to submit per level tkl / pkl/pbl

                    # PR2023-02-19 debug:  VWO didnt show records, because of filter sel_lvlbase_pk=5
                    # solved bij adding: if sel_department.level_req

                    if sel_department.level_req and sel_level:
                        sql_list.append(''.join(("AND (lvl.base_id = ", str(sel_level.base_id), "::INT)")))

        # - other filters are only allowed when approving, not when is_submit
                    if not is_submit:
                        # - get selected values from usersetting selected_dict
                        sel_sctbase_pk, sel_subject_pk, sel_cluster_pk = None, None, None
                        selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                        if selected_dict:
                            sel_sctbase_pk = selected_dict.get(c.KEY_SEL_SCTBASE_PK)
                            sel_subject_pk = selected_dict.get(c.KEY_SEL_SUBJECT_PK)
                            sel_cluster_pk = selected_dict.get(c.KEY_SEL_CLUSTER_PK)

                        if sel_sctbase_pk:
                            sql_list.append(''.join(("AND sct.base_id = ", str(sel_sctbase_pk), "::INT")))

            # - filter on selected subject, not when is_submit TODO to be changed to subjectbase
                        if sel_subject_pk:
                            sql_list.append(''.join(("AND subj.id = ", str(sel_subject_pk), "::INT")))

            # - filter on selected sel_cluster_pk, not when is_submit
                        if sel_cluster_pk and not is_submit:
                            sql_list.append(''.join(("AND (studsubj.cluster_id = ", str(sel_cluster_pk), "::INT)")))

        # - get allowed_sections_dict from request
                    userallowed_sections_dict = acc_prm.get_userallowed_sections_dict_from_request(request)
                    # allowed_sections_dict: {'2': {'1': {'4': [117, 114], '5': [], '-9': [118, 121]}}} <class 'dict'>

        # - filter on allowed depbases, levelbase, subjectbases, not when is_submit PR2023-02-18
                    #TODO when approve: filter on all allowed, when submit: only filter on allowed lvlbase
                    #dont filter on allowed subjects and allowed clusters, but do filter on allowed lvlbases'
                    userallowed_schoolbase_dict, userallowed_depbases_pk_arr = acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(userallowed_sections_dict, sel_school.base_id)
                    allowed_depbase_dict, allowed_lvlbase_pk_arr = acc_prm.get_userallowed_depbase_dict_lvlbases_pk_arr(userallowed_schoolbase_dict, sel_department.base_id)

                    allowed_lvlbase_clause = acc_prm.get_sqlclause_allowed_lvlbase_from_lvlbase_pk_arr(allowed_lvlbase_pk_arr)

                    if logging_on:
                        logger.debug('    allowed_sections_dict: ' + str(userallowed_sections_dict))
                        logger.debug('    userallowed_schoolbase_dict: ' + str(userallowed_schoolbase_dict))
                        logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict))
                        logger.debug('    allowed_lvlbase_pk_arr: ' + str(allowed_lvlbase_pk_arr))
                        logger.debug('    allowed_lvlbase_clause: ' + str(allowed_lvlbase_clause))

                    if allowed_lvlbase_clause:
                        sql_list.append(allowed_lvlbase_clause)

                    if logging_on and False:
                        for sql_txt in sql_list:
                            logger.debug('  > ' + str(sql_txt))

        # - don't filter on allowed clusters PR2023-02-18
                    # PR2022-04-20 tel Bruno New Song: chairperson is also examiner.
                    # must be able to approve all subjects as chairperson.
                    # therefore: don't filter on allowed clusters when requsr is chairperson or secretary

                    sql_list.append("ORDER BY stud.lastname, stud.firstname")

                    sql = ' '.join(sql_list)
                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                        studsubject_rows = af.dictfetchall(cursor)

                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

            return studsubject_rows

################################
# function sets auth and publish of studentsubject records of current department # PR2021-07-25
        update_wrap = {}
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

    # -  get user_lang
            user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
            activate(user_lang)

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

                form_name = 'excomp'

# - get selected mode. Modes are 'approve_test', 'approve_save', 'approve_reset', 'submit_test' 'submit_save'
                mode = upload_dict.get('mode')
                is_approve = True if mode in ('approve_test', 'approve_save', 'approve_reset') else False
                is_submit = True if mode in ('submit_test', 'submit_save') else False
                is_reset = True if mode == 'approve_reset' else False
                is_test = True if mode in ('approve_test', 'submit_test') else False

                if logging_on:
                    logger.debug('    upload_dict ' + str(upload_dict))
                    logger.debug('    mode:       ' + str(mode))

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

                    usercompensation_rows = create_usercompensation_rows(
                        sel_examyear=sel_examyear,
                        request=request
                    )
                    if logging_on:
                        logger.debug('    row_count:      ' + str(len(usercompensation_rows)))

                    count_dict = {'count': 0,
                                  'student_count': 0,
                                  'student_committed_count': 0,
                                  'student_saved_count': 0,
                                  'already_published': 0,
                                  'double_approved': 0,
                                  'studsubj_tobedeleted': 0,
                                  'committed': 0,
                                  'saved': 0,
                                  'saved_error': 0,
                                  'reset': 0,
                                  'already_approved': 0,
                                  'auth_missing': 0
                                  #'test_is_ok': False
                                }
                    if usercompensation_rows:

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
                                request=request)
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
                        tobesaved_usercomp_pk_list = []

# +++++ loop through usercompensation_rows +++++
                        for usercomp_row in usercompensation_rows:

                            if logging_on and False:
                                logger.debug('............ ')
                                logger.debug('   ' + str(usercomp_row))

                            row_count += 1

                            is_committed = False
                            is_saved = False

                            if is_approve:
                                is_committed, is_saved = approve_usercomp(
                                    usercomp_row=usercomp_row,
                                    requsr_auth=requsr_auth,
                                    is_test=is_test,
                                    is_reset=is_reset,
                                    count_dict=count_dict,
                                    request=request
                                )

                            elif is_submit:
                                is_committed, is_saved = submit_usercom(
                                    usercomp_row=usercomp_row,
                                    is_test=is_test,
                                    count_dict=count_dict
                                )

                            if is_saved:
                                usercomp_pk = usercomp_row.get('id')
                                if usercomp_pk:
                                    tobesaved_usercomp_pk_list.append(usercomp_pk)


                            #if is_committed:
                            #    if student_pk not in student_committed_list:
                            #        student_committed_list.append(student_pk)
                            #if is_saved:
                            #    if student_pk not in student_saved_list:
                            #        student_saved_list.append(student_pk)

# +++++  end of loop through  studsubjects

                        if logging_on:
                            logger.debug('    tobesaved_usercomp_pk_list: ' + str(tobesaved_usercomp_pk_list))

                        auth_missing_count = count_dict.get('auth_missing', 0)
                        double_approved_count = count_dict.get('double_approved', 0)

                        test_has_failed = False
                        if not row_count:
                            test_has_failed = True

                        elif is_submit and auth_missing_count:
                            test_has_failed = True
                        elif is_submit and double_approved_count:
                            test_has_failed = True

                        count_dict['count'] = row_count
                        #count_dict['student_committed_count'] = student_committed_count
                        #count_dict['student_saved_count'] = len(student_saved_list)

                        if logging_on:
                            logger.debug('    count_dict: ' + str(count_dict))

                        update_wrap['approve_count_dict'] = count_dict

# - create msg_html with info of rows
                        msg_html = self.create_msg_list(
                            sel_department=sel_department,
                            sel_level=sel_level,
                            count_dict=count_dict,
                            requsr_auth=requsr_auth,
                            is_approve=is_approve,
                            is_test=is_test,
                            published_instance_filename=published_instance_filename
                        )

# +++++ create Ex1 Ex4 form
                        if row_count:
                            saved_studsubj_pk_list = []
                            if not is_test:
                                if is_submit:
                                    self.create_usercomp_form(
                                        published_instance=published_instance,
                                        sel_examyear=sel_examyear,
                                        sel_school=sel_school,
                                        sel_department=sel_department,
                                        sel_level=sel_level,
                                        save_to_disk=True,
                                        request=request,
                                        user_lang=user_lang
                                    )

# +++++ batch save approval / published PR2023-01-10
                                if logging_on:
                                    logger.debug('    tobesaved_usercomp_pk_list: ' + str(tobesaved_usercomp_pk_list))

                                if tobesaved_usercomp_pk_list:
                                    err_html = None
                                    if is_approve:
                                        saved_studsubj_pk_list, err_html = self.save_approved_in_studsubj(tobesaved_usercomp_pk_list, is_reset, 'subj_', requsr_auth, request.user)
                                    elif is_submit:
                                        saved_studsubj_pk_list, err_html = self.save_published_in_studsubj(tobesaved_usercomp_pk_list, 'subj_', published_instance.pk)

                                    if err_html:
                                        msg_html = "<div class='p-2 border_bg_invalid'>" + err_html + "</div>"

                                    if logging_on:
                                        logger.debug('    saved_studsubj_pk_list: ' + str(saved_studsubj_pk_list))

                            # - delete the 'tobedeleted' rows from StudSubject, only after submitting and no test!

                                # PR2022-12-30 instead of updating each studsubj instance separately, create list of tobesaved studsubj_pk
                                # list is created outside this function, when is_saved = True

                            # TODO put back 'tobedeleted' functions
                                #self.delete_tobedeleted_from_studsubj(
                                #    published_instance=published_instance,
                                #    sel_examyear=sel_examyear,
                                #    sel_school=sel_school,
                                #    sel_department=sel_department,
                                #    request=request
                                #)

                            if logging_on:
                                logger.debug('    saved_studsubj_pk_list: ' + str(saved_studsubj_pk_list))

        # - add rows to studsubj_rows, to be sent back to page
                            # to increase speed, dont create return rows but refresh page after finishing this request
                            if saved_studsubj_pk_list:
                                pass
                                #studsubj_rows = create_studentsubject_rows(
                                #    sel_examyear=sel_examyear,
                                #    sel_schoolbase=sel_school.base if sel_school else None,
                                #    sel_depbase=sel_department.base if sel_department else None,
                                #    append_dict={},
                                #    request=request,
                                #    requsr_same_school=True, # when requsr_same_school=True, it includes students without studsubjects
                                #    studsubj_pk_list=saved_studsubj_pk_list
                                #)

                            if logging_on:
                                logger.debug('    studsubj_rows: ' + str(studsubj_rows))

                            #if (studsubj_rows):
                            #    update_wrap['updated_studsubj_approve_rows'] = studsubj_rows

                            if is_test:
                                if not test_has_failed:
                                    update_wrap['test_is_ok'] = True

    # - add  msg_html to update_wrap (this one triggers MASS_UpdateFromResponse in page studsubjcts
        update_wrap['msg_html'] = msg_html

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


    def create_msg_list(self, sel_department, sel_level, count_dict, requsr_auth, is_approve, is_test,  published_instance_filename):
        # PR2022-08-25 PR2023-01-15
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ----- create_msg_list -----')
            logger.debug('    count_dict: ' + str(count_dict))
            logger.debug('    is_test: ' + str(is_test))

        count = count_dict.get('count', 0)
        student_count = count_dict.get('student_count', 0)
        committed = count_dict.get('committed', 0)
        student_committed_count = count_dict.get('student_committed_count', 0)
        saved = count_dict.get('saved', 0)
        saved_error = count_dict.get('saved_error', 0)
        student_saved_count = count_dict.get('student_saved_count', 0)
        student_saved_error_count = count_dict.get('student_saved_error_count', 0)
        already_published = count_dict.get('already_published', 0)

        all_published = count and already_published == count

        auth_missing = count_dict.get('auth_missing', 0)
        already_approved = count_dict.get('already_approved', 0)
        double_approved = count_dict.get('double_approved', 0)

        studsubj_tobedeleted = count_dict.get('studsubj_tobedeleted', 0)

        student_composition_error_count = count_dict.get('student_composition_error_count', 0)

        if logging_on:
            logger.debug('.....count: ' + str(count))
            logger.debug('.....committed: ' + str(committed))
            logger.debug('.....already_published: ' + str(already_published))
            logger.debug('.....auth_missing: ' + str(auth_missing))
            logger.debug('.....already_approved: ' + str(already_approved))
            logger.debug('.....double_approved: ' + str(double_approved))
            logger.debug('.....double_approved: ' + str(double_approved))
            logger.debug('.....student_composition_error_count: ' + str(student_composition_error_count))

        show_msg_first_approve_by_pres_secr = False

        if is_test:
            if is_approve:
                class_str = 'border_bg_valid' if committed else 'border_bg_invalid'
            else:
                if all_published:
                    class_str = 'border_bg_valid'
                elif student_composition_error_count:
                    class_str = 'border_bg_invalid'
                elif auth_missing or double_approved:
                    class_str = 'border_bg_invalid'
                elif committed:
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
        if logging_on:
            logger.debug('    class_str: ' + str(class_str))

        form_txt = exform = gettext('Compensation correctors')
        subjects_txt = '---'
        level_html = ''
        if sel_level:
            if sel_department.level_req and sel_level.abbrev:
                level_html = '<br>' + str(_('The selection contains only candidates of the learning path: %(lvl_abbrev)s.') % {'lvl_abbrev': sel_level.abbrev})

        tobedeleted_html = ''
        #if studsubj_tobedeleted:
        #    tobedeleted_html = ' ' + str(_('%(subj)s marked to be deleted.') % {'subj': get_subjects_are_text(examperiod, studsubj_tobedeleted)})

# - create first line with 'The selection contains 4 candidates with 39 subjects'
        msg_list = ["<div class='p-2 ", class_str, "'>"]
        #if is_test:
            #msg_list.append(''.join(( "<p class='pb-2'>",
            #            str(_("The selection contains %(stud)s with %(subj)s.") %
            #                {'stud': get_student_count_text(student_count), 'subj': get_subject_count_text(examperiod, count)}), ' ',
            #                tobedeleted_html,
            #                level_html,
            #            '</p>')))

# if students with errors in compositiosn: skip other msg
        try:

############## is_approve  #########################
            if is_approve:

    #++++++++++++++++ is_test +++++++++++++++++++++++++
                if is_test:

        # - if any subjects skipped: create lines 'The following subjects will be skipped' plus the reason
                    if committed == count:
                        msg_list.append("<p class='pb-0'>" + str(_("All %(cpt)s will be approved.") % {'cpt': subjects_txt}) + ':</p><ul>')
                    else:
                        willbe_or_are_txt = pgettext_lazy('plural', 'will be') if is_test else _('are')
                        msg_list.append("<p class='pb-0'>" + str(_("The following %(cpt)s %(willbe)s skipped")
                                                                 % {'cpt': subjects_txt, 'willbe': willbe_or_are_txt}) + \
                                        ":</p><ul class='my-0'>")
                        if already_published:
                            #msg_list.append('<li>' + str(_("%(val)s already submitted") %
                            #                             {'val': get_subjects_are_text(examperiod, already_published)}) + ';</li>')

                            if logging_on:
                                logger.debug('    already_published: ' + str(already_published))

                        if auth_missing:
                            #msg_list.append('<li>' + str(_("%(subj)s not fully approved") %
                            #                             {'subj': get_subjects_are_text(examperiod, auth_missing)}) + ';</li>')
                            show_msg_first_approve_by_pres_secr = True
                            if logging_on:
                                logger.debug('    auth_missing: ' + str(auth_missing))

                        if already_approved:
                            #msg_list.append('<li>' + get_subjects_are_text(examperiod, already_approved) + str(_(' already approved')) + ';</li>')
                            if logging_on:
                                logger.debug('    already_approved: ' + str(already_approved))

                        if double_approved:
                            other_function =  str(_('chairperson')) if requsr_auth == 'auth2' else str(_('secretary'))
                            caption = _('subject')
                            #msg_list.append(''.join(('<li>', get_subjects_are_text(examperiod, double_approved),
                            #                         str(_(' already approved by you as ')), other_function, '.<br>',
                            #                str(_("You cannot approve a %(cpt)s both as chairperson and as secretary.") % {'cpt': caption} ), '</li>')))
                            if logging_on:
                                logger.debug('    double_approved: ' + str(double_approved))

                        msg_list.append('</ul>')

            # - line with text how many subjects will be approved / submitted
                        msg_list.append("<p class='pb-2'>")
                        if not committed:
                            msg_str = _("No %(cpt)s will be approved.") % {'cpt': subjects_txt}
                            if logging_on:
                                logger.debug('    is_approve not committed: ' + str(not committed))

                        #else:
                            #student_count_txt = get_student_count_text(student_committed_count)
                            #subject_count_txt = get_subject_count_text(examperiod, committed)
                            #will_be_text = get_will_be_text(committed)
                            #msg_str = ' '.join((str(subject_count_txt), str(_('of')),  str(student_count_txt),
                            #                    str(will_be_text), str(_('approved.'))))
                            #if logging_on:
                            #    logger.debug('    is_approve msg_str: ' + str(not msg_str))

                        msg_list.append(str(msg_str))
                        msg_list.append('</p>')

                # - add line 'both prseident and secretary must first approve all subjects before you can submit the Ex form
                        if show_msg_first_approve_by_pres_secr:
                            msg_txt = ''.join(('<div>', str(_('The chairperson and the secretary must approve all %(cpt)s before you can submit the %(frm)s form.') % {'cpt': subjects_txt, 'frm': form_txt}   ), '</div>'))
                            msg_list.append(msg_txt)

    # ++++++++++++++++ not is_test +++++++++++++++++++++++++
                else:

                    # - line with text how many subjects have been approved
                    msg_list.append('<p>')

                    #student_count_txt = get_student_count_text(student_saved_count)
                    #subject_count_txt = get_subject_count_text(examperiod, saved)
                    #student_saved_error_count_txt = get_student_count_text(student_saved_error_count)
                    #subject_error_count_txt = get_subject_count_text(examperiod, saved_error)

                    #if logging_on:
                    #    logger.debug('    not is_text: ' + str(not student_count_txt))

                    # - line with text how many subjects have been approved / submitted
                    if not saved and not saved_error:
                        msg_str = str(_("No subjects have been approved."))
                    else:
                        if saved:
                            have_has_been_txt = _('has been') if saved == 1 else _('have been')
                            #msg_str = str(_("%(subj)s of %(stud)s %(havehasbeen)s approved.")
                            #              % {'subj': subject_count_txt, 'stud': student_count_txt,
                            #                 'havehasbeen': have_has_been_txt})
                        else:
                            msg_str = str(_("No subjects have been approved."))
                        if saved_error:
                            if msg_str:
                                msg_str += '<br>'
                            #could_txt = pgettext_lazy('singular', 'could') if saved_error == 1 else pgettext_lazy(
                            #    'plural', 'could')
                            #msg_str += str(
                            #    _("%(subj)s of %(stud)s %(could)s not be approved because an error occurred.")
                            #    % {'subj': subject_error_count_txt, 'stud': student_saved_error_count_txt,
                            #       'could': could_txt})

                    msg_list.append(str(msg_str))
                    msg_list.append('</p>')

############## is submit #########################
            else:
                if all_published :
                    msg_str = ''.join((
                        "<p class='pb-2'>",
                       str(_("All subjects are already submitted.")),
                       "</p>"
                    ))
                    msg_list.append(msg_str)

                elif auth_missing or double_approved:
                    if auth_missing + double_approved == 1:
                        subjects_txt = str(_('There is 1 subject'))
                    else:
                        subjects_txt = str(_("There are %(count)s subjects") % {'count': auth_missing + double_approved})

                    approved_txt = ''
                    if auth_missing:
                        if double_approved:
                            approved_txt = str(_("that are not fully approved")), str(_(" or ")), str(_("that are double approved by the same person."))
                        else:
                            if auth_missing == 1:
                                approved_txt = str(_("that is not fully approved"))
                            else:
                                approved_txt = str(_("that are not fully approved"))
                    else:
                        if double_approved:
                            if double_approved == 1:
                                approved_txt = str(_("that is double approved by the same person"))
                            else:
                                approved_txt = str(_("that are double approved by the same person"))

                    msg_txt = ''.join((subjects_txt, ', ', approved_txt, "."))
                    if logging_on:
                        logger.debug('   msg_txt: ' + str(msg_txt))

                    msg_str = ''.join((
                        "<p class='pb-2'>",
                       str(_("The %(frm)s form can not be submitted.") % {'frm': form_txt}),
                        "<br>",
                        msg_txt,
                       "</p><p class='pb-2'>",
                        str(_('The chairperson and the secretary must approve all subjects before you can submit the Ex1 form.')),
                       "</p>"
                    ))

                    if logging_on:
                        logger.debug('   msg_str: ' + str(msg_str))
                    msg_list.append(msg_str)

                else:

                    if is_test and committed < count:

                        if already_published or committed:
                            msg_list.append('<ul>')

                        #if already_published:
                        #    msg_list.append('<li>' + str(_("%(val)s already submitted") % {'val': get_subjects_are_text(examperiod, already_published)}) + ';</li>')

                        #if committed:
                        #    msg_list.append('<li>' + str(_("%(val)s submitted") % {'val': get_subjects_willbe_text(examperiod, committed)}) + ';</li>')

                        if already_published or committed:
                            msg_list.append('</ul>')

                    # - line with text how many subjects will be approved / submitted
                    msg_list.append('<p>')
                    if is_test:
                        if not committed:
                            msg_str = ''.join((
                                '<p>',
                                str(_("The %(frm)s form can not be submitted.") % {'frm': form_txt}),
                                "</p><p>",
                                str(_('The chairperson and the secretary must approve all subjects before you can submit the Ex1 form.')),
                                "</p>"
                            ))
                            msg_list.append(msg_str)
                            if logging_on:
                                logger.debug('   msg_str: ' + str(msg_str))
                            if logging_on:
                                logger.debug('   not is_approve not committed: ' + str(not not committed))
                        else:
                            """
                            msg_list.append('<p>')

                            student_count_txt = get_student_count_text(student_committed_count)
                            subject_count_txt = get_subject_count_text(examperiod, committed)
                            will_be_text = get_will_be_text(committed)
                            approve_txt = _('added to the %(frm)s form.') % {'frm': form_txt}
                            msg_str = ' '.join((str(subject_count_txt), str(_('of')), str(student_count_txt),
                                                str(will_be_text), str(approve_txt)))

                            if logging_on:
                                logger.debug('    not is_approve msg_str: ' + str(not msg_str))

                            msg_list.append('</p>')
                            """
                    else:

                        msg_list.append("<p class='pb-2'>")
                        #student_count_txt = get_student_count_text(student_saved_count)
                        #subject_count_txt = get_subject_count_text(examperiod, saved)
                        #student_saved_error_count_txt = get_student_count_text(student_saved_error_count)
                        #subject_error_count_txt = get_subject_count_text(examperiod, saved_error)

                        # - line with text how many subjects have been approved / submitted

                        not_str = '' if saved else str(_('not')) + ' '
                        msg_str = str(_("The %(frm)s form has %(not)s been submitted.") % {'frm': form_txt, 'not': not_str})
                        if saved:
                            #student_count_txt = get_student_count_text(student_saved_count)
                            #subject_count_txt = get_subject_count_text(examperiod, saved)
                            file_name = published_instance_filename if published_instance_filename else '---'
                            msg_str += ''.join(('<br>',
                                                # PR2023-02-12 dont give number of subjects, because all subjects are added to the Ex form
                                                #str(_("It contains %(subj)s of %(stud)s.") % {'stud': student_count_txt,
                                                #                                              'subj': subject_count_txt}),
                                                #'<br>',
                                                str(_("The %(frm)s form has been saved as '%(val)s'.") % {'frm': form_txt,
                                                                                                          'val': file_name}),
                                                '<br>', str(_("Go to the page 'Archive' to download the file."))
                                                ))

                        msg_list.append(str(msg_str))
                        msg_list.append('</p>')

            if logging_on:
                logger.debug('   msg_list: ' + str(msg_list))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))


#######################################

        msg_list.append('</div>')


        if logging_on:
            logger.debug('   msg_list: ' + str(msg_list))

        msg_html = ''.join(msg_list)

        if logging_on:
            logger.debug('    msg_html: ' + str(msg_html))

        return msg_html
# - end of create_msg_list


    def create_usercomp_form(self, published_instance, sel_examyear, sel_school, sel_department, sel_level,
                                    save_to_disk, request, user_lang):
        #PR2021-07-27 PR2021-08-14
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= create_usercomp_form ============= ')
            logger.debug('    sel_level: ' + str(sel_level))
            logger.debug('    save_to_disk: ' + str(save_to_disk))

# +++ create Ex_compensation form

        create_excomp_xlsx(
            published_instance=published_instance,
            examyear=sel_examyear,
            sel_school=sel_school,
            sel_department=sel_department,
            sel_level=sel_level,
            save_to_disk=save_to_disk,
            request=request,
            user_lang=user_lang)

        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= end of create_usercomp_form ============= ')
# --- end of create_usercomp_form

#################################################################################
@method_decorator([login_required], name='dispatch')
class UserCompensationApproveSingleView(View):  # PR2021-07-25 PR2023-02-18

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UserCompensationApproveSingleView ============= ')

# function sets auth and publish of studentsubject records of current department # PR2021-07-25
        update_wrap = {}
        msg_list = []

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = acc_prm.get_permit_list('page_studsubj', req_usr)
            if permit_list:
                has_permit = 'permit_approve_subject' in permit_list

        if not has_permit:
            msg_list.append(str(_("You don't have permission to perform this action.")))
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('    upload_dict: ' + str(upload_dict))

# ----- get selected examyear, school and department from usersettings
                # may_edit = False when:
                # - examyear, schoolbase, school, depbase or department is None
                # - country, examyear or school is locked
                # - not requsr_same_school,
                # - not sel_examyear.published,
                # not af.is_allowed_depbase_requsr or not af.is_allowed_depbase_school,

                sel_examyear, sel_school, sel_department, sel_level, may_editNIU, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                if err_list:
                    msg_list.extend(err_list)
                else:

# check if studsubj is allowed PR2023-02-12
                    userallowed_instance = acc_prm.get_userallowed_instance_from_request(request)
                    if logging_on:
                        logger.debug('    userallowed_instance: ' + str(userallowed_instance))

                    userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
                    if logging_on:
                        logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))

                    userallowed_schoolbase_dict, userallowed_depbases_pk_arr = acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(userallowed_sections_dict, sel_school.base_id)
                    if logging_on:
                        logger.debug('    userallowed_schoolbase_dict: ' + str(userallowed_schoolbase_dict))
                        logger.debug('    userallowed_depbases_pk_arr: ' + str(userallowed_depbases_pk_arr))

                    userallowed_depbase_dict, userallowed_lvlbase_pk_arr = acc_prm.get_userallowed_depbase_dict_lvlbases_pk_arr(userallowed_schoolbase_dict, sel_department.base_id)
                    if logging_on:
                        logger.debug('    userallowed_depbase_dict: ' + str(userallowed_depbase_dict))
                        logger.debug('    userallowed_lvlbase_pk_arr: ' + str(userallowed_lvlbase_pk_arr))

                    sel_lvlbase_pk = sel_level.base_id if sel_level else None
                    userallowed_subjbase_pk_list = acc_prm.get_userallowed_subjbase_arr(userallowed_depbase_dict, sel_lvlbase_pk)

                    userallowed_cluster_pk_list = acc_prm.get_userallowed_cluster_pk_list(userallowed_instance)
                    if logging_on:
                        logger.debug('    userallowed_subjbase_pk_list: ' + str(userallowed_subjbase_pk_list))
                        logger.debug('    userallowed_cluster_pk_list: ' + str(userallowed_cluster_pk_list))

# - get list of studentsubjects from upload_dict
                    studsubj_list = upload_dict.get('studsubj_list')
                    #  'studsubj_list': [{'student_pk': 7959, 'studsubj_pk': 64174, 'subj_auth1by': True}]}
                    if studsubj_list:
                        studsubj_rows = []
# -------------------------------------------------
# - loop through list of uploaded studentsubjects
                        for studsubj_dict in studsubj_list:
                            usercompensationt_pk = studsubj_dict.get('usercompensationt_pk')

                            append_dict = {}
                            error_dict = {}

# - get current student and studsubj
                            usercomp_instance = acc_mod.UserCompensation.objects.get_or_none(
                                id=usercompensationt_pk,
                                department=sel_department
                            )
                            if logging_on:
                                logger.debug('---------- ')
                                logger.debug('    usercomp_instance: ' + str(usercomp_instance))

                            if usercomp_instance and False:
# +++ update studsubj

                                err_list, err_fields = [], []
                                #update_studsubj(studsubj, studsubj_dict, si_dict,
                                #                sel_examyear, sel_school, sel_department,
                                #                err_list, err_fields, request)
                                if logging_on:
                                    logger.debug('>>>>> err_list: ' + str(err_list))
                                    logger.debug('>>>>> err_fields: ' + str(err_fields))

                                if err_list:
                                    msg_list.extend(err_list)
                                if err_fields:
                                    append_dict['err_fields'] = err_fields

                                # TODO check value of error_dict
                                # error_dict = {err_update: "Er is een fout opgetreden. De wijzigingen zijn niet opgeslagen."}
                                if error_dict:
                                    append_dict['error'] = error_dict
                                setting_dict = {
                                    'sel_examyear_pk': sel_school.examyear.pk,
                                    'sel_schoolbase_pk': sel_school.base_id,
                                    'sel_depbase_pk': sel_department.base_id
                                }

                                #if logging_on:
                                #    logger.debug('studsubj.pk: ' + str(studsubj.pk))
                                #studsubj_pk_list = [studsubj.pk] if studsubj.pk else None

                                #rows = create_studentsubject_rows(
                                #    sel_examyear=sel_examyear,
                                #    sel_schoolbase=sel_school.base if sel_school else None,
                                #    sel_depbase=sel_department.base if sel_department else None,
                                #    append_dict=append_dict,
                                #    request=request,
                                #    sel_lvlbase=sel_level.base if sel_level else None,
                                #    requsr_same_school=True,  # check for same_school is included in may_edit
                                #    student_pk=student.pk,
                                #    studsubj_pk_list=studsubj_pk_list
                               # )
                                #if rows:
                                #    studsubj_row = rows[0]
                                #    if studsubj_row:
                               #        studsubj_rows.append(studsubj_row)
# - end of loop
# -------------------------------------------------
                        if studsubj_rows:
                            update_wrap['updated_studsubj_approve_rows'] = studsubj_rows

        if logging_on:
            logger.debug('>>>>> msg_list: ')
            if msg_list:
                for msg in msg_list:
                    logger.debug('msg: ' + str(msg))
        if msg_list:
            messages = []
            msg_html = '<br>'.join(msg_list)
            messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UserCompensationApproveSingleView
##################################################################################

def create_corrector_rows(sel_examyear, sel_schoolbase, sel_depbase, sel_lvlbase, request):
    # --- create list of users with role = corrector and usergroup auth4
    # - filter on allowed school and allowed dep
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


def create_usercompensation_rows(sel_examyear, request):
    # --- create list of all correctors of this school, or  PR2023-02-19
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_usercompensation_rows ============= ')
        logger.debug('    request.user.role: ' + str(request.user.role))
        logger.debug('    request.user.schoolbase.pk: ' + str(request.user.schoolbase.pk))

    userapproval_rows = []
    if sel_examyear:
        try:

            sql_sub_list = ["SELECT uc.id,",
                        "CONCAT('usercomp_', uc.id::TEXT) AS mapid,",

                        "SUBSTRING(u.username, 7) AS username, u.last_name, u.is_active,",
                        "user_sb.code AS user_sb_code,",

                        "school.abbrev AS school_abbrev,",
                        "schoolbase.code AS sb_code,",
                        "depbase.code AS depbase_code,",
                        "lvlbase.code AS lvlbase_code,",
                        "exam.version AS exam_version,",
                        "exam.examperiod AS examperiod,",

                        "subj.name_nl AS subj_name_nl,",
                        "subjbase.code AS subjbase_code,",

                        "uc.amount AS uc_amount,",
                        "uc.meetings AS uc_meetings,",
                        "uc.correction_amount AS uc_corr_amount,",
                        "uc.correction_meetings AS uc_corr_meetings,",
                        "uc.compensation AS uc_compensation,",

                        "uc.meetingdate1 AS uc_meetingdate1,",
                        "uc.meetingdate2 AS uc_meetingdate2,",

                        "uc.auth1by_id AS uc_auth1by_id,",
                        "uc.auth2by_id AS uc_auth2by_id,",
                        "uc.published_id AS uc_published_id,",

                        "uc.notes AS uc_notes",
##########################

                        "FROM accounts_usercompensation AS uc",

                        "INNER JOIN accounts_user AS u ON (u.id = uc.user_id)",
                        "LEFT JOIN schools_schoolbase AS user_sb ON (user_sb.id = u.schoolbase_id)",

                        "INNER JOIN subjects_exam AS exam ON (exam.id = uc.exam_id)",

                        "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                        "INNER JOIN schools_school AS school ON (school.id = uc.school_id)",
                        "INNER JOIN schools_schoolbase AS schoolbase ON (schoolbase.id = school.base_id)",

                        "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
                        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                        "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",
                        "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                        ''.join(("WHERE school.examyear_id=", str(sel_examyear.pk), "::INT"))
                        ]

            sql_list = ["SELECT ",  # uc.id,",
                        "SUBSTRING(u.username, 7) AS username, u.last_name, u.is_active,",

                        "ual.examyear_id, ual.allowed_sections",

                        #"school.abbrev AS school_abbrev,",
                        #"schoolbase.code AS sb_code,",
                        #"depbase.code AS depbase_code,",
                       # "lvlbase.code AS lvlbase_code,",
                       # "exam.version AS exam_version,",
                       # "exam.examperiod AS examperiod,",

                      #  "subj.name_nl AS subj_name_nl,",
                      #  "subjbase.code AS subjbase_code,",

                       # "uc.amount AS uc_amount,",
                       # "uc.meetings AS uc_meetings,",
                       # "uc.correction_amount AS uc_corr_amount,",
                       # "uc.correction_meetings AS uc_corr_meetings,",
                      #  "uc.compensation AS uc_compensation,",

                    #    "uc.meetingdate1 AS uc_meetingdate1,",
                    #    "uc.meetingdate2 AS uc_meetingdate2,",

                   #     "uc.auth1by_id AS uc_auth1by_id,",
                    #    "uc.auth2by_id AS uc_auth2by_id,",
                   #     "uc.published_id AS uc_published_id,",

                    #    "uc.notes AS uc_notes",

                        "FROM accounts_user AS u",
                        "INNER JOIN accounts_userallowed AS ual ON (ual.user_id = u.id)",
                        "LEFT JOIN accounts_usercompensation AS uc ON (uc.user_id = u.id)",

                        ''.join(("WHERE ual.examyear_id=", str(sel_examyear.pk), "::INT")),
                        ''.join(("AND (POSITION('", c.USERGROUP_AUTH4_CORR, "' IN ual.usergroups) > 0)")),

                        ''.join(("AND u.is_active AND u.role=", str(c.ROLE_016_CORR), "::INT")),
                        ]

            #if request.user.role < c.ROLE_016_CORR:
            #    schoolbase_pk = request.user.schoolbase.pk if request.user.schoolbase.pk else 0
           #     sql_list.append(''.join(("AND u.schoolbase_id=", str(schoolbase_pk), "::INT")))

            sql = ' '.join(sql_list)

            if logging_on:
                if sql_list:
                    for sql_txt in sql_list:
                        logger.debug(' > ' + str(sql_txt))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                userapproval_rows = af.dictfetchall(cursor)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('  len  userapproval_rows: ' + str(len(userapproval_rows)))

    return userapproval_rows
# - end of create_usercompensation_rows

def create_usercomp_agg_rows(sel_examyear, request):
    # --- create list of all approvals per correctors per exam and calcultae total compensation PR2023-02-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_usercomp_agg_rows ============= ')

    usercompensation_agg_rows = []
    if request.user.country and request.user.schoolbase:
        if request.user.role >= c.ROLE_008_SCHOOL:

            # ATTENTION: sxm may use exams of ETE, therefore don't filter on examyear of exam,
            # this filter is ok: school.examyear_id

            try:
                requsr_country_pk = request.user.country.pk
                # sql_moduser = "SELECT mod_au.id, SUBSTRING(mod_au.username, 7) AS modby_username FROM accounts_user AS mod_au"
                sql_list = ["SELECT u.id AS u_id, exam.id AS exam_id,",

                            "CONCAT('user_exam_', u.id::TEXT, '_',  exam.id::TEXT) AS mapid,",

                            "SUBSTRING(u.username, 7) AS username, u.last_name, u.is_active,",
                            "user_sb.code AS user_sb_code,",

                            "depbase.code AS depbase_code,",
                            "lvlbase.code AS lvlbase_code,",
                            "exam.version AS exam_version,",
                            "exam.examperiod AS examperiod,",

                            "subj.name_nl AS subj_name_nl,",
                            "subjbase.code AS subjbase_code,",

                            "SUM(uc.amount) AS uc_amount, SUM(uc.meetings) AS uc_meetings,",
                            "SUM(uc.correction_amount) AS uc_corr_amount, SUM(uc.correction_meetings) AS uc_corr_meetings",

                            "FROM accounts_usercompensation AS uc",

                            "INNER JOIN accounts_user AS u ON (u.id = uc.user_id)",
                            "LEFT JOIN schools_schoolbase AS user_sb ON (user_sb.id = u.schoolbase_id)",

                            "INNER JOIN subjects_exam AS exam ON (exam.id = uc.exam_id)",
                            "INNER JOIN schools_school AS school ON (school.id = uc.school_id)",

                            "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                            "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
                            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)"

                            "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",
                            "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)"

                            "WHERE school.examyear_id=" + str(sel_examyear.pk) + "::INT",

                            # for testimg only: "AND u.last_name ILIKE '%%jeska%%'"
                            ]

                sql_list.append("GROUP BY u.id, u.username, u.last_name, u.is_active, user_sb.code, exam.id,")
                sql_list.append(
                    "exam.version, exam.examperiod, depbase.code, lvlbase.code, subj.name_nl, subjbase.code")

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
                            amount_sum=row.get('amount_sum') or 0,
                            meetings_sum=row.get('meetings_sum') or 0,
                            corr_amount_sum=row.get('corr_amount_sum') or 0,
                            corr_meetings_sum=row.get('corr_meetings_sum') or 0
                        )
                        row['compensation'] = compensation

                        if logging_on:
                            logger.debug('   row: ' + str(row))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('   len usercompensation_agg_rows: ' + str(len(usercompensation_agg_rows)))

    return usercompensation_agg_rows
# - end of create_usercomp_agg_rows


####################################################
def calc_compensation(amount_sum, meetings_sum, corr_amount_sum, corr_meetings_sum):
    # calculate compensation PR2023-02-25
    # values, to be stored in examyear_settings
    first_approval_amount = 2500  # in cents
    other_approval_amount = 1000  # in cents
    meeting_amount = 3000  # in cents
    max_meetings = 2

    total_amount = amount_sum + corr_amount_sum
    total_meetings = meetings_sum + corr_meetings_sum
    if total_meetings > max_meetings:
        total_meetings = max_meetings

    compensation = 0
    if total_amount >= 1:
        compensation = first_approval_amount + (other_approval_amount * (total_amount - 1))
    if total_meetings:
        compensation += meeting_amount * total_meetings

    return compensation


def update_usercompensation(sel_examyear, request):
    # --- create list of all correctors,pprovals and return dict with key (eser_pk, exam_pk, school_pk) and count PR2023-02-24
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== update_usercompensation ============= ')

    # ++++++++++++++++++++++++++++++++++++++
    def get_approval_count_dict():
        # --- create list of all grades, that are approved by correctors
        # return dict with key (user_pk, exam_pk, school_pk) and value = count PR2023-02-24
        # NOTE: grades that are approved by corrector, but have no exam, are NOT included!
        # NOTE: sxm may use exams of ETE, therefore don't filter on examyear of exam,
        #       this filter is ok: grd.studsubj.stud.school.examyear_id

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
            # "AND (POSITION('" + c.USERGROUP_AUTH4_CORR + "' IN ual.usergroups) > 0)",

            # include approval of deleted students and subjects, so dont add:
            #   "AND NOT stud.deleted AND NOT studsubj.deleted AND NOT grd.deleted",
        ]

        if request.user.role < c.ROLE_016_CORR:
            schoolbase_pk = request.user.schoolbase.pk if request.user.schoolbase.pk else 0
            sql_list.append(''.join(('AND u.schoolbase_id=', str(schoolbase_pk), '::INT')))

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
        # get rows from usercompensation, create dict with key (user_pk, exam_pk, school_pk) and value = tuple (uc.amount, uc.id) PR2023-02-24

        # ATTENTION: sxm may use exams of ETE, therefore don't filter on examyear of exam,
        # this filter is ok: school.examyear_id

        usercompensation_dict = {}
        sql_list = [
            "SELECT uc.user_id AS user_id, uc.exam_id AS exam_id, uc.school_id AS school_id,",
            "uc.id, uc.amount, uc.meetings, uc.correction_amount, uc.correction_meetings",

            "FROM accounts_usercompensation AS uc",
            "INNER JOIN schools_school AS school ON (school.id = uc.school_id)",

            "WHERE school.examyear_id=" + str(sel_examyear.pk) + "::INT",
        ]

        if request.user.role < c.ROLE_016_CORR:
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

        return usercompensation_dict
    # - end of get_usercompensation

    def create_tobe_lists():
        tobe_updated_list, tobe_added_list = [], []

 # +++++ loop through approval_count_dict +++++
        if approval_count_dict:
            for key_tuple, count_int in approval_count_dict.items():

                # check if recrd already exists in usercompensation_dict:
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
                first_approval_amount = 2500  # in cents
                other_approval_amount = 1000  # in cents
                meeting_amount = 3000
                max_meetings = 2

                # - get dict with approval_count and dict with usercompensations
                approval_count_dict = get_approval_count_dict()
                if logging_on:
                    logger.debug('    len approval_count_dict: ' + str(len(approval_count_dict)))
                usercompensation_dict = get_usercompensation_dict()
                if logging_on:
                    logger.debug('    len usercompensation_dict: ' + str(len(usercompensation_dict)))

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
def create_excomp_xlsx(published_instance, examyear, sel_school, sel_department, sel_level,
                    save_to_disk, request, user_lang):  # PR2021-02-13 PR2021-08-14
    # called by StudsubjDownloadEx4View
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_excomp_xlsx -----')

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
    ex4_rows_dict = {}
    #ex4_rows_dict = create_ex1_ex4_rows_dict(
    #    examyear=examyear,
    #    sel_school=sel_school,
    #    sel_department=sel_department,
    #    sel_level=sel_level,
    #    save_to_disk=save_to_disk,
    #    examperiod=examperiod,
    #    prefix=prefix,
    #    published_instance=published_instance
    #)

    #if logging_on:
    #    logger.debug('ex4_rows_dict: ' + str(ex4_rows_dict))


    response = None

    # - get text from examyearsetting
    settings = {}  # awpr_lib.get_library(examyear, ['exform', 'ex4'])

    if settings and ex4_rows_dict:

        # PR2021-07-28 changed to file_dir = 'published/'
        # this one gives path: awpmedia / awpmedia / media / private / published
        # PR2021-08-06 create different folders for country and examyear
        # this one gives path: awpmedia / awpmedia / media / private / cur / 2022 / published
        # published_instance is None when downloading preliminary Ex1 form

        examyear_str = str(examyear.code)

        file_path = None
        if published_instance:

# ---  create file_path
            # PR2021-08-07 changed to file_dir = 'country/examyear/published/'
            # this one gives path:awpmedia/awpmedia/media/cur/2022/published
            requsr_school = sch_mod.School.objects.get_or_none(
                base=request.user.schoolbase,
                examyear=examyear
            )
            requsr_schoolcode = requsr_school.base.code if requsr_school.base.code else '---'
            country_abbrev = examyear.country.abbrev.lower()
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
        title = ' '.join( ('Ex4', str(examyear), sel_school.base.code, today_dte.isoformat() ) )
        file_name = title + ".xlsx"
        worksheet_name = str(_('Ex4'))

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
        if logging_on:
            logger.debug('output: ' + str(output))
            logger.debug('book: ' + str(book))
            logger.debug('sheet: ' + str(sheet))

# --- create format of Ex4 sheet
        ex4_formats = {}  # create_ex1_ex4_format_dict(book, sheet, sel_school, sel_department, subject_pk_list, subject_code_list)
        field_width = ex4_formats.get('field_width')
        bold_format = ex4_formats.get('bold_format')
        bold_blue = ex4_formats.get('bold_blue')
        normal_blue = ex4_formats.get('normal_blue')
        th_merge_bold = ex4_formats.get('th_merge_bold')
        th_merge_normal = ex4_formats.get('th_merge_normal')
        th_exists = ex4_formats.get('th_exists')
        th_prelim  = ex4_formats.get('th_prelim')
        totalrow_merge = ex4_formats.get('totalrow_merge')
        col_count = len(ex4_formats['field_width'])
        first_subject_column =  ex4_formats.get('first_subject_column', 0)
        th_align_center = ex4_formats.get('th_align_center')

# --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

        """
        'Regel 0:   MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT
        'Regel 1:   Lijst van kandidaten voor het herexamen.
        'Regel 2:   (Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54).
        'Regel 3:   Tevens lijst van kandidaten, die om een geldige reden verhinderd waren het examen te voltooien.
        'Regel 4:   Direct na elke uitslag inzenden naar de Onderwijs Inspectie en digitaal naar het ETE
        'Regel 5:   
        'Regel 6:   EINDEXAMEN H.A.V.O. in het examenjaar 2021
        'Regel 7:   School:
        'Regel 8:
        'Regel 9:  "Examen Nr"
        """
# --- title row
        # was: sheet.write(0, 0, str(_('Report')) + ':', bold)
        title_str =  settings['ex4_title']
        sheet.write(0, 0, settings['minond'], bold_format)
        sheet.write(1, 0, title_str, bold_format)

        key_str = 'ex4_lex_article' if sel_school.islexschool else 'ex4_eex_article'
        sheet.write(2, 0, settings[key_str], bold_format)

        sheet.write(3, 0, settings['ex4_tevens_lijst'], bold_format)

        key_str = 'ex4_lex_submit' if sel_school.islexschool else 'ex4_eex_submit'
        sheet.write(4, 0, settings[key_str], bold_format)

        lb_ex_key = 'lex' if sel_school.islexschool else 'eex'
        lb_ex_key_str = ' '.join((  settings[lb_ex_key], sel_department.abbrev, settings['in_examyear'], examyear_str))

        sheet.write(6, 0, lb_ex_key_str, bold_format)
        lb_school_key = 'school' if sel_school.islexschool else 'school'
        sheet.write(7, 0, settings[lb_school_key], bold_format)
        sheet.write(7, 2, sel_school.name, bold_blue)

# - put Ex4 in right upper corner
        #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        sheet.merge_range(0, col_count - 5, 1, col_count -1, 'EX.4', th_merge_bold)

        row_index = 9
        if not save_to_disk:
            prelim_txt = 'VOORLOPIG Ex4 FORMULIER'

            sheet.merge_range(row_index, 0, row_index, col_count - 1, prelim_txt, th_prelim)
            row_index += 1

        #if has_published_ex1_rows(examyear, sel_school, sel_department):
        #    exists_txt = str(_('Attention: an Ex1 form has already been submitted. The subjects in that form are not included in this form.'))
        #    sheet.merge_range(row_index, 0, row_index, col_count - 1, exists_txt, th_exists)
        #    row_index += 1

# ---  table header row
        #for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        #    sheet.write(row_index, i, ex4_formats['field_captions'][i], ex4_formats['header_formats'][i])

# ++++++++++++++++++++++++++++
# iterate through levels, if more than 1 exist

        for key, level_dict in ex4_rows_dict.items():
            # skip ex4_rows_dict_totals
            if isinstance(key, int):
                # in subject column 'field_name' is subject_id
                lvl_name = level_dict.get('lvl_name')
                stud_list = level_dict.get('stud_list', [])
                lvl_totals = level_dict.get('total')

# ---  level header row
                row_index += 2
                #sheet.merge_range(row_index, 0, row_index, col_count - 1, lvl_name, th_level)    first_subject_column = col_count

                for i, field_caption in enumerate(ex4_formats['field_captions']):
                     sheet.write(row_index, i, field_caption, ex4_formats['header_formats'][i])

                if len(stud_list):
                    for row in stud_list:

# ---  student rows
                        # row: {'idnr': '2004101103', 'exnr': '21024', 'name': 'Balentien, Rayviendall',
                        # 'lvl': 'PBL', 'sct': 'tech', 'class': '4BH', 'subj': [1047, 1048, 1049, 1050, 1051, 1052, 1055, 1056, 1060, 1070]}
                        row_index += 1
                        for i, field_name in enumerate(ex4_formats['field_names']):
                            exc_format = ex4_formats['row_formats'][i]
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
                                #    exc_format = ex4_formats['row_align_center_red']
                            else:
                                value = row.get(field_name, '')
                            sheet.write(row_index, i, value, exc_format)

# ---  level subtotal row
                # skip subtotal row in Havo/vwo,
                if sel_department.level_req:
                    row_index += 1
                    for i, field_name in enumerate(ex4_formats['field_names']):
                        value = ''
                        if field_name == 'exnr':
                            #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                            sheet.merge_range(row_index, 0, row_index, first_subject_column -1, 'TOTAAL ' + lvl_name, totalrow_merge)
                        else:
                            if isinstance(field_name, int):
                                if field_name in lvl_totals:
                                    value = lvl_totals.get(field_name)
                            sheet.write(row_index, i, value, ex4_formats['totalrow_formats'][i])
                            # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')

# end of iterate through levels,
# ++++++++++++++++++++++++++++

        total_dict = ex4_rows_dict.get('total') or {}

# ---  table total row
        row_index += 1
        if sel_department.level_req:
            row_index += 1
        for i, field_name in enumerate(ex4_formats['field_names']):
            #logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
            value = ''
            if field_name == 'exnr':
                #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                sheet.merge_range(row_index, 0, row_index, first_subject_column -1, 'TOTAAL', totalrow_merge)
            else:
                if isinstance(field_name, int):
                    if field_name in total_dict:
                        value = total_dict.get(field_name)
                sheet.write(row_index, i, value, ex4_formats['totalrow_formats'][i])
                # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')

# ---  table footer row
        row_index += 1
        for i, field_name in enumerate(ex4_formats['field_names']):
            if i == 0:
                sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', totalrow_merge)
            else:
                sheet.write(row_index, i, ex4_formats['field_captions'][i], ex4_formats['header_formats'][i])

# table 'verhinderd
        row_index += 2
        verhinderd_txt = ' '.join((settings['ex4_verhinderd_header01'], '\n', settings['ex4_verhinderd_header02']))
        sheet.merge_range(row_index, 0, row_index + 1, col_count -1, verhinderd_txt, th_merge_normal)
        row_index += 2
        sheet.write(row_index, 0, ex4_formats['field_captions'][0], th_merge_normal)
        sheet.merge_range(row_index, 1, row_index, first_subject_column -1, settings['ex4_verhinderd_header03'], th_merge_normal)

        for i in range(first_subject_column, col_count):
            sheet.write(row_index, i, '', th_merge_normal)

        for x in range(0, 5):
            row_index += 1
            sheet.write(row_index, 0, '', th_merge_normal)
            sheet.merge_range(row_index, 1, row_index, first_subject_column - 1, '', th_merge_normal)

            for i in range(first_subject_column, col_count):
                sheet.write(row_index, i, '', th_merge_normal)

# ---  footnote row
        row_index += 2
        first_footnote_row = row_index
        for i in range(1, 9):
            if sel_school.islexschool and 'lex_footnote0' + str(i) in settings:
                key = 'lex_footnote0' + str(i)
            else:
                key = 'footnote0' + str(i)
            if key in settings:
                value = settings.get(key)
                if value:
                    sheet.write(row_index + i - 1, 0, value, bold_format)

# ---  digitally signed by
        # PR2022-05-31 also show signatures on preliminary Ex4 form
        auth_row = first_footnote_row
        if save_to_disk or True:
            sheet.write(auth_row, first_subject_column, str(_('Digitally signed by')) + ':')
            auth_row += 2
    # - Chairperson
            sheet.write(auth_row, first_subject_column, str(_('Chairperson')) + ':')
            auth1_list = ex4_rows_dict.get('auth1')
            if auth1_list:
                for auth1_pk in auth1_list:
                    auth1 = acc_mod.User.objects.get_or_none(pk=auth1_pk)
                    if auth1:
                        sheet.write(auth_row, first_subject_column + 4, auth1.last_name, normal_blue)
                        auth_row += 1
            else:
                auth_row += 1
            auth_row += 1
    # - Secretary
            sheet.write(auth_row, first_subject_column, str(_('Secretary')) + ':')
            auth2_list = ex4_rows_dict.get('auth2')
            if auth2_list:
                for auth2_pk in auth2_list:
                    auth2 = acc_mod.User.objects.get_or_none(pk=auth2_pk)
                    if auth2:
                        sheet.write(auth_row, first_subject_column + 4, auth2.last_name, normal_blue)
                        auth_row += 1
            else:
                auth_row += 1

            auth_row += 1

    # -  place, date
        sheet.write(auth_row, first_subject_column, 'Plaats:')
        sheet.write(auth_row, first_subject_column + 4, str(sel_school.examyear.country.name),
                    normal_blue)
        sheet.write(auth_row, first_subject_column + 8, 'Datum:')
        sheet.write(auth_row, first_subject_column + 11, today_formatted, normal_blue)

        book.close()

# +++ save file to disk
        if save_to_disk:
            excel_file = File(temp_file)

            published_instance.file.save(file_path, excel_file)

            # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
            published_instance.save(request=request)

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
    return response
# --- end of create_excomp_xlsx


def approve_usercomp(usercomp_row, requsr_auth, is_test, is_reset, count_dict, request):
    # PR2021-07-26 PR2022-05-30 PR2022-12-30 PR2023-02-12
    # auth_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
    #  prefix = 'reex3_'  'reex_'  'subj_'

    # PR2022-12-30 instead of updating each studsubj instance separately, create list of tobesaved studsubj_pk
    # list is created outside this function, when is_saved = True

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- approve_usercomp -----')
        logger.debug('    requsr_auth:  ' + str(requsr_auth))
        logger.debug('    is_reset:     ' + str(is_reset))
        logger.debug('    usercomp_row:     ' + str(usercomp_row))

    is_committed = False
    is_saved = False

    if usercomp_row:
        req_user = request.user

# - skip when this usercomp_row is already published
        published = True if usercomp_row.get('published_id') else False
        if logging_on:
            logger.debug('    published:    ' + str(published))

        if published:
            af.add_one_to_count_dict(count_dict, 'already_published')
        else:
            #requsr_authby_field = prefix + requsr_auth + 'by'
            requsr_authby_field = requsr_auth + 'by_id'

# - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved

            auth1by_id = usercomp_row.get('auth1by_id')
            auth2by_id = usercomp_row.get('auth2by_id')
            if logging_on:
                logger.debug('    auth1by_id:      ' + str(auth1by_id))
                logger.debug('    auth2by_id:      ' + str(auth2by_id))

            save_changes = False

# - remove authby when is_reset
            if is_reset:
                af.add_one_to_count_dict(count_dict, 'reset')
                save_changes = True
            else:

# - skip if this usercomp_row is already approved
                requsr_authby_value = auth1by_id if requsr_auth == 'auth1' else auth2by_id if requsr_auth == 'auth2' else None
                requsr_authby_field_already_approved = True if requsr_authby_value else False
                if logging_on:
                    logger.debug('    requsr_authby_field_already_approved: ' + str(requsr_authby_field_already_approved))

                if requsr_authby_field_already_approved:
                    af.add_one_to_count_dict(count_dict, 'already_approved')
                else:

# - skip if this author (like 'chairperson') has already approved this usercomp_row
        # under a different permit (like 'secretary' or 'corrector')

                    if logging_on:
                        logger.debug('    > requsr_auth: ' + str(requsr_auth))
                        logger.debug('    > req_user:    ' + str(req_user))
                        logger.debug('    > auth1by_id:     ' + str(auth1by_id))
                        logger.debug('    > auth2by_id:     ' + str(auth2by_id))

                    double_approved = False
                    if requsr_auth == 'auth1':
                        double_approved = True if auth2by_id and auth2by_id == req_user.pk else False
                    elif requsr_auth == 'auth2':
                        double_approved = True if auth1by_id and auth1by_id == req_user.pk else False

                    if logging_on:
                        logger.debug('    double_approved: ' + str(double_approved))

                    if double_approved:
                        af.add_one_to_count_dict(count_dict, 'double_approved')
                    else:
                        save_changes = True
                        if logging_on:
                            logger.debug('    save_changes: ' + str(save_changes))

# - set value of requsr_authby_field
            if save_changes:
                if is_test:
                    af.add_one_to_count_dict(count_dict, 'committed')
                    is_committed = True
                else:

# - save changes
                    af.add_one_to_count_dict(count_dict, 'saved')
                    is_saved = True

    return is_committed, is_saved
# - end of approve_usercomp


def submit_usercom(usercomp_row, is_test, count_dict):
    # PR2021-01-21 PR2021-07-27 PR2022-05-30 PR2022-12-30 PR2023-02-12

    # PR2022-12-30 instead of updating each studsubj instance separately, create list of tobesaved studsubj_pk
    # list is created outside this function, when is_saved = True

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- submit_usercom -----')

    is_committed = False
    is_saved = False

    if usercomp_row:

# - check if this studsubj is already published
        #published = getattr(studsubj, prefix + 'published')
        published = True if usercomp_row.get('published_id') else False
        if logging_on:
            logger.debug('     subj_published: ' + str(published))
        if published:
            af.add_one_to_count_dict(count_dict, 'already_published')
        else:

# - check if this studsubj / examtype is approved by all auth
            #auth1by = getattr(studsubj, prefix + 'auth1by')
            #auth2by = getattr(studsubj, prefix + 'auth2by')

            auth1by_id = usercomp_row.get('auth1by_id')
            auth2by_id = usercomp_row.get('auth2by_id')
            auth_missing = auth1by_id is None or auth2by_id is None
            if logging_on:
                logger.debug('    auth1by_id:      ' + str(auth1by_id))
                logger.debug('    auth2by_id:      ' + str(auth2by_id))
                logger.debug('    auth_missing: ' + str(auth_missing))

            if auth_missing:
                af.add_one_to_count_dict(count_dict, 'auth_missing')
            else:
# - check if all auth are different
                double_approved = auth1by_id == auth2by_id
                if logging_on:
                    logger.debug('    double_approved: ' + str(double_approved))

                if double_approved and not auth_missing:
                    af.add_one_to_count_dict(count_dict, 'double_approved')
                else:
# - set value of published_instance and exatmtype_status field
                    if is_test:
                        af.add_one_to_count_dict(count_dict, 'committed')
                        is_committed = True
                    else:
                        af.add_one_to_count_dict(count_dict, 'saved')
                        is_saved = True

    return is_committed, is_saved
# - end of submit_usercom


def create_published_usercomp_instance(sel_school, sel_department, sel_level, now_arr, request):
    # PR2023-03-23
    logging_on = s.LOGGING_ON
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
    minute_str = ("00" +str( now_arr[4]))[-2:]
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
        #sel_examtype = '-'
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

