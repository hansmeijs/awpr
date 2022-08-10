# PR2018-04-22 PR2020-09-14
from django.db import connection
from django.db.models import Model, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField, EmailField
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

    telephone = CharField(null=True, blank=True, max_length=c.MAX_LENGTH_SCHOOLABBREV)

    role = PositiveSmallIntegerField(default=0)

    usergroups = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)
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


    @property
    def usergroup_list(self):
        # --- create list of  usergroups of this user  PR2021-07-26
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' =============== permit_list ============= ')

        usergroup_list = []

        requsr_role = getattr(self, 'role')
        requsr_usergroups = getattr(self, 'usergroups')

        if requsr_role and requsr_usergroups:
            usergroup_list = requsr_usergroups.split(';')

        return usergroup_list
    # - end of usergroup_list


    def permit_list(self, page):
        # --- create list of all permits  of this user PR2021-04-22  PR2021-07-03
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' =============== permit_list ============= ')
            logger.debug('page: ' + str(page) + ' ' + str(type(page)))

        requsr_role = getattr(self, 'role')
        requsr_usergroups = getattr(self, 'usergroups')
        if logging_on:
            logger.debug('requsr_usergroups: ' + str(requsr_usergroups) + ' ' + str(type(requsr_usergroups)))
            logger.debug('requsr_role: ' + str(requsr_role) + ' ' + str(type(requsr_role)))
        # requsr_usergroups_list: ['admin', 'auth2', 'edit'] <class 'list'>

        permit_list = []
        if page and requsr_role and requsr_usergroups:
            requsr_usergroups_list = requsr_usergroups.split(';')
            if logging_on:
                logger.debug('requsr_usergroups_list: ' + str(requsr_usergroups_list) + ' ' + str(type(requsr_usergroups_list)))

            sql_filter = ""
            for usergroup in requsr_usergroups_list:
                sql_filter += " OR (POSITION('" + usergroup + "' IN p.usergroups) > 0)"

            if sql_filter:
                # remove first 'OR ' from sql_filter
                sql_filter = "AND (" + sql_filter[4:] + ")"

                sql_keys = {'page': page, 'role': requsr_role}
                sql_list = ["SELECT p.action FROM accounts_userpermit AS p",
                            "WHERE (p.page = %(page)s OR p.page = 'page_all')",
                            "AND p.role = %(role)s::INT",
                            sql_filter]
                sql = ' '.join(sql_list)

                with connection.cursor() as cursor:
                    cursor.execute(sql, sql_keys)
                    """
                    accounts_userpermit = {role: 8, page: 'page_school', action: 'view', usergroups: 'admin;anlz;auth1;auth2;auth3;edit;read'} 
                    """
                    for row in cursor.fetchall():
                        if logging_on:
                            logger.debug('row: ' + str(row) + ' ' + str(type(row)))

                        if row[0]:
                            permit = 'permit_' + row[0]
                            if permit not in permit_list:
                                permit_list.append(permit)

        if logging_on:
            logger.debug('permit_list: ' + str(permit_list) + ' ' + str(type(permit_list)))
        return permit_list
    # - end of permit_list


    @property
    def is_usergroup_admin(self):
        _has_permit = False
        if self.is_authenticated:
            if self.usergroups is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                usergroups_delim = ''.join((';', self.usergroups, ';' ))
                if ';admin;' in usergroups_delim:
                    _has_permit = True
        return _has_permit


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
    def is_role_system_group_system(self):
        _has_permit = False
        #if self.is_authenticated:
        #    if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        #        if self.role == c.ROLE_128_SYSTEM:
        #            _has_permit = (c.GROUP_128_SYSTEM in self.permits_tuple)
        return _has_permit

    @property
    def is_role_admin(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        # PR220-09-24 system has also admin rights
        return (self.is_authenticated) and (self.role is not None) and \
               (self.role == c.ROLE_064_ADMIN)

    @property
    def is_role_insp(self):
        # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
        return self.is_authenticated and self.role is not None and self.role == c.ROLE_032_INSP

    @property
    def is_role_comm(self):
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

    @property
    def is_role_insp_or_system_and_group_admin(self):
        _has_permit = False
        if self.is_authenticated:
            if self.role is not None: # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
                if self.role == c.ROLE_128_SYSTEM or self.role == c.ROLE_032_INSP:
                    if self.is_usergroup_admin:
                        _has_permit = True
        return _has_permit

 # -----
    def message(self, page_name ='None'):
        # PR2018-08-18 Give message when page is not enabled, page is enabled if _page_message = None
        # school admin may add his own school, subjects etc. Is function, not form
        # system and insp may add schoolyear
        #         _has_permit = False
        # self.is_role_insp_or_system_and_group_admin is: self.is_authenticated AND (self.is_role_system OR self.is_role_insp) AND (self.is_usergroup_admin:

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
            if not self.is_usergroup_admin:
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
                # logger.debug('page: is_role_insp_or_system_and_group_admin')
                return _("You don't have permission to view exam years.")
            else:
                # logger.debug('page: return False')
                return None  # Not disabled:  role_system and role_insp can view examyear_list

# - examyear_modify, only by role_system and role_insp, only admin
        # TODO exclude read, authorize and None permissions
        if page_name == 'examyear_modify':
            # logger.debug('page: examyear_modify')
            if not self.is_role_insp_or_system_and_group_admin:
                # logger.debug('page: is_role_insp_or_system_and_group_admin')
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
                # logger.debug('page: is_role_insp_or_system_and_group_admin')
                return _("You don't have permission to view these items.")
            else:
                # logger.debug('page: return False')
                return None  # Not disabled:  role_system and role_insp can view examyear_list

        # - departments / levels / sectors: can only be modified by role_system and role_insp, only admin
        # TODO exclude read, authorize and None permissions
        if page_name == 'default_items_modify':
            if not self.is_role_insp_or_system_and_group_admin:
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
            if not self.is_role_insp_or_system_and_group_admin:
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
            elif not self.is_usergroup_admin:
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