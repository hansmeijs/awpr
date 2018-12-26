# PR2018-07-20
from django.core.exceptions import ValidationError
from django.forms import Form, ModelForm, CharField, ChoiceField, MultipleChoiceField, SelectMultiple
from django.forms import TextInput, URLField, URLInput
from django.forms.formsets import BaseFormSet

from django.forms import Select # PR2018-10-23 to add attr to select options

from django.utils.translation import ugettext_lazy as _
from awpr import constants as c
from schools.models import Country, Department
from subjects.models import Level, Sector, Subjecttype, Scheme, Schemeitem, Subject

# PR2018-04-20 from: https://experiencehq.net/articles/better-django-modelform-html
#class BaseModelForm(ModelForm):
#    def __init__(self, *args, **kwargs):
#        kwargs.setdefault('auto_id', '%s')
#        kwargs.setdefault('label_suffix', '')
#        super().__init__(*args, **kwargs)
#        for field_name in self.fields:
#            field = self.fields.get(field_name)
#            if field:
#                field.widget.attrs.update({
#                    'placeholder': field.help_text
#                })

# PR2018-05-04
import logging
logger = logging.getLogger(__name__)


# === Level =====================================
class LevelAddForm(ModelForm):
    class Meta:
        model = Level
        fields = ('name', 'abbrev', 'sequence')
        labels = {'name': _('Name'), 'abbrev': _('Abbreviation'), 'sequence': _('Sequence')}

    # PR2018-06-09 from https://stackoverflow.com/questions/16205908/django-modelform-not-required-field/30403969?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # called by SubjectdefaultAddForm(request=request) in SubjectdefaultAddView.get and -.post
    def __init__(self, *args, **kwargs):
        # request is added as parameter in ExamyearAddView by form = ExamyearAddForm(request=request)
        # pop() removes and returns an element from a dictionary, second argument is default when not foundrequest = kwargs.pop('request', None)  # pop() removes and returns an element from a dictionary, second argument is default when not found
        self.request = kwargs.pop('request', None)
        super(LevelAddForm, self).__init__(*args, **kwargs)

        # ======= field 'name' ============
        self.fields['name'] = CharField(
            max_length = 50,
            required = True,
            validators=[validate_unique_level_name(self.request.user.examyear)]
        )
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'}) # , 'placeholder': 'Default subject name'

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            max_length = 6,
            required = True,
            validators=[validate_unique_level_abbrev(self.request.user.examyear)]
        )

        # ======= field 'depbase_list' ============
        # in AddMode: get examyear from request.user
        dep_choices = Department.depbase_list_choices(examyear=self.request.user.examyear)
        self.fields['depbase_list_field'] = MultipleChoiceField(
            required=False,
            widget=SelectMultiple,
            choices=dep_choices,
            label=_('Departments'),
            help_text=_('Select the departments where this level is available. Press the Ctrl button to select multiple departments.')
        )

class LevelEditForm(ModelForm):  # PR2018-08-11
    class Meta:
        model = Level
        fields = ('examyear', 'name', 'abbrev', 'sequence')
        labels = {'examyear': _('Exam year'),  'name': _('Name'), 'abbrev': _('Abbreviation'), 'sequence': _('Sequence')}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        super(LevelEditForm, self).__init__(*args, **kwargs)

        self.this_instance = kwargs.get('instance')

        # ======= field 'examyear' ============
        self.fields['examyear'].disabled = True

        # ======= field 'name' ============
        self.fields['name'] = CharField(
            max_length = 50,
            required = True,
            validators=[validate_unique_level_name(self.request.user.examyear, self.this_instance)])
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'})

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            max_length = 8,
            required = True,
            validators=[validate_unique_level_abbrev(self.request.user.examyear, self.this_instance)])

        # ======= field 'depbase_list' ============
        # in EditMode: get country from current record
        dep_choices = Department.depbase_list_choices(examyear=self.this_instance.examyear)
        self.fields['depbase_list_field'] = MultipleChoiceField(
            required=False,
            widget=SelectMultiple,
            choices=dep_choices,
            label=_('Departments'),
            help_text=_('Select the departments where this level is available. Press the Ctrl button to select multiple departments.'),
            initial=self.this_instance.depbase_list_tuple
        )

        # NOT IN USE ======= field 'is_active' ============
        # PR2018-08-09 value in is_active is stored as str: '0'=False, '1'=True, default=True
        #__initial_is_active = 1
        # if self.this_instance is not None:
        #     __initial_is_active = int(self.this_instance.is_active)
        # self.fields['is_active_field'] = ChoiceField(
        #     choices=c.IS_ACTIVE_CHOICES,
        #     label=_('Active'),
        #     initial=__initial_is_active)


