# PR2020-09-17 PR2021-01-27
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Q, Value
from django.db.models.functions import Lower, Coalesce
from django.http import HttpResponse
from django.shortcuts import render, redirect #, get_object_or_404
from django.utils.translation import activate, ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.generic import View

from timeit import default_timer as timer

from accounts import views as av

from awpr import constants as c
from awpr import functions as af
from awpr import validators as val
from awpr import locale as loc
from schools import models as sch_mod
from schools import functions as sch_fnc
from schools import dicts as school_dicts
from subjects import views as sj_vw
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
        #logger.debug(' ')
        #logger.debug(' ++++++++++++++++++++ DatalistDownloadView ++++++++++++++++++++ ')
        #logger.debug('request.POST' + str(request.POST))

        #logger.debug('request.user' + str(request.user))
        #logger.debug('request.user.country' + str(request.user.country))
        #logger.debug('request.user.schoolbase' + str(request.user.schoolbase))

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
                #logger.debug('datalist_request: ' + str(datalist_request) + ' ' + str(type(datalist_request)))

# ----- get user settings -- first get settings, these are used in other downloads
                # download_setting will update usersetting with items in request_item_setting, and retrieve saved settings
                request_item_setting = datalist_request.get('setting')
                new_setting_dict, awp_message, sel_examyear, sel_schoolbase, sel_depbase = \
                    download_setting(request_item_setting, user_lang, request)
                # only add setting_dict to  datalists when called by request_item_setting 'setting'
                if request_item_setting and new_setting_dict:
                    datalists['setting_dict'] = new_setting_dict
                if awp_message:
                    awp_messages.append(awp_message)
                    datalists['awp_messages'] = awp_messages

# ----- get school settings
                request_item_setting = datalist_request.get('schoolsetting')
                if request_item_setting:
                    datalists['schoolsetting_dict'] = sch_fnc.get_schoolsetting(
                        request_item_setting, sel_examyear, sel_schoolbase, sel_depbase)

# ----- run system_updates if necessary
                af.system_updates(sel_examyear, request)

# ----- locale
                request_item_setting = datalist_request.get('locale')
                if request_item_setting:
                    # request_item_setting: {page: "employee"}
                    datalists['locale_dict'] = loc.get_locale_dict(request_item_setting, user_lang)

                # 9. return datalists
                # PR2020-05-23 debug: datalists = {} gives parse error.
                # elapsed_seconds to the rescue: now datalists will never be empty

# ----- get users
                request_item_setting = datalist_request.get('user_rows')
                if request_item_setting:
                    datalists['user_rows'] = av.create_user_list(request)

# ----- examyears
                if datalist_request.get('examyear_rows'):
                    datalists['examyear_rows'] = school_dicts.create_examyear_rows(request.user.country, {}, None)
# ----- departments
                if datalist_request.get('department_rows'):
                    datalists['department_rows'] = school_dicts.create_department_rows(sel_examyear)
# ----- levels
                if datalist_request.get('level_rows'):
                    datalists['level_rows'] = school_dicts.create_level_rows(sel_examyear)
# ----- sectors
                if datalist_request.get('sector_rows'):
                    datalists['sector_rows'] = school_dicts.create_sector_rows(sel_examyear)
# ----- schools
                if datalist_request.get('school_rows'):
                    datalists['school_rows'] = school_dicts.create_school_rows(sel_examyear, new_setting_dict)
# ----- subjects
                if datalist_request.get('subject_rows'):
                    datalists['subject_rows'] = sj_vw.create_subject_rows(new_setting_dict, {}, None)
# ----- students
                if datalist_request.get('student_rows'):
                    datalists['student_rows'] = st_vw.create_student_rows(new_setting_dict, {}, None)
# ----- studentsubjects
                if datalist_request.get('studentsubject_rows'):
                    datalists['studentsubject_rows'] = st_vw.create_studentsubject_rows(new_setting_dict, {})
# ----- studentsubjectnote
                request_item = datalist_request.get('studentsubjectnote_rows')
                if request_item:
                    datalists['studentsubjectnote_rows'] = st_vw.create_studentsubjectnote_rows(new_setting_dict,request_item)
# ----- grades
                if datalist_request.get('grade_rows'):
                    if sel_examyear and sel_schoolbase and sel_depbase:
                        datalists['grade_rows'] = gr_vw.create_grade_rows(
                            sel_examyear_pk=sel_examyear.pk,
                            sel_schoolbase_pk=sel_schoolbase.pk,
                            sel_depbase_pk=sel_depbase.pk,
                            sel_examperiod=new_setting_dict.get('sel_examperiod'),
                        )
