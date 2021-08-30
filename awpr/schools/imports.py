# PR2020-12-06

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse

from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import activate, pgettext_lazy, ugettext_lazy as _

from django.views.generic import View

from accounts import models as acc_mod
from accounts import views as acc_view
from awpr import constants as c
from awpr import functions as af
from awpr import settings as s
from awpr import downloads as dl
from awpr import validators as awpr_val

from schools import models as sch_mod
from students import models as stud_mod
from students import validators as stud_val
from students import views as stud_view
from subjects import models as subj_mod
from subjects import views as subj_view

import json
import logging

logger = logging.getLogger(__name__)


@method_decorator([login_required], name='dispatch')
class UploadImportSettingView(View):   # PR2020-12-05
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request, *args, **kwargs):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= UploadImportSettingView ============= ')

        updated_stored_setting = {}
        has_permit = False
        if request.user is not None and request.user.schoolbase is not None:
            # TODO has_permit = (request.user.is_perm_hrman)
            has_permit = True
        if has_permit:
            if request.POST['upload']:
                new_setting_dict = json.loads(request.POST['upload'])

                if logging_on:
                    logger.debug('new_setting_dict' + str(new_setting_dict))

                # new_setting_dict{'importtable': 'import_student', 'sel_schoolbase_pk': 16, 'sel_examyear_pk': 6,
                # 'worksheetname': 'Compleetlijst', 'noheader': False}
                # 'sector': {'CM': 4, 'EM': 5}}

                """
                new_setting_dict{
                'importtable': 'import_permit', 
                'sel_examyear_pk': None, 
                'sel_schoolbase_pk': None, 
                'sel_depbase_pk': None, 
                'worksheetname': 'Permits', 
                'noheader': False}
                """

                if new_setting_dict:
                    # setting_keys are: 'import_student', import_studsubj
                    # {importtable: "import_studsubj", ...}
                    setting_key = new_setting_dict.get('importtable')

                    sel_examyear_pk = new_setting_dict.get('sel_examyear_pk')
                    sel_examyear = sch_mod.Examyear.objects.get_or_none(pk=sel_examyear_pk)

                    sel_schoolbase_pk = new_setting_dict.get('sel_schoolbase_pk')
                    sel_schoolbase = sch_mod.Schoolbase.objects.get_or_none(pk=sel_schoolbase_pk)

                    sel_depbase_pk = new_setting_dict.get('sel_depbase_pk')
                    sel_depbase = sch_mod.Schoolbase.objects.get_or_none(pk=sel_depbase_pk)

                    if logging_on:
                        logger.debug('setting_key: ' + str(setting_key))
                        logger.debug('sel_schoolbase: ' + str(sel_schoolbase))

                    if setting_key and sel_schoolbase:
                        stored_setting_dict = sel_schoolbase.get_schoolsetting_dict(setting_key)
                        if logging_on:
                            logger.debug('stored_setting_dict' + str(stored_setting_dict))

                        new_stored_setting = {}
                        # note: fields 'department', 'level', 'sector', 'subject', 'subjecttype' contain dict with mapped values
                        import_keys = ('worksheetname', 'noheader', 'coldef', 'department', 'level', 'sector', 'subject', 'subjecttype')
                        for import_key in import_keys:
                            new_setting_value = new_setting_dict.get(import_key)

                            if new_setting_value is None and stored_setting_dict:
                                new_setting_value = stored_setting_dict.get(import_key)

                            if import_key is 'noheader' and  new_setting_value is None:
                                new_setting_value = False

                            if new_setting_value is not None:
                                new_stored_setting[import_key] = new_setting_value

                        if logging_on:
                            logger.debug('new_stored_setting: ' + str(new_stored_setting))
                        if new_stored_setting:
                            sel_schoolbase.set_schoolsetting_dict(setting_key, new_stored_setting)

        # get updated stored_setting from database, return to page to update mimp_stored
                    # NIU: mimp_stored is updated in client js
                    #request_item_setting = {'setting_key': setting_key}
                    #updated_stored_setting['schoolsetting_dict'] = sf.get_schoolsetting(
                        #request_item_setting, sel_examyear, sel_schoolbase, sel_depbase)

        return HttpResponse(json.dumps(updated_stored_setting, cls=af.LazyEncoder))
# - end of UploadImportSettingView


