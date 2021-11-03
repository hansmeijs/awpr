# PR2020-09-17 PR2021-01-27
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import activate, ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.generic import View

from timeit import default_timer as timer

from accounts import views as acc_view

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
from students import models as stud_mod
from students import views as stud_view
from students import functions as stud_fnc
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
        messages = []
        if request.user and request.user.country and  request.user.schoolbase:
            if request.POST['download']:

# ----- get user_lang
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# ----- get datalist_request
                datalist_request = json.loads(request.POST['download'])
                if logging_on:
                    logger.debug('datalist_request: ' + str(datalist_request) + ' ' + str(type(datalist_request)))

# ----- get user permits and settings -- first get settings, these are used in other downloads
                # download_setting will update usersetting with items in request_item_setting, and retrieve saved settings
                request_item_setting = datalist_request.get('setting')
                if logging_on:
                    logger.debug('request_item_setting: ' + str(request_item_setting) + ' ' + str(type(request_item_setting)))
                new_setting_dict, permit_dict, sel_examyear, sel_schoolbase, sel_depbase, sel_examperiod, sel_examtype = \
                    download_setting(request_item_setting, messages, user_lang, request)

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
                    logger.debug('messages: ' + str(messages) + ' ' + str(type(messages)))

                if messages:
                    # messages" [{'msg_list':
                    # ['Waarschuwing: het geselecteerde examenjaar 2021 is niet gelijk aan het huidige examenjaar.'],
                    # 'class': 'border_bg_warning'}]
                    message_html = ''
                    for message in messages:
                        msg_list = message.get('msg_list')
                        class_str = message.get('class', '')
                        if msg_list:
                            msg_html = ' '.join(("<div class'm-2 p-2", class_str, "'>"))
                            for msg_txt in msg_list:
                                msg_html += ''.join(("<p>", msg_txt, "</p>"))
                            msg_html += "</div>"
                            message_html += msg_html
                    datalists['messages'] = messages

# ----- get school settings (includes import settings)
                request_item_schoolsetting = datalist_request.get('schoolsetting')
                if request_item_schoolsetting:
                    datalists['schoolsetting_dict'] = sch_fnc.get_schoolsetting(
                        request_item_schoolsetting, sel_examyear, sel_schoolbase, sel_depbase)
                if logging_on:
                    logger.debug('request_item_schoolsetting: ' + str(request_item_schoolsetting) + ' ' + str(type(request_item_schoolsetting)))

# ----- run system_updates if necessary
                af.system_updates(sel_examyear, request)

# ----- locale
                request_item_locale = datalist_request.get('locale')
                if request_item_locale:
                    datalists['locale_dict'] = loc.get_locale_dict(request_item_locale, user_lang, request)
                if logging_on:
                    logger.debug('request_item_locale: ' + str(request_item_locale) + ' ' + str(type(request_item_locale)))

                # 9. return datalists
                # PR2020-05-23 debug: datalists = {} gives parse error.
                # elapsed_seconds to the rescue: now datalists will never be empty

# ----- get users
                if datalist_request.get('user_rows'):
                    datalists['user_rows'] = acc_view.create_user_rows(request)
                    datalists['permit_rows'] = acc_view.create_permit_list()
# ----- examyears
                if datalist_request.get('examyear_rows'):
                    cur_ey_only = af.get_dict_value(datalist_request, ('examyear_rows', 'cur_ey_only'), False)
                    get_all_countries =  af.get_dict_value(datalist_request, ('examyear_rows', 'get_all_countries'), False)
                    sel_examyear_pk = None
                    if cur_ey_only and sel_examyear:
                        sel_examyear_pk = sel_examyear.pk
                    datalists['examyear_rows'] = school_dicts.create_examyear_rows(request.user, {}, sel_examyear_pk, get_all_countries)
# ----- schools
                if datalist_request.get('school_rows'):
                    datalists['school_rows'] = school_dicts.create_school_rows(sel_examyear, permit_dict)
# ----- departments
                if datalist_request.get('department_rows'):
                    datalists['department_rows'] = school_dicts.create_department_rows(sel_examyear)
