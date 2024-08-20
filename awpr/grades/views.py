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
from django.utils.translation import activate, gettext, pgettext, gettext_lazy as _
from django.views.generic import View

from reportlab.pdfgen.canvas import Canvas

from accounts import views as acc_view
from accounts import permits as acc_prm

from awpr import constants as c
from awpr import settings as s
from awpr import menus as awpr_menu
from awpr import functions as af
from awpr import excel as awpr_excel
from awpr import library as awpr_lib
from  awpr import logs as awpr_log

from schools import models as sch_mod
from schools import views as sch_view
from students import models as stud_mod
from students import functions as stud_fnc
from subjects import models as subj_mod
from subjects import views as subj_vw
from grades import validators as grad_val
from grades import calc_score as calc_score
from grades import calc_finalgrade as calc_final
from grades import calc_results as calc_res
from grades import exfiles as grade_exfiles

import json # PR2018-12-03
# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy


# ========  GRADES SECRET EXAMS =====================================
@method_decorator([login_required], name='dispatch')
class SecretExamListView(View):  # PR2023-04-03

    def get(self, request):

# - set headerbar parameters
        page = 'page_secretexam'
        # PR2024-06-14 moved to get_headerbar_param
        # param = {'display_school': False, 'display_department': True}
        headerbar_param = awpr_menu.get_headerbar_param(request, page)

        return render(request, 'secretexam.html', headerbar_param)

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
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
            acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

# - get selected examperiod, examtype, subject_pk from usersettings
            sel_examperiod, sel_examtype, sel_subject_pk = acc_view.get_selected_experiod_extype_subject_from_usersetting(request)

            if logging_on:
                logger.debug('sel_examperiod: ' + str(sel_examperiod))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))

            grade_note_icon_rows = create_grade_note_icon_rows(
                sel_examyear_pk=sel_examyear.pk if sel_examyear else None,
                sel_schoolbase_pk=sel_school.base_id if sel_school else None,
                sel_depbase_pk=sel_department.base_id if sel_department else None,
                sel_examperiod=sel_examperiod,
                studsubj_pk=None,
                request=request)
            if grade_note_icon_rows:
                download_wrap['grade_note_icon_rows'] = grade_note_icon_rows

            #grade_stat_icon_rows = create_grade_stat_icon_rows(
            #    sel_examyear_pk=sel_examyear.pk if sel_examyear else None,
            #    sel_schoolbase_pk=sel_school.base_id if sel_school else None,
           #     sel_depbase_pk=sel_department.base_id if sel_department else None,
            #    sel_examperiod=sel_examperiod,
           #     request=request)

            #if grade_stat_icon_rows:
            #    download_wrap['grade_stat_icon_rows'] = grade_stat_icon_rows
        # - return update_wrap
        return HttpResponse(json.dumps(download_wrap, cls=af.LazyEncoder))

# - end of GradeDownloadGradeIconsView


########################################

@method_decorator([login_required], name='dispatch')
class GradeBlockView(View):  # PR2022-04-16 PR2023-04-08

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= GradeBlockView ============= ')

        # function blockes or unblocks grade by Inspectorate

        def update_grades(is_block, examtype, grade_pk_list):
            err_html = None
            updated_grade_rows = []
            try:
                # TODO add modified info after adding fields to grades
                modifiedby_pk_str = str(request.user.pk)
                modifiedat_str = str(timezone.now())

                # when grade is not yet submitted, do'nt set blocked = True but just remove approvals
                # was: blocked_value = "TRUE, " if is_block else "FALSE "
                if is_block:
                    blocked_value = ''.join(("CASE WHEN ", examtype, "_published_id=NULL THEN FALSE ELSE TRUE END, "))
                else:
                    blocked_value = "FALSE "  # no additional field, therefore no comma after FALSE

                blocked_filter = "NOT " if is_block else ""

                update_values = ''.join((
                    examtype, "_published_id=NULL, ",
                    examtype, "_auth1by_id=NULL, ",
                    examtype, "_auth2by_id=NULL, ",
                    examtype, "_auth3by_id=NULL, ",
                    examtype, "_auth4by_id=NULL "
                )) if is_block else ''

                # fields are 'se_blocked', 'sr_blocked', 'pe_blocked', ce'_blocked'
                # don't update modifiedby
                sql_list = ["UPDATE students_grade SET ", examtype, "_blocked=", blocked_value,
                    update_values,
                    # TODO add when fields are added to grade model
                    #"modifiedby_id=", modifiedby_pk_str, ", modifiedat='", modifiedat_str, "'",
                    "WHERE NOT tobedeleted AND NOT deleted ",
                    "AND ", blocked_filter, examtype, "_blocked ",
                    "AND id IN (SELECT UNNEST(ARRAY", str(grade_pk_list), "::INT[])) "
                    "RETURNING id;"
                ]
                sql = ''.join(sql_list)

                if logging_on:
                    for sql_txt in sql_list:
                        logger.debug('    > ' + str(sql_txt))

                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    if rows:
                        for row in rows:
                            updated_grade_rows.append(row[0])
                    if logging_on:
                        logger.debug('    updated_grade_rows rows: ' + str(updated_grade_rows))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                err_html = acc_prm.errhtml_error_occurred_with_border(e, _('This CVTE exam can not be deleted.'))

            return updated_grade_rows, err_html
########################



        update_wrap = {}

        #<PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school not locked, examyear is published and school is activated

        if request.user and request.user.country and request.user.schoolbase:
            req_usr = request.user

# -  get user_lang
            user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
            activate(user_lang)

            # TODO 2022-12-09 so far
            permit_list, requsr_usergroups_listNIU,  requsr_allowed_sections_dictNIU, requsr_allowed_clusters_arr = \
                acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, 'page_grade')

            # Not in use  > can be removed?? PR2022-12-11
            # allowed_dict = {}
            # dl.get_requsr_allowed(req_usr, allowed_dict)
            # if logging_on:
            #     logger.debug('permit_list: ' + str(permit_list))
            #     logger.debug('allowed_dict: ' + str(allowed_dict))
            #     # allowed_dict: {'requsr_allowed_clusters': [300]}

            has_permit = 'permit_block_grade' in permit_list
            if logging_on:
                logger.debug('has_permit: ' + str(has_permit))

            if has_permit:

    # - get upload_dict from request.POST
                upload_json = request.POST.get('upload', None)
                if upload_json:
                    upload_dict = json.loads(upload_json)

                    """
                    upload_dict{'mode': 'block', 'grade_pk': 22433, 'examtype': 'se'}
                    """

    # - get selected mode. Modes are 'block' 'unblock'
                    mode = upload_dict.get('mode')

    # - get grade_pk. It only has value when a single grade is approved
                    grade_pk_list = upload_dict.get('grade_pk_list')
                    examperiod = upload_dict.get('examperiod')
                    examtype = upload_dict.get('examtype')

                    if logging_on:
                        logger.debug('    upload_dict' + str(upload_dict))
                        logger.debug('    mode: ' + str(mode))
                        logger.debug('    grade_pk_list: ' + str(grade_pk_list))
                        logger.debug('    examperiod:   ' + str(examperiod))
                        logger.debug('    examtype: ' + str(examtype))

    # - get selected examyear, school and department from usersettings
                    # - get selected examyear, school and department from usersettings
                    sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                        acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                    if err_list:
                        update_wrap['messages'] = [{'class': "border_bg_invalid", 'header': str(_('Block grade')),
                                    'msg_html': '<br>'.join(err_list)}]
                    else:
                        is_block = mode == 'block'
                        updated_grade_pk_list, err_html = update_grades(is_block, examtype, grade_pk_list)

                        if updated_grade_pk_list:
                            updated_grade_rows = create_grade_rows(
                                sel_examyear=sel_examyear,
                                sel_schoolbase=sel_school.base if sel_school else None,
                                sel_depbase=sel_department.base if sel_department else None,
                                sel_lvlbase=None,
                                sel_examperiod=examperiod,
                                # PR2021-06-01 debug. Remove key 'note_status', otherwise it will erase not icon when refreshing this row
                                remove_note_status=True,
                                request=request,
                                append_dict={},
                                grade_pk_list=updated_grade_pk_list
                            )
                            if updated_grade_rows:
                                update_wrap['updated_grade_rows'] = updated_grade_rows

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of GradeBlockView


########################################

@method_decorator([login_required], name='dispatch')
class GradeApproveView(View):  # PR2021-01-19 PR2022-03-08 PR2023-02-02 PR2023-05-30

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= GradeApproveView ============= ')

# - function approves single or multiple scores / grades
        update_wrap = {}
        msg_html_list = []
        msg_single_update_list = []
        border_class = "border_bg_transparent"

        if request.user and request.user.country and request.user.schoolbase:
            req_usr = request.user

    # -  get user_lang
            user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
            activate(user_lang)

    # - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                page_name = upload_dict.get('page') or 'page_grade'
                sel_examtype = upload_dict.get('examtype')

                is_single_update = upload_dict.get('is_single_update') or False
                secret_exams_only = page_name == 'page_secretexam'

                if logging_on:
                    logger.debug('    upload_dict: ' + str(upload_dict))

                """
                upload_dict{'table': 'grade', 'mode': 'approve_save', 'mapid': 'grade_75597', 'grade_pk': 75597, 
                            'field': 'se_status', 'examperiod': 4, 'examtype': 'se', 'auth_index': 1}
                upload_dict{'table': 'grade', 'mode': 'approve_save', 'is_single_update': True, 'mapid': 'grade_69231', 
                            'grade_pk': 69231, 'field': 'ce_status', 'examperiod': 1, 'examtype': 'ce', 'auth_index': 4}
                upload_dict: {'table': 'grade', 'page': 'page_secretexam', 'mode': 'approve_save', 'is_single_update': True, 'mapid': 'grade_76891', 'grade_pk': 76891, 'field': 'ce_status', 'examperiod': 2, 'examtype': 'ce', 'auth_index': 2}
                """

    # -  get permit
                has_permit = acc_prm.get_permit_of_this_page(page_name, 'approve_grade', request)
                if logging_on:
                    logger.debug('    has_permit: ' + str(has_permit))

                if not has_permit:
                    border_class = "border_bg_invalid"
                    action_txt = _('to approve grades') if sel_examtype == 'se' else  _('to approve scores')
                    err_txt = acc_prm.err_txt_no_permit(action_txt)
                    if is_single_update:
                        msg_single_update_list.append(err_txt)
                    else:
                        msg_html_list.append(err_txt)
                else:

    # - get selected mode. Modes are 'approve_save', 'approve_reset', 'submit_test' 'submit_save', 'reset'
                    mode = upload_dict.get('mode')
                    is_reset = True if mode == 'approve_reset' else False
                    is_test = True if mode in ('approve_test', 'submit_test') else False

                    # TODO PR2023-04-10
                    #  Een goedkeuring kan alleen worden verwijderd door dezelfde gebruiker,
                    #  PR2024-05-30 and to be added: of door de vz of secr

    # - get grade_pk. It only has value when a single grade is approved
                    grade_pk = upload_dict.get('grade_pk')
                    field = upload_dict.get('field')

                    auth_index = upload_dict.get('auth_index')

                    if auth_index:
                        requsr_auth = 'auth' + str(auth_index)

    # - check if auth_index is in requsr_usergroup_list, to be on the safe side PR2022-04-20
                        requsr_usergroup_list = acc_prm.get_usergroup_list_from_user_instance(req_usr)
                        if logging_on:
                            logger.debug('    requsr_auth: ' + str(requsr_auth))
                            logger.debug('    requsr_usergroup_list: ' + str(requsr_usergroup_list))

                        if requsr_auth in requsr_usergroup_list:

                            # msg_err is made on client side. Here: just skip if user has no or multiple functions

        # - get auth_index (1 = Chairperson, 2 = Secretary, 3 = examiner, 4 = Corrector
                            # PR2021-03-27 auth_index is taken from requsr_usergroup_list, not from upload_dict
                            #  function may have changed if grade page is not refreshed in time)
                            #  was: auth_index = upload_dict.get('auth_index')
                            #  can't do it like this any more. User can be examiner and pres/secr at the same time. Get index from upload again

                            # back to upload_dict.get('auth_bool_at_index')
                            # 'auth_bool_at_index' not in use any more. Set or reset is determined by 'approve_save' or 'approve_reset'

                            if logging_on:
                                logger.debug('....upload_dict' + str(upload_dict))
                                logger.debug('    mode: ' + str(mode))
                                logger.debug('    auth_index: ' + str(auth_index))
                            """
                            upload_dict{'table': 'grade', 'mode': 'approve_save', 'mapid': 'grade_22432', 'field': 'se_status', 
                            'auth_index': 4, 'auth_bool_at_index': True, 'examtype': 'se', 'grade_pk': 22432}
                            """

        # - get selected examyear, school and department from usersettings
                            sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                            if err_list:
                                border_class = "border_bg_invalid"
                                err_list.append(gettext("You cannot approve grades."))
                                if is_single_update:
                                    msg_single_update_list.extend(err_list)
                                else:
                                    msg_html_list.extend(err_list)

                            else:

        # - get selected examperiod from usersetting
                                sel_examperiod, sel_lvlbase_pk, sel_subject_pk, sel_cluster_pk = None, None, None, None
                                selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                                if selected_pk_dict:
                                    sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
                                    # don't filter on lvl, subj, cluster when approving single grade
                                    if grade_pk is None:
                                        sel_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)
                                        sel_subject_pk = selected_pk_dict.get(c.KEY_SEL_SUBJECT_PK)
                                        sel_cluster_pk = selected_pk_dict.get(c.KEY_SEL_CLUSTER_PK)

        # - get selected examtype from upload_dict
                                # if examtype exists in upload_dict : get from upload_dict, get from usersettings otherwise
                                # sel_examtype may contain 'all'
                                # examtype = 'se', 'sr', 'pe', 'ce', 'reex','reex03', 'exem', 'all'
                                # examtype has no value when called bij MAG_Save > get then from usersetting

                                saved_examtype = selected_pk_dict.get(c.KEY_SEL_EXAMTYPE)
                                if sel_examtype and sel_examtype != saved_examtype:
                                    # save sel_examtype when changed
                                    selected_pk_dict[c.KEY_SEL_EXAMTYPE] = sel_examtype
                                    acc_view.set_usersetting_dict('selected_pk', selected_pk_dict, request)

        # replace examtype 'reex', 'reex03' with 'ce' (sel_examperiod determines if it is reex)
                                if sel_examtype in ('reex', 'reex03'):
                                    sel_examtype = 'ce'

                                is_score = 'ce' in sel_examtype

                                if logging_on:
                                    logger.debug('    sel_examtype:   ' + str(sel_examtype))
                                    logger.debug('    sel_examperiod: ' + str(sel_examperiod))
                                    logger.debug('    sel_subject_pk: ' + str(sel_subject_pk))
                                    logger.debug('    is_score: ' + str(is_score))

        # - get allowed filter > this is part of create_grade_approve_rows
                                if sel_examyear and sel_school and sel_department and sel_examperiod and sel_examtype:
                                    err_list = []
                                    if logging_on:
                                        logger.debug('    err_list: ' + str(err_list))
                                        logger.debug('    sel_examperiod: ' + str(sel_examperiod) + ' ' + str(type(sel_examperiod)))
                                        logger.debug('    sel_examtype: ' + str(sel_examtype) + ' ' + str(type(sel_examtype)))

        # give msg when corrector wants to approve exem or se, or when examiner wants to approve exem
                                    auth_txt, gradetype_txt = None, None
                                    if requsr_auth == c.USERGROUP_AUTH4_CORR:
                                        auth_txt = gettext('Second corrector').lower()
                                        if sel_examperiod == c.EXAMPERIOD_EXEMPTION:
                                            gradetype_txt = gettext('exemption grades')
                                        elif sel_examtype == 'se':
                                            gradetype_txt = gettext('school exam grades')

                                    elif requsr_auth == c.USERGROUP_AUTH3_EXAM:
                                        auth_txt = gettext('Examiner').lower()
                                        if sel_examperiod == c.EXAMPERIOD_EXEMPTION:
                                            gradetype_txt = gettext('exemption grades')

                                    if logging_on:
                                        logger.debug('    auth_txt: ' + str(auth_txt))
                                        logger.debug('    gradetype_txt: ' + str(gradetype_txt))
                                    if gradetype_txt is not None:
                                        err_list.append(
                                            gettext("As %(auth)s you don't have to approve %(gradetype)s.")
                                            % {'auth': auth_txt, 'gradetype': gradetype_txt}
                                        )
                                        border_class = 'border_bg_invalid'
                                        if is_single_update:
                                            msg_single_update_list.extend(err_list)
                                        else:
                                            msg_html_list.extend(err_list)

                                    else:
        # get_allowed_sections
                                        userallowed_instance = acc_prm.get_userallowed_instance(request.user, sel_examyear)
                                        userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
                                        userallowed_cluster_pk_list = acc_prm.get_userallowed_cluster_pk_list(userallowed_instance)

                                        if logging_on:
                                            logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))
                                            logger.debug('    userallowed_cluster_pk_list: ' + str(userallowed_cluster_pk_list))

                                        # PR2024-05-30 filter on examyear_pk added
                                        allowed_clusters_of_sel_school = acc_prm.get_allowed_clusters_of_sel_school(
                                            sel_schoolbase_pk = sel_school.base_id if sel_school else None,
                                            sel_examyear_pk=sel_school.examyear_id if sel_school else None,
                                            allowed_cluster_pk_list=userallowed_cluster_pk_list
                                        )
                                        if logging_on:
                                            logger.debug('    allowed_clusters_of_sel_school: ' + str(allowed_clusters_of_sel_school))

                                        # blank scores / grades are not included
                                        grade_approve_rows = create_grade_approve_rows(
                                            request=request,
                                            sel_examyear=sel_examyear,
                                            sel_school=sel_school,
                                            sel_department=sel_department,
                                            sel_level=sel_level,
                                            sel_examperiod=sel_examperiod,
                                            sel_examtype=sel_examtype,
                                            secret_exams_only=secret_exams_only,
                                            userallowed_sections_dict=userallowed_sections_dict,
                                            allowed_clusters_of_sel_school=allowed_clusters_of_sel_school,
                                            grade_pk=grade_pk
                                        )
                                        if logging_on:
                                            logger.debug(' >> len grade_approve_rows: ' + str(len(grade_approve_rows)))
                                            #for row in grade_approve_rows:
                                            #    logger.debug(' -- ' + str(row))
                                        """
                                        grade_approve_row: {'id': 69226, 'examperiod': 1, 'studsubj_id': 64296, 'cluster_id': None, 
                                        'has_exemption': False, 'secret_exam': False, 'subjbase_id': 167, 
                                        'lvlbase_id': None, 'depbase_id': 2, 'schoolbase_id': 13, 
                                        'auth1by_id': None, 'auth2by_id': None, 'auth3by_id': None, 'auth4by_id': None,
                                         'published_id': None, 'blocked': False, 'has_value': True, 
                                         'status': 0, 'stud_name': ' Chin-A-Lien, Paola Juliette Viana', 
                                         'subj_name': 'Engelse taal en literatuur', 
                                         'composition_error': False, 'studsubj_tobedeleted': False, 'studsubj_not_published': False}
                                        """

                                        count_dict = {} # used when approving multiple grades, to count grades

                                        msg_list = [] # used when approving single grade, to display message

                                        test_is_ok = False

# ++++++++++++++++++++++ loop through grade_approve_rows
                                        grade_rows_tobe_updated = [] # list of grdaepk that passed validation
                                        updated_grade_pk_list = []

                                        for grade_row in grade_approve_rows:
                                            if logging_on:
                                                 logger.debug('    grade_row: ' + str(grade_row))

                                            # PR2023-03-25 remove approval can only be done by the same auth or by the chairperson and secretary

                                            err_html = grad_val.validate_grade_approval_remove_allowed(is_reset, is_score, auth_index,
                                                                                   requsr_auth, grade_row, req_usr)
                                            if err_html:
                                                border_class = 'border_bg_invalid'
                                                if is_single_update:
                                                    msg_single_update_list.append(err_html)
                                                else:
                                                    msg_html_list.append(err_html)

                                            else:
                # +++ check if approving grade is allowed
                                                # use validate_grade_is_allowed when single grade is approved (in that case grade_pk has value)
                                                # checks if grade is in allowed_subjectbases etc
                                                if grade_pk:
                                                    is_allowed = grad_val.validate_grade_is_allowed(
                                                        request=request,
                                                        requsr_auth=requsr_auth,
                                                        userallowed_sections_dict=userallowed_sections_dict,
                                                        allowed_clusters_of_sel_school=allowed_clusters_of_sel_school,

                                                        schoolbase_pk=grade_row.get('schoolbase_id'),
                                                        depbase_pk=grade_row.get('depbase_id'),
                                                        lvlbase_pk=grade_row.get('lvlbase_id'),
                                                        subjbase_pk=grade_row.get('subjbase_id'),
                                                        cluster_pk=grade_row.get('cluster_id'),
                                                        studsubj_tobedeleted=grade_row.get('studsubj_tobedeleted'),
                                                        is_secret_exam=grade_row.get('secret_exam'),
                                                        is_reset=is_reset,
                                                        msg_list=msg_list,
                                                        is_approve=True, # only used for msg text
                                                        is_score=is_score # only used for msg text
                                                    )
                                                else:
                                                    is_allowed = grad_val.validate_grade_multiple_is_allowed(
                                                        request=request,
                                                        requsr_auth=requsr_auth,
                                                        allowed_clusters_of_sel_school=allowed_clusters_of_sel_school,
                                                        sel_examyear=sel_examyear,
                                                        schoolbase_pk=grade_row.get('schoolbase_id'),
                                                        depbase_pk=grade_row.get('depbase_id'),
                                                        lvlbase_pk=grade_row.get('lvlbase_id'),
                                                        subjbase_pk=grade_row.get('subjbase_id'),
                                                        cluster_pk=grade_row.get('cluster_id')
                                                    )
                                                if is_allowed:

                # +++ approvie grade, returns grade_rows_tobe_updated with grade_pk, new_auth_id, new_status_sum
                                                    get_grades_tobe_updated(
                                                        grade_row, grade_rows_tobe_updated, sel_examtype,
                                                        requsr_auth, auth_index, is_test, is_reset,
                                                        count_dict, request
                                                    )
                                                else:
                                                    if msg_list:
                                                        if grade_pk:
                                                            logger.debug('grade_row: ' + str(grade_row))
                                                            header_text = str(_('Approve score') if is_score else _('Approve grade'))
                                                            update_wrap['messages'] = [
                                                                {'class': "border_bg_invalid", 'header': header_text,
                                                                 'msg_html': '<br>'.join(msg_list)}]
                                                            # add grade_pk to updated_grade_pk_list, to return grade_row with error field
                                                            updated_grade_pk_list = [grade_pk]
                                                        else:
                                                            pass
# ++++++++++++++++++++++ end of loop through grade_approve_rows

                                        if logging_on:
                                            logger.debug('----- grade_rows_tobe_updated: ' + str(grade_rows_tobe_updated))
                                            # grade_rows_tobe_updated = [grade_pk, new_auth_id, new_status_sum]

                                        if not is_test and grade_rows_tobe_updated:
                                            err_html, updated_grade_pk_list = batch_approve_grade_rows(grade_rows_tobe_updated, sel_examtype, is_reset, requsr_auth, request)
                                            if err_html:
                                                border_class = 'border_bg_invalid'
                                                if is_single_update:
                                                    msg_single_update_list.append(err_html)
                                                else:
                                                    msg_html_list.append(err_html)

                                            else:
                                                test_is_ok = True
                                                # approve_msg_html needs a value to trigger response on client
                                                msg_html_list.append('ok')

                                        row_count = len(grade_approve_rows)
                                        if logging_on:
                                            logger.debug('row_count: ' + str(row_count))

                                        if not row_count:
                                            msg_html_list.append(''.join(("<p>",
                                                                    str(_("The selection contains %(val)s.")
                                                                    % {'val': get_grade_score_text(0, is_score)}), "</p>")))
                                        else:
                                            if logging_on:
                                                logger.debug('updated_grade_pk_list: ' + str(updated_grade_pk_list))
                                            if updated_grade_pk_list:

                                                append_dict = {}
                                                if msg_list:
                                                    # only one grade is updated, therefore multiple fields are not possible
                                                    append_dict['err_fields'] = [field]

                                                if logging_on:
                                                    logger.debug('msg_list: ' + str(msg_list))
                                                    logger.debug('updated_grade_pk_list:    ' + str(updated_grade_pk_list))
                                                    logger.debug('append_dict: ' + str(append_dict))

                                                updated_grade_rows = create_grade_rows(
                                                    sel_examyear=sel_examyear,
                                                    sel_schoolbase=sel_school.base if sel_school else None,
                                                    sel_depbase=sel_department.base if sel_department else None,
                                                    sel_lvlbase=sel_level.base if sel_level else None,
                                                    sel_examperiod=sel_examperiod,
                                                    secret_exams_only=secret_exams_only,
                                                    # PR2021-06-01 debug. Remove key 'note_status', otherwise it will erase note icon when refreshing this row
                                                    remove_note_status=True,
                                                    request=request,
                                                    append_dict=append_dict,
                                                    grade_pk_list=updated_grade_pk_list
                                                )
                                                if updated_grade_rows:
                                                    update_wrap['updated_grade_rows'] = updated_grade_rows

            # - create msg_html with info of rows
                                            if is_test:
                                                msg_html_list, border_class, test_is_ok, has_already_approved = \
                                                     create_approve_grade_msg_dict(count_dict, is_score)
                                                if has_already_approved:
                                                    update_wrap['has_already_approved'] = has_already_approved

            # - add  msg_dict to update_wrap
                                        update_wrap['test_is_ok'] = test_is_ok

        # show modmessage when single update
        if msg_single_update_list:
            update_wrap['msg_html'] = ''.join((
                "<div class='p-2 ", border_class, "'>",
                ''.join(msg_single_update_list),
                "</div>"))
            if logging_on:
                logger.debug('msg_html_list:    ' + str(msg_html_list))

        # show message in MAG modal when multiple  update
        elif msg_html_list:
            update_wrap['approve_msg_html'] = ''.join((
                "<div class='p-2 ", border_class, "'>",
                ''.join(msg_html_list),
                "</div>"))
            if logging_on:
                logger.debug('msg_html_list:    ' + str(msg_html_list))

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of GradeApproveView


def create_approve_grade_msg_dict(count_dict, is_score):
    # PR2022-03-11 PR2023-02-23 PR2023-05-30
    # only called by GradeApproveView
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_approve_grade_msg_dict -----')
        logger.debug('    count_dict: ' + str(count_dict))

    # this function is only called if is_test:
    count = count_dict.get('count', 0)
    committed = count_dict.get('committed', 0)
    no_value = count_dict.get('no_value', 0)
    secret_exam = count_dict.get('is_secret_exam', 0)
    already_published = count_dict.get('already_published', 0)
    auth_missing = count_dict.get('auth_missing', 0)
    already_approved = count_dict.get('already_approved', 0)
    double_approved = count_dict.get('double_approved', 0)

    if logging_on:
        logger.debug('    count_dict: ' + str(count_dict))
        logger.debug('    committed: ' + str(committed))
        logger.debug('    no_value: ' + str(no_value))
        logger.debug('    secret_exam: ' + str(secret_exam))
        logger.debug('    already_published: ' + str(already_published))
        logger.debug('    auth_missing: ' + str(auth_missing))
        logger.debug('    already_approved: ' + str(already_approved))
        logger.debug('    double_approved: ' + str(double_approved))

    has_already_approved = already_approved > 0

    border_class = 'border_bg_valid'
    msg_html_list = []

    msg_html_list.append(''.join(("<p>", str(_("The selection contains %(val)s.") % {'val': get_grade_score_text(count, is_score)}), "</p>")))

    test_is_ok = False
    if committed:
        test_is_ok = True

    if already_published or auth_missing or double_approved or already_approved or no_value or secret_exam:
        msg_html_list.append(''.join(("<p>",
                                      gettext("The following %(cpt)s will be skipped") % {'cpt': gettext('Scores').lower() if is_score else gettext('Grades').lower()},
                                      ":</p><ul>")))

        if already_published:
            msg_html_list.append(''.join(("<li>", str(_("%(val)s already submitted") % {'val': get_grades_scores_are_text(already_published, is_score)}), "</li>")))

        if auth_missing:
            msg_html_list.append(''.join(("<li>", str(_("  - %(val)s not fully approved") % {'val': get_grades_scores_are_text(auth_missing, is_score)}), "</li>")))

        if double_approved:
            msg_html_list.append(''.join(("<li>", get_approved_by_you_text(double_approved, is_score) + str(_(', in a different function')), "</li>")))

        if already_approved:
            msg_html_list.append(''.join(("<li>", get_approved_text(already_approved, is_score), "</li>")))

        if secret_exam:
            secret_exam_txt = "<li>" + str(_("%(val)s designated exam.") % {'val': get_grades_scores_are_text(secret_exam, is_score)})
            if secret_exam == 1:
                secret_exam_txt += ' ' + str(_("It doesn't have to be approved."))
            else:
                secret_exam_txt += ' ' + str(_("They don't have to be approved."))
            msg_html_list.append(secret_exam_txt + "</li>")

        if no_value:
            no_value_txt = "<li>" + str(_("%(val)s not entered.") % {'val': get_grades_scores_are_text(no_value, is_score)})
            if no_value == 1:
                no_value_txt += ' ' + str(_("It doesn't have to be approved."))
            else:
                no_value_txt += ' ' + str(_("They don't have to be approved."))
            msg_html_list.append(no_value_txt + "</li>")


        msg_html_list.append("</ul>")

    msg_html_list.append("<p>")
    if committed == 1:
        cpt = gettext('Score').lower() if is_score else gettext('Grade').lower()
        msg_html_list.append(gettext("One %(cpt)s will be approved.") % {'cpt': cpt})
    else:
        cpts = gettext('Scores').lower() if is_score else gettext('Grades').lower()
        if committed == 0:
            msg_html_list.append(gettext("No %(cpts)s will be approved.") % {'cpts': cpts})
        else:
            msg_html_list.append(gettext("%(val)s %(cpts)s will be approved.") % {'val': committed, 'cpts': cpts})

    msg_html_list.append("</p>")
# - warning if any subjects are not fully approved
    # dont give warning - no values will be skipped
    #if no_value:
    #    get_warning_no_value(count_dict, no_value)

    return msg_html_list, border_class, test_is_ok, has_already_approved
# --- end of create_approve_grade_msg_dict


def get_warning_no_value(no_value):
    # - warning if any subjects are not fully approved PR2022-03-11 PR2023-04-11
    msg_html = None
    if no_value:
        no_value_str = _("One grade has no value.") if no_value == 1 else _("%(val)s grades have no value.") % {
            'val': no_value}
        msg_list = ["<div class='mt-2 p-2 border_bg_warning'><b>", str(_('WARNING')), ':</b><br>', str(no_value_str), ' ',
                    str(_(
                        'It is only allowed to submit grades without value with the prior approval of the Inspectorate, or when the candidate has an exemption.')),
                    '</div>']
        msg_html = ''.join(msg_list)
    return msg_html
# --- end of get_warning_no_value


