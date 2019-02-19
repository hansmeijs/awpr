#PR2018-04-13
from django.db.models import Model, Manager, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, BooleanField, DateField, DateTimeField
from django.contrib.auth import get_user_model
from django.utils import timezone
import json # PR2018-12-02

# PR2018-05-05 use AUTH_USER_MODEL
#from django.contrib.auth.models import User
#from accounts.models import User
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
# CustomManager adds function get_or_none. Used in  Subjectbase to prevent DoesNotExist exception
class CustomManager(Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except:
            return None


class Country(Model):
    # PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
    objects = CustomManager()

    name = CharField(max_length=50, unique=True)
    abbrev = CharField(max_length=6, unique=True)
    locked = BooleanField(default=False)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Country, self).__init__(*args, **kwargs)
        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # otherwise a logrecord would be created every time the save button is clicked without changes
        self.original_name = self.name
        self.original_abbrev = self.abbrev
        self.original_locked = self.locked

    def save(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)

        # Override the save() method of the model to perform validation on every save.
        # https://stackoverflow.com/questions/14470585/how-to-validate-uniqueness-constraint-across-foreign-key-django?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        # self.full_clean()

    # check if data has changed. If so: save object
        #logger.debug('original_name ' + str(self.original_name) + ' name ' + str(self.name))
        if self.data_has_changed():
            self.modified_by = self.request.user
            # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]  # result = (on_false, on_true)[condition]
            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Country, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Country, self).save
            # save to logfile
            self.save_to_log()

    def delete(self, *args, **kwargs):
        request_user = kwargs.pop('request_user')

        # update modified_by and modified_at, so it can be stored in log
        self.modified_by = request_user
        self.modified_at = timezone.now()
        self.mode = 'd'
        self.data_has_changed()

        # First save to logfile
        self.save_to_log()
        # then delete record
        super(Country, self).delete(*args, **kwargs)

    def save_to_log(self):
        Country_log.objects.create(
            country_id=self.id,

            name=self.name,
            abbrev=self.abbrev,
            locked=self.locked,

            name_mod=self.name_mod,
            abbrev_mod=self.abbrev_mod,
            locked_mod=self.locked_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self):  # PR2018-08-31
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved
        self.name_mod = self.original_name != self.name
        self.abbrev_mod = self.original_abbrev != self.abbrev
        self.locked_mod = self.original_locked != self.locked
        return not self.is_update or \
               self.name_mod or \
               self.abbrev_mod or \
               self.locked_mod

    @property # PR2018-06-22
    def has_no_linked_data(self):
        User = get_user_model()
        linked_users_count = User.objects.filter(country_id=self.pk).count()
        # logger.debug('Country(Model has_linked_data linked_users_count: ' + str(linked_users_count))
        # TODO add other dependencies: Subject, Schoolcode etc
        return not bool(linked_users_count)

    @property
    def locked_str(self):
        return c.LOCKED_DICT.get(self.locked, '')