# ----- published
                if datalist_request.get('published_rows'):
                    datalists['published_rows'] = gr_vw.create_published_rows(new_setting_dict)
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


def download_setting(request_item_setting, user_lang, request):  # PR2020-07-01 PR2020-1-14
    #logger.debug(' ----- download_setting ----- ' )
    #logger.debug('request_item_setting: ' + str(request_item_setting) )
    # this function get settingss from request_item_setting.
    # if not in request_item_setting, it takes the saved settings.

    req_user = request.user

# - selected_dict contains saved selected_pk's from Usersetting, key: selected_pk
    # changes are stored in this dict, saved at the end when
    selected_dict = req_user.get_usersetting_dict(c.KEY_SELECTED_PK)
    selected_dict_has_changed = False

# - setting_dict contains all info to be sent to client
    setting_dict = create_settingdict_with_role_and_permits(req_user, user_lang)

# ==== COUNTRY ========================
# - get country from req_user
    requsr_country = req_user.country
    setting_dict['requsr_country_pk'] = requsr_country.pk  if requsr_country else None
    setting_dict['requsr_country'] = requsr_country.name if requsr_country else None
    if requsr_country.locked:
        setting_dict['requsr_country_locked'] = True

# ===== SCHOOLBASE ======================= PR2020-12-18
# - get schoolbase from settings / request when role is insp, admin or system, from req_user otherwise
    # req_user.schoolbase cannot be changed
    # Selected schoolbase is stored in {selected_pk: {sel_schoolbase_pk: val}}

    requsr_schoolbase = req_user.schoolbase
    setting_dict['requsr_schoolbase_pk'] = requsr_schoolbase.pk if requsr_schoolbase else None
    setting_dict['requsr_schoolbase_code'] = requsr_schoolbase.code if requsr_schoolbase else None

    sel_schoolbase_instance, sel_schoolbase_save = af.get_sel_schoolbase_instance(request, request_item_setting)
    #logger.debug('sel_schoolbase_instance: ' + str(sel_schoolbase_instance) + ' pk: ' + str(sel_schoolbase_instance.pk))
    if sel_schoolbase_save:
        # when sel_schoolbase_save=True, there is always a sel_schoolbase_instance
        selected_dict[c.KEY_SEL_SCHOOLBASE_PK] = sel_schoolbase_instance.pk
        selected_dict_has_changed = True
    if sel_schoolbase_instance:
        setting_dict[c.KEY_SEL_SCHOOLBASE_PK] = sel_schoolbase_instance.pk
        setting_dict['sel_schoolbase_code'] = sel_schoolbase_instance.code
        setting_dict['sel_schoolbase_equals_requsr_sb'] = (sel_schoolbase_instance.pk == requsr_schoolbase.pk)

# ===== EXAMYEAR =======================
    # every user can change examyear, is stored in Usersetting.
    # request_item_setting: {'page_school': {'mode': 'get'}, 'sel_examyear_pk': 6}
# - get selected examyear from request_item_setting, Usersetting or first in list
    sel_examyear_instance, sel_examyear_save, may_select_examyear = af.get_sel_examyear_instance(request, request_item_setting)

    setting_dict['may_select_examyear'] = may_select_examyear

    #logger.debug('sel_examyear_instance: ' + str(sel_examyear_instance) + ' pk: ' + str(sel_examyear_instance.pk))
# - update selected_dict when selected_dict_has_changed, will be saved at end of def
    if sel_examyear_save:
        # sel_examyear_instance has always value when selected_dict_has_changed
        selected_dict[c.KEY_SEL_EXAMYEAR_PK] = sel_examyear_instance.pk
        selected_dict_has_changed = True
        #logger.debug('selected_dict_has_changed: ' + str(selected_dict_has_changed) )
# - add info to setting_dict, will be sent back to client
    if sel_examyear_instance:
        setting_dict[c.KEY_SEL_EXAMYEAR_PK] = sel_examyear_instance.pk
        setting_dict['sel_examyear_code'] = sel_examyear_instance.code if sel_examyear_instance.code else None
        if sel_examyear_instance.published:
            setting_dict['sel_examyear_published'] = sel_examyear_instance.published
        if sel_examyear_instance.locked:
            setting_dict['sel_examyear_locked'] = sel_examyear_instance.locked
# - add message when examyear is different from this eaxamyear
    awp_message = val.message_diff_exyr(sel_examyear_instance)  # PR2020-10-30

    #logger.debug('sel_schoolbase_instance: ' + str(sel_schoolbase_instance) + ' pk: ' + str(sel_schoolbase_instance.pk))
    #logger.debug('sel_examyear_instance: ' + str(sel_examyear_instance) + ' pk: ' + str(sel_examyear_instance.pk))