def batch_approve_grade_rows(grade_rows_tobe_updated, sel_examtype, is_reset, requsr_auth, request):
    #PR2020-03-18
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- batch_approve_grade_rows -----')
        logger.debug('grade_rows_tobe_updated:    ' + str(grade_rows_tobe_updated))
        logger.debug('sel_examtype:    ' + str(sel_examtype))
        logger.debug('requsr_auth:    ' + str(requsr_auth))
        # grade_rows_tobe_updated: [[22961, 146, 2], [21701, 146, 2], [22980, 146, 2]]

    err_html = None
    updated_grade_pk_list = []

    if grade_rows_tobe_updated and sel_examtype and requsr_auth and request.user:
        # sql_keys = {'ey_id': school.examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}

        # dont update modified field when approving.
        #  was: modifiedby_pk_str = str(request.user.pk)
        #       modifiedat_str = str(timezone.now())

        status_field = '_'.join((sel_examtype, 'status'))
        auth_field = ''.join((sel_examtype, "_", requsr_auth, 'by_id'))

        """
        # you can define the types by casting the values of the first row:
        CREATE TEMP TABLE lookup (key, val) AS
        VALUES 
            (0::bigint, -99999::int), 
            (1, 100) ;
        """
        # grade_rows_tobe_updated: [[22961, 146, 2], [21701, 146, 2], [22980, 146, 2]]

        try:
            sql_list = ["CREATE TEMP TABLE gr_update (grade_id, auth_id, status) AS",
                        "VALUES (0::INT, 0::INT, 0::INT)"]

            for row in grade_rows_tobe_updated:
                grade_id= str(row[0])
                auth_id = str(row[1]) if row[1] else 'NULL'
                status = str(row[2])
                sql_list.append(''.join((", (", grade_id, ", ", auth_id , ", ", status, ")")))

            sql_list.extend((
                "; UPDATE students_grade AS gr",
                "SET", auth_field, "= gr_update.auth_id, ", status_field, "= gr_update.status",
                # dont update modified field when approving. Was: "modifiedby_id = ", modifiedby_pk_str, ", modifiedat = '" , modifiedat_str, "'",
                "FROM gr_update",
                "WHERE gr_update.grade_id = gr.id",
                "RETURNING gr.id, gr.studentsubject_id;"
                ))

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()

                for row in rows:
                    updated_grade_pk_list.append(row[0])
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            if len(grade_rows_tobe_updated) == 1:
                if is_reset:
                    msg_txt = _('The approval of this grade has not been removed.')
                else:
                    msg_txt = _('This grade has not been approved.')
            else:
                if is_reset:
                    msg_txt = _('The approval of the grades has not been removed.')
                else:
                    msg_txt = _('The grades have not been approved.')

            err_html = ''.join((
                gettext('An error occurred'),
                '<br>&emsp;<i>', str(e), '</i><br>',
                str(msg_txt)
            ))

    if logging_on:
        logger.debug('updated_grade_pk_list:' + str(updated_grade_pk_list))
    return err_html, updated_grade_pk_list
# - end of batch_approve_grade_rows


def batch_submit_ex2_rows(grade_rows_tobe_updated, sel_examtype, published_pk, request):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- batch_submit_ex2_rows -----')
        logger.debug('grade_rows_tobe_updated:    ' + str(grade_rows_tobe_updated))
        logger.debug('sel_examtype:    ' + str(sel_examtype))

    updated_grade_pk_list = []

    if grade_rows_tobe_updated and sel_examtype  and request.user:

        modifiedby_pk_str = str(request.user.pk)
        modifiedat_str = str(timezone.now())

        status_field = '_'.join((sel_examtype, 'status'))
        published_field = '_'.join((sel_examtype, 'published_id'))

        """
        # you can define the types by casting the values of the first row:
        CREATE TEMP TABLE lookup (key, val) AS
        VALUES 
            (0::bigint, -99999::int), 
            (1, 100) ;
        """
        # grade_rows_tobe_updated: [22961, 21701, 22980]
        if published_pk:
            try:
                sql_list = ["CREATE TEMP TABLE gr_update (grade_id) AS",
                            "VALUES (0::INT)"]

                for pk_int in grade_rows_tobe_updated:
                    grade_id= str(pk_int)
                    sql_list.append(''.join((", (", grade_id, ")")))

                sql_list.extend((
                    "; UPDATE students_grade AS gr",
                    "SET", published_field, "=", str(published_pk), ",", status_field, "=", str(c.STATUS_05_PUBLISHED),
                    # dont update modified field when approving. Was: "modifiedby_id = ", modifiedby_pk_str, ", modifiedat = '" , modifiedat_str, "'",
                    "FROM gr_update",
                    "WHERE gr_update.grade_id = gr.id",
                    "RETURNING gr.id;"
                    ))

                sql = ' '.join(sql_list)

                if logging_on:
                    logger.debug('sql: ' + str(sql))
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    rows = cursor.fetchall()

                    for row in rows:
                        updated_grade_pk_list.append(row[0])
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('updated_grade_pk_list:' + str(updated_grade_pk_list))
    return updated_grade_pk_list
# - end of batch_submit_ex2_rows


def create_grade_approve_rows(request, sel_examyear, sel_school, sel_department, sel_level,
                              sel_examperiod, sel_examtype, secret_exams_only, userallowed_sections_dict,
                              allowed_clusters_of_sel_school, grade_pk=None, include_grades=False):
    # PR2022-03-07 PR2022-06-13 PR2023-02-02 PR2024-05-02
    # called by GradeApproveView, GradeSubmitEx2Ex2aView
    # include_grades is True when called by GradeSubmitEx2Ex2aView

    # don't filter on allowed when submitting Ex form i.e. when include_grades = True PR2023-02-14
    # PR2023-02-22 must filter on allowed school, dep and level, but not on subject and cluster

    # PR2024-045-02 debug: Jacqueline Duggins-Horsford MPC / Sundial
    # cannot approve Havo / Vwo SE grades, it says: no records
    # cause: lvlbase_pk = None, therefore is_allowed = False

    apply_allowed_filter = not include_grades

    sel_examyear_pk = sel_examyear.pk if sel_examyear else None
    sel_schoolbase_pk = sel_school.base_id if sel_school else None
    sel_depbase_pk = sel_department.base_id if sel_department else None
    sel_lvlbase_pk = sel_level.base.pk if sel_level else None

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- create_grade_approve_rows -----')
        logger.debug('     sel_examperiod: ' + str(sel_examperiod))
        logger.debug('     sel_examtype:  ' + str(sel_examtype))
        logger.debug('     grade_pk:       ' + str(grade_pk))
        logger.debug('     include_grades: ' + str(include_grades))
        logger.debug('     sel_lvlbase_pk: ' + str(sel_lvlbase_pk))

    grade_rows = []
    log_list = []

# - get selected_pk_dict of req_usr
    sel_sctbase_pk, sel_subjbase_pk, sel_cluster_pk = None, None, None
    selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
    if selected_pk_dict:
        # don't filter on sct, subj, cluster when approving single grade or when submitting Ex2 form
        if grade_pk is None and apply_allowed_filter:
            sel_sctbase_pk = selected_pk_dict.get(c.KEY_SEL_SCTBASE_PK)
            sel_subjbase_pk = selected_pk_dict.get(c.KEY_SEL_SUBJBASE_PK)
            sel_cluster_pk = selected_pk_dict.get(c.KEY_SEL_CLUSTER_PK)

    if sel_examyear_pk and sel_examperiod and sel_schoolbase_pk and sel_depbase_pk:
        #sql_keys = {'ey_id': sel_examyear_pk, 'experiod': sel_examperiod, 'sb_id': sel_schoolbase_pk, 'depbase_id': sel_depbase_pk}

        # PR2022-05-11 Sentry debug: syntax error at or near "FROM"
        # in: grd.pecegrade, grd.finalgrade, FROM students_grade AS grd
        # because sel_examtype had no or wrong value and therefore auth_line etc were ''
        # put schoolbase_id field at the end, to make sure there is never a comma in front of FROM

        sql_list = [
            "SELECT grd.id, grd.examperiod, studsubj.id AS studsubj_id, studsubj.cluster_id, studsubj.has_exemption,",
            "COALESCE(exam.secret_exam, FALSE) AS secret_exam,",
            "subj.base_id AS subjbase_id, lvl.base_id AS lvlbase_id, dep.base_id AS depbase_id, school.base_id AS schoolbase_id,"]

        if sel_examtype in ('se', 'sr', 'pe', 'ce'):
    # add auth fields
            sql_list.extend([
                "grd." + sel_examtype + "_auth1by_id AS auth1by_id,",
                "grd." + sel_examtype + "_auth2by_id AS auth2by_id,",
                "grd." + sel_examtype + "_auth3by_id AS auth3by_id,",
                "grd." + sel_examtype + "_auth4by_id AS auth4by_id,"
                "grd." + sel_examtype + "_published_id AS published_id,",
                "grd." + sel_examtype + "_blocked AS blocked,"
                ])

    # add has_value field
            if sel_examtype in ('se', 'sr'):
                sql_list.append(''.join(("CASE WHEN grd.", sel_examtype, "grade IS NOT NULL THEN TRUE ELSE FALSE END AS has_value,")))
                # this one doenst work: value_line = ''.join(("grd.", sel_examtype, "grade IS NOT NULL AS has_value,"))
            elif sel_examtype in ('pe', 'ce'):
                sql_list.append(''.join(("CASE WHEN grd.", sel_examtype, "score IS NOT NULL OR grd.", sel_examtype, "grade IS NOT NULL THEN TRUE ELSE FALSE END AS has_value,")))
                # this one doenst work: value_line = ''.join(("grd.", sel_examtype, "score IS NOT NULL OR grd.", sel_examtype, "grade IS NOT NULL AS has_value,"))

    # add grade fields
            if include_grades:
                sql_list.append("grd.pescore, grd.cescore, grd.segrade, grd.srgrade, grd.sesrgrade, grd.pegrade, grd.cegrade, grd.pecegrade, grd.finalgrade,")

    # add status field
            sql_list.append("grd." + sel_examtype + "_status AS status, ")

        sql_list.extend([
            "subj.base_id AS subjbase_id, lvl.base_id AS lvlbase_id, dep.base_id AS depbase_id, school.base_id AS schoolbase_id,",
            "CONCAT_WS (' ', stud.prefix, CONCAT(stud.lastname, ','), stud.firstname) AS stud_name, subj.name_nl AS subj_name,",

            # PR2024-06-4 added: OR stud.partial_exam
            # was: "CASE WHEN stud.subj_composition_ok OR stud.subj_dispensation THEN FALSE ELSE TRUE END AS composition_error,",
            "CASE WHEN stud.subj_composition_ok OR stud.subj_dispensation OR stud.partial_exam THEN FALSE ELSE TRUE END AS composition_error,",

            # PR2024-06-04 added:
            "stud.extrafacilities, stud.iseveningstudent, stud.islexstudent, stud.bis_exam, stud.partial_exam,",

            "studsubj.tobedeleted AS studsubj_tobedeleted,",
            "CASE WHEN studsubj.subj_published_id IS NULL THEN TRUE ELSE FALSE END AS studsubj_not_published",

            "FROM students_grade AS grd",
            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
            "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",

            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",
            "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)"
        ])
        if secret_exams_only:
            sql_list.append("INNER JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id)")
        else:
            sql_list.append("LEFT JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id)")

        sql_list.append(''.join((
             "WHERE ey.id = ", str(sel_examyear_pk) , "::INT AND grd.examperiod = ", str(sel_examperiod), "::INT ",
            "AND dep.base_id = ", str(sel_depbase_pk), "::INT")))

            #PR2022-04-22 Kevin Weert JPD error: cannot submit Ex2 because subjects are not approved
            # turned out to be deleted grade. Forgot to add 'NOT tobedeleted' filter

            # PR2023-09-13 this was not used, but I don/t now why:
            #   #"AND NOT stud.tobedeleted AND NOT stud.deleted ",
            #   #"AND NOT studsubj.tobedeleted AND NOT studsubj.deleted",
            #   #"AND NOT grd.tobedeleted AND NOT grd.deleted",
            # instead this one was used:
            #   AND NOT stud.deleted AND NOT studsubj.deleted",
            # going back to the first one, except for the  grd.tobedeleted / grd.deleted". grd.deleted is filtered further in this function
        sql_list.append("AND NOT stud.tobedeleted AND NOT stud.deleted")
        sql_list.append("AND NOT studsubj.tobedeleted AND NOT studsubj.deleted")

        # grd.deleted is only used when examperiod = exem, reex ofr reex3 PR2023-02-14
        if sel_examperiod in (c.EXAMPERIOD_SECOND, c.EXAMPERIOD_SECOND, c.EXAMPERIOD_EXEMPTION):
            sql_list.append("AND NOT grd.deleted")

        if not secret_exams_only:
            sql_list.append(''.join(("AND school.base_id = ", str(sel_schoolbase_pk), "::INT")))
        else:
            sql_list.append("AND exam.secret_exam")

        # PR2022-05-31 debug: grades without CE were still approved.
            # Must add filter weight_ce > 0 when ep = 1,2,3 and sel_examtype = 'pe', 'ce'
        if sel_examtype in ('se', 'sr'):
            sql_list.append("AND si.weight_se > 0")

        # and sel_examperiod in (1, 2, 3) is not necessary , I think PR2023-02-14
        # was: elif sel_examtype in ('pe', 'ce') and sel_examperiod in (1, 2, 3):
        elif sel_examtype in ('pe', 'ce'):
            sql_list.append("AND si.weight_ce > 0")

        if grade_pk:
            sql_list.append(''.join(("AND grd.id = ", str(grade_pk), "::INT")))

# - filter on selected levelbase, not when Havo Vwo
        if sel_lvlbase_pk and sel_department.level_req:
            sql_list.append(''.join(("AND (lvl.base_id = ", str(sel_lvlbase_pk), "::INT)")))

# - filter on selected sectorbase
        if sel_sctbase_pk and apply_allowed_filter:
            sql_list.append(''.join(("AND (sct.base_id = ", str(sel_sctbase_pk), "::INT)")))

# - filter on selected subjectbase TODO to be changed to subjectbase
        # SO FAR
        #PR2024-06-11 TODO check if sel_subjbase_pk is in allowed subjbase_arr of this school / dep / lvl
        # only add filter when it is in the list
        if sel_subjbase_pk and apply_allowed_filter:
            sql_list.append(''.join(("AND (subj.base_id = ", str(sel_subjbase_pk), "::INT)")))

# - filter on selected cluster_pk
        if sel_cluster_pk and apply_allowed_filter:
            sql_list.append(''.join(("AND (studsubj.cluster_id = ", str(sel_cluster_pk), "::INT)")))

# - get allowed_sections_dict from request
        if apply_allowed_filter:
            if logging_on:
                logger.debug('    allowed_sections_dict: ' + str(userallowed_sections_dict))
                # allowed_sections_dict: {'2': {'1': {'4': [117, 114], '5': [], '-9': [118, 121]}}} <class 'dict'>

# - filter on allowed depbases, levelbase, subjectbases
            sqlclause_allowed_dep_lvl_subj = acc_prm.get_sqlclause_allowed_dep_lvl_subj(
                table='grade',
                userallowed_sections_dict=userallowed_sections_dict,
                sel_schoolbase_pk=sel_schoolbase_pk,
                sel_depbase_pk=sel_depbase_pk
            )
            if sqlclause_allowed_dep_lvl_subj:
                sql_list.append(sqlclause_allowed_dep_lvl_subj)

# - filter on allowed clusters
            # PR2023-05-29 do'nt filter on allowed cluster here, because msg must be sent when cluster not allowed
            # filter in validate_approve
            #userallowed_cluster_pk_clause = acc_prm.get_sqlclause_allowed_clusters(
            #    table='studsubj',
            #    allowed_clusters_of_sel_school=allowed_clusters_of_sel_school
            #)
            #if userallowed_cluster_pk_clause:
            #    sql_list.append( userallowed_cluster_pk_clause)

        sql_list.append('ORDER BY stud.lastname, stud.firstname')

        sql = ' '.join(sql_list)

        if logging_on:
            for sql_txt in sql_list:
                logger.debug('  > ' + str(sql_txt))

        with connection.cursor() as cursor:
            cursor.execute(sql)
            grade_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('     len(grade_rows): ' + str(len(grade_rows)))

    # only used for logger.debug
            no_value_count, not_approved_count, studsubj_tobedeleted_count, studsubj_not_published_count = 0, 0, 0, 0
            for row in grade_rows:
                if not row.get('has_value', False):
                    no_value_count += 1
                if not row.get('auth1by_id') or not row.get('auth2by_id') or not row.get('auth3by_id'):
                    not_approved_count += 1

                if row.get('studsubj_tobedeleted', False):
                    studsubj_tobedeleted_count += 1

                # TODO submit exemption grades

                if not row.get('studsubj_not_published'):
                    studsubj_not_published_count += 1

            logger.debug('     no_value_count:     ' + str(no_value_count))
            logger.debug('     not_approved_count: ' + str(not_approved_count))
            logger.debug('     tobedeleted_count:  ' + str(studsubj_tobedeleted_count))
            logger.debug('     studsubj_not_published_count:    ' + str(studsubj_not_published_count))

    return grade_rows
# --- end of create_grade_approve_rows


def check_ex5_grade_approved_rows(sel_examyear_pk, sel_examperiod, sel_schoolbase_pk, sel_depbase_pk, sel_lvlbase_pk):
    # PR2022-06-12 PR2022-07-12  PR2023-06-20
    # only called by GradeSubmitEx5View
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- check_ex5_grade_approved_rows -----')

    log_list = []
    try:


        # PR2022-05-11 Sentry debug: syntax error at or near "FROM"
        # in: grd.pecegrade, grd.finalgrade, FROM students_grade AS grd
        # because sel_examtype had no or wrong value and therefor auth_line etc were ''
        # put schoolbase_id field at the end, to make sure there is never a comma in front of FROM

        # must add experiod, otherwise E5 ep01 cannot be submitted when there are reex candidates
        # PR2023-07-10 Sentry debug: %(experiod)s not in sql_keys
        # PR2023-12-12 Sentry debug: same issue - solved by adding sel_examperiod

        sql_keys = {'ey_id': sel_examyear_pk, 'experiod': sel_examperiod,
                    'schoolbase_id': sel_schoolbase_pk, 'depbase_id': sel_depbase_pk}

        sql_list = [
            "SELECT grd.id, grd.examperiod, studsubj.id AS studsubj_id, ",
            "subj.base_id AS subjbase_id, lvl.base_id AS lvlbase_id, dep.base_id AS depbase_id, school.base_id AS schoolbase_id,",
            "exam.secret_exam,"
            "subj.base_id AS subjbase_id, lvl.base_id AS lvlbase_id, dep.base_id AS depbase_id, school.base_id AS schoolbase_id,",
            "stud.lastname, stud.firstname, stud.prefix, subj.name_nl AS subj_name",

            "FROM students_grade AS grd",
            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
            "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",

            "LEFT JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id)",

            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",

            "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

            "WHERE ey.id = %(ey_id)s::INT AND grd.examperiod = %(experiod)s::INT",
            "AND school.base_id = %(schoolbase_id)s::INT AND dep.base_id = %(depbase_id)s::INT",

            # PR2022-07-12 was: "AND NOT stud.withdrawn AND NOT studsubj.has_exemption",
            "AND NOT stud.withdrawn",

            #PR2022-04-22 Kevin Weert JPD error: cannot submit Ex2 because subjects are not approved
            # turned out to be deleted grade. Forgot to add 'NOT tobedeleted' filter

            "AND NOT stud.deleted AND NOT stud.tobedeleted",
            "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted",
            "AND NOT grd.deleted AND NOT grd.tobedeleted"
        ]

        if sel_lvlbase_pk:
            sql_list.extend(("AND lvl.base_id = ", str(sel_lvlbase_pk) , "::INT"))

        sql_list.append('ORDER BY stud.lastname, stud.firstname, subj.name_nl')

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)
            if rows:
                for row in rows:

                    # PR2022-07-12 Dafna Azulai Dr. Albert Schweitzer College Parera Vsbo
                    # error: cannot submit Ex5 because subject are is not approved
                    # turned out to be secret exam. Forgot to skip auth3 auth 4 check when secret exam

                    not_fully_approved = False
                    # check if auth1, auth2 and auth3 have approved segrade, only when weight_se > 0 and segrade is not None
                    if row.get('weight_se', 0) > 0 and row.get('segrade') is not None:
                        not_fully_approved = not row.get('se_auth1by_id') or not row.get('se_auth2by_id') or not row.get('se_auth3by_id')
                    if not not_fully_approved:
                        if row.get('weight_ce', 0) > 0 and row.get('cescore') is not None:
                    # check if auth1 and auth2 have approved cescore, only when weight_ce > 0 and cescore is not None
                            not_fully_approved = not row.get('ce_auth1by_id') or not row.get('ce_auth2by_id')
                            if not not_fully_approved and not row.get('secret_exam'):
                    # check if auth3 and auth4 have approved cescore, when not secret_exam
                                not_fully_approved = not row.get('ce_auth3by_id') or not row.get('ce_auth4by_id')
                    if not_fully_approved:
                        stud_name = stud_fnc.get_full_name(row.get('lastname'), row.get('firstname'), row.get('prefix'))
                        log_list.append(' - '.join((stud_name, row.get('subj_name', '-'))))
                    if logging_on :
                        logger.debug('    row: ' + str(row))
                        logger.debug('    not_fully_approved: ' + str(not_fully_approved))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return log_list
# --- end of check_ex5_grade_approved_rows


@method_decorator([login_required], name='dispatch')
class GradeSubmitEx2Ex2aView(View):  # PR2021-01-19 PR2022-03-08 PR2022-04-17 PR2022-06-12
    # function creates new published_instance, Ex2 / Ex2A xlsx and sets published_id in grade

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= GradeSubmitEx2Ex2aView ============= ')

        update_wrap = {}

        authmissing_list = []
        subj_not_published_list = []

        msg_html = None
        test_is_ok = False

        req_usr = request.user

# -  get user_lang
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = False
        requsr_auth = None
        if req_usr and req_usr.country and req_usr.schoolbase:

            permit_list = acc_prm.get_permit_list('page_grade', req_usr)
            if permit_list:
                # msg_err is made on client side. Here: just skip if user has no or multiple functions

                # PR2023-02-03 was: was: requsr_usergroup_list = req_usr.usergroup_list
                requsr_usergroup_list = acc_prm.get_usergroup_list_from_user_instance(req_usr)
                is_auth1 = 'auth1' in requsr_usergroup_list
                is_auth2 = 'auth2' in requsr_usergroup_list
                if is_auth1 + is_auth2 == 1:
                    if is_auth1:
                        requsr_auth = 'auth1'
                    elif is_auth2:
                        requsr_auth = 'auth2'
                if requsr_auth:
                    has_permit = 'permit_submit_grade' in permit_list

            if logging_on:
                #logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

        if not has_permit:
            msg_html = acc_prm.err_html_no_permit()
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                """
                upload_dict{'table': 'grade', 'mode': 'submit_test', 'auth_index': 1, 'now_arr': [2022, 3, 14, 11, 13]}
                upload_dict: {'table': 'grade', 'form': 'ex2a', 'auth_index': 1, 'now_arr': [2022, 6, 1, 9, 38], 'mode': 'submit_test'}
                upload_dict: {'table': 'grade', 'form': 'ex2', 'auth_index': 1, 'examperiod': 1, 'examtype': 'se', 'level_abbrev': 'pbl_pkl', 'now_arr': [2023, 2, 5, 8, 3], 'mode': 'submit_test'}
                """

# -- get selected examyear, school, department and level from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                if err_list:
                    msg_html = '<br>'.join(err_list)
                else:

                    is_sxm = sel_examyear.country.abbrev.lower() == 'sxm'

# -- get selected mode. Modes are 'submit_test' 'submit_save'
                    mode = upload_dict.get('mode')
                    form_name = upload_dict.get('form')
                    is_test = (mode == 'submit_test')
                    auth_index = upload_dict.get('auth_index')
                    level_abbrev = upload_dict.get('level_abbrev')

                    if logging_on:
                        logger.debug('     upload_dict: ' + str(upload_dict))
                        logger.debug('     mode:        ' + str(mode))
                        logger.debug('     form_name:   ' + str(form_name))
                        logger.debug('     auth_index:  ' + str(auth_index))
                        logger.debug('     level_abbrev:' + str(level_abbrev))

                    if auth_index:

                        # msg_err is made on client side. Here: just skip if user has no or multiple functions

        # - get auth_index (1 = Chairperson, 2 = Secretary, 3 = Examiner, 4 = Corrector
                        # PR2021-03-27 auth_index is taken from requsr_usergroups_list, not from upload_dict
                        #  function may have changed if gradepage is not refreshed in time)
                        #  was: auth_index = upload_dict.get('auth_index')
                        #  >>> can't do it like this any more. User can be examiner and pres/secr at the same time
                        #  back to upload_dict.get('auth_index')

        # get_allowed_sections
                        userallowed_instance = acc_prm.get_userallowed_instance(request.user, sel_examyear)
                        userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
                        userallowed_cluster_pk_list = acc_prm.get_userallowed_cluster_pk_list(userallowed_instance)

                        # PR2024-05-30 filter on examyear_pk added
                        allowed_clusters_of_sel_school = acc_prm.get_allowed_clusters_of_sel_school(
                            sel_schoolbase_pk=sel_school.base_id if sel_school else None,
                            sel_examyear_pk=sel_school.examyear_id if sel_school else None,
                            allowed_cluster_pk_list=userallowed_cluster_pk_list
                        )

        # - get selected examperiod, levelbase from usersetting
                        sel_examperiod, sel_examtype, sel_lvlbase_pk = None, None, None
                        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                        if selected_pk_dict:
                            sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
                            sel_examtype = selected_pk_dict.get(c.KEY_SEL_EXAMTYPE)
                            sel_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)

    # replace examtype 'reex', 'reex03' with 'ce' (sel_examperiod determines if it is reex)
                            if sel_examtype in ('reex', 'reex03'):
                                sel_examtype = 'ce'

    # PR2023-02-27 debug: when submitting Ex2, examtype is always 'se'
                        if form_name == 'ex2':
                            sel_examtype = 'se'
                        elif form_name == 'ex2a':
                            sel_examtype = 'ce'

                        if logging_on:
                            logger.debug('     sel_examtype:   ' + str(sel_examtype))
                            logger.debug('     sel_examperiod: ' + str(sel_examperiod))
                            logger.debug('     sel_examtype:   ' + str(sel_examtype))
                            logger.debug('     sel_lvlbase_pk: ' + str(sel_lvlbase_pk))

                        if sel_examperiod and sel_examtype:

# - if examtype haschanged: save it in usersettings
                            selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                            if selected_dict:
                                save_setting = False
                                saved_examperiod = selected_dict.get(c.KEY_SEL_EXAMPERIOD)
                                saved_examtype = selected_dict.get(c.KEY_SEL_EXAMTYPE)
                                if sel_examperiod != saved_examperiod:
                                    selected_dict[c.KEY_SEL_EXAMPERIOD] = sel_examperiod
                                    save_setting = True
                                if sel_examtype != saved_examtype:
                                    selected_dict[c.KEY_SEL_EXAMTYPE] = sel_examtype
                                    save_setting = True
                                if save_setting:
                                    acc_view.set_usersetting_dict(c.KEY_SELECTED_PK, selected_pk_dict, request)

    # - when mode = submit_submit: check verificationcode.
                            verification_is_ok = True
                            if not is_test:
                                verification_is_ok, verif_msg_html = af.check_verifcode_local(upload_dict, request)
                                if verif_msg_html:
                                    msg_html = verif_msg_html
                                if verification_is_ok:
                                    update_wrap['verification_is_ok'] = True
                                else:
                                    # return verificationkey when verification failed
                                    update_wrap['verificationkey'] = upload_dict.get('verificationkey')

                            if logging_on:
                                logger.debug('     verification_is_ok: ' + str(verification_is_ok))
                                logger.debug('     msg_html:           ' + str(msg_html))
                                logger.debug('     is_test:            ' + str(is_test))

                            if verification_is_ok:

# - may submit Ex2 per level.
                                sel_level = None
                                if sel_lvlbase_pk:
                                    sel_level = subj_mod.Level.objects.get_or_none(
                                        base_id=sel_lvlbase_pk,
                                        examyear=sel_examyear
                                    )
                                if logging_on:
                                    logger.debug('     sel_level: ' + str(sel_level))
# - create_grade_approve_rows
                                grade_approve_rows = create_grade_approve_rows(
                                    request=request,
                                    sel_examyear=sel_examyear,
                                    sel_school=sel_school,
                                    sel_department=sel_department,
                                    sel_level=sel_level,
                                    sel_examperiod=sel_examperiod,
                                    sel_examtype=sel_examtype,
                                    secret_exams_only=False,
                                    userallowed_sections_dict=userallowed_sections_dict,
                                    allowed_clusters_of_sel_school=allowed_clusters_of_sel_school,
                                    include_grades=True
                                )

                                if not grade_approve_rows:
                                    msg_txt = str(_("The selection contains %(val)s.") % {'val': str(_('no subjects'))})
                                    msg_html = ''.join(("<div class='p-2 border_bg_invalid'>", msg_txt, "</div>"))

                                else:

# +++ create new published_instance.
                                    # only save it when it is not a test
                                    # file_name will be added after creating Ex-form
                                    published_instance = None
                                    published_pk = None
                                    file_name = None
                                    if not is_test:
                                        now_arr = upload_dict.get('now_arr')
                                        published_instance = create_published_instance(
                                            sel_examyear=sel_examyear,
                                            sel_school=sel_school,
                                            sel_department=sel_department,
                                            sel_level=sel_level,
                                            sel_examtype=sel_examtype,
                                            sel_examperiod=sel_examperiod,
                                            is_test=is_test,
                                            ex_form=form_name,  # 'ex2', 'ex2a'
                                            now_arr=now_arr,
                                            request=request
                                        )
                                        if published_instance:
                                            published_pk = published_instance.pk
                                            file_name = published_instance.name

                                    if logging_on:
                                        logger.debug('     published_pk: ' + str(published_pk))
                                        logger.debug('     file_name:    ' + str(file_name))

# +++++ loop through grade_approve_rows, add row to grade_rows_tobe_updated when it must be updated
                                    grade_rows_tobe_updated = []
                                    count_dict = {}
                                    for grade_row in grade_approve_rows:
                                        subj_not_published_txt, authmissing_txt = calc_grade_rows_tobe_updated(
                                            grade_row=grade_row,
                                            tobe_updated_list=grade_rows_tobe_updated,
                                            sel_examperiod=sel_examperiod,
                                            sel_examtype=sel_examtype,
                                            is_sxm=is_sxm,
                                            is_test=is_test,
                                            count_dict=count_dict
                                        )
                                        if subj_not_published_txt:
                                            subj_not_published_list.append(subj_not_published_txt)
                                        if authmissing_txt:
                                            authmissing_list.append(authmissing_txt)

# +++++  end of loop through grade_approve_rows

                                    updated_grade_pk_list = []
                                    if not is_test and grade_rows_tobe_updated:
                                        updated_grade_pk_list = batch_submit_ex2_rows(grade_rows_tobe_updated, sel_examtype, published_pk, request)

# +++ create Ex2_xlsx
                                    saved_to_disk = False
                                    if not is_test:
                    # - get text from examyearsetting
                                        library = awpr_lib.get_library(sel_examyear, ['exform', 'ex2', 'ex2a'])
                                        # just to prevent PyCharm warning on published_instance=published_instance
                                        # response = awpr_excel.create_ex2_ex2a_ex6_xlsx(
                                        if logging_on:
                                            logger.debug('     is_test: ' + str(is_test))

                                        # PR2023-08-26 function create_ex2_ex2a_rows_dict moved from within create_ex2_ex2a_ex6_xlsx TODO check if this causes any bugs
                                        ex_rows_dict, grades_auth_dict = awpr_excel.create_ex2_ex2a_rows_dict(
                                            examyear=sel_examyear,
                                            school=sel_school,
                                            department=sel_department,
                                            level=sel_level,
                                            examperiod=sel_examperiod,
                                            ex_form=form_name,
                                            published_instance=published_instance
                                        )

                                        responseNIU, saved_to_disk = awpr_excel.create_ex2_ex2a_ex6_xlsx(
                                            published_instance=published_instance,
                                            examyear=sel_examyear,
                                            school=sel_school,
                                            department=sel_department,
                                            level=sel_level,
                                            examperiod=sel_examperiod,
                                            ex_rows_dict=ex_rows_dict,
                                            grades_auth_dict=grades_auth_dict,
                                            library=library,
                                            ex_form=form_name,
                                            save_to_disk=True,
                                            request=request,
                                            user_lang=user_lang
                                        )

                                        update_wrap['updated_published_rows'] = sch_view.create_published_rows(
                                            request=request,
                                            sel_examyear_pk=sel_examyear.pk if sel_examyear else None,
                                            sel_schoolbase_pk=sel_school.base_id if sel_school else None,
                                            published_pk=published_pk
                                        )
                                        if logging_on:
                                            logger.debug('updated_grade_pk_list: ' + str(updated_grade_pk_list))

                                        if updated_grade_pk_list:
                                            updated_grade_rows = create_grade_rows(
                                                sel_examyear=sel_examyear,
                                                sel_schoolbase=sel_school.base if sel_school else None,
                                                sel_depbase=sel_department.base if sel_department else None,
                                                sel_lvlbase=None,
                                                sel_examperiod=sel_examperiod,
                                                # PR2021-06-01 debug. Remove key 'note_status', otherwise it will erase not icon when refreshing this row
                                                remove_note_status=True,
                                                request=request,
                                                grade_pk_list=updated_grade_pk_list
                                            )
                                            if updated_grade_rows:
                                                update_wrap['updated_grade_rows'] = updated_grade_rows

