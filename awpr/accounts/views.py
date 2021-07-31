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
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import activate, ugettext_lazy as _
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
from awpr import settings as s
from awpr import constants as c
from awpr import validators as v

from awpr import functions as af
from awpr import menus as awpr_menu

from schools import models as sch_mod

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
        headerbar_param = awpr_menu.get_headerbar_param(request, 'page_user', {'show_btn_userpermit': show_btn_userpermit} )
        if logging_on:
            logger.debug("show_btn_userpermit: " + str(show_btn_userpermit))
            logger.debug("headerbar_param: " + str(headerbar_param))
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'users.html', headerbar_param)

# How To Create Users Without Setting Their Password PR2018-10-09
# from https://django-authtools.readthedocs.io/en/latest/how-to/invitation-email.html

########################################################################
# === UserUploadView ===================================== PR2020-08-02
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
        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user
            # <PERMIT> PR2020-09-24
            #  - only perm_admin and perm_system can add / edit / delete users
            #  - only role_system and role_admin (ETE) can add users of other schools
            #  - role_system, role_admin, role_insp and role_school can add users of their own school

            requsr_usergroupslist = req_user.usergroups.split(';') if req_user.usergroups else []

            # requsr_permitlist: ['view_page', 'crud_otherschool', 'crud', 'crud', 'permit_userpage']
            requsr_permitlist = req_user.permit_list('page_user')

            has_permit_same_school, has_permit_all_schools = False, False
            if requsr_permitlist:
                has_permit_all_schools = 'permit_crud_otherschool' in requsr_permitlist
                has_permit_same_school = 'permit_crud_sameschool' in requsr_permitlist

            if logging_on:
                logger.debug('requsr_permitlist: ' + str(requsr_permitlist))
                logger.debug('has_permit_all_schools: ' + str(has_permit_all_schools))
                logger.debug('has_permit_same_school: ' + str(has_permit_same_school))

            if has_permit_same_school or has_permit_all_schools:
# - get upload_dict from request.POST
                upload_json = request.POST.get("upload")
                if upload_json:
                    upload_dict = json.loads(upload_json)

                    if logging_on:
                        logger.debug('upload_dict: ' + str(upload_dict))

                    # upload_dict: {'mode': 'validate', 'company_pk': 3, 'pk_int': 114, 'user_ppk': 3,
                    #               'employee_pk': None, 'employee_code': None, 'username': 'Giterson_Lisette',
                    #               'last_name': 'Lisette Sylvia enzo Giterson', 'email': 'hmeijs@gmail.com'}
                    # upload_dict: {'mode': 'delete', 'user_pk': 169, 'user_ppk': 3, 'mapid': 'user_169'}

    # - reset language
                    # PR2019-03-15 Debug: language gets lost, get req_user.lang again
                    user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                    activate(user_lang)

    # - get info from upload_dict
                    user_pk = upload_dict.get('user_pk')
                    user_schoolbase_pk = upload_dict.get('schoolbase_pk')
                    map_id = upload_dict.get('mapid')
                    mode = upload_dict.get('mode')

                    is_validate_only = (mode == 'validate')
                    update_wrap['mode'] = mode

                    if logging_on:
                        logger.debug('user_pk: ' + str(user_pk))
                        logger.debug('user_schoolbase_pk: ' + str(user_schoolbase_pk))
                        logger.debug('map_id: ' + str(map_id))
                        logger.debug('mode: ' + str(mode))

    # - check if the user schoolbase exists
                    user_schoolbase = sch_mod.Schoolbase.objects.get_or_none(
                        id=user_schoolbase_pk,
                        country=req_user.country
                    )
                    is_same_schoolbase = (user_schoolbase and user_schoolbase == req_user.schoolbase)

                    if logging_on:
                        logger.debug('user_schoolbase: ' + str(user_schoolbase))
                        logger.debug('is_same_schoolbase: ' + str(is_same_schoolbase))

                    # <PERMIT> PR2021-04-23
                    # user role can never be higher dan requser role

                    err_dict = {}
                    has_permit = False
                    if user_schoolbase:
                    # <PERMIT> PR2021-04-23
                    # user role can never be higher dan requser role
                        user_schoolbase_defaultrole = getattr(user_schoolbase, 'defaultrole')
                        if user_schoolbase_defaultrole is None:
                            user_schoolbase_defaultrole = 0
                        if user_schoolbase_defaultrole <= req_user.role:
                            if has_permit_all_schools:
                                has_permit = True
                            elif has_permit_same_school:
                                has_permit = is_same_schoolbase

                    if not has_permit:
                        err_dict['msg01'] = _("You don't have permission to perform this action.")
                    else:
                        updated_dict = {}

    # ++++  resend activation email ++++++++++++
                        if mode == 'resend_activation_email':
                            resend_activation_email(user_pk, update_wrap, err_dict, request)

    # ++++  delete user ++++++++++++
                        elif mode == 'delete':
                            if user_pk:
                                instance = None
                                if has_permit_all_schools:
                                    instance = acc_mod.User.objects.get_or_none(
                                        id=user_pk,
                                        country=req_user.country
                                    )
                                elif has_permit_same_school:
                                    instance = acc_mod.User.objects.get_or_none(
                                        id=user_pk,
                                        country=req_user.country,
                                        schoolbase=req_user.schoolbase
                                    )

                                if logging_on:
                                    logger.debug('instance: ' + str(instance))

                                if instance:
                                    deleted_instance_list = create_user_list(request, instance.pk)

                                    if logging_on:
                                        logger.debug('deleted_instance_list: ' + str(deleted_instance_list))

                                    if deleted_instance_list:
                                        updated_dict = deleted_instance_list[0]
                                        updated_dict['mapid'] = map_id

                                    if c.USERGROUP_ADMIN in requsr_usergroupslist and instance == req_user:
                                        err_dict['msg01'] = _("System administrators cannot delete their own account.")
                                    else:
                                        try:
                                            # PR2021-02-05 debug: CASCADE delete usersetting not working. Delete manually
                                            usersettings = Usersetting.objects.filter(user=instance)
                                            for usersetting in usersettings:

                                                if logging_on:
                                                    logger.debug('usersetting delete: ' + str(usersetting))
                                                usersetting.delete()
                                            instance.delete()
                                            updated_dict['deleted'] = True

                                            if logging_on:
                                                logger.debug('deleted: ' + str(True))
                                        except:
                                            err_dict['msg01'] = _("User '%(val)s' can not be deleted.\nInstead, you can make the user inactive.") \
                                                                % {'val': instance.username_sliced}

                                            if logging_on:
                                                logger.debug('err_dict msg01: ' + str(err_dict['msg01']))

    # ++++  create or validate new user ++++++++++++
                        elif mode in ('create', 'validate'):
                            # - get permits of new user.
                            #       - new_permits is 'write' when user_school is same as requsr_school,
                            #       - permits is 'write' plus 'admin' when user_school is different from requsr_school

                            is_existing_user = True if user_pk else False

                            if is_same_schoolbase:
                                new_usergroups = c.USERGROUP_EDIT
                            else:
                                new_usergroups = ';'.join((c.USERGROUP_EDIT, c.USERGROUP_ADMIN))
                            # - new user gets role from defaultrole of user_schoolbase

                            #   PR2021-02-06 debug: don't forget to set values of defaultrole in schoolbase!
                            # new_role = user_schoolbase.defaultrole

                            new_user_pk, err_dict, ok_dict = \
                                create_or_validate_user_instance(
                                    user_schoolbase=user_schoolbase,
                                    upload_dict=upload_dict,
                                    user_pk=user_pk,
                                    usergroups=new_usergroups,
                                    is_validate_only=is_validate_only,
                                    user_lang=user_lang,
                                    request=request
                                )

                            if err_dict:
                                update_wrap['msg_err'] = err_dict
                            if ok_dict:
                                update_wrap['msg_ok'] = ok_dict
                            # - new_user_pk has only value when new user is created, not when is_validate_only
                            # - create_user_list returns list of only 1 user
                            if new_user_pk:
                                created_instance_list = create_user_list(request, new_user_pk)
                                if created_instance_list:
                                    updated_dict = created_instance_list[0]
                                    updated_dict['created'] = True

                        else:
    # - +++++++++ update ++++++++++++
                            instance = None
                            if has_permit_all_schools:
                                instance = acc_mod.User.objects.get_or_none(id=user_pk, country=req_user.country)
                            elif has_permit_same_school:
                                instance = acc_mod.User.objects.get_or_none(
                                    id=user_pk,
                                    country=req_user.country,
                                    schoolbase=req_user.schoolbase
                                )

                            if logging_on:
                                logger.debug('user instance: ' + str(instance))

                            if instance:
                                err_dict, ok_dict = update_user_instance(instance, upload_dict, request)
                                if err_dict:
                                    update_wrap['msg_err'] = err_dict
                                if ok_dict:
                                    update_wrap['msg_ok'] = ok_dict
                                # - create_user_list returns list of only 1 user
                                updated_instance_list = create_user_list(request, instance.pk)
                                updated_dict = updated_instance_list[0] if updated_instance_list else {}
                                updated_dict['updated'] = True
                                updated_dict['mapid'] = map_id

    # - +++++++++ en of is update ++++++++++++
                        if updated_dict:
                            update_wrap['updated_userlist'] = [updated_dict]
                    if err_dict:
                        update_wrap['msg_err'] = err_dict
                    elif is_validate_only:
                        update_wrap['validation_ok'] = True

        # - create_user_list returns list of only 1 user
        #update_wrap['user_list'] = ad.create_user_list(request, instance.pk)
# - return update_wrap
        update_wrap_json = json.dumps(update_wrap, cls=af.LazyEncoder)
        return HttpResponse(update_wrap_json)
# === end of UserUploadView =====================================

########################################################################
# === UserDownloadPermitsView ===================================== PR2021-04-20
@method_decorator([login_required], name='dispatch')
class UserDownloadPermitsView(View):
    #  UserDownloadPermitsView is called from Users form
    #  it returns a HttpResponse, with all permits
    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('  ')
            logger.debug(' ========== UserDownloadPermitsView ===============')

        response = None
        if request.user is not None and request.user.country is not None:
            req_user = request.user
            # PR2021-05-25 debug. Don't use permit_list, to prevent locking out yourself
            permit_listNIU, requsr_usergroups_list = get_userpermit_list('page_user', req_user)
            has_permit = request.user.is_role_system and  'admin' in requsr_usergroups_list
            if logging_on:
                logger.debug('requsr_usergroups_list: ' + str(requsr_usergroups_list))
                logger.debug('has_permit: ' + str(has_permit))

            if has_permit:
                # - reset language
                # PR2019-03-15 Debug: language gets lost, get req_user.lang again
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

                permits_rows = create_permits_rows(request)
                response = create_permits_xlsx(permits_rows, user_lang, request)

        if response:
            return response
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

