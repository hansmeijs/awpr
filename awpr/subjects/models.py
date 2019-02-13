# PR2018-07-20
from django.db.models import Model, Manager, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveIntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField, DateField
from django.core.validators import MaxValueValidator
from django.utils import timezone
# from django.core.exceptions import ObjectDoesNotExist, ValidationError, NON_FIELD_ERRORS
# PR2018-05-05 use AUTH_USER_MODEL
#from django.contrib.auth.models import User
#from accounts.models import User
from django.utils.translation import ugettext_lazy as _

from awpr.settings import AUTH_USER_MODEL
from schools.models import Country, Examyear, Department, Department_log, School, School_log
from awpr import constants as c

import logging
logger = logging.getLogger(__name__)

# PR2018-04-22: backup: (venv) C:\dev\awpr\awpr>py -3 manage.py dumpdata schools --format json --indent 4 > schools/backup/schools.json
#               restore: (venv) C:\dev\awpr\awpr>py -3 manage.py loaddata schools/backup/schools.json

# clean() method rus to_python(), validate(), and run_validators() and propagates their errors.
# If, at any time, any of the methods raise ValidationError, the validation stops and that error is raised.
# This method returns the clean data, which is then inserted into the cleaned_data dictionary of the form.


# PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
# CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
class CustomManager(Manager):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except:
            return None


# === Level =====================================
class Levelbase(Model):  # PR2018-10-17
    objects = CustomManager()


class Level(Model): # PR2018-08-12
    # CustomManager adds function get_or_none to prevent DoesNotExist exception
    objects = CustomManager()

    # base and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Levelbase, related_name='levels', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='levels', on_delete=PROTECT)

    name = CharField(max_length=50, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('50')),)
    abbrev = CharField(max_length=8, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('8')),)
    sequence = PositiveSmallIntegerField(default=1)
    depbase_list = CharField(max_length=20, null=True)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.abbrev

    def __init__(self, *args, **kwargs):
        super(Level, self).__init__(*args, **kwargs)

        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes
        self.original_name = self.name
        self.original_abbrev = self.abbrev
        self.original_sequence = self.sequence
        self.original_depbase_list = self.depbase_list

        # PR2018-10-19 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        self.name_mod = False
        self.abbrev_mod = False
        self.sequence_mod = False
        self.depbase_list_mod = False

    def save(self, *args, **kwargs):  # called by subjectdefault.save(self.request) in SubjectdefaultEditView.form_valid
        self.request = kwargs.pop('request', None)
        # logger.debug('Level(Model) save self.request ' + str(self.request) + ' Type: ' + str(type(self.request)))

        # Override the save() method of the model to perform validation on every save.
        # https://stackoverflow.com/questions/14470585/how-to-validate-uniqueness-constraint-across-foreign-key-django?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        # self.full_clean()

    # check if data has changed. If so: save object
        if self.data_has_changed():
            # First create base record. base.id is used in Department. Create also saves new record
            if not self.is_update:
                self.base = Levelbase.objects.create()

            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Level, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Level, self).save
            self.save_to_log()

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(Level, self).delete(*args, **kwargs)

    def save_to_log(self):  # PR2018-08-27
        # Create method also saves record
        Level_log.objects.create(
            level_id=self.id,  # self.id gets its value in super(Level, self).save

            base = self.base,
            examyear = self.examyear,

            name=self.name,
            abbrev=self.abbrev,
            sequence=self.sequence,
            depbase_list=self.depbase_list,

            name_mod=self.name_mod,
            abbrev_mod=self.abbrev_mod,
            sequence_mod=self.sequence_mod,
            depbase_list_mod=self.depbase_list_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode = None):  # PR2018-07-21 # PR2018-08-24  PR2018-11-08
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        self.name_mod = self.original_name != self.name
        self.abbrev_mod = self.original_abbrev != self.abbrev
        self.sequence_mod = self.original_sequence != self.sequence
        self.depbase_list_mod = self.original_depbase_list != self.depbase_list

        data_changed_bool = (
            not self.is_update or
            self.name_mod or
            self.abbrev_mod or
            self.sequence_mod or
            self.depbase_list_mod
        )

        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        return data_changed_bool

    @property  # PR2018-08-11
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

#  ++++++++++  Class methods  +++++++++++++++++++++++++++
    @classmethod
    def get_level_attr(cls, request_user):  # PR2018-10-25
    # function creates dict of fields of levels in selected schoolyear
    # used in SchemeAddView, SchemeEditView, SchemeitemAddView, SchemeitemEditView
    # attr: {'7': {'name': 'Theoretisch Kadergerichte Leerweg', 'abbrev': 'TKL', 'sequence': 1, 'depbase_list': ';11;'},
    #        '8': {'name': 'Praktisch Kadergerichte Leerweg', 'abbrev': 'PKL', 'sequence': 2, 'depbase_list': ';11;'},
    #        '9': {'name': 'Praktisch Basisgerichte Leerweg', 'abbrev': 'PBL', 'sequence': 3, 'depbase_list': ';11;'}}
        attr = {}
        if request_user is not None:
            if request_user.country is not None and request_user.examyear is not None:
                if request_user.examyear.country.pk == request_user.country.pk:
                    # filter levels of request_user.examyear
                    for item in Level.objects.filter(examyear=request_user.examyear):
                        _id_str = str(item.id)
                        attr[_id_str] = {
                            'name': item.name,
                            'abbrev': item.abbrev,
                            'sequence': item.sequence,
                            'depbase_list': item.depbase_list
                        }
        # logger.debug('attr: ' + str(attr))
        return attr

    @classmethod
    def get_abbrev_list(cls, request_user):  # PR2018-10-25
    # function creates list of abbrev of levels filter request_user.depbase
    # used in get_mapped_levels_student for import student
    # level_list: ['TKL', 'PKL', 'PBL']
        abbrev_list = []
        if request_user is not None:
            if request_user.examyear is not None and request_user.depbase is not None:
                dep_id_str = ';' + str(request_user.depbase.id) + ';'
                levels = cls.objects.filter(examyear=request_user.examyear, depbase_list__contains=dep_id_str)
                for level in levels:
                    abbrev_list.append({"base_id": level.base.id, "abbrev": level.abbrev})
        return abbrev_list


    @classmethod
    def get_select_list(cls, request_user):  # PR2019-01-14
    # function creates list of levels of this examyear
    # filter by depbase is done on clientside
    # used in table select_levelin schemeitemlist
    # select_list: {id: 7, name: "Theoretisch Kadergerichte Leerweg", abbrev: "TKL", depbase_list: ";11;"}
        select_list = []
        if request_user is not None:
            if request_user.examyear is not None:
                levels = cls.objects.filter(examyear=request_user.examyear)
                for level in levels:
                    level_dict = {
                        "id": level.id,
                        "name": level.name,
                        "abbrev": level.abbrev,
                        "depbase_list": level.depbase_list
                    }
                    select_list.append(level_dict)
        return select_list

    """
    @classmethod
    def level_list_choices(cls, user_examyear=None, user_dep=None, init_list_str=None, skip_none=False):
        # PR2018-08-29 function is used in SchemeAddForm, SchemeEditForm
        # filter by user_dep (user_examyear is Foreignkey of user_dep)
        # add records not in user_dep only when it is current record (otherwise it will not display in field) PR2018-08-24
        # choises must be tuple or list, dictionary gives error: 'int' object is not iterable
        # depbase_list_choices: [(0, 'None'), (1, 'Vsbo'), (2, 'Havo'), (3, 'Vwo')]
        # IN USE?? depbase_list_choices_tuple: ((0, 'None'), (1, 'Vsbo'), (2, 'Havo'), (3, 'Vwo')), filter by Country
        #logger.debug('DepartmentModel depbase_list_choices init_list_str: <' + str(init_list_str) + '> Type: ' + str(type(init_list_str)))

        # logger.debug('Level(Model) level_list_choices user_country: ' + str(user_country))
        # logger.debug('Level(Model) __init__ user_dep: ' + str(user_dep))

        choices = []
        if user_examyear and user_dep:
            # add row 'None' at the start, only if not skip_none
            if not skip_none:
                choices = [(0, '---')]

            # PR2018-08-28 init_list is the depbase_list of the current user. Inactive items that are in the init_list will still be shown
            init_list_tuple = ()
            if init_list_str:
                # This function converts init_list_str into init_list_tuple,  e.g.: '1;2' will be converted to (1,2)
                init_list_list = init_list_str.split(';')
                init_list_tuple = tuple(init_list_list)

            # wrap dep_id in delimiters, so ';1;' can be searched in ";1;15;6;'
            if user_dep:
                user_dep_id_str = ';' + str(user_dep.id) + ";"
                # iterate through level rows, filtered by country and user_dep
                levels = cls.objects.filter(country=user_examyear, depbase_list__contains=user_dep_id_str)
            else:
                levels = cls.objects.filter(country=user_examyear)

            for level in levels:
                if level:
                    # check if level must be added to list:
                    # - all active levels are added
                    # - inactive levels are only added when they are in init_list_str
                    show_item = False
                    if level.is_active:
                        show_item = True
                    else:
                        # do show inactive items when they are in init_list
                        if init_list_tuple:
                            for list_item in init_list_tuple:
                                #logger.debug(' depbase_list_choices list_item: ' + str(list_item))
                                if int(list_item) == level.id:
                                    show_item = True
                                    break
                    # add level to list
                    if show_item:
                        level = (level.id, level.abbrev )
                        choices.append(level)
        #logger.debug('depbase_list_choices choices = ' + str(choices))
        return choices
"""


