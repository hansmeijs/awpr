# PR2018-09-02
from django.contrib.auth.decorators import login_required

from django.db.models.functions import Lower
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView, View

from awpr import functions as f
from awpr import constants as c
from students import validations as v
from awpr import menus as awpr_menu
from awpr import functions as af

from accounts import models as acc_mod
from schools import models as sch_mod
from students import models as stud_mod

import json # PR2018-12-03
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
class StudentListView(View):  # PR2018-09-02 PR2020-10-27

    def get(self, request):
        # logger.debug('  =====  StudentListView ===== ')
        # logger.debug('request: ' + str(request) + ' Type: ' + str(type(request)))

        # <PERMIT>
        # school-user can only view his own school
        # insp-users can only view schools from his country
        # system-users can only view school from request_user,country
        schools = None  # User.objects.filter(False) gives error: 'bool' object is not iterable
        menu_items = []
        if request.user is not None and request.user.examyear is not None:
            # logger.debug('request.user: ' + str(request.user) + ' Type: ' + str(type(request.user)))
            if request.user.examyear:
                if request.user.is_role_insp_or_admin_or_system:
                    # examyear has field country, therefore filter country is not necessary
                    schools = sch_mod.School.objects.filter(examyear=request.user.examyear)
                elif request.user.schoolbase is not None:
                    schools = sch_mod.School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear)

        # -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)


        # set headerbar parameters PR2018-08-06
        params = awpr_menu.get_headerbar_param(request, {
            'page': 'students',
            'menu_key': 'students'
        })

        # save this page in Usersetting, so at next login this page will open. Uses in LoggedIn
        acc_mod.Usersetting.set_jsonsetting('sel_page', {'page': 'schools'}, request.user)

        return render(request, 'students.html', params)


#/////////////////////////////////////////////////////////////////


def create_student_rows(examyear, append_dict, student_pk):
    # --- create rows of all students of this examyear / school PR2020-10-27
    # logger.debug(' =============== create_student_rows ============= ')

    sql_keys = {'ey_id': examyear.pk}
    sql_list = ["""SELECT st.id, st.base_id, st.school_id AS s_id, 
        st.department_id AS dep_id, st.level_id AS lvl_id, st.sector_id AS sct_id,
        dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,
        CONCAT('student_', st.id::TEXT) AS mapid,
        st.lastname, st.firstname, st.prefix, st.gender,
        st.idnumber, st.birthdate, st.birthcountry, st.birthcity,
        st.classname, st.examnumber, st.regnumber, st.diplomanumber, st.gradelistnumber,
        st.iseveningstudent, st.locked, st.has_reex, st.bis_exam, st.withdrawn,
        st.modifiedby_id, st.modifiedat,
        SUBSTRING(au.username, 7) AS modby_username

        FROM students_student AS st 
        LEFT JOIN schools_department AS dep ON (dep.id = st.department_id) 
        LEFT JOIN schools_level AS lvl ON (lvl.id = st.level_id) 
        LEFT JOIN schools_sector AS sct ON (sct.id = st.sector_id) 
        LEFT JOIN accounts_user AS au ON (au.id = st.modifiedby_id) 

        WHERE st.examyear_id = %(ey_id)s::INT
        """]

    if student_pk:
        # when student_pk has value: skip other filters
        sql_list.append('AND st.id = %(sj_id)s::INT')
        sql_keys['sj_id'] = student_pk
    else:
        sql_list.append('ORDER BY LOWER(st.lastname), LOWER(st.firstname)')
    sql = ' '.join(sql_list)

    newcursor = connection.cursor()
    newcursor.execute(sql, sql_keys)
    student_rows = sch_mod.dictfetchall(newcursor)

    # - add messages to student_row
    if student_pk and student_rows:
        # when student_pk has value there is only 1 row
        row = student_rows[0]
        if row:
            for key, value in append_dict.items():
                row[key] = value

    return student_rows


# --- end of create_student_rows


