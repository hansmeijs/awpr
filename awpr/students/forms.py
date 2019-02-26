# PR2018-09-03
from django.forms import Form, ModelForm, CharField, ChoiceField, MultipleChoiceField, SelectMultiple, ModelChoiceField, TextInput
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from students.models import Student, Result, Studentsubject, Grade, Birthcountry, Birthcity

from schools.models import Country, Examyear
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

# from https://snakeycode.wordpress.com/2015/02/11/django-dynamic-modelchoicefields/
class AjaxModelChoiceField(ModelChoiceField):
    def __init__(self, model_class, *args, **kwargs):
        queryset = model_class.objects.none()
        super(AjaxModelChoiceField, self).__init__(queryset, *args, **kwargs)
        self.model_class = model_class

    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or 'pk'
            value = self.model_class.objects.get(**{key: value})
        except (ValueError, self.queryset.model.DoesNotExist):
            raise ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')
        return value




# === Student =====================================

class StudentAddForm(ModelForm):  # PR2018-08-09
    class Meta:
        model = Student
        fields = ('school', 'department', 'lastname', 'firstname', 'prefix', 'gender', 'idnumber', 'birthdate')
        labels = {
            "school": _('School'),
            "department": _('Department'),
            "lastname": _('Last name'),
            "firstname": _('First name'),
            "prefix": _('Prefix'),
            "gender": _('Gender'),
            "idnumber": _('ID number'),
            "birthdate": _('Birthdate'),
        }

    # PR2018-06-09 from https://stackoverflow.com/questions/16205908/django-modelform-not-required-field/30403969?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    def __init__(self, *args, **kwargs):
        # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        self.request = kwargs.pop('request', None)
        super(StudentAddForm, self).__init__(*args, **kwargs)

        # ======= field 'school' ============
        self.initial['school'] = self.request.user.school.id
        self.fields['school'].disabled = True

        # ======= field 'department' ============
        self.initial['department'] = self.request.user.department.id
        self.fields['department'].disabled = True

        # ======= field 'lastname' ============
        self.fields['lastname'] = CharField(
            max_length = 80,
            required = True,
            # validators=[validate_unique_subject_name(request.user.country)]
            )
        self.fields['lastname'].widget.attrs.update({'autofocus': 'autofocus'})

        # ======= field 'firstname' ============
        self.fields['firstname'] = CharField(
            max_length = 80,
            required = True,
            # validators=[validate_unique_subject_abbrev(request.user.country)]
            )

        # ======= field 'birthcountry_field' ============
        self.choices = [(0, '---')]
        for _item in Birthcountry.objects.all():
            self.choices.append((_item.id, _item.name))
        # logger.debug('StudentAddForm __init__  self.choices: ' + str(self.choices))
        self.fields['birthcountry_field'] = ChoiceField(
            required=False,
            # choises must be tuple or list, dictionary gives error: 'int' object is not iterable
            choices=self.choices,
            label=_('Country of birth'),
            # PR2018-07-31 debug: use schooldefault.id instead of schooldefault.
            # This showed always first item in choices: initial=self.this_instance.schooldefault
            # initial=self.birthcountry
        )
        # ======= field 'birthcity_list' ============
        self.choices = [(0, '---')]
        for _item in Birthcity.objects.all():
            self.choices.append((_item.id, _item.name))
        # logger.debug('StudentAddForm __init__  self.choices: ' + str(self.choices))
        #self.fields['birthcity_field'] = ChoiceField(
        #    required=False,
            # choises must be tuple or list, dictionary gives error: 'int' object is not iterable
            # choices=self.choices,
            label=_('City of birth'),
            # PR2018-07-31 debug: use schooldefault.id instead of schooldefault.
            # This showed always first item in choices: initial=self.this_instance.schooldefault
            # initial=self.birthcountry
        #)

        #self.fields['birthcity_field'] = AjaxModelChoiceField(
        #    Birthcity,
        #    label=_('Test City of birth'),)


        # self.fields['schooldefault_list'].disabled = self.is_disabled


class StudentEditForm(ModelForm):  # PR2018-08-11
    class Meta:
        model = Student
        fields = ('school', 'department', 'level', 'sector', 'lastname', 'firstname', 'prefix', 'gender', 'idnumber', 'birthdate')
        labels = {
            "school": _('School'),
            "department": _('Department'),
            "level": _('Level'),
            "sector": _('Sector'),
            "lastname": _('Last name'),
            "firstname": _('First name'),
            "prefix": _('Prefix'),
            "gender": _('Gender'),
            "idnumber": _('ID number'),
            "birthdate": _('Birthdate'),
        }

    def __init__(self, *args, **kwargs):
        # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        self.request = kwargs.pop('request', None)
        super(StudentEditForm, self).__init__(*args, **kwargs)

        # self.this_instance = kwargs.get('instance')

        # ======= field 'school' ============
        self.fields['school'].disabled = True

        # ======= field 'department' ============
        self.fields['department'].disabled = True