# PR2018-08-12
class Level_log(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    level_id = IntegerField(db_index=True)

    base = ForeignKey(Levelbase, related_name='+', on_delete=PROTECT)

    # TODO: refer to log table
    examyear = ForeignKey(Examyear, related_name='+', on_delete=PROTECT)

    name = CharField(max_length=50, null=True)
    abbrev = CharField(max_length=8, null=True)
    sequence = PositiveSmallIntegerField(null=True)
    depbase_list = CharField(max_length=20, null=True)

    name_mod = BooleanField(default=False)
    abbrev_mod = BooleanField(default=False)
    sequence_mod = BooleanField(default=False)
    depbase_list_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    @property
    def depbase_list_str(self): # PR108-08-27
        return Department.depbase_list_str(self.depbase_list, self.examyear)

    @property
    def mode_str(self):
        return c.MODE_DICT.get(str(self.mode),'-')


# === Sector =====================================
class Sectorbase(Model):  # PR2018-10-17
    objects = CustomManager()


class Sector(Model):  # PR2018-06-06
    # CustomManager adds function get_or_none to prevent DoesNotExist exception
    objects = CustomManager()

    # levelbase and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Sectorbase, related_name='sectors', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='sectors', on_delete=PROTECT)

    name = CharField(max_length=50, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('50')),)
    abbrev = CharField(max_length=8, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('8')),)
    sequence = PositiveSmallIntegerField(default=1)
    depbase_list = CharField(max_length=20, null=True)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.abbrev

    def __init__(self, *args, **kwargs):
        super(Sector, self).__init__(*args, **kwargs)

        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes
        self.original_name = self.name
        self.original_abbrev = self.abbrev
        self.original_sequence = self.sequence
        self.original_depbase_list = self.depbase_list

        # PR2018-10-19 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        self.name_mod = False
        self.abbrev_mod = False
        self.sequence_mod = False
        self.depbase_list_mod = False

    def save(self, *args, **kwargs):  # called by subjectdefault.save(self.request) in SubjectdefaultEditView.form_valid
        self.request = kwargs.pop('request', None)

        # Override the save() method of the model to perform validation on every save.
        # https://stackoverflow.com/questions/14470585/how-to-validate-uniqueness-constraint-across-foreign-key-django?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        # self.full_clean()

    # check if data has changed. If so: save object
        if self.data_has_changed():
            # First create base record. base.id is used in Department. Create also saves new record
            if not self.is_update:
                self.base = Sectorbase.objects.create()

            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Sector, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Sector, self).save
            self.save_to_log()

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(Sector, self).delete(*args, **kwargs)

    def save_to_log(self): #, *args, **kwargs):
        # Create method also saves record
        Sector_log.objects.create(
            sector_id=self.id,

            base = self.base,
            examyear = self.examyear,

            name=self.name,
            abbrev=self.abbrev,
            sequence=self.sequence,
            depbase_list=self.depbase_list,

            name_mod=self.name_mod,
            abbrev_mod=self.abbrev_mod,
            sequence_mod=self.sequence_mod,
            depbase_list_mod=self.depbase_list_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode=None):  # PR2018-07-21 # PR2018-08-24  PR2018-11-11
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None  # self.id is None before new record is saved

        self.name_mod = self.original_name != self.name
        self.abbrev_mod = self.original_abbrev != self.abbrev
        self.sequence_mod = self.original_sequence != self.sequence
        self.depbase_list_mod = self.original_depbase_list != self.depbase_list

        data_changed_bool = (
                not self.is_update or
                self.name_mod or
                self.abbrev_mod or
                self.sequence_mod or
                self.depbase_list_mod
        )

        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        return data_changed_bool

    @property  # PR2018-08-11
    def has_no_linked_data(self):
        linked_items_count = Scheme.objects.filter(sector_id=self.pk).count()
        # logger.debug('SubjectDefault Model has_no_linked_data linked_items_count: ' + str(linked_items_count))
        return not bool(linked_items_count)

    @property
    def depbase_list_str(self): # PR108-08-27 PR2018-11-06
        return Department.depbase_list_str(depbase_list=self.depbase_list, examyear=self.examyear)

    @property
    def depbase_list_tuple(self):
        # depbase_list_tuple is called bij LevelEditForm, SectorEditForm, SchemeEditForm, SubjectdefaultEditForm
        return get_depbase_list_tuple(self.depbase_list)


