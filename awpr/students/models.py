# PR2018-07-20
from django.db.models import Model, Manager, ForeignKey, OneToOneField, PROTECT, CASCADE
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, DecimalField, BooleanField, DateField, DateTimeField

from django.db.models.functions import Lower

from django.utils import timezone

# PR2018-05-05 use AUTH_USER_MODEL
#from django.contrib.auth.models import User
#from accounts.models import User
from django.utils.translation import ugettext_lazy as _
from awpr.settings import AUTH_USER_MODEL
from awpr import constants as c
from awpr import functions as f

from schools.models import Examyear, Department, Department_log, School, School_log
from subjects.models import Level, Level_log, Sector, Sector_log, Scheme, Scheme_log, Schemeitem, Package, Package_log, Cluster

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

# === Birthcountry =====================================
class Birthcountry(Model):
    # PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
    objects = CustomManager()

    name = CharField(max_length=50, unique=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Birthcountry, self).__init__(*args, **kwargs)
        self.original_name = self.name

    def save(self, *args, **kwargs):
        logger.debug('Birthcountry(Model) save kwargs: ' + str(kwargs))
        self.request = kwargs.pop('request', None)
        # logger.debug('Birthcountry(Model) save self.request.user: ' + str(self.request.user))
        if self.data_has_changed():
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]
            super(Birthcountry, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            self.save_to_log()

    def delete(self, *args, **kwargs):
        self.modified_at = timezone.now()
        self.mode = 'd'
        self.data_has_changed()
        # First save to logfile
        self.save_to_log()
        # then delete record
        super(Birthcountry, self).delete(*args, **kwargs)

    def save_to_log(self):
        Birthcountry_log.objects.create(
            birthcountry_id=self.id,
            name=self.name,
            name_mod=self.name_mod,
            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self):  # PR2018-08-31
        self.is_update = self.id is not None # self.id is None before new record is saved
        self.name_mod = self.original_name != self.name
        return not self.is_update or \
               self.name_mod

# PR2018-05-05
class Birthcountry_log(Model):
    objects = CustomManager()

    birthcountry_id = IntegerField(db_index=True)
    name = CharField(max_length=50, null=True)
    name_mod = BooleanField(default=False)
    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __str__(self):
        return self.name

    @property
    def mode_str(self):
        mode_str = '-'
        if self.mode is not None:
            mode_str = c.MODE_DICT.get(str(self.mode))
        return mode_str


# === Birthcity =====================================
class Birthcity(Model):
    objects = CustomManager()

    birthcountry = ForeignKey(Birthcountry, related_name='birthcities', on_delete=PROTECT)
    name = CharField(max_length=50, unique=False)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Birthcity, self).__init__(*args, **kwargs)
        self.original_name = self.name

    def save(self, *args, **kwargs):
        logger.debug('Birthcity(Model) save kwargs: ' + str(kwargs) + ' Type: ' + str(type(kwargs)))
        self.request = kwargs.pop('request', None)
        if self.data_has_changed():
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]
            super(Birthcity, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            self.save_to_log()

    def delete(self, *args, **kwargs):

        self.modified_at = timezone.now()
        self.mode = 'd'
        self.data_has_changed()
        # First save to logfile
        self.save_to_log()
        # then delete record
        super(Birthcity, self).delete(*args, **kwargs)

    def save_to_log(self):
        Birthcity_log.objects.create(
            birthcity_id=self.id,
            name=self.name,
            name_mod=self.name_mod,
            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self):  # PR2018-08-31
        self.is_update = self.id is not None # self.id is None before new record is saved
        self.name_mod = self.original_name != self.name

        logger.debug('Birthcity(Model) data_has_changed self.is_update: ' + str(self.is_update) + ' Type: ' + str(type(self.is_update)))
        logger.debug('Birthcity(Model) data_has_changed self.name: ' + str(self.name) + ' Type: ' + str(type(self.name)))
        logger.debug('Birthcity(Model) data_has_changed self.name_mod: ' + str(self.name_mod) + ' Type: ' + str(type(self.name_mod)))

        return not self.is_update or \
               self.name_mod


# PR2018-05-05
class Birthcity_log(Model):
    objects = CustomManager()

    birthcity_id = IntegerField(db_index=True)
    name = CharField(max_length=50, null=True)
    name_mod = BooleanField(default=False)
    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __str__(self):
        return self.name

    @property
    def mode_str(self):
        mode_str = '-'
        if self.mode is not None:
            mode_str = c.MODE_DICT.get(str(self.mode))
        return mode_str


# =================
class Studentbase(Model):# PR2018-10-17
    objects = CustomManager()

class Student(Model):# PR2018-06-06, 2018-09-05
    objects = CustomManager()

    base = ForeignKey(Studentbase, related_name='students', on_delete=PROTECT)
    school = ForeignKey(School, related_name='students', on_delete=PROTECT)

    department = ForeignKey(Department, related_name='students', on_delete=PROTECT)
    level = ForeignKey(Level, null=True, blank=True, related_name='students', on_delete=PROTECT)
    sector = ForeignKey(Sector, null=True,blank=True, related_name='students', on_delete=PROTECT)
    scheme = ForeignKey(Scheme, null=True, blank=True, related_name='students', on_delete=PROTECT)
    package = ForeignKey(Package, null=True, blank=True, related_name='students', on_delete=PROTECT)

    lastname = CharField(db_index=True, max_length=80)
    firstname= CharField(db_index=True, max_length=80)
    prefix= CharField(max_length=10, null=True, blank=True)
    gender= CharField(db_index=True, max_length=1, choices=c.GENDER_CHOICES, default=c.GENDER_NONE)
    idnumber= CharField(db_index=True, max_length=20)
    birthdate= DateField(null=True, blank=True)

    birthcountry= CharField(max_length=50, null=True, blank=True)
    birthcity= CharField( max_length=50, null=True, blank=True)
    # birthcountry = ForeignKey(Birthcountry, null=True, blank=True, related_name='students', on_delete=PROTECT)
    # birthcity = ForeignKey(Birthcity, null=True, blank=True, related_name='students', on_delete=PROTECT)

    classname = CharField(db_index=True, max_length=20, null=True, blank=True)
    examnumber = CharField(db_index=True, max_length=20, null=True, blank=True)
    regnumber = CharField(db_index=True, max_length=20, null=True, blank=True)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    class Meta:
        ordering = [Lower('lastname'), Lower('firstname')]

    def __str__(self):
        _lastname = self.lastname
        _firstname = self.firstname
        _fullname = _lastname + ', ' + _firstname
        return _fullname

    def __init__(self, *args, **kwargs):
        super(Student, self).__init__(*args, **kwargs)
        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes
        try:
            self.original_school = self.school
        except:
            self.original_school = None
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
        try:
            self.original_scheme = self.scheme
        except:
            self.original_scheme = None
        try:
            self.original_package = self.package
        except:
            self.original_package = None

        self.original_lastname = self.lastname
        self.original_firstname = self.firstname
        self.original_prefix = self.prefix
        self.original_gender = self.gender
        self.original_idnumber = self.idnumber
        self.original_birthdate = self.birthdate
        self.original_birthcountry = self.birthcountry
        self.original_birthcity = self.birthcity
        self.original_classname = self.classname
        self.original_examnumber = self.examnumber
        self.original_regnumber = self.regnumber

        # PR2018-10-19 initialize here, otherwise delete gives error: object has no attribute 'name_mod'

        self.dep_mod = False
        self.level_mod = False
        self.sector_mod = False
        self.scheme_mod = False
        self.package_mod = False
        self.lastname_mod = False
        self.firstname_mod = False
        self.prefix_mod = False
        self.gender_mod = False
        self.idnumber_mod = False
        self.birthdate_mod = False
        self.birthcountry_mod = False
        self.birthcity_mod = False
        self.classname_mod = False
        self.examnumber_mod = False
        self.regnumber_mod = False

    def save(self, *args, **kwargs):  # called by subjectdefault.save(self.request) in SubjectdefaultEditView.form_valid
        self.request = kwargs.pop('request', None)

    # check if data has changed. If so: save object
        if self.data_has_changed():
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        # When new record:First create base record. base.id is used in Student. Create also saves new record
            if not self.is_update:
                self.base = Studentbase.objects.create()

                logger.debug('Student Model self.base: ' + str(self.base.id) + '> type: ' + str(type(self.base.id)))
            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Student, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            self.save_to_log()

            logger.debug('Student Model self: ' + str(self) + '> type: ' + str(type(self)))

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(Student, self).delete(*args, **kwargs)

    def save_to_log(self):
        # PR2018-11-19

        # get latest School_log row that corresponds with self.school
        school_log = None
        if self.school is not None:
            school_log = School_log.objects.filter(school_id=self.school.id).order_by('-id').first()

        # get latest Department_log row that corresponds with self.department
        dep_log = None
        if self.department is not None:
            dep_log = Department_log.objects.filter(department_id=self.department.id).order_by('-id').first()

        # get latest Level_log row that corresponds with self.level
        level_log = None
        if self.level is not None:
            level_log = Level_log.objects.filter(level_id=self.level.id).order_by('-id').first()

        # get latest Sector_log row that corresponds with self.sector
        sector_log = None
        if self.sector is not None:
            sector_log = Sector_log.objects.filter(sector_id=self.sector.id).order_by('-id').first()

        # get latest Scheme_log row that corresponds with self.scheme
        scheme_log = None
        if self.scheme is not None:
            scheme_log = Scheme_log.objects.filter(scheme_id=self.scheme.id).order_by('-id').first()

        # get latest Package_log row that corresponds with self.package
        package_log = None
        if self.package is not None:
            package_log = Package_log.objects.filter(package_id=self.package.id).order_by('-id').first()

        # Create method also saves record
        Student_log.objects.create(
            student_id=self.id, # self.id gets its value in super(School, self).save

            # # #
            base=self.base,
            school_log = school_log,
            dep_log = dep_log,
            level_log=level_log,
            sector_log = sector_log,
            scheme_log = scheme_log,
            package_log = package_log,

            lastname=self.lastname,
            firstname=self.firstname,
            prefix=self.prefix,
            gender=self.gender,
            idnumber=self.idnumber,
            birthdate=self.birthdate,
            birthcountry=self.birthcountry,
            birthcity=self.birthcity,
            classname=self.classname,
            examnumber=self.examnumber,
            regnumber=self.regnumber,

            dep_mod=self.dep_mod,
            level_mod=self.level_mod,
            sector_mod=self.sector_mod,
            scheme_mod=self.scheme_mod,
            package_mod=self.package_mod,

            lastname_mod = self.lastname_mod,
            firstname_mod = self.firstname_mod,
            prefix_mod = self.prefix_mod,
            gender_mod = self.gender_mod,
            idnumber_mod = self.idnumber_mod,
            birthdate_mod = self.birthdate_mod,
            birthcountry_mod = self.birthcountry_mod,
            birthcity_mod = self.birthcity_mod,
            classname_mod = self.classname_mod,
            examnumber_mod = self.examnumber_mod,
            regnumber_mod = self.regnumber_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode=None):  # PR2018-11-20
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        self.school_mod = self.original_school != self.school
        self.dep_mod = self.original_department != self.department
        self.level_mod = self.original_level != self.level
        self.sector_mod = self.original_sector != self.sector
        self.scheme_mod = self.original_scheme != self.scheme
        self.package_mod = self.original_package != self.package

        self.lastname_mod = self.original_lastname != self.lastname
        self.firstname_mod = self.original_firstname != self.firstname
        self.prefix_mod = self.original_prefix != self.prefix
        self.gender_mod = self.original_gender != self.gender
        self.idnumber_mod = self.original_idnumber != self.idnumber
        self.birthdate_mod = self.original_birthdate != self.birthdate
        self.birthcountry_mod = self.original_birthcountry != self.birthcountry
        self.birthcity_mod = self.original_birthcity != self.birthcity
        self.classname_mod = self.original_classname != self.classname
        self.examnumber_mod = self.original_examnumber != self.examnumber
        self.regnumber_mod = self.original_regnumber != self.regnumber

        data_changed_bool = (
                not self.is_update or
                self.school_mod or
                self.dep_mod or
                self.scheme_mod or
                self.package_mod or
                self.lastname_mod or
                self.firstname_mod or
                self.prefix_mod or
                self.gender_mod or
                self.idnumber_mod or
                self.birthdate_mod or
                self.birthcountry_mod or
                self.birthcity_mod or
                self.classname_mod or
                self.examnumber_mod or
                self.regnumber_mod
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
    def full_name(self):
        full_name = str(self.lastname)
        full_name = full_name.strip()  # Trim
        if self.prefix: # put prefix at the front
            # PR2019-01-13 is str() necessary?. Was:
            # prefix_str = str(self.prefix)
            # full_name = prefix_str .strip() + ' ' + full_name
            full_name = self.prefix .strip() + ' ' + full_name
        if self.firstname:
            # PR2019-01-13 is str() necessary?. Was:
            # firstname_str = str(self.firstname)
            # full_name = firstname_str.strip() + ' ' + full_name
            full_name = self.firstname.strip() + ' ' + full_name
        return full_name

    @property
    def lastname_firstname_initials(self):
        lastname_str = str(self.lastname)
        full_name = lastname_str.strip()
        firstnames = ''
        if self.firstname:
            firstnames_str = str(self.firstname)
            firstnames_arr = firstnames_str.split()
            if len(firstnames_arr) == 0:
                firstnames = firstnames_str.strip()  # 'PR 13 apr 13 Trim toegevoegd
            else:
                skip = False
                for item in firstnames_arr:
                    if not skip:
                        firstnames = firstnames + item + " " # write first firstname in full
                        skip = True
                    else:
                        if item:
                            #PR2017-02-18 VB debug. bij dubbele spatie in voornaam krijg je lege err(x)
                            firstnames = firstnames + item[:1] + ' ' # write of the next firstnames only the first letter
        if firstnames:
            full_name = full_name + ', ' + firstnames
        if self.prefix: # put prefix at the end
            prefix = str(self.prefix)
            full_name = full_name + ' ' + prefix.strip()
        full_name = full_name.strip()
        return full_name

    @property
    def birthcountry_str(self):  # PR2018-05-18 calculates schoolyear from this_examyear
        value = ''
        if self.birthcountry:
            value = self.birthcountry
        return value

    @property
    def birthcity_str(self):  # PR2018-05-18 calculates schoolyear from this_examyear
        value = ''
        if self.birthcity:
            value = self.birthcity
        return value

    @property
    def has_no_linked_data(self):  # PR2018-11-20
        # TODO add search for linked data
        return True


    @classmethod
    def fieldlist(cls):
        return ["idnumber", "examnumber",
            "lastname", "firstname", "prefix", "gender",
            "birthdate", "birthcountry", "birthcity",
            "dep", "level",  "sector", "classname"]



# PR2018-06-08
class Student_log(Model):
    objects = CustomManager()

    student_id = IntegerField(db_index=True)

# # #
    base = ForeignKey(Studentbase, related_name='+', on_delete=PROTECT)

    school_log = ForeignKey(School_log, related_name='+', on_delete=PROTECT)
    dep_log = ForeignKey(Department_log, related_name='+', on_delete=PROTECT)
    level_log = ForeignKey(Level_log, null=True, related_name='+', on_delete=PROTECT)
    sector_log = ForeignKey(Sector_log, null=True, related_name='+', on_delete=PROTECT)
    scheme_log = ForeignKey(Scheme_log, null=True, related_name='+', on_delete=PROTECT)
    package_log = ForeignKey(Package_log, null=True, related_name='+', on_delete=PROTECT)

    lastname = CharField(db_index=True, max_length=80)
    firstname = CharField(db_index=True, max_length=80)
    prefix = CharField(max_length=10, null=True, blank=True)
    gender = CharField(db_index=True, max_length=1, choices=c.GENDER_CHOICES, default=c.GENDER_NONE)
    idnumber = CharField(db_index=True, max_length=20)
    birthdate = DateField(null=True)

    birthcountry = CharField(max_length=50, null=True)
    birthcity = CharField(max_length=50, null=True)
    # birthcountry = ForeignKey(Birthcountry, null=True, blank=True, related_name='students', on_delete=PROTECT)
    # birthcity = ForeignKey(Birthcity, null=True, blank=True, related_name='students', on_delete=PROTECT)

    classname = CharField(db_index=True, max_length=20, null=True, blank=True)
    examnumber = CharField(db_index=True, max_length=20, null=True, blank=True)
    regnumber = CharField(db_index=True, max_length=20, null=True, blank=True)

    school_mod = BooleanField(default=False)
    dep_mod = BooleanField(default=False)
    level_mod = BooleanField(default=False)
    sector_mod = BooleanField(default=False)
    scheme_mod = BooleanField(default=False)
    package_mod = BooleanField(default=False)

    lastname_mod = BooleanField(default=False)
    firstname_mod = BooleanField(default=False)
    prefix_mod = BooleanField(default=False)
    gender_mod = BooleanField(default=False)
    idnumber_mod = BooleanField(default=False)
    birthdate_mod = BooleanField(default=False)

    birthcountry_mod = BooleanField(default=False)
    birthcity_mod = BooleanField(default=False)
    # birthcountry = ForeignKey(Birthcountry, null=True, blank=True, related_name='students', on_delete=PROTECT)
    # birthcity = ForeignKey(Birthcity, null=True, blank=True, related_name='students', on_delete=PROTECT)

    classname_mod = BooleanField(default=False)
    examnumber_mod = BooleanField(default=False)
    regnumber_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    @property
    def mode_str(self):
        return c.get_mode_str(self)

##########################################################################

# ====Studentresult=============
class Studentresult(Model):# PR2018-11-10
    objects = CustomManager()
    # TODO 2019-01-13: make table with row per tv, set realtion one-to-many
    student = OneToOneField(Student, related_name='studentresult', on_delete=CASCADE)

    diplomanumber = CharField(db_index=True, max_length=10, null=True, blank=True)
    gradelistnumber = CharField(db_index=True, max_length=10, null=True, blank=True)
    locked =  BooleanField(default=False)
    has_reex2= BooleanField(default=False)
    has_reex3= BooleanField(default=False)
    is_withdrawn = BooleanField(default=False)

    # # # fields ce/combi avg 6 fields
    grade_ce_avg_tv01 = DecimalField(max_digits=5, decimal_places=2, default = 0)
    grade_ce_avg_tv02 = DecimalField(max_digits=5, decimal_places=2, default = 0)
    grade_ce_avg_tv03 = DecimalField(max_digits=5, decimal_places=2, default = 0)
    grade_ce_avg_final = DecimalField(max_digits=5, decimal_places=2, default = 0)
    grade_ce_avg_text = CharField(db_index=True, max_length=10, null=True, blank=True)
    grade_combi_avg_text = CharField(db_index=True, max_length=10, null=True, blank=True)

    # # # fields endgrade sum/avg/count - 8 fields
    endgrade_sum_tv01 = PositiveSmallIntegerField(default=0)
    endgrade_sum_tv02 = PositiveSmallIntegerField(default=0)
    endgrade_sum_tv03 = PositiveSmallIntegerField(default=0)
    endgrade_count = PositiveSmallIntegerField(default=0)
    endgrade_avg_tv01 = CharField(db_index=True, max_length=10, null=True, blank=True)
    endgrade_avg_tv02 = CharField(db_index=True, max_length=10, null=True, blank=True)
    endgrade_avg_tv03 = CharField(db_index=True, max_length=10, null=True, blank=True)
    endgrade_avg_text = CharField(db_index=True, max_length=10, null=True, blank=True)

    # # # fields result - 9 fields
    result_tv01 = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_tv02 = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_tv03 = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_final = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_info = CharField(db_index=True, max_length=80, null=True, blank=True)
    result_tv01_status = CharField(max_length=12, null=True, blank=True)
    result_tv02_status = CharField(max_length=12, null=True, blank=True)
    result_tv03_status = CharField(max_length=12, null=True, blank=True)
    result_final_status = CharField(max_length=12, null=True, blank=True)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __init__(self, *args, **kwargs):
        super(Studentresult, self).__init__(*args, **kwargs)
        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes

        # # # various fields - 6 fields
        self.original_diplomanumber = self.diplomanumber
        self.original_gradelistnumber = self.gradelistnumber
        self.locked = self.locked
        self.original_has_reex2 = self.has_reex2
        self.original_has_reex3 = self.has_reex3
        self.original_is_withdrawn = self.is_withdrawn

        # # # fields ce/combi avg 6 fields
        self.original_grade_ce_avg_tv01 = self.grade_ce_avg_tv01
        self.original_grade_ce_avg_tv02 = self.grade_ce_avg_tv02
        self.original_grade_ce_avg_tv03 = self.grade_ce_avg_tv03
        self.original_grade_ce_avg_final = self.grade_ce_avg_final
        self.original_grade_ce_avg_text = self.grade_ce_avg_text
        self.original_grade_combi_avg_text = self.grade_combi_avg_text

        # # # fields endgrade sum/avg/count - 8 fields
        self.original_endgrade_sum_tv01 = self.endgrade_sum_tv01
        self.original_endgrade_sum_tv02 = self.endgrade_sum_tv02
        self.original_endgrade_sum_tv03 = self.endgrade_sum_tv03
        self.original_endgrade_count = self.endgrade_count
        self.original_endgrade_avg_tv01 = self.endgrade_avg_tv01
        self.original_endgrade_avg_tv02 = self.endgrade_avg_tv02
        self.original_endgrade_avg_tv03 = self.endgrade_avg_tv03
        self.original_endgrade_avg_text= self.endgrade_avg_text

        # # # fields result - 9 fields
        self.original_result_tv01 = self.result_tv01
        self.original_result_tv02 = self.result_tv02
        self.original_result_tv03 = self.result_tv03
        self.original_result_final = self.result_final
        self.original_result_info = self.result_info
        self.original_result_tv01_status = self.result_tv01_status
        self.original_result_tv02_status = self.result_tv02_status
        self.original_result_tv03_status = self.result_tv03_status
        self.original_result_final_status = self.result_final_status

        # PR2018-11-10 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        # # # various fields - 6 fields
        self.diplomanumber_mod = False
        self.gradelistnumber_mod = False
        self.locked_mod = False
        self.has_reex2_mod = False
        self.has_reex3_mod = False
        self.is_withdrawn_mod = False

        # # # fields ce/combi avg 6 fields
        self.grade_ce_avg_tv01_mod = False
        self.grade_ce_avg_tv02_mod = False
        self.grade_ce_avg_tv03_mod = False
        self.grade_ce_avg_final_mod = False
        self.grade_ce_avg_text_mod = False
        self.grade_combi_avg_text_mod = False

        # # # fields endgrade sum/avg/count - 8 fields
        self.endgrade_sum_tv01_mod = False
        self.endgrade_sum_tv02_mod = False
        self.endgrade_sum_tv03_mod = False
        self.endgrade_count_mod = False
        self.endgrade_avg_tv01_mod = False
        self.endgrade_avg_tv02_mod = False
        self.endgrade_avg_tv03_mod = False
        self.endgrade_avg_text_mod = False

        # # # fields result - 9 fields
        self.result_tv01_mod = False
        self.result_tv02_mod = False
        self.result_tv03_mod = False
        self.result_final_mod = False
        self.result_info_mod = False
        self.result_tv01_status_mod = False
        self.result_tv02_status_mod = False
        self.result_tv03_status_mod = False
        self.result_final_status_mod = False

    def save(self, *args, **kwargs):  # called by subject.save(self.request) in SubjectEditView.form_valid
        self.request = kwargs.pop('request', None)

        # check if data has changed. If so: save object
        if self.data_has_changed():
            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Studentresult, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Subject, self).save
            self.save_to_log()

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(Studentresult, self).delete(*args, **kwargs)


    def save_to_log(self):
        # Create method also saves record
        Studentresult_log.objects.create(
            studentresult_id=self.id, # self.id gets its value in super(School, self).save

            # # # various fields - 6 fields
            diplomanumber = self.diplomanumber,
            gradelistnumber = self.gradelistnumber,
            locked = self.locked,
            has_reex2 = self.has_reex2,
            has_reex3 = self.has_reex3,
            is_withdrawn = self.is_withdrawn,

            # # # fields ce/combi avg 6 fields
            grade_ce_avg_tv01 = self.grade_ce_avg_tv01,
            grade_ce_avg_tv02 = self.grade_ce_avg_tv02,
            grade_ce_avg_tv03 = self.grade_ce_avg_tv03,
            grade_ce_avg_final = self.grade_ce_avg_final,
            grade_ce_avg_text = self.grade_ce_avg_text,
            grade_combi_avg_text = self.grade_combi_avg_text,

            # # # fields endgrade sum/avg/count - 8 fields
            endgrade_sum_tv01 = self.endgrade_sum_tv01,
            endgrade_sum_tv02 = self.endgrade_sum_tv02,
            endgrade_sum_tv03 = self.endgrade_sum_tv03,
            endgrade_count = self.endgrade_count,
            endgrade_avg_tv01 = self.endgrade_avg_tv01,
            endgrade_avg_tv02 = self.endgrade_avg_tv02,
            endgrade_avg_tv03 = self.endgrade_avg_tv03,
            endgrade_avg_text = self.endgrade_avg_text,

            # # # fields result - 9 fields
            result_tv01 = self.result_tv01,
            result_tv02 = self.result_tv02,
            result_tv03 = self.result_tv03,
            result_final = self.result_final,
            result_info = self.result_info,
            result_tv01_status = self.result_tv01_status,
            result_tv02_status = self.result_tv02_status,
            result_tv03_status = self.result_tv03_status,
            result_final_status = self.result_final_status,

            # PR2018-11-10 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
            # # # various fields - 6 fields
            diplomanumber_mod = self.diplomanumber_mod,
            gradelistnumber_mod = self.gradelistnumber_mod,
            locked_mod = self.locked_mod,
            has_reex2_mod = self.has_reex2_mod,
            has_reex3_mod = self.has_reex3_mod,
            is_withdrawn_mod = self.is_withdrawn_mod,

            # # # fields ce/combi avg 6 fields
            grade_ce_avg_tv01_mod = self.grade_ce_avg_tv01_mod,
            grade_ce_avg_tv02_mod = self.grade_ce_avg_tv02_mod,
            grade_ce_avg_tv03_mod = self.grade_ce_avg_tv03_mod,
            grade_ce_avg_final_mod = self.grade_ce_avg_final_mod,
            grade_ce_avg_text_mod = self.grade_ce_avg_text_mod,
            grade_combi_avg_text_mod = self.grade_combi_avg_text_mod,

            # # # fields endgrade sum/avg/count - 8 fields
            endgrade_sum_tv01_mod = self.endgrade_sum_tv01_mod,
            endgrade_sum_tv02_mod = self.endgrade_sum_tv02_mod,
            endgrade_sum_tv03_mod = self.endgrade_sum_tv03_mod,
            endgrade_count_mod = self.endgrade_count_mod,
            endgrade_avg_tv01_mod = self.endgrade_avg_tv01_mod,
            endgrade_avg_tv02_mod = self.endgrade_avg_tv02_mod,
            endgrade_avg_tv03_mod = self.endgrade_avg_tv03_mod,
            endgrade_avg_text_mod = self.endgrade_avg_text_mod,

            # # # fields result - 9 fields
            result_tv01_mod = self.result_tv01_mod,
            result_tv02_mod = self.result_tv02_mod,
            result_tv03_mod = self.result_tv03_mod,
            result_final_mod = self.result_final_mod,
            result_info_mod = self.result_info_mod,
            result_tv01_status_mod = self.result_tv01_status_mod,
            result_tv02_status_mod = self.result_tv02_status_mod,
            result_tv03_status_mod = self.result_tv03_status_mod,
            result_final_status_mod = self.result_final_status_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode=None):  # PR2018-07-21  PR2018-11-10
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        # # # various fields - 6 fields
        self.diplomanumber_mod = self.original_diplomanumber != self.diplomanumber
        self.gradelistnumber_mod = self.original_gradelistnumber != self.gradelistnumber
        self.locked_mod = self.locked != self.locked
        self.has_reex2_mod = self.original_has_reex2 != self.has_reex2
        self.has_reex3_mod = self.original_has_reex3 != self.has_reex3
        self.is_withdrawn_mod = self.original_is_withdrawn != self.is_withdrawn

        # # # fields ce/combi avg 6 fields
        self.grade_ce_avg_tv01_mod = self.original_grade_ce_avg_tv01 != self.grade_ce_avg_tv01
        self.grade_ce_avg_tv02_mod = self.original_grade_ce_avg_tv02 != self.grade_ce_avg_tv02
        self.grade_ce_avg_tv03_mod = self.original_grade_ce_avg_tv03 != self.grade_ce_avg_tv03
        self.grade_ce_avg_final_mod = self.original_grade_ce_avg_final != self.grade_ce_avg_final
        self.grade_ce_avg_text_mod = self.original_grade_ce_avg_text != self.grade_ce_avg_text
        self.grade_combi_avg_text_mod = self.original_grade_combi_avg_text != self.grade_combi_avg_text

        # # # fields endgrade sum/avg/count - 8 fields
        self.endgrade_sum_tv01_mod = self.original_endgrade_sum_tv01 != self.endgrade_sum_tv01
        self.endgrade_sum_tv02_mod = self.original_endgrade_sum_tv02 != self.endgrade_sum_tv02
        self.endgrade_sum_tv03_mod = self.original_endgrade_sum_tv03 != self.endgrade_sum_tv03
        self.endgrade_count_mod = self.original_endgrade_count != self.endgrade_count
        self.endgrade_avg_tv01_mod = self.original_endgrade_avg_tv01 != self.endgrade_avg_tv01
        self.endgrade_avg_tv02_mod = self.original_endgrade_avg_tv02 != self.endgrade_avg_tv02
        self.endgrade_avg_tv03_mod = self.original_endgrade_avg_tv03 != self.endgrade_avg_tv03
        self.endgrade_avg_text_mod = self.original_endgrade_avg_text != self.endgrade_avg_text

        # # # fields result - 9 fields
        self.result_tv01_mod = self.original_result_tv01 != self.result_tv01
        self.result_tv02_mod = self.original_result_tv02 != self.result_tv02
        self.result_tv03_mod = self.original_result_tv03 != self.result_tv03
        self.result_final_mod = self.original_result_final != self.result_final
        self.result_info_mod = self.original_result_info != self.result_info
        self.result_tv01_status_mod = self.original_result_tv01_status != self.result_tv01_status
        self.result_tv02_status_mod = self.original_result_tv02_status != self.result_tv02_status
        self.result_tv03_status_mod = self.original_result_tv03_status != self.result_tv03_status
        self.result_final_status_mod = self.original_result_final_status != self.result_final_status


        data_changed_bool = (
            not self.is_update or

            # # # various fields - 6 fields
            self.diplomanumber_mod or
            self.gradelistnumber_mod or
            self.locked_mod or
            self.has_reex2_mod or
            self.has_reex3_mod or
            self.is_withdrawn_mod or

            # # # fields ce/combi avg 6 fields
            self.grade_ce_avg_tv01_mod or
            self.grade_ce_avg_tv02_mod or
            self.grade_ce_avg_tv03_mod or
            self.grade_ce_avg_final_mod or
            self.grade_ce_avg_text_mod or
            self.grade_combi_avg_text_mod or

            # # # fields endgrade sum/avg/count - 8 fields
            self.endgrade_sum_tv01_mod or
            self.endgrade_sum_tv02_mod or
            self.endgrade_sum_tv03_mod or
            self.endgrade_count_mod or
            self.endgrade_avg_tv01_mod or
            self.endgrade_avg_tv02_mod or
            self.endgrade_avg_tv03_mod or
            self.endgrade_avg_text_mod or

            # # # fields result - 9 fields
            self.result_tv01_mod or
            self.result_tv02_mod or
            self.result_tv03_mod or
            self.result_final_mod or
            self.result_info_mod or
            self.result_tv01_status_mod or
            self.result_tv02_status_mod or
            self.result_tv03_status_mod or
            self.result_final_status_mod
        )

        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        return data_changed_bool

# PR2018-06-08
class Studentresult_log(Model):
    objects = CustomManager()

    studentresult_id = IntegerField(db_index=True)

    diplomanumber = CharField(db_index=True, max_length=10, null=True, blank=True)
    gradelistnumber = CharField(db_index=True, max_length=10, null=True, blank=True)
    locked = BooleanField(default=False)
    has_reex2= BooleanField(default=False)
    has_reex3= BooleanField(default=False)
    is_withdrawn = BooleanField(default=False)

    grade_ce_avg_tv01 = DecimalField(max_digits=5, decimal_places=2, default=0)
    grade_ce_avg_tv02 = DecimalField(max_digits=5, decimal_places=2, default=0)
    grade_ce_avg_tv03 = DecimalField(max_digits=5, decimal_places=2, default=0)
    grade_ce_avg_final = DecimalField(max_digits=5, decimal_places=2, default=0)
    grade_ce_avg_text = CharField(max_length=10, null=True, blank=True)
    grade_combi_avg_text = CharField(max_length=10, null=True, blank=True)

    endgrade_sum_tv01 = PositiveSmallIntegerField(default=0)
    endgrade_sum_tv02 = PositiveSmallIntegerField(default=0)
    endgrade_sum_tv03 = PositiveSmallIntegerField(default=0)
    endgrade_count = PositiveSmallIntegerField(default=0)
    endgrade_avg_tv01 = CharField(max_length=10, null=True, blank=True)
    endgrade_avg_tv02 = CharField(max_length=10, null=True, blank=True)
    endgrade_avg_tv03 = CharField(max_length=10, null=True, blank=True)
    endgrade_avg_text = CharField(max_length=10, null=True, blank=True)

    result_tv01 = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_tv02 = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_tv03 = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_final = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_info = CharField(max_length=80, null=True, blank=True)

    result_tv01_status = CharField(max_length=12, null=True)
    result_tv02_status = CharField(max_length=12, null=True)
    result_tv03_status = CharField(max_length=12, null=True)
    result_final_status = CharField(max_length=12, null=True)

    diplomanumber_mod = BooleanField(default=False)
    gradelistnumber_mod = BooleanField(default=False)
    locked_mod = BooleanField(default=False)
    has_reex2_mod= BooleanField(default=False)
    has_reex3_mod= BooleanField(default=False)
    is_withdrawn_mod = BooleanField(default=False)

    grade_ce_avg_tv01_mod = BooleanField(default=False)
    grade_ce_avg_tv02_mod = BooleanField(default=False)
    grade_ce_avg_tv03_mod = BooleanField(default=False)
    grade_ce_avg_final_mod = BooleanField(default=False)
    grade_ce_avg_text_mod = BooleanField(default=False)
    grade_combi_avg_text_mod = BooleanField(default=False)

    endgrade_sum_tv01_mod = BooleanField(default=False)
    endgrade_sum_tv02_mod = BooleanField(default=False)
    endgrade_sum_tv03_mod = BooleanField(default=False)
    endgrade_count_mod = BooleanField(default=False)
    endgrade_avg_tv01_mod = BooleanField(default=False)
    endgrade_avg_tv02_mod = BooleanField(default=False)
    endgrade_avg_tv03_mod = BooleanField(default=False)
    endgrade_avg_text_mod = BooleanField(default=False)

    result_tv01_mod = BooleanField(default=False)
    result_tv02_mod = BooleanField(default=False)
    result_tv03_mod = BooleanField(default=False)
    result_final_mod = BooleanField(default=False)
    result_info_mod = BooleanField(default=False)

    result_tv01_status_mod = BooleanField(default=False)
    result_tv02_status_mod = BooleanField(default=False)
    result_tv03_status_mod = BooleanField(default=False)
    result_final_status_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

# PR2018-106-17
class Resultnote(Model):
    objects = CustomManager()

    studentresult = ForeignKey(Studentresult, related_name='+', on_delete=PROTECT)
    resultnote =  CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)

    is_insp = BooleanField(default=False)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(default=False)

