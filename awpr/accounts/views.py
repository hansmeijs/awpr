from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required  # PR2018-04-01
from django.contrib.auth.mixins import UserPassesTestMixin  # PR2018-11-03
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.core.mail import send_mail

from django.db import connection
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import ListView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import PasswordResetConfirmView # PR2018-10-14
from django.contrib.auth.forms import SetPasswordForm # PR2018-10-14
from django.views.decorators.debug import sensitive_post_parameters # PR2018-10-14
from django.views.decorators.csrf import csrf_protect # PR2018-10-14
from django.contrib.auth import update_session_auth_hash # PR2018-10-14
from django.views.decorators.cache import never_cache # PR2018-10-14
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, get_user_model, login as auth_login,
    logout as auth_logout, update_session_auth_hash,
)

from .forms import UserActivateForm
from .tokens import account_activation_token
from .models import User, User_log, Usersetting

from accounts import models as am
from awpr import constants as c
from awpr import validators as v

from awpr import functions as af
from awpr import menus as awpr_menu

from schools import models as sch_mod
from schools import functions as sch_fnc


from datetime import datetime
import pytz
import json
import logging
logger = logging.getLogger(__name__)

@method_decorator([login_required], name='dispatch')
class UserListView(ListView):

    def get(self, request, *args, **kwargs):
        User = get_user_model()
        #logger.debug(" =====  UserListView  =====")
        #PR2018-04-24 get all user of the country of the current user (for inspection users)
        #users = User.objects.filter(id__schoolcode_id__country=request_country)

        # PR2018-05-27 list of users in UserListView:
        # - when role is system: show all users
        # - when role is inspection: all users with role 'inspection' and country == request_user.country
        # - else (role is school): all users with role 'school' and schoolcode == request_user.schooldefault

        # logger.debug('UserListView get self: ' + str(self))
        # logger.debug('UserListView get request.user: ' + str(request.user))

        users = None  # User.objects.filter(False) gives error: 'bool' object is not iterable
        if request.user.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
            if request.user.is_role_system:
                users = User.objects.order_by('username').all()
            elif request.user.is_role_insp:
                if request.user.country is not None:
                    # filter only users from this country, with role == insp
                    users = User.objects.filter(country=request.user.country, role__lte=c.ROLE_032_INSP).order_by('username')
            else:
                if request.user.schoolbase is not None:
                    # filter only users from this school, with role == school
                    users = User.objects.filter(schoolbase=request.user.schoolbase, role=c.ROLE_008_SCHOOL).order_by('username')
        else:
            messages.error(request, _("User has no role."))

        headerbar_param = awpr_menu.get_headerbar_param(request, {'users': users} )

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
        logger.debug('  ')
        logger.debug(' ========== UserUploadView ===============')

        update_wrap = {}
        if request.user is not None and request.user.country is not None and request.user.schoolbase is not None:
            req_user = request.user
            # <PERMIT> PR2020-09-24
            #  - only perm_admin and perm_system can add / edit / delete users
            #  - only role_system and role_admin (ETE) can add users of other schools
            #  - role_system, role_admin, role_insp and role_school can add users of their own school

            has_permit_this_school, has_permit_all_schools = False, False
            if req_user.is_perm_admin or req_user.is_perm_system:
                has_permit_all_schools = req_user.is_role_admin or req_user.is_role_system
                has_permit_this_school = req_user.is_role_insp or req_user.is_role_school

            if has_permit_this_school or has_permit_all_schools:

