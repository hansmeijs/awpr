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
from students.models import Student, Student_log, Studentresult, Studentresult_log, Studentsubject, Grade, Grade_log, Birthcountry, Birthcity
from students.forms import StudentAddForm, StudentEditForm, StudentresultEditForm, StudentsubjectFormset, \
    StudentsubjectAddForm, StudentsubjectEditForm, GradeAddForm, GradeEditForm

from awpr import functions as f
from awpr import constants as c

# PR2018-04-27
import logging
logger = logging.getLogger(__name__)



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


# ========  Studentresult  =====================================
@method_decorator([login_required], name='dispatch')
class StudentresultListView(ListView):  # PR2018-11-21

    def get(self, request, *args, **kwargs):
        _params = f.get_headerbar_param(request, {'display_examyear': True, 'display_school': True, 'display_dep': True, 'display_user': True})
        # get school from user.examyear and user.schoolbase PR2018-09-03
        if request.user.examyear and request.user.schoolbase:
            # logger.debug('StudentresultListView get request.user.examyear = ' + str(request.user.examyear) + ' type : ' + str(type(request.user.examyear)))
            # logger.debug('StudentresultListView get request.user.schoolbase = ' + str(request.user.schoolbase) + ' type : ' + str(type(request.user.schoolbase)))

            school= School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
            if school:
                # logger.debug('StudentresultListView get school = ' + str(school) + ' type : ' + str(type(school)))

                if request.user.depbase:
                    # logger.debug('StudentresultListView get request.user.department = ' + str(request.user.department) + ' type : ' + str(type(request.user.department)))
                    # TODO testing
                    department= Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()
                    # logger.debug('StudentresultListView get department = ' + str(department) + ' type : ' + str(type(department)))
                    # filter studentresults of this school and this department
                    studentresults = Studentresult.objects.filter(student__school=school, student__department=department)
                    # logger.debug('StudentresultListView get studentresults = ' + str(studentresults) + ' type : ' + str(type(studentresults)))
                    _params.update({'school': school})
                    _params.update({'studentresults': studentresults})
        return render(request, 'studentresult_list.html', _params)


@method_decorator([login_required], name='dispatch')
class StudentresultEditView(UpdateView):  # PR2018-10-31
    model = Studentresult
    form_class = StudentresultEditForm
    template_name = 'studentresult_edit.html'
    context_object_name = 'studentresult'

    # from https://stackoverflow.com/questions/7299973/django-how-to-access-current-request-user-in-modelform?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # PR 2018-05-25 add request to kwargs, so it passes request to the form
    def get_form_kwargs(self):
        kwargs = super(StudentresultEditView, self).get_form_kwargs()
        # add request to kwargs, so it can be passed to form
        kwargs.update({'request': self.request})
        return kwargs

    def form_valid(self, form):
        studentresult = form.save(commit=False)

        studentresult.save(request=self.request)

        return redirect('studentresult_list_url')


