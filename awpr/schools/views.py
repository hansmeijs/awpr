# PR2018-04-14
from django.contrib.auth.decorators import login_required # PR2018-04-01
from django.contrib import messages

from django.core.mail import send_mail
from django.db import connection
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect, Http404

from django.shortcuts import render, redirect #, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView, FormView

from awpr.menus import get_saved_menubutton_url
from schools.models import Country, Country_log, Examyear, Examyear_log, Department, Departmentbase, Department_log, Schoolbase, School, School_log
from schools.forms import CountryFormSet, CountryAddForm, CountryEditForm, ExamyearAddForm, ExamyearEditForm, \
    DepartmentAddForm, DepartmentEditForm, SchoolAddForm, SchoolEditForm

from awpr import functions as f
from awpr import menus

# PR2018-04-27
import logging
logger = logging.getLogger(__name__)



# PR2018-05-06
from django.utils.translation import activate, get_language_info, ugettext_lazy as _


def home(request):
    # PR2018-04-29
    # function get_headerbar_param sets:
    # - activates request.user.language
    # - display/select schoolyear, schoolyear list, color red when not this schoolyear
    # - display/select school, school list
    # - display user dropdown menu
    # note: schoolyear, school and user are only displayed when user.is_authenticated

    # set headerbar parameters PR2018-08-06
    _display_school = False
    _display_dep = False
    if request.user:
        _display_school = True
        _display_dep = True
    _param = f.get_headerbar_param(request, {
        'display_school': _display_school,
        'display_dep': _display_dep
    })
    # logger.debug('home _param: ' + str(_param))

    # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
    return render(request, 'home.html', _param)


def Loggedin(request):
    # redirect to saved_href of last selected menubutton # PR2018-12-25

    saved_href = get_saved_menubutton_url(request)

    if not saved_href:
        saved_href = 'home'

    return HttpResponseRedirect(reverse_lazy(saved_href))
# === COUNTRY =====================================

@method_decorator([login_required], name='dispatch')
class CountyFormsetView(FormView):  # PR2018-11-24
    model = Country
    form_class = Country
    # PR 2018-11-24 without template_name Django looks for <appname>/<model>_list.html, i.e: Student_list.html
    template_name = 'country_formset.html'
    context_object_name = 'Studentsubject'

    def get(self, request, *args, **kwargs):
        return render(request, 'country_formset.html', {'formset': CountryFormSet})

    def post(self, request, *args, **kwargs):
        formset = CountryFormSet(data=request.POST, files=request.FILES)
        #logger.debug('..')

        if formset.is_valid():
            #logger.debug('++')
            #logger.debug('CountyFormsetView post formset.is_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))

            self.instances = formset.save(commit=False)
            for self.instance in self.instances:
                self.instance.save(request=self.request)
                #logger.debug('CountyFormsetView post self.instance: ' + str(self.instance) + ' type: ' + str(type(self.instance)))

            return render(request, 'country_formset.html', {'formset': formset})
        else:
            #logger.debug('--')
            #logger.debug('CountyFormsetView post formset.is_NOT_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))
            #logger.debug('CountryFormSet: ' + str(CountryFormSet) + ' type: ' + str(type(CountryFormSet)))

            return render(request, 'country_formset.html', {'formset': formset})


@method_decorator([login_required], name='dispatch')
class CountryListView(View):
    # only users with role=System can view country

    # PR 2018-04-22 template_name = 'country_list.html' is not necessary, Django looks for <appname>/<model>_list.html
    # context_object_name = 'countries'

    def get(self, request):
        countries = Country.objects.all().order_by(Lower('name'))

        # set headerbar parameters PR2018-08-07
        _params = f.get_headerbar_param(request, { 'countries': countries, 'select_country': True})
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'country_list.html', _params)


@method_decorator([login_required], name='dispatch')
class CountrySelectView(View):
    # PR2018-08-11  only users with role=System can change country
    def get(self, request, pk):
        # TODO go back to 'next' instead of home page
        #_next = request.GET.get('next', 'home')
        # logger.debug('CountrySelectView get _next: ' + str(_next))

        country_selected = None
        if pk is not None:
            country_selected = Country.objects.get_or_none(id=pk)

        if country_selected is not None:
            # ==========  Validation  ===============
            # if examyear exists in country_selected: change examyear.id from user into examyear.id of country_selected
            # if Examyear.examyear does not exist in country_selected: set examyear=None
            if request.user.examyear is not None:
                request_user_examyear_int =  request.user.examyear.examyear
                # logger.debug('CountrySelectView get request_user_examyear_int: ' + str(request_user_examyear_int) + ' type: ' + str(type(request_user_examyear_int)))
                examyear_country_selected = Validate_examyear.get_examyear_in_selected_country(country_selected, request_user_examyear_int)
            else:
                examyear_country_selected =  None
            request.user.country = country_selected
            request.user.examyear = examyear_country_selected
            # reset selected school and department
            request.user.schoolbase = None
            request.user.depbase = None
            request.user.save(self.request)

        return redirect('home')


