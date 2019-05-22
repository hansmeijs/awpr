# PR2018-09-02
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView, View
import re # PR2018-12-05
import datetime # PR2018-12-05
import json # PR2018-12-03

from schools.models import Department, School, Schoolsetting
from subjects.models import Level, Sector, Subject, Scheme, Schemeitem
from students.models import Student, Student_log, Result, Result_log, Studentsubject, Grade, Grade_log, Birthcountry, Birthcity
from students.forms import StudentAddForm, StudentEditForm, ResultEditForm, StudentsubjectFormset, \
    StudentsubjectAddForm, StudentsubjectEditForm, GradeAddForm, GradeEditForm

from awpr import functions as f
from awpr import constants as c
from students import validations as v


# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder
class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


# ========  Student  =====================================

@method_decorator([login_required], name='dispatch')
class StudentListView(ListView):  # PR2018-09-02

    def get(self, request, *args, **kwargs):
        _params = f.get_headerbar_param(request, {
            'display_school': True,
            'display_dep': True,
            'display_user': True
        })
        # get school from user.examyear and user.schoolbase PR2018-09-03
        if request.user.examyear and request.user.schoolbase:
            # logger.debug('StudentListView get request.user.examyear = ' + str(request.user.examyear) + ' type : ' + str(type(request.user.examyear)))
            # logger.debug('StudentListView get request.user.schoolbase = ' + str(request.user.schoolbase) + ' type : ' + str(type(request.user.schoolbase)))

            school= School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
            if school:
                # logger.debug('StudentListView get school = ' + str(school) + ' type : ' + str(type(school)))

                if request.user.depbase:
                    # logger.debug('StudentListView get request.user.department = ' + str(request.user.department) + ' type : ' + str(type(request.user.department)))
                    # TODO testing
                    department= Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()
                    # logger.debug('StudentListView get department = ' + str(department) + ' type : ' + str(type(department)))
                    # filter students of this school and this department
                    students = Student.objects.filter(school=school, department=department)
                    # logger.debug('StudentListView get students = ' + str(students) + ' type : ' + str(type(students)))
                    _params.update({'school': school})
                    _params.update({'students': students})
        return render(request, 'student_list.html', _params)


@method_decorator([login_required], name='dispatch')
class StudentAddView(CreateView): # PR2018-09-03

    def get(self, request, *args, **kwargs):
        # permission: user.is_authenticated AND user.is_role_insp_or_system
        form = StudentAddForm(request=request)
        _param = f.get_headerbar_param(request, {
            'form': form,
            'display_school': True,
            'display_dep': True})
        return render(request, 'student_add.html', _param)

    def post(self, request, *args, **kwargs):
        form = StudentAddForm(request.POST, request=request) # this one doesn't work: form = Subjectdefault(request=request)
        #logger.debug('StudentAddView post request.POST: ' + str(self.request.POST) + ' type: ' + str(type(self.request.POST)))

        if form.is_valid():
            student = form.save(commit=False)

            # ======  save field 'school'  ============
            _school = form.cleaned_data.get('school')
            student.school = _school
            # logger.debug('StudentAddView form.is_valid _school: ' + str(_school) + ' Type: ' + str(type(_school)))

            # ======  save field 'department'  ============
            _department = form.cleaned_data.get('department')
            student.department = _department
            # logger.debug('StudentAddView form.is_valid _department: ' + str(_department) + ' Type: ' + str(type(_department)))

            # ======  save field 'birthcountry_field'  ============
            _birthcountry_id_str = form.cleaned_data.get('birthcountry_field')  # Value: '18' Type: <class 'str'>
            _birthcountry_id_int = int(_birthcountry_id_str)
            try:
                _birthcountry = Birthcountry.objects.get(id=_birthcountry_id_int)
                # logger.debug('StudentAddView form.is_valid _clean_birthcountry: ' + str(_birthcountry) + ' Type: ' + str(type(_birthcountry)))
                student.birthcountry = _birthcountry
                # logger.debug('StudentAddView form.is_valid _clean_birthcountry: ' + str(_birthcountry) + ' Type: ' + str(type(_birthcountry)))

            except:
                pass

            # ======  save field 'birthcity_field'  ============
            #_birthcity_id_str = form.cleaned_data.get('birthcity_field')  # Value: '18' Type: <class 'str'>
            #logger.debug('StudentAddView form.is_valid _birthcity_id_str: ' + str(_birthcity_id_str) + ' Type: ' + str(type(_birthcity_id_str)))
            #_birthcity_id_int = int(_birthcity_id_str)
            #logger.debug('StudentAddView _birthcity_id_int: ' + str(_birthcity_id_int) + ' Type: ' + str(type(_birthcity_id_int)))
            #try:
            ##    _birthcity = Birthcity.objects.get(id=_birthcity_id_int)
            #    logger.debug('StudentAddView form.is_valid _clean__birthcity: ' + str(_birthcity) + ' Type: ' + str(type(_birthcity)))
            #    student.birthcity = _birthcity
            #except:
            #    pass
           # _birthcity = form.cleaned_data.get('birthcity_field')  # Value: Barbados Type: <class 'students.models.Birthcity'>
            #student.birthcity = _birthcity

            student.save(request=self.request)
            return redirect('student_list_url')
        else:
            """If the form is invalid, render the invalid form."""
            _param = f.get_headerbar_param(request, {
                'form': form,
                'display_school': True
            })
            return render(request, 'student_add.html', _param)


@method_decorator([login_required], name='dispatch')
class StudentEditView(UpdateView):  # PR2018-10-31
    model = Student
    form_class = StudentEditForm
    template_name = 'student_edit.html'
    context_object_name = 'student'

    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        kwargs = super(StudentEditView, self).get_form_kwargs()
        # add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})
        return kwargs

    def form_valid(self, form):
        student = form.save(commit=False)
        # PR2019-02-08 get scheme from dep. lvl and sct; None is not found
        student.scheme = Scheme.get_scheme(student.department,student.level, student.sector)
        logger.debug('student.scheme' + str(student.scheme))
        student.save(request=self.request)

        return redirect('student_list_url')


@method_decorator([login_required], name='dispatch')
class StudentDeleteView(DeleteView):
    model = Student
    template_name = 'student_delete.html'  # without template_name Django searches for student_confirm_delete.html
    success_url = reverse_lazy('student_list_url')

    def delete(self, request, *args, **kwargs):
       self.object = self.get_object()

       if self.request.user:
          self.object.delete(request=self.request)
          return HttpResponseRedirect(self.get_success_url())
       else:
          raise Http404 #or return HttpResponse('404_url')


@method_decorator([login_required], name='dispatch')
class StudentLogView(View):
    def get(self, request, pk):
        # student_log = Student_log.objects.filter(student_id=pk).order_by('-modified_at')
        student_log = Student_log.objects.all().order_by('lastname')
        student = Student.objects.get(id=pk)
        _param = f.get_headerbar_param(request,  {'student_log': student_log, 'student': student})
        return render(request, 'student_log.html', _param)