# === Sector =====================================
class SectorAddForm(ModelForm): # PR2018-08-24
    class Meta:
        model = Sector
        fields = ('name', 'abbrev', 'sequence')
        labels = {'name': _('Name'), 'abbrev': _('Abbreviation'), 'sequence': _('Sequence')}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(SectorAddForm, self).__init__(*args, **kwargs)

        # ======= field 'name' ============
        self.fields['name'] = CharField(
            max_length = 50,
            required = True,
            validators=[validate_unique_sector_name(self.request.user.examyear)]
        )
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'}) # , 'placeholder': 'Default subject name'

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            max_length = 6,
            required = True,
            validators=[validate_unique_sector_abbrev(self.request.user.examyear)]
        )

        # ======= field 'base' ============
        # in AddMode: get country from request.user
        dep_choices = Department.depbase_list_choices(examyear=self.request.user.examyear)
        self.fields['depbase_list_field'] = MultipleChoiceField(
            required=False,
            widget=SelectMultiple,
            choices=dep_choices,
            label=_('Departments'),
            help_text=_('Select the departments where this sector is available. Press the Ctrl button to select multiple departments.'),
        )


class SectorEditForm(ModelForm):  # PR2018-08-24
    class Meta:
        model = Sector
        fields = ('examyear', 'name', 'abbrev', 'sequence')
        labels = {'examyear': _('Exam year'),  'name': _('Name'), 'abbrev': _('Abbreviation'), 'sequence': _('Sequence')}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        super(SectorEditForm, self).__init__(*args, **kwargs)

        self.this_instance = kwargs.get('instance')

        # ======= field 'examyear' ============
        self.fields['examyear'].disabled = True

        # ======= field 'name' ============
        self.fields['name'] = CharField(
            max_length = 50,
            required = True,
            validators=[validate_unique_sector_name(self.request.user.examyear, self.this_instance)])
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'})

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            max_length = 8,
            required = True,
            validators=[validate_unique_sector_abbrev(self.request.user.examyear, self.this_instance)])

        # ======= field 'depbase_list' ============
        # in EditMode: get country from current record
        dep_choices = Department.depbase_list_choices(examyear=self.request.user.examyear)
        self.fields['depbase_list_field'] = MultipleChoiceField(
            required=False,
            widget=SelectMultiple,
            choices=dep_choices,
            label=_('Departments'),
            help_text=_('Select the departments where this sector is available. Press the Ctrl button to select multiple departments.'),
            initial=self.this_instance.depbase_list_tuple
        )

# === Subjecttype =====================================
class SubjecttypeAddForm(ModelForm):
    class Meta:
        model = Subjecttype
        fields = ('name', 'abbrev', 'sequence')
        labels = {'name': _('Name'), 'abbrev': _('Abbreviation'), 'sequence': _('Sequence')}

    # PR2018-06-09 from https://stackoverflow.com/questions/16205908/django-modelform-not-required-field/30403969?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # called by SubjectdefaultAddForm(request=request) in SubjectdefaultAddView.get and -.post
    def __init__(self, *args, **kwargs):
        # request is added as parameter in ExamyearAddView by form = ExamyearAddForm(request=request)
        # pop() removes and returns an element from a dictionary, second argument is default when not foundrequest = kwargs.pop('request', None)  # pop() removes and returns an element from a dictionary, second argument is default when not found
        self.request = kwargs.pop('request', None)
        super(SubjecttypeAddForm, self).__init__(*args, **kwargs)

        # ======= field 'name' ============
        self.fields['name'] = CharField(
            max_length = 50,
            required = True,
            # validators=[validate_unique_subjecttype_name(self.request.user.examyear)]
        )
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'}) # , 'placeholder': 'Default subject name'

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            max_length = 6,
            required = True,
            # validators=[validate_unique_subjecttype_abbrev(self.request.user.examyear)]
        )

        # ======= field 'depbase_list' ============
        # in AddMode: get examyear from request.user
        dep_choices = Department.depbase_list_choices(examyear=self.request.user.examyear)
        self.fields['depbase_list_field'] = MultipleChoiceField(
            required=False,
            widget=SelectMultiple,
            choices=dep_choices,
            label=_('Departments')
        )

