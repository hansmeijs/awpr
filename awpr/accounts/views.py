from django.contrib.auth import login
from django.contrib.auth.decorators import login_required  # PR2018-04-01
from django.contrib.auth.mixins import UserPassesTestMixin  # PR2018-11-03
from django.contrib.sites.shortcuts import get_current_site

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm,
)

from django.core.mail import send_mail

from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotFound, FileResponse

from django.views.decorators.csrf import csrf_protect

from django import forms
from django.template import loader
from django.core.mail import EmailMultiAlternatives

import unicodedata
from django.contrib.auth import get_user_model, authenticate
UserModel = get_user_model()

from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator

# PR2022-02-13 From Django 4 we dont have force_text You Just have to Use force_str Instead of force_text.
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext_lazy as _
from django.views.generic import ListView, View, UpdateView, DeleteView, FormView

from django.contrib.auth.forms import SetPasswordForm # PR2018-10-14

from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.core.exceptions import ValidationError

from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
    REDIRECT_FIELD_NAME, get_user_model, login as auth_login,
    logout as auth_logout, update_session_auth_hash,
)

INTERNAL_RESET_SESSION_TOKEN = '_password_reset_token'


import xlsxwriter

from .forms import UserActivateForm
from .tokens import account_activation_token
from .models import User, User_log, Usersetting

from accounts import models as acc_mod
from accounts import permits as acc_prm
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


def _unicode_ci_compare(s1, s2):
    """
    Perform case-insensitive comparison of two identifiers, using the
    recommended algorithm from Unicode Technical Report 36, section
    2.11.2(B)(2).
    """
    return unicodedata.normalize('NFKC', s1).casefold() == unicodedata.normalize('NFKC', s2).casefold()



@method_decorator([login_required], name='dispatch')
class CorrectorListView(View):

    # PR2023-02-24
    def get(self, request):

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(" =====  CorrectorListView  =====")

    # -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

    # get_headerbar_param(request, page, param=None):
        # display school and department in header only when role = school
        display_school = request.user.role == c.ROLE_008_SCHOOL
        page = 'page_corrector'
        param = { 'display_school': display_school, 'display_department': False }
        headerbar_param = awpr_menu.get_headerbar_param(request, page, param)
        if logging_on:
            logger.debug("headerbar_param: " + str(headerbar_param))
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'correctors.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class UserListView(ListView):

    def get(self, request, *args, **kwargs):

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(" =====  UserListView  =====")

        # PR2018-05-27 list of users in UserListView:
        # - when role is system / admin: show all users
        # - when role is inspection: all users with role 'inspection' and country == request_user.country
        # - else (role is school): all users with role 'school' and schoolcode == request_user.schooldefault

        show_btn_userpermit = False
        if request.user.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
            if request.user.is_role_system:
                show_btn_userpermit = True

        # get_headerbar_param(request, page, param=None):  # PR2021-03-25
        page = 'page_user'
        param = {'show_btn_userpermit': show_btn_userpermit, 'display_school': True, 'display_department': False }
        headerbar_param = awpr_menu.get_headerbar_param(request, page, param)
        if logging_on:
            logger.debug("show_btn_userpermit: " + str(show_btn_userpermit))
            logger.debug("headerbar_param: " + str(headerbar_param))
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'users.html', headerbar_param)

# How To Create Users Without Setting Their Password PR2018-10-09
# from https://django-authtools.readthedocs.io/en/latest/how-to/invitation-email.html

########################################################################
# === UserUploadView ===================================== PR2020-08-02 PR2022-12-07
@method_decorator([login_required], name='dispatch')
class UserUploadView(View):
    #  UserUploadView is called from Users form when the sysadmin has filled in username and email and clicked on 'Submit'
    #  it returns a HttpResponse, with ok_msg or err-msg
    #  when ok: it also sends an email to the user

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ')
            logger.debug(' ========== UserUploadView ===============')

        update_wrap = {}
        msg_list =[]
        user_without_userallowed = None

# - reset language
        # PR2019-03-15 Debug: language gets lost, get req_usr.lang again
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        req_usr = request.user
        if req_usr and req_usr and req_usr:
            req_usr = request.user
            # <PERMIT> PR2020-09-24
            #  - only perm_admin and perm_system can add / edit / delete users
            #  - only role_system and role_admin (ETE) can add users of other schools
            #  - role_system, role_admin, role_insp, role_corr and role_school can add users of their own school

# - get selected examyear from usersettings,
            # - checks if country is locked and if examyear is missing, not published or locked
            # - skip allow_not_published when req_usr is admin (ETE) or system
            allow_not_published = req_usr.role >= c.ROLE_064_ADMIN
            sel_examyear, may_edit, msg_lst = get_selected_examyear_from_usersetting(request, allow_not_published)
            if msg_lst:
                msg_list.extend(msg_lst)

            # requsr_permitlist: ['view_page', 'crud_otherschool', 'crud', 'crud', 'permit_userpage']
            requsr_permitlist = acc_prm.get_permit_list('page_user', req_usr)

            has_permit_same_school, has_permit_other_schools = False, False
            if may_edit and requsr_permitlist:
                has_permit_other_schools = 'permit_crud_otherschool' in requsr_permitlist
                has_permit_same_school = 'permit_crud_sameschool' in requsr_permitlist

            if logging_on:
                logger.debug('    requsr_permitlist: ' + str(requsr_permitlist))
                logger.debug('    has_permit_other_schools: ' + str(has_permit_other_schools))
                logger.debug('    has_permit_same_school: ' + str(has_permit_same_school))

            if has_permit_same_school or has_permit_other_schools:

# - get upload_dict from request.POST
                upload_json = request.POST.get("upload")
                if upload_json:
                    upload_dict = json.loads(upload_json)

                    if logging_on:
                        logger.debug('upload_dict: ' + str(upload_dict))
                        logger.debug('    sel_examyear: ' + str(sel_examyear))

                    # upload_dict: {'mode': 'delete', 'user_pk': 169, 'user_ppk': 3, 'mapid': 'user_169'}
                    """
                    upload_dict: {'user_pk': None, 'schoolbase_pk': 13, 'mode': 'validate', 
                        'username': 'Hans__Meijs', 'last_name': 'Hans', 'email': 'hmeijs@gmail.com'}
                    """

# - get info from upload_dict
                    user_pk = upload_dict.get('user_pk')
                    user_schoolbase_pk = upload_dict.get('schoolbase_pk')
                    map_id = upload_dict.get('mapid')
                    mode = upload_dict.get('mode')

                    is_validate_only = (mode == 'validate')
                    update_wrap['mode'] = mode

                    if logging_on:
                        logger.debug('    user_pk: ' + str(user_pk))
                        logger.debug('    user_schoolbase_pk: ' + str(user_schoolbase_pk))
                        logger.debug('    map_id: ' + str(map_id))
                        logger.debug('    mode: ' + str(mode))

# - check if the user schoolbase exists
                    user_schoolbase = sch_mod.Schoolbase.objects.get_or_none(
                        id=user_schoolbase_pk,
                        country=req_usr.country
                    )
                    is_same_schoolbase = (user_schoolbase and user_schoolbase == req_usr.schoolbase)

                    if is_same_schoolbase:
                        new_usergroups_arr = (c.USERGROUP_READ, c.USERGROUP_EDIT)
                    else:
                        new_usergroups_arr = (c.USERGROUP_READ, c.USERGROUP_EDIT, c.USERGROUP_DOWNLOAD,
                                              c.USERGROUP_ARCHIVE, c.USERGROUP_ADMIN)

                    # <PERMIT> PR2021-04-23
                    # user role can never be higher dan requser role

                    err_dict = {}
                    has_permit = False
                    if user_schoolbase:
                        user_schoolbase_defaultrole = getattr(user_schoolbase, 'defaultrole')
                        if user_schoolbase_defaultrole is None:
                            user_schoolbase_defaultrole = 0
                        if user_schoolbase_defaultrole <= req_usr.role:
                            if has_permit_other_schools:
                                has_permit = True
                            elif has_permit_same_school:
                                has_permit = is_same_schoolbase

                        if logging_on:
                            logger.debug('    user_schoolbase: ' + str(user_schoolbase))
                            logger.debug('    user_schoolbase_defaultrole: ' + str(user_schoolbase_defaultrole))
                            logger.debug('    has_permit_other_schools: ' + str(has_permit_other_schools))
                            logger.debug('    has_permit_same_school: ' + str(has_permit_same_school))
                            logger.debug('    has_permit: ' + str(has_permit))

                    if not has_permit:
                        err_dict['msg01'] = _("You don't have permission to perform this action.")
                    else:
                        updated_dict = {}

# ++++  resend activation email ++++++++++++
                        if mode == 'send_activation_email':
                            send_activation_email(user_pk, update_wrap, err_dict, request)

# ++++  delete user or add userallowed ++++++++++++
                        elif mode in ('delete', 'user_without_userallowed'):
                            if user_pk:
                # - get user_instance
                                user_instance = None
                                if has_permit_other_schools:
                                    user_instance = acc_mod.User.objects.get_or_none(
                                        id=user_pk,
                                        country=req_usr.country
                                    )
                                elif has_permit_same_school:
                                    user_instance = acc_mod.User.objects.get_or_none(
                                        id=user_pk,
                                        country=req_usr.country,
                                        schoolbase=req_usr.schoolbase
                                    )

                                if logging_on:
                                    logger.debug('user_instance: ' + str(user_instance))

                                if user_instance:

                                    if mode == 'user_without_userallowed':

# ++++  add userallowed record of this examyear to user
                        # - get usergroups_arr from last UserAllowed record, get default if None

                                        last_userallowed = acc_mod.UserAllowed.objects.filter(
                                            user=user_instance
                                        ).order_by('-examyear__code').first()

                                        if last_userallowed and last_userallowed.usergroups:
                                            usergroups_str = last_userallowed.usergroups
                                        else:
                                            usergroups_str = json.dumps(new_usergroups_arr)

                                        now_utc = timezone.now()

                                        new_user_allowed = acc_mod.UserAllowed(
                                            user=user_instance,
                                            examyear=sel_examyear,
                                            usergroups=usergroups_str,
                                            modifiedby=request.user,
                                            modifiedat=now_utc
                                        )
                                        new_user_allowed.save()

                                        if new_user_allowed:
                                            created_instance_list = create_user_rowsNEW(sel_examyear, request, user_instance.pk)
                                            if created_instance_list:
                                                updated_dict = created_instance_list[0]
                                                updated_dict['created'] = True

                                    elif mode == 'delete':

# ++++  delete user ++++++++++++
                                        deleted_instance_list = create_user_rowsNEW(sel_examyear, request, user_instance.pk)

                                        if logging_on:
                                            logger.debug('deleted_instance_list: ' + str(deleted_instance_list))

                                        if deleted_instance_list:
                                            updated_dict = deleted_instance_list[0]
                                            updated_dict['mapid'] = 'user_' + str(user_instance.pk)

                                        # TODO change to userexamyear setting

                                        allowed_sections_dict, usergroups_arr, allowed_clusters_arr = get_requsr_usergroups_allowedsections_allowedclusters(request, sel_examyear)

                                        requsr_usergroupslist, allowed_sections_dict, allowed_clusters_list, sel_examyear_instance = acc_prm.get_allowedusergrouplist_allowedsectionsdict_allowedclusterlist(req_usr)

                                        if c.USERGROUP_ADMIN in requsr_usergroupslist and user_instance == req_usr:
                                            err_dict['msg01'] = _("System administrators cannot delete their own account.")
                                        else:
                                            try:
                                                # PR2021-02-05 debug: CASCADE delete usersetting not working. Delete manually
                                                usersettings = Usersetting.objects.filter(user=user_instance)
                                                for usersetting in usersettings:

                                                    if logging_on:
                                                        logger.debug('usersetting delete: ' + str(usersetting))
                                                    usersetting.delete()
                                                user_instance.delete()
                                                updated_dict['deleted'] = True

                                                if logging_on:
                                                    logger.debug('deleted: ' + str(True))
                                            except Exception as e:
                                                logger.error(getattr(e, 'message', str(e)))
                                                msg_html = ''.join((
                                                    str(_("User account '%(val)s' can not be deleted.") % {'val': user_instance.username_sliced}),
                                                    '<br>',
                                                    str(_("Instead, you can make the user account inactive."))))
                                                msg_dict = {'header': str(_('Delete user')), 'class': 'border_bg_invalid',
                                                            'msg_html': msg_html}
                                                msg_list.append(msg_dict)
                                            else:
                                                user_instance = None
                                                deleted_ok = True
                                                ##############

# ++++  create or validate new user ++++++++++++
                        elif mode in ('create', 'validate'):
                            # - get permits of new user.
                            #       - new_permits is 'write' when user_school is same as requsr_school,
                            #       - permits is 'write' plus 'admin' when user_school is different from requsr_school

                            # is_existing_user = True if user_pk else False

                            new_user_pk, err_dict, ok_dict, user_without_userallowed = \
                                create_or_validate_user_instance(
                                    user_schoolbase=user_schoolbase,
                                    upload_dict=upload_dict,
                                    user_pk=user_pk,
                                    usergroups_arr=new_usergroups_arr,
                                    is_validate_only=is_validate_only,
                                    user_lang=user_lang,
                                    sel_examyear=sel_examyear,
                                    request=request
                                )

                            if err_dict:
                                update_wrap['msg_err'] = err_dict
                            elif user_without_userallowed:
                                update_wrap['user_without_userallowed'] = user_without_userallowed
                            elif ok_dict:
                                update_wrap['msg_ok'] = ok_dict
                            # - new_user_pk has only value when new user is created, not when is_validate_only
                            # - create_user_rows returns list of only 1 user
                            if new_user_pk:
                                created_instance_list = create_user_rowsNEW(sel_examyear, request, new_user_pk)
                                if created_instance_list:
                                    updated_dict = created_instance_list[0]
                                    updated_dict['created'] = True
                        else:

# - +++++++++ update ++++++++++++
                            user_instance = None
                            if has_permit_other_schools:
                                user_instance = acc_mod.User.objects.get_or_none(
                                    id=user_pk,
                                    country=req_usr.country)
                            elif has_permit_same_school:
                                user_instance = acc_mod.User.objects.get_or_none(
                                    id=user_pk,
                                    country=req_usr.country,
                                    schoolbase=req_usr.schoolbase
                                )
                            if logging_on:
                                logger.debug('    user_instance: ' + str(user_instance))

                            if user_instance:
                                err_dict, ok_dict = update_user_instance(sel_examyear, user_instance, upload_dict, msg_list, request)
                                if err_dict:
                                    update_wrap['msg_err'] = err_dict
                                if ok_dict:
                                    update_wrap['msg_ok'] = ok_dict

        # - create_user_rows returns list of only 1 user
                                updated_instance_list = create_user_rowsNEW(sel_examyear, request, user_instance.pk)
                                updated_dict = updated_instance_list[0] if updated_instance_list else {}
                                updated_dict['updated'] = True
                                updated_dict['mapid'] = 'user_' + str(user_instance.pk)

    # - +++++++++ en of is update ++++++++++++
                        if updated_dict:
                            update_wrap['updated_user_rows'] = [updated_dict]

                    if err_dict:
                        update_wrap['msg_err'] = err_dict
                    elif is_validate_only:
                        update_wrap['validation_ok'] = True
        # TODO append  err_dict to  msg_list
        if msg_list:
            update_wrap['msg_dictlist'] = msg_list
        if user_without_userallowed:
            update_wrap['user_without_userallowed'] = user_without_userallowed
        # - create_user_rows returns list of only 1 user
        #update_wrap['user_list'] = ad.create_user_rows(request, instance.pk)

# - return update_wrap
        update_wrap_json = json.dumps(update_wrap, cls=af.LazyEncoder)
        return HttpResponse(update_wrap_json)
# === end of UserUploadView =====================================


########################################################################
# === UserAllowedSectionsUploadView ===================================== PR2022-10-26 PR2022-12-04 PR2023-01-16
@method_decorator([login_required], name='dispatch')
class UserAllowedSectionsUploadView(View):
    #  UserAllowedSectionsUploadView is called from Users form MUPS_Open

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ')
            logger.debug(' ========== UserAllowedSectionsUploadView ===============')

        update_wrap = {}
        msg_list = []

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = acc_prm.get_permit_crud_of_this_page('page_user', request)

        if logging_on:
            logger.debug('    has_permit: ' + str(has_permit))

        if not has_permit:
            msg_list.append(str(_("You don't have permission to perform this action.")))
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

# - get info from upload_dict
                selected_user_pk = upload_dict.get('user_pk')
                mode = upload_dict.get('mode')

                update_wrap['mode'] = mode

# - get selected examyear from usersettings
                sel_examyear, may_edit, msg_list = \
                    get_selected_examyear_from_usersetting(request)

# - get selected user instance
                user_instance = acc_mod.User.objects.get_or_none(
                    pk=selected_user_pk
                )
                if logging_on:
                    logger.debug('    user_instance: ' + str(user_instance))

                userallowed_instance = acc_mod.UserAllowed.objects.get_or_none(
                    user=user_instance,
                    examyear = sel_examyear
                )
                if logging_on:
                    logger.debug('userallowed_instance: ' + str(userallowed_instance))
                if mode == 'update':
                    new_allowed_sections = upload_dict.get('allowed_sections')
                    if logging_on:
                        logger.debug('    new_allowed_sections: ' + str(new_allowed_sections) + str(type(new_allowed_sections)))

                # - convert keys (these are strings) to integer, convert to json
                    tobesaved_dict = {}
                    if new_allowed_sections:
                        for schoolbase_pk_str, schoolbase_dict in new_allowed_sections.items():
                            tobesaved_schoolbase_dict = {}
                            if schoolbase_dict:
                                if logging_on:
                                    logger.debug('    schoolbase_dict: ' + str(schoolbase_dict) + str(type(schoolbase_dict)))
                                for depbase_pk_str, depbase_dict in schoolbase_dict.items():
                                    tobesaved_depbase_dict = {}
                                    if depbase_dict:
                                        if logging_on:
                                            logger.debug('    depbase_dict: ' + str(depbase_dict) + str(type(depbase_dict)))

                                        for lvlbase_pk_str, lvlbase_arr in depbase_dict.items():
                                            tobesaved_lvlbase_arr = []
                                            if logging_on:
                                                logger.debug('    lvlbase_arr: ' + str(lvlbase_arr) + str(type(lvlbase_arr)))

                                            if lvlbase_arr:
                                                for subjbase_pk_str in lvlbase_arr:
                                                    tobesaved_lvlbase_arr.append(int(subjbase_pk_str))

                                            tobesaved_depbase_dict[int(lvlbase_pk_str)] = tobesaved_lvlbase_arr

                                    tobesaved_schoolbase_dict[int(depbase_pk_str)] = tobesaved_depbase_dict

                            tobesaved_dict[int(schoolbase_pk_str)] = tobesaved_schoolbase_dict

                    new_allowed_sections_str = json.dumps(tobesaved_dict) if tobesaved_dict else None

                    if logging_on:
                        logger.debug('    tobesaved_dict: ' + str(tobesaved_dict))
                        logger.debug('    new_allowed_sections_str: ' + str(new_allowed_sections_str))

                    setattr(userallowed_instance, 'allowed_sections', new_allowed_sections_str)
                    userallowed_instance.save(request=request)

                allowed_sections_dict = {}
                if userallowed_instance and userallowed_instance.allowed_sections:
                    allowed_sections_dict = json.loads(userallowed_instance.allowed_sections)
                update_wrap['allowed_sections'] = allowed_sections_dict

        # - create_user_rows returns list of only 1 user
                updated_instance_list = create_user_rowsNEW(sel_examyear, request, user_instance.pk)
                updated_dict = updated_instance_list[0] if updated_instance_list else {}
                #updated_dict['updated'] = True
                if updated_dict:
                    update_wrap['updated_user_rows'] = [updated_dict]

        if msg_list:
            msg_html = '<br>'.join(msg_list)
            update_wrap['msg_html'] = msg_html
        if logging_on:
            logger.debug('    update_wrap: ' + str(update_wrap))

        # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UserAllowedSectionsUploadView



########################################################################
# === UserDownloadUserdataXlsxView ===================================== PR2023-01-31

@method_decorator([login_required], name='dispatch')
class UserdataDownloadXlsxView(View):  # PR2023-01-31

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= UserdataDownloadXlsxView ============= ')
        # function xlsx file with student data
        response = None

        def get_mapped_depcodes():
            mapped_depcodes = {-9: str(_('all'))}
            sql = "SELECT id, code FROM schools_departmentbase"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                for row in cursor.fetchall():
                    mapped_depcodes[row[0]] = row[1]
            return mapped_depcodes

        def get_mapped_lvlcodes():
            mapped_lvlcodes = {-9: str(_('all'))}
            sql = "SELECT id, code FROM subjects_levelbase"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                for row in cursor.fetchall():
                    mapped_lvlcodes[row[0]] = row[1]
            return mapped_lvlcodes

        def get_mapped_schoolcodes():
            mapped_schoolcodes = {-9: str(_('all'))}
            sql = "SELECT id, code FROM schools_schoolbase"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                for row in cursor.fetchall():
                    mapped_schoolcodes[row[0]] = row[1]
            return mapped_schoolcodes

        def get_mapped_subjectcodes():
            mapped_subjectcodes = {-9: str(_('all'))}
            sql = "SELECT id, code FROM subjects_subjectbase"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                for row in cursor.fetchall():
                    mapped_subjectcodes[row[0]] = row[1]
            return mapped_subjectcodes

        #try:
        if True:
            if request.user and request.user.country and request.user.schoolbase:
                req_usr = request.user

    # - reset language
                user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
                activate(user_lang)

    # - get selected examyear, school and department from usersettings
                sel_examyear = acc_prm.get_sel_examyear_from_requsr(request)

                req_usr_school = sch_mod.School.objects.get_or_none(
                    base=req_usr.schoolbase_id,
                    examyear=sel_examyear
                )
                if logging_on:
                    logger.debug('    sel_examyear: ' + str(sel_examyear))

                if sel_examyear :
                    req_usr_school = sch_mod.School.objects.get_or_none(
                        base=req_usr.schoolbase_id,
                        examyear=sel_examyear
                    )

                    # --- create rows of all users of this examyear / school  / department PR2020-10-27 PR2022-01-03 PR2022-05-18 PR2023-01-30
                    user_rows = create_user_rowsNEW(sel_examyear, request)
                    mapped_depcodes = get_mapped_depcodes()
                    mapped_lvlcodes = get_mapped_lvlcodes()
                    mapped_schoolcodes = get_mapped_schoolcodes()
                    mapped_subjectcodes = get_mapped_subjectcodes()

                    response = awpr_excel.create_userdata_xlsx(sel_examyear, req_usr_school, req_usr.role, mapped_depcodes, mapped_lvlcodes, mapped_schoolcodes, mapped_subjectcodes, user_rows, user_lang)

                    if logging_on:
                        logger.debug('    response: ' + str(response))

        #except Exception as e:
        #    logger.error(getattr(e, 'message', str(e)))

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of UserdataDownloadXlsxView


########################################################################
# === UserDownloadPermitsView ===================================== PR2021-04-20

@method_decorator([login_required], name='dispatch')
class UserDownloadPermitsView(View):
    #  UserDownloadPermitsView is called from Users form
    #  it returns a HttpResponse, with all permits
    def get(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('  ')
            logger.debug(' ========== UserDownloadPermitsView ===============')

        response = None
        if request.user is not None and request.user.country is not None:
            req_usr = request.user
            # PR2021-05-25 debug. Don't use permit_list, to prevent locking out yourself
            permit_listNIU, requsr_usergroups_list,  requsr_allowed_sections_dictNIU, requsr_allowed_clusters_arr = acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, 'page_user')
            has_permit = request.user.is_role_system and  'admin' in requsr_usergroups_list
            if logging_on:
                logger.debug('requsr_usergroups_list: ' + str(requsr_usergroups_list))
                logger.debug('has_permit: ' + str(has_permit))

            if has_permit:
                # - reset language
                # PR2019-03-15 Debug: language gets lost, get req_usr.lang again
                user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
                activate(user_lang)

                permits_rows = create_permits_rows()
                response = create_permits_xlsx(permits_rows, user_lang, request)

        if response:
            return response
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# - end of UserDownloadPermitsView


def create_permits_rows():
    # --- create list of permits_rows of this country PR2021-04-20
    # PR2021-08-22 country isremoved, permits are for CUR and SXM
    # was: sql_keys = {'country_id': request.user.country.pk}
    sql = ' '.join(("SELECT p.page, p.action, p.role, p.usergroups",
                    "FROM accounts_userpermit AS p",
                    # was: "INNER JOIN schools_country AS c ON (c.id = p.country_id)",
                    # was: "WHERE c.id = %(country_id)s::INT",
                    'ORDER BY p.page, p.action, p.role'))

    with connection.cursor() as cursor:
        cursor.execute(sql)
        permits_rows = af.dictfetchall(cursor)

    return permits_rows
# --- end of create_permits_rows


def create_permits_xlsx(permits_rows, user_lang, request):  # PR2021-04-20
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_permits_xlsx -----')

    # from https://stackoverflow.com/questions/16393242/xlsxwriter-object-save-as-http-response-to-create-download-in-django
    #logger.debug('period_dict: ' + str(period_dict))

# ---  create file Name and worksheet Name

    today_dte = af.get_today_dateobj()
    today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

    title = str(_('Permissions'))
    file_name = title + " " + today_dte.isoformat() + ".xlsx"
    worksheet_name = str(_('Permissions'))

# create the HttpResponse object ...
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = "attachment; filename=" + file_name

    field_names = ('page', 'action', 'usergroups', 'role')

    field_width = (20, 25, 40, 10, 10)

# .. and pass it into the XLSXWriter
    book = xlsxwriter.Workbook(response, {'in_memory': True})
    sheet = book.add_worksheet(worksheet_name)

    tblHead_format = book.add_format({'bold': True})
    tblHead_format.set_bottom()
    tblHead_format.set_bg_color('#d8d8d8') #   #d8d8d8;  /* light grey 218 218 218 100%

    for i, width in enumerate(field_width):
        sheet.set_column(i, i, width)

    row_index = 0
    for i, caption in enumerate(field_names):
        sheet.write(row_index, i, caption, tblHead_format)

    rows_length = len(permits_rows)
    if rows_length:
        for row in permits_rows:
            row_index += 1
            for i, field_name in enumerate(field_names):
                value = row.get(field_name)
                if value is not None:
                    sheet.write(row_index, i, value)

    book.close()
    return response

# --- end of create_permits_xlsx

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@



########################################################################
# === UserpermitUploadView ===================================== PR2021-03-18 PR2023-01-15
@method_decorator([login_required], name='dispatch')
class UserpermitUploadView(View):
    #  UserpermitUploadView is called from Users form
    #  it returns a HttpResponse, with ok_msg or err-msg

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ')
            logger.debug(' ========== UserpermitUploadView ===============')

        update_wrap = {}
# -  get permit -- don't use requsr_usergroups_list, you might lock yourself out PR2021-05-20
        if request.user is not None and request.user.country is not None:
            req_usr = request.user
            has_permit = (req_usr.role == c.ROLE_128_SYSTEM)

            if has_permit:
# -  get user_lang
                user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get upload_dict from request.POST
                upload_json = request.POST.get("upload")
                if upload_json:
                    upload_dict = json.loads(upload_json)
                    if logging_on:
                        logger.debug('upload_dict:     ' + str(upload_dict))

# - get selected mode. Modes are  'create"  'update' 'delete'
                    mode = upload_dict.get('mode')
                    userpermit_pk = upload_dict.get('userpermit_pk')

                    role = upload_dict.get('role')
                    page = upload_dict.get('page')
                    action = upload_dict.get('action')

                    if logging_on:
                        logger.debug('    mode:     ' + str(mode))
                        logger.debug('    role:     ' + str(role) + ' ' + str(type(role)))
                        logger.debug('    page:     ' + str(page))
                        logger.debug('    action:   ' + str(action))
                        logger.debug('    userpermit_pk:   ' + str(userpermit_pk))

                    append_dict = {}
                    error_dict = {}
                    updated_permit_rows = []

# +++  get current permit - when mode is 'create': permit is None. It will be created at "elif mode == 'create'"
                    userpermit_instance = acc_mod.Userpermit.objects.get_or_none(
                        pk=userpermit_pk
                    )
                    if logging_on:
                        logger.debug('    userpermit_instance: ' + str(userpermit_instance))

# +++  delete permit ++++++++++++
                    if mode == 'delete':
                        if userpermit_instance:
                            try:
                                userpermit_instance.delete(request=request)
                                # - add deleted_row to updated_permit_rows
                                updated_permit_rows.append({'userpermit_pk': userpermit_pk,
                                                  'mapid': 'userpermit_' + str(userpermit_pk),
                                                  'deleted': True})
                                if logging_on:
                                    logger.debug('userpermit_instance: ' + str(userpermit_instance))

                            except Exception as e:
                                logger.error(getattr(e, 'message', str(e)))
                                append_dict['err_delete'] = getattr(e, 'message', str(e))

# ++++  create new permit ++++++++++++
                    elif mode == 'create':
                        if page and action:
                            try:
                                if role is None:
                                    role_list = (c.ROLE_008_SCHOOL, c.ROLE_016_CORR, c.ROLE_032_INSP, c.ROLE_064_ADMIN, c.ROLE_128_SYSTEM)
                                else:
                                    role_list = (role,)

                                for value in role_list:
                                    userpermit_instance = acc_mod.Userpermit(
                                        role=value,
                                        page=page,
                                        action=action
                                    )
                                    userpermit_instance.save()
                            except Exception as e:
                                logger.error(getattr(e, 'message', str(e)))

                                append_dict['err_create'] = getattr(e, 'message', str(e))
                            finally:
                                append_dict['created'] = True

# +++ update existing userpermit - also when userpermit is created - userpermit is None when deleted
                    if userpermit_instance and mode in ('create', 'update'):
                        sel_examyear = get_selected_examyear_from_usersetting_short(request)
                    if logging_on :
                        logger.debug('    sel_examyear: ' + str(sel_examyear))

                        update_grouppermit(userpermit_instance, upload_dict, error_dict, request)
                    if logging_on :
                        logger.debug('    error_dict: ' + str(error_dict))

# - add update_dict to update_wrap
                    if userpermit_instance:
                        if error_dict:
                            append_dict['error'] = error_dict

               # - add update_dict to update_wrap
                        if userpermit_instance.pk:
                            permit_row = create_permit_list(userpermit_instance.pk)
                            if permit_row:
                                updated_permit_rows.append(permit_row)

                    update_wrap['updated_permit_rows'] = updated_permit_rows