# ========  Result  =====================================
@method_decorator([login_required], name='dispatch')
class ResultListView(ListView):  # PR2018-11-21

    def get(self, request, *args, **kwargs):
        _params = f.get_headerbar_param(request, {'display_examyear': True, 'display_school': True, 'display_dep': True, 'display_user': True})
        # get school from user.examyear and user.schoolbase PR2018-09-03
        if request.user.examyear and request.user.schoolbase:
            # logger.debug('ResultListView get request.user.examyear = ' + str(request.user.examyear) + ' type : ' + str(type(request.user.examyear)))
            # logger.debug('ResultListView get request.user.schoolbase = ' + str(request.user.schoolbase) + ' type : ' + str(type(request.user.schoolbase)))

            school= School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
            if school:
                # logger.debug('ResultListView get school = ' + str(school) + ' type : ' + str(type(school)))

                if request.user.depbase:
                    # logger.debug('ResultListView get request.user.department = ' + str(request.user.department) + ' type : ' + str(type(request.user.department)))
                    # TODO testing
                    department= Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()
                    # logger.debug('ResultListView get department = ' + str(department) + ' type : ' + str(type(department)))
                    # filter results of this school and this department
                    results = Result.objects.filter(student__school=school, student__department=department)
                    # logger.debug('ResultListView get results = ' + str(results) + ' type : ' + str(type(results)))
                    _params.update({'school': school})
                    _params.update({'results': results})
        return render(request, 'result_list.html', _params)


@method_decorator([login_required], name='dispatch')
class ResultEditView(UpdateView):  # PR2018-10-31
    model = Result
    form_class = ResultEditForm
    template_name = 'result_edit.html'
    context_object_name = 'result'

    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        kwargs = super(ResultEditView, self).get_form_kwargs()
        # add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})
        return kwargs

    def form_valid(self, form):
        result = form.save(commit=False)

        result.save(request=self.request)

        return redirect('result_list_url')


@method_decorator([login_required], name='dispatch')
class ResultLogView(View):
    def get(self, request, pk):
        # result_log = Result_log.objects.filter(result_id=pk).order_by('-modified_at')
        result_log = Result_log.objects.all().order_by('lastname')
        result = Result.objects.get(id=pk)
        _param = f.get_headerbar_param(request,  {'result_log': result_log, 'result': result})
        return render(request, 'result_log.html', _param)


# ========  Student subject  =====================================
@method_decorator([login_required], name='dispatch')
class StudentsubjectListView(ListView):  # PR2018-11-21

    def get(self, request, *args, **kwargs):
        _params = f.get_headerbar_param(request, {
            'display_school': True,
            'display_dep': True,
            'display_user': True
        })
        # get school from user.examyear and user.schoolbase PR2018-09-03
        if request.user.examyear and request.user.schoolbase:
            # logger.debug('StudentsubjectListView get request.user.examyear = ' + str(request.user.examyear) + ' type : ' + str(type(request.user.examyear)))
            # logger.debug('StudentsubjectListView get request.user.schoolbase = ' + str(request.user.schoolbase) + ' type : ' + str(type(request.user.schoolbase)))

            school= School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
            if school:
                # logger.debug('StudentsubjectListView get school = ' + str(school) + ' type : ' + str(type(school)))

                if request.user.depbase:
                    # logger.debug('StudentsubjectListView get request.user.department = ' + str(request.user.department) + ' type : ' + str(type(request.user.department)))

                    department= Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()
                    # logger.debug('StudentsubjectListView get department = ' + str(department) + ' type : ' + str(type(department)))
                    # filter studentsubject of this school and this department
                    # studentsubjects = Studentsubject.objects.filter(result__student__school=school, result__student__department=department)
                    studentsubjects = Studentsubject.objects.all()
                    students = Student.objects.filter(school=school, department =  department).all()
                    student_list = []
                    for student in students:
                        student_dict = {}
                        student_dict['id'] = str(student.id)
                        student_dict['name'] = student.lastname_firstname_initials
                        student_list.append(student_dict)
                    student_list = json.dumps(student_list)

                    # TODO: use Subject.get_subj_list PR2019-01-18 >> move to ajax.download, get scheme-subjects
                    dep_id_str = ';' + str(department.base.id) + ';'
                    subjects = Subject.objects.filter(examyear=request.user.examyear,depbase_list__contains=dep_id_str).all()
                    subject_list = []
                    for subject in subjects:
                        subject_list.append ({'id': str(subject.id), 'name': subject.name})
                    subject_list = json.dumps(subject_list)

                    # logger.debug('StudentsubjectListView get studentsubjects = ' + str(studentsubjects) + ' type : ' + str(type(studentsubjects)))
                    _params.update({'school': school})
                    _params.update({'department': department})
                    _params.update({'student_list': student_list})
                    #_params.update({'subject_list': subject_list})
                    #_params.update({'studentsubjects': studentsubjects})
        return render(request, 'studentsubject.html', _params)


@method_decorator([login_required], name='dispatch')
class StudentsubjectAddView(CreateView): # PR2018-09-03

    def get(self, request, *args, **kwargs):
        form = StudentsubjectAddForm(request=request)

        _param = f.get_headerbar_param(request, {
            'form': form,
            'display_school': True,
            'display_dep': True})
        return render(request, 'studentsubject_add.html', _param)

    def post(self, request, *args, **kwargs):
        form = StudentsubjectAddForm(request.POST, request=request) # this one doesn't work: form = Subjectdefault(request=request)
        # logger.debug('StudentsubjectAddView post request.POST: ' + str(self.request.POST) + ' type: ' + str(type(self.request.POST)))

        if form.is_valid():
            studentsubject = form.save(commit=False)
            # logger.debug('studentsubject commit=False: ' + str(studentsubject) + ' type: ' + str(type(studentsubject)))

            studentsubject.save(request=self.request)
            # logger.debug('studentsubject saved studentsubject.id: ' + str(studentsubject.id) + ' type: ' + str(type(studentsubject.id)))
            return redirect('studentsubject_url')
        else:
            # If the form is invalid, render the invalid form.
            _param = f.get_headerbar_param(request, {
                'form': form,
                'display_school': True,
                'display_dep': True})
            return render(request, 'studentsubject_add.html', _param)



