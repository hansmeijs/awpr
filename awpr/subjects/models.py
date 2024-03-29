# PR2018-07-20
from django.db.models import Model, Manager, ForeignKey, PROTECT, CASCADE, SET_NULL

from django.db.models import CharField, TextField, IntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField, DateField
from django.utils import timezone

from awpr.settings import AUTH_USER_MODEL
from awpr import constants as c
from schools import models as sch_mod

import logging
logger = logging.getLogger(__name__)

# PR2018-04-22: backup: (venv) C:\dev\awpr\awpr>py -3 manage.py dumpdata schools --format json --indent 4 > schools/backup/schools.json
#               restore: (venv) C:\dev\awpr\awpr>py -3 manage.py loaddata schools/backup/schools.json

# clean() method rus to_python(), validate(), and run_validators() and propagates their errors.
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
# - end of AwpModelManager


# === Level =====================================
class Levelbase(Model):  # PR2018-10-17
    objects = AwpModelManager()

    code = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE)

    def __str__(self):
        return str(self.code)
# - end of Levelbase

class Level(sch_mod.AwpBaseModel): # PR2018-08-12
    # AwpModelManager adds function get_or_none to prevent DoesNotExist exception
    objects = AwpModelManager()

    # base and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Levelbase, related_name='levels', on_delete=PROTECT)
    examyear = ForeignKey(sch_mod.Examyear, related_name='levels', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME)
    abbrev = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE)
    sequence = PositiveSmallIntegerField(db_index=True, default=1)
    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    # color is used in envelop module PR2022-08-03
    color = CharField(max_length=c.MAX_LENGTH_10, null=True)

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.abbrev


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

    @classmethod
    def get_lvl_by_abbrev(cls, abbrev, dep, examyear):  # PR2019-02-26
        # function gets Level with this abbrev and examyear, returns None if multiple found
        # also checks if depbase_id is in depbase_list
        lvl = None
        if examyear and dep and abbrev:
            depbase_id_delim = ';' + dep.base.id + ';'
            if cls.objects.filter(
                    examyear=examyear,
                    depbase_list__contains=depbase_id_delim,
                    abbrev__iexact=abbrev).count() == 1:
                lvl = cls.objects.filter(
                        examyear=examyear,
                        depbase_list__contains=depbase_id_delim,
                        abbrev__iexact=abbrev).first()
        return lvl
# - end of Level


# PR2018-08-12
class Level_log(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    level_id = IntegerField(db_index=True)

    base = ForeignKey(Levelbase, related_name='+', on_delete=PROTECT)

    examyear_log = ForeignKey(sch_mod.Examyear_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=8, null=True)
    sequence = PositiveSmallIntegerField(null=True)
    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    # color is used in envelop module PR2022-08-03
    color = CharField(max_length=c.MAX_LENGTH_10, null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)
# - end of Level_log


# === Sector =====================================
class Sectorbase(Model):  # PR2018-10-17
    objects = AwpModelManager()

    code = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE)

    def __str__(self):
        return str(self.code)
# - end of Sectorbase


class Sector(sch_mod.AwpBaseModel):  # PR2018-06-06
    objects = AwpModelManager()

    # levelbase and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Sectorbase, related_name='sectors', on_delete=PROTECT)
    examyear = ForeignKey(sch_mod.Examyear, related_name='sectors', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME)
    abbrev = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE)
    sequence = PositiveSmallIntegerField(db_index=True, default=1)
    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.abbrev

    @classmethod
    def get_sct_by_abbrev(cls, abbrev, dep, examyear):  # PR2019-02-26
        # function gets Sector with this abbrev and examyear, returns None if multiple found
        # also checks if depbase_id is in depbase_list
        sct = None
        if examyear and dep and abbrev:
            depbase_id_delim = ';' + dep.base.id + ';'
            if cls.objects.filter(
                    examyear=examyear,
                    depbase_list__contains=depbase_id_delim,
                    abbrev__iexact=abbrev).count() == 1:
                sct = cls.objects.filter(
                        examyear=examyear,
                        depbase_list__contains=depbase_id_delim,
                        abbrev__iexact=abbrev).first()
        return sct

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
# - end of Sector


# PR2018-06-06
class Sector_log(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    sector_id = IntegerField(db_index=True)

    base = ForeignKey(Sectorbase, related_name='+', on_delete=PROTECT)

    examyear_log = ForeignKey(sch_mod.Examyear_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=8, null=True)
    sequence = PositiveSmallIntegerField(null=True)
    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)
# - end of Sector_log


