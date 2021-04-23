# PR2018-04-13
from django.contrib.auth import get_user_model

# PR2020-12-13 Deprecation warning: django.contrib.postgres.fields import JSONField  will be removed from Django 4
# instead use: django.db.models import JSONField (is added in Django 3)
# PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
from django.contrib.postgres.fields import ArrayField #, JSONField

from django.db import connection
from django.db.models import Model, Manager, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField, DateField, FileField
from django.utils import timezone

import json

# PR2018-05-05 use AUTH_USER_MODEL
from awpr.settings import AUTH_USER_MODEL
from django.utils.translation import ugettext_lazy as _
from awpr import constants as c
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
# AwpModelManager adds function get_or_none. Used in  Subjectbase to prevent DoesNotExist exception
class AwpModelManager(Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except:
            return None


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

        _is_update = self.pk is not None # self.pk is None before new record is saved
        _mode = ('c', 'u')[_is_update]  # result = (on_false, on_true)[condition]

        self.modifiedby = _request_user
        self.modifiedat = timezone.now()  # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07

        # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
        super(AwpBaseModel, self).save(force_insert=not _is_update, force_update=_is_update)

        save_to_log(self, _mode, _request)


    def delete(self, *args, **kwargs):
        _request = kwargs.pop('request')
        save_to_log(self, 'delete', _request)

        super(AwpBaseModel, self).delete(*args, **kwargs)


class Country(AwpBaseModel):
    # PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
    objects = AwpModelManager()

    name = CharField(max_length=c.MAX_LENGTH_NAME, unique=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, unique=True)

    locked = BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property # PR2018-06-22
    def has_no_child_rows(self):
        User = get_user_model()
        linked_users_count = User.objects.filter(country_id=self.pk).count()
        #logger.debug('Country(Model has_linked_data linked_users_count: ' + str(linked_users_count))
        # TODO add other dependencies: Subject, Schoolcode etc
        return not bool(linked_users_count)


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


# ===  Examyear Model =====================================
class Examyear(AwpBaseModel):  # PR2018-06-06
    objects = AwpModelManager()

    country = ForeignKey(Country, related_name='examyears', on_delete=PROTECT)

    code = PositiveSmallIntegerField()
    published = BooleanField(default=False)
    locked = BooleanField(default=False)

    no_practexam = BooleanField(default=False)
    no_centralexam = BooleanField(default=False)
    combi_reex_allowed = BooleanField(default=False)
    no_exemption_ce = BooleanField(default=False)
    no_thirdperiod = BooleanField(default=False)

    createdat = DateTimeField(null=True)
    publishedat = DateTimeField(null=True)
    lockedat = DateTimeField(null=True)

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


# PR2018-06-06
class Examyear_log(AwpBaseModel):
    objects = AwpModelManager()

    examyear_id = IntegerField(db_index=True)

    country_log = ForeignKey(Country_log, related_name='+', on_delete=PROTECT)

    code = PositiveSmallIntegerField(null=True)
    published = BooleanField(default=False)
    locked = BooleanField(default=False)

    no_practexam = BooleanField(default=False)
    no_centralexam = BooleanField(default=False)
    combi_reex_allowed = BooleanField(default=False)
    no_exemption_ce = BooleanField(default=False)
    no_thirdperiod = BooleanField(default=False)

    createdat = DateTimeField(null=True)
    publishedat = DateTimeField(null=True)
    lockedat = DateTimeField(null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


class ExfilesText(Model):  # PR2021-01-
    # PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
    objects = AwpModelManager()

    examyear = ForeignKey(Examyear, related_name='+', on_delete=CASCADE)

    key = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)
    subkey = CharField(db_index=True, max_length=c.MAX_LENGTH_KEY)
    setting = CharField(max_length=2048, null=True, blank=True)

    # +++++++++++++++++++  get and set setting +++++++++++++++++++++++
    def get_setting_dict(cls, key_str, user):  # PR2019-03-09 PR2021-01-25
        # function returns value of setting row that match the filter
        # logger.debug('---  get_setting_dict  ------- ')
        setting_str = None
        if user and key_str:
            row = cls.objects.filter(user=user, key=key_str).order_by('-id').first()
            if row and row.setting:
                setting_str = row.setting
        return setting_str

    @classmethod
    def set_setting(cls, key_str, setting_str, user):  # PR2019-03-09 PR2021-01-25
        # function saves setting in first row that matches the filter, adds new row when not found
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
            logger.debug('row.setting: ' + str(row.setting))


# === Department Model =====================================
# PR2018-09-15 moved from Subjects to School because of circulair refrence when trying to import subjects.Department
class Departmentbase(Model):# PR2018-10-17
    objects = AwpModelManager()

    country = ForeignKey(Country, related_name='+', on_delete=PROTECT)
    code = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE)

    def __str__(self):
        return str(self.code)