# PR2018-05-05
class Country_log(Model):
    objects = CustomManager()

    country_id = IntegerField(db_index=True)

    name = CharField(max_length=50, null=True)
    abbrev = CharField(max_length=6, null=True)
    locked = BooleanField(default=False)

    name_mod = BooleanField(default=False)
    abbrev_mod = BooleanField(default=False)
    locked_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

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
class Examyear(Model):  # PR2018-06-06
    objects = CustomManager()

    country = ForeignKey(Country, related_name='examyears', on_delete=PROTECT)

    examyear = PositiveSmallIntegerField()
    published = BooleanField(default=False)
    locked = BooleanField(default=False)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['-examyear',]

    def __str__(self):
        return str(self.examyear)

    def __init__(self, *args, **kwargs):
        super(Examyear, self).__init__(*args, **kwargs)
        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord would be created every time the save button is clicked without changes

        # NOT IN USE:
        # try: # PR2018-08-03 necessary, otherwise gives error 'Examyear has no country' because self = None.
        #     self._original_country = self.country
        # except:
        #     self._original_country = None

        self.original_examyear = self.examyear
        self.original_published = self.published
        self.original_locked = self.locked

        # PR2018-10-19 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        self.examyear_mod = False
        self.published_mod = False
        self.locked_mod = False

    def save(self, *args, **kwargs):
        # country.save(request) in ExamyearAddView.post
        self.request = kwargs.pop('request', None)

        if self.data_has_changed():
            self.modified_by = self.request.user
            self.modified_at = timezone.now()  # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
            self.mode = ('c', 'u')[self.is_update]  # result = (on_false, on_true)[condition]
            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Examyear, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Country, self).save
            self.save_to_log()

    def delete(self, *args, **kwargs):
        request_user = kwargs.pop('request_user')

        # update modified_by and modified_at, so it can be stored in log
        self.modified_by = request_user
        self.modified_at = timezone.now()
        self.mode = 'd'
        self.data_has_changed()

        # First save to logfile
        self.save_to_log()
        # then delete record
        super(Examyear, self).delete(*args, **kwargs)


    def save_to_log(self, *args, **kwargs):
        #Create method also saves record
        log_obj = Examyear_log.objects.create(
            examyear_id=self.id,
            country_id=self.country.id,

            examyear=self.examyear,
            published=self.published,
            locked=self.locked,

            examyear_mod=self.examyear_mod,
            published_mod=self.published_mod,
            locked_mod=self.locked_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )
        log_obj.save()

    def data_has_changed(self):  # PR2018-10-19
        # returns True when the value of one or more fields has changed
        self.is_update = self.id is not None # self.id is None before new record is saved
        self.examyear_mod = self.original_examyear != self.examyear
        self.published_mod = self.original_published != self.published
        self.locked_mod = self.original_locked != self.locked

        return not self.is_update or \
               self.examyear_mod or \
               self.published_mod or \
               self.locked_mod

    @property
    def published_str(self):
        published_int = int(bool(self.published))
        return c.PUBLISHED_DICT.get(published_int)

    @property
    def locked_str(self):
        locked_int = int(bool(self.locked))
        return c.LOCKED_DICT.get(locked_int)

    @property
    def schoolyear(self):  # PR2018-05-18 calculates schoolyear from this_examyear
        schoolyear = '-'
        if self.examyear is not None:
            last_year = int(str(self.examyear)) - 1
            schoolyear = str(last_year) + '-' + str(self.examyear)
        return schoolyear

    @property
    def equals_this_examyear(self):
        # PR2018-05-18 this_examyear is from August 01 thru July 31
        # PR2018-05-18 returns True if selected_examyear is this_examyear
        examyear_equals_thisyear = False
        if self.examyear is not None:
            now = timezone.now()
            this_examyear = now.year
            selected_examyear = self.examyear

            if now.month > 7:
                this_examyear = now.year + 1
            if selected_examyear == this_examyear:
                examyear_equals_thisyear = True
        return examyear_equals_thisyear

    @classmethod
    def next_examyear(self, request):
        # PR2018-07-25
        # PR2018-04-20 debug: gives error: invalid literal for int() with base 10: 'None' when table is empty
        # year_count = self.objects.count()

        #logger.debug('class Examyear(Model) next_examyear request.user.country: ' + str(request.user.country))
        try:
            examyear_count = self.objects.filter(country=request.user.country).count()
            # logger.debug('class Examyear(Model) next_examyear year_count: ' + str(year_count))
            if examyear_count == 0:
                examyear_max = 2018
            else:
                examyear = self.objects.filter(country=request.user.country).order_by('-examyear').first()
                examyear_max = examyear.examyear
                # logger.debug('class Examyear(Model) next_examyear examyear_max: ' + str(examyear_max))
        except:
            examyear_max = 2018
        examyear_new = int(examyear_max) + 1
        return examyear_new

# PR2018-06-06
class Examyear_log(Model):
    objects = CustomManager()

    examyear_id = IntegerField(db_index=True)
    country_id = IntegerField()

    examyear = PositiveSmallIntegerField(null=True)
    published = BooleanField(default=False)
    locked = BooleanField(default=False)

    examyear_mod = BooleanField(default=False)
    published_mod = BooleanField(default=False)
    locked_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

    @property
    def locked_str(self):
        return c.LOCKED_DICT.get(int(bool(self.locked)))

    @property
    def published_str(self):
        return c.PUBLISHED_DICT.get(int(bool(self.published)))

    @property
    def mode_str(self):
        mode_str = '-'
        if self.mode is not None:
            mode_str = c.MODE_DICT.get(str(self.mode))
        return mode_str


# === Department =====================================
# PR2018-09-15 moved from Subjects to School because of circulair refrence when trying to import subjects.Department
class Departmentbase(Model):# PR2018-10-17
    objects = CustomManager()


