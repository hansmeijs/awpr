#PR2018-04-13
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField, JSONField

from django.db import connection
from django.db.models import Model, Manager, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField
from django.utils import timezone

from datetime import datetime, timedelta

# PR2018-05-05 use AUTH_USER_MODEL
from awpr.settings import AUTH_USER_MODEL
from django.utils.translation import ugettext_lazy as _
from awpr import constants as c

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
    modifiedat = DateTimeField(default=datetime.now)

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

        logger.debug('AwpBaseModel kwargs: ' + str(kwargs))
        _request = None
        _request_user = None
        if 'request' in kwargs:
            _request = kwargs.pop('request')
            _request_user = _request.user if _request else None
        logger.debug('AwpBaseModel _request: ' + str(_request))

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

    name = CharField(max_length=50, unique=True)
    abbrev = CharField(max_length=6, unique=True)

    locked = BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property # PR2018-06-22
    def has_no_child_rows(self):
        User = get_user_model()
        linked_users_count = User.objects.filter(country_id=self.pk).count()
        # logger.debug('Country(Model has_linked_data linked_users_count: ' + str(linked_users_count))
        # TODO add other dependencies: Subject, Schoolcode etc
        return not bool(linked_users_count)

# PR2018-05-05
class Country_log(AwpBaseModel):
    objects = AwpModelManager()

    country_id = IntegerField(db_index=True)

    name = CharField(max_length=50, null=True)
    abbrev = CharField(max_length=6, null=True)

    name_mod = BooleanField(default=False)
    abbrev_mod = BooleanField(default=False)
    locked_mod = BooleanField(default=False)

    locked = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)


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

    examyear = PositiveSmallIntegerField()
    published = BooleanField(default=False)
    locked = BooleanField(default=False)

    createdat = DateTimeField(null=True)
    publishedat = DateTimeField(null=True)
    lockedat = DateTimeField(null=True)

    class Meta:
        ordering = ['-examyear',]

    def __str__(self):
        return str(self.examyear)

    @property
    def schoolyear(self):  # PR2018-05-18 calculates schoolyear from this_examyear
        schoolyear = '---'
        if self.examyear is not None:
            last_year = int(str(self.examyear)) - 1
            schoolyear = str(last_year) + '-' + str(self.examyear)
        return schoolyear


# PR2018-06-06
class Examyear_log(AwpBaseModel):
    objects = AwpModelManager()

    examyear_id = IntegerField(db_index=True)

    country_log = ForeignKey(Country_log, related_name='+', on_delete=PROTECT)

    examyear = PositiveSmallIntegerField(null=True)
    published = BooleanField(default=False)
    locked = BooleanField(default=False)

    createdat = DateTimeField(null=True)
    publishedat = DateTimeField(null=True)
    lockedat = DateTimeField(null=True)

    mode = CharField(max_length=1, null=True)


# === Department Model =====================================
# PR2018-09-15 moved from Subjects to School because of circulair refrence when trying to import subjects.Department
class Departmentbase(Model):# PR2018-10-17
    objects = AwpModelManager()

    country = ForeignKey(Country, related_name='+', on_delete=PROTECT)


class Department(AwpBaseModel):# PR2018-08-10
    objects = AwpModelManager()

    # base and  examyear cannot be changed
    base = ForeignKey(Departmentbase, related_name='departments', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='examyears', on_delete=CASCADE)

    name = CharField(max_length=50, # PR2018-08-06 set Unique per Country True. Was: unique=True,
        help_text=_('Required. {} characters or fewer.'.format('50')),)
    abbrev = CharField(max_length=4, # PR2018-08-06 set Unique per Country True. Was: unique=True,
        help_text=_('Required. {} characters or fewer.'.format('4')),)
    sequence = PositiveSmallIntegerField(db_index=True, default=1)
    level_req = BooleanField(default=True)
    sector_req = BooleanField(default=True)
    level_caption = CharField(max_length=20, null=True, blank=True)  # PR2019-01-17
    sector_caption = CharField(max_length=20, null=True, blank=True)  # PR2019-01-17

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.abbrev

        # for k, v in vars(self).items():
        #     logger.debug('class Department(Model) __init__ for k, v in vars(self).items(): k: ' + str(k) + '_v: ' + str(v))