class Department(AwpBaseModel):# PR2018-08-10
    objects = AwpModelManager()

    # base and  examyear cannot be changed
    base = ForeignKey(Departmentbase, related_name='departments', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='examyears', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, # PR2018-08-06 set Unique per Country True. Was: unique=True,
        help_text=_('Required. {} characters or fewer.'.format('50')),)
    abbrev = CharField(max_length=c.MAX_LENGTH_10)
    sequence = PositiveSmallIntegerField(db_index=True, default=1)
    level_req = BooleanField(default=True)
    sector_req = BooleanField(default=True)
    has_profiel = BooleanField(default=False)
    #level_caption = CharField(max_length=c.MAX_LENGTH_20, null=True, blank=True)  # PR2019-01-17
    #sector_caption = CharField(max_length=c.MAX_LENGTH_20, null=True, blank=True)  # PR2019-01-17

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.abbrev

        # for k, v in vars(self).items():
        #     #logger.debug('class Department(Model) __init__ for k, v in vars(self).items(): k: ' + str(k) + '_v: ' + str(v))


# PR2018-06-06
class Department_log(AwpBaseModel):
    objects = AwpModelManager()

    department_id = IntegerField(db_index=True)

    base = ForeignKey(Departmentbase, related_name='+', on_delete=PROTECT)

    examyear_log = ForeignKey(Examyear_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_04, null=True)
    sequence = PositiveSmallIntegerField()
    level_req = BooleanField(default=True)
    sector_req = BooleanField(default=True)
    has_profiel = BooleanField(default=False)
    #level_caption = CharField(max_length=c.MAX_LENGTH_20, null=True)
    #sector_caption = CharField(max_length=c.MAX_LENGTH_20, null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    def __str__(self):
        return self.name


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
                    # note: empty setting_dict {} = False, empty json "{}" = True, teherfore check if setting_dict is empty
                    if setting_dict:
                        row = Schoolsetting(schoolbase=cls, key=key_str, setting=setting_str)
                row.save()
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            logger.error('key_str: ', str(key_str))
            logger.error('setting_dict: ', str(setting_dict))


# ===  School Model =====================================
class School(AwpBaseModel):  # PR2018-08-20 PR2018-11-11
    objects = AwpModelManager()

    # base and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Schoolbase, related_name='schools', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='schools', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME)
    abbrev = CharField(max_length=c.MAX_LENGTH_SCHOOLABBREV)
    article = CharField(max_length=c.MAX_LENGTH_SCHOOLARTICLE, null=True)

    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    isdayschool = BooleanField(default=False)
    iseveningschool = BooleanField(default=False)
    islexschool = BooleanField(default=False)

    activated = BooleanField(default=False)
    locked = BooleanField(default=False)
    activatedat = DateTimeField(null=True)
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
            if request_user.schoolbase and request_user.examyear:
                school = cls.objects.get_or_none(base=request_user.schoolbase, examyear=request_user.examyear)
        return school