# PR2018-06-07
@method_decorator([login_required], name='dispatch')
class CountryAddView(View):
    # only users with role=System and permit=Admin can add country

    def get(self, request):
        form = CountryAddForm()

        # set headerbar parameters PR2018-08-07
        _params = f.get_headerbar_param(request, {'form': form})
        # render(request, template_name, context=None (A dictiona
        # ry of values to add to the template context), content_type=None, status=None, using=None)
        return render(request, 'country_add.html', _params)

    def post(self, request):
        form = CountryAddForm(request.POST)
        # logger.debug('CountryAddView post form: ' + str(form))

        if form.is_valid():
            #logger.debug('CountryAddView post after form.is_valid')
            country = form.save(commit=False)
            # logger.debug('CountryAddView post after form.save(commit=False)')

            country.save(request=self.request)
            #logger.debug('CountryAddView post after save')
            return redirect('country_list_url')
        else:
            """If the form is invalid, render the invalid form."""
            _params = f.get_headerbar_param(request, {'form': form})
            return render(request, 'country_add.html', _params)


@method_decorator([login_required], name='dispatch')
class CountryEditView(UpdateView):
    # only users with role=System and permit=Admin can add country

    # PR2018-04-17 debug: Specifying both 'fields' and 'form_class' is not permitted.
    model = Country
    form_class = CountryEditForm
    template_name = 'country_edit.html'
    context_object_name = 'country'

    def form_valid(self, form):
        # PR2018-06-10
        country = form.save(commit=False)
        #logger.debug('CountryEditView form_valid country = ' + str(country))

        # value in field_locked is stored as str: '0'=False, '1'=True
        field_locked = form.cleaned_data.get('field_locked')
        #logger.debug('CountryEditView form_valid field_locked = ' + str(field_locked) + ' type : ' + str(type(field_locked)))

        field_locked_int = int(field_locked)
        #logger.debug('CountryEditView form_valid field_locked_int = ' + str(field_locked_int) + ' type : ' + str(type(field_locked_int)))

        field_locked_bool = bool(field_locked_int)
        #logger.debug('CountryEditView form_valid field_locked_bool = ' + str(field_locked_bool) + ' type : ' + str(type(field_locked_bool)))

        country.locked = field_locked_bool

        country.save(request=self.request)
        return redirect('country_list_url')


@method_decorator([login_required], name='dispatch')
class CountryDeleteView(DeleteView):
    model = Country
    template_name = 'country_delete.html'  # without template_name Django searches for country_confirm_delete.html
    success_url = reverse_lazy('country_list_url')

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()
       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')


@method_decorator([login_required], name='dispatch')
class CountryLogView(View):
    # PR 2018-04-22 template_name is not necessary, Django looks for <appname>/<model>_list.html
    # template_name = 'country_list.html'
    # context_object_name = 'countries'
    # paginate_by = 10  After this /country_list/?page=1 will return first 10 countries.

    def get(self, request, pk):

        countries_log = Country_log.objects.filter(country_id=pk).order_by('-modified_at')
        country = Country.objects.get(id=pk)

        param = {'display_school': True}
        headerbar_param = f.get_headerbar_param(request, param)
        headerbar_param['countries_log'] = countries_log
        headerbar_param['country'] = country
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.

        return render(request, 'country_log.html', headerbar_param)


# PR 2018-06-16 Not in use
@method_decorator([login_required], name='dispatch')
class CountryLogDeletedView(View):
    # PR 2018-04-22 template_name is not necessary, Django looks for <appname>/<model>_list.html
    # template_name = 'country_list.html'
    # context_object_name = 'countries'
    # paginate_by = 10  After this /country_list/?page=1 will return first 10 countries.

    def get(self, request):
        inner_qs = Country.objects.all()
        countries_log = Country_log.objects.exclude(country_id=inner_qs).order_by('-modified_at')

        with connection.cursor() as cursor:
            sql = "SELECT * FROM schools_country_log WHERE country_id NOT IN (SELECT id FROM schools_country);"
            cursor.execute(sql)
            rows = cursor.fetchall()


        param = {'display_school': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        headerbar_param['countries_log'] = countries_log
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'country_log_deleted.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class CountryLockView(View):
    # PR2018-08-19 template_name is not necessary, Django looks for <appname>/<model>_list.html
    template_name = 'country_lock.html'

    def get(self, request, pk):

        # countries = Country.objects.all().order_by(Lower('name'))
        # country = Country.objects.filter(id=pk).first()
        # _params = f.get_headerbar_param(request, {'country': country, 'select_country': True})
        _params = f.get_headerbar_param(request,{})
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'country_lock.html', _params)


    def post(self, request, pk):
        if pk is not None:
            country = Country.objects.get_or_none(id=pk)
        else:
            country = None

        if country is not None:
            country.locked = not country.locked
            country.save(request=self.request)

        countries = Country.objects.all().order_by(Lower('name'))
        _params = f.get_headerbar_param(request, {'countries': countries, 'select_country': True})
        return render(request, 'country_list.html', _params)