@method_decorator([login_required], name='dispatch')
class StudentsubjectEditView(UpdateView):  # PR2018-10-31
    model = Studentsubject
    form_class = StudentsubjectEditForm
    template_name = 'Studentsubject_edit.html'
    context_object_name = 'studentsubject'

    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        kwargs = super(StudentsubjectEditView, self).get_form_kwargs()
        # add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})

        # logger.debug('StudentsubjectEditView get_form_kwargs: ' + str(kwargs) + ' type: ' + str(type(kwargs)))
        return kwargs

    def form_valid(self, form):
        studentsubject = form.save(commit=False)
        # logger.debug('form_valid studentsubject: ' + str(studentsubject) + ' type: ' + str(type(studentsubject)))

        studentsubject.save(request=self.request)
        # logger.debug('form_valid studentsubject saved: ')

        return redirect('studentsubject_url')


@method_decorator([login_required], name='dispatch')
class StudentsubjectFormsetView(ListView):  # PR2018-11-29
    model = Studentsubject
    form_class = StudentsubjectFormset
    heading_message = 'Formset Demo'
    template_name = 'studentsubject_formset.html'
    context_object_name = 'studentsubject'

    def get(self, request, *args, **kwargs):
        # we don't want to display the already saved model instances
        formset = StudentsubjectFormset() #(queryset=Studentsubject.objects.none())

        _param = f.get_headerbar_param(request, {
            'formset': formset,
            'heading': self.heading_message,
            'display_examyear': True,
            'display_school': True,
            'override_school': str(request),
            'display_dep': True})
        return render(request, self.template_name, _param)

    def post(self, request, *args, **kwargs):
        formset = StudentsubjectFormset(data=request.POST, files=request.FILES)
        # logger.debug('StudentsubjectFormsetView post request.POST: ' + str(self.request.POST) + ' type: ' + str(type(self.request.POST)))

        if formset.is_valid():
            # logger.debug('StudentsubjectFormsetView post formset.is_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))

            instances = formset.save(commit=False)
            for instance in instances:
                instance.save(request=self.request)

            # logger.debug('StudentsubjectFormsetView post formset.is_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))

            return render(request, 'country_formset.html', {'formset': formset})


        else:
            # logger.debug('StudentsubjectFormsetView post formset.is_NOT_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))
            return render(request, self.template_name, {'formset': formset})



# ===== Import Students ===================
@method_decorator([login_required], name='dispatch')
class ImportStudentView(View):  # PR2018-12-01

    logger.debug('===== Import Students =========' )
    def get(self, request):
        mapped_coldefs = get_mapped_coldefs_student(request.user)  # PR2018-12-01
        logger.debug('mapped_coldefs: ' + str(mapped_coldefs) + ' Type: ' + str(type(mapped_coldefs)))
        param = {
            'display_school': True,
            'display_dep': True,
            'display_user': True,
            'mapped_coldefs': mapped_coldefs
        }
        headerbar_param = f.get_headerbar_param(request, param)


        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_student.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class StudentImportUploadDataView(View):  # PR2018-12-04

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= StudentImportUploadDataView ============= ')

        if request.user is not None and request.user.examyear is not None:
            if request.user.schoolbase is not None and request.user.depbase is not None:
                # get school and department of this schoolyear
                school = School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
                department = Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()

                students = json.loads(request.POST['students'])

                params = []

                for student in students:

# ------------ import student   -----------------------------------
                    logger.debug(' ')
                    logger.debug('import student:')
                    logger.debug(str(student))

# ---  fill in required fields
                    # required field: "idnumber", "lastname" + "firstname" or "fullname"
                    # not required:  "prefix", "gender","birthdate", "birthcountry", "birthcity",
                    # "level", "sector", "classname", "examnumber"

                    data = {}
                    has_error = False
                    dont_add = False

    # ---   validate idnumber, convert to birthdate
                    # otherwise '1999.01.31.15' and '1999013115' are not recognized as the same idnumber
                    if 'idnumber' in student:
                        if student['idnumber']:
                            data['o_idnumber'] = student['idnumber']
                    clean_idnumber, birthdate, msg_dont_add = v.validate_idnumber(data['o_idnumber'])
                    if msg_dont_add:
                        dont_add = True
                        data['e_idnumber'] = msg_dont_add
                    else:
    # ---   validate if idnumber is not None and if it already exist in this school and examyear
                        # function returns None if ID is not None and not exists, otherwise returns msgtext
                        msg_dont_add = v.idnumber_already_exists(clean_idnumber,school)
                        if msg_dont_add:
                            dont_add = True
                            data['e_idnumber'] = msg_dont_add

    # ---   set lastname / firstname / prefix / fullname
                    if 'lastname' in student:
                        if student['lastname']:
                            data['o_lastname'] = student['lastname']
                    if 'firstname' in student:
                        if student['firstname']:
                            data['o_firstname'] = student['firstname']
                    if 'prefix' in student:
                        if student['prefix']:
                            data['o_prefix'] = student['prefix']

                    data['o_fullname'] = data['o_lastname']
                    if 'o_prefix' in data:
                        data['o_fullname'] = data['o_prefix'] + ' ' + data['o_fullname']
                    if 'o_firstname' in data:
                        data['o_fullname'] = data['o_firstname'] + ' ' + data['o_fullname']

    # ---   validate if firstname and lastname are not None and if name already exists in this school and examyear
                    # function returns None if name is not None and not exists, otherwise returns msgtext
                    msg_dont_add = v.studentname_already_exists(data['o_lastname'], data['o_firstname'], school)
                    if msg_dont_add:
                        dont_add = True
                        data['e_lastname'] = msg_dont_add
                        data['e_firstname'] = msg_dont_add

    # ---   validate if examnumber is not None and if it already exists in this school and examyear
                    if 'examnumber' in student:
                        if student['examnumber']:
                            data['o_examnumber'] = student['examnumber']
                    msg_dont_add = v.examnumber_already_exists(data['o_examnumber'], school)
                    if msg_dont_add:
                        dont_add = True
                        data['e_examnumber'] = msg_dont_add

    # ---   validate level / sector
                    level = None
                    sector = None
                    if 'level' in student:
                        if student['level']:
                            # logger.debug('student[level]: ' + str(student['level']))
                            if student['level'].isnumeric():
                                level_id = int(student['level'])
                                level = Level.objects.filter(id=level_id, examyear=request.user.examyear).first()
                    if 'sector' in student:
                        if student['sector']:
                            # logger.debug('student[sector]: ' + str(student['sector']) + str(type(student['sector'])))
                            if student['sector'].isnumeric():
                                sector_id = int(student['sector'])
                                sector = Sector.objects.filter(id=sector_id, examyear=request.user.examyear).first()
                                logger.debug('sector: ' + str(sector.name))
                    scheme = Scheme.get_scheme(department, level, sector)

                    if scheme:
                        logger.debug('scheme: ' + str(scheme))

    # ========== create new student, but only if no errors found
                    if dont_add:
                        logger.debug('Student not created: ')
                        # TODO stud_log.append(_("Student not created."))
                    else:
                        new_student = Student(
                            school=school,
                            department=department,
                            idnumber=clean_idnumber,
                            lastname=data['o_lastname'],
                            firstname=data['o_firstname'],
                            examnumber = data['o_examnumber']
                        )
                        # stud_log['fullname'] = "Student '" + fullname + "' created."
                        # stud_log['fullname'] = _("Student created.")

                        if level:
                            new_student.level = level
                        if sector:
                            new_student.sector = sector
                        if scheme:
                            new_student.scheme = scheme

                    # calculate birthdate from  if lastname / firstname already exist in this school and examyear
                        if birthdate:
                            new_student.birthdate = birthdate


                        for field in ('prefix', 'gender', 'birthcountry', 'birthcity', 'classname'):
                            if field in student:
                                value = student[field]
                                data['o_' + field] = value
                                skip = False

                                # validate 'gender'
                                if field == 'gender':
                                    clean_gender, msg_text = v.validate_gender(value)
                                    if msg_text:
                                        has_error = True
                                        data['e_gender'] = msg_text
                                    # validate_gender eneters '-' as gender on error
                                    new_student.gender = clean_gender

                        # validate 'birthcountry'
                                if field == 'birthcountry':
                                    if value:
                                        new_student.birthcountry = value

                        # validate 'birthcity'
                                if field == 'birthcity':
                                    if value:
                                        new_student.birthcity = value

                        # validate 'classname'
                                if field == 'classname':
                                    if value:
                                        new_student.classname = value

                        try:
                            new_student.save(request=self.request)
                        except:
                            has_error = True
                            data['e_lastname'] = _('An error occurred. The student data is not saved.')

                        if new_student.id:
                            if new_student.idnumber:
                                data['s_idnumber'] = new_student.idnumber
                            if new_student.lastname:
                                data['s_lastname'] = new_student.lastname
                            if new_student.firstname:
                                data['s_firstname'] = new_student.firstname
                            # TODO: full_name
                            if new_student.prefix:
                                data['s_prefix'] = new_student.prefix
                            if new_student.gender:
                                data['s_gender'] = new_student.gender
                            if new_student.birthdate:
                                data['s_birthdate'] = new_student.birthdate
                            if new_student.birthcountry:
                                data['s_birthcountry'] = new_student.birthcountry
                            if new_student.birthcity:
                                data['s_birthcity'] = new_student.birthcity
                            if new_student.level:
                                data['s_level'] = new_student.level.abbrev
                            if new_student.sector:
                                data['s_sector'] = new_student.sector.abbrev
                            if new_student.classname:
                                data['s_classname'] = new_student.classname
                            if new_student.examnumber:
                                data['s_examnumber'] = new_student.examnumber

                        # logger.debug(str(new_student.id) + ': Student ' + new_student.lastname_firstname_initials + ' created ')

                            # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html
                            # for key, val in student.items():
                            #    logger.debug( str(key) +': ' + val + '" found in "' + str(student) + '"')

                    # json_dumps_err_list = json.dumps(msg_list, cls=f.LazyEncoder)
                    if len(data) > 0:
                        params.append(data)
                    # params.append(student)

                #return HttpResponse(json.dumps(params))
                return HttpResponse(json.dumps(params, cls=LazyEncoder))


