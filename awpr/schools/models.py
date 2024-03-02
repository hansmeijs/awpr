# PR2018-04-13
# from django.contrib.auth import get_user_model

# PR2020-12-13 Deprecation warning: django.contrib.postgres.fields import JSONField  will be removed from Django 4
# instead use: django.db.models import JSONField (is added in Django 3)
# PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
# from django.contrib.postgres.fields import ArrayField #, JSONField

from django.db.models import Model, Manager, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField, DateField, FileField
from django.utils import timezone

import json

# PR2018-05-05 use AUTH_USER_MODEL
from awpr.settings import AUTH_USER_MODEL
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _
from awpr import constants as c
from awpr import settings as s
from awpr.storage_backends import PrivateMediaStorage


# PR2018-09-15 Departmnet moved from Subjects to Schools; because this doesn/'t work, circular reference: from subjects.models import Department

import logging
logger = logging.getLogger(__name__)

# PR2018-04-22: backup: (venv) C:\dev\awpr\awpr>py -3 manage.py dumpdata schools --format json --indent 4 > schools/backup/schools.json
#               restore: (venv) C:\dev\awpr\awpr>py -3 manage.py loaddata schools/backup/schools.json

# The clean() method on a Field subclass is responsible for running to_python() , validate() , and run_validators()
# in the correct order and propagating their errors.
# If, at any time, any of the methods raise ValidationError, the validation stops and that error is raised.
# This method returns the clean data, which is then inserted into the cleaned_data dictionary of the form.


# PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
# AwpModelManager adds function get_or_none.
class AwpModelManager(Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except:
            return None
# - end of AwpModelManager


# PR2019-03-12 from https://godjango.com/blog/django-abstract-base-class-model-inheritance/
# tables  inherit fields from this class
class AwpBaseModel(Model):
    objects = AwpModelManager()

    modifiedby = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)

    #PR2020-12-11 debug: on migrate (adding modifiedat field) got the warning:
    # RuntimeWarning: DateTimeField modifiedat received a naive datetime while time zone support is active.
    # solved by changing 'datetime.now' to 'timezone.now()'
    # was: modifiedat = DateTimeField(default=datetime.now)
    # next bug:  HINT: It seems you set a fixed date / time / datetime value as default for this field.
    # This may not be what you want. If you want to have the current date as default, use `django.utils.timezone.now`
    # was:  modifiedat = DateTimeField(default=timezone.now())
    # this one works: modifiedat = DateTimeField(default=timezone.now)
    modifiedat = DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def get_model_name(self):
        return self.__class__.__name__

    def save(self, *args, **kwargs):
        # Note: now_utc and timezone.now() give the same result: PR2020-10-05
        # - get now without timezone
        #   timezone.now() is timezone aware
        # - datetime.now() is timezone naive. PR2018-06-07
        #   now_utc_naive = datetime.utcnow()
        # - convert now to timezone utc
        #   now_utc = now_utc_naive.replace(tzinfo=pytz.utc)
        # now_utc and timezone.now() give the same result
        # now_utc: 2020-10-05 15:48:01.579181+00:00 <class 'datetime.datetime'>
        # timezone.now(): 2020-10-05 15:48:01.580175+00:00 <class 'datetime.datetime'>

        # skip updating modifiedby and modifiedat when request is None
        #_request = kwargs.pop('request')
        #_request_user = _request.user if _request else None

        #logger.debug('AwpBaseModel kwargs: ' + str(kwargs))
        _request = None
        _request_user = None
        if 'request' in kwargs:
            _request = kwargs.pop('request')
            _request_user = _request.user if _request else None
        #logger.debug('AwpBaseModel _request: ' + str(_request))
            # PR2022-08-09 Only save new req_usr and date when request exists.
            # In this way old user names and dates can be copied to new examyear by using save() instead of save(request=request)
            self.modifiedby = _request_user
            self.modifiedat = timezone.now()  # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07

        _is_update = self.pk is not None # self.pk is None before new record is saved
        _mode = ('c', 'u')[_is_update]  # result = (on_false, on_true)[condition]

        # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
        super(AwpBaseModel, self).save(force_insert=not _is_update, force_update=_is_update)

    def delete(self, *args, **kwargs):
        if 'request' in kwargs:
            _request = kwargs.pop('request')

        #save_to_log(self, 'delete', _request)

        super(AwpBaseModel, self).delete(*args, **kwargs)