# ===== SCHOOL =======================
# - only roles insp, admin and system may select other schools
    may_select_school = req_user.is_role_insp or req_user.is_role_admin or req_user.is_role_system
    setting_dict['may_select_school'] = may_select_school

# get school from sel_schoolbase and sel_examyear_instance
    sel_school = sch_mod.School.objects.get_or_none(
        base=sel_schoolbase_instance,
        examyear=sel_examyear_instance)
    #logger.debug('get_or_none sel_school: ' + str(sel_school) )
    #sel_school2 = sch_mod.School.objects.filter(
    #    base=sel_schoolbase_instance,
    #    examyear=sel_examyear_instance).first()
    #logger.debug('first sel_school: ' + str(sel_school))

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

    sel_depbase_instance, sel_depbase_save, allowed_depbases = \
        af.get_sel_depbase_instance(sel_school, request, request_item_setting)

    setting_dict['allowed_depbases'] = allowed_depbases
    allowed_depbases_len = len(allowed_depbases)
    may_select_department = (allowed_depbases_len > 1)
    setting_dict['may_select_department'] = may_select_department

    # - update selected_dict when selected_dict_has_changed, will be saved at end of def
    if sel_depbase_save:
        # sel_depbase_instance has always value when selected_dict_has_changed
        selected_dict[c.KEY_SEL_DEPBASE_PK] = sel_depbase_instance.pk
        selected_dict_has_changed = True
        #logger.debug('selected_dict_has_changed: ' + str(selected_dict[c.KEY_SEL_DEPBASE_PK]))
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
            # setting_dict['sel_dep_sector_req'] = sel_department_instance.sector_req

        #logger.debug('>>>>>>>>>> setting_dict[sel_department_abbrev]: ' + str(setting_dict['sel_department_abbrev']))

# ===== EXAM PERIOD =======================
# every user can change exam period

    # - get saved_examperiod_int
    saved_examperiod_int = selected_dict.get(c.KEY_SEL_EXAMPERIOD)

    # - check if there is a new examperiod_pk in request_item_setting
    request_examperiod_pk = af.get_dict_value(request_item_setting,
                                              (c.KEY_SELECTED_PK, c.KEY_SEL_EXAMPERIOD))

    if saved_examperiod_int is None and request_examperiod_pk is None:
        request_examperiod_pk = c.EXAMPERIOD_FIRST

    # - use request_examyear when it has value and is different from the saved one
    if request_examperiod_pk and request_examperiod_pk != saved_examperiod_int:
        saved_examperiod_int = request_examperiod_pk
        # - update selected_dict, will be saved at end of def
        selected_dict_has_changed = True
        selected_dict[c.KEY_SEL_EXAMPERIOD] = saved_examperiod_int

    # - add info to setting_dict, will be sent back to client
    setting_dict[c.KEY_SEL_EXAMPERIOD] = saved_examperiod_int

    if saved_examperiod_int:
        setting_dict['sel_examperiod'] = saved_examperiod_int
        setting_dict['sel_examperiod_caption'] = c.EXAMPERIOD_CAPTION.get(saved_examperiod_int)

# ===== EXAM TYPE =======================
    # every user can change examtype

    # - get saved_examtype
    saved_examtype = selected_dict.get(c.KEY_SEL_EXAMTYPE)

    # - check if there is a new examtype in request_item_setting
    request_examtype = af.get_dict_value(request_item_setting,
                                              (c.KEY_SELECTED_PK, c.KEY_SEL_EXAMTYPE))

    if saved_examtype is None and request_examtype is None:
        request_examtype = 'se'

    # - use request_examtype when it has value and is different from the saved one
    if request_examtype and request_examtype != saved_examtype:
        saved_examtype = request_examtype
        # - update selected_dict, will be saved at end of def
        selected_dict_has_changed = True
        selected_dict[c.KEY_SEL_EXAMTYPE] = saved_examtype

    # - add info to setting_dict, will be sent back to client
    setting_dict[c.KEY_SEL_EXAMTYPE] = saved_examtype

    if saved_examtype:
        setting_dict['sel_examtype_caption'] = c.EXAMTYPE_CAPTION.get(saved_examtype)

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# ===== SUBJECT and STUDENT ======================= PR2021-01-23
    for key_str in (c.KEY_SEL_SUBJECT_PK, c.KEY_SEL_STUDENT_PK):
    # - get saved_pk_str
        saved_pk_str = selected_dict.get(key_str)
    # - check if there is a new pk_str in request_item_setting
        request_pk_str = af.get_dict_value(request_item_setting, (c.KEY_SELECTED_PK, key_str))
    # - use request_pk_str when it has value and is different from the saved one
        if request_pk_str and request_pk_str != saved_pk_str:
    # - request_pk_str = "-1" means: show all: convert '-1' to None
            if request_pk_str == '-1':
                request_pk_str = None
            saved_pk_str = request_pk_str
    # - update selected_dict, will be saved at end of def
            selected_dict_has_changed = True
            selected_dict[key_str] = saved_pk_str
    # - add info to setting_dict, will be sent back to client
        if saved_pk_str:
            setting_dict[key_str] = int(saved_pk_str)
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# ===== SELECTED_PK SETTINGS =======================
    # request_item_setting: {'selected_pk': {'sel_examyear_pk': 23, 'sel_schoolbase_pk': 15}, 'sel_depbase_pk': 15}}
    if request_item_setting:
        # <PERMIT> PR2020-10-27
        # - user can only change school when req_user is_role_insp, is_role_admin or is_role_system:
        #  otherwise sel_schoolbase_pk is equal to _requsr_schoolbase_pk