# ----- levels
                if datalist_request.get('level_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('level_rows', 'cur_dep_only'), False)
                    datalists['level_rows'] = school_dicts.create_level_rows(sel_examyear, sel_depbase, cur_dep_only)
# ----- sectors
                if datalist_request.get('sector_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('sector_rows', 'cur_dep_only'), False)
                    datalists['sector_rows'] = school_dicts.create_sector_rows(sel_examyear, sel_depbase, cur_dep_only)
# ----- subjecttypes
                if datalist_request.get('subjecttype_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('subjecttype_rows', 'cur_dep_only'), False)
                    datalists['subjecttype_rows'] = sj_vw.create_subjecttype_rows(
                        examyear=sel_examyear,
                        depbase=sel_depbase,
                        cur_dep_only=cur_dep_only)
                    datalists['subjecttypebase_rows'] = sj_vw.create_subjecttypebase_rows()
# ----- subjects
                if datalist_request.get('subject_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('subject_rows', 'cur_dep_only'), False)
                    datalists['subject_rows'] = sj_vw.create_subject_rows(
                        setting_dict=new_setting_dict,
                        subject_pk=None,
                        cur_dep_only=cur_dep_only)
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
                    datalists['schemeitem_rows'] = sj_vw.create_schemeitem_rows(
                        examyear=sel_examyear,
                        cur_dep_only=cur_dep_only,
                        depbase=sel_depbase)
# ----- exams
                if datalist_request.get('exam_rows'):
                    cur_dep_only = af.get_dict_value(datalist_request, ('subject_rows', 'cur_dep_only'), False)
                    datalists['exam_rows'] = sj_vw.create_exam_rows(new_setting_dict, {}, cur_dep_only)
# ----- students
                if datalist_request.get('student_rows'):
                    datalists['student_rows'] = stud_view.create_student_rows(new_setting_dict, {}, None)
# ----- studentsubjects
                if datalist_request.get('studentsubject_rows'):
                    datalists['studentsubject_rows'] = stud_view.create_studentsubject_rows(
                        examyear=sel_examyear,
                        schoolbase=sel_schoolbase,
                        depbase=sel_depbase,
                        requsr_same_school=requsr_same_school,
                        setting_dict=new_setting_dict,
                        append_dict={}
                    )
# ----- studentsubjectnote
                #request_item = datalist_request.get('studentsubjectnote_rows')
                #if request_item:
                #    datalists['studentsubjectnote_rows'] = stud_view.create_studentsubjectnote_rows(request_item, request)
# ----- orderlists
                if datalist_request.get('orderlist_rows'):
                    datalists['orderlist_rows'] = stud_view.create_orderlist_rows(sel_examyear.code, request)
# ----- grade_with_exam_rows
                if datalist_request.get('grade_with_exam_rows'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['grade_with_exam_rows'] = gr_vw.create_grade_with_exam_rows(
                            sel_examyear_pk=sel_examyear.pk,
                            sel_schoolbase_pk=sel_schoolbase.pk,
                            sel_depbase_pk=sel_depbase.pk,
                            sel_examperiod=sel_examperiod,
                            request=request
                        )
# ----- grades
                if datalist_request.get('grade_rows'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['grade_rows'] = gr_vw.create_grade_rows(
                            sel_examyear_pk=sel_examyear.pk,
                            sel_schoolbase_pk=sel_schoolbase.pk,
                            sel_depbase_pk=sel_depbase.pk,
                            sel_examperiod=sel_examperiod,
                            request=request
                        )
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
# ----- published
                if datalist_request.get('published_rows'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['published_rows'] = gr_vw.create_published_rows(
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
                        request=request
                    )
                    datalists['mailmessage_draft_rows'] = school_dicts.create_mailmessage_draft_or_sent_rows(
                        is_sent=False,
                        examyear=sel_examyear,
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

        elapsed_seconds = int(1000 * (timer() - starttime)) / 1000
        datalists['elapsed_seconds'] = elapsed_seconds
        if logging_on:
            logger.debug('datalists elapsed_seconds: ' + str(datalists['elapsed_seconds']))

        datalists_json = json.dumps(datalists, cls=af.LazyEncoder)

        return HttpResponse(datalists_json)
# - end of DatalistDownloadView


def download_setting(request_item_setting, messages, user_lang, request):  # PR2020-07-01 PR2020-1-14 PR2021-08-12

    if request_item_setting is None:
        request_item_setting = {}

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----------------- download_setting ---------------------- ')
        logger.debug('request_item_setting: ' + str(request_item_setting) )
    # this function get settingss from request_item_setting.
    # if not in request_item_setting, it takes the saved settings.

    # datalist_request_item 'setting' can have the follwoing keys that will be saved in usersettings:
    #   - key 'page':       required, stored in usersetting sel_page: ( page: 'page_grade'}
    #   - key 'selected_pk': not required, contains all selected pk's: to be saved in usersetting key 'selected_pk' (used in different pages (like examyear, schoolbase, depbase)

    # datalist_request_item 'setting' can have two key/values that will be saved in usersettings:
    #   - key 'page', required, stored in usersetting sel_page: ( page: 'page_grade'}
    #   - key 'selected_pk' saves selected values that are used in different pages (like examyear, schoolbase, depbase)
    #       - selected_pk: {sel_examyear_pk: 1, sel_schoolbase_pk: 13 etc
    #   - usersetting key 'sel_page' saves current page (to be opened at next login)  and kery 'page_user' etc  with key 'sel_btn'  that is different for every page:
    #       - sel_page: ( page: 'page_grade', page_user: {sel_btn: 'btn_userpermit' }

    req_user = request.user

# ----- get page name from request_item_setting
    # request_item_setting: {'page': 'page_grade', 'sel_examperiod': 4}
    page = request_item_setting.get('page')

# - setting_dict contains all info to be sent to client, permit_dict contains permit related info
    setting_dict = {'user_lang': user_lang, 'sel_page': page}

# - get permit_list
    permit_dict = create_permit_dict(req_user)
    permit_list, usergroup_list = acc_view.get_userpermit_list(page, request.user)
    if permit_list:
        for prm in permit_list:
            if prm:
                permit_dict[prm] = True
    if usergroup_list:
        permit_dict['usergroup_list'] = usergroup_list

    if logging_on:
        logger.debug('permit_list: ' + str(permit_list) )
        logger.debug('usergroup_list: ' + str(usergroup_list) )
        logger.debug('permit_dict: ' + str(permit_dict) )

# - selected_pk_dict contains saved selected_pk's from Usersetting, key: selected_pk
    # changes are stored in this dict, saved at the end when
    selected_pk_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
    selected_pk_dict_has_changed = False

# ==== COUNTRY ========================
# - get country from req_user
    requsr_country = req_user.country
    permit_dict['requsr_country_pk'] = requsr_country.pk  if requsr_country else None
    permit_dict['requsr_country'] = requsr_country.name if requsr_country else None
    if requsr_country.locked:
        permit_dict['requsr_country_locked'] = True

# ===== SCHOOLBASE ======================= PR2020-12-18
# - get schoolbase from settings / request when role is insp, admin or system, from req_user otherwise
    # req_user.schoolbase cannot be changed
    # Selected schoolbase is stored in {selected_pk: {sel_schoolbase_pk: val}}

    requsr_schoolbase = req_user.schoolbase
    permit_dict['requsr_schoolbase_pk'] = requsr_schoolbase.pk if requsr_schoolbase else None
    permit_dict['requsr_schoolbase_code'] = requsr_schoolbase.code if requsr_schoolbase else None

    request_item_schoolbase_pk = request_item_setting.get(c.KEY_SEL_SCHOOLBASE_PK)
    sel_schoolbase_instance, sel_schoolbase_save = af.get_sel_schoolbase_instance(request, request_item_schoolbase_pk)
    #logger.debug('sel_schoolbase_instance: ' + str(sel_schoolbase_instance) + ' pk: ' + str(sel_schoolbase_instance.pk))
    if sel_schoolbase_save:
        # when sel_schoolbase_save=True, there is always a sel_schoolbase_instance
        selected_pk_dict[c.KEY_SEL_SCHOOLBASE_PK] = sel_schoolbase_instance.pk
        selected_pk_dict_has_changed = True
    if sel_schoolbase_instance:
        setting_dict[c.KEY_SEL_SCHOOLBASE_PK] = sel_schoolbase_instance.pk
        setting_dict['sel_schoolbase_code'] = sel_schoolbase_instance.code

    # requsr_same_school = True when selected school is same as requsr_school PR2021-04-27
    # used on entering grades. Users can only enter grades of their own school. Syst, Adm and Insp, Comm can not neter grades
    requsr_same_school = (req_user.role == c.ROLE_008_SCHOOL and
                          sel_schoolbase_instance and requsr_schoolbase.pk == sel_schoolbase_instance.pk)
    permit_dict['requsr_same_school'] = requsr_same_school
    # this one is used in create_studentsubject_rows and create_grade_rows, to block view of non-submitted subjects and grades
    setting_dict['requsr_same_school'] = requsr_same_school

# ===== EXAMYEAR =======================
    # every user can change examyear, may_select_examyear is False when there is only 1 examyear

# - get selected examyear from request_item_setting, Usersetting, this_examyear or latest
    request_item_examyear_pk = request_item_setting.get(c.KEY_SEL_EXAMYEAR_PK)
    sel_examyear_instance, sel_examyear_save, may_select_examyear = af.get_sel_examyear_instance(request, request_item_examyear_pk)

    permit_dict['may_select_examyear'] = may_select_examyear

    #logger.debug('sel_examyear_instance: ' + str(sel_examyear_instance) + ' pk: ' + str(sel_examyear_instance.pk))
# - update selected_pk_dict when selected_pk_dict_has_changed, will be saved at end of def
    if sel_examyear_save:
        # sel_examyear_instance has always value when selected_pk_dict_has_changed
        selected_pk_dict[c.KEY_SEL_EXAMYEAR_PK] = sel_examyear_instance.pk
        selected_pk_dict_has_changed = True

# - add info to setting_dict, will be sent back to client
    if sel_examyear_instance:
        setting_dict[c.KEY_SEL_EXAMYEAR_PK] = sel_examyear_instance.pk
        setting_dict['sel_examyear_code'] = sel_examyear_instance.code if sel_examyear_instance.code else None
        if sel_examyear_instance.published:
            setting_dict['sel_examyear_published'] = sel_examyear_instance.published
        if sel_examyear_instance.locked:
            setting_dict['sel_examyear_locked'] = sel_examyear_instance.locked

# - add message when examyear is different from this eaxamyear
    message = val.message_diff_exyr(sel_examyear_instance)  # PR2020-10-30
    if message:
        messages.append(message)

# ===== SCHOOL =======================
# - only roles insp, admin and system may select other schools
    may_select_school = (req_user.role > c.ROLE_008_SCHOOL)
    permit_dict['may_select_school'] = may_select_school
    display_school = True
    if page == 'page_examyear':
        display_school = (req_user.role <= c.ROLE_008_SCHOOL)
    permit_dict['display_school'] = display_school

# get school from sel_schoolbase and sel_examyear_instance
    sel_school = sch_mod.School.objects.get_or_none(
        base=sel_schoolbase_instance,
        examyear=sel_examyear_instance)
    #logger.debug('get_or_none sel_school: ' + str(sel_school) )

    if sel_school:
        setting_dict['sel_school_pk'] = sel_school.pk
        setting_dict['sel_school_name'] = sel_school.name
        setting_dict['sel_school_abbrev'] = sel_school.abbrev
        if sel_school.activated:
            setting_dict['sel_school_activated'] = sel_school.activated
        if sel_school.locked:
            setting_dict['sel_school_locked'] = sel_school.locked
        #logger.debug('sel_school.depbases: ' + str(sel_school.depbases) )

# ===== DEPBASE =======================
    # every user can change depbase, if in .sel_school_depbases and in user allowed_depbases

# - get sel_depbase_instance from saved_setting or request_item_setting or first allowed, check if allowed
    request_item_depbase_pk = request_item_setting.get(c.KEY_SEL_DEPBASE_PK)
    sel_depbase_instance, sel_depbase_save, allowed_depbases = \
        af.get_sel_depbase_instance(sel_school, request, request_item_depbase_pk)

    if logging_on:
        logger.debug('sel_depbase_instance: ' + str(sel_depbase_instance))

    permit_dict['allowed_depbases'] = allowed_depbases
    allowed_depbases_len = len(allowed_depbases)
    # Note: set may_select_department also in ExamyearListView
    may_select_department = (page not in ('page_examyear',) and allowed_depbases_len > 1)
    permit_dict['may_select_department'] = may_select_department
    permit_dict['display_department'] = (page not in ('page_examyear',))

    if logging_on:
        logger.debug('allowed_depbases: ' + str(allowed_depbases) )
        logger.debug('may_select_department: ' + str(may_select_department) )
        logger.debug('permit_dict[display_department]: ' + str(permit_dict['display_department']) )

# - update selected_pk_dict when selected_pk_dict_has_changed, will be saved at end of def
    if sel_depbase_save:
        # sel_depbase_instance has always value when sel_depbase_save = True
        selected_pk_dict[c.KEY_SEL_DEPBASE_PK] = sel_depbase_instance.pk
        selected_pk_dict_has_changed = True

# - add info to setting_dict, will be sent back to client
    if sel_depbase_instance:
        setting_dict[c.KEY_SEL_DEPBASE_PK] = sel_depbase_instance.pk
        setting_dict['sel_depbase_code'] = sel_depbase_instance.code if sel_depbase_instance.code else None

        sel_department_instance = sch_mod.Department.objects.get_or_none(base=sel_depbase_instance, examyear=sel_examyear_instance)
        if sel_department_instance:
            setting_dict['sel_department_pk'] = sel_department_instance.pk
            # setting_dict['sel_department_abbrev'] = sel_department_instance.abbrev
            # setting_dict['sel_department_name'] = sel_department_instance.name
            setting_dict['sel_dep_level_req'] = sel_department_instance.level_req
            setting_dict['sel_dep_has_profiel'] = sel_department_instance.has_profiel
            # setting_dict['sel_dep_sector_req'] = sel_department_instance.sector_req

# ===== EXAM PERIOD =======================
# every user can change exam period

# - get selected examperiod from request_item_setting, from Usersetting if request_item is None
    request_item_examperiod = request_item_setting.get(c.KEY_SEL_EXAMPERIOD)
    sel_examperiod, sel_examperiod_save = af.get_sel_examperiod(selected_pk_dict, request_item_examperiod)

    if logging_on:
        logger.debug('..... EXAM PERIOD .....')
        logger.debug('request_item_examperiod: ' + str(request_item_examperiod) )
        logger.debug('sel_examperiod: ' + str(sel_examperiod) )
        logger.debug('sel_examperiod_save: ' + str(sel_examperiod_save) )

# - add info to setting_dict, will be sent back to client
    setting_dict[c.KEY_SEL_EXAMPERIOD] = sel_examperiod
    setting_dict['sel_examperiod_caption'] = c.get_examperiod_caption(sel_examperiod)

# - update selected_pk_dict when selected_pk_dict_has_changed, will be saved at end of def
    if sel_examperiod_save:
        # sel_depbase_instance has always value when sel_depbase_save = True
        selected_pk_dict[c.KEY_SEL_EXAMPERIOD] = sel_examperiod
        selected_pk_dict_has_changed = True

# ===== EXAM TYPE =======================
    # every user can change examtype

# - get selected examtype from request_item_setting, from Usersetting if request_item is None
    request_item_examtype = request_item_setting.get(c.KEY_SEL_EXAMTYPE)
    sel_examtype, sel_examtype_save = af.get_sel_examtype(selected_pk_dict, request_item_examtype, sel_examperiod)

# - add info to setting_dict, will be sent back to client
    setting_dict[c.KEY_SEL_EXAMTYPE] = sel_examtype
    setting_dict['sel_examtype_caption'] = c.get_examtype_caption(sel_examtype)

    if logging_on:
        logger.debug('..... EXAM TYPE .....')
        logger.debug('request_item_examtype: ' + str(request_item_examtype) )
        logger.debug('sel_examtype: ' + str(sel_examtype) )
        logger.debug('sel_examtype_save: ' + str(sel_examtype_save) )

    # - update selected_pk_dict when selected_pk_dict_has_changed, will be saved at end of def
    if sel_examtype_save:
        # sel_depbase_instance has always value when sel_depbase_save = True
        selected_pk_dict[c.KEY_SEL_EXAMTYPE] = sel_examtype
        selected_pk_dict_has_changed = True

# ===== DEPBASE, LEVELBASE, SECTORBASE, SCHEME, SUBJECT, STUDENT, ======================= PR2021-01-23 PR2021-03-14 PR2021-08-13

    if logging_on:
        logger.debug('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        logger.debug('selected_pk_dict: ' + str(selected_pk_dict))

    for key_str in (c.KEY_SEL_LVLBASE_PK, c.KEY_SEL_SCTBASE_PK, c.KEY_SEL_SCHEME_PK, c.KEY_SEL_SUBJECT_PK, c.KEY_SEL_STUDENT_PK):
        if logging_on:
            logger.debug('........... key_str: ' + str(key_str))

# - get saved_pk_str
        saved_pk_int = None
        saved_pk_str = selected_pk_dict.get(key_str)
        if saved_pk_str:
            saved_pk_int = int(saved_pk_str)
        if logging_on:
            logger.debug('saved_pk_int: ' + str(saved_pk_int) + ' ' + str(type(saved_pk_int)))

# - if key_str exists in request_item_setting: get new request_item_pk_int from request_item_setting
        if key_str in request_item_setting:
            request_item_pk_int = request_item_setting.get(key_str)
            if logging_on:
                logger.debug('request_item_pk_int: ' + str(request_item_pk_int) + ' ' + str(type(request_item_pk_int)))

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
                    setting_dict['sel_subject_name'] = subject.name

            elif key_str == c.KEY_SEL_STUDENT_PK:
                student = stud_mod.Student.objects.get_or_none(
                    pk=saved_pk_int
                )
                if student:
                    setting_dict['sel_student_name'] = stud_fnc.get_full_name(student.lastname, student.firstname, student.prefix)
                    setting_dict['sel_student_name_init'] = stud_fnc.get_lastname_firstname_initials(student.lastname, student.firstname, student.prefix)

            elif key_str == c.KEY_SEL_DEPBASE_PK:
                department = sch_mod.Department.objects.get_or_none(
                    examyear=sel_examyear_instance,
                    base_id=saved_pk_int)
                if department:
                    setting_dict['sel_depbase_code'] = department.base.code

            elif key_str == c.KEY_SEL_LVLBASE_PK:
                level = subj_mod.Level.objects.get_or_none(
                    examyear=sel_examyear_instance,
                    base_id=saved_pk_int)
                if level:
                    setting_dict['sel_level_abbrev'] = level.abbrev

            elif key_str == c.KEY_SEL_SCTBASE_PK:
                sector = subj_mod.Sector.objects.get_or_none(
                    examyear=sel_examyear_instance,
                    base_id=saved_pk_int)
                if sector:
                    setting_dict['sel_sector_abbrev'] = sector.abbrev

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

# ===== PAGE SETTINGS ======================= PR2021-06-22
# these settings can not be changed by calling download, are changes by b_UploadSettings
# value of key 'sel_page' is set and retrieved in get_headerbar_param

    if logging_on:
        logger.debug('...........page: ' + str(page))

    # request_item_setting: {'page': 'page_grade', 'sel_examperiod': 4}

    # get page settings from usersetting
    if page:
        page_dict = acc_view.get_usersetting_dict(page, request)
        # page_dict: {'sel_btn': 'btn_studsubj', 'cols_hidden': {'published': ['examperiod'], 'studsubj': ['examnumber']}}
        if logging_on:
            logger.debug('...........page_dict: ' + str(page_dict))
        if page_dict is None:
            page_dict = {}
    # - get sel_btn from  usersetting
        sel_btn = page_dict.get(c.KEY_SEL_BTN)

    # - replace by new_sel_btn, if any
        new_sel_btn = request_item_setting.get(c.KEY_SEL_BTN)
        if new_sel_btn and new_sel_btn != sel_btn:
            sel_btn = new_sel_btn
            page_dict[c.KEY_SEL_BTN] = new_sel_btn
    # - save new_sel_btn, if changed
            acc_view.set_usersetting_dict(page, page_dict, request)

        if logging_on:
            logger.debug('...........sel_btn: ' + str(sel_btn))

# - add info to setting_dict, will be sent back to client
        if sel_btn:
            setting_dict[c.KEY_SEL_BTN] = sel_btn
            if logging_on:
                logger.debug('...........setting_dict: ' + str(setting_dict))

# - add list of hidden columns PR2021-07-07 - cols_hidden cannot be changed by calling downloads function
        cols_hidden = page_dict.get(c.KEY_COLS_HIDDEN)
        if cols_hidden:
            setting_dict[c.KEY_COLS_HIDDEN] = cols_hidden

    if logging_on:
        logger.debug('setting_dict: ' + str(setting_dict))
        logger.debug('......................... ')

    return setting_dict, permit_dict, sel_examyear_instance, sel_schoolbase_instance, sel_depbase_instance, \
            sel_examperiod, sel_examtype
# - end of download_setting


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def get_selected_examyear_examperiod_from_usersetting(request):  # PR2021-07-08
    # - get selected examyear.code and examperiod from usersettings, only examyear from request.user.country
    # used in ExamyearUploadView, OrderlistDownloadView
    # note: examyear.code is integer '2021'
    sel_examyear, sel_examperiod = None, None
    req_user = request.user
    if req_user:
        selected_pk_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if selected_pk_dict:
            sel_examyear = sch_mod.Examyear.objects.get_or_none(
                pk=selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK),
                country=request.user.country
            )

        sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)

    return sel_examyear, sel_examperiod


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def get_selected_examyear_scheme_pk_from_usersetting(request):  # PR2021-07-13
    # - get selected examyear.code and scheme_p from usersettings
    # used in SchemeDownloadXlsxView
    # note: examyear.code is integer '2021'
    sel_examyear, sel_scheme_pk = None, None
    req_user = request.user
    if req_user:
        selected_pk_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if selected_pk_dict:
            sel_examyear = sch_mod.Examyear.objects.get_or_none(
                pk=selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK),
                country=request.user.country
            )

        sel_scheme_pk = selected_pk_dict.get(c.KEY_SEL_SCHEME_PK)

    return sel_examyear, sel_scheme_pk


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def get_selected_experiod_extype_subject_from_usersetting(request):  # PR2021-01-20 PR2021-10-06
# - get selected examperiod and examtype and sel_subject_pk from usersettings
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_selected_experiod_extype_subject_from_usersetting ----- ' )

    sel_examperiod, sel_examtype, sel_subject_pk = None, None, None
    req_user = request.user
    if req_user:
        selected_pk_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if logging_on:
            logger.debug('selected_pk_dict: ' + str(selected_pk_dict) )
        if selected_pk_dict:
            sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
            sel_examtype = selected_pk_dict.get(c.KEY_SEL_EXAMTYPE)
            sel_subject_pk = selected_pk_dict.get(c.KEY_SEL_SUBJECT_PK)
    return sel_examperiod, sel_examtype, sel_subject_pk
# - end of get_selected_experiod_extype_subject_from_usersetting


def get_selected_ey_school_dep_from_usersetting(request):  # PR2021-1-13 PR2021-06-14
    logging_on = False # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_selected_ey_school_dep_from_usersetting ----- ' )
    # this function gets sel_examyear, sel_school, sel_department from req_user and usersetting

    # checks if user may edit .
        # may_edit = False when:
        # - examyear, schoolbase, school, depbase or department is None
        # - country, examyear or school is locked
        # - not requsr_same_school,
        # - not sel_examyear.published,
        # - not sel_school.activated,
        # not af.is_allowed_depbase_requsr or not af.is_allowed_depbase_school,

    req_user = request.user
    sel_examyear, sel_school, sel_department = None, None, None
    msg_list = []

# ==== COUNTRY ========================
# - get country from req_user
    if req_user.country is None:
        msg_list.append(str(_('User has no country.')))
    else:
        requsr_country = req_user.country
        if requsr_country.locked:
            msg_list.append(str(_('This country is locked.')))

        selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)

        if logging_on:
            logger.debug('selected_dict: ' + str(selected_dict))

# ===== SCHOOLBASE =================
    # - get selected schoolbase from Usersetting, from role if role = school
        if req_user.role == c.ROLE_008_SCHOOL:
            sel_sb_pk = req_user.schoolbase.pk
        else:
            sel_sb_pk = selected_dict.get(c.KEY_SEL_SCHOOLBASE_PK)

        sel_schoolbase = sch_mod.Schoolbase.objects.get_or_none(
            pk=sel_sb_pk,
            country=requsr_country
        )
        if sel_schoolbase is None:
            msg_list.append(str(_('User has no school.')))
        else:
            # requsr_same_school = True when selected school is same as requsr_school PR2021-04-27
            # used on entering students and grades. Schools can only enter grades of their own school
            requsr_same_school = (req_user.role == c.ROLE_008_SCHOOL and req_user.schoolbase.pk == sel_schoolbase.pk)
            if not requsr_same_school:
                msg_list.append(str(_('Only users of this school are allowed to make changes.')))

            if logging_on:
                logger.debug('sel_schoolbase: ' + str(sel_schoolbase))

# ===== EXAMYEAR =======================
    # - get selected examyear from Usersetting
            sel_examyear = sch_mod.Examyear.objects.get_or_none(
                pk=selected_dict.get(c.KEY_SEL_EXAMYEAR_PK),
                country=requsr_country
            )
    # - add info to msg_list, will be sent back to client
            if sel_examyear is None:
                msg_list.append(str(_('No exam year selected.')))
            elif not sel_examyear.published:
                msg_list.append(str(_('This exam year is not published yet.')))
            elif sel_examyear.locked:
                msg_list.append(str(_('This exam year is locked.')))

            if logging_on:
                logger.debug('sel_examyear: ' + str(sel_examyear))

# ===== SCHOOL =======================
            sel_school = sch_mod.School.objects.get_or_none(
                base=sel_schoolbase,
                examyear=sel_examyear
            )
            if sel_school is None:
                msg_list.append(str(_('School not found in this exam year.')))
            else:
                if not sel_school.activated:
                    msg_list.append(str(_('The school has not activated this exam year yet.')))
                elif sel_school.locked:
                    msg_list.append(str(_('This school is locked.')))

                if logging_on:
                    logger.debug('sel_school: ' + str(sel_school))

# ===== DEPBASE =======================
                sel_depbase = sch_mod.Departmentbase.objects.get_or_none(
                    pk=selected_dict.get(c.KEY_SEL_DEPBASE_PK)
                )

        # get first depbase from sel_school.depbases if sel_depbase is None
                if sel_depbase is None:
                    if sel_school.depbases:
                        depbase_list = sel_school.depbases.split(';')
                        if depbase_list:
                            sel_depbase = sch_mod.Departmentbase.objects.get_or_none(pk=depbase_list[0])
                if logging_on:
                    logger.debug('sel_depbase: ' + str(sel_depbase))

# ===== DEPARTMENT =======================
                if sel_depbase is None:
                    msg_list.append(str(_('There is no department selected.')))
                else:
                    if not af.is_allowed_depbase_requsr(sel_depbase.pk, request):
                        msg_list.append(str(_("You don't have permission to view department %(val)s.") % {'val': sel_depbase.code}))
                    else:
                        if not af.is_allowed_depbase_school(sel_depbase.pk, sel_school):
                            msg_list.append(str(_("This school does not have department %(val)s.") % {'val': sel_depbase.code}))
                        else:
                            sel_department = sch_mod.Department.objects.get_or_none(
                                base=sel_depbase,
                                examyear=sel_examyear
                            )

                            if logging_on:
                                logger.debug('sel_department: ' + str(sel_department))

                            if sel_department is None:
                                msg_list.append(str(_("Department %(val)s not found in this examyear.") % {'val': sel_depbase.code}))

    may_edit = len(msg_list) == 0

    if logging_on:
        logger.debug('msg_list: ' + str(msg_list))
        logger.debug('may_edit: ' + str(may_edit))

    return sel_examyear, sel_school, sel_department, may_edit, msg_list
# - end of get_selected_ey_school_dep_from_usersetting

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def get_selected_examyear_from_usersetting(request):  # PR2021-09-08
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_selected_examyear_from_usersetting ----- ' )
    # this function gets sel_examyear, from req_user and usersetting
    # used in publish orderlist, where no selected school or dep is needed
    # checks if user may edit .

    req_user = request.user
    sel_examyear = None
    msg_list = []

# ==== COUNTRY ========================
# - get country from req_user
    if req_user.country:
        requsr_country = req_user.country
        if requsr_country.locked:
            msg_list.append(str(_('This country is locked.')))
        else:
            selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
            if logging_on:
                logger.debug('selected_dict: ' + str(selected_dict))

# ===== EXAMYEAR =======================
    # - get selected examyear from Usersetting
            sel_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
            sel_examyear = sch_mod.Examyear.objects.get_or_none(
                pk=sel_examyear_pk,
                country=requsr_country
            )
            if logging_on:
                logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk) + ' ' + str(type(sel_examyear_pk)))
                logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    # - add info to msg_list, will be sent back to client
            if sel_examyear is None:
                msg_list.append(str(_('No exam year selected.')))
            elif not sel_examyear.published:
                msg_list.append(str(_('This exam year is not published yet.')))
            elif sel_examyear.locked:
                msg_list.append(str(_('This exam year is locked.')))

            if logging_on:
                logger.debug('sel_examyear: ' + str(sel_examyear))

    may_edit = len(msg_list) == 0

    if logging_on:
        logger.debug('msg_list: ' + str(msg_list))
        logger.debug('may_edit: ' + str(may_edit))

    return sel_examyear, may_edit, msg_list
# - end of get_selected_examyear_from_usersetting


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def create_permit_dict(req_user):
# - get role from req_user, put them in setting_dict PR2020-12-14  PR2021-01-26 PR2021-04-22
    permit_dict = {'requsr_pk': req_user.pk,
                    'requsr_name': req_user.last_name,
                    'requsr_role': req_user.role}

    if req_user.is_authenticated and req_user.role is not None:
        if req_user.role == c.ROLE_008_SCHOOL:
            permit_dict['requsr_role_school'] = True
        elif req_user.role == c.ROLE_016_COMM:
            permit_dict['requsr_role_comm'] = True
        elif req_user.role == c.ROLE_032_INSP:
            permit_dict['requsr_role_insp'] = True
        elif req_user.role == c.ROLE_064_ADMIN:
            permit_dict['requsr_role_admin'] = True
        elif req_user.role == c.ROLE_128_SYSTEM:
            permit_dict['requsr_role_system'] = True

# - get usergroups from req_user, put them in setting_dict
        user_groups = getattr(req_user, 'usergroups')
        if user_groups:
            requsr_usergroups_list = user_groups.split(';')
            for usergroup in requsr_usergroups_list:
                if usergroup == c.USERGROUP_READ:
                    permit_dict['usergroup_read'] = True
                if usergroup == c.USERGROUP_EDIT:
                    permit_dict['usergroup_edit'] = True
                if usergroup == c.USERGROUP_AUTH1_PRES:
                    permit_dict['usergroup_auth1'] = True
                if usergroup == c.USERGROUP_AUTH2_SECR:
                    permit_dict['usergroup_auth2'] = True
                if usergroup == c.USERGROUP_AUTH3_COM:
                    permit_dict['usergroup_auth3'] = True
                if usergroup == c.USERGROUP_AUTH4_EXAM:
                    permit_dict['usergroup_auth4'] = True
                if usergroup == c.USERGROUP_ANALYZE:
                    permit_dict['usergroup_anlz'] = True
                if usergroup == c.USERGROUP_ADMIN:
                    permit_dict['usergroup_admin'] = True

# ===== SCHOOL =======================
# - roles higher than school may select other schools PR2021-04-23
        permit_dict['may_select_school'] = (req_user.role > c.ROLE_008_SCHOOL)

    return permit_dict