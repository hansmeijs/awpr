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



class CountryFormsetForm(ModelForm):  # PR2018-11-24
    class Meta:
        model = Country
        exclude = ()

    # PR2018-06-09 from https://stackoverflow.com/questions/16205908/django-modelform-not-required-field/30403969?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    def __init__(self, *args, **kwargs):
        super(CountryFormsetForm, self).__init__(*args, **kwargs)

        self.fields['name'] = CharField(
            max_length = 20,
            required = True,
            label=_('CountryTEST'),
            # validators=[v.validate_length] Not necessary: is set in Model
        )
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'}) # , 'placeholder': 'Country name'

        # 2018-07-20
        self.fields['abbrev'] = CharField(
            max_length = 6,
            required = True,
            label=_('Abbreviation'),
            # validators=[v.validate_length] Not necessary: is set in Model
        )

CountryFormSet = modelformset_factory(Country, form=CountryFormsetForm, exclude=(), extra=1, can_delete=True)
"""
class CountryFormSet(BaseFormSet):
    model = Country
    absolute_max = 50
    form = CountryFormsetForm
    can_order = False
    can_delete = False
    min_num = 0
    max_num = 50
    extra = 1
    validate_max = False
    validate_min= False

    def clean(self):
      
        Adds validation to check that no two links have the same anchor or URL
        and that all links have both an anchor and URL.
        
        if any(self.errors):
            return

        names = []
        abbrevs = []
        duplicates = False

        for form in self.forms:
            if form.cleaned_data:
                name = form.cleaned_data['name']
                abbrev = form.cleaned_data['abbrev']

                # Check that no two links have the same name or abbrev
                if name and abbrev:
                    if name in names:
                        duplicates = True
                        names.append(name)

                    if abbrev in abbrevs:
                        duplicates = True
                        abbrevs.append(abbrev)

                if duplicates:
                    raise ValidationError(
                        'Links must have unique anchors and abbrevs.',
                        code='duplicate_links'
                    )

                # Check that all links have both an anchor and abbrev
                if abbrev and not name:
                    raise ValidationError(
                        'All links must have an name.',
                        code='missing_name'
                    )
                elif name and not abbrev:
                    raise ValidationError(
                        'All links must have a abbrev.',
                        code='missing_abbrev'
                    )


StudentFormSet = inlineformset_factory(
    parent_model=School,
    model=Student,
    fields=('lastname', 'firstname', 'prefix', 'gender'),
    exclude=(),
    extra=1
)
"""


class CountryAddForm(ModelForm):
    # only users with role=System and permit=Admin can add country

    class Meta:
        model = Country
        fields = ('name', 'abbrev')

    # PR2018-06-09 from https://stackoverflow.com/questions/16205908/django-modelform-not-required-field/30403969?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    def __init__(self, *args, **kwargs):
        super(CountryAddForm, self).__init__(*args, **kwargs)

        self.fields['name'] = CharField(
            max_length = 20,
            required = True,
            label=_('Country'),
            # validators=[v.validate_length] Not necessary: is set in Model
        )
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'}) # , 'placeholder': 'Country name'

        # 2018-07-20
        self.fields['abbrev'] = CharField(
            max_length = 6,
            required = True,
            label=_('Abbreviation'),
            # validators=[v.validate_length] Not necessary: is set in Model
        )

    # PR2018-06-14 this one works, but I dont like it: 1) better put validation in Model 2) dont use try
    # override the clean_<fieldname> method to validate the field yourself
    # http://cheng.logdown.com/posts/2015/05/25/django-customize-error-messages-on-the-user-registration-form
    # def clean_country(self):
    #     country = self.cleaned_data["country"]
    #     try:
    #         Country._default_manager.get(country=name)
    #         # if the country exists, then let's raise an error message
    #         raise ValidationError(
    #             self.error_messages['duplicate_countryname'],  # user my customized error message
    #             code='duplicate_username',  # set the error message key )
    #     except Country.DoesNotExist:
    #         logger.debug('CountryAddForm clean_country except Country.DoesNotExist: ' + str(country))
    #         return country  # great, this country does not exist so we can continue the  process


class CountryEditForm(ModelForm):
    class Meta:
        model = Country
        fields = ('name', 'abbrev')

    # PR2018-06-09 from https://stackoverflow.com/questions/16205908/django-modelform-not-required-field/30403969?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    def __init__(self, *args, **kwargs):
        super(CountryEditForm, self).__init__(*args, **kwargs)
        self.selected_country = kwargs.get('instance')

    # add field locked
        # PR2018-06-10 , value in locked is stored as str: '0'=False, '1'=True
        __initial_locked = 0
        if self.selected_country.locked is not None:
            __initial_locked = int(self.selected_country.locked)
        #logger.debug('CountryEditForm ' + str(self.selected_country) + '__initial_locked: ' + str(__initial_locked) + ' type : ' + str(type(__initial_locked)))
        self.fields['field_locked'] = ChoiceField(
            choices=c.CHOICES_LOCKED,
            label=_('Locked'),
            initial=__initial_locked
        )


