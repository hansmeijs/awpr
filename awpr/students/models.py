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
from subjects.models import Level, Level_log, Sector, Sector_log, Scheme, Scheme_log, Schemeitem, Schemeitem_log,\
    Package, Package_log, Cluster, Cluster_log

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
    modified_at = DateTimeField(db_index=True)

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
    modified_at = DateTimeField(db_index=True)

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
    prefix= CharField(db_index=True, max_length=10, null=True, blank=True)
    gender= CharField(db_index=True, max_length=1, null=True, blank=True)
    idnumber= CharField(db_index=True, max_length=20)
    birthdate= DateField(db_index=True, null=True, blank=True)
    birthcountry= CharField(db_index=True, max_length=50, null=True, blank=True)
    birthcity= CharField(db_index=True, max_length=50, null=True, blank=True)

    classname = CharField(db_index=True, max_length=20, null=True, blank=True)
    examnumber = CharField(db_index=True, max_length=20, null=True, blank=True)
    regnumber = CharField(db_index=True, max_length=20, null=True, blank=True)
    diplomanumber = CharField(db_index=True, max_length=10, null=True, blank=True)
    gradelistnumber = CharField(db_index=True, max_length=10, null=True, blank=True)

    locked =  BooleanField(db_index=True,default=False)
    has_reex= BooleanField(db_index=True,default=False)
    bis_exam= BooleanField(db_index=True,default=False)
    withdrawn = BooleanField(db_index=True,default=False)

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

        self.original_diplomanumber = self.diplomanumber
        self.original_gradelistnumber = self.gradelistnumber
        self.original_locked = self.locked
        self.original_has_reex = self.has_reex
        self.original_bis_exam = self.bis_exam
        self.original_withdrawn = self.withdrawn

        # PR2018-10-19 initialize here, otherwise delete gives error: object has no attribute 'name_mod'
        self.school_mod = False
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
        self.diplomanumber_mod = False
        self.gradelistnumber_mod = False

        self.locked_mod = False
        self.has_reex_mod = False
        self.bis_exam_mod = False
        self.withdrawn_mod = False

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

            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Student, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            self.save_to_log()

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

            base=self.base,

            school_log=school_log,
            dep_log=dep_log,
            level_log=level_log,
            sector_log=sector_log,
            scheme_log=scheme_log,
            package_log=package_log,

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
            diplomanumber=self.diplomanumber,
            gradelistnumber=self.gradelistnumber,

            locked=self.locked,
            has_reex=self.has_reex,
            bis_exam=self.bis_exam,
            withdrawn=self.withdrawn,

            # # # mod variables
            school_log_mod=self.school_mod,
            dep_log_mod=self.dep_mod,
            level_log_mod=self.level_mod,
            sector_log_mod=self.sector_mod,
            scheme_log_mod=self.scheme_mod,
            package_log_mod=self.package_mod,

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
            diplomanumber_mod = self.diplomanumber_mod,
            gradelistnumber_mod = self.gradelistnumber_mod,

            locked_mod = self.locked_mod,
            has_reex_mod = self.has_reex_mod,
            bis_exam_mod = self.bis_exam_mod,
            withdrawn_mod = self.withdrawn_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode_override=None):  # PR2018-11-20
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
        self.diplomanumber_mod = self.original_diplomanumber != self.diplomanumber
        self.gradelistnumber_mod = self.original_gradelistnumber != self.gradelistnumber

        self.locked_mod = self.original_locked != self.locked
        self.has_reex_mod = self.original_has_reex != self.has_reex
        self.bis_exam_mod = self.original_bis_exam != self.bis_exam
        self.withdrawn_mod = self.original_withdrawn != self.withdrawn

        data_changed_bool = (
                not self.is_update or

                self.school_mod or
                self.dep_mod or
                self.level_mod or
                self.sector_mod or
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
                self.regnumber_mod or
                self.diplomanumber_mod or
                self.gradelistnumber_mod or

                self.locked_mod or
                self.has_reex_mod or
                self.bis_exam_mod or
                self.withdrawn_mod
        )

        if data_changed_bool:
            self.modified_by = self.request.user
            self.modified_at = timezone.now()
            self.mode = ('c', 'u')[self.is_update]

        if mode_override:
            # override mode on delete
            self.mode = mode_override

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
    gender = CharField(db_index=True, max_length=1, null=True)
    idnumber = CharField(db_index=True, max_length=20)
    birthdate = DateField(null=True)
    birthcountry = CharField(max_length=50, null=True)
    birthcity = CharField(max_length=50, null=True)

    classname = CharField(db_index=True, max_length=20, null=True, blank=True)
    examnumber = CharField(db_index=True, max_length=20, null=True, blank=True)
    regnumber = CharField(db_index=True, max_length=20, null=True, blank=True)
    diplomanumber = CharField(max_length=10, null=True, blank=True)
    gradelistnumber = CharField(max_length=10, null=True, blank=True)

    locked = BooleanField(default=False)
    has_reex = BooleanField(default=False)
    bis_exam = BooleanField(default=False)
    withdrawn = BooleanField(default=False)

    # mod variables
    school_log_mod = BooleanField(default=False)
    dep_log_mod = BooleanField(default=False)
    level_log_mod = BooleanField(default=False)
    sector_log_mod = BooleanField(default=False)
    scheme_log_mod = BooleanField(default=False)
    package_log_mod = BooleanField(default=False)

    lastname_mod = BooleanField(default=False)
    firstname_mod = BooleanField(default=False)
    prefix_mod = BooleanField(default=False)
    gender_mod = BooleanField(default=False)
    idnumber_mod = BooleanField(default=False)
    birthdate_mod = BooleanField(default=False)
    birthcountry_mod = BooleanField(default=False)
    birthcity_mod = BooleanField(default=False)

    classname_mod = BooleanField(default=False)
    examnumber_mod = BooleanField(default=False)
    regnumber_mod = BooleanField(default=False)
    diplomanumber_mod = BooleanField(default=False)
    gradelistnumber_mod = BooleanField(default=False)

    locked_mod = BooleanField(default=False)
    has_reex_mod = BooleanField(default=False)
    bis_exam_mod = BooleanField(default=False)
    withdrawn_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

    @property
    def mode_str(self):
        return c.get_mode_str(self)

