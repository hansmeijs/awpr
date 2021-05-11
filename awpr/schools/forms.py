# PR2018-04-14

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import ModelForm, IntegerField, ChoiceField, CharField, MultipleChoiceField, SelectMultiple
from django.utils.translation import ugettext_lazy as _
from django.forms import modelformset_factory, inlineformset_factory, BaseFormSet

from schools.models import Country, Examyear, Department, School
from awpr import constants as c

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



# +++++++++++++++++++++  VALIDATORS  ++++++++++++++++++++++++++++++


# ===  Department  =====================================
class validate_unique_department_name(object):  # PR2018-08-15 PR2018-10-20
    def __init__(self, examyear, instance=None):
        self.examyear = examyear
        self.instance = instance
        # logger.debug('validate_unique_department_name __init__ self.instance: ' + str(self.instance))

    def __call__(self, value):
        if self.examyear and value:
            logger.debug('validate_unique_department_name __call__ value: ' + str(value))
            # __iexact looks for case-insensitive string. If value is None, it is interpreted as an SQL NULL
            if self.instance:
                # exclude value of this instance
                department = Department.objects.filter(name__iexact=value, examyear=self.examyear).exclude(pk=self.instance.id).first()
            else:
                department = Department.objects.filter(name__iexact=value, examyear=self.examyear).first()
            if department:
                raise ValidationError(
                    _("Department") + " '" + department.name + "' " + _("already exists") + "."
                )
        return value


# PR2018-08-11:
class validate_unique_department_abbrev(object):
    def __init__(self, examyear, instance=None):
        self.examyear = examyear
        self.instance = instance

    def __call__(self, value):
        if self.examyear and value:
            # logger.debug('validate_unique_department_name __call__ value: ' + str(value))
            # __iexact looks for case-insensitive string. If value is None, it is interpreted as an SQL NULL
            if self.instance:
                # exclude value of this instance
                department = Department.objects.filter(abbrev__iexact=value, examyear=self.examyear).exclude(pk=self.instance.id).first()
            else:
                department = Department.objects.filter(abbrev__iexact=value, examyear=self.examyear).first()
            if department:
                raise ValidationError(
                    _('Abbreviation') + ' ' + department.abbrev + ' ' + _('already exists') + '.'
                )
        return value


# ===  School  =====================================
class validate_unique_school_field(object):  # PR2018-08-27:
    def __init__(self, request_user, fieldname, instance=None):
        # TODO change request.user.examyear to sel_examyear
        self.examyear = request_user.examyear  # examyear has always value; None is blocked in accounts.FORM PERMITS
        self.fieldname = fieldname  # instance=None when adding new record
        self.instance = instance  # instance=None when adding new record

    def __call__(self, value):
        # functions checks if this schoolcode exists in this ezamyear and this country
        # __iexact looks for case-insensitive string. If value is None, it is interpreted as an SQL NULL
        if self.examyear and value: # self.examyear has always value
            if self.fieldname == 'name':
                if self.instance:
                    # Playlist.objects.filter(**{field_name: v})
                    # exclude value of this instance
                    school = School.objects.filter(name__iexact=value, examyear=self.examyear).exclude(
                        pk=self.instance.id).first()
                else:
                    school = School.objects.filter(name__iexact=value, examyear=self.examyear).first()
                if school:
                    raise ValidationError(
                        _('Schoolname') + ' ' + school.name + ' ' + _('already exists') + '.'
                    )
            elif self.fieldname == 'code':
                if self.instance:
                    school = School.objects.filter(code__iexact=value, examyear=self.examyear).exclude(
                        pk=self.instance.id).first()
                else:
                    school = School.objects.filter(code__iexact=value, examyear=self.examyear).first()
                if school:
                    raise ValidationError(
                        _('Schoolcode') + ' ' + school.code + ' ' + _('already exists') + '.'
                    )
            elif self.fieldname == 'abbrev':
                if self.instance:
                    school = School.objects.filter(abbrev__iexact=value, examyear=self.examyear).exclude(
                        pk=self.instance.id).first()
                else:
                    school = School.objects.filter(abbrev__iexact=value, examyear=self.examyear).first()
                if school:
                    raise ValidationError(
                        _('Short schoolname') + ' ' + school.abbrev + ' ' + _('already exists') + '.'
                    )
        return value


# http://www.learningaboutelectronics.com/Articles/How-to-create-a-custom-field-validator-in-Django.php
def validate_school_email(value):
    if not ".edu" in value:
        raise ValidationError("A valid school email must be entered in")
    else:
        return value

# PR2018-06-14 was for testing:
def validate_length(value):
    if len(value) > 10:
        raise ValidationError(
            _('%(value)s exceeds 10 characters.'),
            params={'value': value},
        )