# === EXAMYEAR =====================================
@method_decorator([login_required], name='dispatch')
class ExamyearListView(View):
    # PR2018-08-06 PR2018-05-10 PR2018-03-02

    def get(self, request):
        _params = f.get_headerbar_param(request, {'display_user': True})

        # PR2018-05-14 objects.order_by('-examyear').all() not necessary, because I added to model: class Meta: ordering = ['-examyear',]
        # filter examyears of request.user.country
        if request.user.country is not None:
            examyears = Examyear.objects.filter(country=request.user.country)
            # add examyears to headerbar parameters PR2018-08-12
            _params.update({'examyears': examyears})

        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'examyear_list.html', _params)


# PR2018-05-14
@method_decorator([login_required], name='dispatch')
class ExamyearSelectView(View):

    def get(self, request, pk):
        # logger.debug('ExamyearSelectView get: ' + str(request) + ' pk: ' + str(pk))
        if pk is not None:
            # PR2018-05-18 getting examyear from object not necessary, but let it stay for safety
            try:
                exyear = Examyear.objects.get(id=pk)
                request.user.examyear = exyear
                request.user.save(self.request)
                # logger.debug('ExamyearSelectView exyear saved: ' + str(request.user.examyear.id))

            finally:
                return redirect('home')
        return redirect('home')