class CountryLockForm(ModelForm):
    class Meta:
        model = Country
        fields = ('name', 'locked')


class ExamyearSelectForm(ModelForm):
    class Meta:
        model = Examyear
        fields = ('examyear',)



# === EXAMYEAR =====================================
class ExamyearAddForm(ModelForm):
    # PR1018-05-12
    class Meta:
        model = Examyear
        fields = ('examyear', 'country')
        labels = {'examyear': _('Exam year'), 'country': _('Country')}

    def __init__(self, *args, **kwargs):
        # request is added as parameter in ExamyearAddView by form = ExamyearAddForm(request=request)
        # pop() removes and returns an element from a dictionary, second argument is default when not found
        self.request = kwargs.pop('request', None)
        super(ExamyearAddForm, self).__init__(*args, **kwargs)
        # logger.debug('ExamyearAddForm __init__ request: ' + str(request))

        if self.request.user.country is not None:
    # ======= field 'Examyear' ============
            self.fields['examyear'] = IntegerField(
                label=_('Exam year'),
                min_value=2000,max_value=2099,
                validators=[validate_unique_examyear(self.request.user.country)])

            next_examyear = Examyear.next_examyear(self.request)
            # PR1018-05-12 debug: use self.initial instead of self.fields['examyear'] = IntegerField(min_value=2000,max_value=2099 )
            # from http://avilpage.com/2015/03/django-form-gotchas-dynamic-initial.html
            self.initial['examyear'] = next_examyear
            self.fields['examyear'].disabled = True

    # ======= field 'Country' ============
            # PR2018-08-04 should use self.initial['country'] instead of self.fields['country']
            # see https://avilpage.com/2015/03/django-form-gotchas-dynamic-initial.html
            self.initial['country'] = self.request.user.country.id
            self.fields['country'].disabled = True

        """
# ======= field 'Country_list' ============
                # request.user with role=Insp or role=School: country = request.user.country, field is disabled
                # only request.user with role=System kan choose country
                self.fields['country_list'] = ChoiceField(
                    required=True,
                    # choises must be tuple or list, dictionary gives error: 'int' object is not iterable
                    choices=request.user.country_choices,
                    label=_('Country'),
                    # PR2018-08-04 debug: use request.user.country.id instead of request.user.country, otherwise first country in list shows
                    initial=request.user.country.id
                )
                # PR2018-08-04 should use self.initial['country_list'] instead of self.fields['country_list']
                # see https://avilpage.com/2015/03/django-form-gotchas-dynamic-initial.html
                # self.initial['country_list'] = request.user.country.id
                self.fields['country_list'].disabled = True
        """


