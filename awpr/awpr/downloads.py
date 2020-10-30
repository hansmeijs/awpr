# PR2020-09-17
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Q, Value
from django.db.models.functions import Lower, Coalesce
from django.http import HttpResponse
from django.shortcuts import render, redirect #, get_object_or_404
from django.utils.translation import activate, ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, View

from datetime import date, time, datetime, timedelta
from timeit import default_timer as timer

from accounts.models import User, Usersetting
from accounts import views as av

from awpr import constants as c
from awpr import functions as f
from awpr import validators as val
from awpr import locale as loc
from schools import models as school_model
from schools import functions as sch_fnc
from schools import dicts as school_dicts
from subjects import views as sj_vw
from students import views as st_vw

import json

import logging
logger = logging.getLogger(__name__)


# === DatalistDownloadView ===================================== PR2019-05-23
@method_decorator([login_required], name='dispatch')
class DatalistDownloadView(View):  # PR2019-05-23
    #logging.disable(logging.CRITICAL)  # logging.CRITICAL disables logging calls with levels <= CRITICAL
    logging.disable(logging.NOTSET)  # logging.NOTSET re-enables logging

    def post(self, request, *args, **kwargs):
        logger.debug(' ')
        logger.debug(' ++++++++++++++++++++ DatalistDownloadView ++++++++++++++++++++ ')
        #logger.debug('request.POST' + str(request.POST))

        #logger.debug('request.user' + str(request.user))
        #logger.debug('request.user.country' + str(request.user.country))
        #logger.debug('request.user.schoolbase' + str(request.user.schoolbase))
        #logger.debug('request.user.examyear' + str(request.user.examyear))

        starttime = timer()
        datalists = {}
        awp_messages = []
        if request.user is not None:
            if request.user.country and request.user.examyear and request.user.schoolbase:
                country = request.user.country
                examyear = request.user.examyear
                schoolbase = request.user.schoolbase
                if request.POST['download']:
                    #f.system_updates()
# ----- get user_lang
                    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                    activate(user_lang)

# ----- get datalist_request
                    datalist_request = json.loads(request.POST['download'])
                    logger.debug('datalist_request: ' + str(datalist_request) + ' ' + str(type(datalist_request)))

# ----- get user settings -- first get settings, these are used in other downloads
                    # download_setting will update usersetting with items in request_item, and retrieve saved settings
                    request_item = datalist_request.get('setting')
                    new_setting_dict, awp_message = download_setting(request_item, user_lang, request)
                    # only add setting_dict to  datalists when called by request_item 'setting'
                    if request_item and new_setting_dict:
                        datalists['setting_dict'] = new_setting_dict
                    if awp_message:
                        awp_messages.append(awp_message)
                        datalists['awp_messages'] = awp_messages
# ----- get school settings
                    request_item = datalist_request.get('schoolsetting')
                    if request_item:
                        datalists['schoolsetting_dict'] = sch_fnc.get_schoolsetting(request_item, user_lang, request)

# ----- locale
                    request_item = datalist_request.get('locale')
                    if request_item:
                        # request_item: {page: "employee"}
                        datalists['locale_dict'] = loc.get_locale_dict(request_item, user_lang)

                    # 9. return datalists
                    # PR2020-05-23 debug: datalists = {} gives parse error.
                    # elapsed_seconds to the rescue: now datalists will never be empty

# ----- get user_rows
                    request_item = datalist_request.get('user_rows')
                    if request_item:
                        datalists['user_rows'] = av.create_user_list(request)

# ----- examyears
                    if datalist_request.get('examyear_rows'):
                        datalists['examyear_rows'] = school_dicts.create_examyear_rows(country, {}, None)
# ----- departments
                    if datalist_request.get('department_rows'):
                        datalists['department_rows'] = school_dicts.create_department_rows(examyear)
# ----- schools
                    if datalist_request.get('school_rows'):
                        datalists['school_rows'] = school_dicts.create_school_rows(examyear)
# ----- subjects
                    if datalist_request.get('subject_rows'):
                        datalists['subject_rows'] = sj_vw.create_subject_rows(new_setting_dict, {}, None)