class School_log(AwpBaseModel):
    objects = AwpModelManager()

    school_id = IntegerField(db_index=True)
    base = ForeignKey(Schoolbase, related_name='+', null=True, on_delete=SET_NULL)
    examyear_log = ForeignKey(Examyear_log, related_name='+', on_delete=CASCADE)

    code = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE,null=True)
    name = CharField(max_length=c.MAX_LENGTH_NAME,null=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_SCHOOLABBREV,null=True)
    article = CharField(max_length=c.MAX_LENGTH_SCHOOLARTICLE, null=True)
    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    isdayschool = BooleanField(default=False)
    iseveningschool = BooleanField(default=False)
    islexschool = BooleanField(default=False)

    activated = BooleanField(default=False)
    locked = BooleanField(default=False)
    activatedat = DateTimeField(null=True)
    lockedat = DateTimeField(null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# PR2018-106-17
class School_message(AwpBaseModel):
    objects = AwpModelManager()

    school = ForeignKey(School, related_name='+', on_delete=CASCADE)
    sent_to = CharField(max_length=2048, null=True, blank=True)
    title = CharField(max_length=80, null=True, blank=True)
    note = CharField(max_length=4096, null=True, blank=True)
    is_insp = BooleanField(default=False)
    is_unread = BooleanField(default=False)


# PR2018-106-17
class School_message_log(AwpBaseModel):
    objects = AwpModelManager()

    school_message_id = IntegerField(db_index=True)
    sent_to = CharField(max_length=2048, null=True, blank=True)
    title = CharField(max_length=80, null=True, blank=True)
    note = CharField(max_length=4096, null=True, blank=True)
    is_insp = BooleanField(default=False)
    is_unread = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


class Published(AwpBaseModel): # PR2020-12-02
    objects = AwpModelManager()

    school = ForeignKey(School, related_name='+', on_delete=CASCADE)
    department = ForeignKey(Department, related_name='+', on_delete=CASCADE)

    examtype = CharField(max_length=c.MAX_LENGTH_10, db_index=True)
    examperiod = PositiveSmallIntegerField(db_index=True) # 1 = period 1, 2 = period 2, 3 = period 3, 4 = exemption

    name = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)

    filename = CharField(max_length=255, null=True)

    datepublished = DateField()

    def __str__(self):
        return self.name
    # published has no published_log because its data don't change

# PR2021-03-08 from https://simpleisbetterthancomplex.com/tutorial/2017/08/01/how-to-setup-amazon-s3-in-a-django-project.html
# PR2021-03-13 test
class PrivateDocument(AwpBaseModel):
    objects = AwpModelManager()

    school = ForeignKey(School, related_name='+', on_delete=CASCADE)
    department = ForeignKey(Department, related_name='+', on_delete=CASCADE)

    examtype = CharField(max_length=c.MAX_LENGTH_10, db_index=True)
    examperiod = PositiveSmallIntegerField(db_index=True) # 1 = period 1, 2 = period 2, 3 = period 3, 4 = exemption

    name = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)

    document = FileField(storage=PrivateMediaStorage())

    datepublished = DateField()



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
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# +++++++++++++++++++++   Functions Schooldefault  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def get_depbase_list_tuple(depbase_list):
    # PR2018-08-28 depbase_list_tuple converts self.depbase_list string into tuple,
    # e.g.: depbase_list='1;2' will be converted to depbase_list=(1,2)
    # empty list = (0,), e.g: 'None'

    depbase_list_tuple = ()
    if depbase_list:
        depbase_list_str = str(depbase_list)
        # This function converts init_list_str string into init_list_tuple,  e.g.: '1;2' will be converted to (1,2)
        depbase_list_list = depbase_list_str.split(';')
        depbase_list_tuple = tuple(depbase_list_list)

    # select 0 (None) in EditForm when no other departments are selected
    if not depbase_list_tuple:
        depbase_list_tuple = (0,)

    return depbase_list_tuple


