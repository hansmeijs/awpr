# PR2018-07-20
from django.db.models import Model, Manager, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, \
    BooleanField, DateField, DateTimeField, FileField

from django.utils import timezone
from django.db.models.functions import Lower

# PR2018-05-05 use AUTH_USER_MODEL
from awpr.settings import AUTH_USER_MODEL
from awpr.storage_backends import PrivateMediaStorage
from awpr import constants as c

from schools import models as sch_mod
from subjects import models as subj_mod

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


class Student(sch_mod.AwpBaseModel):# PR2018-06-06, 2018-09-05
    objects = CustomManager()

    base = ForeignKey(Studentbase, related_name='students', on_delete=PROTECT)

    school = ForeignKey(sch_mod.School, related_name='students', on_delete=PROTECT)
    department = ForeignKey(sch_mod.Department, related_name='students', on_delete=PROTECT)
    level = ForeignKey(subj_mod.Level, null=True, blank=True, related_name='students', on_delete=SET_NULL)
    sector = ForeignKey(subj_mod.Sector, null=True,blank=True, related_name='students', on_delete=SET_NULL)
    scheme = ForeignKey(subj_mod.Scheme, null=True, blank=True, related_name='students', on_delete=SET_NULL)
    package = ForeignKey(subj_mod.Package, null=True, blank=True, related_name='students', on_delete=SET_NULL)

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

    # PR2022-07-30 length of diploma- and gradelist number changed from 10 to 20
    diplomanumber = CharField(null=True, blank=True, max_length=c.MAX_LENGTH_EXAMNUMBER)
    gradelistnumber = CharField(null=True, blank=True, max_length=c.MAX_LENGTH_EXAMNUMBER)

    extrafacilities = BooleanField(default=False)
    iseveningstudent = BooleanField(default=False)
    islexstudent = BooleanField(default=False)
    bis_exam = BooleanField(default=False)
    partial_exam = BooleanField(default=False)  # get certificate, only when evening- or lexstudent

    # PR2022-08-22 - is ok when subjects composition is correct. Inspection can give dispensation
    subj_composition_checked = BooleanField(default=False)
    subj_composition_ok = BooleanField(default=False)
    subj_dispensation = BooleanField(default=False)
    subj_disp_modifiedby = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    subj_disp_modifiedat = DateTimeField(default=timezone.now, null=True)

    # additional_exam is deprecated, field partial_exam is used (additional_exam is partial_exam on a day school
    # additional_exam =  when student does extra subject at a different school, possible in day/evening/lex school, only valid in the same examyear

    # notlinked contains ';'-delimited list of student_id's with the same idnumber, but that are not the same student
    # islinked = BooleanField(default=False)
    linked = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)
    notlinked = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)

    exemption_count = PositiveSmallIntegerField(default=0)
    sr_count = PositiveSmallIntegerField(default=0)
    reex_count = PositiveSmallIntegerField(default=0)
    reex03_count = PositiveSmallIntegerField(default=0)
    thumbrule_count = PositiveSmallIntegerField(default=0)

    # TODO deprecate is_reex_cand etc, replaced by reex_count
    #is_reex_cand = BooleanField(default=False)
    #is_reex03_cand = BooleanField(default=False)
    #is_sr_cand = BooleanField(default=False)  # student who has done 'herkansing' (SE-reexamination)
    withdrawn = BooleanField(default=False)

    ep01_ce_avg = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)
    ep01_combi_avg = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    ep01_final_avg = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)
    ep01_result = PositiveSmallIntegerField(db_index=True,default=0)

    ep02_ce_avg = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)
    ep02_combi_avg = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    ep02_final_avg = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)
    ep02_result = PositiveSmallIntegerField(db_index=True,default=0)

    gl_ce_avg = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)
    gl_combi_avg = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    gl_final_avg = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)

    result = PositiveSmallIntegerField(db_index=True,default=0)
    result_status = CharField(max_length=c.MAX_LENGTH_KEY, null=True, blank=True)
    result_info = CharField(max_length=2048, null=True, blank=True)

    # TODO create these fields PR2023-04-08
    # only when result is approved by inspection, gradelist and diploma can be printed PR2023-04-08
    #resultapproved = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    #resultapproved_at = DateTimeField(null=True)

    tobedeleted = BooleanField(default=False)
    deleted = BooleanField(default=False)

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

    school_log = ForeignKey(sch_mod.School_log, related_name='+', on_delete=CASCADE)
    department_log = ForeignKey(sch_mod.Department_log, related_name='+', on_delete=CASCADE)
    level_log = ForeignKey(subj_mod.Level_log, null=True, related_name='+', on_delete=SET_NULL)
    sector_log = ForeignKey(subj_mod.Sector_log, null=True, related_name='+', on_delete=SET_NULL)
    scheme_log = ForeignKey(subj_mod.Scheme_log, null=True, related_name='+', on_delete=SET_NULL)
    package_log = ForeignKey(subj_mod.Package_log, null=True, related_name='+', on_delete=SET_NULL)

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

    # PR 2022-07-30 length of diploma- and gradelist number changed from 10 to 20
    diplomanumber = CharField(max_length=c.MAX_LENGTH_EXAMNUMBER, null=True, blank=True)
    gradelistnumber = CharField(max_length=c.MAX_LENGTH_EXAMNUMBER, null=True, blank=True)

    extrafacilities = BooleanField(default=False)
    iseveningstudent = BooleanField(default=False)
    islexstudent = BooleanField(default=False)
    bis_exam = BooleanField(default=False)
    partial_exam = BooleanField(default=False)  # gets a certificate, only when evening- or lexstudent

    # additional_exam is deprecated, field partial_exam is used (additional_exam is partial_exam on a day school
    # additional_exam = when student does extra subject at a different school, possible in day/evening/lex school, only valid in the same examyear

    # PR2022-08-22 - is ok when subjects composition is correct. Inspection can give dispensation
    subj_composition_checked = BooleanField(default=False)
    subj_composition_ok = BooleanField(default=False)
    subj_dispensation = BooleanField(default=False)
    subj_disp_modifiedby = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    subj_disp_modifiedat = DateTimeField(default=timezone.now, null=True)

    # islinked = BooleanField(default=False)
    linked = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)
    notlinked = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)

    exemption_count = PositiveSmallIntegerField(default=0)
    sr_count = PositiveSmallIntegerField(default=0)
    reex_count = PositiveSmallIntegerField(default=0)
    reex03_count = PositiveSmallIntegerField(default=0)
    thumbrule_count = PositiveSmallIntegerField(default=0)

    # TODO deprecate is_reex_cand is_reex03_cand, is_sr_cand -> is replaced by reex_count
    #is_reex_cand = BooleanField(default=False)
    #is_reex03_cand = BooleanField(default=False)
    #is_sr_cand = BooleanField(default=False)  # student who has done 'herkansing' (SE-reexamination)
    withdrawn = BooleanField(default=False)

    ep01_ce_avg = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)
    ep01_combi_avg = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    ep01_final_avg = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)
    ep01_result = PositiveSmallIntegerField(db_index=True,default=0)

    ep02_ce_avg = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)
    ep02_combi_avg = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    ep02_final_avg = CharField(db_index=True, max_length=c.MAX_LENGTH_10, null=True, blank=True)
    ep02_result = PositiveSmallIntegerField(db_index=True,default=0)

    gl_ce_avg = CharField(max_length=c.MAX_LENGTH_10, null=True, blank=True)
    gl_combi_avg = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    gl_final_avg = CharField(max_length=c.MAX_LENGTH_10, null=True, blank=True)

    result = PositiveSmallIntegerField(db_index=True, default=0)
    result_status = CharField(max_length=c.MAX_LENGTH_KEY, null=True, blank=True)
    result_info = CharField(max_length=2048, null=True, blank=True)

    # TODO create these fields PR2023-04-08
    #resultapproved = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    #resultapproved_at = DateTimeField(null=True)

    tobedeleted = BooleanField(default=False)
    deleted = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    @property
    def mode_str(self):
        return c.get_mode_str(self)