@method_decorator([login_required], name='dispatch')
class StudentImportUploadSettingView(View):  # PR2018-12-03
    # function updates mapped fields, no_header and worksheetname in table Schoolsettings
    def post(self, request, *args, **kwargs):
        # logger.debug(' ============= StudentImportUploadSettingView ============= ')
        # logger.debug('request.POST' + str(request.POST) )

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user is not None and request.user.schoolbase is not None:
            if request.user.schoolbase is not None:
                # fieldlist: ["idnumber", "examnumber", "lastname", "firstname", "prefix", "gender",
                #            "birthdate", "birthcountry", "birthcity", "dep", "level",  "sector", "classname"]
                student_fieldlist = Student.fieldlist()

                awpcoldef = {}
                worksheetname = None
                no_header = False
                awpLevel = {}
                awpSector = {}

                # request.POST:
                # {'worksheetname': ['Compleetlijst'], 'no_header': ['false'],
                # 'col_idnumber': ['LLNR'], 'col_classname': ['KLAS'],
                # 'sct_29': ['abdul_k_'], 'sct_30': ['cm'], 'sct_31': ['ng']}
                for key in request.POST.keys():
                    if key == "worksheetname":
                        worksheetname = request.POST[key]
                    elif key == "no_header":
                        no_header = request.POST[key].lower() == 'true'
                    elif key[:4] == "col_":
                        if key[4:] in student_fieldlist:
                            awpcoldef[key[4:]] = request.POST[key]
                    elif key[:4] == "lvl_":  # slice off 'sector_' from key
                        awpLevel[key[4:]] = request.POST[key]
                    elif key[:4] == "sct_":  # slice off 'sector_' from key
                        awpSector[key[4:]] = request.POST[key]

                setting = Schoolsetting.objects.filter(
                    schoolbase=request.user.schoolbase,
                    key_str=c.KEY_STUDENT_MAPPED_COLDEFS
                ).first()
                if setting is None:
                    setting = Schoolsetting(
                        schoolbase=request.user.schoolbase,
                        key_str=c.KEY_STUDENT_MAPPED_COLDEFS
                    )
                setting.char01 = json.dumps(awpcoldef)
                setting.char02 = worksheetname
                setting.char03 = json.dumps(awpLevel)
                setting.char04 = json.dumps(awpSector)
                setting.bool01 = no_header
                setting.save()

                response = HttpResponse("Student import settings uploaded!")
        return response



@method_decorator([login_required], name='dispatch')
class StudentsubjectDownloadView(View):  # PR2019-02-08

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= StudentsubjectDownloadView ============= ')
        # logger.debug('request.POST' + str(request.POST) )

        params = {}
        if request.user is not None and request.user.examyear is not None and \
                request.user.schoolbase is not None and request.user.depbase is not None:
            school = School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
            dep = Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()
            if school and dep:
                if 'stud_id' in request.POST.keys():
                    student_id = request.POST['stud_id']
                    student = Student.objects.filter(id=student_id, school=school, department=dep).first()
                    # PR2019-02-09 debug: get level and sector from scheme, just in case scheme is None in student
                    # logger.debug('student: ' + str(student))
                    if student:
                        student_dict ={'stud_id': student.id, 'name': student.full_name}  # full_name cannot be None

                        scheme = student.scheme
                        # check if dep - lvl - sct is consistent
                        # error if student.scheme does not exist
                        consistent_error = not student.scheme
                        if not consistent_error:
                            # scheme.department and student.department are required and therefore not None
                            consistent_error = (scheme.department != student.department)
                            if not consistent_error:
                                if scheme.department.level_req:
                                    consistent_error = (not scheme.level or not student.level)
                                    if not consistent_error:
                                        consistent_error = (scheme.level != student.level)
                                if not consistent_error:
                                    if scheme.department.sector_req:
                                        consistent_error = not scheme.sector or not student.sector
                                        if not consistent_error:
                                            consistent_error = scheme.sector != student.sector
                        # logger.debug('consistent_error: ' + str(consistent_error))

                        if not consistent_error:
                            level_sector = ''
                            if student.level:
                                level_sector = student.level.abbrev
                            if student.sector:
                                if level_sector:
                                    level_sector += ' - '
                                level_sector += student.sector.name
                            if level_sector:
                                student_dict['level_sector'] = level_sector

                        params.update({'student': student_dict})
                        # logger.debug('student_dict: ' + str(student_dict)

                        if not consistent_error:
                            # make list of all Subjects from this department and examyear (included in dep)
                            schemeitems = Schemeitem.get_schemeitem_list(scheme)
                            params.update({'schemeitems': schemeitems})
                            logger.debug('schemeitems: ' + str(schemeitems))

                            studentsubjects = Studentsubject.get_studsubj_list(student)
                            params.update({'studentsubjects': studentsubjects})
                            logger.debug('studentsubjects: ' + str(studentsubjects))

        json_dumps_params = json.dumps(params)

        return HttpResponse(json_dumps_params)