# F. return update_wrap
            return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UserpermitUploadView


def update_grouppermit(userpermit_instance, upload_dict, msg_dict, request): # PR2021-03-20 PR2023-01-15
    # --- update existing and new userpermit_instance
    # add new values to update_dict (don't reset update_dict, it has values)
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_grouppermit -------')
        logger.debug('    upload_dict' + str(upload_dict))

    save_changes = False
    for field, new_value in upload_dict.items():
        if field in ['role', 'page', 'action']:
            saved_value = getattr(userpermit_instance, field)
            if logging_on:
                logger.debug('    field:       ' + str(field))
                logger.debug('    saved_value: ' + str(saved_value) + str(type(saved_value)))
                logger.debug('    new_value:   ' + str(new_value) + str(type(new_value)))

            if new_value and new_value != saved_value:
                setattr(userpermit_instance, field, new_value)
                save_changes = True

        elif field == 'usergroups':
            saved_usergroups_str = getattr(userpermit_instance, field)
            if logging_on:
                logger.debug('    saved_usergroups_str: ' + str(saved_usergroups_str))

            if new_value:
                save_usergroups_changes = False

                usergroups_list = saved_usergroups_str.split(';') if saved_usergroups_str else []
                if logging_on:
                    logger.debug('    usergroups_list: ' + str(usergroups_list))

                for usergroup, value in new_value.items():
                    if logging_on:
                        logger.debug('    usergroup: ' + str(usergroup))
                        logger.debug('    value: ' + str(value))
                    if value:
                        if usergroup not in usergroups_list:
                            usergroups_list.append(usergroup)
                            save_usergroups_changes = True
                    else:
                        if usergroup in usergroups_list:
                            usergroups_list.remove(usergroup)
                            save_usergroups_changes = True



                if save_usergroups_changes:
                    if usergroups_list:
                        usergroups_list.sort()
                    if logging_on:
                        logger.debug('    usergroups_list: ' + str(usergroups_list))
                        usergroups_str = ';'.join(usergroups_list)
                        setattr(userpermit_instance, field, usergroups_str)
                    else:
                        setattr(userpermit_instance, field, None)
                    save_changes = True

    # - save changes`
    if logging_on:
        logger.debug('save_changes' + str(save_changes) + str(type(save_changes)))

    if save_changes:
        try:
            userpermit_instance.save(request=request)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            msg_dict['err_update'] = getattr(e, 'message', str(e))
            #msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')

    if logging_on:
        logger.debug('msg_dict' + str(msg_dict) + str(type(msg_dict)))
# --- end of update_grouppermit


@method_decorator([login_required], name='dispatch')
class UserSettingsUploadView(UpdateView):  # PR2019-10-09

    def post(self, request, *args, **kwargs):
        logging_on = False  # s.LOGGING_ON

        update_wrap = {}
        if request.user is not None and request.user.country is not None:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload')
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug(' ============= UserSettingsUploadView ============= ')
                    logger.debug('     upload_dict: ' + str(upload_dict))

                set_usersetting_from_uploaddict(upload_dict, request)

# - add update_dict to update_wrap
                update_wrap['setting'] = {'result': 'ok'}
# F. return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))

###########################################

@method_decorator([login_required], name='dispatch')
class UserLanguageView(View):

    def get(self, request, lang):
        #logger.debug('UserLanguageView get self: ' + str(self) + 'request: ' + str(request) + ' lang: ' + str(lang))
        if request.user is not None :
            #logger.debug('UserLanguageView get request.user: ' + str(request.user))
            request.user.lang = lang
            #logger.debug('UserLanguageView get request.user.language: ' + str(request.user.lang))
            request.user.save(self.request)
            #logger.debug('UserLanguageView get saved.language: ' + str(request.user.lang))
        return redirect('home_url')


# PR2018-04-24
def account_activation_sent(request):
    #logger.debug('account_activation_sent request: ' + str(request))
    # PR2018-05-27
    # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
    return render(request, 'account_activation_sent.html')

# Create Advanced User Sign Up View in Django | Step-by-Step  PR2020-03-29
# from https://dev.to/coderasha/create-advanced-user-sign-up-view-in-django-step-by-step-k9m
# from https://simpleisbetterthancomplex.com/tutorial/2017/02/18/how-to-create-user-sign-up-view.html

# === SignupActivateView ===================================== PR2020-09-29
def SignupActivateView(request, uidb64, token):
    logging_on = True  # s.LOGGING_ON
    if logging_on:
        logger.debug('  === SignupActivateView =====')

    # SignupActivateView is called when user clicks on link 'Activate your AWP-online account'
    # it returns the page 'signup_setpassword'
    # when error: it sends err_msg to this page

    update_wrap = {}
    activation_token_ok = False
    newuser_activated = False

# - get user
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get_or_none(pk=uid)
    except (TypeError, ValueError, OverflowError) as e:
        logger.error(getattr(e, 'message', str(e)))
        user = None

    if logging_on:
        logger.debug('     user:             ' + str(user))
        if user:
            logger.debug('     is_authenticated: ' + str(user.is_authenticated))
            logger.debug('     activated:        ' + str(user.activated))

# - get language from user
    # PR2019-03-15 Debug: language gets lost, get request.user.lang again
    user_lang = user.lang if user and user.lang else c.LANG_DEFAULT
    activate(user_lang)

    if user is None:
        update_wrap['msg_01'] = _('Sorry, we could not find your account.')
        update_wrap['msg_02'] = _('Your account cannot be activated.')
    else:
        user_name = user.username_sliced
        update_wrap['username'] = user_name
        update_wrap['schoolcode'] = user.schoolbase.code
        update_wrap['user_lastname'] = user.last_name

# - get schoolname PR2020-12-24
        examyear = af.get_todays_examyear_or_latest_instance(user.country)
        #logger.debug('examyear: ' + str(examyear))
        school = sch_mod.School.objects.get_or_none( base=user.schoolbase, examyear=examyear)
        #logger.debug('school: ' + str(school))
        usr_schoolname_with_article = '---'
        if school and school.name:
            if school.article:
                usr_schoolname_with_article = school.article + ' ' + school.name
            else:
                usr_schoolname_with_article = school.name
        elif user.schoolbase and user.schoolbase.code:
            usr_schoolname_with_article = user.schoolbase.code
        # PR2021-01-20 this one does not translate to Dutch, because language is not set. Text moved to template
        # msg_txt = _("Your account with username '%(usr)s' is created at %(school)s.") % {'usr': user_name, 'school': usr_schoolname_with_article}
        # update_wrap['schoolnamewithArticle'] = msg_txt
        #logger.debug('usr_schoolname_with_article: ' + str(usr_schoolname_with_article))
        update_wrap['schoolnamewithArticle'] = usr_schoolname_with_article

# - check activation_token
        activation_token_ok = account_activation_token.check_token(user, token)

        if logging_on:
            logger.debug('activation_token_ok: ' + str(activation_token_ok))

        if not activation_token_ok:
            update_wrap['msg_01'] = _('The link to active your account is no longer valid.')
            update_wrap['msg_02'] = _('Maybe it has expired or has been used already.')
            update_wrap['msg_03'] = _('The link expires after 7 days.')

    # don't activate user and company until user has submitted valid password
    update_wrap['activation_token_ok'] = activation_token_ok

    if request.method == 'POST':
        if logging_on and False:
            logger.debug('request.POST' + str(request.POST))

        form = SetPasswordForm(user, request.POST)

        form_is_valid = form.is_valid()

        non_field_errors = af.get_dict_value(form, ('non_field_errors',))
        field_errors = [(field.label, field.errors) for field in form]

        if logging_on:
            logger.debug('     non_field_errors: ' + str(non_field_errors))
            logger.debug('     field_errors:   ' + str(field_errors))
            logger.debug('     form_is_valid:  ' + str(form_is_valid))

        if form_is_valid:
            user = form.save()
            update_session_auth_hash(request, user)  # Important!

            # request has no user, add user to request
            request.user = user
            # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
            datetime_activated = timezone.now()

# - activate user, after he has submitted valid password
            user.is_active = True
            user.activated = True
            user.activatedat = datetime_activated
            user.save()
            newuser_activated = user.activated
            if logging_on:
                logger.debug('     newuser_activated: ' + str(newuser_activated))

            login(request, user)

        else:
            update_wrap['form'] = form

            if logging_on:
                logger.debug('     form: ' + str(form))

    else:
        form = SetPasswordForm(user)
        update_wrap['form'] = form

    update_wrap['newuser_activated'] = newuser_activated
    # PR2021-02-05 debug: when a new user tries to activat his account
    #                     and a different user is already logged in in the same browser,
    #                     in form value user.activated = True and passwoord form does not show.
    #                     use variable 'newuser_activated' and add this error trap to form:
    #                     {% elif user.is_authenticated and user.activated and not newuser_activated %}
    #                     instead of  {% elif user.is_authenticated %}

    # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.

    if logging_on:
        logger.debug('update_wrap: ' + str(update_wrap))

    return render(request, 'signup_setpassword.html', update_wrap)
# === end of SignupActivateView =====================================



# PR2018-04-24

@method_decorator([login_required], name='dispatch')
class UserActivateView(UpdateView):
    model = User
    form_class = UserActivateForm
    template_name = 'user_edit.html'  # without template_name Django searches for user_form.html
    pk_url_kwarg = 'pk'
    context_object_name = 'UserActivateForm'  # "context_object_name" changes the original parameter name "object_list"

    def activate(request, uidb64, token):
        #logger.debug('UserActivateView def activate request: ' +  str(request))

        #try:
        uid = force_text(urlsafe_base64_decode(uidb64))

        user = User.objects.get(pk=uid)
        #logger.debug('UserActivateView def activate user: ' + str(user))

        #except:  #except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        #    logger.debug('def activate except TypeError: ' + str(TypeError))
        #    logger.debug('def activate except ValueError: ' + str(ValueError))
        #    logger.debug('def activate except OverflowError: ' + str(OverflowError))
        #    logger.debug('def activate except User.DoesNotExist: ' + str(User.DoesNotExist))
        #    user = None

        #logger.debug('UserActivateView def activate token: ' + str(token))

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.activated = True
            user.save()
            #logger.debug('UserActivateView def activate user.saved: ' + str(user))
            # login(request, user)
            # logger.debug('UserActivateView def activate user.loggedin: ' + str(user))

            # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
            #return render(request, 'account_activation_success.html', {'user': user,})
            return render(request, 'user_set_password.html', {'user': user,})

            # select_school = False
            display_school = True
            if request.user is not None:
                if request.user.is_authenticated:
                    if request.user.is_role_school_group_systemtem:
                        display_school = True

            param = {'display_school': display_school, 'display_user': True, }
            headerbar_param = awpr_menu.get_headerbar_param(request, 'schools', param)
            headerbar_param['form'] = form
            #logger.debug('def home(request) headerbar_param: ' + str(headerbar_param))

            return render(request, 'user_add.html', headerbar_param)

        else:
            #logger.debug('def activate account_activation_token.check_token False')
            return render(request, 'account_activation_invalid.html')


# PR2018-04-24
def UserActivate(request, uidb64, token):
    #logger.debug('UserActivate def activate request: ' + str(request))

    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        #logger.debug('def activate try uid: ' + str(uid))
        user = User.objects.get(pk=uid)
        #logger.debug('UserActivate def activate try user: ' + str(user))

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        # logger.debug('UserActivate def activate except TypeError: ' + str(TypeError))
        # logger.debug('UserActivate def activate except ValueError: ' + str(ValueError))
        # logger.debug('UserActivate def activate except OverflowError: ' + str(OverflowError))
        # logger.debug('UserActivate def activate except User.DoesNotExist: ' + str(User.DoesNotExist))
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.activated = True
        # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
        user.activated_at = timezone.now()
        user.save()
        #logger.debug('UserActivate def activate user.saved: ' + str(user))

        # open setpassword form

        # login(request, user)
        #logger.debug('UserActivate def activate user.loggedin: ' + str(user))



        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'account_activation_success.html')
        # return render(request, 'password_change.html', {'user': user,})
        # return render(request, 'user_set_password.html', {'user': user,})
        # return render(request, 'password_reset_confirm.html', {'user': user,})

    else:
        #logger.debug('def activate account_activation_token.check_token False')
        return render(request, 'account_activation_invalid.html')


# === send_activation_email ===================================== PR2020-08-15
def send_activation_email(user_pk, update_wrap, err_dict, request):
    #  send_activation_email is called from table Users, field 'activated' when the activation link has expired.
    #  it sends an email to the user
    #  it returns a HttpResponse, with ok_msg or err-msg
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  ')
        logger.debug(' ========== send_activation_email ===============')

    user = acc_mod.User.objects.get_or_none(id=user_pk, country= request.user.country)
    if logging_on:
        logger.debug('user: ' + str(user))

    has_error = False
    if user:
        req_usr = request.user.last_name
        req_school = get_usr_schoolname_with_article(request.user)

        update_wrap['user'] = {'pk': user.pk, 'username': user.username}

        current_site = get_current_site(request)

# - check if user.email is a valid email address:
        msg_err = awpr_val.validate_email_address(user.email)
        if msg_err:
            err_dict['msg01'] = _("'%(email)s' is not a valid email address.") % {'email': user.email}
            has_error = True

# -  send email 'Activate your account'
        if not has_error:
            try:
                subject = 'Activate your AWP-online account'
                from_email = 'AWP-online <noreply@awponline.net>'
                message = render_to_string('signup_activation_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    # PR2018-04-24 debug: In Django 2.0 you should call decode() after base64 encoding the uid, to convert it to a string:
                    # 'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    # PR2021-03-24 debug. Gave error: 'str' object has no attribute 'decode'
                    # apparently force_bytes(user.pk) returns already a string, no need for decode() any more
                    # from https://stackoverflow.com/questions/28583565/str-object-has-no-attribute-decode-python-3-error
                    # was: 'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                    'req_school': req_school,
                    'req_usr': req_usr,
                })
                if logging_on:
                    logger.debug('user: ' + str(user))
                    logger.debug('current_site.domain: ' + str(current_site.domain))
                    logger.debug('urlsafe_base64_encode(force_bytes(user.pk)): ' + str(urlsafe_base64_encode(force_bytes(user.pk))))
                    logger.debug('account_activation_token.make_token(user): ' + str(account_activation_token.make_token(user)))
                    logger.debug('req_usr: ' + str(req_usr))

                # PR2018-04-25 arguments: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
                mail_count = send_mail(subject, message, from_email, [user.email], fail_silently=False)
                if logging_on:
                    logger.debug('mail_count: ' + str(mail_count))

                """
                PR2022-02-14 after installing HP pc send_mail suddenly gives error, also on laptop. Testsite and production site are still working OK.
                    Invalid '/' in sender domain 'https://api.mailgun.net/v3/mg.awponline.net'
                from https://github.com/anymail/django-anymail/issues/144
                    The most likely cause is that you've either set MAILGUN_SENDER_DOMAIN to something invalid, or that the From address has an invalid domain name.
                    In particular / slash characters can't be used in domain names. Here's an example of an incorrect setting that will cause this problem:
                    ANYMAIL = { "MAILGUN_SENDER_DOMAIN": "mail.example.com/myapp",  # NOT VALID
                changing MAILGUN_SENDER_DOMAIN from 'https://api.mailgun.net/v3/mg.awponline.net' to 'mg.awponline.net'
                    IT WORKS!
                """

                if not mail_count:
                    err_dict['msg01'] = _('An error occurred.')
                    err_dict['msg02'] = _('The activation email has not been sent.')
                else:
                # - return message 'We have sent an email to user'
                    msg01 = _("We have sent an email to the email address '%(email)s' of user '%(usr)s'.") % \
                                                    {'email': user.email, 'usr': user.username_sliced}
                    msg02 = _('The user must click the link in that email to verify the email address and create a password.')

                    update_wrap['msg_ok'] = {'msg01': msg01, 'msg02': msg02}

            except:
                err_dict['msg01'] = _('An error occurred.')
                err_dict['msg02'] = _('The activation email has not been sent.')

# - reset expiration date by setting the field 'date_joined', to now
        if not has_error:
            # PR2021-01-01 was:
            # now_utc_naive = datetime.utcnow()
            # now_utc = now_utc_naive.replace(tzinfo=pytz.utc)
            # user.date_joined = now_utc

            now_utc = timezone.now()
            user.date_joined = now_utc  # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
            user.modifiedby = request.user
            user.modifiedat = now_utc

            user.save()
# === end of send_activation_email =====================================

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

class AwpPasswordResetForm(forms.Form):

    #logger.debug(' ============= AwpPasswordResetForm ============= ')

    schoolcode = forms.CharField(
        required=True,
        label="Schoolcode",
        widget=forms.TextInput(attrs={'autofocus': True})
    )

    email = forms.EmailField(
        label="E-mail adres",
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        #logger.debug(' ----- send_mail -----')
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        email_sent = email_message.send()
        logger.debug('     email_sent: ' + str(email_sent))


    def get_users(self, schoolbase_id, email):
        #logger.debug(' ----- get_users -----')
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        email_field_name = UserModel.get_email_field_name()

        #active_users = UserModel._default_manager.filter(**{
        #    '%s__iexact' % email_field_name: email,
       #     'schoolbase_id': schoolbase_id,
        #    'is_active': True,
       # })
        active_users = acc_mod.User.objects.filter(
            email=email,
            schoolbase_id=schoolbase_id,
            is_active=True
        )

        #logger.debug('schoolbase_id: ' + str(schoolbase_id))
        #logger.debug('email_field_name: ' + str(email_field_name))
        #logger.debug('active_users: ' + str(active_users))
        #if active_users:
        #    for usr in active_users:
                #logger.debug('usr: ' + str(usr))

        return (
            u for u in active_users
            if u.has_usable_password() and
            _unicode_ci_compare(email, getattr(u, email_field_name))
        )

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        logger.debug(' ----- new password request -----')

        now = datetime.now()
        logger.debug('     date: ' + str(now.strftime("%Y-%m-%d %H:%M:%S")))

        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        schoolcode = self.cleaned_data["schoolcode"]
        schoolbase_id = None
        if schoolcode:
            schoolbase = sch_mod.Schoolbase.objects.get_or_none(
                code__iexact=schoolcode
            )
            if schoolbase:
                schoolbase_id = schoolbase.pk
        logger.debug('     schoolcode: ' + str(schoolcode))

        email = self.cleaned_data["email"]
        logger.debug('     email: ' + str(email))

        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        email_field_name = UserModel.get_email_field_name()

        #logger.debug('email_field_name: ' + str(email_field_name))

        for user in self.get_users(schoolbase_id, email):
            user_email = getattr(user, email_field_name)

            logger.debug('     username:  ' + str(getattr(user, 'username')))
            logger.debug('     user_email: ' + str(user_email))

            context = {
                'email': user_email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                **(extra_email_context or {}),
            }
            self.send_mail(
                subject_template_name, email_template_name, context, from_email,
                user_email, html_email_template_name=html_email_template_name,
            )
# === end of class AwpPasswordResetForm =====================================


class PasswordContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title,
            **(self.extra_context or {})
        })
        return context


class AwpPasswordResetView(PasswordContextMixin, FormView):
    #logger.debug(' ============= AwpPasswordResetView ============= ')

    email_template_name = 'registration/password_reset_email.html'
    extra_email_context = None
    form_class = AwpPasswordResetForm
    from_email = None
    html_email_template_name = None
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    template_name = 'registration/password_reset_form.html'
    title = 'Nieuw wachtwoord'
    token_generator = default_token_generator

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        form.save(**opts)

        return super().form_valid(form)

# === end of class AwpPasswordResetView =====================================

class AwpSetPasswordForm(forms.Form):
    #logger.debug(' ============= AwpSetPasswordForm ============= ')
    """
    A form that lets a user change set their password without entering the old
    password
    """
    error_messages = {
        'password_mismatch': 'Het nieuwe wachtwoord en de herhaling zijn niet hetzelfde.',
    }

    help_text_html = ''.join((
        "<ul><li>",
        "Het wachtwoord mag niet te veel lijken op je persoonsgegevens.", "</li><li>",
        "Het wachtwoord moet tenminste 8 tekens bevatten.","</li><li>",
        "Het wachtwoord mag geen veel gebruikt wachtwoord zijn.","</li><li>",
        "Het wachtwoord mag niet alleen uit cijfers bestaan.""</li></ul>",
    ))
    new_password1 = forms.CharField(
        label="Nieuw wachtwoord",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        #help_text=password_validation.password_validators_help_text_html(),
        help_text=help_text_html,
    )
    new_password2 = forms.CharField(
        label=_("Herhaling nieuw wachtwoord"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        password_validation.validate_password(password2, self.user)
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
# === end of class AwpSetPasswordForm =====================================


class AwpPasswordResetConfirmView(PasswordContextMixin, FormView):
    #logger.debug(' ============= AwpPasswordResetConfirmView ============= ')

    form_class = AwpSetPasswordForm
    post_reset_login = False
    post_reset_login_backend = None
    reset_url_token = 'set-password'
    success_url = reverse_lazy('password_reset_complete')
    template_name = 'registration/password_reset_confirm.html'
    title = _('Nieuw wachtwoord aanmaken')
    token_generator = default_token_generator

    activate(c.LANG_DEFAULT)

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        assert 'uidb64' in kwargs and 'token' in kwargs

        self.validlink = False
        self.user = self.get_user(kwargs['uidb64'])

        # PR2022-05-01 debug. User can change password and login when account is not activated
        # add 'and self.user.activated' to if clause

        if self.user is not None:
            if not self.user.activated:
                logger.debug('     user.activated: ' + str(self.user.activated))
                # PR2022-05-01 debug. User can change password and login when account is not activated
                # add 'and self.user.activated' to if clause

                response = render_to_string('password_reset_notactivated.html')
                return HttpResponse(response)

            else:
                token = kwargs['token']
                if token == self.reset_url_token:
                    session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)
                    if self.token_generator.check_token(self.user, session_token):
                        # If the token is valid, display the password reset form.
                        self.validlink = True
                        return super().dispatch(*args, **kwargs)
                else:
                    if self.token_generator.check_token(self.user, token):
                        # Store the token in the session and redirect to the
                        # password reset form at a URL without the token. That
                        # avoids the possibility of leaking the token in the
                        # HTTP Referer header.
                        self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                        redirect_url = self.request.path.replace(token, self.reset_url_token)
                        return HttpResponseRedirect(redirect_url)

        logger.debug('     self.get_context_data(): ' + str(self.get_context_data()))
        # Display the "Password reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist, ValidationError):
            user = None
        return user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        del self.request.session[INTERNAL_RESET_SESSION_TOKEN]
        if self.post_reset_login:
            auth_login(self.request, user, self.post_reset_login_backend)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context['validlink'] = True
        else:
            context.update({
                'form': None,
                'title': _('Password reset unsuccessful'),
                'validlink': False,
            })
        return context
# === end of class AwpPasswordResetConfirmView =====================================

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

@method_decorator([login_required], name='dispatch')
class UserModMessageHideView(View):
    #  PR2022-05-29
    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ')
            logger.debug(' ========== UserModMessageHideView ===============')

        update_wrap = {}

        if request.user and request.user.country and request.user.schoolbase:
            set_usersetting_dict(c.KEY_OPENARGS, {'show_msg': False, 'hide_msg': True}, request)

        if logging_on:
            logger.debug(str(acc_prm.get_usersetting_dict(c.KEY_OPENARGS, request)))

# - return update_wrap
        update_wrap_json = json.dumps(update_wrap, cls=af.LazyEncoder)
        return HttpResponse(update_wrap_json)
# end of UserModMessageHideView


def create_user_rowsNEW(sel_examyear, request, user_pk=None, school_correctors_only=False):
    # PR2020-07-31 PR2022-12-02 PR2023-03-26
    # --- create list of all users of this school, or 1 user with user_pk
    # PR2022-12-02 added: join with userallowed, to retrieve only users of this examyear
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' =============== create_user_rowsNEW ============= ')
        logger.debug('    user_pk: ' + str(user_pk))
        logger.debug('    sel_examyear: ' + str(sel_examyear))
        logger.debug('    school_correctors_only: ' + str(school_correctors_only) + ' ' + str(type(school_correctors_only)))

    # <PERMIT> PR2020-10-12
    # PR2018-05-27 list of users in UserListView:
    # - only perm_system and perm_admin can create user_list
    # - role teacher, student have no access
    # - dont show users with higher role
    # - when role is inspection or school: show only users of request.user.schoolbase
    # - when user_pk has value the school of user_pk can be different from the school of request user (in case of admin(ETE) )

    def get_allowed_schoolbases(schoolbase_pk_arr):

        schoolbase_code_list = []
        schoolbase_name_list = []

        if schoolbase_pk_arr:
            try:
                # PR2023-03-26 'All schools' -9 is not in use (yet)
                # add 'All schools' when -9 in list
                if -9 in schoolbase_pk_arr:
                    schoolbase_pk_arr.remove(-9)
                #    is_sxm = sel_examyear.country.abbrev.lower() == 'sxm'
                #    code = 'SXM00' if is_sxm else 'CUR00'
                #    name = str(_('All schools'))
                #    code_name = ' '.join((code, name))

                #    schoolbase_code_list.append(code)
                #    schoolbase_name_list.append(code_name)

                sql_keys = {'ey_pk': sel_examyear.pk, 'sb_arr': schoolbase_pk_arr}
                sql = ' '.join(("SELECT sb.code, sch.name",
                                "FROM schools_school AS sch",
                                "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",
                                "WHERE sch.examyear_id = %(ey_pk)s::INT",
                                "AND sch.base_id IN (SELECT UNNEST(%(sb_arr)s::INT[]))",
                                "ORDER BY sb.code"
                                ))
                with connection.cursor() as cursor:
                    cursor.execute(sql, sql_keys)
                    for row in cursor.fetchall():
                        code = row[0] if row[0] else ''
                        name = row[1] if row[1] else ''
                        code_name = ' '.join((code, name))

                        if code and code not in schoolbase_code_list:
                            schoolbase_code_list.append(code)
                        if code_name and code_name not in schoolbase_name_list:
                            schoolbase_name_list.append(code_name)

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

        schoolbases_code = None
        schoolbases_name = None

        if schoolbase_code_list:
            schoolbases_code = ', '.join(schoolbase_code_list)
        if schoolbase_name_list:
            schoolbases_name = '\n'.join(schoolbase_name_list)

        return schoolbases_code, schoolbases_name

    def get_all_depbases_rows():
        all_depbases_rows = []
        try:
            all_depbases_rows.append({'base_id': -9, 'code': str(_('all'))})

            sql = ' '.join(("SELECT dep.base_id, db.code, dep.level_req",
                            "FROM schools_department AS dep",
                            "INNER JOIN schools_departmentbase AS db ON (db.id = dep.base_id)",
                            "WHERE dep.examyear_id = ", str(sel_examyear.pk), "::INT",
                            "ORDER BY dep.sequence"))
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = af.dictfetchall(cursor)

            if rows:
                all_depbases_rows.extend(rows)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

        return all_depbases_rows

    def get_allowed_depbases(depbase_pk_arr, all_depbases_rows):
        depbase_code_list = []
        has_level_req = False

        if all_depbases_rows and depbase_pk_arr:
            # loop through all_lvlbases_rows to display levels in right sequence
            for depbase_dict in all_depbases_rows:
                depbase_pk = depbase_dict.get('base_id')
                if depbase_pk and depbase_pk in depbase_pk_arr:
                    code = depbase_dict.get('code')
                    if code and code not in depbase_code_list:
                        depbase_code_list.append(code)

                    if depbase_dict.get('level_req') or False:
                        has_level_req = True

        depbases_code = None
        if depbase_code_list:
            depbases_code = ', '.join(depbase_code_list)

        return depbases_code, has_level_req

    def get_all_lvlbases_rows():
        all_lvlbases_rows = []
        try:
            all_lvlbases_rows.append({'base_id': -9, 'code': str(_('all'))})
            sql = ' '.join(("SELECT lvl.base_id, lb.code",
                            "FROM subjects_level AS lvl",
                            "INNER JOIN subjects_levelbase AS lb ON (lb.id = lvl.base_id)",
                            "WHERE lvl.examyear_id = ", str(sel_examyear.pk) , "::INT",
                            "ORDER BY lvl.sequence"))
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = af.dictfetchall(cursor)

            if rows:
                all_lvlbases_rows.extend(rows)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

        return all_lvlbases_rows

    def get_allowed_lvlbases(lvlbase_pk_arr, has_level_req, all_lvlbases_rows):
        lvlbase_code_list = []
        if all_lvlbases_rows and lvlbase_pk_arr and has_level_req:
            # loop through all_lvlbases_rows to display levels in right sequence
            for lvlbase_dict in all_lvlbases_rows:
                lvlbase_pk = lvlbase_dict.get('base_id')
                if logging_on:
                    logger.debug(' WWW   lvlbase_dict: ' + str(lvlbase_dict))
                    logger.debug('    lvlbase_pk: ' + str(lvlbase_pk))
                    logger.debug('    lvlbase_pk_arr: ' + str(lvlbase_pk_arr))
                if lvlbase_pk and lvlbase_pk in lvlbase_pk_arr:
                    code = lvlbase_dict.get('code')
                    if code and code not in lvlbase_code_list:
                        lvlbase_code_list.append(code)

        lvlbases_code = None
        if lvlbase_code_list:
            lvlbases_code = ', '.join(lvlbase_code_list)

        return lvlbases_code

    def get_all_subjbases_dict():
        all_subjbases_dict = {}
        try:
            sql = ' '.join(("SELECT subj.base_id, sb.code, subj.name_nl",
                            "FROM subjects_subject AS subj",
                            "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
                            "WHERE subj.examyear_id = ", str(sel_examyear.pk) , "::INT"
                            ))
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            if rows:
                for row in rows:
                    all_subjbases_dict[row[0]] = {'base_id': row[0], 'code': row[1], 'name_nl': row[2]}

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

        return all_subjbases_dict

    def get_allowed_subjbases(subjbase_pk_arr, all_subjbases_dict):
        subjbase_code_list = []
        subjbase_name_list = []

        if all_subjbases_dict and subjbase_pk_arr:
            # subjects are sorted in this function.Therefore no need to loop through all_subjbases_rows
            # instead: lookup subjbase_pk in all_subjbases_dict
            for subjbase_pk in subjbase_pk_arr:
                if subjbase_pk in all_subjbases_dict:
                    subjbase_dict = all_subjbases_dict.get(subjbase_pk)
                    if subjbase_dict:
                        code = subjbase_dict.get('code') or '-'
                        if code not in subjbase_code_list:
                            subjbase_code_list.append(code)

                        name_nl = subjbase_dict.get('name_nl') or '-'
                        if name_nl not in subjbase_name_list:
                            subjbase_name_list.append(name_nl)

        if subjbase_code_list:
            subjbase_code_list.sort(key=lambda v: v.lower())

        subjbases_code = None
        if subjbase_code_list:
            subjbases_code = ', '.join(subjbase_code_list)

        subjbases_name = None
        if subjbase_name_list:
            subjbases_name = '\n'.join(subjbase_name_list)

        return subjbases_code, subjbases_name

    def get_all_clusters_dict():
        all_clusters_dict = {}
        try:
            sql = ' '.join(("SELECT cl.id, cl.name",
                            "FROM subjects_cluster AS cl",
                            "INNER JOIN schools_school AS sch ON (sch.id = cl.school_id)",
                            "WHERE sch.examyear_id = ", str(sel_examyear.pk) , "::INT"
                            ))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            if rows:
                for row in rows:
                    all_clusters_dict[row[0]] = row[1] if row[1] else '-'

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

        return all_clusters_dict

    def get_allowed_clusters(cluster_pk_arr, all_clusters_dict):
        cluster_pk_list = []
        cluster_name_list = []
        if all_clusters_dict and cluster_pk_arr:
            for cluster_pk in cluster_pk_arr:
                if cluster_pk and cluster_pk in all_clusters_dict:
                    if cluster_pk not in cluster_pk_list:
                        cluster_pk_list.append(cluster_pk)

                    cluster_name = all_clusters_dict.get(cluster_pk)
                    if cluster_name and cluster_name not in cluster_name_list:
                        cluster_name_list.append(cluster_name)

        if cluster_name_list:
            cluster_name_list.sort(key=lambda v: v.lower())

        return cluster_pk_list, cluster_name_list