# - get upload_dict from request.POST
                upload_json = request.POST.get("upload")
                if upload_json:
                    upload_dict = json.loads(upload_json)
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
                    logger.debug('user_schoolbase: ' + str(user_schoolbase))
                    logger.debug('is_same_schoolbase: ' + str(is_same_schoolbase))

                    # <PERMIT> PR220-09-24
                    # user may edit users from their own school

                    err_dict = {}
                    has_permit = False
                    if user_schoolbase:
                        if has_permit_all_schools:
                            has_permit = True
                        elif has_permit_this_school:
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
                                    instance = am.User.objects.get_or_none(
                                        id=user_pk,
                                        country=req_user.country
                                    )
                                elif has_permit_this_school:
                                    instance = am.User.objects.get_or_none(
                                        id=user_pk,
                                        country=req_user.country,
                                        schoolbase=req_user.schoolbase
                                    )
                                logger.debug('instance: ' + str(instance))

                                if instance:
                                    deleted_instance_list = create_user_list(request, instance.pk)
                                    logger.debug('deleted_instance_list: ' + str(deleted_instance_list))
                                    if deleted_instance_list:
                                        updated_dict = deleted_instance_list[0]
                                        updated_dict['mapid'] = map_id

                                    if (req_user.is_perm_system or req_user.is_perm_admin) \
                                            and (instance == req_user):
                                        err_dict['msg01'] = _("System administrators cannot delete their own account.")
                                    else:
                                        try:
                                            # PR2021-02-05 debug: CASCADE delete usersetting not working. Delete manually
                                            usersettings = Usersetting.objects.filter(user=instance)
                                            for usersetting in usersettings:
                                                logger.debug('usersetting delete: ' + str(usersetting))
                                                usersetting.delete()
                                            instance.delete()
                                            updated_dict['deleted'] = True
                                            logger.debug('deleted: ' + str(True))
                                        except:
                                            err_dict['msg01'] = _("User '%(val)s' can not be deleted.\nInstead, you can make the user inactive.") \
                                                                % {'val': instance.username_sliced}
                                            logger.debug('err_dict msg01: ' + str(err_dict['msg01']))

    # ++++  create or validate new user ++++++++++++
                        elif mode in ('create', 'validate'):
                            # - get permits of new user.
                            #       - new_permits is 'write' when user_school is same as requsr_school,
                            #       - permits is 'write' plus 'admin' when user_school is different from requsr_school

                            is_existing_user = True if user_pk else False

                            if is_same_schoolbase:
                                new_permits = c.PERMIT_002_EDIT
                            else:
                                new_permits = (c.PERMIT_002_EDIT + c.PERMIT_064_ADMIN)
                            # - new user gets role from defaultrole of user_schoolbase
                            #   PR2021-02-06 debug: don't forget to set values of defaultrole in schoolbase!
                            new_role = user_schoolbase.defaultrole

                            new_user_pk, err_dict, ok_dict = create_or_validate_user_instance(
                                user_schoolbase, upload_dict, user_pk, new_permits, new_role, is_validate_only, user_lang, request)
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
                                instance = am.User.objects.get_or_none(id=user_pk, country=req_user.country)
                            elif has_permit_this_school:
                                instance = am.User.objects.get_or_none(
                                    id=user_pk,
                                    country=req_user.country,
                                    schoolbase=req_user.schoolbase
                                )
                            if instance:
                                err_dict, ok_dict = update_user_instance(instance, user_pk, upload_dict, is_validate_only, request)
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
                            update_wrap['updated_list'] = [updated_dict]
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


@method_decorator([login_required], name='dispatch')
class UserSettingsUploadView(UpdateView):  # PR2019-10-09

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= UserSettingsUploadView ============= ')

        update_wrap = {}
        if request.user is not None and request.user.country is not None:
            req_user = request.user
# - get upload_dict from request.POST
            upload_json = request.POST.get('upload')
            if upload_json:
                upload_dict = json.loads(upload_json)
                req_user.set_usersetting_from_uploaddict(upload_dict)
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
    logger.debug('  === SignupActivateView =====')
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
    logger.debug('user: ' + str(user))
    logger.debug('user.is_authenticated: ' + str(user.is_authenticated))
    logger.debug('user.activated: ' + str(user.activated))

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
        logger.debug('examyear: ' + str(examyear))
        school = sch_mod.School.objects.get_or_none( base=user.schoolbase, examyear=examyear)
        logger.debug('school: ' + str(school))
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
        logger.debug('usr_schoolname_with_article: ' + str(usr_schoolname_with_article))
        update_wrap['schoolnamewithArticle'] = usr_schoolname_with_article