################################
# - get rest of keys
        for key, request_dict in request_item_setting.items():
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
                    sel_keys = ('sel_btn', 'period_start', 'period_end', 'grid_range')
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
    #logger.debug('setting_dict: ' + str(setting_dict))

    # - save settings when they have changed
    if selected_dict_has_changed:
        req_user.set_usersetting_dict(c.KEY_SELECTED_PK, selected_dict)

    return setting_dict, awp_message, sel_examyear_instance, sel_schoolbase_instance, sel_depbase_instance
# - end of download_setting


def get_selected_examperiod_examtype_from_usersetting(request):  # PR2021-01-20
# - get selected examperiod and examtype from usersettings
    sel_examperiod, sel_examtype, sel_subject_pk = None, None, None
    req_user = request.user
    if req_user:
        selected_dict = req_user.get_usersetting_dict(c.KEY_SELECTED_PK)
        if selected_dict:
            sel_examperiod = selected_dict.get(c.KEY_SEL_EXAMPERIOD)
            sel_examtype = selected_dict.get(c.KEY_SEL_EXAMTYPE)
            sel_subject_pk = selected_dict.get(c.KEY_SEL_SUBJECT_PK)
    return sel_examperiod, sel_examtype, sel_subject_pk


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def get_selected_examyear_school_dep_from_usersetting(request):  # PR2021-1-13
    #logger.debug(' ----- get_selected_examyear_school_dep_from_usersetting ----- ' )
    # logger.debug('request_item_setting: ' + str(request_item_setting) )
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
def create_settingdict_with_role_and_permits(req_user, user_lang):
# - get role from req_user, put them in setting_dict PR2020-12-14  PR2021-01-26
    setting_dict = {'user_lang': user_lang,
                    'requsr_pk': req_user.pk,
                    'requsr_name': req_user.last_name,
                    'requsr_role': req_user.role}
    if req_user.is_role_student:
        setting_dict['requsr_role_student'] = req_user.is_role_student
    if req_user.is_role_teacher:
        setting_dict['requsr_role_teacher'] = req_user.is_role_teacher
    if req_user.is_role_school:
        setting_dict['requsr_role_school'] = req_user.is_role_school
    if req_user.is_role_insp:
        setting_dict['requsr_role_insp'] = req_user.is_role_insp
    if req_user.is_role_admin:
        setting_dict['requsr_role_admin'] = req_user.is_role_admin
    if req_user.is_role_system:
        setting_dict['requsr_role_system'] = req_user.is_role_system

# - get permissions from req_user, put them in setting_dict
    if req_user.is_perm_read:
        setting_dict['requsr_perm_read'] = req_user.is_perm_read
    if req_user.is_perm_edit:
        setting_dict['requsr_perm_edit'] = req_user.is_perm_edit
    if req_user.is_perm_auth1:
        setting_dict['requsr_perm_auth1'] = req_user.is_perm_auth1
    if req_user.is_perm_auth2:
        setting_dict['requsr_perm_auth2'] = req_user.is_perm_auth2
    if req_user.is_perm_auth3:
        setting_dict['requsr_perm_auth3'] = req_user.is_perm_auth3
    if req_user.is_perm_anlz:
        setting_dict['requsr_perm_anlz'] = req_user.is_perm_anlz
    if req_user.is_perm_admin:
        setting_dict['requsr_perm_admin'] = req_user.is_perm_admin
    if req_user.is_perm_system:
        setting_dict['requsr_perm_system'] = req_user.is_perm_system

    return setting_dict