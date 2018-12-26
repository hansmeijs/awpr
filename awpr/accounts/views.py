from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required  # PR2018-04-01
from django.contrib.auth.mixins import UserPassesTestMixin  # PR2018-11-03
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _
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

from .forms import UserAddForm, UserEditForm, UserActivateForm
from .tokens import account_activation_token
from .models import User, User_log, Usersetting
from schools.models import Examyear, Schoolbase
from subjects.models import Department
from awpr import constants as c
from awpr import functions as f

import logging
logger = logging.getLogger(__name__)

@method_decorator([login_required], name='dispatch')
class UserListView(ListView):
    # PR 2018-04-22 template_name = 'user_list.html' is not necessary, Django looks for <appname>/<model>_list.html

    def get(self, request, *args, **kwargs):
        User = get_user_model()

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
                    users = User.objects.filter(country=request.user.country, role__lte=c.ROLE_01_INSP).order_by('username')
            else:
                if request.user.schoolbase is not None:
                    # filter only users from this school, with role == school
                    users = User.objects.filter(schoolbase=request.user.schoolbase, role=c.ROLE_00_SCHOOL).order_by('username')
        else:
            messages.error(request, _("User has no role."))

        _override_school = ''
        if request.user.is_role_insp_or_system:
            _override_school = request.user.role_str
        headerbar_param = f.get_headerbar_param(request,
            {'users': users, 'display_school': True, 'override_school': _override_school})
        # logger.debug('home headerbar_param: ' + str(headerbar_param))
        """
        headerbar_param:
        {
            'context':
                {'schoolyear': '2018-2019', 
                    'select_schoolyear': True, 
                    'display_schoolyear': True,
                    'school': 'CUR02  Skol Avansa Amador Nita - Saan', 
                    'display_school': False,
                    'class_examyear_warning': 'navbar-item-warning'},

            'schoolyear_list':
                [{'pk': '2', 'schoolyear': '2018-2019', 'selected': True},
                 {'pk': '1', 'schoolyear': '2017-2018', 'selected': False}],

            'school_list':
                [{'pk': '5', 'school': 'CUR01 -  Ancilla Domini Vsbo', 'selected': False},
                 {'pk': '6', 'school': 'CUR02 -  Skol Avansa Amador Nita - Saan', 'selected': True},
                 {'pk': '7', 'school': 'CUR03 -  Juan Pablo Duarte Vsbo', 'selected': False}],
        }
        """

        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'user_list.html', headerbar_param)

# How To Create Users Without Setting Their Password PR2018-10-09
# from https://django-authtools.readthedocs.io/en/latest/how-to/invitation-email.html


@method_decorator([login_required], name='dispatch')
class UserAddView(CreateView):
    # model = User
    # form_class = UserAddForm
    # template_name = 'user_add.html' # without template_name Django searches for user_form.html
    # pk_url_kwarg = 'pk'
    # context_object_name = 'UserAddForm' # "context_object_name" changes the original parameter name "object_list"

    def get(self, request, *args, **kwargs):
        # required: user.is_authenticated and user.may_add_or_edit_users
        # PR2018-05-30  user may_add_or_edit_users if:
        # role system: if perm admin
        # role insp:   if perm_admin and country not None
        # role school: if perm_admin and country not None and schooldefault not None

        form = UserAddForm(request=request)

        _params = f.get_headerbar_param(request, {
            'form': form,
            'display_school': True
        })
        # render(request, template_name, context=None (A dictionary of values to add to the template context), content_type=None, status=None, using=None)
        return render(request, 'user_add.html', _params)

        # Every field in the form will have a field_name_clean() method created automatically by Django.\
        # This method is called when you do form.is_valid().
        # def clean_password1(self):
        #    password_default = 'default'
        #    self.cleaned_data['password1'] = password_default
        #    return password_default

    def post(self, request, *args, **kwargs):
        # data = request.POST.copy()
        # logger.debug('UserAddView def post(self, request:data = ' + str(data))
        form = UserAddForm(request.POST, request=request)  # form = UserAddForm(request.POST)
        # logger.debug('UserAddView post form.data: ' + str(form.data))

        if form.is_valid():
            # logger.debug('UserAddView post is_valid form.data: ' + str(form.data))

        # create random password
            randompassword = User.objects.make_random_password() + User.objects.make_random_password()
            form.cleaned_data['password1'] = randompassword
            form.cleaned_data['password2'] = randompassword

        # save user without commit
            user = form.save(commit=False)
            # logger.debug('UserAddView post form.save after commit=False')