@method_decorator([login_required], name='dispatch')
class StudentsubjectUploadView(View):  # PR2019-02-09

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= StudentsubjectUploadView ============= ')
        # stud_ssi =  {'mode': 'c', 'stud_id': '412', 'ssi_id': '1597'}

        params = {}
        if request.user is not None and request.user.examyear is not None and request.user.schoolbase is not None:
            # get sybject scheme item from  request.POST
            studentsubjects = json.loads(request.POST['studentsubjects'])
            logger.debug("studentsubjects: " + str(studentsubjects))

            for item in studentsubjects:
                # convert values

                # studsubj = {'mode': 'c', 'studsubj_id': 'ssiid_1592', 'ssi_id': '1592', 'subj_id': '319',
                # 'subj_name': 'Nederlandse taal en literatuur', 'sjtp_id': '10', 'sjtp_name': 'Gemeensch.',
                # 'sjtp_one': 0, 'sequence': 11001, 'extra_nocount': 0, 'extra_counts': 0, 'choice_combi': 0,
                # 'pws_title': '', 'pws_subjects': ''}

                # get selected student
                stud_id = int(item.get('stud_id', '0'))
                student = Student.objects.filter(id=stud_id).first()
                # logger.debug("student: " + str(student))

                # get selected  schemeitem
                ssi_id = int(item.get('ssi_id', '0'))
                schemeitem = Schemeitem.objects.filter(id=ssi_id).first()
                # logger.debug("schemeitem: " + str(schemeitem.id))

                # ssi_id only necessary when items are updated
                mode = item.get('mode', '')

                if student and schemeitem:
                    if mode == 'c':
                        # create new studentsubject
                        studsubj = Studentsubject(
                            student=student,
                            schemeitem=schemeitem,
                        )
                        # TODO add extra_nocount etc

                        studsubj.save(request=self.request)
                        logger.debug("new studentsubject: " + str(studsubj))

                    else:
                        # lookup studentsubject
                        studsubj_id = int(item.get('studsubj_id', '0'))
                        studsubj = Studentsubject.objects.filter(id=studsubj_id).first()


                    if studsubj:
                        if studsubj.student == student and studsubj.schemeitem == schemeitem:
                            if mode == 'd':
                                logger.debug("delete studsubj  ")
                                # TODO don't delete when there are submitted grades PR2019-02-10
                                studsubj.delete(request=self.request)
                                record_saved = True
                                logger.debug(" studsubj deleted ")
                            else:
                                pass
                                # check for changes > in save
                                studsubj.extra_nocount = bool(item.get('extra_nocount', '0'))
                                studsubj.extra_counts = bool(item.get('extra_counts', '0'))
                                studsubj.choice_combi = bool(item.get('choice_combi', '0'))
                                studsubj.pws_title = item.get('pws_title', '')
                                studsubj.pws_subjects = item.get('pws_subjects', '')

                                # logger.debug("extra_nocount: " + str(extra_nocount) + ' type: ' + str(type(extra_nocount)))
                                # logger.debug("extra_counts: " + str(extra_counts) + ' type: ' + str(type(extra_counts)))
                                # logger.debug("choice_combi: " + str(choice_combi) + ' type: ' + str(type(choice_combi)))
                                # logger.debug("pws_title: " + str(pws_title) + ' type: ' + str(type(pws_title)))
                                # logger.debug("pws_subjects: " + str(pws_subjects) + ' type: ' + str(type(pws_subjects)))


                                # update mode or create mode
                                studsubj.save(request=self.request)

                                logger.debug("studentsubject: " + str(studsubj))

                                record_saved = True

                    # renew list of all Subjects from this department and examyear (included in dep)
                    studentsubjects = Studentsubject.get_studsubj_list(student)
                    params.update({'studentsubjects': studentsubjects})

                    # make list of all Subjects from this department and examyear (included in dep)
                    schemeitems = Schemeitem.get_schemeitem_list(student.scheme)
                    params.update({'schemeitems': schemeitems})

                    if not record_saved:
                        if mode == 'c':
                            err_code = 'err_msg02'
                        elif mode == 'd':
                            err_code = 'err_msg04'
                        else:
                            err_code = 'err_msg03'
                        params.update({'err_code': err_code})

        # logger.debug("params: " + str(params))

        # PR2019-02-04 was: return HttpResponse(json.dumps(params))

        # return HttpResponse(json.dumps(params, cls=LazyEncoder), mimetype='application/javascript')

        return HttpResponse(json.dumps(params, cls=LazyEncoder))


"""
@method_decorator([login_required], name='dispatch')
class StudentsubjectFormsetView(ListView):  # PR2018-11-29
    model = Studentsubject
    form_class = StudentsubjectFormset
    heading_message = 'Formset Demo'
    template_name = 'studentsubject_formset.html'
    context_object_name = 'studentsubject'

    def get(self, request, *args, **kwargs):
        formset = StudentsubjectFormset() #(request=request)
        _param = f.get_headerbar_param(request, {
            'formset': formset,
            'heading': self.heading_message,
            'display_school': True,
            'display_dep': True})
        return render(request, self.template_name, _param)

    def post(self, request, *args, **kwargs):
        formset = StudentsubjectFormset(data=request.POST, files=request.FILES)
        logger.debug('StudentsubjectFormsetView post request.POST: ' + str(self.request.POST) + ' type: ' + str(type(self.request.POST)))

        if formset.is_valid():
            logger.debug('StudentsubjectFormsetView post formset.is_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))

            instances = formset.save(commit=False)
            for instance in instances:
                instance.save(request=self.request)

            logger.debug('StudentsubjectFormsetView post formset.is_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))

            return render(request, 'country_formset.html', {'formset': formset})
        else:
            logger.debug('StudentsubjectFormsetView post formset.is_NOT_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))
            return render(request, self.template_name, {'formset': formset})
"""