# - end of AwpBaseModel


class Systemupdate(AwpBaseModel):
    # PR2021-10-12 stores name of the systemupdate once it has run, to prevent running multiple times
    objects = AwpModelManager()

    name = CharField(db_index=True, max_length=c.MAX_LENGTH_NAME)

    def __str__(self):
        return self.name
# - end of Systemupdate


class Country(Model):
    # PR2022-07-29 debug: database has circular reference accounts.user > country.modifiedby and schoolbase.country.modifiedby
    # this gives trouble when restoring database.
    # Therefore remove fields modifiedby (and modifiedat) by using class Model instead of AwpBaseModel

    objects = AwpModelManager()

    name = CharField(max_length=c.MAX_LENGTH_NAME, unique=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, unique=True)

    # Not in use. Block accounts instead PR2021-09-03
    locked = BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
# - end of Country


# PR2018-05-05
class Country_log(AwpBaseModel):
    objects = AwpModelManager()

    country_id = IntegerField(db_index=True)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)

    name_mod = BooleanField(default=False)
    abbrev_mod = BooleanField(default=False)
    locked_mod = BooleanField(default=False)

    locked = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    def __str__(self):
        return self.name

    @property
    def locked_str(self):
        return c.LOCKED_DICT.get(self.locked)

    @property
    def mode_str(self):
        mode_str = '-'
        if self.mode is not None:
            mode_str = c.MODE_DICT.get(str(self.mode))
        return mode_str
# - end of Country_log


# ===  Examyear Model =====================================
class Examyear(AwpBaseModel):  # PR2018-06-06
    objects = AwpModelManager()

    country = ForeignKey(Country, related_name='examyears', on_delete=PROTECT)

    code = PositiveSmallIntegerField()
    published = BooleanField(default=False)
    locked = BooleanField(default=False)

    # also in schemitemsPR2021-04-24
    no_practexam = BooleanField(default=False)
    sr_allowed = BooleanField(default=False)  # herkansing schoolexamen
    # deleted: reex_combi_allowed = BooleanField(default=False)
    no_centralexam = BooleanField(default=False)
    # deleted: no_reex = BooleanField(default=False)
    no_thirdperiod = BooleanField(default=False)
    # deleted: no_exemption_ce = BooleanField(default=False)

    # PR2023-01-21, to skip thumbrule from 2023
    thumbrule_allowed = BooleanField(default=False)

    # PR2023-06-18, requests from Dorothee Inspectorate SXM  to block reex requests
    reex_requests_blocked = BooleanField(default=False)
    reex03_requests_blocked = BooleanField(default=False)

    createdat = DateTimeField(null=True)
    publishedat = DateTimeField(null=True)
    lockedat = DateTimeField(null=True)

# parameters to calculate extra examns and tv2 exams PR2021-08-31
    order_extra_fixed = PositiveSmallIntegerField(default=2)
    order_extra_perc = PositiveSmallIntegerField(default=5)
    order_round_to = PositiveSmallIntegerField(default=5)

    order_tv2_divisor = PositiveSmallIntegerField(default=25)
    order_tv2_multiplier = PositiveSmallIntegerField(default=5)
    order_tv2_max = PositiveSmallIntegerField(default=25)

    order_admin_divisor = PositiveSmallIntegerField(default=25)
    order_admin_multiplier = PositiveSmallIntegerField(default=5)
    order_admin_max = PositiveSmallIntegerField(default=25)

    class Meta:
        ordering = ['-code',]

    def __str__(self):
        return str(self.code)

    @property
    def schoolyear(self):  # PR2018-05-18 calculates schoolyear from this_examyear
        schoolyear = '---'
        if self.code is not None:
            last_year = int(str(self.code)) - 1
            schoolyear = str(last_year) + '-' + str(self.code)
        return schoolyear