class ExamyearEditForm(ModelForm):
    # examyear = IntegerField(min_value=2000,max_value=2099 )
    class Meta:
        model = Examyear
        fields = ('examyear',)

    def __init__(self, *args, **kwargs):
        # request is added as parameter in ExamyearEditView by form = ExamyearAddForm(request=request)
        # pop() removes and returns an element from a dictionary, second argument is default when not found
        self.request = kwargs.pop('request', None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        super(ExamyearEditForm, self).__init__(*args, **kwargs)

        self.selected_examyear = kwargs.get('instance')

    # ======= field 'Examyear' ============
        self.fields['examyear'].disabled = True

    # ======= field 'Published' ============
        # PR2018-08-04 value in Published is stored as str: '0'=False, '1'=True
        __initial_published = 0
        if self.selected_examyear.published is not None:
            __initial_published = int(self.selected_examyear.published)
        #logger.debug('ExamyearEditForm ' + str(self.selected_examyear) + '__initial_published: ' + str(__initial_published) + ' type : ' + str(type(__initial_published)))
        self.fields['field_published'] = ChoiceField(
            choices=c.PUBLISHED_CHOICES,
            label=_('Published'),
            initial=__initial_published)

    # ======= field 'Locked' ============
    # add field locked
        # PR2018-06-10 , value in locked is stored as str: '0'=False, '1'=True
        __initial_locked = 0
        if self.selected_examyear.locked is not None:
            __initial_locked = int(self.selected_examyear.locked)
        #logger.debug('CountryEditForm ' + str(self.selected_country) + '__initial_locked: ' + str(__initial_locked) + ' type : ' + str(type(__initial_locked)))
        self.fields['field_locked'] = ChoiceField(
            choices=c.CHOICES_LOCKED,
            label=_('Locked'),
            initial=__initial_locked)
        # Examyear can only be locked when published
        self.fields['field_locked'].disabled = not __initial_published


# === Department =====================================
class DepartmentAddForm(ModelForm):
    class Meta:
        model = Department
        fields = ('examyear', 'name', 'abbrev', 'sequence', 'level_caption', 'sector_caption')
        labels = {
            'examyear': _('Exam year'),
            'name': _('Name'),
            'abbrev': _('Abbreviation'),
            'sequence': _('Sequence'),
            'level_caption': _('Level name'),
            'sector_caption': _('Sector name')
        }


    # PR2018-06-09 from https://stackoverflow.com/questions/16205908/django-modelform-not-required-field/30403969?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # called by SubjectdefaultAddForm(request=request) in SubjectdefaultAddView.get and -.post
    def __init__(self, *args, **kwargs):
        # request is added as parameter in ExamyearAddView by form = ExamyearAddForm(request=request)
        # pop() removes and returns an element from a dictionary, second argument is default when not foundrequest = kwargs.pop('request', None)  # pop() removes and returns an element from a dictionary, second argument is default when not found
        self.request = kwargs.pop('request', None)
        super(DepartmentAddForm, self).__init__(*args, **kwargs)

        self.this_instance = kwargs.get('instance')

        # ======= field 'examyear' ============
        # PR2018-08-04 should use self.initial['country'] instead of self.fields['country'].initial =  'override'
        # see https://avilpage.com/2015/03/django-form-gotchas-dynamic-initial.html
        self.initial['examyear'] = self.request.user.examyear.id
        self.fields['examyear'].disabled = True

        # ======= field 'name' ============
        self.fields['name'] = CharField(
            validators=[validate_unique_department_name(self.request.user.examyear)])
        self.fields['name'].widget.attrs.update(
            {'autofocus': 'autofocus'})  # , 'placeholder': 'Default subject name'

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            validators=[validate_unique_department_abbrev(self.request.user.examyear)])

        # ======= field 'level_req_field' ============ PR2018-10-20
        # boolean, required, default=True. Value is stored as str: '0'=False, '1'=True
        self.fields['level_req_field'] = ChoiceField(
            choices=c.YES_NO_INT_TUPLE,
            label=_('Leerweg required'),
            initial=1)

        # ======= field 'sector_req_field' ============ PR2018-10-20
        # boolean, required, default=True. Value is stored as str: '0'=False, '1'=True
        self.fields['sector_req_field'] = ChoiceField(
            choices=c.YES_NO_INT_TUPLE,
            label=_('Sector / Profiel required'),
            initial=1)


class DepartmentEditForm(ModelForm):  # PR2018-08-11
    class Meta:
        model = Department
        fields = ('examyear', 'name', 'abbrev', 'sequence', 'level_caption', 'sector_caption')
        labels = {
            'examyear': _('Exam year'),
            'name': _('Name'),
            'abbrev': _('Abbreviation'),
            'sequence': _('Sequence'),
            'level_caption': _('Level name'),
            'sector_caption': _('Sector name')
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request',
                                  None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        super(DepartmentEditForm, self).__init__(*args, **kwargs)

        self.this_instance = kwargs.get('instance')

        # ======= field 'Examyear' ============
        # PR2018-08-04 should use self.initial['country'] instead of self.fields['country'].initial =  'override'
        # see https://avilpage.com/2015/03/django-form-gotchas-dynamic-initial.html
        # self.initial['country'] = self.request.user.country.id
        self.fields['examyear'].disabled = True

        # ======= field 'name' ============
        self.fields['name'] = CharField(
            validators=[validate_unique_department_name(self.request.user.examyear, self.this_instance)])
        self.fields['name'].widget.attrs.update(
            {'autofocus': 'autofocus'})  # , 'placeholder': 'Default subject name'

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            validators=[validate_unique_department_abbrev(self.request.user.examyear, self.this_instance)])

        # ======= field 'level_req_field' ============ PR2018-10-20
        # boolean, required, default=True. Value is stored as str: '0'=False, '1'=True
        self.fields['level_req_field'] = ChoiceField(
            choices=c.YES_NO_INT_TUPLE,
            label=_('Leerweg required')
        )
        # PR2018-08-04 should use self.initial['country'] instead of self.fields['country'].initial =  'override'
        self.initial['level_req_field'] = int(self.this_instance.level_req)

        # ======= field 'sector_req_field' ============ PR2018-10-20
        # boolean, required, default=True. Value is stored as str: '0'=False, '1'=True
        self.fields['sector_req_field'] = ChoiceField(
            choices=c.YES_NO_INT_TUPLE,
            label=_('Sector / Profiel required')
        )
        self.initial['sector_req_field'] = int(self.this_instance.sector_req)