###############

    user_list = []
    if request.user.country and sel_examyear:

        all_depbases_rows = get_all_depbases_rows()
        all_lvlbases_rows = get_all_lvlbases_rows()
        all_subjbases_dict = get_all_subjbases_dict()
        all_clusters_dict = get_all_clusters_dict()

        try:

            sql_moduser = "SELECT mod_au.id, SUBSTRING(mod_au.username, 7) AS modby_username FROM accounts_user AS mod_au"
            sql_list = ["WITH mod_user AS (", sql_moduser, ")",
                "SELECT u.id, u.schoolbase_id,",
                "CONCAT('user_', u.id) AS mapid, 'user' AS table,",
                "SUBSTRING(u.username, 7) AS username,",
                "u.last_name, u.email, u.role,",

                "u.activated, u.activated_at, u.is_active, u.last_login, u.date_joined,",
                "u.country_id, c.abbrev AS c_abbrev, sb.code AS sb_code, u.schoolbase_id,",

                "ual.usergroups AS ual_usergroups, ual.allowed_sections, ual.allowed_clusters, ual.examyear_id, ual.id AS ual_id, "
                "u.lang, u.modified_at AS modifiedat, mod_user.modby_username",

                "FROM accounts_user AS u",
                "INNER JOIN accounts_userallowed AS ual ON (ual.user_id = u.id)",
                "INNER JOIN schools_country AS c ON (c.id = u.country_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = u.schoolbase_id)",

                "LEFT JOIN mod_user ON (mod_user.id = u.modified_by_id)",

                ''.join(("WHERE ual.examyear_id=", str(sel_examyear.pk), "::INT"))
                ]

            if user_pk:
                sql_list.append(''.join(("AND u.id=", str(user_pk), "::INT")))

            else:
                if school_correctors_only:
                    # PR2023-03-26 when page correctors is called by school,
                    # only the users from role=correctors and usergroup = auth4 are retrieved
                    # and then filtered by allowed school

                    sql_list.append(''.join(("AND u.role=", str(c.ROLE_016_CORR), "::INT ",
                                            "AND (POSITION('", c.USERGROUP_AUTH4_CORR, "' IN ual.usergroups) > 0)")))
                else:
                    if request.user.role >= c.ROLE_064_ADMIN:
                        sql_list.append(''.join(("AND u.role<=", str(request.user.role), "::INT")))
                    else:
                    # user role can never be greater than request.user.role, except when school retrieves correctors
                        sql_list.append(''.join(("AND u.role=", str(request.user.role), "::INT")))

                        schoolbase_pk = request.user.schoolbase.pk if request.user.schoolbase.pk else 0
                        sql_list.append(''.join(("AND u.schoolbase_id=", str(schoolbase_pk), "::INT")))

            # sql_list.append('ORDER BY LOWER(sb.code), LOWER(u.username)')
            sql_list.append('ORDER BY u.id')
            sql = ' '.join(sql_list)

            if logging_on:
                for sql_txt in sql_list:
                    logger.debug(' > ' + str(sql_txt))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = af.dictfetchall(cursor)

                # convert string allowed_schoolbases to dict, remove string PR2022-11-22
                if rows:
                    for user_dict in rows:
                        if logging_on:
                            logger.debug('  ====>  user_dict: ' + str(user_dict))

                        allowed_sections_str = user_dict.get('allowed_sections')
                        allowed_sections_dict = json.loads(allowed_sections_str) if allowed_sections_str else None

                        if logging_on:
                            logger.debug('  ====>  allowed_sections_dict: ' + str(allowed_sections_dict))
                            logger.debug('  ====>  request.user.schoolbase.pk) not in allowed_sections_dict: ' + str(str(request.user.schoolbase.pk) not in allowed_sections_dict))

                        # PR2023-03-26 when school downolads corrector users: add only when school is in allowed schools of corrector user
                        skip_add_to_list = False
                        if school_correctors_only:
                           if str(request.user.schoolbase.pk) not in allowed_sections_dict:
                               skip_add_to_list = True

                        if not skip_add_to_list:

                            usergroups_str = user_dict.get('ual_usergroups')
                            user_dict['usergroups'] = json.loads(usergroups_str) if usergroups_str else None
                            # del user_dict['ual_usergroups']

                            allowed_clusters_str = user_dict.get('allowed_clusters')
                            allowed_cluster_pk_arr = json.loads(allowed_clusters_str) if allowed_clusters_str else None
                            del user_dict['allowed_clusters']

                            user_dict['allowed_sections_dict'] = allowed_sections_dict if allowed_sections_dict else None

                            # create allowed depbase, schoolbases, levelbases
                            if allowed_sections_dict:
                                # allowed_sections_dict: {'5': {'1': {'5': [118, 132, 154], '6': [118, 132, 154]}}} <class 'dict'>

                                if logging_on:
                                    logger.debug('  @@@@@@   allowed_sections_dict: ' + str(allowed_sections_dict))

                                r_allowed_sections = {}
                                schoolbase_pk_arr, r_depbase_pk_arr, lvlbase_pk_arr, r_subjbase_pk_arr = [], [], [], []

                                for schoolbase_pk_str, allowed_depbases_dict in allowed_sections_dict.items():
                                    # depbases_dict: {'1': {'5': [118, 132, 154], '6': [118, 132, 154]}} <class 'dict'>

                                    schoolbase_pk_int = int(schoolbase_pk_str)
                                    if schoolbase_pk_int not in schoolbase_pk_arr:
                                        schoolbase_pk_arr.append(schoolbase_pk_int)

                                    r_depbase_dict = {}
                                    if allowed_depbases_dict:
                                        for depbase_pk_str, lvlbases_dict in allowed_depbases_dict.items():
                                            # lvlbases_dict: {'5': [118, 132, 154], '6': [118, 132, 154]} <class 'dict'>

                                            depbase_pk_int = int(depbase_pk_str)
                                            if depbase_pk_int not in r_depbase_pk_arr:
                                                r_depbase_pk_arr.append(depbase_pk_int)

                                            r_lvlbase_dict = {}
                                            if lvlbases_dict:

                                                if logging_on:
                                                    logger.debug(' ===   lvlbases_dict: ' + str(lvlbases_dict) + ' ' + str(type(lvlbases_dict)))

                                                for lvlbase_pk_str, lvl_base_subjbases_arr in lvlbases_dict.items():
                                                    # lvl_base_subjbases_arr: [118, 132, 154] <class 'list'>
                                                    lvlbase_pk_int = int(lvlbase_pk_str)
                                                    if lvlbase_pk_int not in lvlbase_pk_arr:
                                                        lvlbase_pk_arr.append(int(lvlbase_pk_str))

                                                    r_subjbases_arr = []
                                                    for subjbase_pk_int in lvl_base_subjbases_arr:
                                                        if logging_on:
                                                            logger.debug(' ???   subjbase_pk_int: ' + str(subjbase_pk_int) + ' ' + str(type(subjbase_pk_int)))
                                                        if subjbase_pk_int not in r_subjbase_pk_arr:
                                                            r_subjbase_pk_arr.append(subjbase_pk_int)

                                                    r_lvlbase_dict[lvlbase_pk_int] = lvl_base_subjbases_arr

                                            r_depbase_dict[depbase_pk_int] = r_lvlbase_dict

                                    r_allowed_sections[schoolbase_pk_int] = r_depbase_dict

                                user_dict['allowed_sections'] = r_allowed_sections if r_allowed_sections else None

                                schoolbases_code, schoolbases_name = get_allowed_schoolbases(schoolbase_pk_arr)
                                user_dict['allowed_schoolbases'] = schoolbases_code
                                user_dict['allowed_schoolbases_title'] = schoolbases_name
                                user_dict['allowed_depbases'], has_level_req = get_allowed_depbases(r_depbase_pk_arr, all_depbases_rows)
                                user_dict['allowed_lvlbases'] = get_allowed_lvlbases(lvlbase_pk_arr, has_level_req, all_lvlbases_rows)

                                subjbases_code, subjbases_name = get_allowed_subjbases(r_subjbase_pk_arr, all_subjbases_dict)
                                user_dict['allowed_subjbases'] = subjbases_code
                                user_dict['allowed_subjbases_title'] = subjbases_name

                                cluster_pk_list, cluster_name_list = get_allowed_clusters(allowed_cluster_pk_arr, all_clusters_dict)
                                user_dict['allowed_clusters_pk'] = cluster_pk_list
                                user_dict['allowed_clusters'] = cluster_name_list

                            user_list.append (user_dict)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return user_list
# - end of create_user_rowsNEW


########################################################################

def create_permit_list(permit_pk=None):
    # --- create list of all permits PR2021-03-18
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_permit_list ============= ')

    sql_keys = {}
    sql_list = ["SELECT p.id, CONCAT('userpermit_', p.id::TEXT) AS mapid,",
                "p.action, p.role, p.page, p.usergroups",
                "FROM accounts_userpermit AS p"
                ]
    if permit_pk:
        sql_keys['pk'] = permit_pk
        sql_list.append("WHERE p.id = %(pk)s::INT")

    sql_list.append("ORDER BY p.id")
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    # row: {'id': 69, 'mapid': 'userpermit_69', 'action': 'view', 'role': 8,
    #       'page': 'page_student', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'}

    return rows
# - end of create_permit_list


########################################################################
# === create_or_validate_user_instance ========= PR2020-08-16 PR2021-01-01 PR2022-012-07

def create_or_validate_user_instance(user_schoolbase, upload_dict, user_pk, usergroups_arr, is_validate_only,
                                     user_lang, sel_examyear, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('-----  create_or_validate_user_instance  -----')
        logger.debug('    upload_dict:      ' + str(upload_dict))
        logger.debug('    user_schoolbase:  ' + str(user_schoolbase))
        logger.debug('    user_pk:          ' + str(user_pk))
        logger.debug('    is_validate_only: ' + str(is_validate_only))

    # - also add userAllowed instance, it stores usergroups

    country = request.user.country

    has_error = False

    err_dict = {}
    ok_dict = {}
    new_user_pk = None

    # <PERMIT> PR220-09-24
    #  - only perm_admin and perm_system can add / edit / delete users
    #  - only role_system and role_admin (ETE) can add users of other schools
    #  - role_system, role_admin, role_insp and role_school can add users of their own school

# - check if schoolbase has value
    if user_schoolbase is None:
        err_dict['schoolcode'] = _('Please enter a school.')
        has_error = True

# - check if this username already exists in this schoolbase
    # user_pk is pk of user that will be validated when the user already exist.
    # user_pk is None when new user is created or validated
    username = upload_dict.get('username')
    schoolbaseprefix = user_schoolbase.prefix if user_schoolbase else None
    if logging_on:
        logger.debug('    username: ' + str(username))
        logger.debug('    schoolbaseprefix: ' + str(schoolbaseprefix))
    msg_err, user_without_userallowed = awpr_val.validate_unique_username(sel_examyear, username, schoolbaseprefix, user_pk)

    if user_without_userallowed is None:
        if msg_err:
            err_dict['username'] = msg_err
            has_error = True

    # - check if namelast is blank
        last_name = upload_dict.get('last_name')
        #logger.debug('last_name: ' + str(last_name))
        msg_err = awpr_val.validate_notblank_maxlength(last_name, c.MAX_LENGTH_NAME, _('The name'))
        if msg_err:
            err_dict['last_name'] = msg_err
            has_error = True

    # - check if this is a valid email address:
        email = upload_dict.get('email')
        #logger.debug('email: ' + str(email))
        msg_err = awpr_val.validate_email_address(email)
        if msg_err:
            err_dict['email'] = msg_err
            has_error = True

    # - check if this email address already exists
        else:
            msg_err = awpr_val.validate_unique_useremail(email, country, user_schoolbase, user_pk)
            if msg_err:
                err_dict['email'] = msg_err
                has_error = True

        if not is_validate_only and not has_error:
        # - get now
            # timezone.now() is timezone aware, based on the USE_TZ setting;
            # datetime.now() is timezone naive. PR2018-06-07
            now_utc = timezone.now()

        # - new user gets role from defaultrole of user_schoolbase
        #   PR2021-02-06 debug: don't forget to set values of defaultrole in schoolbase! > is done in create_school_instance
            role = user_schoolbase.defaultrole

        # - create new user
            prefixed_username = user_schoolbase.prefix + username
            new_user = acc_mod.User(
                country=country,
                schoolbase=user_schoolbase,
                username=prefixed_username,
                last_name=last_name,
                email=email,
                role=role,
                # NIU usergroups=usergroups,
                is_active=True,
                activated=False,
                lang=user_lang,
                modified_by=request.user,
                modified_at=now_utc)
            new_user.save()

            #logger.debug('new_user: ' + str(new_user))
            if new_user:
                usergroups_str = json.dumps(usergroups_arr) if usergroups_arr else None
                # PR2023-02-17 add UserAllowed record for each examyear.
                # otherwise new users cannot access previous years
                examyears = sch_mod.Examyear.objects.filter(
                    country=country
                )
                for examyear in examyears:
                    new_user_allowed = acc_mod.UserAllowed(
                        user=new_user,
                        examyear=examyear,
                        usergroups=usergroups_str,
                        modifiedby=request.user,
                        modifiedat=now_utc
                    )
                    new_user_allowed.save()

                new_user_pk = new_user.pk

                current_site = get_current_site(request)

    # -  create first line of email
                # {{ requsr_schoolname }} {% trans 'has made the following AWP-online account for you:' %}
                # When requser and new_user are from the same school: requser.last_name
                # - get selected examyear from request_item_setting, Usersetting or first in list

                sel_examyear, examyear_save_NIU, multiple_examyears_exist = af.get_sel_examyear_with_default(request)
                requsr_school = sch_mod.School.objects.get_or_none( base=request.user.schoolbase, examyear=sel_examyear)
                new_user_school = sch_mod.School.objects.get_or_none( base=user_schoolbase, examyear=sel_examyear)

                req_usr = request.user.last_name if request.user.last_name else request.user.username
                req_school = ''
                if requsr_school and requsr_school.name:
                    if requsr_school.article:
                        req_school = requsr_school.article.capitalize() + ' '
                    req_school += requsr_school.name
                else:
                    req_school = request.user.schoolbase.code if request.user.schoolbase.code else '---'

                usr_schoolname_with_article = ''
                if new_user_school and new_user_school.name:
                    if new_user_school.article:
                        usr_schoolname_with_article = new_user_school.article.lower() + ' '
                    usr_schoolname_with_article += new_user_school.name
                else:
                    usr_schoolname_with_article = '---'

    # -  send email 'Activate your account'
                subject = _('Activate your AWP-online account')
                from_email = 'AWP-online <noreply@awponline.net>'
                message = render_to_string('signup_activation_email.html', {
                    'user': new_user,
                    'usr_schoolname': usr_schoolname_with_article,
                    'req_school': req_school,
                    'req_usr': req_usr,
                    'domain': current_site.domain,

                    # PR2018-04-24 debug: In Django 2.0 you should call decode() after base64 encoding the uid, to convert it to a string:
                    # 'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    # PR2021-03-24 debug. Gave error: 'str' object has no attribute 'decode'
                    # apparently force_bytes(user.pk) returns already a string, no need for decode() any more
                    # from https://stackoverflow.com/questions/28583565/str-object-has-no-attribute-decode-python-3-error
                    # was: 'uid': urlsafe_base64_encode(force_bytes(new_user.pk)).decode(),
                    'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
                    'token': account_activation_token.make_token(new_user),
                })
                # PR2018-04-25 arguments: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
                mails_sent = send_mail(subject, message, from_email, [new_user.email], fail_silently=False)
                #logger.debug('mails sent: ' + str(mails_sent))
                # - return message 'We have sent an email to user'
                msg01 = _("User '%(usr)s' is registered successfully at %(school)s.") % {'usr': new_user.username_sliced, 'school': usr_schoolname_with_article}
                msg02 = _("We have sent an email to the email address '%(email)s'.") % {'email': new_user.email}
                msg03 = _(
                    'The user must click the link in that email to verify the email address and create a password.')
                msg04 = _('Check the spam folder, if the email does not appear within a few minutes.')
                ok_dict = {'msg01': msg01, 'msg02': msg02, 'msg03': msg03, 'msg04': msg04}

    if logging_on:
        logger.debug('    err_dict: ' + str(err_dict))
        logger.debug('    ok_dict: ' + str(ok_dict))
        logger.debug('    user_without_userallowed: ' + str(user_without_userallowed))

    return new_user_pk, err_dict, ok_dict, user_without_userallowed
# - +++++++++ end of create_or_validate_user_instance ++++++++++++


# === update_user_instance ========== PR2020-08-16 PR2020-09-24 PR2021-03-24 PR2021-08-01 PR2022-02-18
def update_user_instance(sel_examyear, user_instance, upload_dict, msg_list, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('-----  update_user_instance  -----')
        logger.debug('    user_instance: ' + str(user_instance))
        logger.debug('    upload_dict: ' + str(upload_dict))

    has_error = False
    err_dict = {}
    ok_dict = {}

    if user_instance:
        country = request.user.country
        usr_schoolbase = user_instance.schoolbase
        user_pk = user_instance.pk

        data_has_changed = False
        # upload_dict: {'mode': 'update', 'schoolbase_pk': 23, 'username': 'Ete', 'last_name': 'Ete2',
        #           'email': 'hmeijs@gmail.com', 'user_pk': 41}
        for field, field_value in upload_dict.items():

            if logging_on:
                logger.debug('    field: ' + str(field))
                logger.debug('    field_value: ' + str(field_value))

# - check if this username already exists in this school, exept for this user
            if field == 'username':
                new_username = field_value
                msg_err, user_without_userallowed = awpr_val.validate_unique_username(sel_examyear, new_username, usr_schoolbase.prefix, user_pk)

                if logging_on:
                    logger.debug('    new_username: ' + str(new_username))
                    logger.debug('    msg_err: ' + str(msg_err))

                if msg_err:
                    err_dict[field] = msg_err
                    has_error = True
                if not has_error and new_username and new_username != user_instance.username:
                    prefixed_username = usr_schoolbase.prefix + new_username
                    user_instance.username = prefixed_username
                    data_has_changed = True

# - check if namelast is blank
            elif field == 'last_name':
                new_last_name = field_value
                msg_err = awpr_val.validate_notblank_maxlength(new_last_name, c.MAX_LENGTH_NAME, _('The name'))

                if logging_on:
                    logger.debug('    new_last_name: ' + str(new_last_name))
                    logger.debug('    msg_err: ' + str(msg_err))

                if msg_err:
                    err_dict[field] = msg_err
                    has_error = True
                if not has_error and new_last_name and new_last_name != user_instance.last_name:
                    user_instance.last_name = new_last_name
                    data_has_changed = True

# - check if this is a valid email address:
            elif field == 'email':
                new_email = field_value
                msg_err = awpr_val.validate_email_address(new_email)

                if logging_on:
                    logger.debug('    new_email: ' + str(new_email))
                    logger.debug('    msg_err: ' + str(msg_err))

                if msg_err:
                    err_dict[field] = msg_err
                    has_error = True
# - check if this email address already exists
                else:
                    msg_err = awpr_val.validate_unique_useremail(new_email, country, usr_schoolbase, user_pk)
                    if msg_err:
                        err_dict[field] = msg_err
                        has_error = True

                if not has_error and new_email and new_email != user_instance.email:
                    user_instance.email = new_email
                    data_has_changed = True

            elif field == 'usergroups':
                # field_value is dict: {'edit': True}
                usergroups_haschanged = update_userallowed_usergroups(request, user_instance, sel_examyear, field_value)
                if usergroups_haschanged:
                    data_has_changed = True
                if logging_on:
                    logger.debug('    usergroups_haschanged: ' + str(usergroups_haschanged))

            elif field == 'allowed_clusters':
                allowedcluster_haschanged = update_allowedclusters(request, user_instance, sel_examyear, field_value, True) # True = validate
                if allowedcluster_haschanged:
                    data_has_changed = True
                if logging_on:
                    logger.debug('    allowedcluster_haschanged: ' + str(allowedcluster_haschanged))

            # PR2023-02-14 deprecated. Table accounts_userallowed is updated by UserAllowedSectionsUploadView
            elif field in ('allowed_depbases', 'allowed_schoolbases', 'allowed_levelbases', 'allowed_subjectbases', 'allowed_clusterbases') and False:
                old_value = getattr(user_instance, field)
                if logging_on:
                    logger.debug('>>>>>>>>>>>>>>> field: ' + str(field))
                    logger.debug('field_value: ' + str(field_value))
                    logger.debug('old_value: ' + str(old_value))
                if field_value != old_value:
                    setattr(user_instance, field, field_value)
                    data_has_changed = True
                if logging_on:
                    logger.debug('field_value: ' + str(field_value))
                    logger.debug('data_has_changed: ' + str(data_has_changed))

        # - sysadmins cannot remove sysadmin permission from their own account
                """
                if acc_prm.is_usergroup_admin(request.user):
                    if permit_field in ('perm_admin', 'perm_system'):
                        if user_instance == request.user:
                            if not new_permit_bool:
                                err_dict[field] = _("System administrators cannot remove their own 'system administrator' permission.")
                                has_error = True

                if not has_error:
        # - validation: user cannot have perm04_auth1 and perm08_auth2 at the same time - resert other auth field

                    permit_sum_has_changed = False
                    if new_permit_bool:
                        if new_permit_int not in saved_permit_list:
                            saved_permit_list.append(new_permit_int)
                            permit_sum_has_changed = True
                    else:
                        if new_permit_int in saved_permit_list:
                            saved_permit_list.remove(new_permit_int)
                            permit_sum_has_changed = True
                    if permit_sum_has_changed:
                    # - remove value of other auth permits when auth permit is set
                        if new_permit_bool:
                            remove_other_auth_permits(permit_field, saved_permit_list)

                        new_permit_sum = get_permit_sum_from_tuple(saved_permit_list)

                        #logger.debug('saved_permit_list: ' + str(saved_permit_list))
                        #logger.debug('new_permit_sum: ' + str(new_permit_sum))

                        user_instance.permits = new_permit_sum
                        data_has_changed = True
                    """
            elif field == 'is_active':
                new_isactive = field_value if field_value else  False
                # sysadmins cannot remove is_active from their own account
                if acc_prm.is_usergroup_admin(request.user) and user_instance == request.user:
                    if not new_isactive:
                        err_dict[field] = _("System administrators cannot make their own account inactive.")
                        has_error = True
                if not has_error and new_isactive != user_instance.is_active:
                    user_instance.is_active = new_isactive
                    data_has_changed = True

# -  update user
        if not has_error:
            if data_has_changed:
# - get now without timezone
                now_utc_naive = datetime.utcnow()
                now_utc = now_utc_naive.replace(tzinfo=pytz.utc)

                try:
                    user_instance.modifiedby = request.user
                    user_instance.modifiedat = now_utc
                    user_instance.save()
                    ok_dict = {'msg01':  _("The changes have been saved successfully.")}
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))
                    msg_html = ''.join((
                        str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                        str(_("The changes have not been saved."))))
                    msg_dict = {'header': str(_('Update user account')), 'class': 'border_bg_invalid',
                                'msg_html': msg_html}
                    msg_list.append(msg_dict)

    if logging_on:
        logger.debug('ok_dict: ' + str(ok_dict))

    return err_dict, ok_dict
# - +++++++++ end of update_user_instance ++++++++++++

# === update_userallowed_usergroups ===================================== PR2021-03-24 PR2021-08-01 PR2023-01-14
def update_userallowed_usergroups(request, user_instance, sel_examyear, field_dict):
    # called by UserUploadView.update_user_instance and UserpermitUploadView.update_grouppermit
    # validate only when called by update_user_instance
    # when validate = True: when setting value: remove auth1 or auth2 when the other one is selected
    #                       when removing value: skip when auuth tries to remove it won auth usergroup

    # usergroups: {auth2: false} dict always contains only 1 auth key

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('-----  update_userallowed_usergroups  -----')
        logger.debug('    field_dict:    ' + str(field_dict) + ' ' + str(type(field_dict)))
        logger.debug('    user_instance: ' + str(user_instance) + '  ' + str(type(user_instance)))
        logger.debug('    sel_examyear:  ' + str(sel_examyear))
        logger.debug('    -----')

# - get sel_examyear_instance from req_usr. NOT from user_instance
    # PR2023-02-17 debug: new user that has not activated his account yet has no selected_examyear yet.
    # therefore admin could not could not cahnge usergroups.
    # must use sel_examyear_instance from req_usr. NOT from user_instance
    sel_examyear_instance = acc_prm.get_sel_examyear_from_user_instance(request.user)

# - get userallowed_instance from user_instance, NOT from request.user
    userallowed_instance = acc_prm.get_userallowed_instance(user_instance, sel_examyear_instance)

    data_has_changed = False

    if userallowed_instance:
        if logging_on:
            logger.debug('    userallowed_instance:  ' + str(userallowed_instance))
            logger.debug('    userallowed_instance.usergroups:  ' + str(userallowed_instance.usergroups))

# - get saved_usergroups_list from userallowed_instance
        saved_usergroups_str = None
        new_usergroups_list = []
        if userallowed_instance:
            saved_usergroups_str = getattr(userallowed_instance, 'usergroups')
            if saved_usergroups_str:
                saved_usergroups_list = json.loads(saved_usergroups_str)
                if saved_usergroups_list:
                    for saved_usergroup in saved_usergroups_list:
                        if saved_usergroup and isinstance(saved_usergroup, str):
                            new_usergroups_list.append(saved_usergroup)

        if logging_on:
            logger.debug('    saved_usergroups_str: ' + str(saved_usergroups_str) + ' ' + str(type(saved_usergroups_str)))
            logger.debug('    new_usergroups_list: ' + str(new_usergroups_list) + ' ' + str(type(new_usergroups_list)))
            # saved_usergroups_list: [1689, 1690] <class 'list'>

        if field_dict:
            if logging_on:
                logger.debug('    field_dict: ' + str(field_dict) + ' ' + str(type(field_dict)))
                # field_dict =  {auth2: false} it always contains only 1 auth key

            for usergroup, new_value in field_dict.items():
                new_value = False if new_value is None else new_value
                if logging_on:
                    logger.debug('    usergroup: ' + str(usergroup) + ' ' + str(type(usergroup)))
                    logger.debug('    new_value: ' + str(new_value) + ' ' + str(type(new_value)))

                if new_value:

                    if new_usergroups_list:

            # - user cannot be auth1 and auth2 at the same time, remove the other if exists
                        auth_list = (c.USERGROUP_AUTH1_PRES, c.USERGROUP_AUTH2_SECR)
                        if usergroup in auth_list:
                            for auth in auth_list:
                                if logging_on:
                                    logger.debug('....usergroup: ' + str(usergroup) + ' ' + str(type(usergroup)))
                                    logger.debug('    auth: ' + str(auth) + ' ' + str(type(auth)))
                                if auth != usergroup:
                                    if auth in new_usergroups_list:
                                        new_usergroups_list.remove(auth)
                                        if logging_on:
                                            logger.debug('    new_usergroups_list.remove(auth): ' + str(auth) + ' ' + str(type(auth)))

                        # PR2022-03-08 yes, user can be auth3 and auth4 at the same time
                        #   was: # PR2022-02-17 cannot be auth3 and auth4 at the same time

                    if usergroup not in new_usergroups_list:
                        new_usergroups_list.append(usergroup)
                        if logging_on:
                            logger.debug('    new_usergroups_list: ' + str(new_usergroups_list))
                else:
                    if usergroup in new_usergroups_list:
            # - admin cannot remove his own admin usergroup
            #   only when called by update_user_instance

                        # pass when request_usr is admin and wants to delete it own admin usergroup
                        if usergroup == c.USERGROUP_ADMIN and user_instance.pk == request.user.pk:
                            if logging_on:
                                logger.debug('pass when request_usr is admin and wants to delete it own admin usergroup')
                            pass
                        else:
                            new_usergroups_list.remove(usergroup)
                logger.debug('    ..........')
# - end of loop

        # sort the list before saving, to be able to compare new and saved usergroups
        new_usergroups_list.sort()
        if logging_on:
            logger.debug('    new_usergroups_list: ' + str(new_usergroups_list))

        new_usergroups_str = json.dumps(new_usergroups_list)

        if new_usergroups_str != saved_usergroups_str:
            setattr(userallowed_instance, 'usergroups', new_usergroups_str)
            userallowed_instance.save()

            data_has_changed = True
        if logging_on:
            logger.debug('    new_usergroups_str: ' + str(new_usergroups_str))
            logger.debug('    data_has_changed: ' + str(data_has_changed))

    return data_has_changed