# PR2018-106-17
class Resultnote_log(Model):
    objects = CustomManager()

    resultnote_id = IntegerField(db_index=True)
    # TODO: refer to log table
    studentresult = ForeignKey(Studentresult, related_name='+', on_delete=PROTECT)
    resultnote = CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)

    is_insp = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(default=False)

# ======= Student subject ======================================================================

# PR2018-06-06 PR19=018-11-19
class Studentsubject(Model):
    objects = CustomManager()

    student = ForeignKey(Student, related_name='studres_studsubs', on_delete=PROTECT)
    schemeitem = ForeignKey(Schemeitem, related_name='schemeitem_studsubs', on_delete=PROTECT)
    cluster = ForeignKey(Cluster, null=True, blank=True, related_name='cluster_studsubs', on_delete=PROTECT)
    # # #
    is_extra_subject = BooleanField(default=False)
    is_extra_subject_counts = BooleanField(default=False)
    is_choice_combi = BooleanField(default=False)
    # # # profielwerkstuk / sectorwerkstuk
    pws_title = CharField(max_length=80, null=True, blank = True)
    pws_subjects = CharField(max_length=80, null=True, blank = True)
    # # #  exemption # # #
    has_exemption = BooleanField(default=False)
    # # # Tv02 # # #
    has_tv02 = BooleanField(default=False)
    # # # Tv03 # # #
    has_tv03 = BooleanField(default=False)
    # # # proof of knowledge # # #
    has_pok = BooleanField(default=False)  # proof of knowledge
    has_pok_status = CharField(max_length=12, null=True)
    # # # endgrade # # #
    endgrade_tv01 = CharField(max_length=2, null=True)
    endgrade_tv02 = CharField(max_length=2, null=True)
    endgrade_tv03 = CharField(max_length=2, null=True)
    endgrade_final = CharField(max_length=2, null=True)
    endgrade_tv01_status = CharField(max_length=12, null=True)
    endgrade_tv02_status = CharField(max_length=12, null=True)
    endgrade_tv03_status = CharField(max_length=12, null=True)
    endgrade_final_status = CharField(max_length=12, null=True)

    # # #
    # put notes in a separate table, per user

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __init__(self, *args, **kwargs): # PR2018-11-24
        super(Studentsubject, self).__init__(*args, **kwargs)
        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes

        try:
            self.original_student = self.student
        except:
            self.original_student = None
        try:
            self.original_schemeitem = self.schemeitem
        except:
            self.original_schemeitem = None
        try:
            self.original_cluster = self.cluster
        except:
            self.original_cluster = None

        self.original_is_extra_subject = self.is_extra_subject
        self.original_is_extra_subject_counts = self.is_extra_subject_counts
        self.original_is_choice_combi = self.is_choice_combi
        self.original_pws_title = self.pws_title
        self.original_pws_subjects = self.pws_subjects
        self.original_has_exemption = self.has_exemption
        self.original_has_tv02 = self.has_tv02
        self.original_has_tv03 = self.has_tv03
        self.original_has_pok = self.has_pok
        self.original_has_pok_status = self.has_pok_status
        self.original_endgrade_tv01 = self.endgrade_tv01
        self.original_endgrade_tv02 = self.endgrade_tv02
        self.original_endgrade_tv03 = self.endgrade_tv03
        self.original_endgrade_final = self.endgrade_final
        self.original_endgrade_tv01_status = self.endgrade_tv01_status
        self.original_endgrade_tv02_status = self.endgrade_tv02_status
        self.original_endgrade_tv03_status = self.endgrade_tv03_status
        self.original_endgrade_final_status = self.endgrade_final_status

        # PR2018-11-10 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        # # # various fields - 6 fields
        self.diplomanumber_mod = False
        self.student_mod = False
        self.schemeitem_mod = False
        self.cluster_mod = False
        self.is_extra_subject_mod = False
        self.is_extra_subject_counts_mod = False
        self.is_choice_combi_mod = False
        self.pws_title_mod = False
        self.pws_subjects_mod = False
        self.has_exemption_mod = False
        self.has_tv02_mod = False
        self.has_tv03_mod = False
        self.has_pok_mod = False
        self.has_pok_status_mod = False
        self.endgrade_tv01_mod = False
        self.endgrade_tv02_mod = False
        self.endgrade_tv03_mod = False
        self.endgrade_final_mod = False
        self.endgrade_tv01_status_mod = False
        self.endgrade_tv02_status_mod = False
        self.endgrade_tv03_status_mod = False
        self.endgrade_final_status_mod = False

    def save(self, *args, **kwargs):  # # PR2018-11-24 called by subject.save(self.request) in SubjectEditView.form_valid
        self.request = kwargs.pop('request', None)
        # logger.debug('Studentsubject Model save self.request: ' + str(self.request) + ' type: ' + str(type(self.request)))

        # check if data has changed. If so: save object
        if self.data_has_changed():
            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Studentsubject, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Subject, self).save
            self.save_to_log()

    def delete(self, *args, **kwargs):  # PR2018-11-24
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()

        logger.debug('Studentsubject Model before delete.')
        super(Studentsubject, self).delete(*args, **kwargs)
        logger.debug('Studentsubject Model after delete.')

    def save_to_log(self): # PR2018-11-24

        logger.debug('Studentsubject Model save_to_log self.schemeitem: ' + str(self.schemeitem) + ' type: ' + str(type(self.schemeitem)))

        # Create method also saves record
        Studentsubject_log.objects.create(
            studentsubject_id=self.id,  # self.id gets its value in super(School, self).save

            student = self.student,
            schemeitem = self.schemeitem,
            cluster = self.cluster,
            is_extra_subject = self.is_extra_subject,
            is_extra_subject_counts = self.is_extra_subject_counts,
            is_choice_combi = self.is_choice_combi,
            pws_title = self.pws_title,
            pws_subjects = self.pws_subjects,
            has_exemption = self.has_exemption,
            has_tv02 = self.has_tv02,
            has_tv03 = self.has_tv03,
            has_pok = self.has_pok,
            has_pok_status = self.has_pok_status,
            endgrade_tv01 = self.endgrade_tv01,
            endgrade_tv02 = self.endgrade_tv02,
            endgrade_tv03 = self.endgrade_tv03,
            endgrade_final = self.endgrade_final,
            endgrade_tv01_status = self.endgrade_tv01_status,
            endgrade_tv02_status = self.endgrade_tv02_status,
            endgrade_tv03_status = self.endgrade_tv03_status,
            endgrade_final_status = self.endgrade_final_status,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode=None):  # PR2018-11-24
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        self.student_mod = self.original_student != self.student
        self.schemeitem_mod = self.original_schemeitem != self.schemeitem
        self.cluster_mod = self.original_cluster != self.cluster
        self.is_extra_subject_mod = self.original_is_extra_subject != self.is_extra_subject
        self.is_extra_subject_counts_mod = self.original_is_extra_subject_counts != self.is_extra_subject_counts
        self.is_choice_combi_mod = self.original_is_choice_combi != self.is_choice_combi
        self.pws_title_mod = self.original_pws_title != self.pws_title
        self.pws_subjects_mod = self.original_pws_subjects != self.pws_subjects
        self.has_exemption_mod = self.original_has_exemption != self.has_exemption
        self.has_tv02_mod = self.original_has_tv02 != self.has_tv02
        self.has_tv03_mod = self.original_has_tv03 != self.has_tv03
        self.has_pok_mod = self.original_has_pok != self.has_pok
        self.has_pok_status_mod = self.original_has_pok_status != self.has_pok_status
        self.endgrade_tv01_mod = self.original_endgrade_tv01 != self.endgrade_tv01
        self.endgrade_tv02_mod = self.original_endgrade_tv02 != self.endgrade_tv02
        self.endgrade_tv03_mod = self.original_endgrade_tv03 != self.endgrade_tv03
        self.endgrade_final_mod = self.original_endgrade_final != self.endgrade_final
        self.endgrade_tv01_status_mod = self.original_endgrade_tv01_status != self.endgrade_tv01_status
        self.endgrade_tv02_status_mod = self.original_endgrade_tv02_status != self.endgrade_tv02_status
        self.endgrade_tv03_status_mod = self.original_endgrade_tv03_status != self.endgrade_tv03_status
        self.endgrade_final_status_mod = self.original_endgrade_final_status != self.endgrade_final_status


        data_changed_bool = (
            not self.is_update or

            self.student_mod or
            self.schemeitem_mod or
            self.cluster_mod or
            self.is_extra_subject_mod or
            self.is_extra_subject_counts_mod or
            self.is_choice_combi_mod or
            self.pws_title_mod or
            self.pws_subjects_mod or
            self.has_exemption_mod or
            self.has_tv02_mod or
            self.has_tv03_mod or
            self.has_pok_mod or
            self.has_pok_status_mod or
            self.endgrade_tv01_mod or
            self.endgrade_tv02_mod or
            self.endgrade_tv03_mod or
            self.endgrade_final_mod or
            self.endgrade_tv01_status_mod or
            self.endgrade_tv02_status_mod or
            self.endgrade_tv03_status_mod or
            self.endgrade_final_status_mod
        )


        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        # logger.debug('Studentsubject Model data_changed_bool: ' + str(data_changed_bool) + ' type: ' + str(type(data_changed_bool)))
        return data_changed_bool