# === School =====================================
class SchoolAddForm(ModelForm):  # PR1018-08-25
    # fields are: examyear = ForeignKey, schooldefault = ForeignKey, is_template = Boolean
    # is_template, name, code, abbrev, article, depbase_list, locked, modified_by, modified_at
    class Meta:
        model = School
        fields = ('name', 'code', 'abbrev', 'article', 'locked')
        labels = {'article': _('Article')}

    def __init__(self, *args, **kwargs):
        # request is added as parameter in ExamyearAddView by form = SchoolAddForm(request=request)
        # pop() removes and returns an element from a dictionary, second argument is default when not found
        self.request = kwargs.pop('request', None)
        super(SchoolAddForm, self).__init__(*args, **kwargs)

        # ======= field 'name' ============
        self.fields['name'] = CharField(
            label=_('Schoolname'),
            validators=[validate_unique_school_field(self.request.user, 'name')])
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'}) # , 'placeholder': 'Default subject name'

        # ======= field 'code' ============
        self.fields['code'] = CharField(
            label=_('Schoolcode'),
            validators=[validate_unique_school_field(self.request.user, 'code')])

        # ======= field 'abbrev' ============
        self.fields['abbrev'] = CharField(
            label=_('Short schoolname'),
            validators=[validate_unique_school_field(self.request.user, 'abbrev')])

        # ======= field 'depbase_list' ============
        # in AddMode: get examyear from request.user
        dep_choices = Department.depbase_list_choices(examyear=self.request.user.examyear)
        self.fields['depbase_list_field'] = MultipleChoiceField(
            required=False,
            widget=SelectMultiple,
            choices=dep_choices,
            label=_('Departments'),
            help_text=_('Select the departments of this school. Press the Ctrl button to select multiple departments.'),
        )

        # ======= field 'Locked' ============
        # add field locked
        # PR2018-06-10 , value in locked is stored as str: '0'=False, '1'=True
        _initial_locked = 0
        # if self.selected_examyear.locked is not None:
        #     _initial_locked = int(self.selected_examyear.locked)
        # logger.debug('CountryEditForm ' + str(self.selected_country) + '__initial_locked: ' + str(__initial_locked) + ' type : ' + str(type(__initial_locked)))
        self.fields['field_locked'] = ChoiceField(
            choices=c.CHOICES_LOCKED,
            label=_('Locked'),
            initial=_initial_locked)

class SchoolEditForm(ModelForm):  # PR2018-08-26
    class Meta:
        model = School
        fields = ('examyear', 'name', 'code', 'abbrev', 'article')
        labels = {
            'examyear': _('Exam year'),
            'code': _('Schoolcode'),
            'name': _('Schoolname'),
            'abbrev': _('Abbreviation')
        }

    # PR2018-06-09 from https://stackoverflow.com/questions/16205908/django-modelform-not-required-field/30403969?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # To get request.user. Do not use kwargs.pop('user', None) due to potential security hole
        super(SchoolEditForm, self).__init__(*args, **kwargs)

        self.this_instance = kwargs.get('instance')

        # ======= field 'examyear' ============
        self.fields['examyear'].disabled = True

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
        # ======= field 'locked' ============
        _initial_locked = 0
        if self.this_instance is not None:
            _initial_locked = int(self.this_instance.locked)
        self.fields['locked_field'] = ChoiceField(
            choices=c.CHOICES_LOCKED,
            label=_('Locked'),
            initial=_initial_locked)


# +++++++++++++++++++++  VALIDATORS  ++++++++++++++++++++++++++++++

# ===  Examyear  =====================================
class validate_unique_examyear(object):  # PR2018-07-25:
    def __init__(self, country):
        self.country = country
        logger.debug('validate_unique_examyear __init__ self.country: ' + str(self.country))

    def __call__(self, value):
        logger.debug('validate_unique_examyear __call__ value: ' + str(value))
        if Examyear.objects.filter(examyear=value, country=self.country).exists():
            logger.debug('validate_unique_examyear ValidationError: Examyear already exists')
            # raise ValidationError({'examyear':[_('Examyear already exists.'),]})
            raise ValidationError(_('Examyear already exists.'))

        return value


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


# PR2018-06-14 was for testing, did not work
#def validate_unique(value, form, field, exclude_initial=True,
#                 format="The %(field)s %(value)s has already been taken."):
#    logger.debug('ValidationError clean_unique field= ' + str(field))
##    if value:
#        qs = form._meta.model._default_manager.filter(**{field: value})
#        if exclude_initial and form.initial:
#            initial_value = form.initial.get(field)
#            qs = qs.exclude(**{field: initial_value})
#        if qs.count() > 0:
#            raise forms.ValidationError(format % {'field': field, 'value': value})
#    return value