# +++ create msg_html with info of rows
                                    exform_txt = 'Ex2A' if form_name == 'ex2a' else 'Ex2'
                                    msg_html, test_is_ok = create_ex2_ex2a_msg_html(
                                        sel_department=sel_department,
                                        sel_level=sel_level,
                                        sel_examtype=sel_examtype,
                                        count_dict=count_dict,
                                        subj_not_published_list=subj_not_published_list,
                                        authmissing_list=authmissing_list,
                                        file_name=file_name,
                                        saved_to_disk=saved_to_disk,
                                        is_test=is_test,
                                        exform_txt=exform_txt
                                    )

        logger.debug('    msg_html: ' + str(msg_html))
 # - add  msg_html to update_wrap
        update_wrap['test_is_ok'] = test_is_ok
        if msg_html:
            update_wrap['approve_msg_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of GradeSubmitEx2Ex2aView


@method_decorator([login_required], name='dispatch')
class GradeSubmitEx5View(View):  # PR2022-06-12 PR2023-06-15
    # function creates new published_instance, Ex5 xlsx and sets published_id in grade

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= GradeSubmitEx5View ============= ')

        update_wrap = {}
        messages = []
        msg_html = None
        msg_dict = {}
        test_is_ok = False

# - get permit
        has_permit = False
        req_usr = request.user

        has_permit = acc_prm.get_permit_of_this_page('page_result', 'submit_ex5', request)
        if logging_on:
            logger.debug('     has_permit: ' + str(has_permit))
        if has_permit:

# -  get user_lang
            user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                """
                upload_dict{'table': 'grade', 'mode': 'submit_test', 'auth_index': 1, 'now_arr': [2022, 3, 14, 11, 13]}
                upload_dict: {'table': 'grade', 'form': 'ex2a', 'auth_index': 1, 'now_arr': [2022, 6, 1, 9, 38], 'mode': 'submit_test'}
                """

# -- get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                if err_list:
                    msg_html = '<br>'.join(err_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                else:

    # - get selected mode. Modes are 'submit_test' 'submit_save'
                    mode = upload_dict.get('mode')
                    form_name = upload_dict.get('form')
                    is_test = (mode == 'submit_test')
                    auth_index = upload_dict.get('auth_index')

                    if logging_on:
                        logger.debug('     upload_dict: ' + str(upload_dict))
                        logger.debug('     mode:        ' + str(mode))
                        logger.debug('     auth_index:  ' + str(auth_index))

                    if auth_index:

                        # msg_err is made on client side. Here: just skip if user has no or multiple functions

        # - get auth_index (1 = Chairperson, 2 = Secretary, 3 = Examiner, 4 = Corrector
                        # PR2021-03-27 auth_index is taken from requsr_usergroups_list, not from upload_dict
                        #  function may have changed if gradepage is not refreshed in time)
                        #  was: auth_index = upload_dict.get('auth_index')
                        #  >>> can't do it like this any more. User can have be examiner and pres/secr at the same time
                        #  back to upload_dict.get('auth_index')

    # - get selected examperiod, levelbase from usersetting
                        sel_examperiod, sel_lvlbase_pk = None, None
                        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                        if selected_pk_dict:
                            sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
                            sel_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)

                        if logging_on:
                            logger.debug('     sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
                            logger.debug('     sel_examperiod: ' + str(sel_examperiod))

                        if sel_examperiod:

    # - when mode = submit_submit: check verificationcode.
                            verification_is_ok = True
                            if not is_test:
                                verification_is_ok, verif_msg_html = af.check_verifcode_local(upload_dict, request)
                                if verif_msg_html:
                                    msg_html = verif_msg_html
                                if verification_is_ok:
                                    update_wrap['verification_is_ok'] = True

                            if verification_is_ok:
# - may submit Ex5 per level
                                sel_level = None
                                if sel_lvlbase_pk:
                                    sel_level = subj_mod.Level.objects.get_or_none(
                                        base_id=sel_lvlbase_pk,
                                        examyear=sel_examyear
                                    )

                                if logging_on:
                                    logger.debug('     sel_level: ' + str(sel_level))
# - check ex5_grade_approved_rows
                                log_list = check_ex5_grade_approved_rows(
                                    sel_examyear_pk=sel_examyear.pk if sel_examyear else None,
                                    sel_examperiod=sel_examperiod,
                                    sel_schoolbase_pk=sel_school.base_id if sel_school else None,
                                    sel_depbase_pk=sel_department.base_id if sel_department else None,
                                    sel_lvlbase_pk=sel_level.base_id if sel_level else None
                                )
                                test_is_ok = not len(log_list)

                                msg_html = create_submit_ex5_test_msg_html(sel_department, sel_level, log_list, test_is_ok)

                                if test_is_ok:
# +++ create new published_instance.
                                    # only save it when it is not a test
                                    # file_name will be added after creating Ex-form
                                    published_instance = None
                                    published_pk = None
                                    file_name = None
                                    if not is_test:
                                        now_arr = upload_dict.get('now_arr')
                                        published_instance = create_published_instance(
                                            sel_examyear=sel_examyear,
                                            sel_school=sel_school,
                                            sel_department=sel_department,
                                            sel_level=sel_level,
                                            sel_examtype='',
                                            sel_examperiod=sel_examperiod,
                                            is_test=is_test,
                                            ex_form='ex5',
                                            now_arr=now_arr,
                                            request=request
                                        )
                                        if published_instance:
                                            published_pk = published_instance.pk
                                            file_name = published_instance.name

                                    if logging_on:
                                        logger.debug('     published_pk: ' + str(published_pk))
                                        logger.debug('     file_name:    ' + str(file_name))

# +++ create Ex5_xlsx
                                    if not is_test:
                    # - get text from examyearsetting
                                        # just to prevent PyCharm warning on published_instance=published_instance
                                        # response = awpr_excel.create_ex2_ex2a_ex6_xlsx(
                                        if logging_on:
                                            logger.debug('     is_test: ' + str(is_test))

                                        saved_is_ok, response = awpr_excel.create_ex5_xlsx(
                                            published_instance=published_instance,
                                            examyear=sel_examyear,
                                            school=sel_school,
                                            department=sel_department,
                                            level=sel_level,
                                            examperiod=sel_examperiod,
                                            save_to_disk=True,
                                            request=request,
                                            user_lang=user_lang)

                                        msg_html = create_submit_ex5_ex6_saved_msg_html(
                                            saved_is_ok=saved_is_ok,
                                            is_ex6=False,
                                            published_instance=published_instance
                                        )


# - add  msg_html to update_wrap
        update_wrap['test_is_ok'] = test_is_ok
        if msg_html:
            update_wrap['approve_msg_html'] = msg_html
        if msg_dict:
            update_wrap['approve_msg_dict'] = msg_dict

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of GradeSubmitEx5View



@method_decorator([login_required], name='dispatch')
class GradeSubmitEx6View(View):  # PR2023-08-26
    # function creates new published_instance, Ex6 xlsx and sets published_id in grade

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= GradeSubmitEx6View ============= ')

        update_wrap = {}
        messages = []
        msg_html = None
        msg_dict = {}
        test_is_ok = False

# - get permit

        has_permit = acc_prm.get_permit_of_this_page('page_result', 'submit_ex5', request)
        if logging_on:
            logger.debug('     has_permit: ' + str(has_permit))
        if has_permit:
            req_usr = request.user

# -  get user_lang
            user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                """
                upload_dict{'table': 'grade', 'mode': 'submit_test', 'auth_index': 1, 'now_arr': [2022, 3, 14, 11, 13]}
                upload_dict: {'table': 'grade', 'form': 'ex2a', 'auth_index': 1, 'now_arr': [2022, 6, 1, 9, 38], 'mode': 'submit_test'}
                """

# -- get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
                if err_list:
                    msg_html = '<br>'.join(err_list)
                    messages.append({'class': "border_bg_warning", 'msg_html': msg_html})
                else:

    # - get selected mode. Modes are 'submit_test' 'submit_save'
                    mode = upload_dict.get('mode')
                    is_test = (mode == 'submit_test')
                    auth_index = upload_dict.get('auth_index')

                    if logging_on:
                        logger.debug('     upload_dict: ' + str(upload_dict))
                        logger.debug('     mode:        ' + str(mode))
                        logger.debug('     auth_index:  ' + str(auth_index))

                    if auth_index:

                        # msg_err is made on client side. Here: just skip if user has no or multiple functions

        # - get auth_index (1 = Chairperson, 2 = Secretary, 3 = Examiner, 4 = Corrector
                        # PR2021-03-27 auth_index is taken from requsr_usergroups_list, not from upload_dict
                        #  function may have changed if gradepage is not refreshed in time)
                        #  was: auth_index = upload_dict.get('auth_index')
                        #  >>> can't do it like this any more. User can have be examiner and pres/secr at the same time
                        #  back to upload_dict.get('auth_index')

    # - get selected examperiod, levelbase from usersetting
                        sel_examperiod, sel_lvlbase_pk = None, None
                        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                        if selected_pk_dict:
                            sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
                            sel_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)

                        if logging_on:
                            logger.debug('     sel_lvlbase_pk: ' + str(sel_lvlbase_pk))

# - when mode = submit_submit: check verificationcode.
                        verification_is_ok = True
                        if not is_test:
                            verification_is_ok, verif_msg_html = af.check_verifcode_local(upload_dict, request)
                            if verif_msg_html:
                                msg_html = verif_msg_html
                            if verification_is_ok:
                                update_wrap['verification_is_ok'] = True

                        if verification_is_ok:
# - may submit Ex6 per level
                            sel_level = None
                            if sel_lvlbase_pk:
                                sel_level = subj_mod.Level.objects.get_or_none(
                                    base_id=sel_lvlbase_pk,
                                    examyear=sel_examyear
                                )

                            if logging_on:
                                logger.debug('     sel_level: ' + str(sel_level))
# - check ex6_grade_approved_rows
                            # not necessary to check grades
                            test_is_ok = True
                            msg_html = ''.join((
                                "<div class='p-2 ", c.HTMLCLASS_border_bg_valid, "'>",
                                    gettext("The %(cpt)s form can be submitted.") % {'cpt': 'Ex6'},
                                '</div>'
                            ))

                            if test_is_ok:
# +++ create new published_instance.
                                # only save it when it is not a test
                                # file_name will be added after creating Ex-form
                                published_instance = None
                                published_pk = None
                                file_name = None

                                if not is_test:
                                    now_arr = upload_dict.get('now_arr')
                                    published_instance = create_published_instance(
                                        sel_examyear=sel_examyear,
                                        sel_school=sel_school,
                                        sel_department=sel_department,
                                        sel_level=sel_level,
                                        sel_examtype='',
                                        sel_examperiod=sel_examperiod,
                                        is_test=is_test,
                                        ex_form='ex6',
                                        now_arr=now_arr,
                                        request=request
                                    )
                                    if published_instance:
                                        published_pk = published_instance.pk
                                        file_name = published_instance.name

                                if logging_on:
                                    logger.debug('     published_pk: ' + str(published_pk))
                                    logger.debug('     file_name:    ' + str(file_name))

# +++ create Ex5_xlsx
                                if not is_test:
                # - get text from examyearsetting
                                    # just to prevent PyCharm warning on published_instance=published_instance
                                    # response = awpr_excel.create_ex2_ex2a_ex6_xlsx(
                                    if logging_on:
                                        logger.debug('     is_test: ' + str(is_test))

                # - get library from examyearsetting
                                    save_to_disk = True
                                    library = awpr_lib.get_library(sel_examyear, ['exform', 'ex6', 'gradelist'])
                                    ex_rows_dict, subject_dictlist_sorted = awpr_excel.create_ex6_rows_dict(
                                        sel_examyear, sel_school, sel_department, sel_level)

                                    # put name of req_usr in field chairperson or secretary.
                                    req_user = request.user
                                    requsr_usergroup_list = acc_prm.get_usergroup_list_from_user_instance(req_user)
                                    auth1_in_requsr_usergroups = 'auth1' in requsr_usergroup_list if requsr_usergroup_list else False
                                    auth2_in_requsr_usergroups = 'auth2' in requsr_usergroup_list if requsr_usergroup_list else False

                                    grades_auth_dict = {}
                                    if auth1_in_requsr_usergroups:
                                        grades_auth_dict['auth1'] = [req_user.last_name]  # value is a list
                                    elif auth2_in_requsr_usergroups:
                                        grades_auth_dict['auth2'] = [req_user.last_name]  # value is a list

                    # +++ create Ex6_xlsx
                                    response, saved_to_disk = awpr_excel.create_ex2_ex2a_ex6_xlsx(
                                        published_instance=published_instance,
                                        examyear=sel_examyear,
                                        school=sel_school,
                                        department=sel_department,
                                        ex_rows_dict=ex_rows_dict,
                                        grades_auth_dict=grades_auth_dict,
                                        level=sel_level,
                                        examperiod=c.EXAMPERIOD_FIRST,
                                        library=library,
                                        ex_form='ex6',
                                        save_to_disk=save_to_disk,
                                        request=request,
                                        user_lang=user_lang
                                    )

                                    msg_html = create_submit_ex5_ex6_saved_msg_html(
                                        saved_is_ok=saved_to_disk,
                                        is_ex6=True,
                                        published_instance=published_instance
                                    )

# - add  msg_html to update_wrap
        update_wrap['test_is_ok'] = test_is_ok
        if msg_html:
            update_wrap['approve_msg_html'] = msg_html
        if msg_dict:
            update_wrap['approve_msg_dict'] = msg_dict

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of GradeSubmitEx6View


def create_ex2_ex2a_msg_html(sel_department, sel_level, sel_examtype, count_dict, subj_not_published_list, authmissing_list, file_name, saved_to_disk, is_test, exform_txt): # PR2022-03-11
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('  ----- create_ex2_ex2a_msg_html -----')
        logger.debug('    count_dict: ' + str(count_dict))
        logger.debug('    is_test: ' + str(is_test))

    test_is_ok = False
    show_warning_novalue = False
    no_value = 0
    class_str = 'border_bg_transparent'

    msg_list = []

    cannot_submit_list = []
    skipped_list = []

    if is_test:
        count = count_dict.get('count', 0)
        committed = count_dict.get('committed', 0)
        no_value = count_dict.get('no_value', 0)
        exemption_no_value = count_dict.get('exemption_no_value', 0)

        already_published = count_dict.get('already_published', 0)
        auth_missing = count_dict.get('auth_missing', 0)
        already_approved = count_dict.get('already_approved', 0)
        double_approved = count_dict.get('double_approved', 0)
        secret_exam = count_dict.get('secret_exam', 0)
        studsubj_not_published = count_dict.get('studsubj_not_published', 0)
        blocked = count_dict.get('blocked', 0)
        composition_error = count_dict.get('composition_error', 0)

        if logging_on:
            logger.debug('    studsubj_not_published: ' + str(studsubj_not_published))

# - create line with 'only candidates of the learning path'
        if sel_department and sel_department.level_req:
            if sel_level and sel_level.abbrev:
                abbrev = sel_level.abbrev if sel_level.abbrev else '-'
                level_txt = ''.join((
                    gettext('The selection contains only %(cpt)s of the learning path: %(lvl_abbrev)s.')
                        % {'cpt': gettext('Candidates').lower(), 'lvl_abbrev': abbrev},
                    '<br>',
                    gettext("Select 'All learning paths' in the vertical gray bar on the left to submit all learning paths.")
                ))
            else:
                level_txt = ''.join((
                        '<b>', gettext('ATTENTION'), '</b>: ',
                        gettext('The selection contains the candidates of all learning paths.'), '<br>',
                        gettext('Select a learning path in the vertical gray bar on the left to submit one learning path.')
                ))
            msg_list.append(''.join(("<p class='pb-2'>", level_txt, '</p>')))

# - create line with 'The selection contains 39 subjects'
        # was: grade_score_txt = get_grade_text(count) if sel_examtype == 'se' else get_score_text(count)
        is_score = sel_examtype != 'se'
        grade_score_txt = get_grade_score_text(count, is_score)
        #count_txt = str(_("The selection contains %(val)s.") % {'val': grade_score_txt})
        count_txt = gettext("The selection contains %(val)s.") % {'val': grade_score_txt}
        msg_list.append(''.join(("<p class='pb-2'>", count_txt, '</p>')))

# - create line with 'composition not correct'
        if composition_error:
            is_are = gettext('is') if composition_error == 1 else gettext('are')
            cannot_submit_list.append(''.join(("<li>",
                                               gettext(
                                                   "There %(is_are)s %(val)s whose composition of the subjects is not correct.") % \
                                               {'is_are': is_are, 'val': get_grade_text(composition_error)},
                                               '<br>',
                                               gettext(
                                                   "Make the necessary corrections in the subject composition or contact the  Inspectorate."),
                                               '</li>')))

# - create line with 'not yet submitted in an additional Ex1 form' with list of students, if less than 25
        if studsubj_not_published:
            examperiod = 1
            studsubj_not_published_txt = str(_("%(val)s not yet submitted in an additional Ex1 form.") % \
                                   {'val': get_subjects_are_text(examperiod, studsubj_not_published)})

            if subj_not_published_list and len(subj_not_published_list) <= 25:
                for log_str in subj_not_published_list:
                    studsubj_not_published_txt += '<br>&emsp;&emsp;' + log_str

            submitE_ex1_form_txt = str(_("You have to submit an additional Ex1 form first, before you can submit the Ex2 form."))

            cannot_submit_list.append(''.join(("<li>",
                                     studsubj_not_published_txt,
                                     '<br>',
                                     submitE_ex1_form_txt,
                                     '</li>')))

# - create line with 'not fully approved'
        if auth_missing:
            auth_missing_txt = str(_("%(val)s not fully approved") % \
                                   {'val': get_grades_scores_are_text(auth_missing, is_score)})

            if authmissing_list and len(authmissing_list) <= 25:
                for log_str in authmissing_list:
                    auth_missing_txt += '<br>&emsp;&emsp;' + log_str

            exam_comm = _(' and examiner') if exform_txt == 'Ex2' else _(', examiner and corrector')

            if secret_exam:
                msg_txt = ',<br>'.join((
                    str(_("All grades must be approved by the chairperson, secretary%(exam_comm)s") % {'exam_comm': exam_comm}),
                    str(_("except for the designated exams, they will be approved by the Division of Examinations."))))
            else:
                msg_txt = str(_(
                    "All grades must be approved by the chairperson, secretary%(exam_comm)s.") % {
                                              'exam_comm': exam_comm})

            cannot_submit_list.append(''.join(("<li>",
                                     auth_missing_txt,
                                     '<br>',
                                     msg_txt,
                                     '</li>')))

        if cannot_submit_list:
            # msg_txt = "<div class='mx-2'>" + str(_("The %(cpt)s form can not be submitted") % {'cpt': exform_txt}) + ':</div><ul>'
            msg_txt = '<ul>'
            for txt in cannot_submit_list:
                msg_txt += txt
            msg_txt += '</ul>'
            if logging_on:
                logger.debug(' >>>>>>>> msg_txt: ' + str(msg_txt))
            msg_list.append(msg_txt)

        else:

            if committed:
                test_is_ok = True

            #if committed < count:
            #    msg_dict['skip_text'] = _("The following grades will be skipped:")

            if already_published:
                already_published_txt = str(_("%(val)s already submitted") % \
                                                     {'val': get_grades_scores_are_text(already_published, is_score)})
                skipped_list.append(''.join(("<li>", already_published_txt, '</li>')))

            if blocked:
                count_txt = get_grade_text(blocked) if sel_examtype == 'se' else get_score_text(blocked)
                if blocked == 1:
                    blocked_txt = str(_("%(val)s is unlocked by the Inspectorate") % {'val': count_txt})
                else:
                    blocked_txt = str(_("%(val)s are unlocked by the Inspectorate") % {'val': count_txt})
                skipped_list.append(''.join(("<li>", blocked_txt, '</li>')))

            if no_value:
                # was: count_txt = get_grade_text(no_value) if sel_examtype == 'se' else get_score_text(no_value)
                count_txt = get_grade_score_text(no_value, is_score)
                if no_value == 1:
                    no_value_txt = str(_("%(val)s has no value") % {'val': count_txt})
                else:
                    no_value_txt = str(_("%(val)s have no value") % {'val': count_txt})
                skipped_list.append(''.join(("<li>", no_value_txt, '</li>')))

            if exemption_no_value:
                # was: count_txt = get_grade_text(exemption_no_value) if sel_examtype == 'se' else get_score_text(exemption_no_value)
                count_txt = get_grade_score_text(exemption_no_value, is_score)
                se_ce = gettext('the CE score') if is_score else gettext('the SE grade')
                if exemption_no_value == 1:
                    no_value_txt = str(_("%(val)s is exemption, %(se_ce)s is not entered.") % \
                                       {'val': count_txt, 'se_ce': se_ce })
                else:
                    se_ce = gettext('the SE grades') if sel_examtype == 'se' else gettext('the CE scores')
                    no_value_txt = str(_("%(val)s are exemptions, %(se_ce)s are not entered.") % \
                                       {'val': count_txt, 'se_ce': se_ce })
                skipped_list.append(''.join(("<li>", no_value_txt, '</li>')))

            if is_test and double_approved:
                double_approved_txt = get_approved_text(double_approved, is_score) + str(_(', in a different function'))
                skipped_list.append(''.join(("<li>", double_approved_txt, '</li>')))

            if is_test and already_approved:
                already_approved_txt = get_approved_text(already_approved, is_score)
                skipped_list.append(''.join(("<li>", already_approved_txt, '</li>')))

            if skipped_list:

                #msg_list.append(''.join(("<p class='pb-2'>",
                #                         str(_("The following grades will be skipped:")),
                #                         '</p><ul>')))
                msg_list.append('<ul>')
                msg_list.extend(skipped_list)
                msg_list.append('</ul>')

            msg_list.append('<p>')
            if not committed:
                class_str = 'border_bg_invalid'
                msg_list.append(gettext("The %(frm)s form can not be submitted.") % {'frm': exform_txt })
            elif committed == 1:
                class_str = 'border_bg_valid'
                sc_gr = gettext('score') if is_score else gettext('grade')
                msg_list.append(gettext("One %(sc_gr)s will be added to the %(frm)s form.") % \
                                {'frm': exform_txt, 'sc_gr': sc_gr})
            else:
                class_str = 'border_bg_valid'
                sc_gr = gettext('scores') if is_score else gettext('grades')
                msg_list.append(gettext("%(val)s %(sc_gr)s will be added to the %(frm)s form.") % \
                                         {'frm': exform_txt, 'val': committed, 'sc_gr': sc_gr})
            msg_list.append('</p>')

    # - warning if any subjects are not fully approved
            if no_value:
                show_warning_novalue = True

        if studsubj_not_published or composition_error or auth_missing:
            class_str = 'border_bg_invalid'
            msg_list.append(''.join(("<p>", str(_("The %(frm)s form can not be submitted.") % {'frm': exform_txt}), '</p>')))

            if logging_on:
                logger.debug('  +++ class_str: ' + str(class_str))

        elif test_is_ok:
            class_str = 'border_bg_valid'
            msg_list.append(''.join(("<p>", str(_("The %(frm)s form can be submitted.") % {'frm': exform_txt}), '</p>')))

        if logging_on:
            logger.debug('  ????  class_str: ' + str(class_str))

# +++++ if not is_test +++++
    else:
        saved = count_dict.get('saved', 0)
        if not saved:
            class_str = 'border_bg_invalid'
            msg_list.append(gettext("The %(frm)s form has not been submitted.") % {'frm': exform_txt })

        else:
            class_str = 'border_bg_valid'
            test_is_ok = True
            if saved == 1:
                msg_list.append( ' '.join((str(_("The %(frm)s form has been submitted.") % {'frm': exform_txt }),
                                                   str(_("It contains 1 grade.")))))
            else:
                msg_list.append(' '.join((str(_("The %(frm)s form has been submitted.") % {'frm': exform_txt}),
                                                   str(_("It contains %(val)s grades.") % {'val': saved}))))
            if file_name:
                msg_list.append(''.join(('<br>',
                    str(_("The %(frm)s form has been saved as '%(val)s'.") % {'frm': exform_txt, 'val': file_name}),
                    '<br>',
                    str(_("Go to the page 'Archive' to download the file."))
                )))

    if logging_on:
        logger.debug('   msg_list: ' + str(msg_list))
        logger.debug('   class_str: ' + str(class_str))

    msg_html = ''.join((
            "<div class='p-2 ", class_str, "'>",
            ''.join(msg_list),
            '</div>'
    ))

# - warning if any subjects are not fully approved
    if show_warning_novalue:
        msg_html += get_warning_no_value(no_value)

    if logging_on:
        logger.debug('msg_html: ' + str(msg_html))
        logger.debug('test_is_ok: ' + str(test_is_ok))

    return msg_html, test_is_ok
# - end of create_ex2_ex2a_msg_html


def create_submit_ex5_test_msg_html(sel_department, sel_level, log_list, test_is_ok):
    # PR2022-06-12 PR2023-06-15
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('  ----- create_submit_ex5_test_msg_html -----')

    msg_list = []

    if not test_is_ok:
        class_str = 'border_bg_invalid'
        auth_missing_txt = '<br>'.join((_("The %(frm)s form can not be submitted.") % {'frm': 'Ex5'},
                                       str(_("The following grades are not fully approved:"))))
        for log_str in log_list:
            auth_missing_txt += '<br>&emsp;&emsp;' + log_str
        msg_list.append(auth_missing_txt)
    else:
        class_str = 'border_bg_valid'
        saved_text = str(_("All grades are fully approved."))
        saved_text += '<br>' + _("The %(cpt)s form can be submitted.") % {'cpt': 'Ex5' }
        msg_list.append(saved_text)

    msg_html = ''.join((
            "<div class='p-2 ", class_str, "'>",
            ''.join(msg_list),
            '</div>'
    ))
    # - create line with 'only candidates of the learning path'
    if sel_department and sel_department.level_req:
        if sel_level and sel_level.abbrev:
            abbrev = sel_level.abbrev if sel_level.abbrev else '-'
            level_txt = ''.join((
                gettext('The selection contains only candidates of the learning path'), ' <b>', abbrev,
                '</b>.<br>',
                gettext(
                    "Select 'All learning paths' in the vertical gray bar on the left to submit all learning paths.")
            ))
        else:
            level_txt = ''.join((
                '<b>', gettext('ATTENTION'), '</b>: ',
                gettext('The selection contains the candidates of all learning paths.'), '<br>',
                gettext('Select a learning path in the vertical gray bar on the left to submit one learning path.')
            ))
        msg_html += ''.join(("<div class='mt-2 p-2 border_bg_warning'>", level_txt, '</div>'))

    return msg_html
# - end of create_submit_ex5_test_msg_html


def create_submit_ex5_ex6_saved_msg_html(saved_is_ok, is_ex6, published_instance):
    # PR2022-06-12 PR2023-06-15 PR2023-09-03
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('  ----- create_submit_ex5_ex6_saved_msg_html -----')

    msg_list = []
    ex_form = 'Ex6' if is_ex6 else 'Ex5'
    if not saved_is_ok:
        class_str = 'border_bg_invalid'
        msg_list.append(gettext("The %(frm)s form has not been submitted.") % {'frm': ex_form })
    else:

        published_instance_filename = ''
        published_instance_file_url = ''
        if published_instance:
            published_instance_filename = published_instance.filename
            if published_instance.file:
                published_instance_file_url = published_instance.file.url

        class_str = 'border_bg_valid'
        msg_list.extend((
            gettext("The %(frm)s form has been submitted.") % {'frm': ex_form}, ' ',
            gettext("Click <a href='%(href)s' class='awp_href' target='_blank'>here</a> to download it.")
            % {'href': published_instance_file_url},
            '<br>',
            gettext("It has been saved in the page 'Archive' as '%(frm)s'.")
            % {'frm': published_instance_filename},
        ))

    msg_html = ''.join((
            "<div class='p-2 ", class_str, "'>",
            ''.join(msg_list),
            '</div>'
    ))
    if logging_on:
        logger.debug('    msg_html: ' + str(msg_html))

    return msg_html
# - end of create_submit_ex5_ex6_saved_msg_html


def create_published_instance(sel_examyear, sel_school, sel_department, sel_level,
                              sel_examtype, sel_examperiod, is_test, ex_form, now_arr, request):
    # PR2021-01-21 PR2022-04-21 PR2023-08-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_published_instance ----- ')

    # ex_form = 'ex2', 'ex2a', 'ex5', 'ex6', 'wolf'
    exform_capitalized = ex_form.capitalize() if ex_form else '---'

    # create new published_instance and save it when it is not a test
    depbase_code = sel_department.base.code if sel_department.base.code else '-'

    school_code = sel_school.base.code if sel_school.base.code else '-'
    school_abbrev = sel_school.abbrev if sel_school.abbrev else '-'

    if logging_on:
        logger.debug('depbase_code: ' + str(depbase_code))
        logger.debug('school_code: ' + str(school_code))
        logger.debug('school_abbrev: ' + str(school_abbrev))

    examtype_caption = None

    if ex_form == 'ex2a':
        if sel_examperiod == 2:
            examtype_caption = sel_examtype.upper() + '-tv2'
        elif sel_examperiod == 3:
            examtype_caption = sel_examtype.upper() + '-tv3'
        else:
            examtype_caption = sel_examtype.upper() + '-tv1'

    file_extension = '.xlsx'

    if logging_on:
        logger.debug('examtype_caption: ' + str(examtype_caption))

    # PR2021-04-28 get now_formatted from client
    # was:
    #today_iso = today_date.isoformat()
    #now = timezone.now()
    #now_iso = now.isoformat()

    today_date = af.get_date_from_arr(now_arr)

    #year_str = str(now_arr[0])
    #month_str = ("00" + str(now_arr[1]))[-2:]
    #date_str = ("00" + str(now_arr[2]))[-2:]
    #hour_str = ("00" + str(now_arr[3]))[-2:]
    #minute_str = ("00" +str( now_arr[4]))[-2:]
    #now_formatted = ''.join([year_str, "-", month_str, "-", date_str, " ", hour_str, "u", minute_str])

    now_formatted = af.get_now_formatted_from_now_arr(now_arr)
    filename_list = [exform_capitalized, school_code, school_abbrev]
    if depbase_code:
        filename_list.append(depbase_code)
    if sel_level:
        filename_list.append(sel_level.base.code)
    if examtype_caption:
        filename_list.append(examtype_caption)
    filename_list.append(now_formatted)
    file_name = ' '.join(filename_list)

    # skip school_abbrev if total file_name is too long
    if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
        file_name = ' '.join((ex_form, school_code, depbase_code, examtype_caption, now_formatted))
    # if total file_name is still too long: cut off
    if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
        file_name = file_name[0:c.MAX_LENGTH_FIRSTLASTNAME]
    file_name += file_extension

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
        #file_dir = '/'.join((country_abbrev, examyear_str, requsr_schoolcode, 'exfiles'))
        #file_path = '/'.join((file_dir, published_instance.filename))
        file_name = published_instance.name

        published_instance.filename = file_name
        published_instance.save(request=request)
        if logging_on:
            logger.debug('saved published_instance: ' + str(published_instance))
            logger.debug('saved published_instance.pk: ' + str(published_instance.pk))

    return published_instance
# - end of create_published_instance

#$$$$$$$$$$$$$$$$$$$$$$$$$$$


def create_published_instance_gradelist_diploma(sel_examyear, sel_school, sel_department, lvlbase_code, student_pk,
                              lastname_initials, regnumber, save_to_disk, is_diploma, now_arr, request):
    # PR2023-06-17
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_published_instance_gradelist_diploma ----- ')

    # TODO add field 'doctype' to table schools_published instead of filtering by name PR2023-04-18

    # create new published_instance and save it when it is not a test
    form_name = 'dp' if is_diploma else 'gl'

    depbase_code = sel_department.base.code if sel_department.base.code else '-'
    if lvlbase_code:
        depbase_code += ' ' + lvlbase_code

    school_abbrev = sel_school.abbrev if sel_school.abbrev else '-'

    examyear = str(sel_examyear.code) if sel_examyear.code else '-'

    today_date = af.get_date_from_arr(now_arr)
    now_formatted = af.get_now_formatted_from_now_arr(now_arr)

    file_name = ' '.join((
        lastname_initials,
        form_name,
        depbase_code,
        examyear,
        school_abbrev,
        now_formatted
    ))
    if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
        file_name = file_name[0:c.MAX_LENGTH_FIRSTLASTNAME]

    file_extension = '.pdf'
    filename_ext = file_name + file_extension

    if logging_on:
        logger.debug('filename_ext: ' + str(filename_ext))

    published_instance = stud_mod.DiplomaGradelist(
        student_id=student_pk,
        regnumber=regnumber,
        doctype=form_name,
        name=file_name,
        filename=filename_ext,
        datepublished=today_date
    )

    # Note: filefield 'file' gets value on creating Ex form
    if save_to_disk:
        published_instance.save(request=request)
        if logging_on:
            logger.debug('saved published_instance: ' + str(published_instance))
            logger.debug('saved published_instance.pk: ' + str(published_instance.pk))

    return published_instance
# - end of create_published_instance_gradelist_diploma


def create_published_diplomagradelist_rows(sel_school, sel_department):
    # --- create rows of published records PR2021-01-21 PR2022-09-16 PR2023-04-19
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_published_diplomagradelist_rows -----')

    # can't use sql because of file field > create mapped_dict to add url's, so you can use sql

    published_diplomagradelist_rows = []

# - create dict with urls
    mapped_urls_dict = {}

    rows = stud_mod.DiplomaGradelist.objects.filter(
        student__school=sel_school,
        student__department=sel_department
    )
    for row in rows:

        if row.file:
            file_url = row.file.url

            # PR2022-06-12 There a a lot of published_instances saved without file_url
            # that should not happen, but it does. I don't know why.Check out TODO
            # for now: filter on file_url
            if file_url:
                mapped_urls_dict[row.pk] = file_url

    # don't filter on deleted students
    sub_sql = ''.join((
        "SELECT dpgl.student_id, dpgl.doctype, ",
        "ARRAY_AGG(dpgl.id ORDER BY dpgl.id DESC) AS dpgl_id_arr ",

        "FROM students_diplomagradelist AS dpgl ",
        "INNER JOIN students_student AS stud ON (stud.id = dpgl.student_id) ",
        "WHERE stud.school_id=", str(sel_school.pk), "::INT ",
        "AND stud.department_id=", str(sel_department.pk), "::INT "
        "GROUP BY dpgl.student_id, dpgl.doctype"
    ))

    sql = ''.join(("WITH sub_sql AS (", sub_sql, ") ",
            "SELECT dpgl.id, ",
            "stud.lastname, stud.firstname, stud.prefix, sub_sql.dpgl_id_arr, "
            "dpgl.regnumber, dpgl.name AS dpgl_name, dpgl.doctype, dpgl.datepublished, dpgl.modifiedat, ",
            "au.last_name AS modby_username ",

            "FROM students_diplomagradelist AS dpgl ",
            "INNER JOIN students_student AS stud ON (stud.id = dpgl.student_id) ",
            "LEFT JOIN sub_sql ON (sub_sql.student_id = dpgl.student_id AND sub_sql.doctype = dpgl.doctype) ",
            "LEFT JOIN accounts_user AS au ON (au.id = dpgl.modifiedby_id) ",

            "WHERE stud.school_id=", str(sel_school.pk), "::INT ",
            "AND stud.department_id=", str(sel_department.pk), "::INT "
    ))

    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = af.dictfetchall(cursor)

    if rows:
        for row in rows:
            dpgl_id = row.get('id')
            file_url = mapped_urls_dict.get(dpgl_id)

            full_name = stud_fnc.get_full_name(row.get('lastname'), row.get('firstname'), row.get('prefix'))

            dpgl_id_arr = row.get('dpgl_id_arr') or []

            has_multiple_dpgl, is_latest_dpgl = False, False
            if len(dpgl_id_arr) > 1:
                has_multiple_dpgl = True
                if dpgl_id_arr[0] == dpgl_id:
                    is_latest_dpgl = True
            else:
                is_latest_dpgl = True

            dict = {
                'id': dpgl_id,
                'mapid': 'diplomagradelist_' + str(dpgl_id),
                'full_name': full_name,
                'dpgl_name': row.get('dpgl_name'),
                'regnumber': row.get('regnumber'),
                'doctype': row.get('doctype'),
                'datepublished': row.get('datepublished'),
                'dpgl_id_arr': row.get('dpgl_id_arr'),
                'has_multiple_dpgl': has_multiple_dpgl,
                'is_latest_dpgl': is_latest_dpgl,
                'selected': is_latest_dpgl,  # to enable showing multiple dpgl
                'url': file_url,
                'modifiedby': row.get('modby_username'),
                'modifiedat': row.get('modifiedat')
            }
            published_diplomagradelist_rows.append(dict)

    if logging_on:
        logger.debug('saved published_diplomagradelist_rows: ' + str(published_diplomagradelist_rows))
    return published_diplomagradelist_rows
# --- end of create_published_diplomagradelist_rows



#$$$$$$$$$$$$$$$$$$$$$$$$$$$
def get_grade_score_text(count, is_score):
    return get_score_text(count) if is_score else get_grade_text(count)


def get_score_text(count):
    return gettext('no scores') if not count else gettext('1 score') if count == 1 else ' '.join((str(count), gettext('scores')))


def get_grade_text(count):
    return gettext('no grades') if not count else gettext('1 grade') if count == 1 else ' '.join((str(count), gettext('grades')))


def get_grades_scores_are_text(count, is_score):
    return get_scores_are_text(count) if is_score else get_grades_are_text(count)


def get_grades_are_text(count):
    return gettext('no grades are') if not count else gettext('1 grade is') if count == 1 else ' '.join((str(count), gettext('grades are')))


def get_scores_are_text(count):
    return gettext('no scores are') if not count else gettext('1 score is') if count == 1 else ' '.join((str(count), gettext('scores are')))

def get_subjects_are_text(examperiod, count):
    if not count:
        msg_text = gettext('no subjects are') if examperiod == 1 else gettext('no re-examinations are')
    elif count == 1:
        msg_text = gettext('1 subject is') if examperiod == 1 else gettext('1 re-examination is')
    else:
        subjects_txt = gettext('subjects are') if examperiod == 1 else gettext('re-examinations are')
        msg_text = ' '.join((str(count), subjects_txt))
    return msg_text


def get_approved_text(count, is_score):
    if count == 1:
        cpt = gettext('Score').lower() if is_score else gettext('Grade').lower()
        msg_text = gettext('1 %(cpt)s is already approved') % {'cpt': cpt}
    else:
        cpts = gettext('Scores').lower() if is_score else gettext('Grades').lower()
        msg_text = str(count) + gettext(' %(cpts)s are already approved') % {'cpts': cpts}
    return msg_text


def get_approved_by_you_text(count, is_score):
    if count == 1:
        cpt = gettext('Score').lower() if is_score else gettext('Grade').lower()
        msg_text = gettext('1 %(cpt)s is already approved by you') % {'cpt': cpt}
    else:
        cpts = gettext('Scores').lower() if is_score else gettext('Grades').lower()
        msg_text = str(count) + gettext(' %(cpts)s are already approved by you') % {'cpts': cpts}
    return msg_text


def get_grades_tobe_updated(grade_row, tobe_updated_list, sel_examtype, requsr_auth, auth_index, is_test, is_reset, count_dict, request):
    # PR2021-01-19 PR2022-03-08
    # auth_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
    # PR2022-03-08 this one will replace approve_grade
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_grades_tobe_updated -----')
        logger.debug('     sel_examtype: ' + str(sel_examtype))
        logger.debug('     requsr_auth:  ' + str(requsr_auth) + ' ' + str(type(requsr_auth)))
        logger.debug('     is_reset:     ' + str(is_reset))
        logger.debug('     grade_row:     ' + str(grade_row))

    af.add_one_to_count_dict(count_dict, 'count')

    if grade_row and sel_examtype and sel_examtype in ('se', 'sr', 'pe', 'ce'):
        req_usr = request.user
        grade_pk = grade_row.get('id')

# - skip if this grade/examtype is already published
        # create_grade_approve_rows selects only the info from the selected examtype
        # i.e.: grd.se_published_id AS published_id, '
        published_id = grade_row.get('published_id')
        is_blocked = grade_row.get('blocked')
        if logging_on:
            logger.debug('   published_id:    ' + str(published_id))

        if published_id:
            af.add_one_to_count_dict(count_dict, 'already_published')
        else:

            requsr_authby_field = sel_examtype + '_' + requsr_auth + 'by_id'

# - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved
            auth1by_id = grade_row.get('auth1by_id')
            auth2by_id = grade_row.get('auth2by_id')
            auth3by_id = grade_row.get('auth3by_id')
            auth4by_id = grade_row.get('auth4by_id')

            if logging_on:
                logger.debug(' .. requsr_authby_field: ' + str(requsr_authby_field))
                logger.debug('    auth1by_id:      ' + str(auth1by_id))
                logger.debug('    auth2by_id:      ' + str(auth2by_id))
                logger.debug('    auth3by_id:      ' + str(auth3by_id))
                logger.debug('    auth4by_id:      ' + str(auth4by_id))

            save_changes = False

# - remove authby when is_reset
            if is_reset:
                af.add_one_to_count_dict(count_dict, 'reset')
                save_changes = True
            else:

# - skip if this grade is already approved
                requsr_authby_id = grade_row.get(requsr_auth + 'by_id')
                requsr_authby_field_already_approved = True if requsr_authby_id else False
                if logging_on:
                    logger.debug('  > requsr_authby_field_already_approved: ' + str(requsr_authby_field_already_approved))

                if requsr_authby_field_already_approved:
                    af.add_one_to_count_dict(count_dict, 'already_approved')
                else:

# - skip if this author (like 'chairperson') has already approved this grade
        # under a different permit (like 'secretary' or 'corrector')
                    # chairperson cannot also approve as secretary or as corrector
                    # secretary cannot also approve as chairperson or as corrector
                    # examiner cannot also approve as corrector
                    # corrector cannot also approve as chairperson, secretary or examiner

                    # PR2023-04-10 debug. there are se-grades with approval of corrector. To prevent double approval notcie, skip corrector in se grade
                    double_approved = False
                    if requsr_auth == 'auth1':
                        double_approved = (auth2by_id and auth2by_id == req_usr.pk or sel_examtype in ('pe', 'ce') and auth4by_id and auth4by_id == req_usr.pk)
                    elif requsr_auth == 'auth2':
                        double_approved = (auth1by_id and auth1by_id == req_usr.pk or sel_examtype in ('pe', 'ce') and auth4by_id and auth4by_id == req_usr.pk)
                    elif requsr_auth == 'auth3':
                        double_approved = (sel_examtype in ('pe', 'ce') and auth4by_id and auth4by_id == req_usr.pk)
                    elif requsr_auth == 'auth4':
                        double_approved = (auth1by_id and auth1by_id == req_usr.pk) or (auth2by_id and auth2by_id == req_usr.pk) or (auth3by_id and auth3by_id == req_usr.pk)

                    if logging_on:
                        logger.debug('  > double_approved: ' + str(double_approved))

                    if double_approved:
                        af.add_one_to_count_dict(count_dict, 'double_approved')
                    else:
                        is_secret_exam = grade_row.get('secret_exam') or False

    # skip if this is a secret_exam, is ce and requsr is not admin
                        # or when se / sr and authindex = commissioner
                        if is_secret_exam and sel_examtype == 'ce' and request.user.role != c.ROLE_064_ADMIN:
                            af.add_one_to_count_dict(count_dict, 'is_secret_exam')
                            if logging_on:
                                logger.debug('  > is_secret_exam: ' + str(is_secret_exam))
                        else:

    # skip if this grade has no value - not when deleting approval
                            # PR2022-03-11 after tel with Nancy Josephina: blank grades can also be approved, give warning first
                            # PR2022-05-31 afte corrector has blocked all empty scores by approving: skip approve when empty

                            has_value = grade_row.get('has_value', False)

                            if not has_value:
                                af.add_one_to_count_dict(count_dict, 'no_value')
                                if logging_on:
                                    logger.debug('  > no_value   : ' + str(not has_value))
                            else:
                                if logging_on:
                                    logger.debug('  > has_value   : ' + str(has_value))
                                # add pk and req_usr.pk to tobe_updated_list
                                save_changes = True
                                if logging_on:
                                    logger.debug('  > save_changes: ' + str(save_changes))

# - set value of requsr_authby_field
            if save_changes:
                if is_test:
                    af.add_one_to_count_dict(count_dict, 'committed')
                else:
                    af.add_one_to_count_dict(count_dict, 'saved')

                    saved_status_sum = grade_row.get('status')

                    new_auth_id = req_usr.pk if not is_reset else None
                    if requsr_auth == 'auth1':
                        auth1by_id = new_auth_id
                    elif requsr_auth == 'auth2':
                        auth2by_id = new_auth_id
                    elif requsr_auth == 'auth3':
                        auth3by_id = new_auth_id
                    elif requsr_auth == 'auth4':
                        auth4by_id = new_auth_id

# calculate status_sum from auth_id, not by changing saved status_sum
                    # new way of calculating:  create sum based on auth_id, not on saved sum. Like:
                    # was: new_value_bool = True if not is_reset else False
                    #      new_status_sum = af.set_status_sum_by_index(saved_status_sum, auth_index, new_value_bool)
                    new_status_sum = af.get_status_sum(auth1by_id, auth2by_id, auth3by_id, auth4by_id, published_id, is_blocked)

                    # add pk and authby_id to tobe_updated_list
                    tobe_updated = [grade_pk, new_auth_id, new_status_sum]
                    tobe_updated_list.append(tobe_updated)

                    if logging_on:
                        logger.debug('     is_reset:     ' + str(is_reset))
                        logger.debug('     auth_index:   ' + str(auth_index))
                        logger.debug('     saved_st_sum: ' + str(saved_status_sum))
                        logger.debug('     new_st_sum:   ' + str(new_status_sum))
                        logger.debug('     tobe_updated: ' + str(tobe_updated))

# - end of get_grades_tobe_updated


def calc_grade_rows_tobe_updated(grade_row, tobe_updated_list, sel_examperiod, sel_examtype, is_sxm, is_test, count_dict):
    # PR2022-03-09 PR2022-04-17 PR2022-06-03 PR2023-02-23
    # only called by GradeSubmitEx2Ex2aView
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- calc_grade_rows_tobe_updated -----')
        logger.debug('     sel_examperiod: ' + str(sel_examperiod))
        logger.debug('     sel_examtype:   ' + str(sel_examtype))
        logger.debug('     grade_row:      ' + str(grade_row))

    """
    grade_row:  {
        'id': 48685, 'examperiod': 2, 'studsubj_id': 20702, 'cluster_id': 967, 
        'has_exemption': False, 'secret_exam': True, 
        'subjbase_id': 114, 'lvlbase_id': 4, 'depbase_id': 1, 'schoolbase_id': 4, 
        'auth1by_id': None, 'auth2by_id': 498, 'auth3by_id': None, 'auth4by_id': None, 'published_id': None, 'blocked': False, 
        'has_value': True, 
        'pescore': None, 'cescore': 24, 'segrade': '7.4', 'srgrade': None, 'sesrgrade': '7.4', 
        'pegrade': None, 'cegrade': None, 'pecegrade': None, 'finalgrade': None, 'status': 4, 
        'stud_name': 'Ahoua, Candy Kimberly', 'subj_name': 'Engelse taal'}
    """
    subj_not_published_txt, authmissing_txt = None, None

    af.add_one_to_count_dict(count_dict, 'count')

    if grade_row and sel_examtype and sel_examtype in ('se', 'sr', 'pe', 'ce'):

        grade_pk = grade_row.get('id')
        # has_exemption = studsubj.has_exemption
        has_exemption = grade_row.get('has_exemption') or False
        is_secret_exam = grade_row.get('secret_exam') or False
        composition_error = grade_row.get('composition_error') or False
        studsubj_not_published = grade_row.get('studsubj_not_published') or False
        is_blocked = grade_row.get('blocked') or False

        if logging_on:
            logger.debug('     composition_error: ' + str(composition_error))

        # add no_value to count here to add to msg also when grade is already published, but set add_to_update_list further
        has_value = grade_row.get('has_value', False)
        if not has_value:
            # TODO remove skip when has_exemp. Maybe this is still here because empty scores had to be approved. Can be deleted?
            if has_exemption:
                af.add_one_to_count_dict(count_dict, 'exemption_no_value')
            else:
                af.add_one_to_count_dict(count_dict, 'no_value')
                if logging_on:
                    logger.debug('     has_value   : ' + str(has_value))
                    logger.debug('     grade_row:      ' + str(grade_row))

# - count studsubj_not_published
        if studsubj_not_published:
            af.add_one_to_count_dict(count_dict, 'studsubj_not_published')
            subj_not_published_txt = ' - '.join((grade_row.get('stud_name', '-'), grade_row.get('subj_name', '-')))

# - count is_blocked
        if is_blocked:
            af.add_one_to_count_dict(count_dict, 'blocked')

# - count secret_exams
        if is_secret_exam:
            af.add_one_to_count_dict(count_dict, 'secret_exam')

 # - skip if composition error - only on Curacao for now PR2023-02-12
        if composition_error and not is_sxm:
            af.add_one_to_count_dict(count_dict, 'composition_error')
            if logging_on:
                logger.debug('     composition_error: ' + str(composition_error))

        else:

# - skip if this grade/examtype is already published
            published_id = grade_row.get( 'published_id')

            if published_id:
                af.add_one_to_count_dict(count_dict, 'already_published')
                if logging_on:
                    logger.debug('     already_published published_id: ' + str(published_id))
            else:
                add_to_update_list = False

    # skip if this grade has no value
        # PR2022-03-11 after tel with Nancy Josephina: blank grades can also be approved, give warning first
        # PR2022-05-31 after corrector has blocked all empty scores by approving: skip approve when empty
                has_value = grade_row.get('has_value', False)

                if not has_value:

    # add empty grades and exemptions to Ex2 form
            # PR2023-07-03 don't add published_id when grade has no value
                    # was: add_to_update_list = True
                    pass
                else:
                    auth1by_id = grade_row.get('auth1by_id')
                    auth2by_id = grade_row.get('auth2by_id')
                    auth3by_id = grade_row.get('auth3by_id')
                    auth4by_id = grade_row.get('auth4by_id')

        # - skip if this grade / examtype is not approved by all auth
                    # Ex2 and Ex2A must always be approved by  auth1 and auth2
                    auth_missing = auth1by_id is None or auth2by_id is None

                    # TODO change when submitting exemption grades (NIU yet)
                    if not auth_missing:
                        # se_grade must also be approved by  auth3
                        # sel_examtypes are : 'se', 'sr', 'pe', 'ce'
                        if sel_examtype in ('se', 'sr'):
                            auth_missing = auth3by_id is None
                        else:
                            # secret_exam does not have to be approved by auth3
                            if not is_secret_exam:
                                auth_missing = auth3by_id is None

                    if not auth_missing:
                        if sel_examperiod != c.EXAMPERIOD_EXEMPTION:
                            if sel_examtype in ('pe', 'ce'):
                                if not is_secret_exam:
                                    auth_missing = auth4by_id is None

                    if auth_missing:
                        af.add_one_to_count_dict(count_dict, 'auth_missing')
                        authmissing_txt = ' - '.join((grade_row.get('stud_name', '-'), grade_row.get('subj_name', '-')))
                        if logging_on:
                            logger.debug('     authmissing_txt: ' + str(authmissing_txt))
                            logger.debug('     grade_pk: ' + str(grade_pk))
                    else:

        # - check if all auth are different
                        # chairperson cannot also approve as secretary or as corrector
                        # secretary cannot also approve as chairperson or as corrector
                        # examiner cannot also approve as corrector
                        # corrector cannot also approve as chairperson, secretary or examiner
                        # in Python None == None = True, therefore add: auth1by_id and ...
                        #PR2023-04-11 there was a se grade with auth4by_id value, gave double_approved.
                        # don't know why, skip auth4by_id when se

                        double_approved = (auth1by_id and auth1by_id == auth2by_id)
                        if not double_approved and sel_examtype in ('ce', 'pe'):
                            double_approved = (auth1by_id and auth1by_id == auth4by_id) or \
                                              (auth2by_id and auth2by_id == auth4by_id) or \
                                              (auth3by_id and auth3by_id == auth4by_id)
                        if logging_on:
                            logger.debug('   double_approved: ' + str(double_approved))
                            logger.debug('     auth1by_id: ' + str(auth1by_id))
                            logger.debug('     auth2by_id: ' + str(auth2by_id))
                            logger.debug('     auth3by_id: ' + str(auth3by_id))
                            logger.debug('     auth4by_id: ' + str(auth4by_id))

                        if double_approved:
                            af.add_one_to_count_dict(count_dict, 'double_approved')

                        else:
                            add_to_update_list = True

        # - set value of published_instance and examtype_status field
                if add_to_update_list:
                    if is_test:
                        af.add_one_to_count_dict(count_dict, 'committed')
                    else:
                        af.add_one_to_count_dict(count_dict, 'saved')

                        # add grade_pk to tobe_updated_list
                        # new_published_id, new_status_sum don't have to be added, they are always the same
                        #   new_published_id = published_instance.pk if published_instance else None
                        #   new_status_sum = c.STATUS_05_PUBLISHED
                        tobe_updated_list.append(grade_pk)

    return subj_not_published_txt, authmissing_txt
# - end of calc_grade_rows_tobe_updated


def approve_single_grade(grade, sel_examtype, requsr_auth, auth_index, is_test, is_reset, count_dict, request):  # PR2021-01-19 PR2022-03-07
    # auth_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- approve_single_grade -----')
        logger.debug('     sel_examtype: ' + str(sel_examtype))
        logger.debug('     requsr_auth:  ' + str(requsr_auth) + ' ' + str(type(requsr_auth)))
        logger.debug('     is_reset:     ' + str(is_reset))

    if grade and sel_examtype and sel_examtype in ('se', 'sr', 'pe', 'ce'):
        req_usr = request.user

# - skip if this grade / examtype is already published
        published = getattr(grade, sel_examtype + '_published')
        if logging_on:
            logger.debug('     published:    ' + str(published))

        if published:
            af.add_one_to_count_dict(count_dict, 'already_published')
        else:

# skip if this grade has no value - not when deleting approval
    # PR2022-03-11 after tel with Nancy Josephina: blank grades can also be approved, give warning first
            grade_value = getattr(grade, sel_examtype + 'grade')
            score_value = None
            if sel_examtype in ('pe', 'ce'):
                score_value = getattr(grade, sel_examtype + 'score')
            no_value = grade_value is None and score_value is None and not is_reset
            if no_value:
                af.add_one_to_count_dict(count_dict, 'no_value')

            requsr_authby_field = sel_examtype + '_' + requsr_auth + 'by'

# - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved

            auth1by = getattr(grade, sel_examtype + '_auth1by')
            auth2by = getattr(grade, sel_examtype + '_auth2by')
            auth3by = getattr(grade, sel_examtype + '_auth3by')
            auth4by = getattr(grade, sel_examtype + '_auth4by')

            if logging_on:
                logger.debug('     requsr_authby_field: ' + str(requsr_authby_field))
                logger.debug('     auth1by:      ' + str(auth1by))
                logger.debug('     auth2by:      ' + str(auth2by))
                logger.debug('     auth3by:      ' + str(auth3by))
                logger.debug('     auth4by:      ' + str(auth4by))

            double_approved = False
            save_changes = False

# - remove  authby when is_reset
            if is_reset:
                setattr(grade, requsr_authby_field, None)
                af.add_one_to_count_dict(count_dict, 'reset')
                save_changes = True
            else:

# - skip if this grade is already approved
                requsr_authby_value = getattr(grade, requsr_authby_field)
                requsr_authby_field_already_approved = True if requsr_authby_value else False
                if logging_on:
                    logger.debug('     requsr_authby_field_already_approved: ' + str(requsr_authby_field_already_approved))

                if requsr_authby_field_already_approved:
                    af.add_one_to_count_dict(count_dict, 'already_approved')
                else:

# - skip if this author (like 'chairperson') has already approved this grade
        # under a different permit (like 'secretary' or 'corrector')
                    # chairperson cannot also approve as secretary or as corrector
                    # secretary cannot also approve as chairperson or as corrector
                    # examiner cannot also approve as corrector
                    # corrector cannot also approve as chairperson, secretary or examiner
                    if requsr_auth == 'auth1':
                        double_approved = (auth2by and auth2by == req_usr or auth4by and auth4by == req_usr)
                    elif requsr_auth == 'auth2':
                        double_approved = (auth1by and auth1by == req_usr or auth4by and auth4by == req_usr)
                    elif requsr_auth == 'auth3':
                        double_approved = (auth4by and auth4by == req_usr)
                    elif requsr_auth == 'auth4':
                        double_approved = (auth1by and auth1by == req_usr) or (auth2by and auth2by == req_usr) or (auth3by and auth3by == req_usr)
                    if logging_on:
                        logger.debug('     double_approved: ' + str(double_approved))

                    if double_approved:
                        af.add_one_to_count_dict(count_dict, 'double_approved')
                    else:
                        setattr(grade, requsr_authby_field, req_usr)
                        save_changes = True
                        if logging_on:
                            logger.debug('     save_changes: ' + str(save_changes))

# - set value of requsr_authby_field
            if save_changes:
                if is_test:
                    af.add_one_to_count_dict(count_dict, 'committed')
                else:
                    af.add_one_to_count_dict(count_dict, 'saved')

                    saved_status_sum = getattr(grade, sel_examtype + '_status')

                    new_value_bool = True if not is_reset else False
                    new_status_sum = af.set_status_sum_by_index(saved_status_sum, auth_index, new_value_bool)

                    setattr(grade, sel_examtype + '_status', new_status_sum)

                    if logging_on:
                        logger.debug('     is_reset:         ' + str(is_reset))
                        logger.debug('     auth_index:     ' + str(auth_index))
                        logger.debug('     saved_status_sum: ' + str(saved_status_sum))
                        logger.debug('     new_status_sum:   ' + str(new_status_sum))

# - save changes
                    grade.save(request=request)
# - end of approve_single_grade


@method_decorator([login_required], name='dispatch')
class GradeUploadView(View):
    # PR2020-12-16 PR2021-01-15 PR2021-12-15 PR2022-01-24 PR2022-03-18 PR2022-05-25

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= GradeUploadView ============= ')
        # function updates grade records of current studentsubject PR2020-11-21
        # adding or deleting grades is done by StudentsubjectSingleUpdateView
        update_wrap = {}
        msg_list = []
        is_score = False

        req_usr = request.user

# - reset language
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

        if req_usr and req_usr.country and req_usr.schoolbase:

            try:

# - get upload_dict from request.POST
                upload_json = request.POST.get('upload', None)
                if upload_json:
                    upload_dict = json.loads(upload_json)
                    if logging_on:
                        logger.debug('    upload_dict: ' + str(upload_dict))

                    mode = upload_dict.get('mode')
                    page = upload_dict.get('page')
                    secret_exams_only = page == 'page_secretexam'

# - get permit
                    #permit_list, requsr_usergroups_listNIU, requsr_allowed_sections_dictNIU, requsr_allowed_clusters_arr = acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(
                    #    request, 'page_grade')
                    #has_permit = 'permit_crud' in permit_list

                    page_name = page if page else 'page_grade'
                    if 'approve' in mode:
                        # PR203-06-29 approve is only done in GradeApproveView
                        has_permit = False  # acc_prm.get_permit_of_this_page(page_name, 'approve_exam' ,request)
                    elif 'undo_submitted' in mode:
                        has_permit = acc_prm.get_permit_of_this_page(page_name, 'submit_exam' ,request)
                    else:
                        has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

                    if logging_on:
                        logger.debug('    page_name: ' + str(page_name))
                        logger.debug('    has_permit: ' + str(has_permit))
                        logger.debug('    mode: ' + str(mode))

                    if not has_permit:
                        msg_list.append(acc_prm.err_txt_no_permit())  # default: 'to perform this action')
                    else:

# - get selected examyear, school and department from usersettings
                        # may_edit = False when:
                        #  - country is locked,
                        #  - examyear is not found, not published or locked
                        #  - school is not found, not same_school, not activated, or locked
                        #  - department is not found, not in user allowed depbase or not in school_depbase
                        sel_examyear, sel_school, sel_department, sel_level, may_edit, err_list = \
                            acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                        if logging_on:
                            logger.debug('    sel_school: ' + str(sel_school))
                            logger.debug('    sel_department: ' + str(sel_department))

                        if err_list:
                            err_list.append(str(_('You cannot make changes.')))
                            msg_list.extend(err_list)
                        else:

# - get upload_dict variables
                            # get examperiod and examtype from upload_dict
                            # don't get it from usersettings, get it from upload_dict instead
                            # was: sel_examperiod, sel_examtype, sel_subject_pkNIU = acc_prm.get_selected_experiod_extype_subject_from_usersetting(request)

                            grade_pk = upload_dict.get('grade_pk')
                            examgradetype = upload_dict.get('examgradetype', '')
                            # 'examgradetype': 'segrade'

                            return_grades_with_exam = upload_dict.get('return_grades_with_exam', False)

        # when admin is entering secret exams, sel_school = school of admin. Skip getting student
                            grade = stud_mod.Grade.objects.get_or_none(pk=grade_pk)
                            student = grade.studentsubject.student if grade else None
                            student_school_is_correct = False

                            if logging_on:
                                logger.debug('    grade: ' + str(grade))
                                logger.debug('    student: ' + str(student))

        # - check if student is from requsr_school
                            if student:
                                if student.department == sel_department:
                                    if logging_on:
                                        logger.debug('    student.department == sel_department ')
                                    if page_name == 'page_secretexam':
                                        if req_usr.role == c.ROLE_064_ADMIN:
                                            student_school_is_correct = True
                                            if logging_on:
                                                logger.debug('    req_usr.role == c.ROLE_064_ADMIN ')
                                    else:
                                        if student.school.base == req_usr.schoolbase:
                                            student_school_is_correct = True
                                            if logging_on:
                                                logger.debug('    student.school.base == req_usr.schoolbase ')

        # - get current student from upload_dict, filter: sel_school, sel_department, student is not locked
                            if logging_on:
                                logger.debug('    student_school_is_correct: ' + str(student_school_is_correct))

                            if student_school_is_correct:
                                # student_subj_grade_dict is not in use, I think
                                #   examperiod_int = grade.examperiod
                                #   double_entrieslist = []
                                #   studsubj_pk = grade.studentsubject_id
                                #   student_subj_grade_dict =  grad_val.get_student_subj_grade_dict(sel_school, sel_department, examperiod_int, examgradetype, double_entrieslist, student_pk, studsubj_pk)

                                requsr_auth = None
                                auth_index = upload_dict.get('auth_index')
                                if auth_index:
                                    requsr_auth = 'auth' + str(auth_index)

                # +++ check if editing grade is allowed
                                # check if studsubj is tobedeleted
                                studsubj_tobedeleted = grade.studentsubject.tobedeleted or False

                                is_score = 'score' in examgradetype

                                # PR2022-04-06 <Marisela Cijntje Radulphus cannot edit grade:
                                # error: 'NoneType' object has no attribute 'base_id'
                                # cause: Havo/Vwo has no level
                                lvlbase_pk = grade.studentsubject.student.level.base_id if grade.studentsubject.student.level else None

                                userallowed_instance = acc_prm.get_userallowed_instance(request.user, sel_examyear)
                                userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
                                userallowed_cluster_pk_list = acc_prm.get_userallowed_cluster_pk_list(userallowed_instance)

                                # PR2024-05-30 filter on examyear_pk added
                                allowed_clusters_of_sel_school = acc_prm.get_allowed_clusters_of_sel_school(
                                    sel_schoolbase_pk=grade.studentsubject.student.school.base_id,
                                    sel_examyear_pk=grade.studentsubject.student.school.examyear_id,
                                    allowed_cluster_pk_list=userallowed_cluster_pk_list
                                )
                                is_allowed = grad_val.validate_grade_is_allowed(
                                    request=request,
                                    requsr_auth=requsr_auth,

                                    userallowed_sections_dict=userallowed_sections_dict,
                                    allowed_clusters_of_sel_school=allowed_clusters_of_sel_school,

                                    schoolbase_pk=grade.studentsubject.student.school.base_id,
                                    depbase_pk=grade.studentsubject.student.department.base_id,
                                    lvlbase_pk=lvlbase_pk,
                                    subjbase_pk=grade.studentsubject.schemeitem.subject.base_id,
                                    cluster_pk=grade.studentsubject.cluster_id,
                                    studsubj_tobedeleted=studsubj_tobedeleted,
                                    is_secret_exam=grade.ce_exam.secret_exam if grade.ce_exam else False,
                                    is_reset=False, # only used when approving
                                    msg_list=msg_list,
                                    is_score=is_score,
                                    is_grade_exam=return_grades_with_exam
                                )

                                if logging_on:
                                    logger.debug('    validate_grade_is_allowed: ' + str(is_allowed))
                                    logger.debug('    msg_list: ' + str(msg_list))

                                if is_allowed:

        # - get schemitem_info, separately, instead of getting from grade_instance, should be faster
                                    si_pk = grade.studentsubject.schemeitem_id
                                    schemeitems_dict = subj_vw.get_scheme_si_dict(
                                        examyear_pk=sel_examyear.pk if sel_examyear else None,
                                        depbase_pk=sel_department.base_id if sel_department else None,
                                        schemeitem_pk=si_pk)
                                    si_dict = schemeitems_dict.get(si_pk)

            # +++ update existing grade - not when grade is created - grade is None when deleted
                                    # undo_submitted means: undo submitted wolf exam (ce_exam)
                                    if mode in ('update', 'undo_submitted'):
                                        err_list = update_grade_instance(
                                            grade_instance=grade,
                                            upload_dict=upload_dict,
                                            sel_examyear=sel_examyear,
                                            sel_department=sel_department,
                                            si_dict=si_dict,
                                            request=request
                                        )
                                    if err_list:
                                        msg_list.extend(err_list)

                                    if logging_on:
                                        logger.debug('    student: ' + str(student))
                                        logger.debug('    grade: ' + str(grade))

                    # - add update_dict to update_wrap
                                grade_rows = []
                                if return_grades_with_exam:
                                    rows = create_grade_with_exam_rows(
                                        sel_examyear=sel_examyear,
                                        sel_schoolbase=sel_school.base if sel_school else None,
                                        sel_depbase=sel_department.base if sel_department else None,
                                        sel_lvlbase=sel_level.base if sel_level else None,
                                        sel_examperiod=grade.examperiod,
                                        request=request,
                                        ete_exams_only=False,
                                        grade_pk_list=[grade.pk]
                                    )
                                else:
                                    #TODO add error fieldname to err_fields in update)grade, not here

                        # - err_fields is used when there is an error entering grade, to restore old value on page
                                    append_dict = {}
                                    if msg_list:
                                         # only one grade is updated, therefore multiple fields are not possible
                                        if examgradetype in ('pescore', 'cescore', 'segrade', 'srgrade', 'pegrade', 'cegrade'):
                                            append_dict[grade.pk] = {'err_fields': [examgradetype]}

                                    if logging_on:
                                        logger.debug('    msg_list: ' + str(msg_list))
                                        logger.debug('    append_dict: ' + str(append_dict))

                                    rows = create_grade_rows(
                                        sel_examyear=sel_examyear,
                                        sel_schoolbase=sel_school.base,
                                        sel_depbase=sel_department.base if sel_department else None,
                                        sel_lvlbase=sel_level.base if sel_level else None,
                                        sel_examperiod=grade.examperiod,
                                        secret_exams_only=secret_exams_only,
                                        request=request,
                                        append_dict=append_dict,
                                        grade_pk_list=[grade.pk],
                                        remove_note_status=True
                                    )
                                if rows:
                                    row = rows[0]
                                    if row:
                                        grade_rows.append(row)
                                if logging_on:
                                    logger.debug('    grade_rows: ' + str(grade_rows))

                                if grade_rows:
                                    update_wrap['updated_grade_rows'] = grade_rows
            except Exception as e:
                # - create error when exam is not created PR2023-03-20
                logger.error(getattr(e, 'message', str(e)))
                msg_list.append(acc_prm.errhtml_error_occurred_no_border(e, _('The changes have not been saved.')))

        if logging_on:
            logger.debug('    msg_list: ' + str(msg_list))

        if msg_list:
            #msg_html = '<br>'.join(msg_list)
            #update_wrap['msg_html'] = msg_html
            header_txt = str(_('Enter score') if is_score else _('Enter grade')),
            update_wrap['messages'] = [{'class': "border_bg_invalid", 'header': header_txt,
                                        'msg_html': '<br>'.join(msg_list)}]

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of GradeUploadView


#######################################################

def update_grade_instance(grade_instance, upload_dict, sel_examyear, sel_department, si_dict, request):
    # --- update existing grade PR2020-12-16 PR2021-12-13 PR2021-12-25 PR2022-04-24 PR2023-08-15
    # add new values to update_dict (don't reset update_dict, it has values)
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ------- update_grade_instance -------')
        logger.debug('    upload_dict: ' + str(upload_dict))

    """
    upload_dict: {'mode': 'update', 'mapid': 'grade_67275', 'examperiod': 1, 
                    'grade_pk': 67275, 'student_pk': 9226, 'studsubj_pk': 67836, 
                    'examgradetype': 'segrade', 'segrade': '5,8'}
                    
    PR2024-06-01 change of exam version:
    upload_dict: {'table': 'grade', 'mode': 'update', 'return_grades_with_exam': True, 
                    'examyear_pk': 6, 'depbase_pk': 1, 'examperiod': 1, 
                    'exam_pk': 600, 'student_pk': 9920, 'lvlbase_pk': 6, 'studsubj_pk': 88082, 'grade_pk': 95509}
    """
    def savetolog_fields_append(field_list):
        #PR2024-05-31
        for fieldname in field_list:
            if fieldname not in savetolog_fields:
                savetolog_fields.append(fieldname)

    def get_ce_score_is_approved():
        return getattr(grade_instance, 'ce_auth1by') is not None or \
                           getattr(grade_instance, 'ce_auth2by') is not None or \
                           getattr(grade_instance, 'ce_auth3by') is not None or \
                           getattr(grade_instance, 'ce_auth4by') is not None

    def get_ce_exam_is_approved():
        return getattr(grade_instance, 'ce_exam_auth1by') is not None or \
                              getattr(grade_instance, 'ce_exam_auth2by') is not None or \
                              getattr(grade_instance, 'ce_exam_auth3by') is not None

    err_list = []
    save_changes = False
    recalc_finalgrade = False
    must_recalc_reex_reex03 = False

    savetolog_mode = None
    savetolog_fields = []

    for field, new_value in upload_dict.items():

# +++++ update score or grade
        if field in ('pescore', 'cescore', 'segrade', 'srgrade', 'pegrade', 'cegrade'):

# - validate new_value
        # - check if it is allowed to enter this examgradetype this examyear
        # - check if grade is published or authorized
        # - check restrictions in schemeitem

            validated_value, err_lst = grad_val.validate_grade_input_value(grade_instance, field, new_value, sel_examyear, si_dict, request)
            if logging_on:
                logger.debug('    validated_value: ' + str(validated_value) + ' ' + str(type(validated_value)))
                logger.debug('    err_lst: ' + str(err_lst))

            if err_lst:
                err_list.extend(err_lst)
            else:
                saved_value = getattr(grade_instance, field)
                if logging_on:
                    logger.debug('    saved_value:     ' + str(saved_value) + ' ' + str(type(saved_value)))

# - save changes if changed and no_error
                if validated_value != saved_value:
                    setattr(grade_instance, field, validated_value)

        # - remove exemption_imported - is only True when AWP has entered exemption from previous year
                    # PR2024-05-09 added: only when examperiod is exemption
                    # PR2024-05-17 TODO cannot change grade when exemption_imported, must add unblock by inspectorate
                    if grade_instance.examperiod == c.EXAMPERIOD_EXEMPTION:
                        saved_exemption_imported = getattr(grade_instance, 'exemption_imported')
                        if saved_exemption_imported:
                            setattr(grade_instance, 'exemption_imported', False)

                            savetolog_fields_append(['exemption_imported'])

                    save_changes = True
                    recalc_finalgrade = True

                    savetolog_mode = 'u'

                    savetolog_fields_append([field])

                    if logging_on:
                        logger.debug('  > save_changes of : ' + str(field))

        # - when reex or reex03: copy segrade, srgrade and pegrade to reex grade_instance
                    must_recalc_reex_reex03 = field in ('segrade', 'srgrade', 'pegrade')

 # when score has changed: recalc grade when cesuur/nterm is given
                    # PR2022-05-29 changed my mind: due to batch update needs those grades in reex_grade to calc final grade
                    # must make sure that values in reex_grade are updated when update them in ep 1

                    # - recalculate gl_sesr, gl_pece, gl_final, gl_use_exem in studsubj record
                    # - also update these fields when scores are changed or nterm entered

                    # PR2024-06-01: is done at and of function:
                    # was:
                    # if field in ('pescore', 'cescore'):
                    #     recalc_grade_from_score_in_grade_instance(grade_instance, field, validated_value)

# +++++  update field 'exam'
        elif field == 'exam_pk':
            exam = subj_mod.Exam.objects.get_or_none(pk=new_value) if new_value else None

            # PR2024-05-09 TODO: when score is approved, changing exam should not be possible

            # 'pe_exam' is not in use. Let it stay in case they want to introduce pe-exam again
            db_field = 'ce_exam_id'
            saved_exam_pk = getattr(grade_instance, db_field)

            if logging_on:
                logger.debug('....field: ' + str(field))
                logger.debug('    new_value: ' + str(new_value))
                logger.debug('    saved_exam_pk: ' + str(saved_exam_pk) + ' ' + str(type(saved_exam_pk)))

            # PR2023-05-25 skip when exam and saved exam are the same ( None == None gives True in Python)
            if new_value != saved_exam_pk:

    # - validate if ce_exam is approved or submitted:
                # ce_exam_auth1by is approval of exam (wolf)
                # ce_auth1by is approval of score

            # PR2023-05-29 debug tel Angela Richardson Masis Stella: cannot remove exam because is published (with empty score)
            # was:
                    # ce_score_is_approved, ce_exam_is_submitted, ce_exam_is_approved = False, False, False
                # - cannot change exam when ce_score_is_submitted
                    #ce_score_is_submitted = getattr(grade_instance, 'ce_published') is not None
                    #if not ce_score_is_submitted:
                    #    ce_score_is_approved = get_ce_score_is_approved()

            # - cannot change exam when Wolf-scores are submitted or (partly) approved
                ce_exam_is_submitted = getattr(grade_instance, 'ce_exam_published') or False
                ce_exam_is_approved = get_ce_exam_is_approved() if not ce_exam_is_submitted else False

                if logging_on:
                    logger.debug('....field: ' + str(field))
                    logger.debug('    ce_exam_is_submitted: ' + str(ce_exam_is_submitted))
                    logger.debug('    ce_exam_is_approved:  ' + str(ce_exam_is_approved))

                if ce_exam_is_submitted or ce_exam_is_approved:
                    score_exam_txt = gettext('this Wolf exam')
                    score_exam_txt_capitalized = af.capitalize_first_char(score_exam_txt)

                    submitted_approved_txt = gettext('Submitted') if ce_exam_is_submitted else gettext('Approved')
                    change_delete = str(_('Change') if new_value else _('Delete')).lower()
                    err_list.append(str(_("%(cpt)s' is already %(publ_appr_cpt)s.") \
                                        % {'cpt': score_exam_txt_capitalized,  'publ_appr_cpt': submitted_approved_txt.lower()}))
                    err_list.append(str(_("You cannot %(ch_del)s %(cpt)s.") % {'ch_del': change_delete, 'cpt': score_exam_txt}))

                else:
                    # has_changed is already checked above
                    # save_exam = True

                    setattr(grade_instance, db_field, new_value)

            # reset ce_exam_ fields when exam_pk changes
                    setattr(grade_instance, "ce_exam_blanks", None)
                    setattr(grade_instance, "ce_exam_result", None)
                    setattr(grade_instance, "ce_exam_score", None)

                    setattr(grade_instance, "ce_exam_auth1by", None)
                    setattr(grade_instance, "ce_exam_auth2by", None)
                    setattr(grade_instance, "ce_exam_auth3by", None)

                    setattr(grade_instance, "ce_exam_published", None)
                    setattr(grade_instance, "ce_exam_blocked", False)

                    # PR2022-06-08 debug tel Angela Richardson Maris Stella: score disappears
                    # dont reset score
                    # was: setattr(grade_instance, "pescore", None)
                    # was: setattr(grade_instance, "cescore", None)

                    # but do reset cegrade, pecegrade, finalgrade
                    setattr(grade_instance, "pegrade", None)
                    setattr(grade_instance, "cegrade", None)
                    setattr(grade_instance, "pecegrade", None)
                    setattr(grade_instance, "finalgrade", None)

                    # PR2024-06-01: is done at and of function:
                    # was: recalc_grade_from_score_in_grade_instance(grade_instance, 'cescore', getattr(grade_instance, "cescore"))

                    save_changes = True
                    recalc_finalgrade = True

                    savetolog_mode = 'u'

                    # ce_exam_id is not stored in log
                    savetolog_fields_append([db_field, 'cegrade', 'pecegrade', 'finalgrade'])

                    if logging_on:
                        logger.debug('  > save_changes of : ' + str(field))
                        logger.debug('  > savetolog_fields : ' + str(savetolog_fields))


# +++++  update field 'ce_exam_result', 'pe_exam_result'
        elif field in ('ce_exam_result', 'pe_exam_result'):

            if logging_on:
                logger.debug('....field: ' + str(field))
                logger.debug('    new_value:   ' + str(new_value))

            saved_value = getattr(grade_instance, field)
            if logging_on:
                logger.debug('    saved_value: ' + str(saved_value))

    # - save changes if changed and no_error
            # always calculate and save result, to be on the safe side. Was: if new_value != saved_value:
            total_score, total_blanks, total_no_scoreNIU, total_no_keyNIU = None, None, None, None
            exam_instance = grade_instance.ce_exam
            if exam_instance:
                # PR2022-05-22 use same calc for all updates. Was:
                #total_score, total_blanks, total_has_errorsNIU = \
                #    get_all_result_with_assignment_dict_CALC_SCORE_BLANKS(
                #        partex_str=getattr(exam_instance, 'partex'),
                #        assignment_str=getattr(exam_instance, 'assignment'),
                 #       keys_str=getattr(exam_instance, 'keys'),
                 #       result_str=new_value
                #    )

                # create list of results
                all_result_dictNIU, total_amountNIU, max_scoreNIU, total_score, total_blanks, total_no_scoreNIU, total_no_keyNIU = \
                    get_grade_assignment_with_results_dict(
                        partex_str=getattr(exam_instance, 'partex'),
                        assignment_str=getattr(exam_instance, 'assignment'),
                        keys_str=getattr(exam_instance, 'keys'),
                        result_str=new_value
                    )

            if logging_on:
                logger.debug('     field:                  ' + str(field) + ' new_value: ' + str(new_value))
                logger.debug('     total_score:            ' + str(total_score) + ' total_blanks: ' + str(total_blanks))
                logger.debug('     total_no_scoreNIU:      ' + str(total_no_scoreNIU))
                logger.debug('     total_no_keyNIU:        ' + str(total_no_keyNIU))

            field_prefix = field[:8]  # field_prefix = 'ce_exam_' or 'pe_exam_'
            setattr(grade_instance, field_prefix + 'result', new_value)
            setattr(grade_instance, field_prefix + 'score', total_score)
            setattr(grade_instance, field_prefix + 'blanks', total_blanks)

            save_changes = True

            # ce_exam_result is not stored in log

# +++++  update field 'xx_status' and 'xxpublished'
        elif field in ('se_status', 'pe_status', 'ce_status', 'sepublished', 'pepublished', 'cepublished'):
            pass
            # fields are updated in GradeApproveView

# +++++  update field 'ce_exam_published'
        elif field == 'ce_exam_published':
            # can only remove published. Also remove auth1, auth2, auth3. PR2022-05-22
            setattr(grade_instance, field, None)
            setattr(grade_instance, 'ce_exam_auth1by', None)
            setattr(grade_instance, 'ce_exam_auth2by', None)
            setattr(grade_instance, 'ce_exam_auth3by', None)
            save_changes = True

# +++++  update fields 'ce_exam_auth1by' and 'ce_exam_auth2by' and 'ce_exam_auth3by'
        elif field == 'auth_index':
            auth_index = upload_dict.get(field)
            auth_bool_at_index = upload_dict.get('auth_bool_at_index', False)
            if logging_on:
                logger.debug('....field: ' + str(field))
                logger.debug('    auth_index: ' + str(auth_index))
                logger.debug('    auth_bool_at_index: ' + str(auth_bool_at_index))

            if auth_index == 1:
                fldName = 'ce_exam_auth1by'
            elif auth_index == 2:
                fldName = 'ce_exam_auth2by'
            elif auth_index == 3:
                fldName = 'ce_exam_auth3by'
            else:
                fldName = None

            if logging_on:
                logger.debug('     auth_index: ' + str(auth_index))
                logger.debug('     auth_bool_at_index: ' + str(auth_bool_at_index))
                logger.debug('     fldName: ' + str(fldName))

            if fldName:
                new_ce_exam_authby = request.user if auth_bool_at_index else None
                if logging_on:
                    logger.debug('new_ce_exam_authby: ' + str(new_ce_exam_authby))

                setattr(grade_instance, fldName, new_ce_exam_authby)
                save_changes = True

# --- end of for field, new_value in upload_dict.items()

    if logging_on:
        logger.debug('  > save_changes : ' + str(save_changes))

# +++++ save changes`
    if save_changes:

    # --- first calculate ce_grade if necessary
        if recalc_finalgrade:
            if logging_on:
                logger.debug('  > recalc_finalgrade')

            ce_exam = grade_instance.ce_exam if grade_instance else None

            new_ce_grade = calc_score.calc_grade_from_score_v2(
                examperiod=grade_instance.examperiod,
                no_centralexam=si_dict['no_centralexam'],
                weight_ce=si_dict['weight_ce'],
                cegrade=grade_instance.cegrade,
                cescore=grade_instance.cescore,
                ete_exam=si_dict['ete_exam'],
                scalelength=ce_exam.scalelength if ce_exam else None,
                cesuur=ce_exam.cesuur if ce_exam else None,
                nterm=ce_exam.nterm if ce_exam else None,
                exam_published_id=ce_exam.published_id if ce_exam else None
            )
            setattr(grade_instance, 'cegrade', new_ce_grade)

            savetolog_fields_append(['cegrade'])

            if logging_on:
                logger.debug('  > new_ce_grade : ' + str(new_ce_grade))

    # --- then calc final grade
            studsubj = grade_instance.studentsubject if grade_instance else None

            if studsubj:
                new_sesrgrade, new_pecegrade, new_finalgrade, delete_exemption_cegrade_without_ce = \
                    calc_final.calc_final_grade_v2(
                        examperiod=grade_instance.examperiod,
                        subj_code=si_dict['subj_code'],
                        gradetype=si_dict['gradetype'],
                        weight_se=si_dict['weight_se'],
                        weight_ce=si_dict['weight_ce'],
                        no_ce_years=si_dict['no_ce_years'],
                        sr_allowed=si_dict['sr_allowed'],
                        has_practex=si_dict['has_practex'],

                        exemption_year=studsubj.exemption_year,
                        has_sr=studsubj.has_sr,

                        segrade=grade_instance.segrade,
                        srgrade=grade_instance.srgrade,
                        pegrade=grade_instance.pegrade,
                        cegrade=new_ce_grade
                    )

                setattr(grade_instance, 'sesrgrade', new_sesrgrade)
                setattr(grade_instance, 'pecegrade', new_pecegrade)
                setattr(grade_instance, 'finalgrade', new_finalgrade)

                savetolog_fields_append(['sesrgrade', 'pecegrade', 'finalgrade'])

                if logging_on:
                    logger.debug('  > new_sesrgrade : ' + str(new_sesrgrade))
                    logger.debug('  > new_pecegrade : ' + str(new_pecegrade))
                    logger.debug('  > new_finalgrade : ' + str(new_finalgrade))


# - save grade instance
        try:
            grade_instance.save(request=request)

            if logging_on:
                logger.debug('The changes have been saved.')

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            err_list.append(str(_('An error occurred. The changes have not been saved.')))
        else:

# - save changes to gradelog
            if savetolog_mode:
                # PR2023-08-15
                #awpr_log.savetolog_grade(
                #    grade_pk=grade_instance.pk,
                #    req_mode=savetolog_mode,
                #    request=request,
                #    updated_fields=savetolog_fields
                #)

                awpr_log.copytolog_grade_v2(
                    grade_pk_list=[grade_instance.pk],
                    log_mode=savetolog_mode,
                    modifiedby_id=request.user.pk
                )

# +++ if one of the input fields has changed: recalc final grade
            # if recalc_finalgrade:
            #    calc_score.batch_update_finalgrade(
            #        department_instance=sel_department,
            #        grade_pk_list=[grade_instance.pk]
            #    )

# - recalculate gl_sesr, gl_pece, gl_final, gl_use_exem in studsubj record
            # TODO also update these fields when scores are changed or nterm entered
            if must_recalc_reex_reex03:
    # - when field = 'segrade', 'srgrade', 'pegrade': also update and save grades in reex, reex03, if exist
                # PR2022-05-29 due to batch update needs those grades in reex_grade to calc final grade
                # must make sure that values in reex_grade are updated when update them in ep 1

                recalc_finalgrade_in_reex_reex03_grade_and_save(grade_instance, si_dict)

    # PR2024-05-14
            calc_final.batch_recalc_update_studsubj_grade_v2(
                request=request,
                studsubj_pk_list=[grade_instance.studentsubject_id]
            )


    if logging_on:
        logger.debug('....err_list:  ' + str(err_list))

    return err_list
# --- end of update_grade_instance


def recalc_grade_from_score_in_grade_instanceNIU(grade_instance, field, validated_value):
    # PR2022-06-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- recalc_grade_from_score_in_grade_instance -------')

    # when score has changed: recalc grade when cesuur/nterm is given
    if field in ('pescore', 'cescore'):
        grade_field = 'pegrade' if field == 'pescore' else 'cegrade'
        grade_value = None
        if logging_on:
            logger.debug('....field_tobe_calculated:  ' + str(grade_field))
            logger.debug('    grade_examperiod:       ' + str(grade_instance.examperiod))
            logger.debug('    grade_instance.ce_exam: ' + str(grade_instance.ce_exam))
            logger.debug('    grade_instance.cescore: ' + str(grade_instance.cescore) + ' ' + str(type(grade_instance.cescore)))
            logger.debug('    validated_value:        ' + str(validated_value) + ' ' + str(type(validated_value)))

        if grade_instance.ce_exam and grade_instance.cescore is not None:
            exam_instance = grade_instance.ce_exam
            # DUO exams don't have to be published
            if exam_instance.ete_exam:
                if exam_instance.published:
                    grade_value = calc_score.calc_grade_from_score_ete(validated_value, exam_instance.scalelength,
                                                                   exam_instance.cesuur)
            elif not exam_instance.ete_exam:
                grade_value = calc_score.calc_grade_from_score_duo(validated_value, exam_instance.scalelength,
                                                                   exam_instance.nterm)

        if logging_on:
            logger.debug('  > grade_value:            ' + str(grade_value))

        old_value = getattr(grade_instance, grade_field)
        if logging_on:
            logger.debug('    old_value:            ' + str(old_value))


        if grade_value != old_value:
            setattr(grade_instance, grade_field, grade_value)
            if logging_on:
                logger.debug('  > saved value:            ' + str(getattr(grade_instance, grade_field)))
# - end of recalc_grade_from_score_in_grade_instance


def update_studsubj_and_recalc_student_result(sel_examyear, sel_school, sel_department, student):
    # PR2022-01-01
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_studsubj_and_recalc_student_result -------')

    sql_studsubj_value_list, sql_student_list, log_list = [], [], []

    if student:
        # - get_scheme_dict
        scheme_dict = calc_res.get_scheme_dict(sel_examyear, sel_department)

        # - get_schemeitems_dict
        schemeitems_dict = calc_res.get_schemeitems_dict(sel_examyear, sel_department)
        student_dict = {}

    # - get student_dict
        student_pk_list = [student.pk]
        student_dictlist = calc_res.get_students_with_grades_dictlist(
            examyear = sel_examyear,
            school = sel_school,
            department = sel_department,
            student_pk_list = student_pk_list
        )

        student_dict = student_dictlist[0] if student_dictlist else {}

        calc_res.calc_student_result(sel_examyear, sel_department, student_dict, scheme_dict, schemeitems_dict,
                                     log_list, sql_studsubj_value_list, sql_student_list)
    if logging_on:
        logger.debug('    sql_studsubj_value_list: ' + str(sql_studsubj_value_list))
        logger.debug('    sql_student_list: ' + str(sql_student_list))
        if log_list:
            for line in log_list:
                logger.debug(' .. ' + str(line))
        logger.debug(' -- end of update_studsubj_and_recalc_student_result')

    return sql_studsubj_value_list, sql_student_list
# - end of update_studsubj_and_recalc_student_result


def recalc_finalgrade_in_reex_reex03_grade_and_save(grade_instance, si_dict):  # PR2021-12-28 PR2022-01-05
    # called by:  - update_grade_instance, - update_studsubj
    # when first examperiod:
    #  - check if there is a reex or reex03 grade: if so, recalc final grade in reex or reex03
    #  - only when first examperiod ( is filtered in update_grade_instance)

    logging_on = s.LOGGING_ON
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

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('------- recalc_finalgrade_in_grade_and_save -------')
        logger.debug('     grade_instance: ' + str(grade_instance))
        logger.debug('     si_dict: ' + str(si_dict))
        logger.debug('     skip_save: ' + str(skip_save))

    if grade_instance:
        try:
            studentsubject = grade_instance.studentsubject
            has_sr = studentsubject.has_sr
            exemption_year = studentsubject.exemption_year

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

            if logging_on:
                logger.debug('     se_grade: ' + str(se_grade))
                logger.debug('     sr_grade: ' + str(sr_grade))
                logger.debug('     pe_grade: ' + str(pe_grade))
                logger.debug('     ce_grade: ' + str(ce_grade))

# - calc sesr pece and final grade
            if logging_on:
                logger.debug(' calc sesr pece and final grade ')

            sesr_grade, pece_grade, finalgrade, delete_cegrade = \
                calc_final.calc_sesr_pece_final_grade(
                    si_dict=si_dict,
                    examperiod=grade_instance.examperiod,
                    has_sr=has_sr,
                    exemption_year=exemption_year,
                    se_grade=se_grade,
                    sr_grade=sr_grade,
                    pe_grade=pe_grade,
                    ce_grade=ce_grade
                )

            setattr(grade_instance, 'sesrgrade', sesr_grade)
            setattr(grade_instance, 'pecegrade', pece_grade)
            setattr(grade_instance, 'finalgrade', finalgrade)

            if logging_on:
                logger.debug(' >>> sesr_grade: ' + str(sesr_grade))
                logger.debug(' >>> pece_grade: ' + str(pece_grade))
                logger.debug(' >>> finalgrade: ' + str(finalgrade))

            # - when exemption: in case ce_grade has value: remove value when exemption has no central exam
            if delete_cegrade:
                setattr(grade_instance, 'cegrade', None)

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
            "AND NOT grade.tobedeleted AND NOT grade.deleted",
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
        # req_usr can only view nots of his wwn organization

        # only role_school and same_school can view grades that are not published, PR2021-04-29
        # by filtering subquery : (intern_schoolbase_id = requsr_sb_id) OR ssn.intern_schoolbase_id IS NULL)
        # filter on exyr, schoolbase, depbase, examperiod is in main query
        requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase_pk)

        # PRE2022-04-17 show not icon of last note, instead of max icon
        # from: https://ubiq.co/database-blog/how-to-get-first-row-per-group-in-postgresql/
        # nope, keep max icon
        # sql_ssn_list = [
        #    "SELECT studsubj_id, last_note_status FROM (",
        #    "SELECT ssn.studentsubject_id AS studsubj_id, ",
        #     "COALESCE(note_status, '0_1') AS last_note_status, ",
        #    "ROW_NUMBER() over (PARTITION BY ssn.studentsubject_id ORDER BY ssn.modifiedat DESC) AS row_number",
        #     "FROM students_studentsubjectnote AS ssn",
        #    "WHERE (ssn.intern_schoolbase_id = %(requsr_sb_id)s::INT OR ssn.intern_schoolbase_id IS NULL)",
        #    ") temp WHERE row_number=1"]
        # sql_ssn = ' '.join(sql_ssn_list)
        # row: {'studsubj_id': 23033, 'last_note_status': '1_3'}

        sql_keys = {
            'ey_id': sel_examyear_pk,
            'sb_id': sel_schoolbase_pk,
            'db_id': sel_depbase_pk,
            'ex_per': sel_examperiod,
            'requsr_sb_id': request.user.schoolbase_id}

        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))
            logger.debug('requsr_same_school: ' + str(requsr_same_school))

        # was:
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
                    "AND NOT grd.tobedeleted AND NOT grd.deleted",
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
        # req_usr can only view nots of his wwn organization

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


