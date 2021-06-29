# PR2020-12-06
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse

from django.utils.decorators import method_decorator
from django.utils.translation import activate, pgettext_lazy, ugettext_lazy as _

from django.views.generic import View

from accounts import models as acc_mod
from accounts import views as acc_view
from awpr import constants as c
from awpr import functions as af
from awpr import settings as s
from awpr import downloads as dl

from schools import models as sch_mod
from students import models as stud_mod
from students import validators as stud_val
from students import views as stud_view
from subjects import models as subj_mod

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
                'importtable': 'import_permits', 
                'sel_examyear_pk': None, 
                'sel_schoolbase_pk': None, 
                'sel_depbase_pk': None, 
                'worksheetname': 'Permits', 
                'noheader': False}
                """

                if new_setting_dict:
                    # setting_keys are: 'import_student', import_studentsubject
                    # {importtable: "import_studentsubject", ...}
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
class UploadImportDataView(View):  # PR2020-12-05 PR2021-02-23
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request, *args, **kwargs):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UploadImportDataView ============= ')

        update_dict = {}
        has_permit = False
        if request.user is not None and request.user.schoolbase is not None:

            # -  get user_lang
            requsr_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(requsr_lang)

            has_permit = False
            if request.user and request.user.country and request.user.schoolbase:
                permit_list, requsr_usergroups_listNIU = acc_view.get_userpermit_list('page_student', request.user)
                has_permit = 'permit_crud' in permit_list
            if not has_permit:
                err_html = _("You don't have permission to perform this action.")
                update_dict['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))

        if has_permit:
            if request.POST['upload']:
                upload_dict = json.loads(request.POST['upload'])

    # - Reset language
                # PR2019-03-15 Debug: language gets lost, get request.user.lang again
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

                importtable = upload_dict.get('importtable')
                if importtable == 'import_student':
                    update_dict = import_students(upload_dict, user_lang, request)
                elif importtable == 'import_studentsubject':
                    update_dict = import_studentsubjects(upload_dict, user_lang, logging_on, request)
                elif importtable == 'import_permits':
                    update_dict = import_permits(upload_dict, user_lang, logging_on, request)
        if logging_on:
            logger.debug('update_dict: ' + str(update_dict) + ' ' + str(type(update_dict)))

        return HttpResponse(json.dumps(update_dict, cls=af.LazyEncoder))
# - end of UploadImportDataView



# ========  import_students  ======= PR2020-12-06 PR2021-02-23 PR2021-06-17
def import_students(upload_dict, user_lang, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ============= import_students ============= ')
        #logger.debug('upload_dict: ' + str(upload_dict))

    _update_dict = {}

# - get selected examyear, school and department from usersettings
    sel_examyear, sel_school, sel_department, may_edit, msg_list = \
        dl.get_selected_ey_school_dep_from_usersetting(request)

# - get info from upload_dict
    is_test = upload_dict.get('test', False)
    awpColdef_list = upload_dict.get('awpColdef_list')
    data_list = upload_dict.get('data_list')
    dateformat = upload_dict.get('dateformat', '')

    student_list = []
    log_list = []

    count_total, count_existing, count_new, count_error, count_bisexam = 0, 0, 0, 0, 0

    if awpColdef_list and data_list and sel_school and sel_department:

# - create log_list
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

        school_name = sel_school.base.code + ' ' + sel_school.name
        log_list = [c.STRING_DOUBLELINE_80,
                   '  ' + school_name + '  -  ' +
                            str(_('Upload candidates')) + ' ' + str(_('date')) + ': ' + str(today_formatted),
                   c.STRING_DOUBLELINE_80]

        if is_test:
            info_txt = str(_("This is a test. The candidate data are not saved."))
            log_list.append(c.STRING_SPACE_05 + info_txt)
        else:
            info_txt = str(_("The candidate data are saved."))
            log_list.append(c.STRING_SPACE_05 + info_txt)

        if dateformat:
            info_txt = str(_("The date format is: '%(fld)s'.") % {'fld': dateformat})
            log_list.append(c.STRING_SPACE_05 + info_txt)

        log_list.append(c.STRING_SPACE_05)

# - get double_entrieslist, a list of trimmed idnumbers without dots that occur multiple times in data_list
        double_entrieslist = stud_val.get_double_entrieslist_from_uploadfile(data_list)

        if logging_on:
            logger.debug('school_name: ' + str(school_name))
            logger.debug('dateformat: ' + str(dateformat))
            logger.debug('double_entrieslist: ' + str(double_entrieslist))

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++ loop through data_list
        update_list = []

        bisexam_dict = {}
        for data_dict in data_list:
            # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html
            #for key, val in student.items():
            # #logger.debug( str(key) +': ' + val + '" found in "' + str(student) + '"')

# - upload student
            student_dict, is_existing, is_new_student, has_error, might_be_bisexam = upload_student(
                data_dict=data_dict,
                awpColdef_list=awpColdef_list,
                examyear=sel_examyear,
                school=sel_school,
                department=sel_department,
                is_test=is_test,
                dateformat=dateformat,
                double_entrieslist=double_entrieslist,
                log_list=log_list,
                bisexam_dict=bisexam_dict,
                request=request)
            #json_dumps_err_list = json.dumps(msg_list, cls=af.LazyEncoder)
            if student_dict:
                student_list.append(student_dict)

            count_total += 1
            if is_existing:
               count_existing += 1
            if is_new_student:
               count_new += 1
            if has_error:
               count_error += 1
            #if has_error:
            #   count_bisexam += 1
# +++++ end of loop through data_list
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# - return html with number of students, existing, new and erros
    update_dict = {'result': crate_result_html(count_total, count_existing, count_new, count_error),
                    'log_list': log_list,
                    'student_list': student_list}

    return update_dict
# - end of import_students


# ========  upload_student  ======= # PR2019-12-17 PR2020-06-03 PR2021-06-19
def upload_student(data_dict, awpColdef_list, examyear, school, department, is_test, dateformat, double_entrieslist, log_list, bisexam_dict, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- upload_student  --------------------')
        logger.debug('data_dict: ' + str(data_dict))

# - required fields are: base, school, department, lastname, firstname and
    # the lookup fields 'examnumber' or 'idnumber' are not required in model, but one of them is required for upload
    """
    upload_dict{
    'importtable': 'student', 
    'awpColdef_list': ['examnumber', 'lastname', 'firstname', 'classname', 'birthdate', 'idnumber', 'gender', 'sector'], 
    'test': True, 
    'data_list': [
        {'rowindex': 0, 'examnumber': '68', 'lastname': 'Janssens', 'firstname': 'Andreas Jil Sander Zagarias', 'classname': 'H5', 'birthdate': 'xxx', 'idnumber': '1986101906', 'gender': 'x', 'sector': 'EM'}, 
        {'rowindex': 1, 'examnumber': '34', 'lastname': 'El Chami', 'firstname': 'Omar TEST', 'classname': 'H5', 'birthdate': '25 xx 2020', 'idnumber': 'ffdffsfwrakuuuuuuuuuuuussssssss', 'gender': 'm', 'sector': 'NT'}, 

    """
    error_list = []
    is_existing_student, is_new_student, has_error, might_be_bisexam = False, False, False, False

# - get variables from data_dict
    row_index = data_dict.get('rowindex', -1)
    id_number = data_dict.get('idnumber', '')
    last_name = data_dict.get('lastname', '')
    first_name = data_dict.get('firstname', '')
    prefix = data_dict.get('prefix', '')
    birth_date = data_dict.get('birthdate')

# base_pk only has vaue when user has ticked of 'same_student' after test_upload
    # insteaad of ccreating a new student_base, the pase_pk will be used and 'islinked' will be set True
    base_pk = data_dict.get('base_pk')

    id_number_nodots = id_number.strip().replace('.', '') if id_number else ''
    lastname_stripped = last_name.strip() if last_name else ''
    firstname_stripped = first_name.strip() if first_name else ''
    prefix_stripped = prefix.strip() if prefix else ''
    full_name = get_fullname(lastname_stripped, firstname_stripped, prefix_stripped)
    birthdate_iso = get_birthdate_iso(birth_date, dateformat, error_list)

    if logging_on:
        logger.debug('id_number_nodots: ' + str(id_number_nodots))
        logger.debug('full_name: ' + str(full_name))
        logger.debug('birthdate_iso: ' + str(birthdate_iso))

# - create student_dict
    student_dict = {'rowindex': row_index}

# - validate double occurrence in upload file
    has_error = stud_val.validate_double_entries_in_uploadfile(id_number_nodots, double_entrieslist, error_list)
    if not has_error:
# - validate length of name and idnumber
        has_error = stud_val.validate_name_idnumber_length(
            id_number_nodots, lastname_stripped, firstname_stripped, prefix_stripped, error_list)
    if logging_on:
        logger.debug('has_error: ' + str(has_error))
        logger.debug('error_list: ' + str(error_list))
        logger.debug('log_list: ' + str(log_list))

    student = None
    if not has_error:
# - lookup student in database
        # multiple_found returns lookup_value, returns None when 0 or 1 found
        student, is_new_student, has_error = lookup_student(school, department, id_number_nodots, full_name, is_test, error_list)

    if not has_error:
        if student:
            is_existing_student = True
            student_dict['student_pk'] = student.pk
        else:
# - create new student when student not found in database
            base = None
            is_linked = False
            # base_pk only has vaue when user has ticked of 'same_student' after test_upload
            # insteaad of creating a new student_base, the pase_pk will be used and 'islinked' will be set True
            if base_pk:
                base = stud_mod.Studentbase.objects.filter( pk=base_pk,country=request.user.country)

    # - create base record. Create also saves new record
            if base:
                is_linked = True
            else:
                base = stud_mod.Studentbase.objects.create(country=request.user.country)
            if logging_on:
                logger.debug('student base: ' + str(base))

    # - create base record. Create also saves new record
            student = stud_mod.Student(
                base=base,
                school=school,
                department=department,
                idnumber=id_number_nodots,
                lastname=lastname_stripped,
                firstname=firstname_stripped,
                prefix=prefix_stripped,
                islinked=is_linked
            )
            if student:
                save_instance = is_test
                student_dict['created'] = True
            else:
    # - give error msg when creating student failed
                error_list.append(str(_("An error occurred.")))

#@@@@@@@@@@@@@@@$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# -- check for doubles, only when is new student
            double_dict = validate_students_doubles(request.user.country, id_number_nodots,
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

# create log for this student

            skipped_str = full_name + str(_(' will be skipped.')) if is_test else str(_(' is skipped.'))
            is_added_str = str(_(' will be added.')) if is_test else str(_(' is added.'))
            not_added_str = str(_(' will not be added.')) if is_test else str(_(' is not added.'))

    student_header = ''.join(((id_number_nodots + c.STRING_SPACE_10)[:10], c.STRING_SPACE_05, full_name))
    if has_error:
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

    return student_dict, is_existing_student, is_new_student, has_error, might_be_bisexam
# --- end of upload_student



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


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# funstions for upload

# ========  get_fullname  ======= PR2021-06-19
def get_fullname(lastname_stripped, firstname_stripped, prefix_stripped):
    full_name = '---'

    if lastname_stripped:
        full_name = lastname_stripped
    if prefix_stripped:  # put prefix before last_name
        full_name = prefix_stripped + ' ' + full_name
    if firstname_stripped:  # put first_name after last_name
        full_name += ', ' + firstname_stripped

    return full_name


# ========  get_fullname  ======= PR2021-06-19
def get_birthdate_iso(birth_date, dateformat, error_list):
    # function converts birth_date to iso, checks for valid birthdate

    birthdate_iso = None

    date_iso = af.get_dateISO_from_string(birth_date, dateformat)
    birthdate_dte = af.get_date_from_ISO(date_iso)  # datefirst_dte: 1900-01-01 <class 'datetime.date'>
    if birthdate_dte is None:
        error_list.append(str(_("'%(val)s' is not a valid date.") % {'val': birth_date}))
    else:
        birthdate_iso = birthdate_dte.isoformat()

    return birthdate_iso

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# ========  import_students_testupload  ======= PR2021-06-17
def import_students_testupload(school, department, upload_dict, user_lang, request):
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
        count_existing, count_new, count_error, count_bisexam = 0, 0, 0,0
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
                    else:
                        birthdate_iso = birthdate_dte.isoformat()
# -- check for doubles
                double_dict = validate_students_doubles(request.user.country, id_number_nodots, lastname_stripped, firstname_stripped, birthdate_iso)
                if logging_on:
                    logger.debug('double_dict: ' + str(double_dict))
                if double_dict:
                    count_bisexam += 1
                    bisexam_dict[row_index] = double_dict
                    if logging_on:
                        logger.debug('double_dict: ' + str(double_dict))
                        logger.debug('bisexam_dict: ' + str(bisexam_dict))
# +++++ end of loop through data_list

        # return html with number of students, existing, new and erros
        update_dict['result'] = crate_result_html(count_existing, count_new, count_error)

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


def crate_result_html(count_total, count_existing, count_new, count_error):  # PR2021-06-18
    # function returns an html string with number of students, existing, new and erros

    result_html = ''.join(("<h6 class='mx-2 mt-2 mb-0'>", str(_('Test results')), '</h6>'))
    if count_total:
        result_html += ''.join(("<p>",
                                str(_("The uploaded file has %(count)s %(cnd)s:")
                                    % {'count': count_total,
                                       'cnd': _('candidates') if count_total > 1 else _('candidate')}),
                                "</p>"))
        result_html += "<ul class='mb-0'>"
        if count_existing:
            result_html += ''.join(("<li>",
                                    str(_("%(count)s %(cnd)s already %(exs)s, changes will be saved.")
                                        % {'count': count_existing,
                                           'cnd': _('candidates') if count_existing > 1 else _('candidate'),
                                           'exs': _('exist') if count_existing > 1 else _('exists')}),
                                    "</li>"))
        if count_new:
            result_html += ''.join(("<li>",
                                    str(_("%(count)s %(cnd)s %(nw)s.")
                                        % {'count': count_new,
                                           'cnd': _('candidates') if count_new > 1 else _('candidate'),
                                           'nw': _('are new and will be added') if count_new > 1 else _(
                                               'is new and will be added')}),
                                    "</li>"))
        if count_error:
            result_html += ''.join(("<li>",
                                    str(_("%(count)s %(cnd)s %(skip)s.")
                                        % {'count': count_error,
                                           'cnd': _('candidates') if count_error > 1 else _('candidate'),
                                           'skip': _('have errors and will be skipped') if count_error > 1 else _(
                                               'has an error and will be skipped')}),
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
                                str(_('The uploaded file has no candidates.')),
                                "</p>"))

    result_html += ''.join(("<h6 class='mx-2 mt-4 mb-0'>",
                            str(_("Possible bis-candidates")),
                            "</h6>"))

    result_html += ''.join(("<p>",
                            str(_("At %(count)s new %(cnd)s, AWP has found candidates in previous years, who might be the same person as the candidate, you are about to upload.")
                                % {'count': count_total,
                                   'cnd': _('candidates') if count_total > 1 else _('candidate')}),
                            "</p><p>",
                            str(_("If that is the case, you must link the existing candidate to the new candidate.")),
                            "</p><p>",
                            str(_("Click the arrow buttons below, to loop through the candidates.")),
                            "</p>"))

    return result_html
# - end of crate_result_html


def validate_students_doubles(requsr_country, id_number, last_name, first_name, birthdate_iso):  # PR2021-06-18
    # function returns list of trimmed idnumbers without dots that occur multiple times in data_list

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
        err_str = str(_("ID-number '%(val)s' exists multiple times this year ") % {'val': id_number_nodots})
        if found_in_diff_dep:
            if found_in_this_dep:
                err_str = str(_("in multiple departments of your school."))
            else:
                err_str = str(_("in other departments of your school."))
        elif found_in_this_dep:
            err_str = str(_("in this department of your school."))

    elif row_count == 1:
        if found_in_diff_dep:
            err_str = str(_("ID-number '%(val)s' already exists this year in a different department of your school.") % {'val': id_number_nodots})
        else:
            # return student_pk when student only occurs once and is in this department
            student_pk = row_pk

    else:
        not_found = True

    if logging_on:
        logger.debug('not_found: ' + str(not_found))
        logger.debug('err_str: ' + str(err_str))

    return student_pk, not_found, err_str


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def lookup_student(school, department, id_number_nodots, upload_studentname, is_test, error_list):  # PR2019-12-17 PR2020-12-06 PR2020-12-31  PR2021-02-27  PR2021-06-19
    # function searches for existing student by idnumber in this school and this examyear, all departments
    # gives error if multiple found, or found in differenet department
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------- lookup_student ----------- ')
        logger.debug('school: ' + str(school))
        logger.debug('department: ' + str(department))
        logger.debug('id_number_nodots: ' + str(id_number_nodots))

    student = None
    not_found = False
    has_error = False

# - search student in this school and department by idnumber
    if id_number_nodots:

# - check if lookup_value already exists in this school (all departments
        students = stud_mod.Student.objects.filter(
            idnumber__iexact=id_number_nodots,
            school=school)

        row_count, not_found, found_in_this_dep, found_in_diff_dep, err_str = 0, False, False, False, ''

        for row in students:
            row_count += 1
            if row.department_id == department.pk:
                found_in_this_dep = True
                student = row
            else:
                found_in_diff_dep = True

        if logging_on:
            logger.debug('row_count: ' + str(row_count))

        if row_count == 0:
            student = None
            not_found = True

        elif row_count == 1:
            if found_in_diff_dep:
                student = None
                has_error = True
                err_str = str(_("ID-number '%(val)s' already exists this year in a different department of your school.") % {'val': id_number_nodots})
            else:
                # return student when student only occurs once and is in this department
                pass

        elif row_count > 1:
            student = None
            has_error = True
            err_str = str(_("ID-number '%(val)s' exists multiple times this year ") % {'val': id_number_nodots})
            if found_in_diff_dep:
                if found_in_this_dep:
                    err_str = str(_("in multiple departments of your school."))
                else:
                    err_str = str(_("in other departments of your school."))
            elif found_in_this_dep:
                err_str = str(_("in this department of your school."))

        if logging_on:
            logger.debug('lookup student: ' + str(student))
            logger.debug('found_in_diff_dep: ' + str(found_in_diff_dep))

        if has_error:
            skipped_str = upload_studentname + str(_(' will be skipped.')) if is_test else str(_(' is skipped.'))
            error_list.append(' '.join((skipped_str, err_str)))

        if logging_on:
            logger.debug('student: ' + str(student))
            logger.debug('not_found: ' + str(not_found))
            logger.debug('err_str: ' + str(err_str))
            logger.debug('----------- end of lookup_student ---- ')

    return student, not_found, has_error
# --- end of lookup_student


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_student(upload_dict, request):
    # --- create student # PR2019-07-30 PR2020-09-11

    student = None
    msg_err = None

# - get parent
    parent = request.user.company
    if parent:

# - get value of 'code'
        code = None
        code_dict = upload_dict.get('code')
        if code_dict:
            code = code_dict.get('value')
        if code:
# - validate code checks null, max len and exists
            msg_err = stud_val.validate_code_name_identifier(
                table='student',
                field='code',
                new_value=code,
                is_absence=False,
                parent=parent,
                update_dict={},
                msg_dict={},
                request=request,
                this_pk=None)
# - create and save studentstudent
            if not msg_err:
                try:
                    student = stud_mod.student(
                        company=parent,
                        code=code)
                    student.save(request=request)
                except:
                    msg_err = str(_("An error occurred. Candidate '%(val)s' could not be added.") % {'val': code})

    return student, msg_err


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
            'importtable': 'import_studentsubject', 
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
            depbase = sch_mod.Departmentbase.objects.get_or_none(pk=sel_depbase_pk, country=request.user.country)
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
                    update_dict = upload_studentsubject(data_dict, lookup_field, lookup_value, occurrences_in_datalist,
                                                  count_subjectbase_dict, subject_code_dict, is_test, examyear, school, department, logfile, logging_on, request)
                    # json_dumps_err_list = json.dumps(msg_list, cls=af.LazyEncoder)
                    if update_dict:  # 'Any' returns True if any element of the iterable is true.
                        update_list.append(update_dict)

                if update_list:  # 'Any' returns True if any element of the iterable is true.
                    params['data_list'] = update_list
            if logfile:  # 'Any' returns True if any element of the iterable is true.
                params['logfile'] = logfile
                    # params.append(new_student)
    return params
# - end of import_studentsubjects


def subjectbase_code_dict(department):  # PR2021-02-27
    # get subject_codes from subjects of this department
    code_dict = {}
    schemeitems = subj_mod.Schemeitem.objects.filter(scheme__department=department)
    for schemeitem in schemeitems:
        subject_base = schemeitem.subject.base
        if subject_base and  subject_base.id not in code_dict:
            code_dict[subject_base.id] = subject_base.code
    return code_dict


def count_subjectbase_in_scheme(department):  # PR2021-02-27
    #logger.debug('----------------- count_subjectbase_in_scheme  --------------------')
    # function counts how many times a subject occurs in a scheme
    # when a subjects occurs only once, a subjecttype is not needed to add the subject to a student
    # output:
    # count_dict: {8: {20: 1, 3: 1, 4: 1, 1: 1, 6: 2, 7: 2, 10: 1, 27: 1, 29: 1, 31: 1, 39: 1, 40: 1, 41: 1, 46: 1},
    #              7: {3: 1, 4: 1, 1: 1, 6: 1, 7: 1, 10: 1, 15: 1, 27: 1, 29: 1, 31: 1, 33: 1, 34: 1, 35: 1, 36: 1, 37: 1, 38: 1, 46: 1},
    count_dict = {}
    schemeitems = subj_mod.Schemeitem.objects.filter(scheme__department=department)
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


def upload_studentsubject(data_dict, lookup_field, lookup_value, occurrences_in_datalist, count_subjectbase_dict,
                          subject_code_dict, is_test, examyear, school, department, logfile, logging_on, request):  # PR2021-02-26
    if logging_on:
        logger.debug('----------------- upload_studentsubject  --------------------')
        logger.debug('data_dict: ' + str(data_dict))

    """
    data_dict: {'rowindex': 0, 'examnumber': '63', 'idnumber': '1999112405', 
                    'pws_title': 'titel werkstuk', 'pws_subjects': 'vakken werkstuk',     
           (format of subjects: {subjectBasePk: subjecttypeBasePk, ..})
    'subjects': {'1': 4, '3': 0, '4': 0, '10': 0, '15': 0, '27': 0, '29': 0, '31': 0, '36': 0, '42': 7, '46': 0}}
    """

# - get row_index and lookup info from data_dict
    row_index = data_dict.get('rowindex', -1)

# - create update_dict
    update_dict = {'id': {'table': 'studentsubject', 'rowindex': row_index}}

# - lookup student in database
    # multiple_found and exceeded_length return the lookup_value of the error field
    lookup_field_caption = af.get_dict_value(c.CAPTIONS, ('student', lookup_field), '')
    lookup_field_capitalized = '-'
    if lookup_field_caption:
        lookup_field_capitalized = lookup_field_caption.capitalize()
    if logging_on:
        logger.debug('lookup_field: ' + str(lookup_field) + ' lookup_field_caption: ' + str(lookup_field_caption))
        logger.debug('lookup_value: ' + str(lookup_value))

    student, multiple_found, found_in_diff_dep, exceeded_length, is_existing_student = None, None, None, False, False
    student_name = '---'
    if lookup_value:
        # multiple_found returns lookup_value, returns None when 0 or 1 found
        student, exceeded_length, multiple_found, found_in_diff_dep = \
            lookup_student(school, department, lookup_field, lookup_value)
        if student:
            #student_name = student.fullname
            student_name = student.fullnamewithinitials
        else:
            student_name = '---'
    if logging_on:
        logger.debug('student_name: ' + str(student_name))

# - give row_error when lookup went wrong
    skipped_str = student_name + str(_(' will be skipped.')) if is_test else str(_(' is skipped.'))
    is_added_str = str(_(' will be added.')) if is_test else str(_(' is added.'))
    not_added_str = str(_(' will not be added.')) if is_test else str(_(' is not added.'))
    not_added_plural_str = str(pgettext_lazy('plural', ' will not be added.')) if is_test else str(pgettext_lazy('plural', ' is not added.'))

    logfile.append(c.STRING_SPACE_05)

    msg_err = None
    log_str = ''
    if occurrences_in_datalist > 1:
        log_str = str(_("%(fld)s '%(val)s' is not unique in Excel file.") % {'fld': lookup_field_capitalized, 'val': lookup_value})
        msg_err = ' '.join((skipped_str, log_str))
    elif not lookup_value:
        log_str = str(_("No value for lookup field: '%(fld)s'.") % {'fld': lookup_field_caption})
        msg_err = ' '.join((skipped_str, log_str))
    elif found_in_diff_dep:
        log_str = str(_("Value '%(fld)s' already exists in a different department.") % {'fld': lookup_value})
        msg_err = ' '.join((skipped_str, log_str))
    elif multiple_found:
        log_str = str(_("Value '%(fld)s' is found multiple times.") % {'fld': lookup_value})
        msg_err = ' '.join((skipped_str, log_str))

    if msg_err:
        logfile.append(student_name + str(_(' is not added.')))
        update_dict['row_error'] = msg_err
        update_dict[lookup_field] = {'error': msg_err}

        logfile.append(c.STRING_SPACE_05 + log_str)
        if logging_on:
            logger.debug('lookup-went-wrong error: ' + str(log_str))
    else:
        save_instance = False

        if student:
            logfile.append(student.fullname + ' ' + str(student.scheme))
            student_scheme_pk = student.scheme_id
            student_scheme = student.scheme

# - get list of 'count-of-occurrencies' of subjects of this scheme
            # count_scheme_subjectbase: {20: 1, 3: 1, 4: 1, 1: 1, 6: 2, 7: 2, ... }
            count_scheme_subjectbase = count_subjectbase_dict[student_scheme_pk]

# - create list of subjects of this student - to speed up search
            # student_subjectbase_list: [29, 7, 41, 27, 6, 46, 3]
            student_subjectbase_dict = {}
            studsubjects = stud_mod.Studentsubject.objects.filter(student=student)
            for studsubject in studsubjects:
                pk_int = studsubject.schemeitem.subject.base_id
                subject_code = studsubject.schemeitem.subject.base.code
                if pk_int in student_subjectbase_dict:
                    caption_txt = c.STRING_SPACE_05 + (subject_code + c.STRING_SPACE_10)[:8]
                    log_str = str(_('WARNING: This candidate already has this subject multiple times.'))
                    logfile.append(caption_txt + ' ' + log_str)
                else:
                    student_subjectbase_dict[pk_int] = subject_code
            if logging_on:
                logger.debug('..... student: ' + str(student))
                logger.debug('     student_scheme: ' + str(student_scheme_pk) + ' ' + str(student.scheme))
                logger.debug('     count_scheme_subjectbase: ' + str(count_scheme_subjectbase))
                logger.debug('     student_subjectbase_list: ' + str(student_subjectbase_dict))

            # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
            # solved bij wrapping with str()

# +++ subjects ++++++++++++++++++++++++++++++++++++++
            if 'subjects' in data_dict:
                # 'subjects': {'1': 4, '3': 0, '4': 0, '10': 0, '15': 0, '27': 0, '29': 0, '31': 0, '36': 0, '42': 7, '46': 0}
                subjects = data_dict.get('subjects')
                if subjects:
                    for subjectbase_pk_str, upload_subjecttypeBasePk in subjects.items():
                        upload_subjectBasePk = int(subjectbase_pk_str)
                        # subject_code_dict contains subject_codes from all subjects of this department,
                        # to make sure subject_code_dict als ohas value when subject not in scheme of student
                        subject_code = subject_code_dict.get(upload_subjectBasePk, '---')
                        caption_txt = c.STRING_SPACE_05 + (subject_code + c.STRING_SPACE_10)[:8]

    # - skip if student already has this subject
                        if upload_subjectBasePk in student_subjectbase_dict:
                            # TODO save new subjecttype if different from saved subjecttype
                            log_str = ' '.join( (caption_txt, not_added_str, str(_('This candidate already has this subject.'))))
                            logfile.append(log_str)
                            if logging_on:
                                logger.debug('        subject: ' + str(subject_code) + ' already exists')

    # - skip if this subject is not found in scheme
                        # count_scheme_subjectbase: {20: 1, 3: 1, 4: 1, 1: 1, 6: 2, 7: 2, 10: 1, 27: 1, 29: 1, 31: 1, 39: 1, 40: 1, 41: 1, 46: 1}
                        elif upload_subjectBasePk not in count_scheme_subjectbase:
                            log_str = ' '.join((caption_txt, not_added_str, str(_('This subject does not occur in this subject scheme.'))))
                            logfile.append(log_str)
                            if logging_on:
                                logger.debug('        subject: ' + str(subject_code) + ' not in subject scheme')
                        else:

    # - if student does not have this subject and subject is found in scheme:
                            count = count_scheme_subjectbase.get(upload_subjectBasePk, 0)
                            if logging_on:
                                logger.debug('        subject: ' + str(subject_code) + ' count: ' + str(count))

        # - when subject occurs only once in scheme:
# if subjecttype provided: check if the same, if not: add subject
                            if count == 1:
                                schemeitem, subjecttype_pk, subjecttype_abbrev = None, None, '---'
                # - get subject
                                subject = subj_mod.Subject.objects.get_or_none(
                                    base_id=upload_subjectBasePk,
                                    examyear=examyear)
                                if logging_on:
                                    logger.debug('        subject: ' + str(subject.name) + ' count: ' + str(count))

                                if subject:

                # - get schemeitem and upload_subjecttype
 # if so. or no upload subjecttype given, add subject to student
                                    schemeitem = stud_mod.Schemeitem.objects.get_or_none(
                                        scheme=student_scheme,
                                        subject=subject)
                                    if logging_on:
                                        logger.debug('        schemeitem: ' + str(schemeitem) + ' ' + str(type(schemeitem)))

                                    upload_subjecttype = subj_mod.Subjecttype.objects.get_or_none(
                                        base=upload_subjecttypeBasePk,
                                        examyear=examyear)
                                    if logging_on:
                                        logger.debug('        upload_subjecttype: ' + str(upload_subjecttype) + ' ' + str(type(upload_subjecttype)))

                # - check if lookup subjecttype is the same as the upload subjecttype
                                    if schemeitem:
                                        lookup_subjecttypeBasePk = schemeitem.subjecttype.base.pk
                                        subjecttype_abbrev = schemeitem.subjecttype.abbrev
                                        if logging_on:
                                            logger.debug( '        schemeitem: ' + str(subjecttype_abbrev))
                    # - skip if upload_subjecttypeBasePk has value and is not the same as lookup
                                        # upload_subjecttypeBasePk = 0 means: no value
                                        if upload_subjecttypeBasePk and upload_subjecttypeBasePk != lookup_subjecttypeBasePk:
                                            msg_err = _("Subject '%(subj)s - %(subjtype)s' does not occur in this subject scheme.") \
                                                      % {'subj': subject_code, 'subjtype': subjecttype_abbrev}
                                        else:
                    # - add studentsubject if upload- and lookup- subjecttype are the same or if no upload_subjecttype given
                                            studsubj, msg_err = stud_view.create_studsubj(student, schemeitem, request)
                                if msg_err:
                                    logfile.append(' '.join((caption_txt, msg_err)))
                                    logfile.append(' '.join((caption_txt, not_added_str, str(_('An error occurred.')) )))
                                else:
                                    logfile.append(' '.join((caption_txt, is_added_str, " (" + subjecttype_abbrev + ")" )))
                            elif count > 1:
                                log_str = ' '.join((caption_txt, not_added_str, str(_("Subject '%(subj)s' occurs multiple times in this subject scheme.\nPlease select a character."))))
                                logfile.append(log_str)

# +++ pws_title pws_subjects ++++++++++++++++++++++++++++++++++++++
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
                    logfile.append(''.join( (caption_txt, not_added_single_plural, '\n', str(_('Candidate has no subject with assignment.')))))
                elif multiple_studsubj_with_pws_found:
                    logfile.append(''.join( (caption_txt, not_added_single_plural, '\n', str(_('Candidate has multiple subjects with assignment.')))))
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
                    # add field_dict to update_dict
                       # update_dict[field] = field_dict

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
                    #update_dict['id']['ppk'] = student.company.pk
                except:
    # - give error msg when creating student failed
                    error_str = str(_("An error occurred. The student data is not saved."))
                    # TODO
                    code_text = '---'
                    logfile.append(" ".join((code_text, error_str)))
                    update_dict['row_error'] = error_str

    return update_dict
# --- end of upload_student



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
    country = sch_mod.get_country(c_abbrev)
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
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

"""
def StudentImportUploadDataViewXXX(upload_dict):  # PR2018-12-04 PR2020-12-06

    #logger.debug(' ============= StudentImportUploadDataView ============= ')

    if request.user is not None and request.user.examyear is not None:
        if request.user.schoolbase is not None and request.user.depbase is not None:
            # get school and department of this schoolyear
            school = sch_mod.School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
            department = sch_mod.Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()

            students = json.loads(request.POST['students'])

            params = []

            for student in students:

# ------------ import student   -----------------------------------
                #logger.debug(' ')
                #logger.debug('import student:')
                #logger.debug(str(student))

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
                        #logger.debug('student[level]: ' + str(student['level']))
                        if student['level'].isnumeric():
                            level_id = int(student['level'])
                            level = Level.objects.filter(id=level_id, examyear=request.user.examyear).first()
                if 'sector' in student:
                    if student['sector']:
                        #logger.debug('student[sector]: ' + str(student['sector']) + str(type(student['sector'])))
                        if student['sector'].isnumeric():
                            sector_id = int(student['sector'])
                            sector = Sector.objects.filter(id=sector_id, examyear=request.user.examyear).first()
                            #logger.debug('sector: ' + str(sector.name))
                scheme = Scheme.get_scheme(department, level, sector)

                if scheme:
                    #logger.debug('scheme: ' + str(scheme))

# ========== create new student, but only if no errors found
                if dont_add:
                    #logger.debug('Student not created: ')
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

                    #logger.debug(str(new_student.id) + ': Student ' + new_student.lastname_firstname_initials + ' created ')

                        # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html
                        # for key, val in student.items():
                        #    logger.debug( str(key) +': ' + val + '" found in "' + str(student) + '"')

                # json_dumps_err_list = json.dumps(msg_list, cls=af.LazyEncoder)
                if len(data) > 0:
                    params.append(data)
                # params.append(student)
"""

