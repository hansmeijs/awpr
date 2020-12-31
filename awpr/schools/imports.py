# PR2020-12-06
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from django.utils.decorators import method_decorator
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import activate, ugettext_lazy as _

from django.views.generic import View
from awpr import constants as c
from awpr import functions as af
from schools import functions as sf
from schools import models as sch_mod
from students import models as stud_mod
from subjects import models as subj_mod

import json
import logging

logger = logging.getLogger(__name__)


@method_decorator([login_required], name='dispatch')
class UploadImportSettingView(View):   # PR2020-12-05
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request, *args, **kwargs):
        logger.debug(' ============= UploadImportSettingView ============= ')

        updated_stored_setting = {}
        has_permit = False
        if request.user is not None and request.user.schoolbase is not None:
            # TODO has_permit = (request.user.is_perm_hrman)
            has_permit = True
        if has_permit:
            if request.POST['upload']:
                new_setting_dict = json.loads(request.POST['upload'])
                logger.debug('new_setting_dict' + str(new_setting_dict))
                # new_setting_dict{'importtable': 'import_student', 'sel_schoolbase_pk': 16, 'sel_examyear_pk': 6,
                # 'worksheetname': 'Compleetlijst', 'noheader': False}
                # 'sector': {'CM': 4, 'EM': 5}}
                if new_setting_dict:
                    # setting_keys: 'import_student', 'import_subject'
                    setting_key = new_setting_dict.get('importtable')

                    sel_schoolbase_pk = new_setting_dict.get('sel_schoolbase_pk')
                    sel_schoolbase = sch_mod.Schoolbase.objects.get_or_none(pk=sel_schoolbase_pk)
                    sel_examyear_pk = new_setting_dict.get('sel_examyear_pk')
                    sel_examyear = sch_mod.Examyear.objects.get_or_none(pk=sel_examyear_pk)

                    if setting_key and sel_schoolbase:
                        stored_setting_dict = sch_mod.Schoolsetting.get_jsonsetting(setting_key, sel_schoolbase)

                        logger.debug('stored_setting_dict' + str(stored_setting_dict))
                        new_stored_setting = {}
                        for import_key in ('worksheetname', 'noheader', 'coldef', 'department', 'level', 'sector'):
                            new_setting_value = new_setting_dict.get(import_key)
                            logger.debug('new_setting_value' + str(new_setting_value))

                            if new_setting_value is None and stored_setting_dict:
                                new_setting_value = stored_setting_dict.get(import_key)
                            if import_key is 'noheader' and  new_setting_value is None:
                                new_setting_value = False
                            logger.debug('new_setting_value' + str(new_setting_value))

                            if new_setting_value is not None:
                                new_stored_setting[import_key] = new_setting_value

                        logger.debug('new_stored_setting' + str(new_stored_setting))
                        if new_stored_setting:
                            sch_mod.Schoolsetting.set_jsonsetting(setting_key, new_stored_setting, sel_schoolbase)

        # get updated stored_setting from database, return tp page to update mimp_stored
                    #request_item_setting = {'setting_key': setting_key}
                    #updated_stored_setting['schoolsetting_dict'] = sf.get_schoolsetting(
                    #    request_item_setting, sel_examyear, sel_schoolbase, request)

        return HttpResponse(json.dumps(updated_stored_setting, cls=af.LazyEncoder))
# - end of UploadImportSettingView


@method_decorator([login_required], name='dispatch')
class UploadImportDataView(View):  # PR2020-12-05
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request, *args, **kwargs):
        logger.debug(' ============= UploadImportDataView ============= ')

        update_dict = {}
        has_permit = False
        if request.user is not None and request.user.schoolbase is not None:
            # TODO has_permit
            has_permit = True
        if has_permit:
            if request.POST['upload']:
                upload_dict = json.loads(request.POST['upload'])
                #logger.debug('upload_dict' + str(upload_dict))

                # new_setting_dict: {'importtable': 'student', 'coldefs': {'birthdate': 'GEB_DAT', 'classname': 'KLAS'}}
    # - Reset language
                # PR2019-03-15 Debug: language gets lost, get request.user.lang again
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

                importtable = upload_dict.get('importtable')
                if importtable == 'import_student':
                    update_dict = import_students(upload_dict, user_lang, request)

        return HttpResponse(json.dumps(update_dict, cls=af.LazyEncoder))
