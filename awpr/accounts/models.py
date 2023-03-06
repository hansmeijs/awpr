# PR2018-04-22 PR2020-09-14
from django.db import connection
from django.db.models import Model, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, TextField, IntegerField, PositiveSmallIntegerField, SmallIntegerField, BooleanField, DateField, DateTimeField, EmailField
from django.contrib.auth.models import AbstractUser, UserManager

# PR2020-12-13 Deprecation warning: django.contrib.postgres.fields import JSONField  will be removed from Django 4
# instead use: django.db.models import JSONField (is added in Django 3)
# PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
from django.contrib.postgres.fields import ArrayField # ,JSONField

from django.core.validators import RegexValidator
from django.utils import timezone
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _
from schools.models import Country, Examyear, Departmentbase, Department, Schoolbase, School
from awpr import constants as c
from awpr import settings as s
from schools import models as sch_mod
from subjects import models as subj_mod

from subjects.models import Exam

import json #PR2018-12-19
import logging # PR2018-05-10
logger = logging.getLogger(__name__)

# === USER =====================================
# PR2018-05-22 added to create a case-insensitive username
# from https://simpleisbetterthancomplex.com/tutorial/2017/02/06/how-to-implement-case-insensitive-username.html
class CustomUserManager(UserManager):
    def get_by_natural_key(self, username):
        case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
        return self.get(**{case_insensitive_username_field: username})

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except:
            return None