class SubjecttypeEditForm(ModelForm):  # PR2018-08-11
    class Meta:
        model = Subjecttype
        fields = ('examyear', 'name', 'abbrev', 'code', 'sequence')
        labels = {'examyear': _('Exam year'),  'name': _('Name'), 'abbrev': _('Abbreviation'), 'sequence': _('Sequence')}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        super(SubjecttypeEditForm, self).__init__(*args, **kwargs)

        self.this_instance = kwargs.get('instance')

        # ======= field 'examyear' ============
        self.fields['examyear'].disabled = True

        # ======= field 'name' ============
        self.fields['name'] = CharField(
           #  validators=[validate_unique_subjecttype_name(self.request.user.examyear, self.this_instance)]
        )
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'})

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            # validators=[validate_unique_subjecttype_abbrev(self.request.user.examyear, self.this_instance)]
        )

        # ======= field 'depbase_list' ============
        # in EditMode: get country from current record
        dep_choices = Department.depbase_list_choices(examyear=self.this_instance.examyear)
        self.fields['depbase_list_field'] = MultipleChoiceField(
            required=False,
            widget=SelectMultiple,
            choices=dep_choices,
            label=_('Departments'),
            help_text=_('Select the departments where this level is available. Press the Ctrl button to select multiple departments.'),
            initial=self.this_instance.depbase_list_tuple
        )

        # NOT IN USE ======= field 'is_active' ============
        # PR2018-08-09 value in is_active is stored as str: '0'=False, '1'=True, default=True
        #__initial_is_active = 1
        # if self.this_instance is not None:
        #     __initial_is_active = int(self.this_instance.is_active)
        # self.fields['is_active_field'] = ChoiceField(
        #     choices=c.IS_ACTIVE_CHOICES,
        #     label=_('Active'),
        #     initial=__initial_is_active)



# === Schemeitem =====================================
class SchemeitemAddForm(ModelForm): # PR2018-08-24
    class Meta:
        model = Schemeitem
        fields = ('department', 'level', 'sector', 'name')
        labels = {'department': _('Department'), 'level': _('Level'), 'sector': _('Sector'), 'name': _('Name')}


        fields = ('school',
                  'scheme',
                  'subject',
                  'subjecttype',
                  'gradetype',
                  'sequence',
                  'weightSE',
                  'weightCE',
                  'is_mandatory',
                  'is_combi',
                  'choicecombi_allowed',
                  'has_practexam',
                  'is_template',
                  'is_voided_id',
                  )

        labels = {
            'subjecttype': _('Subject type'),
            'gradetype': _('Grade type'),
            'weightSE': _('Weight SE'),
            'weightCE': _('Weight CE'),
            'is_mandatory': _('Mandatory'),
            'is_combi': _('Combi subject'),
            'choicecombi_allowed': _('Choice combi'),
            'has_practexam': _('Has practical exam'),
            'is_template': _('Template'),
            'is_voided_id': _('Voided')}


    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        # PR2018-10-23 from //https://stackoverflow.com/questions/6477856/how-to-add-attributes-to-option-tags-in-django
        super(SchemeitemAddForm, self).__init__(*args, **kwargs)