#  ++++++++++  Class methods  +++++++++++++++++++++++++++
    @classmethod
    def sector_list_choices(cls, user_examyear=None, user_dep=None, init_list_str=None, skip_none=False, full_name=False):
        # PR2018-08-29 function is used in SchemeAddForm, SchemeEditForm
        # filter by user_dep (user_examyear is Foreignkey of user_dep)
        # add records not in user_dep only when it is current record (otherwise it will not display in field) PR2018-08-24
        # choises must be tuple or list, dictionary gives error: 'int' object is not iterable
        # depbase_list_choices: [(0, 'None'), (1, 'Vsbo'), (2, 'Havo'), (3, 'Vwo')]
        # IN USE?? depbase_list_choices_tuple: ((0, 'None'), (1, 'Vsbo'), (2, 'Havo'), (3, 'Vwo')), filter by Country
        #logger.debug('DepartmentModel depbase_list_choices init_list_str: <' + str(init_list_str) + '> Type: ' + str(type(init_list_str)))

        # logger.debug('Sector(Model) level_list_choices user_country: ' + str(user_country))
        # logger.debug('Sector(Model) __init__ user_dep: ' + str(user_dep))

        choices = []
        if user_examyear and user_dep:
            # add row 'None' at the start, only if not skip_none
            if not skip_none:
                choices = [(0, '---')]

            # PR2018-08-28 init_list is the depbase_list of the current user. Inactive items that are in the init_list will still be shown
            init_list_tuple = ()
            if init_list_str:
                # This function converts init_list_str into init_list_tuple,  e.g.: '1;2' will be converted to (1,2)
                init_list_list = init_list_str.split(';')
                init_list_tuple = tuple(init_list_list)

            # wrap dep_id in delimiters, so ';1;' can be searched in ";1;15;6;'
            if user_dep:
                user_dep_id_str = ';' + str(user_dep.id) + ";"
                # iterate through sector rows, filtered by examyear and user_dep
                sectors = cls.objects.filter(examyear=user_examyear, depbase_list__contains=user_dep_id_str)
            else:
                sectors = cls.objects.filter(examyear=user_examyear)

            # iterate through sector rows, filtered by country and
            for sector in sectors:
                if sector:
                    # check if sector must be added to list:
                    # - all active sectors are added
                    # - inactive sectors are only added when they are in init_list_str
                    show_item = False
                    if sector.is_active:
                        show_item = True
                    else:
                        # do show inactive items when they are in init_list
                        if init_list_tuple:
                            for list_item in init_list_tuple:
                                #logger.debug(' depbase_list_choices list_item: ' + str(list_item))
                                if int(list_item) == sector.id:
                                    show_item = True
                                    break
                    # add sector to list
                    if show_item:
                        if full_name:
                            display = sector.name
                        else:
                            display = sector.abbrev
                        sector = (sector.id, display )
                        choices.append(sector)
        #logger.debug('depbase_list_choices choices = ' + str(choices))
        return choices

    @classmethod
    def get_sector_attr(cls, request_user):  # PR2018-10-26
    # function creates dict of fields of sectors in selected schoolyear
        attr = {}
        if request_user is not None:
            if request_user.country is not None and request_user.examyear is not None:
                if request_user.examyear.country.pk == request_user.country.pk:
                    # filter sectors of request_user.examyear
                    for item in Sector.objects.filter(examyear=request_user.examyear):
                        _id_str = str(item.id)
                        attr[_id_str] = {
                            'name': item.name,
                            'abbrev': item.abbrev,
                            'sequence': item.sequence,
                            'depbase_list': item.depbase_list
                        }
        # logger.debug('attr: ' + str(attr))
        return attr

    @classmethod
    def get_abbrev_list(cls, request_user):  # PR2019-01-01
    # function creates list of abbrev of sectors filter request_user.depbase
    # used in get_mapped_sectors_student for import student
    # sector_list: ['ec', 'tech', 'z&w']
        abbrev_list = []
        if request_user is not None:
            if request_user.examyear is not None and request_user.depbase is not None:
                dep_id_str = ';' + str(request_user.depbase.id) + ';'
                sectors = cls.objects.filter(examyear=request_user.examyear, depbase_list__contains=dep_id_str)
                for sector in sectors:
                    abbrev_list.append({"base_id": sector.base.id, "abbrev": sector.abbrev})
        return abbrev_list

    @classmethod
    def get_select_list(cls, request_user):  # PR2019-01-14
    # function creates list of sectors of yhis examyear
    # filter by depbase is done on clientside
    # used in table select_sector in schemeitemlist
    # select_list: {id: 32, name: "Cultuur en Maatschappij", abbrev: "c&m", depbase_list: ""}
        select_list = []
        if request_user is not None:
            if request_user.examyear is not None:
                sectors = cls.objects.filter(examyear=request_user.examyear)
                for sector in sectors:
                    sector_dict = {
                        "id": sector.id,
                        "name": sector.name,
                        "abbrev": sector.abbrev,
                        "depbase_list": sector.depbase_list
                    }
                    select_list.append(sector_dict)
        return select_list

    @classmethod
    def get_caption(cls, request_user):  #  # PR2019-01-01
        # caption Sector/Profiel depends on department
        caption =  "Sector/Profiel"
        if request_user.depbase:
            dep = request_user.department
            if dep.abbrev == "Vsbo":
                caption = "Sector"
            else:
                caption = "Profiel"
        return caption