# ----- students
                    if datalist_request.get('student_rows'):
                        datalists['student_rows'] = st_vw.create_student_rows(examyear, {}, None)

        elapsed_seconds = int(1000 * (timer() - starttime)) / 1000
        datalists['elapsed_seconds'] = elapsed_seconds

        datalists_json = json.dumps(datalists, cls=f.LazyEncoder)

        return HttpResponse(datalists_json)

def download_setting(request_item, user_lang, request):  # PR2020-07-01
    logger.debug(' ----- download_setting ----- ' )
    logger.debug('request_item: ' + str(request_item) )
    # this function get settingss from request_item.
    # if not in request_item, it takes the saved settings.
    new_setting_dict = {'user_lang': user_lang}
    awp_message = {}
    if request.user:
        req_user = request.user

        if req_user.is_role_student:
            new_setting_dict['requsr_role_student'] = req_user.is_role_student
        if req_user.is_role_teacher:
            new_setting_dict['requsr_role_teacher'] = req_user.is_role_teacher
        if req_user.is_role_school:
            new_setting_dict['requsr_role_school'] = req_user.is_role_school
        if req_user.is_role_insp:
            new_setting_dict['requsr_role_insp'] = req_user.is_role_insp
        if req_user.is_role_admin:
            new_setting_dict['requsr_role_admin'] = req_user.is_role_admin
        if req_user.is_role_system:
            new_setting_dict['requsr_role_system'] = req_user.is_role_system

        if req_user.is_perm_read:
            new_setting_dict['requsr_perm_read'] = req_user.is_perm_read
        if req_user.is_perm_edit:
            new_setting_dict['requsr_perm_edit'] = req_user.is_perm_edit
        if req_user.is_perm_auth1:
            new_setting_dict['requsr_perm_auth1'] = req_user.is_perm_auth1
        if req_user.is_perm_auth2:
            new_setting_dict['requsr_perm_auth2'] = req_user.is_perm_auth2
        if req_user.is_perm_docs:
            new_setting_dict['requsr_perm_anlz'] = req_user.is_perm_docs
        if req_user.is_perm_admin:
            new_setting_dict['requsr_perm_admin'] = req_user.is_perm_admin
        if req_user.is_perm_system:
            new_setting_dict['requsr_perm_system'] = req_user.is_perm_system

        _req_user_schoolbase_pk = None
        if req_user.country:
            req_user_country = req_user.country
            new_setting_dict['requsr_country_pk'] = req_user_country.pk
            new_setting_dict['requsr_country'] = req_user_country.name
            _schoolbase = req_user.schoolbase
            if _schoolbase:
                _req_user_schoolbase_pk = _schoolbase.pk
                new_setting_dict['requsr_schoolbase_pk'] = _req_user_schoolbase_pk
                new_setting_dict['requsr_schoolbase_code'] = _schoolbase.code

# --- first save new selected examyear before retrieving examyear from req_user
                if request_item:
                    new_examyear_pk = request_item.get('requsr_examyear_pk')
                    if new_examyear_pk:
                        new_examyear = school_model.Examyear.objects.get_or_none(pk=new_examyear_pk)
                        if new_examyear:
                            req_user.examyear = new_examyear
                            req_user.save()
# --- get selected examyear
                _examyear = req_user.examyear
                if _examyear:
                    new_setting_dict['requsr_examyear_pk'] = _examyear.pk
                    new_setting_dict['requsr_examyear_examyear'] = _examyear.examyear
                    if _examyear.published:
                        new_setting_dict['requsr_examyear_published'] = _examyear.published
                    if _examyear.locked:
                        new_setting_dict['requsr_examyear_locked'] = _examyear.locked

                    awp_message = val.message_diff_exyr(_examyear)  # PR2020-10-30


# --- get selected school
                    _school = school_model.School.objects.get_or_none(base=req_user.schoolbase, examyear=_examyear)
                    if _school:
                        new_setting_dict['requsr_school_pk'] = _school.pk
                        new_setting_dict['requsr_school_name'] = _school.name
                        new_setting_dict['requsr_school_abbrev'] = _school.abbrev
                        if _school.activated:
                            new_setting_dict['requsr_school_activated'] = _school.activated
                        if _school.locked:
                            new_setting_dict['requsr_school_locked'] = _school.locked