@method_decorator([login_required], name='dispatch')
class StudentUploadView(View):  # PR2020-10-01

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= studentUploadView ============= ')

        update_wrap = {}
        has_permit = False
        if request.user is not None and request.user.country is not None and request.user.schoolbase is not None:
            has_permit = True  # (request.user.is_perm_planner or request.user.is_perm_hrman)
        if has_permit:

            # - Reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                logger.debug('upload_dict' + str(upload_dict))

                # - get id  variables
                student_pk = f.get_dict_value(upload_dict, ('id', 'pk'))
                is_create = f.get_dict_value(upload_dict, ('id', 'create'), False)
                is_delete = f.get_dict_value(upload_dict, ('id', 'delete'), False)

                student_rows = []
                append_dict = {}
                error_dict = {}

                # A. check if examyear exists  (examyear is parent of student)
                examyear = request.user.examyear
                logger.debug('examyear' + str(examyear))
                if examyear:
                    # C. Delete student
                    if is_delete:
                        student = stud_mod.student.objects.get_or_none(id=student_pk, examyear=examyear)
                        if student:
                            this_text = _("student '%(tbl)s' ") % {'tbl': student.name}
                            # a. check if student has emplhours, put msg_err in update_dict when error
                            msg_err = None  # validate_student_has_emplhours(student)
                            if msg_err:
                                error_dict['err_delete'] = msg_err
                            else:
                                # b. check if there are teammembers with this student: absence teammembers, remove student from shift teammembers
                                # delete_student_from_teammember(student, request)
                                # c. delete student
                                deleted_ok = True  # m.delete_instance(student, {}, error_dict, request, this_text)
                                # logger.debug('deleted_ok' + str(deleted_ok))
                                if deleted_ok:
                                    # - add deleted_row to absence_rows
                                    student_rows.append({'pk': student_pk,
                                                         'mapid': 'student_' + str(student_pk),
                                                         'deleted': True})
                                    student = None
                                # logger.debug('student_rows' + str(student_rows))
                    else:
                        # D. Create new student
                        if is_create:
                            student, msg_err = create_student(examyear, upload_dict, request)
                            if student:
                                append_dict['created'] = True
                            elif msg_err:
                                append_dict['err_create'] = msg_err
                        # E. Get existing student
                        else:
                            student = stud_mod.Student.objects.get_or_none(id=student_pk, examyear=examyear)

                            # F. Update student, also when it is created.
                            #  Not necessary. Most fields are required. All fields are saved in create_student
                            # if student:
                            update_student(student, examyear, upload_dict, error_dict, request)

                    # I. add update_dict to update_wrap
                    if student:
                        if error_dict:
                            append_dict['error'] = error_dict

                        student_rows = create_student_rows(
                            examyear=examyear,
                            append_dict=append_dict,
                            student_pk=student.pk
                        )

                update_wrap['updated_student_rows'] = student_rows

        # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=f.LazyEncoder))


@method_decorator([login_required], name='dispatch')
class StudentImportView(View):  # PR2020-10-01

    def get(self, request):
        param = {}
        has_permit = False
        if request.user is not None and request.user.country is not None and request.user.schoolbase is not None:
            has_permit = True  # (request.user.is_perm_planner or request.user.is_perm_hrman)
        if has_permit:
            # coldef_list = [{'tsaKey': 'student', 'caption': _('Company name')},
            #                      {'tsaKey': 'ordername', 'caption': _('Order name')},
            #                      {'tsaKey': 'orderdatefirst', 'caption': _('First date order')},
            #                      {'tsaKey': 'orderdatelast', 'caption': _('Last date order')} ]

            # get coldef_list  and caption
            coldef_list = c.COLDEF_SUBJECT
            captions_dict = c.CAPTION_IMPORT

            # get mapped coldefs from table Companysetting
            # get stored setting from Companysetting
            settings_json = sch_mod.Schoolsetting.get_jsonsetting(c.KEY_SUBJECT_MAPPED_COLDEFS, request.user.schoolbase)
            stored_setting = json.loads(settings_json) if settings_json else {}

            # don't replace keyvalue when new_setting[key] = ''
            self.has_header = True
            self.worksheetname = ''
            self.codecalc = 'linked'
            if 'has_header' in stored_setting:
                self.has_header = False if Lower(stored_setting['has_header']) == 'false' else True
            if 'worksheetname' in stored_setting:
                self.worksheetname = stored_setting['worksheetname']
            if 'codecalc' in stored_setting:
                self.codecalc = stored_setting['codecalc']

            if 'coldefs' in stored_setting:
                stored_coldefs = stored_setting['coldefs']
                # skip if stored_coldefs does not exist
                if stored_coldefs:
                    # loop through coldef_list
                    for coldef in coldef_list:
                        # coldef = {'tsaKey': 'student', 'caption': 'Cliënt'}
                        # get fieldname from coldef
                        fieldname = coldef.get('tsaKey')
                        # logger.debug('fieldname: ' + str(fieldname))

                        if fieldname:  # fieldname should always be present
                            # check if fieldname exists in stored_coldefs
                            if fieldname in stored_coldefs:
                                # if so, add Excel name with key 'excKey' to coldef
                                coldef['excKey'] = stored_coldefs[fieldname]
                                # logger.debug('stored_coldefs[fieldname]: ' + str(stored_coldefs[fieldname]))

            coldefs_dict = {
                'worksheetname': self.worksheetname,
                'has_header': self.has_header,
                'codecalc': self.codecalc,
                'coldefs': coldef_list
            }
            coldefs_json = json.dumps(coldefs_dict, cls=LazyEncoder)

            captions = json.dumps(captions_dict, cls=LazyEncoder)

            param = awpr_menu.get_headerbar_param(request, {'captions': captions, 'setting': coldefs_json})

        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'studentimport.html', param)