# +++++++++++++++++++  get and set setting +++++++++++++++++++++++
    def get_examyearsetting_dict(cls, key_str):
        # PR2023-07-18 function retrieves the string value of the setting row that match the filter and converts it to a dict

        #  json.dumps converts a dict in a json object
        #  json.loads retrieves a dict (or other type) from a json object

        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ---  get_examyearsetting_dict  ------- ')
            logger.debug('cls: ' + str(cls) + ' ' + str(type(cls)))
            logger.debug('key_str: ' + str(key_str) + ' ' + str(type(key_str)))

        setting_dict = {}
        try:
            if cls and key_str:
                row = Examyearsetting.objects.filter(examyear=cls, key=key_str).order_by('-id').first()
                if row and row.setting:
                    setting_dict = json.loads(row.setting)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

        return setting_dict

    def set_examyearsetting_dict(cls, key_str, setting_dict):
        # PR2023-07-18 function saves setting in first row that matches the filter, adds new row when not found

        #  json.dumps converts a dict in a json object
        #  json.loads retrieves a dict (or other type) from a json object

        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ---  set_examyearsetting_dict  ------- ')
            logger.debug('cls: ' + str(cls) + ' ' + str(type(cls)))
            logger.debug('key_str: ' + str(key_str) + ' ' + str(type(key_str)))
            logger.debug('setting_dict: ' + str(setting_dict) + ' ' + str(type(setting_dict)))

        try:
            if cls and key_str:
                setting_str = json.dumps(setting_dict)
                row = Examyearsetting.objects.filter(examyear=cls, key=key_str).order_by('-id').first()
                if row:
                    row.setting = setting_str
                else:
                    # don't add row when setting has no value
                    # note: empty setting_dict {} = False, empty json "{}" = True, therefore check if setting_dict is empty
                    if setting_dict:
                        row = Examyearsetting(examyear=cls, key=key_str, setting=setting_str)
                row.save()

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            logger.error('key_str: ', str(key_str))
            logger.error('setting_dict: ', str(setting_dict))
# - end of Examyear


# PR2018-06-06
class Examyear_log(AwpBaseModel):
    objects = AwpModelManager()

    examyear_id = IntegerField(db_index=True)

    # link on country, not on country_log PR2021-04-24
    country = ForeignKey(Country, related_name='+', on_delete=PROTECT)

    code = PositiveSmallIntegerField(null=True)
    published = BooleanField(null=True)
    locked = BooleanField(null=True)

    no_practexam = BooleanField(null=True)
    sr_allowed = BooleanField(null=True)
    no_centralexam = BooleanField(null=True)
    no_thirdperiod = BooleanField(null=True)

    # PR2023-01-21, to skip thumbrule from 2023
    thumbrule_allowed = BooleanField(null=True)

    # PR2023-06-18, requests from Dorothee Inspectorate SXM  to block reex requests
    reex_requests_blocked = BooleanField(null=True)
    reex03_requests_blocked = BooleanField(null=True)

    createdat = DateTimeField(null=True)
    publishedat = DateTimeField(null=True)
    lockedat = DateTimeField(null=True)

    # parameters to calculate extra examns and tv2 exams PR2021-08-31
    order_extra_fixed = PositiveSmallIntegerField(null=True)
    order_extra_perc = PositiveSmallIntegerField(null=True)
    order_round_to = PositiveSmallIntegerField(null=True)

    order_tv2_divisor = PositiveSmallIntegerField(null=True)
    order_tv2_multiplier = PositiveSmallIntegerField(null=True)
    order_tv2_max = PositiveSmallIntegerField(null=True)

    order_admin_divisor = PositiveSmallIntegerField(null=True)
    order_admin_multiplier = PositiveSmallIntegerField(null=True)
    order_admin_max = PositiveSmallIntegerField(null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)
# - end of Examyear_log


# PR2023-02-19 to store compensation per approved subject
class Examyearsetting(AwpBaseModel):
    objects = AwpModelManager()

    examyear = ForeignKey(Examyear, related_name='+', on_delete=CASCADE)
    key = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)

    setting = CharField(db_index=True, max_length=2048)
    # PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
    # jsonsetting = JSONField(null=True)
# - end of Examyearsetting


# PR2023-02-19
class Examyearsetting_log(AwpBaseModel):
    objects = AwpModelManager()

    examyearsetting_id = IntegerField(db_index=True)

    examyear_log = ForeignKey(Examyear_log, related_name='+', on_delete=CASCADE)

    key = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)

    setting = CharField(db_index=True, max_length=2048)
    # PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
    # jsonsetting = JSONField(null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)
# - end of Examyearsetting_log


