# PR2020-09-17 PR2021-01-27
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils import timezone
from django.utils.translation import activate, gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.generic import View

from timeit import default_timer as timer

from accounts import views as acc_view
from accounts import permits as acc_prm
from accounts import correctors as acc_corr

from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import validators as val
from awpr import locale as loc

from schools import models as sch_mod
from schools import functions as sch_fnc
from schools import dicts as school_dicts
from subjects import models as subj_mod
from subjects import views as sj_vw
from subjects import orderlists as sj_ol
from students import models as stud_mod
from students import views as stud_view
from  students import functions as stud_fnc
from grades import views as gr_vw

import json

import logging
logger = logging.getLogger(__name__)


# === DatalistDownloadView ===================================== PR2019-05-23
@method_decorator([login_required], name='dispatch')
class DatalistDownloadView(View):  # PR2019-05-23
    #logging.disable(logging.CRITICAL)  # logging.CRITICAL disables logging calls with levels <= CRITICAL
    logging.disable(logging.NOTSET)  # logging.NOTSET re-enables logging

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ++++++++++++++++++++ DatalistDownloadView ++++++++++++++++++++ ')

        starttime = timer()
        datalists = {}
        message_list = []

        if request.user and request.user.country and  request.user.schoolbase:
            if request.POST['download']:


# once only function converts allowed deps, levels and subjects to a dict and stores it in allword_schools PR2022-11-23
                # af.convertAllowedSectionsONCEONLY(request)

# ----- get user_lang
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# ----- get datalist_request
                datalist_request = json.loads(request.POST['download'])
                if logging_on:
                    logger.debug('    datalist_request: ' + str(datalist_request) + ' ' + str(type(datalist_request)))

# ----- get user permits and settings -- first get settings, these are used in other downloads
                # download_setting will update usersetting with items in request_item_setting, and retrieve saved settings
                request_item_setting = datalist_request.get('setting')
                if logging_on:
                    logger.debug('request_item_setting: ' + str(request_item_setting) + ' ' + str(type(request_item_setting)))

                new_setting_dict, permit_dict, sel_examyear, sel_schoolbase, sel_school, sel_depbase, sel_lvlbase, \
                    sel_examperiod, sel_examtype, msg_list = \
                        download_setting(request_item_setting, user_lang, request)
                if msg_list:
                    message_list.extend(msg_list)

                if sel_examyear is None:
                   message_list.append({'msg_html':
                                            [str(_('No exam year selected.'))], 'class': 'border_bg_warning'})
                if sel_depbase is None:
                   message_list.append({'msg_html': [str(_('No department selected.'))], 'class': 'border_bg_warning'})

                if logging_on:
                    logger.debug('    message_list: ' + str(message_list))

                requsr_same_school = permit_dict.get('requsr_same_school', False)

    # PR2021-11-03 was:
                #if permit_dict:
                #    datalists['permit_dict'] = permit_dict

                # only add setting_dict to datalists when called by request_item_setting 'setting'
                # PR2021-11-03 also only add permit_dict when by request_item_setting 'setting'
                # - because permys were lost when refreshing mailbox page.
                # - might cause other problems?
                if request_item_setting and new_setting_dict:
                    datalists['setting_dict'] = new_setting_dict
                    datalists['permit_dict'] = permit_dict
                if logging_on:
                    logger.debug('new_setting_dict: ' + str(new_setting_dict) + ' ' + str(type(new_setting_dict)))

# ----- get school settings (includes import settings)
                request_item_schoolsetting = datalist_request.get('schoolsetting')
                if request_item_schoolsetting:
                    datalists['schoolsetting_dict'] = sch_fnc.get_schoolsettings(
                        request, request_item_schoolsetting, sel_examyear, sel_schoolbase, sel_depbase)
                if logging_on:
                    logger.debug('request_item_schoolsetting: ' + str(request_item_schoolsetting) + ' ' + str(type(request_item_schoolsetting)))

# ----- run system_updates if necessary
                af.system_updates(sel_examyear, request)

# ----- locale
                request_item_locale = datalist_request.get('locale')
                if request_item_locale:
                    datalists['locale_dict'] = loc.get_locale_dict(request_item_locale, user_lang, request)

                # 9. return datalists
                # PR2020-05-23 debug: datalists = {} gives parse error.
                # elapsed_seconds to the rescue: now datalists will never be empty

# ----- get users
                if datalist_request.get('user_rows'):
                    datalists['user_rows'] = acc_view.create_user_rowsNEW(sel_examyear, request)
                    datalists['permit_rows'] = acc_view.create_permit_list()

# ----- get correctors
                if datalist_request.get('corrector_rows'):
                    logger.debug('    datalist_request corrector_rows ')
                    datalists['corrector_rows'] = acc_corr.create_corrector_rows(
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_schoolbase,
                        sel_depbase=sel_depbase,
                        sel_lvlbase=sel_lvlbase,
                        request=request)

# ----- get UserCompensation
                if datalist_request.get('usercompensation_rows'):
                    acc_corr.update_usercompensation(sel_examyear, request)
                    datalists['usercompensation_rows'] = acc_corr.create_usercompensation_rows(sel_examyear, request)
                    datalists['usercomp_agg_rows'] = acc_corr.create_usercomp_agg_rows(sel_examyear, request)