@method_decorator([login_required], name='dispatch')
class StudentresultLogView(View):
    def get(self, request, pk):
        # studentresult_log = Studentresult_log.objects.filter(studentresult_id=pk).order_by('-modified_at')
        studentresult_log = Studentresult_log.objects.all().order_by('lastname')
        studentresult = Studentresult.objects.get(id=pk)
        _param = f.get_headerbar_param(request,  {'studentresult_log': studentresult_log, 'studenresultt': studentresult})
        return render(request, 'studentresult_log.html', _param)


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
                    # TODO testing
                    department= Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()
                    # logger.debug('StudentsubjectListView get department = ' + str(department) + ' type : ' + str(type(department)))
                    # filter studentsubject of this school and this department
                    # studentsubjects = Studentsubject.objects.filter(studentresult__student__school=school, studentresult__student__department=department)
                    studentsubjects = Studentsubject.objects.all()

                    # logger.debug('StudentsubjectListView get studentsubjects = ' + str(studentsubjects) + ' type : ' + str(type(studentsubjects)))
                    _params.update({'school': school})
                    _params.update({'studentsubjects': studentsubjects})
        return render(request, 'studentsubject_list.html', _params)


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
            return redirect('studentsubject_list_url')
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

        return redirect('studentsubject_list_url')


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

    def get(self, request):
        mapped_coldefs = get_mapped_coldefs_student(request.user)  # PR2018-12-01
        param = {
            'display_school': True,
            'display_dep': True,
            'display_user': True,
            'mapped_coldefs': mapped_coldefs
        }
        headerbar_param = f.get_headerbar_param(request, param)
        # logger.debug('headerbar_param: ' + str(headerbar_param) + ' Type: ' + str(type(headerbar_param)))

        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_student.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class StudentImportUploadDataView(View):  # PR2018-12-04

    def post(self, request, *args, **kwargs):

        logger.debug(' ============= StudentImportUploadDataView ============= ')
        # logger.debug('post request.POST: ' + str(request.POST) + ' type: ' + str(type(request.POST)))

        if request.user is not None and request.user.examyear is not None:
            if request.user.schoolbase is not None and request.user.depbase is not None:
                # get school and department of this schoolyear
                school = School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
                department = Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()

                logger.debug('request.user.examyear: ' + str(request.user.examyear))
                logger.debug('school: ' + str(school))
                logger.debug('department: ' + str(department))

                students = json.loads(request.POST['students'])
                # logger.debug('post students: '  + str(students) + ' type: ' + str(type(students)))
                students_log = []
                for student in students:
    # ------------ import student   -----------------------------------
                    logger.debug('post student: '  + str(student) + ' type: ' + str(type(student)))

            # check if required fields are present
                    # required field: "idnumber", "lastname" + "firstname" or "fullname"
                    # not required:  "prefix", "gender","birthdate", "birthcountry", "birthcity",
                    # "level", "sector", "classname", "examnumber"

                    stud_log = []
                    msg_list = []

    # delete non-numeric characters from idnumber,
                    # otherwise '1999.01.31.15' and '1999013115' are not recognized as the same idnumber
                    has_error = False
                    msg_str = ''
                    k = 'idnumber'
                    idnumber_stripped = ''
                    if k in student:
                        if student[k]:
                            idnumber_stripped = re.sub("[^0-9]", "", student[k])
                    if not idnumber_stripped:
                        msg_list.append(_("ID number not entered."))

                    logger.debug('idnumber_stripped: ' + str(idnumber_stripped) + ' type: ' + str(type(idnumber_stripped)))
            # validate if idnumber already exist in this school and examyear
                    if Student.objects.filter(
                            idnumber__iexact=idnumber_stripped, # _iexact filters a Case-insensitive exact match.
                            school=school).exists():
                        msg_list.append(_("ID number already exists."))

            # validate if lastname / firstname already exist in this school and examyear
                    k = 'lastname'
                    lastname = ''
                    if k in student:
                        if student[k]:
                            lastname = student[k]
                    if not lastname:
                        msg_list.append(_("Last name not entered."))
                    logger.debug('lastname: ' + str(lastname) + ' type: ' + str(type(lastname)))

                    k = 'firstname'
                    firstname = ''
                    if k in student:
                        if student[k]:
                            firstname = student[k]
                    if not firstname:
                        msg_list.append(_("First name not entered."))
                    logger.debug('firstname: ' + str(firstname) + ' type: ' + str(type(firstname)))

                    k = 'prefix'
                    prefix = ''
                    if k in student:
                        if student[k]:
                            prefix = student[k]

                    fullname = lastname
                    if prefix:
                        fullname = prefix + ' ' +fullname
                    if firstname:
                        fullname = firstname + ' ' +fullname

    # from https://stackoverflow.com/questions/1285911/how-do-i-check-that-multiple-keys-are-in-a-dict-in-a-single-pass
                    # if all(k in student for k in ('idnumber','lastname', 'firstname')):

                    if Student.objects.filter(
                            lastname__iexact=lastname,
                            firstname__iexact=firstname,
                            school=school).exists():
                        msg_list.append(_("Student name already exists."))