class Department(Model):# PR2018-08-10
    objects = CustomManager()

    # base and  examyear cannot be changed
    base = ForeignKey(Departmentbase, related_name='departments', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='examyears', on_delete=PROTECT)

    name = CharField(max_length=50, # PR2018-08-06 set Unique per Country True. Was: unique=True,
        help_text=_('Required. {} characters or fewer.'.format('50')),)
    abbrev = CharField(max_length=4, # PR2018-08-06 set Unique per Country True. Was: unique=True,
        help_text=_('Required. {} characters or fewer.'.format('4')),)
    sequence = PositiveSmallIntegerField(db_index=True, default=1)
    level_req = BooleanField(default=True)
    sector_req = BooleanField(default=True)
    level_caption = CharField(max_length=20, null=True, blank=True)  # PR2019-01-17
    sector_caption = CharField(max_length=20, null=True, blank=True)  # PR2019-01-17

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.abbrev

    def __init__(self, *args, **kwargs):
        super(Department, self).__init__(*args, **kwargs)

        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes
        self.original_name = self.name
        self.original_abbrev = self.abbrev
        self.original_sequence = self.sequence
        self.original_level_req = self.level_req
        self.original_sector_req = self.sector_req
        self.original_level_caption = self.level_caption
        self.original_sector_caption = self.sector_caption

        """
        # TODO iterate through field list PR2018-08-22
        see: https://www.caktusgroup.com/blog/2018/05/07/creating-dynamic-forms-django/
        for i in range(len(interests) + 1):
            field_name = 'interest_%s' % (i,)
            self.fields[field_name] = forms.CharField(required=False)
            try:
                self.initial[field_name] = interests[i].interest
            Except IndexError:
                self.initial[field_name] = “”
        field_name = 'interest_%s' % (i + 1,)
        self.fields[field_name] = forms.CharField(required=False)
        self.fields[field_name] = “”
        """

        # for k, v in vars(self).items():
        #     logger.debug('class Department(Model) __init__ for k, v in vars(self).items(): k: ' + str(k) + '_v: ' + str(v))

    def save(self, *args, **kwargs):  # called by subjectbase.save(self.request) in SubjectbaseEditView.form_valid
        self.request = kwargs.pop('request', None)

        # Override the save() method of the model to perform validation on every save.
        # https://stackoverflow.com/questions/14470585/how-to-validate-uniqueness-constraint-across-foreign-key-django?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        # self.full_clean()

    # check if data has changed. If so: save object
        if self.data_has_changed():

            # First create base record. base.id is used in Department. Create also saves new record
            if not self.is_update:
                self.base = Departmentbase.objects.create()

            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Department, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Department, self).save
            self.save_to_log()

    def delete(self, *args, **kwargs):  # PR2018-11-22
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(Department, self).delete(*args, **kwargs)

    def save_to_log(self):
        # Create method also saves record
        Department_log.objects.create(
            department_id=self.id, # self.id gets its value in super(School, self).save

            base = self.base,
            examyear = self.examyear,

            name=self.name,
            abbrev=self.abbrev,
            sequence = self.sequence,
            level_req = self.level_req,
            sector_req = self.sector_req,
            level_caption = self.level_caption,
            sector_caption = self.sector_caption,

            name_mod = self.name_mod,
            abbrev_mod = self.abbrev_mod,

            sequence_mod = self.sequence_mod,
            level_req_mod = self.level_req_mod,
            sector_req_mod = self.sector_req_mod,
            level_caption_mod=self.level_caption_mod,
            sector_caption_mod=self.sector_caption_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode = None):  # PR2018-11-22
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        self.name_mod = self.original_name != self.name
        self.abbrev_mod = self.original_abbrev != self.abbrev
        self.sequence_mod = self.original_sequence != self.sequence
        self.level_req_mod = self.original_level_req != self.level_req
        self.sector_req_mod = self.original_sector_req != self.sector_req
        self.level_caption_mod = self.original_level_caption != self.level_caption
        self.sector_caption_mod = self.original_sector_caption != self.sector_caption

        data_changed_bool = (
            not self.is_update or
            self.name_mod or
            self.abbrev_mod or
            self.sequence_mod or
            self.level_req_mod or
            self.sector_req_mod or
            self.level_caption_mod or
            self.sector_caption_mod
        )

        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        return data_changed_bool

    # @property  # PR2018-08-11
    # def has_no_linked_data(self):
    #     linked_items_count = Scheme.objects.filter(department_id=self.pk).count()
    #     # logger.debug('Subjectbase Model has_no_linked_data linked_items_count: ' + str(linked_items_count))
    #     return not bool(linked_items_count)

    @property
    def level_req_str(self):
        return c.YES_NO_BOOL_DICT.get(self.level_req)

    @property
    def sector_req_str(self):
        return c.YES_NO_BOOL_DICT.get(self.sector_req)

