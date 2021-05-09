# PR2020-09-17 PR2021-01-27
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import activate
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
from students import views as st_vw
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
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ++++++++++++++++++++ DatalistDownloadView ++++++++++++++++++++ ')

        starttime = timer()
        datalists = {}
        awp_messages = []
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
                new_setting_dict, permit_dict, awp_messages, sel_examyear, sel_schoolbase, sel_depbase = \
                    download_setting(request_item_setting, user_lang, request)

                if permit_dict:
                    datalists['permit_dict'] = permit_dict

                # only add setting_dict to  datalists when called by request_item_setting 'setting'
                if request_item_setting and new_setting_dict:
                    datalists['setting_dict'] = new_setting_dict

                if awp_messages:
                    datalists['awp_messages'] = awp_messages

# ----- get school settings (includes import settings)
                request_item_setting = datalist_request.get('schoolsetting')
                if request_item_setting:
                    datalists['schoolsetting_dict'] = sch_fnc.get_schoolsetting(
                        request_item_setting, sel_examyear, sel_schoolbase, sel_depbase)

# ----- run system_updates if necessary
                af.system_updates(sel_examyear, request)

# ----- locale
                request_item_setting = datalist_request.get('locale')
                if request_item_setting:
                    datalists['locale_dict'] = loc.get_locale_dict(request_item_setting, user_lang)

                # 9. return datalists
                # PR2020-05-23 debug: datalists = {} gives parse error.
                # elapsed_seconds to the rescue: now datalists will never be empty

# ----- get users
                if datalist_request.get('user_rows'):
                    datalists['user_rows'] = acc_view.create_user_list(request)
                    datalists['permit_rows'] = acc_view.create_permit_list()

# ----- examyears
                if datalist_request.get('examyear_rows'):
                    datalists['examyear_rows'] = school_dicts.create_examyear_rows(request.user, {}, None)
# ----- schools
                if datalist_request.get('school_rows'):
                    datalists['school_rows'] = school_dicts.create_school_rows(sel_examyear, permit_dict, {}, None)
# ----- departments
                if datalist_request.get('department_rows'):
                    datalists['department_rows'] = school_dicts.create_department_rows(sel_examyear)
# ----- levels
                if datalist_request.get('level_rows'):
                    datalists['level_rows'] = school_dicts.create_level_rows(sel_examyear, sel_depbase)
# ----- sectors
                if datalist_request.get('sector_rows'):
                    datalists['sector_rows'] = school_dicts.create_sector_rows(sel_examyear, sel_depbase)
# ----- subjects
                if datalist_request.get('subject_rows'):
                    datalists['subject_rows'] = sj_vw.create_subject_rows(new_setting_dict, {}, None)
# ----- exams
                if datalist_request.get('exam_rows'):
                    datalists['exam_rows'] = sj_vw.create_exam_rows(new_setting_dict, {}, None)
# ----- students
                if datalist_request.get('student_rows'):
                    datalists['student_rows'] = st_vw.create_student_rows(new_setting_dict, {}, None)
# ----- studentsubjects
                if datalist_request.get('studentsubject_rows'):
                    datalists['studentsubject_rows'] = st_vw.create_studentsubject_rows(new_setting_dict, {})
# ----- studentsubjectnote
                #request_item = datalist_request.get('studentsubjectnote_rows')
                #if request_item:
                #    datalists['studentsubjectnote_rows'] = st_vw.create_studentsubjectnote_rows(request_item, request)