def dep_initials(dep_name):
    # PR2018-12-13 calculates 'V.S.B.O.' from full name
    initials = ''
    if dep_name:
        array = dep_name.split()
        for item in array:
            initials = item[1].upper() + '.'
    return initials


def delete_instance(instance, msg_dict, request, this_text=None):
    #logger.debug(' ----- delete_instance  -----')
    #logger.debug('instance: ' + str(instance))

    # function deletes instance of table,  PR2019-08-25 PR2020-10-23
    deleted_ok = False

    if instance:
        try:
            instance.delete(request=request)
        except:
            err_text = _('An error occurred.')
            tbl = this_text if this_text else _('This item')
            msg_dict['err_delete'] = str(err_text + ' ' + _('%(tbl)s could not be deleted.') % {'tbl': tbl})
        else:
            deleted_ok = True

    return deleted_ok


def save_to_log(instance, req_mode, request):
    #logger.debug(' ----- save_to_log  ----- mode: ' + str(req_mode) )  # PR2019-02-23 PR2020-10-23 PR2020-12-15

    if instance:
        model_name = str(instance.get_model_name())
        #logger.debug('model_name: ' + str(model_name))
        mode = req_mode[0:1] if req_mode else '-'

        modby_id = 'NULL'
        mod_at = 'NULL'
        if mode == 'd':
            # when log delete: add req_user and now
            if request and request.user:
                modby_id = str(request.user.pk)
            mod_at = timezone.now().isoformat()
        else:
            # when log save: add user and moodat of saved record
            if instance.modifiedby_id:
                modby_id = str(instance.modifiedby_id)
            if instance.modifiedat:
                mod_at = instance.modifiedat.isoformat()
        pk_int = instance.pk
        #logger.debug('model_name: ' + str(model_name))
        #logger.debug('mode: <' + str(mode) + '>')
        #logger.debug('modby_id: ' + str(modby_id))
        #logger.debug('mod_at: ' + str(mod_at))
        #logger.debug('model_name == Examyear')

        if model_name == 'Studentsubject':
            pass
        elif model_name == 'Grade':
            # this one not working, cannot get filter pc.id with LIMIT 1 in query, get info from pricecodelist instead
            sub_ssl_list = ["SELECT id, studentsubject_id AS studsubj_id,",
                            "FROM studentsubject_log",
                            "ORDER BY id DESC NULLS LAST LIMIT 1"]
            sub_ssl = ' '.join(sub_ssl_list)
            # note: multiple WITH clause syntax:WITH cte1 AS (SELECT...), cte2 AS (SELECT...) SELECT * FROM ...
            sql_keys = {'grade_id': pk_int,  'mode': mode, 'modby_id': modby_id, 'mod_at': mod_at}
            sql_list = ["WITH sub_ssl AS (" + sub_ssl + ")",
                        "INSERT INTO students_grade_log (id,",
                            "grade_id, studentsubject_log_id, examperiod,",
                            "pescore, cescore, segrade, pegrade, cegrade, pecegrade, finalgrade,",
                            "sepublished, pepublished, cepublished,",
                            "mode, modifiedby_id, modifiedat)",
                        "SELECT nextval('students_grade_log_id_seq'),",
                            "grade_id, sub_ssl.id, examperiod,",
                            "pescore, cescore, segrade, pegrade, cegrade, pecegrade, finalgrade,",
                            "sepublished, pepublished, cepublished,",
                            "%(mode)s::TEXT, %(modby_id)s::INT, %(mod_at)s::DATE",
                        "FROM students_grade AS grade",
                        "INNER JOIN sub_ssl ON (sub_ssl.studsubj_id = grade.studentsubject_id)",
                        "WHERE (grade.id = %(grade_id)s::INT"]

            sql_list = ["SELECT nextval('students_grade_log_id_seq') AS sgl_id,",
                            "grade.id, grade.examperiod,",
                            "%(mode)s::TEXT AS mode, %(modby_id)s::INT AS modby_id, %(mod_at)s::DATE AS mod_at",
                        "FROM students_grade AS grade",
                        "WHERE id = %(grade_id)s::INT"]
            sql = ' '.join(sql_list)
            #logger.debug('sql_keys: ' + str(sql_keys))
            #logger.debug('sql: ' + str(sql))

            #logger.debug('---------------------- ')
            with connection.cursor() as cursor:
                #logger.debug('================= ')
                cursor.execute(sql, sql_keys)
                #for qr in connection.queries:
                    #logger.debug('-----------------------------------------------------------------------------')
                    #logger.debug(str(qr))

                #logger.debug('---------------------- ')
                #rows = dictfetchall(cursor)
                #logger.debug('---------------------- ')
                #for row in rows:
                    #logger.debug('row: ' + str(row))


        if model_name == 'Examyear':

            """
            INSERT INTO schools_school (examyear_id, schoolbase_id, name, code, abbrev, article, dep_list, locked, modifiedby_id, modifiedat) ' + \
                    'SELECT %s AS examyear_id, sb.id, sb.name, sb.code, sb.abbrev, sb.article, sb.dep_list, False AS locked, %s AS modifiedby_id, %s AS modifiedat  ' + \
                    'FROM schools_school AS sb WHERE sb.examyear_id = %s;',
                    [self.new_examyear_id, self.modifiedby_id, self.modifiedat, self.prev_examyear_id])
                connection.commit()
            """


            # PR2019-02-24 This works, but is rather complicated
            insert_other_fields = 'examyear, published, locked, modifiedby_id, createdat, publishedat, lockedat,'

            insert_from_table = 'schools_examyear'
            insert_into = 'mode, examyear_id, country_log_id, examyear, published, locked, modifiedby_id, createdat, publishedat, lockedat,'
            insert_from = '%(mode)s::TEXT, id, ' \
                          '(SELECT id FROM schools_country_log WHERE country_id=exy.country_id ORDER BY id DESC LIMIT 1),'

            if mode == 'd':
                # when delete: enter req_user and now in modified_by / modifiedat
                select_modified = "%(mod_by_id)s::INT, %(mod_at)s::TIMESTAMPTZ"

            else:
                # in other modes: copy modifiedby_id, modifiedat from instance
                select_modified = "modifiedby_id, modifiedat"
            #                     "SELECT (nextval('" + insert_from_table + "_log_id_seq'), id) FROM",
            sql_list = ['INSERT INTO schools_examyear_log',
                        '(examyear_id, country_log_id, examyear, published, locked, createdat, publishedat, lockedat, mode, modifiedby_id, modifiedat)',
                        "SELECT id, ",
                        "(SELECT id FROM schools_country_log WHERE country_id=schools_examyear.country_id ORDER BY id DESC LIMIT 1)"
                        ", examyear, published, locked, createdat, publishedat, lockedat, %(mode)s::TEXT,",
                        select_modified,
                        "FROM schools_examyear",
                        'WHERE id=%(instance_pk)s::INT',
                        'RETURNING id, examyear'
                        ]
            sql = ' '.join(sql_list)

            #logger.debug('sql: ' + str(sql))
            sql_keys = {
                'mode': mode,
                'mod_by_id': modby_id,
                'mod_at': mod_at,
                'instance_pk': instance.pk}
            #logger.debug('sql_keys: ' + str(sql_keys))

            newcursor = connection.cursor()
            newcursor.execute(sql, sql_keys)
            #rows = dictfetchall(newcursor)
            #for row in rows:
                #logger.debug('row: ' + str(row))



#######################################

def get_country(country_abbrev):
    # get existing country PR2020-12-14
    # don't use get_or_none, it will return None when there are multiple countries with the same name
    # get the latest one instead (with highest pk)
    country = None
    if country_abbrev:
        country = Country.objects.filter(
            abbrev__iexact=country_abbrev
        ).order_by('-pk').first()
    return country