# - end of UserDownloadPermitsView


def create_permits_rows(request):
    # --- create list of permits_rows of this country PR2021-04-20

    sql_keys = {'country_id': request.user.country.pk}
    sql = ' '.join(("SELECT LOWER(c.abbrev) AS c_abbrev, p.page, p.action, p.role, p.usergroups",
                    "FROM accounts_userpermit AS p",
                    "INNER JOIN schools_country AS c ON (c.id = p.country_id)",
                    "WHERE c.id = %(country_id)s::INT",
                    'ORDER BY LOWER(c.abbrev), p.page, p.action, p.role'))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        permits_rows = af.dictfetchall(cursor)

    return permits_rows
# --- end of create_permits_rows


def create_permits_xlsx(permits_rows, user_lang, request):  # PR2021-04-20
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_permits_xlsx -----')

    # from https://stackoverflow.com/questions/16393242/xlsxwriter-object-save-as-http-response-to-create-download-in-django
    #logger.debug('period_dict: ' + str(period_dict))

# ---  create file Name and worksheet Name
    country_name = request.user.country.name
    today_dte = af.get_today_dateobj()
    today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

    title = ' '.join((str(_('Permissions')), str(_(' of ')), country_name))
    file_name = title + " " + today_dte.isoformat() + ".xlsx"
    worksheet_name = str(_('Permissions'))

# create the HttpResponse object ...
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = "attachment; filename=" + file_name

    field_names = ('c_abbrev', 'page', 'action', 'usergroups', 'role')

    field_width = (10, 20, 25, 40, 10, 10)

# .. and pass it into the XLSXWriter
    book = xlsxwriter.Workbook(response, {'in_memory': True})
    sheet = book.add_worksheet(worksheet_name)

    #cell_format = book.add_format({'bold': True, 'font_color': 'red'})
    bold = book.add_format({'bold': True})

    tblHead_format = book.add_format({'bold': True})
    tblHead_format.set_bottom()
    tblHead_format.set_bg_color('#d8d8d8') #   #d8d8d8;  /* light grey 218 218 218 100%

    for i, width in enumerate(field_width):
        sheet.set_column(i, i, width)

# --- title row
    # was: sheet.write(0, 0, str(_('Report')) + ':', bold)
    # sheet.write(0, 0, str(_('Report')) + ':')
    # sheet.write(0, 1, title)
    # sheet.write(1, 0, str(_('Country')) + ':')
    # sheet.write(1, 1, country_name)
    # sheet.write(2, 0, str(_('Created on ')) + ':')
    # sheet.write(2, 1, today_formatted)
    #row_index = 4

    row_index = 0
    for i, caption in enumerate(field_names):
        sheet.write(row_index, i, caption, tblHead_format)

    rows_length = len(permits_rows)
    if rows_length:
        #first_detail_row = row_index + 1
        #last_detail_row = row_index + rows_length
        for row in permits_rows:
            row_index +=1
            for i, field_name in enumerate(field_names):
                value = row.get(field_name)
                if value is not None:
                    sheet.write(row_index, i, value)

    book.close()
    return response

# --- end of create_permits_xlsx

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@



########################################################################
# === UserpermitUploadView ===================================== PR2021-03-18
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
            req_user = request.user
            has_permit = (req_user.role == c.ROLE_128_SYSTEM)

            if has_permit:
# -  get user_lang
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
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
                        logger.debug('mode:     ' + str(mode))
                        logger.debug('role:     ' + str(role) + ' ' + str(type(role)))
                        logger.debug('page:     ' + str(page))
                        logger.debug('action:   ' + str(action))
                        logger.debug('userpermit_pk:   ' + str(userpermit_pk))

                    append_dict = {}
                    error_dict = {}
                    updated_permit_rows = []

# +++  get current permit - when mode is 'create': permit is None. It will be created at "elif mode == 'create'"
                    instance = acc_mod.Userpermit.objects.get_or_none(
                        pk=userpermit_pk
                    )
                    if logging_on:
                        logger.debug('instance: ' + str(instance))

# +++  delete permit ++++++++++++
                    if mode == 'delete':
                        if instance:
                            try:
                                instance.delete(request=request)
                                # - add deleted_row to updated_permit_rows
                                updated_permit_rows.append({'userpermit_pk': userpermit_pk,
                                                  'mapid': 'userpermit_' + str(userpermit_pk),
                                                  'deleted': True})
                                if logging_on:
                                    logger.debug('instance: ' + str(instance))

                            except Exception as e:
                                logger.error(getattr(e, 'message', str(e)))
                                append_dict['err_delete'] = getattr(e, 'message', str(e))

# ++++  create new permit ++++++++++++
                    elif mode == 'create':
                        if page and action:
                            try:
                                if role is None:
                                    role_list = (c.ROLE_008_SCHOOL, c.ROLE_016_COMM, c.ROLE_032_INSP, c.ROLE_064_ADMIN, c.ROLE_128_SYSTEM)
                                else:
                                    role_list = (role,)

                                for value in role_list:
                                    instance = acc_mod.Userpermit(
                                        country=request.user.country,
                                        role=value,
                                        page=page,
                                        action=action
                                    )
                                    instance.save()
                            except Exception as e:
                                logger.error('e: ' + str(e))
                                append_dict['err_create'] = getattr(e, 'message', str(e))
                            finally:
                                append_dict['created'] = True