def create_grade_rows(sel_examyear, sel_schoolbase, sel_depbase, sel_lvlbase, sel_examperiod, request,
                      secret_exams_only=False, append_dict=None, grade_pk_list=None, auth_dict=None,
                      remove_note_status=False):
    # --- create grade rows of all students of this examyear / school PR2020-12-14  PR2021-12-03 PR2022-02-09 PR2022-12-12

    # note: don't forget to filter tobedeleted = false!! PR2021-03-15
    # grades that are not published are only visible when 'same_school'
    # note_icon is downloaded in separate call

    # PR2023-05-22 when secret_exams_only = True: show grdaes of all schools, but secret_exams_only

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_grade_rows -----')
        logger.debug('    sel_examyear:    ' + str(sel_examyear))
        logger.debug('    sel_examperiod:    ' + str(sel_examperiod))
        logger.debug('    grade_pk_list:     ' + str(grade_pk_list))
        logger.debug('    sel_schoolbase:     ' + str(sel_schoolbase) + ' pk: ' + str(sel_schoolbase.pk if sel_schoolbase else '-') )
        logger.debug('    sel_depbase:     ' + str(sel_depbase) + ' pk: ' + str(sel_depbase.pk if sel_depbase else '-') )
        logger.debug('    sel_lvlbase:     ' + str(sel_lvlbase) + ' pk: ' + str(sel_lvlbase.pk if sel_lvlbase else '-') )
        logger.debug('    secret_exams_only:     ' + str(secret_exams_only))
        logger.debug(' ----------')

    req_usr = request.user