# PR2018-106-17 PR2021-07-02
class Studentnote(sch_mod.AwpBaseModel):
    objects = CustomManager()

    # PR2019-02-14 changed: refer to log table student_log instead of student, to prevent ref_int with table student
    student = ForeignKey(Student, null=True, related_name='+', on_delete=CASCADE)

    # intern_schoolbase only has value when it is an intern memo.
    # It has the value of the school of the user, NOT the school of the student
    intern_schoolbase = ForeignKey(sch_mod.Schoolbase, related_name='+', null=True, on_delete=SET_NULL)

    note = CharField(max_length=2048, null=True, blank=True)
    recipients = CharField(max_length=2048, null=True, blank=True)
    note_status = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)


# PR2018-106-17 PR2021-07-02
class Studentnote_log(sch_mod.AwpBaseModel):
    objects = CustomManager()

    studentnote_id = IntegerField(db_index=True)

    # PR2019-02-14 changed: refer to log table student_log instead of student, to prevent ref_int with table student
    student_log = ForeignKey(Student_log, null=True, related_name='+', on_delete=CASCADE)

    # intern_schoolbase only has value when it is an intern memo.
    # It has the value of the school of the user, NOT the school of the student
    intern_schoolbase = ForeignKey(sch_mod.Schoolbase, related_name='+', null=True, on_delete=SET_NULL)

    note = CharField(max_length=2048, null=True, blank=True)
    recipients = CharField(max_length=2048, null=True, blank=True)
    note_status = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# ======= Student subject =========== PR2018-06-06 PR19=018-11-19