# PR2018-06-06 There is one Scheme per department/level/sector per year per country
class Scheme(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    # PR2018-11-07 blank=True is necessary otherwise blank field gives error 'Dit veld is verplicht.'
    # PR2019-02-16 scheme is linked with department, level and sector . get s examyear from department
    department = ForeignKey(sch_mod.Department, related_name='schemes', on_delete=CASCADE)
    level = ForeignKey(Level, null=True, blank=True, related_name='schemes', on_delete=CASCADE)
    sector = ForeignKey(Sector, null=True,  blank=True, related_name='schemes', on_delete=CASCADE)

    name = CharField(max_length=50)  # TODO set department+level+sector Unique per examyear True.
    # TODO check if fields is still in use, deprecate otherwise
    fields = CharField(max_length=255, null=True, blank=True)

    min_studyloadhours = PositiveSmallIntegerField(null=True)

    min_subjects = PositiveSmallIntegerField(null=True)
    max_subjects = PositiveSmallIntegerField(null=True)

    min_mvt = PositiveSmallIntegerField(null=True)
    max_mvt = PositiveSmallIntegerField(null=True)

    min_wisk = PositiveSmallIntegerField(null=True)
    max_wisk = PositiveSmallIntegerField(null=True)

    min_combi = PositiveSmallIntegerField(null=True)
    max_combi = PositiveSmallIntegerField(null=True)

    max_reex = PositiveSmallIntegerField(default=1)

# - rule variables are used in calculating results PR2021-11-27
    rule_avg_pece_sufficient = BooleanField(default=False)
    rule_avg_pece_notatevlex = BooleanField(default=False)  # PR2021-11-27  NOT IN USE: mustbe_avg_pece_sufficient not at evening or lex school

    rule_core_sufficient = BooleanField(default=False)
    rule_core_notatevlex = BooleanField(default=False)  # PR2021-11-27  NOT IN USE: mustbe_avg_pece_sufficient not at evening or lex school

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name

#  ++++++++++  Class methods  +++++++++++++++++++++++++++

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
# - end of Scheme

class Scheme_log(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    scheme_id = IntegerField(db_index=True)

    department_log = ForeignKey(sch_mod.Department_log, related_name='+', on_delete=CASCADE)
    level_log = ForeignKey(Level_log, null=True, related_name='+', on_delete=CASCADE)
    sector_log = ForeignKey(Sector_log, null=True, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    fields = CharField(max_length=c.MAX_LENGTH_NAME, null=True)

    min_studyloadhours = PositiveSmallIntegerField(null=True)

    min_subjects = PositiveSmallIntegerField(null=True)
    max_subjects = PositiveSmallIntegerField(null=True)
    min_mvt = PositiveSmallIntegerField(null=True)
    max_mvt = PositiveSmallIntegerField(null=True)
    min_wisk = PositiveSmallIntegerField(null=True)
    max_wisk = PositiveSmallIntegerField(null=True)
    min_combi = PositiveSmallIntegerField(null=True)
    max_combi = PositiveSmallIntegerField(null=True)
    max_reex = PositiveSmallIntegerField(null=True)

# - rule variables are used in calculating results PR2021-11-27
    rule_avg_pece_sufficient = BooleanField(default=False)
    rule_avg_pece_notatevlex = BooleanField(default=False)  # PR2021-11-27  NOT IN USE: mustbe_avg_pece_sufficient not at evening or lex school

    rule_core_sufficient = BooleanField(default=False)
    rule_core_notatevlex = BooleanField(default=False)  # PR2021-11-27  NOT IN USE: mustbe_avg_pece_sufficient not at evening or lex school

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    @property
    def mode_str(self):
        return c.MODE_DICT.get(str(self.mode),'-')
# - end of Scheme_log


# === Subjecttype =====================================
class Subjecttypebase(Model):  # PR2018-10-17 PR2021-07-11
    objects = AwpModelManager()

    code = CharField(db_index=True, max_length=c.MAX_LENGTH_04)
    name = CharField(max_length=50)
    abbrev = CharField(db_index=True, max_length=20)
    # value '0' is reserved for combi in gradelist, values must be unique!
    sequence = PositiveSmallIntegerField(db_index=True, default=1)

    def __str__(self):
        return self.name
# - end of Subjecttypebase


# PR2018-06-06
class Subjecttype(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    base = ForeignKey(Subjecttypebase, related_name='characters', on_delete=CASCADE)
    scheme = ForeignKey(Scheme, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=50)
    abbrev = CharField(max_length=20, null=True)

    # has_prac only enables the has_practexam option of a schemeitem
    has_prac = BooleanField(default=False)  # has practical exam

    # schemeitem.has_pws is deprecated, use subjecttype.has_pws instead
    has_pws = BooleanField(default=False)  # has profielwerkstuk or sectorwerkstuk

    min_subjects = PositiveSmallIntegerField(null=True)
    max_subjects = PositiveSmallIntegerField(null=True)

    min_extra_nocount = PositiveSmallIntegerField(null=True)
    max_extra_nocount = PositiveSmallIntegerField(null=True)

    min_extra_counts = PositiveSmallIntegerField(null=True)
    max_extra_counts = PositiveSmallIntegerField(null=True)

    def __str__(self):
        return self.name
# - end of Subjecttype


class Subjecttype_log(sch_mod.AwpBaseModel):
    objects = AwpModelManager()
    subjecttype_id = IntegerField(db_index=True)

    base = ForeignKey(Subjecttypebase, related_name='+', on_delete=CASCADE)

    scheme_log = ForeignKey(Scheme_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_20, null=True)
    sequence = PositiveSmallIntegerField(null=True)

    has_prac = BooleanField(default=False)
    has_pws = BooleanField(default=False)

    min_subjects = PositiveSmallIntegerField(null=True)
    max_subjects = PositiveSmallIntegerField(null=True)

    min_extra_nocount = PositiveSmallIntegerField(null=True)
    max_extra_nocount = PositiveSmallIntegerField(null=True)

    min_extra_counts = PositiveSmallIntegerField(null=True)
    max_extra_counts = PositiveSmallIntegerField(null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

# - end of Subjecttype_log


# =============  Subject Model  =====================================
class Subjectbase(Model):
    objects = AwpModelManager()

    # PR2021-08-09 removed: country = ForeignKey(sch_mod.Country, related_name='+', on_delete=PROTECT)
    code = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE)
# - end of Subjectbase


class Subject(sch_mod.AwpBaseModel):  # PR1018-11-08 PR2020-12-11
    # PR2018-06-05 Subject has one subject per examyear per country
    # subject abbrev is stored as 'code' in Subjectbase
    # Subject has no country field: country is a field in examyear

    objects = AwpModelManager()

    # base and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Subjectbase, related_name='subjects', on_delete=PROTECT)
    examyear = ForeignKey(sch_mod.Examyear, related_name='subjects', on_delete=CASCADE)

    name_nl = CharField(max_length=c.MAX_LENGTH_NAME)
    name_en = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    name_pa = CharField(max_length=c.MAX_LENGTH_NAME, null=True)

    sequence = PositiveSmallIntegerField(default=9999, db_index=True)
    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    # pr2021-05-04 temporary, used when importing from AWP to determine if subject is uploaded from school
    addedbyschool = BooleanField(default=False)

    # PR2022-08-22 moved from schemeitem
    notatdayschool = BooleanField(default=False)

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.name_nl
# - end of Subject


# PR2018-06-05 Subject is the base Model of all subjects
class Subject_log(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    subject_id = IntegerField(db_index=True)

    base = ForeignKey(Subjectbase, related_name='+', on_delete=PROTECT)

    examyear_log = ForeignKey(sch_mod.Examyear_log, related_name='+', on_delete=CASCADE)

    name_nl = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    name_en = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    name_pa = CharField(max_length=c.MAX_LENGTH_NAME, null=True)

    code = CharField(max_length=c.MAX_LENGTH_10, null=True)  # stored in subjectbase PR2020-12-11
    sequence = PositiveSmallIntegerField(null=True)
    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    addedbyschool = BooleanField(default=False)

    # PR2022-08-22 moved from schemeitem
    notatdayschool = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)
# - end of Subject_log
######################################
# Module exam envelops PR2022-08-03 PR2022-10-09


class Enveloporderlist(sch_mod.AwpBaseModel):  # PR2022-10-12
    # contains published envelop_count_per_school_dict
    objects = AwpModelManager()

    examyear = ForeignKey(sch_mod.Examyear, related_name='+', on_delete=CASCADE)

    orderdict = TextField()
# - end of Enveloporderlist


class Envelopbundlebase(Model):  # PR2022-08-03
    objects = AwpModelManager()
# - end of Envelopbundlebase


class Envelopbundle(sch_mod.AwpBaseModel):  # PR2022-08-03
    # contains groups of available envelop labels
    objects = AwpModelManager()

    base = ForeignKey(Envelopbundlebase, related_name='+', on_delete=PROTECT)
    examyear = ForeignKey(sch_mod.Examyear, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME)
# - end of Envelopbundle

class Envelopsubject(sch_mod.AwpBaseModel):  # PR2022-10-09
    # contains Envelopbundle of each subject / dep / level combination
    objects = AwpModelManager()

    subject = ForeignKey(Subject, related_name='+', on_delete=CASCADE)
    department = ForeignKey(sch_mod.Department, related_name='+', on_delete=CASCADE)
    level = ForeignKey(Level, related_name='+', null=True, on_delete=SET_NULL)

    examperiod = PositiveSmallIntegerField(db_index=True, default=1)

    envelopbundle = ForeignKey(Envelopbundle, related_name='+', null=True, on_delete=SET_NULL)

    firstdate = DateField(null=True)
    lastdate = DateField(null=True)
    starttime = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)
    endtime = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)

    # labels can be printed with errata labels, without errata labels of errata labels only
    has_errata = BooleanField(default=False)
    # PR2023-08-10 todo: to be removesremove, use secret_exam in Exam instead
    secret_exam = BooleanField(default=False)  # PR2023-03-31 added
# - end of Envelopsubject


class Enveloplabelbase(Model):  # PR2022-08-03
    objects = AwpModelManager()
# - end of Enveloplabelbase


class Enveloplabel(sch_mod.AwpBaseModel):  # PR2022-08-03
    # contains available envelop labels
    objects = AwpModelManager()

    base = ForeignKey(Enveloplabelbase, related_name='+', on_delete=PROTECT)
    examyear = ForeignKey(sch_mod.Examyear, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME)

    # labels can be printed with errata labels, without errata labels of errata labels only
    is_errata = BooleanField(default=False)
    is_variablenumber = BooleanField(default=False)
    # when not is_variablenumber: numberinenvelop is a fixed number
    # when is_variablenumber: numberinenvelop is the maximum number of exams in the envelop
    numberinenvelop = PositiveSmallIntegerField(null=True)
    numberofenvelops = PositiveSmallIntegerField(null=True)
# - end of Enveloplabel


class Envelopbundlelabel(sch_mod.AwpBaseModel):  # PR2022-08-03
    # contains groups of available envelop labels
    objects = AwpModelManager()

    envelopbundle = ForeignKey(Envelopbundle, related_name='+', on_delete=CASCADE)
    enveloplabel = ForeignKey(Enveloplabel, related_name='+', on_delete=CASCADE)

    sequence = PositiveSmallIntegerField(default=1)
# - end of Envelopbundlelabel


class Envelopitembase(Model):  # PR2022-08-03
    objects = AwpModelManager()
# - end of Envelopitembase


class Envelopitem(sch_mod.AwpBaseModel):  # PR2022-08-03 PR2022-09-27 PR2022-10-19
    # contains available envelop content items
    objects = AwpModelManager()

    base = ForeignKey(Envelopitembase, related_name='+', on_delete=PROTECT)
    examyear = ForeignKey(sch_mod.Examyear, related_name='+', on_delete=CASCADE)

    content_nl = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    content_en = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    content_pa = CharField(max_length=c.MAX_LENGTH_NAME, null=True)

    instruction_nl = CharField(max_length=c.MAX_LENGTH_EMAIL_ADDRESS, null=True)
    instruction_en = CharField(max_length=c.MAX_LENGTH_EMAIL_ADDRESS, null=True)
    instruction_pa = CharField(max_length=c.MAX_LENGTH_EMAIL_ADDRESS, null=True)

    # color is used in envelop module PR2022-08-03
    content_color = CharField(max_length=c.MAX_LENGTH_10, null=True)
    instruction_color = CharField(max_length=c.MAX_LENGTH_10, null=True)

    # PR2022-10-19
    content_font = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    instruction_font = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
# - end of Envelopitem


class Enveloplabelitem(sch_mod.AwpBaseModel):  # PR2022-08-03
    # contains groups of available envelop labels
    objects = AwpModelManager()

    enveloplabel = ForeignKey(Enveloplabel, related_name='+', on_delete=CASCADE)
    envelopitem = ForeignKey(Envelopitem, related_name='+', on_delete=CASCADE)

    sequence = PositiveSmallIntegerField(default=1)
# - end of Enveloplabelitem


# PR2022-02-28
class Ntermentable(sch_mod.AwpBaseModel):
    objects = AwpModelManager()
    # PR2022-07-01 TODO in addition to link with examyear, add examyear as integer field, to prevent

    examyear = ForeignKey(sch_mod.Examyear, related_name='+', on_delete=CASCADE)

    nex_id = IntegerField(db_index=True)

    sty_id = PositiveSmallIntegerField(null=True)
    opl_code = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    leerweg = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    ext_code = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    tijdvak = PositiveSmallIntegerField(null=True)

    omschrijving = CharField(max_length=c.MAX_LENGTH_EMAIL_ADDRESS, null=True)
    schaallengte = PositiveSmallIntegerField(null=True)
    n_term = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)
    afnamevakid = PositiveSmallIntegerField(null=True)
    extra_vakcodes_tbv_wolf = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)

    datum = DateField(null=True)
    begintijd = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)
    eindtijd = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)