# - end of UploadImportDataView


def import_students(upload_dict, user_lang, request):  # PR2020-12-06
    logger.debug(' ============= import_students ============= ')

    logger.debug('upload_dict: ' + str(upload_dict))
# - get info from upload_dict
    is_test = upload_dict.get('test', False)
    dateformat = upload_dict.get('dateformat', '')
    awpColdef_list = upload_dict.get('awpColdef_list')
    data_list = upload_dict.get('data_list')
    sel_examyear_pk = upload_dict.get('sel_examyear_pk')
    sel_schoolbase_pk = upload_dict.get('sel_schoolbase_pk')
    sel_depbase_pk = upload_dict.get('sel_depbase_pk')

    params = {}
    if awpColdef_list and data_list:
        logger.debug('awpColdef_list: ' + str(awpColdef_list))

# - get lookup_field
        # lookup_field is field that determines if student alreay exist.
        # check if one of the fields 'examnumber', 'idnumber' exists
        # first in the list is lookup_field
        lookup_field = None
        if 'examnumber' in awpColdef_list:
            lookup_field = 'examnumber'
        elif 'idnumber' in awpColdef_list:
            lookup_field = 'idnumber'
        logger.debug( 'lookup_field: ' + str(lookup_field))

# - get examyear from sel_examyear_pk and request.user.country
        examyear = sch_mod.Examyear.objects.get_or_none(pk=sel_examyear_pk, country=request.user.country)

# - get school from sel_schoolbase_pk and sel_examyear_pk
        schoolbase = sch_mod.Schoolbase.objects.get_or_none(pk=sel_schoolbase_pk, country=request.user.country)
        school = sch_mod.School.objects.get_or_none(base=schoolbase, examyear=examyear)
        school_name = school.base.code + ' ' + school.name

        if school:
# - get department from sel_depbase_pk and sel_examyear_pk
            depbase = sch_mod.Departmentbase.objects.get_or_none(pk=sel_depbase_pk, country=request.user.country)
            department = sch_mod.Department.objects.get_or_none(base=depbase, examyear=examyear)

    # - create logfile
            today_dte = af.get_today_dateobj()
            today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

            logfile = [c.STRING_DOUBLELINE_80,
                       '  ' + school_name + '  -  ' +
                                str(_('Upload candidates')) + ' ' + str(_('date')) + ': ' + str(today_formatted),
                       c.STRING_DOUBLELINE_80]

            if lookup_field is None:
                info_txt = str(_('There is no field given to lookup candidates. Candidates cannot be uploaded.'))
                logfile.append(c.STRING_INDENT_5 + info_txt)
            else:
                if is_test:
                    info_txt = str(_("This is a test. The candidate data are not saved."))
                else:
                    info_txt = str(_("The candidate data are saved."))
                logfile.append(c.STRING_INDENT_5 + info_txt)
                lookup_caption = af.get_dict_value(c.CAPTIONS, ('student', lookup_field), '')
                info_txt = str(_("Candidates are looked up by the field: '%(fld)s'.") % {'fld': lookup_caption})
                logfile.append(c.STRING_INDENT_5 + info_txt)
                if dateformat:
                    info_txt = str(_("The date format is: '%(fld)s'.") % {'fld': dateformat})
                    logfile.append(c.STRING_INDENT_5 + info_txt)
                logger.debug('dateformat: ' + str(dateformat))

    # +++++ loop through data_list
                update_list = []
                for data_dict in data_list:
                    # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html
                    # for key, val in student.items():
                    # #logger.debug( str(key) +': ' + val + '" found in "' + str(student) + '"')

    # - check if lookup_value occurs mutiple times in data_list
                    lookup_value = data_dict.get(lookup_field)
                    occurrences_in_datalist = 0
                    if lookup_value:
                        for dict in data_list:
                            value = dict.get(lookup_field)
                            if value and value == lookup_value:
                                occurrences_in_datalist += 1
                    logger.debug('occurrences_in_datalist: ' + str(occurrences_in_datalist))

    # - upload student
                    update_dict = upload_student(data_dict, lookup_field, lookup_value, occurrences_in_datalist,
                                                 awpColdef_list, is_test, examyear, school, department, dateformat, logfile, request)
                    # json_dumps_err_list = json.dumps(msg_list, cls=af.LazyEncoder)
                    if update_dict:  # 'Any' returns True if any element of the iterable is true.
                        update_list.append(update_dict)

                if update_list:  # 'Any' returns True if any element of the iterable is true.
                    params['data_list'] = update_list
            if logfile:  # 'Any' returns True if any element of the iterable is true.
                params['logfile'] = logfile
                    # params.append(new_student)
    return params