class Studentsubject(sch_mod.AwpBaseModel):
    objects = CustomManager()

    student = ForeignKey(Student, related_name='+', on_delete=CASCADE)

    # subject not in use (yet). Linked with subject.subject
    subject = ForeignKey(subj_mod.Subject, null=True, related_name='+', on_delete=PROTECT)
    schemeitem = ForeignKey(subj_mod.Schemeitem, related_name='+', on_delete=PROTECT)

    cluster = ForeignKey(subj_mod.Cluster, null=True, blank=True, related_name='+', on_delete=SET_NULL)

    is_extra_nocount = BooleanField(default=False)
    is_extra_counts = BooleanField(default=False)
    is_thumbrule = BooleanField(default=False)

    pws_title = CharField(max_length=80, null=True, blank = True)
    pws_subjects = CharField(max_length=80, null=True, blank = True)

    has_exemption = BooleanField(default=False)
    has_sr = BooleanField(default=False)  # has se_reex (herkansing)
    has_reex = BooleanField(default=False)
    has_reex03 = BooleanField(default=False)

    # deprecated, replaced by pok_validthru = NOT NULL
    #has_pok = BooleanField(default=False)  # proof of knowledge  (for day school)
    #has_pex = BooleanField(default=False)  # proof of exemption (for evening school, lex school)

    #  exemption_year to be added in 2023
    exemption_year = PositiveSmallIntegerField(null=True)  # examyear of exemption, to determine if has no CE (year 2020, also for some subjects in 2021)

    # has proof of knowledge = True when pok_validthru has value PR2021-09-07
    pok_validthru = PositiveSmallIntegerField(null=True)

    # PR2022-07-30 pok_sesr etc added, to store proof of knowledge / proof of exemption
    pok_sesr = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pok_pece = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pok_final = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)

    subj_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    subj_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    subj_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    # 'tobechanged' is set True when schemeitem (=subjecttype) changes, it must be submitted again
    tobechanged = BooleanField(default=False)
    tobedeleted = BooleanField(default=False)
    deleted = BooleanField(default=False)

    prev_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    prev_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    prev_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    # TODO deprecate exem_auth1by, exem_published only grades must be authorized
    exem_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    exem_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    exem_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    sr_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    reex_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    reex3_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex3_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex3_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    pok_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pok_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pok_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    gradelist_sesrgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    gradelist_pecegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    gradelist_finalgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    gradelist_use_exem = BooleanField(default=False)

    # PR2022-01-02 added: no input info and max_ep
    gl_ni_se = BooleanField(default=False)
    gl_ni_sr = BooleanField(default=False)
    gl_ni_pe = BooleanField(default=False)
    gl_ni_ce = BooleanField(default=False)
    gl_examperiod = PositiveSmallIntegerField(null=True)