# PR2018-06-06
class Sector_log(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    sector_id = IntegerField(db_index=True)

    base = ForeignKey(Sectorbase, related_name='+', on_delete=PROTECT)
    # TODO: refer to log table
    examyear = ForeignKey(Examyear, related_name='+', on_delete=PROTECT)

    name = CharField(max_length=50, null=True)
    abbrev = CharField(max_length=8, null=True)
    sequence = PositiveSmallIntegerField(null=True)
    depbase_list = CharField(max_length=20, null=True)

    name_mod = BooleanField(default=False)
    abbrev_mod = BooleanField(default=False)
    sequence_mod = BooleanField(default=False)
    depbase_list_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    @property
    def depbase_list_str(self): # PR108-08-27
        return Department.depbase_list_str(self.depbase_list, self.examyear)

    @property
    def mode_str(self):
        return c.MODE_DICT.get(str(self.mode),'-')


# === Subjecttype =====================================
class Subjecttypebase(Model): # PR2018-10-17
    objects = CustomManager()


# PR2018-06-06
class Subjecttype(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    base = ForeignKey(Subjecttypebase, related_name='characters', on_delete=CASCADE)
    examyear = ForeignKey(Examyear, related_name='characters', on_delete=PROTECT)

    name = CharField(max_length=50)
    abbrev = CharField(db_index=True,max_length=20)
    code = CharField(db_index=True,max_length=4)
    sequence = PositiveSmallIntegerField(default=1)
    depbase_list = CharField(max_length=20, null=True)
    has_pws = BooleanField(default=False) # has profielwerkstuk or sectorwerkstuk
    one_allowed = BooleanField(default=False) # if true: only one subject with this Subjecttype allowed per student

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Subjecttype, self).__init__(*args, **kwargs)

        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes
        self.original_name = self.name
        self.original_abbrev = self.abbrev
        self.original_code = self.code
        self.original_sequence = self.sequence
        self.original_depbase_list = self.depbase_list
        self.original_has_pws = self.has_pws
        self.original_one_allowed = self.one_allowed

        # PR2018-10-19 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        self.name_mod = False
        self.abbrev_mod = False
        self.code_mod = False
        self.sequence_mod = False
        self.depbase_list_mod = False
        self.has_pws_mod = False
        self.one_allowed_mod = False

    def save(self, *args, **kwargs):  # called by subjectdefault.save(self.request) in SubjectdefaultEditView.form_valid
        self.request = kwargs.pop('request', None)

    # check if data has changed. If so: save object
        if self.data_has_changed():
            # First create base record. base.id is used in Department. Create also saves new record
            if not self.is_update:
                self.base = Subjecttypebase.objects.create()

            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Subjecttype, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Level, self).save
            self.save_to_log()

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(Subjecttype, self).delete(*args, **kwargs)

    def save_to_log(self):  # PR2018-08-27
        # Create method also saves record
        Subjecttype_log.objects.create(
            subjecttype_id=self.id,  # self.id gets its value in super(Level, self).save

            base=self.base,
            examyear=self.examyear,

            name=self.name,
            abbrev=self.abbrev,
            code=self.code,
            sequence=self.sequence,
            depbase_list=self.depbase_list,
            has_pws=self.has_pws,
            one_allowed=self.one_allowed,

            name_mod=self.name_mod,
            abbrev_mod=self.abbrev_mod,
            code_mod=self.code_mod,
            sequence_mod=self.sequence_mod,
            depbase_list_mod=self.depbase_list_mod,
            has_pws_mod=self.has_pws_mod,
            one_allowed_mod=self.one_allowed_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode = None):  # PR2018-07-21 # PR2018-08-24
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        self.name_mod = self.original_name != self.name
        self.abbrev_mod = self.original_abbrev != self.abbrev
        self.code_mod = self.original_code != self.code
        self.sequence_mod = self.original_sequence != self.sequence
        self.depbase_list_mod = self.original_depbase_list != self.depbase_list
        self.has_pws_mod = self.original_has_pws != self.has_pws
        self.one_allowed_mod = self.original_one_allowed != self.one_allowed

        data_changed_bool = (
            not self.is_update or
            self.name_mod or
            self.abbrev_mod or
            self.code_mod or
            self.sequence_mod or
            self.depbase_list_mod or
            self.has_pws_mod or
            self.one_allowed_mod
        )
        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        return data_changed_bool

    @property
    def depbase_list_str(self): # PR108-08-27 PR2018-11-06
        return Department.depbase_list_str(depbase_list=self.depbase_list, examyear=self.examyear)

    @property
    def depbase_list_tuple(self):
        # TODO: check if this prop is in use
        # depbase_list_tuple is called bij LevelEditForm, SectorEditForm, SchemeEditForm, SubjectdefaultEditForm
        return get_depbase_list_tuple(self.depbase_list)


#  ++++++++++  Class methods  +++++++++++++++++++++++++++
    @classmethod
    def get_subjtype_list(cls, department):  # PR2019-01-18
        depbase_id_str = ';' + str(department.base.id) + ';'
        subjecttypes = cls.objects.filter(examyear=department.examyear, depbase_list__contains=depbase_id_str).all()
        subjecttype_list = []
        for item in subjecttypes:
            subjecttype_list.append({
                'sjtp_id': str(item.id),
                'name': item.name,
                'abbrev': item.abbrev,
                'sequ': item.sequence,
                'pws': item.has_pws,
                'one': item.one_allowed
            })
        return subjecttype_list