class ExfilesText(AwpBaseModel):  # PR2021-01-
    # PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
    objects = AwpModelManager()

    examyear = ForeignKey(Examyear, related_name='+', on_delete=CASCADE)

    key = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)
    subkey = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)
    setting = CharField(max_length=2048, null=True, blank=True)

    # +++++++++++++++++++  get and set setting +++++++++++++++++++++++
    def get_setting_dict(cls, key_str, user):  # PR2019-03-09 PR2021-01-25
        # function returns value of setting row that match the filter
        #logger.debug('---  get_setting_dict  ------- ')
        setting_str = None
        if user and key_str:
            row = cls.objects.filter(user=user, key=key_str).order_by('-id').first()
            if row and row.setting:
                setting_str = row.setting
        return setting_str

    @classmethod
    def set_setting(cls, key_str, setting_str, user):  # PR2019-03-09 PR2021-01-25
        # function saves setting in first row that matches the filter, adds new row when not found

        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('---  set_setting  ------- ')
            logger.debug('key_str: ' + str(key_str))
            logger.debug('setting_str: ' + str(setting_str))
        if user and key_str:
            row = cls.objects.filter(user=user, key=key_str).order_by('-id').first()
            if row:
                row.setting = setting_str
            else:
                # don't add row when setting has no value
                if setting_str:
                    row = cls(user=user, key=key_str, setting=setting_str)
            row.save()
            if logging_on:
                logger.debug('row.setting: ' + str(row.setting))
# - end of ExfilesText


# PR2021-04-25
class ExfilesText_log(AwpBaseModel):
    objects = AwpModelManager()

    exfilestext_id = IntegerField(db_index=True)

    examyear_log = ForeignKey(Examyear_log, related_name='+', on_delete=CASCADE)

    key = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)
    subkey = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)
    setting = CharField(max_length=2048, null=True, blank=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)
# - end of ExfilesText_log


# === Department Model =====================================
# PR2018-09-15 moved from Subjects to School because of circulair refrence when trying to import subjects.Department
class Departmentbase(Model): # PR2018-10-17 PR2021-07-11
    objects = AwpModelManager()

    code = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE)

    def __str__(self):
        return str(self.code)
# - end of Departmentbase

class Department(AwpBaseModel):# PR2018-08-10
    objects = AwpModelManager()

    # base and  examyear cannot be changed
    base = ForeignKey(Departmentbase, related_name='departments', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='examyears', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, # PR2018-08-06 set Unique per Country True. Was: unique=True,
        help_text=_('Required. {} characters or fewer.'.format('50')),)
    abbrev = CharField(max_length=c.MAX_LENGTH_10)
    sequence = PositiveSmallIntegerField(default=1)

    level_req = BooleanField(default=True)
    sector_req = BooleanField(default=True)
    has_profiel = BooleanField(default=False)

    # color is used in envelop module PR2022-08-03
    color = CharField(max_length=c.MAX_LENGTH_10, null=True)

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.abbrev

        # for k, v in vars(self).items():
        #     #logger.debug('class Department(Model) __init__ for k, v in vars(self).items(): k: ' + str(k) + '_v: ' + str(v))
# - end of Department


# PR2018-06-06
class Department_log(AwpBaseModel):
    objects = AwpModelManager()

    department_id = IntegerField(db_index=True)

    base = ForeignKey(Departmentbase, related_name='+', on_delete=PROTECT)
    examyear_log = ForeignKey(Examyear_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_10, null=True)
    sequence = PositiveSmallIntegerField(null=True)
    level_req = BooleanField(default=True)
    sector_req = BooleanField(default=True)
    has_profiel = BooleanField(default=False)

    # color is used in envelop module PR2022-08-03
    color = CharField(max_length=c.MAX_LENGTH_10, null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    def __str__(self):
        return self.name
# - end of Department_log


class Schoolbase(Model):  # PR2018-05-27 PR2018-11-11

    objects = AwpModelManager()

    country = ForeignKey(Country, related_name='+', on_delete=PROTECT)
    code = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE)
    # the role of new users is set to defaultrole of their schoolbase PR2021-01-25
    # defaultroles are: school = 8, comm = 16, insp = 32, admin = 64, system = 128
    defaultrole = PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.code

    @property
    def prefix(self): # PR2020-09-17
        #PR2019-03-13 Prefix is added at front of username, to make usernames unique per schoolbase
        id_str = '000000' + str(self.pk)
        return id_str[-6:]