# PR2018-05-10 PR2018-04-16
@method_decorator([login_required], name='dispatch')
class ExamyearAddView(CreateView):
    # the following lines are not necessary:
    # model = Examyear
    # form_class = ExamyearAddForm
    # template_name = 'examyear_add.html' # without template_name Django searches for user_form.html
    # pk_url_kwarg = 'pk'
    # context_object_name = 'ExamyearAddForm' # "context_object_name" changes the original parameter name "object_list"

    def get(self, request, *args, **kwargs):
        # logger.debug('ExamyearAddView get request: ' + str(request))
        # permission:   user.is_authenticated AND user.is_role_insp_or_system
        form = ExamyearAddForm(request=request)

        # set headerbar parameters PR 2018-08-06
        _param = f.get_headerbar_param(request, {
            'form': form,
            'display_school': True,
            'override_school': request.user.role_str})
        # logger.debug('ExamyearAddView def get headerbar_param: ' + str(headerbar_param))

        # render(request, template_name, context=None (A dictionary of values to add to the template context), content_type=None, status=None, using=None)
        return render(request, 'examyear_add.html', _param)

    def post(self, request, *args, **kwargs):
        self.request = request
        #logger.debug('ExamyearAddView post self.request: ' + str(self.request))

        form = ExamyearAddForm(self.request.POST, request=self.request) # this one doesn't work: form = ExamyearAddForm(request=request)

        if form.is_valid():
            #logger.debug('ExamyearAddView post is_valid form.data: ' + str(form.data))

            # save examyear without commit
            self.new_examyear = form.save(commit=False)

            # ======  save field 'Country'  ============
            # initial value of 'country' is set in ExamyearAddForm: self.initial['country'] = request.user.country.id

            self.new_examyear.published = False
            self.new_examyear.locked = False

            self.new_examyear.modified_by = self.request.user
            # PR2018-06-07 datetime.now() is timezone naive, whereas timezone.now() is timezone aware, based on the USE_TZ setting
            self.new_examyear.modified_at = timezone.now()

            # PR2018-08-04 debug: don't forget argument (request), otherwise gives error 'tuple index out of range' at request = args[0]
            self.new_examyear.save(request=self.request)
            self.new_examyear_id = self.new_examyear.id
            self.modified_at = timezone.now()

            # get previous examyear
            self.prev_examyear_int = int(self.new_examyear.examyear) - 1
            self.prev_examyear = Examyear.objects.filter(country=self.new_examyear.country, examyear=self.prev_examyear_int).first()

            # copy departments from previous prev_examyear if it exists
            if self.prev_examyear is not None:
                if self.request.user.is_role_insp_or_system_and_perm_admin:
                    self.prev_examyear_id = self.prev_examyear.id

                    cursor = connection.cursor()

            # copy departments from previous year
                    cursor.execute(
                        'INSERT INTO schools_department (base_id, examyear_id, name, abbrev, sequence, modified_by_id, modified_at) ' + \
                        'SELECT dep.base_id, %s AS examyear_id, dep.name, dep.abbrev, dep.sequence, %s AS modified_by_id, %s AS modified_at ' + \
                        'FROM schools_department as dep WHERE dep.examyear_id = %s;',
                        [self.new_examyear.id, self.new_examyear.modified_by_id, self.modified_at, self.prev_examyear_id])
                    connection.commit()
                # copy new departments to department_log
                    cursor.execute(
                        'INSERT INTO schools_department_log (department_id, base_id, examyear_id, name, abbrev, sequence, mode, modified_by_id, modified_at) ' + \
                        'SELECT dep.id, dep.base_id, %s AS examyear_id, dep.name, dep.abbrev, dep.sequence, %s AS mode, %s AS modified_by_id, %s AS modified_at ' + \
                        'FROM schools_department as dep WHERE dep.examyear_id = %s;',
                        [self.new_examyear.id, 'c', self.new_examyear.modified_by_id, self.modified_at, self.new_examyear_id])
                    connection.commit()

            # copy levels from previous examyear to new examyear
                    cursor.execute(
                        'INSERT INTO subjects_level (base_id, examyear_id, name, abbrev, sequence, depbase_list, modified_by_id, modified_at) ' + \
                        'SELECT lvl.base_id, %s AS examyear_id, lvl.name, lvl.abbrev, lvl.sequence, lvl.depbase_list, %s AS modified_by_id, %s AS modified_at ' + \
                        'FROM subjects_level as lvl WHERE lvl.examyear_id = %s;',
                        [self.new_examyear.id, self.new_examyear.modified_by_id, self.modified_at, self.prev_examyear_id])
                    connection.commit()
                # copy levels from new_examyear to level_log
                    cursor.execute(
                        'INSERT INTO subjects_level_log (level_id, base_id, examyear_id, name, abbrev, sequence, depbase_list, mode, modified_by_id, modified_at) ' + \
                        'SELECT lvl.id, lvl.base_id, %s AS examyear_id, lvl.name, lvl.abbrev, lvl.sequence, %s AS mode, %s AS modified_by_id, %s AS modified_at ' + \
                        'FROM subjects_level as lvl WHERE lvl.examyear_id = %s;',
                        [self.new_examyear.id, 'c', self.new_examyear.modified_by_id, self.modified_at, self.new_examyear_id])
                    connection.commit()

            # copy sectors from previous examyear to new examyear
                    cursor.execute(
                        'INSERT INTO subjects_sector (base_id, examyear_id, name, abbrev, sequence, depbase_list, modified_by_id, modified_at) ' + \
                        'SELECT sct.base_id, %s AS examyear_id, sct.name, sct.abbrev, sct.sequence, sct.depbase_list, %s AS modified_by_id, %s AS modified_at ' + \
                        'FROM subjects_sector as sct WHERE sct.examyear_id = %s;',
                        [self.new_examyear.id, self.new_examyear.modified_by_id, self.modified_at, self.prev_examyear_id])
                    connection.commit()

                    # copy sectors from new_examyear to sector_log
                    cursor.execute(
                        'INSERT INTO subjects_sector_log (sector_id, base_id, examyear_id, name, abbrev, sequence, depbase_list, mode, modified_by_id, modified_at) ' + \
                        'SELECT sct.id, sct.base_id, %s AS examyear_id, sct.name, sct.abbrev, sct.sequence, %s AS mode, %s AS modified_by_id, %s AS modified_at ' + \
                        'FROM subjects_sector as sct WHERE sct.examyear_id = %s;',
                        [self.new_examyear.id, 'c', self.new_examyear.modified_by_id, self.modified_at, self.new_examyear_id])
                    connection.commit()

            # copy schemes from previous examyear to new examyear
                    # isrt get dep_id, level_id and sector of this examyear
                    cursor.execute(
                        'INSERT INTO Scheme(department_id, level_id, sector_id, name, modified_by_id, modified_at) ' +
                        'SELECT sch.department_id, sch.level_id, sch.sector_id, sch.name, %s AS modified_by_id, %s AS modified_at ' +
                        'FROM Department AS dep INNER JOIN Scheme AS sch ON dep.department_id = sch.department_id ' +
                        'WHERE dep.examyear_id = %s;',
                        [self.new_examyear.id, self.new_examyear.modified_by_id, self.modified_at,
                         self.prev_examyear_id])
                    connection.commit()
                    # copy sectors from new_examyear to sector_log
                    cursor.execute(
                        'INSERT INTO subjects_scheme_log (level_id, base_id, examyear_id, name, abbrev, sequence, depbase_list, mode, modified_by_id, modified_at) ' + \
                        'SELECT sch.id, sch.base_id, %s AS examyear_id, sch.name, sch.abbrev, sch.sequence, %s AS mode, %s AS modified_by_id, %s AS modified_at ' + \
                        'FROM subjects_scheme as sch WHERE sch.examyear_id = %s;',
                        [self.new_examyear.id, 'c', self.new_examyear.modified_by_id, self.modified_at,
                         self.new_examyear_id])
                    connection.commit()


            #elif self.request.user.is_role_school_perm_admin:

            # TODO: let schools copy their own school to the new examyear
            # TODO: schools can only be added when new examyear is published > filter in form new_examyear
            # add info from previous examyear:
            #  - inpection / system:
                    # adds dep, level, sector, scheme, subjects,
                    # from is_template school: scheme_items, packages
                    # examyear not yet published
            # school: only after examyear is pubvlished:
                    # from own school: school, scheme_items, package_items
                    # students from last year

            # ======  Add schools from previous examyear from this country to table school with new examyear  ============

                """
            # if previous examyear exists: copy schools
            if self.prev_examyear:
            self.prev_examyear_id = self.prev_examyear.id
            self.new_examyear_id = self.new_examyear.id
            self.country_id = self.new_examyear.country_id
            self.modified_by_id = self.new_examyear.modified_by_id
            self.modified_at = timezone.now()
            cursor = connection.cursor()
            cursor.execute(
                'INSERT INTO schools_school (examyear_id, schoolbase_id, name, code, abbrev, article, dep_list, locked, modified_by_id, modified_at) ' + \
                'SELECT %s AS examyear_id, sb.id, sb.name, sb.code, sb.abbrev, sb.article, sb.dep_list, False AS locked, %s AS modified_by_id, %s AS modified_at  ' + \
                'FROM schools_school AS sb WHERE sb.examyear_id = %s;',
                [self.new_examyear_id, self.modified_by_id, self.modified_at, self.prev_examyear_id])
            connection.commit()


            #PR2018-08-08 This took way too long:
            subjectdefaults = Subjectdefault.objects.filter(country=examyear.country)

            for subjectdefault in subjectdefaults:
                subject_new = Subject(
                    examyear_id=examyear.id,
                    subjectdefault_id=subjectdefault.id,
                    name=subjectdefault.name,
                    abbrev=subjectdefault.abbrev,
                    sequence=subjectdefault.sequence,
                    dep_list=subjectdefault.dep_list,
                    modified_by=examyear.modified_by,
                    modified_at=examyear.modified_at
                )
                subject_new.save(self.request)

            # ======  Add active subjectdefault from this country to table subject with new examyear  ============
            _examyear_id = examyear.id
            _country_id = examyear.country_id
            _modified_by_id = examyear.modified_by_id
            _modified_at = timezone.now()
            cursor = connection.cursor()
            cursor.execute(
                'INSERT INTO subjects_subject (examyear_id, subjectdefault_id, name, abbrev, sequence, dep_list, is_active, modified_by_id, modified_at) ' + \
                'SELECT %s AS examyear_id, sd.id, sd.name, sd.abbrev, sd.sequence, sd.dep_list, sd.is_active, %s AS modified_by_id, %s AS modified_at ' + \
                'FROM subjects_subjectdefault AS sd WHERE sd.is_active = True AND sd.country_id = %s;',
                [_examyear_id, _modified_by_id, _modified_at, _country_id]
            )
            connection.commit()
            """

            return redirect('examyear_list_url')
        else:
            """If the form is invalid, render the invalid form."""
            return render(self.request, 'examyear_add.html', {'form': form})