##########################################################################

# ====Result=============
class Result(Model):# PR2018-11-10
    objects = CustomManager()

    student = ForeignKey(Student, related_name='results', on_delete=PROTECT)
    period = PositiveSmallIntegerField(db_index=True, default=0, choices=c.PERIOD_CHOICES) # 1 = period 1, 2 = period 2, 3 = period 3

    grade_ce_avg = DecimalField(max_digits=5, decimal_places=2, default = 0)
    grade_ce_avg_text = CharField(db_index=True, max_length=10, null=True, blank=True)
    grade_combi_avg_text = CharField(db_index=True, max_length=10, null=True, blank=True)

    endgrade_sum = PositiveSmallIntegerField(default=0)
    endgrade_count = PositiveSmallIntegerField(default=0)
    endgrade_avg = DecimalField(max_digits=5, decimal_places=2, default = 0)
    endgrade_avg_text = CharField(db_index=True, max_length=10, null=True, blank=True)

    result = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_info = CharField(db_index=True, max_length=80, null=True, blank=True)
    result_status = CharField(max_length=12, null=True, blank=True)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    def __init__(self, *args, **kwargs):
        super(Result, self).__init__(*args, **kwargs)
        # private variable __original checks if data_has_changed, to prevent update record when no changes are made.
        # Otherwise a logrecord is created every time the save button is clicked without changes

        self.original_grade_ce_avg = self.grade_ce_avg
        self.original_grade_ce_avg_text = self.grade_ce_avg_text
        self.original_grade_combi_avg_text = self.grade_combi_avg_text

        self.original_endgrade_sum = self.endgrade_sum
        self.original_endgrade_count = self.endgrade_count
        self.original_endgrade_avg = self.endgrade_avg
        self.original_endgrade_avg_text= self.endgrade_avg_text

        self.original_result = self.result
        self.original_result_info = self.result_info
        self.original_result_status = self.result_status

        # PR2018-11-10 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        self.grade_ce_avg_mod = False
        self.grade_ce_avg_text_mod = False
        self.grade_combi_avg_text_mod = False

        self.endgrade_sum_mod = False
        self.endgrade_count_mod = False
        self.endgrade_avg_mod = False
        self.endgrade_avg_text_mod = False

        self.result_mod = False
        self.result_info_mod = False
        self.result_status_mod = False

    def save(self, *args, **kwargs):  # called by subject.save(self.request) in SubjectEditView.form_valid
        self.request = kwargs.pop('request', None)

        # check if data has changed. If so: save object
        if self.data_has_changed():
            # when adding record: self.id=None, set force_insert=True; otherwise: set force_update=True PR2018-06-09
            super(Result, self).save(force_insert = not self.is_update, force_update = self.is_update, **kwargs)
            # self.id gets its value in super(Subject, self).save
            self.save_to_log()

    def delete(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.data_has_changed('d')
        # save to logfile before deleting record
        self.save_to_log()
        super(Result, self).delete(*args, **kwargs)

    def save_to_log(self):
        # Create method also saves record
        Result_log.objects.create(
            result_id=self.id, # self.id gets its value in super(School, self).save

            grade_ce_avg = self.grade_ce_avg,
            grade_ce_avg_text = self.grade_ce_avg_text,
            grade_combi_avg_text = self.grade_combi_avg_text,

            # # # fields endgrade sum/avg/count - 8 fields
            endgrade_sum_tv01 = self.endgrade_sum,
            endgrade_count = self.endgrade_count,
            endgrade_avg_tv01 = self.endgrade_avg,
            endgrade_avg_text = self.endgrade_avg_text,

            # # # fields result - 9 fields
            result_tv01 = self.result,
            result_info = self.result_info,
            result_tv01_status = self.result_status,

            # PR2018-11-10 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
            grade_ce_avg_mod = self.grade_ce_avg_mod,
            grade_ce_avg_text_mod = self.grade_ce_avg_text_mod,
            grade_combi_avg_text_mod = self.grade_combi_avg_text_mod,

            endgrade_sum_mod = self.endgrade_sum_mod,
            endgrade_count_mod = self.endgrade_count_mod,
            endgrade_avg_mod = self.endgrade_avg_mod,
            endgrade_avg_text_mod = self.endgrade_avg_text_mod,

            result_mod = self.result_mod,
            result_info_mod = self.result_info_mod,
            result_status_mod = self.result_status_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode=None):  # PR2018-07-21  PR2018-11-10
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        # # # fields ce/combi avg 6 fields
        self.grade_ce_avg_mod = self.original_grade_ce_avg != self.grade_ce_avg
        self.grade_ce_avg_text_mod = self.original_grade_ce_avg_text != self.grade_ce_avg_text
        self.grade_combi_avg_text_mod = self.original_grade_combi_avg_text != self.grade_combi_avg_text

        # # # fields endgrade sum/avg/count - 8 fields
        self.endgrade_sum_mod = self.original_endgrade_sum != self.endgrade_sum
        self.endgrade_count_mod = self.original_endgrade_count != self.endgrade_count
        self.endgrade_avg_mod = self.original_endgrade_avg != self.endgrade_avg
        self.endgrade_avg_text_mod = self.original_endgrade_avg_text != self.endgrade_avg_text

        # # # fields result - 9 fields
        self.result_mod = self.original_result != self.result
        self.result_info_mod = self.original_result_info != self.result_info
        self.result_status_mod = self.original_result_status != self.result_status

        data_changed_bool = (
            not self.is_update or

            self.grade_ce_avg_mod or
            self.grade_ce_avg_text_mod or
            self.grade_combi_avg_text_mod or

            self.endgrade_sum_mod or
            self.endgrade_count_mod or
            self.endgrade_avg_mod or
            self.endgrade_avg_text_mod or

            self.result_mod or
            self.result_info_mod or
            self.result_status_mod
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
class Result_log(Model):
    objects = CustomManager()
    # TODO bind to student
    result_id = IntegerField(db_index=True)

    grade_ce_avg = DecimalField(max_digits=5, decimal_places=2, default=0)
    grade_ce_avg_text = CharField(max_length=10, null=True, blank=True)
    grade_combi_avg_text = CharField(max_length=10, null=True, blank=True)

    endgrade_sum = PositiveSmallIntegerField(default=0)
    endgrade_count = PositiveSmallIntegerField(default=0)
    endgrade_avg = CharField(max_length=10, null=True, blank=True)
    endgrade_avg_text = CharField(max_length=10, null=True, blank=True)

    result = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_info = CharField(max_length=80, null=True, blank=True)

    result_status = CharField(max_length=12, null=True)

    # mod variables
    grade_ce_avg_mod = BooleanField(default=False)
    grade_ce_avg_text_mod = BooleanField(default=False)
    grade_combi_avg_text_mod = BooleanField(default=False)

    endgrade_sum_mod = BooleanField(default=False)
    endgrade_count_mod = BooleanField(default=False)
    endgrade_avg_mod = BooleanField(default=False)
    endgrade_avg_text_mod = BooleanField(default=False)

    result_mod = BooleanField(default=False)
    result_info_mod = BooleanField(default=False)
    result_status_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

# PR2018-106-17
class Resultnote(Model):
    objects = CustomManager()

    # PR2019-02-14 changed: refer to log table student_log instead of student, to prevent ref_int with table student
    student = ForeignKey(Student, null=True, related_name='+', on_delete=PROTECT)

    resultnote =  CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)

    is_insp = BooleanField(default=False)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

# PR2018-106-17
class Resultnote_log(Model):
    objects = CustomManager()

    resultnote_id = IntegerField(db_index=True)
    # TODO: refer to log table
    # PR2019-02-14 changed: refer to log table student_log instead of student, to prevent ref_int with table student
    student_log = ForeignKey(Student_log, null=True, related_name='+', on_delete=PROTECT)

    resultnote = CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)

    is_insp = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