# PR2018-06-06
class Studentsubject_log(sch_mod.AwpBaseModel):
    objects = CustomManager()
    studentsubject_id = IntegerField(db_index=True)

    # PR2019-02-14 changed: refer to log table student_log instead of student, to prevent ref_int with table student
    student_log = ForeignKey(Student_log, null=True, related_name='+', on_delete=CASCADE)
    subject_log = ForeignKey(subj_mod.Subject_log, null=True, related_name='+', on_delete=SET_NULL)
    schemeitem_log = ForeignKey(subj_mod.Schemeitem_log, null=True, related_name='+', on_delete=SET_NULL)

    cluster_log = ForeignKey(subj_mod.Cluster_log,null=True, related_name='+', on_delete=SET_NULL)

    is_extra_nocount = BooleanField(default=False)
    is_extra_counts = BooleanField(default=False)
    is_thumbrule = BooleanField(default=False)

    pws_title = CharField(max_length=80, null=True, blank = True)
    pws_subjects = CharField(max_length=80, null=True, blank = True)

    has_exemption = BooleanField(default=False)  # PR2022-06-10 this field will be recalculated in calc_result
    has_sr = BooleanField(default=False)  # has se_reex (herkansing) ,only possible when si.sr_allowed
    has_reex = BooleanField(default=False)  # PR2022-06-10 this field will be recalculated in calc_result
    has_reex03 = BooleanField(default=False) # only possible when no_thirdperiod = False  # PR2022-06-10 this field will be recalculated in calc_result

    # deprecated, replaced by pok_validthru = NOT NULL
    #has_pok = BooleanField(default=False) # proof of knowledge  (for day school)
    #has_pex = BooleanField(default=False)  # proof of exemption (for evening school, lex school)

    exemption_year = PositiveSmallIntegerField(null=True)  # examyear of exemption, to determine if has no CE (year 2020)

    # has proof of knowledge = True when pok_validthru has value PR2021-09-07
    pok_validthru = PositiveSmallIntegerField(null=True)

    # PR2022-07-30 pok_sesr etc added, to store proff of knowledge / proof of exemption
    pok_sesr = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pok_pece = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pok_final = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)

    subj_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    subj_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    subj_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    tobedeleted = BooleanField(default=False)
    deleted = BooleanField(default=False)

    prev_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    prev_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    prev_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    exem_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    exem_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    exem_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    sr_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    reex_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    reex3_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex3_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    reex3_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    pok_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pok_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pok_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    # TODO deprecate
    #ex_max_segrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    #ex_max_pecegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    #ex_max_finalgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    #reex_max_segrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    #reex_max_pecegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    #reex_max_finalgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    #reex3_max_segrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    #reex3_max_pecegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    #reex3_max_finalgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)

    gradelist_sesrgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    gradelist_pecegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    gradelist_finalgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    gradelist_use_exem = BooleanField(default=False)

    # PR2022-01-02 added: no input info and max_ep
    gl_ni_se = BooleanField(default=False)
    gl_ni_sr = BooleanField(default=False)
    gl_ni_pe = BooleanField(default=False)
    gl_ni_ce = BooleanField(default=False)
    gl_examperiod = PositiveSmallIntegerField(null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


class Studentsubjectnote(sch_mod.AwpBaseModel):
    objects = CustomManager()

    studentsubject = ForeignKey(Studentsubject, related_name='+', on_delete=CASCADE)

    # intern_schoolbase only has value when it is an intern memo.
    # It has the value of the school of the user, NOT the school of the student
    intern_schoolbase = ForeignKey(sch_mod.Schoolbase, related_name='+', null=True, on_delete=SET_NULL)

    note = CharField(max_length=2048, null=True, blank=True)
    recipients = CharField(max_length=2048, null=True, blank=True)
    note_status = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)