# - only requsr of the same school can view grades that are not published, PR2021-04-29
    # requsr_same_school = (req_usr.role == c.ROLE_008_SCHOOL and req_usr.schoolbase.pk == sel_schoolbase.pk)
# - also corrector can view grades

#  - add_auth_list is used in Ex form to add name of auth
    add_auth_list = True if auth_dict is not None else False

# - get selected_pk_dict of req_usr
    selected_pk_dict = acc_prm.get_selected_pk_dict_of_user_instance(request.user)

# - get allowed_sections_dict from request
    userallowed_instance = acc_prm.get_userallowed_instance_from_request(request)

    userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
    if logging_on:
        logger.debug('    allowed_sections_dict: ' + str(userallowed_sections_dict) + ' ' + str(type(userallowed_sections_dict)))
        # allowed_sections_dict: {'2': {'1': {'4': [117, 114], '5': [], '-9': [118, 121]}}} <class 'dict'>

    """
    # PR2023-04-08 don't hide grades any more for Inspection and adminshow grades
    # - only when requsr_same_school the not-published grades are visible
    # - also the role_corrector may see the grades
    # - also exemptions, because they are not published - they are always visible.
    # was:
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

        status = "se_status, sr_status, pe_status, ce_status,"
    """

    sql_list = ["SELECT grd.id, studsubj.id AS studsubj_id, studsubj.schemeitem_id, cl.id AS cluster_id, cl.name AS cluster_name,",
                "CONCAT('grade_', grd.id::TEXT) AS mapid,",
                "stud.id AS student_id, stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
                "dep.base_id AS depbase_id, depbase.code AS depbase_code,",
                "lvl.id AS lvl_id, lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev,",
                "sct.id AS sct_id, sct.base_id AS sctbase_id, sct.abbrev AS sct_abbrev,",
                "stud.iseveningstudent, ey.locked AS ey_locked, school.locked AS school_locked,",
                "school.islexschool,",
                "studsubj.has_exemption, studsubj.exemption_year, studsubj.has_sr, studsubj.has_reex, studsubj.has_reex03,",
                "studsubj.tobedeleted AS studsubj_tobedeleted,",

                "grd.examperiod, grd.segrade, grd.srgrade, grd.sesrgrade, grd.cescore, grd.cegrade,",
                "grd.pescore, grd.pegrade, grd.pecegrade, grd.finalgrade AS finalgrade,",
                "grd.se_status, grd.sr_status, grd.pe_status, grd.ce_status,",

                "grd.se_auth1by_id, grd.se_auth2by_id, grd.se_auth3by_id, grd.se_blocked,", #  grd.se_auth4by_id,
                "grd.ce_auth1by_id, grd.ce_auth2by_id, grd.ce_auth3by_id, grd.ce_auth4by_id, grd.ce_blocked,",

                "se_auth1.last_name AS se_auth1by_usr, se_auth2.last_name AS se_auth2by_usr, se_auth3.last_name AS se_auth3by_usr,", # se_auth4.last_name AS se_auth4by_usr,",
                "ce_auth1.last_name AS ce_auth1by_usr, ce_auth2.last_name AS ce_auth2by_usr, ce_auth3.last_name AS ce_auth3by_usr, ce_auth4.last_name AS ce_auth4by_usr,",

                #  exam_published_id    is the exam,       published by ETE
                #  ce_exam_published_id is the Wolf score, submitted by the school
                #  ce_published_id      is the Ex2A score, submitted by the school

                "grd.se_published_id, se_published.modifiedat AS se_publ_modat,",
                "grd.ce_published_id, ce_published.modifiedat AS ce_publ_modat,",

                "grd.ce_exam_id, grd.ce_exam_score,",

                #  ce_exam_published_id is the Wolf score, submitted by the school
                "grd.ce_exam_auth1by_id, grd.ce_exam_auth2by_id, grd.ce_exam_auth3by_id, grd.ce_exam_published_id,",

                "grd.ce_exam_blanks, grd.ce_exam_result, grd.ce_exam_score,",

                "grd.exemption_imported,",  # PR2023-01-24 added

                "ce_exam.ete_exam, ce_exam.secret_exam, ce_exam.version, ntb.omschrijving AS ntb_omschrijving,",

                # exam_published_id is the published ETE exam
                "ce_exam.published_id AS exam_published_id,"
                
                "si.subject_id, si.subjecttype_id,",
                "si.gradetype, si.weight_se, si.weight_ce, si.is_mandatory, si.is_mand_subj_id, si.is_combi, si.extra_count_allowed,",
                "si.extra_nocount_allowed, si.has_practexam,",

                # TODO check if sjtp.has_pws is used. If so: add join with subjecttype
                # was:  "si.has_pws,",
                "si.is_core_subject, si.is_mvt, si.sr_allowed, si.no_ce_years, si.thumb_rule,",
                "si.rule_grade_sufficient, si.rule_gradesuff_notatevlex,",

                "subj.name_nl AS subj_name_nl, subjbase.id AS subjbase_id, subjbase.code AS subj_code,",
    ]
    # add schoolname, only when secret_exams_only
    if secret_exams_only:
        sql_list.append("school.id AS school_id, schoolbase.code AS school_code, school.abbrev AS school_abbrev,")

    sql_list.extend((
                "NULL AS note_status", # will be filled in after downloading note_status

                "FROM students_grade AS grd",
                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",

                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",

                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)"
    ))

    # PR2023-05-22 only show grades with exams when secret_exams_only
    if secret_exams_only:
        # show ete_cluster
        sql_list.extend((
            "INNER JOIN schools_schoolbase AS schoolbase ON (schoolbase.id = school.base_id)",
            # was: "INNER JOIN subjects_exam AS exam ON (ce_exam.id = grd.ce_exam_id)",
            "LEFT JOIN subjects_exam AS ce_exam ON (ce_exam.id = grd.ce_exam_id)",
            "LEFT JOIN subjects_cluster AS cl ON (cl.id = studsubj.ete_cluster_id)"
        ))
    else:
        sql_list.extend((
            "LEFT JOIN subjects_exam AS ce_exam ON (ce_exam.id = grd.ce_exam_id)",
            "LEFT JOIN subjects_cluster AS cl ON (cl.id = studsubj.cluster_id)"
        ))

    sql_list.extend((
                "LEFT JOIN subjects_ntermentable AS ntb ON (ntb.id = ce_exam.ntermentable_id)",
                "LEFT JOIN schools_published AS se_published ON (se_published.id = grd.se_published_id)",
                "LEFT JOIN schools_published AS ce_published ON (ce_published.id = grd.ce_published_id)",

                "LEFT JOIN accounts_user AS se_auth1 ON (se_auth1.id = grd.se_auth1by_id)",
                "LEFT JOIN accounts_user AS se_auth2 ON (se_auth2.id = grd.se_auth2by_id)",
                "LEFT JOIN accounts_user AS se_auth3 ON (se_auth3.id = grd.se_auth3by_id)",

                "LEFT JOIN accounts_user AS ce_auth1 ON (ce_auth1.id = grd.ce_auth1by_id)",
                "LEFT JOIN accounts_user AS ce_auth2 ON (ce_auth2.id = grd.ce_auth2by_id)",
                "LEFT JOIN accounts_user AS ce_auth3 ON (ce_auth3.id = grd.ce_auth3by_id)",
                "LEFT JOIN accounts_user AS ce_auth4 ON (ce_auth4.id = grd.ce_auth4by_id)",

                # grd.deleted is only used when examperiod = exem, reex ofr reex3 PR2023-02-14
                # not true: in 2022 there were some deleted grades  PR2023-03-29
                "WHERE NOT stud.deleted AND NOT studsubj.deleted AND NOT grd.deleted",

                ''.join(("AND ey.id=", str(sel_examyear.pk), "::INT")),
                ''.join(("AND grd.examperiod=", str(sel_examperiod), "::INT")),
                ''.join(("AND dep.base_id=", str(sel_depbase.pk), "::INT"))
                ))

    # PR2023-05-22 skip schoolbase clause when secret_exams_only
    # PR2023-06-08 Joan SXM wants to see the secret exams before publishing them.
    if secret_exams_only:
        sql_list.append("AND ce_exam.secret_exam")
    else:
        if sel_schoolbase:
            sql_list.append(''.join(("AND school.base_id=", str(sel_schoolbase.pk), "::INT")))
        else:
            sql_list.append("AND FALSE")

    if grade_pk_list:
        # when grade_pk_list has value: skip subject filter
        sql_list.append(''.join(("AND grd.id IN (SELECT UNNEST(ARRAY", str(grade_pk_list), "::INT[]))")))