@method_decorator([login_required], name='dispatch')
class ExamyearEditView(UpdateView):
    # PR2018-04-17 debug: Specifying both 'fields' and 'form_class' is not permitted.
    model = Examyear
    form_class = ExamyearEditForm
    template_name = 'examyear_edit.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'examyear'

    def form_valid(self, form):
        examyear = form.save(commit=False)

    # ======= field 'Published' ============
        # value in Published is stored as str: '0'=False, '1'=True
        _field_published = form.cleaned_data.get('field_published')
        examyear.published = bool(int(_field_published))

    # ======= field 'Locked' ============
        # value in Locked is stored as str: '0'=False, '1'=True
        _field_locked = form.cleaned_data.get('field_locked')
        examyear.locked = bool(int(_field_locked))

        # PR2018-08-04 debug: don't forget argument (self.request), otherwise gives error 'tuple index out of range' at request = args[0]
        examyear.save(request=self.request)

        return redirect('examyear_list_url')


@method_decorator([login_required], name='dispatch')
class ExamyearDeleteView(DeleteView):
    model = Examyear
    template_name = 'examyear_delete.html'  # without template_name Django searches for examyear_confirm_delete.html
    success_url = reverse_lazy('examyear_list_url')

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()
       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')


@method_decorator([login_required], name='dispatch')
class ExamyearLogView(View):

    def get(self, request, pk):
        # permits: user.is_authenticated  and user.is_role_insp_or_system_and_perm_admin
        examyears_log = Examyear_log.objects.filter(examyear_id=pk).order_by('-modified_at')
        examyear = Examyear.objects.get(id=pk)

        #logger.debug('ExamyearLogView ' + str(examyears_log))
        #logger.debug('examyear ' + str(examyear))

        param = {'display_school': True}
        headerbar_param = f.get_headerbar_param(request, param)
        headerbar_param['examyears_log'] = examyears_log
        headerbar_param['examyear'] = examyear
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'examyear_log.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class ExamyearLockView(View):
    template_name = 'Examyear_lock.html'

    #def get(self, request, pk):
    #    examyear = Examyear.objects.filter(id=pk).first()
    #    _params = f.get_headerbar_param(request, {'examyear': examyear})
    #    return render(request, 'examyear_lock.html', _params)

    def post(self, request, pk):
        examyear = Examyear.objects.get_or_none(id=pk)
        if examyear is not None:
            examyear.locked = not examyear.locked
            examyear.save(request=self.request)
        return redirect('examyear_list_url')