# ======= Student subject ======================================================================

# PR2018-06-06 PR19=018-11-19
class Studentsubject(Model):
    objects = CustomManager()

    student = ForeignKey(Student, related_name='studres_studsubs', on_delete=PROTECT)
    schemeitem = ForeignKey(Schemeitem, related_name='schemeitem_studsubs', on_delete=PROTECT)
    cluster = ForeignKey(Cluster, null=True, blank=True, related_name='cluster_studsubs', on_delete=PROTECT)

    is_extra_nocount = BooleanField(default=False)
    is_extra_counts = BooleanField(default=False)
    is_choice_combi = BooleanField(default=False)

    pws_title = CharField(max_length=80, null=True, blank = True)
    pws_subjects = CharField(max_length=80, null=True, blank = True)

    has_exemption = BooleanField(default=False)
    has_reex = BooleanField(default=False)
    has_reex03 = BooleanField(default=False)
    has_pok = BooleanField(default=False)  # proof of knowledge
    has_pok_status = CharField(max_length=12, null=True)

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

        self.original_is_extra_nocount = self.is_extra_nocount
        self.original_is_extra_counts = self.is_extra_counts
        self.original_is_choice_combi = self.is_choice_combi

        self.original_pws_title = self.pws_title
        self.original_pws_subjects = self.pws_subjects

        self.original_has_exemption = self.has_exemption
        self.original_has_reex = self.has_reex
        self.original_has_reex03 = self.has_reex03
        self.original_has_pok = self.has_pok
        self.original_has_pok_status = self.has_pok_status

        # PR2018-11-10 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        # # # various fields - 6 fields
        self.diplomanumber_mod = False
        self.student_mod = False
        self.schemeitem_mod = False
        self.cluster_mod = False
        self.is_extra_nocount_mod = False
        self.is_extra_counts_mod = False
        self.is_choice_combi_mod = False
        self.pws_title_mod = False
        self.pws_subjects_mod = False
        self.has_exemption_mod = False
        self.has_reex_mod = False
        self.has_reex03_mod = False
        self.has_pok_mod = False
        self.has_pok_status_mod = False


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
        # PR2018-10-28 debug: 'NoneType' object has no attribute 'id'

        # get latest Student_log row that corresponds with self.student
        student_log = None
        if self.student is not None:
            student_log = Student_log.objects.filter(student_id=self.student.id).order_by('-id').first()

        # get latest Schemeitem_log row that corresponds with self.schemeitem
        schemeitem_log = None
        if self.schemeitem is not None:
            schemeitem_log = Schemeitem_log.objects.filter(schemeitem_id=self.schemeitem.id).order_by('-id').first()

        # get latest Cluster_log row that corresponds with self.cluster
        cluster_log = None
        if self.cluster is not None:
            cluster_log = Cluster_log.objects.filter(subjecttype_id=self.cluster.id).order_by('-id').first()

        # Create method also saves record
        Studentsubject_log.objects.create(
            studentsubject_id=self.id,  # self.id gets its value in super(School, self).save

            student_log = student_log, #PR2019-02-15 debug: must be student_log, not self.student_log
            schemeitem_log = schemeitem_log,#PR2019-02-15 debug: must be schemeitem_log, not self.schemeitem_log
            cluster_log = cluster_log,#PR2019-02-15 debug: must be cluster_log, not self.cluster_log
            is_extra_nocount = self.is_extra_nocount,
            is_extra_counts = self.is_extra_counts,
            is_choice_combi = self.is_choice_combi,
            pws_title = self.pws_title,
            pws_subjects = self.pws_subjects,
            has_exemption = self.has_exemption,
            has_reex = self.has_reex,
            has_reex03 = self.has_reex03,
            has_pok = self.has_pok,
            has_pok_status = self.has_pok_status,

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
        self.is_extra_nocount_mod = self.original_is_extra_nocount != self.is_extra_nocount
        self.is_extra_counts_mod = self.original_is_extra_counts != self.is_extra_counts
        self.is_choice_combi_mod = self.original_is_choice_combi != self.is_choice_combi
        self.pws_title_mod = self.original_pws_title != self.pws_title
        self.pws_subjects_mod = self.original_pws_subjects != self.pws_subjects
        self.has_exemption_mod = self.original_has_exemption != self.has_exemption
        self.has_reex_mod = self.original_has_reex != self.has_reex
        self.has_reex03_mod = self.original_has_reex03 != self.has_reex03
        self.has_pok_mod = self.original_has_pok != self.has_pok
        self.has_pok_status_mod = self.original_has_pok_status != self.has_pok_status

        data_changed_bool = (
            not self.is_update or

            self.student_mod or
            self.schemeitem_mod or
            self.cluster_mod or
            self.is_extra_nocount_mod or
            self.is_extra_counts_mod or
            self.is_choice_combi_mod or
            self.pws_title_mod or
            self.pws_subjects_mod or
            self.has_exemption_mod or
            self.has_reex_mod or
            self.has_reex03_mod or
            self.has_pok_mod or
            self.has_pok_status_mod
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

            sequence = item.schemeitem.subject.sequence * 1000 + item.schemeitem.subjecttype.sequence
            item_dict = {
                'mode': '-',
                'studsubj_id': item.id,
                'stud_id': item.student.id,
                'ssi_id': item.schemeitem.id
            }

            if item.schemeitem.is_mandatory:
                item_dict['ssi_mand'] = 1

            if item.schemeitem.is_combi:
                item_dict['ssi_comb'] = 1

            if item.schemeitem.extra_count_allowed:
                item_dict['ssi_exal'] = 1
                item_dict['extra_counts'] = (0, 1)[item.is_extra_counts],

            if item.schemeitem.extra_nocount_allowed:
                item_dict['ssi_exna'] = 1
                item_dict['extra_nocount'] = (0, 1)[item.is_extra_nocount],

            if item.schemeitem.choicecombi_allowed:
                item_dict['ssi_chal'] = 1
                item_dict['choice_combi'] = (0, 1)[item.is_choice_combi]

            if item.schemeitem.subject:
                item_dict['subj_id'] = item.schemeitem.subject.id
                item_dict['subj_name'] = item.schemeitem.subject.name
                item_dict['subj_sequ'] = item.schemeitem.subject.sequence

            if item.schemeitem.subjecttype:
                item_dict['sjtp_id'] = item.schemeitem.subjecttype.id
                item_dict['sjtp_name'] = item.schemeitem.subjecttype.abbrev

                if item.schemeitem.subjecttype.has_prac:
                    item_dict['sjtp_has_prac'] = 1  # (0, 1)[item.schemeitem.subjecttype.has_prac]

                if item.schemeitem.subjecttype.has_pws:
                    item_dict['sjtp_has_pws'] = 1  # (0, 1)[item.schemeitem.subjecttype.has_pws]

                    # add pws only if has_pws, then pws_title = '' when empty
                    pws_title = ''
                    if item.pws_title:
                        pws_title = item.pws_title
                    item_dict['pws_title'] = pws_title

                    pws_subjects = ''
                    if item.pws_subjects:
                        pws_subjects = item.pws_subjects
                    item_dict['pws_subjects'] = pws_subjects

                if item.schemeitem.subjecttype.one_allowed:
                    item_dict['sjtp_only_one'] = 1  #  (0, 1)[item.schemeitem.subjecttype.one_allowed]

            item_dict['sequence'] = sequence


            studentsubject_list.append(item_dict)

            #schemeitem = ForeignKey(Schemeitem, related_name='schemeitem_studsubs', on_delete=PROTECT)
            #cluster = ForeignKey(Cluster, null=True, blank=True, related_name='cluster_studsubs', on_delete=PROTECT)
            # # #
            #is_extra_nocount = BooleanField(default=False)
            #is_extra_counts = BooleanField(default=False)
            #is_choice_combi = BooleanField(default=False)
            # # # profielwerkstuk / sectorwerkstuk
            #pws_title = CharField(max_length=80, null=True, blank=True)
            #pws_subjects = CharField(max_length=80, null=True, blank=True)

        return studentsubject_list

# PR2018-06-06
class Studentsubject_log(Model):
    objects = CustomManager()
    studentsubject_id = IntegerField(db_index=True)

    # PR2019-02-14 changed: refer to log table student_log instead of student, to prevent ref_int with table student
    student_log = ForeignKey(Student_log, null=True, related_name='+', on_delete=PROTECT)
    schemeitem_log = ForeignKey(Schemeitem_log, null=True, related_name='+', on_delete=PROTECT)
    cluster_log = ForeignKey(Cluster_log,null=True,  related_name='+', on_delete=PROTECT)

    is_extra_nocount = BooleanField(default=False)
    is_extra_counts = BooleanField(default=False)
    is_choice_combi = BooleanField(default=False)

    pws_title = CharField(max_length=80, null=True, blank = True)
    pws_subjects = CharField(max_length=80, null=True, blank = True)

    has_exemption = BooleanField(default=False)
    has_reex = BooleanField(default=False)
    has_reex03 = BooleanField(default=False)
    has_pok = BooleanField(default=False)
    has_pok_status = CharField(max_length=12, null=True)

    #  mod variables
    student_log_mod = BooleanField(default=False)
    schemeitem_log_mod = BooleanField(default=False)
    cluster_log_mod = BooleanField(default=False)

    is_extra_nocount_mod = BooleanField(default=False)
    is_extra_counts_mod = BooleanField(default=False)
    is_choice_combi_mod = BooleanField(default=False)

    pws_title_mod = BooleanField(default=False)
    pws_subjects_mod = BooleanField(default=False)

    has_exemption_mod = BooleanField(default=False)
    has_reex_mod = BooleanField(default=False)
    has_reex03_mod = BooleanField(default=False)
    has_pok_mod = BooleanField(default=False)
    has_pok_status_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

# PR2018-106-17
class Studentsubjectnote(Model):
    objects = CustomManager()

    studentsubject = ForeignKey(Studentsubject, related_name='+', on_delete=PROTECT)

    note =  CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)
    is_insp = BooleanField(default=False)

    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField()

    # TODO: refer to log table studentsubject_log

# PR2018-106-17
class Studentsubjectnote_log(Model):
    objects = CustomManager()

    studentsubjectnote_id = IntegerField(db_index=True)

    studentsubject_log = ForeignKey(Studentsubject_log, related_name='+', on_delete=PROTECT)

    note = CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)
    is_insp = BooleanField(default=False)

    studentsubject_mod = BooleanField(default=False)
    note_mod = BooleanField(default=False)
    mailto_user_mod = BooleanField(default=False)
    is_insp_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