# - end of update_userallowed_usergroups


# === update_allowedclusters ===================================== PR2023-01-27
def update_allowedclusters(request, user_instance, sel_examyear, field_value, validate):
    # called by UserUploadView.update_user_instance and UserpermitUploadView.update_grouppermit
    # validate only when called by update_user_instance
    # usergroups: {auth2: false} dict always contains only 1 auth key
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('-----  update_allowedclusters  -----')
        logger.debug('    field_value:    ' + str(field_value) + ' ' + str(type(field_value)))
        logger.debug('    validate:      ' + str(validate))
        logger.debug('    user_instance: ' + str(user_instance))
        logger.debug('    sel_examyear:  ' + str(sel_examyear))

# - get userallowed
    userallowed_instance = acc_mod.UserAllowed.objects.filter(
        user=user_instance,
        examyear=sel_examyear
    ).order_by('-pk').first()
    if logging_on:
        logger.debug('    userallowed_instance:    ' + str(userallowed_instance))

    data_has_changed = False

    if userallowed_instance:
        new_allowed_clusters_str = None
        saved_allowed_clusters_str = userallowed_instance.allowed_clusters

        if field_value:
            # field_value:    [407, 412, 413, 414, 421, 423] <class 'list'>
            new_allowed_clusters_list = field_value

        # sort the list before saving, to be able to compare new and saved allowed_clusters
            new_allowed_clusters_list.sort()

            new_allowed_clusters_str = json.dumps(new_allowed_clusters_list)

        if logging_on:
            logger.debug('    new_allowed_clusters_str: ' + str(new_allowed_clusters_str))
            logger.debug('    saved_allowed_clusters_str: ' + str(saved_allowed_clusters_str))

        if new_allowed_clusters_str != saved_allowed_clusters_str:
            setattr(userallowed_instance, 'allowed_clusters', new_allowed_clusters_str)
            userallowed_instance.save()

            data_has_changed = True

    return data_has_changed
# - end of update_allowedclusters

# +++++++++++++++++++  permits +++++++++++++++++++++++
def get_permit(permits_int, permit_index):  # PR2020-10-12 PR2021-01-18
    has_permit = False
    if permits_int and permit_index:
        permits_tuple = get_permits_tuple(permits_int)
        has_permit = permit_index in permits_tuple
    return has_permit


def get_permits_tuple(permits_int): # PR2020-10-12 separate function made
    # PR2018-05-27 permits_tuple converts self.permits_int into tuple, e.g.: permits=15 will be converted to permits_tuple=(1,2,4,8)
    permits_list = []
    if permits_int is not None:
        if permits_int != 0:
            for i in range(7, -1, -1):  # range(start_value, end_value, step), end_value is not included!
                power = 2 ** i
                if permits_int >= power:
                    permits_int = permits_int - power
                    permits_list.insert(0, power)  # list.insert(0, value) adds at the beginning of the list
    if not permits_list:
        permits_list = [0]
    return tuple(permits_list)


def get_permit_sum_from_tuple(permits_tuple):
    # PR2021-01-19 sum all values of permits in tuple
    return sum(permits_tuple) if permits_tuple else 0


def remove_other_auth_permits(permit_field, permit_list):
    # PR2021-01-19 remove value of other auth permits when auth permit is set
    if permit_field != "perm_auth1" and c.USERGROUP_AUTH1_PRES in permit_list:
        permit_list.remove(c.USERGROUP_AUTH1_PRES)
    if permit_field != "perm_auth2" and c.USERGROUP_AUTH2_SECR in permit_list:
        permit_list.remove(c.USERGROUP_AUTH2_SECR)
    if permit_field != "perm_auth3" and c.USERGROUP_AUTH3_EXAM in permit_list:
        permit_list.remove(c.USERGROUP_AUTH3_EXAM)
    if permit_field != "perm_auth4" and c.USERGROUP_AUTH4_CORR in permit_list:
        permit_list.remove(c.USERGROUP_AUTH4_CORR)


def has_permit(permits_int, permit_index): # PR2020-10-12 separate function made PR2021-01-18
    has_permit = False
    if permits_int:
        permits_tuple = get_permits_tuple(permits_int)
        has_permit = permit_index in permits_tuple
    return has_permit


# +++++++++++++++++++  get and set setting +++++++++++++++++++++++

#   get_usersetting_dict is moved to accounts.permits PR2023-01-25

def set_usersetting_dict(key_str, setting_dict, request):  # PR2019-03-09 PR2021-01-25
    # function saves setting in first row that matches the filter, adds new row when not found
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('---  set_usersetting_dict  ------- ')
        logger.debug('key_str: ' + str(key_str))
        logger.debug('setting_dict: ' + str(setting_dict))

    #  json.dumps converts a dict in a json object
    #  json.loads retrieves a dict (or other type) from a json object

    try:
        #PR2021-07-05 debug: is_authenticated added to prevent error: 'AnonymousUser' object is not iterable
        if request.user and request.user.is_authenticated and key_str:
            setting_str = json.dumps(setting_dict)
            row = Usersetting.objects.filter(user=request.user, key=key_str).order_by('-id').first()
            if row:
                row.setting = setting_str
            else:
                # don't add row when setting has no value
                # note: empty setting_dict {} = False, empty json "{}" = True, therefore check if setting_dict is empty
                if setting_dict:
                    row = Usersetting(user=request.user, key=key_str, setting=setting_str)
            row.save()

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        logger.error('key_str: ', str(key_str))

    if logging_on:
        logger.error('setting_dict: ', str(setting_dict))
# - end of set_usersetting_dict


def set_usersetting_from_uploaddict(upload_dict, request):  # PR2021-02-07
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- set_usersetting_from_uploaddict ----- ')
        logger.debug('     upload_dict: ' + str(upload_dict))

    # upload_dict: {'selected_pk': {'sel_examtype': 'sr', 'sel_examperiod': 1}}
    # upload_dict: {'selected_pk': {'sel_subject_pk': 46}}
    # logger.debug('upload_dict: ' + str(upload_dict))

    # PR2020-07-12 debug. creates multiple rows when key does not exist and new dict has multiple subkeys
    # PR2020-10-04 not any more, don't know why
    # - loop through keys of upload_dict
    for key, new_setting_dict in upload_dict.items():
        if logging_on:
            logger.debug('     key: ' + str(key))
            logger.debug('     new_setting_dict: ' + str(new_setting_dict))
        set_usersetting_from_upload_subdict(key, new_setting_dict, request)
# - end of set_usersetting_from_uploaddict


def set_usersetting_from_upload_subdict(key_str, new_setting_dict, request):  # PR2021-02-07 PR2021-08-19 PR2021-12-02

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- set_usersetting_from_upload_subdict ----- ')
        logger.debug('     key_str: ' + str(key_str))
        # key_str: page_grade
        logger.debug('     new_setting_dict: ' + str(new_setting_dict))
        # new_setting_dict: {'cols_hidden': {'all': ['examnumber', 'subj_name']}}
        # new_setting_dict: {'sel_examtype': 'sr', 'sel_examperiod': 1}

    # upload_dict: {'selected_pk': {'sel_subject_pk': 46}}
    # PR2020-07-12 debug. creates multiple rows when key does not exist ans newdict has multiple subkeys
    # PR2020-10-04 not any more, don't know why
    # - loop through keys of upload_dict

    # keys are: 'sel_page'  = {'page': 'page_student'},
    #           'selected_pk' = {'sel_depbase_pk': 23'}
    #           'page_student' = {'sel_btn': 'btn_subject', 'cols_hidden': {'subject': ['name', ...]}
    # new_setting_dict = 'page_examyear', dict = {'sel_btn': 'examyears'}
    # get saved_settings_dict. new settings will be put in saved_settings_dict,  saved_settings_dict will be saved
    saved_settings_dict = acc_prm.get_usersetting_dict(key_str, request)

    if logging_on:
        logger.debug('     saved_settings_dict: ' + str(saved_settings_dict))
        # saved_settings_dict: {}
        # saved_settings_dict: {'all': ['examnumber', 'subj_name']}
        # saved_settings_dict: {'sel_examyear_pk': 58, 'sel_depbase_pk': 1, 'sel_examtype': None, 'sel_examperiod': 1, 'sel_lvlbase_pk': 12, 'sel_sctbase_pk': 12}
    try:
        has_changed = False
    # - loop through subkeys of new_setting_dict
        if logging_on:
            logger.debug(' --------------------- loop ')
        for subkey, new_subdict_or_value in new_setting_dict.items():
            # subkeys are the keys in new_setting_dict, for instance: 'cols_hidden'
            # values in new_setting_dict can be a string, number or a dict
            # string, number: {'page': 'page_student'}, {'sel_depbase_pk': 23'}
            # or dict:        {'cols_hidden': {'scheme': ['min_mtv', 'max_mvt')}}

            if logging_on:
                logger.debug('    subkey: ' + str(subkey))
                # subkey: cols_hidden
                # subkey: sel_examperiod
                logger.debug('    new_subdict_or_value: ' + str(new_subdict_or_value))
                # new_subdict_or_value: {'all': ['examnumber', 'subj_name']}
                # new_subdict_or_value: sr

            # when subkey = cols_hidden it contains a dict: saved_subdict_or_value = {'published': ['examperiod', 'datepublished', 'url']}}
            # when subkey = sel_btn it contains a value: 'btn_studsubj'
            # check if value is dict or sting
            if isinstance(new_subdict_or_value, dict):
                # get saved_subdict_or_value exists in saved_settings_dict, create empty dict when not found
                # when subkey = cols_hidden: saved_subdict_or_value is a dict
                saved_subdict_or_value = af.get_dict_value(saved_settings_dict, (subkey,))
                if logging_on:
                    logger.debug('saved_subdict_or_value: ' + str(saved_subdict_or_value) + ' ' + str(type(saved_subdict_or_value)))

                # PR2021-12-02 debug: don't use 'saved_subdict_or_value is None', because get_dict_value returns {}, not None
                if not saved_subdict_or_value:
                    saved_settings_dict[subkey] = {}
                    saved_subdict_or_value = saved_settings_dict[subkey]
                if logging_on:
                    logger.debug('saved_subdict_or_value: ' + str(saved_subdict_or_value))
                    # saved_subdict_or_value: {}

                for subsubkey, new_subsubvalue in new_subdict_or_value.items():
                    saved_subsubvalue = af.get_dict_value(saved_subdict_or_value, (subsubkey,))

                    if logging_on:
                        logger.debug('..... saved_subsubvalue: ' + str(saved_subsubvalue))
                        # saved_subsubvalue: {}
                        logger.debug('..... subsubkey: ' + str(subsubkey))
                        # subsubkey: 'all'
                        logger.debug('       new_subsubvalue: ' + str( new_subsubvalue))
                        # new_subsubvalue: ['examnumber', 'subj_name']

                    # subsubkey is the tab name: 'studsubj', 'published' or 'all'
                    # new_subsubvalue is a list: ['examperiod', 'datepublished', 'url']

                    item_has_changed = replace_value_in_dict(saved_subdict_or_value, subsubkey, new_subsubvalue)

                    if logging_on:
                        logger.debug('----- saved_subdict_or_value: ' + str(saved_subdict_or_value))

                    if item_has_changed:
                        has_changed = True
            else:
                item_has_changed = replace_value_in_dict(saved_settings_dict, subkey, new_subdict_or_value)
                if item_has_changed:
                    has_changed = True

        if logging_on:
            logger.debug('----- saved_settings_dict: ' + str(saved_settings_dict))

        if has_changed:
            # - save key in usersetting and return settings_dict
            set_usersetting_dict(key_str, saved_settings_dict, request)

            if logging_on:
                logger.debug('******. saved_settings_dict: ' + str(saved_settings_dict) )
                logger.debug('Usersetting.set_setting from UserSettingsUploadView')

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        logger.error('key_str: ', str(key_str))
        logger.error('new_setting_dict: ', str(new_setting_dict))

    if logging_on:
        logger.debug('saved_settings_dict: ' + str(saved_settings_dict))
    return saved_settings_dict
# - end of set_usersetting_from_upload_subdict


def replace_value_in_dict(settings_dict, key_str, new_value): # PR2021-08-19 PR2021-12-02

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- replace_value_in_dict ----- ')
        logger.debug('    settings_dict: ' + str(settings_dict))
        #  settings_dict: {'sel_examyear_pk': 58, 'sel_depbase_pk': 1, 'sel_examtype': None, 'sel_examperiod': 1, 'sel_lvlbase_pk': 12, 'sel_sctbase_pk': 12}
        logger.debug('    key_str: ' + str(key_str))
        # key_str: all
        # key_str: sel_examtype
        logger.debug('    new_value: ' + str(new_value))
        # new_value: ['examnumber', 'sct_abbrev']
        # new_value: sr
    item_has_changed = False

    saved_subdict_or_value = af.get_dict_value(settings_dict, (key_str,))
    if logging_on:
        logger.debug('    saved_subdict_or_value: ' + str(saved_subdict_or_value))

    if new_value is None:
        if key_str in settings_dict:
            item_has_changed = True
            settings_dict.pop(key_str)
    elif new_value != saved_subdict_or_value:
        item_has_changed = True
        settings_dict[key_str] = new_value

    if logging_on:
        logger.debug('    item_has_changed: ' + str(item_has_changed))
        logger.debug('    settings_dict: ' + str(settings_dict))
    return item_has_changed


# +++++++++++++++++++  get and set setting +++++++++++++++++++++++
def get_usr_schoolname_with_article(user):  # PR2019-03-09 PR2021-01-25 PR2021-08-16

# - get schoolname PR2020-12-24
    examyear = af.get_todays_examyear_or_latest_instance(user.country)

    school = sch_mod.School.objects.get_or_none( base=user.schoolbase, examyear=examyear)

    usr_schoolname_with_article = ''
    if school and school.name:
        if school.article:
            usr_schoolname_with_article = school.article + ' ' + school.name
        else:
            usr_schoolname_with_article = school.name
    elif user.schoolbase and user.schoolbase.code:
        usr_schoolname_with_article = user.schoolbase.code

    return usr_schoolname_with_article
# - end of set_usersetting_from_upload_subdict


def get_username_dict(request):  # PR2021-12-19 PR2022-06-24
    # create dict with key = user_pk and value = username
    # used to add auth names without adding LEFT JOIN accounts_user to sql

    schoolbase_pk = request.user.schoolbase.pk if request.user.schoolbase.pk else 0
    sql_keys = {'sb_id': schoolbase_pk}

    username_dict = {}
    sql = "SELECT au.id, au.last_name FROM accounts_user AS au WHERE au.schoolbase_id = %(sb_id)s::INT"
    with connection.cursor() as cursor:
        cursor.execute(sql,sql_keys)

        for row in cursor.fetchall():
            username_dict[row[0]] = row[1]

    return username_dict
# - end of get_username_dict



def get_userfilter_allowed_lvlbase(request, sql_keys, sql_list, lvlbase_pk=None,
                                   sel_schoolbase_pk=None, sel_depbase_pk=None, skip_allowed_filter=False):
    # PR2022-03-12 PR2022-12-09

    #  if lvlbase_pk has value:
    #       if arr exists:
    #           --> filter on lvlbase_pk, only when lvlbase_pk in arr, otherwise: return no records
    #       else:
    #           --> filter on lvlbase_pk
    #  if lvlbase_pk is None:
    #       if arr exists:
    #           --> filter on lvlbase_pk's in array
    #       else:
    #           --> no filter

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_userfilter_allowed_lvlbase ----- ')
        logger.debug('    lvlbase_pk: ' + str(lvlbase_pk) + ' ' + str(type(lvlbase_pk)))
        logger.debug('    sel_schoolbase_pk: ' + str(sel_schoolbase_pk) + ' ' + str(type(sel_schoolbase_pk)))
        logger.debug('    sel_depbase_pk: ' + str(sel_depbase_pk) + ' ' + str(type(sel_depbase_pk)))
        logger.debug('    skip_allowed_filter: ' + str(skip_allowed_filter))

    filter_single_pk, filter_pk_arr, filter_none = None, None, False

    usergroups_arrNIU, allowed_sections_dict, allowed_clusters_arrNIU = get_request_userallowed(request)
    if logging_on:
        logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict) + ' ' + str( type(allowed_sections_dict)))

    allowed_lvlbase_pk_arr = []

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
                all_allowed = False
                for lvlbase_pk_str in allowed_depbase_dict:
                    lvlbase_pk_int = int(lvlbase_pk_str)
                    if lvlbase_pk_int == -9:
                        all_allowed = True
                        break
                    else:
                        allowed_lvlbase_pk_arr.append(lvlbase_pk_int)
                if all_allowed:
                    allowed_lvlbase_pk_arr = []
    if logging_on:
        logger.debug('    allowed_lvlbase_pk_arr: ' + str(allowed_lvlbase_pk_arr) + ' ' + str( type(allowed_lvlbase_pk_arr)))

    # NIU, moved to allowed_sections_dict: PR2022-12-09
    #   allowed_levelbase_arr = request.user.allowed_levelbases.split(';') if request.user.allowed_levelbases else []

    if lvlbase_pk:
        if not allowed_lvlbase_pk_arr or str(lvlbase_pk) in allowed_lvlbase_pk_arr or skip_allowed_filter:
            filter_single_pk = lvlbase_pk
        else:
            filter_none = True

    elif allowed_lvlbase_pk_arr and not skip_allowed_filter:
        if len(allowed_lvlbase_pk_arr) == 1:
            filter_single_pk = allowed_lvlbase_pk_arr[0]
        else:
            filter_pk_arr = allowed_lvlbase_pk_arr

    if logging_on:
        logger.debug('allowed_lvlbase_pk_arr: ' + str(allowed_lvlbase_pk_arr) + ' ' + str(type(allowed_lvlbase_pk_arr)))
        logger.debug('filter_single_pk: ' + str(filter_single_pk) + ' ' + str(type(filter_single_pk)))
        logger.debug('filter_pk_arr: ' + str(filter_pk_arr) + ' ' + str(type(filter_pk_arr)))
        logger.debug('filter_none: ' + str(filter_none) + ' ' + str(type(filter_none)))

    if filter_single_pk:
        sql_keys['lvlbase_pk'] = filter_single_pk
        sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

    elif filter_pk_arr:
        sql_keys['lvl_arr'] = filter_pk_arr
        sql_list.append("AND lvl.base_id IN ( SELECT UNNEST(%(lvl_arr)s::INT[]) )")

    elif filter_none:
        sql_list.append("AND FALSE")
# - end of get_userfilter_allowed_lvlbase


def get_userallowed_for_subjects_studsubj(sel_examyear, sel_schoolbase, sel_depbase, sel_lvlbase,
    request, skip_allowedsubjbase_filter, table=None):
    # PR2022-03-13 PR2022-12-17 PR2023-01-09
    # this function adds selected / allowed  filter to sql for subjects row, for page studsubject, subjects, exam, wolf
    # called by subjects.create_subject_rows

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' +++++ get_userallowed_for_subjects_studsubj +++++')

    sql_clause = ""

    try:
        sql_clause_arr = []

        req_usr = request.user
        subjbase_id_fld = 'studsubj.subjbase_id'  if table == 'studsubj' else 'subj.base_id'
        depbase_id_fld = 'dep.base_id'

# - get selected_pk_dict from usersettings
        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if logging_on:
            logger.debug('    selected_pk_dict: ' + str(selected_pk_dict) + ' ' + str(type(selected_pk_dict)))
        # selected_pk_dict: {'sel_schoolbase_pk': 2, 'sel_examyear_pk': 4, 'sel_depbase_pk': 1, 'sel_examperiod': 1, 'sel_examtype': 'ce', 'sel_auth_index': 2, 'sel_lvlbase_pk': 5} <class 'dict'>

# - get allowed_sections_dict from userallowed
        allowed_sections_dict = acc_prm.get_userallowed_sections_dict_from_request(request)
        if logging_on:
            logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict))
        #  allowed_sections_dict: {'13': {'1': {'4': [131], '-9': [117]}, '2': {'-9': [167, 118]}, '3': {'-9': []}}}

# +++ SCHOOL +++
    # - get selected school
        # - when role = school: selected school = req_usr.schoolbase
        # - otherwise: get selected school from settings
        #   do not add school_clause, only get allowed departments from school, school_clause and examyear are already in sql

        sel_schoolbase_pk = None
        if req_usr.role == c.ROLE_008_SCHOOL:
            if req_usr.schoolbase:
                sel_schoolbase_pk = req_usr.schoolbase_id
        else:
            # - check if school base is allowed
            # when allowed_sections_dict is empty: selected school is always allowed
            sel_schoolbase_pk = selected_pk_dict.get(c.KEY_SEL_SCHOOLBASE_PK)

# - check if selected school is allowed
    # - get allowed_schoolbase_dict, dict with allowed depbases / lvlbases of selected school
        allowed_schoolbase_dict, allowed_depbases_pk_arr = acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(allowed_sections_dict, sel_schoolbase_pk)
        # allowed_schoolbase_dict: {'1': {'-9': []}, '2': {'-9': []}, '3': {'-9': []}}
        # allowed_depbases_pk_arr: [1, 2, 3] <class 'list'>

        # - school is allowed when exists in allowed_sections_dict or when allowed_sections_dict is empty
        school_is_allowed = False
        if allowed_sections_dict:
            if str(sel_schoolbase_pk) in allowed_sections_dict or '-9' in allowed_sections_dict:
                school_is_allowed = True
        else:
            school_is_allowed = True

        sel_school = None
        if sel_examyear and sel_schoolbase_pk and school_is_allowed:
            sel_school = sch_mod.School.objects.get_or_none(
                examyear=sel_examyear,
                base_id=sel_schoolbase_pk
                )
        if logging_on:
            logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict))
            logger.debug('    school_is_allowed: ' + str(school_is_allowed))
            logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))
            logger.debug('    sel_schoolbase_pk: ' + str(sel_schoolbase_pk))

# +++ DEPARTMENT +++
        # Note: there can be multiple departments allowed,
        # but there must be a selected depbase in page studsubject

    # - get saved_depbase_pk of req_usr
        saved_depbase_pk = selected_pk_dict.get(c.KEY_SEL_DEPBASE_PK)

    # - get allowed_depbase_dict
        allowed_depbase_dict, allowed_lvlbase_pk_arr = acc_prm.get_userallowed_depbase_dict_lvlbases_pk_arr(
            allowed_schoolbase_dict, saved_depbase_pk)
        if logging_on:
            logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict))
            logger.debug('    allowed_lvlbase_pk_arr: ' + str(allowed_lvlbase_pk_arr))
            logger.debug('    sel_school: ' + str(sel_school))
            logger.debug('    sel_school.depbases: ' + str(sel_school.depbases))

    # - get array of school_allowed_depbases_arr
        sel_school_allowed_depbases_arr = []
        if sel_school:
            # - get allowed_depbases of selected school
            # sel_school_allowed_depbases_arr must always have at least 1 value
            sel_school_allowed_depbases_arr = list(
                map(int, sel_school.depbases.split(';'))) if sel_school.depbases else []
        else:
            # get all deps when skip_school_clause
            for depbase in sch_mod.Departmentbase.objects.all().values('pk'):
                sel_school_allowed_depbases_arr.append(depbase.pk)

        if logging_on:
            logger.debug('    saved_depbase_pk: ' + str(saved_depbase_pk))
            logger.debug('    sel_school_allowed_depbases_arr: ' + str(sel_school_allowed_depbases_arr))
        # sel_school_allowed_depbases_arr: [1, 2, 3]

    # - get allowed_depbases of req_usr
        # allowed_schoolbase_dict = {} when sel_schoolbase_pk is None
        allowed_schoolbase_dict, allowed_depbases_pk_arr = acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(
            allowed_sections_dict, sel_schoolbase_pk)

        if logging_on:
            logger.debug('    sel_schoolbase_pk: ' + str(sel_schoolbase_pk))
            logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))
        # allowed_schoolbase_dict: {'1': {'4': [131], '-9': [117]}, '2': {'-9': [167, 118]}, '3': {'-9': []}}

    # - get array of depbase_pk that are in requsr_allowed_depbases and school_allowed_depbases and saved_depbase_pk (if any)
        sel_depbase_pk_arr = []
        # loop through sel_school_allowed_depbases_arr
        for school_depbase_pk in sel_school_allowed_depbases_arr:
            # if saved_depbase_pk has value: filter only saved_depbase_pk
            if saved_depbase_pk is None or school_depbase_pk == saved_depbase_pk:
                # filter only allowed_depbases of user
                if not allowed_schoolbase_dict or str(school_depbase_pk) in allowed_schoolbase_dict:
                    sel_depbase_pk_arr.append(school_depbase_pk)
        if logging_on:
            logger.debug('    sel_depbase_pk_arr: ' + str(sel_depbase_pk_arr))

        dep_lvl_subj_clause_arr = []
        if sel_depbase_pk_arr:

# +++++ loop through allowed depbases +++++
            for sel_depbase_pk in sel_depbase_pk_arr:

    # - get sel_department_instance
                sel_department_instance = sch_mod.Department.objects.get_or_none(
                    examyear=sel_examyear,
                    base_id=sel_depbase_pk
                )
                if sel_department_instance:

        # - get depbase_clause
                    depbase_clause = get_depbase_clause(sel_depbase_pk)
                    if logging_on:
                        logger.debug(' .. sel_depbase_pk: ' + str(sel_depbase_pk))
                        logger.debug('    depbase_clause: ' + str(depbase_clause))
                    # depbase_clause: CONCAT(';', subj.depbases::TEXT, ';') LIKE %(depbase_pk_2)s::TEXT

        # - get allowed_lvlbases_dict
                    allowed_lvlbases_dict = get_requsr_allowed_lvlbases_dict(allowed_schoolbase_dict, sel_depbase_pk)
                    if logging_on:
                        logger.debug('    allowed_lvlbases_dict: ' + str(allowed_lvlbases_dict))
                    # allowed_lvlbases_dict: {'-9': [167, 118]}

        # - get array of allowed levels, [-9] when 'all levels'
                    level_is_required = sel_department_instance.level_req
                    sel_lvlbase_pk_arr = get_sel_lvlbase_pk_arr(allowed_lvlbases_dict, selected_pk_dict, level_is_required)

                    if logging_on:
                        logger.debug('    level_is_required: ' + str(level_is_required))
                        logger.debug('    sel_lvlbase_pk_arr: ' + str(sel_lvlbase_pk_arr) + ' ' + str(type(sel_lvlbase_pk_arr)))
                    # sel_lvlbase_pk_arr: [-9] <class 'list'>

        # get lvl_subjbase_clause
                    lvl_subjbase_clause = get_lvl_subjbase_clause(sel_lvlbase_pk_arr, allowed_lvlbases_dict, subjbase_id_fld, skip_allowedsubjbase_filter)
                    if logging_on:
                        logger.debug(' >> lvl_subjbase_clause: ' + str(lvl_subjbase_clause))
                        # lvl_subjbase_clause: ((subj.base_id IN (SELECT UNNEST(ARRAY[167, 118]::INT[]))))

            # - join depbase_clause and lvlbase_clause  and add to array, to prvent error when base_clause = None
                    dep_lvl_subj_clause = join_dep_lvl_subj_clause(depbase_clause, lvl_subjbase_clause)
                    if dep_lvl_subj_clause:
                        dep_lvl_subj_clause_arr.append(''.join(('(', dep_lvl_subj_clause, ')')))

########## end of loop through allowed depbases ########################

            # - join depbase_clause and lvlbase_clause  and add to array, to prevent error when base_clause = None
            if dep_lvl_subj_clause_arr:
                depbase_lvlbase_clause = ' OR '.join(dep_lvl_subj_clause_arr)
                if logging_on:
                    logger.debug(' >  depbase_lvlbase_clause: ' + str(depbase_lvlbase_clause))

# +++ end of loop through allowed depbases
            if dep_lvl_subj_clause_arr:
                all_depbase_lvlbase_clauses = ''.join(('(', ' OR '.join(dep_lvl_subj_clause_arr), ')'))
            else:
                all_depbase_lvlbase_clauses = "(FALSE)"
            sql_clause_arr.append(all_depbase_lvlbase_clauses)
            if logging_on:
                logger.debug('    sql_clause_arr: ' + str(sql_clause_arr))

# +++ SELECTED SECTORBASE +++
        # - get selected sctbase_pk of req_usr
        saved_sctbase_pk = selected_pk_dict.get(c.KEY_SEL_SCTBASE_PK)
        if saved_sctbase_pk and saved_sctbase_pk != -9:
            sql_clause_arr.append(''.join(("(sct.base_id = ", str(saved_sctbase_pk), "::INT)")))

        sql_clause = ' AND '.join(sql_clause_arr)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug(' >>> sql_clause: ' + str(sql_clause))
        logger.debug('--- of get_userfilter_allowed_subjbase: ')

    return sql_clause
# - end of get_userallowed_for_subjects_studsubj


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def get_depbase_clause(sel_depbase_pk):
    # PR2022-12-22
    #depbase_lookup_key = 'depbase_pk_' + str(sel_depbase_pk)
    #depbase_lookup = ''.join(('%;', str(sel_depbase_pk), ';%'))

    # PR2022-12-18 debug: this one gives error: argument formats can't be mixed:
    # depbase_clause =  ''.join(("CONCAT(';', subj.depbases::TEXT, ';') LIKE ", depbase_lookup , "::TEXT"))
    # the one with LIKE %(key)s works

    # THis one works: depbase_clause = ''.join(("CONCAT(';', subj.depbases::TEXT, ';') LIKE %(", depbase_lookup_key, ")s::TEXT"))

    # PR2022-12-21 instead of filtering on allowed_depbases, filter on dep.base_id
    depbase_clause = ''.join(("dep.base_id = ", str(sel_depbase_pk), "::INT"))

    return depbase_clause


def get_sel_lvlbase_pk_arr(allowed_lvlbases_dict, selected_pk_dict, level_is_required):
    # PR2022-12-22
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ..... get_sel_lvlbase_pk_arr .....')

# - get array of allowed levels, [-9] when 'all levels'
    sel_lvlbase_pk_arr = []
    #allowed_lvlbases_arr = []
    #if level_is_required:
    #    if allowed_lvlbases_dict:
    #        for lvlbase_pk_str in allowed_lvlbases_dict:
    #            allowed_lvlbases_arr.append(int(lvlbase_pk_str))
    #if not allowed_lvlbases_arr:
    #    allowed_lvlbases_arr.append(-9)
    # if logging_on:
    #    logger.debug('    allowed_lvlbases_arr: ' + str(allowed_lvlbases_arr))
    # allowed_lvlbases_arr: [-9]

    # - sel_lvlbase_pk_arr contains the selected lvlbase or all allowed lvlbasescreate array of allowed depbases of requsr from allowed_depbases_dict and sel_school_allowed_depbases_arr

    if level_is_required:

# - get saved_lvlbase_pk of req_usr
        saved_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)
        if logging_on:
            logger.debug('    saved_lvlbase_pk: ' + str(saved_lvlbase_pk) + ' ' + str(type(saved_lvlbase_pk)))
            logger.debug('    allowed_lvlbases_dict: ' + str(allowed_lvlbases_dict) + ' ' + str(type(allowed_lvlbases_dict)))

# - filter only the saved_lvlbase_pk if exists and allowed
        if saved_lvlbase_pk and allowed_lvlbases_dict and str(saved_lvlbase_pk) in allowed_lvlbases_dict:

            sel_lvlbase_pk_arr.append(saved_lvlbase_pk)
            if logging_on:
                logger.debug('  ???  saved_lvlbase_pk: ' + str(saved_lvlbase_pk) + ' ' + str(type(saved_lvlbase_pk)))
                logger.debug('  ???  sel_lvlbase_pk_arr: ' + str(sel_lvlbase_pk_arr) + ' ' + str(type(sel_lvlbase_pk_arr)))

        else:
            if logging_on:
                logger.debug('    else allowed_lvlbases_dict: ' + str(allowed_lvlbases_dict) + ' ' + str(type(allowed_lvlbases_dict)))
# - filter all allowed lvlbases
            if allowed_lvlbases_dict:
                for sel_lvlbase_pk_str in allowed_lvlbases_dict:
                    if logging_on:
                        logger.debug('    else sel_lvlbase_pk_str: ' + str(sel_lvlbase_pk_str) + ' ' + str(type(sel_lvlbase_pk_str)))
                    sel_lvlbase_pk_arr.append(int(sel_lvlbase_pk_str))
    else:
        sel_lvlbase_pk_arr.append(-9)

    if logging_on:
        logger.debug('    sel_lvlbase_pk_arr: ' + str(sel_lvlbase_pk_arr) + ' ' + str(type(sel_lvlbase_pk_arr)))

    return sel_lvlbase_pk_arr
# end of get_sel_lvlbase_pk_arr


def get_lvl_subjbase_clause(sel_lvlbase_pk_arr, allowed_lvlbases_dict, subjbase_id_fld, skip_allowedsubjbase_filter):
    # PR2022-12-22
    logging_on = s.LOGGING_ON
    lvl_subjbase_clause = None

    if sel_lvlbase_pk_arr:
        lvl_subjbase_clause_arr = []

# +++++ loop through sel_lvlbase_pk_arr
        for sel_lvlbase_pk in sel_lvlbase_pk_arr:

            # - create lvlbase_clause
            if sel_lvlbase_pk == -9:
                lvlbase_clause = None
            else:
                lvlbase_id_fld = 'lvl.base_id'
                lvlbase_clause = ''.join((lvlbase_id_fld, " = ", str(sel_lvlbase_pk), "::INT"))

            # - create subjbase_clause
            subjbase_clause = None
            subjbase_pk_arr = allowed_lvlbases_dict.get(str(sel_lvlbase_pk))
            if subjbase_pk_arr and not skip_allowedsubjbase_filter:
                if len(subjbase_pk_arr) == 1:
                    subjbase_clause = ''.join((subjbase_id_fld, " = ", str(subjbase_pk_arr[0]), "::INT"))
                else:
                    subjbase_clause = ''.join(
                        (subjbase_id_fld, " IN (SELECT UNNEST(ARRAY", str(subjbase_pk_arr), "::INT[]))"))
            # subjbase_clause: subj.base_id IN (SELECT UNNEST(ARRAY[167, 118]::INT[]))

    # - join depbase_clause and lvlbase_clause  and add to array, to prvent error when base_clause = None
            lvl_subjbase = None
            if lvlbase_clause:
                if subjbase_clause:
                    lvl_subjbase = ' AND '.join((lvlbase_clause, subjbase_clause))
                else:
                    lvl_subjbase = lvlbase_clause
            else:
                if subjbase_clause:
                    lvl_subjbase = subjbase_clause

            if lvl_subjbase:
                lvl_subjbase_clause_arr.append(''.join(('(', lvl_subjbase, ')')))
            # lvl_subjbase: subj.base_id IN (SELECT UNNEST(ARRAY[167, 118]::INT[]))

# +++++ end of loop through sel_lvlbase_pk_arr
        # lvl_subjbase_clause_arr: ['(subj.base_id IN (SELECT UNNEST(ARRAY[167, 118]::INT[])))']

        # join lvl_subjbase_clause_arr
        if lvl_subjbase_clause_arr:
            lvl_subjbase_clause = ''.join(('(', ' OR '.join(lvl_subjbase_clause_arr), ')'))

    return lvl_subjbase_clause


def join_dep_lvl_subj_clause(depbase_clause, lvl_subjbase_clause):
    # PR2022-12-22
    # - join depbase_clause and lvlbase_clause  and add to array, to prvent error when base_clause = None
    dep_lvl_subj_clause = None
    if depbase_clause:
        if lvl_subjbase_clause:
            dep_lvl_subj_clause = ' AND '.join((depbase_clause, lvl_subjbase_clause))
        else:
            dep_lvl_subj_clause = depbase_clause
    else:
        if lvl_subjbase_clause:
            dep_lvl_subj_clause = lvl_subjbase_clause
    return dep_lvl_subj_clause

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

""" NIU 
def get_userfilter_allowed_school_dep_lvl_sct(request, table=None):
    # PR2022-12-15
    # this function adds selected / allowed  filter to sql
    # called by downloads.create_student_rows

    req_usr = request.user

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' +++++ get_userfilter_allowed_school_dep_lvl_sct +++++ ')

    sql_clause = ""
    sql_clause_arr = []

# - get sel_examyear_instance
    sel_examyear_instance = get_selected_examyear_from_usersetting_short(request)

# - get allowed_sections_dict from userallowed
    allowed_sections_dict = acc_prm.get_userallowed_sections_dict_from_request(request)

# - get selected_pk_dict from usersettings
    selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)

# +++ SCHOOL +++
    sel_school, sel_schoolbase_pk, schoolbase_clause = get_sql_schoolbase_clause(req_usr, sel_examyear_instance, allowed_sections_dict, selected_pk_dict)
    sql_clause_arr.append(schoolbase_clause)
    if logging_on:
        logger.debug('    schoolbase_clause: ' + str(schoolbase_clause))
    if sel_school:

# +++ DEPARTMENT +++
        allowed_schoolbase_dict, allowed_depbases_pk_arr = acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(
                allowed_sections_dict, sel_schoolbase_pk)
        sel_department_instance, sel_depbase_pk, depbase_clause = get_sql_depbase_clause(sel_examyear_instance, sel_school, allowed_schoolbase_dict, selected_pk_dict)
        sql_clause_arr.append(depbase_clause)
        if logging_on:
            logger.debug('    depbase_clause: ' + str(depbase_clause))
        if sel_department_instance:

# +++ LEVEL +++
            allowed_lvlbases_dict = get_requsr_allowed_lvlbases_dict(allowed_schoolbase_dict, sel_depbase_pk)
            level_is_required = sel_department_instance.level_req
            sql_levelbases_clause = get_sql_levelbases_clause(req_usr, level_is_required, allowed_lvlbases_dict, selected_pk_dict)
            if sql_levelbases_clause:
                sql_clause_arr.append(sql_levelbases_clause)
            if logging_on:
                logger.debug('    sql_levelbases_clause: ' + str(sql_levelbases_clause))

# +++ SELECTED SECTORBASE +++
            # - get selected sctbase_pk of req_usr
            saved_sctbase_pk = selected_pk_dict.get(c.KEY_SEL_SCTBASE_PK)
            sql_sctbases_clause = ''.join(("(sct.base_id = ", str(saved_sctbase_pk), "::INT)")) if saved_sctbase_pk else None
            if sql_sctbases_clause:
                sql_clause_arr.append(sql_sctbases_clause)
            if logging_on:
                logger.debug('    sql_sctbases_clause: ' + str(sql_sctbases_clause))

    if sql_clause_arr:
        sql_clause ='AND ' + ' AND '.join(sql_clause_arr)

    if logging_on:
        logger.debug('    sql_clause: ' + str(sql_clause))
        logger.debug('--- end of get_userfilter_allowed_subjbase: ')

    return sql_clause
# - end of get_userfilter_allowed_school_dep_lvl_sct


def get_sql_levelbases_clause(req_usr, level_is_required, allowed_lvlbases_dict, selected_pk_dict):
    # PR2022-12-15
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_sql_levelbases_clause ----- ')
        logger.debug('    level_is_required: ' + str(level_is_required))
        logger.debug('    allowed_lvlbases_dict: ' + str(allowed_lvlbases_dict))
        logger.debug('    selected_pk_dict: ' + str(selected_pk_dict))

    sql_levelbases_clause = None

    try:
    # - get allowed_lvlbases_dict
        # allowed_lvlbases_dict: {'5': [123]}

    # - sel_lvlbase_pk_arr contains the selected lvlbase or all allowed lvlbasescreate array of allowed depbases of requsr from allowed_depbases_dict and sel_school_allowed_depbases_arr
        sel_lvlbase_pk_arr = []
        sql_levelbases_clause = None

        if level_is_required:

    # - get saved_lvlbase_pk of req_usr
            saved_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)
            if logging_on:
                logger.debug('    saved_lvlbase_pk: ' + str(saved_lvlbase_pk) + ' ' + str(type(saved_lvlbase_pk)))

    # - filter only the saved_lvlbase_pk if exists and allowed
            if saved_lvlbase_pk:
                if str(saved_lvlbase_pk) in allowed_lvlbases_dict or \
                        '-9' in allowed_lvlbases_dict:
                    sel_lvlbase_pk_arr.append(saved_lvlbase_pk)
            else:
    # - filter all allowed lvlbases
                if allowed_lvlbases_dict:
                    for sel_lvlbase_pk_str in allowed_lvlbases_dict:
                        sel_lvlbase_pk_arr.append(int(sel_lvlbase_pk_str))

        else:
            # add '-9' when lvl not required (allowedsubjects are stored in lvl '-9'
            sel_lvlbase_pk_arr.append(-9)

        if logging_on:
            logger.debug('    sel_lvlbase_pk_arr: ' + str(sel_lvlbase_pk_arr) + ' ' + str(type(sel_lvlbase_pk_arr)))

# +++ loop through selected levels +++
        levelbases_clause_arr = []
        if sel_lvlbase_pk_arr:
            for sel_lvlbase_pk in sel_lvlbase_pk_arr:

                allowed_subjbases_arr = get_requsr_allowed_subjbases_arr(allowed_lvlbases_dict, sel_lvlbase_pk)
                if logging_on:
                    logger.debug('   +++++ ')
                    logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
                    logger.debug('    allowed_subjbases_arr: ' + str(allowed_subjbases_arr) + ' ' + str(type(allowed_subjbases_arr)))
                    # allowed_subjbase_pk_arr: [123] <class 'list'>

                len_allowed_subjbases_arr = len(allowed_subjbases_arr)

    # - create lvlbase_clause
                lvlbase_clause = None
                if sel_lvlbase_pk == -9:
                    pass
                elif len_allowed_subjbases_arr == 0 and req_usr.role == c.ROLE_016_CORR:
                    # when corrector: must have allowd_subjects, 'all' is not allowed
                    pass
                else:
                    # - when not corrector: show allowed subjects or all subjects when allowed_subjbases_arr is empty
                    lvlbase_clause = ''.join(("lvl.base_id = ", str(sel_lvlbase_pk), "::INT"))

                if lvlbase_clause:
                    levelbases_clause_arr.append(lvlbase_clause)

    # - join lvlbase_clause and subjbase_clause


    # +++ end of loop through levels
        if levelbases_clause_arr:
            sql_levelbases_clause = ''.join(('(', ' OR '.join(levelbases_clause_arr), ')'))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('    sql_levelbases_clause: ' + str(sql_levelbases_clause))

    return sql_levelbases_clause

# - end of get_sql_levelbases_clause


"""

def get_sql_schoolbase_clause(req_usr, sel_examyear_instance, allowed_sections_dict, selected_pk_dict):
    # PR2022-12-15
    # - get selected school
    # - when role = school: selected school = req_usr.schoolbase
    # - otherwise: get selected school from settings
    # - if None: don't return records

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_sql_schoolbase_clause ----- ')
        if logging_on:
            logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict))

    sel_schoolbase_pk = None
    if req_usr.role == c.ROLE_008_SCHOOL:
        if req_usr.schoolbase:
            sel_schoolbase_pk = req_usr.schoolbase_id
    else:
        # - check if schoolbase is allowed
        # when allowed_sections_dict is empty: selected school is always allowed
        saved_schoolbase_pk = selected_pk_dict.get(c.KEY_SEL_SCHOOLBASE_PK)
        if logging_on:
            logger.debug('    saved_schoolbase_pk: ' + str(saved_schoolbase_pk))
        if saved_schoolbase_pk:
            if allowed_sections_dict:
                if str(saved_schoolbase_pk) in allowed_sections_dict or '-9' in allowed_sections_dict:
                    sel_schoolbase_pk = saved_schoolbase_pk
            else:
                sel_schoolbase_pk = saved_schoolbase_pk

    if logging_on:
        logger.debug('    sel_schoolbase_pk: ' + str(sel_schoolbase_pk))

    sel_school = None
    if sel_examyear_instance and sel_schoolbase_pk:
        sel_school = sch_mod.School.objects.get_or_none(
            examyear=sel_examyear_instance,
            base_id=sel_schoolbase_pk
        )

    schoolbase_clause = ''.join(("(school.base_id = ", str(sel_schoolbase_pk), "::INT)")) if sel_school else "(FALSE)"

    if logging_on:
        logger.debug('    schoolbase_clause: ' + str(schoolbase_clause))
    return sel_school, sel_schoolbase_pk, schoolbase_clause
# - end of get_sql_schoolbase_clause


def get_sql_depbase_clause(sel_examyear_instance, sel_school, allowed_depbases_dict, selected_pk_dict):
    # PR2022-12-15 PR2023-01-06
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_sql_depbase_clause ----- ')

    sel_depbase_pk = None

# - get allowed_depbases of selected school
    # sel_school_allowed_depbases_arr must always have at least 1 value
    sel_school_allowed_depbases_arr = list(
        map(int, sel_school.depbases.split(';'))) if sel_school.depbases else []
    if logging_on:
        logger.debug('    sel_school_allowed_depbases_arr: ' + str(sel_school_allowed_depbases_arr) + ' ' + str(
            type(sel_school_allowed_depbases_arr)))
        # sel_school_allowed_depbases_arr: [1] <class 'list'>

    # - use depbase of selected school when school has only 1 department (is always allowed when school has only 1 dep)
    if len(sel_school_allowed_depbases_arr) == 1:
        sel_depbase_pk = sel_school_allowed_depbases_arr[0]
    else:

# - get saved_depbase_pk of req_usr
        saved_depbase_pk = selected_pk_dict.get(c.KEY_SEL_DEPBASE_PK)
        if logging_on:
            logger.debug('    saved_depbase_pk: ' + str(saved_depbase_pk) + ' ' + str(type(saved_depbase_pk)))

        if saved_depbase_pk:
            if saved_depbase_pk in sel_school_allowed_depbases_arr:
                if allowed_depbases_dict and  str(saved_depbase_pk) in allowed_depbases_dict or not allowed_depbases_dict:
                    sel_depbase_pk = saved_depbase_pk

    if logging_on:
        logger.debug('    sel_depbase_pk: ' + str(sel_depbase_pk) + ' ' + str(type(sel_depbase_pk)))

    sel_department_instance = sch_mod.Department.objects.get_or_none(
        examyear=sel_examyear_instance,
        base_id=sel_depbase_pk
    )

    depbase_clause = ''.join(("(dep.base_id = ", str(sel_depbase_pk), "::INT)")) if sel_department_instance else "(FALSE)"

    if logging_on:
        logger.debug('    depbase_clause: ' + str(depbase_clause))

    return sel_department_instance, sel_depbase_pk, depbase_clause
# - end of get_sql_depbase_clause



def get_permit_crud(page, request):
    # --- get crud permit for page # PR2022-08-07
    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug(' ----- get_permit_crud ----- ')

    has_permit = False
    if request.user and request.user.country and request.user.schoolbase:
        permit_list = request.user.permit_list(page)
        if permit_list:
            has_permit = 'permit_crud' in permit_list

        if logging_on:
            logger.debug('permit_list: ' + str(permit_list))
            logger.debug('has_permit: ' + str(has_permit))

    return has_permit
# - end of get_permit_crud


def check_schoolbase_allowed(schoolbase_instance, request):
    # - check if requsr_schoolbase is in allowed_sections, set None if not found PR2022-0=12-05
    schoolbase_is_allowed = False
    if schoolbase_instance:
        usergroups_arrNIU, allowed_sections_dict, allowed_clusters_arrNIU = get_request_userallowed(request)
        if allowed_sections_dict:
            requsr_schoolbase_pk_str = str(schoolbase_instance.pk)
            # schoolbase is also allowed when 'all' (-9) in allowed_sections_dict
            if requsr_schoolbase_pk_str in allowed_sections_dict or '-9' in allowed_sections_dict:
                schoolbase_is_allowed = True
        else:
            # schoolbase is also allowed when allowed_sections_dict is empty
            schoolbase_is_allowed = True
    return schoolbase_is_allowed


def get_request_userallowed(request):  # PR2022-12-04
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('---  get_request_userallowed  ------- ')

# - get selected examyear
    sel_examyear, examyear_save_NIU, multiple_examyears_exist = af.get_sel_examyear_with_default(request)

    allowed_sections_dict, usergroups_arr, allowed_clusters_arr = get_requsr_usergroups_allowedsections_allowedclusters(request, sel_examyear)

    if logging_on:
        logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict))

    return usergroups_arr, allowed_sections_dict, allowed_clusters_arr


def get_requsr_allowed_lvlbases_dict(allowed_depbase_dict, sel_lvlbase_pk):
    # PR2022-12-10 PR2023-01-09
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---  get_requsr_allowed_lvlbases_dict  ------- ')
        logger.debug('    allowed_depbase_dict:      ' + str(allowed_depbase_dict))
        logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))

    allowed_lvlbase_dict = {}
    if allowed_depbase_dict and sel_lvlbase_pk:
        sel_lvlbase_pk_str = str(sel_lvlbase_pk)
        if sel_lvlbase_pk_str in allowed_depbase_dict:
            allowed_lvlbase_dict = allowed_depbase_dict.get(sel_lvlbase_pk_str) or {}

    if logging_on:
        logger.debug('    allowed_lvlbase_dict: ' + str(allowed_lvlbase_dict))


    return allowed_lvlbase_dict
# - end of get_requsr_allowed_lvlbases_dict


def get_requsr_usergroups_allowedsections_allowedclusters (request, sel_examyear):  # PR2022-12-11 PR2023-01-07
    # function gets setting in first row that matches the filter
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('---  get_requsr_usergroups_allowedsections_allowedclusters  ------- ')
        logger.debug('    request.user:      ' + str(request.user))
        logger.debug('    sel_examyear:      ' + str(sel_examyear))

    #  json.dumps converts a dict to a json object
    #  json.loads retrieves a dict (or other type) from a json string
    #  json.load deserialize file

    allowed_sections_dict = {}
    usergroups_arr = []
    allowed_clusters_arr = []
    try:
        if request.user and sel_examyear:
            userallowed = acc_mod.UserAllowed.objects.filter(
                user=request.user,
                examyear=sel_examyear,
            ).order_by('id').first()

            if userallowed:
                allowed_sections_str = getattr(userallowed, 'allowed_sections')
                if allowed_sections_str:
                    allowed_sections_dict = json.loads(allowed_sections_str)

                usergroups_str = getattr(userallowed, 'usergroups')
                if usergroups_str:
                    usergroups_arr = json.loads(usergroups_str)

                allowed_clusters_str = getattr(userallowed, 'allowed_clusters')
                if allowed_clusters_str:
                    allowed_clusters_arr = json.loads(allowed_clusters_str)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return allowed_sections_dict, usergroups_arr, allowed_clusters_arr
# - end of get_requsr_usergroups_allowedsections_allowedclusters


def set_userallowed_dict(user_pk, examyear_pk, usergroups_arr, allowed_clusters_arr, allowed_sections_dict):  # PR2022-12-02
    # function saves setting in first row that matches the filter, adds new row when not found
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('---  set_userallowed_dict  ------- ')
        logger.debug('    user_pk:      ' + str(user_pk))
        logger.debug('    usergroups_arr:      ' + str(usergroups_arr))
        logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict))

    #  json.dumps converts a dict to a json object
    #  json.loads retrieves a dict (or other type) from a json object
    is_added = False
    try:
        if user_pk and examyear_pk:
            allowed_sections_str = json.dumps(allowed_sections_dict) if allowed_sections_dict else None
            usergroups_str = json.dumps(usergroups_arr) if usergroups_arr else None
            allowed_clusters_str = json.dumps(allowed_clusters_arr) if allowed_clusters_arr else None

            row = acc_mod.UserAllowed.objects.filter(
                user_id=user_pk,
                examyear_id=examyear_pk
            ).order_by('id').first()

            if row:
                setattr(row, 'usergroups', usergroups_str)
                setattr(row, 'allowed_clusters', allowed_clusters_str)
                setattr(row, 'allowed_sections', allowed_sections_str)

            else:
                # don't add row when setting has no value
                # note: empty setting_dict {} = False, empty json "{}" = True, therefore check if setting_dict is empty

                row = acc_mod.UserAllowed(
                    user_id=user_pk,
                    examyear_id=examyear_pk,
                    usergroups=usergroups_str,
                    allowed_clusters=allowed_clusters_str,
                    allowed_sections=allowed_sections_str
                )
            row.save()
        is_added = True
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
    return is_added
# - end of set_userallowed_dict



############## get selected ###############################

############## moved frnm downloads 2022-12-18 ###########################

# ===== PAGE SETTINGS =======================
def get_settings_page(request, request_item_setting, page, setting_dict):
    # PR2021-06-22 PR2022-02-25 PR2022-12-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_settings_page -------')

# settings 'sel_btn' can be changed by calling download, also changes by b_UploadSettings
# settings 'cols_hidden' cannot be changed by calling downloads function
# value of key 'sel_page' is set and retrieved in get_headerbar_param

    if logging_on:
        logger.debug('++++++++++++  PAGE SETTINGS  ++++++++++++++++++++++++')
        logger.debug('..... page: ' + str(page))

        # request_item_setting: {'page': 'page_exams', 'page_exams': {'sel_btn': 'btn_ntermen'}}

    # get page settings from usersetting
    if page:
        # get new page settings from request_item_setting
        reqitem_page_dict = request_item_setting.get(page)
        reqitem_sel_btn, saved_sel_btn = None, None
        if reqitem_page_dict:
            reqitem_sel_btn = reqitem_page_dict.get('sel_btn')
        # get saved page settings from usersetting
        saved_page_dict = acc_prm.get_usersetting_dict(page, request)
        if saved_page_dict is None:
            saved_page_dict = {}
        else:
    # - get saved_sel_btn from  usersetting
            saved_sel_btn = saved_page_dict.get(c.KEY_SEL_BTN)

        # page_dict: {'sel_btn': 'btn_studsubj', 'cols_hidden': {'published': ['examperiod'], 'studsubj': ['examnumber']}}
        if logging_on:
            logger.debug('..... reqitem_page_dict: ' + str(reqitem_page_dict))
            logger.debug('..... reqitem_sel_btn: ' + str(reqitem_sel_btn))
            logger.debug('..... saved_page_dict: ' + str(saved_page_dict))
            logger.debug('..... saved_sel_btn: ' + str(saved_sel_btn))
            # saved_page_dict: {'sel_btn': 'btn_ntermen'}

    # - replace by reqitem_sel_btn, if any
        if reqitem_sel_btn and reqitem_sel_btn != saved_sel_btn:
            saved_sel_btn = reqitem_sel_btn
            saved_page_dict[c.KEY_SEL_BTN] = reqitem_sel_btn

    # - save reqitem_sel_btn, if changed
            set_usersetting_dict(page, saved_page_dict, request)

        if logging_on:
            logger.debug('..... saved_sel_btn: ' + str(saved_sel_btn))

# - add info to setting_dict, will be sent back to client
        if saved_sel_btn:
            setting_dict[c.KEY_SEL_BTN] = saved_sel_btn

# - add list of hidden columns PR2021-07-07 - cols_hidden cannot be changed by calling downloads function
        cols_hidden = saved_page_dict.get(c.KEY_COLS_HIDDEN)
        if cols_hidden:
            setting_dict[c.KEY_COLS_HIDDEN] = cols_hidden
# - end of get_settings_page


# ===== COUNTRY =======================
def get_settings_country(request, permit_dict):
    # - get country from req_usr PR2022-12-10
    if request.user.country:
        permit_dict['requsr_country_pk'] = request.user.country.pk
        permit_dict['requsr_country'] = request.user.country.name
        # set locked=True if country is locked or country is None
        permit_dict['requsr_country_locked'] = request.user.country.locked
# - end of get_settings_country


# ===== EXAMYEAR =======================
def get_settings_examyear(request, request_item_setting, page, permit_dict, setting_dict, selected_pk_dict, msg_list):
    # PR2022-12-10 PR2023-01-24
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_settings_examyear -------')

# - get selected examyear:
    # - check if there is a new examyear_pk in request_setting, check if request_examyear exists
    # - if None: get saved_examyear_pk from Usersetting, check if saved_examyear exists
    # - if None: get today's examyear
    # - if None: get latest examyear_int of table
    # this comes before get permit_list, rest of examyear is done further in this def
    sel_examyear_instance, sel_examyear_tobesaved, multiple_examyears_exist = \
        af.get_sel_examyear_with_default(
            request=request,
            request_item_examyear_pk=request_item_setting.get(c.KEY_SEL_EXAMYEAR_PK)
        )

    # every user can change examyear, may_select_examyear is False when there is only 1 allowed examyear PR2023-01-08
    permit_dict['may_select_examyear'] = multiple_examyears_exist

    if logging_on:
        logger.debug('    sel_examyear_instance: ' + str(sel_examyear_instance) + ' pk: ' + str(sel_examyear_instance.pk))

    reset_examperiod = False

# - update selected_pk_dict when selected_pk_dict_has_changed, will be saved at end of def
    if sel_examyear_tobesaved:
        # sel_examyear_instance has always value when selected_pk_dict_has_changed
        selected_pk_dict[c.KEY_SEL_EXAMYEAR_PK] = sel_examyear_instance.pk

        # PR2022-08-23 Roland Guribadi Lauffer: cannot find upload subject btn. Reason: tab was not set to first exam period
        # to prevent this: reset examperiod to 1st when changing examyear
        reset_examperiod = True

# - add info to setting_dict, will be sent back to client
    if sel_examyear_instance:
        setting_dict[c.KEY_SEL_EXAMYEAR_PK] = sel_examyear_instance.pk
        # sel_country_is_sxm is only used in page studsubj show_thumbrule = (setting_dict.sel_country_is_sxm || setting_dict.sel_depbase_code !== "Vsbo");
        setting_dict['sel_country_is_sxm'] = (sel_examyear_instance.country.abbrev == 'Sxm')

        setting_dict['sel_examyear_code'] = sel_examyear_instance.code if sel_examyear_instance.code else None
        setting_dict['sel_examyear_thumbrule_allowed'] = sel_examyear_instance.thumbrule_allowed
        if not sel_examyear_instance.published:
            permit_dict['examyear_not_published'] = True

# - add message when school is not published PR2021-12-04
            # not when role is admin PR2022-08-09
            if request.user.role < c.ROLE_064_ADMIN:
                msg_list.append({'msg_html': [
                    '<br>'.join((str(_("%(admin)s has not yet published examyear %(exyr)s.") % \
                                                     {'admin': _('The Division of Examinations'), 'exyr': str(sel_examyear_instance.code)}),
                                 str(_('You cannot enter data.'))))
                ], 'class': 'border_bg_warning'})

        if sel_examyear_instance.locked:
            permit_dict['examyear_locked'] = True

# - add message when examyear is locked PR22021-12-04
            # not when page_examyear PR2022-08-09
            if request.user.role != c.ROLE_064_ADMIN or page != 'page_examyear':
                msg_list.append({'msg_html': [
                    '<br>'.join((str(_('Exam year %(exyr)s is locked.') % {'exyr': str(sel_examyear_instance.code)}),
                                 str(_('You cannot make changes.'))))
                ], 'class': 'border_bg_warning'})

        if sel_examyear_instance.no_practexam:
            setting_dict['no_practexam'] = sel_examyear_instance.no_practexam
        if sel_examyear_instance.sr_allowed:
            setting_dict['sr_allowed'] = sel_examyear_instance.sr_allowed
        if sel_examyear_instance.no_centralexam:
            setting_dict['no_centralexam'] = sel_examyear_instance.no_centralexam
        if sel_examyear_instance.no_thirdperiod:
            setting_dict['no_thirdperiod'] = sel_examyear_instance.no_thirdperiod

# - add message when examyear is different from this examyear
        message = message_diff_exyr(request, sel_examyear_instance)
        if message:
            msg_list.append(message)

    return sel_examyear_instance, sel_examyear_tobesaved, reset_examperiod
# - end of get_settings_examyear


# ===== SCHOOLBASE ======================= PR2020-12-18 PR2022-12-10
def get_settings_schoolbase(request, request_item_setting, sel_examyear_instance, allowed_sections_dict, page,
                            permit_dict, setting_dict, selected_pk_dict, msg_list):
    # PR2022-12-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_settings_schoolbase -------')

    # - get schoolbase from settings / request when role is corr, insp, admin or system, from req_usr when role is school
    # req_usr.schoolbase cannot be changed
    # Selected schoolbase is stored in {selected_pk: {sel_schoolbase_pk: val}}.
    # Note: key 'selected_pk' is not used in request_item, format is: datalist_request: {'setting': {'page': 'page_studsubj', 'sel_lvlbase_pk': 14}}

# - get requsr_schoolbase
    requsr_schoolbase = request.user.schoolbase
    permit_dict['requsr_schoolbase_pk'] = requsr_schoolbase.pk if requsr_schoolbase else None
    permit_dict['requsr_schoolbase_code'] = requsr_schoolbase.code if requsr_schoolbase else None