# === Department =====================================
@method_decorator([login_required], name='dispatch')
class DepartmentListView(View): # PR2018-08-11

    def get(self, request):
        # filter Department of request.user.examyear
        # logger.debug('DepartmentListView request.user.examyear: ' + str(request.user.examyear))
        _params = f.get_headerbar_param(request, {'select_country': True})
        if request.user.examyear is not None:
            # filter Departments of request.user.examyear. Country is parent of Examyear
            departments = Department.objects.filter(examyear=request.user.examyear)
            # add departments to headerbar parameters PR2018-09-02
            _params.update({'departments': departments})
        return render(request, 'department_list.html', _params)


@method_decorator([login_required], name='dispatch')
class DepartmentSelectView(View):  # PR2018-08-24 PR2018-11-23
    def get(self, request, pk):
        #logger.debug('=== DepartmentSelectView ============================')
        #logger.debug('request.user: ' + str(request.user) + ' Type: ' + str(type(request.user)))
        #logger.debug('pk: ' + str(pk) + ' Type: ' + str(type(pk)))

        if pk is not None:
            # PR2018-05-18 getting school from object not necessary, but let it stay for safety
            try:
                department = Department.objects.get(id=pk)
                #logger.debug('department: ' + str(department) + ' Type: ' + str(type(department)))

                request.user.depbase = department.base
                #logger.debug('request.user.depbase: ' + str(request.user.depbase) + ' Type: ' + str(type(request.user.depbase)))

                request.user.save(request=self.request)  # PR 2018-11-23 debug: was: request.user.save(self.request)  PR 2018-08-04 debug: was: request.user.save()

                #logger.debug('department saved: ' + str(request.user.department.id))
            finally:
                return redirect('home')
        return redirect('home')


@method_decorator([login_required], name='dispatch')
class DepartmentAddView(CreateView):
    # PR2018-08-11
    def get(self, request, *args, **kwargs):
        # logger.debug('DepartmentAddView get request.user: ' + str(request.user) + '> Type: ' + str(type(request.user)))
        form = DepartmentAddForm(request=request)

        _params = f.get_headerbar_param(request, {'form': form, 'display_school': True})
        return render(request, 'department_add.html', _params)

    def post(self, request, *args, **kwargs):
        form = DepartmentAddForm(request.POST, request=request)

        if form.is_valid():
            department = form.save(commit=False)

            # ======  save field 'level_req_field'  ============
            level_req_field = form.cleaned_data.get('level_req_field')
            department.level_req = bool(int(level_req_field))

            # ======  save field 'sector_req_field'  ============
            sector_req_field = form.cleaned_data.get('sector_req_field')
            department.sector_req = bool(int(sector_req_field))

            department.save(request=self.request)

            return redirect('department_list_url')
        else:
            _params = f.get_headerbar_param(request, {'form': form, 'display_school': True})
            return render(request, 'department_add.html', _params)


@method_decorator([login_required], name='dispatch')
class DepartmentEditView(UpdateView):  # PR2018-08-11
    model = Department
    form_class = DepartmentEditForm
    template_name = 'department_edit.html'
    context_object_name = 'department'
    # TODO: init value of levelreq / sectorreq not working PR2018-10-26
    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        kwargs = super(DepartmentEditView, self).get_form_kwargs()
        # add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})
        return kwargs

    def form_valid(self, form):
        department = form.save(commit=False)

    # ======  save field 'level_req_field'  ============
        level_req_str = form.cleaned_data.get('level_req_field')
        level_req_bool = bool(int(level_req_str))
        department.level_req = level_req_bool

    # ======  save field 'sector_req_field'  ============
        sector_req_str = form.cleaned_data.get('sector_req_field')
        sector_req_bool = bool(int(sector_req_str))
        department.sector_req = sector_req_bool

        logger.debug('DepartmentEditView department.id: ' + str(department.id) + '> type: ' + str(type(department.id)))
        logger.debug('DepartmentEditView department.level_req: ' + str(department.level_req) + '> type: ' + str(type(department.level_req)))
        logger.debug('DepartmentEditView department.sector_req: ' + str(department.sector_req) + '> type: ' + str(type(department.sector_req)))
        logger.debug('DepartmentEditView department.abbrev: <' + str(department.abbrev) + '> type: ' + str(type(department.abbrev)))

        department.save(request=self.request)

        return redirect('department_list_url')


@method_decorator([login_required], name='dispatch')
class DepartmentDeleteView(DeleteView):
    model = Department
    template_name = 'department_delete.html'  # without template_name Django searches for subjectdefault_confirm_delete.html
    success_url = reverse_lazy('department_list_url')

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()
       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')


@method_decorator([login_required], name='dispatch')
class DepartmentLogView(View):
    def get(self, request, pk):
        department_log = Department_log.objects.filter(department_id=pk).order_by('-modified_at')
        department = Department.objects.get(id=pk)
        _param = {
            'department_log': department_log,
            'department': department,
            'display_school': True,
            'override_school': request.user.role_str}
        _headerbar_param = f.get_headerbar_param(request, _param)
        return render(request, 'department_log.html', _headerbar_param)


#@method_decorator([login_required], name='dispatch')
#class CountriesListView(ListView):
#    model = Country
    #paginate_by = 10  # if pagination is desired

#    def get_context_data(self, **kwargs):
#        context = super().get_context_data(**kwargs)
#        # context['now'] = timezone.now()
#        return context