# - check activation_token
        activation_token_ok = account_activation_token.check_token(user, token)
        logger.debug('activation_token_ok: ' + str(activation_token_ok))

        if not activation_token_ok:
            update_wrap['msg_01'] = _('The link to active your account is no longer valid.')
            update_wrap['msg_02'] = _('Maybe it has expired or has been used already.')
            update_wrap['msg_03'] = _('The link expires after 7 days.')

    # don't activate user and company until user has submitted valid password
    update_wrap['activation_token_ok'] = activation_token_ok
    logger.debug('update_wrap: ' + str(update_wrap))

    if request.method == 'POST':
        logger.debug('request.POST' + str(request.POST))
        form = SetPasswordForm(user, request.POST)
        logger.debug('form: ' + str(form))

        form_is_valid = form.is_valid()

        non_field_errors = af.get_dict_value(form, ('non_field_errors',))
        field_errors = [(field.label, field.errors) for field in form]
        logger.debug('non_field_errors' + str(non_field_errors))
        logger.debug('field_errors' + str(field_errors))
        logger.debug('form_is_valid' + str(form_is_valid))

        if form_is_valid:
            logger.debug('form_is_valid' + str(form_is_valid))
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
            logger.debug('user.saved: ' + str(user))

            #login_user = authenticate(username=user.username, password=password1)
            #login(request, login_user)
            login(request, user)
            logger.debug('user.login' + str(user))
            #if request.user:
            #    update_wrap['msg_01'] = _("Congratulations.")
            #    update_wrap['msg_02'] = _("Your account is succesfully activated.")
           #     update_wrap['msg_03'] = _('You are now logged in to AWP-online.')
        else:
            # TODO check if this is correct when user enters wrong password PR2021-02-05
            form = SetPasswordForm(user)
            logger.debug('form: ' + str(form))
            update_wrap['form'] = form
    else:
        form = SetPasswordForm(user)
        logger.debug('form: ' + str(form))
        update_wrap['form'] = form
    update_wrap['newuser_activated'] = newuser_activated
    # PR2021-02-05 debug: when a new user tries to activat his account
    #                     and a different user is already logged in in the same browser,
    #                     in form value user.activated = True and passwoord form does not show.
    #                     use variable 'newuser_activated' and add this error trap to form:
    #                     {% elif user.is_authenticated and user.activated and not newuser_activated %}
    #                     instead of  {% elif user.is_authenticated %}
    logger.debug('activation_token_ok: ' + str(activation_token_ok))
    logger.debug('user.is_authenticated: ' + str(user.is_authenticated))
    logger.debug('user.activated: ' + str(user.activated))
    logger.debug('newuser_activated: ' + str(newuser_activated))
    logger.debug('update_wrap: ' + str(update_wrap))
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
                    if request.user.is_role_school_perm_admin:
                        display_school = True

            param = {'display_school': display_school, 'display_user': True, }
            headerbar_param = awpr_menu.get_headerbar_param(request, param)
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


# PR2018-05-05
@method_decorator([login_required], name='dispatch')
class UserActivatedSuccessXXX(View):

    def get(self, request):
        def get(self, request):
            #logger.debug('UserActivatedSuccess get request: ' + str(request))
            return self.render(request)

        def render(self, request):
            usr = request.user
            # TODO I don't think schoolbase is correct PR2018-10-19
            schoolbase = usr.schoolbase

            #logger.debug('UserActivatedSuccess render usr: ' + str(usr))

            return render(request, 'country_list.html', {'user': usr, 'schoolbase': schoolbase})