# ----- grades
                if datalist_request.get('grade_rows'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['grade_rows'] = gr_vw.create_grade_rows(
                            sel_examyear_pk=sel_examyear.pk,
                            sel_schoolbase_pk=sel_schoolbase.pk,
                            sel_depbase_pk=sel_depbase.pk,
                            sel_examperiod=new_setting_dict.get('sel_examperiod'),
                            request=request
                        )
# ----- grade_note_icons
                if datalist_request.get('grade_note_icons'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['grade_note_icons'] = gr_vw.create_grade_note_icon_rows(
                            sel_examyear_pk=sel_examyear.pk,
                            sel_schoolbase_pk=sel_schoolbase.pk,
                            sel_depbase_pk=sel_depbase.pk,
                            sel_examperiod=new_setting_dict.get('sel_examperiod'),
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
# ----- schemes
                if datalist_request.get('scheme_rows'):
                    datalists['scheme_rows'] = sj_vw.create_scheme_rows(new_setting_dict, {}, None)
# ----- schemeitems
                if datalist_request.get('schemeitem_rows'):
                    datalists['schemeitem_rows'] = sj_vw.create_schemeitem_rows(new_setting_dict, {}, None)

        elapsed_seconds = int(1000 * (timer() - starttime)) / 1000
        datalists['elapsed_seconds'] = elapsed_seconds

        datalists_json = json.dumps(datalists, cls=af.LazyEncoder)

        return HttpResponse(datalists_json)


def download_setting(request_setting, user_lang, request):  # PR2020-07-01 PR2020-1-14

    if request_setting is None:
        request_setting = {}

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- download_setting ----- ')
        logger.debug('request_setting: ' + str(request_setting) )
    # this function get settingss from request_setting.
    # if not in request_setting, it takes the saved settings.

    # datalist_request_item 'setting' can have the follwoing keys that will be saved in usersettings:
    #   - key 'page':       required, stored in usersetting sel_page: ( page: 'page_grade'}
    #   - key 'selected_pk': not required, contains all selected pk's: to be saved in usersetting key 'selected_pk' (used in different pages (like examyear, schoolbase, depbase)

    # datalist_request_item 'setting' can have two key/values that will be saved in usersettings:
    #   - key 'page', required, stored in usersetting sel_page: ( page: 'page_grade'}
    #   - key 'selected_pk' saves selected values that are used in different pages (like examyear, schoolbase, depbase)
    #       - selected_pk: {sel_examyear_pk: 1, sel_schoolbase_pk: 13 etc
    #   - usersetting key 'sel_page' saves current page (to be opened at next login)  and kery 'page_user' etc  with key 'sel_btn'  that is different for every page:
    #       - sel_page: ( page: 'page_grade', page_user: {sel_btn: 'btn_grouppermits' }

    req_user = request.user

# ----- get page
    # request_item with key: 'setting' must always contain key: 'page'
    page = request_setting.get('page')

# - setting_dict contains all info to be sent to client, permit_dict contains permit related info
    setting_dict = {'user_lang': user_lang, 'sel_page': page}

# - get permit_list
    permit_dict = create_permit_dict(req_user)
    permit_list, usergroup_list = acc_view.get_userpermit_list(page, request.user)
    if permit_list:
        permit_dict['permit_list'] = permit_list
        permit_dict['usergroup_list'] = usergroup_list

# - selected_pk_dict contains saved selected_pk's from Usersetting, key: selected_pk
    # changes are stored in this dict, saved at the end when
    selected_pk_dict = req_user.get_usersetting_dict(c.KEY_SELECTED_PK)
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

    sel_schoolbase_instance, sel_schoolbase_save = af.get_sel_schoolbase_instance(request, request_setting)
    #logger.debug('sel_schoolbase_instance: ' + str(sel_schoolbase_instance) + ' pk: ' + str(sel_schoolbase_instance.pk))
    if sel_schoolbase_save:
        # when sel_schoolbase_save=True, there is always a sel_schoolbase_instance
        selected_pk_dict[c.KEY_SEL_SCHOOLBASE_PK] = sel_schoolbase_instance.pk
        selected_pk_dict_has_changed = True
    if sel_schoolbase_instance:
        setting_dict[c.KEY_SEL_SCHOOLBASE_PK] = sel_schoolbase_instance.pk
        setting_dict['sel_schoolbase_code'] = sel_schoolbase_instance.code
        setting_dict['sel_schoolbase_equals_requsr_sb'] = (sel_schoolbase_instance.pk == requsr_schoolbase.pk)

    # only role_school and same_school can view grades that are not published, PR2021-04-29
    permit_dict['requsr_same_school'] = (req_user.role == c.ROLE_008_SCHOOL and requsr_schoolbase.pk == sel_schoolbase_instance.pk)

# ===== EXAMYEAR =======================
    # every user can change examyear, is stored in Usersetting.
    # request_setting: {'page_school': {'mode': 'get'}, 'sel_examyear_pk': 6}
# - get selected examyear from request_setting, Usersetting or first in list
    sel_examyear_instance, sel_examyear_save, may_select_examyear = af.get_sel_examyear_instance(request, request_setting)

    permit_dict['may_select_examyear'] = may_select_examyear

    #logger.debug('sel_examyear_instance: ' + str(sel_examyear_instance) + ' pk: ' + str(sel_examyear_instance.pk))
# - update selected_pk_dict when selected_pk_dict_has_changed, will be saved at end of def
    if sel_examyear_save:
        # sel_examyear_instance has always value when selected_pk_dict_has_changed
        selected_pk_dict[c.KEY_SEL_EXAMYEAR_PK] = sel_examyear_instance.pk
        selected_pk_dict_has_changed = True
        #logger.debug('selected_pk_dict_has_changed: ' + str(selected_pk_dict_has_changed) )
# - add info to setting_dict, will be sent back to client
    if sel_examyear_instance:
        setting_dict[c.KEY_SEL_EXAMYEAR_PK] = sel_examyear_instance.pk
        setting_dict['sel_examyear_code'] = sel_examyear_instance.code if sel_examyear_instance.code else None
        if sel_examyear_instance.published:
            setting_dict['sel_examyear_published'] = sel_examyear_instance.published
        if sel_examyear_instance.locked:
            setting_dict['sel_examyear_locked'] = sel_examyear_instance.locked
# - add message when examyear is different from this eaxamyear
    awp_messages = []
    awp_message = val.message_diff_exyr(sel_examyear_instance)  # PR2020-10-30
    if awp_message:
        awp_messages.append(awp_message)
    #logger.debug('sel_examyear_instance: ' + str(sel_examyear_instance) + ' pk: ' + str(sel_examyear_instance.pk))

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
        # is_requsr_school = True when selected school is same as requsr_school PR2021-04-27
        # used on entering grades. Users can only enter grades of their own school. Syst, Adm and Insp, Comm can not neter grades
        permit_dict['is_requsr_school'] = (sel_schoolbase_instance.pk == requsr_schoolbase.pk)
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

    # - get saved_examperiod_int
    saved_depbase_pk_int = selected_pk_dict.get(c.KEY_SEL_DEPBASE_PK)

    # - check if there is a new examperiod_pk in request_setting
    request_depbase_pk_int = af.get_dict_value(request_setting,(c.KEY_SELECTED_PK, c.KEY_SEL_DEPBASE_PK))

    sel_depbase_instance, sel_depbase_save, allowed_depbases = \
        af.get_sel_depbase_instance(sel_school, request, request_setting)

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
        # sel_depbase_instance has always value when selected_pk_dict_has_changed
        selected_pk_dict[c.KEY_SEL_DEPBASE_PK] = sel_depbase_instance.pk
        selected_pk_dict_has_changed = True
        #logger.debug('selected_pk_dict_has_changed: ' + str(selected_pk_dict[c.KEY_SEL_DEPBASE_PK]))
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

        #logger.debug('>>>>>>>>>> setting_dict[sel_department_abbrev]: ' + str(setting_dict['sel_department_abbrev']))

# ===== EXAM PERIOD =======================
# every user can change exam period

    # - get saved_examperiod_int
    saved_examperiod_int = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)

    # - check if there is a new examperiod_pk in request_setting
    request_examperiod_pk = af.get_dict_value(request_setting,
                                              (c.KEY_SELECTED_PK, c.KEY_SEL_EXAMPERIOD))

    if saved_examperiod_int is None and request_examperiod_pk is None:
        request_examperiod_pk = c.EXAMPERIOD_FIRST

    # - use request_examyear when it has value and is different from the saved one
    if request_examperiod_pk and request_examperiod_pk != saved_examperiod_int:
        saved_examperiod_int = request_examperiod_pk
        # - update selected_pk_dict, will be saved at end of def
        selected_pk_dict_has_changed = True
        selected_pk_dict[c.KEY_SEL_EXAMPERIOD] = saved_examperiod_int

    # - add info to setting_dict, will be sent back to client
    setting_dict[c.KEY_SEL_EXAMPERIOD] = saved_examperiod_int

    if saved_examperiod_int:
        setting_dict['sel_examperiod'] = saved_examperiod_int
        setting_dict['sel_examperiod_caption'] = c.EXAMPERIOD_CAPTION.get(saved_examperiod_int)

# ===== EXAM TYPE =======================
    # every user can change examtype

    # - get saved_examtype
    saved_examtype = selected_pk_dict.get(c.KEY_SEL_EXAMTYPE)

    # - check if there is a new examtype in request_setting
    request_examtype = af.get_dict_value(request_setting,
                                              (c.KEY_SELECTED_PK, c.KEY_SEL_EXAMTYPE))

    if logging_on:
        logger.debug('saved_examtype: ' + str(saved_examtype))
        logger.debug('request_examtype: ' + str(request_examtype))

# - check if examtype is allowed in this saved_examperiod_int

# make list of examtypes that are allowed in this examperiod
# - also get the default_examtype of this examperiod
    allowed_examtype_list = []
    default_examtype = None
    for examtype_dict in c.EXAMTYPE_OPTIONS:
        # filter examtypes of this examperiod
        if examtype_dict.get('filter', -1) == saved_examperiod_int:
            value = examtype_dict.get('value')
            if value:
                allowed_examtype_list.append(value)

        # make first examtype the default_examtype
            if default_examtype is None:
                default_examtype = value
    if logging_on:
        logger.debug('allowed_examtype_list: ' + str(allowed_examtype_list))

# - check if saved examtype is allowed in this examperiod, set to default if not, make selected_pk_dict_has_changed = True
    if saved_examtype not in allowed_examtype_list:
        if logging_on:
            logger.debug('saved_examtype: ' + str(saved_examtype) + ' is not allowed in this examperiod, replace by: ' + str(default_examtype))
        saved_examtype = default_examtype
        # - update selected_pk_dict, may be replaced by request_examtype
        selected_pk_dict[c.KEY_SEL_EXAMTYPE] = saved_examtype
        selected_pk_dict_has_changed = True

# - check if saved request_examtype is allowed in this examperiod, set to None if not
    if request_examtype and request_examtype not in allowed_examtype_list:
        if logging_on:
            logger.debug('request_examtype: ' + str(request_examtype) + ' is not allowed in this examperiod, set to: None')
        request_examtype = None

# - use request_examtype when it has value and is different from the saved one
    if request_examtype and request_examtype != saved_examtype:
        if logging_on:
            logger.debug('Replace saved_examtype: ' + str(saved_examtype) + ' by request_examtype: ' + str(request_examtype))

        saved_examtype = request_examtype
        # - update selected_pk_dict, will be saved at end of def
        selected_pk_dict[c.KEY_SEL_EXAMTYPE] = saved_examtype
        selected_pk_dict_has_changed = True

        if logging_on:
            logger.debug(' update saved_examtype: ' + str(saved_examtype))

    # - add info to setting_dict, will be sent back to client
    setting_dict[c.KEY_SEL_EXAMTYPE] = saved_examtype

    if saved_examtype:
        setting_dict['sel_examtype_caption'] = c.EXAMTYPE_CAPTION.get(saved_examtype)

    if logging_on:
        logger.debug('setting_dict[c.KEY_SEL_EXAMTYPE]: ' + str(setting_dict[c.KEY_SEL_EXAMTYPE]))
        logger.debug('setting_dict[c.sel_examtype_caption]: ' + str(setting_dict['sel_examtype_caption']))

# ===== SUBJECT, STUDENT, LEVEL,SECTOR ======================= PR2021-01-23 PR2021-03-14
    for key_str in (c.KEY_SEL_SUBJECT_PK, c.KEY_SEL_STUDENT_PK, c.KEY_SEL_LEVEL_PK, c.KEY_SEL_SECTOR_PK):
    # - get saved_pk_str
        saved_pk_str = selected_pk_dict.get(key_str)
    # - check if there is a new pk_str in request_setting
        request_pk_str = af.get_dict_value(request_setting, (c.KEY_SELECTED_PK, key_str))
    # - use request_pk_str when it has value and is different from the saved one
        if request_pk_str and request_pk_str != saved_pk_str:
    # - request_pk_str = "-1" means: show all: convert '-1' to None
            if request_pk_str == '-1':
                request_pk_str = None
            saved_pk_str = request_pk_str
    # - update selected_pk_dict, will be saved at end of def
            selected_pk_dict_has_changed = True
            selected_pk_dict[key_str] = saved_pk_str
    # - add info to setting_dict, will be sent back to client
        if saved_pk_str:
            pk_int = int(saved_pk_str)
            setting_dict[key_str] = int(pk_int)
            if key_str == c.KEY_SEL_SUBJECT_PK:
                subject = subj_mod.Subject.objects.get_or_none(pk=pk_int)
                if subject:
                    setting_dict['sel_subject_code'] = subject.base.code
            elif key_str == c.KEY_SEL_STUDENT_PK:
                student = stud_mod.Student.objects.get_or_none(pk=pk_int)
                if student:
                    setting_dict['sel_student_name'] = student.fullname
            elif key_str == c.KEY_SEL_LEVEL_PK:
                level = subj_mod.Level.objects.get_or_none(pk=pk_int)
                if level:
                    setting_dict['sel_level_abbrev'] = level.abbrev
            elif key_str == c.KEY_SEL_SECTOR_PK:
                sector = subj_mod.Sector.objects.get_or_none(pk=pk_int)
                if sector:
                    setting_dict['sel_sector_abbrev'] = sector.abbrev

    # - save settings when they have changed
    if selected_pk_dict_has_changed:
        req_user.set_usersetting_dict(c.KEY_SELECTED_PK, selected_pk_dict)

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    """
    # - get rest of keys
    for key, request_dict in request_setting.items():
        skip_keys = ('selected_pk',)
        if key not in skip_keys:
            has_changed = False
            new_page_dict = {}
            saved_setting_dict = req_user.get_usersetting_dict(key)

            ################################
            # get page settings - keys starting with 'page_'
            if key[:5] == 'page_':
                # if 'page_' in request: and saved_btn == 'planning': also retrieve period
                setting_dict['sel_page'] = key
                # logger.debug('setting_dict: ' + str(setting_dict))
                sel_keys = ('sel_btn', ) #'period_start', 'period_end', 'grid_range')
                for sel_key in sel_keys:
                    saved_value = saved_setting_dict.get(sel_key)
                    new_value = saved_value
                    if request_dict and sel_key in request_dict:
                        request_value = request_dict.get(sel_key)
                        if request_value is None:
                            if saved_value is not None:
                                has_changed = True
                        elif request_value != saved_value:
                            new_value = request_value
                            has_changed = True
                    if new_value is not None:
                        new_page_dict[sel_key] = new_value
                        setting_dict[sel_key] = new_value
            if has_changed:
                req_user.set_usersetting_dict(key, new_page_dict)
    # logger.debug('setting_dict: ' + str(setting_dict))
    """

    return setting_dict, permit_dict, awp_messages, sel_examyear_instance, sel_schoolbase_instance, sel_depbase_instance
# - end of download_setting


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def get_selected_examperiod_examtype_from_usersetting(request):  # PR2021-01-20
# - get selected examperiod and examtype from usersettings
    sel_examperiod, sel_examtype, sel_subject_pk = None, None, None
    req_user = request.user
    if req_user:
        selected_pk_dict = req_user.get_usersetting_dict(c.KEY_SELECTED_PK)
        if selected_pk_dict:
            sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
            sel_examtype = selected_pk_dict.get(c.KEY_SEL_EXAMTYPE)
            sel_subject_pk = selected_pk_dict.get(c.KEY_SEL_SUBJECT_PK)
    return sel_examperiod, sel_examtype, sel_subject_pk


def get_selected_examyear_school_dep_from_usersetting(request):  # PR2021-1-13
    #logger.debug(' ----- get_selected_examyear_school_dep_from_usersetting ----- ' )
    #logger.debug('request_item_setting: ' + str(request_item_setting) )
    # this function get settingss from request_item_setting.
    # if not in request_item_setting, it takes the saved settings.

    req_user = request.user
    is_locked, examyear_published, school_activated, is_requsr_school = False, False, False, False

# ==== COUNTRY ========================
# - get country from req_user
    requsr_country = req_user.country
    if requsr_country.locked:
        is_locked = True

# ===== SCHOOLBASE ======================= PR2020-12-18
# - get sel_schoolbase from settings / request when role is insp, admin or system, from req_user otherwise
    sel_schoolbase, sel_schoolbase_saveNIU = af.get_sel_schoolbase_instance(request)
    if sel_schoolbase and req_user.schoolbase and sel_schoolbase == req_user.schoolbase:
        is_requsr_school = True

# ===== EXAMYEAR =======================
# every user can change examyear, is stored in Usersetting.
# - get selected examyear from request_item_setting, Usersetting or first in list
    sel_examyear, sel_examyear_save, may_select_examyear = af.get_sel_examyear_instance(request)

    # - add info to setting_dict, will be sent back to client
    if sel_examyear:
        if sel_examyear.published:
            examyear_published = True
        if sel_examyear.locked:
            is_locked = True

# ===== SCHOOL =======================
    sel_school = sch_mod.School.objects.get_or_none(base=sel_schoolbase, examyear=sel_examyear)
    if sel_school:
        if sel_school.activated:
            school_activated = True
        if sel_school.locked:
            is_locked = True

# ===== DEPBASE =======================
    sel_depbase, sel_depbase_saveNIU, allowed_depbasesNIU = af.get_sel_depbase_instance(sel_school, request)
    sel_department = None
    if sel_depbase:
        sel_department = sch_mod.Department.objects.get_or_none(base=sel_depbase, examyear=sel_examyear)

    return sel_examyear, sel_school, sel_department, \
           is_locked, examyear_published, school_activated, is_requsr_school
# - end of get_selected_examyear_school_dep_from_usersetting


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
                    permit_dict['requsr_group_read'] = True
                if usergroup == c.USERGROUP_EDIT:
                    permit_dict['requsr_group_edit'] = True
                if usergroup == c.USERGROUP_AUTH1_PRES:
                    permit_dict['requsr_group_auth1'] = True
                if usergroup == c.USERGROUP_AUTH2_SECR:
                    permit_dict['requsr_group_auth2'] = True
                if usergroup == c.USERGROUP_AUTH3_COM:
                    permit_dict['requsr_group_auth3'] = True
                if usergroup == c.USERGROUP_ANALYZE:
                    permit_dict['requsr_group_anlz'] = True
                if usergroup == c.USERGROUP_ADMIN:
                    permit_dict['requsr_group_admin'] = True

# ===== SCHOOL =======================
# - roles higher than school may select other schools PR2021-04-23
        permit_dict['may_select_school'] = (req_user.role > c.ROLE_008_SCHOOL)

    return permit_dict