# +++++++++++++++++++  get and set setting +++++++++++++++++++++++
    def get_schoolsetting_dict(cls, key_str):  # PR2019-03-09 PR2021-01-25
        # function retrieves the string value of the setting row that match the filter and converts it to a dict
        # logger.debug(' ---  get_schoolsetting_dict  ------- ')
        #  json.dumps converts a dict in a json object
        #  json.loads retrieves a dict (or other type) from a json object

        # logger.debug('cls: ' + str(cls) + ' ' + str(type(cls)))
        setting_dict = {}
        row_setting = None
        try:
            if cls and key_str:
                row = Schoolsetting.objects.filter(schoolbase=cls, key=key_str).order_by('-id').first()
                if row:
                    row_setting = row.setting
                    if row_setting:
                        setting_dict = json.loads(row_setting)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            logger.error('key_str: ', str(key_str))
            logger.error('row_setting: ', str(row_setting))

        return setting_dict

    def set_schoolsetting_dict(cls, key_str, setting_dict):  # PR2019-03-09 PR2021-01-25
        # function saves setting in first row that matches the filter, adds new row when not found
        # logger.debug('---  set_setting  ------- ')
        # logger.debug('key_str: ' + str(key_str))
        # logger.debug('setting_dict: ' + str(setting_dict))
        # logger.debug('cls: ' + str(cls) + ' ' + str(type(cls)))
        #  json.dumps converts a dict in a json object
        #  json.loads retrieves a dict (or other type) from a json object

        try:
            if cls and key_str:
                setting_str = json.dumps(setting_dict)
                row = Schoolsetting.objects.filter(schoolbase=cls, key=key_str).order_by('-id').first()
                if row:
                    row.setting = setting_str
                else:
                    # don't add row when setting has no value
                    # note: empty setting_dict {} = False, empty json "{}" = True, therefore check if setting_dict is empty
                    if setting_dict:
                        row = Schoolsetting(schoolbase=cls, key=key_str, setting=setting_str)
                row.save()
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            logger.error('key_str: ', str(key_str))
            logger.error('setting_dict: ', str(setting_dict))
# - end of Schoolbase


# ===  School Model =====================================
class School(AwpBaseModel):  # PR2018-08-20 PR2018-11-11
    objects = AwpModelManager()

    # base and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Schoolbase, related_name='schools', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='schools', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME)
    abbrev = CharField(max_length=c.MAX_LENGTH_SCHOOLABBREV)
    article = CharField(max_length=c.MAX_LENGTH_SCHOOLARTICLE, null=True)
    telephone = CharField(null=True, blank=True, max_length=c.MAX_LENGTH_SCHOOLABBREV)

    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    otherlang = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    # TODO deprecate, not in use any more
    no_order = BooleanField(default=False)

    isdayschool = BooleanField(default=False)
    iseveningschool = BooleanField(default=False)
    islexschool = BooleanField(default=False)

    # TODO deprecate activated and activatedat, not in use any more
    # TODO locked is not in use, but let it stay PR2022-07-31
    # school will be activated when adding student in create_student
    activated = BooleanField(default=False)
    activatedat = DateTimeField(null=True)
    locked = BooleanField(default=False)
    lockedat = DateTimeField(null=True)

    class Meta:
        ordering = ['abbrev',]

    def __str__(self):
        return self.name


#  ++++++++++  Class methods  ++++++++++++++++++++++++

    @classmethod  # PR1019-01-15
    def get_by_user_schoolbase_examyear(cls, request_user):
        school = None
        if request_user:
            # TODO change request.user.examyear to sel_examyear
            if request_user.schoolbase and request_user.examyear:
                school = cls.objects.get_or_none(base=request_user.schoolbase, examyear=request_user.examyear)
        return school
# - end of School


class School_log(AwpBaseModel):
    objects = AwpModelManager()

    school_id = IntegerField(db_index=True)

    base = ForeignKey(Schoolbase, related_name='+', null=True, on_delete=SET_NULL)
    examyear_log = ForeignKey(Examyear_log, related_name='+', on_delete=CASCADE)

    code = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE,null=True)
    name = CharField(max_length=c.MAX_LENGTH_NAME,null=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_SCHOOLABBREV,null=True)
    article = CharField(max_length=c.MAX_LENGTH_SCHOOLARTICLE, null=True)
    telephone = CharField(null=True, blank=True, max_length=c.MAX_LENGTH_SCHOOLABBREV)

    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    otherlang = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    # TODO deprecate, not in use any more
    no_order = BooleanField(default=False)

    isdayschool = BooleanField(default=False)
    iseveningschool = BooleanField(default=False)
    islexschool = BooleanField(default=False)

    # TODO deprecate activated and activatedat, not in use any more
    activated = BooleanField(default=False)
    activatedat = DateTimeField(null=True)

    locked = BooleanField(default=False)
    lockedat = DateTimeField(null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)