class Studentsubjectnote_log(sch_mod.AwpBaseModel):
    objects = CustomManager()

    studentsubjectnote_id = IntegerField(db_index=True)

    studentsubject_log = ForeignKey(Studentsubject_log, related_name='+', on_delete=CASCADE)
    intern_schoolbase = ForeignKey(sch_mod.Schoolbase, related_name='+', null=True, on_delete=SET_NULL)

    note = CharField(max_length=2048, null=True, blank=True)
    recipients = CharField(max_length=2048, null=True, blank=True)
    note_status = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# PR2021-03-08 from https://simpleisbetterthancomplex.com/tutorial/2017/08/01/how-to-setup-amazon-s3-in-a-django-project.html
# PR2021-03-13 test
class Noteattachment(sch_mod.AwpBaseModel):
    objects = CustomManager()

    studentsubjectnote = ForeignKey(Studentsubjectnote, related_name='+', on_delete=CASCADE)
    contenttype = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)
    filename = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME)
    file = FileField(storage=PrivateMediaStorage())


#==== GRADES ======================================================
# PR2018-06-06
class Grade(sch_mod.AwpBaseModel):
    objects = CustomManager()

    studentsubject = ForeignKey(Studentsubject, related_name='+', on_delete=CASCADE)

    # TODO deprecated, use pe_exam and ce_exam
    # exam = ForeignKey(subj_mod.Exam, related_name='+', null=True, on_delete=SET_NULL)

    examperiod = PositiveSmallIntegerField(db_index=True, default=1) # 1 = period 1, 2 = period 2, 3 = period 3, 4 = exemption

    # NOTE: total wolf score was stored in pescore, is moved to ce_exam_score PR2022-05-15
    pescore = PositiveSmallIntegerField(null=True)
    cescore = PositiveSmallIntegerField(null=True)

    # PR2021-11-22 from now grades are saved with dots instead of comma's,
    #  so they can be used by Decimal() without having to convert to dots
    #  replace by comma's when printing gradelist and reports

    segrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    srgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    sesrgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)

    pegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    cegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pecegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    finalgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)

    #   se_blocked etc is True when Inspectorate has blocked the subject from gradelist, until it is changed
    #   when blocked is set True, published_id  and all auth_id will be erased, so the school can submit the grade again

    se_status = PositiveSmallIntegerField(default=0)
    se_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_auth4by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    se_blocked = BooleanField(default=False)

    # sr = se_reex = herkansing schoolexamen PR2021-05-01
    sr_status = PositiveSmallIntegerField(default=0)
    sr_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_auth4by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    sr_blocked = BooleanField(default=False)

    pe_status = PositiveSmallIntegerField(default=0)
    pe_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_auth4by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    pe_blocked = BooleanField(default=False)

    ce_status = PositiveSmallIntegerField(default=0)
    ce_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_auth4by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    ce_blocked = BooleanField(default=False)

    # 'pe_exam' is not in use. Let it stay in case they want to introduce pe-exam again PR2022-01-19
    pe_exam = ForeignKey(subj_mod.Exam, related_name='+', null=True, on_delete=SET_NULL)
    #pe_exam_blanks = PositiveSmallIntegerField(null=True)
    pe_exam_result = CharField(max_length=2048, null=True)
    pe_exam_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_exam_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    # PR2022-05-14 added
    pe_exam_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_exam_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    pe_exam_blocked = BooleanField(default=False)

    # NOTE: total score was stored in pescore, is moved to ce_exam_score PR2022-05-15
    ce_exam = ForeignKey(subj_mod.Exam, related_name='+', null=True, on_delete=SET_NULL)
    ce_exam_blanks = PositiveSmallIntegerField(null=True)
    ce_exam_result = CharField(max_length=2048, null=True)
    ce_exam_score = PositiveSmallIntegerField(null=True)   # PR2022-05-14 added

    ce_exam_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_exam_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_exam_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)   # PR2022-05-14 added
    ce_exam_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    ce_exam_blocked = BooleanField(default=False)

    # PR2023-01-24 added, to skip approval when imported
    exemption_imported = BooleanField(default=False)

    # TODO deprecate tobedeleted, only deleted is used PR2023-01-24
    tobedeleted = BooleanField(default=False)
    deleted = BooleanField(default=False)

    # TODO deprecate
    del_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    del_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    del_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    status = PositiveSmallIntegerField(default=0)