# - end of Ntermentable


# PR2022-02-28
class Ntermentable_log(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    ntermentable_id = IntegerField(db_index=True)

    examyear_log = ForeignKey(sch_mod.Examyear_log, related_name='+', on_delete=CASCADE)

    nex_id = IntegerField(db_index=True)

    sty_id = PositiveSmallIntegerField(null=True)
    opl_code = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    leerweg = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    ext_code = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    tijdvak = PositiveSmallIntegerField(null=True)

    omschrijving = CharField(max_length=c.MAX_LENGTH_EMAIL_ADDRESS, null=True)
    schaallengte = PositiveSmallIntegerField(null=True)
    n_term = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)
    afnamevakid = PositiveSmallIntegerField(null=True)
    extra_vakcodes_tbv_wolf = CharField(max_length=c.MAX_LENGTH_FIRSTLASTNAME, null=True)

    datum = DateField(null=True)
    begintijd = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)
    eindtijd = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)
# - end of Ntermentable_log


class Exam(sch_mod.AwpBaseModel):  # PR2021-03-04
    # PR2021-03-04 contains exam with possible answers per exam question
    objects = AwpModelManager()

    subject = ForeignKey(Subject, related_name='+', on_delete=CASCADE)
    department = ForeignKey(sch_mod.Department, related_name='+', on_delete=CASCADE)
    level = ForeignKey(Level, related_name='+', null=True, on_delete=SET_NULL)
    ntermentable = ForeignKey(Ntermentable, related_name='+', null=True, on_delete=SET_NULL)

    ete_exam = BooleanField(default=False)
    examperiod = PositiveSmallIntegerField(db_index=True, default=1)

    # deprecated. was: examtype = CharField(max_length=c.MAX_LENGTH_10, db_index=True, default='ce')

    version = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    has_partex = BooleanField(default=False)
    partex = CharField(max_length=2048, null=True)
    # amount contains total number of questions, amount per partex is stored in partex
    amount = PositiveSmallIntegerField(null=True)
    blanks = PositiveSmallIntegerField(null=True)

    assignment = CharField(max_length=2048, null=True)
    keys = CharField(max_length=2048, null=True)

    status = PositiveSmallIntegerField(default=0)
    auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    # PR2023-05-28 removed:
    # auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    locked = BooleanField(default=False)

    # PR2023-05-28 added: publish cesuur
    cesuur_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    cesuur_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    cesuur_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    nex_id = PositiveSmallIntegerField(null=True)
    scalelength = PositiveSmallIntegerField(null=True)
    cesuur = PositiveSmallIntegerField(null=True)
    nterm = CharField(max_length=c.MAX_LENGTH_04, null=True)

    datum = DateField(null=True)
    begintijd = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)
    eindtijd = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)

    # PR2022-05-14 'Geheim examen': school gets grade from ETE.
    # PR2023-03-31 when  secret_exam = True: only ETE can enter scores. school doesn't have to approve
    # All 3rd periodexams are secret, part of 2nd period exams are secret
    secret_exam = BooleanField(default=False)

    envelopbundle = ForeignKey(Envelopbundle, related_name='+', db_index=True, null=True, on_delete=SET_NULL)
    # labels can be printed with errata labels, without errata labels of errata labels only
    has_errata = BooleanField(default=False)
    subject_color = CharField(max_length=c.MAX_LENGTH_10, null=True)

    evl_modifiedby = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    evl_modifiedat = DateTimeField(default=timezone.now, null=True)