@method_decorator([login_required], name='dispatch')
class StudentImportUploadSetting(View):  # PR2019-03-10
    # function updates mapped fields, no_header and worksheetname in table Companysetting
    def post(self, request, *args, **kwargs):
        # logger.debug(' ============= StudentImportUploadSetting ============= ')
        # logger.debug('request.POST' + str(request.POST) )
        schoolsetting_dict = {}
        has_permit = False
        if request.user is not None and request.user.examyear is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_perm_adm_or_sys_)
        if has_permit:
            if request.POST['upload']:
                new_setting_json = request.POST['upload']
                # new_setting is in json format, no need for json.loads and json.dumps
                # logger.debug('new_setting_json' + str(new_setting_json))

                new_setting_dict = json.loads(request.POST['upload'])
                settings_key = c.KEY_SUBJECT_MAPPED_COLDEFS

                new_worksheetname = ''
                new_has_header = True
                new_code_calc = ''
                new_coldefs = {}
                stored_json = sch_mod.Schoolsetting.get_jsonsetting(settings_key, request.user.schoolbase)
                if stored_json:
                    stored_setting = json.loads(stored_json)
                    # logger.debug('stored_setting: ' + str(stored_setting))
                    if stored_setting:
                        new_has_header = stored_setting.get('has_header', True)
                        new_worksheetname = stored_setting.get('worksheetname', '')
                        new_code_calc = stored_setting.get('codecalc', '')
                        new_coldefs = stored_setting.get('coldefs', {})

                if new_setting_json:
                    new_setting = json.loads(new_setting_json)
                    # logger.debug('new_setting' + str(new_setting))
                    if new_setting:
                        if 'worksheetname' in new_setting:
                            new_worksheetname = new_setting.get('worksheetname', '')
                        if 'has_header' in new_setting:
                            new_has_header = new_setting.get('has_header', True)
                        if 'coldefs' in new_setting:
                            new_coldefs = new_setting.get('coldefs', {})
                    # logger.debug('new_code_calc' + str(new_code_calc))
                new_setting = {'worksheetname': new_worksheetname,
                               'has_header': new_has_header,
                               'codecalc': new_code_calc,
                               'coldefs': new_coldefs}
                new_setting_json = json.dumps(new_setting)
                # logger.debug('new_setting' + str(new_setting))
                # logger.debug('---  set_jsonsettingg  ------- ')
                # logger.debug('new_setting_json' + str(new_setting_json))
                # logger.debug(new_setting_json)
                sch_mod.Schoolsetting.set_jsonsetting(settings_key, new_setting_json, request.user.schoolbase)

        # only for testing
        # ----- get user_lang
        # user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        # tblName = 'student'
        # coldefs_dict = compdicts.get_stored_coldefs_dict(tblName, user_lang, request)
        # if coldefs_dict:
        #    schoolsetting_dict['coldefs'] = coldefs_dict
        # logger.debug('new_setting from saved ' + str(coldefs_dict))

        # m.Companysetting.set_setting(c.settings_key, new_setting_json, request.user.schoolbase)

        return HttpResponse(json.dumps(schoolsetting_dict, cls=LazyEncoder))


# --- end of StudentImportUploadSetting

@method_decorator([login_required], name='dispatch')
class StudentImportUploadData(View):  # PR2018-12-04 PR2019-08-05 PR2020-06-04

    def post(self, request):
        logger.debug(' ========================== StudentImportUploadData ========================== ')
        params = {}
        has_permit = False
        is_not_locked = False
        if request.user is not None and request.user.examyear is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_perm_adm_or_sys_)
            is_not_locked = not request.user.examyear.locked

        if is_not_locked and has_permit:
            # - Reset language
            # PR2019-03-15 Debug: language gets lost, get request.user.lang again
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                params = import_students(upload_dict, user_lang, request)

        return HttpResponse(json.dumps(params, cls=LazyEncoder))