# PR2018-06-06
class Grade_log(sch_mod.AwpBaseModel):
    objects = CustomManager()

    grade_id = IntegerField(db_index=True)

    studentsubject_log = ForeignKey(Studentsubject_log, related_name='+', on_delete=CASCADE)
    # exam_log = ForeignKey(subj_mod.Exam_log, related_name='+', null=True, on_delete=SET_NULL)

    examperiod = PositiveSmallIntegerField(db_index=True, default=1) # 1 = period 1, 2 = period 2, 3 = period 3, 4 = exemption

    pescore = PositiveSmallIntegerField(null=True)
    cescore = PositiveSmallIntegerField(null=True)

    segrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    srgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    sesrgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    cegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    pecegrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)
    finalgrade = CharField(max_length=c.MAX_LENGTH_04, null=True, blank=True)

    se_status = PositiveSmallIntegerField(default=0)
    se_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_auth4by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    se_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    se_blocked = BooleanField(default=False)

    # sr = se_reex = herkansing schoolexamen PR2021-05-01
    sr_status = PositiveSmallIntegerField(default=0)
    sr_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_auth4by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    sr_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    sr_blocked = BooleanField(default=False)

    pe_status = PositiveSmallIntegerField(default=0)
    pe_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_auth4by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    pe_blocked = BooleanField(default=False)

    ce_status = PositiveSmallIntegerField(default=0)
    ce_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_auth4by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    ce_blocked = BooleanField(default=False)

    pe_exam_log = ForeignKey(subj_mod.Exam_log, related_name='+', null=True, on_delete=SET_NULL)
    #pe_exam_blanks = PositiveSmallIntegerField(null=True)
    pe_exam_result = CharField(max_length=2048, null=True)
    pe_exam_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_exam_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_exam_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    pe_exam_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    pe_exam_blocked = BooleanField(default=False)

    ce_exam_log = ForeignKey(subj_mod.Exam_log, related_name='+', null=True, on_delete=SET_NULL)
    ce_exam_blanks = PositiveSmallIntegerField(null=True)
    ce_exam_result = CharField(max_length=2048, null=True)
    ce_exam_score = PositiveSmallIntegerField(null=True)   # PR2022-05-14 added

    ce_exam_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_exam_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    ce_exam_auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)   # PR2022-05-14 added
    ce_exam_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    ce_exam_blocked = BooleanField(default=False)

    # PR2023-01-24 added, to skip approval when imported
    exemption_imported = BooleanField(default=False)

    #answers = CharField(max_length=2048, null=True)
    #blanks = PositiveSmallIntegerField(null=True)
    #answers_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    # TODO deprecate tobedeleted, only deleted is used PR2023-01-24
    tobedeleted = BooleanField(default=False)
    deleted = BooleanField(default=False)

    del_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    del_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    del_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    status = PositiveSmallIntegerField(default=0)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


class DiplomaGradelist(sch_mod.AwpBaseModel): # PR2023-02-19
    objects = CustomManager()

    student = ForeignKey(Student, related_name='+', on_delete=PROTECT)

    regnumber = CharField(db_index=True, max_length=c.MAX_LENGTH_IDNUMBER, null=True)
    name = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)
    filename = CharField(max_length=255, null=True)

    file = FileField(storage=PrivateMediaStorage(), null=True)

    datepublished = DateField()
    deleted = BooleanField(default=False)

    def __str__(self):
        return self.name
    # DiplomaGradelist has no log because its data don't change