class SchemeitemEditForm(ModelForm):  # PR2018-08-11
    class Meta:
        model = Schemeitem
        fields = ('school', 'scheme', 'subject', 'subjecttype', 'gradetype', 'sequence', 'weightSE', 'weightCE',
                  'is_mandatory', 'is_combi', 'choicecombi_allowed', 'has_practexam', 'is_template', 'is_voided_id')

        labels = {'subjecttype': _('Subject type'), 'gradetype': _('Grade type'),
                  'weightSE': _('SE weight'), 'weightCE': _('CE weight'),
                  'is_mandatory': _('Mandatory'), 'is_combi': _('Combination'),
                  'choicecombi_allowed': _('Choice combi allowed'),
                  'has_practexam': _('Practical exam'),
                  'is_template': _('Template'), 'is_voided_id': _('Voided')}


    def __init__(self, *args, **kwargs):
        #logger.debug('SchemeitemEditForm kwargs: ' + str(kwargs) + ' Type: ' + str(type(kwargs)))

        self.request = kwargs.pop('request', None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        # self.src = kwargs.pop('src', None)
        super(SchemeitemEditForm, self).__init__(*args, **kwargs)
        #self.this_instance = kwargs.get('instance')


# === Scheme =====================================
class SchemeAddForm(ModelForm): # PR2018-08-24
    class Meta:
        model = Scheme
        fields = ('department', 'level', 'sector', 'name')
        labels = {'department': _('Department'), 'level': _('Level'), 'sector': _('Sector'), 'name': _('Name')}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        # PR2018-10-23 from //https://stackoverflow.com/questions/6477856/how-to-add-attributes-to-option-tags-in-django
        super(SchemeAddForm, self).__init__(*args, **kwargs)

        # ======= field 'department' ============
        self.dep_choices = Department.depbase_list_choices(examyear=self.request.user.examyear, show_none=True)
        if self.dep_choices:
            self.fields['department'].choices = self.dep_choices

class SchemeEditForm(ModelForm):  # PR2018-08-11
    class Meta:
        model = Scheme
        fields = ('department', 'level', 'sector', 'name')
        labels = {'department': _('Department'), 'level': _('Level'), 'sector': _('Sector'), 'name': _('Name')}

    def __init__(self, *args, **kwargs):
        #logger.debug('SchemeEditForm kwargs: ' + str(kwargs) + ' Type: ' + str(type(kwargs)))

        self.request = kwargs.pop('request', None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        # self.src = kwargs.pop('src', None)
        super(SchemeEditForm, self).__init__(*args, **kwargs)
        #self.this_instance = kwargs.get('instance')

        # TODO: country en examyear not showing in header

        # ======= field 'department' ============
        self.dep_choices = Department.depbase_list_choices(examyear=self.request.user.examyear, show_none=True)
        if self.dep_choices:
            self.fields['department'].choices = self.dep_choices

            # PR2018-08-04 should use self.initial['country'] instead of self.fields['country'].initial =  'override'
        # self.initial['department_list'] = self.this_instance.department







# === Subject =====================================
# PR2018-08-09
class SubjectAddForm(ModelForm):
    class Meta:
        model = Subject
        fields = ('examyear', 'name', 'abbrev', 'sequence')
        labels = {
            "examyear": _('Exam year'),
            "name": _('Name'),
            "abbrev": _('Abbreviation'),
            "sequence": _('Sequence')
        }

    # PR2018-06-09 from https://stackoverflow.com/questions/16205908/django-modelform-not-required-field/30403969?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # called by SubjectdefaultAddForm(request=request) in SubjectdefaultAddView.get and -.post
    def __init__(self, *args, **kwargs):
        # request is added as parameter in ExamyearAddView by form = ExamyearAddForm(request=request)
        # pop() removes and returns an element from a dictionary, second argument is default when not foundrequest = kwargs.pop('request', None)  # pop() removes and returns an element from a dictionary, second argument is default when not found
        self.request = kwargs.pop('request', None)
        super(SubjectAddForm, self).__init__(*args, **kwargs)
        # logger.debug('SubjectAddForm __init__ request: ' + str(request))

        # self.selected_subject = kwargs.get('instance')

        # ======= field 'examyear' ============
        # PR2018-08-09 should use self.initial['examyear'] instead of self.fields['examyear'].initial =  'override'
        # see https://avilpage.com/2015/03/django-form-gotchas-dynamic-initial.html
        self.initial['examyear'] = self.request.user.examyear.id
        self.fields['examyear'].disabled = True

        # ======= field 'name' ============
        self.fields['name'] = CharField(
           #  max_length = 50,
           #  required = True,
            validators=[validate_unique_subject_name(self.request.user.examyear)]
        )
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'}) # , 'placeholder': 'Default subject name'

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            # max_length = 10,
            # required = True,
            validators=[validate_unique_subject_abbrev(self.request.user.examyear)])

        # ======= field 'depbase_list' ============
        # in AddMode: get examyear from request.user
        dep_choices = Department.depbase_list_choices(examyear=self.request.user.examyear)
        self.fields['depbase_list_field'] = MultipleChoiceField(
            required=False,
            widget=SelectMultiple,
            choices=dep_choices,
            label=_('Departments'),
            help_text=_('Select the departments where this subject is available. Press the Ctrl button to select multiple departments.'),
        )


class SubjectEditForm(ModelForm):  # PR2018-08-11
    class Meta:
        model = Subject
        fields = ('examyear', 'name', 'abbrev', 'sequence')
        labels = {'examyear': _('Exam year'),  'name': _('Name'), 'abbrev': _('Abbreviation'), 'sequence': _('Sequence')}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        super(SubjectEditForm, self).__init__(*args, **kwargs)

        self.this_instance = kwargs.get('instance')

        # ======= field 'examyear' ============
        self.fields['examyear'].disabled = True

        # ======= field 'name' ============
        self.fields['name'] = CharField(
            # max_length = 50,
            # required = True,
            # validators=[validate_unique_level_name(self.request.user.examyear, self.this_instance)]
            )
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'})

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            # max_length = 10,
            # required = True,
            # validators=[validate_unique_level_abbrev(self.request.user.examyear, self.this_instance)]
            )

        # ======= field 'depbase_list' ============
        # in EditMode: get country from current record
        dep_choices = Department.depbase_list_choices(examyear=self.this_instance.examyear)
        self.fields['depbase_list_field'] = MultipleChoiceField(
            required=False,
            widget=SelectMultiple,
            choices=dep_choices,
            label=_('Departments'),
            help_text=_('Select the departments where this subject is available. Press the Ctrl button to select multiple departments.'),
            initial=self.this_instance.depbase_list_tuple
        )