# --- filter on usersetting
    # PR2022-05-29 don't filter on sel_student_pk anymore
    # PR2024-06-06 also don't filter on sel_cluster, is done on client side

    else:

        # - filter on selected schoolbase
            # - filter selected schoolbase_pk is required, is already part of sql
            # - validation of sel_schoolbase_pk has taken place in download_setting

        # - filter on selected depbase
            # - filter selected depbase_pk is required, is already part of sql
            # - validation of sel_depbase_pk has taken place in download_setting

        # +++ add sql_clause with selected sct, cluster an d allowed depbase, lvlbase, subj_base

# - filter on selected levelbase
        # PR2023-04-29 debug: don't use saved_lvlbase_pk, it will show no records when changing to havo/vwo
        # PR2024-03-26 debug: Ancilla Domini Yolande van Erven: teacher R_Soliana cannot see grades
        # subject with base_id 118 = Papiamentu
        # subjct with id = 223 is Papiament 2023 Cur
        # becasue it is used in 2024, no records are shwon
        # solution: save base_id, not subject_id
        # allowed_sections_dict: {'2': {'1': {'-9': [118]}}} <class 'dict'>
        #      sql_clause_lvlbase:  AND (lvl.base_id=6::INT)
        #   saved_sctbase_pk:  13
        #     sql_clause_sctbase:  AND (sct.base_id=13::INT)
        #     saved_subject_pk:  223
        #      sql_clause_subject_pk:  AND (subj.id = 223::INT)
        if sel_lvlbase:
            sql_clause_lvlbase = ''.join(("AND (lvl.base_id=", str(sel_lvlbase.pk), "::INT)"))
            sql_list.append(sql_clause_lvlbase)
            if logging_on:
                logger.debug('     sql_clause_lvlbase:  ' + str(sql_clause_lvlbase))

# - filter on selected sectorbase
        # PR2024-06-06 is sectorbase is not part of get_sqlclause_allowed_v2, so it must stay here
        # PR2024-06-19 Dorothee C. Illis-Laurence Insectorate doe not see grades.
        # cause: filter AND (sct.base_id=-9::INT)
        # filter out '-9' and make sure it is not saved in usersettings,usenull instea
        saved_sctbase_pk = selected_pk_dict.get(c.KEY_SEL_SCTBASE_PK)
        if logging_on:
            logger.debug('     saved_sctbase_pk:  ' + str(saved_sctbase_pk))
        if saved_sctbase_pk and saved_sctbase_pk != -9:
            sql_clause_sctbase = ''.join(("AND (sct.base_id=", str(saved_sctbase_pk), "::INT)"))
            sql_list.append(sql_clause_sctbase)
            if logging_on:
                logger.debug('     sql_clause_sctbase:  ' + str(sql_clause_sctbase))

# - filter on selected subjectbase
        # PR2024-03-29 switched to subjbase_pk
        # PR2024-06-06 selected subjectbase is not part of get_sqlclause_allowed_v2, so it muust stay here
        saved_subjbase_pk = selected_pk_dict.get(c.KEY_SEL_SUBJBASE_PK)
        if logging_on:
            logger.debug('     saved_subjbase_pk:  ' + str(saved_subjbase_pk))
        if saved_subjbase_pk and saved_subjbase_pk != -9:
            sql_clause_subjbase_pk = ''.join(("AND (subj.base_id = ", str(saved_subjbase_pk), "::INT)"))
            sql_list.append(sql_clause_subjbase_pk)
            if logging_on:
                logger.debug('     sql_clause_subjbase_pk:  ' + str(sql_clause_subjbase_pk))

# - filter on selected subject_pk - deprecated
        #saved_subject_pk = selected_pk_dict.get(c.KEY_SEL_SUBJECT_PK)
        #if logging_on:
        #    logger.debug('     saved_subject_pk:  ' + str(saved_subject_pk))
        #if saved_subject_pk:
        #    sql_clause_subject_pk = ''.join(("AND (subj.id = ", str(saved_subject_pk), "::INT)"))
        #    sql_list.append(sql_clause_subject_pk)
        #    if logging_on:
        #        logger.debug('     sql_clause_subject_pk:  ' + str(sql_clause_subject_pk))

# - filter on selected cluster_pk
        # don't filter on allowed clusters. Allowed clusters give permit to edit and approve, but others may be viewed
        # also don't filter on selected cluster, will be done on client side
        #saved_cluster_pk = selected_pk_dict.get(c.KEY_SEL_CLUSTER_PK)
        #if saved_cluster_pk:
        #    sql_clause_cluster_pk = ''.join(("AND (studsubj.cluster_id = ", str(saved_cluster_pk), "::INT)"))
        #    sql_list.append(sql_clause_cluster_pk)
        #    if logging_on:
        #        logger.debug('     sql_clause_cluster_pk:  ' + str(sql_clause_cluster_pk))

# - filter on allowed depbases, levelbase, subjectbases
        # was: sqlclause_allowed_dep_lvl_subj = acc_prm.get_sqlclause_allowed_dep_lvl_subj(
        #    table='grade',
        #    userallowed_sections_dict=userallowed_sections_dict,
        #    sel_schoolbase_pk=sel_schoolbase_pk,
        #    sel_depbase_pk=sel_depbase_pk
        #)
        #if sqlclause_allowed_dep_lvl_subj:
        #    sql_list.append(sqlclause_allowed_dep_lvl_subj)

        # PR2023-03-27
        # when a corrector has no allowed subjects, must return None.
        # when an examiner has no allowed subjects, must return all subjects.
        # PR2023-06-02 Shalini v Uytrecht: wants to be able to see the grades. Ship when chairperson or secretary

        return_false_when_no_allowedsubjects = False
        if (req_usr.role == c.ROLE_016_CORR):
            # - skip if auth1 or auth2 is in requsr_usergroup_list
            requsr_usergroup_list = acc_prm.get_usergroup_list_from_user_instance(req_usr)
            return_false_when_no_allowedsubjects = not requsr_usergroup_list or ('auth1' not in requsr_usergroup_list and 'auth2' not in requsr_usergroup_list)

            if logging_on:
                logger.debug('    requsr_usergroup_list: ' + str(requsr_usergroup_list))
                logger.debug('    return_false_when_no_allowedsubjects: ' + str(return_false_when_no_allowedsubjects))

        # don't filter on sel_schoolbase when secret_exams_only
        if secret_exams_only:
            sel_schoolbase = None

        sql_clause = acc_prm.get_sqlclause_allowed_v2(
            table='grade',
            sel_schoolbase_pk=sel_schoolbase.pk if sel_schoolbase else None,
            sel_depbase_pk=sel_depbase.pk if sel_depbase else None,
            sel_lvlbase_pk=sel_lvlbase.pk if sel_lvlbase else None,
            userallowed_sections_dict=userallowed_sections_dict,
            return_false_when_no_allowedsubjects=return_false_when_no_allowedsubjects
        )
        if sql_clause:
            sql_list.append(sql_clause)

        if logging_on:
            logger.debug('    sql_clause: ' + str(sql_clause))

    sql_list.append('ORDER BY grd.id')
    if logging_on:
        for sql_txt in sql_list:
            logger.debug(' > ' + str(sql_txt))

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql)
        grade_rows = af.dictfetchall(cursor)

# - add full name to rows, and array of id's of auth
    if grade_rows:
        # create auth_dict, with lists of each auth
        #auth_fields = ('se_auth1by_id', 'se_auth2by_id', 'se_auth3by_id', 'se_auth4by_id',
        #                  'sr_auth1by_id', 'sr_auth2by_id', 'sr_auth3by_id', 'sr_auth4by_id',
        #                  'pe_auth1by_id', 'pe_auth2by_id', 'pe_auth3by_id', 'pe_auth4by_id',
        #                  'ce_auth1by_id', 'ce_auth2by_id', 'ce_auth3by_id' 'ce_auth4by_id')

        if logging_on :
            logger.debug('---------------- ')

        for row in grade_rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')

    # - add full_name
            prefix = row.get('prefix')
            full_name = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

    # - add exam_name
            ce_exam_id = row.get('ce_exam_id')
            exam_name = None
            if ce_exam_id:
                exam_name = subj_vw.get_exam_name(
                    ce_exam_id=ce_exam_id,
                    ete_exam=row.get('ete_exam'),
                    subj_name_nl=row.get('subj_name_nl'),
                    depbase_code=row.get('depbase_code'),
                    lvl_abbrev=row.get('lvl_abbrev'),
                    examperiod=row.get('examperiod'),
                    examyear=sel_examyear,
                    version=row.get('version'),
                    ntb_omschrijving=row.get('ntb_omschrijving')
                )
            row['exam_name'] = exam_name

    # PR2021-06-01 debug. Remove key 'note_status', otherwise it will erase note icon when refreshing this row
            if remove_note_status:
                row.pop('note_status')

    # - add messages to studsubj_rows, only when student_pk or grade_pk_list have value
            if append_dict and grade_pk_list:
                if logging_on:
                    logger.debug('......... ')
                    logger.debug('append_dict: ' + str(append_dict))

                grade_pk = row.get('id')
                if grade_pk:
                    grade_append_dict = append_dict.get(grade_pk)
                    if grade_append_dict:
                        for key, value in grade_append_dict.items():
                            row[key] = value

            #if logging_on:
            #    logger.debug(' row: ' + str(row))

    if logging_on:
        logger.debug(' grade_rows len: ' + str(len(grade_rows)))
        logger.debug('---------------- ')

    return grade_rows
# --- end of create_grade_rows


def create_grade_with_exam_rows(sel_examyear, sel_schoolbase, sel_depbase, sel_lvlbase, sel_examperiod, ete_exams_only,
                                    request, setting_dict=None, grade_pk_list=None):
    # --- create grade rows of all students of this examyear / school PR2020-12-14 PR2022-02-20 PR2023-02-22

    # note: don't forget to filter deleted = false!! PR2021-03-15
    # PR2023-04-17 not any more: was: grades that are not published are only visible when 'same_school'
    # note_icon is downloaded in separate call

    # IMPORTANT: only add field 'keys' when ETE has logged in .
    #   Field 'keys' contains the answers of multiple choice questions,
    #   they may not be downloaded by schools,
    #   to be 100% sure that the answers cannot be retrieved by a school.

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_grade_with_exam_rows -----')
        logger.debug('    setting_dict: ' + str(setting_dict))
        logger.debug('    ete_exams_only: ' + str(ete_exams_only))

    # - only requsr of the same school  can view grades that are not published, PR2021-04-29
    # - also corrector .TODO: add school to corrector permit

    # - only exams that are published are visible
    # - only ce_exams that are submitted are visible for non - requsr_same_school user > not necessary
    #       > not necessary, because only requsr_same_school can access grade_exam_rows

    grade_rows = []

    req_usr = request.user
    requsr_same_school = (req_usr.role == c.ROLE_008_SCHOOL and req_usr.schoolbase == sel_schoolbase)

    # PR2023-05-12 was: if requsr_same_school and sel_examyear and sel_schoolbase and sel_depbase:
    if sel_examyear and sel_schoolbase and sel_depbase:
        #examkeys_fields = ""
        #if req_usr.role == c.ROLE_064_ADMIN:
        #    # pe_exam not in use: was: examkeys_fields = "ce_exam.keys AS ceex_keys, pe_exam.keys AS peex_keys,"
        #    examkeys_fields = "ce_exam.keys AS ceex_keys,"

        sql_keys = {'ey_id': sel_examyear.pk if sel_examyear else None,
                    'sb_id': sel_schoolbase.pk if sel_schoolbase else None,
                    'depbase_id': sel_depbase.pk if sel_depbase else None,
                    'experiod': sel_examperiod
                    }
        sub_list = ["SELECT exam.id, subjbase.id AS exam_subjbase_id,",
                    "CONCAT(subjbase.code,",
                        "CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' - ', lvl.abbrev) END,",
                        "CASE WHEN exam.version IS NULL OR exam.version = '' THEN NULL ",
                            "ELSE CONCAT(' - ', exam.version) END ) AS exam_name,",

                    "exam.examperiod, exam.ete_exam, exam.version, exam.has_partex, exam.partex, ",
                    "exam.amount, exam.blanks, exam.assignment, exam.keys,",
                    "exam.nex_id, exam.scalelength, exam.cesuur, exam.nterm, exam.secret_exam, exam.published_id,",
                    "ntb.omschrijving AS ntb_omschrijving",

                    "FROM subjects_exam AS exam",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

                    "LEFT JOIN subjects_ntermentable AS ntb ON (ntb.id = exam.ntermentable_id)",

                    "WHERE exam.published_id IS NOT NULL"
                    ]
        sub_exam = ' '.join(sub_list)

        sql_list = ["WITH sub_exam AS (" + sub_exam + ")",
                    "SELECT grd.id, CONCAT('grade_', grd.id::TEXT) AS mapid,",
                    "stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
                    "stud.id AS student_id, stud.lastname, stud.firstname, stud.prefix,",
                    "depbase.code AS depbase_code,",
                    "lvl.id AS level_id, lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev,",
                    "subj.id AS subj_id, subjbase.code AS subj_code, subjbase.id AS subjbase_id, subj.name_nl AS subj_name_nl,",
                    "studsubj.id AS studsubj_id, cls.id AS cluster_id, cls.name AS cluster_name,",

                    "grd.examperiod, grd.pescore, grd.cescore,",
                    "grd.ce_exam_id, grd.ce_exam_blanks, grd.ce_exam_result, grd.ce_exam_score,",
                    "grd.ce_exam_auth1by_id, grd.ce_exam_auth2by_id, grd.ce_exam_auth3by_id,",
                    "grd.ce_exam_published_id AS ce_exam_published_id, grd.ce_exam_blocked,",

                    "sub_exam.exam_name,"
                    "sub_exam.exam_subjbase_id,",
                    "sub_exam.examperiod, sub_exam.ete_exam,",
                    "sub_exam.version, sub_exam.amount,",
                    "sub_exam.has_partex, sub_exam.partex,",
                    "sub_exam.blanks, sub_exam.assignment,",
                    "sub_exam.nex_id, sub_exam.scalelength,",
                    "sub_exam.cesuur, sub_exam.nterm,",
                    "sub_exam.secret_exam, ",

                    # exam_published_id is the published ETE exam
                    "sub_exam.published_id AS exam_published_id,",
                    "sub_exam.ntb_omschrijving,",

                    "auth1.last_name AS ce_exam_auth1_usr, auth2.last_name AS ce_exam_auth2_usr,",
                    "auth3.last_name AS ce_exam_auth3_usr, publ.modifiedat AS ce_exam_publ_modat",

                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                    "LEFT JOIN sub_exam ON (sub_exam.id = grd.ce_exam_id)",

                    "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                    "LEFT JOIN subjects_cluster AS cls ON (cls.id = studsubj.cluster_id)",

                    "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                    "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                    "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                    "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                    "LEFT JOIN accounts_user AS auth1 ON (auth1.id = grd.ce_exam_auth1by_id)",
                    "LEFT JOIN accounts_user AS auth2 ON (auth2.id = grd.ce_exam_auth2by_id)",
                    "LEFT JOIN accounts_user AS auth3 ON (auth3.id = grd.ce_exam_auth3by_id)",
                    "LEFT JOIN schools_published AS publ ON (publ.id = grd.ce_exam_published_id)",

                    ''.join(("WHERE ey.id = ", str(sel_examyear.pk), "::INT")),
                    ''.join(("AND school.base_id = ", str(sel_schoolbase.pk), "::INT")),
                    ''.join(("AND dep.base_id = ", str(sel_depbase.pk), "::INT")),

                    # PR2023-01-16 added:
                    # show tobedeleted students / subjects PR2-23-02-09
                    # was:  "AND NOT stud.tobedeleted AND NOT stud.deleted",
                    #       "AND NOT studsubj.tobedeleted AND NOT studsubj.deleted",

                    "AND NOT stud.deleted AND NOT studsubj.deleted AND NOT grd.deleted",

                    # PR2023-05-05 added: only subjects with CE must be shown
                    "AND si.weight_ce > 0"
                    ]

        # PR2023-05-12 in page wolf: show only ete exams
        if ete_exams_only:
            sql_list.append("AND si.ete_exam")

        if logging_on:
            logger.debug(' sql_list: ' + str(sql_list))

        # note: don't filter on sel_subjbase_pk, must be able to change within allowed

        if grade_pk_list:
            # when grade_pk_list has value: skip subject filter
            sql_keys['grade_pk_arr'] = grade_pk_list
            sql_list.append("AND grd.id IN ( SELECT UNNEST( %(grade_pk_arr)s::INT[]))")
        else:

            if setting_dict:

                sel_examperiod = setting_dict.get(c.KEY_SEL_EXAMPERIOD)
                if sel_examperiod in (1, 2):
                    sql_keys['ep'] = sel_examperiod
                    sql_list.append(''.join(("AND grd.examperiod=", str(sel_examperiod), "::INT")))

                # filter on sel_cluster_pk happens on client.
                # filter on sel_student_pk happens on client.

# show grades that are not published only when requsr_same_school PR2021-04-29

            # - filter on selected schoolbase
            # - filter selected schoolbase_pk is required, is already part of sql
            # - validation of sel_schoolbase_pk has taken place in download_setting

            # - filter on selected depbase
            # - filter selected depbase_pk is required, is already part of sql
            # - validation of sel_depbase_pk has taken place in download_setting

            # +++ add sql_clause with selected sct, cluster an d allowed depbase, lvlbase, subj_base

            # - filter on selected sectorbase

            # - get selected sctbase_pk of req_usr
            selected_pk_dict = acc_prm.get_selected_pk_dict_of_user_instance(request.user)
            # PR 2023-04-17 Sentry error: missing FROM-clause entry for table "sct"
            # sql has no table sct, dont filter on sector:

            # - filter on selected subjectbase
            # PR2023-04-17 filtering on subj_pk takes place on client function FillTblRows()

            # - filter on selected cluster_pk
            # dont filter on allowed clusters. Allowed clusters give permit to edit and approve, but others mat be viewed
            # PR2023-04-17 filtering on selected cluster_pk takes place on client function FillTblRows()

# - get allowed_sections_dict from request
        userallowed_instance = acc_prm.get_userallowed_instance_from_request(request)
        userallowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
        if logging_on:
            logger.debug(
                '    allowed_sections_dict: ' + str(userallowed_sections_dict) + ' ' + str(
                    type(userallowed_sections_dict)))
            # allowed_sections_dict: {'2': {'1': {'4': [117, 114], '5': [], '-9': [118, 121]}}} <class 'dict'>

        # PR2023-03-27
        # when a corrector has no allowed subjects, must return None.
        # when an examiner has no allowed subjects, must return all subjects.
        return_false_when_no_allowedsubjects = acc_prm.get_return_false_when_no_allowedsubjects(req_usr)

        sql_clause = acc_prm.get_sqlclause_allowed_v2(
            table='grade',
            sel_schoolbase_pk=sel_schoolbase.pk if sel_schoolbase else None,
            sel_depbase_pk=sel_depbase.pk if sel_depbase else None,
            sel_lvlbase_pk=sel_lvlbase.pk if sel_lvlbase else None,
            userallowed_sections_dict=userallowed_sections_dict,
            return_false_when_no_allowedsubjects=return_false_when_no_allowedsubjects
        )
        if sql_clause:
            sql_list.append(sql_clause)

        if logging_on:
            logger.debug('    sql_clause: ' + str(sql_clause))

        sql_list.append('ORDER BY grd.id')

        sql = ' '.join(sql_list)

        if logging_on:
            for sql_txt in sql_list:
                logger.debug(' > ' + str(sql_txt))

        with connection.cursor() as cursor:

            cursor.execute(sql, sql_keys)
            grade_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('    len grade_rows: ' + str(len(grade_rows)))

    # - add full name to rows, and array of id's of auth
        if grade_rows:
            if logging_on:
                logger.debug('len(grade_rows): ' + str(len(grade_rows)))
            for row in grade_rows:

                if logging_on:
                    logger.debug('    row: ' + str(row))

                first_name = row.get('firstname')
                last_name = row.get('lastname')
                prefix = row.get('prefix')
                full_name = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)
                row['fullname'] = full_name if full_name else None
                ce_exam_id = row.get('ce_exam_id')
                exam_name = None

                if ce_exam_id:
                # def get_exam_name(ce_exam_id, ete_exam, subj_name, depbase_code, lvl_abbrev, examperiod, version, ntb_omschrijving):
                    exam_name = subj_vw.get_exam_name(
                        ce_exam_id=ce_exam_id,
                        ete_exam=row.get('ete_exam'),
                        subj_name_nl=row.get('subj_name_nl'),
                        depbase_code=row.get('depbase_code'),
                        lvl_abbrev=row.get('lvl_abbrev') or '-',
                        examperiod=row.get('examperiod'),
                        examyear=sel_examyear,
                        version=row.get('version'),
                        ntb_omschrijving=row.get('ntb_omschrijving')
                    )
                row['exam_name'] = exam_name


        if logging_on:
            logger.debug('---------------- ')

    return grade_rows
# --- end of create_grade_with_exam_rows


def create_grade_exam_result_rows(sel_examyear, sel_schoolbase_pk, sel_depbase, sel_department, sel_examperiod,
                                  setting_dict, request):
    # --- create grade exam rows of all students with results, also SXM of this examyear PR2022-04-27

    # - only ce_exams that are submitted have results shown
    # - group by exam and school

    # when ETE: show all CUR exams + ETE exams of SXM
    # when DOE: show all SXM exams
    # when school: show all exams of this school

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_grade_exam_result_rows -----')
        logger.debug('    setting_dict: ' + str(setting_dict))

    req_usr = request.user
    # PR2022-05-25 debug: no records were showing because ep = exemption, set to default if not in [1,2, 3]
    if sel_examperiod not in (1, 2, 3):
        sel_examperiod = c.EXAMPERIOD_FIRST
    #sql_keys = {'ey_pk': sel_examyear.pk if sel_examyear else None,
    #            'depbase_id': sel_depbase.pk if sel_depbase else None,
    #            'experiod': sel_examperiod}
    sel_examyear_pk = sel_examyear.pk if sel_examyear else None
    sel_depbase_pk = sel_depbase.pk if sel_depbase else None

    # sub_grd_result calculates score_frac and score_count
    sub_list = ["SELECT grd.id AS grd_id, ",

                "(grd.ce_exam_score::FLOAT / exam.scalelength::FLOAT) AS score_frac, ",
                "grd.ce_exam_score, exam.scalelength, "
                "1 AS score_count ",

                "FROM students_grade AS grd ",
                "INNER JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id) ",

                "WHERE grd.examperiod = ", str(sel_examperiod) , "::INT ",
                #"AND exam.ete_exam ",

                # - when ETE exam: only published exams are calculated, not applicable for DUO exams
                "AND (exam.published_id IS NOT NULL OR not exam.ete_exam) ",
                "AND exam.scalelength IS NOT NULL AND exam.scalelength > 0 ",

                # - only submitted exams are calculated
                "AND grd.ce_exam_published_id IS NOT NULL ",
                # - grade_exams with total score = null are skipped, total score = 0 is not skipped
                "AND grd.ce_exam_score IS NOT NULL "
                ]

    # - when role other than school: only submitted exams are calulated in avg, when school: also exams that are not submitted are calculated
    if req_usr.role != c.ROLE_008_SCHOOL:
        sub_list.append("AND grd.ce_exam_published_id IS NOT NULL ")

    sub_grd_result = ''.join(sub_list)

    sql_list = ["WITH grd_result AS (" + sub_grd_result + ") ",

                "SELECT exam.id AS exam_id, exam.subject_id AS subj_id, ey.code AS ey_code, ",
                "school.id AS school_id, schoolbase.code AS schoolbase_code, school.name AS school_name, ",
                "depbase.code AS depbase_code, lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev, ",
                "subjbase.code AS subj_code, subj.name_nl AS subj_name_nl, ",
                "exam.version, exam.examperiod, ",

                #"CONCAT(subj.name_nl, ",
                #"CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' - ', lvl.abbrev) END, ",
                #"CASE WHEN exam.version IS NULL OR exam.version = '' THEN NULL ELSE CONCAT(' - ', exam.version) END ) AS exam_name, ",

                "CASE WHEN exam.ete_exam THEN ",
                    "CONCAT(subj.name_nl, ",
                    "CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' ', lvl.abbrev) END, ",
                    "CASE WHEN exam.version IS NULL OR exam.version = '' THEN NULL ELSE CONCAT(' ', exam.version) END ) ",
                "ELSE CASE WHEN ntt.id IS NOT NULL THEN ntt.omschrijving ELSE '---' END ",
                "END AS exam_name, "

                "COUNT(grd.id) AS grd_count, ",
                "COUNT(grd_result.score_frac) AS result_count, ",
                "AVG(grd_result.score_frac) AS result_avg ",

                "FROM students_grade AS grd ",
                "INNER JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id) ",
                "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id) ",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id) ",

                "LEFT JOIN grd_result ON (grd_result.grd_id = grd.id) ",

                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id) ",
                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id) ",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id) ",

                "LEFT JOIN subjects_ntermentable AS ntt ON (ntt.id = exam.ntermentable_id) ",

                "INNER JOIN schools_school AS school ON (school.id = stud.school_id) ",
                "INNER JOIN schools_schoolbase AS schoolbase ON (school.base_id = schoolbase.id) ",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id) ",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id) ",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id) ",

                "WHERE grd.examperiod = ", str(sel_examperiod), "::INT ",
                "AND ey.code = ", str(sel_examyear.code), "::INT ",
                "AND dep.base_id = ", str(sel_depbase_pk), "::INT ",

                # PR2023-01-16 deleted added:
                #"AND NOT stud.tobedeleted AND NOT stud.deleted ",
                #"AND NOT studsubj.tobedeleted AND NOT studsubj.deleted ",
                #"AND NOT grd.tobedeleted AND NOT grd.deleted "

                "AND NOT stud.deleted ",
                "AND NOT studsubj.deleted ",
                "AND NOT grd.deleted "
                ]