#  ++++++++++  Class methods  +++++++++++++++++++++++++++
    @classmethod
    def get_studsubj_list(cls, student):  # PR2019-02-08
        studentsubject = cls.objects.filter(student=student).order_by('schemeitem__subject__sequence', 'schemeitem__subjecttype__sequence').all()
        studentsubject_list = []
        for item in studentsubject:
            pws_title = ''
            pws_subjects = ''
            if item.pws_title:
                pws_title = item.pws_title
            if item.pws_subjects:
                pws_subjects = item.pws_subjects
            sequence = item.schemeitem.subject.sequence * 1000 + item.schemeitem.subjecttype.sequence
            studentsubject_list.append({
                'mode': '-',
                'studsubj_id': item.id,
                'stud_id': item.student.id,
                'ssi_id': item.schemeitem.id,
                'subj_id': item.schemeitem.subject.id,
                'subj_name': item.schemeitem.subject.name,
                'sjtp_id': item.schemeitem.subjecttype.id,
                'sjtp_name': item.schemeitem.subjecttype.abbrev,
                'sjtp_one': (0, 1)[item.schemeitem.subjecttype.one_allowed],
                'sequence': sequence,
                'extra_nocount': (0, 1)[item.is_extra_subject],
                'extra_counts': (0, 1)[item.is_extra_subject_counts],
                'choice_combi': (0, 1)[item.is_choice_combi],
                'pws_title': pws_title,
                'pws_subjects': pws_subjects
            })

            #schemeitem = ForeignKey(Schemeitem, related_name='schemeitem_studsubs', on_delete=PROTECT)
            #cluster = ForeignKey(Cluster, null=True, blank=True, related_name='cluster_studsubs', on_delete=PROTECT)
            # # #
            #is_extra_subject = BooleanField(default=False)
            #is_extra_subject_counts = BooleanField(default=False)
            #is_choice_combi = BooleanField(default=False)
            # # # profielwerkstuk / sectorwerkstuk
            #pws_title = CharField(max_length=80, null=True, blank=True)
            #pws_subjects = CharField(max_length=80, null=True, blank=True)

        return studentsubject_list