# +++ update existing studsubj - also when studsubj is created - studsubj is None when deleted
                    if instance and mode in ('create', 'update'):
                        update_grouppermit(instance, upload_dict, error_dict, request)
                    if logging_on and error_dict:
                        logger.debug('error_dict: ' + str(error_dict))

# - add update_dict to update_wrap
                    if instance:
                        if error_dict:
                            append_dict['error'] = error_dict

               # - add update_dict to update_wrap
                        if instance.pk:
                            permit_row = create_permit_list(instance.pk)
                            if permit_row:
                                update_wrap['updated_permit_rows'] = permit_row

# F. return update_wrap
            return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UserpermitUploadView


def update_grouppermit(instance, upload_dict, msg_dict, request):
    # --- update existing and new instance PR2021-03-20
    # add new values to update_dict (don't reset update_dict, it has values)
    logger.debug(' ------- update_grouppermit -------')
    logger.debug('upload_dict' + str(upload_dict))

    save_changes = False
    for field, new_value in upload_dict.items():
        if field in ['role', 'page', 'action']:
            saved_value = getattr(instance, field)
            logger.debug('field:       ' + str(field))
            logger.debug('saved_value: ' + str(saved_value) + str(type(saved_value)))
            logger.debug('new_value:   ' + str(new_value) + str(type(new_value)))

            if new_value and new_value != saved_value:
                setattr(instance, field, new_value)
                save_changes = True

        elif field == 'usergroups':
            # 'permits': {'group_read': True}}
            usergroups_haschanged = update_usergroups(instance, new_value, False, request)  # False = don't validate
            if usergroups_haschanged:
                save_changes = True

    # - save changes`
    logger.debug('save_changes' + str(save_changes) + str(type(save_changes)))
    if save_changes:
        try:
            instance.save(request=request)
        except Exception as e:
            msg_dict['err_update'] = getattr(e, 'message', str(e))
            #msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')
    logger.debug('msg_dict' + str(msg_dict) + str(type(msg_dict)))
# --- end of update_grouppermit


@method_decorator([login_required], name='dispatch')
class UserSettingsUploadView(UpdateView):  # PR2019-10-09

    def post(self, request, *args, **kwargs):
        #logger.debug(' ============= UserSettingsUploadView ============= ')

        update_wrap = {}
        if request.user is not None and request.user.country is not None:
            req_user = request.user
# - get upload_dict from request.POST
            upload_json = request.POST.get('upload')
            if upload_json:
                upload_dict = json.loads(upload_json)
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
    #logger.debug('  === SignupActivateView =====')
    #logger.debug('request: ' + str(request))
    #logger.debug('uidb64: ' + str(uidb64))
    #logger.debug('token: ' + str(token))

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
    except (TypeError, ValueError, OverflowError):
        user = None
    #logger.debug('user: ' + str(user))
    #logger.debug('user.is_authenticated: ' + str(user.is_authenticated))
    #logger.debug('user.activated: ' + str(user.activated))

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
        #logger.debug('activation_token_ok: ' + str(activation_token_ok))

        if not activation_token_ok:
            update_wrap['msg_01'] = _('The link to active your account is no longer valid.')
            update_wrap['msg_02'] = _('Maybe it has expired or has been used already.')
            update_wrap['msg_03'] = _('The link expires after 7 days.')

    # don't activate user and company until user has submitted valid password
    update_wrap['activation_token_ok'] = activation_token_ok
    #logger.debug('update_wrap: ' + str(update_wrap))

    if request.method == 'POST':
        #logger.debug('request.POST' + str(request.POST))
        form = SetPasswordForm(user, request.POST)
        #logger.debug('form: ' + str(form))

        form_is_valid = form.is_valid()

        non_field_errors = af.get_dict_value(form, ('non_field_errors',))
        field_errors = [(field.label, field.errors) for field in form]
        #logger.debug('non_field_errors' + str(non_field_errors))
        #logger.debug('field_errors' + str(field_errors))
        #logger.debug('form_is_valid' + str(form_is_valid))

        if form_is_valid:
            #logger.debug('form_is_valid' + str(form_is_valid))
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
            #logger.debug('user.saved: ' + str(user))

            #login_user = authenticate(username=user.username, password=password1)
            #login(request, login_user)
            login(request, user)
            #logger.debug('user.login' + str(user))
            #if request.user:
            #    update_wrap['msg_01'] = _("Congratulations.")
            #    update_wrap['msg_02'] = _("Your account is succesfully activated.")
           #     update_wrap['msg_03'] = _('You are now logged in to AWP-online.')
        else:
            # TODO check if this is correct when user enters wrong password PR2021-02-05
            form = SetPasswordForm(user)
            #logger.debug('form: ' + str(form))
            update_wrap['form'] = form
    else:
        form = SetPasswordForm(user)
        #logger.debug('form: ' + str(form))
        update_wrap['form'] = form
    update_wrap['newuser_activated'] = newuser_activated
    # PR2021-02-05 debug: when a new user tries to activat his account
    #                     and a different user is already logged in in the same browser,
    #                     in form value user.activated = True and passwoord form does not show.
    #                     use variable 'newuser_activated' and add this error trap to form:
    #                     {% elif user.is_authenticated and user.activated and not newuser_activated %}
    #                     instead of  {% elif user.is_authenticated %}
    #logger.debug('activation_token_ok: ' + str(activation_token_ok))
    #logger.debug('user.is_authenticated: ' + str(user.is_authenticated))
    #logger.debug('user.activated: ' + str(user.activated))
    #logger.debug('newuser_activated: ' + str(newuser_activated))
    #logger.debug('update_wrap: ' + str(update_wrap))
    # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
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