# ========  Grade  =====================================
@method_decorator([login_required], name='dispatch')
class GradeListView(ListView):  # PR2018-11-21

    def get(self, request, *args, **kwargs):
        _params = f.get_headerbar_param(request, {'display_school': True, 'display_dep': True, 'display_user': True})
        # get school from user.examyear and user.schoolbase PR2018-09-03
        if request.user.examyear and request.user.schoolbase:
            logger.debug('GradeListView get request.user.examyear = ' + str(request.user.examyear) + ' type : ' + str(type(request.user.examyear)))
            logger.debug('GradeListView get request.user.schoolbase = ' + str(request.user.schoolbase) + ' type : ' + str(type(request.user.schoolbase)))

            school= School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
            if school:
                # logger.debug('GradeListView get school = ' + str(school) + ' type : ' + str(type(school)))

                if request.user.depbase:
                    # logger.debug('GradeListView get request.user.department = ' + str(request.user.department) + ' type : ' + str(type(request.user.department)))
                    # TODO testing
                    department= Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()
                    logger.debug('GradeListView get department = ' + str(department) + ' type : ' + str(type(department)))
                    # filter grade of this school and this department
                    # grades = Grade.objects.filter(result__student__school=school, result__student__department=department)
                    grades = Grade.objects.all()

                    # logger.debug('GradeListView get grades = ' + str(grades) + ' type : ' + str(type(grades)))
                    _params.update({'school': school})
                    _params.update({'grades': grades})
        return render(request, 'grade_list.html', _params)


@method_decorator([login_required], name='dispatch')
class GradeAddView(CreateView): # PR2018-09-03

    def get(self, request, *args, **kwargs):
        form = GradeAddForm(request=request)

        _param = f.get_headerbar_param(request, {
            'form': form,
            'display_school': True,
            'display_dep': True})
        return render(request, 'Grade_add.html', _param)

    def post(self, request, *args, **kwargs):
        form = GradeAddForm(request.POST, request=request) # this one doesn't work: form = Subjectdefault(request=request)
        logger.debug('GradeAddView post request.POST: ' + str(self.request.POST) + ' type: ' + str(type(self.request.POST)))

        if form.is_valid():
            grade = form.save(commit=False)
            logger.debug('grade commit=False: ' + str(grade) + ' type: ' + str(type(grade)))

            grade.save(request=self.request)
            logger.debug('grade saved grade.id: ' + str(grade.id) + ' type: ' + str(type(grade.id)))
            return redirect('grade_list_url')
        else:
            # If the form is invalid, render the invalid form.
            _param = f.get_headerbar_param(request, {
                'form': form,
                'display_examyear': True,
                'display_school': True,
                'display_dep': True})
            return render(request, 'grade_add.html', _param)



@method_decorator([login_required], name='dispatch')
class GradeEditView(UpdateView):  # PR2018-10-31
    model = Grade
    form_class = GradeEditForm
    template_name = 'Grade_edit.html'
    context_object_name = 'grade'

    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        kwargs = super(GradeEditView, self).get_form_kwargs()
        # add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})

        logger.debug('GradeEditView get_form_kwargs: ' + str(kwargs) + ' type: ' + str(type(kwargs)))
        return kwargs

    def form_valid(self, form):
        grade = form.save(commit=False)
        logger.debug('form_valid grade: ' + str(grade) + ' type: ' + str(type(grade)))

        grade.save(request=self.request)
        logger.debug('form_valid grade saved: ')

        return redirect('grade_list_url')



@method_decorator([login_required], name='dispatch')
class GradeLogView(View):
    def get(self, request, pk):
        # grade_log = Grade_log.objects.filter(student_id=pk).order_by('-modified_at')
        grade_log = Grade_log.objects.all().order_by('-modified_at')

        _param = f.get_headerbar_param(request,  {'grade_log': grade_log})
        return render(request, 'grade_log.html', _param)


# oooooooooooooo Functions ooooooooooooooooooooooooooooooooooooooooooooooooooo

def get_mapped_coldefs_student(request_user):  # PR2018-12-01
    # function creates dict of fieldnames of table Student
    # It is used in ImportSudent to map Excel fieldnames to AWP fieldnames
    # mapped_coldefs: {
    #     "worksheetname": "Compleetlijst",
    #     "no_header": 0,
    #     "mapped_coldef_list": [{"awpKey": "idnumber", "caption": "ID nummer", "excKey": "ID"},
    #                            {"awpKey": "lastname", "caption": "Achternaam", "excKey": "ANAAM"}, ....]

    logger.debug('==============get_mapped_coldefs_student ============= ' )

    # get mapped excelColDef from table Schoolsetting
    mapped_coldefs = {}
    if request_user is not None:
        if request_user.examyear is not None and request_user.schoolbase is not None and request_user.depbase is not None:

            # get list of level base_id and abbrev of this school, examyear and department
            level_abbrev_list = Level.get_abbrev_list(request_user)

            # get saved settings from schoolsettings
            no_header, worksheetname, setting_columns, setting_levels, setting_sectors = get_student_mapped_coldefs(request_user)
            # setting_columns: {'gender': 'MV', 'birthdate': 'GEB_DAT', 'birthcountry': 'geboorte_land',
            #                   'birthcity': 'geboorte_plaats', 'sector': 'Profiel', 'classname': 'KLAS'}
            # setting_sectors: {'29': 'em', '30': 'ng', '31': 'cm'}