# +++++++++++++++++++++  VALIDATORS  ++++++++++++++++++++++++++++++

# ===  Level  =====================================
# PR2018-08-06:
class validate_unique_level_name(object):
    def __init__(self, examyear, instance=None):
        self.examyear = examyear
        if instance:
            self.instance_id = instance.id
        else:
            self.instance_id = None

    def __call__(self, value):
        # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
        if value is None:
            _value_exists = False
        elif self.instance_id is None:
            _value_exists = Level.objects.filter(name__iexact=value, examyear=self.examyear).exists()
        else:
            _value_exists = Level.objects.filter(name__iexact=value, examyear=self.examyear).exclude(pk=self.instance_id).exists()
        if _value_exists:
            raise ValidationError(_('Level name already exists.'))
        return value

# PR2018-08-11:
class validate_unique_level_abbrev(object):
    def __init__(self, examyear, instance=None):
        self.examyear = examyear
        if instance is None:
            # instance_id gets value=-1 when adding new record, to skip exclude
            self.instance_id = -1
        else:
            self.instance_id = instance.id

    def __call__(self, value):
        # logger.debug('validate_unique_level_abbrev __call__ value: ' + str(value))
        # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
        _value_exists = False
        if value is not None:
            _value_exists = Level.objects.filter(abbrev__iexact=value, examyear=self.examyear).exclude(pk=self.instance_id).exists()
        if _value_exists:
            raise ValidationError(_('Abbreviation of level already exists.'))
        # logger.debug('validate_unique_level_abbrev __init__ _value_exists: ' + str(_value_exists))
        return value

# ===  Sector  =====================================
class validate_unique_sector_name(object):  # PR2018-08-24
    def __init__(self, examyear, instance=None):
        self.examyear = examyear
        if instance:
            self.instance_id = instance.id
        else:
            self.instance_id = None

    def __call__(self, value):
        # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
        if value is None:
            _value_exists = False
        elif self.instance_id is None:
            _value_exists = Sector.objects.filter(name__iexact=value, examyear=self.examyear).exists()
        else:
            _value_exists = Sector.objects.filter(name__iexact=value, examyear=self.examyear).exclude(pk=self.instance_id).exists()
        if _value_exists:
            raise ValidationError(_('Sector name already exists.'))
        return value