# ----- examyears
                if datalist_request.get('examyear_rows'):
                    datalists['examyear_rows'] = school_dicts.create_examyear_rows(request.user, {})

# ----- schools
                datalist_request_school_rows = datalist_request.get('school_rows')
                if datalist_request_school_rows:
                    skip_allowed_filter = datalist_request_school_rows.get('skip_allowed_filter')
                    datalists['school_rows'] = school_dicts.create_school_rows(
                        request=request,
                        examyear=sel_examyear,
                        append_dict={},
                        skip_allowed_filter=skip_allowed_filter
                    )

# ----- departments
                if datalist_request.get('department_rows'):
                    skip_allowed_filter = af.get_dict_value(datalist_request, ('department_rows', 'skip_allowed_filter'), False)
                    datalists['department_rows'] = school_dicts.create_department_rows(
                        examyear=sel_examyear,
                        sel_schoolbase=sel_schoolbase,
                        sel_school=sel_school,
                        skip_allowed_filter=skip_allowed_filter,
                        request=request)

# ----- levels
                if datalist_request.get('level_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('level_rows', 'cur_dep_only'), False)
                    skip_allowed_filter = af.get_dict_value(datalist_request, ('level_rows', 'skip_allowed_filter'), False)
                    datalists['level_rows'] = school_dicts.create_level_rows(
                        request=request,
                        examyear=sel_examyear,
                        sel_schoolbase=sel_schoolbase,
                        sel_depbase=sel_depbase,
                        cur_dep_only=cur_dep_only,
                        skip_allowed_filter=skip_allowed_filter
                    )

# ----- sectors
                if datalist_request.get('sector_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('sector_rows', 'cur_dep_only'), False)
                    datalists['sector_rows'] = school_dicts.create_sector_rows(sel_examyear, sel_depbase, cur_dep_only)
# ----- subjecttypes
                if datalist_request.get('subjecttype_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('subjecttype_rows', 'cur_dep_only'), False)
                    datalists['subjecttype_rows'] = sj_vw.create_subjecttype_rows(
                        examyear=sel_examyear,
                        append_dict={},
                        depbase=sel_depbase,
                        cur_dep_only=cur_dep_only)
                    datalists['subjecttypebase_rows'] = sj_vw.create_subjecttypebase_rows()
# ----- subjects
                if datalist_request.get('subject_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('subject_rows', 'cur_dep_only'), False)
                    skip_allowedsubjbase_filter = af.get_dict_value(datalist_request, ('subject_rows', 'skip_allowed_filter'), False)

                    # PR2022-08-21 notatdayschool added: show this subject only when school is evening school or lex school
                    # attention: day/evening school shows notatdayschool subjects. Must be filtered out when adding subjects to day student
                    # also don't filter on notatdayschool when user is admin
                    skip_notatdayschool = sch_fnc.get_skip_notatdayschool(sel_school, request)

                    datalists['subject_rows'] = sj_vw.create_subject_rows(
                        request=request,
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_schoolbase,
                        sel_depbase=sel_depbase,
                        sel_lvlbase=sel_lvlbase,
                        skip_allowedsubjbase_filter=skip_allowedsubjbase_filter,
                        skip_notatdayschool=skip_notatdayschool,
                        cur_dep_only=cur_dep_only)

# ----- duo_subjects -- shows subjects + dep + level that may have duo exam, used in exam page link DUO exams
                if datalist_request.get('duo_subject_rows'):
                    datalists['duo_subject_rows'] = sj_vw.create_duo_subject_rows(
                        sel_examyear=sel_examyear,
                        sel_depbase=sel_depbase,
                        sel_lvlbase=sel_lvlbase,
                        append_dict={}
                    )
# ----- subjects for page subjectscheme
                if datalist_request.get('subject_rows_page_subjects'):
                    datalists['subject_rows'] = sj_vw.create_subjectrows_for_page_subjects(
                        sel_examyear=sel_examyear,
                        append_dict={}
                    )

# ----- subjects for page users, tab corrector permits
                if datalist_request.get('subject_rows_page_users'):
                    datalists['subject_rows_page_users'] = sj_vw.create_subjectrows_for_page_users(
                        sel_examyear=sel_examyear
                    )
# ----- clusters
                if datalist_request.get('cluster_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('cluster_rows', 'cur_dep_only'), False)
                    allowed_only = af.get_dict_value(datalist_request, ('cluster_rows', 'allowed_only'), False)
                    datalists['cluster_rows'] = sj_vw.create_cluster_rows(
                        request=request,
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_schoolbase,
                        sel_depbase=sel_depbase,
                        cur_dep_only=cur_dep_only,
                        allowed_only=allowed_only)
# ----- schemes
                if datalist_request.get('scheme_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('scheme_rows', 'cur_dep_only'), False)
                    datalists['scheme_rows'] = sj_vw.create_scheme_rows(
                        examyear=sel_examyear,
                        depbase=sel_depbase,
                        cur_dep_only=cur_dep_only)
# ----- schemeitems
                if datalist_request.get('schemeitem_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('schemeitem_rows', 'cur_dep_only'), False)

                    # PR2022-08-21 notatdayschool added: show this subject only when school is evening school or lex school
                    # attention: day/evening school shows notatdayschool subjects. Must be filtered out when adding subjects to day student
                    # also don't filter on notatdayschool when user is admin
                    skip_notatdayschool = sch_fnc.get_skip_notatdayschool(sel_school, request)

                    datalists['schemeitem_rows'] = sj_vw.create_schemeitem_rows(
                        sel_examyear=sel_examyear,
                        append_dict={},
                        cur_dep_only=cur_dep_only,
                        skip_notatdayschool=skip_notatdayschool,
                        depbase=sel_depbase
                    )
# ----- ete_exams
                if datalist_request.get('ete_exam_rows'):
                    # in page orderlist: show ete_exams of all deps
                    show_all = af.get_dict_value(datalist_request, ('ete_exam_rows', 'show_all'), False)
                    datalists['ete_exam_rows'] = sj_vw.create_ete_exam_rows(
                        req_usr=request.user,
                        sel_examyear=sel_examyear,
                        sel_depbase=sel_depbase,
                        append_dict={},
                        setting_dict=new_setting_dict,
                        show_all=show_all,
                        exam_pk_list=None
                    )
# ----- duo exams
                if datalist_request.get('duo_exam_rows'):
                    datalists['duo_exam_rows'] = sj_vw.create_duo_exam_rows(
                        req_usr=request.user,
                        sel_examyear=sel_examyear,
                        sel_depbase=sel_depbase,
                        sel_lvlbase=sel_lvlbase,
                        sel_examperiod=sel_examperiod,
                        append_dict={}
                        )
# ----- all exams
                if datalist_request.get('all_exam_rows'):
                    datalists['all_exam_rows'] = sj_vw.create_all_exam_rows(
                        req_usr=request.user,
                        sel_examyear=sel_examyear,
                        sel_depbase=sel_depbase,
                        sel_examperiod=sel_examperiod,
                        append_dict={},
                        setting_dict=new_setting_dict,
                        exam_pk_list=None
                        )
# ----- ntermentable
                if datalist_request.get('ntermentable_rows'):
                    datalists['ntermentable_rows'] = sj_vw.create_ntermentable_rows(
                        sel_examyear=sel_examyear,
                        sel_depbase=sel_depbase,
                        setting_dict=new_setting_dict
                    )
# ----- students
                if datalist_request.get('student_rows'):
                    # in page students: show deleted students when SBR 'Show all' is clicked
                    show_deleted = af.get_dict_value(datalist_request, ('student_rows', 'show_deleted'), False)
                    datalists['student_rows'], error_dict = stud_view.create_student_rows(
                        request=request,
                        sel_examyear= sel_examyear,
                        sel_schoolbase=sel_schoolbase,
                        sel_depbase=sel_depbase,
                        append_dict={},
                        show_deleted=show_deleted
                    )
                    if error_dict:
                        message_list.append(error_dict)
                        if logging_on:
                            logger.debug('    error_dict: ' + str(error_dict))
# ----- check birthcountry
                if datalist_request.get('check_birthcountry_rows'):
                    datalists['check_birthcountry_rows'], msg_html = stud_view.create_check_birthcountry_rows(
                        sel_examyear= sel_examyear,
                        sel_schoolbase=sel_schoolbase,
                        sel_depbase=sel_depbase)
                    if msg_html:
                        datalists['check_birthcountry_msg_html'] = msg_html
# ----- studentsubjects
                if datalist_request.get('studentsubject_rows'):
                    datalists['studentsubject_rows'] = stud_view.create_studentsubject_rows(
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_schoolbase,
                        sel_depbase=sel_depbase,
                        sel_lvlbase=sel_lvlbase,
                        requsr_same_school=requsr_same_school,
                        append_dict={},
                        request=request
                    )
# ----- studentsubjectnote
                #request_item = datalist_request.get('studentsubjectnote_rows')
                #if request_item:
                #    datalists['studentsubjectnote_rows'] = stud_view.create_studentsubjectnote_rows(request_item, request)

# ----- grade_exam_rows
                if datalist_request.get('grade_exam_rows'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['grade_exam_rows'] = gr_vw.create_grade_with_ete_exam_rows(
                            sel_examyear=sel_examyear,
                            sel_schoolbase=sel_schoolbase,
                            sel_depbase=sel_depbase,
                            sel_lvlbase=sel_lvlbase,
                            sel_examperiod=sel_examperiod,
                            setting_dict=new_setting_dict,
                            request=request
                        )
# ----- grade_exam_result_rows
                if datalist_request.get('grade_exam_result_rows'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['grade_exam_result_rows'] = gr_vw.create_grade_exam_result_rows(
                            sel_examyear=sel_examyear,
                            sel_schoolbase_pk=sel_schoolbase.pk if sel_schoolbase else None,
                            sel_depbase=sel_depbase,
                            sel_examperiod=sel_examperiod,
                            setting_dict=new_setting_dict,
                            request=request
                        )
# ----- grades
                if datalist_request.get('grade_rows'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['grade_rows'] = gr_vw.create_grade_rows(
                            sel_examyear_pk=sel_examyear.pk if sel_examyear else None,
                            sel_schoolbase_pk=sel_schoolbase.pk if sel_schoolbase else None,
                            sel_depbase_pk=sel_depbase.pk if sel_depbase else None,
                            sel_lvlbase_pk=sel_lvlbase.pk if sel_lvlbase else None,
                            sel_examperiod=sel_examperiod,
                            request=request
                        )

                        # PR2022-05-11 just added to answer question of Nancy Josefina
                        #datalists['grade_rows_with_modby'] = gr_vw.create_grade_rows_with_modbyTEMP(
                        #    sel_examyear_pk=sel_examyear.pk,
                        #    sel_schoolbase_pk=sel_schoolbase.pk,
                        #    sel_depbase_pk=sel_depbase.pk,
                        #    sel_examperiod=sel_examperiod,
                        #    request=request
                        #)
# ----- grade_note_icons
                if datalist_request.get('grade_note_icons'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['grade_note_icons'] = gr_vw.create_grade_note_icon_rows(
                            sel_examyear_pk=sel_examyear.pk,
                            sel_schoolbase_pk=sel_schoolbase.pk,
                            sel_depbase_pk=sel_depbase.pk,
                            sel_examperiod=sel_examperiod,
                            studsubj_pk=None,
                            request=request
                        )
# ----- results_per_school_rows
                if datalist_request.get('results_per_school_rows'):
                    datalists['results_per_school_rows'], error_dict = stud_view.create_results_per_school_rows(
                        request=request,
                        sel_examyear= sel_examyear,
                        sel_schoolbase=sel_schoolbase
                    )
                    if error_dict:
                        message_list.append(error_dict)

                        if logging_on:
                            logger.debug('    error_dict: ' + str(error_dict))
# ----- published
                if datalist_request.get('published_rows'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['published_rows'] = gr_vw.create_published_rows(
                            request=request,
                            sel_examyear_pk=sel_examyear.pk,
                            sel_schoolbase_pk=sel_schoolbase.pk,
                            sel_depbase_pk=sel_depbase.pk
                        )
# ----- mailbox
                if datalist_request.get('mailmessage_rows'):
                    datalists['mailmessage_received_rows'] = school_dicts.create_mailmessage_received_rows(
                        examyear=sel_examyear,
                        request=request
                    )
                    datalists['mailmessage_sent_rows'] = school_dicts.create_mailmessage_draft_or_sent_rows(
                        is_sent=True,
                        examyear=sel_examyear,
                        append_dict={},
                        request=request
                    )
                    datalists['mailmessage_draft_rows'] = school_dicts.create_mailmessage_draft_or_sent_rows(
                        is_sent=False,
                        examyear=sel_examyear,
                        append_dict={},
                        request=request
                    )
                    datalists['mailinglist_rows'] = school_dicts.create_mailinglist_rows(
                        request=request
                    )
                    datalists['mailattachment_rows'] = school_dicts.create_mailattachment_rows(
                        examyear=sel_examyear,
                        request=request
                    )
                    datalists['mailbox_user_rows'] = school_dicts.create_mailbox_user_rows(
                        examyear=sel_examyear,
                        request=request
                    )
                    datalists['mailbox_school_rows'] = school_dicts.create_mailbox_school_rows(
                        examyear=sel_examyear,
                        request=request
                    )
                    datalists['mailbox_usergroup_rows'] = school_dicts.create_mailbox_usergroup_rows()

# ----- orderlist_rows
                if datalist_request.get('orderlist_rows'):
                    datalists['orderlist_rows'] = sj_ol.create_orderlist_rows(
                        request=request,
                        sel_examyear=sel_examyear
                    )

# ----- envelopsubject_rows
                if datalist_request.get('envelopsubject_rows'):
                    sj_ol.check_envelopsubject_rows(
                        sel_examyear=sel_examyear,
                        request=request
                    )
                    datalists['envelopsubject_rows'] = sj_ol.get_envelopsubject_rows(
                        sel_examyear=sel_examyear,
                        append_dict={},
                        practex_only=None,  # values are None (all), True (only), False (excluded)
                        errata_only=False,
                        secret_only=None  # values are None (all), True (only), False (excluded)
                    )

# ----- envelopbundle_rows
                if datalist_request.get('envelopbundle_rows'):
                    datalists['envelopbundle_rows'] = sj_ol.create_envelopbundle_rows(
                        sel_examyear=sel_examyear,
                        append_dict={}
                    )

# ----- enveloplabel_rows
                if datalist_request.get('enveloplabel_rows'):
                    datalists['enveloplabel_rows'] = sj_ol.create_enveloplabel_rows(
                        sel_examyear=sel_examyear,
                        append_dict={}
                    )
# ----- envelopitem_rows
                if datalist_request.get('envelopitem_rows'):
                    datalists['envelopitem_rows'] = sj_ol.create_envelopitem_rows(
                        sel_examyear=sel_examyear,
                        append_dict={}
                    )
# ----- envelopbundlelabel_rows
                if datalist_request.get('envelopbundlelabel_rows'):
                    datalists['envelopbundlelabel_rows'] = sj_ol.create_envelopbundlelabel_rows(
                        sel_examyear=sel_examyear
                    )
# ----- enveloplabelitem_rows
                if datalist_request.get('enveloplabelitem_rows'):
                    datalists['enveloplabelitem_rows'] = sj_ol.create_enveloplabelitem_rows(
                        sel_examyear=sel_examyear
                    )

# ----- enveloporderlist_rows
                if datalist_request.get('enveloporderlist_rows'):
                    datalists['enveloporderlist_rows'] = sj_ol.create_enveloporderlist_rows(
                        sel_examyear=sel_examyear
                    )

        if message_list:
            datalists['messages'] = message_list

        if logging_on:
            logger.debug('    message_list: ' + str(message_list))

        elapsed_seconds = int(1000 * (timer() - starttime)) / 1000
        datalists['elapsed_seconds'] = elapsed_seconds
        if logging_on:
            logger.debug('datalists elapsed_seconds: ' + str(datalists['elapsed_seconds']))

        datalists_json = json.dumps(datalists, cls=af.LazyEncoder)

        return HttpResponse(datalists_json)
# - end of DatalistDownloadView

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def download_setting(request_item_setting, user_lang, request):
    # PR2020-07-01 PR2020-1-14 PR2021-08-12 PR2021-12-03 PR2022-12-10

    if request_item_setting is None:
        request_item_setting = {}

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('  ')
        logger.debug(' ----------------- download_setting ---------------------- ')
        logger.debug('    request_item_setting: ' + str(request_item_setting))

    # this function get settingss from request_item_setting.
    # if not in request_item_setting, it takes the saved settings.

    # datalist_request_item 'setting' can have several key/dict values that will be saved in usersettings:
    #   - key 'sel_page', required, stores selected page: sel_page = {page: "page_grade"}
    #   - key 'page_<pagename>'
    #       ' page dict may contain the following keys:
    #           - key 'sel_btn': saves the selected button {'sel_btn' = 'btn_ep_01}
    #       - key 'cols_hidden' saves hidden columns of page {"cols_hidden": ["examnumber", "lvl_abbrev", "sct_abbrev", "subj_name"]}

    #   - key 'selected_pk' saves selected values that are used in different pages (like examyear, depbase)
    #       ' selected_pk dict may contain the following keys:
    #       - key 'sel_depbase_pk' saves selected depbase_pk {'sel_depbase_pk' = 1} et cetera
    #       - key 'sel_examperiod' saves selected examperiod  {'sel_examperiod' = 1}
    #   - key 'ex3'
    #   - key 'verificationcode'
    #   - key 'open_args' stores if opening message must be shown after login {"show_msg": true}

    """
    # examples :
    # PR2021-12-03 grades.js: on opening page: 
        datalist_request: {'setting': {'page': 'page_grade'}
    on changing sel_btn:
        datalist_request: {'setting': {'page': 'page_grade', 'sel_btn': 'btn_exem', 'sel_examperiod': 4}} 
        request_item_setting: {'page': 'page_grade', 'sel_btn': 'btn_reex', 'sel_examperiod': 2, 'sel_examtype': 'ce'}
    page_studsubj, on changing SBR level:
        datalist_request: {'setting': {'page': 'page_studsubj', 'sel_lvlbase_pk': 14}}
    page orderlist, select all depbases:
      request_item_setting: {'page': 'page_orderlist', 'sel_depbase_pk': None}
  
    """
    msg_list = []

# ----- get page name from request_item_setting
    # - page is saved in Usersetting in function: get_headerbar_param

    # request_item_setting: {'page': 'page_grade', 'sel_examperiod': 4}
    page = request_item_setting.get('page')
    if logging_on:
        logger.debug('    page: ' + str(page) )

# - create setting_dict
    # setting_dict contains all info to be sent to client, permit_dict contains permit related info
    setting_dict = {'user_lang': user_lang, 'sel_page': page}

# - create permit_dict
    permit_dict = create_permit_dict(request)

    sel_examyear_instance = acc_prm.get_sel_examyear_from_user_instance(request.user)
    requsr_userallowed_instance = acc_prm.get_userallowed_instance(request.user, sel_examyear_instance)
    requsr_usergroup_list = acc_prm.get_usergroup_list(requsr_userallowed_instance)
    permit_dict['usergroup_list'] = requsr_usergroup_list

    requsr_allowed_sections_dict = acc_prm.get_userallowed_sections_dict(requsr_userallowed_instance)
    if requsr_allowed_sections_dict:
        permit_dict['allowed_sections'] = requsr_allowed_sections_dict

    requsr_allowed_cluster_list = acc_prm.get_userallowed_cluster_pk_list(requsr_userallowed_instance)
    if requsr_allowed_cluster_list:
        permit_dict['allowed_clusters'] = requsr_allowed_cluster_list

    permit_list, requsr_usergroups_arrXX, requsr_allowed_sections_dictXX, requsr_allowed_clusters_arrXX = acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, page)

    if permit_list:
        for prm in permit_list:
            if prm:
                permit_dict[prm] = True

# - selected_pk_dict contains saved selected_pk's from Usersetting, key: selected_pk
    # changes are stored in this dict, saved at the end when
    selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
    selected_pk_dict_has_changed = False
    if logging_on:
        logger.debug('    selected_pk_dict: ' + str(selected_pk_dict))

# ==== MESSAGES ========================
# - add message when logged in to testsite
    message = val.message_testsite()  # PR2022-01-12
    if message:
        msg_list.append(message)

# ----- display opening message ------ PR2022-05-28
    usersetting_dict = acc_prm.get_usersetting_dict(c.KEY_OPENARGS, request)
    # skip displaying opening message when user has ticked off 'Dont show message again'
    # set 'show_msg' = False to prevent showing this messages when changing page.
    # 'show_msg' will be set to False after first display, to prevent showing multiple times in one session
    hide_msg = usersetting_dict.get('hide_msg')
    if not hide_msg:
        if usersetting_dict.get('show_msg'):
            message = val.message_openargs()
            if message:
                msg_list.append(message)
            acc_view.set_usersetting_dict(c.KEY_OPENARGS, {'show_msg': False}, request)

# ===== PAGE =======================
    acc_view.get_settings_page(request, request_item_setting, page, setting_dict)

# ==== COUNTRY ========================
    acc_view.get_settings_country(request, permit_dict)

# ===== EXAMYEAR =======================
    # every user can change examyear, within examyears of  userallowed records PR2023-01-08
    # may_select_examyear is False when there is only 1 allowed examyear PR2023-01-08
    sel_examyear_instance, sel_examyear_tobesaved, reset_examperiod = \
        acc_view.get_settings_examyear(
            request=request,
            request_item_setting=request_item_setting,
            page=page,
            permit_dict=permit_dict,
            setting_dict=setting_dict,
            selected_pk_dict=selected_pk_dict,
            msg_list=msg_list
        )
    if sel_examyear_tobesaved:
        selected_pk_dict_has_changed = True

# ===== SCHOOLBASE ======================= PR2020-12-18 PR2022-12-04
    sel_schoolbase_instance, sel_schoolbase_tobesaved, sel_school_instance = \
        acc_view.get_settings_schoolbase(
            request=request,
            request_item_setting=request_item_setting,
            sel_examyear_instance=sel_examyear_instance,
            allowed_sections_dict=requsr_allowed_sections_dict,
            page=page,
            permit_dict=permit_dict,
            setting_dict=setting_dict,
            selected_pk_dict=selected_pk_dict,
            msg_list=msg_list
        )
    if sel_schoolbase_tobesaved:
        selected_pk_dict_has_changed = True
    if logging_on:
        logger.debug('    sel_schoolbase_instance: ' + str(sel_schoolbase_instance))
        logger.debug('    sel_school_instance: ' + str(sel_school_instance))

# ===== DEPARTMENTBASE =======================
    allowed_schoolbase_dict, allowed_depbases_pk_arr = \
        acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(
            userallowed_sections_dict=requsr_allowed_sections_dict,
            sel_schoolbase_pk=sel_schoolbase_instance.pk if sel_schoolbase_instance else None
        )

    if logging_on:
        logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))
        logger.debug('    allowed_depbases_pk_arr: ' + str(allowed_depbases_pk_arr))

    # PR2023-03-04 debug: when sel_schoolbase_pk is a vsbo school, the selected dep will go to vsbo
    # solved by resetting sel_schoolbase_pk to null in page orderlist,
    sel_depbase_instance, sel_depbase_tobesaved, sel_department_instance = \
        acc_view.get_settings_departmentbase(
            request=request,
            request_item_setting=request_item_setting,
            sel_examyear_instance=sel_examyear_instance,
            sel_schoolbase_instance=sel_schoolbase_instance,
            sel_school_instance=sel_school_instance,
            allowed_schoolbase_dict=allowed_schoolbase_dict,
            page=page,
            permit_dict=permit_dict,
            setting_dict=setting_dict,
            selected_pk_dict=selected_pk_dict,
            msg_list=msg_list
        )
    if sel_depbase_tobesaved:
        selected_pk_dict_has_changed = True
    if logging_on:
        logger.debug('    sel_depbase_instance: ' + str(sel_depbase_instance))
        logger.debug('    sel_department_instance: ' + str(sel_department_instance))

# ===== LEVELBASE =======================
    allowed_depbase_dict, allowed_lvlbases_pk_arr = acc_prm.get_userallowed_depbase_dict_lvlbases_pk_arr(
        allowed_schoolbase_dict=allowed_schoolbase_dict,
        sel_depbase_pk=sel_depbase_instance.pk if sel_depbase_instance else None
    )

    sel_lvlbase_instance, sel_lvlbase_tobesaved, sel_level_instance = \
        acc_view.get_settings_levelbase(
            request=request,
            request_item_setting=request_item_setting,
            sel_examyear_instance=sel_examyear_instance,
            sel_department_instance=sel_department_instance,
            allowed_depbase_dict=allowed_depbase_dict,
            page=page,
            permit_dict=permit_dict,
            setting_dict=setting_dict,
            selected_pk_dict=selected_pk_dict
        )
    if sel_lvlbase_tobesaved:
        selected_pk_dict_has_changed = True

# ===== SUBJECTBASE =======================
    sel_lvlbase_instance_pk = sel_lvlbase_instance.pk if sel_lvlbase_instance else -9
    allowed_subjbases_arr = acc_prm.get_userallowed_subjbase_arr(allowed_depbase_dict, sel_lvlbase_instance_pk)

    acc_view.get_settings_subjectbase(allowed_subjbases_arr, permit_dict)

# ===== EXAM PERIOD =======================
    sel_examperiod, sel_examperiod_tobesaved = acc_view.get_settings_examperiod(
        request=request,
        request_item_setting=request_item_setting,
        setting_dict=setting_dict,
        selected_pk_dict=selected_pk_dict,
        reset_examperiod=reset_examperiod
    )
    if sel_examperiod_tobesaved:
        selected_pk_dict_has_changed = True

# ===== EXAM TYPE =======================
    sel_examtype, sel_examptype_tobesaved = acc_view.get_settings_examtype(
        request_item_setting=request_item_setting,
        setting_dict=setting_dict,
        selected_pk_dict=selected_pk_dict,
        sel_examperiod=sel_examperiod
    )
    if sel_examptype_tobesaved:
        selected_pk_dict_has_changed = True


# ===== AUTH INDEX =======================
    sel_authindex_tobesaved = acc_view.get_settings_auth_index(
        usergroups_arr=requsr_usergroup_list,
        request_item_setting=request_item_setting,
        setting_dict=setting_dict,
        selected_pk_dict=selected_pk_dict,
        sel_examperiod=sel_examperiod
    )
    if sel_authindex_tobesaved:
        selected_pk_dict_has_changed = True


# ===== SECTORBASE, SCHEME, SUBJECT, STUDENT, =======================
    # PR2021-01-23 PR2021-03-14 PR2021-08-13 PR2022-03-06

    if logging_on:
        logger.debug('++++++++++++  SECTORBASE, SCHEME, SUBJECT, STUDENT, CLUSTER ++++++++++++++++++++++++')
        logger.debug('selected_pk_dict: ' + str(selected_pk_dict))
    # PR2022-05-29 dont save sel_student_pk, but only filter locally. Was: , c.KEY_SEL_STUDENT_PK):
    for key_str in (c.KEY_SEL_SCTBASE_PK, c.KEY_SEL_SCHEME_PK,
                    c.KEY_SEL_STUDENT_PK, c.KEY_SEL_CLUSTER_PK, c.KEY_SEL_SUBJECT_PK):

        if logging_on:
            logger.debug('........... key_str: ' + str(key_str))

# - get saved_pk_str
        saved_pk_int = None
        saved_pk_str = selected_pk_dict.get(key_str)
        if saved_pk_str:
            saved_pk_int = int(saved_pk_str)
        if logging_on:
            logger.debug('     saved_pk_int: ' + str(saved_pk_int) + ' ' + str(type(saved_pk_int)))
            logger.debug('     request_item_setting: ' + str(request_item_setting) + ' ' + str(type(request_item_setting)))

# - if key_str exists in request_item_setting: get new request_item_pk_int from request_item_setting
        if key_str in request_item_setting:
            request_item_pk_int = request_item_setting.get(key_str)
            if logging_on:
                logger.debug('     request_item_pk_int: ' + str(request_item_pk_int) + ' ' + str(type(request_item_pk_int)))

# - use request_pk_str when it has value and is different from the saved one
            # also use request_item_pk_int when its value is None, to reset filter
            if request_item_pk_int != saved_pk_int:
                selected_pk_dict_has_changed = True
                saved_pk_int = request_item_pk_int
                if logging_on:
                    logger.debug('>>>>> new_saved_pk_int: ' + str(saved_pk_int) + ' ' + str(type(saved_pk_int)))

# --- update selected_pk_dict, will be saved at end of def
                if saved_pk_int:
                    selected_pk_dict[key_str] = saved_pk_int
                elif key_str in selected_pk_dict:
                    selected_pk_dict.pop(key_str)

# --- add info to setting_dict, will be sent back to client
        if saved_pk_int:
            setting_dict[key_str] = saved_pk_int
            if key_str == c.KEY_SEL_SUBJECT_PK:
                subject = subj_mod.Subject.objects.get_or_none(
                    pk=saved_pk_int
                )
                if subject:
                    setting_dict['sel_subject_code'] = subject.base.code
                    setting_dict['sel_subject_name'] = subject.name_nl

            # use studentbase_pk instead of student_pk PR2022-02-07
            # on second thought: don't, student might be in multiple schools in the same examyear PR2022-12-07

            elif key_str == c.KEY_SEL_STUDENT_PK:
                student = stud_mod.Student.objects.get_or_none(
                    pk=saved_pk_int
                )
                if student:
                    setting_dict['sel_student_name'] = stud_fnc.get_full_name(student.lastname, student.firstname, student.prefix)
                    setting_dict['sel_student_name_init'] = stud_fnc.get_lastname_firstname_initials(student.lastname, student.firstname, student.prefix)

            elif key_str == c.KEY_SEL_SCTBASE_PK:
                sector = subj_mod.Sector.objects.get_or_none(
                    examyear=sel_examyear_instance,
                    base_id=saved_pk_int)
                if sector:
                    setting_dict['sel_sctbase_code'] = sector.base.code if sector.base else '-'
                    setting_dict['sel_sector_name'] = sector.name

            elif key_str == c.KEY_SEL_CLUSTER_PK:
                cluster = subj_mod.Cluster.objects.get_or_none(
                    id=saved_pk_int)
                if cluster:
                    setting_dict['sel_cluster_name'] = cluster.name

            elif key_str == c.KEY_SEL_SCHEME_PK:
                scheme = subj_mod.Scheme.objects.get_or_none(pk=saved_pk_int)
                if scheme:
                    setting_dict['sel_scheme_name'] = scheme.name

    if logging_on:
        logger.debug('..... selected_pk_dict: ' + str(selected_pk_dict) + ' ' + str(type(selected_pk_dict)))
        logger.debug('..... setting_dict: ' + str(setting_dict) + ' ' + str(type(setting_dict)))

    # - save settings when they have changed
    if selected_pk_dict_has_changed:
        acc_view.set_usersetting_dict(c.KEY_SELECTED_PK, selected_pk_dict, request)

        if logging_on:
            logger.debug('..... saved selected_pk_dict: ' + str(selected_pk_dict))
            logger.debug('......................... ')
    if logging_on:
        logger.debug('..... setting_dict: ' + str(setting_dict))
        logger.debug('......................... ')

    return setting_dict, permit_dict, sel_examyear_instance, sel_schoolbase_instance, \
           sel_school_instance, sel_depbase_instance, sel_lvlbase_instance, \
            sel_examperiod, sel_examtype, msg_list
# - end of download_setting


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


def create_permit_dict(request):
# - get role from req_usr, put them in setting_dict PR2020-12-14  PR2021-01-26 PR2021-04-22 PR2022-12-09
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- create_permit_dict -------')

    req_usr = request.user
    permit_dict = {'requsr_pk': req_usr.pk,
                    'requsr_name': req_usr.last_name,
                    'requsr_role': req_usr.role}

    if req_usr.is_authenticated and req_usr.role is not None:
        if req_usr.role == c.ROLE_008_SCHOOL:
            permit_dict['requsr_role_school'] = True
        elif req_usr.role == c.ROLE_016_CORR:
            permit_dict['requsr_role_corr'] = True
        elif req_usr.role == c.ROLE_032_INSP:
            permit_dict['requsr_role_insp'] = True
        elif req_usr.role == c.ROLE_064_ADMIN:
            permit_dict['requsr_role_admin'] = True
        elif req_usr.role == c.ROLE_128_SYSTEM:
            permit_dict['requsr_role_system'] = True

    return permit_dict
# - end of create_permit_dict

"""
def get_requsr_allowedNIU (request, permit_dict):
    # not in use, only called by GradeBlockView PR2022-12-11
    # PR2022-03-18
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_requsr_allowed -------')
    try:
        usergroups_arr, allowed_sections_dict, allowed_clusters_arr = acc_view.get_request_userallowed(request)
        if logging_on:
            logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict) + ' ' + str(type(allowed_sections_dict)))

        if allowed_sections_dict:
            sel_schoolbase_pk_str = str(sel_schoolbase_pk)
            allowed_schoolbase_dict = allowed_sections_dict.get(sel_schoolbase_pk_str)
            if logging_on:
                logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))

            if allowed_schoolbase_dict:
                sel_depbase_pk_str = str(sel_depbase_pk)
                allowed_depbase_dict = allowed_schoolbase_dict.get(sel_depbase_pk_str)
                if logging_on:
                    logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict))

                if allowed_depbase_dict:
                    sel_lvlbase_pk_str = str(sel_lvlbase_pk)
                    allowed_lvlbase_arr = allowed_depbase_dict.get(sel_lvlbase_pk_str)
                    if logging_on:
                        logger.debug('    allowed_lvlbase_arr: ' + str(allowed_lvlbase_arr) + ' ' + str(
                            type(allowed_lvlbase_arr)))

                    if allowed_lvlbase_arr:

                        for subjbase_pk_int in allowed_lvlbase_arr:
                            allowed_subjbase_pk_arr.append(subjbase_pk_int)

        if req_usr.allowed_depbases:
            # PR2021-05-04 warning. if depbases contains ';2;3;',
            # it will give error:  invalid literal for int() with base 10: ''
            allowed_depbases_arr = req_usr.allowed_depbases.split(';') if req_usr.allowed_depbases else []
            permit_dict['requsr_allowed_depbases'] = list(map(int, allowed_depbases_arr))
        if req_usr.allowed_levelbases:
            allowed_levelbases_arr = req_usr.allowed_levelbases.split(';') if req_usr.allowed_levelbases else []
            permit_dict['requsr_allowed_levelbases'] = list(map(int, allowed_levelbases_arr))
        #if req_usr.allowed_schoolbases:
           #allowed_schoolbases_arr = req_usr.allowed_schoolbases.split(';') if req_usr.allowed_schoolbases else []
            #permit_dict['requsr_allowed_schoolbases'] = list(map(int, allowed_schoolbases_arr))
        if req_usr.allowed_subjectbases:
            allowed_subjectbases_arr = req_usr.allowed_subjectbases.split(';') if req_usr.allowed_subjectbases else []
            permit_dict['requsr_allowed_subjectbases'] = list(map(int, allowed_subjectbases_arr))
        if req_usr.allowed_clusters:
            # note: allowed_clusters contains allowed_cluster_pk, cluster does not have base
            allowed_clusters_arr = req_usr.allowed_clusters.split(';') if req_usr.allowed_clusters else []
            permit_dict['requsr_allowed_clusters'] = list(map(int, allowed_clusters_arr))
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('    permit_dict: ' + str(permit_dict))
# end of get_requsr_allowed
"""