# ======  save field 'Role'  ============
        # only request.user with role=System and role=Insp kan set different role, School can only set its own role
            # logger.debug('UserAddView post form.is_valid request.user.role: '+ str(request.user.role))
            if request.user.is_role_insp_or_system:
                _role_int = form.cleaned_data.get('role_list')
            else:
                _role_int = request.user.role
            user.role = _role_int
            # logger.debug('UserAddView post form.is_valid user.username: '+ str(user.username))
            # logger.debug('UserAddView post form.is_valid user.role: '+ str(user.role))

# ======  save field 'Country'  ============ PR2018-08-17
        # user.country cannot be changed, except for users with role.system. They can switch country in headerbar.
            user.country = request.user.country
            # PR2018-08-17 was:
            # get request_user.country, set as initial in UserAddForm:  initial = request.user.country.id
            # country_list = form.cleaned_data.get('country_list')
            # try:
            #     country_id = int( country_list)
            #     # PR2018-06-08 objects.get gives error: 'matching query does not exist' when record not found (should not be possible)
            #     # use Country.objects.filter instead
            #     country = Country.objects.get(id=country_id)
            #     if country:
            #         user.country = country
            # except:
            #     pass

# ======  save field 'Country'  ============ PR2018-08-17
            # user.examyear get default value user.examyear


            user.examyear = request.user.examyear



# ======  save field 'schoolbase'  ============ PR2018-08-17
            # when request.user.role=System: schoolbase = None, when Insp and School:  schoolbase= request.user.schoolbase
            if not request.user.is_role_system:
                if request.user.schoolbase:
                    user.schoolbase = request.user.schoolbase
            # logger.debug('UserAddView post form.is_valid user.role: '+ str(user.role))

        # save field 'Permit'
            permit_sum = 0
            permit_list = form.cleaned_data.get('permit_list')
            if permit_list:
                for item in permit_list:
                    try:
                        permit_sum = permit_sum + int(item)
                    except:
                        pass
            user.permits = permit_sum

            user.is_active = False
            user.activated = False

            user.save(self.request)  # PR 2018-08-04 debug: was: user.save()
            # logger.debug('UserAddView post password: ' +  str(user.password))

            current_site = get_current_site(request)
            # logger.debug('UserAddView post current_site: ' +  str(current_site))

            # domain = current_site.domain
            # logger.debug('UserAddView post domain: ' +  str(domain) + '\n')

            # uid_code = urlsafe_base64_encode(force_bytes(user.pk))
            # logger.debug('UserAddView post uid_code: ' + str(uid_code))

            # token = account_activation_token.make_token(user)
            # logger.debug('UserAddView post token: ' + str(token))

            subject = 'Activate Your AWP online Account'
            message = render_to_string('account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                # PR2018-04-24 debug: In Django 2.0 you should call decode() after base64 encoding the uid, to convert it to a string:
                # 'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user),
            })
            # logger.debug('UserAddView post subject: ' + str(subject))
            # PR2018-04-25 arguments: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
            user.email_user(subject, message)
            # logger.debug('UserAddView post message sent. ')
            return redirect('account_activation_sent_url')
        else:
            # logger.debug('UserAddView post NOT is_valid form.data: ' + str(form.data))
            return render(request, 'user_add.html', {'form': form})


@method_decorator([login_required], name='dispatch')
class UserEditView(UserPassesTestMixin, UpdateView):
    User = get_user_model()
    model = User
    form_class = UserEditForm
    template_name = 'user_edit.html' # without template_name Django searches for user_form.html
    # PR2018-08-02 debug: omitting context_object_name = 'UserEditView' has a weird effect:
    # the selected_user becomes the request_user
    context_object_name = 'UserEditView' # "context_object_name" changes the original parameter name "object_list"

    # +++ VULNERABILITY !!! +++++++++++++++++++++++++++++++++++++++
    # PR2018-08-19
    # VULNERABILITY: User Insp / School can access other users by entering: http://127.0.0.1:8000/users/6/edit
    # must check if country is same as country of insp OR selected_school is same as school of role_school

    # PR2018-11-03 from: https://python-programming.com/django/permission-checking-django-views/
    # UserPassesTestMixin uses test_func to check permissions
    def test_func(self):
        is_ok = False
        if self.request.user is not None:
            request_user = self.request.user
        # request_user must be active
            if request_user.is_active:
        # is_role_system is_ok
                if self.request.user.is_role_system:
                    is_ok = True
        # request_user must have country
                elif request_user.country is not None:
                    selected_user_id = self.kwargs['pk']
                    if selected_user_id is not None:
                        selected_user = User.objects.filter(id=selected_user_id).first()
                        if selected_user is not None:
        # selected_user must have country
                            if selected_user.country is not None:
        # request_user.country and selected_user.country must be the same
                                if selected_user.country.id == request_user.country.id:
        # is_role_insp is_ok
                                    if self.request.user.is_role_insp:
                                        is_ok = True
        # request_user and selected_user must have schoolbase
                                    elif request_user.schoolbase is not None and selected_user.schoolbase is not None:
        # request_user.schoolbase and selected_user.schoolbase must be the same
                                        is_ok = selected_user.schoolbase.id == request_user.schoolbase.id
        return is_ok

    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        """
        FormMixin
            kwargs = {
                'initial': self.get_initial(),
                'prefix': self.get_prefix(),}
            if self.request.method in ('POST', 'PUT'):
                kwargs.update({
                    'data': self.request.POST,
                    'files': self.request.FILES,})
        ModelFormMixin
            if hasattr(self, 'object'):
                kwargs.update({
                    'instance': self.object})
        """
        kwargs = super(UserEditView, self).get_form_kwargs()
        #  add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})

        # eg: kwargs: {'initial': {}, 'prefix': None, 'instance': <User: Ad>, 'request': <WSGIRequest: GET '/users/18/edit'>}
        # logger.debug('UserEditView get_form_kwargs kwargs: ' + str(kwargs))
        return kwargs


    def form_valid(self, form):
        user = form.save(commit=False)

