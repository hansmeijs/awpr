# PR2018-07-20
from django.db.models import Model, Manager, ForeignKey, OneToOneField, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, \
    DecimalField, BooleanField, DateField, FileField

from django.db.models.functions import Lower

from django.utils import timezone

# PR2018-05-05 use AUTH_USER_MODEL
#from django.contrib.auth.models import User
#from accounts.models import User
from django.utils.translation import ugettext_lazy as _
from awpr.settings import AUTH_USER_MODEL
from awpr import constants as c
from awpr import functions as f

from schools import models as sch_mod

from schools.models import Examyear, Department, Department_log, School, School_log
from subjects.models import Level, Level_log, Sector, Sector_log, Scheme, Scheme_log, Schemeitem, Schemeitem_log,\
    Exam, Exam_log, Package, Package_log, Cluster, Cluster_log

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
class Birthcountry(sch_mod.AwpBaseModel):
    # PR2018-07-20 from https://stackoverflow.com/questions/3090302/how-do-i-get-the-object-if-it-exists-or-none-if-it-does-not-exist
    objects = CustomManager()

    name = CharField(max_length=c.MAX_LENGTH_NAME, unique=True)

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name


# PR2018-05-05
class Birthcountry_log(sch_mod.AwpBaseModel):
    objects = CustomManager()

    birthcountry_id = IntegerField(db_index=True)
    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    name_mod = BooleanField(default=False)
    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    def __str__(self):
        return self.name


# === Birthcity =====================================
class Birthplace(sch_mod.AwpBaseModel):
    objects = CustomManager()

    birthcountry = ForeignKey(Birthcountry, related_name='+', on_delete=CASCADE)
    name = CharField(max_length=c.MAX_LENGTH_NAME, unique=False)

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name


# PR2018-05-05
class Birthplace_log(sch_mod.AwpBaseModel):
    objects = CustomManager()

    birthplace_id = IntegerField(db_index=True)
    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    name_mod = BooleanField(default=False)
    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    def __str__(self):
        return self.name


# =================
class Studentbase(Model):# PR2018-10-17 PR2020-12-07
    objects = CustomManager()
    country = ForeignKey(sch_mod.Country, related_name='+', on_delete=PROTECT)


class Student(sch_mod.AwpBaseModel):# PR2018-06-06, 2018-09-05
    objects = CustomManager()

    base = ForeignKey(Studentbase, related_name='students', on_delete=PROTECT)

    school = ForeignKey(School, related_name='students', on_delete=CASCADE)
    department = ForeignKey(Department, related_name='students', on_delete=CASCADE)
    level = ForeignKey(Level, null=True, blank=True, related_name='students', on_delete=SET_NULL)
    sector = ForeignKey(Sector, null=True,blank=True, related_name='students', on_delete=SET_NULL)
    scheme = ForeignKey(Scheme, null=True, blank=True, related_name='students', on_delete=SET_NULL)
    package = ForeignKey(Package, null=True, blank=True, related_name='students', on_delete=SET_NULL)

    lastname = CharField(db_index=True, max_length=c.MAX_LENGTH_FIRSTLASTNAME)
    firstname= CharField(db_index=True, max_length=c.MAX_LENGTH_FIRSTLASTNAME)
    prefix= CharField(null=True, blank=True, max_length=c.MAX_LENGTH_10)
    gender= CharField(null=True, blank=True, max_length=c.MAX_LENGTH_01)
    idnumber= CharField(db_index=True, null=True, blank=True, max_length=c.MAX_LENGTH_IDNUMBER)
    birthdate= DateField(null=True, blank=True)
    birthcountry= CharField(max_length=c.USER_LASTNAME_MAX_LENGTH, null=True, blank=True)
    birthcity= CharField(max_length=c.USER_LASTNAME_MAX_LENGTH, null=True, blank=True)

    classname = CharField(null=True, blank=True, max_length=c.MAX_LENGTH_EXAMNUMBER)
    examnumber = CharField(db_index=True, null=True, blank=True, max_length=c.MAX_LENGTH_EXAMNUMBER)
    regnumber = CharField(null=True, blank=True, max_length=c.MAX_LENGTH_EXAMNUMBER)
    diplomanumber = CharField(null=True, blank=True, max_length=c.MAX_LENGTH_10)
    gradelistnumber = CharField(null=True, blank=True, max_length=c.MAX_LENGTH_10)

    iseveningstudent = BooleanField(default=False)
    islexstudent = BooleanField(default=False)
    hasdyslexia = BooleanField(default=False)

    locked = BooleanField(default=False)
    has_reex = BooleanField(default=False)
    bis_exam= BooleanField(default=False)
    withdrawn = BooleanField(default=False)

    class Meta:
        ordering = [Lower('lastname'), Lower('firstname')]

    def __str__(self):
        _fullname = str(self.lastname) + ', ' + str(self.firstname)
        return _fullname

    @property
    def fullname(self):
        # PR2019-01-13 is str() necessary?.
        # PR2020-12-07 Yes, must convert class 'CharField' to String,
        # otherwise self.lastname.strip()  gets error: Unresolved attribute reference 'strip' for class 'CharField'
        last_name = str(self.lastname) if self.lastname else ''
        first_name = str(self.firstname) if self.firstname else ''
        prefix_str = str(self.prefix) if self.prefix else ''
        full_name = ''
        if last_name:
            full_name = last_name.strip()  # Trim
        if prefix_str: # put prefix before last_name
            full_name = prefix_str.strip() + ' ' + full_name
        if first_name:  # put first_name after last_name
            full_name += ', ' + first_name.strip()
        return full_name

    @property
    def fullnamewithinitials(self):
        # PR2019-01-13 is str() necessary?.
        # PR2020-12-07 Yes, must convert class 'CharField' to String,
        # otherwise self.lastname.strip()  gets error: Unresolved attribute reference 'strip' for class 'CharField'
        last_name = str(self.lastname) if self.lastname else ''
        first_name = str(self.firstname) if self.firstname else ''
        prefix_str = str(self.prefix) if self.prefix else ''
        full_name = ''

        if last_name:
            full_name = last_name.strip()  # Trim
        if prefix_str: # put prefix before last_name
            full_name = prefix_str.strip() + ' ' + full_name
        first_names = ''
        first_name_stripped = first_name.strip()
        if ' ' in first_name_stripped:
            arr = first_name_stripped.split()
            get_initial = False
            initials = ''
            for a in arr:
                if not get_initial:
                    first_names = a
                    get_initial = True
                else:
                    a_strip = a.strip()
                    if a_strip:
                        initials += a_strip[0:1].upper()
            if initials:
                first_names += ' ' + initials
        full_name += ', ' + first_names
        return full_name

    @property
    def has_no_child_rows(self):  # PR2018-11-20
        # TODO add search for linked data
        return True