class validate_unique_sector_abbrev(object):  # PR2018-08-24
    def __init__(self, examyear, instance=None):
        self.examyear = examyear
        if instance:
            self.instance_id = instance.id
        else:
            self.instance_id = None

    def __call__(self, value):
        # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
        if value is None:
            _value_exists = False
        elif self.instance_id is None:
            _value_exists = Sector.objects.filter(abbrev__iexact=value, examyear=self.examyear).exists()
        else:
            _value_exists = Sector.objects.filter(abbrev__iexact=value, examyear=self.examyear).exclude(pk=self.instance_id).exists()
        if _value_exists:
            raise ValidationError(_('Abbreviation of sector already exists.'))
        return value

# ===  Subjectdefault  =====================================
# TODO test PR2-18-10-18
class validate_unique_subject_name(object):  # PR2018-08-16:
    def __init__(self, examyear, instance=None):
        self.examyear = examyear
        self.instance = instance
        # logger.debug('validate_unique_subjectdefault_name __init__ self.instance: ' + str(self.instance))

    def __call__(self, value):
        if self.examyear and value:
            # logger.debug('validate_unique_subjectdefault_name __call__ value: ' + str(value))
            # __iexact looks for case-insensitive string. If value is None, it is interpreted as an SQL NULL
            if self.instance:
                # exclude value of this instance
                subject = Subject.objects.filter(name__iexact=value, examyear=self.examyear).exclude(pk=self.instance.id).first()
            else:
                subject = Subject.objects.filter(name__iexact=value, examyear=self.examyear).first()
            if subject:
                raise ValidationError(_('Name "%s" already exists.' %subject.name))
        return value

# TODO test PR2-18-10-18
class validate_unique_subject_abbrev(object):  # PR2018-08-16:
# TODO test PR2-18-10-18
    def __init__(self, examyear, instance=None):
        self.examyear = examyear
        self.instance = instance

    def __call__(self, value):
        if self.examyear and value:
            # __iexact looks for case-insensitive string. If value is None, it is interpreted as an SQL NULL
            if self.instance:
                # exclude value of this instance
                subject = Subject.objects.filter(abbrev__iexact=value, examyear=self.examyear).exclude(pk=self.instance.id).first()
            else:
                subject = Subject.objects.filter(abbrev__iexact=value, examyear=self.examyear).first()
            if subject:
                raise ValidationError(_('Abbreviation "%s" already exists.' %subject.abbrev))
        return value


# === VALIDATORS =====================================
# PR2018-08-06:
class validate_unique_subject_name(object):
    def __init__(self, examyear):
        self.examyear = examyear
        # logger.debug('validate_unique_subject __init__ self.examyear: ' + str(self.examyear))

    def __call__(self, value):
        # logger.debug('validate_unique_subjec __call__ value: ' + str(value))
        # filter a Case-insensitive exact match.
        if Subject.objects.filter(name__iexact=value, examyear=self.examyear).exists():
            #logger.debug('validate_unique_subjectdefault ValidationError: Default subject exists')
            # raise ValidationError({'subjectdefault':[_('Subject already exists.'),]})
            raise ValidationError(_('Subject already exists.'))
        return value

# PR2018-08-09:
class validate_unique_subject_abbrev(object):
    def __init__(self, examyear):
        self.examyear = examyear
        # logger.debug('validate_unique_subject_abbrev __init__ self.examyear: ' + str(self.examyear))

    def __call__(self, value):
        # logger.debug('validate_unique_subject_abbrev __call__ value: ' + str(value))
        # filter a Case-insensitive exact match.
        if Subject.objects.filter(abbrev__iexact=value, examyear=self.examyear).exists():
            # logger.debug('validate_unique_subject_abbrev ValidationError: Default subject exists')
            # raise ValidationError({'subject':[_('Abbreviation of default subject already exists.'),]})
            raise ValidationError(_('Abbreviation of default subject already exists.'))
        return value