# - end of import_students


def upload_student(data_dict, lookup_field, lookup_value, occurrences_in_datalist,
                   awpColdef_list, is_test, examyear, school, department, format_str, logfile, request):  # PR2019-12-17 PR2020-06-03
    logger.debug('----------------- upload_student  --------------------')
    #logger.debug('data_dict: ' + str(data_dict))


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

    table = 'student'

# - get row_index and lookup info from data_dict
    row_index = data_dict.get('rowindex', -1)
    new_examnumber = data_dict.get('examnumber')
    new_idnumber = data_dict.get('idnumber')
    logger.debug('new_examnumber: ' + str(new_examnumber))
    logger.debug('new_idnumber: ' + str(new_idnumber))

    new_lastname, new_firstname, new_prefix = None, None, None
    required_lastname_novalue, required_firstname_novalue = False, False
    required_lastname_toolong, required_firstname_toolong = False, False

    lastname_input = data_dict.get('lastname')
    logger.debug('lastname_input: ' + str(lastname_input) + ' ' + str(type(lastname_input)))
    if lastname_input is None:
        required_lastname_novalue = True
    elif len(lastname_input) > c.MAX_LENGTH_FIRSTLASTNAME:
        required_lastname_toolong = True
    else:
        new_lastname = lastname_input
    logger.debug('new_lastname: ' + str(new_lastname))

    firstname_input = data_dict.get('firstname')
    if firstname_input is None:
        required_firstname_novalue = True
    elif len(firstname_input) > c.MAX_LENGTH_FIRSTLASTNAME:
        required_firstname_toolong = True
    else:
        new_firstname = firstname_input
    logger.debug('new_lastname: ' + str(new_lastname))

    prefix_input = data_dict.get('prefix')
    prefix_str = ''
    if prefix_input is not None:
        prefix_str = prefix_input[0:c.MAX_LENGTH_10]

    new_full_name = '---'
    if new_lastname:
        new_full_name = new_lastname.strip()  # Trim
    if prefix_str:  # put prefix before last_name
        new_full_name = prefix_str.strip() + ' ' + new_full_name
    if new_firstname:  # put first_name after last_name
        new_full_name += ', ' + new_firstname.strip()

# - create update_dict
    update_dict = {'id': {'table': 'student', 'rowindex': row_index}}

# - lookup student in database
    # multiple_found and exceeded_length return the lookup_value of the error field
    lookup_field_caption = af.get_dict_value(c.CAPTIONS, (table, lookup_field), '')
    lookup_field_capitalized = '-'
    if lookup_field_caption:
        lookup_field_capitalized = lookup_field_caption.capitalize()
    logger.debug('lookup_field: ' + str(lookup_field) + ' lookup_field_caption: ' + str(lookup_field_caption))
    logger.debug('lookup_value: ' + str(lookup_value))

    student, multiple_found, found_in_diff_dep, exceeded_length, is_existing_student = None, None, None, False, False
    student_name = '---'
    if lookup_value:
        # multiple_found returns lookup_value, retturns None when 0 or 1 found
        student, exceeded_length, multiple_found, found_in_diff_dep = lookup_student(school, department, lookup_field, lookup_value)
        if student:
            is_existing_student = True
            student_name = student.fullname
        else:
            student_name = new_full_name