# PR2018-06-08
class Student_log(sch_mod.AwpBaseModel):
    objects = CustomManager()

    student_id = IntegerField(db_index=True)

    base = ForeignKey(Studentbase, related_name='+', on_delete=PROTECT)

    school_log = ForeignKey(School_log, related_name='+', on_delete=CASCADE)
    dep_log = ForeignKey(Department_log, related_name='+', on_delete=CASCADE)
    level_log = ForeignKey(Level_log, null=True, related_name='+', on_delete=SET_NULL)
    sector_log = ForeignKey(Sector_log, null=True, related_name='+', on_delete=SET_NULL)
    scheme_log = ForeignKey(Scheme_log, null=True, related_name='+', on_delete=SET_NULL)
    package_log = ForeignKey(Package_log, null=True, related_name='+', on_delete=SET_NULL)

    lastname = CharField(db_index=True, max_length=c.MAX_LENGTH_FIRSTLASTNAME)
    firstname = CharField(db_index=True, max_length=c.MAX_LENGTH_FIRSTLASTNAME)
    prefix = CharField(max_length=c.MAX_LENGTH_10, null=True, blank=True)
    gender = CharField(db_index=True, max_length=c.MAX_LENGTH_01, null=True)
    idnumber = CharField(db_index=True, max_length=c.MAX_LENGTH_IDNUMBER)
    birthdate = DateField(null=True)
    birthcountry = CharField(max_length=c.USER_LASTNAME_MAX_LENGTH, null=True)
    birthcity = CharField(max_length=c.USER_LASTNAME_MAX_LENGTH, null=True)

    classname = CharField(db_index=True, max_length=c.MAX_LENGTH_EXAMNUMBER, null=True, blank=True)
    examnumber = CharField(db_index=True, max_length=c.MAX_LENGTH_EXAMNUMBER, null=True, blank=True)
    regnumber = CharField(db_index=True, max_length=c.MAX_LENGTH_EXAMNUMBER, null=True, blank=True)
    diplomanumber = CharField(max_length=c.MAX_LENGTH_10, null=True, blank=True)
    gradelistnumber = CharField(max_length=c.MAX_LENGTH_10, null=True, blank=True)

    iseveningstudent = BooleanField(default=False)
    hasdyslexia = BooleanField(default=False)

    locked = BooleanField(default=False)
    has_reex = BooleanField(default=False)
    bis_exam = BooleanField(default=False)
    withdrawn = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    @property
    def mode_str(self):
        return c.get_mode_str(self)

##########################################################################