# add excKey to coldef if found in setting_columns
            column_list = get_student_column_list(request_user)
            # column_list is list of default student coldef keys and captions
            # column_list = [{"awpKey": "idnumber", "caption": "ID nummer"},
            #                {"awpKey": "fullname", "caption": "Volledige naam"}, ...]
            for coldef in column_list:
                awpKey = coldef.get('awpKey')
                # awpKey: 'idnumber'
                if awpKey: # awpKey should always be present
                    if setting_columns:
                        # lookup awpKey 'idnumber' in setting_columns, return None if not found
                        # setting_columns: {'idnumber': 'ID', ...}
                        excKey = setting_columns.get(awpKey)
                        # excKey: 'ID'
                        if excKey:
                        # if 'idnumber' found in setting_columns, add {'excKey': 'ID'} to coldef
                            coldef['excKey'] = excKey
            # column_list: [{'awpKey': 'idnumber', 'caption': 'ID nummer', 'excKey': 'ID'},

            # level_list is list of levels of this school, dep and examyear
            # level_list =  [{'base_id': 7, 'abbrev': 'TKL'},
            #                {'base_id': 8, 'abbrev': 'PKL'},
            #                {'base_id': 9, 'abbrev': 'PBL'}]
            level_list = Level.get_abbrev_list(request_user)
            logger.debug('level_list: ' + str(level_list) + ' type: ' + str(type(level_list)))

            mapped_level_list = []
            for level in level_list:
                base_id_str = str(level.get('base_id',''))
                abbrev = level.get('abbrev')
                level_dict = {}
                if base_id_str and abbrev:
                    level_dict['awpKey'] = base_id_str
                    level_dict['caption'] = abbrev
                    # check if base_id_str of this level is stored in setting_levels
                    # setting_levels: {'29': 'em', '30': 'ng', '31': 'cm'}
                    if base_id_str in setting_levels:
                        excKey = setting_levels[base_id_str]
                        if excKey:
                            level_dict['excKey'] = excKey
                if level_dict:
                    mapped_level_list.append(level_dict)
            logger.debug('mapped_level_list: ' + str(mapped_level_list) + ' type: ' + str(type(mapped_level_list)))


            # sector_list is list of sectors of this school, dep and examyear
            # sector_list =  [{'base_id': 29, 'abbrev': 'ec'},
            #                 {'base_id': 30, 'abbrev': 'tech'},
            #                 {'base_id': 31, 'abbrev': 'z&w'}]
            sector_list = Sector.get_abbrev_list(request_user)
            mapped_sector_list = []
            for sector in sector_list:
                base_id_str = str(sector.get('base_id',''))
                abbrev = sector.get('abbrev')
                sector_dict = {}
                if base_id_str and abbrev:
                    sector_dict['awpKey'] = base_id_str
                    sector_dict['caption'] = abbrev
                    # check if base_id_str of this sector is stored in setting_sectors
                    # setting_sectors: {'29': 'em', '30': 'ng', '31': 'cm'}
                    if base_id_str in setting_sectors:
                        excKey = setting_sectors[base_id_str]
                        if excKey:
                            sector_dict['excKey'] = excKey
                if sector_dict:
                    mapped_sector_list.append(sector_dict)
            #logger.debug('mapped_sector_list: ' + str(mapped_sector_list) + ' type: ' + str(type(mapped_sector_list)))

            mapped_coldefs = {
                "worksheetname": worksheetname,
                "no_header": no_header,
                "mapped_coldef_list": column_list
            }
            if mapped_level_list:
                mapped_coldefs['mapped_level_list'] = mapped_level_list
            if mapped_sector_list:
                mapped_coldefs['mapped_sector_list'] = mapped_sector_list

            logger.debug('mapped_coldefs: ' + str(mapped_coldefs) + ' type: ' + str(type(mapped_coldefs)))
            mapped_coldefs = json.dumps(mapped_coldefs)
    return mapped_coldefs

# ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo

def get_student_column_list(request_user):
    # function creates dict of fieldnames of table Student
    # It is used in ImportSudent to map Excel fieldnames to AWP fieldnames
    # mapped_coldefs: {
    #     "worksheetname": "Compleetlijst",
    #     "no_header": 0,
    #     "mapped_coldef_list": [{"awpKey": "idnumber", "caption": "ID nummer", "excKey": "ID"},
    #                            {"awpKey": "lastname", "caption": "Achternaam", "excKey": "ANAAM"}, ....]

    # logger.debug('==============get_mapped_coldefs_student ============= ' )

    # caption Sector/Profiel depends on department
    sector_caption = Sector.get_caption(request_user)
    skip_level = True
    if request_user.depbase:
        dep = request_user.department
        if dep.abbrev == "Vsbo":
            skip_level = False

    if request_user.lang == 'nl':
        coldef_list = [
            {"awpKey": "idnumber", "caption": "ID nummer"},
            {"awpKey": "fullname", "caption": "Volledige naam"},
            {"awpKey": "lastname", "caption": "Achternaam"},
            {"awpKey": "firstname", "caption": "Voornamen"},
            {"awpKey": "prefix", "caption": "Voorvoegsel"},
            {"awpKey": "gender", "caption": "Geslacht"},
            {"awpKey": "birthdate", "caption": "Geboortedatum"},
            {"awpKey": "birthcountry", "caption": "Geboorteland"},
            {"awpKey": "birthcity", "caption": "Geboorteplaats"},
        ]
    else:
        coldef_list = [
            {"awpKey": "idnumber", "caption": "ID number"},
            {"awpKey": "fullname", "caption": "Full name"},
            {"awpKey": "lastname", "caption": "Last name"},
            {"awpKey": "firstname", "caption": "First name"},
            {"awpKey": "prefix", "caption": "Prefix"},
            {"awpKey": "gender", "caption": "Gender"},
            {"awpKey": "birthdate", "caption": "Birthdate"},
            {"awpKey": "birthcountry", "caption": "Birth country"},
            {"awpKey": "birthcity", "caption": "Birth place"},
        ]

    if not skip_level:
        coldef_list.append({"awpKey": "level", "caption": "Leerweg"})
    coldef_list.append({"awpKey": "sector", "caption": sector_caption})

    if request_user.lang == 'nl':
        coldef_list.extend((
            {"awpKey": "classname", "caption": "Klas"},
            {"awpKey": "examnumber", "caption": "Examennummer"}
        ))
    else:
        coldef_list.extend((
            {"awpKey": "classname", "caption": "Class"},
            {"awpKey": "examnumber", "caption": "Exam number"}
        ))

    return coldef_list

def get_student_mapped_coldefs(request_user):
    logger.debug(        '---  get_student_mapped_coldefs  ------- ' + str(request_user))
    # get mapped excelColDef from table Schoolsetting

    no_header = False
    worksheetname = ''
    setting_columns = {}
    setting_levels = {}
    setting_sectors = {}

    if request_user is not None:
        if request_user.schoolbase is not None:
            logger.debug('request_user.schoolbase: ' + str(request_user.schoolbase) + ' type: ' + str(type(request_user.schoolbase)))
            setting = Schoolsetting.objects.filter(
                schoolbase=request_user.schoolbase,
                key_str=c.KEY_STUDENT_MAPPED_COLDEFS
            ).first()

            if setting:
                no_header = int(setting.bool01)

                # setting_columns: {'firstname': 'Voornamen', 'classname': 'STAMKLAS'} type: <class 'dict'>
                if setting.char01:
                    try:
                        setting_columns = json.loads(setting.char01)
                    except:
                        pass

                if setting.char02:
                    worksheetname = setting.char02

                if setting.char03:
                    try:
                        setting_levels = json.loads(setting.char03)
                    except:
                        pass
                if setting.char04:
                    try:
                        setting_sectors = json.loads(setting.char04)
                    except:
                        pass
            logger.debug('setting_columns: ' + str(setting_columns) + ' type: ' + str(type(setting_columns)))
    return  no_header, worksheetname, setting_columns, setting_levels, setting_sectors