# - get sel_schoolbase_instance
    # - when role = school: sel_schoolbase = requsr_schoolbase
    # - else[ check if request_item_schoolbase_pk exists: check if is allowed
    # - if requestitem_saved schoolbase is None or not allowed: check if saved schoolbase exists and is allowed
    # - if saved schoolbase is None or not allowed: use requsr_schoolbase

    sel_schoolbase_instance, sel_schoolbase_tobesaved = \
        get_sel_schoolbase_instance(
            request=request,
            request_item_schoolbase_pk=request_item_setting.get(c.KEY_SEL_SCHOOLBASE_PK),
            allowed_sections_dict=allowed_sections_dict
        )
    if sel_schoolbase_tobesaved:
        # when sel_schoolbase_tobesaved=True, there is always a sel_schoolbase_instance
        selected_pk_dict[c.KEY_SEL_SCHOOLBASE_PK] = sel_schoolbase_instance.pk

    if sel_schoolbase_instance:
        setting_dict[c.KEY_SEL_SCHOOLBASE_PK] = sel_schoolbase_instance.pk
        setting_dict['sel_schoolbase_code'] = sel_schoolbase_instance.code

    # requsr_same_school = True when requsr.role = school and selected school is same as requsr_school PR2021-04-27
    # used on entering grades. Users can only enter grades of their own school. Syst, Adm and Insp, Corrector can not neter grades
    requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and
                          sel_schoolbase_instance and requsr_schoolbase.pk == sel_schoolbase_instance.pk)
    permit_dict['requsr_same_school'] = requsr_same_school
    # this one is used in create_studentsubject_rows and create_grade_rows, to block view of non-submitted subjects and grades
    setting_dict['requsr_same_school'] = requsr_same_school

# ===== SCHOOL =======================
    # - only roles corr, insp, admin and system may select other schools
    # these are use in b_UpdateHeaderbar
    may_select_school = (request.user.role > c.ROLE_008_SCHOOL)
    permit_dict['may_select_school'] = may_select_school

    if page in ('page_examyear', 'page_user'):
        display_school = (request.user.role <= c.ROLE_008_SCHOOL)
    else:
        display_school = True
    permit_dict['display_school'] = display_school

# - get school from sel_schoolbase and sel_examyear_instance
    sel_school_instance = sch_mod.School.objects.get_or_none(
        base=sel_schoolbase_instance,
        examyear=sel_examyear_instance)
    if logging_on:
        logger.debug('    sel_school_instance: ' + str(sel_school_instance) + ' pk: ' + str(sel_school_instance.pk))

    if sel_school_instance:
        setting_dict['sel_school_pk'] = sel_school_instance.pk
        setting_dict['sel_school_name'] = sel_school_instance.name
        setting_dict['sel_school_abbrev'] = sel_school_instance.abbrev
        setting_dict['sel_school_depbases'] = sel_school_instance.depbases

        if sel_school_instance.isdayschool:
            setting_dict['sel_school_isdayschool'] = True
        if sel_school_instance.iseveningschool:
            setting_dict['sel_school_iseveningschool'] = True
        if sel_school_instance.islexschool:
            setting_dict['sel_school_islexschool'] = True

# - add message when school is locked PR2021-12-04
        if sel_school_instance.locked:
            setting_dict['sel_school_locked'] = True
            msg_list.append({'msg_html': [
                '<br>'.join((str(_('Exam year %(exyr)s of this school is locked.') % {
                    'exyr': str(sel_school_instance.examyear.code)}),
                             str(_('You cannot make changes.'))))], 'class': 'border_bg_warning'})

    return sel_schoolbase_instance, sel_schoolbase_tobesaved, sel_school_instance
# - end of get_settings_schoolbase


# ===== DEPARTMENTBASE ======================= PR2022-12-10
def get_settings_departmentbase(request, request_item_setting, sel_examyear_instance, sel_schoolbase_instance, sel_school_instance,
                                allowed_schoolbase_dict, page, permit_dict, setting_dict, selected_pk_dict, msg_list):
    # PR2022-12-10  PR2023-01-08
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_settings_departmentbase -------')

    # every user can change depbase, if in .sel_school_depbases and in user_allowed if existst
# - get sel_depbase_instance
    #   - check if request_item_depbase_pk is allowed and exists
    #   - if not exists and not 'all_allowed': check if saved depbase is allowed and exists
    #   - if not exists and not 'all_allowed': get first available depbase that is allowed

    request_item_depbase_pk = request_item_setting.get(c.KEY_SEL_DEPBASE_PK)

    sel_depbase_instance, sel_depbase_tobesaved, allowed_schoolbase_dict, allowed_depbases_arr = \
        get_sel_depbase_instance(
                sel_school_instance=sel_school_instance,
                page=page,
                request=request,
                request_item_depbase_pk=request_item_depbase_pk,
                allowed_schoolbase_dict=allowed_schoolbase_dict
            )
    if logging_on:
        logger.debug('    sel_depbase_instance: ' + str(sel_depbase_instance))
        logger.debug('    sel_depbase_tobesaved: ' + str(sel_depbase_tobesaved))
        logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))
        logger.debug('    allowed_depbases_arr: ' + str(allowed_depbases_arr))

    # every user can change examyear, may_select_examyear is False when there is only 1 allowed examyear PR2023-01-08
    # permit_dict['may_select_department'] = True


    permit_dict['allowed_depbases'] = allowed_depbases_arr
    allowed_depbases_len = len(allowed_depbases_arr)
    # Note: set may_select_department also in ExamyearListView
    # in page exam: ETE may_select_department
    may_select_department = False
    if page == 'page_examyear':
        pass
    elif page == 'page_exams' and request.user.role >= c.ROLE_064_ADMIN:
        may_select_department = True
    else:
        may_select_department = allowed_depbases_len > 1

    permit_dict['may_select_department'] = may_select_department
    permit_dict['display_department'] = (page not in ('page_examyear', 'page_user'))

    # NIU, I think PR2022-12-11
    # get_sel_depbase_instance has already filter requser_allowed_databases
    # now remove depbases from requser_allowed_databases when not in allowed_databases
    # requsr_allowed_depbases = permit_dict.get('requsr_allowed_depbases')
    # if allowed_depbases_arr and requsr_allowed_depbases:
    #     new_arr = []
    #     for item in requsr_allowed_depbases:
    #         if item in allowed_depbases_arr:
    #             new_arr.append(item)
    #     if new_arr:
    #         permit_dict['requsr_allowed_depbases'] = new_arr
    #     else:
    #         permit_dict.pop('requsr_allowed_depbases')

    # if logging_on:
    #     logger.debug('    allowed_depbases_arr: ' + str(allowed_depbases_arr))
    #     logger.debug('    may_select_department: ' + str(may_select_department))
    #     logger.debug('    permit_dict[display_department]: ' + str(permit_dict['display_department']))

# - update selected_pk_dict when selected_pk_dict_has_changed, will be saved at end of def
    if sel_depbase_tobesaved:
        # sel_depbase_instance has always value when sel_depbase_tobesaved = True
        selected_pk_dict[c.KEY_SEL_DEPBASE_PK] = sel_depbase_instance.pk

# - add info to setting_dict, will be sent back to client
    sel_department_instance = None
    if sel_depbase_instance:
        setting_dict[c.KEY_SEL_DEPBASE_PK] = sel_depbase_instance.pk
        setting_dict['sel_depbase_code'] = sel_depbase_instance.code if sel_depbase_instance.code else None

        sel_department_instance = sch_mod.Department.objects.get_or_none(base=sel_depbase_instance,
                                                                         examyear=sel_examyear_instance)
        if sel_department_instance:
            setting_dict['sel_department_pk'] = sel_department_instance.pk
            # setting_dict['sel_department_abbrev'] = sel_department_instance.abbrev
            # setting_dict['sel_department_name'] = sel_department_instance.name
            setting_dict['sel_dep_level_req'] = sel_department_instance.level_req
            setting_dict['sel_dep_has_profiel'] = sel_department_instance.has_profiel
            # setting_dict['sel_dep_sector_req'] = sel_department_instance.sector_req

    return sel_depbase_instance, sel_depbase_tobesaved, sel_department_instance
# - end of get_settings_departmentbase


# ===== LEVELBASE =======================
def get_settings_levelbase(request, request_item_setting, sel_examyear_instance, sel_department_instance,
                                allowed_depbase_dict, page, permit_dict, setting_dict, selected_pk_dict):
    # PR2022-12-11 PR2023-01-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('===== LEVELBASE ======================= ')
        logger.debug(' ------- get_settings_levelbase -------')
        logger.debug('    request_item_setting: ' + str(request_item_setting))

    # every user can change lvlbase, if in sel_department_lvlbases and in user allowed_lvlbases
    # only called by DatalistDownloadView.download_setting

# - get sel_lvlbase_instance
    request_item_lvlbase_pk = request_item_setting.get(c.KEY_SEL_LVLBASE_PK)
    if logging_on:
        logger.debug('    request_item_lvlbase_pk: ' + str(request_item_lvlbase_pk) + ' ' + str(type(request_item_lvlbase_pk)))

    sel_lvlbase_instance, sel_lvlbase_tobesaved, allowed_lvlbases_arr = \
        get_sel_lvlbase_instance(
                sel_department=sel_department_instance,
                request=request,
                request_item_lvlbase_pk=request_item_lvlbase_pk,
                allowed_depbase_dict=allowed_depbase_dict
            )
    if logging_on:
        logger.debug('    sel_lvlbase_instance: ' + str(sel_lvlbase_instance))
        logger.debug('    allowed_lvlbases_arr: ' + str(allowed_lvlbases_arr))

# - update permit_dict
    permit_dict['allowed_lvlbases'] = allowed_lvlbases_arr
    permit_dict['may_select_level'] = len(allowed_lvlbases_arr) > 1

# - update selected_pk_dict when selected_pk_dict_has_changed, will be saved at end of def
    if sel_lvlbase_tobesaved:
        # save lvlbase_pk when sel_lvlbase_instance exists
        if sel_lvlbase_instance:
            selected_pk_dict[c.KEY_SEL_LVLBASE_PK] = sel_lvlbase_instance.pk
        else:
            # romeove key when 'all' is selected
            if selected_pk_dict and c.KEY_SEL_LVLBASE_PK in selected_pk_dict:
                selected_pk_dict.pop(c.KEY_SEL_LVLBASE_PK)

# - add info to setting_dict, will be sent back to client
    sel_level_instance = None
    if sel_lvlbase_instance:
        setting_dict[c.KEY_SEL_LVLBASE_PK] = sel_lvlbase_instance.pk
        setting_dict['sel_lvlbase_code'] = sel_lvlbase_instance.code if sel_lvlbase_instance.code else None

        sel_level_instance = subj_mod.Level.objects.get_or_none(base=sel_lvlbase_instance,
                                                                         examyear=sel_examyear_instance)
        if sel_level_instance:
            setting_dict['sel_level_pk'] = sel_level_instance.pk
            setting_dict['sel_level_name'] = sel_level_instance.name

    if logging_on:
        logger.debug('    setting_dict: ' + str(setting_dict))
        logger.debug(' ------- end of get_settings_levelbase -------')

    return sel_lvlbase_instance, sel_lvlbase_tobesaved, sel_level_instance
# - end of get_settings_levelbase


# ===== SUBJECTBASE ======================= PR2022-12-11
def get_settings_subjectbase(allowed_subjbases_arr, permit_dict):
    # PR2022-12-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_settings_subjectbase -------')

    if allowed_subjbases_arr:
        permit_dict['allowed_subjbases'] = allowed_subjbases_arr
# - end of get_settings_subjectbase


# ===== EXAMPERIOD ======================= PR2022-12-11
def get_settings_examperiod(request, request_item_setting, setting_dict, selected_pk_dict, reset_examperiod):
    # every user can change exam period
    # PR2022-12-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_settings_examperiod -------')

# - get selected examperiod from request_item_setting, from Usersetting if request_item is None
    request_item_examperiod = request_item_setting.get(c.KEY_SEL_EXAMPERIOD)
    sel_examperiod, sel_examperiod_save = get_sel_examperiod(selected_pk_dict, request_item_examperiod)

    # PR2022-08-23 Roland Guribadi Lauffer: cannot find upload subject btn. Reason: tab was not set to first exam period
    # to prevent this: reset examperiod to 1st when changing examyear
    if reset_examperiod:
        if sel_examperiod != c.EXAMPERIOD_FIRST:
            sel_examperiod = c.EXAMPERIOD_FIRST
            sel_examperiod_save = True
            # not working, must set sel_btn in page_studsubj and page_grade

            set_usersetting_from_uploaddict({'page_studsubj': {'sel_btn': 'btn_ep_01'}}, request)
            set_usersetting_from_uploaddict({'page_grade': {'sel_btn': 'btn_ep_01'}}, request)
            # this works

    if logging_on:
        logger.debug('..... EXAM PERIOD .....')
        logger.debug('    request_item_examperiod: ' + str(request_item_examperiod))
        logger.debug('    sel_examperiod: ' + str(sel_examperiod))
        logger.debug('    sel_examperiod_save: ' + str(sel_examperiod_save))

    # - add info to setting_dict, will be sent back to client
    setting_dict[c.KEY_SEL_EXAMPERIOD] = sel_examperiod

# - update selected_pk_dict when sel_examperiod_tobesaved, will be saved at end of def
    sel_examperiod_tobesaved = False
    if sel_examperiod_save:
        # sel_depbase_instance has always value when sel_depbase_save = True
        selected_pk_dict[c.KEY_SEL_EXAMPERIOD] = sel_examperiod
        sel_examperiod_tobesaved = True

    return sel_examperiod, sel_examperiod_tobesaved
# - end of get_settings_examperiod


def get_sel_examperiod(selected_pk_dict, request_item_examperiod):  # PR2021-09-07 PR2021-12-04
    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_sel_examperiod  -----')
        logger.debug('selected_pk_dict: ' + str(selected_pk_dict))
        logger.debug('request_item_examperiod: ' + str(request_item_examperiod))

    save_changes = False

# - get saved_examperiod from Usersetting, default EXAMPERIOD_FIRST if not found
    sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)

# - check if request_item_examperiod is the same as the saved one
    # examperiod cannot be None, ignore request_item_examperiod when it is None
    if request_item_examperiod:
        if request_item_examperiod != sel_examperiod:
            sel_examperiod = request_item_examperiod
            save_changes = True

# - set sel_examperiod to default EXAMPERIOD_FIRST if None
    if sel_examperiod is None:
        sel_examperiod = c.EXAMPERIOD_FIRST
        save_changes = True

    return sel_examperiod, save_changes
# --- end of get_sel_examperiod


# ===== EXAMTYPE ======================= PR2022-12-11
def get_settings_examtype(request_item_setting, setting_dict, selected_pk_dict, sel_examperiod):
    # every user can change exam period
    # PR2022-12-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_settings_examtype -------')

    # every user can change examtype

    # - get selected examtype from request_item_setting, from Usersetting if request_item is None
    request_item_examtype = request_item_setting.get(c.KEY_SEL_EXAMTYPE)
    sel_examtype, sel_examtype_save = get_sel_examtype(selected_pk_dict, request_item_examtype, sel_examperiod)

    # - add info to setting_dict, will be sent back to client
    setting_dict[c.KEY_SEL_EXAMTYPE] = sel_examtype
    setting_dict['sel_examtype_caption'] = c.get_examtype_caption(sel_examtype)

    if logging_on:
        logger.debug('..... EXAM TYPE .....')
        logger.debug('    request_item_examtype: ' + str(request_item_examtype))
        logger.debug('    sel_examtype: ' + str(sel_examtype))
        logger.debug('    sel_examtype_save: ' + str(sel_examtype_save))

# - update selected_pk_dict when selected_pk_dict_has_changed, will be saved at end of def
    sel_examptype_tobesaved = False
    if sel_examtype_save:
        # sel_depbase_instance has always value when sel_depbase_save = True
        selected_pk_dict[c.KEY_SEL_EXAMTYPE] = sel_examtype
        sel_examptype_tobesaved = True

    return sel_examtype, sel_examptype_tobesaved
# - end of get_settings_examtype


def get_sel_examtype(selected_pk_dict, request_item_examtype, sel_examperiod):  # PR2021-09-07  PR2021-12-04  PR2023-02-03
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_sel_examtype  -----')
        logger.debug('selected_pk_dict: ' + str(selected_pk_dict))
        logger.debug('request_item_examtype: ' + str(request_item_examtype))

# - get saved_examtype from Usersetting
    sel_examtype = selected_pk_dict.get(c.KEY_SEL_EXAMTYPE)

# - check if request_item_examtype is the same as the saved one
    save_changes = False
    # skip if request_item_examtype is None
    if request_item_examtype:
        if request_item_examtype != sel_examtype:
            sel_examtype = request_item_examtype
            save_changes = True

    if logging_on:
        logger.debug('sel_examtype: ' + str(sel_examtype))

# - check if examtype is allowed in this saved_examperiod_int
    # make list of examtypes that are allowed in this examperiod
    # - also get the default_examtype of this examperiod
    if sel_examperiod == 1:
        allowed_examtype_list = ['se', 'sr', 'pe', 'ce']
        default_examtype = 'se'
    elif sel_examperiod == 2:
        allowed_examtype_list = ['ce']
        default_examtype = 'ce'
    elif sel_examperiod == 3:
        allowed_examtype_list = ['ce']
        default_examtype = 'ce'
    elif sel_examperiod == 4:
        allowed_examtype_list = ['se', 'ce']
        default_examtype = 'se'
    else:
        allowed_examtype_list = []
        default_examtype = None

    if logging_on:
        logger.debug('allowed_examtype_list: ' + str(allowed_examtype_list))

# - check if saved examtype is allowed in this examperiod, set to default if not, make selected_pk_dict_has_changed = True
    if sel_examtype:
        if allowed_examtype_list:
            if sel_examtype not in allowed_examtype_list:
                sel_examtype = default_examtype
                save_changes = True
        else:
            sel_examtype = None
            save_changes = True
    else:
        sel_examtype = default_examtype
        save_changes = True

    if allowed_examtype_list:
        if sel_examtype not in allowed_examtype_list:
            sel_examtype = default_examtype
            save_changes = True

    # - update selected_pk_dict
    selected_pk_dict[c.KEY_SEL_EXAMTYPE] = sel_examtype

    return sel_examtype, save_changes
# --- end of get_sel_examtype


# ===== AUTH INDEX ======================= PR2022-12-11
def get_settings_auth_index(usergroups_arr, request_item_setting, setting_dict, selected_pk_dict, sel_examperiod):
    # PR2022-12-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_settings_auth_index -------')

# - get all auth index from usergroups_arr
    auth_index_list = []
    sel_auth_index = None
    sel_auth_index_tobesaved = False

    if usergroups_arr:
        for ug in usergroups_arr:
            if 'auth' in ug:
                auth_index_list.append(int(ug[4:]))
    if logging_on:
        logger.debug('usergroups_arr: ' + str(usergroups_arr))
        logger.debug('auth_index_list: ' + str(auth_index_list))

    if auth_index_list:
        if len(auth_index_list) == 1:
            # when user has only 1 auth: make it selected
            sel_auth_index = auth_index_list[0]
        else:
            # - get selected auth_index from request_item_setting
            request_item_auth = request_item_setting.get(c.KEY_SEL_AUTH_INDEX)
            if logging_on:
                logger.debug('request_item_auth: ' + str(request_item_auth) + ' ' + str(type(request_item_auth)))
            # - make it the selected auth if in auth_list
            if request_item_auth and request_item_auth in auth_index_list:
                sel_auth_index = request_item_auth
                if logging_on:
                    logger.debug('make request_item_auth the selected auth: ' + str(sel_auth_index))

    # - get saved_auth_index from Usersetting - saved_auth_index is string!
    saved_auth_index = None
    saved_auth_index_str = selected_pk_dict.get(c.KEY_SEL_AUTH_INDEX)
    if saved_auth_index_str:
        saved_auth_index = int(saved_auth_index_str)
    if logging_on:
        logger.debug('get saved_auth_index: ' + str(saved_auth_index) + ' ' + str(type(saved_auth_index)))
        logger.debug('sel_auth_index: ' + str(sel_auth_index) + ' ' + str(type(sel_auth_index)))

    # - make saved_auth_index the selected index if sel_auth_index is None
    if sel_auth_index is None:
        if saved_auth_index and saved_auth_index in auth_index_list:
            sel_auth_index = saved_auth_index
            if logging_on:
                logger.debug('make saved_auth_index the selected index: ' + str(sel_auth_index))

    # - get first_auth_index if sel_auth_index is still None
    if sel_auth_index is None:
        if auth_index_list:
            sel_auth_index = auth_index_list[0]
            if logging_on:
                logger.debug('get first_auth_index if still None: ' + str(sel_auth_index))

    # - add info to setting_dict, will be sent back to client
    if sel_auth_index:
        setting_dict[c.KEY_SEL_AUTH_INDEX] = sel_auth_index
        setting_dict['sel_auth_function'] = c.USERGROUP_CAPTION.get('auth' + str(sel_auth_index))

    # save sel_auth_index if it is different from saved_auth_index
    if sel_auth_index != saved_auth_index:
        selected_pk_dict[c.KEY_SEL_AUTH_INDEX] = sel_auth_index
        sel_auth_index_tobesaved = True

    if logging_on:
        logger.debug('sel_auth_index: ' + str(sel_auth_index))
        logger.debug('sel_auth_index_tobesaved: ' + str(sel_auth_index_tobesaved))

    return sel_auth_index_tobesaved
# - end of get_settings_auth_index


def message_diff_exyr(request, sel_examyear_instance):
    # PR2020-10-30 PR2022-12-18
    # check if selected examyear is the same as this examyear,
    # return warning when examyear is different from this_examyear
    msg_dict = {}
    if sel_examyear_instance and sel_examyear_instance.code:
        examyear_int = sel_examyear_instance.code

        now = timezone.now()
        this_examyear = now.year
        if now.month > 7:
            this_examyear = now.year + 1
        if examyear_int != this_examyear:
            # TODO === FIXIT set msg, not for admin in July
            if request.user.role == c.ROLE_064_ADMIN and now.month == 7:
                # skip message in July when role = admin, in July ETE is working on the subjectscheme for the next examyear
                pass
            else:
                # PR2018-08-24 debug: in base.html  href="#" is needed,
                # because bootstrap line 233: a:not([href]):not([tabindex]) overrides navbar-item-warning
                msg = str(_(
                    '<b>Please note</b>:<br>The selected exam year %(exyr)s is different from the current exam year %(cur_ey)s.')
                          % {'exyr': str(examyear_int), 'cur_ey': str(this_examyear)})
                msg_dict = {'msg_html': [msg], 'class': 'border_bg_warning'}
    return msg_dict


############## end of moved from downloads 2022-12-18 ###########################

def get_selected_examyear_from_usersetting(request, allow_not_published=False):
    # PR2021-09-08 PR2022-02-26 PR2022-04-16 PR2022-08-04
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_selected_examyear_from_usersetting ----- ' )
    # this function gets sel_examyear, from req_usr and usersetting
    # used in user_upload, userallowed.uplaod, publish orderlist and upload dnt, where no selected school or dep is needed
    # checks if country is locked and if examyear is missing, not published or locked

    req_usr = request.user
    sel_examyear = None
    msg_list = []

# ==== COUNTRY ========================
# - get country from req_usr
    if req_usr.country:
        requsr_country = req_usr.country
        if requsr_country.locked:
            msg_list.append(str(_('This country is locked.')))
        else:
            selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
            if logging_on:
                logger.debug('selected_pk_dict: ' + str(selected_pk_dict))

# ===== EXAMYEAR =======================
    # - get selected examyear from Usersetting
            sel_examyear_pk = selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK)
            sel_examyear = sch_mod.Examyear.objects.get_or_none(
                pk=sel_examyear_pk,
                country=requsr_country
            )
            if logging_on:
                logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk) + ' ' + str(type(sel_examyear_pk)))
                logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    # - add info to msg_list, will be sent back to client
            message_examyear_missing_notpublished_locked(sel_examyear, msg_list, allow_not_published)

    may_edit = not msg_list
    if not may_edit:
        sel_examyear = None

    if logging_on:
        logger.debug('msg_list: ' + str(msg_list))
        logger.debug('may_edit: ' + str(may_edit))

    return sel_examyear, may_edit, msg_list
# - end of get_selected_examyear_from_usersetting


def get_selected_examyear_from_usersetting_short(request):  #  PR2022-12-11
    sel_examyear_instance = None
    selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
    if selected_pk_dict:
        sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(
            pk=selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK),
            country=request.user.country
        )
    return sel_examyear_instance


def get_selected_examyear_examperiod_from_usersetting(request):  # PR2021-07-08 PR2022-12-11
    # - get selected examyear.code and examperiod from usersettings, only examyear from request.user.country
    # used in ExamyearUploadView, OrderlistDownloadView, ExamDownloadExamJsonView
    # note: examyear.code is integer '2021'
    sel_examyear, sel_examperiod = None, None
    req_usr = request.user
    if req_usr:
        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if selected_pk_dict:
            sel_examyear = sch_mod.Examyear.objects.get_or_none(
                pk=selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK),
                country=request.user.country
            )

        sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)

    return sel_examyear, sel_examperiod


def get_selected_examyear_examperiod_dep_school_from_usersetting(request):  # PR2022-01-31
    # - get selected examyear and department from usersettings, only examyear from request.user.country
    # used in ExamyearUploadView, OrderlistDownloadView
    # note: examyear.code is integer '2021'
    sel_examyear, sel_department, sel_school, sel_examperiod = None, None, None, None
    if request.user and request.user.country:
        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if selected_pk_dict:
            sel_examyear = sch_mod.Examyear.objects.get_or_none(
                pk=selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK),
                country=request.user.country
            )
            sel_department = sch_mod.Department.objects.get_or_none(
                base_id=selected_pk_dict.get(c.KEY_SEL_DEPBASE_PK),
                examyear=sel_examyear
            )
            sel_school = sch_mod.School.objects.get_or_none(
                base_id=selected_pk_dict.get(c.KEY_SEL_SCHOOLBASE_PK),
                examyear=sel_examyear
            )
            sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)

    return sel_examyear, sel_department, sel_school, sel_examperiod
# - end of get_selected_examyear_examperiod_dep_school_from_usersetting


def get_selected_examyear_scheme_pk_from_usersetting(request):  # PR2021-07-13
    # - get selected examyear.code and scheme_p from usersettings
    # used in SchemeDownloadXlsxView
    # note: examyear.code is integer '2021'
    sel_examyear, sel_scheme_pk = None, None
    req_usr = request.user
    if req_usr:
        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if selected_pk_dict:
            sel_examyear = sch_mod.Examyear.objects.get_or_none(
                pk=selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK),
                country=request.user.country
            )

        sel_scheme_pk = selected_pk_dict.get(c.KEY_SEL_SCHEME_PK)

    return sel_examyear, sel_scheme_pk
#  end of get_selected_examyear_scheme_pk_from_usersetting


def get_selected_experiod_extype_subject_from_usersetting(request): # PR2021-01-20 PR2021-10-06 PR2022-03-08
    # - get selected examperiod and examtype and sel_subject_pk from usersettings
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_selected_experiod_extype_subject_from_usersetting ----- ')

    sel_examperiod, sel_examtype, sel_subject_pk = None, None, None
    req_usr = request.user
    if req_usr:
        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if logging_on:
            logger.debug('selected_pk_dict: ' + str(selected_pk_dict))

        if selected_pk_dict:
            sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
            sel_examtype = selected_pk_dict.get(c.KEY_SEL_EXAMTYPE)
            sel_subject_pk = selected_pk_dict.get(c.KEY_SEL_SUBJECT_PK)
    return sel_examperiod, sel_examtype, sel_subject_pk
# - end of get_selected_experiod_extype_subject_from_usersetting


def get_selected_ey_school_dep_lvl_from_usersetting(request, skip_same_school_clause=False, page=None):
    # PR2021-01-13 PR2021-06-14 PR2022-02-05 PR2022-12-18
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ' )
        logger.debug(' +++++ get_selected_ey_school_dep_lvl_from_usersetting +++++ ' )
        logger.debug('    skip_same_school_clause: ' + str(skip_same_school_clause))
    # this function gets sel_examyear, sel_school, sel_department from req_usr and usersetting

    # checks if user may edit .
        # may_edit = False when:
        # - examyear, schoolbase, school, depbase or department is None
        # - country, examyear or school is locked
        # - not requsr_same_school,
        # - not sel_examyear.published,
        # not af.is_allowed_depbase_requsr or not af.is_allowed_depbase_school,

    sel_examyear_instance, sel_school_instance, sel_department_instance, sel_level_instance = None, None, None, None

    def get_sel_examyear_instance():
        err_list = []

    # - get selected exam year
        selected_pk = selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK)
        sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(pk=selected_pk)

        if sel_examyear_instance:

    # - add message when examyear is not published PR22021-12-04
            # not when role is admin PR2022-08-09
            if not sel_examyear_instance.published:
                if request.user.role < c.ROLE_064_ADMIN:
                    err_list.append({'msg_html': [
                        '<br>'.join((str(_("%(admin)s has not yet published examyear %(exyr)s.") % \
                                         {'admin': _('The Division of Examinations'),
                                          'exyr': str(sel_examyear_instance.code)}),
                                     str(_('You cannot enter data.'))))
                    ], 'class': 'border_bg_warning'})

    # - add message when examyear is locked PR22021-12-04
            # not when page_examyear PR2022-08-09
            if request.user.role != c.ROLE_064_ADMIN or page != 'page_examyear':
                if sel_examyear_instance.locked:
                    err_list.append({'msg_html': [
                        '<br>'.join(
                            (str(_('Exam year %(exyr)s is locked.') % {'exyr': str(sel_examyear_instance.code)}),
                             str(_('You cannot make changes.'))))
                    ], 'class': 'border_bg_warning'})
        else:
            err_list.append({'msg_html': [str(_('Exam year is not found.'))], 'class': 'border_bg_invalid'})

        return sel_examyear_instance, err_list
