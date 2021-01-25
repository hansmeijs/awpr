from django.contrib.auth import get_user_model, authenticate

from django.contrib.auth.forms import (AuthenticationForm,  UserCreationForm)
from django.contrib.auth import password_validation # PR2018-10-10
from django.core.validators import RegexValidator

from django.forms import Form, ModelForm, CharField, PasswordInput, ChoiceField, MultipleChoiceField, TextInput, SelectMultiple, Select

from collections import OrderedDict

from django.shortcuts import render
from django.utils.translation import activate, get_language_info, ugettext_lazy as _
from django.utils.text import capfirst

from awpr import constants as c
from awpr import functions as f
from schools.models import Schoolbase
from accounts import models as acc_mod

from schools import models as sch_mod
from django.forms.widgets import PasswordInput
from django.core.exceptions import ValidationError

import unicodedata

UserModel = get_user_model()

# PR2018-05-04
import logging
logger = logging.getLogger(__name__)



class UsernameField(CharField):
    def to_python(self, value):
        return unicodedata.normalize('NFKC', super().to_python(value))


class SchoolbaseAuthenticationForm(Form):
    """
    This code is based on class AuthenticationForm PR2020-09-25 PR2020-10-22
    """
    schoolcode = CharField(
        required=True,
        label=_("School code"),
        widget=TextInput(attrs={'autofocus': True})
    )

    username = UsernameField(
        widget=TextInput(attrs={'autofocus': True}),
        label = _("Username"),
    )
    password = CharField(
        label=_("Password"),
        strip=False,
        widget=PasswordInput,
    )

    error_messages = {
        'invalid_login': _(
            "Please enter a correct school code, username and password. Note that the password is case-sensitive."
        ),
        'inactive': _("This account is inactive. You cannot login."),
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

        # Set the max length and label for the "username" field.
        self.username_field = UserModel._meta.get_field(UserModel.USERNAME_FIELD)
        self.fields['username'].max_length = self.username_field.max_length or 254
        if self.fields['username'].label is None:
            self.fields['username'].label = capfirst(self.username_field.verbose_name)

    def clean(self):
        schoolcode = self.cleaned_data.get('schoolcode')
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        #logger.debug('schoolcode: ' + str(schoolcode))
        #logger.debug('username: ' + str(username))
        #logger.debug('password: ' + str(password))

        if username is not None and password:
            # put schoolprefix in front of username PR2019-03-13
            schoolbase = None
            if schoolcode:
                schoolbase = sch_mod.Schoolbase.objects.filter(
                    code__iexact=schoolcode
                ).first()
            if schoolbase:
                username = schoolbase.prefix + username
            else:
                username = "xxxxxx" + username
            #logger.debug('schoolbase: ' + str(schoolbase))
            #logger.debug('username: ' + str(username))

            self.user_cache = authenticate(self.request, username=username, password=password)
            #logger.debug('self.user_cache: ' + str(self.user_cache))

            # PR2020-10-22 from https://stackoverflow.com/questions/46459258/how-to-inform-a-user-that-he-is-not-active-in-django-login-view
            if self.user_cache is None:
                try:
                    user_temp = acc_mod.User.objects.get(username=username)
                except:
                    user_temp = None

            # - set language so the return message can be sent in the language of the user
                if user_temp is not None:
                    user_lang = user_temp.lang if user_temp.lang else c.LANG_DEFAULT
                    activate(user_lang)

                if user_temp is not None and user_temp.check_password(password):
                    self.confirm_login_allowed(user_temp)
                else:
                    raise self.get_invalid_login_error()
#//////////////////////////////////////////////////
        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )
        #logger.debug('SchoolbaseAuthenticationForm self.error_messages : ' + str(self.error_messages) + ' Type: ' + str(type(self.error_messages)))

    def get_user(self):
        return self.user_cache

    def get_invalid_login_error(self):
        return ValidationError(
            self.error_messages['invalid_login'],
            code='invalid_login',
            params={'username': self.username_field.verbose_name},
        )

    def get_inactive_login_error(self):
        # PR2020-10-22 added, to show 'user is inactive' message in login form
        return ValidationError(
            self.error_messages['inactive'],
            code='inactive',
            params={'username': self.username_field.verbose_name},
        )


# PR2018-04-23
class UserActivateForm(ModelForm):

    class Meta:
        User = get_user_model()
        model = User
        fields = ('last_name', 'email') # , 'password1', 'password2',)

    def __init__(self, *args, **kwargs):
        #logger.debug('UserActivateForm __init__  kwargs: ' + str(kwargs))
        self.request = kwargs.pop('request', None)  # pop() removes and returns an element from a dictionary, second argument is default when not found
        #logger.debug('UserActivateForm __init__ request: ' + str(self.request))
        super(UserActivateForm, self).__init__(*args, **kwargs)

        self.fields['password1'] = CharField(max_length=32, label='Password') # label -='' works, but appears again after formerror
        self.fields['password2'] = CharField(max_length=32, label='Repeat password')

        self.fields['password1'].widget = PasswordInput # this is not working
        self.fields['password2'].widget = PasswordInput # this is not working
        # self.fields['password1'].widget = HiddenInput() # this works, but label stays
        # self.fields['password2'].widget = HiddenInput() # this works, but label stays


"""
USED TO FIND PROBLEM THAT PASSWORDS ARE NOT SAVED - problem: forgot 'password_mod' in datahaschanged in model User
# PR2018-10-13
class UserResetPasswordForm(Form):


    A form that lets a user change set their password without entering the old
    password

    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    new_password1 = CharField(
        label=_("New password"),
        widget=PasswordInput,
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=PasswordInput,
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        logger.debug('UserResetPasswordForm __init__ kwargs ' + str(kwargs))
        logger.debug('UserResetPasswordForm __init__ self.user ' + str(self.user))

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        logger.debug('UserResetPasswordForm password1 ' + str(password1))
        logger.debug('UserResetPasswordForm password2 ' + str(password2))

        if password1 and password2:
            if password1 != password2:
                raise ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        password_validation.validate_password(password2, self.user)

        logger.debug('UserResetPasswordForm password_validation ' + str(password2))
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        logger.debug('UserResetPasswordForm save password ' + str(password))
        logger.debug('UserResetPasswordForm self.user ' + str(self.user))
        self.user.set_password(password)
        if commit:
            logger.debug('UserResetPasswordForm before save password: ' + self.user.password)
            logger.debug('UserResetPasswordForm before save has_usable_password: ' + str(self.user.has_usable_password()))
            logger.debug('UserResetPasswordForm before save modified_at: ' + str(self.user.modified_at))
            self.user.modified_at = timezone.now
            self.user.save()
            logger.debug('UserResetPasswordForm password saved')
            logger.debug('UserResetPasswordForm after save password: ' + self.user.password)
            logger.debug('UserResetPasswordForm after save has_usable_password: ' + str(self.user.has_usable_password()))
            logger.debug('UserResetPasswordForm after save modified_at: ' + str(self.user.modified_at))

            checked = self.user.check_password('jumper77')
            logger.debug('UserResetPasswordForm password checked: ' + str(checked))

        from accounts.models import User
        thisusr = User.objects.filter(username='InspCur').first()
        logger.debug('UserSetPasswordForm password thisusr: ' + str(thisusr.username))
        checked = self.user.check_password('jumper77')
        logger.debug('UserSetPasswordForm password InspCur jumper77: ' + str(checked))
        logger.debug('UserSetPasswordForm password jumper77: ' + str(checked))
        checked = self.user.check_password('jumper55')
        logger.debug('UserSetPasswordForm password jumper55: ' + str(checked))

        return self.user
"""