# PR2018-06-06
class Studentsubject_log(Model):
    objects = CustomManager()
    studentsubject_id = IntegerField(db_index=True)

    # # #
    # TODO: refer to log table
    student = ForeignKey(Student, null=True, related_name='+', on_delete=PROTECT)
    schemeitem = ForeignKey(Schemeitem, null=True, related_name='+', on_delete=PROTECT)
    cluster = ForeignKey(Cluster, null=True, related_name='+', on_delete=PROTECT)
    # # #
    is_extra_subject = BooleanField(default=False)
    is_extra_subject_counts = BooleanField(default=False)
    is_choice_combi = BooleanField(default=False)
    # # # profielwerkstuk / sectorwerkstuk
    pws_title = CharField(max_length=80, null=True, blank = True)
    pws_subjects = CharField(max_length=80, null=True, blank = True)
    # # #  exemption # # #
    has_exemption = BooleanField(default=False)
    # # # Tv02 # # #
    has_tv02 = BooleanField(default=False)
    # # # Tv03 # # #
    has_tv03 = BooleanField(default=False)
    # # # proof of knowledge # # #
    has_pok = BooleanField(default=False)
    has_pok_status = CharField(max_length=12, null=True)
    # # # endgrade # # #
    endgrade_tv01 = CharField(max_length=2, null=True)
    endgrade_tv02 = CharField(max_length=2, null=True)
    endgrade_tv03 = CharField(max_length=2, null=True)
    endgrade_final = CharField(max_length=2, null=True)

    endgrade_tv01_status = CharField(max_length=12, null=True)
    endgrade_tv02_status = CharField(max_length=12, null=True)
    endgrade_tv03_status = CharField(max_length=12, null=True)
    endgrade_final_status = CharField(max_length=12, null=True)

    # # #
    student_mod = BooleanField(default=False)
    schemeitem_mod = BooleanField(default=False)
    cluster_mod = BooleanField(default=False)
    # # #
    is_extra_subject_mod = BooleanField(default=False)
    is_extra_subject_counts_mod = BooleanField(default=False)
    is_choice_combi_mod = BooleanField(default=False)
    # # # profielwerkstuk / sectorwerkstuk
    pws_title_mod = BooleanField(default=False)
    pws_subjects_mod = BooleanField(default=False)
    # # #  exemption # # #
    has_exemption_mod = BooleanField(default=False)
    # # # Tv02 # # #
    has_tv02_mod_mod = BooleanField(default=False)
    # # # Tv03 # # #
    has_tv03_mod_mod = BooleanField(default=False)
    # # # proof of knowledge # # #
    has_pok_mod = BooleanField(default=False)
    has_pok_status_mod = BooleanField(default=False)
    # # # endgrade # # #
    endgrade_tv01_mod = BooleanField(default=False)
    endgrade_tv02_mod = BooleanField(default=False)
    endgrade_tv03_mod = BooleanField(default=False)
    endgrade_final_mod = BooleanField(default=False)

    endgrade_tv01_status_mod = BooleanField(default=False)
    endgrade_tv02_status_mod = BooleanField(default=False)
    endgrade_tv03_status_mod = BooleanField(default=False)
    endgrade_final_status_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