# === Student result =====================================
class ResultEditForm(ModelForm):  # PR2018-11-21
    class Meta:
        model = Result
        fields = ('grade_ce_avg', 'grade_ce_avg_text', 'grade_combi_avg_text',
                  'endgrade_sum', 'endgrade_count', 'endgrade_avg', 'endgrade_avg_text',
                  'result', 'result_info', 'result_status'
                  )

    def __init__(self, *args, **kwargs):
        # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        self.request = kwargs.pop('request', None)
        super(ResultEditForm, self).__init__(*args, **kwargs)

        # self.this_instance = kwargs.get('instance')

        # ======= field 'school' ============
        self.fields['school'].disabled = True

        # ======= field 'department' ============
        self.fields['department'].disabled = True


# === Studentsubject =====================================
class StudentsubjectAddForm(ModelForm):  # PR2018-11-27
    class Meta:
        model = Studentsubject
        fields = ( 'schemeitem',  'cluster',
            'is_extra_nocount', 'is_extra_counts', 'is_choice_combi',
            'pws_title', 'pws_subjects',
            'has_exemption', 'has_reex', 'has_reex03', 'has_pok', 'has_pok_status'
        )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(StudentsubjectAddForm, self).__init__(*args, **kwargs)

class StudentsubjectEditForm(ModelForm):  # PR2018-11-24
    class Meta:
        model = Studentsubject
        exclude = ()

    def __init__(self, *args, **kwargs):
        #logger.debug('SchemeitemEditForm kwargs: ' + str(kwargs) + ' Type: ' + str(type(kwargs)))

        self.request = kwargs.pop('request', None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        # self.src = kwargs.pop('src', None)
        super(StudentsubjectEditForm, self).__init__(*args, **kwargs)
        #self.this_instance = kwargs.get('instance')




class StudentsubjectFormsetForm(ModelForm):  # PR2018-11-29
    class Meta:
        model = Studentsubject
        exclude = ()

    pws_title = CharField(
        label='pws_title',
        widget=TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter pws_title here'
        })
    )

StudentsubjectFormset = modelformset_factory(
    Studentsubject,
    fields=('pws_title',),
    extra=1,
    widgets={'pws_title': TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter pws_title here'
        })
    }
)

#StudentsubjectFormset = modelformset_factory(Result,  # parent form
#                                            StudentsubjectFormsetForm,  # inline-form
#                                            #fk_name='studres_studsubs',
#                                            fields=['result', 'pws_title',], # inline-form fields
#                                            # labels for the fields
#                                            labels={
#                                                  'pws_title': _(u'Question and '
#                                                                    u'deliverable'),
#                                            },
#                                            # help texts for the fields
#                                            help_texts={
#                                                  'pws_title': 'help texts for the fields',
#                                            },
#                                            # set to false because cant' delete an non-exsitant instance
##                                            can_delete=False,
#                                            # how many inline-forms are sent to the template by default
#                                            extra=1)


# === Grade =====================================
class GradeAddForm(ModelForm):  # PR2018-11-27
    class Meta:
        model = Grade
        fields = ( 'studentsubject', 'examcode', 'gradecode', 'period', 'value', 'status' , 'published'
        )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(GradeAddForm, self).__init__(*args, **kwargs)

class GradeEditForm(ModelForm):  # PR2018-11-24
    class Meta:
        model = Grade
        exclude = ()

    def __init__(self, *args, **kwargs):
        #logger.debug('SchemeitemEditForm kwargs: ' + str(kwargs) + ' Type: ' + str(type(kwargs)))

        self.request = kwargs.pop('request', None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        # self.src = kwargs.pop('src', None)
        super(GradeEditForm, self).__init__(*args, **kwargs)
        #self.this_instance = kwargs.get('instance')



#  =========== Functions  ===========
def birthcountry_choices():
    _choices = []
    for _item in Birthcountry.objects.all():
        _choices.append((_item.id, _item.name))

    # logger.debug('class User(AbstractUser) schooldefault_choices: ' + str(_choices))
    return _choices