# === resend_activation_email ===================================== PR2020-08-15
def resend_activation_email(user_pk, update_wrap, err_dict, request):
    #  resend_activation_email is called from table Users, field 'activated' when the activation link has expired.
    #  it sends an email to the user
    #  it returns a HttpResponse, with ok_msg or err-msg

    user = acc_mod.User.objects.get_or_none(id=user_pk, country= request.user.country)
    #logger.debug('user: ' + str(user))
    has_error = False
    if user:
        update_wrap['user'] = {'pk': user.pk, 'username': user.username}

        current_site = get_current_site(request)

# - check if user.email is a valid email address:
        msg_err = v.validate_email_address(user.email)
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
                })
                # PR2018-04-25 arguments: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
                mail_count = send_mail(subject, message, from_email, [user.email], fail_silently=False)
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
# === end of resend_activation_email =====================================

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

        email_message.send()

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
        #logger.debug(' ----- save -----')
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
        #logger.debug('schoolcode: ' + str(schoolcode))
        #logger.debug('schoolbase_id: ' + str(schoolbase_id))

        email = self.cleaned_data["email"]

        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        email_field_name = UserModel.get_email_field_name()

        #logger.debug('email: ' + str(email))
        #logger.debug('email_field_name: ' + str(email_field_name))

        for user in self.get_users(schoolbase_id, email):
            user_email = getattr(user, email_field_name)
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

        if self.user is not None:
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
class UserDeleteView(DeleteView):
    model = User
    success_url = reverse_lazy('user_list_url')


def csrf_failure(request, reason=""):
    ctx = {'message': 'some custom messages'}
    return render_to_response(your_custom_template, ctx)



def create_user_list(request, user_pk=None):
    # --- create list of all users of this school, or 1 user with user_pk PR2020-07-31
    #logger.debug(' =============== create_user_list ============= ')
    #logger.debug('user_pk: ' + str(user_pk))

    #ROLE_008_SCHOOL = 8
    #ROLE_032_INSP = 32
    #ROLE_064_ADMIN = 64
    #ROLE_128_SYSTEM = 128

    # <PERMIT> PR2020-10-12
    # PR2018-05-27 list of users in UserListView:
    # - only perm_system and perm_admin can create user_list
    # - role teacher, student have no access
    # - dont show users with higher role
    # - when role is inspection or school: show only users of request.user.schoolbase
    # - when user_pk has value the school of user_pk can be different from the school of request user (in case of admin(ETE) )

    user_list = []
    if request.user.country and request.user.schoolbase:
        if request.user.role >= c.ROLE_008_SCHOOL:
            #if request.user.is_usergroup_admin:
            if True:

                sql_keys = {'country_id': request.user.country.pk, 'max_role': request.user.role}
                sql_list = ["SELECT u.id, u.schoolbase_id,",
                    "CONCAT('user_', u.id) AS mapid, 'user' AS table,",
                    "SUBSTRING(u.username, 7) AS username,",
                    "u.last_name, u.email, u.role, u.usergroups,",

                    "u.activated, u.activated_at, u.is_active, u.last_login, u.date_joined,",
                    "u.country_id, c.abbrev AS c_abbrev, sb.code AS sb_code, u.schoolbase_id,",
                    "u.lang, u.modified_by_id, u.modified_at",

                    "FROM accounts_user AS u",
                    "INNER JOIN schools_country AS c ON (c.id = u.country_id)",
                    "LEFT JOIN schools_schoolbase AS sb ON (sb.id = u.schoolbase_id)",
                    "WHERE u.country_id = %(country_id)s::INT",
                    "AND role <= %(max_role)s::INT"]
                if user_pk:
                    sql_keys['u_id'] = user_pk
                    sql_list.append('AND u.id = %(u_id)s::INT')
                elif request.user.role < c.ROLE_064_ADMIN:
                    schoolbase_pk = request.user.schoolbase.pk if request.user.schoolbase.pk else 0
                    sql_keys['sb_id'] = schoolbase_pk
                    sql_list.append('AND u.schoolbase_id = %(sb_id)s::INT')

                sql_list.append('ORDER BY LOWER(sb.code), LOWER(u.username)')

                sql = ' '.join(sql_list)

                newcursor = connection.cursor()
                newcursor.execute(sql, sql_keys)
                user_list = af.dictfetchall(newcursor)
    return user_list


########################################################################

def create_permit_list(permit_pk=None):
    # --- create list of all permits PR2021-03-18
    #logger.debug(' =============== create_permit_list ============= ')

    sql_keys = {}
    sql_list = ["SELECT p.id, CONCAT('userpermit_', p.id::TEXT) AS mapid,",
                "p.action, p.role, p.page, p.usergroups",
                "FROM accounts_userpermit AS p",
                ]
    if permit_pk:
        sql_keys['pk'] = permit_pk
        sql_list.append("WHERE p.id = %(pk)s::INT")
    else:
        sql_list.append("ORDER BY p.action")
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    return rows
# - end of create_permit_list

# TODO to be replaced by req_usr.permit_list('page_xxx') PR2021-07-03