# PR2018-106-17
class Studentsubjectnote(Model):
    objects = CustomManager()

    studentsubject = ForeignKey(Studentsubject, related_name='+', on_delete=PROTECT)

    note =  CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)
    is_insp = BooleanField(default=False)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(default=False)

# PR2018-106-17
class Studentsubjectnote_log(Model):
    objects = CustomManager()

    studentsubjectnote_id = IntegerField(db_index=True)

    # TODO: refer to log table
    studentsubject = ForeignKey(Studentsubject, related_name='+', on_delete=PROTECT)
    note = CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)
    is_insp = BooleanField(default=False)

    studentsubject_mod = BooleanField(default=False)
    note_mod = BooleanField(default=False)
    mailto_user_mod = BooleanField(default=False)
    is_insp_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(default=False)

#==== GRADES ======================================================

# PR2018-06-06
class Grade(Model):
    objects = CustomManager()

    studentsubject = ForeignKey(Studentsubject, related_name='grades', on_delete=PROTECT)

    examcode = CharField(max_length=4, choices=c.EXAMCODE_CHOICES) # se, pe ce, ce2, ce3, fin
    gradeclass = CharField(max_length=1, null=True, choices=c.GRADECLASS_CHOICES) # s = score, g = grade, x = exemption, f = final grade
    value = CharField(max_length=4, null=True, blank=True)
    status = CharField(max_length=12, null=True, blank=True)
    published = BooleanField(default=False)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __init__(self, *args, **kwargs): # PR2018-11-24
        super(Grade, self).__init__(*args, **kwargs)
        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes

        try:
            self.original_studentsubject = self.studentsubject
        except:
            self.original_studentsubject = None

        self.original_examcode = self.examcode
        self.original_gradeclass = self.gradeclass
        self.original_published = self.published
        self.original_status = self.status

        # PR2018-11-10 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        # # # various fields - 6 fields
        self.examcode_mod = False
        self.gradeclass_mod = False
        self.value_mod = False
        self.published_mod = False
        self.status_mod = False

    def save(self, *args, **kwargs):  # # PR2018-11-24 called by subject.save(self.request) in SubjectEditView.form_valid
        self.request = kwargs.pop('request', None)
        logger.debug('Grade Model save self.request: ' + str(self.request) + ' type: ' + str(type(self.request)))

        # check if data has changed. If so: save object
        if self.data_has_changed():
            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Grade, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Subject, self).save
            self.save_to_log()

    def delete(self, *args, **kwargs):  # PR2018-11-28
        request_user = kwargs.pop('request_user')

        # update modified_by and modified_at, so it can be stored in log
        self.modified_by = request_user
        self.modified_at = timezone.now()
        self.mode = 'd'
        self.data_has_changed()

        # First save to logfile
        self.save_to_log()
        # then delete record
        super(Grade, self).delete(*args, **kwargs)

    def save_to_log(self): # PR2018-11-28
        # get latest Studentsubject_log row that corresponds with self.studentsubject
        self.studentsubject_log = None
        if self.studentsubject is not None:
            self.studentsubject_log = Studentsubject_log.objects.filter(studentsubject_id=self.studentsubject.id).order_by('-id').first()

        # Create method also saves record
        Grade_log.objects.create(
            grade_id=self.id,  # self.id gets its value in super(School, self).save

            studentsubject_log = self.studentsubject_log,

            examcode=self.examcode,
            gradeclass=self.gradeclass,
            value=self.value,
            published=self.published,
            status=self.status,

            examcode_mod=self.examcode_mod,
            gradeclass_mod=self.gradeclass_mod,
            value_mod=self.value_mod,
            status_mod=self.status_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode=None):  # PR2018-11-24
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        self.studentsubject_mod = self.original_studentsubject != self.studentsubject
        self.examcode_mod = self.original_examcode != self.examcode
        self.gradeclass_mod = self.original_gradeclass != self.gradeclass
        self.value_mod = self.original_value != self.value
        self.published_mod = self.original_published != self.published
        self.status_mod = self.original_status != self.status

        data_changed_bool = (
            not self.is_update or

            self.studentsubject_mod or
            self.examcode_mod or
            self.gradeclass_mod or
            self.value_mod or
            self.published_mod or
            self.status_mod
        )


        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode:
            # override mode on delete
            self.mode = mode

        return data_changed_bool

# PR2018-06-06
class Grade_log(Model):
    objects = CustomManager()

    grade_id = IntegerField(db_index=True)

    studentsubject_log = ForeignKey(Studentsubject_log, related_name='+', on_delete=PROTECT)

    examcode = CharField(max_length=4, null=True)
    gradeclass = CharField(max_length=1, null=True)
    value = CharField(max_length=4, null=True)
    published = BooleanField(default=False)
    status = CharField(max_length=12, null=True)

    examcode_mod = BooleanField(default=False)
    gradeclass_mod = BooleanField(default=False)
    value_mod = BooleanField(default=False)
    published_mod = BooleanField(default=False)
    status_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    @property
    def mode_str(self):
        return f.get_mode_str(self)