# --- get selected department
                    _department = school_model.Department.objects.get_or_none(base=req_user.depbase, examyear=_examyear)
                    if _department:
                        new_setting_dict['requsr_depbase_pk'] = _department.base.pk
                        new_setting_dict['requsr_department_name'] = _department.name
                        new_setting_dict['requsr_department_abbrev'] = _department.abbrev

        # request_item: {'selected_pk': {'sel_examyear_pk': 23, 'sel_schoolbase_pk': 15}, 'sel_depbase_pk': 15}}
        if request_item:
            #<PERMIT> PR2020-10-27
            # - user can only change school when req_user is_role_insp, is_role_admin or is_role_system:
            #  otherwise sel_schoolbase_pk is equal to _req_user_schoolbase_pk

    # - get selected examyear
            new_examyear_pk = request_item.get('requsr_examyear_pk')
            if new_examyear_pk:
                new_examyear = school_model.Examyear.objects.get_or_none(pk=new_examyear_pk)
                if new_examyear:
                    req_user.examyear = new_examyear
                    req_user.save()


             # - always get selected pks from key 'selected_pk'
            key = 'selected_pk'
            has_changed = False
        # - get saved setting_dict
            saved_setting_dict = Usersetting.get_jsonsetting(key, req_user)
            new_selected_pk_dict = {}
        # - get request_dict
            request_dict = request_item.get(key)
            logger.debug('request_dict: ' + str(request_dict))
            logger.debug('saved_setting_dict: ' + str(saved_setting_dict))

        # - loop through  sel_keys
            sel_keys = ( 'sel_schoolbase_pk', 'sel_depbase_pk')
            for sel_key in sel_keys:
                skip_item = False
                if sel_key == 'sel_schoolbase_pk':
                    if not req_user.is_role_insp and not req_user.is_role_admin and not req_user.is_role_system:
                        skip_item = True
                        new_setting_dict[sel_key] = _req_user_schoolbase_pk

                logger.debug('sel_key: ' + str(sel_key))
                logger.debug('skip_item: ' + str(skip_item))
                if not skip_item:
        # - get saved_value
                    saved_value = saved_setting_dict.get(sel_key, 0)
                    new_value = saved_value
                    logger.debug('saved_value: ' + str(saved_value))
            # - check if sel_key is in request_dict
                    if request_dict and sel_key in request_dict:
            # - get request_value
                        request_value = request_dict.get(sel_key, 0)
                        logger.debug('request_value: ' + str(request_value))
            # - use saved_value if request_value is None
                        if request_value != saved_value:
                            new_value = request_value
                            has_changed = True
                        logger.debug('new_value: ' + str(new_value))
            # - store value in dict, also saved value when value has not changed
                    new_selected_pk_dict[sel_key] = new_value
                    new_setting_dict[sel_key] = new_value
                    #logger.debug('new_setting_dict: ' + str(new_setting_dict))
            logger.debug('has_changed: ' + str(has_changed))
            if has_changed:
                Usersetting.set_jsonsetting(key, new_selected_pk_dict, req_user)

    # - get rest of keys
            for key in request_item:
                if key != 'selected_pk' and key != 'requsr_examyear_pk':
                    has_changed = False
                    new_page_dict = {}
                    saved_setting_dict = Usersetting.get_jsonsetting(key, req_user)

                    request_dict = request_item.get(key)

    ################################
    # get page
                    if key[:4] == 'page':
                        # if 'page_' in request: and saved_btn == 'planning': also retrieve period
                        new_setting_dict['sel_page'] = key
                        #logger.debug('new_setting_dict: ' + str(new_setting_dict))
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
                                new_setting_dict[sel_key] = new_value

    ###################################
    # get others, with key = 'value'
                    else:
                        sel_key = 'value'
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
                            new_page_dict[key] = new_value
                            new_setting_dict[key] = new_value
    # - save
                    if has_changed:
                        Usersetting.set_jsonsetting(key, new_page_dict, req_user)
    return new_setting_dict, awp_message