# --- end of StudentImportUploadData

def import_students(upload_dict, user_lang, request):
    logger.debug(' -----  import_students ----- ')
    logger.debug('upload_dict: ' + str(upload_dict))
    # - get is_test, codecalc, dateformat, awpKey_list
    is_test = upload_dict.get('test', False)
    awpKey_list = upload_dict.get('awpKey_list')
    dateformat = upload_dict.get('dateformat', '')

    params = {}
    if awpKey_list:
        # - get lookup_field
        # lookup_field is field that determines if student alreay exist.
        # check if one of the fields 'payrollcode', 'identifier' or 'code' exists
        # first in the list is lookup_field
        lookup_field = 'code'

        # - get upload_dict from request.POST
        student_list = upload_dict.get('students')
        if student_list:

            today_dte = af.get_today_dateobj()
            today_formatted = f.format_WDMY_from_dte(today_dte, user_lang)
            double_line_str = '=' * 80
            indent_str = ' ' * 5
            space_str = ' ' * 30
            logfile = []
            logfile.append(double_line_str)
            logfile.append('  ' + str(request.user.schoolbase.code) + '  -  ' +
                           str(_('Import students')) + ' ' + str(_('date')) + ': ' + str(today_formatted))
            logfile.append(double_line_str)

            if lookup_field is None:
                info_txt = str(_('There is no field given to lookup candidates. Candidates cannot be uploaded.'))
                logfile.append(indent_str + info_txt)
            else:
                if is_test:
                    info_txt = str(_("This is a test. The candidate data are not saved."))
                else:
                    info_txt = str(_("The candidate data are saved."))
                logfile.append(indent_str + info_txt)
                lookup_caption = str(get_field_caption('student', lookup_field))
                info_txt = str(_("Candidates are looked up by the field: '%(fld)s'.") % {'fld': lookup_caption})
                logfile.append(indent_str + info_txt)
                # if dateformat:
                #    info_txt = str(_("The date format is: '%(fld)s'.") % {'fld': dateformat})
                #    logfile.append(indent_str + info_txt)
                update_list = []
                for student_dict in student_list:
                    # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html

                    update_dict = upload_student(student_list, student_dict, lookup_field,
                                                 awpKey_list, is_test, dateformat, indent_str, space_str, logfile,
                                                 request)
                    # json_dumps_err_list = json.dumps(msg_list, cls=f.LazyEncoder)
                    if update_dict:  # 'Any' returns True if any element of the iterable is true.
                        update_list.append(update_dict)

                if update_list:  # 'Any' returns True if any element of the iterable is true.
                    params['student_list'] = update_list
            if logfile:  # 'Any' returns True if any element of the iterable is true.
                params['logfile'] = logfile
                # params.append(new_student)
    return params

def lookup_student(studentbase, request):  # PR2019-12-17 PR2020-10-20
    #logger.debug('----------- lookup_student ----------- ')

    student = None
    multiple_students_found = False

# - search student by studentbase and request.user.examyear
    if studentbase:
        # check if student exists multiple times
        row_count = stud_mod.Student.objects.filter(base=studentbase, examyear=request.user.examyear).count()
        if row_count > 1:
            multiple_students_found = True
        elif row_count == 1:
            # get student when only one found
            student = stud_mod.Student.objects.get_or_none(base=studentbase, examyear=request.user.examyear)

    return student, multiple_students_found



def get_field_caption(table, field):
    caption = ''
    if table == 'student':
        if field == 'code':
            caption = _('Abbreviation')
        elif field == 'name':
            caption = _('Student name')
        elif field == 'sequence':
            caption = _('Sequence')
        elif field == 'depbases':
            caption = _('Departments')
    return caption


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_student(examyear, upload_dict, request):
    # --- create student # PR2019-07-30 PR2020-10-11
    logger.debug(' ----- create_student ----- ')

    student = None
    msg_err = None

    logger.debug('examyear: ' + str(examyear))

    if examyear:

# - get value of 'abbrev'
        abbrev = f.get_dict_value(upload_dict, ('abbrev', 'value'))
        name = f.get_dict_value(upload_dict, ('name', 'value'))
        sequence = f.get_dict_value(upload_dict, ('sequence', 'value'))
        depbases = f.get_dict_value(upload_dict, ('depbases', 'value'))
        logger.debug('abbrev: ' + str(abbrev))
        logger.debug('name: ' + str(name))
        logger.debug('sequence: ' + str(sequence))
        logger.debug('depbases: ' + str(depbases) + str(type(depbases)))
        if abbrev and name and sequence:
# - validate abbrev checks null, max len and exists
            """
            msg_err = validate_code_name_identifier(
                table='student',
                field='code',
                new_value=code,
                is_absence=False,
                parent=parent,
                update_dict={},
                msg_dict={},
                request=request,
                this_pk=None)
            """
            msg_err = None
# - create and save student
            if not msg_err:

                try:
                    # First create base record. base.id is used in Student. Create also saves new record
                    base = stud_mod.Studentbase.objects.create()

                    student = stud_mod.Student(
                        base=base,
                        examyear=examyear,
                        name=name,
                        abbrev=abbrev,
                        sequence=sequence,
                        depbases=depbases
                    )
                    student.save(request=request)
                except:
                    msg_err = str(_("An error occurred. Student '%(val)s' could not be added.") % {'val': name})

    logger.debug('student: ' + str(student))
    logger.debug('msg_err: ' + str(msg_err))
    return student, msg_err


#######################################################
def update_student(instance, parent, upload_dict, msg_dict, request):
    # --- update existing and new instance PR2019-06-06
    # add new values to update_dict (don't reset update_dict, it has values)
    #logger.debug(' ------- update_student -------')
    #logger.debug('upload_dict' + str(upload_dict))

    if instance:
        # FIELDS_SUBJECT = ('base', 'examyear', 'name', 'abbrev','sequence', 'depbases', 'modifiedby', 'modifiedat')
        save_changes = False
        for field in c.FIELDS_SUBJECT:

# --- get field_dict from  upload_dict  if it exists
            field_dict = upload_dict[field] if field in upload_dict else {}
            if field_dict:
                if 'update' in field_dict:
# a. get new_value and saved_value
                    new_value = field_dict.get('value')
                    saved_value = getattr(instance, field)