# ======  save field 'Permit_list'  ============
    # ATTENTION user with permission admin cannot cancel this, otherwise he could lock himself out
    # get selected permits from permit_list, convert it to permit_sum, save it in user.permits
        # check if regusat user is changing himself
        user_equals_requestuser = user == self.request.user
        cleaned_permit_has_admin = False

        permit_list = form.cleaned_data.get('permit_list')
        permit_sum = 0
        if permit_list:
            for item in permit_list:
                try:
                    if int(item) == c.PERMIT_08_ADMIN:
                        cleaned_permit_has_admin = True
                    permit_sum = permit_sum + int(item)
                except:
                    pass

        # add admin to permit if admin user has removed admin from his own permit list PR2018-08-25
        if user_equals_requestuser:
            if not cleaned_permit_has_admin:
                permit_sum = permit_sum + c.PERMIT_08_ADMIN

        user.permits = permit_sum

# ======  save field 'field_is_active'  ============
        # PR2018-08-09 get value from field 'field_is_active', save it in user.is_active
        # value in field_is_active is stored as str: '0'=False, '1'=True
        field_is_active = form.cleaned_data.get('field_is_active')
        # logger.debug('UserEditView form_valid field_is_active: ' +  str(field_is_active) + ' Type: ' + str(type(field_is_active)))
        _is_active = bool(int(field_is_active))
        user.is_active = _is_active

        user.modified_by = self.request.user
        # user.modified_at will be updated in model.save

        user.save(self.request)  # was: user.save()
        return redirect('user_list_url')


@method_decorator([login_required], name='dispatch')
class UserLogView(View):
    # PR 2018-04-22 template_name is not necessary, Django looks for <appname>/<model>_list.html
    # template_name = 'country_list.html'
    # context_object_name = 'countries'
    # paginate_by = 10  After this /country_list/?page=1 will return first 10 countries.