def get_userpermit_list(page, req_user):
    # --- create list of all permits and usergroups of req_usr PR2021-03-19
    logging_on = False  # s.LOGGING_ON

    role = req_user.role

    requsr_usergroups_list = []
    if req_user.usergroups:
        requsr_usergroups_list = req_user.usergroups.split(';')
    if logging_on:
        logger.debug('=============== get_userpermit_list ============= ')
        logger.debug('page:                   ' + str(page) + ' ' + str(type(page)))
        logger.debug('requsr_usergroups_list: ' + str(requsr_usergroups_list) + ' ' + str(type(requsr_usergroups_list)))

    permit_list = []
    if role and page:
        sql_filter = ""
        for usergroup in requsr_usergroups_list:
            sql_filter += " OR (POSITION('" + usergroup + "' IN p.usergroups) > 0)"

        if sql_filter:
            sql_filter = "AND (" + sql_filter[4:] + ")"

            sql_keys = {'page': page, 'role': role}
            sql_list = ["SELECT p.action FROM accounts_userpermit AS p",
                        "WHERE (p.page = %(page)s OR p.page = 'page_all') AND p.role = %(role)s::INT",
                        sql_filter
                        ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                for row in cursor.fetchall():
                    if row[0]:
                        permit = 'permit_' + row[0]
                        if permit not in permit_list:
                            permit_list.append(permit)

    if logging_on:
        logger.debug('permit_list: ' + str(permit_list) + ' ' + str(type(permit_list)))

    return permit_list, requsr_usergroups_list
# - end of get_userpermit_list

########################################################################


# === create_or_validate_user_instance ========= PR2020-08-16 PR2021-01-01

def create_or_validate_user_instance(user_schoolbase, upload_dict, user_pk, usergroups, is_validate_only, user_lang, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('-----  create_or_validate_user_instance  -----')
        logger.debug('upload_dict: ' + str(upload_dict))
        logger.debug('user_pk: ' + str(user_pk))
        logger.debug('is_validate_only: ' + str(is_validate_only))

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
    #logger.debug('username: ' + str(username))
    schoolbaseprefix = user_schoolbase.prefix if user_schoolbase else None
    msg_err = v.validate_unique_username(username, schoolbaseprefix, user_pk)
    if msg_err:
        err_dict['username'] = msg_err
        has_error = True

# - check if namelast is blank
    last_name = upload_dict.get('last_name')
    #logger.debug('last_name: ' + str(last_name))
    msg_err = v.validate_notblank_maxlength(last_name, c.MAX_LENGTH_NAME, _('The name'))
    if msg_err:
        err_dict['last_name'] = msg_err
        has_error = True

# - check if this is a valid email address:
    email = upload_dict.get('email')
    #logger.debug('email: ' + str(email))
    msg_err = v.validate_email_address(email)
    if msg_err:
        err_dict['email'] = msg_err
        has_error = True

# - check if this email address already exists
    else:
        msg_err = v.validate_unique_useremail(email, country, user_schoolbase, user_pk)
        if msg_err:
            err_dict['email'] = msg_err
            has_error = True

    if not is_validate_only and not has_error:
    # - get now
        # timezone.now() is timezone aware, based on the USE_TZ setting;
        # datetime.now() is timezone naive. PR2018-06-07
        now_utc = timezone.now()

    # - new user gets role from defaultrole of user_schoolbase
    #   PR2021-02-06 debug: don't forget to set values of defaultrole in schoolbase!
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
            usergroups=usergroups,
            is_active=True,
            activated=False,
            lang=user_lang,
            modified_by=request.user,
            modified_at=now_utc)
        new_user.save()

        #logger.debug('new_user: ' + str(new_user))
        if new_user:
            new_user_pk = new_user.pk

            current_site = get_current_site(request)

# -  create first line of email
            # {{ requsr_schoolname }} {% trans 'has made the following AWP-online account for you:' %}
            # When requser and new_user are from the same school: requser.last_name
            # - get selected examyear from request_item_setting, Usersetting or first in list

            sel_examyear, examyear_save_NIU, may_select_NIU = af.get_sel_examyear_instance(request)
            requsr_school = sch_mod.School.objects.get_or_none( base=request.user.schoolbase, examyear=sel_examyear)
            new_user_school = sch_mod.School.objects.get_or_none( base=user_schoolbase, examyear=sel_examyear)

            req_user = request.user.last_name if request.user.last_name else request.user.username
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
                'req_user': req_user,
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

    return new_user_pk, err_dict, ok_dict

# - +++++++++ end of create_or_validate_user_instance ++++++++++++

# === update_user_instance ========== PR2020-08-16 PR2020-09-24 PR2021-03-24 PR2021-07-22
def update_user_instance(instance, upload_dict, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('-----  update_user_instance  -----')
        logger.debug('instance: ' + str(instance))
        logger.debug('upload_dict: ' + str(upload_dict))
    has_error = False
    err_dict = {}
    ok_dict = {}

    if instance:
        country = request.user.country
        usr_schoolbase = instance.schoolbase
        user_pk = instance.pk

        data_has_changed = False
        # upload_dict: {'mode': 'update', 'schoolbase_pk': 23, 'username': 'Ete', 'last_name': 'Ete2',
        #           'email': 'hmeijs@gmail.com', 'user_pk': 41}
        for field, field_value in upload_dict.items():

            if logging_on:
                logger.debug('field: ' + str(field))
                logger.debug('field_value: ' + str(field_value))

            if field in ('username', 'last_name', 'email', 'usergroups', 'is_active'):
# - check if this username already exists in this school, exept for this user
                if field == 'username':
                    new_username = field_value
                    msg_err = v.validate_unique_username(new_username, usr_schoolbase.prefix, user_pk)

                    if logging_on:
                        logger.debug('new_username: ' + str(new_username))
                        logger.debug('msg_err: ' + str(msg_err))

                    if msg_err:
                        err_dict[field] = msg_err
                        has_error = True
                    if not has_error and new_username and new_username != instance.username:
                        prefixed_username = usr_schoolbase.prefix + new_username
                        instance.username = prefixed_username
                        data_has_changed = True

# - check if namelast is blank
                elif field == 'last_name':
                    new_last_name = field_value
                    msg_err = v.validate_notblank_maxlength(new_last_name, c.MAX_LENGTH_NAME, _('The name'))

                    if logging_on:
                        logger.debug('new_last_name: ' + str(new_last_name))
                        logger.debug('msg_err: ' + str(msg_err))

                    if msg_err:
                        err_dict[field] = msg_err
                        has_error = True
                    if not has_error and new_last_name and new_last_name != instance.last_name:
                        instance.last_name = new_last_name
                        data_has_changed = True

# - check if this is a valid email address:
                elif field == 'email':
                    new_email = field_value
                    msg_err = v.validate_email_address(new_email)

                    if logging_on:
                        logger.debug('new_email: ' + str(new_email))
                        logger.debug('msg_err: ' + str(msg_err))

                    if msg_err:
                        err_dict[field] = msg_err
                        has_error = True
# - check if this email address already exists
                    else:
                        msg_err = v.validate_unique_useremail(new_email, country, usr_schoolbase, user_pk)
                        if msg_err:
                            err_dict[field] = msg_err
                            has_error = True

                    if not has_error and new_email and new_email != instance.email:
                        instance.email = new_email
                        data_has_changed = True

                elif field == 'usergroups':
                    # field_value is dict: {read: true}
                    usergroups_haschanged = update_usergroups(instance, field_value, True, request) # True = validate
                    if usergroups_haschanged:
                        data_has_changed = True

            # - sysadmins cannot remove sysadmin permission from their own account
                    """
                    if request.user.is_usergroup_admin:
                        if permit_field in ('perm_admin', 'perm_system'):
                            if instance == request.user:
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

                            instance.permits = new_permit_sum
                            data_has_changed = True
                        """
                elif field == 'is_active':
                    new_isactive = field_value if field_value else  False
                    # sysadmins cannot remove is_active from their own account
                    if request.user.is_usergroup_admin and instance == request.user:
                        if not new_isactive:
                            err_dict[field] = _("System administrators cannot make their own account inactive.")
                            has_error = True
                    if not has_error and new_isactive != instance.is_active:
                        instance.is_active = new_isactive
                        data_has_changed = True

# -  update user
        if not has_error:
            if data_has_changed:
# - get now without timezone
                now_utc_naive = datetime.utcnow()
                now_utc = now_utc_naive.replace(tzinfo=pytz.utc)

                try:
                    instance.modifiedby = request.user
                    instance.modifiedat = now_utc
                    instance.save()
                    ok_dict = {'msg01':  _("The changes have been saved successfully.")}
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))
                    err_dict['save'] = {'msg01':  _('An error occurred.'),
                                        'msg02': str(e),
                                        'msg03':  _('The changes have not been saved.')}

    if logging_on:
        logger.debug('ok_dict: ' + str(ok_dict))
        logger.debug('err_dict: ' + str(err_dict))

    return err_dict, ok_dict