# - end of School_log


class Published(AwpBaseModel): # PR2020-12-02
    objects = AwpModelManager()

    school = ForeignKey(School, related_name='+', db_index=True, null=True, on_delete=SET_NULL)
    department = ForeignKey(Department, related_name='+', db_index=True, null=True, on_delete=SET_NULL)

    examtype = CharField(max_length=c.MAX_LENGTH_10, db_index=True, null=True)
    examperiod = PositiveSmallIntegerField(db_index=True) # 1 = period 1, 2 = period 2, 3 = period 3, 4 = exemption, 12 = ce + reex

    name = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)
    filename = CharField(max_length=255, null=True)

    file = FileField(storage=PrivateMediaStorage(), null=True)

    datepublished = DateField()

    def __str__(self):
        return self.name
    # published has no published_log because its data don't change
# - end of Published



class Schoolsetting(Model):  # PR2020-10-20
    # PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
    objects = AwpModelManager()

    schoolbase = ForeignKey(Schoolbase, related_name='schoolsetting', on_delete=CASCADE)
    key = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)

    setting = CharField(db_index=True, max_length=2048)
    # PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
    # jsonsetting = JSONField(null=True)

    @classmethod
    def get_datetimesetting(cls, key_str, schoolbase):  # PR2020-08-23
        datetime_setting = None
        datetime_setting2 = None
        if schoolbase and key_str:
            row = cls.objects.filter(schoolbase=schoolbase, key=key_str).first()
            if row:
                if row.datetimesetting:
                    datetime_setting = row.datetimesetting
                if row.datetimesetting2:
                    datetime_setting2 = row.datetimesetting2

        return datetime_setting, datetime_setting2

    @classmethod
    def set_datetimesetting(cls, key_str, new_datetime, schoolbase):   # PR2020-08-12
        if schoolbase and key_str:
            # don't use get_or_none, gives none when multiple settings exist and will create extra setting.
            row = cls.objects.filter(schoolbase=schoolbase, key=key_str).first()
            if row:
                row.datetimesetting = new_datetime
            elif new_datetime:
                row = cls(schoolbase=schoolbase, key=key_str, datetimesetting=new_datetime)
            row.save()

    @classmethod
    def set_datetimesetting2(cls, key_str, new_datetime, schoolbase):  # PR2020-08-23
        if schoolbase and key_str:
            # don't use get_or_none, gives none when multiple settings exist and will create extra setting.
            row = cls.objects.filter(schoolbase=schoolbase, key=key_str).first()
            if row:
                row.datetimesetting2 = new_datetime
            elif new_datetime:
                row = cls(schoolbase=schoolbase, key=key_str, datetimesetting2=new_datetime)
            row.save()
# - end of Schoolsetting


# +++++++++++++++++++++   Messaging Service  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
class Mailmessage(AwpBaseModel):
    objects = AwpModelManager()

    examyear = ForeignKey(Examyear, related_name='+', on_delete=CASCADE)
    sender_user = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    sender_school = ForeignKey(School, related_name='+', null=True, on_delete=SET_NULL)

    header = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True, blank=True)
    body = CharField(max_length=2048, null=True, blank=True)
    recipients = CharField(max_length=2048, null=True, blank=True)

    # when a mailmessage is sent, sentdate IS NOT NULL
    sentdate = DateTimeField(null=True)
# - end of Mailmessage

# PR2021-03-08 from https://simpleisbetterthancomplex.com/tutorial/2017/08/01/how-to-setup-amazon-s3-in-a-django-project.html
class Mailattachment(AwpBaseModel):
    objects = AwpModelManager()

    mailmessage = ForeignKey(Mailmessage, related_name='+', on_delete=CASCADE)
    contenttype = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)
    file = FileField(storage=PrivateMediaStorage())
    filename = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME)
    filesize = IntegerField(null=True)