# === School =====================================
@method_decorator([login_required], name='dispatch')
class SchoolListView(ListView):  # PR2018-08-25

    def get(self, request, *args, **kwargs):
        # school-user can only view his own school
        # insp-users can only view schools from his country
        # system-users can only view school from request_user,country
        schools = None  # User.objects.filter(False) gives error: 'bool' object is not iterable
        menu_items = []
        if request.user:
            if request.user.examyear:
                if request.user.is_role_insp_or_system:
                    # examyear has field country, therefore filter country is not necessary
                    schools = School.objects.filter(examyear=request.user.examyear)
                else:
                    schools = School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear)

        # set headerbar parameters
        _params = f.get_headerbar_param(request, {
            'schools': schools
        })
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'school_list.html', _params)



@method_decorator([login_required], name='dispatch')
class SchoolSelectView(View):  # PR2018-08-04 PR2018-11-21

    def get(self, request, pk):
        # PR2018-11-22 request is needed as argument, don't ask me why
        #logger.debug('===SchoolSelectView============================')
        #logger.debug('pk: ' + str(pk) + ' Type: ' + str(type(pk)))
        #logger.debug('request.user: ' + str(request.user) + ' Type: ' + str(type(request.user)))

        if request.user is not None:
            if request.user.country is not None and request.user.examyear is not None:
                if request.user.country == request.user.examyear.country:
                    if pk is not None:
                # get selected school
                        schoolbase = Schoolbase.objects.filter(id=pk).first()
                        if schoolbase is not None:
                            request.user.schoolbase = schoolbase
                            request.user.save(request=request)  # PR 2018-08-04 debug: was: request.user.save()

        return redirect('home')


@method_decorator([login_required], name='dispatch')
class SchoolAddView(CreateView):  # PR2018-08-25 PR2018-11-11

    def get(self, request, *args, **kwargs):
        form = SchoolAddForm(request=request)
        _param = f.get_headerbar_param(request, {
            'form': form,
            'display_school': True
        })
        return render(request, 'school_add.html', _param)

    def post(self, request, *args, **kwargs):
        form = SchoolAddForm(request.POST, request=request) # this one doesn't work: form = SchoolAddForm(request=request)

        if form.is_valid():
            school = form.save(commit=False)

            # ======  set value 'examyear'  ============
            school.examyear = request.user.examyear

            # ======  save field 'depbase_list_field'  ============
            _clean_depbase_list_field = form.cleaned_data.get('depbase_list_field')  # Type: <class 'list'>
            school.depbase_list = f.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)

            school.save(request=self.request)

            return redirect('school_list_url')
        else:
            # If the form is invalid, render the invalid form.
            _param = f.get_headerbar_param(request, {
                'form': form,
                'display_school': True
            })
            return render(request, 'school_add.html', _param)


@method_decorator([login_required], name='dispatch')
class SchoolEditView(UpdateView):
    model = School
    form_class = SchoolEditForm
    template_name = 'school_edit.html'
    context_object_name = 'school'

    # PR2018-11-03 from: https://python-programming.com/django/permission-checking-django-views/
    # UserPassesTestMixin uses test_func to check permissions
    def test_func(self):
        is_ok = False
        school_id = self.kwargs['pk']
        if school_id is not None:
            school = School.objects.filter(id=school_id).first()
            if school.examyear is not None:
                is_ok = self.request.user.examyear_correct(school.examyear.id)
        return is_ok

    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        kwargs = super(SchoolEditView, self).get_form_kwargs()
        # add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})
        return kwargs

    def form_valid(self, form):
        school = form.save(commit=False)

        # ======  save field 'depbase_list_field'  ============
        _clean_depbase_list_field = form.cleaned_data.get('depbase_list_field')  # Type: <class 'list'>
        school.depbase_list = f.get_depbase_list_field_sorted_zerostripped(_clean_depbase_list_field)

        # ======  save field 'locked_field'  ============
        locked_str = form.cleaned_data.get('locked_field')
        locked_bool = bool(int(locked_str))
        school.locked = locked_bool

        school.save(request=self.request)
        return redirect('school_list_url')


@method_decorator([login_required], name='dispatch')
class SchoolDeleteView(DeleteView):
    # PR2018-04-20
    model = School
    template_name = 'school_delete.html'  # without template_name Django searches for level_confirm_delete.html
    success_url = reverse_lazy('school_list_url')

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()
       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')

@method_decorator([login_required], name='dispatch')
class SchoolLogView(View):
    # PR 2018-04-22 template_name is not necessary, Django looks for <appname>/<model>_list.html
    # template_name = 'country_list.html'
    # context_object_name = 'countries'
    # paginate_by = 10  After this /country_list/?page=1 will return first 10 countries.

    def get(self, request, pk):
        school_log = School_log.objects.filter(school_id=pk).order_by('-modified_at')
        school = School.objects.get(id=pk)

        param = {'display_school': True, 'select_examyear': True,'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        headerbar_param['school_log'] = school_log
        headerbar_param['school'] = school
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'school_log.html', headerbar_param)