# - give row_error when lookup went wrong
    skipped_str = student_name + str(_(" is skipped."))
    #skipped_str = str(_("Skipped."))
    logfile.append(c.STRING_INDENT_5)
    msg_err = None
    log_str = ''
    if occurrences_in_datalist > 1:
        log_str = str(_("%(fld)s '%(val)s' is not unique in Excel file.") % {'fld': lookup_field_capitalized, 'val': lookup_value})
        msg_err = ' '.join((skipped_str, log_str))
    elif required_lastname_novalue:
        field_caption = af.get_dict_value(c.CAPTIONS, (table, 'lastname'), '')
        log_str = str(_("No value for required field: '%(fld)s'.") % {'fld': field_caption})
        msg_err = ' '.join((skipped_str, log_str))
    elif required_lastname_toolong:
        field_caption = af.get_dict_value(c.CAPTIONS, (table, 'lastname'), '')
        value_too_long_str = str(_("Value of field: '%(fld)s' is too long.") % {'fld': field_caption})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_FIRSTLASTNAME})
        log_str =  value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))
    elif required_firstname_novalue:
        field_caption = af.get_dict_value(c.CAPTIONS, (table, 'firstname'), '')
        log_str = str(_("No value for required field: '%(fld)s'.") % {'fld': field_caption})
        msg_err = ' '.join((skipped_str, log_str))
    elif required_firstname_toolong:
        field_caption = af.get_dict_value(c.CAPTIONS, (table, 'firstname'), '')
        value_too_long_str = str(_("Value of field: '%(fld)s' is too long.") % {'fld': field_caption})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_FIRSTLASTNAME})
        log_str =  value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))
    elif not lookup_value:
        log_str = str(_("No value for lookup field: '%(fld)s'.") % {'fld': lookup_field_caption})
        msg_err = ' '.join((skipped_str, log_str))
    elif exceeded_length:
        value_too_long_str = str(_("Value '%(val)s' is too long.") % {'val': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': exceeded_length})
        log_str =  value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))
    elif found_in_diff_dep:
        log_str = str(_("Value '%(fld)s' already exists in a different department.") % {'fld': lookup_value})
        msg_err = ' '.join((skipped_str, log_str))
    elif multiple_found:
        log_str = str(_("Value '%(fld)s' is found multiple times.") % {'fld': lookup_value})
        msg_err = ' '.join((skipped_str, log_str))
    logger.debug('msg_err: ' + str(msg_err))

    if msg_err:
        logfile.append(student_name + str(_(' is not added.')))
        update_dict['row_error'] = msg_err
        update_dict[lookup_field] = {'error': msg_err}
        #logfile.append(code_text + is_skipped_str)
        logfile.append(c.STRING_SPACE_30 + log_str)
    else:

# - create new student when student not found in database
        is_existing_student = False
        save_instance = False

        if student is None:
    # - create base record. Create also saves new record
            base = stud_mod.Studentbase.objects.create(
                country=request.user.country
            )

            logger.debug('student base: ' + str(base))
            student = stud_mod.Student(
                base=base,
                school=school,
                department=department,
                lastname=new_lastname,
                firstname=new_firstname,
            )
            logger.debug('ooooooooooo new  student: ' + str(student))
            logger.debug('ooooooooooooo department: ' + str(department))
            if student:
                save_instance = True
                update_dict['id']['created'] = True
                logfile.append(student_name + str(_(' is added.')))
            else:
    # - give error msg when creating student failed
                error_str = str(_("An error occurred. The student is not added."))
                logfile.append(" ".join((student_name, error_str )))
                update_dict['row_error'] = error_str
        else:
            is_existing_student = True
            logfile.append(student_name + ' ' + str(_('already exists.')))
            logger.debug('ooooooooooo is_existing_student  student: ' + str(student))
            logger.debug('ooooooooooooo department: ' + str(department))

        logger.debug('is_existing_student: ' + str(is_existing_student))

        if student:
            # add 'id' at the end, after saving the student. Pk doent have value until instance is saved
            #update_dict['id']['pk'] = student.pk
            #update_dict['id']['ppk'] = student.company.pk
            #if is_created_student:
            #    update_dict['id']['created'] = True

            # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
            # solved bij wrapping with str()

            blank_str = '<' + str(_('blank')) + '>'
            was_str = str(_('was') + ': ')

            fields = ('lastname', 'firstname', 'prefix', 'gender', 'idnumber', 'birthdate',
                              'level', 'sector', 'scheme', 'package',
                              'birthcountry',
                              'birthcity',
                              'classname', 'examnumber', 'regnumber', 'diplomanumber', 'gradelistnumber',
                              'iseveningstudent', 'hasdyslexia',
                              'locked', 'has_reex', 'bis_exam', 'withdrawn', 'modifiedby', 'modifiedat')

            for field in fields:
                # --- get field_dict from  upload_dict  if it exists
                if field in awpColdef_list:
                    logger.debug('---------- field: ' + str(field))
                    field_dict = {}
                    field_caption = af.get_dict_value(c.CAPTIONS, ('student', field), '')
                    logger.debug('field_caption: ' + str(field_caption))
                    caption_txt = (c.STRING_INDENT_5 + field_caption + c.STRING_SPACE_30)[:30]
                    # text fields
                    if field in ('lastname', 'firstname', 'prefix', 'gender', 'idnumber',  'birthcountry', 'birthcity',
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
                                    update_str = ((new_value or blank_str) + c.STRING_SPACE_30)[:25] + old_value_str
                                    logfile.append(caption_txt + update_str)

######################################
                    elif field == 'birthdate':
            # - get new value, convert to date, using format_str
                        new_value = data_dict.get(field)
                        new_date_dte = None
            # - get saved_value
                        saved_dte = getattr(student, field)
                        saved_date_iso = None
                        if saved_dte:
                            saved_date_iso = saved_dte.isoformat()
                        old_value_str = was_str + (saved_date_iso or blank_str)

            # - validate new value
                        msg_err = None
                        if new_value and format_str:
                            date_iso = af.get_dateISO_from_string(new_value, format_str)
                            new_date_dte = af.get_date_from_ISO(date_iso)  # datefirst_dte: 1900-01-01 <class 'datetime.date'>
                            if new_date_dte is None:
                                msg_err = str(_("'%(val)s' is not a valid date.") % {'val': new_value})
                        if msg_err:
                            field_dict['error'] = msg_err
                            if is_existing_student:
                                field_dict['info'] = field_caption + ' ' + old_value_str
                                update_str = (msg_err + c.STRING_SPACE_30)[:25] + old_value_str
                                logfile.append(caption_txt + update_str)
                        else:
                            new_date_iso = None
                            if new_date_dte:
                                new_date_iso = new_date_dte.isoformat()
                            field_dict['value'] = new_date_iso
                            if not is_existing_student:
                                logfile.append(caption_txt + (new_date_iso or blank_str))
                            if new_date_dte != saved_dte:
                # put new value in student instance
                                setattr(student, field, new_date_dte)
                                field_dict['updated'] = True
                                save_instance = True
                # create field_dict and log
                                if is_existing_student:
                                    field_dict['info'] = field_caption + ' ' + old_value_str
                                    update_str = ((new_date_iso or blank_str) + c.STRING_SPACE_30)[:25] + old_value_str
                                    logfile.append(caption_txt + update_str)

                    elif field in ('level', 'sector'):
                        new_base_pk = data_dict.get(field)
                        saved_instance = getattr(student, field)

                        logger.debug('field: ' + str(field))
                        logger.debug('new_base_pk: ' + str(new_base_pk))
                        logger.debug('saved_instance: ' + str(saved_instance))

                         # check if dep / lvl / sct exists
                        new_instance = None
                        if field == 'level':
                            new_instance = subj_mod.Level.objects.get_or_none(base_id=new_base_pk, examyear=examyear)
                        elif field == 'sector':
                            new_instance = subj_mod.Sector.objects.get_or_none(base_id=new_base_pk, examyear=examyear)
                        logger.debug('new_instance: ' + str(new_instance))

                        if new_instance is None:
                            save_new_instance = (saved_instance is not None)
                        else:
                            save_new_instance = (saved_instance is None) or (new_instance != saved_instance)
                        logger.debug('save_new_lvl_sct: ' + str(save_new_instance))

                        if save_new_instance:
                            setattr(student, field, new_instance)
                            field_dict['updated'] = True
                            save_instance = True
                            new_abbrev = new_instance.abbrev if new_instance else None
                            logger.debug('new_abbrev: ' + str(new_abbrev))

                            if field == 'level':
                                caption_txt = department.level_caption
                            elif field == 'sector':
                                caption_txt = department.sector_caption

                            if not is_existing_student:
                                logfile.append(caption_txt + (new_abbrev or blank_str))
                                logger.debug('logfile.append: ' + str(caption_txt + (new_abbrev or blank_str)))
                            else:
                                saved_abbrev = saved_instance.abbrev if saved_instance else None
                                old_abbrev_str = was_str + (saved_abbrev or blank_str)
                                logger.debug('old_abbrev_str: ' + str(old_abbrev_str))
                                field_dict['info'] = field_caption + ' ' + old_abbrev_str
                                update_str = ((new_abbrev or blank_str) + c.STRING_SPACE_30)[:25] + old_abbrev_str
                                logfile.append(caption_txt + update_str)
                                logger.debug('logfile.append: ' + str(caption_txt + update_str))
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

                #student.save(request=request)
                #update_dict['id']['pk'] = student.pk
                #update_dict['id']['ppk'] = student.company.pk
                # wagerate wagecode
                # priceratejson additionjson
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


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def lookup_student(school, department, lookup_field, lookup_value):  # PR2019-12-17 PR2020-12-06 PR2020-12-31
    #logger.debug('----------- lookup_student ----------- ')
    # function searches for existing student in the following order: examnumber, idnumber

    #logger.debug('lookup_field: ' + str(lookup_field))
    #logger.debug('lookup_value: ' + str(lookup_value) + ' ' + str(type(lookup_value)))

    student = None
    exceeded_length = None
    multiple_found = None
    found_in_diff_dep = None

# - search student by lookup_field
    if lookup_value:
# - check if value is not too long
        max_length = None
        if lookup_field == 'examnumber':
            max_length =  c.MAX_LENGTH_EXAMNUMBER
        elif lookup_field == 'idnumber':
            max_length =  c.MAX_LENGTH_IDNUMBER
        if len(lookup_value) > max_length:
            exceeded_length = max_length

# - only lookup when lookup_value is not too long
        if exceeded_length is None:

# - check if lookup_value already exists
            students = None
            if lookup_field == 'examnumber':
                students = stud_mod.Student.objects.filter(
                    examnumber__iexact=lookup_value, school=school, department=department)
            elif lookup_field == 'idnumber':
                students = stud_mod.Student.objects.filter(idnumberr__iexact=lookup_value, school=school)
            row_count = 0
            for row in students:
                student = row
                row_count += 1
            if row_count == 1:
                if student.department != department:
                    found_in_diff_dep = lookup_value
            elif row_count > 1:
                multiple_found = lookup_value
                student = None

    #logger.debug('lookup student: ' + str(student))
    return student, exceeded_length, multiple_found, found_in_diff_dep


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
        #                   'iseveningstudent', 'hasdyslexia',
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
                            msg_err = validate_code_name_identifier(
                                table='student',
                                field=field,
                                new_value=new_value, parent=parent,
                                is_absence=False,
                                update_dict={},
                                msg_dict={},
                                request=request,
                                this_pk=instance.pk)
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
                            has_error = validate_lastname_firstname(
                                lastname=name_last,
                                firstname=name_first,
                                company=request.user.company,
                                update_field=field,
                                msg_dict=msg_dict,
                                this_pk=instance.pk)
                            if not has_error:
                                setattr(instance, field, new_value)
                                save_changes = True

# 3. save changes in date fields
                    elif field in ['datefirst', 'datelast']:
        # a. get new_date
                        new_date, msg_err = af.get_date_from_ISOstring(new_value, False)  # False = blank_allowed
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




def StudentImportUploadDataViewXXX(upload_dict):  # PR2018-12-04 PR2020-12-06

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

                # json_dumps_err_list = json.dumps(msg_list, cls=af.LazyEncoder)
                if len(data) > 0:
                    params.append(data)
                # params.append(student)