# TODO not working yet, is copy of country_log PR2018-07-19
    def get(self, request, pk):
        users_log = User_log.objects.filter(user_id=pk).order_by('-modified_at')
        user = User.objects.get(id=pk)

        param = {'display_school': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        headerbar_param['users_log'] = users_log
        headerbar_param['user'] = user
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'user_log.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class UserLanguageView(View):

    def get(self, request, lang, pk):
        logger.debug('UserLanguageView get self: ' + str(self) + 'request: ' + str(request) + ' lang: ' + str(lang) + ' pk: ' + str(pk))
        if request.user is not None :
            logger.debug('UserLanguageView get request.user: ' + str(request.user))
            request.user.lang = lang
            logger.debug('UserLanguageView get request.user.language: ' + str(request.user.lang))
            request.user.save(self.request)
            logger.debug('UserLanguageView get saved.language: ' + str(request.user.lang))
        return redirect('home')


# PR2018-04-24
def account_activation_sent(request):
    # logger.debug('account_activation_sent request: ' + str(request))
    # PR2018-05-27
    # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
    return render(request, 'account_activation_sent.html')


# PR2018-04-24
@method_decorator([login_required], name='dispatch')
class UserActivateView(UpdateView):
    model = User
    form_class = UserActivateForm
    template_name = 'user_edit.html'  # without template_name Django searches for user_form.html
    pk_url_kwarg = 'pk'
    context_object_name = 'UserEditForm'  # "context_object_name" changes the original parameter name "object_list"
    # logger.debug('UserEditView load')

    def activate(request, uidb64, token):
        logger.debug('UserActivateView def activate request: ' +  str(request))

        #try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        logger.debug('UserActivateView def activate try uid: ' + str(uid))
        user = User.objects.get(pk=uid)
        logger.debug('UserActivateView def activate try user: ' + str(user))
        logger.debug('UserActivateView def activate try user again: ' + str(user))

        #except:  #except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        #    logger.debug('def activate except TypeError: ' + str(TypeError))
        #    logger.debug('def activate except ValueError: ' + str(ValueError))
        #    logger.debug('def activate except OverflowError: ' + str(OverflowError))
        #    logger.debug('def activate except User.DoesNotExist: ' + str(User.DoesNotExist))
        #    user = None

        logger.debug('UserActivateView def activate check_token: ' + str(account_activation_token.check_token(user, token)))
        logger.debug('UserActivateView def activate token: ' + str(token))

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.activated = True
            user.save()
            logger.debug('UserActivateView def activate user.saved: ' + str(user))
            #login(request, user)
            logger.debug('UserActivateView def activate user.loggedin: ' + str(user))

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
            headerbar_param = f.get_headerbar_param(request, param)
            headerbar_param['form'] = form
            # logger.debug('def home(request) headerbar_param: ' + str(headerbar_param))

            return render(request, 'user_add.html', headerbar_param)

        else:
            # logger.debug('def activate account_activation_token.check_token False')
            return render(request, 'account_activation_invalid.html')


# PR2018-04-24
def UserActivate(request, uidb64, token):
    logger.debug('UserActivate def activate request: ' + str(request))

    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        logger.debug('def activate try uid: ' + str(uid))
        user = User.objects.get(pk=uid)
        logger.debug('UserActivate def activate try user: ' + str(user))

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
        logger.debug('UserActivate def activate user.saved: ' + str(user))

        # open setpassword form

        # login(request, user)
        logger.debug('UserActivate def activate user.loggedin: ' + str(user))



        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'account_activation_success.html')
        # return render(request, 'password_change.html', {'user': user,})
        # return render(request, 'user_set_password.html', {'user': user,})
        # return render(request, 'password_reset_confirm.html', {'user': user,})

    else:
        # logger.debug('def activate account_activation_token.check_token False')
        return render(request, 'account_activation_invalid.html')


# PR2018-05-05
@method_decorator([login_required], name='dispatch')
class UserActivatedSuccess(View):

    def get(self, request):
        def get(self, request):
            # logger.debug('UserActivatedSuccess get request: ' + str(request))
            return self.render(request)

        def render(self, request):
            usr = request.user
            # TODO I don't think schoolbase is correct PR2018-10-19
            schoolbase = usr.schoolbase

            logger.debug('UserActivatedSuccess render usr: ' + str(usr))

            return render(request, 'country_list.html', {'user': usr, 'schoolbase': schoolbase})


@method_decorator([login_required], name='dispatch')
class UserDeleteView(DeleteView):
    model = User
    success_url = reverse_lazy('user_list_url')



@method_decorator([login_required], name='dispatch')
class DownloadSubmenusView(View):  # PR2018-12-19
    # function updates Usersettings
    def post(self, request, *args, **kwargs):
        # logger.debug(' ============= DownloadSubmenusView ============= ')
        if request.user is not None:
            for key in request.POST.keys():
                # logger.debug('request.POST[' + str(key) + ']: ' + request.POST[key] + ' type: ' + str(type(request.POST[key])))
                if key == c.KEY_USER_MENU_SELECTED:
                    selected_index = request.POST[key]
                    if Usersetting.objects.filter(
                            user=request.user, key_str=c.KEY_USER_MENU_SELECTED).exists():
                        setting = Usersetting.objects.filter(
                            user=request.user, key_str=c.KEY_USER_MENU_SELECTED).first()
                    else:
                        setting = Usersetting(
                            user=request.user, key_str=c.KEY_USER_MENU_SELECTED)
                    setting.char01 = selected_index
                    setting.save()
                    href = reverse_lazy('import_student_url')
                    caption = _('Import students')
                    item = '<li class="nav-item active"><a class="nav-link" href="/">' + selected_index + ' <span class="sr-only"></span></a></li>'
        submenus = [{'class': 'nav-item active', 'caption': caption, 'href': href},
                    {'class': 'nav-item active', 'caption': _('Subjects'), 'href': href},
                    {'class': 'nav-item active', 'caption': _('Student subjects'), 'href': href},
                    ]
        return render(request, 'includes/menubar_submenu.html', {'submenus': submenus})




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