# ========== create new student, but only if no errors found
                    if  msg_list:
                        logger.debug('Student not created: ')
                        stud_log.append(_("Student not created."))
                    else:

                        logger.debug('Student created ')
                        new_student = Student(
                            school=school,
                            department=department,
                            idnumber=idnumber_stripped,
                            lastname=lastname,
                            firstname=firstname
                        )
                        new_student.save(request=self.request)
                        stud_log.append(fullname)

                    # calcultae birthdate from  if lastname / firstname already exist in this school and examyear
                        birthdate_calc, msg_str, has_error = calc_bithday_from_id(idnumber_stripped)
                        #if not has_error:
                         #   new_student.birthdate = birthdate_calc
                        logger.debug('birthdate_calc: ' + str(birthdate_calc))

                        gender_clean = ''
                        birthdate_clean = None
                        for field in ('prefix', 'gender', 'birthdate', 'birthcountry', 'birthcity',
                                  'level', 'sector', 'classname', 'examnumber'):
                            if field in student:
                                value = student[field]
                                skip = False

                        # validate 'gender'
                                if field == 'gender':
                                    value_upper=''
                                    if len(value) > 1:
                                        skip = True
                                    else:
                                        value_upper = value.upper()
                                        if value_upper in ('M', 'F',):
                                            pass
                                        elif value_upper == 'V':
                                            value_upper = 'F'
                                        else:
                                            skip = True
                                    if skip:
                                        msg_list.append("Gender" + "'" + value + "' not allowed." + "Only 'M', 'm', 'F', 'f', 'V', 'v' are allowed.")
                                    else:
                                        new_student.gender = value_upper
                                    logger.debug('msg_list: ' + str(msg_list))
                                    logger.debug('gender_clean: ' + str(gender_clean))

                                #if field == 'birthdate':
                                #    logger.debug('birthdate value: ' + str(value))
                                #    try:
                                #        # try to convert to date_time_obj
                                #        logger.debug('value: ' + str(value) + ' type: ' + str(type(value)))
                                #        birthdate_clean = datetime.datetime.strptime(value, '%b %d %Y %I:%M%p')
                                #        logger.debug('birthdate_clean: ' + str(birthdate_clean) + ' type: ' + str(type(birthdate_clean)))
                                #    except:
                                #        skip = True
                                #        msg_list.append(_("Birthdate") + "'" + value + "'" + _("cannot be converted to valid birh date"))

                                #if not skip:
                                #    setattr(new_student, field, value)


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

                        # validate 'examnumber'
                                if field == 'examnumber':
                                    if value:
                                        new_student.examnumber = value


                        new_student.save(request=self.request)

                            # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html
                            # for key, val in student.items():
                            #    logger.debug( str(key) +': ' + val + '" found in "' + str(student) + '"')

        logger.debug('msg_list: ' + str(msg_list))


        response = HttpResponse("It works!!")
        logger.debug('post response: ' + str(response) + ' type: ' + str(type(response)))

        return response