# ++++++++++++++++++   VALIDATORS     ++++++++++++++++++++++++++++++++++++++

class Validate_examyear(object):

    @staticmethod  # PR2018-08-14
    def examyear_does_not_exist_in_country(user_country, new_examyear_int):
        # This validation is used when user wants to add a new examyear (only systenm and insp users can add new examyear)
        # It checks if new examyear exists in user.country. Name of examyear is Int type.
        # returns True if examyear.examyear does not exist in user.country, otherwise False
        _does_not_exist = True
        if user_country is not None:
            if new_examyear_int is not None:
                if not Examyear.objects.filter(country=user_country, examyear=new_examyear_int).exists():
                    _does_not_exist = True
        return _does_not_exist

    @staticmethod  # PR2018-08-14
    def get_examyear_in_selected_country(country_selected, user_examyear_int):
        # This validation is used when user wants to change user.country (only systenm users can change user.country)
        # It checks if user.examyear exists in selected_country. Returns examyear in selected_country if it exists, otherwise None
        # If it exists: selected_country is OK, if not: delete user.examyear
        if country_selected is None:
            # if country is None: selected_country NOT OK, exit code is outside this function
            _examyear_country_selected = None
        else:
            if user_examyear_int is None:
                # if examyear is None: selected_country OK (examyear is None, no need to delete)
                _examyear_country_selected = None
            else:
                if Examyear.objects.filter(examyear=user_examyear_int, country=country_selected).exists():
                    # examyear exists in selected_country: selected_country OK
                    _examyear_country_selected = Examyear.objects.filter(examyear=user_examyear_int, country=country_selected).get()
                    #logger.debug('get_examyear_in_selected_country _examyear_country_selected: ' + str(_examyear_country_selected) + ' type: ' + str(type(_examyear_country_selected)))
                else:
                    # examyear does not exist in country: select country NOT OK: delete user.examyear
                    _examyear_country_selected = None
        return _examyear_country_selected


    def examyear_exists_in_this_country(cls, country, examyear):
        # PR2018-08-13
        # This validation is used when user wants to add a new examyear (only systenm and insp users can add new examyear)
        # It checks if new examyear exists in user.country.
        # If it exists: new examyear cannot be added, if not: OK

        # except_for_this_examyear not necessray because examyear cannot be changed

        if country is None:
            # if country is None: new examyear cannot be added
            _isOK = False
        else:
            if examyear is None:
                # if examyear is None: new examyear cannot be added
                _isOK = False
            else:
                if Examyear.objects.filter(examyear=examyear, country=country).exists():
                    # examyear exists in country: new examyear cannot be added
                    _isOK = False
                else:
                    # examyear does not exist in country: add examyear OK, new examyear can be added
                    _isOK = True
        return _isOK



"""

from tablib import Dataset
def import_view(request):
    if request.method == 'POST':
        person_resource = SchoolcodeResource()
        dataset = Dataset()
        new_persons = request.FILES['myfile']

        imported_data = dataset.load(new_persons.read())
        result = person_resource.import_data(dataset, dry_run=True)  # Test the data import

        if not result.has_errors():
            person_resource.import_data(dataset, dry_run=False)  # Actually import now

    return render(request, 'core/simple_upload.html')


def home(request):
# PR2018-03-02
#was: return HttpResponse('Welcome to the AWP forum')
#was:    boards = Board.objects.all()
    #boards_names = list()
    # for board in boards:
    #    boards_names.append(board.name)
    ## '<br>' is the separator (i.e. linebreak), .join(list) joins the elements of the list, divided by the separator
    #response_html = '<br>'.join(boards_names)
    #return HttpResponse(response_html)

    boards = Board.objects.all()
    return render(request, 'home.html', {'boards': boards})


@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    fields = ('message', )
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()
        return redirect('topic_posts', pk=post.topic.board.pk, topic_pk=post.topic.pk)



# PR2018-04-16
@login_required
def examyear_edit_view(request, pk):
    year = get_object_or_404(Examyear, pk=pk)
    if request.method == 'POST':
        form = Examyear_edit_form(request.POST)
        if form.is_valid():
            return redirect('schools/examyear_edit', pk=pk)
    else:
        form = Examyear_edit_form()
    return render(request, 'examyear_edit.html', {'year': year, 'form': form})

# PR2018-03-08
def board_topics(request, pk):
    try:
        board = Board.objects.get(pk=pk)
    except Board.DoesNotExist:
        raise Http404
    return render(request, 'topics.html', {'board': board})


@login_required # PR2018-04-01
def new_topic(request, pk): # PR2018-03-11
    board = get_object_or_404(Board, pk=pk)
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            topic.starter = request.user  # PR2018-04-01
            topic.save()
            post = Post.objects.create(
                message=form.cleaned_data.get('message'),
                topic=topic,
                created_by=request.user  # PR2018-04-01
            )
            return redirect('board_topics', pk=board.pk)  # TODO: redirect to the created topic page
    else:
        form = NewTopicForm()
    return render(request, 'new_topic.html', {'board': board, 'form': form})

"""