# - +++++++++ end of update_user_instance ++++++++++++

# === update_usergroups ===================================== PR2021-03-24

def update_usergroups(instance, field_dict, validate, request):
    # called by UserUploadView.update_user_instance and UserpermitUploadView.update_grouppermit
    # validate only when called by update_user_instance
    # usergroups: {auth2: false}
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('-----  update_usergroups  -----')
        logger.debug('field_dict: ' + str(field_dict))
        logger.debug('validate: ' + str(validate))

    saved_usergroups_str = instance.usergroups
    saved_usergroups_list = []
    data_has_changed = False
    if instance.usergroups:
        saved_usergroups_list = instance.usergroups.split(';')

    if logging_on:
        logger.debug('saved_usergroups_str:  ' + str(saved_usergroups_str))
        logger.debug('saved_usergroups_list: ' + str(saved_usergroups_list))

    if field_dict:
        for usergroup, new_value in field_dict.items():
            new_value = False if new_value is None else new_value
            if logging_on:
                logger.debug('usergroup: ' + str(usergroup))
                logger.debug('new_value: ' + str(new_value))

            if new_value:
        # - remove other 'auth' usergroups when usergroup = 'auth123' is set to True
        #   only when called by update_user_instance
                if validate:
                    auth_list = (c.USERGROUP_AUTH1_PRES, c.USERGROUP_AUTH2_SECR, c.USERGROUP_AUTH3_COM)
                    if usergroup in auth_list:
                        for auth in auth_list:
                            if auth != usergroup:
                                if auth in saved_usergroups_list:
                                    saved_usergroups_list.remove(auth)
                if usergroup not in saved_usergroups_list:
                    saved_usergroups_list.append(usergroup)
            else:
                if usergroup in saved_usergroups_list:
        # - admin cannot remove his own admin usergroup
        #   only when called by update_user_instance
                    if validate and \
                            instance.pk == request.user.pk and \
                            usergroup == c.USERGROUP_ADMIN and \
                            request.user.usergroups and c.USERGROUP_ADMIN in request.user.usergroups:
                        if logging_on:
                            logger.debug('pass: request.user.usergroups: ' + str(request.user.usergroups))
                        pass
                    else:
                        saved_usergroups_list.remove(usergroup)

    # sort the list before saving, to be able to compare new and saved usergroups
    saved_usergroups_list.sort()

    if logging_on:
        logger.debug('saved_usergroups_list: ' + str(saved_usergroups_list))

    new_usergroups_str = ';'.join(saved_usergroups_list)
    if logging_on:
        logger.debug('new_usergroups_str: ' + str(new_usergroups_str))
    if new_usergroups_str != saved_usergroups_list:
        setattr(instance, 'usergroups', new_usergroups_str)
        data_has_changed = True

    return data_has_changed


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
    if permit_field != "perm_auth3" and c.USERGROUP_AUTH3_COM in permit_list:
        permit_list.remove(c.USERGROUP_AUTH3_COM)