class User(AbstractUser):
    # PR2018-05-22 added to create a case-insensitive username
    objects = CustomUserManager()

    username = CharField(
        max_length=c.USERNAME_MAX_LENGTH,
        unique=True,
        # help_text=_('Required. {} characters or fewer. Letters, digits and @/./+/-/_ only.'.format(c.USERNAME_MAX_LENGTH)),
        help_text=_('Required, %(len)s characters or fewer. Letters, digits and @/./+/-/_ only.') % {'len': c.USERNAME_SLICED_MAX_LENGTH},
        validators=[
            RegexValidator(r'^[\w.@+-]+$',
            _('Enter a valid username. '
            'This value may contain only letters, numbers '
            'and @/./+/-/_ characters.'), 'invalid'),
        ],
        error_messages={
            'unique': _("A user with that username already exists."),
        })
    last_name = CharField(
        max_length=c.MAX_LENGTH_NAME,
        help_text=_('Required. {} characters or fewer.'.format(50)),
        validators=[
            RegexValidator(r'^[\w .\'-]+$',
            _('Enter a valid name. '
            'This value may contain only letters, numbers '
            'and \'/./-/_ characters.'), 'invalid'),
        ],)
    email = EmailField( _('email address'),)

    idnumber= CharField(db_index=True, null=True, blank=True, max_length=c.MAX_LENGTH_IDNUMBER)

    telephone = CharField(null=True, blank=True, max_length=c.MAX_LENGTH_SCHOOLABBREV)

    role = PositiveSmallIntegerField(default=0)

    #PR2023-01-12 to be deprecated, moved to table UserAllowed
    usergroups = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)

    #PR2023-01-12 to be deprecated, moved to table UserAllowed
    allowed_depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    allowed_levelbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    allowed_schoolbases = CharField(max_length=2048, null=True)
    allowed_subjectbases = CharField(max_length=2048, null=True)
    allowed_clusterbases = CharField(max_length=2048, null=True)

    activated = BooleanField(default=False)
    activated_at = DateTimeField(null=True)
    # country and schoolbase get their value when user is created - value can never change PR2020-11-17
    # insp and admin selected school is stored in usersettings
    country = ForeignKey(Country, null=True, blank=True, related_name='+', on_delete=PROTECT)
    schoolbase = ForeignKey(Schoolbase, null=True, blank=True, related_name='+', on_delete=PROTECT)

    # PR2020-12-24 examyear and depbase are removed from user - are saved in usersetting
    # examyear can always be set by user - value can change PR2020-11-17
    # depbase can be set by user if allowed_depbases has multiple values- value can change PR2020-11-17
    # examyear = ForeignKey(Examyear, null=True, blank=True, related_name='+', on_delete=SET_NULL)
    # depbase = ForeignKey(Departmentbase, null=True, blank=True, related_name='+', on_delete=SET_NULL)

    lang = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    created_by = ForeignKey(s.AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    created_at = DateTimeField(null=True)
    modified_by = ForeignKey(s.AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    modified_at = DateTimeField(null=True)

    class Meta:
        ordering = ['username',]

    def __str__(self):
        return self.username[6:]

    def save(self, *args, **kwargs):
        # when request_user changes his own settings: self = request_user
        # when request_user changes other user: self = selected_user
        # logger.debug('class User(AbstractUser) save self (selected_user): ' + str(self))
        self.request = kwargs.pop('request', None)
        # PR2018-08-27 use kwargs instead of args. Was:
        # request_user = None
        # if len(args) > 0:
        #     request = args[0]  # user.save(self.request)  # was: user.save() in UserEditView.post
        #     request_user = request.user
        # logger.debug('class User(AbstractUser) save self.request: ' + str(self.request))
        request_user = None
        if self.request:
            if self.request.user:
                request_user = self.request.user
                self.modified_by = request_user
        # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
        self.modified_at = timezone.now()

        # logger.debug('class User(AbstractUser) save _is_update ' + str(_is_update) + ' self.mode ' + str(self.mode))

        # self.id gets its value in super(Country, self).save
        # save to logfile

        self.is_update = self.pk is not None  # self.id is None before new record is saved
        self.mode = ('c', 'u')[self.is_update]  # result = (on_false, on_true)[condition]

        # PR2018-06-07 self.modified_by is updated in View, couldn't get Country object passed to save function
        # self.modified_at = timezone.now()

        # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
        super(User, self).save(force_insert=not self.is_update, force_update=self.is_update, **kwargs)
        # self.id gets its value in super(Country, self).save

    @property
    def username_sliced(self):
        # PR2019-03-13 Show username 'Hans' instead of '000001Hans'
        return self.username[6:]


    # PR2018-05-30 list of permits that user can be assigned to:
    # - System users can only have permits: 'Admin' and 'Read'
    # - System users can add all roles: 'System', Insp', School', but other roles olny with 'Admin' and 'Read' permit

    # - Inspectorate and School users can only add their own role
    # - Inspectorate and School users can have all permits: 'Admin', 'Auth',  'Write' and 'Read'

    # PR2018-07-31 debug. 'def': This is a method, not a @property. Property gave error: 'list' object is not callable
    # see: https://www.b-list.org/weblog/2006/aug/18/django-tips-using-properties-models-and-managers/?utm_medium=twitter&utm_source=twitterfeed

    # PR2018-05-27 property returns True when user has ROLE_128_SYSTEM
    @property
    def is_role_system(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        return self.is_authenticated and self.role is not None and self.role == c.ROLE_128_SYSTEM

    @property
    def is_role_admin(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        # PR220-09-24 system has also admin rights
        return (self.is_authenticated) and (self.role is not None) and (self.role == c.ROLE_064_ADMIN)

    @property
    def is_role_insp(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        return self.is_authenticated and self.role is not None and self.role == c.ROLE_032_INSP

    @property
    def is_role_corr(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        return self.is_authenticated and self.role is not None and self.role == c.ROLE_016_CORR

    @property
    def is_role_school(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        return self.is_authenticated and self.role is not None and self.role == c.ROLE_008_SCHOOL

    @property
    def is_role_insp_or_admin_or_system(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_128_SYSTEM or self.role == c.ROLE_064_ADMIN or self.role == c.ROLE_032_INSP:
                    _has_permit = True
        return _has_permit


# +++++++++++++++++++  END OF FORM PERMITS  +++++++++++++++++++++++

class User_log(Model):
    objects = CustomUserManager()

    user_id = IntegerField(db_index=True)
    username = CharField(max_length=c.USERNAME_MAX_LENGTH, null=True)
    last_name = CharField( max_length=150, null=True)
    email = EmailField(null=True)

    idnumber= CharField(db_index=True, null=True, blank=True, max_length=c.MAX_LENGTH_IDNUMBER)

    last_login = DateTimeField(null=True)
    is_superuser = BooleanField(default=False)
    is_staff = BooleanField(default=False)
    is_active = BooleanField(default=False)
    date_joined = DateTimeField(null=True)

    role = PositiveSmallIntegerField(null=True)
    permits = PositiveSmallIntegerField(null=True)

    activated = BooleanField(default=False)
    activated_at = DateTimeField(null=True)

    country = ForeignKey(Country, null=True, related_name='+', on_delete=PROTECT)
    schoolbase = ForeignKey(Schoolbase, null=True, related_name='+', on_delete=PROTECT)

    mode = CharField(max_length=1, null=True)

    created_at = DateTimeField(null=True)
    created_by = ForeignKey(s.AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    created_username = CharField(max_length=c.USERNAME_MAX_LENGTH, null=True)

    modified_at = DateTimeField(null=True)
    modified_by = ForeignKey(s.AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    modified_username = CharField(max_length=c.USERNAME_MAX_LENGTH, null=True)

    def __str__(self):
        return self.username

    @property
    def mode_str(self):
        mode_str = '-'
        if self.mode is not None:
            mode_str = c.MODE_DICT.get(str(self.mode))
        return mode_str


class Userpermit(sch_mod.AwpBaseModel):  # PR2021-03-18 PR2021-04-20
    # PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
    # AwpModelManager already is in AwpBaseModel
    # was: objects = sch_mod.AwpModelManager()

    role = PositiveSmallIntegerField(default=0)
    page = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)
    action = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)
    description = CharField(db_index=True, max_length=c.MAX_LENGTH_NAME)

    # PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
    usergroups = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)

    # removed: roles = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)
    # removed: pages = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)


class Usergroup(sch_mod.AwpBaseModel):  # PR2021-06-19
    # PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
    # AwpModelManager already is in AwpBaseModel
    # was: objects = sch_mod.AwpModelManager()

    # PR2022-07-05 NOT IN USE
    name = CharField(max_length=c.USERNAME_SLICED_MAX_LENGTH, null=True)
    # PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
    roles = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)


# PR2018-05-06
class Usersetting(Model):
    objects = CustomUserManager()

    user = ForeignKey(User, related_name='+', on_delete=CASCADE)
    key = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)

    setting = CharField(db_index=True, max_length=2048)
    # PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
    # jsonsetting = JSONField(null=True)


# PR2022-12-04 this table contains the usergroup and allowed settings per examyear
class UserAllowed(sch_mod.AwpBaseModel):
    objects = CustomUserManager()

    user = ForeignKey(User, related_name='+', on_delete=CASCADE)
    examyear = ForeignKey(Examyear, related_name='+', on_delete=CASCADE)

    usergroups = TextField(null=True)
    allowed_sections = TextField(null=True)

    # PR2023-01-07 allowed_clusterbases was used in table User, cahnged to allowed_clusters in table accounts_userallowed
    allowed_clusters = TextField(null=True)

    # PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
    # jsonsetting = JSONField(null=True)


# PR2023-02-19 this table contains the info for paying compensation to correctors
class UserCompensation(sch_mod.AwpBaseModel):
    objects = CustomUserManager()

    user = ForeignKey(User, related_name='+', on_delete=CASCADE)

    exam = ForeignKey(Exam, related_name='+', on_delete=CASCADE)
    school = ForeignKey(School, related_name='+', on_delete=CASCADE)

    amount = PositiveSmallIntegerField(default=0)  # entered by corrector
    meetings = PositiveSmallIntegerField(default=0)   # entered by corrector

    correction_amount = SmallIntegerField(default=0)   # entered by ministry
    correction_meetings = SmallIntegerField(default=0) # entered by ministry
    compensation = IntegerField(default=0) # compensation is calculated in cents

    meetingdate1 = DateField(null=True)
    meetingdate2 = DateField(null=True)

    notes = TextField(null=True)

    auth1by = ForeignKey(User, null=True, related_name='+', on_delete=PROTECT)
    auth2by = ForeignKey(User, null=True, related_name='+', on_delete=PROTECT)
    published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    void = BooleanField(default=False)


# PR2023-02-19
class UserCompensation_log(sch_mod.AwpBaseModel):
    objects = CustomUserManager()

    usercompensation_id = IntegerField(db_index=True)

    user_log = ForeignKey(User_log, related_name='+', on_delete=CASCADE)

    school_log = ForeignKey(sch_mod.School_log, related_name='+', on_delete=CASCADE)
    exam_log = ForeignKey(subj_mod.Exam_log, related_name='+', on_delete=CASCADE)

    amount = PositiveSmallIntegerField(default=0)  # entered by corrector
    meetings = PositiveSmallIntegerField(default=0)   # entered by corrector

    correction_amount = SmallIntegerField(default=0)   # entered by ministry
    correction_meetings = SmallIntegerField(default=0) # entered by ministry
    compensation = IntegerField(default=0) # compensation is calculated in cents

    meetingdate1 = DateField(null=True)
    meetingdate2 = DateField(null=True)

    notes = TextField(null=True)

    auth1by = ForeignKey(User, null=True, related_name='+', on_delete=PROTECT)
    auth2by = ForeignKey(User, null=True, related_name='+', on_delete=PROTECT)
    published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    void = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