#==== GRADES ======================================================

# PR2018-06-06
class Grade(Model):
    objects = CustomManager()

    studentsubject = ForeignKey(Studentsubject, related_name='grades', on_delete=PROTECT)

    examcode = PositiveSmallIntegerField(db_index=True, default=0, choices=c.EXAMCODE_CHOICES)  # 1:se, 2:pe 3:ce, 4:ce2, 5:ce3, 6:se-exemption, 7:ce-exemption
    gradecode = PositiveSmallIntegerField(db_index=True, default=0, choices=c.GRADECODE_CHOICES) # s = score, g = grade, pe-ce, f = final grade
    period = PositiveSmallIntegerField(db_index=True, default=0, choices=c.PERIOD_CHOICES) # 1 = period 1, 2 = period 2, 3 = period 3
    value = CharField(max_length=4, null=True, blank=True)
    status = CharField(db_index=True, max_length=12, null=True, blank=True)
    published = BooleanField(db_index=True, default=False)

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
        self.original_gradecode = self.gradecode
        self.original_period = self.period
        self.original_value = self.value
        self.original_status = self.status
        self.original_published = self.published

        # PR2018-11-10 initialize here, otherwise delete gives error: 'Examyear' object has no attribute 'examyear_mod'
        # # # various fields - 6 fields
        self.examcode_mod = False
        self.gradecode_mod = False
        self.period_mod = False
        self.value_mod = False
        self.status_mod = False
        self.published_mod = False

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
            gradecode=self.gradecode,
            value=self.value,
            period=self.period,
            status=self.status,
            published=self.published,

            examcode_mod=self.examcode_mod,
            gradecode_mod=self.gradecode_mod,
            value_mod=self.value_mod,
            period_mod=self.period_mod,
            status_mod=self.status_mod,
            published_mod=self.published_mod,

            mode=self.mode,
            modified_by=self.modified_by,
            modified_at=self.modified_at
        )

    def data_has_changed(self, mode=None):  # PR2018-11-24
        # returns True when the value of one or more fields has changed PR2018-08-26
        self.is_update = self.id is not None # self.id is None before new record is saved

        self.studentsubject_mod = self.original_studentsubject != self.studentsubject

        self.examcode_mod = self.original_examcode != self.examcode
        self.gradecodemod = self.original_gradecode != self.gradecode
        self.value_mod = self.original_value != self.value
        self.period_mod = self.original_period != self.period
        self.status_mod = self.original_status != self.status
        self.published_mod = self.original_published != self.published

        data_changed_bool = (
            not self.is_update or
            self.studentsubject_mod or
            self.examcode_mod or
            self.gradecode_mod or
            self.value_mod or
            self.period_mod or
            self.status_mod or
            self.published_mod
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

    examcode = PositiveSmallIntegerField(default=0)
    gradecode = PositiveSmallIntegerField(default=0)
    value = CharField(max_length=4, null=True)
    published = BooleanField(default=False)
    status = CharField(max_length=12, null=True)

    examcode_mod = BooleanField(default=False)
    gradecode_mod = BooleanField(default=False)
    value_mod = BooleanField(default=False)
    published_mod = BooleanField(default=False)
    status_mod = BooleanField(default=False)

    mode = CharField(max_length=1, null=True)
    modified_by = ForeignKey(AUTH_USER_MODEL, related_name='+', on_delete=PROTECT)
    modified_at = DateTimeField(db_index=True)

    @property
    def mode_str(self):
        return f.get_mode_str(self)