#  ++++++++++  Class methods  ++++++++++++++++++++++++
    @classmethod
    def depbase_list_str(cls, depbase_list, examyear):
        # PR2018-08-16 depbase_list_str displays string of depbase_list, level_list or sector_list.
        # e.g.: '1;2;3' becomes 'Vsbo, Havo, Vwo', '0' is skipped', empty is displayed as '-'
        # PR 2018-11-06 depbase_list stores dep_base.id's. In this way you can copy a level etc to next year,
        # without having too look up the dep_id of that year
        list_str = ''
        if depbase_list is not None and examyear is not None:
            # logger.debug('DepartmentModel depbase_list_str depbase_list: <' + str(depbase_list) + '> type: <' + str(type(depbase_list)) + '>')
            list_split = depbase_list.split(';')
            if bool(list_split):
                # logger.debug('DepartmentModel depbase_list_str list_split: <' + str(list_split) + '> type: <' + str(type(list_split)) + '>')
                for base_id_str in list_split:
                    if base_id_str:
                        value = ''

                        base_id_int = int(base_id_str)
                        # logger.debug('DepartmentModel depbase_list_str base_id_int: ' + str(base_id_int) + '> type: <' + str(type(base_id_int)) + '>')
                        # skip value 0 (None)
                        if base_id_int:
                            # base = Departmentbase.objects.filter(id=base_id_int).first()
                            # if base:
                            # logger.debug('base_id_int: ' + str(base_id_int))
                            # logger.debug('base: ' + str(base))
                            # logger.debug(' examyear: ' + str(examyear))
                            # instance = cls.objects.filter(base=base, examyear=examyear).first()

                            instance = cls.objects.filter(base__id=base_id_int, examyear=examyear).first()
                            if instance:
                                value = instance.abbrev
                            # logger.debug('DepartmentModel depbase_list_str value: ' + str(value) + '> type: <' + str(type(value)) + '>')

                        if value:
                            list_str = list_str + ', ' + value
                if list_str:
                    # slice off first 2 characters: ', '
                  list_str = list_str[2:]
        if not list_str:
            list_str = '-'
        # logger.debug('DepartmentModel depbase_list_str list_str: <' + str(list_str) + '>')
        return list_str

    @classmethod
    def depbase_list_choices(cls, examyear=None, depbase_list=None, show_none=False):
        # PR2018-08-12 function creates list of depbase_list, used in LevelAddForm, LevelEditForm, SecctorAddForm, SectorEditForm
        # filter by examyear: show only deps of user's examyear (country is parent of examyear)
        # filter by user_schoolbase: show only deps of user's schoolbase

        # NIU: add inactive records only when it is the current record (otherwise it will not display in field) PR2018-08-24

        # choises must be tuple or list, dictionary gives error: 'int' object is not iterable

        # IN USE?? depbase_list_choices_tuple: ((0, 'None'), (1, 'Vsbo'), (2, 'Havo'), (3, 'Vwo')), filter by Country

        # PR 2018-11-06 depbase_list stores dep_base.id's. In this way you can copy a level etc to next year,
        # without having too look up the dep_id of that year

        # depbase_list_choices = [(0, 'None'), (11, 'Vsbo'), (12, 'Havo'), (13, 'Vwo')]
        _choices = []
        if examyear:
            # logger.debug('user_country: <' + str(examyear) + '> Type: ' + str(type(examyear)))

            # add row 'None' at the start, only if not skip_none
            if show_none:
                _choices = [(0, '---')]

            # Not in use
            # convert list into tuple
            # PR2018-08-28 init_list is the depbase_list of the current user. Inactive items that are in the init_list will still be shown
            # init_list_tuple = ()
            # if init_list_str:
                # This function converts init_list_str string into init_list_tuple,  e.g.: ';1;2;' will be converted to (,1,2,)
                # init_list_list = init_list_str.split(';')
                # init_list_tuple = tuple(init_list_list)

            # iterate through departments rows, filtered by examyear (country is parent of examyear) PR2018-10-18
            departments = cls.objects.filter(examyear=examyear)
            for item in departments:
                # wrap item.id in delimiters, so ';1;' can be searched in depbase_list ";1;15;6;'
                # PR 2018-11-06 stores dep_base.id instead of dep.id. In this way you can copy a level etc to next year,
                # without having too look up the dep_id of that year
                base_id_str = ';' + str(item.base.id) + ";"

                # check if item must be added to list:
                    # - if not show_all: only active items that are in depbase_list are shown
                    # - inactive items are notadded, unless they are in init_list_str

                show_item = False
                if depbase_list is None:
                    # PR2018-10-18 was: # if no depbase_list given: show all departments of this examyear
                    show_item = True # PR2018-10-18 was: item.is_active
                else:
                    # if depbase_list is given: show only departments that are in depbase_list
                    if depbase_list:
                        # function ('' in '') returns True, ('' in 'x') returns True, ('x' in '') returns False
                        if base_id_str in depbase_list:
                            show_item = True

                # PR2018-11-06 NIU: was needed to show inactive deps that were in inti_list
                # if there is a init_list: show also the items of the init_list, if not yet shown
                # if not show_item:
                #    if init_list_str:
                #        init_list_str = ';' + init_list_str + ';'
                #        if base_id_str in init_list_str:
                #            # add item to list
                #            show_item = True

                # logger.debug(' item_id_str: <' + str(item_id_str) + '> show_item: ' + str(show_item))
                # if show_item: add item to list

                if show_item:
                    item = (item.base.id, item.abbrev )
                    _choices.append(item)
        logger.debug('depbase_list_choices _choices = ' + str(_choices))
        return _choices


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
                if request_user.is_role_school or request_user.is_role_insp_or_system:
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