def has_permit(permits_int, permit_index): # PR2020-10-12 separate function made PR2021-01-18
    has_permit = False
    if permits_int:
        permits_tuple = get_permits_tuple(permits_int)
        has_permit = permit_index in permits_tuple
    return has_permit


# +++++++++++++++++++  get and set setting +++++++++++++++++++++++
def get_usersetting_dict(key_str, request):  # PR2019-03-09 PR2021-01-25
    # function retrieves the string value of the setting row that match the filter and converts it to a dict
    # logger.debug(' ---  get_usersetting_dict  ------- ')
    #  json.dumps converts a dict in a json object
    #  json.loads retrieves a dict (or other type) from a json object

    # logger.debug('cls: ' + str(cls) + ' ' + str(type(cls)))
    setting_dict = {}
    row_setting = None
    try:
        if request.user and key_str:
            row = Usersetting.objects.filter(user=request.user, key=key_str).order_by('-id').first()
            if row:
                row_setting = row.setting
                if row_setting:
                    setting_dict = json.loads(row_setting)
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        logger.error('key_str: ', str(key_str))
        logger.error('row_setting: ', str(row_setting))

    return setting_dict


def set_usersetting_dict(key_str, setting_dict, request):  # PR2019-03-09 PR2021-01-25
    # function saves setting in first row that matches the filter, adds new row when not found
    # logger.debug('---  set_usersetting_dict  ------- ')
    # logger.debug('key_str: ' + str(key_str))
    # logger.debug('setting_dict: ' + str(setting_dict))
    # logger.debug('cls: ' + str(cls) + ' ' + str(type(cls)))

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
        logger.error('setting_dict: ', str(setting_dict))

# - end of set_usersetting_dict

def set_usersetting_from_uploaddict(upload_dict, request):  # PR2021-02-07
    # logger.debug(' ----- set_usersetting_from_uploaddict ----- ')
    # upload_dict: {'selected_pk': {'sel_subject_pk': 46}}
    # logger.debug('upload_dict: ' + str(upload_dict))
    # PR2020-07-12 debug. creates multiple rows when key does not exist ans newdict has multiple subkeys
    # PR2020-10-04 not any more, don't know why
    # - loop through keys of upload_dict
    for key, new_setting_dict in upload_dict.items():
        set_usersetting_from_upload_subdict(key, new_setting_dict, request)

# - end of set_usersetting_from_uploaddict

def set_usersetting_from_upload_subdict(key_str, new_setting_dict, request):  # PR2021-02-07
    # logger.debug(' ----- set_usersetting_from_upload_subdict ----- ')
    # upload_dict: {'selected_pk': {'sel_subject_pk': 46}}
    # logger.debug('upload_dict: ' + str(upload_dict))
    # PR2020-07-12 debug. creates multiple rows when key does not exist ans newdict has multiple subkeys
    # PR2020-10-04 not any more, don't know why
    # - loop through keys of upload_dict

    # key = 'page_examyear', dict = {'sel_btn': 'examyears'}
    saved_settings_dict = get_usersetting_dict(key_str, request)
    # logger.debug('new_setting_dict: ' + str(new_setting_dict))
    # logger.debug('saved_settings_dict: ' + str(saved_settings_dict))

    try:
    # - loop through subkeys of new settings
        for subkey, value in new_setting_dict.items():
            # new_setting_dict: {'sel_subject_pk': 46}
            # - if subkey has value in saved_settings_dict: replace saved value with new value
            if subkey in saved_settings_dict:
                if value:
                    saved_settings_dict[subkey] = value
                else:
                    # - if subkey has no value in saved_settings_dict: remove key from dict
                    saved_settings_dict.pop(subkey)
            else:
                # - if subkey not found in saved_settings_dict and value is not None: create subkey with value
                if value:
                    saved_settings_dict[subkey] = value
        # logger.debug('Usersetting.set_setting from UserSettingsUploadView')
        # - save key in usersetting and return settings_dict
        set_usersetting_dict(key_str, saved_settings_dict, request)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        logger.error('key_str: ', str(key_str))
        logger.error('setting_dict: ', str(new_setting_dict))

    return saved_settings_dict
# - end of set_usersetting_from_upload_subdict



"""
class AwpPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'registration/password_change_done.html'
    title = _('Password change successful')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class TransactionImportConfirmView(FormView):
    template_name = "import.html"
    form_class = TransactionFormSet
    success_url = reverse_lazy("accounts.transaction.list")

    def get_form_kwargs(self):
        kwargs = super(TransactionImportConfirmView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


# PR2018-04-13
class UserAddForm(UserCreationForm):
    interests = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self):
        # save(commit=False) returns an object that hasn't yet been saved to the database.
        user = super().save(commit=False)
        user.is_student = True
        user.save()
        student = Student.objects.create(user=user)
        student.interests.add(*self.cleaned_data.get('interests'))
        return user
"""