# ====Result=============
class Result(sch_mod.AwpBaseModel):# PR2018-11-10
    objects = CustomManager()

    student = ForeignKey(Student, related_name='results', on_delete=CASCADE)
    examperiod = PositiveSmallIntegerField(db_index=True, default=1) # 1 = period 1, 2 = period 2, 3 = period 3

    grade_ce_avg = DecimalField(max_digits=5, decimal_places=2, default = 0)
    grade_ce_avg_text = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)
    grade_combi_avg_text = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)

    endgrade_sum = PositiveSmallIntegerField(default=0)
    endgrade_count = PositiveSmallIntegerField(default=0)
    endgrade_avg = DecimalField(max_digits=5, decimal_places=2, default = 0)
    endgrade_avg_text = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)

    result = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_info = CharField(db_index=True, max_length=80, null=True, blank=True)
    result_status = CharField(max_length=c.MAX_LENGTH_12, null=True, blank=True)


# PR2018-06-08
class Result_log(sch_mod.AwpBaseModel):
    objects = CustomManager()
    # TODO bind to student
    result_id = IntegerField(db_index=True)

    grade_ce_avg = DecimalField(max_digits=5, decimal_places=2, default=0)
    grade_ce_avg_text = CharField(max_length=c.MAX_LENGTH_10, null=True, blank=True)
    grade_combi_avg_text = CharField(max_length=c.MAX_LENGTH_10, null=True, blank=True)

    endgrade_sum = PositiveSmallIntegerField(default=0)
    endgrade_count = PositiveSmallIntegerField(default=0)
    endgrade_avg = CharField(max_length=c.MAX_LENGTH_10, null=True, blank=True)
    endgrade_avg_text = CharField(max_length=c.MAX_LENGTH_10, null=True, blank=True)

    result = PositiveSmallIntegerField(db_index=True,default=0, choices=c.RESULT_CHOICES)
    result_info = CharField(max_length=80, null=True, blank=True)

    result_status = CharField(max_length=c.MAX_LENGTH_12, null=True)

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

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# PR2018-106-17
class Resultnote(sch_mod.AwpBaseModel):
    objects = CustomManager()

    # PR2019-02-14 changed: refer to log table student_log instead of student, to prevent ref_int with table student
    student = ForeignKey(Student, null=True, related_name='+', on_delete=CASCADE)

    resultnote =  CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)

    is_insp = BooleanField(default=False)


# PR2018-106-17
class Resultnote_log(sch_mod.AwpBaseModel):
    objects = CustomManager()

    resultnote_id = IntegerField(db_index=True)
    # TODO: refer to log table
    # PR2019-02-14 changed: refer to log table student_log instead of student, to prevent ref_int with table student
    student_log = ForeignKey(Student_log, null=True, related_name='+', on_delete=CASCADE)

    resultnote = CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)

    is_insp = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# ======= Student subject =========== PR2018-06-06 PR19=018-11-19
class Studentsubject(sch_mod.AwpBaseModel):
    objects = CustomManager()

    student = ForeignKey(Student, related_name='+', on_delete=CASCADE)
    schemeitem = ForeignKey(Schemeitem, related_name='+', on_delete=PROTECT)
    cluster = ForeignKey(Cluster, null=True, blank=True, related_name='+', on_delete=SET_NULL)

    is_extra_nocount = BooleanField(default=False)
    is_extra_counts = BooleanField(default=False)
    is_elective_combi = BooleanField(default=False)

    pws_title = CharField(max_length=80, null=True, blank = True)
    pws_subjects = CharField(max_length=80, null=True, blank = True)

    has_exemption = BooleanField(default=False)
    has_reex = BooleanField(default=False)
    has_reex03 = BooleanField(default=False)
    has_pok = BooleanField(default=False)  # proof of knowledge

    subj_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    subj_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    subj_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    exem_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    exem_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    exem_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    reex_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    reex3_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex3_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex3_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    pok_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pok_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pok_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    has_schoolnotes = BooleanField(default=False)
    has_inspnotes = BooleanField(default=False)
    note_status = PositiveSmallIntegerField(default=0)

    deleted = BooleanField(default=False)


# PR2018-06-06
class Studentsubject_log(sch_mod.AwpBaseModel):
    objects = CustomManager()
    studentsubject_id = IntegerField(db_index=True)

    # PR2019-02-14 changed: refer to log table student_log instead of student, to prevent ref_int with table student
    student_log = ForeignKey(Student_log, null=True, related_name='+', on_delete=CASCADE)
    schemeitem_log = ForeignKey(Schemeitem_log, null=True, related_name='+', on_delete=SET_NULL)
    cluster_log = ForeignKey(Cluster_log,null=True,  related_name='+', on_delete=SET_NULL)

    is_extra_nocount = BooleanField(default=False)
    is_extra_counts = BooleanField(default=False)
    is_elective_combi = BooleanField(default=False)

    pws_title = CharField(max_length=80, null=True, blank = True)
    pws_subjects = CharField(max_length=80, null=True, blank = True)

    has_exemption = BooleanField(default=False)
    has_reex = BooleanField(default=False)
    has_reex03 = BooleanField(default=False)
    has_pok = BooleanField(default=False)

    subj_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    subj_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    subj_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    exem_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    exem_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    exem_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    reex_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    reex3_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex3_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex3_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    pok_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pok_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pok_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    has_schoolnotes = BooleanField(default=False)
    has_inspnotes = BooleanField(default=False)
    note_status = PositiveSmallIntegerField(default=0)

    deleted = BooleanField(default=False)
    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# PR2018-106-17