# - schools can only view their own exams
        # when ETE: show all CUR exams + ETE exams of SXM
        # when DOE: show all SXM exams
        # when school: show all school exams
    if req_usr.role == c.ROLE_008_SCHOOL:
        sql_list.extend(("AND school.base_id = ", str(sel_schoolbase_pk), "::INT AND ey.id = ", str(sel_examyear_pk), "::INT "))
    else:
        if sel_examyear.country.abbrev == 'Sxm':
            sql_list.extend(("AND ey.id = ", str(sel_examyear_pk), "::INT "))
        elif sel_examyear.country.abbrev == 'Cur':
            sql_list.extend(("AND (exam.ete_exam OR ey.id = ", str(sel_examyear_pk), "::INT) "))

    if setting_dict:
        sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)
        if sel_department.level_req and sel_lvlbase_pk:
            sql_list.extend(("AND lvl.base_id = ", str(sel_lvlbase_pk), "::INT "))

        # get sel_subjbase_pk from sel_subject_pk
        sel_subject_pk = setting_dict.get(c.KEY_SEL_SUBJECT_PK) if setting_dict else None
        if sel_subject_pk:
            subject = subj_mod.Subject.objects.get_or_none(pk=sel_subject_pk)
            if subject and subject.base.pk:
                sql_list.extend(("AND subj.base_id = ", str(subject.base.pk), "::INT "))

    sql_list.extend(("GROUP BY exam.id, exam.subject_id, ey.code, ntt.id, ",
                     "school.id, schoolbase.code, school.name, depbase.code, lvl.base_id, lvl.abbrev, ",
                     "subjbase.code, subj.name_nl, exam.version, exam.examperiod ",
                     "ORDER BY exam.id, school.id;"))

    sql = ''.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql)
        result_rows = af.dictfetchall(cursor)

    if logging_on:
        for txt in sql_list:
            logger.debug(' > ' + str(txt))

    if result_rows:
        if logging_on:
            logger.debug('len(grade_rows): ' + str(len(result_rows)))
            #for row in result_rows:
            #    logger.debug('row: ' + str(row))

    return result_rows


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


def get_all_result_with_assignment_dict_CALC_SCORE_BLANKS(partex_str, assignment_str, keys_str, result_str):
    #PR2022-05-11
    #  ce_exam_result: "189;202#1|1;1|2;a|3;2|4;b|5;2|6;0|7;x|8;x#2|1;x|2;c|3;b|4;d|5;x#3#4"
    # This functyion calculates score and blanks from grade.ce_exam_result, without creating dict
    # its uses string as arguments, not instances
    # to be usesd in grade.update when ce_exam_result is saved

    # called by sysupdate recalc_score_of_ce_result and update_grade_instance

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- get_all_result_with_assignment_dict_CALC_SCORE_BLANKS -----')
        logger.debug('     partex_str: ' + str(partex_str))
        logger.debug('     assignment_str: ' + str(assignment_str))
        logger.debug('     keys_str: ' + str(keys_str))

# set default total_score to 0, make None when there are blanks or error.
    # This is to prevent None when all questions are not entered by student (has 'x' value)
    total_score = 0
    total_amount = 0  # total number of questions
    total_error_list = []
    entered_count = 0  # is_entered, ie score entered by school

# - get dict with assignments
    grade_partex_assignment_keys_dict = get_grade_partex_assignment_keys_dict(partex_str, assignment_str, keys_str)

    if logging_on:
        logger.debug('     grade_partex_assignment_keys_dict: ' + str(grade_partex_assignment_keys_dict))

# - error when no assignment found
    if not grade_partex_assignment_keys_dict:
        total_error_list.append('no grade_partex_assignment_keys_dict')
    else:

# - get dict with results
        all_result_dict = get_results_dict_from_result_string(result_str)
        if logging_on:
            logger.debug('     all_result_dict: ' + str(all_result_dict))

# - error when no results found
        if not all_result_dict:
            total_error_list.append('no all_result_dict')
        else:

# - get dict with all partex of result_dict
            all_result_partex_dict = all_result_dict.get('partex')
            if logging_on:
                logger.debug('     all_result_dict.get(blanks): ' + str(all_result_dict.get('blanks')))
                logger.debug('     all_result_dict.get(amount): ' + str(all_result_dict.get('amount')))
                logger.debug('     all_result_partex_dict: ' + str(all_result_partex_dict))

    # - error when result_dict exists, but has no partex
            if not all_result_partex_dict:
                total_error_list.append('result_dict has no result_partex_dict')
            else:

# +++  loop through all partex of assignment_dict
                for partex_pk, assignment_detaildict in grade_partex_assignment_keys_dict.items():
                    if logging_on:
                        logger.debug('----- ' + str(partex_pk) + ' -----  ')
                        logger.debug('     assignment_detaildict: ' + str(assignment_detaildict))
    # - error when assignment_detaildict is empty
                    if not assignment_detaildict:
                        total_error_list.append('no assignment_detaildict')
                    else:

    # - get number of questions of this partex, skip if it has no questions (dont give error)
                        partex_amount = assignment_detaildict.get('amount', 0) or 0
                        if partex_amount:
                            if logging_on:
                                logger.debug('     partex_amount: ' + str(partex_amount))

    # - add number of questions of this partex to total_amount
                            total_amount += partex_amount

    # - get result_dict of this partex
                            partex_result_dict = all_result_partex_dict.get(partex_pk)

    # - skip when partex not found in result_dict
                            if partex_result_dict:
                                if logging_on:
                                    logger.debug('     partex_result_dict: ' + str(partex_result_dict))
    # get assignment info from this partex
                                all_q_dict = assignment_detaildict.get('q')

    # +++  loop through all questions of this partex
                                for q_number in range(1, partex_amount + 1):  # range(start_value, end_value, step), end_value is not included!

                                    if logging_on:
                                        logger.debug('     q_number: ' + str(q_number))
                        # get question info from this assignment
                                    q_dict = all_q_dict.get(q_number) or {}
                                    if logging_on:
                                        logger.debug('     q_dict: ' + str(q_dict))

                            # error when there are no question info for this q_number
                                    if not q_dict:
                                        total_error_list.append('no q_dict')
                                        if logging_on:
                                            logger.debug(str(q_number) + ': >>>>  no q_dict: ' + str(q_dict))
                                    else:
                                        q_result_str = partex_result_dict.get(q_number)
                            # skip if is_not_entered, ie answer not entered by school, dont give error
                                        if q_result_str:
                                            if q_result_str == 'x':
                                                entered_count += 1  # count entered by school, score = 0
                                                if logging_on:
                                                    logger.debug(str(q_number) + ': x  entered_count: ' + str(entered_count))
                                            else:
                                                q_max_char = q_dict.get('max_char')
                                                q_max_score = q_dict.get('max_score')
                                                q_max_score_int = int(q_max_score) if q_max_score else None
                                                # min_score = int(q_dict.get('min_score', 0))
                                                q_keys = q_dict.get('keys')
                                                if logging_on:
                                                    logger.debug(str(q_number) + ':     q_dict: ' + str(q_dict))

                                   # if max_char has value, it is a multiplechoice question
                                                if q_max_char:
                                    # - each multiplechoice question needs a key, error when no key found
                                                    if not q_keys:
                                                        total_error_list.append('no q_keys')
                                                        if logging_on:
                                                            logger.debug('     no q_keys: ' + str('no q_keys'))
                                                    else:
                                                        q_max_char_lc = q_max_char.lower()
                                                        q_result_lc = q_result_str.lower()
                                                        # The ord() function returns an integer representing the Unicode character.
                                                        q_result_ord = ord(q_result_lc)
                                                        if not (ord('a') <= q_result_ord <= ord('w')):
                                                            total_error_list.append('not a <= q_result <= w')
                                                        elif q_result_ord > ord(q_max_char_lc):
                                                            total_error_list.append('q_result > q_max_char)')
                                                        else:
                                                            entered_count += 1  # count entered by school
                                                            if logging_on:
                                                                logger.debug(str(q_number) + ':   mc  entered_count: ' + str(entered_count))

                                                            # answer is correct if result_str is in q_keys
                                                            # q_keys may contain multiple characters: 'ac'
                                                            if q_result_str in q_keys:
                                                                # q_max_score may be > 1, default = 1 when not entered
                                                                if not q_max_score_int:
                                                                    q_max_score_int = 1

                                                                total_score += q_max_score_int

                                    # - max_char has no value, it is a open question
                                                else:
                                    # - each open question needs a max_score, error when no max_score found
                                                    if not q_max_score_int:
                                                        total_error_list.append('not q_max_score_int')
                                                    else:

                                                        if logging_on:
                                                            logger.debug('     q_result_str: ' + str('q_result_str'))
                                                            logger.debug('     q_result_str: ' + str(q_result_str))
                                                            logger.debug('     partex_result_dict: ' + str('partex_result_dict'))

                                                        # q_result can be '0' or even 'b'
                                                        try:
                                                            q_result_int = int(q_result_str)
                                                        except Exception as e:
                                                            total_error_list.append('error q_result_int = int(' + str(q_result_str) + ')')
                                                        else:
                                                            if q_result_int > q_max_score_int:
                                                                total_error_list.append('q_result_int > q_max_score_in')
                                                            elif q_result_int < 0:
                                                                total_error_list.append('q_result_int < 0')
                                                            else:
                                                                entered_count += 1  # count entered by school
                                                                total_score += q_result_int  # add score to total_score
                                                                if logging_on:
                                                                    logger.debug(str(q_number) + ':   int  entered_count: ' + str(entered_count))

    # +++  end of loop through all questions of this partex

    # +++  end of loop through all partex of this assignment

    # when a student has all questions wrong the total_score = 0 and will be calculated in the avergae score
    # when an error or not blanks > 0 then  total_score = None

    total_blanks = (total_amount - entered_count)

    if total_error_list or total_blanks:
        total_score = None

    if logging_on:
        logger.debug('     total_score: ' + str(total_score))
        logger.debug('     total_amount: ' + str(total_amount))
        logger.debug('     total_blanks: ' + str(total_blanks))
        logger.debug('     total_error_list: ' + str(total_error_list))

    return total_score, total_blanks, total_error_list
# - end of get_all_result_with_assignment_dict_CALC_SCORE_BLANKS


def get_grade_assignment_with_results_dict(partex_str, assignment_str, keys_str, result_str):
    # PR2022-01-29 PR2022-04-22 PR2022-05-14 PR2022-05-21 PR2023-05-25
    # called by  update_grade_instance, recalc_grade_ce_exam_score, draw_grade_exam
    #  ce_exam_result: "189;202#1|1;1|2;a|3;2|4;b|5;2|6;0|7;x|8;x#2|1;x|2;c|3;b|4;d|5;x#3#4"
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- get_grade_assignment_with_results_dict -----')

# - get dict with assignments PR2021-05-08
    grade_partex_assignment_keys_dict = \
        get_grade_partex_assignment_keys_dict(
            partex_str=partex_str,
            assignment_str=assignment_str,
            keys_str=keys_str
        )
    if logging_on:
        logger.debug('grade_partex_assignment_keys_dict: ' + str(grade_partex_assignment_keys_dict))
        """
        grade_partex_assignment_keys_dict: 
            {1: {'amount': 4, 'max_score': 20, 'name': 'Praktijkexamen onderdeel A', 
                'q': {1: {'max_char': '', 'max_score': '6', 'min_score': ''}, 
                    2: {'max_char': '', 'max_score': '4', 'min_score': ''}, 
                    3: {'max_char': '', 'max_score': '4', 'min_score': ''}, 
                    4: {'max_char': '', 'max_score': '6', 'min_score': ''}}}, 
            3: {'amount': 8, 'max_score': 12, 'name': 'Minitoets 1 BLAUW onderdeel A', 
                    'q': {1: {'max_char': 'D', 'max_score': '3', 'min_score': '', 'keys': 'ac'}, 
                        2: {'max_char': 'C', 'max_score': '2', 'min_score': '', 'keys': 'b'}, 
                        3: {'max_char': 'C', 'max_score': '1', 'min_score': '', 'keys': 'ab'}, 
                        4: {'max_char': '', 'max_score': '1', 'min_score': ''}, 
                        5: {'max_char': '', 'max_score': '1', 'min_score': ''}, 
                        6: {'max_char': '', 'max_score': '1', 'min_score': ''}, 
                        7: {'max_char': 'D', 'max_score': '1', 'min_score': '', 'keys': 'd'}, 
                        8: {'max_char': '', 'max_score': '2', 'min_score': ''}}}, 
        """


# set default assignment_total_score to 0, make None when there are blanks.
    # This is to prevent None when all questions are not entered by student (has 'x' value)
    total_amount = 0
    total_blanks = 0
    total_max_score = 0
    total_score = 0
    total_no_score = 0
    total_no_key = 0
    total_has_errors = False
    total_error_list = []

    assignment_with_results_return_dict = {
        'partex': {}
    }

# - error when no assignment found
    if not grade_partex_assignment_keys_dict:
        total_error_list.append('assignment does not exist')
    else:

# - get dict with results
        # get_results_dict_from_result_string returns {} when result_str is None
        all_result_dict = get_results_dict_from_result_string(
            result_str=result_str
        )
        if logging_on:
            logger.debug('all_result_dict: ' + str(all_result_dict))
        """           
        all_result_dict: {
            'partex': {1: {1: '2', 2: '3', 3: '4', 4: '5'}, 
                       3: {1: 'a', 2: 'b', 3: 'b', 4: '0', 5: '1', 6: 'x', 7: 'x', 8: 'x'}, 
                       4: {1: '1', 2: '1', 3: '1'}, 
                       6: {1: '1', 2: 'a', 3: '1', 4: '1', 5: '1', 6: 'a', 7: 'x'}, 
                       7: {1: '1'}, 
                       9: {1: 'a', 2: '1', 3: '1', 4: 'a', 5: 'x', 6: 'c', 7: '1'}, 
                       10: {1: '6'}, 12: {1: 'a', 2: 'a', 3: 'a', 4: '1', 5: '1', 6: 'a', 7: 'a', 8: '1'}}, 
            'blanks': 0, 
            'amount': 39}
        """

# - skip when no results found
        # don't give error when no results found: must be able to print blank result report
        all_result_partex_dict = {}
        if all_result_dict:

# - get dict with all partex of result_dict
            all_result_partex_dict = all_result_dict.get('partex') or {}
            if logging_on:
                logger.debug('all_result_partex_dict: ' + str(all_result_partex_dict))
                """
                all_result_partex_dict: 
                    {1: {1: '2', 2: '3', 3: '4', 4: '5'}, 
                     3: {1: 'a', 2: 'b', 3: 'b', 4: '0', 5: '1', 6: 'x', 7: 'x', 8: 'x'}, 
                """

# ++++++++++++  loop through all partex of assignment_dict
        for partex_pk, this_partex_assignment_keys_dict in grade_partex_assignment_keys_dict.items():
# - get assignment info from this partex of assignment_dict
            if logging_on:
                logger.debug('this_partex_assignment_keys_dict: ' + str(this_partex_assignment_keys_dict))
            """
            this_partex_assignment_keys_dict: 
                {'amount': 8, 'max_score': 12, 'name': 'Minitoets 1 BLAUW onderdeel A', 
                'q': {1: {'max_char': 'D', 'max_score': '3', 'min_score': '', 'keys': 'ac'}, 
                    2: {'max_char': 'C', 'max_score': '2', 'min_score': '', 'keys': 'b'}, 
                    3: {'max_char': 'C', 'max_score': '1', 'min_score': '', 'keys': 'ab'}, 
                    4: {'max_char': '', 'max_score': '1', 'min_score': ''}, 
                    5: {'max_char': '', 'max_score': '1', 'min_score': ''}, 
                    6: {'max_char': '', 'max_score': '1', 'min_score': ''}, 
                    7: {'max_char': 'D', 'max_score': '1', 'min_score': '', 'keys': 'd'}, 
                    8: {'max_char': '', 'max_score': '2', 'min_score': ''}}}            
            """

            this_partex_amount = 0
            this_partex_maxscore = 0
            this_partex_total_score = 0
            this_partex_has_errors = False

            this_partex_not_entered_count = 0

            this_partex_result_dict = {
                'blanks': None,
                'q': {}, # q = display value
                's': {}, # s = score
                'm': []  # m = multiple choice list
            }

# - get result_dict of this partex
            partex_result_dict = all_result_partex_dict.get(partex_pk) or {}
            if logging_on:
                logger.debug('partex_pk: ' + str(partex_pk) + ' partex_result_dict: ' + str(partex_result_dict))
                """
                partex_pk: 1 partex_result_dict: {'1': '1', '2': 'a', '3': '2', '4': 'b', '5': '2', '6': '0', '7': 'x', '8': 'x'}
                """

# - error when this_partex_assignment_keys_dict is empty
            if not this_partex_assignment_keys_dict:
                this_partex_has_errors = True
                total_error_list.append('no question found in this partial exam')

                if logging_on:
                    logger.debug(' >> this_partex_has_errors: ' + str(this_partex_has_errors))
            else:
                name = this_partex_assignment_keys_dict.get('name')
                this_partex_result_dict['name'] = name

# - skip if this partex has no questions (don't give error)
                this_partex_amount = this_partex_assignment_keys_dict.get('amount')
                if this_partex_amount:
                    this_partex_result_dict['amount'] = this_partex_amount
                    total_amount += this_partex_amount

                    this_partex_no_score = this_partex_assignment_keys_dict.get('no_score')
                    if this_partex_no_score:
                        this_partex_result_dict['no_score'] = this_partex_no_score
                        total_no_score += this_partex_no_score
                        this_partex_has_errors = True
                        if logging_on:
                            logger.debug(' >> this_partex_has_errors: ' + str(this_partex_has_errors))

                    this_partex_no_key = this_partex_assignment_keys_dict.get('no_key')
                    if this_partex_no_key:
                        this_partex_result_dict['no_key'] = this_partex_no_key
                        total_no_key += this_partex_no_key
                        this_partex_has_errors = True

                        if logging_on:
                            logger.debug(' >> this_partex_has_errors: ' + str(this_partex_has_errors))

# - add number of questions of this partex to total_amount
                    all_q_dict = this_partex_assignment_keys_dict.get('q')
                    if logging_on:
                        logger.debug('all_q_dict: ' + str(all_q_dict))
                        """
                        all_q_dict: 
                            {1: {'max_char': 'D', 'max_score': '3', 'min_score': '', 'keys': 'ac'}, 
                            4: {'max_char': '', 'max_score': '1', 'min_score': ''}, 
                        """

# ------------  loop through all questions of this partex
                    for q_number in range(1, this_partex_amount + 1):  # range(start_value, end_value, step), end_value is not included!
                        q_result_str = partex_result_dict.get(q_number) if partex_result_dict else None
                        # PR2024-06-03 debug MIL: q_result_str = 'b while question was not multiple choice
                        # solve by ignoring q_result_str when not multiple choice
                        q_dict = all_q_dict.get(q_number) or {}

                        """
                         q_dict: {'max_char': 'D', 'max_score': '3', 'min_score': '', 'keys': 'ac'}
                         q_result: a
                        """

                        if logging_on:
                            logger.debug(' ' + str( q_number) + ':  q_dict: ' + str(q_dict))
                            logger.debug('      q_result_str: ' + str( q_result_str))

                        # PR2023-05-25 debug use boolean instead of this_partex_entered_count, this_partex_not_entered_count got value -1
                        q_entered_by_school = False

                        q_score = None  # note: q_score can be 0 when student has question wrong
                        q_is_multiple_choice = False

                        if not q_dict:
                            # error when there are no assignment for this q_number
                            total_error_list.append('no assignment for question ' + str(q_number))
                            this_partex_has_errors = True
                            if logging_on:
                                logger.debug(' >> this_partex_has_errors: ' + str(this_partex_has_errors))

                            if logging_on:
                                logger.debug('      no assignment for question')
                        else:

                # - q_max_score_int
                            q_max_score = q_dict.get('max_score')
                            if logging_on:
                                logger.debug('      q_max_score: ' + str(q_max_score))

                            try:
                                q_max_score_int = int(q_max_score) if q_max_score else None
                            except:
                                q_max_score_int = None
                                this_partex_has_errors = True
                                if logging_on:
                                    logger.debug(' >> this_partex_has_errors: ' + str(this_partex_has_errors))

                                total_error_list.append(
                                    'q_max_score_int is not an integer. q_max_score: ' + str(q_max_score))
                                if logging_on:
                                    logger.debug(
                                        '      q_max_score_int is not an integer. q_max_score: ' + str(q_max_score))
                            if q_max_score_int:
                                this_partex_maxscore += q_max_score_int

                            if not q_result_str:
                                if logging_on:
                                    logger.debug('      q_result_str is None')
                                pass # is_not_entered, ie answer not entered by school

                            elif q_result_str == 'x':
                                # when a student does not answer a question or has mutiple answers in multiple choice the school enters 'x'
                                    # it is counted as q_entered_by_school
                                    q_entered_by_school = True
                                    if logging_on:
                                        logger.debug('      q_entered_by_school q=x: ' + str(q_entered_by_school))

                            else:
                                q_max_char = q_dict.get('max_char')

                                # min_score = int(q_dict.get('min_score', 0))
                                q_keys = q_dict.get('keys')
                                if logging_on:
                                    logger.debug('      q_max_score_int: ' + str(q_max_score_int))
                                    logger.debug('      q_keys: ' + str(q_keys))
                                    logger.debug('      q_max_char:  ' + str(q_max_char))

            # if max_char has value, it is a multiplechoice question
                                if q_max_char:
                                    q_is_multiple_choice = True
                                    if logging_on:
                                        logger.debug('      q_is_multiple_choice: ' + str(q_is_multiple_choice) )

                                    if not q_keys:
                                        this_partex_has_errors = True
                                        total_error_list.append('no keys in mc question ' + str(q_number))

                                        if logging_on:
                                            logger.debug(' >> this_partex_has_errors: ' + str(this_partex_has_errors))
                                            logger.debug('      no keys in mc question')
                                    else:
                                        q_max_char_lc = q_max_char.lower()
                                        q_result_lc = q_result_str.lower()
                                        # The ord() function returns an integer representing the Unicode character.
                                        q_result_ord = ord(q_result_lc)
                                        if not (ord('a') <= q_result_ord <= ord('w')) :
                                            this_partex_has_errors = True
                                            total_error_list.append('not a <= q_result <= w')

                                            if logging_on:
                                                logger.debug(' >> this_partex_has_errors: ' + str(this_partex_has_errors))
                                                logger.debug('      not a <= q_result <= w')

                                        elif q_result_ord > ord(q_max_char_lc):
                                            this_partex_has_errors = True
                                            total_error_list.append('q_result > q_max_char)')

                                            if logging_on:
                                                logger.debug(' >> this_partex_has_errors: ' + str(this_partex_has_errors))
                                                logger.debug('      q_result > q_max_char)')
                                        else:
                                            q_entered_by_school = True

                                            # q_max_score may be > 1, default = 1 when not entered
                                            if not q_max_score_int:
                                                q_max_score_int = 1

                                            # answer is correct if result_str is in q_keys
                                            # q_keys may contain multiple characters: 'ac'
                                            if q_result_str in q_keys:
                                                q_score = q_max_score_int
                                            else:
                                                q_score = 0

                                else:
            # if max_char has no value, it is not a multiplechoice question
                                    if logging_on:
                                        logger.debug('      q is not a multiple_choice ')

                                    # q_result can be '0' or even 'b' (should not be possible)
                                    try:
                                        q_result_int = int(q_result_str)

                                    except:
                                        this_partex_has_errors = True
                                        total_error_list.append('q_result_int is not an integer. q_result_str: ' + str(q_result_str))

                                        if logging_on:
                                            logger.debug(' >> this_partex_has_errors: ' + str(this_partex_has_errors))
                                            logger.debug('      q_result_int is not an integer: ' + str(q_result_str))
                                    else:
                                        if logging_on:
                                            logger.debug('      q_result_str: ' + str(q_result_str))

                                        if q_result_int > q_max_score_int:
                                            this_partex_has_errors = True
                                            total_error_list.append('score exceeds max_score in question ' + str(q_number))
                                            if logging_on:
                                                logger.debug(' >> score exceeds max_score in question: ' + str(q_result_int))

                                        elif q_result_int < 0:
                                            this_partex_has_errors = True
                                            total_error_list.append('score is fewer than zero in question ' + str(q_number))

                                            if logging_on:
                                                logger.debug(' >> score is fewer than zero in question: ' + str(q_number))
                                        else:
                                            q_entered_by_school = True

                                            q_score = q_result_int
                                            if logging_on:
                                                logger.debug('      q_score = q_result_int')
                                            if logging_on:
                                                logger.debug('      q_score = ' + str(q_result_int))

                        if logging_on:
                            logger.debug('      q_entered_by_school: ' + str(q_entered_by_school) )
                            logger.debug('      this_partex_total_score: ' + str(this_partex_total_score) )

            # add score to this_partex_total_score
                        if q_score is not None:
                            this_partex_total_score += q_score

                        if not q_entered_by_school:
                            this_partex_not_entered_count += 1

            # put score in 's' dict, when score has value. Skip None and 0
                        # 's': dict = score: contains integer, 0 or None
                        # 'q' dict = display value: contains integer, 0, letter or 'x'
                        # 'm': dict = multiple choice list
                        if q_score:
                            this_partex_result_dict['s'][q_number] = str(q_score)

                        if q_result_str:
                            this_partex_result_dict['q'][q_number] = q_result_str

                        if q_is_multiple_choice:
                            this_partex_result_dict['m'].append(q_number)

# ------------  end of loop through all questions of this partex


            # this_partex_not_entered_count = (this_partex_amount - this_partex_entered_count)

            if logging_on:
                logger.debug(' > this_partex_amount: ' + str(this_partex_amount))
                logger.debug(' > this_partex_not_entered_count: ' + str(this_partex_not_entered_count))
                logger.debug(' > this_partex_maxscore: ' + str(this_partex_maxscore))
                logger.debug(' > this_partex_total_score: ' + str(this_partex_total_score))
                logger.debug(' > this_partex_has_errors: ' + str(this_partex_has_errors))
                logger.debug(' > this_partex_not_entered_count: ' + str(this_partex_not_entered_count))

            if this_partex_has_errors:
                total_has_errors = True

            if this_partex_not_entered_count:
                total_blanks += this_partex_not_entered_count

            if this_partex_has_errors or this_partex_not_entered_count:
                this_partex_total_score = None
            else:
                total_score += this_partex_total_score

            total_max_score += this_partex_maxscore

            this_partex_result_dict['max_score'] = this_partex_maxscore
            this_partex_result_dict['blanks'] = this_partex_not_entered_count
            this_partex_result_dict['score'] = this_partex_total_score

            assignment_with_results_return_dict['partex'][partex_pk] = this_partex_result_dict

# +++  end of loop through all partex of this assignment

    # when a student has all questions wrong the total_score = 0 and will be calculated in the average score
    # when an error or not blanks > 0 then  total_score = None
    if total_has_errors or total_blanks:
        total_score = None

    assignment_with_results_return_dict['amount'] = total_amount
    assignment_with_results_return_dict['blanks'] = total_blanks
    assignment_with_results_return_dict['max_score'] = total_max_score
    assignment_with_results_return_dict['score'] = total_score
    assignment_with_results_return_dict['no_score'] = total_no_score
    assignment_with_results_return_dict['no_key'] = total_no_key

    if total_error_list:
        assignment_with_results_return_dict['errors'] = total_error_list

    if logging_on:
        logger.debug('total_max_score: ' + str(total_max_score))
        logger.debug('total_score: ' + str(total_score))
        logger.debug('total_has_errors: ' + str(total_has_errors))
        logger.debug('total_blanks: ' + str(total_blanks))
        logger.debug('assignment_with_results_return_dict: ' + str(assignment_with_results_return_dict))

    """       
    assignment_with_results_return_dict: {
        'amount': 39,
        'blanks': 0, 
        'max_score': 0, 
        'score': None, 
        'no_score': 2, 
        'no_key': 2,
         'errors': ['no max_score for question 1', 'no max_score for question 4', 'no max_score for question 1', 'no max_score for question 5']}
        'partex': {
            1: {'blanks': 0, 
                'q': {1: '6', 2: '4', 3: '3', 4: '5'}, 
                's': {1: '6', 2: '4', 3: '3', 4: '5'}, 
                'm': [], 
                'name': 'Praktijkexamen onderdeel A', 
                'amount': 4, 'max_score': 20, 'score': 18, 
                'no_score': 0}, 
            3: {'blanks': 2, 
                'q': {1: 'a', 2: 'b', 3: 'c', 4: '0', 5: '0', 6: '1', 7: 'd', 8: '2'}, 
                's': {2: '1', 6: '1', 7: '1', 8: '2'}, 
                'm': [2, 3, 7], 
                'name': 'Minitoets 1 BLAUW onderdeel A', 
                'amount': 8, 'max_score': 0, 
                'no_score': 1, 
                'no_key': 1, 
                'score': None},            
                
                
                
assignment_with_results_return_dict: {
'partex': {1: {'blanks': 0, 'q': {1: '6', 2: '4', 3: '4', 4: '5'}, 's': {1: '6', 2: '4', 3: '4', 4: '5'}, 'm': [], 
                'name': 'Praktijkexamen onderdeel A', 'amount': 4, 'max_score': 20, 'score': 19}, 
            2: {'blanks': 1, 
                'q': {1: 'c', 2: 'a', 3: 'c', 4: '0', 5: '1', 6: '0', 7: 'a', 8: '1'}, 
                's': {1: '13', 3: '1', 5: '1', 8: '1'}, 'm': [1, 3, 7], 
                'name': 'Minitoets 1 ROOD onderdeel A', 
                'amount': 8, 'max_score': 25, 'score': None}, 
4: {'blanks': 0, 'q': {1: '0', 2: '6', 3: '10'}, 's': {2: '6', 3: '10'}, 'm': [], 
'name': 'Praktijkexamen onderdeel B', 'amount': 3, 'max_score': 22, 'score': 16}, 
5: {'blanks': 0, 'q': {1: '0', 2: 'c', 3: '1', 4: '0', 5: '1', 6: 'a', 7: '1'}, 's': {3: '1', 5: '1', 7: '1'}, 'm': [2, 6], 
'name': 'Minitoets 2 ROOD onderdeel B', 'amount': 7, 'max_score': 7, 'score': 3}, 
7: {'blanks': 0, 'q': {1: '5'}, 's': {1: '5'}, 'm': [], 
'name': 'Praktijkexamen onderdeel C', 'amount': 1, 'max_score': 9, 'score': 5}, 
8: {'blanks': 0, 'q': {1: 'c', 2: '1', 3: '0', 4: 'a', 5: '2', 6: 'b', 7: '0'}, 's': {1: '1', 2: '1', 4: '1', 5: '2', 6: '1'}, 'm': [1, 4, 6], 
'name': 'Minitoets 3 ROOD onderdeel C', 'amount': 7, 'max_score': 8, 'score': 6}, 
10: {'blanks': 0, 'q': {1: '7'}, 's': {1: '7'}, 'm': [], 'name': 'Praktijkexamen onderdeel D', 'amount': 1, 'max_score': 10, 'score': 7}, 
11: {'blanks': 0, 'q': {1: 'd', 2: 'a', 3: 'c', 4: '0', 5: '0', 6: 'b', 7: 'a', 8: '0'}, 's': {1: '1', 2: '1', 3: '1', 6: '1'}, 'm': [1, 2, 3, 6, 7], 
'name': 'Minitoets 4 ROOD onderdeel D', 'amount': 8, 'max_score': 8, 'score': 4}}, 

'amount': 39, 'blanks': 1, 'max_score': 109, 'score': None, 'no_score': 0, 'no_key': 0, 'errors': ['error q_result_int = int(a)']}
           
    """
    return assignment_with_results_return_dict, total_amount, total_max_score, total_score, total_blanks, total_no_score, total_no_key