class Subjecttype_log(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    subjecttype_id = IntegerField(db_index=True)

    base = ForeignKey(Subjecttypebase, related_name='+', on_delete=CASCADE)
    # TODO: refer to log table
    examyear = ForeignKey(Examyear, related_name='+', on_delete=PROTECT)

    name = CharField(max_length=50, null=True)
    abbrev = CharField(max_length=20,null=True)
    code = CharField(max_length=4,null=True)
    sequence = PositiveSmallIntegerField(null=True)
    depbase_list = CharField(max_length=20, null=True)
    has_pws = BooleanField(default=False)
    one_allowed = BooleanField(default=False)

    name_mod = BooleanField(default=False)
    abbrev_mod = BooleanField(default=False)
    code_mod = BooleanField(default=False)
    sequence_mod = BooleanField(default=False)
    depbase_list_mod = BooleanField(default=False)
    has_pws_mod = BooleanField(default=False)
    one_allowed_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    @property
    def depbase_list_str(self): # PR108-08-27
        return Department.depbase_list_str(self.depbase_list, self.examyear)

    @property
    def mode_str(self):
        return c.MODE_DICT.get(str(self.mode),'-')


# PR2018-06-06 There is one Scheme per department/level/sector per year per country
class Scheme(Model):  # PR2018-09-07
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()
    # PR2018-11-07 blank=True is necessary otherwise blank field gives error 'Dit veld is verplicht.'
    department = ForeignKey(Department, related_name='schemes', on_delete=PROTECT)
    level = ForeignKey(Level, null=True, blank=True, related_name='schemes', on_delete=PROTECT)
    sector = ForeignKey(Sector, null=True,  blank=True, related_name='schemes', on_delete=PROTECT)
    name = CharField(max_length=50)  # TODO set department+level+sector Unique per examyear True.
    fields = CharField(max_length=50, null=True,  blank=True)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Scheme, self).__init__(*args, **kwargs)
        try:
            self.original_department = self.department
        except:
            self.original_department = None
        try:
            self.original_level = self.level
        except:
            self.original_level = None
        try:
            self.original_sector = self.sector
        except:
            self.original_sector = None

        self.original_name = self.name
        self.original_fields = self.fields

    def save(self, *args, **kwargs):  # called by subjectdefault.save(self.request) in SubjectdefaultEditView.form_valid
        self.request = kwargs.pop('request', None)

        # check if data has changed. If so: save object
        if self.data_has_changed():
            super(Scheme, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            self.save_to_log()

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(Scheme, self).delete(*args, **kwargs)

    def save_to_log(self):  # PR2018-08-27
        # PR2018-10-28 debug: 'NoneType' object has no attribute 'id'

        # get latest Department_log row that corresponds with self.department
        dep_log = None
        if self.department is not None:
            dep_log = Department_log.objects.filter(department_id=self.department.id).order_by('-id').first()

        # get latest Level_log row that corresponds with self.level
        level_log = None
        if self.level is not None:
            level_log = Level_log.objects.filter(level_id=self.level.id).order_by('-id').first()
            # level_id = self.level.id if self.level is not None else None

        # get latest Sector_log row that corresponds with self.sector
        sector_log = None
        if self.sector is not None:
            sector_log = Sector_log.objects.filter(sector_id=self.sector.id).order_by('-id').first()

        # Create method also saves record
        Scheme_log.objects.create(
            scheme_id=self.id,  # self.id gets its value in super(Level, self).save

            dep_log=dep_log,
            level_log=level_log,
            sector_log=sector_log,

            name=self.name,
            fields=self.fields,

            dep_mod=self.dep_mod,
            level_mod=self.level_mod,
            sector_mod=self.sector_mod,
            name_mod=self.name_mod,
            fields_mod=self.fields_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode = None):  # PR2018-09-07 PR2018-11-07
        # returns True when the value of one or more fields has changed
        self.is_update = self.id is not None  # self.id is None before new record is saved

        self.dep_mod = self.original_department != self.department
        self.level_mod = self.original_level != self.level
        self.sector_mod = self.original_sector != self.sector
        self.name_mod = self.original_name != self.name
        self.fields_mod = self.original_fields != self.fields

        data_changed_bool = (
            not self.is_update or
            self.dep_mod or
            self.level_mod or
            self.sector_mod or
            self.name_mod or
            self.fields_mod
        )

        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        return data_changed_bool

    @property  # PR2018-08-11
    def has_no_linked_data(self):
        linked_items_count = Scheme.objects.filter(level_id=self.pk).count()
        # logger.debug('SubjectDefault Model has_no_linked_data linked_items_count: ' + str(linked_items_count))
        return not bool(linked_items_count)

    @property
    def fields_str(self): # PR2019-01-19
        # logger.debug('--------- DepartmentModel fields_str ----------')
        # PR2018-08-16 fields_str displays string available fields in scheme.
        # e.g.: ';chco;prac;' becomes 'Choice combi, 'Has practical exam', empty is displayed as '-'
        list_str = ''
        if self.fields:
            # translation was working, error: 'must be str, not __proxy__' Solved by using 'ugettext' instead of 'ugettext_lazy'
            # fields_dict: {'chco': 'Keuze-combi vak', 'prac': 'Praktijkexamen'}
            fields_dict = c.SCHEMEFIELD_DICT

            # fields_split: ['', 'chco', ''] type: 'list'
            fields_split = self.fields.split(';')

            for key in fields_split:
                if key in fields_dict:
                    if fields_dict[key]:
                        list_str = list_str + ', ' + fields_dict[key]
            if list_str:
                # slice off first 2 characters: ', '
                list_str = list_str[2:]
        if not list_str:
            list_str = '-'
        return list_str

    def get_scheme_list_str(self):  # PR2019-01-21
        # get list with dict of this scheme, used in ajax_schemeitems_download - SchemeitemsDownloadView
        level_id_str = ''
        if (self.level):
            level_id_str = str(self.level.id)
        sector_id_str = ''
        if (self.sector):
            sector_id_str = str(self.sector.id)
        name = ''
        if (self.name):
            name = self.name
        fields = ''
        if (self.fields):
            fields = self.fields
        scheme_list = {
            'scheme_id': str(self.id),
            'depid': str(self.department.id),
            'lvlid': level_id_str,
            'sctid': sector_id_str,
            'name': name,
            'fields': fields
        }
        return scheme_list

#  ++++++++++  Class methods  +++++++++++++++++++++++++++
    @classmethod
    def create_scheme_name(cls, dep_abbrev='', level_abbrev='', sector_abbrev='' ):
        # PR2018-11-09 create scheme-name i.e.: 'vsbo - tkl - tech'
        scheme_name = ''
        if dep_abbrev:
            scheme_name = dep_abbrev
        if level_abbrev:
            scheme_name = scheme_name + " - " + level_abbrev
        if sector_abbrev:
            scheme_name = scheme_name + " - " + sector_abbrev
        return scheme_name


    @classmethod
    def get_scheme(cls, department, level, sector): # PR2019-02-08
        # lookup scheme by department, level (if required) and sector (if required)
        scheme = None
        if department:
            if department.level_req:
                if level:
                    if department.sector_req:
                        if sector:
                            scheme = Scheme.objects.filter(department=department, level=level, sector=sector).first()
                    else:
                        scheme = Scheme.objects.filter(department=department, level=level).first()
            else:
                if department.sector_req:
                    if sector:
                        scheme = Scheme.objects.filter(department=department, sector=sector).first()
                else:
                    scheme = Scheme.objects.filter(department=department).first()
        return scheme


class Scheme_log(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    scheme_id = IntegerField(db_index=True)

    dep_log = ForeignKey(Department_log, related_name='+', on_delete=PROTECT)
    level_log = ForeignKey(Level_log, null=True, related_name='+', on_delete=PROTECT)
    sector_log = ForeignKey(Sector_log, null=True, related_name='+', on_delete=PROTECT)

    name = CharField(max_length=50, null=True)
    fields = CharField(max_length=50, null=True)

    dep_mod = BooleanField(default=False)
    level_mod = BooleanField(default=False)
    sector_mod = BooleanField(default=False)
    name_mod = BooleanField(default=False)
    fields_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    @property
    def mode_str(self):
        return c.MODE_DICT.get(str(self.mode),'-')

    @property
    def dep_str(self):
        dep_abbrev = '-'
        dep = Department_log.objects.filter(id=self.dep_log.id).first()
        if dep is not None:
            dep_abbrev = dep.abbrev
        return dep_abbrev

    @property
    def level_str(self):
        # get level abbrev from Level_log
        level_abbrev = '-'
        level = Level_log.objects.filter(id=self.level_log.id).first()
        if level is not None:
            level_abbrev = level.abbrev + ' (' + str(level.id) + ')'
        return level_abbrev

    @property
    def sector_str(self):
        # get level abbrev from Level_log
        sector_abbrev = '-'
        sector = Sector_log.objects.filter(id=self.sector_log.id).first()
        if sector is not None:
            sector_abbrev = sector.abbrev + ' (' + str(sector.id) + ')'
        return sector_abbrev

# =============  Subject Model  =====================================
class Subjectbase(Model):
    objects = CustomManager()


class Subject(Model):  # PR1018-11-08
    # PR2018-06-05 Subject has one subject per examyear per country
    # Subject has no country field: country is a field in examyear

    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    # base and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Subjectbase, related_name='subjects', on_delete=PROTECT)
    examyear = ForeignKey(Examyear, related_name='subjects', on_delete=PROTECT)

    name = CharField(max_length=50, # PR2018-08-08 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('50')),)
    abbrev = CharField(max_length=10, # PR2018-08-08 set Unique per Examyear True. Was: unique=True,
        help_text=_('Required. {} characters or fewer.'.format('10')),)
    sequence = PositiveSmallIntegerField(default=9999,
        help_text=_('Sets subject sequence in reports. Required. Maximum value is {}.'.format(9999)),
        validators=[MaxValueValidator(9999),],
        error_messages={'max_value': _('Value must be less or equal to {}.'.format(9999))})
    depbase_list = CharField(max_length=20, null=True)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Subject, self).__init__(*args, **kwargs)

        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes
        self.original_name = self.name
        self.original_abbrev = self.abbrev
        self.original_sequence = self.sequence  # Was: = (None, self.sequence)[bool(self.sequence)]  # result = (on_false, on_true)[condition]
        self.original_depbase_list = self.depbase_list

        # PR2018-10-19 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        self.name_mod = False
        self.abbrev_mod = False
        self.sequence_mod = False
        self.depbase_list_mod = False

    def save(self, *args, **kwargs):  # called by subject.save(self.request) in SubjectEditView.form_valid
        self.request = kwargs.pop('request', None)

    # check if data has changed. If so: save object
        if self.data_has_changed():
            # First create base record. base.id is used in Department. Create also saves new record
            if not self.is_update:
                self.base = Subjectbase.objects.create()
            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Subject, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Subject, self).save
            self.save_to_log()

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(Subject, self).delete(*args, **kwargs)

    def save_to_log(self):  # PR2018-08-29
        # Create method also saves record
        Subject_log.objects.create(
            subject_id=self.id,  # self.id gets its value in super(Subject, self).save

            base=self.base,
            examyear=self.examyear,

            name=self.name,
            abbrev=self.abbrev,
            sequence=self.sequence,
            depbase_list=self.depbase_list,

            name_mod=self.name_mod,
            abbrev_mod=self.abbrev_mod,
            sequence_mod=self.sequence_mod,
            depbase_list_mod=self.depbase_list_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode = None):  # PR2018-07-21  PR2018-11-08
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        self.name_mod = self.original_name != self.name
        self.abbrev_mod = self.original_abbrev != self.abbrev
        self.sequence_mod = self.original_sequence != self.sequence
        self.depbase_list_mod = self.original_depbase_list != self.depbase_list

        data_changed_bool = (
            not self.is_update or
            self.name_mod or
            self.abbrev_mod or
            self.sequence_mod or
            self.depbase_list_mod
        )
        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        return data_changed_bool

    @property  # PR2018-07-19
    def has_no_linked_data(self):
        # TODO find records in linked tables
        linked_items_count = False  # Subject.objects.filter(subject_id=self.pk).count()
        # logger.debug('SubjectDefault Model has_no_linked_data linked_items_count: ' + str(linked_items_count))
        return not bool(linked_items_count)

    @property
    def depbase_list_str(self): # PR108-08-27 PR2018-11-06
        return Department.depbase_list_str(depbase_list=self.depbase_list, examyear=self.examyear)

    @property
    def depbase_list_tuple(self):
        # TODO: check if this prop is in use
        # dep_list_tuple is called bij LevelEditForm, SectorEditForm, SchemeEditForm, SubjectdefaultEditForm
        return get_depbase_list_tuple(self.depbase_list)

#  ++++++++++  Class methods  +++++++++++++++++++++++++++
    @classmethod
    def get_subj_list(cls, department):  # PR2019-01-18
        depbase_id_str = ';' + str(department.base.id) + ';'
        subjects = cls.objects.filter(examyear=department.examyear, depbase_list__contains=depbase_id_str).all()
        subject_list = []
        for subject in subjects:
            subject_list.append({
                'subj_id': str(subject.id),
                'subj_name': subject.name,
                'subj_abbr': subject.abbrev,
                'subj_sequ': subject.sequence
            })
        return subject_list


# PR2018-06-05 Subject is the base Model of all subjects
class Subject_log(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    subject_id = IntegerField(db_index=True)

    base = ForeignKey(Subjectbase, related_name='+', on_delete=PROTECT)
    # TODO: refer to log table
    examyear = ForeignKey(Examyear, related_name='+', on_delete=PROTECT)

    name = CharField(max_length=50, null=True)
    abbrev = CharField(max_length=10, null=True)
    sequence = PositiveSmallIntegerField(null=True)
    depbase_list = CharField(max_length=20, null=True)

    name_mod = BooleanField(default=False)
    abbrev_mod = BooleanField(default=False)
    sequence_mod = BooleanField(default=False)
    depbase_list_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    @property
    def depbase_list_str(self): # PR2018-11-04
        return Department.depbase_list_str(self.depbase_list, self.examyear)

    @property
    def mode_str(self):
        return c.MODE_DICT.get(str(self.mode),'-')


# PR2018-06-06
class Package(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    school = ForeignKey(School, related_name='packages', on_delete=PROTECT)
    scheme = ForeignKey(Scheme, related_name='packages', on_delete=PROTECT)

    name = CharField(max_length=50)
    abbrev = CharField(max_length=20)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __str__(self):
        return self.abbrev


# PR2018-06-06
class Package_log(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    package_id = IntegerField(db_index=True)

    name = CharField(max_length=50, null=True)
    abbrev = CharField(max_length=20, null=True)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()


# PR2018-06-05
class Schemeitem(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    scheme = ForeignKey(Scheme, related_name='schemeitems', on_delete=PROTECT)
    subject = ForeignKey(Subject, related_name='schemeitems', on_delete=PROTECT)
    subjecttype = ForeignKey(Subjecttype, related_name='schemeitems', on_delete=PROTECT)

    gradetype = PositiveSmallIntegerField(default=0, choices = c.GRADETYPE_CHOICES)
    weightSE = PositiveSmallIntegerField(default=0)
    weightCE = PositiveSmallIntegerField(default=0)

    is_mandatory = BooleanField(default=False)
    is_combi = BooleanField(default=False)
    extra_count_allowed = BooleanField(default=False)
    extra_nocount_allowed = BooleanField(default=False)
    choicecombi_allowed = BooleanField(default=False)
    has_practexam = BooleanField(default=False)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __init__(self, *args, **kwargs):
        super(Schemeitem, self).__init__(*args, **kwargs)
        try:
            self.original_scheme = self.scheme
            self.original_subject = self.subject
            self.original_subjecttype = self.subjecttype
        except:
            self.original_scheme = None
            self.original_subject = None
            self.original_subjecttype = None

        self.original_gradetype = self.gradetype
        self.original_weightSE = self.weightSE
        self.original_weightCE = self.weightCE

        self.original_is_mandatory = self.is_mandatory
        self.original_is_combi = self.is_combi

        self.original_extra_count_allowed = self.extra_count_allowed
        self.original_extra_nocount_allowed = self.extra_nocount_allowed
        self.original_choicecombi_allowed = self.choicecombi_allowed
        self.original_has_practexam = self.has_practexam

        # PR2018-10-19 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        self.scheme_mod = False
        self.subject_mod = False
        self.subjecttype_mod = False

        self.gradetype_mod = False
        self.weightSE_mod = False
        self.weightCE_mod = False

        self.is_mandatory_mod = False
        self.is_combi_mod = False
        self.extra_count_allowed_mod = False
        self.extra_nocount_allowed_mod = False
        self.choicecombi_allowed_mod = False
        self.has_practexam_mod = False

    def save(self, *args, **kwargs):  # called by subjectdefault.save(self.request) in SubjectdefaultEditView.form_valid
        self.request = kwargs.pop('request', None)
        if self.data_has_changed():
            super(Schemeitem, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            self.save_to_log()

    def delete(self, *args, **kwargs):
        logger.debug("Schemeitem delete kwargs: " + str(kwargs) + str(type(kwargs)))
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(Schemeitem, self).delete(*args, **kwargs)

    def save_to_log(self):  # PR2018-08-27
        # PR2018-10-28 debug: 'NoneType' object has no attribute 'id'
        logger.debug("----- Schemeitem save_to_log")
        # get latest Scheme_log row that corresponds with self.scheme
        scheme_log = None
        if self.scheme is not None:
            scheme_log = Scheme_log.objects.filter(scheme_id=self.scheme.id).order_by('-id').first()

        # get latest Subject_log row that corresponds with self.subject
        subject_log = None
        if self.subject is not None:
            subject_log = Subject_log.objects.filter(subject_id=self.subject.id).order_by('-id').first()

        # get latest Subjecttype_log row that corresponds with self.subjecttype
        subjecttype_log = None
        if self.subjecttype is not None:
            subjecttype_log = Subjecttype_log.objects.filter(subjecttype_id=self.subjecttype.id).order_by('-id').first()

        # Create method also saves record
        Schemeitem_log.objects.create(
            schemeitem_id=self.id,  # self.id gets its value in super(Level, self).save

            scheme_log=scheme_log,
            subject_log=subject_log,
            subjecttype_log=subjecttype_log,

            gradetype=self.gradetype,
            weightSE=self.weightSE,
            weightCE=self.weightCE,

            is_mandatory=self.is_mandatory,
            is_combi=self.is_combi,

            extra_count_allowed=self.extra_count_allowed,
            extra_nocount_allowed=self.extra_nocount_allowed,
            choicecombi_allowed=self.choicecombi_allowed,
            has_practexam=self.has_practexam,

            scheme_mod=self.scheme_mod,
            subject_mod=self.subject_mod,
            subjecttype_mod=self.subjecttype_mod,

            gradetype_mod=self.gradetype_mod,
            weightSE_mod=self.weightSE_mod,
            weightCE_mod=self.weightCE_mod,

            is_mandatory_mod=self.is_mandatory_mod,
            is_combi_mod=self.is_combi_mod,

            extra_count_allowed_mod=self.extra_count_allowed_mod,
            extra_nocount_allowed_mod=self.extra_nocount_allowed_mod,
            choicecombi_allowed_mod=self.choicecombi_allowed_mod,
            has_practexam_mod=self.has_practexam_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode = None):  # PR2018-11-10
        # returns True when the value of one or more fields has changed
        self.is_update = self.id is not None  # self.id is None before new record is saved

        self.scheme_mod = self.original_scheme != self.scheme
        self.subject_mod = self.original_subject != self.subject
        self.subjecttype_mod = self.original_subjecttype != self.subjecttype

        self.gradetype_mod = self.original_gradetype != self.gradetype
        self.weightSE_mod = self.original_weightSE != self.weightSE
        self.weightCE_mod = self.original_weightCE != self.weightCE

        self.is_mandatory_mod = self.original_is_mandatory != self.is_mandatory
        self.is_combi_mod = self.original_is_combi != self.is_combi


        self.extra_count_allowed_mod = self.original_extra_count_allowed != self.extra_count_allowed
        self.extra_nocount_allowed_mod = self.original_extra_nocount_allowed != self.extra_nocount_allowed
        self.choicecombi_allowed_mod = self.original_choicecombi_allowed != self.choicecombi_allowed
        self.has_practexam_mod = self.original_has_practexam != self.has_practexam

        data_changed_bool = (
            not self.is_update or
            self.scheme_mod or
            self.subjecttype_mod or

            self.gradetype_mod or
            self.weightSE_mod or
            self.weightCE_mod or

            self.is_mandatory_mod or
            self.is_combi_mod or

            self.extra_count_allowed_mod or
            self.extra_nocount_allowed_mod or
            self.choicecombi_allowed_mod or
            self.has_practexam_mod
        )

        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        return data_changed_bool

    @property
    def gradetype_str(self): # PR2018-11-11
        return c.GRADETYPE_ABBREV[self.gradetype]

    @property
    def is_mandatory_str(self): # PR2018-11-11
        return c.YES_NO_BOOL_DICT[self.is_mandatory]
    @property
    def is_combi_str(self): # PR2018-11-11
        return c.YES_NO_BOOL_DICT[self.is_combi]

    @property
    def extra_count_allowed_str(self): # PR2019-02-11
        return c.YES_NO_BOOL_DICT[self.extra_count_allowed]
    @property
    def extra_nocount_allowed_str(self): # PR2019-02-11
        return c.YES_NO_BOOL_DICT[self.extra_nocount_allowed]

    @property
    def choicecombi_allowed_str(self): # PR2018-11-11
        return c.YES_NO_BOOL_DICT[self.choicecombi_allowed]

    @property
    def has_practexam_str(self):
        return c.YES_NO_BOOL_DICT.get(self.has_practexam)



#  ++++++++++  Class methods  +++++++++++++++++++++++++++
    @classmethod
    def get_schemeitem_list(cls, scheme):  # PR2019-01-18
        # logger.debug('------------- get_schemeitem_list -------------> ' + str(scheme))
        schemeitems = cls.objects.filter(scheme=scheme).order_by('subject__sequence', 'subjecttype__sequence').all()
        # logger.debug(schemeitems)
        schemeitem_list = []
        for item in schemeitems:
            sequence = item.subject.sequence * 1000 + item.subjecttype.sequence
            schemeitem_list.append({
                'mode': '-',
                'ssi_id': item.id,
                'scm_id': item.scheme.id,
                'subj_id': item.subject.id,
                'sjtp_id': item.subjecttype.id,
                'grtp_id': item.gradetype,
                'wtse': item.weightSE,
                'wtce': item.weightCE,
                'mand': (0, 1)[item.is_mandatory],
                'comb': (0, 1)[item.is_combi],
                'exal': (0, 1)[item.extra_count_allowed],
                'exna': (0, 1)[item.extra_nocount_allowed],
                'chal': (0, 1)[item.choicecombi_allowed],
                'prac': (0, 1)[item.has_practexam],
                'subj_name': item.subject.name,
                'subj_sequ': item.subject.sequence,
                'sjtp_name': item.subjecttype.abbrev,
                'sjtp_pws': (0, 1)[item.subjecttype.has_pws],
                'sjtp_one': (0, 1)[item.subjecttype.one_allowed],
                'sequence': sequence
            })


        return schemeitem_list




# PR2018-06-08
class Schemeitem_log(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    schemeitem_id = IntegerField(db_index=True)

    scheme_log = ForeignKey(Scheme_log, null=True, related_name='+', on_delete=PROTECT)
    subject_log = ForeignKey(Subject_log, null=True, related_name='+', on_delete=PROTECT)
    subjecttype_log = ForeignKey(Subjecttype_log,null=True,  related_name='+', on_delete=PROTECT)

    gradetype = PositiveSmallIntegerField(null=True)
    weightSE = PositiveSmallIntegerField(null=True)
    weightCE = PositiveSmallIntegerField(null=True)

    is_mandatory = BooleanField(default=False)
    is_combination = BooleanField(default=False)
    is_combi = BooleanField(default=False)

    extra_count_allowed = BooleanField(default=False)
    extra_nocount_allowed = BooleanField(default=False)
    choicecombi_allowed = BooleanField(default=False)
    has_practexam = BooleanField(default=False)

    scheme_mod =  BooleanField(default=False)
    subject_mod =  BooleanField(default=False)
    subjecttype_mod = BooleanField(default=False)

    gradetype_mod =  BooleanField(default=False)
    weightSE_mod =  BooleanField(default=False)
    weightCE_mod =  BooleanField(default=False)

    is_mandatory_mod =  BooleanField(default=False)
    is_combi_mod =  BooleanField(default=False)

    extra_count_allowed_mod =  BooleanField(default=False)
    extra_nocount_allowed_mod =  BooleanField(default=False)
    choicecombi_allowed_mod =  BooleanField(default=False)
    has_practexam_mod =  BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()


# PR2018-08-23
class Norm(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    scheme = ForeignKey(Scheme, related_name='norms', on_delete=PROTECT)
    subject = ForeignKey(Subject, related_name='norms', on_delete=PROTECT)

    is_etenorm = BooleanField(default=False)
    is_primarynorm = BooleanField(default=False)
    scalelength_ce = CharField(max_length=10, null=True)
    norm_ce = CharField(max_length=10, null=True)
    scalelength_reex = CharField(max_length=10, null=True)
    norm_reex = CharField(max_length=10, null=True)
    scalelength_practex = CharField(max_length=10, null=True)
    norm_practex = CharField(max_length=10, null=True)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __str__(self):
        subjectscheme_str = ''
        if self.subject:
            subjectscheme_str = self.subject
        if self.scheme:
            subjectscheme_str = subjectscheme_str + '-' + self.scheme
        return subjectscheme_str


# PR2018-08-23
class Norm_log(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    norm_id = IntegerField(db_index=True)

    # TODO: refer to log table
    scheme = ForeignKey(Scheme, null=True, related_name='+', on_delete=PROTECT)
    subject = ForeignKey(Subject, null=True, related_name='+', on_delete=PROTECT)

    is_etenorm = BooleanField(default=False)
    is_primarynorm = BooleanField(default=False)
    scalelength_ce = CharField(max_length=10, null=True)
    norm_ce = CharField(max_length=10, null=True)
    scalelength_reex = CharField(max_length=10, null=True)
    norm_reex = CharField(max_length=10, null=True)
    scalelength_practex = CharField(max_length=10, null=True)
    norm_practex = CharField(max_length=10, null=True)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()


# PR2018-06-06
class Package_item(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    package = ForeignKey(Package, related_name='packageschemes', on_delete=PROTECT)
    scheme_item = ForeignKey(Schemeitem, related_name='packageschemes', on_delete=PROTECT)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __str__(self):
        name = ''
        if self.package:
            name = str(self.package)
        if self.scheme_item:
            name = name + '-' + str(self.scheme_item)
        return name


# PR2018-06-06
class Package_item_log(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    package_item_id = IntegerField(db_index=True)
    # TODO: refer to log table
    package = ForeignKey(Package, null=True, related_name='+', on_delete=PROTECT)
    scheme_item = ForeignKey(Schemeitem, null=True, related_name='+', on_delete=PROTECT)
    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()


# PR2018-06-06
class Cluster(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    school = ForeignKey(School, related_name='clusters', on_delete=PROTECT)
    subject = ForeignKey(Subject, related_name='clusters', on_delete=PROTECT)

    name = CharField(max_length=50)
    abbrev = CharField(max_length=20)
    depbase_list = CharField(max_length=20, null=True)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __str__(self):
        return self.abbrev

# PR2018-06-06
class Cluster_log(Model):
    # CustomManager adds function get_or_none. Used in  Subjectdefault to prevent DoesNotExist exception
    objects = CustomManager()

    cluster_id = IntegerField(db_index=True)

    # TODO: refer to log table
    school = ForeignKey(School, related_name='+', on_delete=PROTECT)
    subject = ForeignKey(Subject, null=True, related_name='+', on_delete=PROTECT)

    name = CharField(max_length=50, null=True)
    abbrev = CharField(max_length=20, null=True)
    depbase_list = CharField(max_length=20, null=True)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __str__(self):
        return self.abbrev

# +++++++++++++++++++++   Functions Department, Level, Sector, Subject  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def get_depbase_list_tuple(depbase_list):
    # PR2018-08-28 depbase_list_tuple converts self.depbase_list string into tuple,
    # This function converts init_list_str string into init_list_tuple,  e.g.: '1;2' will be converted to (1,2)
    # e.g.: depbase_list='1;2' will be converted to depbase_list=(1,2)
    # empty list = (0,), e.g: 'None'

    depbase_list_tuple = ()
    if depbase_list:
        depbase_list_str = str(depbase_list)
        depbase_list_list = depbase_list_str.split(';')
        depbase_list_tuple = tuple(depbase_list_list)

    # select 0 (None) in EditForm when no other departments are selected
    if not depbase_list_tuple:
        depbase_list_tuple = (0,)

    return depbase_list_tuple


def get_list_str(list, model):
    # PR2018-08-16 get_list_str displays string of depbase_list, level_list or sector_list. e.g.: Vsbo, Havo, Vwo'
    _list_str = '-'
    # logger.debug('def get_list_str list: <' + str(list) + '> type: <' + str(type(list)) + '>')
    if list:
        _list_split = list.split(';')
        if bool(_list_split):
            for _id_str in _list_split:
                if _id_str:
                    _field = ''
                    try:
                        _id_int = int(_id_str)
                        # logger.debug('def get_list_str _id_int: ' + str(_id_int) + '> type: <' + str(type(_id_int)) + '>')
                        # skip value 0 (None)
                        if _id_int:
                            # logger.debug('def get_list_str _id_int: ' + str(_id_int))
                            if model =='Department':
                                _instance = Department.objects.filter(pk=_id_int).first()
                                _field = _instance.shortname
                            elif model == 'Level':
                                _instance = Level.objects.filter(pk=_id_int).first()
                                _field = _instance.abbrev
                            elif model == 'Sector':
                                _instance = Sector.objects.filter(pk=_id_int).first()
                                _field = _instance.abbrev
                    except:
                        _field = ''
                    if _field:
                        _list_str = _list_str + ', ' + _field
            if _list_str: # means: if not _list_str == '':
                # slice off first 2 characters: ', '
                _list_str = _list_str[2:]
    # logger.debug('def get_list_str _list_str: <' + str(_list_str) + '>')
    return _list_str


def get_list_tupleXXX(list_str):
    # PR2018-08-23 get_list_tuple converts list_str string into tuple,
    # e.g.: level_list='1;2' will be converted to _list_tuple=(1,2)
    # empty list = None. Was: empty list = (0,), e.g: 'None'
    if list_str:
        # logger.debug('get_list_tuple list_str=<' + str(list_str) + '> type: ' + str(type(list_str)))
        try:
            _list_split = list_str.split(';')
            # logger.debug('get_list_tuple _list_split=<' + str(_list_split) + '>')
            _list_tuple = tuple(_list_split)
            # logger.debug('get_list_tuple _list_tuple=<' + str(_list_tuple) + '>')
        except:
            _list_tuple = ('0',)
        if not bool(_list_tuple):
            # _list_tuple = ('0',)
            _list_tuple = None
    else:
        # _list_tuple = ('0',)
        _list_tuple = None
    # logger.debug('get_list_tuple _list_tuple=#' + str(_list_tuple) + '#')
    return _list_tuple