# - end of Mailattachment

class Mailbox(AwpBaseModel):
    objects = AwpModelManager()

    user = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=CASCADE)
    mailmessage = ForeignKey(Mailmessage, related_name='+', on_delete=CASCADE)
    read = BooleanField(default=False)
    deleted = BooleanField(default=False)
# - end of Mailbox

class Mailinglist(AwpBaseModel):
    objects = AwpModelManager()

    # base and examyear cannot be changed PR2018-10-17
    schoolbase = ForeignKey(Schoolbase, related_name='+', on_delete=CASCADE)
    # when user is None the mailinglist can be used by all users of this schoolbase
    user = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)

    name = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME)

    recipients = CharField(max_length=2048, null=True, blank=True)
# - end of Mailinglist


def delete_instance(table, instance, request, this_txt=None):
    # PR2019-08-25 PR2020-10-23 PR2021-06-20  PR2022-08-04
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_instance  -----')
        logger.debug('    table: ' + str(table))
        logger.debug('    instance: ' + str(instance))
        logger.debug('    this_txt: ' + str(this_txt))

    # function deletes instance of table,  PR2019-08-25 PR2020-10-23 PR2021-06-20  PR2022-08-04

    # error_list is list of strings, used for error message under input field,
    #  messages is list of dicts with format:
    #   {'field': fldName, header': header_txt, 'retry': True, 'class': 'border_bg_invalid', 'msg_html': msg_html}
    #  retry: not in use yet, lets user retry again
    #  error_list is to be deprecated PR2021-10-24
    # P2022-01-10 I think it is best to use error_list instead of msg_html.
    # error_list doenst have 'header' and 'class', is better when there are multiple errors in err_list

    err_html = None
    deleted_row = None

    caption = this_txt if this_txt else _('This item')

    if instance is None:
        err_html = str(_('%(cpt)s is not found.') % {'cpt': caption})
    else:
# - create deleted_row, to be sent back to page
        deleted_row = {'id': instance.pk,
                       'mapid': '_'.join((table, str(instance.pk))),
                       'deleted': True}

        try:
            if logging_on:
                 logger.debug('    this instance will be deleted:: ' + str(instance) + ' ' + str(type(instance)))

            #PR2022-08-06 debug: error when deleting subjecttypebase: Model.delete() got an unexpected keyword argument 'request'
            if 'base' in table:
                instance.delete()
            else:
                instance.delete(request=request)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            err_html = ''.join((
                str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                str(_('%(cpt)s could not be deleted.') % {'cpt': caption})
            ))
            deleted_row = None
            # msg_dict = {'header': header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html}

            """
            new approach PR2022-08-04:
            if this_text is None:
                this_text = str(_('This item'))
            # &emsp; add 4 'hard' spaces
            err_html = ''.join((
                str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                str(_('%(cpt)s could not be deleted.') % {'cpt': this_text})
            ))
            return err_html
            ...
            deleted_row, err_html = delete_customer_instance (customer_instance, request)
            if msg_html:
                error_dict['nonfield'] = err_html
            
            if error_dict:
                updated_row['error'] = error_dict
            .....    
            if updated_rows and updated_rows[0]:
                updated_row = updated_rows[0]
                if is_created:
                # - add 'created' to updated_row, to show OK when new row is added to table
                    updated_row['created'] = True
                if error_dict:
                    updated_row['error'] = error_dict
            """

    if logging_on:
        logger.debug('    deleted_row: ' + str(deleted_row))
        logger.debug('    err_html: ' + str(err_html))

    return deleted_row, err_html
# - end of delete_instance

"""
# PR2024-03-02 not in use:
# PR2018-06-07
class Entrylist(AwpBaseModel):
    school = ForeignKey(School, related_name='+', on_delete=CASCADE)
    key_id = IntegerField(db_index=True, default=0)
    char01 = CharField(max_length=255, null=True)
    char02 = CharField(max_length=255, null=True)
    int01 = IntegerField(null=True)
    int02 = IntegerField(null=True)
    bool01 = BooleanField(default=False)
    bool02 = BooleanField(default=False)
    date01 = DateTimeField(null=True)
    date02 = DateTimeField(null=True)

    # field to be excluded from AwpBaseModel
    modifiedby = None
    modifiedat = None
# - end of Entrylist


"""