# - end of get_grade_assignment_with_results_dict


def get_grade_partex_assignment_keys_dict(partex_str, assignment_str, keys_str):  # PR2022-01-30 PR22-5-15
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- get_grade_partex_assignment_keys_dict -----')
        logger.debug('     partex_str: ' + str(partex_str))
        logger.debug('     assignment_str: ' + str(assignment_str))
        logger.debug('     keys_str: ' + str(keys_str))

    """
    partex: 1;1;15;19;Praktijktoets blauw # 2;1;12;12;Minitoets rood # 3;2;12;13;Minitoets groen
    assignment: 1;15;19|1;;4;|2;D;2;|3;;6;|4;E;;|5;;2;|6;;1;|7;;1;|8;;1;|9;;1; # 2;12;12|1;;2;|2;D;2;|3;B;;|4;E;;|5;;6; # 3;12;13|1;;2;|2;C;;|3;;2;|4;;3;|5;E;;|6;;2;|7;;2;
    keys: 1|2;b|4;d # 2|2;a|3;b|4;c # 3|2;ab|3;d|5;a
    """

# return value, is {} when one of the parameters is blank
    grade_partex_assignment_keys_dict = {}

# - create dict with assignments PR2021-05-08
    all_assignment_detail_dict, no_key_count, no_max_score_count = get_grade_assignment_detail_dict(assignment_str, keys_str)

    if logging_on:
        logger.debug('all_assignment_detail_dict -----')
        logger.debug(str(all_assignment_detail_dict))

    if all_assignment_detail_dict:

 #  create dict from partex_str
        if partex_str:
            for pp in partex_str.split('#'):
                if pp:
                    pp_arr = pp.split(';')
                    # each partex contains partex_pk, partex_examperiod, partex_amount, max_score, partex_name
                    partex_pk = int(pp_arr[0])
                    partex_dict = {
                        'amount': int(pp_arr[2]),
                        'max_score': int(pp_arr[3]),
                        'name': pp_arr[4],
                    }
                    partex_assignment_detail_dict = all_assignment_detail_dict.get(partex_pk)
                    if partex_assignment_detail_dict:
                        no_score = partex_assignment_detail_dict.get('no_score')
                        if no_score:
                            partex_dict['no_score'] = no_score
                        no_key = partex_assignment_detail_dict.get('no_key')
                        if no_key:
                            partex_dict['no_key'] = no_score

                        partex_dict['q'] = partex_assignment_detail_dict

                    grade_partex_assignment_keys_dict[partex_pk] = partex_dict

        if logging_on:
            logger.debug( 'grade_partex_assignment_keys_dict: ' + str(grade_partex_assignment_keys_dict) + ' ' + str(type(grade_partex_assignment_keys_dict)))
        """
        grade_partex_assignment_keys_dict: {
            1: {'amount': 4, 'max_score': 20, 'name': 'Praktijkexamen onderdeel A', 
                'q': {1: {'max_score': '6'}, 2: {'max_score': '4'}, 3: {'max_score': '4'}, 4: {'max_score': '6'}}}, 
            3: {'amount': 8, 'max_score': 0, 'name': 'Minitoets 1 BLAUW onderdeel A', 'no_score': 1, 'no_key': 1, 
                'q': {2: {'max_char': 'C', 'max_score': '1', 'keys': 'b'}, 
                      3: {'max_char': 'C', 'max_score': '1', 'keys': 'b'}, 5: {'max_score': '1'}, 6: {'max_score': '1'}, 7: {'max_char': 'D', 'max_score': '1', 'keys': 'd'}, 8: {'max_score': '2'}, 'no_score': 1, 'no_key': 1}}, 
            4: {'amount': 3, 'max_score': 22, 'name': 'Praktijkexamen onderdeel B', 
                'q': {1: {'max_score': '6'}, 2: {'max_score': '6'}, 3: {'max_score': '10'}}}, 
        """
    return grade_partex_assignment_keys_dict
# - end of get_grade_partex_assignment_keys_dict


def get_results_dict_from_result_string(result_str):  # PR2022-01-30
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('   ')
        logger.debug('----- get_results_dict_from_result_string -----')
        logger.debug('result_str: ' + str(result_str))
        """
        result_str: 27;39#1|1;2|2;3|3;4|4;5#3|1;a|2;b|3;b|4;0|5;1|6;x|7;x|8;x#4#6#7#9#10#12
        """

# - loop through result_str
    # dont add 'partex' key here, because on empty all_result_dict must retirn False. {} returns False
    # was: all_result_dict = {'partex': {}}
    all_result_dict = {}
    if result_str:
        partex_result_arr = result_str.split('#')
        if logging_on:
            logger.debug('-----------------------------')
            logger.debug('partex_result_arr: ' + str(partex_result_arr))

        is_first_row = True
        for r_str in partex_result_arr:
            if r_str:
                # first item contains blanks ; total_amount
                # r_str: 189;202
                #  r_str: 1|1;1|2;a|3;2|4;b|5;2|6;0|7;x|8;x

                if is_first_row:
                    is_first_row = False
                # first item contains [blanks ; total_amount]
                    r_arr = r_str.split(';')
                    # r_arr = [ 189, 202 ]
                    if r_arr:
                        all_result_dict['blanks'] = int(r_arr[0]) if r_arr[0] else None
                        all_result_dict['amount'] = int(r_arr[1]) if r_arr[1] else None
                else:
                    this_partex_dict = {}
                    r_arr = r_str.split('|')
                    if logging_on:
                        logger.debug('r_arr: ' + str(r_arr))
                        """
                            r_arr: ['1', '1;1', '2;a', '3;2', '4;b', '5;2', '6;0', '7;x', '8;x']
                        """
                    if r_arr:
                        is_first_r_row = True
                        partex_pk = None
                        this_result_dict = {}
                        for q_str in r_arr:
                            if is_first_r_row:
                                is_first_r_row = False
                                partex_pk = int(r_arr[0])
                            else:
                                q_arr = q_str.split(';')
                                if q_arr:
                                    q_number = int(q_arr[0]) if q_arr[0] else None
                                    q_result = q_arr[1] if q_arr[1] else None
                                    if q_number:
                                        this_result_dict[q_number] = q_result

                        if 'partex' not in all_result_dict:
                            all_result_dict['partex'] = {}

                        all_result_dict['partex'][partex_pk] = this_result_dict

    if logging_on:
        logger.debug('all_result_dict: ' + str(all_result_dict))
        """
        all_result_dict: {
            'partex': {1: {1: '2', 2: '3', 3: '4', 4: '5'}, 
                       3: {1: 'a', 2: 'b', 3: 'b', 4: '0', 5: '1', 6: 'x', 7: 'x', 8: 'x'}, 
            'blanks': 27, 
            'amount': 39}
        """
    return all_result_dict
# - end of get_results_dict_from_result_string


def get_grade_assignment_detail_dict(assignment_str, keys_str):
    # - create dict with assignments and keys PR2022-01-30  PR2022-05-20
    # only called by get_grade_partex_assignment_keys_dict

# get_all_keys_dict_from_string returns {} when keys_str is None
    all_keys_dict = get_all_keys_dict_from_string(keys_str)

    """
    partex: "1;1;4;20;Praktijkexamen onderdeel A # 3;1;8;12;Minitoets 1 BLAUW onderdeel A # ...
    format of partex_str is:
        partex are divided by "#"
            each item of partex contains: partex_pk ; partex_examperiod ; partex_amount ; max_score ; partex_name #

    assignment: "1;4;20|1;;6;|2;;4;|3;;4;|4;;6; # 3;8;12|1;D;3;|2;C;2;|3;C;;|4;;1;|5;;1;|6;;1;|7;D;;|8;;2; # ...
    format of assignment_str is:
        partex are divided by "#"
            first item of partex contains partex info: partex_pk ; partex_amount ; max_score |
            other items =  | q_number ; max_char ; max_score ; min_score |

    keys: "1 # 3|1;ac|2;b|3;ab|7;d # ...
    format of keys_str is:
        partex are divided by "#"
            first item of partex contains partex_pk |
            other items =  | q_number ; keys |
    """
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- get_grade_assignment_detail_dict -----')
        logger.debug('assignment_str: ' + str(assignment_str) + ' ' + str(type(assignment_str)))
        logger.debug('keys_str: ' + str(keys_str) + ' ' + str(type(keys_str)))

# return value is {} when assignment_str is blank
    all_assignment_dict = {}

    no_key_count = 0
    no_max_score_count = 0

    if assignment_str:
        # pa is the assignment of a partial exam
        for pa in assignment_str.split('#'):
            if pa:
                assignment_dict = {}
                partex_pk = None

                partex_no_key_count = 0
                partex_no_max_score_count = 0

                # pa: 1;15;19 | 1;;4; | 2;D;2; | 3;;6; | 4;E;; | 5;;2; | 6;;1; | 7;;1; | 8;;1; | 9;;1;

                pa_arr = pa.split('|')
                if pa_arr:
                    """
                    when no score: the key/value of that question is missing. Loop through number of questions
                    pa_arr: ['5;10;0', '2;D;;', '3;D;;', '4;D;;', '6;;1;', '7;;1;', '8;;1;', '9;C;;', '10;C;;']
                    """
                    # first item contains partex_pk, amount and max_score
                    info_str = pa_arr[0]
                    partex_amount = 0
                    if info_str:
                        info_arr = info_str.split(';')
                        partex_pk = int(info_arr[0])
                        partex_amount = int(info_arr[1])

                    # create list of question numbers, to check for missing values.
                    q_list = []
                    for q in range(1, partex_amount + 1):  # range(start_value, end_value, step), end_value is not included!
                        q_list.append(q)

                    # all_keys_dict: {1: {2: 'b', 4: 'd'}, 2: {2: 'a', 3: 'b', 4: 'c'}, 3: {2: 'ab', 3: 'd', 5: 'a'}}
                    if all_keys_dict and partex_pk in all_keys_dict:
                        keys_dict = all_keys_dict[partex_pk]
                    else:
                        keys_dict = None

                    skip_first = True
                    for qa in pa_arr:
                        # qa: 1;C;22;
                        # first item contains partex_pk, amount and max_score
                        if skip_first:
                            skip_first = False
                        else:
                            qa_arr = qa.split(';')

                            # qa_arr: ['2', 'D', '2', '']  q_number, max_char, max_score, min_score
                            if len(qa_arr) == 4:
                                q_number = int(qa_arr[0])

                                # q is found, remove from q_list
                                if q_number in q_list:
                                    q_list.remove(q_number)

                                max_char = qa_arr[1] if qa_arr[1] else ''
                                max_score_str = qa_arr[2] if qa_arr[2] else ''
                                min_score_str = qa_arr[3] if qa_arr[3] else ''

                                q_dict = {}

                                if max_char:
                                    # default max_score when multiple choice is '1', set to '1' when field is blank
                                    if not max_score_str:
                                        max_score_str = '1'

                                    keys = keys_dict.get(q_number) if keys_dict else None
                                    if keys:
                                        q_dict['max_char'] = max_char
                                        q_dict['max_score'] = max_score_str
                                        q_dict['keys'] = keys

                                    else:
                                        partex_no_key_count += 1
                                        no_key_count += 1

                                else:
                                    if max_score_str and int(max_score_str):
                                        q_dict['max_score'] = max_score_str
                                    else:
                                        partex_no_max_score_count += 1
                                        no_max_score_count += 1

                                if min_score_str:
                                    q_dict['min_score_str'] = min_score_str

                                if q_dict:
                                    assignment_dict[q_number] = q_dict

                    missing_questions_count = len(q_list)
                    if missing_questions_count:
                        partex_no_max_score_count += missing_questions_count
                        no_max_score_count += missing_questions_count

                if partex_no_max_score_count:
                    assignment_dict['no_score'] = partex_no_max_score_count

                if partex_no_key_count:
                    assignment_dict['no_key'] = partex_no_key_count

                all_assignment_dict[partex_pk] = assignment_dict
    if logging_on:
        logger.debug('all_assignment_dict: ' + str(all_assignment_dict))
    """
    all_assignment_dict: {
    1: {1: {'max_score': '6'}, 2: {'max_score': '4'}, 3: {'max_score': '4'}, 4: {'max_score': '6'}}, 
    3: {2: {'max_char': 'C', 'max_score': '1', 'keys': 'b'}, 
        3: {'max_char': 'C', 'max_score': '1', 'keys': 'b'}, 
        5: {'max_score': '1'}, 6: {'max_score': '1'}, 
        7: {'max_char': 'D', 'max_score': '1', 'keys': 'd'}, 
        8: {'max_score': '2'}, 'no_score': 1, 'no_key': 1}, 
    4: {1: {'max_score': '6'}, 2: {'max_score': '6'}, 3: {'max_score': '10'}}, 
    6: {1: {'max_score': '1'}, 2: {'max_char': 'D', 'max_score': '1', 'keys': 'b'}, 
        3: {'max_score': '1'}, 4: {'max_score': '1'}, 5: {'max_score': '1'}, 
        6: {'max_char': 'D', 'max_score': '1', 'keys': 'b'}, 7: {'max_score': '1'}}, 
    7: {1: {'max_score': '9'}}, 
    9: {2: {'max_score': '1'}, 3: {'max_score': '1'}, 
        4: {'max_char': 'D', 'max_score': '1', 'keys': 'c'}, 
        6: {'max_char': 'D', 'max_score': '1', 'keys': 'a'}, 
        7: {'max_score': '1'}, 'no_score': 1, 'no_key': 1}, 
        10: {1: {'max_score': '10'}}, 
    12: {1: {'max_char': 'D', 'max_score': '1', 'keys': 'a'}, 2: {'max_char': 'D', 'max_score': '1', 'keys': 'b'}, 
        3: {'max_char': 'C', 'max_score': '1', 'keys': 'a'}, 4: {'max_score': '1'}, 5: {'max_score': '1'}, 
        6: {'max_char': 'D', 'max_score': '1', 'keys': 'd'}, 7: {'max_char': 'D', 'max_score': '1', 'keys': 'd'}, 
        8: {'max_score': '1'}}}
    """
    return all_assignment_dict, no_key_count, no_max_score_count
# - end of get_grade_assignment_detail_dict


def get_all_keys_dict_from_string(keys_str):
    #  keys: 1|2;b|4;d # 2|2;a|3;b|4;c # 3|2;ab|3;d|5;a
    all_keys_dict = {}
    if keys_str:
        for ka in keys_str.split('#'):
            # ka is the keys of a partial exam
            #  ka: 2|2;a|3;b|4;c
            if ka:
                ka_arr = ka.split('|')
                if ka_arr:
                    # first item contains partex_pk
                    partex_pk = int(ka_arr[0])
                    keys_dict = {}
                    skip_first = True
                    for kq in ka.split('|'):
                        # skip first item, it contains partex_pk
                        if skip_first:
                            skip_first = False
                        else:
                            # kq[0] = partex_number
                            #  kq{1] etc : 2;a  q_number ; keys (a,b,c etc)
                            kq_arr = kq.split(';')
                            if len(kq_arr) > 0:
                                q_number = int(kq_arr[0])
                                keys_dict[q_number] = kq_arr[1]
                    all_keys_dict[partex_pk] = keys_dict

                # keys_dict: {2: 'ab', 3: 'd', 5: 'a'} <class 'dict'>
    # all_keys_dict: {1: {2: 'b', 4: 'd'}, 2: {2: 'a', 3: 'b', 4: 'c'}, 3: {2: 'ab', 3: 'd', 5: 'a'}}

    return all_keys_dict
# - end of get_all_keys_dict_from_string


def get_exam_assignment_detail_dict(assignment_str, keys_str):
    # - create dict with assignments and keys PR2022-01-27  PR2022-05-20
    # only called by get_grade_partex_assignment_keys_dict

    logging_on = False  # s.LOGGING_ON

    """
    partex: "1;1;4;20;Praktijkexamen onderdeel A # 3;1;8;12;Minitoets 1 BLAUW onderdeel A # ...
    format of partex_str is:
        partex are divided by "#"
            each item of partex contains: partex_pk ; partex_examperiod ; partex_amount ; max_score ; partex_name #

    assignment: "1;4;20|1;;6;|2;;4;|3;;4;|4;;6; # 3;8;12|1;D;3;|2;C;2;|3;C;;|4;;1;|5;;1;|6;;1;|7;D;;|8;;2; # ...
    format of assignment_str is:
        partex are divided by "#"
            first item of partex contains partex info: partex_pk ; partex_amount ; max_score |
            other items =  | q_number ; max_char ; max_score ; min_score |

    keys: "1 # 3|1;ac|2;b|3;ab|7;d # ...
    format of keys_str is:
        partex are divided by "#"
            first item of partex contains partex_pk |
            other items =  | q_number ; keys |
    """

    # get_all_keys_dict_from_string returns {} when keys_str is None
    all_keys_dict = get_all_keys_dict_from_string(keys_str)
    if logging_on:
        logger.debug('all_keys_dict: ' + str(all_keys_dict) + ' ' + str(type(all_keys_dict)))

    all_assignment_dict = {}

    no_key_count = 0
    no_max_score_count = 0

    if assignment_str:
        # pa is the assignment of a partial exam
        for pa in assignment_str.split('#'):
            if pa:
                assignment_dict = {}
                partex_pk = None

                partex_no_key_count = 0
                partex_no_max_score_count = 0

                # pa: 1;15;19 | 1;;4; | 2;D;2; | 3;;6; | 4;E;; | 5;;2; | 6;;1; | 7;;1; | 8;;1; | 9;;1;

                pa_arr = pa.split('|')
                if pa_arr:
                    if logging_on:
                        logger.debug('pa_arr: ' + str(pa_arr))
                        """
                        when no score: the key/value of that question is missing. Loop through number of questions
                        pa_arr: ['5;10;0', '2;D;;', '3;D;;', '4;D;;', '6;;1;', '7;;1;', '8;;1;', '9;C;;', '10;C;;']
                        """
                    # first item contains partex_pk, amount and max_score
                    info_str = pa_arr[0]
                    partex_amount = 0
                    if info_str:
                        info_arr = info_str.split(';')
                        partex_pk = int(info_arr[0])
                        partex_amount = int(info_arr[1])

                    # create list of question numbers, to check for missing values.
                    q_list = []
                    for q in range(1, partex_amount + 1):  # range(start_value, end_value, step), end_value is not included!
                        q_list.append(q)

                    # all_keys_dict: {1: {2: 'b', 4: 'bd'}, 2: {2: 'a', 3: 'b', 4: 'c'}, 3: {2: 'ab', 3: 'd', 5: 'a'}}
                    if all_keys_dict and partex_pk in all_keys_dict:
                        keys_dict = all_keys_dict.get(partex_pk)
                    else:
                        keys_dict = None

                    skip_first = True
                    for qa in pa_arr:
                        # qa: 1;C;22;
                        # first item contains partex_pk, amount and max_score
                        if skip_first:
                            skip_first = False
                        else:
                            qa_arr = qa.split(';')
                            # qa_arr: ['2', 'D', '2', '']  q_number, max_char, max_score, min_score

                            if len(qa_arr) == 4:
                                q_number = int(qa_arr[0])

                                # q is found, remove from q_list
                                if q_number in q_list:
                                    q_list.remove(q_number)

                                max_char = qa_arr[1] if qa_arr[1] else ""
                                max_score_str = qa_arr[2] if qa_arr[2] else ""
                                min_score_str = qa_arr[3] if qa_arr[3] else ""

                                q_value = ''

                                if max_char:
                                    # default max_score when multiple choice is '1', set to '1' when field is blank
                                    if not max_score_str:
                                        max_score_str = '1'

                                    q_value = max_char

                                    keys = keys_dict.get(q_number) if keys_dict else None
                                    if keys:
                                        q_value += ' - ' + keys
                                        if max_score_str:
                                            q_value += ' - ' + max_score_str
                                    else:
                                        partex_no_key_count += 1
                                        no_key_count += 1

                                else:
                                    if max_score_str and int(max_score_str):
                                        q_value = max_score_str
                                    else:
                                        partex_no_max_score_count += 1
                                        no_max_score_count += 1

                                if min_score_str:
                                    q_value += ' min: ' + min_score_str
                                assignment_dict[q_number] = q_value

                    missing_questions_count = len(q_list)
                    if missing_questions_count:
                        partex_no_max_score_count += missing_questions_count
                        no_max_score_count += missing_questions_count

                if partex_no_max_score_count:
                    assignment_dict['no_score'] = partex_no_max_score_count

                if partex_no_key_count:
                    assignment_dict['no_key'] = partex_no_key_count

                all_assignment_dict[partex_pk] = assignment_dict

    if logging_on:
        logger.debug('all_assignment_dict: ' + str(all_assignment_dict))
        logger.debug('>>>>>>>>>>> no_key_count: ' + str(no_key_count))
        logger.debug('no_max_score_count: ' + str(no_max_score_count))
    """
    all_assignment_dict: {
        1: {1: '12', 2: '8', 3: '5'}, 
        2: {1: '30'}, 
        3: {1: '11', 2: '8', 3: '6', 4: '20'}, 
        5: {1: '1', 2: 'D - d - 1', 3: 'D - c - 1', 4: 'D - c - 1', 6: '1', 7: '1', 8: '1', 9: 'C - c - 1', 10: 'C - b - 1', 
            'no_score': 1}, 
        7: {1: '1', 2: 'C - c - 1', 3: 'C - a - 1', 4: '1', 5: '1', 6: 'D - b - 1', 7: '1', 8: 'D - a - 1', 9: 'D - a - 1', 10: '1'}, 
        9: {1: 'C - a - 1', 2: 'F - a - 1', 3: 'C - a - 1', 4: 'C - a - 1', 5: '1', 6: '2', 7: 'C - a - 1', 8: 'D', 9: '1',
            'no_key': 1}}
        no_key_count: 1
        no_max_score_count: 1
    """
    return all_assignment_dict, no_key_count, no_max_score_count
# - end of get_exam_assignment_detail_dict

###################################


def calc_amount_and_scalelength_of_assignment(exam):
    # PR2022-05-02 PR2022-05-20
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' --------- calc_amount_and_scalelength_of_assignment -------------')
        logger.debug('exam: ' + str(exam))

    """
    partex: "1;1;4;20;Praktijkexamen onderdeel A # 3;1;8;12;Minitoets 1 BLAUW onderdeel A # ...
    format of partex_str is:
        partex are divided by "#"
            each item of partex contains: partex_pk ; partex_examperiod ; partex_amount ; max_score ; partex_name #

    assignment: "1;4;20|1;;6;|2;;4;|3;;4;|4;;6; # 3;8;12|1;D;3;|2;C;2;|3;C;;|4;;1;|5;;1;|6;;1;|7;D;;|8;;2; # ...
    format of assignment_str is:
        partex are divided by "#"
            first item of partex contains partex info: partex_pk ; partex_amount ; max_score |
            other items =  | q_number ; max_char ; max_score ; min_score |

    keys: "1 # 3|1;ac|2;b|3;ab|7;d # ...
    format of keys_str is:
        partex are divided by "#"
            first item of partex contains partex_pk |
            other items =  | q_number ; keys |
    """
    e_scalelength = getattr(exam, 'scalelength')
    e_amount = getattr(exam, 'amount')
    e_blanks = getattr(exam, 'blanks')

    partex_str = getattr(exam, 'partex')
    assignment_str = getattr(exam, 'assignment')
    keys_str = getattr(exam, 'keys')  # keys_str is only used to check if multiple choice questioon has keys

    assignment_dict = get_grade_partex_assignment_keys_dict(partex_str, assignment_str, keys_str)

    """
     assignment_dict: {
     1: {'amount': 3, 'max_score': 25, 'name': 'Praktijkexamen onderdeel A', 
            'q': {1: {'max_char': '', 'max_score': '12', 'min_score': ''}, 
                    2: {'max_char': '', 'max_score': '8', 'min_score': ''}, 
                    3: {'max_char': '', 'max_score': '5', 'min_score': ''}}}, 
     5: {'amount': 10, 'max_score': 10, 'name': 'Minitoets 1 BLAUW Onderdeel A', 
            'q': {1: {'max_char': '', 'max_score': '1', 'min_score': ''}, 
                 10: {'max_char': 'C', 'max_score': '1', 'min_score': '', 'keys': 'b'}}}, 
    , 
      9: {'amount': 9, 'max_score': 10, 'name': 'Minitoets 3 BLAUW Onderdeel C',
            'q': {1: {'max_char': 'C', 'max_score': '1', 'min_score': '', 'keys': 'a'}, 
            >>> keys is missing in this one <<<
               2: {'max_char': 'F', 'max_score': '1', 'min_score': ''}, 
               3: {'max_char': 'C', 'max_score': '1', 'min_score': ''}, 
    """

    if logging_on:
        logger.debug('assignment_dict: ' + str(assignment_dict))

    total_amount = 0
    total_maxscore = 0
    total_entered = 0
    has_changed = False
    total_keys_missing = 0

    for partex_dict in assignment_dict.values():

        # note: p_maxscore of each partex is calculated on client side and stored in assignment
        # there is no check if p_maxscore equals the sum of scores in the assignment_str

        # p_amount is entered value of number of questions in partex
        p_amount = partex_dict.get('amount')

        # was: p_maxscore = partex_dict.get('max_score')
        q_dict = partex_dict.get('q')

        if p_amount:
            total_amount += p_amount
            for q_number in range(1, p_amount + 1):  # range(start_value, end_value, step), end_value is not included!
                q = q_dict.get(q_number) or {}
                if q:
                    q_max_char = q.get('max_char')
                    q_max_score = q.get('max_score')
                    if q_max_char:
                        # give error if keys does not exist
                        if 'keys' not in q:
                            total_keys_missing += 1
                        else:
                        # default score of multiple choice is 1
                            if not q_max_score:
                                q_max_score = 1

                            q_maxscore_int = int(q_max_score)
                            total_maxscore += q_maxscore_int
                            total_entered += 1
                    else:
                        if q_max_score:
                            q_maxscore_int = int(q_max_score)
                            total_maxscore += q_maxscore_int
                            total_entered += 1

    if logging_on:
        logger.debug('e_amount:      ' + str(e_amount) +     ' total_amount:   ' + str(total_amount))
        logger.debug('e_scalelength: ' + str(e_scalelength) + ' total_maxscore: ' + str(total_maxscore))


# set total_maxscore = 0 when exam has questions that are not entered
    total_blanks = total_amount - total_entered
    if total_blanks > 0 or total_keys_missing > 0:
        total_maxscore = None

    if total_amount != e_amount or total_maxscore != e_scalelength or total_blanks != e_blanks:
        has_changed = True

    if logging_on:
        logger.debug('     total_amount:   ' + str(total_amount))
        logger.debug('     total_maxscore: ' +str(total_maxscore))
        logger.debug('     total_entered:   ' +str(total_entered))
        logger.debug('     total_blanks:   ' +str(total_blanks))
        logger.debug('     total_keys_missing:   ' +str(total_keys_missing))
        logger.debug('     has_changed:    ' +str(has_changed))

    return total_amount, total_maxscore, total_blanks, total_keys_missing, has_changed
# - end of calc_amount_and_scalelength_of_assignment


def recalc_grade_ce_exam_score(exam_pk_list):
    # PR2022-05-15 # debug: Yolande van Erven Ancilla Domini : pescore not calculated. recalc missing pescore
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ------- recalc_grade_ce_exam_score -------')
        logger.debug('exam_pk_list: ' + str(exam_pk_list))

# create list of grades that must be recalculated
    tobeupdated_grade_rows = []

    #try:
    if True:
        sql_keys = {'exam_pk_list': exam_pk_list}
        sql_list = ["SELECT grd.id, grd.ce_exam_result, exam.partex, exam.assignment, exam.keys",
                    "FROM students_grade AS grd",
                    "INNER JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id)",
                    "WHERE grd.ce_exam_id IN (SELECT UNNEST( %(exam_pk_list)s::INT[]))"
                    "AND (grd.ce_exam_blanks IS NULL OR grd.ce_exam_blanks = 0)",
                    "AND NOT grd.tobedeleted AND NOT grd.deleted"]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

        for row in rows:
            grade_pk = row.get('id')
            partex_str = row.get('partex')
            assignment_str = row.get('assignment')
            keys_str = row.get('keys')
            result_str = row.get('ce_exam_result')

            #total_score, xtotal_blanks, xtotal_has_errors = \
            #    get_all_result_with_assignment_dict_CALC_SCORE_BLANKS(
            #        partex_str=partex_str,
            #        assignment_str=assignment_str,
            #        keys_str=keys_str,
            #        result_str=result_str
            #    )
            #if logging_on:
            #    logger.debug('xtotal_score: ' + str(xtotal_score) + ' xtotal_blanks: ' + str(xtotal_blanks) + \
            #                 ' xtotal_has_errors: ' + str(xtotal_has_errors))

            # create list of results
            all_result_dictNIU, total_amountNIU, max_scoreNIU, total_score, total_blanks, total_no_scoreNIU, total_no_keyNIU = \
                get_grade_assignment_with_results_dict(
                    partex_str=partex_str,
                    assignment_str=assignment_str,
                    keys_str=keys_str,
                    result_str=result_str
                )
            tobeupdated_grade_rows.append([grade_pk, total_score, total_blanks])

    #except Exception as e:
    #    logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('tobeupdated_grade_rows: ' + str(tobeupdated_grade_rows))


    updated_grade_rows = []
    if tobeupdated_grade_rows:
        #try:
        if True:
            sql_list = ["CREATE TEMP TABLE gr_update (grade_id, ce_score, ce_blanks) AS",
                        "VALUES (0::INT, 0::INT, 0::INT)"]

            for row in tobeupdated_grade_rows:
                grade_pk_str = str(row[0])
                score_str = str(row[1]) if row[1] is not None else 'NULL'
                blanks_str = str(row[2]) if row[2] else 'NULL'

                sql_list.append(''.join((", (", grade_pk_str, ", ", score_str, ", ", blanks_str, ")")))

            sql_list.extend((
                "; UPDATE students_grade AS gr",
                "SET ce_exam_score = gr_update.ce_score, ce_exam_blanks = gr_update.ce_blanks",
                "FROM gr_update",
                "WHERE gr_update.grade_id = gr.id",
                "RETURNING gr.id, gr.ce_exam_score, gr.ce_exam_blanks;"
            ))

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql: ' + str(sql))
            """
            sql: CREATE TEMP TABLE gr_update (grade_id, ce_score, ce_blanks) AS 
            VALUES (0::INT, 0::INT, 0::INT) , (36742, NULL, NULL) , 
            (36702, NULL, NULL) , (36662, NULL, NULL) , (22519, NULL, NULL) , 
            (22459, NULL, NULL) ; UPDATE students_grade AS gr SET ce_exam_score = gr_update.ce_score, ce_exam_blanks = gr_update.ce_blanks FROM gr_update WHERE gr_update.grade_id = gr.id RETURNING gr.id, gr.ce_exam_score;

            """


            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        updated_grade_rows.append(row[0])
                        # add studsubj_pk to list, to udate has_exemption later

                        if row[1] not in updated_grade_rows:
                            updated_grade_rows.append(row[1])
                        # row: (61180, '7.1')



        #except Exception as e:
        #    logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('updated_grade_rows: ' + str(updated_grade_rows))
    return updated_grade_rows

# - end of recalc_grade_ce_exam_score