# 2. save changes in field 'name', 'abbrev'
                    if field in ['name', 'abbrev']:
                        if new_value != saved_value:
            # validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                            """
                            msg_err = validate_code_name_identifier(
                                table='student',
                                field=field,
                                new_value=new_value, parent=parent,
                                is_absence=False,
                                update_dict={},
                                msg_dict={},
                                request=request,
                                this_pk=instance.pk)
                            """
                            msg_err = None
                            if not msg_err:
                                # c. save field if changed and no_error
                                setattr(instance, field, new_value)
                                save_changes = True
                            else:
                                msg_dict['err_' + field] = msg_err

    # 3. save changes in fields 'namefirst', 'namelast'
                    elif field in ['namefirst', 'namelast']:
                        if new_value != saved_value:
                            name_first = None
                            name_last = None
                            if field == 'namefirst':
                                name_first = new_value
                                name_last = getattr(instance, 'namelast')
                            elif field == 'namelast':
                                name_first = getattr(instance, 'namefirst')
                                name_last = new_value
                            # check if student namefirst / namelast combination already exists
                            """
                            has_error = validate_namelast_namefirst(
                                namelast=name_last,
                                namefirst=name_first,
                                company=request.user.company,
                                update_field=field,
                                msg_dict=msg_dict,
                                this_pk=instance.pk)
                            """
                            has_error = False
                            if not has_error:
                                setattr(instance, field, new_value)
                                save_changes = True

# 3. save changes in depbases
                    elif field == 'depbases':
                        # save new value when it has different length
                        len_new = len(new_value) if new_value else 0
                        len_saved = len(saved_value) if saved_value else 0
                        if len_new != len_saved:
                            setattr(instance, field, new_value)
                            save_changes = True
                        elif len_new:
                        # compare items in sorted list when len>0 (givers error otherwise)
                            new_value_sorted = sorted(new_value)
                            saved_value_sorted = sorted(saved_value)
                            if new_value_sorted != saved_value_sorted:
                                setattr(instance, field, new_value_sorted)
                                save_changes = True

# 4. save changes in field 'inactive'
                    elif field == 'inactive':
                        #logger.debug('inactive new_value]: ' + str(new_value) + ' ' + str(type(new_value)))
                        saved_value = getattr(instance, field)
                        #logger.debug('inactive saved_value]: ' + str(saved_value) + ' ' + str(type(saved_value)))
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
                    else:
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
# --- end of for loop ---

# 5. save changes
        if save_changes:
            try:
                instance.save(request=request)
            except:
                msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def upload_student(student_list, student_dict, lookup_field, awpKey_list,
                   is_test, dateformat, indent_str, space_str, logfile, request):  # PR2019-12-17 PR2020-10-21
    logger.debug('----------------- import student  --------------------')
    logger.debug(str(student_dict))
    # awpKeys are: 'code', 'name', 'sequence', 'depbases'

    # - get index and lookup info from student_dict
    row_index = student_dict.get('rowindex', -1)
    new_code = student_dict.get('code')
    new_name = student_dict.get('name')
    new_sequence = student_dict.get('sequence')
    new_depbases = student_dict.get('depbases')

    # - create update_dict
    update_dict = {'id': {'table': 'student', 'rowindex': row_index}}

    # - give row_error when lookup went wrong
    # multiple_found and value_too_long return the lookup_value of the error field

    lookup_field_caption = str(get_field_caption('student', lookup_field))
    lookup_field_capitalized = '-'
    if lookup_field_caption:
        lookup_field_capitalized = lookup_field_caption.capitalize()
    is_skipped_str = str(_("is skipped."))
    skipped_str = str(_("Skipped."))
    logfile.append(indent_str)
    msg_err = None
    log_str = ''

    studentbase = None
    student = None

    # check if lookup_value has value ( lookup_field = 'code')
    lookup_value = student_dict.get(lookup_field)
    if not lookup_value:
        log_str = str(_("No value for lookup field: '%(fld)s'.") % {'fld': lookup_field_caption})
        msg_err = ' '.join((skipped_str, log_str))

    # check if lookup_value is not too long
    elif len(lookup_value) > c.MAX_LENGTH_SUBJECTCODE:
        value_too_long_str = str(_("Value '%(fld)s' is too long.") % {'fld': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_SUBJECTCODE})
        log_str = value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))

    # check if new_name has value
    elif new_name is None:
        field_caption = str(get_field_caption('student', 'name'))
        log_str = str(_("No value for required field: '%(fld)s'.") % {'fld': field_caption})
        msg_err = ' '.join((skipped_str, log_str))

    # check if student name  is not too long
    elif len(new_name) > c.MAX_LENGTH_NAME:
        value_too_long_str = str(_("Value '%(fld)s' is too long.") % {'fld': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_NAME})
        log_str = value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))
    else:

        # - check if lookup_value occurs mutiple times in Excel file
        excel_list_multiple_found = False
        excel_list_count = 0
        for dict in student_list:
            value = dict.get(lookup_field)
            if value and value == lookup_value:
                excel_list_count += 1
            if excel_list_count > 1:
                excel_list_multiple_found = True
                break
        if excel_list_multiple_found:
            log_str = str(_("%(fld)s '%(val)s' is not unique in Excel file.") % {'fld': lookup_field_capitalized,
                                                                                 'val': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

    if msg_err is None:

        # - check if studentbase with this code exists in request.user.country. studentbase has value when only one found
        # lookup_value = student_dict.get(lookup_field)
        studentbase, multiple_found = lookup_studentbase(lookup_value, request)
        if multiple_found:
            log_str = str(_("Value '%(fld)s' is found multiple times.") % {'fld': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

        # - check if student with this studentbase exists in request.user.examyear. student has value when only one found
        multiple_students_found = False
        if studentbase:
            student, multiple_students_found = lookup_student(studentbase, request)
        if multiple_students_found:
            log_str = str(_("Value '%(fld)s' is found multiple times in this exam year.") % {'fld': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

    code_text = (new_code + space_str)[:30]

    # - if error: put msg_err in update_dict and logfile
    if msg_err:
        update_dict['row_error'] = msg_err
        update_dict[lookup_field] = {'error': msg_err}
        logfile.append(code_text + is_skipped_str)
        logfile.append(' ' * 30 + log_str)
    else:

        # - create new studentbase when studentbase not found in database
        if studentbase is None:
            try:
                studentbase = stud_mod.Studentbase(
                    country=request.user.country,
                    code=new_code
                )
                if studentbase:
                    studentbase.save()
            except:
                # - give error msg when creating studentbase failed
                error_str = str(_("An error occurred. The student is not added."))
                logfile.append(" ".join((code_text, error_str)))
                update_dict['row_error'] = error_str

        if studentbase:

            # - create new student when student not found in database
            is_existing_student = False
            save_instance = False

            if student is None:
                try:
                    student = stud_mod.Student(
                        base=studentbase,
                        examyear=request.user.examyear,
                        name=new_name
                    )
                    if student:
                        student.save(request=request)
                        update_dict['id']['created'] = True
                        logfile.append(code_text + str(_('is added.')))
                except:
                    # - give error msg when creating student failed
                    error_str = str(_("An error occurred. The student is not added."))
                    logfile.append(" ".join((code_text, error_str)))
                    update_dict['row_error'] = error_str
            else:
                is_existing_student = True
                logfile.append(code_text + str(_('already exists.')))

            if student:
                # add 'id' at the end, after saving the student. Pk doent have value until instance is saved
                # update_dict['id']['pk'] = student.pk
                # update_dict['id']['ppk'] = student.company.pk
                # if student:
                #    update_dict['id']['created'] = True

                # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
                # solved bij wrapping with str()

                blank_str = '<' + str(_('blank')) + '>'
                was_str = str(_('was') + ': ')
                # FIELDS_SUBJECT = ('base', 'examyear', 'name', 'abbrev', 'sequence', 'depbases', 'modifiedby', 'modifiedat')
                for field in ('name', 'abbrev', 'sequence', 'depbases'):
                    # --- get field_dict from  upload_dict  if it exists
                    if field in awpKey_list:
                        # ('field: ' + str(field))
                        field_dict = {}
                        field_caption = str(get_field_caption('student', field))
                        caption_txt = (indent_str + field_caption + space_str)[:30]

                        if field in ('code', 'name', 'namefirst', 'email', 'address', 'city', 'country'):
                            if field == 'code':
                                # new_code is created in this function and already checked for max_len
                                new_value = new_code
                            else:
                                new_value = student_dict.get(field)
                            # check length of new_value
                            max_len = c.MAX_LENGTH_NAME \
                                if field in ('namelast', 'namefirst', 'email', 'address', 'city', 'country') \
                                else c.MAX_LENGTH_CODE

                            if max_len and new_value and len(new_value) > max_len:
                                msg_err = str(_("'%(val)s' is too long. Maximum is %(max)s characters'.") % {
                                    'val': new_value, 'max': max_len})
                                field_dict['error'] = msg_err
                            else:
                                # - replace '' by None
                                if not new_value:
                                    new_value = None
                                field_dict['value'] = new_value
                                if not is_existing_student:
                                    logfile.append(caption_txt + (new_value or blank_str))
                                # - get saved_value
                                saved_value = getattr(student, field)
                                if new_value != saved_value:
                                    # put new value in student instance
                                    setattr(student, field, new_value)
                                    field_dict['updated'] = True
                                    save_instance = True
                                    # create field_dict and log
                                    if is_existing_student:
                                        old_value_str = was_str + (saved_value or blank_str)
                                        field_dict['info'] = field_caption + ' ' + old_value_str
                                        update_str = ((new_value or blank_str) + space_str)[:25] + old_value_str
                                        logfile.append(caption_txt + update_str)

                        # add field_dict to update_dict
                        update_dict[field] = field_dict

                # dont save data when it is a test run
                if not is_test and save_instance:
                    student.save(request=request)
                    update_dict['id']['pk'] = student.pk
                    update_dict['id']['ppk'] = student.company.pk
                    # wagerate wagecode
                    # priceratejson additionjson
                    try:
                        student.save(request=request)
                        update_dict['id']['pk'] = student.pk
                        update_dict['id']['ppk'] = student.company.pk
                    except:
                        # - give error msg when creating student failed
                        error_str = str(_("An error occurred. The student data is not saved."))
                        logfile.append(" ".join((code_text, error_str)))
                        update_dict['row_error'] = error_str

    return update_dict


# --- end of upload_student


# //////////////////////////////////////////////////////////////////


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
                school = sch_mod.School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
                department = sch_mod.Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()

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

                setting = sch_mod.Schoolsetting.objects.filter(
                    schoolbase=request.user.schoolbase,
                    key_str=c.KEY_STUDENT_MAPPED_COLDEFS
                ).first()
                if setting is None:
                    setting = sch_mod.Schoolsetting(
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
class StudentstudentDownloadView(View):  # PR2019-02-08

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= StudentstudentDownloadView ============= ')
        # logger.debug('request.POST' + str(request.POST) )

        params = {}
        if request.user is not None and request.user.examyear is not None and \
                request.user.schoolbase is not None and request.user.depbase is not None:
            school = sch_mod.School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
            dep = sch_mod.Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()
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
                            # make list of all Students from this department and examyear (included in dep)
                            schemeitems = Schemeitem.get_schemeitem_list(scheme)
                            params.update({'schemeitems': schemeitems})
                            logger.debug('schemeitems: ' + str(schemeitems))

                            studentstudents = Studentstudent.get_studsubj_list(student)
                            params.update({'studentstudents': studentstudents})
                            logger.debug('studentstudents: ' + str(studentstudents))

        json_dumps_params = json.dumps(params)

        return HttpResponse(json_dumps_params)


@method_decorator([login_required], name='dispatch')
class StudentstudentUploadView(View):  # PR2019-02-09

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= StudentstudentUploadView ============= ')
        # stud_ssi =  {'mode': 'c', 'stud_id': '412', 'ssi_id': '1597'}

        params = {}
        if request.user is not None and request.user.examyear is not None and request.user.schoolbase is not None:
            # get sybject scheme item from  request.POST
            studentstudents = json.loads(request.POST['studentstudents'])
            logger.debug("studentstudents: " + str(studentstudents))

            for item in studentstudents:
                # convert values

                # studsubj = {'mode': 'c', 'studsubj_id': 'ssiid_1592', 'ssi_id': '1592', 'subj_id': '319',
                # 'subj_name': 'Nederlandse taal en literatuur', 'sjtp_id': '10', 'sjtp_name': 'Gemeensch.',
                # 'sjtp_one': 0, 'sequence': 11001, 'extra_nocount': 0, 'extra_counts': 0, 'choice_combi': 0,
                # 'pws_title': '', 'pws_students': ''}

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
                        # create new studentstudent
                        studsubj = Studentstudent(
                            student=student,
                            schemeitem=schemeitem,
                        )
                        # TODO add extra_nocount etc

                        studsubj.save(request=self.request)
                        logger.debug("new studentstudent: " + str(studsubj))

                    else:
                        # lookup studentstudent
                        studsubj_id = int(item.get('studsubj_id', '0'))
                        studsubj = Studentstudent.objects.filter(id=studsubj_id).first()


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
                                studsubj.pws_students = item.get('pws_students', '')

                                # logger.debug("extra_nocount: " + str(extra_nocount) + ' type: ' + str(type(extra_nocount)))
                                # logger.debug("extra_counts: " + str(extra_counts) + ' type: ' + str(type(extra_counts)))
                                # logger.debug("choice_combi: " + str(choice_combi) + ' type: ' + str(type(choice_combi)))
                                # logger.debug("pws_title: " + str(pws_title) + ' type: ' + str(type(pws_title)))
                                # logger.debug("pws_students: " + str(pws_students) + ' type: ' + str(type(pws_students)))


                                # update mode or create mode
                                studsubj.save(request=self.request)

                                logger.debug("studentstudent: " + str(studsubj))

                                record_saved = True

                    # renew list of all Students from this department and examyear (included in dep)
                    studentstudents = Studentstudent.get_studsubj_list(student)
                    params.update({'studentstudents': studentstudents})

                    # make list of all Students from this department and examyear (included in dep)
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
class StudentstudentFormsetView(ListView):  # PR2018-11-29
    model = Studentstudent
    form_class = StudentstudentFormset
    heading_message = 'Formset Demo'
    template_name = 'studentstudent_formset.html'
    context_object_name = 'studentstudent'

    def get(self, request, *args, **kwargs):
        formset = StudentstudentFormset() #(request=request)
        _param = f.get_headerbar_param(request, {
            'formset': formset,
            'heading': self.heading_message,
            'display_school': True,
            'display_dep': True})
        return render(request, self.template_name, _param)

    def post(self, request, *args, **kwargs):
        formset = StudentstudentFormset(data=request.POST, files=request.FILES)
        logger.debug('StudentstudentFormsetView post request.POST: ' + str(self.request.POST) + ' type: ' + str(type(self.request.POST)))

        if formset.is_valid():
            logger.debug('StudentstudentFormsetView post formset.is_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))

            instances = formset.save(commit=False)
            for instance in instances:
                instance.save(request=self.request)

            logger.debug('StudentstudentFormsetView post formset.is_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))

            return render(request, 'country_formset.html', {'formset': formset})
        else:
            logger.debug('StudentstudentFormsetView post formset.is_NOT_valid: ' + str(formset.is_valid) + ' type: ' + str(type(formset.is_valid)))
            return render(request, self.template_name, {'formset': formset})
"""

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
            setting = sch_mod.Schoolsetting.objects.filter(
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