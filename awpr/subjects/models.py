# PR2018-07-20
from django.db.models import Model, Manager, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField

from django.contrib.postgres.fields import ArrayField

from django.core.validators import MaxValueValidator
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

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


# === Level =====================================
class Levelbase(Model):  # PR2018-10-17
    objects = sch_mod.AwpModelManager()

    country = ForeignKey(sch_mod.Country, related_name='+', on_delete=PROTECT)


class Level(sch_mod.AwpBaseModel): # PR2018-08-12
    # AwpModelManager adds function get_or_none to prevent DoesNotExist exception
    objects = sch_mod.AwpModelManager()

    # base and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Levelbase, related_name='levels', on_delete=PROTECT)
    examyear = ForeignKey(sch_mod.Examyear, related_name='levels', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('50')),)
    abbrev = CharField(max_length=8, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('8')),)
    sequence = PositiveSmallIntegerField(db_index=True, default=1)
    depbases = ArrayField(IntegerField(), null=True)


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


# PR2018-08-12
class Level_log(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    level_id = IntegerField(db_index=True)

    base = ForeignKey(Levelbase, related_name='+', on_delete=PROTECT)

    examyear_log = ForeignKey(sch_mod.Examyear_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=8, null=True)
    sequence = PositiveSmallIntegerField(null=True)
    depbases = ArrayField(IntegerField(), null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# === Sector =====================================
class Sectorbase(Model):  # PR2018-10-17
    objects = sch_mod.AwpModelManager()

    country = ForeignKey(sch_mod.Country, related_name='+', on_delete=PROTECT)


class Sector(sch_mod.AwpBaseModel):  # PR2018-06-06
    objects = sch_mod.AwpModelManager()

    # levelbase and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Sectorbase, related_name='sectors', on_delete=PROTECT)
    examyear = ForeignKey(sch_mod.Examyear, related_name='sectors', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('50')),)
    abbrev = CharField(max_length=8, # PR2018-10-20 set Unique per Examyear True.
        help_text=_('Required. {} characters or fewer.'.format('8')),)
    sequence = PositiveSmallIntegerField(db_index=True, default=1)
    depbases = ArrayField(IntegerField(), null=True)

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.abbrev

    @property  # PR2018-08-11
    def has_no_child_rows(self):
        linked_items_count = Scheme.objects.filter(sector_id=self.pk).count()
        # logger.debug('SubjectDefault Model has_no_child_rows linked_items_count: ' + str(linked_items_count))
        return not bool(linked_items_count)


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


# PR2018-06-06
class Sector_log(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    sector_id = IntegerField(db_index=True)

    base = ForeignKey(Sectorbase, related_name='+', on_delete=PROTECT)

    examyear_log = ForeignKey(sch_mod.Examyear_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=8, null=True)
    sequence = PositiveSmallIntegerField(null=True)
    depbases = ArrayField(IntegerField(), null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# === Subjecttype =====================================
class Subjecttypebase(Model): # PR2018-10-17
    objects = sch_mod.AwpModelManager()

    country = ForeignKey(sch_mod.Country, related_name='+', on_delete=PROTECT)


# PR2018-06-06
class Subjecttype(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    base = ForeignKey(Subjecttypebase, related_name='characters', on_delete=CASCADE)
    examyear = ForeignKey(sch_mod.Examyear, related_name='characters', on_delete=CASCADE)

    name = CharField(max_length=50)
    abbrev = CharField(db_index=True,max_length=20)
    code = CharField(db_index=True,max_length=4)
    sequence = PositiveSmallIntegerField(db_index=True, default=1)
    depbases = ArrayField(IntegerField(), null=True)
    has_prac = BooleanField(default=False) # has practical exam
    has_pws = BooleanField(default=False) # has profielwerkstuk or sectorwerkstuk
    one_allowed = BooleanField(default=False) # if true: only one subject with this Subjecttype allowed per student

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.name


class Subjecttype_log(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    subjecttype_id = IntegerField(db_index=True)

    base = ForeignKey(Subjecttypebase, related_name='+', on_delete=CASCADE)

    examyear_log = ForeignKey(sch_mod.Examyear_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_20,null=True)
    code = CharField(max_length=c.MAX_LENGTH_04,null=True)
    sequence = PositiveSmallIntegerField(null=True)
    depbases = ArrayField(IntegerField(), null=True)
    has_prac = BooleanField(default=False)
    has_pws = BooleanField(default=False)
    one_allowed = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# PR2018-08-23 PR2020-12-16
class Norm(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    examyear = ForeignKey(sch_mod.Examyear, related_name='+', on_delete=CASCADE)

    is_etenorm = BooleanField(default=False)
    scalelength_ce = PositiveSmallIntegerField(null=True)
    norm_ce = CharField(max_length=c.MAX_LENGTH_10, null=True)
    scalelength_reex =  PositiveSmallIntegerField(null=True)
    norm_reex = CharField(max_length=c.MAX_LENGTH_10, null=True)
    scalelength_pe = PositiveSmallIntegerField(null=True)
    norm_practex = CharField(max_length=c.MAX_LENGTH_10, null=True)

# PR2018-08-23
class Norm_log(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    norm_id = IntegerField(db_index=True)

    examyear_log = ForeignKey(sch_mod.Examyear_log, related_name='+', on_delete=CASCADE)

    is_etenorm = BooleanField(default=False)
    scalelength_ce = PositiveSmallIntegerField(null=True)
    norm_ce = CharField(max_length=c.MAX_LENGTH_10, null=True)
    scalelength_reex = PositiveSmallIntegerField(null=True)
    norm_reex = CharField(max_length=c.MAX_LENGTH_10, null=True)
    scalelength_pe = PositiveSmallIntegerField(null=True)
    norm_practex = CharField(max_length=c.MAX_LENGTH_10, null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# PR2018-06-06 There is one Scheme per department/level/sector per year per country
class Scheme(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    # PR2018-11-07 blank=True is necessary otherwise blank field gives error 'Dit veld is verplicht.'
    # PR2019-02-16 scheme is linked with department, level and sector . get s examyear from department
    department = ForeignKey(sch_mod.Department, related_name='schemes', on_delete=CASCADE)
    level = ForeignKey(Level, null=True, blank=True, related_name='schemes', on_delete=CASCADE)
    sector = ForeignKey(Sector, null=True,  blank=True, related_name='schemes', on_delete=CASCADE)
    name = CharField(max_length=50)  # TODO set department+level+sector Unique per examyear True.
    fields = CharField(max_length=c.MAX_LENGTH_NAME, null=True,  blank=True, choices=c.SCHEMEFIELD_CHOICES)

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name

    @property  # PR2018-08-11
    def has_no_child_rows(self):
        linked_items_count = Scheme.objects.filter(level_id=self.pk).count()
        # logger.debug('SubjectDefault Model has_no_child_rows linked_items_count: ' + str(linked_items_count))
        return not bool(linked_items_count)

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


class Scheme_log(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    scheme_id = IntegerField(db_index=True)

    dep_log = ForeignKey(sch_mod.Department_log, related_name='+', on_delete=CASCADE)
    level_log = ForeignKey(Level_log, null=True, related_name='+', on_delete=CASCADE)
    sector_log = ForeignKey(Sector_log, null=True, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    fields = CharField(max_length=c.MAX_LENGTH_NAME, null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    @property
    def mode_str(self):
        return c.MODE_DICT.get(str(self.mode),'-')



# =============  Subject Model  =====================================
class Subjectbase(Model):
    objects = sch_mod.AwpModelManager()

    country = ForeignKey(sch_mod.Country, related_name='+', on_delete=PROTECT)
    code = CharField(max_length=c.MAX_LENGTH_SCHOOLCODE)


class Subject(sch_mod.AwpBaseModel):  # PR1018-11-08 PR2020-12-11
    # PR2018-06-05 Subject has one subject per examyear per country
    # subject abbrev is stored as 'code' in Subjectbase
    # Subject has no country field: country is a field in examyear

    objects = sch_mod.AwpModelManager()

    # base and examyear cannot be changed PR2018-10-17
    base = ForeignKey(Subjectbase, related_name='subjects', on_delete=PROTECT)
    examyear = ForeignKey(sch_mod.Examyear, related_name='subjects', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME)
    sequence = PositiveSmallIntegerField(default=9999)
    depbases = ArrayField(IntegerField(), null=True)

    class Meta:
        ordering = ['sequence',]

    def __str__(self):
        return self.name

    @property  # PR2018-07-19
    def has_no_child_rows(self):
        # TODO find records in linked tables
        linked_items_count = False  # Subject.objects.filter(subject_id=self.pk).count()
        # logger.debug('SubjectDefault Model has_no_child_rows linked_items_count: ' + str(linked_items_count))
        return not bool(linked_items_count)

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
class Subject_log(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    subject_id = IntegerField(db_index=True)

    base = ForeignKey(Subjectbase, related_name='+', on_delete=PROTECT)

    examyear_log = ForeignKey(sch_mod.Examyear_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    code = CharField(max_length=c.MAX_LENGTH_10, null=True)  # stored in subjectbase PR2020-12-11
    sequence = PositiveSmallIntegerField(null=True)
    depbases = ArrayField(IntegerField(), null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)



# PR2018-06-05
class Schemeitem(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    scheme = ForeignKey(Scheme, related_name='+', on_delete=CASCADE)
    subject = ForeignKey(Subject, related_name='+', on_delete=CASCADE)
    subjecttype = ForeignKey(Subjecttype, related_name='+', on_delete=CASCADE)

    norm = ForeignKey(Norm, related_name='+', null=True, on_delete=CASCADE)

    gradetype = PositiveSmallIntegerField(default=0)
    weight_se = PositiveSmallIntegerField(default=0)
    weight_ce = PositiveSmallIntegerField(default=0)

    is_mandatory = BooleanField(default=False)
    is_combi = BooleanField(default=False)
    extra_count_allowed = BooleanField(default=False)
    extra_nocount_allowed = BooleanField(default=False)
    elective_combi_allowed = BooleanField(default=False)
    has_practexam = BooleanField(default=False)

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
            if item.is_combi:
                item_dict['ssi_comb'] = 1 # was: (0, 1)[item.is_combi]
            if item.extra_count_allowed:
                item_dict['ssi_exal'] = 1 # was: (0, 1)[item.extra_count_allowed]
            if item.extra_nocount_allowed:
                item_dict['ssi_exna'] = 1 # was: (0, 1)[item.extra_nocount_allowed]
            if item.elective_combi_allowed:
                item_dict['ssi_chal'] = 1 # was: (0, 1)[item.elective_combi_allowed]
            if item.is_core_subject:
                item_dict['ssi_core'] = 1 # PR2019-02-26 is core subject

            if item.subject:
                item_dict['subj_id'] = item.subject.id
                item_dict['subj_name'] = item.subject.name
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

                if item.subjecttype.one_allowed:
                    item_dict['sjtp_onlyone'] = 1

            item_dict['sequence'] = sequence
            schemeitem_list.append(item_dict)


        return schemeitem_list


# PR2018-06-08
class Schemeitem_log(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    schemeitem_id = IntegerField(db_index=True)

    scheme_log = ForeignKey(Scheme_log, null=True, related_name='+', on_delete=CASCADE)
    subject_log = ForeignKey(Subject_log, null=True, related_name='+', on_delete=CASCADE)
    subjecttype_log = ForeignKey(Subjecttype_log, null=True,  related_name='+', on_delete=CASCADE)
    norm_log = ForeignKey(Norm_log, related_name='+', null=True, on_delete=CASCADE)

    gradetype = PositiveSmallIntegerField(null=True)
    weight_se = PositiveSmallIntegerField(null=True)
    weight_ce = PositiveSmallIntegerField(null=True)

    is_mandatory = BooleanField(default=False)
    is_combination = BooleanField(default=False)
    is_combi = BooleanField(default=False)

#   extra_count_allowed: only at Havo Vwo) 'PR2017-01-28
#   extra_nocount_allowed: at Vsbo TKL and Havo Vwo)) 'PR2017-01-28
#   elective_combi_allowed: only at Vwo and subject du fr sp 'PR2017-01-28
#   has_practexam: only at Vsbo PBL and PKL, all sectorprogramma's except uv 'PR2017-01-28

    extra_count_allowed = BooleanField(default=False)
    extra_nocount_allowed = BooleanField(default=False)
    elective_combi_allowed = BooleanField(default=False)
    has_practexam = BooleanField(default=False)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# PR2018-06-06 # PR2019-02-17
class Package(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    school = ForeignKey(sch_mod.School, related_name='packages', on_delete=CASCADE)
    scheme = ForeignKey(Scheme, related_name='packages', on_delete=CASCADE)

    name = CharField(max_length=50)

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name


# PR2018-06-06
class Package_log(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    package_id = IntegerField(db_index=True)

    school_log = ForeignKey(sch_mod.School_log, related_name='+', on_delete=CASCADE)
    scheme_log = ForeignKey(Scheme_log, null=True, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

    @property
    def mode_str(self):
        return c.MODE_DICT.get(str(self.mode),'-')


# PR2018-06-06
class Packageitem(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    package = ForeignKey(Package, related_name='packageschemes', on_delete=CASCADE)
    schemeitem = ForeignKey(Schemeitem, related_name='packageschemes', on_delete=CASCADE)


# PR2018-06-06
class Packageitem_log(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    packageitem_id = IntegerField(db_index=True)

    # TODO: refer to log table
    package_log = ForeignKey(Package_log, related_name='+', on_delete=CASCADE)
    schemeitem_log = ForeignKey(Schemeitem_log, related_name='+', on_delete=CASCADE)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)


# PR2018-06-06
class Cluster(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    school = ForeignKey(sch_mod.School, related_name='clusters', on_delete=CASCADE)
    subject = ForeignKey(Subject, related_name='clusters', on_delete=CASCADE)

    name = CharField(max_length=50)
    abbrev = CharField(max_length=20)
    depbases = ArrayField(IntegerField(), null=True)


    def __str__(self):
        return self.abbrev

# PR2018-06-06
class Cluster_log(sch_mod.AwpBaseModel):
    objects = sch_mod.AwpModelManager()

    cluster_id = IntegerField(db_index=True)

    # TODO: refer to log table
    school_log = ForeignKey(sch_mod.School_log, related_name='+', on_delete=CASCADE)
    subject_log = ForeignKey(Subject_log, related_name='+', on_delete=CASCADE)

    name = CharField(max_length=c.MAX_LENGTH_NAME, null=True)
    abbrev = CharField(max_length=c.MAX_LENGTH_20, null=True)
    depbases = ArrayField(IntegerField(), null=True)

    mode = CharField(max_length=c.MAX_LENGTH_01, null=True)

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