# - end of get_sel_examyear_instance

    def get_school_instance(request, sel_examyear_instance, allowed_sections_dict, selected_pk_dict):
        # PR2022-12-18  PR2023-02-21

        sel_schoolbase_instance = None
        msg_list = []

        req_usr = request.user

    # - get req_usr.schoolbase if role = school
        if req_usr.role == c.ROLE_008_SCHOOL:
            sel_schoolbase_instance = req_usr.schoolbase
        else:

    # - otherwise: get saved_schoolbase_pk from Usersetting, check if saved_schoolbase exists
            saved_schoolbase_pk = selected_pk_dict.get(c.KEY_SEL_SCHOOLBASE_PK)

    # - check if saved_schoolbase exists
            saved_schoolbase = sch_mod.Schoolbase.objects.get_or_none(
                pk=saved_schoolbase_pk,
                country=req_usr.country
            )
            if saved_schoolbase:

    # - check if saved_schoolbase is in allowed_sections
                # schoolbase is allowed when allowed_sections_dict is empty,
                #  or when 'all schools' (-9) in allowed_sections_dict
                #  or when  saved_schoolbase.pk in allowed_sections_dict
                if (not allowed_sections_dict) or \
                        ('-9' in allowed_sections_dict) or \
                        ( str(saved_schoolbase.pk) in allowed_sections_dict):
                    sel_schoolbase_instance = saved_schoolbase

        # requsr_same_school = True when selected school is same as requsr_school PR2021-04-27
        # used on entering grades. Users can only enter grades of their own school. Syst, Adm and Insp, Corrector can not neter grades
        requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and
                              sel_schoolbase_instance and request.user.schoolbase and request.user.schoolbase.pk == sel_schoolbase_instance.pk)

    # - get school from sel_schoolbase and sel_examyear_instance
        sel_school_instance = sch_mod.School.objects.get_or_none(
            base=sel_schoolbase_instance,
            examyear=sel_examyear_instance)

    # - add message when school is locked PR2021-12-04
        if sel_school_instance:
            if sel_school_instance.locked:
                msg_list.append({'msg_html': [
                    '<br>'.join((str(_('Exam year %(exyr)s of this school is locked.') % {
                        'exyr': str(sel_school_instance.examyear.code)}),
                                 str(_('You cannot make changes.'))))], 'class': 'border_bg_warning'})

        return sel_school_instance, requsr_same_school, msg_list
# - end of get_school_instance

    def get_department_instance(sel_examyear_instance, sel_school_instance,
                                          allowed_schoolbase_dict, selected_pk_dict):
        # PR2022-12-19 PR2023-01-08  PR2023-02-21
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ------- get_department_instance -------')

        sel_department_instance = None

        sel_depbase_pk = None

# - get list of allowed_depbases of selected school
        sel_school_allowed_depbases_list = []
        if sel_school_instance and sel_school_instance.depbases:
            sel_school_allowed_depbases_list = list(map(int, sel_school_instance.depbases.split(';')))

        if logging_on:
            logger.debug('    sel_school_allowed_depbases_list: ' + str(sel_school_allowed_depbases_list))
            # sel_school_allowed_depbases_list: [1, 2, 3]

    # - if there is only 1 allowed_depbase: select that one
        if len(sel_school_allowed_depbases_list) == 1:
            sel_depbase_pk = sel_school_allowed_depbases_list[0]
            if logging_on:
                logger.debug('    there is only 1 sel_school_allowed_depbase: ' + str(sel_depbase_pk))

    # - create array of allowed depbases: allowed_depbases_list
        # - must be in sel_school_allowed_depbases_list
        # - and also in allowed_depbases_dict, unless allowed_depbases_dict is empty

        allowed_depbases_list = []
        for depbase_pk_int in sel_school_allowed_depbases_list:
            if not allowed_schoolbase_dict or str(depbase_pk_int) in allowed_schoolbase_dict:
                allowed_depbases_list.append(depbase_pk_int)
        if logging_on:
            logger.debug('    allowed_depbases_list: ' + str(allowed_depbases_list))
            # allowed_depbases_list: [1, 3]

    # - get saved depbase if sel_depbase_pk is empty :
        if not sel_depbase_pk:
            #  - get saved_depbase_pk from Usersetting
            if selected_pk_dict:
                saved_depbase_pk = selected_pk_dict.get(c.KEY_SEL_DEPBASE_PK)
                if logging_on:
                    logger.debug('    saved_depbase_pk: ' + str(saved_depbase_pk))
                if saved_depbase_pk and saved_depbase_pk in allowed_depbases_list:
                    sel_depbase_pk = saved_depbase_pk

    # - get sel_department_instance
        if sel_depbase_pk:
            sel_department_instance = sch_mod.Department.objects.get_or_none(
                base_id=sel_depbase_pk,
                examyear=sel_examyear_instance
            )
        if logging_on:
            logger.debug('    sel_depbase_pk: ' + str(sel_depbase_pk))
            logger.debug('    sel_department_instance: ' + str(sel_department_instance))

        return sel_department_instance
    # - end of get_department_instance

    def get_level_instance(sel_examyear_instance, sel_department_instance,
                                        allowed_depbase_dict, selected_pk_dict):
        # PR2022-12-19 PR2023-02-21
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ------- get_level_instance -------')

        sel_level_instance = None

    # - check if level is required in this department
        level_is_required = (sel_department_instance and sel_department_instance.level_req)
        if logging_on:
            logger.debug('    level_is_required: ' + str(level_is_required))
            logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict))
            # allowed_depbase_dict: {'4': [], '5': []}
        if level_is_required:
            sel_lvlbase_pk = None

# - create array of allowed lvlbase_pk of requsr from allowed_depbase_dict
            allowed_lvlbases_arr = []
            # PR2023-02-21 debug: when allowed_lvlbases_dict is empty: all levels are allowed
            if allowed_depbase_dict:
                for lvlbase_pk_str in allowed_depbase_dict:
                    allowed_lvlbases_arr.append(int(lvlbase_pk_str))
            else:
                # - if multiple allowed: get saved_lvlbase_pk from Usersetting
                saved_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)
                # - don't get saved_depbase when saved_depbase_pk is 'select all'
                if saved_lvlbase_pk and saved_lvlbase_pk != -9:
                    sel_lvlbase_pk = saved_lvlbase_pk

            if logging_on:
                logger.debug('    allowed_lvlbases_arr: ' + str(allowed_lvlbases_arr))

            # - get sel_lvlbase_pk if only 1 allowed
            if len(allowed_lvlbases_arr) == 1:
                sel_lvlbase_pk = allowed_lvlbases_arr[0]
            else:
                # - if multiple allowed: get saved_lvlbase_pk from Usersetting
                saved_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)

                # - don't get saved_depbase when saved_depbase_pk is 'select all'
                if saved_lvlbase_pk and saved_lvlbase_pk != -9:
                    # - check if saved_depbase is in allowed_depbases_arr
                    if saved_lvlbase_pk in allowed_lvlbases_arr:
                        sel_lvlbase_pk = saved_lvlbase_pk

            if sel_lvlbase_pk:
                sel_level_instance = subj_mod.Level.objects.get_or_none(
                    base_id=sel_lvlbase_pk,
                    examyear=sel_examyear_instance
                )

        if logging_on:
            logger.debug('    sel_level_instance: ' + str(sel_level_instance))

        return sel_level_instance
    # - end of get_level_instance

#######################################
    msg_list = []
    req_usr = request.user

    try:
        if logging_on:
            logger.debug('    req_usr: ' + str(req_usr))
            logger.debug('    req_usr.country: ' + str(req_usr.country))

    # - get country from req_usr
        if req_usr.country is None:
            msg_list.append(str(_('User has no country.')))
        else:
            requsr_country = req_usr.country
            if requsr_country.locked:
                msg_list.append(str(_('This country is locked.')))

            selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)

            if logging_on:
                logger.debug('    selected_pk_dict: ' + str(selected_pk_dict))

    # - get selected examyear
            sel_examyear_instance, msg_lst = get_sel_examyear_instance()
            if msg_lst:
                msg_list.extend(msg_lst)

            if logging_on:
                logger.debug('    sel_examyear_instance: ' + str(sel_examyear_instance))
                logger.debug('msg_list: ' + str(msg_list))

    # - get allowed_sections_dict
            allowed_sections_dict = acc_prm.get_userallowed_sections_dict_from_request(request)
            if logging_on:
                logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict))

    # - get sel_school_instance
            sel_school_instance, requsr_same_school, msg_lst = \
                get_school_instance(
                    request=request,
                    sel_examyear_instance=sel_examyear_instance,
                    allowed_sections_dict=allowed_sections_dict,
                    selected_pk_dict=selected_pk_dict
                )
            if msg_lst:
                msg_list.extend(msg_lst)

            if logging_on:
                logger.debug('    sel_school_instance: ' + str(sel_school_instance))
                logger.debug('msg_list: ' + str(msg_list))

    # - get allowed_schoolbase_dict
            allowed_schoolbase_dict, allowed_depbases_pk_arr = \
                acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(
                    userallowed_sections_dict=allowed_sections_dict,
                    sel_schoolbase_pk=sel_school_instance.base_id if sel_school_instance else None
                )

            if logging_on:
                logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))

            sel_department_instance = get_department_instance(
                    sel_examyear_instance=sel_examyear_instance,
                    sel_school_instance=sel_school_instance,
                    allowed_schoolbase_dict=allowed_schoolbase_dict,
                    selected_pk_dict=selected_pk_dict
                )

            if logging_on:
                logger.debug('    sel_department_instance: ' + str(sel_department_instance))

    # - get allowed_depbase_dict
            allowed_depbase_dict, allowed_lvlbase_pk_arr = \
                acc_prm.get_userallowed_depbase_dict_lvlbases_pk_arr(
                    allowed_schoolbase_dict=allowed_schoolbase_dict,
                    sel_depbase_pk=sel_department_instance.base_id if sel_department_instance else None
                )
            if logging_on:
                logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict))
                logger.debug('    allowed_lvlbase_pk_arr: ' + str(allowed_lvlbase_pk_arr))

            allowed_lvlbases_dict = get_requsr_allowed_lvlbases_dict(
                allowed_depbase_dict=allowed_depbase_dict,
                sel_lvlbase_pk=sel_department_instance.base_id if sel_department_instance else None
            )
            if logging_on:
                logger.debug('    allowed_lvlbases_dict: ' + str(allowed_lvlbases_dict))

            sel_level_instance = get_level_instance(
                    sel_examyear_instance=sel_examyear_instance,
                    sel_department_instance=sel_department_instance,
                    allowed_depbase_dict=allowed_depbase_dict,
                    selected_pk_dict=selected_pk_dict
                )
            if logging_on:
                logger.debug('    sel_level_instance: ' + str(sel_level_instance))

# ===== EXAM PERIOD =======================
            # NIU
            # - get saved_examperiod from Usersetting, default EXAMPERIOD_FIRST if not found
            #sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
            # - set sel_examperiod to default EXAMPERIOD_FIRST if None
            #if sel_examperiod is None:
            #    sel_examperiod = c.EXAMPERIOD_FIRST

# ===== EXAM TYPE =======================
            # dont get examtype

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        msg_txt = ''.join((str(_('An error occurred')), ':<br><i>', str(e), '</i>'))
        msg_html = ''.join(("<div class='p-2 border_bg_invalid'>", msg_txt, "</div>"))
        msg_list.append(msg_html)

    may_edit = len(msg_list) == 0

    if logging_on:
        logger.debug(' >> msg_list: ' + str(msg_list))
        logger.debug('    may_edit: ' + str(may_edit))

    return sel_examyear_instance, sel_school_instance, sel_department_instance, sel_level_instance, may_edit, msg_list
# - end of get_selected_ey_school_dep_lvl_from_usersetting


def get_sel_schoolbase_instance(request, request_item_schoolbase_pk, allowed_sections_dict):
    # PR2020-12-25 PR2021-04-23 PR2021-08-12 PR2022-12-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_sel_schoolbase_instance  -----')
        logger.debug('    request_item_schoolbase_pk: ' + str(request_item_schoolbase_pk))
        logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict))

    # - get schoolbase from req_usr when role = school,
    #   from request_item_schoolbase_pk or saved settings otherwise
    #   req_usr.schoolbase cannot be changed
    #   Selected schoolbase is stored in {selected_pk: {sel_schoolbase_pk: val}}

    sel_schoolbase_instance = None
    sel_schoolbase_tobesaved = False

    if request.user and request.user.country:
        req_usr = request.user
        requsr_country = req_usr.country

# - get req_usr.schoolbase if role = school
        may_select_schoolbase = (req_usr.role > c.ROLE_008_SCHOOL)
        if not may_select_schoolbase:
            sel_schoolbase_instance = req_usr.schoolbase
        else:

# - check if there is a new schoolbase_pk in request_item, check if request_item_schoolbase exists
            if request_item_schoolbase_pk:
                request_item_schoolbase = sch_mod.Schoolbase.objects.get_or_none(
                    pk=request_item_schoolbase_pk,
                    country=requsr_country
                )
                if request_item_schoolbase:

    # - check if request_item_schoolbase is in allowed_sections
                # schoolbase is allowed when allowed_sections_dict is empty or when 'all schools' (-9) in allowed_sections_dict
                    if not allowed_sections_dict or '-9' in allowed_sections_dict:
                        request_item_schoolbase_is_allowed = True
                    else:
                # schoolbase is allowed when request_item_schoolbase in allowed_sections_dict
                        request_item_schoolbase_is_allowed = (str(request_item_schoolbase.pk) in allowed_sections_dict)

                    if request_item_schoolbase_is_allowed:
                        sel_schoolbase_instance = request_item_schoolbase
                        sel_schoolbase_tobesaved = True

# - if sel_schoolbase_instance does not exist:
#       get saved_schoolbase_pk from Usersetting, check if saved_schoolbase exists
            if sel_schoolbase_instance is None:
                selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                saved_schoolbase_pk = selected_pk_dict.get(c.KEY_SEL_SCHOOLBASE_PK)

        # check if saved_schoolbase exists
                saved_schoolbase = sch_mod.Schoolbase.objects.get_or_none(pk=saved_schoolbase_pk, country=requsr_country)
                if saved_schoolbase:

        # check if saved_schoolbase is in allowed_sections
                # schoolbase is allowed when allowed_sections_dict is empty or  when 'all schools' (-9) in allowed_sections_dict
                    if not allowed_sections_dict or '-9' in allowed_sections_dict:
                        saved_schoolbase_is_allowed = True
                    else:
                # schoolbase is allowed when request_item_schoolbase in allowed_sections_dict
                        saved_schoolbase_is_allowed = (str(saved_schoolbase.pk) in allowed_sections_dict)
                    if saved_schoolbase_is_allowed:
                        sel_schoolbase_instance = saved_schoolbase

    # - if there is no saved nor request schoolbase: get schoolbase of this user
            if sel_schoolbase_instance is None:
                sel_schoolbase_instance = req_usr.schoolbase
                if sel_schoolbase_instance is not None:
                    sel_schoolbase_tobesaved = True
    if logging_on:
        logger.debug('    sel_schoolbase_instance: ' + str(sel_schoolbase_instance))
        logger.debug('    sel_schoolbase_tobesaved: ' + str(sel_schoolbase_tobesaved))

    return sel_schoolbase_instance, sel_schoolbase_tobesaved
# --- end of get_sel_schoolbase_instance


def get_sel_depbase_instance___ISN(sel_school_instance, page, request, request_item_depbase_pk, allowed_schoolbase_dict):
    # PR2020-12-26 PR2021-05-07 PR2021-08-13 PR2022-10-19 PR2022-03-16
    #  code works ok: it returns
    #  - combination of allowed_depbases from user and school and
    #  - request_item_depbase_pk or saved depbase_pk or first allowed depbase_pk

    # PR2022-10-19 TODO
    # code to switch selected depbase is not perfect yet. To be improved, take in account:
    # depbase can be changed in 2 ways:
    # - in the menubar. Then there is no 'all deps' possible, use saved or default if necessary
    # - in sidebar (only bij admin in page exam, subjects, orderlist). 'All deps' is allowed, stored with value -1
    # tobe checked  if sel_depbase_pk will be saved when using download function, or is saved separately bij set_user_setting

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  get_sel_depbase_instance  -----')
        logger.debug('    request_item_depbase_pk: ' + str(request_item_depbase_pk))
        logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))

    """
    # userallowed_sections_dict:  {"28": {"1": {"-9": [116]}, "2": {"-9": [116]}, "3": {"-9": [116]}}}
    # userallowed_schoolbase_dict:       {"1": {"-9": [116]}, "2": {"-9": [116]}, "3": {"-9": [116]}}}
    # allowed_depbases_pk_arr:           [1, 2, 3] <class 'list'>
    """

    def get_saved_depbase_instance():
        saved_depbase_instance = None
        selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if selected_dict:
            sel_depbase_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)
            if sel_depbase_pk:
                saved_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=sel_depbase_pk)
        return saved_depbase_instance

    def get_school_allowed_depbases_list():
        # - get list of allowed_depbases of selected school
        school_allowed_depbases_list = []
        if sel_school_instance and sel_school_instance.depbases:
            school_allowed_depbases_list = list(map(int, sel_school_instance.depbases.split(';')))
        return school_allowed_depbases_list

    def get_user_allowed_depbases_list():
        user_allowed_depbases_list = []
        # - create array of allowed depbases: userallowed_depbases_list
        # - must be in sel_school_allowed_depbases_list
        # - and in allowed_schoolbase_dict, unless allowed_schoolbase_dict is empty
        """
        allowed_schoolbase_dict: {'-9': {'1': []}, '2': {'2': [], '3': []} }
        """

        logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))
        logger.debug('    sel_school_instance: ' + str(sel_school_instance))
        if allowed_schoolbase_dict:
            # check for sel_school and 'all schools'
            schoolbase_pk_arr = ['-9']
            if sel_school_instance:
                schoolbase_pk_arr.append(str(sel_school_instance.base.pk))

            for schoolbase_pk_str in schoolbase_pk_arr:
                if schoolbase_pk_str in allowed_schoolbase_dict:
                    allowed_depbase_dict = allowed_schoolbase_dict[schoolbase_pk_str]

                    for depbase_pk_str in allowed_depbase_dict.keys():
                        depbase_pk_int = int(depbase_pk_str)
                        if depbase_pk_int not in userallowed_depbases_list:
                            userallowed_depbases_list.append(depbase_pk_int)
        return user_allowed_depbases_list

    sel_depbase_instance = None
    sel_depbase_tobesaved = False
    multiple_depbases_exist = False
    allowed_depbases_list = []
    userallowed_depbases_list = []

    if request.user and request.user.country:
        req_usr = request.user

        # PR2022-10-16 debug: when setting depbase_pk in orderlist, 'Havo' switched back to 'Vsbo when refreshing page.
        # cause: ETE user had Vsbo school selected, since it doesn't have Havo, it changed dp to Vsbo
        # solution: skip this check when page = orderlist
        skip_school_allowed_depbases = (page in ('page_subject', 'page_orderlist'))

# +++++ get allowed_depbases_list
    # - get list of allowed_depbases of selected school
        school_allowed_depbases_list = get_school_allowed_depbases_list()
        if logging_on:
            logger.debug('    school_allowed_depbases_list: ' + str(school_allowed_depbases_list))

        user_allowed_depbases_list = get_user_allowed_depbases_list()
        if logging_on:
            logger.debug('    userallowed_depbases_list: ' + str(userallowed_depbases_list))
    # combine both lists
        allowed_depbases_list = []

    return sel_depbase_instance, sel_depbase_tobesaved, allowed_schoolbase_dict, allowed_depbases_list
# --- end of get_sel_depbase_instance


def get_sel_depbase_instance(sel_school_instance, page, request, request_item_depbase_pk, allowed_schoolbase_dict):
    # PR2020-12-26 PR2021-05-07 PR2021-08-13 PR2022-10-19 PR2022-03-16
    #  code works ok: it returns
    #  - combination of allowed_depbases from user and school and
    #  - request_item_depbase_pk or saved depbase_pk or first allowed depbase_pk

    # PR2022-10-19 TODO
    # code to switch selected depbase is not perfect yet. To be improved, take in account:
    # depbase can be changed in 2 ways:
    # - in the menubar. Then there is no 'all deps' possible, use saved or default if necessary
    # - in sidebar (only bij admin in page exam, subjects, orderlist). 'All deps' is allowed, stored with value -1
    # tobe checked  if sel_depbase_pk will be saved when using download function, or is saved separately bij set_user_setting

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  get_sel_depbase_instance  -----')
        logger.debug('    request_item_depbase_pk: ' + str(request_item_depbase_pk))
        logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))

    def get_saved_depbase_instance():
        saved_depbase_instance = None
        selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if selected_dict:
            sel_depbase_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)
            if sel_depbase_pk:
                saved_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=sel_depbase_pk)
        return saved_depbase_instance

    sel_depbase_instance = None
    sel_depbase_tobesaved = False
    multiple_depbases_exist = False
    allowed_depbases_list = []

    if request.user and request.user.country:
        req_usr = request.user

        # PR2022-10-16 debug: when setting depbase_pk in orderlist, 'Havo' switched back to 'Vsbo when refreshing page.
        # cause: ETE user had Vsbo school selected, since it doesn't have Havo, it changed dp to Vsbo
        # solution: skip this check when page = orderlist
        skip_school_allowed_depbases = (page in ('page_subject', 'page_orderlist'))

# +++++ get allowed_depbases_list
    # - get list of allowed_depbases of selected school
        sel_school_allowed_depbases_list = []
        if sel_school_instance and sel_school_instance.depbases:
            sel_school_allowed_depbases_list = list(map(int, sel_school_instance.depbases.split(';')))
        if logging_on:
            logger.debug('    sel_school_allowed_depbases_list: ' + str(sel_school_allowed_depbases_list))

    # - if there is only 1 allowed_depbase: select that one
        if len(sel_school_allowed_depbases_list) == 1:
            sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(
                pk=sel_school_allowed_depbases_list[0],
            )
            if logging_on:
                logger.debug('    there is only 1 sel_school_allowed_depbases: ' + str(sel_depbase_instance))

            # - save if different from saved_examyear_instance
            if sel_depbase_instance:
                saved_depbase_instance = get_saved_depbase_instance()
                if sel_depbase_instance != saved_depbase_instance:
                    sel_depbase_tobesaved = True

    # - create array of allowed depbases: allowed_depbases_list
        # - must be in sel_school_allowed_depbases_list
        # - and in allowed_schoolbase_dict, unless allowed_schoolbase_dict is empty
        if sel_depbase_instance is None:
            if allowed_schoolbase_dict:
                for depbase_pk_int in sel_school_allowed_depbases_list:
                    if str(depbase_pk_int) in allowed_schoolbase_dict or not allowed_schoolbase_dict:
                        allowed_depbases_list.append(depbase_pk_int)
            else:
                allowed_depbases_list = sel_school_allowed_depbases_list

        if logging_on:
            logger.debug('    allowed_depbases_list: ' + str(allowed_depbases_list))

# +++++ get request_item_depbase
    # - check if there is a new depbase_pk in request_item and check if request_item_depbase exists
        if sel_depbase_instance is None:
            if request_item_depbase_pk:
                if request_item_depbase_pk == -1:
                    # TODO check if this is in use and correct (is 'all' = -1 or -9 ? )
                    # don't get saved_depbase_pk when request_item_depbase_pk is 'select all'
                    sel_depbase_instance = None
                    sel_depbase_tobesaved = True
                else:
                    if request_item_depbase_pk in allowed_depbases_list:
                        request_item_depbase = sch_mod.Departmentbase.objects.get_or_none(
                            pk=request_item_depbase_pk
                        )
                        if request_item_depbase:
                            sel_depbase_instance = request_item_depbase
                            sel_depbase_tobesaved = True

        if logging_on:
            logger.debug('    sel_depbase_instance = request_item_depbase: ' + str(sel_depbase_instance))

# +++++ saved depbase
    # - if sel_depbase_instance does not exist:
        #  get saved_depbase_pk from Usersetting, except when request_item_depbase_pk == -1
        if sel_depbase_instance is None and not sel_depbase_tobesaved:
            saved_depbase_instance = None
            selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
            if logging_on:
                logger.debug('    selected_dict: ' + str(selected_dict))

            if selected_dict:
                saved_depbase_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)
                # when saving 'All departments' saved_depbase_pk = -1, change it to None
                if logging_on:
                    logger.debug('    saved_depbase_pk: ' + str(saved_depbase_pk))

                if saved_depbase_pk == -1:
                    # don't get saved_depbase when saved_depbase_pk is 'select all'
                    pass
                else:
    # check if saved_schoolbase exists
                    saved_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=saved_depbase_pk)

                    if logging_on:
                        logger.debug('    saved_depbase_instance: ' + str(saved_depbase_instance))

                    if saved_depbase_instance:
    # check if saved_depbase is in allowed_schoolbase_dict
                        # PR2023-01-16 debug: skip this check when allowed_schoolbase_dict is empty
                        if allowed_schoolbase_dict and str(saved_depbase_instance.pk) in allowed_schoolbase_dict or \
                                not allowed_schoolbase_dict:
                            sel_depbase_instance = saved_depbase_instance

# +++++ get first available depbase
    # - get first available depbase when sel_depbase_instance is None, except when select_all_allowed

        if sel_depbase_instance is None:
            # PR2022-10-17 debug: in page_orderlist dep returns Vsbo instead of 'All deps'
            # also in page_exams when requsr = admin
            select_all_allowed = (page == 'page_orderlist') or \
                                 (page == 'page_exams' and req_usr.role == c.ROLE_064_ADMIN)
            if not select_all_allowed:
                if allowed_depbases_list:
                    allowed_depbases_list.sort()
                    depbase_pk_int = allowed_depbases_list[0]
                    depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=depbase_pk_int)
                    if depbase_instance:
                        sel_depbase_instance = depbase_instance
                        sel_depbase_tobesaved = True

    if logging_on:
        logger.debug('....sel_depbase_instance: ' + str(sel_depbase_instance) + ' ' + str(type(sel_depbase_instance)))
        logger.debug('....sel_depbase_tobesaved: ' + str(sel_depbase_tobesaved) + ' ' + str(type(sel_depbase_tobesaved)))
        logger.debug('....allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict) + ' ' + str(type(allowed_schoolbase_dict)))
        logger.debug('....allowed_depbases_list: ' + str(allowed_depbases_list) + ' ' + str(type(allowed_depbases_list)))

    return sel_depbase_instance, sel_depbase_tobesaved, allowed_schoolbase_dict, allowed_depbases_list
# --- end of get_sel_depbase_instance




def get_sel_lvlbase_instance(sel_department, request, request_item_lvlbase_pk, allowed_depbase_dict):
    # PR2022-12-11 PR2023-01-11

    # PR2023-01-11 only called by get_settings_levelbase
    # ThisCodeIsOK

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  get_sel_lvlbase_instance  -----')
        logger.debug('    sel_department: ' + str(sel_department))
        logger.debug('    request_item_lvlbase_pk: ' + str(request_item_lvlbase_pk))
        logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict))
        logger.debug(' ----------')

    sel_lvlbase_instance = None
    sel_lvlbase_tobesaved = False
    allowed_lvlbases_arr = []

    if request.user:

    # - check if level is required in this department
        level_is_required = (sel_department and sel_department.level_req)
        if level_is_required:
            if logging_on:
                logger.debug('    level_is_required: ' + str(level_is_required))

        # - create array of allowed lvlbases integers of requsr from allowed_depbase_dict,
            # array stays empty when '-9' (all) in allowed_depbase_dict
            if allowed_depbase_dict:
                if '-9' not in allowed_depbase_dict:
                    for lvlbase_pk_str in allowed_depbase_dict:
                        allowed_lvlbases_arr.append(int(lvlbase_pk_str))
            if logging_on:
                logger.debug('    allowed_lvlbases_arr: ' + str(allowed_lvlbases_arr))

        # - get saved_lvlbase_pk from Usersetting
            saved_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
            saved_lvlbase_pk = saved_dict.get(c.KEY_SEL_LVLBASE_PK)
            if logging_on:
                logger.debug('    saved_lvlbase_pk: ' + str(saved_lvlbase_pk))

        # - check if request_item_lvlbase_pk exists and is allowed
            sel_lvlbase_pk = None
            if request_item_lvlbase_pk == -9:
                sel_lvlbase_pk = request_item_lvlbase_pk
                sel_lvlbase_tobesaved = sel_lvlbase_pk != saved_lvlbase_pk

            elif request_item_lvlbase_pk:
                # value -9 (all) is not in allowed_lvlbases_arr, it is filtered out above in this function
                if (not allowed_lvlbases_arr) or (allowed_lvlbases_arr and request_item_lvlbase_pk in allowed_lvlbases_arr):
                    sel_lvlbase_pk = request_item_lvlbase_pk
                    sel_lvlbase_tobesaved = sel_lvlbase_pk != saved_lvlbase_pk

            if logging_on:
                logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
                logger.debug('    sel_lvlbase_tobesaved: ' + str(sel_lvlbase_tobesaved))

    # - if sel_lvlbase_pk is None: get saved_lvlbase_pk, check if is allowed
            if not sel_lvlbase_pk:
                if saved_lvlbase_pk == -9:
                    sel_lvlbase_pk = saved_lvlbase_pk
                elif saved_lvlbase_pk:
                    # value -9 (all) is not in allowed_lvlbases_arr, it is filtered out above in this function
                    if allowed_lvlbases_arr:
                        if saved_lvlbase_pk in allowed_lvlbases_arr:
                            sel_lvlbase_pk = saved_lvlbase_pk
                    else:
                        sel_lvlbase_pk = saved_lvlbase_pk

     # - if sel_lvlbase_pk is None and there is only 1 allowed lvlbase_pk : get allowed lvlbase_pk
            if not sel_lvlbase_pk or sel_lvlbase_pk == -9:
                # value -9 (all) is not in allowed_lvlbases_arr, it is filtered out above in this function
                if len(allowed_lvlbases_arr) == 1:
                    sel_lvlbase_pk = allowed_lvlbases_arr[0]
                    sel_lvlbase_tobesaved = True

    # - get sel_lvlbase_instance from sel_lvlbase_instance
            if sel_lvlbase_pk and sel_lvlbase_pk != -9:
                sel_lvlbase_instance = subj_mod.Levelbase.objects.get_or_none(
                    pk=sel_lvlbase_pk
                )

    if logging_on:
        logger.debug('....sel_lvlbase_instance: ' + str(sel_lvlbase_instance))
        logger.debug('....sel_lvlbase_tobesaved: ' + str(sel_lvlbase_tobesaved))
        logger.debug('....allowed_lvlbases_arr: ' + str(allowed_lvlbases_arr))

    return sel_lvlbase_instance, sel_lvlbase_tobesaved, allowed_lvlbases_arr
# --- end of get_sel_lvlbase_instance

