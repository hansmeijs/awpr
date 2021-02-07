# PR2018-04-22 PR2020-09-14
from django.db.models import Model, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField, EmailField
from django.contrib.auth.models import AbstractUser, UserManager

# PR2020-12-13 Deprecation warning: django.contrib.postgres.fields import JSONField  will be removed from Django 4
# instead use: django.db.models import JSONField (is added in Django 3)
# PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
from django.contrib.postgres.fields import ArrayField # ,JSONField

from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from schools.models import Country, Examyear, Departmentbase, Department, Schoolbase, School
from awpr import constants as c
from awpr.settings import AUTH_USER_MODEL

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
    # PR2018-08-01 role choices cannot be set in Model, because allowed values depend on request_user. Use role_list in Form instead
    role = PositiveSmallIntegerField(default=0)
    permits = PositiveSmallIntegerField(default=0)

    allowed_depbases = ArrayField(IntegerField(), null=True)
    allowed_levelbases = ArrayField(IntegerField(), null=True)
    allowed_subjectbases = ArrayField(IntegerField(), null=True)
    allowed_clusterbases = ArrayField(IntegerField(), null=True)

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
    created_by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    created_at = DateTimeField(null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
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

    @property
    def role_str(self):
        # PR2018-05-31 NB: self.role = False when None or value = 0
        #if self.role == c.ROLE_08_SCHOOL:
        #    _role_str = _('School')
        #elif self.role == c.ROLE_16_INSP:
        #    _role_str = _('Inspection')
        #elif self.role == c.ROLE_64_SYSTEM:
        #    _role_str = _('System')
        _role_str = c.CHOICES_ROLE_DICT.get(self.role,'')
        return _role_str

    @property
    def permits_str(self):
        # PR2018-05-26 permits_str displays list of permits un UserListForm, e.g.: 'Schooladmin, Authorize, Write'
        permits_all_dict = {
            c.PERMIT_001_READ: _('Read'),
            c.PERMIT_002_EDIT: _('Write'),
            c.PERMIT_004_AUTH1: _('Authorize'),
            c.PERMIT_064_ADMIN: _('Admin'),
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
                    # if permit_int == c.PERMIT_002_EDIT:
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
                for i in range(7, -1, -1): # range(start_value, end_value, step), end_value is not included!
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
            permit_str = c.PERMIT_DICT.get(permit_int)
            if permit_str:
                permits_list.append(permit_str)
        return tuple(permits_list)

    # PR2018-05-30 list of permits that user can be assigned to:
    # - System users can only have permits: 'Admin' and 'Read'
    # - System users can add all roles: 'System', Insp', School', but other roles olny with 'Admin' and 'Read' permit

    # - Inspection and School users can only add their own role
    # - Inspection and School users can have all permits: 'Admin', 'Auth',  'Write' and 'Read'

    # PR2018-07-31 debug. 'def': This is a method, not a @property. Property gave error: 'list' object is not callable
    # see: https://www.b-list.org/weblog/2006/aug/18/django-tips-using-properties-models-and-managers/?utm_medium=twitter&utm_source=twitterfeed

    # PR2018-05-27 property returns True when user has ROLE_64_SYSTEM
    @property
    def is_role_system(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        return self.is_authenticated and self.role is not None and self.role == c.ROLE_64_SYSTEM

    @property
    def is_role_system_perm_admin(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_64_SYSTEM:
                    _has_permit = (c.PERMIT_064_ADMIN in self.permits_tuple)
        return _has_permit

    @property
    def is_role_admin(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        # PR220-09-24 system has also admin rights
        return (self.is_authenticated) and (self.role is not None) and \
               (self.role == c.ROLE_32_ADMIN)

    @property
    def is_role_insp(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        return self.is_authenticated and self.role is not None and self.role == c.ROLE_16_INSP

    @property
    def is_role_school(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        return self.is_authenticated and self.role is not None and self.role == c.ROLE_08_SCHOOL

    @property
    def is_role_teacher(self):
        return self.is_authenticated and self.role is not None and self.role == c.ROLE_04_TEACHER

    @property
    def is_role_student(self):
        return self.is_authenticated and self.role is not None and self.role == c.ROLE_02_STUDENT

    @property
    def is_role_insp_or_admin_or_system(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_64_SYSTEM or self.role == c.ROLE_32_ADMIN or self.role == c.ROLE_16_INSP:
                    _has_permit = True
        return _has_permit

    @property
    def is_role_insp_or_system_and_perm_admin(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_64_SYSTEM or self.role == c.ROLE_16_INSP:
                    if self.is_perm_admin:
                        _has_permit = True
        return _has_permit

    @property
    def is_role_adm_or_sys_and_perm_adm_or_sys(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_32_ADMIN or self.role == c.ROLE_64_SYSTEM:
                    if self.is_perm_admin or self.is_perm_system:
                        _has_permit = True
        return _has_permit

    @property
    def is_role_school_perm_admin(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_08_SCHOOL:
                    _has_permit = (c.PERMIT_064_ADMIN in self.permits_tuple)
        return _has_permit

    @property
    def is_perm_system(self):
        return self.is_authenticated and self.permits_tuple and c.PERMIT_128_SYSTEM in self.permits_tuple

    @property
    def is_perm_admin(self):
        return self.is_authenticated and self.permits_tuple and c.PERMIT_064_ADMIN in self.permits_tuple

    @property
    def is_perm_anlz(self):
        return self.is_authenticated and self.permits_tuple and c.PERMIT_032_ANALYZE in self.permits_tuple

    @property
    def is_perm_auth3(self):
        return self.is_authenticated and self.permits_tuple and c.PERMIT_016_AUTH3 in self.permits_tuple

    @property
    def is_perm_auth2(self):
        return self.is_authenticated and self.permits_tuple and c.PERMIT_008_AUTH2 in self.permits_tuple

    @property
    def is_perm_auth1(self):
        return self.is_authenticated and self.permits_tuple and c.PERMIT_004_AUTH1 in self.permits_tuple

    @property
    def is_perm_edit(self):
        return self.is_authenticated and self.permits_tuple and c.PERMIT_002_EDIT in self.permits_tuple

    @property
    def is_perm_read(self):
        return self.is_authenticated and self.permits_tuple and c.PERMIT_001_READ in self.permits_tuple

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

# +++++++++++++++++++  get and set setting +++++++++++++++++++++++


    def get_usersetting_dict(cls, key_str): # PR2019-03-09 PR2021-01-25
        # function retrieves the string value of the setting row that match the filter and converts it to a dict
        #logger.debug(' ---  get_usersetting_dict  ------- ')
        #  json.dumps converts a dict in a json object
        #  json.loads retrieves a dict (or other type) from a json object

        #logger.debug('cls: ' + str(cls) + ' ' + str(type(cls)))
        setting_dict = {}
        row_setting = None
        try:
            if cls and key_str:
                row = Usersetting.objects.filter(user=cls, key=key_str).order_by('-id').first()
                if row:
                    row_setting = row.setting
                    if row_setting:
                        setting_dict = json.loads(row_setting)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            logger.error('key_str: ', str(key_str))
            logger.error('row_setting: ', str(row_setting))

        return setting_dict

    def set_usersetting_dict(cls, key_str, setting_dict): #PR2019-03-09 PR2021-01-25
        # function saves setting in first row that matches the filter, adds new row when not found
        #logger.debug('---  set_usersetting_dict  ------- ')
        #logger.debug('key_str: ' + str(key_str))
        #logger.debug('setting_dict: ' + str(setting_dict))
        #logger.debug('cls: ' + str(cls) + ' ' + str(type(cls)))

        #  json.dumps converts a dict in a json object
        #  json.loads retrieves a dict (or other type) from a json object

        try:
            if cls and key_str:
                setting_str = json.dumps(setting_dict)
                row = Usersetting.objects.filter(user=cls, key=key_str).order_by('-id').first()
                if row:
                    row.setting = setting_str
                else:
                    # don't add row when setting has no value
                    # note: empty setting_dict {} = False, empty json "{}" = True, therefore check if setting_dict is empty
                    if setting_dict:
                        row = Usersetting(user=cls, key=key_str, setting=setting_str)
                row.save()

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            logger.error('key_str: ', str(key_str))
            logger.error('setting_dict: ', str(setting_dict))
# - end of set_usersetting_dict


    def set_usersetting_from_uploaddict(cls, upload_dict): #PR2021-02-07
        #logger.debug(' ----- set_usersetting_from_uploaddict ----- ')
        # upload_dict: {'selected_pk': {'sel_subject_pk': 46}}
        # logger.debug('upload_dict: ' + str(upload_dict))
        # PR2020-07-12 debug. creates multiple rows when key does not exist ans newdict has multiple subkeys
        # PR2020-10-04 not any more, don't know why
# - loop through keys of upload_dict
        for key, new_setting_dict in upload_dict.items():
            cls.set_usersetting_from_upload_subdict(key, new_setting_dict)
    # - end of set_usersetting_from_uploaddict


    def set_usersetting_from_upload_subdict(cls, key, new_setting_dict):  # PR2021-02-07
        # logger.debug(' ----- set_usersetting_from_upload_subdict ----- ')
        # upload_dict: {'selected_pk': {'sel_subject_pk': 46}}
        # logger.debug('upload_dict: ' + str(upload_dict))
        # PR2020-07-12 debug. creates multiple rows when key does not exist ans newdict has multiple subkeys
        # PR2020-10-04 not any more, don't know why
        # - loop through keys of upload_dict

        # key = 'page_examyear', dict = {'sel_btn': 'examyear'}
        saved_settings_dict = cls.get_usersetting_dict(key)
        # logger.debug('new_setting_dict: ' + str(new_setting_dict))
        # logger.debug('saved_settings_dict: ' + str(saved_settings_dict))
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
        cls.set_usersetting_dict(key, saved_settings_dict)
        return saved_settings_dict
    # - end of set_usersetting_from_upload_subdict


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
        if not self.is_role_insp_or_admin_or_system:
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
            if not self.is_role_insp_or_admin_or_system:
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
            if not self.is_role_insp_or_admin_or_system:
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
                if not self.is_role_insp_or_admin_or_system:
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
    username = CharField(max_length=c.USERNAME_MAX_LENGTH, null=True)
    last_name = CharField( max_length=150, null=True)
    email = EmailField(null=True)

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
    created_by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    created_username = CharField(max_length=c.USERNAME_MAX_LENGTH, null=True)

    modified_at = DateTimeField(null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    modified_username = CharField(max_length=c.USERNAME_MAX_LENGTH, null=True)

    def __str__(self):
        return self.username

    @property
    def mode_str(self):
        mode_str = '-'
        if self.mode is not None:
            mode_str = c.MODE_DICT.get(str(self.mode))
        return mode_str

# PR2018-05-06
class Usersetting(Model):
    objects = CustomUserManager()

    user = ForeignKey(User, related_name='+', on_delete=CASCADE)
    key = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)

    setting = CharField(db_index=True, max_length=2048)
    # PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
    # jsonsetting = JSONField(null=True)

    """ NOT IN USE PR2021-01-25
    @classmethod
    def get_jsonsetting(cls, key_str, user):  # PR2019-07-02
        setting_dict = {}
        if user and key_str:
            row = cls.objects.filter(user=user, key=key_str).first()
            if row:
                if row.jsonsetting:
                     # no need to use json.loads: Was: setting_dict = json.loads(row.jsonsetting)
                    setting_dict = row.jsonsetting

        return setting_dict

    @classmethod
    def set_jsonsetting(cls, key_str, setting_dict, user):  # PR2019-07-02 PR2020-07-12
        #logger.debug('---  set_jsonsetting  ------- ')
        #logger.debug('key_str: ' + str(key_str))
        #logger.debug('setting_dict: ' + str(setting_dict))
        # No need to use json.dumps. Was: new_setting_json = json.dumps(setting_dict)
        if user and key_str:
            rowcount = cls.objects.filter(user=user, key=key_str).count()
            #logger.debug('rowcount: ' + str(rowcount))
            #rows = cls.objects.filter(user=user, key=key_str)
            #for item in rows:
                #logger.debug('row key: ' + str(item.key) + ' jsonsetting: ' + str(item.jsonsetting))

            # don't use get_or_none, gives none when multiple settings exist and will create extra setting.
            row = cls.objects.filter(user=user, key=key_str).first()
            if row:
                #logger.debug('row exists')
                row.jsonsetting = setting_dict
            elif setting_dict:
                #logger.debug('row does not exist')
                row = cls(user=user, key=key_str, jsonsetting=setting_dict)
            row.save()
    """