# PR2018-06-06
class Department_log(Model):
    objects = CustomManager()

    department_id = IntegerField(db_index=True)

    base = ForeignKey(Departmentbase, related_name='+', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='+', on_delete=PROTECT)

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
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

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


class Schoolbase(Model):  # PR2018-05-27 PR2018-10-17 PR2018-11-11
    objects = CustomManager()


# ===  School Model =====================================
class School(Model):  # PR2018-08-20 PR2018-11-11
    objects = CustomManager()

    # base and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Schoolbase, related_name='schools', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='schools', on_delete=PROTECT)

    name = CharField(max_length=50, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('50')),)
    abbrev = CharField(max_length=30, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('30')),)
    code = CharField(max_length=8, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('8')),)
    article = CharField(max_length=3, null=True)
    depbase_list = CharField(max_length=20, null=True)

    # is_template stores the examyear.id. In that way there can only be one template per examyear / country
    is_template = IntegerField(unique=True, null=True)

    locked = BooleanField(default=False)

    # president = CharField(max_length=50, null=True)
    # secretary = CharField(max_length=50, null=True)
    # diplomadate = DateField(null=True)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['code',]

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):  # PR2018-08-20
        super(School, self).__init__(*args, **kwargs)
        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes
        self.original_name = self.name
        self.original_code = self.code
        self.original_abbrev = self.abbrev
        self.original_article = self.article
        self.original_depbase_list = self.depbase_list
        self.original_is_template = self.is_template
        self.original_locked = self.locked

        # PR2018-10-19 initialize here, otherwise delete gives error: object has no attribute 'name_mod'
        self.name_mod = False
        self.code_mod = False
        self.abbrev_mod = False
        self.article_mod = False
        self.depbase_list_mod = False
        self.is_template_mod = False
        self.locked_mod = False

    def save(self, *args, **kwargs):  #PR2018-08-20 called by school.save(self.request) in SchoolEditView.form_valid
        self.request = kwargs.pop('request', None)

    # Check if data has changed. If so: save object
        if self.data_has_changed():
            # First create base record. base.id is used in School. Create also saves new record
            if not self.is_update:
                self.base = Schoolbase.objects.create()

            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(School, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            self.save_to_log()

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(School, self).delete(*args, **kwargs)

    def save_to_log(self):
        # Create method also saves record
        School_log.objects.create(
            school_id=self.id,  # self.id gets its value in super(School, self).save

            base=self.base,
            examyear=self.examyear,

            name=self.name,
            code=self.code,
            abbrev=self.abbrev,
            article=self.article,
            depbase_list=self.depbase_list,
            is_template=self.is_template,
            locked=self.locked,

            name_mod=self.name_mod,
            code_mod=self.code_mod,
            abbrev_mod=self.abbrev_mod,
            article_mod=self.article_mod,
            depbase_list_mod=self.depbase_list_mod,
            is_template_mod = self.is_template_mod,
            locked_mod=self.locked_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode = None):
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        self.name_mod = self.original_name != self.name
        self.code_mod = self.original_code != self.code
        self.abbrev_mod = self.original_abbrev != self.abbrev
        self.article_mod = self.original_article != self.article
        self.depbase_list_mod = self.original_depbase_list != self.depbase_list
        self.is_template_mod = self.original_is_template != self.is_template
        self.locked_mod = self.original_locked != self.locked

        data_changed_bool = (
            not self.is_update or
            self.name_mod or
            self.code_mod or
            self.abbrev_mod or
            self.article_mod or
            self.depbase_list_mod or
            self.is_template_mod or
            self.locked_mod
        )

        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        return data_changed_bool

    @property  # PR2018-11-11
    def has_no_linked_data(self):
        # TODO find records in linked tables
        # PR2018-10-20 from http://blog.etianen.com/blog/2013/06/08/django-querysets/
        # No rows were fetched from the database, so we save on bandwidth and memory.
        _has_linked_data = False # Scheme.objects.filter(level_id=self.pk).exists()
        # was: linked_items_count = Scheme.objects.filter(level_id=self.pk).count()
        return not _has_linked_data

    @property
    def depbase_list_str(self): # PR108-08-27 PR2018-11-06
        return Department.depbase_list_str(depbase_list=self.depbase_list, examyear=self.examyear)

    @property
    def depbase_list_tuple(self):
        # depbase_list_tuple is called bij LevelEditForm, SectorEditForm, SchemeEditForm, SubjectdefaultEditForm
        return get_depbase_list_tuple(self.depbase_list)

    @property
    def locked_str(self):
        locked_int = int(bool(self.locked))
        return c.LOCKED_DICT.get(locked_int)

    @property
    def is_template_str(self):
        is_template_int = int(bool(self.is_template))
        return c.YES_NO_DICT.get(is_template_int)

#  ++++++++++  Class methods  ++++++++++++++++++++++++

    @classmethod  # PR1019-01-15
    def get_by_user_schoolbase_examyear(cls, request_user):
        school = None
        if request_user:
            if request_user.schoolbase and request_user.examyear:
                school = cls.objects.filter(base=request_user.schoolbase, examyear=request_user.examyear).first()
        return school


    @classmethod
    def school_choices(cls, request_user):
        #PR2018-11-02 school_choices is used in User_add Form.
        # school_choices creates list of tuples with (schoolbase_id, school_name)
        _choices = [(0, '---')]
        if request_user:
            if request_user.examyear:
                # PR2018-12-17
                # request_user.is_role_insp_or_system: show schools from this country and this examyear
                # request_user.is_role_school: show only school of request_user, field is disabled
                _schools = None
                if request_user.is_role_insp_or_system:
                    _schools = cls.objects.filter(examyear=request_user.examyear)
                    for _school in _schools:
                        _school_name = _school.name
                        if _school.code:
                            _school_name = _school.code + '  ' + _school_name
                        item = (_school.base.id, _school_name )
                        _choices.append(item)
                else:
                    _school = cls.objects.filter(base=request_user.schoolbase, examyear=request_user.examyear).first()
                    _school_name = _school.name
                    if _school.code:
                        _school_name = _school.code + '  ' + _school_name
                    _choices = [(_school.base.id, _school_name)]
            return _choices
"""

    # PR2018-06-03
    @property
    def code_schoolname(self):
        code_str = ''
        if self.code:
            code_str = str(self.code) + ' - '
        if self.name:
            code_str = code_str + str(self.name)
        return code_str

    @property
    def article_str(self):  # PR2018-10-01
        art_str = ''
        if self.article:
            art_str = self.article
        return art_str

    @property
    def depbase_list_str(self): # PR108-10-01
        return Department.depbase_list_str(self.depbase_list)

    @property
    def depbase_list_tuple(self):
        # depbase_list_tuple is called bij LevelEditForm, SectorEditForm, SchemeEditForm, SubjectdefaultEditForm
        return get_depbase_list_tuple(self.depbase_list)

    @property
    def is_active_str(self):  # PR108-09-02
        return c.IS_ACTIVE_DICT.get(self.is_active, '')

    @property
    def is_active_choices(self):  # PR108-09-02
        return c.IS_ACTIVE_DICT.get(self.is_active, '')


"""

class School_log(Model):
    objects = CustomManager()

    school_id = IntegerField(db_index=True)

    base = ForeignKey(Schoolbase, related_name='+', on_delete=PROTECT)

    examyear = ForeignKey(Examyear, related_name='+', on_delete=PROTECT)

    name = CharField(max_length=50,null=True)
    code = CharField(max_length=12,null=True)
    abbrev = CharField(max_length=50,null=True)
    article = CharField(max_length=3, null=True)
    depbase_list = CharField(max_length=20, null=True)
    is_template = BooleanField(null=True)  # default School of this country and examyear PR2018-08-23
    locked =  BooleanField(default=False)

    name_mod = BooleanField(default=False)
    code_mod = BooleanField(default=False)
    abbrev_mod = BooleanField(default=False)
    article_mod = BooleanField(default=False)
    depbase_list_mod = BooleanField(default=False)
    is_template_mod =  BooleanField(default=False)
    locked_mod =  BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

    def __str__(self):
        return self.name

    @property
    def depbase_list_str(self): # PR108-08-27 PR2018-11-06
        return Department.depbase_list_str(depbase_list=self.depbase_list, examyear=self.examyear)

    @property
    def depbase_list_tuple(self):
        # depbase_list_tuple is called bij LevelEditForm, SectorEditForm, SchemeEditForm, SubjectdefaultEditForm
        return get_depbase_list_tuple(self.depbase_list)

    @property
    def locked_str(self):
        return c.YES_NO_DICT.get(int(bool(self.locked)))

    @property
    def is_template_str(self):
        return c.YES_NO_DICT.get(int(bool(self.is_template)))

    @property
    def mode_str(self):
        mode_str = '-'
        if self.mode is not None:
            mode_str = c.MODE_DICT.get(str(self.mode))
        return mode_str

# PR2018-106-17
class School_message(Model):
    objects = CustomManager()

    school = ForeignKey(School, related_name='+', on_delete=PROTECT)
    sent_to =  CharField(max_length=2048, null=True, blank=True)
    title =  CharField(max_length=80, null=True, blank=True)
    note =  CharField(max_length=4096, null=True, blank=True)
    is_insp = BooleanField(default=False)
    is_unread = BooleanField(default=False)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

# PR2018-106-17
class School_message_log(Model):
    objects = CustomManager()

    school_message_id = IntegerField(db_index=True)
    sent_to =  CharField(max_length=2048, null=True, blank=True)
    title =  CharField(max_length=80, null=True, blank=True)
    note =  CharField(max_length=4096, null=True, blank=True)
    is_insp = BooleanField(default=False)
    is_unread = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

# PR2018-06-07
class Entrylist(Model):
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


class Schoolsetting(Model):  # PR2018-12-02
    # PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
    objects = CustomManager()

    schoolbase = ForeignKey(Schoolbase, related_name='schoolsetting', on_delete=CASCADE)
    depbase = ForeignKey(Departmentbase, null=True, related_name='schoolsetting', on_delete=SET_NULL)
    key_str = CharField(db_index=True, max_length=50)

    char01 = CharField(max_length=2048, null=True)
    char02 = CharField(max_length=2048, null=True)
    char03 = CharField(max_length=2048, null=True)
    char04 = CharField(max_length=2048, null=True)
    int01 = IntegerField(null=True)
    int02 = IntegerField(null=True)
    bool01 = BooleanField(default=False)
    bool02 = BooleanField(default=False)
    date01 = DateTimeField(null=True)
    date02 = DateTimeField(null=True)


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


"""
# PR2018-12-03 not working with dict, only with Queryset

from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

from django.core.serializers import serialize # PR2018-12-03

mapped_coldef_list =  serialize('json', coldef_list, cls=LazyEncoder)
                    
class LazyEncoder(DjangoJSONEncoder):
    # PR2018-12-03 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy/19734757
    # and https://docs.djangoproject.com/en/2.1/topics/serialization/#serialization-formats-json
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)
"""