######################################################


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


def get_selected_lvlbase_sctbase_from_usersetting(request):  # PR2021-11-18
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_selected_lvlbase_sctbase_from_usersetting ----- ' )
    # this function gets sel_lvlbase_pk and sel_sctbase_pk from req_usr and usersetting
    # used in DownloadGradelistDiplomaView (for now)
    # checks if user may edit .

    req_usr = request.user
    sel_lvlbase_pk = None
    sel_sctbase_pk = None

    if req_usr and req_usr.schoolbase:
        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if selected_pk_dict:
            sel_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)
            sel_sctbase_pk = selected_pk_dict.get(c.KEY_SEL_SCTBASE_PK)

    return sel_lvlbase_pk, sel_sctbase_pk
# - end of get_selected_lvlbase_sctbase_from_usersetting


def message_examyear_missing_notpublished_locked(sel_examyear, msg_list, allow_not_published=False):  # PR2021-12-04 PR2022-08-04
    if sel_examyear is None:
        msg_list.append(str(_('There is no exam year selected.')))
    elif sel_examyear.locked:
        msg_list.append(str(_('Exam year %(ey_code)s is locked.') % {'ey_code': str(sel_examyear.code)}))
    elif not allow_not_published and not sel_examyear.published:
        msg_list.extend((str(_("%(admin)s has not yet published examyear %(exyr)s.") % \
                             {'admin': _('The Division of Examinations'), 'exyr': str(sel_examyear.code)}),
                         str(_('You cannot enter data.'))))
# - end of message_examyear_missing_notpublished_locked


def message_school_missing_locked(sel_school, sel_examyear, msg_list):
    # PR2021-12-04  PR2022-02-05 PR2022-08-20

    if sel_school is None:
        msg_list.append(str(_('School not found in this exam year.')))
    elif sel_school.locked:
        msg_list.append(str(_('Exam year %(ey_code)s of this school is locked.') % {'ey_code': str(sel_examyear.code)}))
# - end of message_school_missing_locked




############ allowed sections #########################

"""
def get_requsr_allowed_depbases_arr(req_usr, sel_examyear, sel_school, skip_school_allowed_depbases):
    # PR2022-10-18 PR2022-12-09

    # +++ get allowed_depbases - combination of user_allowed_depbases and school_allowed_depbases with skip_school_allowed_depbases
    # skip school_allowed_depbases when page == 'page_orderlist'

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug(' ----- get_requsr_allowed_depbases_arr -----')

    allowed_depbases_list = []

    def get_user_allowed_depbases_list():
        allowed_depbases_list = []
        allowed_sections_dict, usergroups_arr, allowed_clusterbases_arr = get_requsr_usergroups_allowedsections_allowedclusters(request, sel_examyear)
        # allowed_sections_dict: {'2': {'1': {}}, '16': {'3': {'-9': []}}, '17': {'3': {'-9': [160]}}}

        if allowed_sections_dict and sel_school:
            sel_schoolbase_pk_str = str(sel_school.base.pk)
            allowed_depbases_dict = allowed_sections_dict[sel_schoolbase_pk_str]
            # allowed_depbases_dict: {'3': {'-9': []}}

            if allowed_depbases_dict:
                for depbase_pk_str in allowed_depbases_dict:
                    allowed_depbases_list.append(int(depbase_pk_str))
            # allowed_depbases_list: [3]

        return allowed_depbases_list

    def get_school_allowed_depbases_list():
        allowed_depbases_list = []
        if not skip_school_allowed_depbases and sel_school and sel_school.depbases:
            allowed_depbases_list = list(map(int, sel_school.depbases.split(';')))
        return allowed_depbases_list

# - get user_allowed_depbases_list from allowed_sections_dict
    user_allowed_depbases_list = get_user_allowed_depbases_list()

# - get school_allowed_depbases_list, not when skip_school_allowed_depbases
    school_allowed_depbases_list = get_school_allowed_depbases_list()

# - combine allowed_depbases
    # if allowed_depbases is empty, all depbases are allowed
    if user_allowed_depbases_list:
        if school_allowed_depbases_list:
            for depbase_pk in user_allowed_depbases_list:
                if depbase_pk in school_allowed_depbases_list:
                    allowed_depbases_list.append(depbase_pk)
        else:
            allowed_depbases_list = user_allowed_depbases_list
    else:
        if school_allowed_depbases_list:
            allowed_depbases_list = school_allowed_depbases_list

    if logging_on:
        logger.debug('    user_allowed_depbases_list: ' + str(user_allowed_depbases_list))
        logger.debug('    school_allowed_depbases_list: ' + str(school_allowed_depbases_list))
        logger.debug('    allowed_depbases_list: ' + str(allowed_depbases_list))

    return allowed_depbases_list
# end of get_requsr_allowed_depbases_arr

def get_requsr_allowed_lvlbases_arrNIU(req_usr, sel_examyear, sel_school, sel_department, skip_school_allowed_depbases):
    # PR2022-12-10

    # +++ get allowed_depbases - combination of user_allowed_depbases and school_allowed_depbases with skip_school_allowed_depbases
    # skip school_allowed_depbases when page == 'page_orderlist'

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug(' ----- get_requsr_allowed_lvlbases_arr -----')

    allowed_depbases_list = []

    def get_user_allowed_lvlbases_list():
        allowed_lvlbases_list = []
        usergroups_arr, allowed_sections_dict, allowed_clusterbases_arr = get_requsr_allowedsections(req_usr.pk, sel_examyear.pk)
        # allowed_sections_dict: {'2': {'1': {}}, '16': {'3': {'-9': []}}, '17': {'3': {'-9': [160]}}}

        if allowed_sections_dict and sel_school:
            sel_schoolbase_pk_str = str(sel_school.base.pk)
            allowed_depbases_dict = allowed_sections_dict.get(sel_schoolbase_pk_str)
            # allowed_depbases_dict: {'3': {'-9': []}}
            if allowed_depbases_dict and sel_department:
                sel_depbase_pk_str = str(sel_department.base.pk)
                allowed_lvlbases_dict = allowed_depbases_dict.get(sel_depbase_pk_str)
                if allowed_lvlbases_dict:
                    for lvlbase_pk_str in allowed_lvlbases_dict:
                        allowed_lvlbases_list.append(int(lvlbase_pk_str))
            # allowed_lvlbases_list: [3]

        return allowed_lvlbases_list

    def get_school_allowed_depbases_list():
        allowed_depbases_list = []
        if not skip_school_allowed_depbases and sel_school and sel_school.depbases:
            allowed_depbases_list = list(map(int, sel_school.depbases.split(';')))
        return allowed_depbases_list

# - get user_allowed_depbases_list from allowed_sections_dict
    user_allowed_depbases_list = get_user_allowed_depbases_list()

# - get school_allowed_depbases_list, not when skip_school_allowed_depbases
    school_allowed_depbases_list = get_school_allowed_depbases_list()

# - combine allowed_depbases
    # if allowed_depbases is empty, all depbases are allowed
    if user_allowed_depbases_list:
        if school_allowed_depbases_list:
            for depbase_pk in user_allowed_depbases_list:
                if depbase_pk in school_allowed_depbases_list:
                    allowed_depbases_list.append(depbase_pk)
        else:
            allowed_depbases_list = user_allowed_depbases_list
    else:
        if school_allowed_depbases_list:
            allowed_depbases_list = school_allowed_depbases_list

    if logging_on:
        logger.debug('    user_allowed_depbases_list: ' + str(user_allowed_depbases_list))
        logger.debug('    school_allowed_depbases_list: ' + str(school_allowed_depbases_list))
        logger.debug('    allowed_depbases_list: ' + str(allowed_depbases_list))

    return allowed_depbases_list
# end of get_requsr_allowed_lvlbases_arr



def get_requsr_allowedsections_dict_OK (req_usr, sel_examyear):
    # PR2022-12-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('---  get_requsr_allowedsections_dict_OK  ------- ')
        logger.debug('req_usr:      ' + str(req_usr))
        logger.debug('sel_examyear: ' + str(sel_examyear))

    #  json.dumps converts a dict to a json object
    #  json.loads retrieves a dict (or other type) from a json string
    #  json.load deserializes a file

    allowed_sections_dict = {}

    if req_usr and sel_examyear :
        userallowed = acc_mod.UserAllowed.objects.filter(
            user=req_usr,
            examyear=sel_examyear,
        ).order_by('id').first()

        if userallowed:
            allowed_sections_str = getattr(userallowed, 'allowed_sections')
            if allowed_sections_str:
                allowed_sections_dict = json.loads(allowed_sections_str)

    return allowed_sections_dict
# - end of get_requsr_allowedsections_dict_OK

def get_requsr_allowed_schoolbase_dict_OK(allowed_sections_dict, sel_schoolbase_pk):
    # PR2023-01-09
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---  get_requsr_allowed_schoolbase_dict_OK  ------- ')
        logger.debug('    allowed_sections_dict:      ' + str(allowed_sections_dict))
        logger.debug('    sel_schoolbase_pk: ' + str(sel_schoolbase_pk))

    allowed_schoolbase_dict = {}
    allowed_depbases_pk_arr = []
    if allowed_sections_dict:

# - check if sel_schoolbase_pk exists in allowed_sections_dict
        if sel_schoolbase_pk:
            sel_schoolbase_pk_str = str(sel_schoolbase_pk)
            allowed_schoolbase_dict = allowed_sections_dict.get(sel_schoolbase_pk_str) or {}

# - if not, check if '-9' (all) exists in allowed_sections_dict
        if not allowed_schoolbase_dict:
            sel_schoolbase_pk_str = '-9'
            allowed_schoolbase_dict = allowed_sections_dict.get(sel_schoolbase_pk_str) or {}

# - add allowed depbase_pk_int to allowed_depbases_pk_arr
        if allowed_schoolbase_dict:
            for depbase_pk_str in allowed_schoolbase_dict:
                allowed_depbases_pk_arr.append(int(depbase_pk_str))

    if logging_on:
        logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))
        logger.debug('    allowed_depbases_pk_arr: ' + str(allowed_depbases_pk_arr) + ' ' + str( type(allowed_depbases_pk_arr)))

    # allowed_schoolbase_dict: {'1': {'-9': []}, '2': {'-9': []}, '3': {'-9': []}}
    # allowed_depbases_pk_arr: [1, 2, 3] <class 'list'>
    return allowed_schoolbase_dict, allowed_depbases_pk_arr
# - end of get_requsr_allowed_schoolbase_dict_OK


def  get_userfilter_allowed_school_dep_lvl_subj_sct_cluster(request, table=None):
    # PR2022-03-13 PR2022-12-12
    # this function adds selected / allowed  filter to sql, called by create_grade_rows
    # called by downloads.create_grade_rows

    # filter examyear and examperiod are outside this function
    # filter school is required:
    #  - when user is school: get req_usr.schoolbase
    #  - get selected otherwise
    #  - check if school is allowed
    #  - return no records when no school
    # filter depbase is required:
    #  - get depbase of selected school when school has only 1 department
    #  - get selected depbase otherwise
    #  - return no records when no depbase
    # filter lvlbase:
    #  - don't filter on lvlbase when level not required in selected department (then lvlbase_pk = -9 ('all levels')
    #  - filter on selected lvlbase, if allowed
    #  - if no selected lvlbase: filter through allowed lvlbases

    #  if subjectbase_pk has value:
    #       if arr exists and not skip_allowed_filter:
    #           --> filter on subjectbase_pk_pk, only when subjectbase_pk_pk in arr, otherwise: return no records
    #       else:
    #           --> filter on subjectbase_pk_pk
    #  if subjectbase_pk_pk is None:
    #       if arr exists and not skip_allowed_filter:
    #           --> filter on subjectbase_pk_pk's in array
    #       else:
    #           --> no filter

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' +++++ get_userfilter_allowed_school_dep_lvl_subj_sct_cluster +++++')

    sql_clause = ""

    try:
        req_usr = request.user
        sql_clause_arr = []

        if table == 'studsubj':
            subjbase_id_fld= 'studsubj.subjbase_id'
        else:
            subjbase_id_fld = 'subj.base_id'

    # - get sel_examyear_instance
        sel_examyear_instance = get_selected_examyear_from_usersetting_short(request)

    # - get allowed_sections_dict from request
        allowed_sections_dict = acc_prm.get_userallowed_sections_dict_from_request(request)
        if logging_on:
            logger.debug('    allowed_sections_dict: ' + str(allowed_sections_dict) + ' ' + str(type(allowed_sections_dict)))
        #  allowed_sections_dict: {'2': {'1': {'5': [123]}}, '16': {'2': {'-9': [123]}, '3': {'-9': []}}, '17': {'3': {'-9': [160]}}} <class 'dict'>

    # - get selected_pk_dict from usersettings
        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if logging_on:
            logger.debug('    selected_pk_dict: ' + str(selected_pk_dict) + ' ' + str(type(selected_pk_dict)))
        # selected_pk_dict: {'sel_schoolbase_pk': 2, 'sel_examyear_pk': 4, 'sel_depbase_pk': 1, 'sel_examperiod': 1, 'sel_examtype': 'ce', 'sel_auth_index': 2, 'sel_lvlbase_pk': 5} <class 'dict'>

# +++ SCHOOL +++
        # - get selected school
        # - when role = school: selected school = req_usr.schoolbase
        # - otherwise: get selected school from settings
        # - if None: don't return records

        sel_schoolbase_pk = None
        if req_usr.role == c.ROLE_008_SCHOOL:
            if req_usr.schoolbase:
                sel_schoolbase_pk = req_usr.schoolbase_id
        else:
            # - check if schoolbase is allowed
            # when allowed_sections_dict is empty: selected school is always allowed
            schoolbase_pk_tobechecked = selected_pk_dict.get(c.KEY_SEL_SCHOOLBASE_PK)
            if schoolbase_pk_tobechecked:
                if allowed_sections_dict:
                    if str(schoolbase_pk_tobechecked) in allowed_sections_dict:
                        sel_schoolbase_pk = schoolbase_pk_tobechecked
                else:
                    sel_schoolbase_pk = schoolbase_pk_tobechecked

        sel_school = None
        if sel_examyear_instance and sel_schoolbase_pk:
            sel_school = sch_mod.School.objects.get_or_none(
                examyear=sel_examyear_instance,
                base_id=sel_schoolbase_pk
            )

        sel_depbase_pk = None
        allowed_depbases_dict = {}

        if sel_school is None:
            sql_clause_arr.append("(FALSE)")
        else:
            sql_clause_arr.append(''.join(("(school.base_id = ", str(sel_schoolbase_pk), "::INT)")))

    # +++ DEPARTMENT +++
            # - get allowed_depbases of selected school
            # sel_school_allowed_depbases_arr must always have at least 1 value
            sel_school_allowed_depbases_arr = list(
                map(int, sel_school.depbases.split(';'))) if sel_school.depbases else []
            if logging_on:
                logger.debug('    sel_school_allowed_depbases_arr: ' + str(sel_school_allowed_depbases_arr) + ' ' + str(
                    type(sel_school_allowed_depbases_arr)))
                # sel_school_allowed_depbases_arr: [1] <class 'list'>

        # - use depbase of selected school when school has only 1 department
            if len(sel_school_allowed_depbases_arr) == 1:
                depbase_pk_tobechecked = sel_school_allowed_depbases_arr[0]
            else:

        # - get saved_depbase_pk of req_usr
                depbase_pk_tobechecked = selected_pk_dict.get(c.KEY_SEL_DEPBASE_PK)
            if logging_on:
                logger.debug('    depbase_pk_tobechecked: ' + str(depbase_pk_tobechecked) + ' ' + str(
                    type(depbase_pk_tobechecked)))

            if depbase_pk_tobechecked:
                allowed_schoolbase_dict, allowed_depbases_pk_arr = \
                    acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(
                        userallowed_sections_dict=allowed_sections_dict,
                        sel_schoolbase_pk=sel_schoolbase_pk
                    )

                if logging_on:
                    logger.debug('    allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))
                    # allowed_schoolbase_dict:  {'1': {'5': [123]}}

                if str(depbase_pk_tobechecked) in allowed_schoolbase_dict and \
                        depbase_pk_tobechecked in sel_school_allowed_depbases_arr:
                    sel_depbase_pk = depbase_pk_tobechecked

            sel_department_instance = sch_mod.Department.objects.get_or_none(
                examyear=sel_examyear_instance,
                base_id=sel_depbase_pk
            )

            if sel_department_instance is None:
                sql_clause_arr.append("(FALSE)")

            else:
                sql_clause_arr.append(''.join(("(dep.base_id = ", str(sel_depbase_pk), "::INT)")))

    # +++ SELECTED SECTORBASE +++
                # - get selected sctbase_pk of req_usr
                saved_sctbase_pk = selected_pk_dict.get(c.KEY_SEL_SCTBASE_PK)
                if saved_sctbase_pk:
                    sql_clause_arr.append(''.join(("(sct.base_id = ", str(saved_sctbase_pk), "::INT)")))

    # +++ SELECTED CLUSTER +++
        # - get selected cluster_pk of req_usr
                saved_cluster_pk = selected_pk_dict.get(c.KEY_SEL_CLUSTER_PK)
                if saved_cluster_pk:
                    sql_clause_arr.append(''.join(("(studsubj.cluster_id = ", str(saved_cluster_pk), "::INT)")))

    # +++ LEVEL +++
                allowed_lvlbases_arr = []

                level_is_required = sel_department_instance.level_req

                # - get allowed_lvlbases_dict
                allowed_lvlbases_dict = get_requsr_allowed_lvlbases_dict(allowed_schoolbase_dict, sel_depbase_pk)
                if logging_on:
                    logger.debug('    level_is_required: ' + str(level_is_required))
                    logger.debug('    allowed_lvlbases_dict: ' + str(allowed_lvlbases_dict) + ' ' + str(
                        type(allowed_lvlbases_dict)))
                # allowed_lvlbases_dict: {'5': [123]}

                # - get array of allowed levels, [-9] when 'all levels'
                if level_is_required:
                    if allowed_lvlbases_dict:
                        for lvlbase_pk_str in allowed_lvlbases_dict:
                            allowed_lvlbases_arr.append(int(lvlbase_pk_str))
                if not allowed_lvlbases_arr:
                    allowed_lvlbases_arr.append(-9)

                # - sel_lvlbase_pk_arr contains the selected lvlbase or all allowed lvlbasescreate array of allowed depbases of requsr from allowed_schoolbase_dict and sel_school_allowed_depbases_arr
                sel_lvlbase_pk_arr = []

                if level_is_required:

        # - get saved_lvlbase_pk of req_usr
                    saved_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)
                    if logging_on:
                        logger.debug(
                            '    saved_lvlbase_pk: ' + str(saved_lvlbase_pk) + ' ' + str(type(saved_lvlbase_pk)))

                    # - filter only the saved_lvlbase_pk if exists and allowed
                    if saved_lvlbase_pk:
                        if str(saved_lvlbase_pk) in allowed_lvlbases_dict or \
                                '-9' in allowed_lvlbases_dict:
                            sel_lvlbase_pk_arr.append(saved_lvlbase_pk)
                    else:
                        # - filter all allowed lvlbases
                        if allowed_lvlbases_dict:
                            for sel_lvlbase_pk_str in allowed_lvlbases_dict:
                                sel_lvlbase_pk_arr.append(int(sel_lvlbase_pk_str))

                else:
                    # add '-9' when lvl not required (allowedsubjects are stored in lvl '-9'
                    sel_lvlbase_pk_arr.append(-9)

                if logging_on:
                    logger.debug('    sel_lvlbase_pk_arr: ' + str(sel_lvlbase_pk_arr) + ' ' + str(type(sel_lvlbase_pk_arr)))

                # format of lvl / subjc filter clause:
                #   - when lvl.base_id = -9 there is no filter on lvl.base_id, only on subjbase_pk
                #   - when subjbase_pk_arr is empty:
                #       - when role = corrector: dont show any subjbase_pk: filter: WHERE NOT lvl.base_id = 5
                #       - when other roles: show all subjects: filter: no filter
                #  AND (
                #        (subj.base_id IN (SELECT UNNEST(ARRAY[116, 145]::INT[])) OR
                #        (lvl.base_id = 5::INT AND subj.base_id IN (SELECT UNNEST(ARRAY[116, 145]::INT[])) OR
                #        (lvl.base_id = 6::INT AND subj.base_id = 116::INT)
                #       )

         # +++ loop through selected levels +++
                levelbases_clause_arr = []
                if sel_lvlbase_pk_arr:
                    for sel_lvlbase_pk in sel_lvlbase_pk_arr:

                        allowed_subjbases_arr = acc_prm.get_userallowed_subjbase_arr(allowed_lvlbases_dict, sel_lvlbase_pk)
                        if logging_on:
                            logger.debug('   +++++ ')
                            logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
                            logger.debug('    allowed_subjbases_arr: ' + str(allowed_subjbases_arr) + ' ' + str(
                                type(allowed_subjbases_arr)))
                            # allowed_subjbase_pk_arr: [123] <class 'list'>

                        len_allowed_subjbases_arr = len(allowed_subjbases_arr)

            # - create lvlbase_clause
                        lvlsubjbase_clause_arr = []
                        lvlbase_clause = None
                        if sel_lvlbase_pk == -9:
                            pass
                        elif len_allowed_subjbases_arr == 0 and req_usr.role == c.ROLE_016_CORR:
                            # when corrector: must have allowd_subjects, 'all' is not allowed
                            pass
                        else:
                            # - when not corrector: show allowed subjects or all subjects when allowed_subjbases_arr is empty
                            lvlbase_clause = ''.join(("lvl.base_id = ", str(sel_lvlbase_pk), "::INT"))
                        if lvlbase_clause:
                            lvlsubjbase_clause_arr.append(lvlbase_clause)
                        if logging_on:
                            logger.debug(' >  lvlbase_clause: ' + str(lvlbase_clause))

        # +++ SUBJECTBASES +++
                        subjbase_clause = ""

            # - get saved_subjbase_pk of req_usr
                        saved_subjbase_pk = selected_pk_dict.get(c.KEY_SEL_SUBJBASE_PK)
                        if logging_on:
                            logger.debug(
                                '    saved_subjbase_pk: ' + str(saved_subjbase_pk) + ' ' + str(type(saved_subjbase_pk)))

            # + loop through allowed subjects and add selected or allowed subjects
                        sel_subjbase_pk_arr = []
                        if allowed_subjbases_arr:
                            for subjbase_pk_int in allowed_subjbases_arr:
                                if not saved_subjbase_pk or subjbase_pk_int == saved_subjbase_pk:
                                    sel_subjbase_pk_arr.append(subjbase_pk_int)
                        len_subjbase_pk_arr = len(sel_subjbase_pk_arr)

            # - create subjbase_clause
                        if len_subjbase_pk_arr:
                            if len_subjbase_pk_arr == 1:
                                subjbase_clause = ''.join((subjbase_id_fld, " = ", str(sel_subjbase_pk_arr[0]), "::INT"))
                            else:
                                # unnest(ARRAY[10, 11, 12, 13, 14, 15, 16]
                                subjbase_clause = ''.join(
                                    (subjbase_id_fld, " IN (SELECT UNNEST(ARRAY", str(sel_subjbase_pk_arr), "::INT[]))"))
                        if subjbase_clause:
                            lvlsubjbase_clause_arr.append(subjbase_clause)

                        if logging_on:
                            logger.debug(
                                ' >  subjbase_clause: ' + str(subjbase_clause) + ' ' + str(type(subjbase_clause)))

            # - join lvlbase_clause and subjbase_clause
                        lvlsubjbase_clause = " AND ".join(lvlsubjbase_clause_arr)
                        if logging_on:
                            logger.debug(' >> lvlsubjbase_clause: ' + str(lvlsubjbase_clause))

                        if lvlsubjbase_clause:
                            levelbases_clause_arr.append(lvlsubjbase_clause)

        # +++ end of loop through levels
                if levelbases_clause_arr:
                    sql_clause_arr.append(''.join(('(', ' OR '.join(levelbases_clause_arr), ')')))

        sql_clause = ' AND '.join(sql_clause_arr)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug(' >>>sql_clause: ' + str(sql_clause))
        logger.debug('--- end of get_userfilter_allowed_subjbase: ')

    return sql_clause
# - end of get_userfilter_allowed_school_dep_lvl_subj_sct_cluster



def get_userfilter_allowed_schoolbase(request, sql_keys, sql_list, schoolbase_pk=None, skip_allowed_filter=False, table=None):
    # PR2022-03-13 PR2022-12-04
    #  if schoolbase_pk has value:
    #       if arr exists and not skip_allowed_filter:
    #           --> filter on schoolbase_pk_pk, only when schoolbase_pk_pk in arr, otherwise: return no records
    #       else:
    #           --> filter on schoolbase_pk_pk
    #  if schoolbase_pk_pk is None:
    #       if arr exists and not skip_allowed_filter:
    #           --> filter on schoolbase_pk_pk's in array
    #       else:
    #           --> no filter

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_userfilter_allowed_schoolbase_pk ----- ')
        logger.debug('    schoolbase_pk: ' + str(schoolbase_pk) + ' ' + str(type(schoolbase_pk)))

    filter_single_pk, filter_pk_arr, filter_none = None, None, False

    usergroups_arr, allowed_sections_dict, allowed_clusters_arr = get_request_userallowed(request)

    allowed_schoolbase_pk_arr = []
    if allowed_sections_dict:
        for schoolbase_pk_str in allowed_sections_dict:
            allowed_schoolbase_pk_arr.append(int(schoolbase_pk_str))
    if logging_on:
        logger.debug('allowed_schoolbase_pk_arr: ' + str(allowed_schoolbase_pk_arr) + ' ' + str(type(allowed_schoolbase_pk_arr)))

    if schoolbase_pk and schoolbase_pk != -9:
        if not allowed_schoolbase_pk_arr or str(schoolbase_pk) in allowed_schoolbase_pk_arr or skip_allowed_filter:
            filter_single_pk = schoolbase_pk
        else:
            filter_none = True

    elif allowed_schoolbase_pk_arr and not skip_allowed_filter:
        if len(allowed_schoolbase_pk_arr) == 1:
            filter_single_pk = allowed_schoolbase_pk_arr[0]
        else:
            filter_pk_arr = allowed_schoolbase_pk_arr
    # TODO 2022-11-24
    # allowed_schoolbase_pk_arr: ['{"2": {"1": {"4": ["120"]}}, "11": {"1": {"4": ["120"]}}}'] <class 'list'>

    # [2022-11-24 19:07:32] DEBUG [accounts.views.get_userfilter_allowed_schoolbase:2550]
    if logging_on:
        logger.debug('    allowed_schoolbase_pk_arr: ' + str(allowed_schoolbase_pk_arr) + ' ' + str(type(allowed_schoolbase_pk_arr)))
        logger.debug('    filter_single_pk: ' + str(filter_single_pk) + ' ' + str(type(filter_single_pk)))
        logger.debug('    filter_pk_arr: ' + str(filter_pk_arr) + ' ' + str(type(filter_pk_arr)))
        logger.debug('    filter_none: ' + str(filter_none) + ' ' + str(type(filter_none)))

    if filter_single_pk:
        sql_keys['sb_pk'] = filter_single_pk
        if table == 'studsubj':
            sql_list.append("AND studsubj.schoolbase_id = %(sb_pk)s::INT")
        else:
            sql_list.append("AND school.base_id = %(sb_pk)s::INT")
    elif filter_pk_arr:
        sql_keys['sb_arr'] = filter_pk_arr
        if table == 'studsubj':
            sql_list.append("AND studsubj.schoolbase_id IN ( SELECT UNNEST(%(sb_arr)s::INT[]) )")
        else:
            sql_list.append("AND school.base_id IN ( SELECT UNNEST(%(sb_arr)s::INT[]) )")
    elif filter_none:
        sql_list.append("AND FALSE")
# - end of get_userfilter_allowed_schoolbase



def get_userfilter_allowed_cluster(request, sql_keys, sql_list, cluster_pk=None, skip_allowed_filter=False, table=None):
    # PR2022-03-18
    # this function adds allowed_cluster filter to sql, or filters single cluster_pk

    #  if cluster_pk has value:
    #       if arr exists and not skip_allowed_filter:
    #           --> filter on cluster_pk, only when cluster_pk in arr, otherwise: return no records
    #       else:
    #           --> filter on cluster_pk
    #  if cluster_pk is None:
    #       if arr exists and not skip_allowed_filter:
    #           --> filter on cluster_pk's in array
    #       else:
    #           --> no filter

    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug('----- get_userfilter_allowed_cluster ----- ')
        logger.debug('cluster_pk: ' + str(cluster_pk) + ' ' + str(type(cluster_pk)))

    filter_single_pk, filter_pk_arr, filter_none = None, None, False

    allowed_cluster_arr = request.user.allowed_clusters.split(';') if request.user.allowed_clusters else []

    if cluster_pk:
        if not allowed_cluster_arr or str(cluster_pk) in allowed_cluster_arr or skip_allowed_filter:
            filter_single_pk = cluster_pk
        else:
            filter_none = True

    elif allowed_cluster_arr and not skip_allowed_filter:
        if len(allowed_cluster_arr) == 1:
            filter_single_pk = allowed_cluster_arr[0]
        else:
            filter_pk_arr = allowed_cluster_arr

    if logging_on:
        logger.debug('allowed_cluster_arr: ' + str(allowed_cluster_arr) + ' ' + str(type(allowed_cluster_arr)))
        logger.debug('filter_single_pk: ' + str(filter_single_pk) + ' ' + str(type(filter_single_pk)))
        logger.debug('filter_pk_arr: ' + str(filter_pk_arr) + ' ' + str(type(filter_pk_arr)))
        logger.debug('filter_none: ' + str(filter_none) + ' ' + str(type(filter_none)))

    if filter_single_pk:
        sql_keys['cls_pk'] = filter_single_pk
        if table == 'studsubj':
            sql_list.append("AND studsubj.cluster_id = %(cls_pk)s::INT")
        else:
            sql_list.append("AND cl.id = %(cls_pk)s::INT")

    elif filter_pk_arr:
        sql_keys['cls_arr'] = filter_pk_arr
        if table == 'studsubj':
            sql_list.append("AND studsubj.cluster_id IN ( SELECT UNNEST(%(cls_arr)s::INT[]) )")
        else:
            sql_list.append("AND cl.id IN ( SELECT UNNEST(%(cls_arr)s::INT[]) )")

    elif filter_none:
        sql_list.append("AND FALSE")
# - end of get_userfilter_allowed_cluster




"""