# - end of Exam


class Exam_log(sch_mod.AwpBaseModel):  # PR2021-03-04
    # PR2021-03-04 contains exam possible ansewers per exam question
    # subject abbrev is stored as 'code' in Subjectbase
    # Subject has no country field: country is a field in examyear

    objects = AwpModelManager()

    exam_id = IntegerField(db_index=True)

    subject_log = ForeignKey(Subject_log, related_name='+', null=True, on_delete=SET_NULL)
    department_log = ForeignKey(sch_mod.Department_log, related_name='+', null=True, on_delete=SET_NULL)
    level_log = ForeignKey(Level_log, related_name='+', null=True, on_delete=SET_NULL)
    ntermentable_log = ForeignKey(Ntermentable_log, related_name='+', null=True, on_delete=SET_NULL)

    ete_exam = BooleanField(default=False)
    examperiod = PositiveSmallIntegerField(db_index=True, default=1)
    # deprecated. was: examtype = CharField(max_length=c.MAX_LENGTH_10, db_index=True)

    version = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    has_partex = BooleanField(default=False)
    partex = CharField(max_length=2048, null=True)
    amount = PositiveSmallIntegerField(null=True)
    blanks = PositiveSmallIntegerField(null=True)

    assignment = CharField(max_length=2048, null=True)
    keys = CharField(max_length=2048, null=True)

    status = PositiveSmallIntegerField(default=0)
    auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    # PR2023-05-28 removed:
    # auth3by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)
    locked = BooleanField(default=False)

    # PR2023-05-28 added: publish cesuur
    cesuur_auth1by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    cesuur_auth2by = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=PROTECT)
    cesuur_published = ForeignKey(sch_mod.Published, related_name='+', null=True, on_delete=PROTECT)

    nex_id = PositiveSmallIntegerField(null=True)
    scalelength = PositiveSmallIntegerField(null=True)
    cesuur = PositiveSmallIntegerField(null=True)
    nterm = CharField(max_length=c.MAX_LENGTH_04, null=True)

    datum = DateField(null=True)
    begintijd = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)
    eindtijd = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE, null=True)

    secret_exam = BooleanField(default=False)

    envelopbundle = ForeignKey(Envelopbundle, related_name='+', db_index=True, null=True, on_delete=SET_NULL)

    has_errata = BooleanField(default=False)
    subject_color = CharField(max_length=c.MAX_LENGTH_10, null=True)

    evl_modifiedby = ForeignKey(AUTH_USER_MODEL, null=True, related_name='+', on_delete=SET_NULL)
    evl_modifiedat = DateTimeField(default=timezone.now, null=True)
    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)
