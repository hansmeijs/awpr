# PR2018-04-22
from django.db.models import Model, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField, EmailField
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import json #PR2018-12-19
from schools.models import Country, Examyear, Departmentbase, Department, Schoolbase, School
from awpr import constants as c
from awpr.settings import AUTH_USER_MODEL

# PR2018-05-10
import logging
logger = logging.getLogger(__name__)

"""
Preferable attributes and methods order in a model (an empty string between the points).
    constants (for choices and other)
    fields of the model
    custom manager indication
    meta
    def __unicode__ (python 2) or def __str__ (python 3)
    other special methods
    def clean
    def save
    def get_absolut_url
    other methods
"""

IS_ACTIVE_DICT = {
    0: _('Inactive'),
    1: _('Active')
}

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
        help_text=_('Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.'),
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
        max_length=50,
        help_text=_('Required. {} characters or fewer.'.format(50)),
        validators=[
            RegexValidator(r'^[\w .\'-]+$',
            _('Enter a valid name. '
            'This value may contain only letters, numbers '
            'and \'/./-/_ characters.'), 'invalid'),
        ],)

    email = EmailField( _('email address'),)
    # PR2018-08-01 role choices cannot be set in Model, because allowed values depend on request_user. Use role_list in Form instead
    role = PositiveSmallIntegerField(
        default=0,
        # choises must be tuple or list, dictionary gives error: 'int' object is not iterable
        choices=c.CHOICES_ROLE
    )
    permits = PositiveSmallIntegerField(default=0)
    allowed_depbase_list = CharField(max_length=255, null=True, blank=True)
    allowed_levelbase_list = CharField(max_length=255, null=True, blank=True)
    allowed_subjectbase_list = CharField(max_length=255, null=True, blank=True)
    allowed_clusterbase_list = CharField(max_length=255, null=True, blank=True)

    activated = BooleanField(default=False)
    activated_at = DateTimeField(null=True)
    country = ForeignKey(Country, null=True, blank=True, related_name='+', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, null=True, blank=True, related_name='+', on_delete=PROTECT)
    schoolbase = ForeignKey(Schoolbase, null=True, blank=True, related_name='+', on_delete=PROTECT)
    depbase = ForeignKey(Departmentbase, null=True, blank=True, related_name='+', on_delete=PROTECT)
    lang = CharField(max_length=4, null=True, blank=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(null=True)

    class Meta:
        ordering = ['username',]

    def __str__(self):
        return self.username

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # otherwise a logrecord would be created every time the save button is clicked without changes
        self.original_username = self.username
        self.original_password = self.password
        self.original_last_name = self.last_name
        self.original_email = self.email
        self.original_last_login = self.last_login
        self.original_is_superuser = self.is_superuser
        self.original_is_staff = self.is_staff
        self.original_is_active = self.is_active
        self.original_date_joined = self.date_joined

        self.original_role = self.role
        self.original_permits = self.permits
        self.original_allowed_depbase_list = self.allowed_depbase_list
        self.original_allowed_levelbase_list = self.allowed_levelbase_list
        self.original_allowed_subjectbase_list = self.allowed_subjectbase_list
        self.original_allowed_clusterbase_list = self.allowed_clusterbase_list

        self.original_activated = self.activated
        self.original_activated_at = self.activated_at
        self.original_country = self.country
        self.original_examyear = self.examyear
        self.original_schoolbase = self.schoolbase
        self.original_depbase = self.depbase
        self.original_lang = self.lang

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

    # check if data has changed. If so: save object
        if self.data_has_changed:
            if self.request:
                if self.request.user:
                    self.modified_by = self.request.user
            # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]  # result = (on_false, on_true)[condition]
            # logger.debug('class User(AbstractUser) save _is_update ' + str(_is_update) + ' self.mode ' + str(self.mode))

            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            # super(User, self).save(force_insert=not is_update, force_update=is_update, **kwargs)
            # self.id gets its value in super(Country, self).save
            # save to logfile

            # PR2018-06-07 self.modified_by is updated in View, couldn't get Country object passed to save function
            # self.modified_at = timezone.now()

            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(User, self).save(force_insert=not self.is_update, force_update=self.is_update, **kwargs)
            # self.id gets its value in super(Country, self).save

            self.save_to_user_log()

        """
        # PR2018-06-07 self.modified_by is updated in View, couldn't get Country object passed to save function
        self.modified_at = timezone.now()
        super(User, self).save(*args, **kwargs)
        # at login: self = user that logs in; kwargs = {'update_fields': ['last_login']}
        logger.debug('User save after super(User) self: ' + str(self) +  ' kwargs: ' + str(kwargs))
        self.save_to_user_log(self)
        """
    def save_to_user_log(self):
        # Create method also saves record
        User_log.objects.create(
            user_id=self.id,
            username=self.username,
            last_name=self.last_name,
            email=self.email,

            last_login=self.last_login,
            is_superuser=self.is_superuser,
            is_staff=self.is_staff,
            is_active=self.is_active,
            date_joined=self.date_joined,

            role=self.role,
            permits=self.permits,
            allowed_depbase_list=self.allowed_depbase_list,
            allowed_levelbase_list=self.allowed_levelbase_list,
            allowed_subjectbase_list=self.allowed_subjectbase_list,
            allowed_clusterbase_list=self.allowed_clusterbase_list,

            activated=self.activated,
            activated_at=self.activated_at,

            country=self.country,
            examyear=self.examyear,
            schoolbase=self.schoolbase,
            depbase=self.depbase,
            lang=self.lang,

            username_mod=self.username_mod,
            last_name_mod=self.last_name_mod,
            email_mod=self.email_mod,
            last_login_mod=self.last_login_mod,
            is_superuser_mod=self.is_superuser_mod,
            is_staff_mod=self.is_staff_mod,
            is_active_mod=self.is_active_mod,
            date_joined_mod=self.date_joined_mod,

            role_mod=self.role_mod,
            permits_mod=self.permits_mod,
            allowed_depbase_list_mod=self.allowed_depbase_list_mod,
            allowed_levelbase_list_mod=self.allowed_levelbase_list_mod,
            allowed_subjectbase_list_mod=self.allowed_subjectbase_list_mod,
            allowed_clusterbase_list_mod=self.allowed_clusterbase_list_mod,

            activated_mod=self.activated_mod,
            activated_at_mod=self.activated_at_mod,

            country_mod=self.country_mod,
            examyear_mod=self.examyear_mod,
            schoolbase_mod=self.schoolbase_mod,
            depbase_mod=self.depbase_mod,
            lang_mod=self.lang_mod,

            mode=self.mode,
            modified_by=self,
            modified_at=self.modified_at
        )

    @property
    def data_has_changed(self):
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        self.username_mod = self.original_username != self.username
        self.password_mod = self.original_password != self.password

        self.last_name_mod = self.original_last_name != self.last_name
        self.email_mod = self.original_email != self.email

        self.last_login_mod = self.original_last_login != self.last_login
        self.is_superuser_mod = self.original_is_superuser != self.is_superuser
        self.is_staff_mod = self.original_is_staff != self.is_staff
        self.is_active_mod = self.original_is_active != self.is_active
        self.date_joined_mod = self.original_date_joined != self.date_joined

        self.role_mod = self.original_role != self.role
        self.permits_mod = self.original_permits != self.permits
        self.allowed_depbase_list_mod = self.original_allowed_depbase_list != self.allowed_depbase_list
        self.allowed_levelbase_list_mod = self.original_allowed_levelbase_list != self.allowed_levelbase_list
        self.allowed_subjectbase_list_mod = self.original_allowed_subjectbase_list != self.allowed_subjectbase_list
        self.allowed_clusterbase_list_mod = self.original_allowed_clusterbase_list != self.allowed_clusterbase_list

        self.activated_mod = self.original_activated != self.activated
        self.activated_at_mod = self.original_activated_at != self.activated_at

        self.country_mod = self.original_country != self.country
        self.examyear_mod = self.original_examyear != self.examyear
        self.schoolbase_mod = self.original_schoolbase != self.schoolbase
        self.depbase_mod = self.original_depbase != self.depbase
        self.lang_mod = self.original_lang != self.lang

        return not self.is_update or \
            self.username_mod or \
            self.password_mod or \
            self.last_name_mod or \
            self.email_mod or \
            self.last_login_mod or \
            self.is_superuser_mod or \
            self.is_staff_mod or \
            self.is_active_mod or \
            self.date_joined_mod or \
            self.role_mod or \
            self.permits_mod or \
            self.allowed_depbase_list_mod or \
            self.allowed_levelbase_list_mod or \
            self.allowed_subjectbase_list_mod or \
            self.allowed_clusterbase_list_mod or \
            self.activated_mod or \
            self.activated_at_mod or \
            self.country_mod or \
            self.examyear_mod or \
            self.schoolbase_mod or \
            self.depbase_mod or \
            self.lang_mod

    def email_user(self, *args, **kwargs):
        # PR2018-04-25 debug. Had wrong number of arguments:
        # send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
        send_mail(
            '{}'.format(args[0]),
            '{}'.format(args[1]),
            #'{}'.format(args[2]),
            'info@awponline.net',
            [self.email],
            fail_silently=False,
        )

    @property
    def role_str(self):
        # PR2018-05-31 NB: self.role = False when None or value = 0
        #if self.role == c.ROLE_00_SCHOOL:
        #    _role_str = _('School')
        #elif self.role == c.ROLE_01_INSP:
        #    _role_str = _('Inspection')
        #elif self.role == c.ROLE_02_SYSTEM:
        #    _role_str = _('System')
        _role_str = c.CHOICES_ROLE_DICT.get(self.role,'')
        return _role_str

    @property
    def country_str(self): # PR2018-08-01
        if self.country:
            _country_str = self.country.name
        else:
            _country_str = ''
        return _country_str

    @property
    def country_locked(self): # PR2018-08-17
        _country_locked = False
        if self.country:
            _country_locked = self.country.locked
        return _country_locked

    @property
    def examyear_str(self): # PR2018-09-02
        if self.examyear:
            return str(self.examyear)
        else:
            return _("<No exam year selected>")

    @property
    def examyear_locked(self): # PR2018-08-17
        # examyear is locked when country is locked or examyear is locked
        _examyear_locked = False
        if self.country:
            if self.country.locked:
                _examyear_locked = True
        if not _examyear_locked:
            if self.examyear:
                if self.examyear.locked:
                    _examyear_locked = True
        return _examyear_locked

    # TODO check if in in use
    #@property
    #def school(self): # PR2018-09-15
    #    school = None
    #    if self.country and self.examyear and self.schoolbase:
    #        # get school from this schoolbase and this examyear. Countr is field of Examyear, therefore filter Counrry not necessary
    #        school= School.objects.filter(base=self.schoolbase, examyear=self.examyear).first()
    #    return school

    @property
    def schoolabbrev(self): # PR2018-12-18 used in user_list
        abbrev = '-'
        if self.country and self.examyear and self.schoolbase:
            school= School.objects.filter(base=self.schoolbase, examyear=self.examyear).first()
            if school:
                if school.abbrev:
                    abbrev = school.abbrev
        return abbrev
    @property

    def school_locked(self): # PR2018-09-03
        # school is locked when (country is locked OR examyear is locked OR school is locked)
        _school_locked = True
        if self.country and self.examyear and self.schoolbase:
            if not self.country.locked and not self.examyear_locked:
                # get school from this schoolbase and this examyear
                school= School.objects.filter(base=self.schoolbase, examyear=self.examyear).first()
                if school:
                    _school_locked = school.locked
        return _school_locked

    @property
    def department(self): # PR2018-11-19 Used in StudentAddForm
        department = None
        if self.country and self.examyear and self.schoolbase and self.depbase:
            # get school from this schoolbase and this examyear. Countr is field of Examyear, therefore filter Counrry not necessary
            department= Department.objects.filter(base=self.depbase, examyear=self.examyear).first()
        return department

    @property
    def permits_str(self):
        # PR2018-05-26 permits_str displays list of permits un UserListForm, e.g.: 'Schooladmin, Authorize, Write'
        permits_all_dict = {
            c.PERMIT_01_READ: _('Read'),
            c.PERMIT_02_WRITE: _('Write'),
            c.PERMIT_04_AUTH: _('Authorize'),
            c.PERMIT_08_ADMIN: _('Admin'),
        }
        permits_str = ''
        if self.permits_tuple is not None:
            #logger.debug('class User(AbstractUser): permits_tuple: ' + str(self.permits_tuple))
            for permit_int in self.permits_tuple:
                #logger.debug('class User(AbstractUser): permit_int: ' + str(permit_int))
                list_item = permits_all_dict.get(permit_int)
                #logger.debug('class User(AbstractUser): permits_str list_item: ' + str(list_item))

                if list_item is not None:
                    # PR2018-06-01 debug: ... + (list_item) gives error: must be str, not __proxy__
                    # solved bij wrapping with str(): + str(list_item)
                    permits_str = permits_str + ', ' + str(list_item)
                    # stop when write permission is found . 'Read' will then not be displayed
                    # PR2018-07-26 debug: doesn't work, because tuple is not in reverse order
                    # if permit_int == c.PERMIT_02_WRITE:
                    #    break
        if not permits_str: # means: if permits_str == '':
            permits_str = ', None'
        # slice off first 2 characters: ', '
        permits_str = permits_str[2:]
        #logger.debug('class User(AbstractUser): permits_str: ' + str(permits_str))
        return permits_str

    @property
    def permits_tuple(self):
        # PR2018-05-27 permits_tuple converts self.permits string into tuple, e.g.: permits=15 will be converted to permits_tuple=(1,2,4,8)
        permits_int = self.permits
        permits_list = []
        if permits_int is not None:
            if permits_int != 0:
                for i in range(6, -1, -1): # range(start_value, end_value, step), end_value is not included!
                    power = 2 ** i
                    if permits_int >= power:
                        permits_int = permits_int - power
                        permits_list.insert(0, power) # list.insert(0,value) adds at the beginning of the list
        if not permits_list:
            permits_list = [0]
        return tuple(permits_list)

    @property
    def permits_str_tuple(self): # 2018-12-23
        permits_list = []
        for permit_int in self.permits_tuple:
            permit_str = c.PERMIT_DICT.get(permit_int,'')
            if permit_str:
                permits_list.append(permit_str)
        return tuple(permits_list)









    # PR2018-05-30 list of permits that user can be assigned to:
    # - System users can only have permits: 'Admin' and 'Read'
    # - System users can add all roles: 'System', Insp', School', but other roles olny with 'Admin' and 'Read' permit

    # - Inspection and School users can only add their own role
    # - Inspection and School users can have all permits: 'Admin', 'Auth',  'Write' and 'Read'

    @property
    def permits_choices(self):
        # PR201806-01 function creates tuple of permits, used in UserAddForm, UserEditForm
        # permit_choices: ((1, 'Read'), (2, 'Write'), (4, 'Authorize'), (8, 'Admin'))

        if self.role is not None:  # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
            choices = [
                (c.PERMIT_01_READ, _('Read')),
                (c.PERMIT_02_WRITE, _('Write')),
                (c.PERMIT_04_AUTH, _('Authorize')),
                (c.PERMIT_08_ADMIN, _('Admin'))
            ]
        else:
            # get permit 'None'
            choices = [(c.PERMIT_00_NONE, _('None'),),]
        return tuple(choices)


    @property
    def country_choices_NOT_IN_USE(self):
        # PR2018-05-31 country_choices = [(1, 'SXM01 -  Milton Peters College')]
        # only role System can choose country in headerbar, other roles have list of their own country
        # this function is used in UserAddForm
        _country_choices = []
        if self.is_role_system:
            countries = Country.objects.order_by('name')
        else:
            # PR2018-06-01 debug: objects.get gives error: 'Country' object is not iterable
            # use objects.filter instead
            countries = Country.objects.filter(id=self.country.id)
        for country in countries:
            if country.name is not None:
                _item = (country.id, country.name)
                logger.debug('SubjectdefaultAddForm __init__ _item: ' + str(_item) + ' Type: ' + str(type(_item)))
                _country_choices.append(_item)
        logger.debug('SubjectdefaultAddForm __init__ _country_choices: ' + str(_country_choices) + ' Type: ' + str(type(_country_choices)))

        return _country_choices

    def examyear_correct(self, instance_examyear_id):
        # PR2018-11-02 check if:
        #  - both country and examyear have value
        #  - self.examyear.country is same as self.country
        #  - self.examyear is same as instance_examyear

        is_ok = False
        if self.country is not None and self.examyear is not None:
            if self.examyear.country.id == self.country.id:
                if self.examyear.id == instance_examyear_id:
                    is_ok = True
        return is_ok

    # PR2018-07-31 debug. This is a method, not a @property. Property gave error: 'list' object is not callable
    # see: https://www.b-list.org/weblog/2006/aug/18/django-tips-using-properties-models-and-managers/?utm_medium=twitter&utm_source=twitterfeed
    def schoolbase_choices(self, selected_user):
        # PR2018-06-02 this function is used in UserEditForm, only when request_user.role = system or Insp
        # PR2018-07-28 Show only schools from selected_user.country
        # self = request_user, not selected_user when called by UserEditForm

        # logger.debug('class User schoolbase_choices  request_user.username: ' + str(self.username))

        _schools = None
        _choices = []
        _choices.append((0, 'None'))
        if selected_user.examyear: # _selecteduser_countryid = False when _selecteduser_countryid == 0 or None:
            _schools = School.objects.filter(examyear=selected_user.examyear)
            logger.debug('class User(AbstractUser) _schools: ' + str(_schools))
            if _schools:
                for _school in _schools:
                    _school_str = ''
                    if _school.code is not None:
                        _school_str = str(_school.code) + ' - '
                    if _school.name is not None:
                        _school_str = _school_str + str(_school.name)
                    # logger.debug('class User(AbstractUser) _schooldefault_str: ' + str(_schooldefault_str))
                    _choices.append((_school.base.id, _school_str))

        # logger.debug('class User(AbstractUser) schooldefault_choices: ' + str(_choices))
        return _choices


    # PR2018-07-31 debug. This is a method, not a @property. Property gave error: 'list' object is not callable
    # see: https://www.b-list.org/weblog/2006/aug/18/django-tips-using-properties-models-and-managers/?utm_medium=twitter&utm_source=twitterfeed
    def depbase_choices(self, selected_user):
        # PR2018-06-02 this function is used in UserEditForm
        # PR2018-08-29 Show only departments from depbase_list of selected_user.schooldefault
        # self = request_user, not selected_user when called by UserEditForm

        logger.debug('class User depbase_choices  request_user.username: ' + str(self.username))
        logger.debug('class User depbase_choices  request_user.schooldefault: ' + str(self.schoolbase))
        logger.debug('class User depbase_choices  selected_user.username: ' + str(selected_user.username))
        logger.debug('class User depbase_choices  selected_user.schooldefault: ' + str(selected_user.schooldefault))


        _selecteduser_schooldefault_id = 0
        if selected_user.schooldefault is not None:
            _selecteduser_schooldefault_id = selected_user.schooldefault.id
        _department = None
        _choices = []
        _choices.append((0, 'None'))
        if _selecteduser_schooldefault_id: # _selecteduser_schooldefault_id = False when _selecteduser_schooldefault_id == 0 or None:
            _department = Department.objects.filter(department_id=_selecteduser_schooldefault_id)
            logger.debug('class User(AbstractUser) _department: ' + str(_department))
            if _department:
                for _schooldefault in _department:
                    _schooldefault_str = ''
                    if _schooldefault.code is not None:
                        _schooldefault_str = str(_schooldefault.code) + ' - '
                    if _schooldefault.name is not None:
                        _schooldefault_str = _schooldefault_str + str(_schooldefault.name)
                    # logger.debug('class User(AbstractUser) _schooldefault_str: ' + str(_schooldefault_str))
                    _choices.append((_schooldefault.id, _schooldefault_str))

        logger.debug('class User(AbstractUser) schooldefault_choices: ' + str(_choices))
        return _choices


    # PR2018-07-31 debug. This is a method, not a @property. Property gave error: 'list' object is not callable
    # see: https://www.b-list.org/weblog/2006/aug/18/django-tips-using-properties-models-and-managers/?utm_medium=twitter&utm_source=twitterfeed
    def examyear_choices(self, selected_user):
        # PR2018-06-02 this function is used in UserEditForm, only when request_user.role = system or Insp
        # PR2018-07-28 Show only examyears from selected_user.country
        # self = request_user, not selected_user when called by UserEditForm

        #logger.debug('class User examyear_choices  request_user.username: ' + str(self.username))
        #logger.debug('class User examyear_choices  request_user.country: ' + str(self.country))
        #logger.debug('class User examyear_choices  selected_user.username: ' + str(selected_user.username))
        #logger.debug('class User examyear_choices  selected_user.country: ' + str(selected_user.country))

        _selecteduser_countryid = 0
        if selected_user.country is not None:
            _selecteduser_countryid = selected_user.country.id
        _schooldefaults = None
        _choices = []
        _choices.append((0, 'None'))
        if _selecteduser_countryid: # _selecteduser_countryid = False when _selecteduser_countryid == 0 or None:
            _examyears = Examyear.objects.filter(country_id=_selecteduser_countryid)
            # logger.debug('class User examyear_choices _examyears: ' + str(_examyears))
            if _examyears:
                for _item in _examyears:
                    _item_str = ''
                    if _item.examyear is not None:
                        _item_str = str(_item.examyear)
                    # logger.debug('class User examyear_choices _item_str: ' + str(_item_str))
                    _choices.append((_item.id, _item_str))

        # logger.debug('class User examyear_choices class User examyear_choices: ' + str(_choices))
        return _choices

    # PR2018-07-31 debug. This is a method, not a @property. Property gave error: 'list' object is not callable
    # see: https://www.b-list.org/weblog/2006/aug/18/django-tips-using-properties-models-and-managers/?utm_medium=twitter&utm_source=twitterfeed
    def user_settings(self):  # PR2018-12-19
        # function gets usersettings MENU_SELECTED
        settings = {}
        usersettings = Usersetting.objects.filter(user=self)
        if usersettings:
            for usersetting in usersettings:
                # TODO: remove filter and get all settings
                if usersetting.key_str == c.KEY_USER_MENU_SELECTED:
                    if usersetting.char01:
                        settings[c.KEY_USER_MENU_SELECTED] = usersetting.char01
                        # logger.debug('user_settings: ' + str(user_settings) + ' type: ' +  str(type(user_settings)))
        settings_str = json.dumps(settings)
        # logger.debug('user_settings_str: ' + str(user_settings_str) + ' type: ' +  str(type(user_settings_str)))
        return settings_str

    @property
    def depbase_str(self): # PR2018-11-23
        dep_str = ''
        if self.depbase is not None:
            dep = Department.objects.filter(base=self.depbase, examyear=self.examyear).first()
            if dep is not None:
                dep_str = dep.abbrev
        return dep_str

    @property
    def allowed_depbase_list_str(self): # PR2018-11-23
        return Department.depbase_list_str(depbase_list=self.allowed_depbase_list, examyear=self.examyear)

    @property
    def is_active_str(self): # PR108-08-09
        return str(c.IS_ACTIVE_DICT.get(int(self.is_active)))

    @property
    def is_active_choices(self): # PR108-06-22
        return c.IS_ACTIVE_CHOICES.get(int(self.is_active))

    # PR2018-05-27 property returns True when user has ROLE_02_SYSTEM
    @property
    def is_role_system(self):
        _has_role = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_02_SYSTEM:
                    _has_role = True
        return _has_role

    @property
    def is_role_system_perm_admin(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_02_SYSTEM:
                    _has_permit = (c.PERMIT_08_ADMIN in self.permits_tuple)
        return _has_permit

    @property
    def is_role_insp(self):
        _has_role = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_01_INSP:
                    _has_role = True
        return _has_role

    @property
    def is_role_school(self):
        _has_role = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_00_SCHOOL:
                    _has_role = True
        return _has_role

    @property
    def is_role_insp_or_system(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_02_SYSTEM or self.role == c.ROLE_01_INSP:
                    _has_permit = True
        return _has_permit

    @property
    def is_role_insp_or_system_and_perm_admin(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_02_SYSTEM or self.role == c.ROLE_01_INSP:
                    if self.is_perm_admin:
                        _has_permit = True
        return _has_permit


    @property
    def is_role_school_perm_admin(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_00_SCHOOL:
                    _has_permit = (c.PERMIT_08_ADMIN in self.permits_tuple)
        return _has_permit

    @property
    def is_perm_admin(self):
        _has_permit = False
        if self.is_authenticated:
            _has_permit = c.PERMIT_08_ADMIN in self.permits_tuple
        return _has_permit

    @property
    def is_perm_auth(self):
        _has_permit = False
        if self.is_authenticated:
            _has_permit = c.PERMIT_04_AUTH in self.permits_tuple
        return _has_permit

    @property
    def is_perm_write(self):
        _has_permit = False
        if self.is_authenticated:
            _has_permit = c.PERMIT_02_WRITE in self.permits_tuple
        return _has_permit

    @property
    def is_perm_read_only(self):
        _has_permit = False
        if self.is_authenticated:
            _has_permit = c.PERMIT_01_READ in self.permits_tuple
        return _has_permit

    @property
    def may_add_or_edit_users(self):
        # PR2018-05-30  user may add user if:
        # role system: if perm admin
        # role insp:   if perm_admin and country not None
        # role school: if perm_admin and country not None and schooldefault not None
        _has_permit = False
        if self.is_perm_admin:
            if self.is_role_system:
                _has_permit = True
            elif self.is_role_insp:
                if self.country is not None:
                    _has_permit = True
            elif self.is_role_school:
                if self.country is not None:
                    if self.schoolbase is not None:
                        _has_permit = True
        return _has_permit



# +++++++++++++++++++  FORM PERMITS  +++++++++++++++++++++++

# - user
    @property
    def message_user_authenticated(self):
        return _("You must be logged in to view this page.")

    @property
    def enable_user_view_modify(self):
        return not bool(self.message('user_view_modify'))

    @property
    def message_user_view_modify(self):  # PR2018-08-18
        return self.message('user_view_modify')

# - country
    @property
    def enable_country_view(self):  # PR2018-08-18
        return not bool(self.message('country_view'))

    @property
    def message_country_view(self):  # PR2018-08-18
        return self.message('country_view')

    @property
    def enable_country_modify(self):  # PR2018-08-18
        enable_modify = False
        enable_view = not bool(self.message('country_view'))
        if enable_view:
            if self.is_perm_admin:
                enable_modify = True
        return enable_modify

    @property
    def message_country_modify(self):  # PR2018-08-18
        if not self.enable_country_modify:
            return _("You don't have permission to modify countries.")
        else:
            return None
# - examyear
    @property
    def enable_examyear_view(self):  # PR2018-08-19
        return not bool(self.message('examyear_view'))

    @property
    def message_examyear_view(self):  # PR2018-08-18
        return self.message('examyear_view')

    @property
    def enable_examyear_modify(self):  # PR2018-08-18
        return not bool(self.message('examyear_modify'))

    @property
    def message_examyear_modify(self):  # PR2018-08-18
        return self.message('examyear_modify')

# -- default items: schooldefault / subjectdefault / departments / levels / sectors:
    @property
    def enable_default_items_view(self):  # PR2018-08-19
        return not bool(self.message('default_items_view'))

    @property
    def message_default_items_view(self):  # PR2018-08-18
        return self.message('default_items_view')

    @property
    def enable_default_items_modify(self):  # PR2018-08-18
        return not bool(self.message('default_items_modify'))

    @property
    def message_default_items_modify(self):  # PR2018-08-18
        return self.message('default_items_modify')

    # -- schemes, levels, sectors deps, subjects:
    @property
    def enable_schemes_view(self):  # PR2018-08-23
        return not bool(self.message('scheme_etc_view'))

    @property
    def message_schemes_view(self):  # PR2018-08-23
        return self.message('scheme_etc_view')

    @property
    def enable_schemes_modify(self):  # PR2018-08-23
        return not bool(self.message('scheme_etc_edit'))

    @property
    def message_schemes_modify(self):  # PR2018-08-23
        return self.message('scheme_etc_edit')

    # -- schools
    @property
    def enable_schools_view(self):  # PR2018-09-15
        return not bool(self.message('school_view'))

    @property
    def message_schools_view(self):  # PR2018-09-15
        return self.message('school_view')

    @property
    def enable_schools_modify(self):  # PR2018-09-15
        return not bool(self.message('school_edit'))

    @property
    def message_schools_modify(self):  # PR2018-09-15
        return self.message('school_edit')

    @property
    def enable_schools_add_delete(self):  # PR2018-09-15
        return not bool(self.message('school_add_delete'))

    @property
    def message_schools_add_delete(self):  # PR2018-09-15
        return self.message('school_add_delete')

# -- students: PR2018-09-02
    @property
    def enable_students_view(self):
        return not bool(self.message('students_view'))

    @property
    def message_students_view(self):
        return self.message('students_view')

    @property
    def enable_students_modify(self):
        return not bool(self.message('students_modify'))

    @property
    def message_students_modify(self):
        return self.message('students_modify')

 # -----
    def message(self, page_name ='None'):
        # PR2018-08-18 Give message when page is not enabled, page is enabled if _page_message = None
        # school admin may add his own school, subjects etc. Is function, not form
        # system and insp may add schoolyear
        #         _has_permit = False
        # self.is_role_insp_or_system_and_perm_admin is: self.is_authenticated AND (self.is_role_system OR self.is_role_insp) AND (self.is_perm_admin:

        _no_permission =_("You don't have permission to view this page.")

# ===== every user must be authenticated
        if not self.is_authenticated:
            # logger.debug('message : user not authenticated')
            return _("You must be logged in to view this page.")
        # logger.debug('message : user is authenticated')

# ===== every insp and school user must have a country PR2018-09-15
        if not self.is_role_system:
            if not self.country:
 # >>>>>
                return _("You are not connected to a country. You cannot view this page.")

# ===== every school user must have a school PR2018-09-15
        if not self.is_role_insp_or_system:
            if not self.schoolbase:
                return _("You are not connected to a school. You cannot view this page.")

# ==============================================================
# ----- these pages can be viewed without country selected:
# ==============================================================
    # - userlist: only admin can view and modify userlist
        if page_name == 'user_view_modify':
            # only admins can view user list
            if not self.is_perm_admin:
                return _no_permission
            else:
                return None
    # - countrylist: only system can view countrylist
        if page_name == 'country_view':
            # logger.debug('page: country_view username: ' + str(self.username) + ' role: ' + str(self.role))
            if not self.is_role_system:
                # logger.debug('page: not self.is_role_system')
 # >>>
                return _("You don't have permission to view countries.")
            else:
                return None # Not disabled: role_system can view country list
# =====================================================================
# ===== country selected
# =====================================================================
        if not self.country:
            # logger.debug('page: user not connected to a country')
  # >>>>>
            return _("You are not connected to a country. You cannot view this page.")
# =====================================================================
# ===== the rest of the pages cannot be viewed without country selected
# =====================================================================
    # - userlist, but only by role_insp
        if page_name == 'user_view':
            # logger.debug('page: user_view')
            if self.is_role_insp:
                # logger.debug('page: user is_role_insp')
                return None  # Not disabled:  role_insp can view userlist without school selected
            elif not self.schoolbase:  # role_school need school selected to view userlist
                # logger.debug('page: user not connected to a school')
                return _("You are not connected to a school. You cannot view this page.")
            else:
                # logger.debug('page: user connected to a school')
                return None  # Not disabled:  role_system can view userlist without country selected

    # - examyear_list, can only be viewed by role_system and role_insp
        if page_name == 'examyear_view':
            # logger.debug('page: examyear_view')
            if not self.is_role_insp_or_system:
                # logger.debug('page: is_role_insp_or_system_and_perm_admin')
                return _("You don't have permission to view exam years.")
            else:
                # logger.debug('page: return False')
                return None  # Not disabled:  role_system and role_insp can view examyear_list

# - examyear_modify, only by role_system and role_insp, only admin
        # TODO exclude read, authorize and None permissions
        if page_name == 'examyear_modify':
            # logger.debug('page: examyear_modify')
            if not self.is_role_insp_or_system_and_perm_admin:
                # logger.debug('page: is_role_insp_or_system_and_perm_admin')
                return _("You don't have permission to modify exam years.")
            elif self.country_locked:
                # logger.debug('page: country_locked')
                return _("This country is locked. You cannot modify exam years.")
            else:
                # logger.debug('page: return None')
                return None  # Not disabled: admin of role_system and role_insp can modify examyears, if country not locked
# =====================================================================
# ===== no permissions if no examyear selected
# =====================================================================
        if not self.examyear:
            return _("You must first select an examyear, before you can view this page.")

# =====================================================================
# ===== the rest of the pages cannot be viewed without examyear selected
# =====================================================================

        # - departments / levels / sectors:  can only be viewed by role_system and role_insp
        if page_name == 'default_items_view':
            if not self.is_role_insp_or_system:
                # logger.debug('page: is_role_insp_or_system_and_perm_admin')
                return _("You don't have permission to view these items.")
            else:
                # logger.debug('page: return False')
                return None  # Not disabled:  role_system and role_insp can view examyear_list

        # - departments / levels / sectors: can only be modified by role_system and role_insp, only admin
        # TODO exclude read, authorize and None permissions
        if page_name == 'default_items_modify':
            if not self.is_role_insp_or_system_and_perm_admin:
                return _("You don't have permission to modify these items.")
            elif self.country_locked:
                return _("This country is locked. You cannot modify these items.")
            else:
                return None  # TODO: change: Not disabled: admin of role_system and role_insp can modify default schools, if country not locked

        # - scheme, PR2018-08-23   >>>>>>>>>/ subject / package:
        if page_name == 'scheme_etc_view':
            return None  # Not disabled:  anyone can view schemes

        # - scheme, PR2018-08-23   >>>>>>>>>schooldefault / subjectdefault / departments / levels / sectors: can only be modified by role_system and role_insp, only admin
        if page_name == 'scheme_etc_edit':
            # TODO exclude read, authorize and None permissions
            if not self.is_role_insp_or_system_and_perm_admin:
                return _("You don't have permission to modify these items.")
            elif self.country_locked:
                return _("This country is locked. You cannot modify these items.")
            elif self.examyear_locked:
                return _("This examyear is locked. You cannot modify these items.")
            else:
                return None  # Not disabled: admin of role_system and role_insp can modify schemes, if country not locked


        # - school PR2018-09-15
        if page_name == 'school_view':
            # filter that role-school users can only view their own school is part of view
            return None  # Not disabled:  anyone can view school


 # =====================================================================
# ===== no permissions if no schoolbase selected
# =====================================================================
        if not self.schoolbase:
            return _("You are not connected to a school. You cannot view this page.")

# =====================================================================
# ==== the rest of the pages cannot be viewed without schooldefault selected
# =====================================================================

        if page_name == 'school_edit' or page_name == 'school_add_delete':
            if self.country_locked:
                return _("This country is locked. You cannot modify schools.")
            elif self.examyear_locked:
                return _("This examyear is locked. You cannot modify schools.")
            elif not self.is_perm_admin:
                # only admin users can modify school
                # filter that role-school users can only modify their own school is part of form-get
                return _("You don't have permission to modify schools.")
            elif page_name == 'school_add_delete':
                if not self.is_role_insp_or_system:
                    return _("You don't have permission to add or delete schools.")
                else:
                    return None
            else:
                return None  # Not disabled: admin of role_system and role_insp can modify schemes, if country not locked

        # - students
        if page_name == 'students_view':
            return None  # Not disabled:  anyone can view students

        # - scheme, also for school PR2018-08-23   >>>>>>>>>schooldefault / subjectdefault / departments / levels / sectors: can only be modified by role_system and role_insp, only admin
        if page_name == 'students_modify':
            # TODO activate rule that only schools can enter students
            #  if not self.is_role_school:
            #    return _("You don't have permission to modify these items.")
            if self.country_locked:
                return _("This country is locked. You cannot modify these items.")
            elif self.examyear_locked:
                return _("This examyear is locked. You cannot modify these items.")
            elif self.school_locked:
                return _("This school is locked. You cannot modify these items.")
            # TODO  student_locked:, exclude read, authorise, None permissions
            #     return _("This student is locked. You cannot modify thise item.")
            else:
                return None  # Not disabled: admin of role_system and role_insp can modify schemes, if country not locked

# =====================================================================
# ===== the rest of the pages cannot be viewed without schooldefault selected
# =====================================================================

        return _("Error. You cannot view this page.")


# +++++++++++++++++++  END OF FORM PERMITS  +++++++++++++++++++++++

class User_log(Model):
    objects = CustomUserManager()

    user_id = IntegerField(db_index=True)

    username = CharField(max_length=150, null=True)
    # Field is not in use: first_name = CharField(max_length=30, null=True)
    # Field is not in use: first_name_mod = BooleanField(default=False)
    last_name = CharField( max_length=150, null=True)
    email = EmailField(null=True)
    last_login = DateTimeField(null=True)
    is_superuser = BooleanField(default=False)
    is_staff = BooleanField(default=False)
    is_active = BooleanField(default=False)
    date_joined = DateTimeField(null=True)
    permits = PositiveSmallIntegerField(null=True)
    role = PositiveSmallIntegerField(null=True)
    allowed_depbase_list = CharField(max_length=255, null=True)
    allowed_levelbase_list = CharField(max_length=255, null=True)
    allowed_subjectbase_list = CharField(max_length=255, null=True)
    allowed_clusterbase_list = CharField(max_length=255, null=True)

    activated = BooleanField(default=False)
    activated_at = DateTimeField(null=True)
    country = ForeignKey(Country, null=True, related_name='+', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, null=True, related_name='+', on_delete=SET_NULL)
    schoolbase = ForeignKey(Schoolbase, null=True, related_name='+', on_delete=PROTECT)
    depbase = ForeignKey(Departmentbase, null=True, related_name='+', on_delete=SET_NULL)
    lang = CharField(max_length=4, null=True)

    username_mod = BooleanField(default=False)
    last_name_mod = BooleanField(default=False)
    email_mod = BooleanField(default=False)
    last_login_mod = BooleanField(default=False)
    is_superuser_mod = BooleanField(default=False)
    is_staff_mod = BooleanField(default=False)
    is_active_mod = BooleanField(default=False)
    date_joined_mod = BooleanField(default=False)

    permits_mod = BooleanField(default=False)
    role_mod = BooleanField(default=False)
    allowed_depbase_list_mod = BooleanField(default=False)
    allowed_levelbase_list_mod = BooleanField(default=False)
    allowed_subjectbase_list_mod = BooleanField(default=False)
    allowed_clusterbase_list_mod = BooleanField(default=False)

    activated_mod = BooleanField(default=False)
    activated_at_mod = BooleanField(default=False)
    country_mod = BooleanField(default=False)
    examyear_mod = BooleanField(default=False)
    schoolbase_mod = BooleanField(default=False)
    depbase_mod = BooleanField(default=False)
    lang_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    @property
    def mode_str(self):
        mode_str = '-'
        if self.mode is not None:
            mode_str = c.MODE_DICT.get(str(self.mode))
        return mode_str

    @property
    def is_active_str(self): # PR108-08-29
        return str(c.IS_ACTIVE_DICT.get(int(self.is_active)))

# PR2018-05-06
class Usersetting(Model):
    objects = CustomUserManager()

    user = ForeignKey(User, related_name='usr_settings', on_delete=CASCADE)
    key_str = CharField(max_length=20)
    char01 = CharField(max_length=2048, null=True)
    char02 = CharField(max_length=2048, null=True)
    int01 = IntegerField(null=True)
    int02 = IntegerField(null=True)
    bool01 = BooleanField(default=False)
    bool02 = BooleanField(default=False)
    date01 = DateTimeField(null=True)
    date02 = DateTimeField(null=True)