#  ++++++++++  Class methods  ++++++++++++++++++++++++

    @classmethod
    def get_dep_attr(cls, request_user):  # PR2018-10-25
        # function creates dict of attributes of deps in selected schoolyear
        # It is used to add option attributes to form field select Department
        # src = {'0': {'abbrev': '', 'level_req': 'false', 'sector_req': 'false'},
        #            '4': {'abbrev': 'Vsbo', 'level_req': 'true', 'sector_req': 'true'},
        #            '5': {'abbrev': 'Havo', 'level_req': 'falxse', 'sector_req': 'true'},
        #            '6': {'abbrev': 'Vwo', 'level_req': 'false', 'sector_req': 'true'},
        #      }
        attr = {}
        if request_user is not None:
            if request_user.country is not None and request_user.examyear is not None:
                if request_user.examyear.country.pk == request_user.country.pk:
                    # filter departments of request_user.examyear
                    for item in Department.objects.filter(examyear=request_user.examyear):
                        _id_str = str(item.id)
                        _abbrev = item.abbrev
                        _level_req_str = 'true' if item.level_req else 'false'
                        _sector_req_str = 'true' if item.sector_req else 'false'

                        attr[_id_str] = {
                            'abbrev': _abbrev,
                            'level_req':_level_req_str,
                            'sector_req':_sector_req_str
                        }
        # logger.debug('attr: ' + str(attr))
        return attr

    @classmethod
    def get_select_list(cls, request_user):  # PR2019-01-14
    # function creates list of departments of this examyear
    # when role = school: filter dep_list of school
    # used in table select_dep in schemeitemlist
    # select_list: {id: 32, name: "Cultuur en Maatschappij", abbrev: "c&m", depbase_list: ""}
        select_list = []
        if request_user is not None:
            if request_user.examyear is not None:
        # if role = school: filter by school.deplist: ";11;12;13;"
                depbase_list = ''
        # TODO: remove 'or request_user.is_role_insp_or_syst', this is just for testing
                if request_user.is_role_school or request_user.is_role_insp_or_admin_or_system:
                    school = School.get_by_user_schoolbase_examyear(request_user)
                    if school:
                        depbase_list = school.depbase_list
                deps = cls.objects.filter(examyear=request_user.examyear)
                for dep in deps:
                    skip_add = False
         # allways add dep when depbase_list of school is empty
                    if depbase_list:
                        skip_add = not (';' + str(dep.base.id) + ';') in depbase_list
                    if not skip_add:
                        level_caption = '-'
                        sector_caption = '-'
                        if dep.level_caption:
                            level_caption = dep.level_caption
                        if dep.sector_caption:
                            sector_caption = dep.sector_caption
                        select_list.append( {
                            "id": dep.id,
                            "name": dep.name,
                            "abbrev": dep.abbrev,
                            "level_req": dep.level_req,
                            "sector_req": dep.sector_req,
                            "level_caption": level_caption,
                            "sector_caption": sector_caption,
                        })
        return select_list


    @classmethod
    def get_dep_by_abbrev(cls, abbrev, examyear):  # PR2019-02-26
        # function gets Department with this abbrev and examyear, returns None if multiple found
        dep = None
        if examyear and abbrev:
            if cls.objects.filter(examyear=examyear,abbrev__iexact=abbrev).count() == 1:
                dep = cls.objects.filter(examyear=examyear,abbrev__iexact=abbrev).first()
        return dep


# PR2018-06-06
class Department_log(AwpBaseModel):
    objects = AwpModelManager()

    department_id = IntegerField(db_index=True)

    base = ForeignKey(Departmentbase, related_name='+', on_delete=PROTECT)

    examyear_log = ForeignKey(Examyear_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=50, null=True)
    abbrev = CharField(max_length=4, null=True)
    sequence = PositiveSmallIntegerField()
    level_req = BooleanField(default=True)
    sector_req = BooleanField(default=True)
    level_caption = CharField(max_length=20, null=True)
    sector_caption = CharField(max_length=20, null=True)

    name_mod = BooleanField(default=False)
    abbrev_mod = BooleanField(default=False)
    sequence_mod = BooleanField(default=False)
    level_req_mod = BooleanField(default=False)
    sector_req_mod = BooleanField(default=False)
    level_caption_mod = BooleanField(default=False)
    sector_caption_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)

    def __str__(self):
        return self.name

    @property
    def level_req_str(self):
        return c.YES_NO_BOOL_DICT.get(self.level_req)

    @property
    def sector_req_str(self):
        return c.YES_NO_BOOL_DICT.get(self.sector_req)

    @property
    def mode_str(self):
        mode_str = '-'
        if self.mode is not None:
            mode_str = c.MODE_DICT.get(str(self.mode),'-')
        return mode_str


class Schoolbase(Model):  # PR2018-05-27 PR2018-11-11
    objects = AwpModelManager()

    country = ForeignKey(Country, related_name='+', on_delete=PROTECT)
    code = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE)

    @property
    def prefix(self): # PR2020-09-17
        #PR2019-03-13 Prefix is added at front of username, to make usernames unique per schoolbase
        id_str = '000000' + str(self.pk)
        return id_str[-6:]