# - end of Exam_log


#######################################
# PR2018-06-05
class Schemeitem(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    scheme = ForeignKey(Scheme, related_name='+', on_delete=CASCADE)
    subject = ForeignKey(Subject, related_name='+', on_delete=CASCADE)
    subjecttype = ForeignKey(Subjecttype, related_name='+', on_delete=CASCADE)

    ete_exam = BooleanField(default=False)
    # PR2023-08-10 secret_exam cannot be stored in schemeitem, becasue it can have diferent value per examperiod
    # keep it in exam, although it is awkward because score cannot be entered when tehre is no exam selected
    # was: secret_exam = BooleanField(default=False)  # PR2023-08-10 added

    # PR2021-10-11 request ETS Esther: subject may have different language per level,
    # therefore otherlang is moved from subject to schemeitem
    # TODO move otherlang to Exam instead of Schemeitem PR2022-09-04
    otherlang = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    no_order = BooleanField(default=False)

    # delete exam from schemeitem, is linked to grade
    # exam = ForeignKey(Exam, related_name='+', null=True, on_delete=SET_NULL)

    gradetype = PositiveSmallIntegerField(default=1)
    weight_se = PositiveSmallIntegerField(default=1)
    weight_ce = PositiveSmallIntegerField(default=1)
    multiplier = PositiveSmallIntegerField(default=1)

    # is_mand_subj: only mandatory if student has this subject
    is_mandatory = BooleanField(default=False)
    is_mand_subj = ForeignKey(Subject, related_name='+', null=True, on_delete=SET_NULL)
    is_combi = BooleanField(default=False)

    # PR2023-06-18 TODO to be replaced by  min_extra_nocount, extra_count_allowed and  extra_count_allowed not in use
    extra_count_allowed = BooleanField(default=False)
    extra_nocount_allowed = BooleanField(default=False)

    # PR2023-06-18 to be implemented ?? > also in subjecttype
    #max_extra_nocount = PositiveSmallIntegerField(default=0)

    has_practexam = BooleanField(default=False)
    # schemeitem.has_pws is deprecated, use subjecttype.has_pws instead
    # has_pws = BooleanField(default=False)

    is_core_subject = BooleanField(default=False)
    is_mvt = BooleanField(default=False)
    is_wisk = BooleanField(default=False)

# - rule variables are used in calculating results PR2021-11-27
    rule_grade_sufficient = BooleanField(default=False)
    rule_gradesuff_notatevlex = BooleanField(default=False) # PR2021-11-23 rule_grade_sufficient not at evening or lex school

    sr_allowed = BooleanField(default=False) # herkansing schoolexamen
    # deleted: reex_combi_allowed = BooleanField(default=False)
    # deleted: no_centralexam = BooleanField(default=False)
    # deleted: no_reex = BooleanField(default=False)

    # deprecated, moved to scheme
    # max_reex = PositiveSmallIntegerField(default=1)
    # removed, not in use
    # no_thirdperiod = BooleanField(default=False)
    # no_exemption_ce = BooleanField(default=False)

    # TODO
    # PR2022-03-09 to skip ce in calc endgrade when exemption has no ce
    # contains array of examyears with no ce for this subject
    # best way: calc endgrade based on info of that examyear
    no_ce_years = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    thumb_rule = BooleanField(default=False)

    studyloadhours = PositiveSmallIntegerField(null=True)

    # PR2022-08-22 tobe deprecated, moved to subject
    notatdayschool = BooleanField(default=False)

    #   extra_count_allowed: only at Havo Vwo) 'PR2017-01-28
    #   extra_nocount_allowed: at Vsbo TKL and Havo Vwo)) 'PR2017-01-28
    #   has_practexam: only at Vsbo PBL and PKL, all sectorprogramma's except uv 'PR2017-01-28

    # Corona issues PR2021-04-25
    # sr_allowed = BooleanField(default=False)
    # reex_combi_allowed = BooleanField(default=False)
    # no_centralexam = BooleanField(default=False)
    # no_reex = BooleanField(default=False)
    # no_thirdperiod = BooleanField(default=False)
    # no_exemption_ce = BooleanField(default=False)


#  ++++++++++  Class methods  +++++++++++++++++++++++++++
    @classmethod
    def get_schemeitem_list(cls, scheme):  # PR2019-01-18
        # logger.debug('------------- get_schemeitem_list -------------> ' + str(scheme))
        schemeitems = cls.objects.filter(scheme=scheme).order_by('subject__sequence', 'subjecttype__sequence').all()
        # logger.debug(schemeitems)
        schemeitem_list = []
        for item in schemeitems:
            sequence = item.subject.sequence * 1000 + item.subjecttype.sequence
            item_dict = {
                'mode': '-',
                'ssi_id': item.id,
                'scm_id': item.scheme.id,
                'grtp_id': item.gradetype,
                'ssi_wtse': item.weight_se,
                'ssi_wtce': item.weight_ce,
            }

            if item.is_mandatory:
                item_dict['ssi_mand'] = 1 # was: (0, 1)[item.is_mandatory]
           # if item.is_mand_subj:
            #    item_dict['ssi_mand_subj'] = 1 # was: (0, 1)[item.is_mandatory]
            if item.is_combi:
                item_dict['ssi_comb'] = 1 # was: (0, 1)[item.is_combi]
            if item.extra_count_allowed:
                item_dict['ssi_exal'] = 1 # was: (0, 1)[item.extra_count_allowed]
            if item.extra_nocount_allowed:
                item_dict['ssi_exna'] = 1 # was: (0, 1)[item.extra_nocount_allowed]
            if item.is_core_subject:
                item_dict['ssi_core'] = 1 # PR2019-02-26 is core subject
            if item.rule_grade_sufficient:
                item_dict['ssi_sufficient'] = 1 # PR2019-11-23
            if item.rule_gradesuff_notatevlex:
                item_dict['ssi_rule_gradesuff_notatevlex'] = 1 # PR2019-11-23

            if item.subject:
                item_dict['subj_id'] = item.subject.id
                item_dict['subj_name'] = item.subject.name_nl
                item_dict['subj_sequ'] = item.subject.sequence

            if item.subjecttype:
                item_dict['sjtp_id'] = item.subjecttype.id
                item_dict['sjtp_name'] = item.subjecttype.abbrev

                if item.subjecttype.has_prac:
                    item_dict['sjtp_hasprac'] = 1
                    # schemeitem.has_practexam only when subjecttype.has_prac
                    item_dict['prac'] = (0, 1)[item.has_practexam]

                if item.subjecttype.has_pws:
                    item_dict['sjtp_haspws'] = 1

                #if item.subjecttype.one_allowed:
                #    item_dict['sjtp_onlyone'] = 1

            item_dict['sequence'] = sequence
            schemeitem_list.append(item_dict)


        return schemeitem_list
# - end of Schemeitem

# PR2018-06-08
class Schemeitem_log(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    schemeitem_id = IntegerField(db_index=True)

    scheme_log = ForeignKey(Scheme_log, null=True, related_name='+', on_delete=CASCADE)
    subject_log = ForeignKey(Subject_log, null=True, related_name='+', on_delete=CASCADE)
    subjecttype_log = ForeignKey(Subjecttype_log, null=True,  related_name='+', on_delete=CASCADE)

    ete_exam = BooleanField(default=False)

    otherlang = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    no_order = BooleanField(default=False)

    # delete exam from schemitem, is linked to grade
    #exam_log = ForeignKey(Exam_log, related_name='+', null=True, on_delete=CASCADE)

    gradetype = PositiveSmallIntegerField(null=True)
    weight_se = PositiveSmallIntegerField(null=True)
    weight_ce = PositiveSmallIntegerField(null=True)
    multiplier = PositiveSmallIntegerField(null=True)

    is_mandatory = BooleanField(default=False)
    is_mand_subj_log = ForeignKey(Subject_log, related_name='+', null=True, on_delete=SET_NULL)
    is_combi = BooleanField(default=False)

    extra_count_allowed = BooleanField(default=False)
    extra_nocount_allowed = BooleanField(default=False)

    # PR2023-06-18 to be implemented ?? > also in subjecttype
    #max_extra_nocount = PositiveSmallIntegerField(default=0)

    has_practexam = BooleanField(default=False)

    # has_pws is deprecated, use sjtp.has_prac instead
    # has_pws = BooleanField(default=False)

    is_core_subject = BooleanField(default=False)
    is_mvt = BooleanField(default=False)
    is_wisk = BooleanField(default=False)

# - rule variables are used in calculating results PR2021-11-27
    rule_grade_sufficient = BooleanField(default=False)
    rule_gradesuff_notatevlex = BooleanField(default=False)  # PR2021-11-23 rule_grade_sufficient not at evening or lex school

    sr_allowed = BooleanField(default=False)  # herkansing schoolexamen
    # max_reex = PositiveSmallIntegerField(default=1)
    # no_thirdperiod = BooleanField(default=False)
    # no_exemption_ce = BooleanField(default=False)

    no_ce_years = CharField(max_length=c.MAX_LENGTH_KEY, null=True)
    thumb_rule = BooleanField(default=False)

    studyloadhours = PositiveSmallIntegerField(null=True)
    notatdayschool = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)
# - end of Schemeitem_log


# PR2018-06-06 # PR2019-02-17
class Package(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    scheme = ForeignKey(Scheme, related_name='packages', on_delete=CASCADE)

    name = CharField(max_length=50)

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name
# - end of Package

# PR2018-06-06
class Package_log(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    package_id = IntegerField(db_index=True)

    scheme_log = ForeignKey(Scheme_log, null=True, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    @property
    def mode_str(self):
        return c.MODE_DICT.get(str(self.mode),'-')
# - end of Package_log

# PR2018-06-06
class Packageitem(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    package = ForeignKey(Package, related_name='packageschemes', on_delete=CASCADE)
    schemeitem = ForeignKey(Schemeitem, related_name='packageschemes', on_delete=CASCADE)
# - end of Packageitem


# PR2018-06-06
class Cluster(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    school = ForeignKey(sch_mod.School, related_name='clusters', on_delete=CASCADE)
    department = ForeignKey(sch_mod.Department, related_name='clusters', on_delete=CASCADE)
    subject = ForeignKey(Subject, related_name='clusters', on_delete=CASCADE)

    name = CharField(max_length=50)

    def __str__(self):
        return self.name
# - end of Cluster


# PR2018-06-06
class Cluster_log(sch_mod.AwpBaseModel):
    objects = AwpModelManager()

    cluster_id = IntegerField(db_index=True)

    # TODO: refer to log table
    school_log = ForeignKey(sch_mod.School_log, related_name='+', on_delete=CASCADE)
    subject_log = ForeignKey(Subject_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_20, null=True)
    depbases = CharField(max_length=c.MAX_LENGTH_KEY, null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    def __str__(self):
        return self.abbrev
# - end of Cluster_log

"""
# +++++++++++++++++++++   Functions Department, Level, Sector, Subject  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# PR2024-03-02 not in use
def get_list_strNIU(list, model):
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
                                _instance = sch_mod.Department.objects.filter(pk=_id_int).first()
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
"""