@method_decorator([login_required], name='dispatch')
class UploadImportDataView(View):  # PR2020-12-05 PR2021-02-23 PR2021-07-17
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request, *args, **kwargs):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UploadImportDataView ============= ')

        update_dict = {}

        if request.user and request.user.country and request.user.schoolbase:

            if request.POST['upload']:
                upload_dict = json.loads(request.POST['upload'])

                importtable = upload_dict.get('importtable')
                page = importtable.replace('import', 'page')

                permit_list, requsr_usergroups_listNIU = acc_view.get_userpermit_list(page, request.user)

            # to prevent you from locking out when no permits yet
                if request.user.role == c.ROLE_128_SYSTEM:
                    if 'permit_crud' not in permit_list:
                        permit_list.append('permit_crud')

                has_permit = 'permit_crud' in permit_list

                if logging_on:
                    logger.debug('request.user.role: ' + str(request.user.role) + ' ' + str(type(request.user.role)))
                    logger.debug('permit_list: ' + str(permit_list) + ' ' + str(type(permit_list)))
                    logger.debug('has_permit: ' + str(has_permit) + ' ' + str(type(has_permit)))

                if not has_permit:
                    err_html = _("You don't have permission to perform this action.")
                    update_dict['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))
                else:

        # - Reset language
                    # PR2019-03-15 Debug: language gets lost, get request.user.lang again
                    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                    activate(user_lang)

                    #if importtable == 'import_student':
                    #    update_dict = import_students(upload_dict, user_lang, request)
                   # elif importtable == 'import_studsubj':
                   #     update_dict = import_studentsubjects(upload_dict, user_lang, logging_on, request)
                   # elif importtable == 'import_permit':
                   #     update_dict = import_permits(upload_dict, user_lang, logging_on, request)

        if logging_on:
            logger.debug('update_dict: ' + str(update_dict) + ' ' + str(type(update_dict)))

        return HttpResponse(json.dumps(update_dict, cls=af.LazyEncoder))
# - end of UploadImportDataView


@method_decorator([login_required], name='dispatch')
class UploadImportStudentsubjectView(View):  # PR2021-07-20
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request, *args, **kwargs):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UploadImportStudentsubjectView ============= ')

        update_dict = {}

        if request.user and request.user.country and request.user.schoolbase:

            if request.POST['upload']:
                upload_dict = json.loads(request.POST['upload'])

                importtable = upload_dict.get('importtable')
                page = importtable.replace('import', 'page')

                permit_list, requsr_usergroups_listNIU = acc_view.get_userpermit_list(page, request.user)

            # to prevent you from locking out when no permits yet
                if request.user.role == c.ROLE_128_SYSTEM:
                    if 'permit_crud' not in permit_list:
                        permit_list.append('permit_crud')

                has_permit = 'permit_crud' in permit_list

                if logging_on:
                    logger.debug('importtable: ' + str(importtable) + ' ' + str(type(importtable)))
                    logger.debug('page: ' + str(page) + ' ' + str(type(page)))
                    logger.debug('request.user.role: ' + str(request.user.role) + ' ' + str(type(request.user.role)))
                    logger.debug('permit_list: ' + str(permit_list) + ' ' + str(type(permit_list)))
                    logger.debug('has_permit: ' + str(has_permit) + ' ' + str(type(has_permit)))

                if not has_permit:
                    err_html = _("You don't have permission to perform this action.")
                    update_dict['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))
                else:

        # - Reset language
                    # PR2019-03-15 Debug: language gets lost, get request.user.lang again
                    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                    activate(user_lang)

        # - get selected examyear, school and department from usersettings
                    sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                        dl.get_selected_ey_school_dep_from_usersetting(request)

        # - get info from upload_dict
                    is_test = upload_dict.get('test', False)
                    lookup_field = upload_dict.get('lookup_field')
                    data_list = upload_dict.get('data_list')
                    filename = upload_dict.get('filename', '')

                    if logging_on:
                        logger.debug('is_test: ' + str(is_test))
                        logger.debug('lookup_field: ' + str(lookup_field))
                        logger.debug('filename: ' + str(filename))
                        if data_list:
                            logger.debug('length data_list: ' + str(len(data_list)))

                    updated_rows = []
                    log_list = []

                    count_total, count_existing, count_new, count_error, count_bisexam = 0, 0, 0, 0, 0

                    if lookup_field and data_list and sel_school and sel_department:

        # - create log_list
                        today_dte = af.get_today_dateobj()
                        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

                        school_name = sel_school.base.code + ' ' + sel_school.name
                        log_list = [c.STRING_DOUBLELINE_80,
                                    str(_('Upload subjects of candidates')) + ' ' + str(_('date')) + ': ' + str(today_formatted),
                                    c.STRING_DOUBLELINE_80]

                        log_list.append(c.STRING_SPACE_05 + str(_("School    : %(name)s") % {'name': school_name}))
                        log_list.append(c.STRING_SPACE_05 + str(_("Department: %(dep)s") % {'dep': sel_department.name}))
                        log_list.append(c.STRING_SPACE_05 + str(_("Exam year : %(ey)s") % {'ey': str(sel_examyear.code)}))
                        log_list.append(c.STRING_SPACE_05 + str(_("File name : %(file)s") % {'file': filename}))

                        if is_test:
                            info_txt = str(_("This is a test. The subjects are not saved."))
                            log_list.append(c.STRING_SPACE_05 + info_txt)
                        else:
                            info_txt = str(_("The subjects are saved."))
                            log_list.append(c.STRING_SPACE_05 + info_txt)

                        log_list.append(c.STRING_SPACE_05)

        # - get list of idnumbers, that occur multiple times in data_list
                        double_entrieslist = stud_val.get_double_entrieslist_from_uploadfile(data_list)

        # - get a dict per scheme of subjects with the lowest sequence
                        # mapped_subjectbase_pk_dict = { scheme_id: { subjectbase_pk: [schemeitem_id, subject_code] }, ... }
                        # mapped_subjectbase_pk_dict: {249: {140: [2070, 'sp'], 133: [2054, 'ne'],
                        mapped_subjectbase_pk_dict = map_subjectbase_pk_to_schemeitem_pk(sel_school, sel_department)

        # - get a dict with key student_pk and as value a dict with key: subjbase_pk and value: subject_code
                        # output: subjbase_pk_list_per_student: { student_id: {subjectbase_pk: subject_code, ...}, ... }
                        #subjbase_pk_list_per_student = get_subjbase_pk_list_per_student(sel_school, sel_department)
                        # output: subjbase_pk_list_per_student: { idnumber: {student_id:  ,  subjectbase_pk: subject_code, ...}, ... }
                        subjbase_pk_list_per_student = get_subjbase_pk_list_per_student_NEW(sel_school, sel_department, double_entrieslist)
                        if logging_on:
                            logger.debug('school_name: ' + str(school_name))
                            logger.debug('double_entrieslist: ' + str(double_entrieslist))
                            #logger.debug('mapped_subjectbase_pk_dict: ' + str(mapped_subjectbase_pk_dict))
                            logger.debug('subjbase_pk_list_per_student: ' + str(subjbase_pk_list_per_student))
                            logger.debug('++++++++++++++++++++++++++++++++++++++++++++++++ ')

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++ loop through data_list

                        for data_dict in data_list:
                            # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html
                            # for key, val in student.items():
                            # #logger.debug( str(key) +': ' + val + '" found in "' + str(student) + '"')

    # skip empty rows
                            has_values = False
                            if data_dict.get(lookup_field):
                                has_values = True
                            elif data_dict.get('subjects'):
                                has_values = True

                            if has_values:

    # - upload studentsubject
                                studsubj_rows, is_existing, is_new_student, has_error = \
                                    upload_studentsubject_from_datalist(
                                        data_dict=data_dict,
                                        school=sel_school,
                                        department=sel_department,
                                        is_test=is_test,
                                        double_entrieslist=double_entrieslist,
                                        mapped_subjectbase_pk_dict=mapped_subjectbase_pk_dict,
                                        subjbase_pk_list_per_student=subjbase_pk_list_per_student,
                                        log_list=log_list,
                                        request=request
                                    )

                                if not is_test and studsubj_rows:
                                    updated_rows.extend(studsubj_rows)

                                count_total += 1
                                if is_existing:
                                    count_existing += 1
                                if is_new_student:
                                    count_new += 1
                                if has_error:
                                    count_error += 1
                                # if has_error:
                                #   count_bisexam += 1
# +++++ end of loop through data_list
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # - return html with number of students, existing, new and erros
                    update_dict = { 'is_test': is_test,
                                    'table': 'studsubj',
                                    'result': crate_result_html(is_test, count_total, count_existing, count_new, count_error),
                                    'log_list': log_list}
                    # was: if not is_test and updated_rows:
                    #    update_dict['updated_studsubj_rows'] = updated_rows
                    if not is_test:
                        update_dict['updated_studsubj_rows'] = "tobedownloaded"

        return HttpResponse(json.dumps(update_dict, cls=af.LazyEncoder))
# - end of UploadImportStudentsubjectView


@method_decorator([login_required], name='dispatch')
class UploadImportStudentView(View):  # PR2020-12-05 PR2021-02-23  PR2021-07-17
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request, *args, **kwargs):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UploadImportStudentView ============= ')

        update_dict = {}

        if request.user and request.user.country and request.user.schoolbase:

            if request.POST['upload']:
                upload_dict = json.loads(request.POST['upload'])
                # upload_dict: {'sel_examyear_pk': 58, 'sel_schoolbase_pk': 11, 'sel_depbase_pk': 1, 'sel_depbase_code': 'Vsbo', 'sel_school_abbrev': '---',
                # 'importtable': 'import_student', 'filename': 'StJozef_2021_Kandidaten.xlsx',
                # 'awpColdef_list': ['examnumber', 'lastname', 'firstname', 'prefix', 'gender', 'idnumber', 'birthdate', 'birthcountry', 'birthcity', 'classname', 'level', 'sector'], 'test': True, 'data_list': [{'

                importtable = upload_dict.get('importtable')
                page = importtable.replace('import', 'page')

                permit_list, requsr_usergroups_listNIU = acc_view.get_userpermit_list(page, request.user)

            # to prevent you from locking out when no permits yet
                if request.user.role == c.ROLE_128_SYSTEM:
                    if 'permit_crud' not in permit_list:
                        permit_list.append('permit_crud')

                has_permit = 'permit_crud' in permit_list

                if logging_on:
                    logger.debug('request.user.role: ' + str(request.user.role))
                    logger.debug('permit_list: ' + str(permit_list))
                    logger.debug('has_permit: ' + str(has_permit))
                    #logger.debug('upload_dict: ' + str(upload_dict))

                if not has_permit:
                    err_html = _("You don't have permission to perform this action.")
                    update_dict['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))
                else:

        # - Reset language
                    # PR2019-03-15 Debug: language gets lost, get request.user.lang again
                    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                    activate(user_lang)

        # - get selected examyear, school and department from usersettings
                    sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                        dl.get_selected_ey_school_dep_from_usersetting(request)

        # - get info from upload_dict
                    is_test = upload_dict.get('test', False)
                    awpColdef_list = upload_dict.get('awpColdef_list')
                    data_list = upload_dict.get('data_list')
                    filename = upload_dict.get('filename', '')

                    if logging_on:
                        logger.debug('is_test: ' + str(is_test))
                        logger.debug('awpColdef_list: ' + str(awpColdef_list))
                        logger.debug('len(data_list: ' + str(len(data_list)))
                        logger.debug('sel_school: ' + str(sel_school))
                        logger.debug('sel_department: ' + str(sel_department))

                    updated_rows, log_list = [], []
                    count_total, count_existing, count_new, count_error, count_bisexam = 0, 0, 0, 0, 0

                    if awpColdef_list and data_list and sel_school and sel_department:

        # - create log_list
                        today_dte = af.get_today_dateobj()
                        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

                        school_name = sel_school.base.code + ' ' + sel_school.name
                        log_list = [c.STRING_DOUBLELINE_80,
                                    str(_('Upload candidates')) + ' ' + str(_('date')) + ': ' + str(today_formatted),
                                    c.STRING_DOUBLELINE_80]

                        log_list.append(c.STRING_SPACE_05 + str(_("School    : %(name)s") % {'name': school_name}))
                        log_list.append(c.STRING_SPACE_05 + str(_("Department: %(dep)s") % {'dep': sel_department.name}))
                        log_list.append(c.STRING_SPACE_05 + str(_("Exam year : %(ey)s") % {'ey': str(sel_examyear.code)}))
                        log_list.append(c.STRING_SPACE_05 + str(_("File name : %(file)s") % {'file': filename}))

                        if is_test:
                            info_txt = str(_("This is a test. The candidate data are not saved."))
                            log_list.append(c.STRING_SPACE_05 + info_txt)
                        else:
                            info_txt = str(_("The candidate data are saved."))
                            log_list.append(c.STRING_SPACE_05 + info_txt)

                        log_list.append(c.STRING_SPACE_05)

        # - get double_entrieslist, a list of idnumbers/lastname/firstname that occur multiple times in data_list
                        double_entrieslist = stud_val.get_double_entrieslist_from_uploadfile(data_list)

        # - get id_number_list, the list of idnumbers of this school
                        # new idnumbers will be added to the idnumber_list in upload_student_from_datalist
                        idnumber_list = stud_val.get_idnumberlist_from_database(sel_school)

        # - get examnumber_list and id_number_list, the list of examnumbers of this department
                        # new examnumbers will be added to the examnumber_list in upload_student_from_datalist
                        examnumber_list = stud_val.get_examnumberlist_from_database(sel_school, sel_department)

                        if logging_on:
                            logger.debug('school_name: ' + str(school_name))
                            logger.debug('double_entrieslist: ' + str(double_entrieslist))
                            logger.debug('idnumber_list: ' + str(idnumber_list))
                            logger.debug('examnumber_list: ' + str(examnumber_list))
                            logger.debug('awpColdef_list: ' + str(awpColdef_list))

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++ loop through data_list

                        for data_dict in data_list:
                            # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html
                            # for key, val in student.items():
                            # #logger.debug( str(key) +': ' + val + '" found in "' + str(student) + '"')

    # skip empty rows
                            has_values = False
                            for field in awpColdef_list:
                                value = data_dict.get(field)
                                if value is not None:
                                    has_values = True

                            if has_values:
    # - upload student
                                student_dict, is_existing, is_new_student, has_error, might_be_bisexam = \
                                    upload_student_from_datalist(
                                        data_dict=data_dict,
                                        school=sel_school,
                                        department=sel_department,
                                        is_test=is_test,
                                        double_entrieslist=double_entrieslist,
                                        idnumber_list=idnumber_list,
                                        examnumber_list=examnumber_list,
                                        log_list=log_list,
                                        request=request
                                    )
                                if not is_test and student_dict:
                                    updated_rows.append(student_dict)

                                count_total += 1
                                if is_existing:
                                    count_existing += 1
                                if is_new_student:
                                    count_new += 1
                                if has_error:
                                    count_error += 1
                                # if has_error:
                                #   count_bisexam += 1
# +++++ end of loop through data_list
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # - return html with number of students, existing, new and erros
                    update_dict = { 'is_test': is_test,
                                    'table': 'student',
                                    'result': crate_result_html(is_test, count_total, count_existing, count_new, count_error),
                                    'log_list': log_list}

                    if not is_test and updated_rows:
                        update_dict['updated_student_rows'] = updated_rows

        return HttpResponse(json.dumps(update_dict, cls=af.LazyEncoder))
# - end of UploadImportStudentView


# ========  upload_student_from_datalist  ======= # PR2019-12-17 PR2020-06-03 PR2021-06-19
def upload_student_from_datalist(data_dict, school, department, is_test, double_entrieslist, idnumber_list, examnumber_list, log_list, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- upload_student_from_datalist  --------------------')
        logger.debug('data_dict: ' + str(data_dict))
        logger.debug('is_test: ' + str(is_test))

# - required fields are: base, school, department, lastname, firstname
    # the lookup field 'idnumber' is not required in model, but is required for upload

# awpColdef_list:  idnumber,  lastname, firstname, prefix, gender, examnumber, birthdate, birthcountry, birthcity
#                   classname, (iseveningstudent), bis_exam, department, level, sector, profiel

    error_list = []
    is_existing_student, is_new_student, has_error, might_be_bisexam = False, False, False, False

# - get variables from data_dict
    id_number = data_dict.get('idnumber', '')
    last_name = data_dict.get('lastname', '')
    first_name = data_dict.get('firstname', '')
    prefix = data_dict.get('prefix', '')

# - base_pk only has value when user has ticked off 'same_student' after test_upload
    # insteaad of creating a new student_base, the pase_pk will be used and 'islinked' will be set True
    # base_pk = data_dict.get('base_pk')

    idnumber_nodots_stripped = stud_val.get_idnumber_nodots_stripped(id_number)
    lastname_stripped = last_name.strip() if last_name else ''
    firstname_stripped = first_name.strip() if first_name else ''
    prefix_stripped = prefix.strip() if prefix else ''
    full_name = stud_val.get_prefix_lastname_comma_firstname(lastname_stripped, firstname_stripped, prefix_stripped)

    if logging_on:
        logger.debug('idnumber_nodots_stripped: ' + str(idnumber_nodots_stripped))
        logger.debug('full_name: ' + str(full_name))

# - create student_dict
    student_dict = {}

# - check for double occurrence in upload file
    error_idnumber = stud_val.validate_double_entries_in_uploadfile(idnumber_nodots_stripped, double_entrieslist, error_list)
    if not error_idnumber:

# - validate length of name and idnumber
        error_idnumber = stud_val.validate_name_idnumber_length(
            idnumber_nodots_stripped, lastname_stripped, firstname_stripped, prefix_stripped, error_list)
    if logging_on:
        logger.debug('error_list: ' + str(error_list))

    student = None
    is_new_student, error_create, changes_are_saved, error_save, field_error = False, False, False, False, False
    if not error_idnumber:

# - replace idnumber by idnumber_nodots_stripped
        data_dict['idnumber'] = idnumber_nodots_stripped

# - lookup student in database
       # either student, not_found or error_idnumber is trueish
        student, not_found, error_idnumber = \
            stud_val.lookup_student_by_idnumber(
                school=school,
                department=department,
                id_number=id_number,
                upload_fullname=full_name,
                is_test=is_test,
                is_import=True,
                error_list=error_list,
                notfound_is_error=False
            )
        if logging_on:
            student_pk = student.pk if student else 'None'
            logger.debug('..........student.pk: ' + str(student_pk))
            logger.debug('student: ' + str(student))
            logger.debug('error_idnumber: ' + str(error_idnumber))

    if not error_idnumber:
        messagesNIU = []

# - check if birthdate is a valid date
        # birthdate has format of excel ordinal
        birthdate_ordinal = data_dict.get('birthdate')
        if logging_on:
            logger.debug('birthdate_ordinal: ' + str(birthdate_ordinal) + ' ' + str(type(birthdate_ordinal)))

        birthdate_iso = af.get_birthdateiso_from_excel_ordinal(birthdate_ordinal, error_list)
        if birthdate_iso is None:
            birthdate_iso = af.get_birthdateiso_from_idnumber(idnumber_nodots_stripped)
            #if birthdate_iso:
            #    error_list.append(str(_("AWP has calculated the birthdate from the ID-number.")))

    # - replace birthdate with birthdate_iso in data_dict
        # PR2021-08-12 debug: must also replace 0 with None, otherwise error occurs in update_student_instance
        # data_dict['birthdate'] = birthdate_iso
        data_dict['birthdate'] = birthdate_iso

        if logging_on:
            logger.debug('birthdate_iso: ' + str(birthdate_iso) + ' ' + str(type(birthdate_iso)))

        if student:
            is_existing_student = True
            student_dict['student_pk'] = student.pk
        else:

# +++ create new student when student not found in database
            #base = None
            #is_linked = False

            # check if student exists in other year is replaced to exemption.
            # here it is not in use
            # base_pk only has vaue when user has ticked of 'same_student' after test_upload
            # instead of creating a new student_base, the pase_pk will be used and 'islinked' will be set True

            #if base_pk:
            #    base = stud_mod.Studentbase.objects.filter( pk=base_pk,country=request.user.country)

    # - create base record. Don't save when is_test
            # skip_save = is_test
            # note: error_list is list of strings,
            #  messages is list of dicts with format: {'field': fldName, header': header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html}

            upload_dict = {'idnumber': idnumber_nodots_stripped, 'lastname': lastname_stripped, 'firstname': firstname_stripped}

    # - create student record
            student = stud_view.create_student(school, department, upload_dict, messagesNIU, error_list, request, is_test) # skip_save = is_test
            if logging_on:
                student_pk = student.pk if student else 'None'
                logger.debug('student:    ' + str(student))
                logger.debug('student_pk: ' + str(student_pk))
                logger.debug('error_list: ' + str(error_list))

            if student is None:
    # - give error msg when creating student failed - is already done in create_student
                error_create = True

            else:
                is_new_student = True

                student_dict['created'] = True

# -- check for doubles, only when is new student
                double_dict = validate_students_doubles(request.user.country, idnumber_nodots_stripped,
                                                lastname_stripped,
                                                firstname_stripped, birthdate_iso)
                #if logging_on:
                #    logger.debug('double_dict: ' + str(double_dict))
                #if double_dict:
                #    might_be_bisexam = True
                #    bisexam_dict[row_index] = double_dict
                #    if logging_on:
                #        logger.debug('double_dict: ' + str(double_dict))
                #        #logger.debug('bisexam_dict: ' + str(bisexam_dict))

# - update fields, both in new and existing students
        if student:
            data_dict.pop('rowindex')
            changes_are_saved, error_save, field_error = stud_view.update_student_instance(student, data_dict, idnumber_list, examnumber_list, messagesNIU, error_list, request, is_test)
            setting_dict = {
                'sel_examyear_pk': school.examyear.pk,
                'sel_schoolbase_pk': school.base_id,
                'sel_depbase_pk': department.base_id}
            append_dict = {'created': True} if is_new_student else {}
            rows = stud_view.create_student_rows(
                setting_dict=setting_dict,
                append_dict=append_dict,
                student_pk=student.pk)
            if rows and rows[0]:
                student_dict = rows[0]

        if logging_on:
            logger.debug('changes_are_saved: ' + str(changes_are_saved))
            logger.debug('field_error: ' + str(field_error))
            logger.debug('error_list: ' + str(error_list))

# create log for this student

    student_header = ''.join(((idnumber_nodots_stripped + c.STRING_SPACE_10)[:10], c.STRING_SPACE_05, full_name))
    if error_idnumber or error_create:
        student_header += str(_(' will be skipped.')) if is_test else str(_(' is skipped.'))
    elif is_new_student:
        student_header += str(_(' will be added.')) if is_test else str(_(' is added.'))
    elif is_existing_student:
        student_header += str(_(' already exists.'))
    log_list.append(student_header)
    if error_list:
        for err in error_list:
            if err:
                log_list.append('- '.join((c.STRING_SPACE_15, err)))
    if changes_are_saved:
        if not is_new_student:
            changed_txt = _('The changes will be saved.') if is_test else _('The changes have been saved.')
            log_list.append('- '.join((c.STRING_SPACE_15, str(changed_txt))))
        if field_error:
            changed_txt = _('Some fields have errors. They will not be saved.') \
                if is_test else _('Some fields have errors. They have not been saved.')
            log_list.append('- '.join((c.STRING_SPACE_15, str(changed_txt))))

    if error_save:
        changed_txt = _('The changes will not be saved.') if is_test else _('The changes have not been saved.')
        log_list.append('- '.join((c.STRING_SPACE_15, str(changed_txt))))

    return student_dict, is_existing_student, is_new_student, has_error, might_be_bisexam
# --- end of upload_student_from_datalist


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# ========  update_student_fields  ======= # PR2019-12-17 PR2020-06-03 PR2021-06-19
def update_student_fields(data_dict, awpColdef_list, examyear, school, department, is_test, dateformat,
                          student, is_existing_student,  log_list, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- upload_student  --------------------')
        logger.debug('data_dict: ' + str(data_dict))

    update_dict = {}
    save_instance = False
    if student:
        # add 'id' at the end, after saving the student. Pk doent have value until instance is saved
        # update_dict['id']['pk'] = student.pk
        # update_dict['id']['ppk'] = student.company.pk
        # if is_created_student:
        #    update_dict['id']['created'] = True

        # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
        # solved bij wrapping with str()

        blank_str = '<' + str(_('blank')) + '>'
        was_str = str(_('was') + ': ')

        for field in awpColdef_list:
            # --- get field_dict from  upload_dict  if it exists

            if logging_on:
                logger.debug('---------- field: ' + str(field))

            field_dict = {}
            field_caption = af.get_dict_value(c.CAPTIONS, ('student', field), '')
            caption_txt = (c.STRING_SPACE_05 + field_caption + c.STRING_SPACE_30)[:30]
            # text fields
            if field in ('lastname', 'firstname', 'prefix', 'gender', 'idnumber', 'birthcountry', 'birthcity',
                         'classname', 'examnumber', 'regnumber', 'diplomanumber', 'gradelistnumber'):
                new_value = data_dict.get(field)
                max_len = c.MAX_LEN_DICT_STUDENT.get(field)

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
                        log_list.append(caption_txt + (new_value or blank_str))
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
                            update_str = ((new_value or blank_str) + c.STRING_SPACE_30)[:25] + old_value_str
                            log_list.append(caption_txt + update_str)

            ######################################
            elif field == 'birthdate':
                # - get new value, convert to date, using dateformat
                new_value = data_dict.get(field)
                new_date_dte = None
                # - get saved_value
                saved_dte = getattr(student, field)
                saved_date_iso = None
                if saved_dte:
                    saved_date_iso = saved_dte.isoformat()
                old_value_str = was_str + (saved_date_iso or blank_str)

                # - validate new date
                new_date_dte, msg_err = None, None
                if new_value and dateformat:
                    date_iso = af.get_dateISO_from_string(new_value, dateformat)
                    new_date_dte = af.get_date_from_ISO(
                        date_iso)  # datefirst_dte: 1900-01-01 <class 'datetime.date'>
                    if new_date_dte is None:
                        msg_err = str(_("'%(val)s' is not a valid date.") % {'val': new_value})
                        if logging_on:
                            logger.debug('msg_err' + str(msg_err))
                if msg_err:
                    field_dict['error'] = msg_err
                    if is_existing_student:
                        field_dict['info'] = field_caption + ' ' + old_value_str
                        update_str = (msg_err + c.STRING_SPACE_30)[:25] + old_value_str
                        log_list.append(caption_txt + update_str)
                else:
                    new_date_iso = None
                    if new_date_dte:
                        new_date_iso = new_date_dte.isoformat()
                    field_dict['value'] = new_date_iso
                    if not is_existing_student:
                        log_list.append(caption_txt + (new_date_iso or blank_str))
                    if new_date_dte != saved_dte:
                        # put new value in student instance
                        setattr(student, field, new_date_dte)
                        field_dict['updated'] = True
                        save_instance = True
                        # create field_dict and log
                        if is_existing_student:
                            field_dict['info'] = field_caption + ' ' + old_value_str
                            update_str = ((new_date_iso or blank_str) + c.STRING_SPACE_30)[:25] + old_value_str
                            log_list.append(caption_txt + update_str)

            elif field in ('level', 'sector', 'profiel'):
                # 'profiel' is not a database field, will be stored in 'sector'
                db_field = 'sector' if field == 'profiel' else field
                new_base_pk = data_dict.get(field)
                saved_instance = getattr(student, db_field)

                # logger.debug('field: ' + str(field))
                # logger.debug('new_base_pk: ' + str(new_base_pk))
                # logger.debug('saved_instance: ' + str(saved_instance))

                # check if dep / lvl / sct exists
                new_instance = None
                if db_field == 'level':
                    new_instance = subj_mod.Level.objects.get_or_none(base_id=new_base_pk, examyear=examyear)
                elif db_field == 'sector':
                    new_instance = subj_mod.Sector.objects.get_or_none(base_id=new_base_pk, examyear=examyear)
                # logger.debug('new_instance: ' + str(new_instance))

                if new_instance is None:
                    save_new_instance = (saved_instance is not None)
                else:
                    save_new_instance = (saved_instance is None) or (new_instance != saved_instance)
                # logger.debug('save_new_lvl_sct: ' + str(save_new_instance))

                if save_new_instance:
                    setattr(student, db_field, new_instance)
                    field_dict['updated'] = True
                    save_instance = True
                    new_abbrev = new_instance.abbrev if new_instance else None
                    # logger.debug('new_abbrev: ' + str(new_abbrev))

                    if field == 'level':
                        caption_txt = (c.STRING_SPACE_05 + str(_('leerweg')) + c.STRING_SPACE_30)[:30]
                    elif field == 'sector':
                        caption_txt = (c.STRING_SPACE_05 + str(_('sector')) + c.STRING_SPACE_30)[:30]
                    elif field == 'profiel':
                        caption_txt = (c.STRING_SPACE_05 + str(_('profiel')) + c.STRING_SPACE_30)[:30]

                    if not is_existing_student:
                        log_list.append(caption_txt + (new_abbrev or blank_str))
                        # logger.debug('log_list.append: ' + str(caption_txt + (new_abbrev or blank_str)))
                    else:
                        saved_abbrev = saved_instance.abbrev if saved_instance else None
                        old_abbrev_str = was_str + (saved_abbrev or blank_str)
                        # logger.debug('old_abbrev_str: ' + str(old_abbrev_str))
                        field_dict['info'] = field_caption + ' ' + old_abbrev_str
                        update_str = ((new_abbrev or blank_str) + c.STRING_SPACE_30)[:25] + old_abbrev_str
                        log_list.append(caption_txt + update_str)
                        # logger.debug('log_list.append: ' + str(caption_txt + update_str))
            # add field_dict to update_dict
            update_dict[field] = field_dict

    # - dont save data when it is a test run
    if not is_test and save_instance:

        # - get scheme and update in student, also remove if necessary
        new_scheme = subj_mod.Scheme.objects.get_or_none(
            department=student.department,
            level=student.level,
            sector=student.sector)
        setattr(student, 'scheme', new_scheme)

        try:
            student.save(request=request)
            update_dict['id']['pk'] = student.pk
            # update_dict['id']['ppk'] = student.company.pk
        except:
            # - give error msg when creating student failed
            error_str = str(_("An error occurred. The student data is not saved."))
            # TODO
            code_text = '---'
            log_list.append(" ".join((code_text, error_str)))
            update_dict['row_error'] = error_str

    return update_dict
# --- end of update_student_fields


@method_decorator([login_required], name='dispatch')
class UploadImportUsernameView(View):  # PR2021-08-04
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UploadImportUsernameView ============= ')

        update_dict = {}

        if request.user and request.user.country and request.user.schoolbase:
            if request.POST['upload']:
                upload_dict = json.loads(request.POST['upload'])

                importtable = upload_dict.get('importtable')
                page = importtable.replace('import', 'page')

                permit_list, requsr_usergroups_listNIU = acc_view.get_userpermit_list(page, request.user)
# - get permit
                has_permit = False
            # to prevent you from locking out when no permits yet
                if request.user.role == c.ROLE_128_SYSTEM:
                    has_permit = True
                elif request.user.role == c.ROLE_064_ADMIN:
                    has_permit = 'permit_userpage' in permit_list

                if logging_on:
                    logger.debug('request.user.role: ' + str(request.user.role))
                    logger.debug('permit_list: ' + str(permit_list))
                    logger.debug('has_permit: ' + str(has_permit))

                if not has_permit:
                    err_html = _("You don't have permission to perform this action.")
                    update_dict['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))
                else:

        # - Reset language
                    # PR2019-03-15 Debug: language gets lost, get request.user.lang again
                    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                    activate(user_lang)

        # - get selected examyear, school and department from usersettings
                    # no examyear, school and department needed, only system and admin can upload usernames

        # - get info from upload_dict
                    is_test = upload_dict.get('test', False)
                    awpColdef_list = upload_dict.get('awpColdef_list')
                    data_list = upload_dict.get('data_list')
                    filename = upload_dict.get('filename', '')

                    if logging_on:
                        logger.debug('is_test: ' + str(is_test))
                        logger.debug('awpColdef_list: ' + str(awpColdef_list))
                        logger.debug('len(data_list: ' + str(len(data_list)))

                    updated_rows, log_list = [], []
                    count_total, count_existing, count_new, count_error, count_bisexam = 0, 0, 0, 0, 0

                    if awpColdef_list and data_list:

        # - create log_list
                        today_dte = af.get_today_dateobj()
                        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

                        log_list = [c.STRING_DOUBLELINE_80,
                                    str(_('Upload usernames')) + ' ' + str(_('date')) + ': ' + str(today_formatted),
                                    c.STRING_DOUBLELINE_80]

                        log_list.append(c.STRING_SPACE_10 + str(_("File name : %(file)s") % {'file': filename}))

                        info_txt = str(_("This is a test.")) + ' ' if is_test else ''
                        not_txt = str(_("not ")) if is_test else ''
                        info_txt += str(_("The user data are %(val)ssaved.") % {'val': not_txt})

                        log_list.append(c.STRING_SPACE_10 + info_txt)

                        log_list.append(c.STRING_SPACE_10)

    # - get double_username_list, a list of schoolcode + usernames that occur multiple times in data_list
    # - get double_email_list, a list of schoolcode + email that occur multiple times in data_list
                        double_username_list, double_email_list = stud_val.get_double_schoolcode_usernamelist_from_uploadfile(data_list)
                        if logging_on:
                            logger.debug('double_username_list: ' + str(double_username_list))
                            # double_username_list: [('cur05', 'user 5')]

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++ loop through data_list
                        for data_dict in data_list:

    # skip empty rows
                            has_values = False
                            for field in awpColdef_list:
                                value = data_dict.get(field)
                                if value is not None:
                                    has_values = True

                            if has_values:
    # - upload username
                                user_dict, is_new_user, is_existing_user, has_error = \
                                    upload_username_from_datalist(
                                        data_dict=data_dict,
                                        double_username_list=double_username_list,
                                        double_email_list=double_email_list,
                                        log_list=log_list,
                                        is_test=is_test,
                                        user_lang=user_lang,
                                        request=request
                                    )
                                if not is_test and user_dict:
                                    updated_rows.append(user_dict)

                                count_total += 1
                                if is_new_user:
                                    count_new += 1
                                elif is_existing_user:
                                    count_existing += 1
                                elif has_error:
                                    count_error += 1
# +++++ end of loop through data_list
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # - return html with number of students, existing, new and erros
                    update_dict = { 'is_test': is_test,
                                    'table': 'user',
                                    'result': crate_result_html(is_test, count_total, count_existing, count_new, count_error, True),
                                    'log_list': log_list}
                    if not is_test and updated_rows:
                        update_dict['updated_user_rows'] = updated_rows

        return HttpResponse(json.dumps(update_dict, cls=af.LazyEncoder))
# - end of UploadImportUsernameView


# ========  upload_username_from_datalist  ======= # PR2021-08-04
def upload_username_from_datalist(data_dict, double_username_list, double_email_list, log_list, is_test, user_lang, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- upload_username_from_datalist  --------------------')
        logger.debug('data_dict: ' + str(data_dict))
        logger.debug('is_test: ' + str(is_test))
        # data_dict: {'schoolcode': 'CUR01', 'username': 'User 1', 'last_name': 'User 1', 'email': 'user@email.com', 'function': 'v'}

    # NOTE: do not update existing user, to prevent accidental overwriting school users by ETE
    error_list = []
    user_dict = {}

# - get variables from data_dict
    school_code = data_dict.get('schoolcode')
    user_name = data_dict.get('username')
    username_with_underscore = user_name.replace(' ', '_') if user_name else ''

    last_name = data_dict.get('last_name', '')
    email = data_dict.get('email', '')
    function = data_dict.get('function')
    function_first_letter_lc = function[0].lower() if function else None
    usergroups = ''
    if function_first_letter_lc:
        if function_first_letter_lc == 'v':
            usergroups = 'admin;auth1;edit;read'
        elif function_first_letter_lc == 's':
            usergroups = 'admin;auth2;edit;read'
        else:
            usergroups = 'admin;edit;read'

    if logging_on:
        logger.debug('schoolcode: ' + str(school_code))
        logger.debug('username_with_underscore: ' + str(username_with_underscore))
        logger.debug('last_name:  ' + str(last_name))
        logger.debug('email:      ' + str(email))
        logger.debug('usergroups: ' + str(usergroups))

# - check for double occurrence in upload file
    has_error = False
    has_username_error = stud_val.validate_double_schoolcode_username_in_uploadfile(school_code, username_with_underscore, double_username_list, error_list)
    if has_username_error:
        has_error = True

    has_email_error = stud_val.validate_double_schoolcode_email_in_uploadfile(school_code, email, double_email_list, error_list)
    if has_email_error:
        has_error = True

    if not has_error:
        has_email_error = stud_val.validate_double_schoolcode_email_in_uploadfile(school_code, email, double_email_list, error_list)
        if not has_error:
# - validate length of fields school_code and username
            msg_err = stud_val.validate_length(_('The school code'), school_code, c.MAX_LENGTH_SCHOOLCODE, False)
            if msg_err:
                has_error = True
                error_list.append(str(msg_err))

            msg_err = stud_val.validate_length(_('The username'), username_with_underscore, c.USERNAME_SLICED_MAX_LENGTH, False)
            if msg_err:
                has_error = True
                error_list.append(str(msg_err))

    if logging_on:
        logger.debug('error_list: ' + str(error_list))

    schoolbase = None
    is_new_user = False
    is_existing_user = False
    new_user_pk = None
    if not has_error:

# - lookup schoolbase and user in database
        # only one of is_new_user, is_existing_user or msg_err is trueish
        schoolbase, is_new_user, is_existing_user, msg_err = lookup_user(school_code, username_with_underscore, request)
        if msg_err:
            has_error = True
            error_list.append(str(msg_err))
        if logging_on:
            logger.debug('schoolbase: ' + str(schoolbase))
            logger.debug('is_new_user: ' + str(is_new_user))
            logger.debug('is_existing_user: ' + str(is_existing_user))
            logger.debug('msg_err: ' + str(msg_err))

    if not has_error:

# - validate length of last_name and unique at school
        if is_new_user:
            msg_err = awpr_val.validate_unique_user_lastname(schoolbase, last_name, None, True)
            if msg_err:
                has_error = True
                error_list.append(msg_err)

# - validate length and format of the email_address
            msg_err = awpr_val.validate_email_address(email)
            if msg_err:
                has_error = True
                error_list.append(msg_err)
            else:
# - validate unique email_address at school
                msg_err = awpr_val.validate_unique_useremail(email, request.user.country, schoolbase, None, True)
                if msg_err:
                    has_error = True
                    error_list.append(msg_err)

        if has_error:
            is_new_user = False

        elif is_new_user:

# - create new user, save only when not a test
            try:
                prefixed_username_with_underscore = schoolbase.prefix + username_with_underscore
                role = schoolbase.defaultrole
                now_utc = timezone.now()
                new_user = acc_mod.User(
                    country=request.user.country,
                    schoolbase=schoolbase,
                    username=prefixed_username_with_underscore,
                    last_name=last_name,
                    email=email,
                    role=role,
                    usergroups=usergroups,
                    is_active=True,
                    activated=False,
                    lang=user_lang,
                    modified_by=request.user,
                    modified_at=now_utc
                )
                if not is_test:
                    new_user.save()
                    new_user_pk = new_user.pk

            except Exception as e:
                has_error = True
                is_new_user = False
                new_user_pk = None

                logger.error(getattr(e, 'message', str(e)))
                msg_err = ''.join((str(_('An error occurred')), ': ', str(e)))
                error_list.append(msg_err)
                error_list.append(str(_("User account '%(val)s' can not be created.") % {'val': username_with_underscore}))

# create log for this user

    schoolcode_nz = school_code if school_code else "---"
    username_with_underscore_nz = username_with_underscore if last_name else "---"

    item_header = ''.join(((schoolcode_nz + c.STRING_SPACE_10)[:10], str(_("User")),  " '",  username_with_underscore_nz, "'"))

    if is_new_user:
        item_header += str(_(' will be added.')) if is_test else str(_(' is added.'))
    else:
        if is_existing_user:
            item_header += str(_(' already exists at this school and'))
        item_header += str(pgettext_lazy('singular', ' will be skipped.')) if is_test else str(_(' is skipped.'))
    log_list.append(item_header)
    if error_list:
        for err in error_list:
            if err:
                log_list.append(' - '.join((c.STRING_SPACE_10, str(err))))

    if new_user_pk:
        updated_rows = acc_view.create_user_rows(request, user_pk=new_user_pk)
        if updated_rows:
            user_dict = updated_rows[0]
            user_dict['created'] = True

    return user_dict, is_new_user, is_existing_user, has_error
# --- end of upload_username_from_datalist



#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# ========  update_username_fields  ======= # PR2019-12-17 PR2020-06-03 PR2021-06-19
def update_username_fields(data_dict, awpColdef_list, examyear, school, department, is_test, dateformat,
                          student, is_existing_student,  log_list, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- update_username_fields  --------------------')
        logger.debug('data_dict: ' + str(data_dict))

    update_dict = {}
    save_instance = False
    if student:
        # add 'id' at the end, after saving the student. Pk doent have value until instance is saved
        # update_dict['id']['pk'] = student.pk
        # update_dict['id']['ppk'] = student.company.pk
        # if is_created_student:
        #    update_dict['id']['created'] = True

        # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
        # solved bij wrapping with str()

        blank_str = '<' + str(_('blank')) + '>'
        was_str = str(_('was') + ': ')

        for field in awpColdef_list:
            # --- get field_dict from  upload_dict  if it exists

            if logging_on:
                logger.debug('---------- field: ' + str(field))

            field_dict = {}
            field_caption = af.get_dict_value(c.CAPTIONS, ('student', field), '')
            caption_txt = (c.STRING_SPACE_05 + field_caption + c.STRING_SPACE_30)[:30]
            # text fields
            if field in ('lastname', 'firstname', 'prefix', 'gender', 'idnumber', 'birthcountry', 'birthcity',
                         'classname', 'examnumber', 'regnumber', 'diplomanumber', 'gradelistnumber'):
                new_value = data_dict.get(field)
                max_len = c.MAX_LEN_DICT_STUDENT.get(field)

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
                        log_list.append(caption_txt + (new_value or blank_str))
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
                            update_str = ((new_value or blank_str) + c.STRING_SPACE_30)[:25] + old_value_str
                            log_list.append(caption_txt + update_str)

            ######################################
            elif field == 'birthdate':
                # - get new value, convert to date, using dateformat
                new_value = data_dict.get(field)
                new_date_dte = None
                # - get saved_value
                saved_dte = getattr(student, field)
                saved_date_iso = None
                if saved_dte:
                    saved_date_iso = saved_dte.isoformat()
                old_value_str = was_str + (saved_date_iso or blank_str)

                # - validate new date
                new_date_dte, msg_err = None, None
                if new_value and dateformat:
                    date_iso = af.get_dateISO_from_string(new_value, dateformat)
                    new_date_dte = af.get_date_from_ISO(
                        date_iso)  # datefirst_dte: 1900-01-01 <class 'datetime.date'>
                    if new_date_dte is None:
                        msg_err = str(_("'%(val)s' is not a valid date.") % {'val': new_value})
                        if logging_on:
                            logger.debug('msg_err' + str(msg_err))
                if msg_err:
                    field_dict['error'] = msg_err
                    if is_existing_student:
                        field_dict['info'] = field_caption + ' ' + old_value_str
                        update_str = (msg_err + c.STRING_SPACE_30)[:25] + old_value_str
                        log_list.append(caption_txt + update_str)
                else:
                    new_date_iso = None
                    if new_date_dte:
                        new_date_iso = new_date_dte.isoformat()
                    field_dict['value'] = new_date_iso
                    if not is_existing_student:
                        log_list.append(caption_txt + (new_date_iso or blank_str))
                    if new_date_dte != saved_dte:
                        # put new value in student instance
                        setattr(student, field, new_date_dte)
                        field_dict['updated'] = True
                        save_instance = True
                        # create field_dict and log
                        if is_existing_student:
                            field_dict['info'] = field_caption + ' ' + old_value_str
                            update_str = ((new_date_iso or blank_str) + c.STRING_SPACE_30)[:25] + old_value_str
                            log_list.append(caption_txt + update_str)

            elif field in ('level', 'sector', 'profiel'):
                # 'profiel' is not a database field, will be stored in 'sector'
                db_field = 'sector' if field == 'profiel' else field
                new_base_pk = data_dict.get(field)
                saved_instance = getattr(student, db_field)

                # logger.debug('field: ' + str(field))
                # logger.debug('new_base_pk: ' + str(new_base_pk))
                # logger.debug('saved_instance: ' + str(saved_instance))

                # check if dep / lvl / sct exists
                new_instance = None
                if db_field == 'level':
                    new_instance = subj_mod.Level.objects.get_or_none(base_id=new_base_pk, examyear=examyear)
                elif db_field == 'sector':
                    new_instance = subj_mod.Sector.objects.get_or_none(base_id=new_base_pk, examyear=examyear)
                # logger.debug('new_instance: ' + str(new_instance))

                if new_instance is None:
                    save_new_instance = (saved_instance is not None)
                else:
                    save_new_instance = (saved_instance is None) or (new_instance != saved_instance)
                # logger.debug('save_new_lvl_sct: ' + str(save_new_instance))

                if save_new_instance:
                    setattr(student, db_field, new_instance)
                    field_dict['updated'] = True
                    save_instance = True
                    new_abbrev = new_instance.abbrev if new_instance else None
                    # logger.debug('new_abbrev: ' + str(new_abbrev))

                    if field == 'level':
                        caption_txt = (c.STRING_SPACE_05 + str(_('leerweg')) + c.STRING_SPACE_30)[:30]
                    elif field == 'sector':
                        caption_txt = (c.STRING_SPACE_05 + str(_('sector')) + c.STRING_SPACE_30)[:30]
                    elif field == 'profiel':
                        caption_txt = (c.STRING_SPACE_05 + str(_('profiel')) + c.STRING_SPACE_30)[:30]

                    if not is_existing_student:
                        log_list.append(caption_txt + (new_abbrev or blank_str))
                        # logger.debug('log_list.append: ' + str(caption_txt + (new_abbrev or blank_str)))
                    else:
                        saved_abbrev = saved_instance.abbrev if saved_instance else None
                        old_abbrev_str = was_str + (saved_abbrev or blank_str)
                        # logger.debug('old_abbrev_str: ' + str(old_abbrev_str))
                        field_dict['info'] = field_caption + ' ' + old_abbrev_str
                        update_str = ((new_abbrev or blank_str) + c.STRING_SPACE_30)[:25] + old_abbrev_str
                        log_list.append(caption_txt + update_str)
                        # logger.debug('log_list.append: ' + str(caption_txt + update_str))
            # add field_dict to update_dict
            update_dict[field] = field_dict

    # - dont save data when it is a test run
    if not is_test and save_instance:

        # - get scheme and update in student, also remove if necessary
        new_scheme = subj_mod.Scheme.objects.get_or_none(
            department=student.department,
            level=student.level,
            sector=student.sector)
        setattr(student, 'scheme', new_scheme)

        try:
            student.save(request=request)
            update_dict['id']['pk'] = student.pk
            # update_dict['id']['ppk'] = student.company.pk
        except:
            # - give error msg when creating student failed
            error_str = str(_("An error occurred. The student data is not saved."))
            # TODO
            code_text = '---'
            log_list.append(" ".join((code_text, error_str)))
            update_dict['row_error'] = error_str

    return update_dict
# --- end of update_username_fields



# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def lookup_user(school_code, username_with_underscore, request):
    # PR2021-08-04

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------- lookup_user ----------- ')
        logger.debug('--- school_code:           ' + str(school_code))
        logger.debug('--- username_with_underscore: ' + str(username_with_underscore))

    schoolbase = None
    is_new_user = False
    is_existing_user = False
    msg_err = None

# - lookup schoolbase
    # msg_err already given when schoolbase is blank or too long ( in validate_name_idnumber_length)
    if school_code:
        schoolbase = sch_mod.Schoolbase.objects.get_or_none(
            code__iexact=school_code.lower(),
            country=request.user.country
        )
    if schoolbase is None:
        msg_err = _("%(cpt)s '%(val)s' not found.") % {'cpt': _('School with code'), 'val': school_code}
    else:

# - check if a user exists with this username in this schoolcode
        if username_with_underscore:
            username_with_prefix = ('000000' + str(schoolbase.pk))[-6:] + username_with_underscore
            if logging_on:
                logger.debug('uername_with_prefix: ' + str(username_with_prefix))
            user_count = acc_mod.User.objects.filter(
                username__iexact=username_with_prefix,
                schoolbase=schoolbase
            ).count()
            if user_count == 0:
                is_new_user = True
            elif user_count == 1:
                is_existing_user = True
            else:
                # This should not be possible
                msg_err = _("Multiple users with username '%(val)s' exist at this school.") \
                          % {'val': username_with_underscore}

    if logging_on:
        logger.debug('----------- lookup_user ----------- ')
        logger.debug('--- schoolbase: ' + str(schoolbase))
        logger.debug('--- msg_err:    ' + str(msg_err))
        logger.debug('----------- end of lookup_user ----------- ')

    return schoolbase, is_new_user, is_existing_user, msg_err
# --- end of lookup_user


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# functions for upload



# ========  get_prefix_lastname_comma_firstname  ======= PR2021-06-19  PR2021-07-20
def get_birthdate_iso(birthdate_str, dateformat, error_list):
    # function converts birth_date to iso, checks for valid birthdate
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_birthdate_iso -----')
        logger.debug('birthdate_str: ' + str(birthdate_str) + ' ' + str(type(birthdate_str)))

    birthdate_iso = None

    if birthdate_str:
        date_iso = af.get_dateISO_from_string(birthdate_str, dateformat)
        if logging_on:
            logger.debug('date_iso: ' + str(date_iso) + ' ' + str(type(date_iso)))

        birthdate_dte = af.get_date_from_ISO(date_iso)  # datefirst_dte: 1900-01-01 <class 'datetime.date'>
        if logging_on:
            logger.debug('birthdate_dte: ' + str(birthdate_dte) + ' ' + str(type(birthdate_dte)))

        if birthdate_dte is None:
            err_str = str(_("'%(val)s' is not a valid date.") % {'val': birthdate_str})
            error_list.append(err_str)
            if logging_on:
                logger.debug('err_str' + str(err_str))
        else:
            birthdate_iso = birthdate_dte.isoformat()

    if logging_on:
        logger.debug('birthdate_iso: ' + str(birthdate_iso))

    return birthdate_iso

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# ========  import_students_testupload  ======= PR2021-06-17
def import_students_testuploadNIU(school, department, upload_dict, user_lang, request):
    logging_on = s.LOGGING_ON
    update_dict = {}
    update_list = []
    logfile = []
    log_dict = {}
    if logging_on:
        logger.debug(' ============= import_students_testupload ============= ')
        logger.debug('school: ' + str(school))
        logger.debug('department: ' + str(department))
    # TODO add permit -- in UploadImportDataView
    dateformat = upload_dict.get('dateformat', '')

    if dateformat:
        info_txt = str(_("The date format is: '%(fld)s'.") % {'fld': dateformat})
        logfile.append(c.STRING_SPACE_05 + info_txt)

    data_list = upload_dict.get('data_list')
    if data_list:

# - check if id_nr occurs multiple times in data_list
        # function returns list of idnumbers that occur multiple times in data_list
        double_entrieslist = stud_val.get_double_entrieslist_from_uploadfile(data_list)
        if logging_on:
            logger.debug('double_entrieslist: ' + str(double_entrieslist))

# +++++ loop through data_list +++++++++++++++++++++++++++
        count_total, count_existing, count_new, count_error, count_bisexam = 0, 0, 0, 0, 0
        bisexam_dict = {}
        for data_dict in data_list:
            row_index = data_dict.get('rowindex', -1)
            id_number = data_dict.get('idnumber')
            last_name = data_dict.get('lastname')
            first_name = data_dict.get('firstname')

            id_number_nodots = id_number.strip().replace('.', '')  if id_number else None
            lastname_stripped = last_name.strip() if last_name else None
            firstname_stripped = first_name.strip() if first_name else None

            is_create = False
            log = {}
            count_total += 1

            if logging_on:
                logger.debug('row_index: ' + str(row_index))
                logger.debug('id_number_nodots: ' + str(id_number_nodots))

            error_str = None
            if not id_number_nodots:
                error_str = _('%(fld)s cannot be blank.') % {'fld': _("The ID-number")}
            elif id_number_nodots in double_entrieslist:
                error_str = _("%(fld)s '%(val)s' is found multiple times in this upload file.") \
                            % {'fld': _("ID-number"), 'val': id_number}

            elif not lastname_stripped:
                error_str = _('%(fld)s cannot be blank.') % {'fld': _("The last name")}
            elif len(lastname_stripped) > c.MAX_LENGTH_FIRSTLASTNAME:
                error_str = _("%(fld)s '%(val)s' is too long, %(max)s characters or fewer.") \
                            % {'fld':  _("The last name"), 'val': lastname_stripped, 'max': c.MAX_LENGTH_FIRSTLASTNAME}

            elif not firstname_stripped:
                error_str = _('%(fld)s cannot be blank.') % {'fld': _("The first name")}
            elif len(firstname_stripped) > c.MAX_LENGTH_FIRSTLASTNAME:
                error_str = _("%(fld)s '%(val)s' is too long, %(max)s characters or fewer.") \
                            % {'fld': _("The first name"), 'val': firstname_stripped, 'max': c.MAX_LENGTH_FIRSTLASTNAME}

            if error_str:
                count_error += 1
                log['error'] = str(error_str)
            else:

                student_pk, not_found, err_str = validate_student_exists_thisschool_thisschoolyear(school, department, id_number_nodots)
                if logging_on:
                    logger.debug('student_pk: ' + str(student_pk))
                    logger.debug('not_found: ' + str(not_found))
                    logger.debug('err_str: ' + str(err_str))
                if err_str:
                    count_error += 1
                    log['error'] = err_str
                    logger.debug('count_error: ' + str(count_error))
                    logger.debug('>>>>>>>>>err_str: ' + str(err_str))
                elif student_pk:
                    count_existing += 1
                    log['pk'] = student_pk
                elif not_found:
                    count_new += 1
                    log['create'] = True
                    is_create = True
            log_dict[row_index] = log

            if is_create:
                # convert birth_date to iso, check for valid birthdate
                birth_date = data_dict.get('birthdate')
                birthdate_iso = None
                if birth_date:
                    date_iso = af.get_dateISO_from_string(birth_date, dateformat)
                    birthdate_dte = af.get_date_from_ISO(date_iso)  # datefirst_dte: 1900-01-01 <class 'datetime.date'>
                    if birthdate_dte is None:
                        msg_err = str(_("'%(val)s' is not a valid date.") % {'val': birth_date})
                        if logging_on:
                            logger.debug('msg_err' + str(msg_err))

                    else:
                        birthdate_iso = birthdate_dte.isoformat()



# +++++ end of loop through data_list

        # return html with number of students, existing, new and erros count_total, count_existing, count_new, count_error
        update_dict['result'] = crate_result_html(count_total, count_existing, count_new, count_error)

        if bisexam_dict:
            update_dict['bisexam_dict'] = bisexam_dict

            if logging_on:
                logger.debug('update_dict: ' + str(update_dict))
    if update_list:
        update_dict['data_list'] = update_list
    if logfile:
        update_dict['logfile'] = logfile
    if log_dict:
        update_dict['logdict'] = log_dict
    return update_dict


def crate_result_html(is_test, count_total, count_existing, count_new, count_error, is_user=False):  # PR2021-06-18 PR2021-08-05
    # function returns an html string with number of students, existing, new and erros
    title = _('Test results') if is_test else _('Upload results')

    caption_sing = _('user') if is_user else _('candidate')
    caption_plur = _('users') if is_user else _('candidates')

    result_html = ''.join(("<h6 class='mx-2 mt-2 mb-0'>", str(title), '</h6>'))
    if count_total:
        result_html += ''.join(("<p>",
                                str(_("The uploaded file has %(count)s %(cnd)s:")
                                    % {'count': count_total,
                                       'cnd': caption_plur if count_total > 1 else caption_sing}),
                                "</p>"))
        result_html += "<ul class='mb-0'>"
        if count_new:
            txt_plur = _('are new and will be added') if is_test else _('are new and have been added')
            txt_sing = _('is new and will be added') if is_test else _('is new and has been added')
            result_html += ''.join(("<li>",
                                    str(_("%(count)s %(cnd)s %(nw)s.")
                                        % {'count': count_new,
                                           'cnd': caption_plur if count_new > 1 else caption_sing,
                                           'nw': txt_plur if count_new > 1 else txt_sing}),
                                    "</li>"))
        if count_existing:
            # dont show msg 'changes have been saved; when uploading user, user upload doesnt save changes
            if is_user:
                if count_existing == 1:
                    txt_01 = pgettext_lazy('singular', ' and will be skipped.') if is_test else _(' and is skipped.')
                else:
                    txt_01 = pgettext_lazy('plural', ' and will be skipped.') if is_test else _(' and sre skipped.')
            else:
                txt_01 = ''
                # existing students will not be updatted PR22021-08-07don't update
                #  was: txt_01 = _(", changes will be saved.") if is_test else _(", changes have been saved.")
            result_html += ''.join(("<li>",
                                    str(_("%(count)s %(cnd)s %(exs)s")
                                        % {'count': count_existing,
                                           'cnd': caption_plur if count_existing > 1 else caption_sing,
                                           'exs': _('already exist') if count_existing > 1 else _('already exists')}),
                                    str(txt_01),
                                    "</li>"))



        if count_error:
            txt_plur = _('have errors and will be skipped') if is_test else _('have errors and are skipped')
            txt_sing = _('has an error and will be skipped') if is_test else _('has an error and is skipped')
            result_html += ''.join(("<li>",
                                    str(_("%(count)s %(cnd)s %(skip)s.")
                                        % {'count': count_error,
                                           'cnd': caption_plur if count_error > 1 else caption_sing,
                                           'skip': txt_plur if count_error > 1 else txt_sing}),
                                    '</li>'))
        result_html += "</ul>"
        result_html += ' '.join(( '<p>', str(_("Click")),
                                        "<a href='#' class='awp_href' onclick='MIMP_OpenLogfile()'>",
                                        str(_("here")),
                                        "</a>",
                                        str(_("to download the logfile with the details.")),
                                        "</p>"
                                        ))
    else:
        result_html += ''.join(("<p class='pb-0'>",
                                str(_('The uploaded file has no %(cnd)s.') % {'cnd': caption_plur }),
                                "</p>"))
    """
    NOT IN USE
    result_html += ''.join(("<h6 class='mx-2 mt-4 mb-0'>",
                            str(_("Possible bis-candidates")),
                            "</h6>"))

    result_html += ''.join(("<p>",
                            str(_("At %(count)s new %(cnd)s, AWP has found candidates in previous years, who might be the same person as the candidate, you are about to upload.")
                                % {'count': count_total,
                                   'cnd': caption_plur if count_total > 1 else caption_sing}),
                            "</p><p>",
                            str(_("If that is the case, you must link the existing candidate to the new candidate.")),
                            "</p><p>",
                            str(_("Click the arrow buttons below, to loop through the candidates.")),
                            "</p>"))
    """
    return result_html
# - end of crate_result_html


def validate_students_doubles(requsr_country, id_number, last_name, first_name, birthdate_iso):  # PR2021-06-18
    # function returns list of candidate dicts that are found
    # not in use yet, to be used when exemptions are enetered PR2021-07-18
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ============= validate_students_doubles ============= ')
        logger.debug('id_number: ' + str(id_number))
        logger.debug('last_name: ' + str(last_name))
        logger.debug('first_name: ' + str(first_name))
        logger.debug('birthdate_iso: ' + str(birthdate_iso))


# +++ create rows with potential same candidates
    sql_keys = {'country_id': requsr_country.pk,
                'id_nr': id_number.lower(),
                'ln': last_name.lower(),
                'fn': first_name.lower()}

    birth_date_filter = ""
    if birthdate_iso:
        sql_keys['bd'] = birthdate_iso
        birth_date_filter =  "OR (st.birthdate = %(bd)s::DATE AND LOWER(st.lastname) = %(ln)s) " + \
                             "OR (st.birthdate = %(bd)s::DATE AND LOWER(st.firstname) = %(fn)s)"

    sql_list = [
        "SELECT st.id, st.base_id, st.idnumber, st.lastname, st.firstname, st.prefix, st.classname,",
        "sch.abbrev AS sch_abbrev, db.code AS db_code, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev",

        "FROM students_student AS st",
        "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "INNER JOIN schools_Departmentbase AS db ON (db.id = dep.base_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
        "WHERE ey.country_id = %(country_id)s::INT AND ("
            "(LOWER(st.idnumber) = %(id_nr)s)",
            birth_date_filter,
            "OR (LOWER(st.lastname) = %(ln)s AND LOWER(st.firstname) = %(fn)s)",
        ")"
    ]
    sql = ' '.join(sql_list)

    double_dict = {}

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)

        for row_dict in af.dictfetchall(cursor):
            if logging_on:
                logger.debug('row_dict: ' + str(row_dict))

            base_id = row_dict.get('base_id')
            if base_id not in double_dict:
                double_dict[base_id] = []
            double_dict[base_id].append(row_dict)

    return double_dict
# - end of validate_students_doubles


def validate_student_exists_thisschool_thisschoolyear(school, department, id_number_nodots):  # PR2021-06-14
    # - check if id_number_nodots already exists in this school, this examyear

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ============= validate_student_exists_thisschool_thisschoolyear ============= ')
        logger.debug('id_number_nodots: ' + str(id_number_nodots))

    students = stud_mod.Student.objects.filter(
        idnumber__iexact=id_number_nodots,
        school=school)

    row_pk, student_pk, err_str = None, None, None
    row_count, not_found, found_in_this_dep, found_in_diff_dep = 0, False, False, False
    for row in students:
        row_count += 1
        if row.department_id == department.pk:
            found_in_this_dep = True
            row_pk = row.pk
        else:
            found_in_diff_dep = True

    if logging_on:
        logger.debug('row_count: ' + str(row_count))
        logger.debug('found_in_this_dep: ' + str(found_in_this_dep))

    if row_count > 1:
        err_str = str(_("ID-number '%(val)s' exists multiple times ") % {'val': id_number_nodots})
        if found_in_diff_dep:
            if found_in_this_dep:
                err_str = str(_("in multiple departments of your school."))
            else:
                err_str = str(_("in other departments of your school."))
        elif found_in_this_dep:
            err_str = str(_("in this department."))

    elif row_count == 1:
        if found_in_diff_dep:
            err_str = str(_("ID-number '%(val)s' already exists in a different department.") % {'val': id_number_nodots})
        else:
            # return student_pk when student only occurs once and is in this department
            student_pk = row_pk

    else:
        not_found = True

    if logging_on:
        logger.debug('not_found: ' + str(not_found))
        logger.debug('err_str: ' + str(err_str))

    return student_pk, not_found, err_str



#######################################################
def update_student(instance, parent, upload_dict, msg_dict, request):
    # --- update existing and new instance PR2019-06-06
    # add new values to update_dict (don't reset update_dict, it has values)
    #logger.debug(' ------- update_student -------')
    #logger.debug('upload_dict' + str(upload_dict))

    if instance:
# 1. get iddict variables
        #  FIELDS_STUDENT = ('base', 'school', 'department', 'level', 'sector', 'scheme', 'package',
        #                   'lastname', 'firstname', 'prefix', 'gender', 'idnumber', 'birthdate', 'birthcountry', 'birthcity',
        #                   'classname', 'examnumber', 'regnumber', 'diplomanumber', 'gradelistnumber',
        #                   'iseveningstudent',
        #                   'locked', 'has_reex', 'bis_exam', 'withdrawn', 'modifiedby', 'modifiedat')

        save_changes = False
        for field in c.FIELDS_STUDENT:

# --- get field_dict from  upload_dict  if it exists
            field_dict = upload_dict[field] if field in upload_dict else {}
            if field_dict:
                if 'update' in field_dict:
# a. get new_value
                    new_value = field_dict.get('value')
                    saved_value = getattr(instance, field)

# 2. save changes in field 'code', required field
                    if field in ['code', 'identifier']:
                        if new_value != saved_value:
            # validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                            msg_err = None #stud_val.validate_code_name_identifier(
                               # table='student',
                                #field=field,
                                #new_value=new_value, parent=parent,
                               # is_absence=False,
                              #  update_dict={},
                              #  msg_dict={},
                              #  request=request,
                             #   this_pk=instance.pk)
                            if not msg_err:
                                # c. save field if changed and no_error
                                setattr(instance, field, new_value)
                                save_changes = True
                            else:
                                msg_dict['err_' + field] = msg_err

    # 3. save changes in fields 'firstname', 'lastname'
                    elif field in ['firstname', 'lastname']:
                        if new_value != saved_value:
                            name_first = None
                            name_last = None
                            if field == 'firstname':
                                name_first = new_value
                                name_last = getattr(instance, 'lastname')
                            elif field == 'lastname':
                                name_first = getattr(instance, 'firstname')
                                name_last = new_value
                            # check if student firstname / lastname combination already exists
                            #has_error = validate_lastname_firstname(
                            #    lastname=name_last,
                           #     firstname=name_first,
                           #     company=request.user.company,
                            #    update_field=field,
                            #    msg_dict=msg_dict,
                            #    this_pk=instance.pk)
                            setattr(instance, field, new_value)
                            save_changes = True

# 3. save changes in date fields
                    elif field in ['datefirst', 'datelast']:
        # a. get new_date
                        new_date = af.get_date_from_ISO(new_value)  # datefirst_dte: 1900-01-01 <class 'datetime.date'>

        # b. validate value
                        if msg_err:
                            msg_dict['err_' + field] = msg_err
                        else:
        # c. save field if changed and no_error
                            old_date = getattr(instance, field, None)
                            if new_date != old_date:
                                setattr(instance, field, new_date)
                                save_changes = True

# 4. save changes in fields functioncode', 'wagecode'
                    elif field in ['functioncode', 'wagecode']:
                        new_value = None
                        new_pk = field_dict.get('value')
                        is_wagecode = (field == 'wagecode')
                        is_functioncode = (field == 'functioncode')
                        if new_pk:
                            new_value = stud_mod.Wagecode.objects.get_or_none(
                                company=request.user.company,
                                pk=new_pk,
                                iswagecode=is_wagecode,
                                iswagefactor= False,
                                isfunctioncode=is_functioncode
                            )
                        saved_value = getattr(instance, field)
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
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
def import_studentsubjects(upload_dict, user_lang, logging_on, request):  # PR2021-02-26
    if logging_on:
        logger.debug(' ============= import_studentsubjects ============= ')
        logger.debug('upload_dict: ' + str(upload_dict))
        """              
        upload_dict: {
            'importtable': 'import_studsubj', 
            'test': True, 
            'is_crosstab': True, 
            'sel_examyear_pk': 1, 
            'sel_schoolbase_pk': 12, 
            'sel_depbase_pk': 1, 
            'lookup_field': 'examnumber', 
            'data_list': [
                   {'rowindex': 0, 
                    'examnumber': '63', 
                    'idnumber': '1999112405', 
                    'pws_title': 'titel werkstuk', 
                    'pws_subjects': 'vakken werkstuk', 
                        (format of subjects: {subjectBasePk: subjecttypeBasePk, ..})
                    'subjects': {'1': 4, '3': 0, '4': 0, '10': 0, '15': 0, '27': 0, '29': 0, '31': 0, '36': 0, '42': 7, '46': 0}
                }, 
                {'rowindex': 7, 'examnumber': '28', 'idnumber': '1999110505', 'subjects': {'1': 0, '3': 0, '4': 0, '10': 9, '15': 0, '27': 0, '29': 0, '31': 0, '34': 9, '42': 7, '46': 4}}, 
                {'rowindex': 8, 'examnumber': '29', 'idnumber': '1997053111', 'subjects': {'1': 0, '3': 0, '4': 0, '10': 0, '15': 0, '27': 0, '29': 0, '31': 0, '34': 0, '42': 7, '46': 0}}
                ]
            }           
        """

# - get info from upload_dict
    is_test = upload_dict.get('test', False)
    lookup_field = upload_dict.get('lookup_field')
    is_crosstab = upload_dict.get('is_crosstab', False)
    data_list = upload_dict.get('data_list')
    sel_examyear_pk = upload_dict.get('sel_examyear_pk')
    sel_schoolbase_pk = upload_dict.get('sel_schoolbase_pk')
    sel_depbase_pk = upload_dict.get('sel_depbase_pk')

    params = {}

    if data_list:
# - get lookup_field
        # lookup_field is field that determines if student alreay exist.
        # check if one of the fields 'examnumber', 'idnumber' exists
        # first in the list is lookup_field
        # gets value on client in import.js
        if logging_on:
            logger.debug( 'lookup_field: ' + str(lookup_field))
            logger.debug( 'is_crosstab: ' + str(is_crosstab))
            logger.debug( 'sel_examyear_pk: ' + str(sel_examyear_pk))
            logger.debug( 'sel_schoolbase_pk: ' + str(sel_schoolbase_pk))
            logger.debug( 'sel_depbase_pk: ' + str(sel_depbase_pk))

# - get examyear from sel_examyear_pk and request.user.country
        examyear = sch_mod.Examyear.objects.get_or_none(pk=sel_examyear_pk, country=request.user.country)

# - get school from sel_schoolbase_pk and sel_examyear_pk
        school, school_name, department = None, None, None
        if examyear:
            schoolbase = sch_mod.Schoolbase.objects.get_or_none(pk=sel_schoolbase_pk, country=request.user.country)
            school = sch_mod.School.objects.get_or_none(base=schoolbase, examyear=examyear)
            school_name = school.base.code + ' ' + school.name

# - get department from sel_depbase_pk and sel_examyear_pk
            depbase = sch_mod.Departmentbase.objects.get_or_none(pk=sel_depbase_pk)
            department = sch_mod.Department.objects.get_or_none(base=depbase, examyear=examyear)

        if logging_on:
            logger.debug('examyear: ' + str(examyear) + ' ' + str(type(examyear)))
            logger.debug('school: ' + str(school) + ' ' + str(type(school)))
            logger.debug('department: ' + str(department) + ' ' + str(type(department)))

        if school and department:

# - get subject list of this school/dep with number of occurrencies in scheme
            count_subjectbase_dict = count_subjectbase_in_scheme(department)

# - get subject_codes from subjects of this department
            subject_code_dict = subjectbase_code_dict(department)

# - create logfile
            today_dte = af.get_today_dateobj()
            today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

            logfile = [c.STRING_DOUBLELINE_80,
                       '  ' + school_name + '  -  ' +
                                str(_('Upload candidates')) + ' ' + str(_('date')) + ': ' + str(today_formatted),
                       c.STRING_DOUBLELINE_80]

            if lookup_field is None:
                info_txt = str(_('There is no field given to lookup candidates. Candidates cannot be uploaded.'))
                logfile.append(c.STRING_SPACE_05 + info_txt)
            else:
                if is_test:
                    info_txt = str(_("This is a test. The subjects of the candidates will not be saved."))
                else:
                    info_txt = str(_("The subjects of the candidates are saved."))
                logfile.append(c.STRING_SPACE_05 + info_txt)
                lookup_caption = af.get_dict_value(c.CAPTIONS, ('student', lookup_field), '')
                info_txt = str(_("Candidates are looked up by the field: '%(fld)s'.") % {'fld': lookup_caption})
                logfile.append(c.STRING_SPACE_05 + info_txt)

# +++++ loop through data_list
                update_list = []
                for data_dict in data_list:
                    # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html
                    # for key, val in student.items():
                    # #logger.debug( str(key) +': ' + val + '" found in "' + str(student) + '"')

    # - check if value of lookup_field occurs multiple times in data_list
                    # only check for multiple lookup_values when is_crosstab
                    # (in tabular each subject is in a separate row and lookup_value occurs multiple times in data_list)
                    lookup_value = data_dict.get(lookup_field)
                    occurrences_in_datalist = 0
                    if is_crosstab and lookup_value:
                        for dict in data_list:
                            value = dict.get(lookup_field)
                            if value and value == lookup_value:
                                occurrences_in_datalist += 1
                    if logging_on:
                        logger.debug('lookup_value occurrences in datalist: ' + str(occurrences_in_datalist))

    # - upload student
                    #update_dict = upload_studentsubject(data_dict, lookup_field, lookup_value, occurrences_in_datalist,
                    #                              count_subjectbase_dict, subject_code_dict, is_test, examyear, school, department, logfile, logging_on, request)
                    # json_dumps_err_list = json.dumps(msg_list, cls=af.LazyEncoder)
                    #if update_dict:  # 'Any' returns True if any element of the iterable is true.
                    #    update_list.append(update_dict)

                if update_list:  # 'Any' returns True if any element of the iterable is true.
                    params['data_list'] = update_list
            if logfile:  # 'Any' returns True if any element of the iterable is true.
                params['logfile'] = logfile
                    # params.append(new_student)
    return params
# - end of import_studentsubjects


def get_mapped_subjectbase_code_dict(department):  # PR2021-02-27 PR2021-07-21
    # get subject_codes from subjects of this department
    code_dict = {}
    schemeitems = subj_mod.Schemeitem.objects.filter(scheme__department=department)
    for schemeitem in schemeitems:
        subject_base = schemeitem.subject.base
        if subject_base and  subject_base.id not in code_dict:
            code_dict[subject_base.id] = subject_base.code
    return code_dict


def get_subjbase_pk_list_per_student_NEW(school, department, double_entrieslist):  # PR2021-07-21
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- get_subjbase_pk_list_per_student_NEW  --------------------')
        logger.debug('double_entrieslist: ' + str(double_entrieslist))
        logger.debug('school.pk: ' + str(school.pk))
        logger.debug('department.pk: ' + str(department.pk))

    # this one uses idnumber as key, this way you can skip lookup student
    # don't add idnumber to list when it is found multiple times in upload list

    # function creates a dict with as key idnumber and as value a dict with key: subjbase_pk and value: subject_code
    # output:       dict: { idnumber: {student_id: id, subjectbase_pk: subject_code, ...}, ... }
    # '2004042204': {'stud_id': 3110, 133: 'ne', 134: 'en', 135: 'mm1', 136: 'lo', 138: 'pa', 141: 'wk', 142: 'ns1', 154: 'ns2', 155: 'sws'},

   # sql_keys = {'ey_id': school.examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}
    sql_keys = {'sch_id': school.pk, 'dep_id': department.pk}
    sql_studsubj_list = ["SELECT studsubj.student_id, subj.base_id AS subjbase_id, subjbase.code AS subjbase_code",
        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
        # "WHERE subj.examyear_id = %(ey_id)s::INT AND NOT studsubj.tobedeleted"]
        "WHERE NOT studsubj.tobedeleted"]
    sub_sql = ' '.join(sql_studsubj_list)

    sql_list = ["WITH sub_sql AS (" + sub_sql + ")",
        "SELECT stud.idnumber, stud.id AS stud_id, stud.lastname, stud.firstname, stud.prefix, ",
        "sub_sql.subjbase_id, sub_sql.subjbase_code",
        "FROM students_student AS stud",
        "LEFT JOIN sub_sql ON (sub_sql.student_id = stud.id)",
        "WHERE stud.school_id = %(sch_id)s::INT AND stud.department_id = %(dep_id)s::INT"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = cursor.fetchall()

    subjectbase_pk_dict = {}
    if rows:
        for row in rows:

# - get student_id, add as key to student_dict if it does not exists yet
            id_number = row[0]
            if double_entrieslist and id_number in double_entrieslist:
                if logging_on:
                    logger.debug('id_number found in double_entrieslist: ' + str(id_number))
            else:
                # student_pk = row[1]
                if id_number not in subjectbase_pk_dict:
                    subjectbase_pk_dict[id_number] = {'stud_id': row[1]}
                student_dict = subjectbase_pk_dict[id_number]

    # - get subjectbase_pk, add as key to scheme_dict if it does not exists yet
                # rows is ordered by sjtpbase.sequence
                # therefore the schemeitem_subject with the lowest sequence will be added
                # a schemeitem_subject can only occur once in the subject_dict

                subjectbase_pk = row[2]
                subjectbase_code = row[3] if row[3] else '-'
                if subjectbase_pk not in student_dict:
                    student_dict[subjectbase_pk] = subjectbase_code

    if logging_on:
        logger.debug('subjectbase_pk_dict: ' + str(subjectbase_pk_dict))

    return subjectbase_pk_dict
# - end of get_subjbase_pk_list_per_student_NEW


def get_subjbase_pk_list_per_student(school, department):  # PR2021-07-21
    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- get_subjbase_pk_list_per_student  --------------------')
    # function creates a dict with as key student_pk and as value a dict with key: subjbase_pk and value: subject_code
    # output:       schemeitem_dict: { student_id: {subjectbase_pk: subject_code, ...}, ... }


    sql_keys = {'sch_id': school.pk, 'dep_id': department.pk}
    sql_list = ["SELECT studsubj.student_id, subj.base_id AS subjbase_id, subjbase.code AS subjbase_code",
        "FROM students_studentsubject AS studsubj",
        "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
        "WHERE stud.school_id = %(sch_id)s::INT AND stud.department_id = %(dep_id)s::INT AND NOT studsubj.tobedeleted"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = cursor.fetchall()

    subjectbase_pk_dict = {}
    if rows:
        for row in rows:
            if logging_on:
                logger.debug('row: ' + str(row))

# - get student_id, add as key to student_dict if it does not exists yet
            student_pk = row[0]
            if student_pk not in subjectbase_pk_dict:
                subjectbase_pk_dict[student_pk] = {}
            student_dict = subjectbase_pk_dict[student_pk]

# - get subjectbase_pk, add as key to scheme_dict if it does not exists yet
            # rows is ordered by sjtpbase.sequence
            # therefore the schemeitem_subject with the lowest sequence will be added
            # a schemeitem_subject can only occur once in the subject_dict

            subjectbase_pk = row[1]
            subjectbase_code = row[2] if row[2] else '-'
            if subjectbase_pk not in student_dict:
                student_dict[subjectbase_pk] = subjectbase_code

            if logging_on:
                logger.debug('subjectbase_pk: ' + str(subjectbase_pk))
                logger.debug('subjectbase_code: ' + str(subjectbase_code))
                logger.debug('student_dict: ' + str(student_dict))

    if logging_on:
        logger.debug('subjectbase_pk_dict' + str(subjectbase_pk_dict))
    return subjectbase_pk_dict
# - end of get_subjbase_pk_list_per_student


def map_subjectbase_pk_to_schemeitem_pk(school, department):  # PR2021-07-21
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- map_subjectbase_pk_to_schemeitem_pk  --------------------')
    # function creates a dict per scheme of subjects with the lowest sequence
    # output:       schemeitem_dict: { scheme_id: { subjectbase_pk: [schemeitem_id, subject_code] }, ... }

    schemeitem_dict = {}

    rows = subj_view.create_schemeitem_rows(
        examyear=school.examyear,
        cur_dep_only=True,
        depbase=department.base,
        orderby_sjtpbase_sequence=True
    )

    if rows:
        for row in rows:
            schemeitem_id = row.get('id')

# - get scheme_id, add as key to schemeitems_dict if it does not exists yet
            scheme_id = row.get('scheme_id')
            if scheme_id not in schemeitem_dict:
                schemeitem_dict[scheme_id] = {}
            scheme_dict = schemeitem_dict[scheme_id]

# - get subjbase_id, add as key to scheme_dict if it does not exists yet
            # rows is ordered by sjtpbase.sequence
            # therefore the schemeitem_subject with the lowest sequence will be added
            # a schemeitem_subject can only occur once in the subject_dict
            subjectbase_pk = row.get('subjbase_id')
            subject_code = row.get('subj_code')
            if subjectbase_pk and subjectbase_pk not in scheme_dict:
                scheme_dict[subjectbase_pk] = [schemeitem_id, subject_code]
    if logging_on:
        logger.debug('schemeitem_dict' + str(schemeitem_dict))
    return schemeitem_dict
# - end of map_subjectbase_pk_to_schemeitem_pk


def count_subjectbase_in_scheme(department):  # PR2021-02-27
    #logger.debug('----------------- count_subjectbase_in_scheme  --------------------')
    # function counts how many times a subject occurs in a scheme
    # when a subjects occurs only once, a subjecttype is not needed to add the subject to a student
    # output:       count_dict: { scheme_id: { subject_base_id: count, ... }, ... }
    # count_dict: {8: {20: 1, 3: 1, 4: 1, 1: 1, 6: 2, 7: 2, 10: 1, 27: 1, 29: 1, 31: 1, 39: 1, 40: 1, 41: 1, 46: 1},
    #              7: {3: 1, 4: 1, 1: 1, 6: 1, 7: 1, 10: 1, 15: 1, 27: 1, 29: 1, 31: 1, 33: 1, 34: 1, 35: 1, 36: 1, 37: 1, 38: 1, 46: 1},
    count_dict = {}
    schemeitems = subj_mod.Schemeitem.objects.filter(
        scheme__department=department
    )
    for schemeitem in schemeitems:
        scheme_id = schemeitem.scheme_id
        subject = schemeitem.subject
        subject_base_id = subject.base_id

        if scheme_id not in count_dict:
            count_dict[scheme_id] = {}
        scheme_dict = count_dict[scheme_id]

        if subject_base_id not in scheme_dict:
            scheme_dict[subject_base_id] = 0
        scheme_dict[subject_base_id] += 1

    return count_dict
# - end of count_subjectbase_in_scheme


def upload_studentsubject_from_datalist(data_dict, school, department, is_test,
                                        double_entrieslist, mapped_subjectbase_pk_dict, subjbase_pk_list_per_student,
                                        log_list, request):  # PR2021-07-21 PR2021-08-12

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- upload_studentsubject_from_datalist  --------------------')
        logger.debug('data_dict: ' + str(data_dict))

    """
    mapped_subjectbase_pk_dict: {scheme_id: {subjectbase_pk: [schemeitem_id, subject_code]} }
    mapped_subjectbase_pk_dict: {247: {137: [2022, 'be'], 138: [2031, 'pa'], 140: [2033, 'sp'], ...}
        
    mapped_subjectbase_pk_dict: {idnumber: {stud_id: id, subjectBasePk: subjecttypeBasePk, ..} }
    subjbase_pk_list_per_student: {'2004101103': {'stud_id': 3117, 'fullname': 'Balentien, Rayviendall', 
                                                    133: 'ne', 134: 'en', 135: 'mm1', 136: 'lo', 138: 'pa', 141: 'wk', 142: 'ns1', 146: 'bw', 156: 'stg'}, 
    """

    caption = _('This subject')
    caption_plural = _('This subject')
    this_subject_is_added_str = str(_("%(cpt)s will be added") % {'cpt': caption}) \
        if is_test else str(_("%(cpt)s is added") % {'cpt': caption})
    not_added_str = str(_("%(cpt)s will not be added.") % {'cpt': caption}) \
        if is_test else str(_("%(cpt)s is not added.") % {'cpt': caption})

    not_added_plural_str = str(pgettext_lazy('plural', "%(cpt)s will not be added.") % {'cpt': caption_plural}) \
        if is_test else str(pgettext_lazy('plural', "%(cpt)s are not added.") % {'cpt': caption_plural})

    error_list = []
    studsubj_rows = []

# - lookup student in database
    # multiple_found and exceeded_length return the lookup_value of the error field

    lookup_field_caption = af.get_dict_value(c.CAPTIONS, ('student', 'idnumber'), '')
    lookup_field_capitalized = '-'
    if lookup_field_caption:
        lookup_field_capitalized = lookup_field_caption.capitalize()
    id_number = data_dict.get('idnumber')
    id_number_nodots = stud_val.get_idnumber_nodots_stripped(id_number)

# - check for double occurrence in upload file
    has_error = stud_val.validate_double_entries_in_uploadfile(id_number_nodots, double_entrieslist, error_list)
    if error_list:
        log_list.extend(error_list)

    if logging_on:
        logger.debug('lookup_field_caption: ' + str(lookup_field_caption))
        logger.debug('id_number_nodots: ' + str(id_number_nodots))
        logger.debug('error_list: ' + str(error_list))
        logger.debug('has_error: ' + str(has_error))

    student = None
    if not has_error:
        if logging_on:
            logger.debug('subjbase_pk_list_per_student: ' + str(subjbase_pk_list_per_student))

# - lookup student in subjbase_pk_list_per_student ( list only contains students of this dep, doubles in uploadlist are filtered out
        # either student, is_new_student or has_error is trueish
        if id_number_nodots in subjbase_pk_list_per_student:
            subjbase_dict = subjbase_pk_list_per_student.get(id_number_nodots)

            if logging_on:
                logger.debug('subjbase_dict: ' + str(subjbase_dict))

            student_pk = subjbase_dict.get('stud_id')
            if logging_on:
                logger.debug('student_pk: ' + str(student_pk))

            if student_pk:
                student = stud_mod.Student.objects.get_or_none(pk=student_pk, school=school, department=department)


    if logging_on:
        logger.debug('student: ' + str(student))

    if student is None:
        has_error = True
        log_list.append(_("Candidate with ID-number '%(val)s' is not found.") % {'val': id_number_nodots})

    elif student.scheme is None:
        log_list.append(id_number_nodots + '  ' + student.fullname + ' ' + str(student.scheme))
        caption_txt = c.STRING_SPACE_05 + (c.STRING_SPACE_10)[:8]
        if student.department_id is None:
            log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': _('department')}))
        if department.sector_req and student.sector_id is None:
            caption = _('profiel') if department.has_profiel else _('sector')
            log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': caption}))
        if department.level_req and student.level_id is None:
            log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': _('leerweg')}))
        cpt = _('The subjects')
        if is_test:
            not_added_txt = pgettext_lazy('plural', "%(cpt)s will not be added.") % {'cpt': cpt}
        else:
            not_added_txt = pgettext_lazy('plural', "%(cpt)s have not been added.") % {'cpt':cpt}
        log_list.append(''.join((caption_txt, str(not_added_txt))))

    else:
        log_list.append(id_number_nodots + '  ' + student.fullname + ' ' + str(student.scheme))

        save_student = False

        student_scheme_pk = student.scheme_id

        # mapped_subjectbase_pk_dict = { scheme_id: { subjectbase_pk: [schemeitem_id, subject_code] }, ... }
        # mapped_subjectbase_pk_dict: {249: {140: [2070, 'sp'], 133: [2054, 'ne'],
        scheme_dict = {}
        if student.scheme.pk in mapped_subjectbase_pk_dict:
            scheme_dict = mapped_subjectbase_pk_dict.get(student.scheme.pk)

# - use list of subjectbase_pk's of this student - to speed up search
        # - subjbase_pk_list_per_student is a dict with key: student_pk and value: a dict with key: subjbase_pk and value: subject_code
        # output: subjbase_pk_list_per_student: { student_id: {subjectbase_pk: subject_code, ...}, ... }
        student_subjbase_pk_dict = {}
        if student.pk in subjbase_pk_list_per_student:
            student_subjbase_pk_dict = subjbase_pk_list_per_student.get(student.pk)

        if logging_on:
            logger.debug('..... student: ' + str(student))
            logger.debug('      student_scheme: ' + str(student_scheme_pk) + ' ' + str(student.scheme))

        # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
        # solved bij wrapping with str()

        if 'subjects' in data_dict:
            # subjects: {'133': 'ne', '134': 'en', '136': 'lo', '137': 'cav', '138': 'pa', '140': 'sp', '143': 'bi', '175': 'ec'}
            subjects = data_dict.get('subjects')
            if logging_on:
                logger.debug('..... subjects: ' + str(subjects))
                logger.debug('..... student_subjbase_pk_dict: ' + str(student_subjbase_pk_dict))
            if subjects:
                has_created_studsubj = False

# +++ loop through subjects of data_list ++++++++++++++++++++++++++++++++++++++
                for subjectbase_pk_str, subject_code in subjects.items():
                    upload_subjectBasePk = int(subjectbase_pk_str)
                    caption_txt = c.STRING_SPACE_05 + (subject_code + c.STRING_SPACE_10)[:8]

                    # mapped_subjectbase_pk_dict contains a dict per scheme of subjects with the lowest sequence
                    # mapped_subjectbase_pk_dict = { scheme_id: { subjectbase_pk: [schemeitem_id, subject_code] }, ... }
                    # mapped_subjectbase_pk_dict: {249: {140: [2070, 'sp'], 133: [2054, 'ne'],

# - skip if student already has this subject
                    # student_subjbase_pk_dict = {subjectbase_pk: subject_code, ...}
                    if upload_subjectBasePk in student_subjbase_pk_dict:
                        log_str = ' '.join( (caption_txt, not_added_str, str(_("This candidate already has this subject."))))
                        log_list.append(log_str)
                        if logging_on:
                            logger.debug('..... ' + str(log_str))

# - skip if this subject is not found in scheme
                    # scheme_dict = { subjectbase_pk: [schemeitem_id, subject_code] }
                    # scheme_dict = {140: [2070, 'sp'], 133: [2054, 'ne'], ...}
                    elif upload_subjectBasePk not in scheme_dict:
                        log_str = ' '.join((caption_txt, not_added_str, str(_("This subject does not occur in this subject scheme."))))
                        log_list.append(log_str)
                        if logging_on:
                            logger.debug('..... ' + str(log_str))
                    else:

# - add subject when student does not have this subject and subject is found in scheme:
                        # scheme_dict = { subjectbase_pk: [schemeitem_id, subject_code] }
                        # scheme_dict = {140: [2070, 'sp'], 133: [2054, 'ne'], ...}
                        schemeitem_list = scheme_dict.get(upload_subjectBasePk)
                        if schemeitem_list:
                            schemeitem_pk = schemeitem_list[0]

        # - get schemeitem and upload_subjecttype
# if so. or no upload subjecttype given, add subject to student
                            schemeitem = subj_mod.Schemeitem.objects.get_or_none(
                                pk=schemeitem_pk)

        # - check if lookup subjecttype is the same as the upload subjecttype
                            if schemeitem:
            # - add studentsubject  - schemeitem_pk is the subject with the lowest subjecttype sequence
                                messages, error_list = [], []
                                studsubj = stud_view.create_studsubj(student, schemeitem, messages, error_list, request, is_test)
                                if studsubj:
                                    has_created_studsubj = True
                                    log_str = ''.join((caption_txt, this_subject_is_added_str, ' ',
                                                       str(_('with character')),
                                                       " '" + schemeitem.subjecttype.abbrev + "'."))
                                    log_list.append(log_str)
                                    if logging_on:
                                        logger.debug('..... ' + str(log_str))
                                elif error_list:
                                    log_list.append(' '.join((caption_txt, ' '.join(error_list))))
                                    if logging_on:
                                        logger.debug('..... ' + str(error_list))

# +++ end of loop through subjects of data_list ++++++++++++++++++++++++++++++++++++++

# - when studsubjects are adde to student: add rows to studsubj_rows
                # PR2021-08-13 to prevent timeout error: download studentsubject_rows in separate ajax call
                if has_created_studsubj:
                    pass
                    """
                    append_dict = {'created': True}
                    rows = stud_view.create_studentsubject_rows(
                        examyear=school.examyear,
                        schoolbase=school.base,
                        depbase=department.base,
                        append_dict=append_dict,
                        setting_dict={},
                        student_pk=student.pk)
                    if rows:
                        studsubj_rows.extend(rows)
                    """
                else:
                    has_error = True
                    caption_txt = c.STRING_SPACE_05 + (c.STRING_SPACE_10)[:8]
                    log_str = ' '.join(
                        (caption_txt, str(_("No subjects are added."))))
                    log_list.append(log_str)
                    if logging_on:
                        logger.debug('..... ' + str(log_str))

# +++ end of loop ++++++++++++++++++++++++++++++++++++++

        # TODO move to grade upload
        """
        # +++ add pws_title pws_subjects ++++++++++++++++++++++++++++++++++++++
        # - add pws_title and pws_subjects
        if 'pws_title' in data_dict or 'pws_subjects' in data_dict:

            upload_pws_title = data_dict.get('pws_title')
            upload_pws_subjects = data_dict.get('pws_subjects')

            caption_txt = ''
            not_added_single_plural = not_added_str
            if upload_pws_title:
                if upload_pws_subjects:
                    caption_txt = str(_('Assignment title and -subjects'))
                    not_added_single_plural = not_added_plural_str
                else:
                    caption_txt = str(_('Assignment title'))
            elif upload_pws_subjects:
                caption_txt = str(_('Assignment subjects'))
                not_added_single_plural = not_added_plural_str

            studsubj, lookup_pws_title, lookup_pws_subjects = None, None, None
            studsubj_with_pws_found = False
            multiple_studsubj_with_pws_found = False

        # - get student_subjects with subjecttype has_pws = True
            # check if there is none or multiple
            studsubjects = stud_mod.Studentsubject.objects.filter(
                    student=student,
                    schemeitem__subjecttype__has_pws=True)
            if studsubjects:
                for studsubj in studsubjects:
                    if not studsubj_with_pws_found:
                        lookup_pws_title = studsubj.pws_title
                        lookup_pws_subjects = studsubj.pws_subjects
                        studsubj_with_pws_found = True
                    else:
                        multiple_studsubj_with_pws_found = True
                        studsubj = None
                        lookup_pws_title = None
                        lookup_pws_subjects = None
            if not studsubj_with_pws_found:
                log_list.append(''.join( (caption_txt, not_added_single_plural, '\n', str(_('Candidate has no subject with assignment.')))))
            elif multiple_studsubj_with_pws_found:
                log_list.append(''.join( (caption_txt, not_added_single_plural, '\n', str(_('Candidate has multiple subjects with assignment.')))))
            else:
                # only save if value has changed, skip if upload_pws has no value
                save_studsubj = False
                if upload_pws_title and upload_pws_title != lookup_pws_title:
                    studsubj.pws_title = lookup_pws_title
                    save_studsubj = True
                if upload_pws_subjects and upload_pws_subjects != lookup_pws_subjects:
                    studsubj.pws_subjects = lookup_pws_subjects
                    save_studsubj = True
                if not is_test and save_studsubj:
                    studsubj.save(request=request)
                # add field_dict to studsubj_dict
                   # studsubj_dict[field] = field_dict
        # +++ end of add pws_title pws_subjects ++++++++++++++++++++++++++++++++++++++
        """
# - dont save data when it is a test run
        # TODO save_student is always false. Can save_student be deleted?
        if save_student and not is_test:

    # - get scheme and update in student, also remove if necessary
            new_scheme = subj_mod.Scheme.objects.get_or_none(
                department=student.department,
                level=student.level,
                sector=student.sector)
            setattr(student, 'scheme', new_scheme)

            try:
                student.save(request=request)
                #studsubj_dict['id']['pk'] = student.pk
                #studsubj_dict['id']['ppk'] = student.company.pk
            except Exception as e:
# - give error msg when creating student failed
                error_str = str(_("An error occurred. The student data is not saved."))
                # TODO
                code_text = '---'
                log_list.append(" ".join((code_text, error_str)))
                #studsubj_dict['row_error'] = error_str

    is_existing, is_new_student= False, False
    return studsubj_rows, is_existing, is_new_student, has_error
# --- end of upload_studentsubject_from_datalist


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def import_permits(upload_dict, user_lang, logging_on, request):  # PR2021-04-20
    if logging_on:
        logger.debug(' ============= import_permits ============= ')
        logger.debug('upload_dict: ' + str(upload_dict))

# - get info from upload_dict
    is_test = upload_dict.get('test', False)
    awpColdef_list = upload_dict.get('awpColdef_list')
    data_list = upload_dict.get('data_list')

    params = {}
    logfile = []

    if awpColdef_list and data_list:

        if logging_on:
            logger.debug('awpColdef_list: ' + str(awpColdef_list))
            # - create logfile
            today_dte = af.get_today_dateobj()
            today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

            logfile = [c.STRING_DOUBLELINE_80,
                       str(_('Upload permissions')) + ' ' + str(_('date')) + ': ' + str(today_formatted),
                       c.STRING_DOUBLELINE_80]
            # awpColdef_list: ['c_abbrev', 'page', 'role', 'action', 'usergroups', 'sequence']
            lookup_field_missing = False
            for lookup_field in ('c_abbrev', 'page', 'role', 'action'):
                if lookup_field not in awpColdef_list:
                    lookup_field_missing = True
            if lookup_field_missing:
                info_txt = str(_('Not all required fields to lookup permissions are linked. Permits cannot be uploaded.'))
                logfile.append(c.STRING_SPACE_05 + info_txt)
            else:
                if is_test:
                    info_txt = str(_("This is a test. The permission data are not saved."))
                else:
                    info_txt = str(_("The permission data are saved."))
                logfile.append(c.STRING_SPACE_05 + info_txt)
                logfile.append(' ')

# +++++ loop through data_list
        update_list = []
        for data_dict in data_list:
            # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html
            # for key, val in student.items():
            # #logger.debug( str(key) +': ' + val + '" found in "' + str(student) + '"')

# - upload permit
            update_dict = upload_permit(data_dict, is_test, logfile, logging_on, request)
            # json_dumps_err_list = json.dumps(msg_list, cls=af.LazyEncoder)
            if update_dict:  # 'Any' returns True if any element of the iterable is true.
                update_list.append(update_dict)

        if update_list:  # 'Any' returns True if any element of the iterable is true.
            params['data_list'] = update_list
    if logfile:  # 'Any' returns True if any element of the iterable is true.
        params['logfile'] = logfile
            # params.append(new_student)
    return params
# - end of import_permits


def upload_permit(data_dict, is_test, logfile, logging_on, request):   # PR2021-04-20
    if logging_on:
        logger.debug('----------------- upload_permit  --------------------')
        logger.debug('data_dict: ' + str(data_dict))

    """
    'data_list': [{'rowindex': 0, 'c_abbrev': 'cur', 'page': 'page_all', 'role': 'permit_userpage', 'action': 'admin', 'usergroups': '128', 'sequence': '10'},
        {'rowindex': 1, 'c_abbrev': 'cur', 'page': 'page_exams', 'role': 'view_page', 'action': 'admin;read', 'usergroups': '8', 'sequence': '10'},
        {'rowindex': 2, 'c_abbrev': 'cur', 'page': 'page_grade', 'role': 'read_note', 'action': 'admin;anlz;auth1;auth2;auth3;edit;read', 'usergroups': '8', 'sequence': '60'}]}
    """

# - get info from data_dict
    row_index = data_dict.get('rowindex')
    c_abbrev = data_dict.get('c_abbrev')

# - create update_dict
    update_dict = {'table': 'permit', 'rowindex': row_index}

# - get country based on c_abbrev 'Cur' in excel file, not requsr_country
    country = af.get_country_instance_by_abbrev(c_abbrev)
    if country is None:
        msg_err = ' '.join((str(_('Country')), "'" + c_abbrev + "'", str(_('is not found'))))
        update_dict['row_error'] = msg_err
        logfile.append(c.STRING_SPACE_05 + msg_err)
    else:

# get required fields
        page = data_dict.get('page')
        role = data_dict.get('role')
        action = data_dict.get('action')

# - check of required fields have value
        if not c_abbrev or not page or not role or not action:
            missing_str = ''
            if not page:
                missing_str += str(_('Page')).lower()
            if not role:
                if missing_str:
                    missing_str += ', '
                missing_str += str(_('Organization')).lower()
            if not action:
                if missing_str:
                    missing_str += ', '
                missing_str += str(_('Action')).lower()
            if missing_str:
                msg_err = ' '.join((str(_('Row')), str(row_index), str(_('is missing required field:')), missing_str))
                update_dict['row_error'] = msg_err
                logfile.append(c.STRING_SPACE_05 + msg_err)
        else:

# get non-required fields
            usergroups = data_dict.get('usergroups')
            sequence = data_dict.get('sequence')

# - check if there is already a permit with this  page, role and action
            try:
                is_created = False
                permit = acc_mod.Userpermit.objects.filter(
                    country=country,
                    role=role,
                    page__iexact=page,
                    action__iexact=action
                ).order_by('-pk').first()
                if permit is None:
                    permit = acc_mod.Userpermit(
                        country=country,
                        role=role,
                        page=page,
                        action=action
                    )
                    is_created = True
                setattr(permit, 'usergroups', usergroups)
                setattr(permit, 'sequence', sequence)

# - dont save data when it is a test run
                if not is_test:
                    permit.save(request=request)
                is_updated_str = _('is created.') if is_created else _('is updated.')
                msg_err = ' '.join((str(_('Row')), str(row_index), country.abbrev, page, str(role), action, str(is_updated_str)))
                logfile.append(c.STRING_SPACE_05 + msg_err)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_err = ' '.join((str(_('Error in row')), str(row_index), ":" , str(e)))
                update_dict['row_error'] = msg_err
                logfile.append(c.STRING_SPACE_05 + msg_err)

    return update_dict
# --- end of upload_permit