# ===  School Model =====================================
class School(AwpBaseModel):  # PR2018-08-20 PR2018-11-11
    objects = AwpModelManager()

    # base and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Schoolbase, related_name='schools', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='schools', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME)
    abbrev = CharField(max_length=c.MAX_LENGTH_SCHOOLABBREV)

    article = CharField(max_length=c.MAX_LENGTH_SCHOOLARTICLE, null=True)
    depbases = ArrayField(IntegerField(), null=True)

    isdayschool = BooleanField(default=False)
    iseveningschool = BooleanField(default=False)
    islexschool = BooleanField(default=False)

    activated = BooleanField(default=False)
    locked = BooleanField(default=False)
    activatedat = DateTimeField(null=True)
    lockedat = DateTimeField(null=True)

    # is_template stores the examyear.id. In that way there can only be one template per examyear / country
    istemplate = IntegerField(unique=True, null=True)

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
    depbases = ArrayField(IntegerField(), null=True)

    isdayschool = BooleanField(default=False)
    iseveningschool = BooleanField(default=False)
    islexschool = BooleanField(default=False)

    activated = BooleanField(default=False)
    locked = BooleanField(default=False)
    activatedat = DateTimeField(null=True)
    lockedat = DateTimeField(null=True)

    #is_template = BooleanField(null=True)  # default School of this country and examyear PR2018-08-23

    # is_template stores the examyear.id. In that way there can only be one template per examyear / country
    istemplate = IntegerField(unique=True, null=True)

    mode = CharField(max_length=1, null=True)


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
    sent_to =  CharField(max_length=2048, null=True, blank=True)
    title =  CharField(max_length=80, null=True, blank=True)
    note =  CharField(max_length=4096, null=True, blank=True)
    is_insp = BooleanField(default=False)
    is_unread = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)


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
    key = CharField(db_index=True, max_length=c.MAX_LENGTH_CODE)

    jsonsetting = JSONField(null=True)  # stores invoice dates for this customer
    datetimesetting = DateTimeField(null=True)  #  for last_emplhour_updated PR2020-08-10
    datetimesetting2 = DateTimeField(null=True)  #  for last_emplhour_deleted PR2020-08-23

#===========  Classmethods
    @classmethod
    def get_jsonsetting(cls, key_str, schoolbase, default_setting=None):  # PR2019-03-09 PR2020-10-20
        setting = None
        if schoolbase and key_str:
            row = cls.objects.get_or_none(schoolbase=schoolbase, key=key_str)
            if row:
                if row.jsonsetting:
                    setting = row.jsonsetting
        if setting is None:
            if default_setting:
                setting = default_setting
        return setting

    @classmethod
    def set_jsonsetting(cls, key_str, jsonsetting, schoolbase): #PR2019-03-09
        #logger.debug('---  set_jsonsettingg  ------- ')
        #logger.debug('key_str: ' + str(key_str) + ' jsonsetting: ' + str(jsonsetting))

        if schoolbase and key_str:
            # don't use get_or_none, gives none when multiple settings exists and will create extra setting.
            row = cls.objects.filter(schoolbase=schoolbase, key=key_str).first()
            if row:
                row.jsonsetting = jsonsetting
            else:
                if jsonsetting:
                    row = cls(schoolbase=schoolbase, key=key_str, jsonsetting=jsonsetting)
            row.save()
            # test
            row = None
            saved_row = cls.objects.filter(schoolbase=schoolbase, key=key_str).first()
            #logger.debug('saved_row.jsonsetting: ' + str(saved_row.jsonsetting))

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
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


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


def save_to_log(instance, req_mode=None, modifiedby_id=None):
    logger.debug(' ----- save_to_log  -----')  # PR2019-02-23 PR2020-10-23

    if instance:
        model_name = str(instance.get_model_name())

        if req_mode is None:
            mode = '-'
        else:
            mode = req_mode[0:1]

        modby_id = 'NULL'
        mod_at = 'NULL'
        if mode == 'd':
            if modifiedby_id:
                modby_id = str(modifiedby_id)
            mod_at = timezone.now().isoformat()
        else:
            if instance.modifiedby_id:
                modby_id = str(instance.modifiedby_id)
            if instance.modifiedat:
                mod_at = instance.modifiedat.isoformat()

        logger.debug('model_name: ' + str(model_name))
        logger.debug('mode: <' + str(mode) + '>')
        logger.debug('modby_id: ' + str(modby_id))
        logger.debug('mod_at: ' + str(mod_at))
        logger.debug('model_name == Examyear')

        is_exyr = model_name == 'Examyear'
        logger.debug('is_exyr: ' + str(is_exyr))
        if is_exyr:

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

            logger.debug('sql: ' + str(sql))
            sql_keys = {
                'mode': mode,
                'mod_by_id': modby_id,
                'mod_at': mod_at,
                'instance_pk': instance.pk}
            logger.debug('sql_keys: ' + str(sql_keys))

            newcursor = connection.cursor()
            newcursor.execute(sql, sql_keys)
            rows = dictfetchall(newcursor)
            for row in rows:
                logger.debug('row: ' + str(row))



#######################################


def dictfetchall(cursor):
    # PR2019-10-25 from https://docs.djangoproject.com/en/2.1/topics/db/sql/#executing-custom-sql-directly
    # creates dict from output cusror.execute instead of list
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def dictfetchone(cursor):
    # Return one row from a cursor as a dict  PR2020-06-28
    return_dict = {}
    try:
        columns = [col[0] for col in cursor.description]
        return_dict = dict(zip(columns, cursor.fetchone()))
    except:
        pass
    return return_dict