@method_decorator([login_required], name='dispatch')
class UserDeleteView(DeleteView):
    model = User
    success_url = reverse_lazy('user_list_url')


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
            if request.user.is_perm_admin or request.user.is_perm_system :

                sql_keys = {'country_id': request.user.country.pk, 'max_role': request.user.role}
                sql_list = ["SELECT u.id, u.schoolbase_id,",
                    "CONCAT('user_', u.id) AS mapid, 'user' AS table,",
                    "SUBSTRING(u.username, 7) AS username,",
                    "u.last_name, u.email, u.role, u.permits,",
                    "(TRUNC(u.permits / 128) = 1) AS perm_system,",
                    "(TRUNC( MOD(u.permits, 128) / 64) = 1) AS perm_admin,",
                    "(TRUNC( MOD(u.permits, 64) / 32) = 1) AS perm_anlz,",
                    "(TRUNC( MOD(u.permits, 32) / 16) = 1) AS perm_auth3,",
                    "(TRUNC( MOD(u.permits, 16) / 8) = 1) AS perm_auth2,",
                    "(TRUNC( MOD(u.permits, 8) / 4) = 1) AS perm_auth1,",
                    "(TRUNC( MOD(u.permits, 4) / 2) = 1) AS perm_edit,",
                    "(MOD(u.permits, 2) = 1) AS perm_read,",

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

                sql_list.append('ORDER BY  LOWER(sb.code), LOWER(u.username)')
                sql = ' '.join(sql_list)

                newcursor = connection.cursor()
                newcursor.execute(sql, sql_keys)
                user_list = af.dictfetchall(newcursor)
    return user_list


########################################################################

# === create_or_validate_user_instance ========= PR2020-08-16 PR2021-01-01
def create_or_validate_user_instance(user_schoolbase, upload_dict, user_pk, permits, role, is_validate_only, user_lang, request):
    #logger.debug('-----  create_or_validate_user_instance  -----')
    #logger.debug('upload_dict: ' + str(upload_dict))
    #logger.debug('user_pk: ' + str(user_pk))
    #logger.debug('is_validate_only: ' + str(is_validate_only))

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

        role = user_schoolbase.defaultrole

    # - create new user
        prefixed_username = user_schoolbase.prefix + username
        new_user = am.User(
            country=country,
            schoolbase=user_schoolbase,
            username=prefixed_username,
            last_name=last_name,
            email=email,
            role=role,
            permits=permits,
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
                'uid': urlsafe_base64_encode(force_bytes(new_user.pk)).decode(),
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

# === update_user_instance ========== PR2020-08-16 PR2020-09-24
def update_user_instance(instance, user_pk, upload_dict, is_validate_only, request):
    logger.debug('-----  update_user_instance  -----')
    logger.debug('upload_dict: ' + str(upload_dict))
    has_error = False
    err_dict = {}
    ok_dict = {}
    field_changed_list = []
    if instance:
        country = request.user.country
        schoolbase = request.user.schoolbase
        data_has_changed = False
        fields = ('username', 'last_name', 'email', 'permits', 'is_active')
        for field in fields:
            # --- get field_dict from  item_dict  if it exists
            field_dict = upload_dict[field] if field in upload_dict else {}
            if field_dict and 'update' in field_dict:
# - check if this username already exists
                if field == 'username':
                    new_username = field_dict.get('value')
                    msg_err = v.validate_unique_username(new_username, schoolbase.prefix, user_pk)
                    if msg_err:
                        err_dict[field] = msg_err
                        has_error = True
                    if not has_error and new_username and new_username != instance.username:
                        prefixed_username = schoolbase.prefix + new_username
                        instance.username = prefixed_username
                        data_has_changed = True
# - check if namelast is blank
                elif field == 'last_name':
                    new_last_name = field_dict.get('value')
                    msg_err = v.validate_notblank_maxlength(new_last_name, c.MAX_LENGTH_NAME, _('The name'))
                    if msg_err:
                        err_dict[field] = msg_err
                        has_error = True
                    if not has_error and new_last_name and new_last_name != instance.last_name:
                        instance.last_name = new_last_name
                        data_has_changed = True
# - check if this is a valid email address:
                elif field == 'email':
                    new_email = field_dict.get('value')
                    msg_err = v.validate_email_address(new_email)
                    if msg_err:
                        err_dict[field] = msg_err
                        has_error = True
# - check if this email address already exists
                    else:
                        msg_err = v.validate_unique_useremail(new_email, country, schoolbase, user_pk)
                        if msg_err:
                            err_dict[field] = msg_err
                            has_error = True

                    if not has_error and new_email and new_email != instance.email:
                        instance.email = new_email
                        data_has_changed = True

                elif field == 'permits':
                    permit_field = field_dict.get('field')
                    new_permit_bool = field_dict.get('value', False)
                    new_permit_int = c.PERMIT_LOOKUP[permit_field] if permit_field else 0
                    saved_permit_list = list(get_permits_tuple(instance.permits))
                    logger.debug('permit_field: ' + str(permit_field))
                    logger.debug('new_permit_bool: ' + str(new_permit_bool))
                    logger.debug('new_permit_int: ' + str(new_permit_int))
                    logger.debug('saved_permit_list: ' + str(saved_permit_list))
            # - sysadmins cannot remove sysadmin permission from their own account
                    if request.user.is_perm_admin or request.user.is_perm_system:
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

                            logger.debug('saved_permit_list: ' + str(saved_permit_list))
                            logger.debug('new_permit_sum: ' + str(new_permit_sum))

                            instance.permits = new_permit_sum
                            data_has_changed = True

                elif field == 'is_active':
                    new_isactive = field_dict.get('value', False)
                    # sysadmins cannot remove is_active from their own account
                    if request.user.is_perm_admin and instance == request.user:
                        if not new_isactive:
                            err_dict[field] = _("System administrators cannot make their own account inactive.")
                            has_error = True
                    if not has_error and new_isactive != instance.is_active:
                        instance.is_active = new_isactive
                        data_has_changed = True

# -  update user
        if not is_validate_only and not has_error:
            if data_has_changed:
# - get now without timezone
                now_utc_naive = datetime.utcnow()
                now_utc = now_utc_naive.replace(tzinfo=pytz.utc)

                try:
                    instance.modifiedby = request.user
                    instance.modifiedat = now_utc
                    instance.save()
                    ok_dict['msg_ok'] = _("The changes have been saved successfully.")
                except:
                    err_dict['save'] = _('An error occurred. The changes have not been saved.')

    return err_dict, ok_dict
# - +++++++++ end of update_user_instance ++++++++++++


# === resend_activation_email ===================================== PR2020-08-15
def resend_activation_email(user_pk, update_wrap, err_dict, request):
    #  resend_activation_email is called from table Users, field 'activated' when the activation link has expired.
    #  it sends an email to the user
    #  it returns a HttpResponse, with ok_msg or err-msg

    user = am.User.objects.get_or_none(id=user_pk, country= request.user.country)
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
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                    'token': account_activation_token.make_token(user),
                })
                # PR2018-04-25 arguments: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
                mail_count = send_mail(subject, message, from_email, [user.email], fail_silently=False)
                if not mail_count:
                    err_dict['msg01'] = _('An error occurred.')
                    err_dict['msg0'] = _('The activation email has not been sent.')
                else:
                # - return message 'We have sent an email to user'
                    msg01 = _("We have sent an email to the email address '%(email)s' of user '%(usr)s'.") % \
                                                    {'email': user.email, 'usr': user.username_sliced}
                    msg02 = _('The user must click the link in that email to verify the email address and create a password.')

                    update_wrap['msg_ok'] = {'msg01': msg01, 'msg02': msg02}

            except:
                err_dict['msg01'] = _('An error occurred.')
                err_dict['msg0'] = _('The activation email has not been sent.')

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
    if permit_field != "perm_auth1" and c.PERMIT_004_AUTH1 in permit_list:
        permit_list.remove(c.PERMIT_004_AUTH1)
    if permit_field != "perm_auth2" and c.PERMIT_008_AUTH2 in permit_list:
        permit_list.remove(c.PERMIT_008_AUTH2)
    if permit_field != "perm_auth3" and c.PERMIT_016_AUTH3 in permit_list:
        permit_list.remove(c.PERMIT_016_AUTH3)



def has_permit(permits_int, permit_index): # PR2020-10-12 separate function made PR2021-01-18
    has_permit = False
    if permits_int:
        permits_tuple = get_permits_tuple(permits_int)
        has_permit = permit_index in permits_tuple
    return has_permit



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