class Studentsubjectnote(sch_mod.AwpBaseModel):
    objects = CustomManager()

    studentsubject = ForeignKey(Studentsubject, related_name='+', on_delete=CASCADE)

    note = CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)
    is_insp = BooleanField(default=False)  # False: school note True: insp / admin note PR2021-01-16
    is_public = BooleanField(default=False)  # True: visbible for schools and insp / admin PR2021-01-16

    # TODO: refer to log table studentsubject_log


# PR2018-106-17
class Studentsubjectnote_log(sch_mod.AwpBaseModel):
    objects = CustomManager()

    studentsubjectnote_id = IntegerField(db_index=True)

    studentsubject_log = ForeignKey(Studentsubject_log, related_name='+', on_delete=CASCADE)

    note = CharField(max_length=2048, null=True, blank=True)
    mailto_user = CharField(max_length=2048, null=True, blank=True)

    is_insp = BooleanField(default=False)  # False: school note True: insp / admin note PR2021-01-16
    is_public = BooleanField(default=False)  # True: visbible for schools and insp / admin PR2021-01-16

    studentsubject_mod = BooleanField(default=False)
    note_mod = BooleanField(default=False)
    mailto_user_mod = BooleanField(default=False)
    is_insp_mod = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

#==== GRADES ======================================================

# PR2018-06-06
class Grade(sch_mod.AwpBaseModel):
    objects = CustomManager()

    studentsubject = ForeignKey(Studentsubject, related_name='+', on_delete=CASCADE)

    examperiod = PositiveSmallIntegerField(db_index=True, default=1) # 1 = period 1, 2 = period 2, 3 = period 3, 4 = exemption

    pescore = PositiveSmallIntegerField(null=True)
    cescore = PositiveSmallIntegerField(null=True)

    segrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    cegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pecegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    finalgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)

    se_status = PositiveSmallIntegerField(default=0)
    se_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    pe_status = PositiveSmallIntegerField(default=0)
    pe_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    ce_status = PositiveSmallIntegerField(default=0)
    ce_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    deleted = BooleanField(default=False)
    status = PositiveSmallIntegerField(default=0)


# PR2018-06-06
class Grade_log(sch_mod.AwpBaseModel):
    objects = CustomManager()

    grade_id = IntegerField(db_index=True)

    studentsubject_log = ForeignKey(Studentsubject_log, related_name='+', on_delete=CASCADE)

    examperiod = PositiveSmallIntegerField(db_index=True, default=1) # 1 = period 1, 2 = period 2, 3 = period 3, 4 = exemption

    pescore = PositiveSmallIntegerField(null=True)
    cescore = PositiveSmallIntegerField(null=True)

    segrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    cegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pecegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    finalgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)

    se_status = PositiveSmallIntegerField(default=0)
    se_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    pe_status = PositiveSmallIntegerField(default=0)
    pe_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    ce_status = PositiveSmallIntegerField(default=0)
    ce_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    deleted = BooleanField(default=False)
    status = PositiveSmallIntegerField(default=0)
    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    @property
    def mode_str(self):
        return f.get_mode_str(self)

# PR2021-03-04
class Examresult(sch_mod.AwpBaseModel):
    objects = CustomManager()

    studentsubject = ForeignKey(Studentsubject, related_name='+', on_delete=CASCADE)

    exam = ForeignKey(Exam, related_name='+', on_delete=CASCADE)
    examperiod = PositiveSmallIntegerField(db_index=True,
                                           default=1)  # 1 = period 1, 2 = period 2, 3 = period 3, 4 = exemption

    examtype = CharField(max_length=c.MAX_LENGTH_10, db_index=True)

    result = CharField(max_length=2048, null=True, blank=True)

    auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)


class Examresult_log(sch_mod.AwpBaseModel):
    objects = CustomManager()

    answer_id = IntegerField(db_index=True)

    studentsubject_log = ForeignKey(Studentsubject_log, related_name='+', on_delete=CASCADE)

    examperiod = PositiveSmallIntegerField(db_index=True, default=1)  # 1 = period 1, 2 = period 2, 3 = period 3, 4 = exemption

    examtype = CharField(max_length=c.MAX_LENGTH_10, db_index=True)

    result = CharField(max_length=2048, null=True, blank=True)

    auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