def get_mapped_levels_sectors(request_user):  # PR2019-01-01
    # function creates dict of fieldnames of table Student
    # It is used in ImportSudent to map Excel fieldnames to AWP fieldnames
    #     "settings_level_list": [{"awpLevel": "TKL", "excelLevel": ["tkl", "t.k.l."]"},
    #                            {"awpLevel": "PBL", "excelLevel": [], ....]

    logger.debug('==============get_mapped_levels_student ============= ' )
    level_abbrev_list = Level.get_abbrev_list(request_user)
    sector_abbrev_list = Sector.get_abbrev_list(request_user)
    # sector_abbrev_list =  [{'base_id': 29, 'abbrev': 'ec'},
    #                        {'base_id': 30, 'abbrev': 'tech'},
    #                        {'base_id': 31, 'abbrev': 'z&w'}]

    # get mapped levels and mapped sectors from table Schoolsetting
    """
    TODO: settings_level_list and settings_sector_list not defined PR2019-02-11
    mapped_level_list = []
    # iterate through list of levels: [{"base_id": 1, "caption": TKL}, {"base_id": 2, "caption": PKL}, {"base_id": 3, "caption": PBL}]
    for level_abbrev in level_abbrev_list:
        level_dict = {'awpKey': str(level_abbrev.get('base_id')), 'caption': level_abbrev.get('abbrev')}
    # check if this awpLevel is stored in settings_level_list
        for settings_dict in settings_level_list:
            # settings_dict = {"id": 2, "caption": "pkl"},
            if 'awpKey' in settings_dict:
                if settings_dict['awpKey'] == level_dict['awpKey']:
    # check if this awpLevel has excKey
                    if "excKey" in settings_dict:
    # if so: add to  awpLevel is stored in settings_level_list
                        level_dict['excKey'] = settings_dict['excKey']
                        break
        mapped_level_list.append(level_dict)

    mapped_sector_list = []
    # iterate through list of sectors ["eco", "techn", "z&w"]
    for sector_abbrev in sector_abbrev_list:
        sector_dict = {'awpKey': str(sector_abbrev.get('base_id')), 'caption': sector_abbrev.get('abbrev')}
    # check if this awpSector is stored in settings_sector_list
        for settings_dict in settings_sector_list:
            # dict = {"awpSct": "tkl", "excKey": ["tkl", "t.k.l."]"},
            if 'awpKey' in settings_dict:
                if settings_dict['awpKey'] == sector_dict['awpKey']:
    # check if this awpSector has excKey
                    if "excKey" in dict:
    # if so: add to  awpSector is stored in settings_sector_list
                        sector_dict['excKey'] = settings_dict['excKey']
                        break
        mapped_sector_list.append(sector_dict)

    logger.debug('mapped_sector_list: ' + str(mapped_sector_list))
    logger.debug('mapped_level_list: ' + str(mapped_level_list))
    return mapped_level_list, mapped_sector_list

    """
# ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo


#  =========== Ajax requests  ===========
# PR2018-09-03 from https://simpleisbetterthancomplex.com/tutorial/2018/01/29/how-to-implement-dependent-or-chained-dropdown-list-with-django.html
def load_cities(request):
    # logger.debug('load_cities request: ' + str(request) + ' Type: ' + str(type(request)))
    # load_cities request: <WSGIRequest: GET '/student/ajax/load_cities/?birthcountry_id=16'> Type: WSGIRequest
    birthcountry_id = request.GET.get('birthcountry_id')
    # logger.debug('load_cities country_id ' + str(birthcountry_id) + ' Type: ' + str(type(birthcountry_id)))

    # create list of tuples
    # items = [(0, '---')]
    # for _city in Birthcity.objects.filter(birthcountry_id=birthcountry_id).order_by('name'):
    #     items.append((_city.id, _city.name))
    # see: https: // www.journaldev.com / 15891 / python - zip - function

    # create list of dicts
    items =[] # [{'id': 0, 'name': '---'}]
    keys = ['id', 'name']
    for _city in Birthcity.objects.filter(birthcountry_id=birthcountry_id).order_by('name'):
        values = [_city.id, _city.name]
        items.append(dict(zip(keys, values)))

    logger.debug('load_cities items: ' + str(items) + ' Type: ' + str(type(items)))
    # was: cities: < QuerySet[ < Birthcity: Anderlecht >, ... , < Birthcity: Wilrijk >] > Type: <class 'QuerySet'>
    # items: [{'id': 13, 'name': 'Anderlecht'}, ... , {'id': 27, 'name': 'Wilrijk'}]Type: <class 'list'>

    return render(request, 'dropdown_list_options.html', {'items': items})


"""

      $(document).ready(function(){
        $("#id_birthcountry").change(function () {
          var url = $("#StudentAddForm").attr("data-cities-url");  // get the url of the `load_cities` view
          var birthcountryId = $(this).val();  // get the selected country ID from the HTML input

          $.ajax({                       // initialize an AJAX request
            url: url,                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
            data: {
              'birthcountry': birthcountryId       // add the country id to the GET parameters
            },
            success: function (data) {   // `data` is the return of the `load_cities` view function
              $("#id_birthcity").html(data);  // replace the contents of the city input with the data that came from the server
            }

        });
      });
"""

"""

      $(document).ready(function(){
      // from http://jsfiddle.net/CZcvM/

        var sel = $('#testing'),
            opts =[],
            debug = $('#debug');

      debug.append(typeof sel);
      var opt_array = sel.attr('options');
      //for(var i = 0, len = opt_array.length; i < len; ++i)
      for (var a in opt_array)
      {
          debug.append(a + ':' + opt_array[a] + "<br>");
          //opts.push(opt_array[a]);
      }
      //delete the first option
      function remove()
      {
          $('#testing option:first').remove();
      }

      function restore()
      {
          sel.options.length = 0;
          for(var i = 0, len = opts.length; i < len; ++i)
          {
              //debug.append(a + ':' + opts[a] + '<br>');
              sel.options.add(opts[i]);
          }
      }
      */
      $('#remove').click(remove);
      $('#restore').click(restore);








        $("#testbutton").click(function(){
            $(this).css("background-color", "pink");

            var temp = "myXXValue";

            // Create New Option.
            var newOption = $("<option>");

            newOption.attr("value", temp).text(temp);
            $("#showtext").html(newOption.value);

            // Append that to the DropDownList.
            $('#carselect').append(newOption);

            // Select the Option.
            // $("#carselect" > [value=" + temp + "]").attr("selected", "true");


            $("#showtext").html(temp);

        });
                 // $("p").hover(function(){
                 //        $(this).css("background-color", "yellow");
                 //        }, function(){
                 //        $(this).css("background-color", "pink");
                 //    });
      });
     </script>


"""