@method_decorator([login_required], name='dispatch')
class StudentImportUploadSettingView(View):  # PR2018-12-03
    # function updates mapped fields, no_header and worksheetname in table Schoolsettings
    def post(self, request, *args, **kwargs):
        logger.debug(' ============= StudentImportUploadSettingView ============= ')
        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user is not None:
            if request.user.schoolbase is not None:
                student_fieldlist = Student.fieldlist()

                awpcoldef = {}
                worksheetname = None
                no_header = False

                for key in request.POST.keys():
                    logger.debug('request.POST[' + str(key) + ']: ' + request.POST[key] + ' type: ' + str(type(request.POST[key])))
                    if key == "worksheetname":
                        worksheetname = request.POST[key]
                    elif key == "no_header":
                        no_header = request.POST[key].lower() == 'true'
                    elif key in student_fieldlist:
                        awpcoldef[key] = request.POST[key]

                awpcoldef_json = json.dumps(awpcoldef)
                logger.debug('post awpcoldef_json: ' + str(awpcoldef_json) + ' type: ' + str(type(awpcoldef_json)))
                # awpcoldef_json: {"firstname": "Voornamen", "classname": "STAMKLAS"} type: <class 'str'>
                logger.debug('post no_header: ' + str(no_header) + ' type: ' + str(type(no_header)))
                setting = Schoolsetting.objects.filter(
                    schoolbase=request.user.schoolbase,
                    key_str=c.KEY_STUDENT_MAPPED_COLDEFS
                ).first()
                if setting is None:
                    setting = Schoolsetting(
                        schoolbase=request.user.schoolbase,
                        key_str=c.KEY_STUDENT_MAPPED_COLDEFS
                    )
                if no_header:
                    setting.char01 = awpcoldef_json
                else:
                    setting.char02 = awpcoldef_json
                setting.char03 = worksheetname
                setting.bool01 = no_header

                setting.save()

                response = HttpResponse("StudentImportAwpcoldefView works!!")
                logger.debug('post response: ' + str(response) + ' type: ' + str(type(response)))

        return response


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
                    # grades = Grade.objects.filter(studentresult__student__school=school, studentresult__student__department=department)
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

# ============== Functions =====================================


# ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo

def get_mapped_coldefs_student(request_user):  # PR2018-12-01
    # function creates dict of fieldnames of table Student
    # It is used in ImportSudent to map Excel fieldnames to AWP fieldnames
    # AwpColDef = {'no_header': 0,
    #               'AwpColDef': [
    #                   {'awpCol': 'dep', 'excCol': '', 'caption': 'Departement'},
    #                   {'awpCol': 'level', 'excCol': '', 'caption': 'Level'},
    #                   etc
    logger.debug('==============get_mapped_coldefs_student ============= ' )

    # caption Sector/Profiel depends on department
    sector_caption =  "Sector/Profiel"
    if request_user.depbase:
        dep = request_user.department
        if dep.abbrev == "Vsbo":
            sector_caption = "Sector"
        else:
            sector_caption = "Profiel"

    if request_user.lang == 'nl':
        coldef_list = [
            {"awpCol": "idnumber", "caption": "ID nummer"},
            {"awpCol": "fullname", "caption": "Volledige naam"},
            {"awpCol": "lastname", "caption": "Achternaam"},
            {"awpCol": "firstname", "caption": "Voornamen"},
            {"awpCol": "prefix", "caption": "Voorvoegsel"},
            {"awpCol": "gender", "caption": "Geslacht"},
            {"awpCol": "birthdate", "caption": "Geboortedatum"},
            {"awpCol": "birthcountry", "caption": "Geboorteland"},
            {"awpCol": "birthcity", "caption": "Geboorteplaats"},
            {"awpCol": "level", "caption": "Leerweg"},
            {"awpCol": "sector", "caption": sector_caption},
            {"awpCol": "classname", "caption": "Klas"},
            {"awpCol": "examnumber", "caption": "Examennummer"}
        ]
    else:
        coldef_list = [
            {"awpCol": "idnumber", "caption": "ID number"},
            {"awpCol": "fullname", "caption": "Full name"},
            {"awpCol": "lastname", "caption": "Last name"},
            {"awpCol": "firstname", "caption": "First name"},
            {"awpCol": "prefix", "caption": "Prefix"},
            {"awpCol": "gender", "caption": "Gender"},
            {"awpCol": "birthdate", "caption": "Birthdate"},
            {"awpCol": "birthcountry", "caption": "Birth country"},
            {"awpCol": "birthcity", "caption": "Birth place"},
            {"awpCol": "level", "caption": "Level"},
            {"awpCol": "sector", "caption": sector_caption},
            {"awpCol": "classname", "caption": "Class"},
            {"awpCol": "examnumber", "caption": "Exam number"}
        ]

    # get mapped excelColDef from table Schoolsetting
    mapped_coldefs = {}
    if request_user is not None:
        if request_user.schoolbase is not None:
           # logger.debug('request_user.schoolbase: ' + str(request_user.schoolbase) + ' type: ' + str(type(request_user.schoolbase)))

            no_header = False
            worksheetname = ''
            setting_dict = {}

            setting = Schoolsetting.objects.filter(
                schoolbase=request_user.schoolbase,
                key_str=c.KEY_STUDENT_MAPPED_COLDEFS
            ).first()
            # logger.debug('setting: ' + str(setting) + ' type: ' + str(type(setting)))

            if setting:
                no_header = int(setting.bool01)

                # setting_dict: {'firstname': 'Voornamen', 'classname': 'STAMKLAS'} type: <class 'dict'>
                if no_header:
                    if setting.char01:
                        try:
                            setting_dict = json.loads(setting.char01)
                        except:
                            pass
                else:
                    if setting.char02:
                        # logger.debug('setting.char02: ' + str(setting.char02) + ' type: ' + str(type(setting.char02)))
                        try:
                            setting_dict = json.loads(setting.char02)
                        except:
                            pass
                if setting.char03:
                    worksheetname = setting.char03

            for coldef in coldef_list:
                awpCol = coldef["awpCol"]
                if setting_dict:
                    excCol = setting_dict.get(awpCol)
                    if excCol:
                        coldef["excCol"] = excCol

            mapped_coldefs = {
                "worksheetname": worksheetname,
                "no_header": no_header,
                "mapped_coldef_list": coldef_list
            }
            mapped_coldefs = json.dumps(mapped_coldefs)
    # logger.debug('mapped_coldefs: ' + str(mapped_coldefs) + ' type: ' + str(type(mapped_coldefs)))
    return mapped_coldefs



# ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo





def calc_bithday_from_id(id_str):
    #PR 28 jun 07 from Lrs 'PR2014-10-19 'PR2015-12-23
    # id_str is sedulanummer: format:: YYYY.MM.DD.XX or  YYYYMMDDXX

    #reset returnvalues
    date_dte = None
    msg_str = None
    has_error = False

    # return None when id_str is empty
    # logger.debug('calc_bithday_from_id id_str: ' + str(id_str) + ' type: ' + str(type(id_str)))
    if id_str:
    # get year, month and day from id_str
        month_str = '00'
        day_str = '00'
        if '.' in id_str:
        # make array if id_str contains dots (format: yyyy.mm.dd.xx)
            # PR2014 - 05 - 01 toegevoegd op vezoek HvD.SXM gebruikt sedulanr met punten
            arr =id_str.split('.')
            # logger.debug('calc_bithday_from_id arr: ' + str(arr) + ' type: ' + str(type(arr)))
            year_str = arr[0]
            if len(arr) >= 1:
                month_str = "00" + arr[1]
                month_str = month_str[-2:]
            if len (arr) >= 2:
                day_str =  "00" +arr[2]
                day_str = day_str[-2:]
        else:
        # get year, month and day from id_str (format: yyyymmddxx)
            year_str = id_str[:4]
            month_str = id_str[4:6]
            day_str = id_str[6:8]
            # logger.debug('year_str=' + str(year_str) + ' month_str=' + str(month_str) +' day_str=' + str(day_str))

        date_str = year_str + "-" + month_str + "-" + day_str
        # logger.debug('date_str=' + str(date_str))
        try:
            date_dte = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            # logger.debug('date_dte=' + str(date_dte) + ' type: ' + str(type(date_dte)))
        except ValueError as ve:
            # msg_str = "'" + date_str + "'" + _("is not a valid birthday.")

            # logger.debug("'" + date_str + "'is not a valid birthday.")
            has_error = True

    return date_dte, msg_str, has_error

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