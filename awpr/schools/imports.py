# PR2020-12-06

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse

from django.utils import timezone
from django.utils.decorators import method_decorator

#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext, pgettext_lazy, gettext_lazy as _

from django.views.generic import View

from accounts import models as acc_mod
from accounts import views as acc_view
from accounts import permits as acc_prm

from awpr import constants as c
from awpr import functions as af
from awpr import settings as s
from awpr import validators as awpr_val
from awpr import logs as awpr_log

from grades import validators as grade_val
from grades import views as grade_view
from grades import calc_finalgrade as calc_final

from schools import models as sch_mod
from schools import functions as sch_fnc
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
    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= UploadImportSettingView ============= ')

        update_wrap = {}

        req_user = request.user
        if req_user and req_user.country and req_user.schoolbase:
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
                'noheader': False,
                'examgradetype': 'segrade'
                }
                """

                if new_setting_dict:
                    # 'importtable' are: 'import_student', import_studsubj, 'import_grade'
                    setting_key = new_setting_dict.get('importtable')

                    sel_examyear_pk = new_setting_dict.get('sel_examyear_pk')
                    sel_examyear = sch_mod.Examyear.objects.get_or_none(pk=sel_examyear_pk)

                    sel_schoolbase_pk = new_setting_dict.get('sel_schoolbase_pk')
                    sel_schoolbase = sch_mod.Schoolbase.objects.get_or_none(pk=sel_schoolbase_pk)

                    sel_depbase_pk = new_setting_dict.get('sel_depbase_pk')
                    sel_depbase = sch_mod.Departmentbase.objects.get_or_none(pk=sel_depbase_pk)

                    if logging_on:
                        logger.debug('setting_key: ' + str(setting_key))
                        logger.debug('sel_schoolbase: ' + str(sel_schoolbase))

                    is_same_schoolbase = (sel_schoolbase and sel_schoolbase == req_user.schoolbase)
                    if setting_key and is_same_schoolbase:
                        stored_setting_dict = sel_schoolbase.get_schoolsetting_dict(setting_key)
                        if logging_on:
                            logger.debug('stored_setting_dict' + str(stored_setting_dict))

                        new_stored_setting = {}
                        # note: fields 'department', 'level', 'sector', 'subject', 'subjecttype' contain dict with mapped values
                        import_keys = ('worksheetname', 'noheader', 'examgradetype', 'coldef', 'department', 'level', 'sector', 'subject', 'subjecttype')
                        for import_key in import_keys:
                            new_setting_value = new_setting_dict.get(import_key)

                            if new_setting_value is None and stored_setting_dict:
                                new_setting_value = stored_setting_dict.get(import_key)

                            if import_key == 'noheader' and new_setting_value is None:
                                new_setting_value = False

                            if new_setting_value is not None:
                                new_stored_setting[import_key] = new_setting_value

                        if logging_on:
                            logger.debug('new_stored_setting: ' + str(new_stored_setting))

                        if new_stored_setting:
                            sel_schoolbase.set_schoolsetting_dict(setting_key, new_stored_setting)

        # get updated stored_setting from database, return to page to update mimp_stored
                    request_item_setting = {'setting_key': setting_key}
                    update_wrap['schoolsetting_dict'] = sch_fnc.get_schoolsettings(
                        request=request,
                        request_item_setting=request_item_setting,
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_schoolbase,
                        sel_depbase=sel_depbase
                    )

        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UploadImportSettingView


@method_decorator([login_required], name='dispatch')
class UploadImportDataView(View):  # PR2020-12-05 PR2021-02-23 PR2021-07-17
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request):
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

                permit_list, requsr_usergroups_listNIU, requsr_allowed_sections_dictNIU, requsr_allowed_clusters_arr = acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, page)

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
class UploadImportGradeView(View):  # PR2021-07-20 PR2021-12-10
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UploadImportGradeView ============= ')

        update_wrap = {}

        if request.user and request.user.country and request.user.schoolbase:

            if request.POST['upload']:
                upload_dict = json.loads(request.POST['upload'])

                importtable = upload_dict.get('importtable')
                page = importtable.replace('import', 'page')
                examgradetype = upload_dict.get('examgradetype')

# - Reset language
                # PR2019-03-15 Debug: language gets lost, get request.user.lang again
                # PR2021-12-09 Debug: must come before get_selected_ey_school_dep_lvl_from_usersetting
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get permit
                permit_list, requsr_usergroups_listNIU,  requsr_allowed_sections_dictNIU, requsr_allowed_clusters_arr = acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, page)
                has_permit = 'permit_crud' in permit_list

# - get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - not requsr_same_school
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not activated, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

# - check if examyear has no_practexam, sr_allowed, no_centralexam, no_thirdperiod
                err_list = grade_val.validate_grade_examgradetype_in_examyear(sel_examyear, examgradetype)
                if err_list:
                    may_edit = False
                    msg_list.extend(err_list)

                if logging_on:
                    logger.debug('    importtable: ' + str(importtable))
                    logger.debug('    page:        ' + str(page))
                    logger.debug('    requsr.role: ' + str(request.user.role))
                    logger.debug('    permit_list: ' + str(permit_list))
                    logger.debug('    has_permit: ' + str(has_permit))

                if not has_permit:
                    err_html = _("You don't have permission to perform this action.")
                    update_wrap['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))
                elif not may_edit:
                    err_html = '<br>'.join(msg_list)
                    update_wrap['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))
                else:

# - get info from upload_dict
                    # PR2021-07-20 only idnumber is lookupfield.
                    lookup_field = 'idnumber'
                    is_test = upload_dict.get('test', False)
                    filename = upload_dict.get('filename', '')
                    upload_data_list = upload_dict.get('data_list')

                    sel_examperiod = grade_val.get_examperiod_from_examgradetype(examgradetype)
                    sel_db_field = grade_val.get_grade_db_field_from_examgradetype(examgradetype)

                    if logging_on:
                        logger.debug('    is_test:        ' + str(is_test))
                        logger.debug('    filename:       ' + str(filename))
                        logger.debug('    examgradetype:  ' + str(examgradetype))
                        logger.debug('    sel_examperiod: ' + str(sel_examperiod))
                        if upload_data_list:
                            logger.debug('    len upload_data_list : ' + str(len(upload_data_list)))
                            #logger.debug('    upload_data_list : ' + str(upload_data_list))

                    log_list = []
                    tobe_updated_dict = {}

                    new_exemption_pk_list = [1]
                    mapped_new_exemption_grade_list = []

                    count_total = len(upload_data_list) if upload_data_list else 0
                    count_error = 0
                    count_dict = {
                        'stud_count': count_total,
                        'stud_not_found': 0,
                        'stud_with_error': 0,
                        'no_subjects': 0,
                        'notfound_subjects': 0,
                        'subjects_with_error': 0,
                        'grades_with_error': 0,
                        'changed_values': 0
                    }

                    if lookup_field and upload_data_list and sel_school and sel_department and examgradetype:

# - create log_list
                        today_dte = af.get_today_dateobj()
                        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

                        school_name = sel_school.base.code + ' ' + sel_school.name
                        score_grade_cpt = _('scores') if 'score' in examgradetype else _('grades')

                        examgradetype_str = '-'
                        for egt in c.EXAMGRADE_OPTIONS:
                            value = egt.get('value')
                            if value == examgradetype:
                                examgradetype_str = egt.get('caption', '-')
                                break
                        log_list = [c.STRING_DOUBLELINE_80,
                            ''.join((str(_('Upload %(cpt)s of candidates') % {'cpt': score_grade_cpt}), ' ',
                                    str(_('date')), ': ', str(today_formatted))),
                            c.STRING_DOUBLELINE_80]

                        log_list.append(c.STRING_SPACE_05 + str(_("School    : %(name)s") % {'name': school_name}))
                        log_list.append(c.STRING_SPACE_05 + str(_("Department: %(dep)s") % {'dep': sel_department.name}))
                        log_list.append(c.STRING_SPACE_05 + str(_("Exam year : %(ey)s") % {'ey': str(sel_examyear.code)}))
                        log_list.append(c.STRING_SPACE_05 + str(_("Exam type : %(egt)s") % {'egt': str(examgradetype_str)}))
                        log_list.append(c.STRING_SPACE_05 + str(_("File name : %(file)s") % {'file': filename}))

                        if is_test:
                            info_txt = str(_("This is a test. The %(cpt)s are not saved.") % {'cpt': score_grade_cpt})
                            log_list.append(c.STRING_SPACE_05 + info_txt)
                        else:
                            info_txt = str(_("The %(cpt)s are saved.") % {'cpt': score_grade_cpt})
                            log_list.append(c.STRING_SPACE_05 + info_txt)

# - get list of idnumbers, that occur multiple times in upload_data_list
                        double_idnumberlist = stud_val.get_double_idnumberlist_from_uploadfile(upload_data_list)
                        if logging_on:
                            logger.debug('double_idnumberlist: ' + str(double_idnumberlist))

# - get a dict per scheme of subjects with the lowest sequence
                        # mapped_subjectbase_pk_dict = { scheme_id: { subjectbase_pk: [schemeitem_id, subject_code] }, ... }
                        # mapped_subjectbase_pk_dict: {249: {140: [2070, 'sp'], 133: [2054, 'ne'],
                        # mapped_subjectbase_pk_dict = map_subjectbase_pk_to_schemeitem_pk(sel_school, sel_department)

# - get a dict with schemes and schemitems of this this department
                        scheme_si_dict = get_stud_subj_schemeitem_dict(sel_examyear, sel_school, sel_department)

# - get a dict with key idnumber and as value a dict with key: subjbase_pk and grade values
                        # function creates a dict with as key idnumber and as value a dict with key: subjbase_pk and value: subject_code
                        # output: dict: { idnumber: {student_id: id, subjectbase_pk: subject_code, ...}, ... }
                        student_subj_grade_dict = \
                            grade_val.get_student_subj_grade_dict(sel_school, sel_department, sel_examperiod,
                                                                  examgradetype, double_idnumberlist)

# - get allowed sections and allowed clusters PR2023-02-16
                        userallowed_instance = acc_prm.get_userallowed_instance(request.user, sel_examyear)
                        requsr_allowed_sections_dict = acc_prm.get_userallowed_sections_dict(userallowed_instance)
                        requsr_allowed_cluster_pk_list = acc_prm.get_userallowed_cluster_pk_list(userallowed_instance)

                        if logging_on:
                            logger.debug('school_name: ' + str(school_name))
                            #logger.debug('student_subj_grade_dict: ' + str(student_subj_grade_dict))

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++ loop through list of students in upload_data_list
                        for upload_data_dict in upload_data_list:
    # - import grade
                            has_error = \
                                get_tobe_updated_gradelist_from_datalist(
                                    upload_data_dict=upload_data_dict,
                                    department=sel_department,
                                    examyear=sel_examyear,
                                    examperiod=sel_examperiod,
                                    examgradetype=examgradetype,
                                    is_test=is_test,
                                    requsr_allowed_sections_dict=requsr_allowed_sections_dict,
                                    requsr_allowed_cluster_pk_list=requsr_allowed_cluster_pk_list,
                                    double_idnumberlist=double_idnumberlist,
                                    scheme_si_dict=scheme_si_dict,
                                    count_dict=count_dict,
                                    saved_student_subj_grade_dict=student_subj_grade_dict,
                                    tobe_updated_dict=tobe_updated_dict,
                                    new_exemption_pk_list=new_exemption_pk_list,
                                    mapped_new_exemption_grade_list=mapped_new_exemption_grade_list,
                                    log_list=log_list,
                                    request=request
                                )

                            count_total += 1
                            if has_error:
                                count_error += 1
                            # if has_error:
                            #   count_bisexam += 1
# +++++ end of loop through upload_data_list
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# +++++ update grades
                    if logging_on:
                        logger.debug('tobe_updated_dict: ' + str(tobe_updated_dict))
                        logger.debug('count_dict: ' + str(count_dict))

                    if tobe_updated_dict and not is_test:

# --- if examperiod is exemption: check for empty grades. create exemption_grade when empty and put pk back in tobe_updated_dict
                        studsubj_pk_list_of_created_exem_grades = create_exemption_grades(sel_examperiod, tobe_updated_dict, request)
                        if logging_on:
                            logger.debug('studsubj_pk_list_of_created_exem_grades: ' + str(studsubj_pk_list_of_created_exem_grades))

    # - set has_exemption True in studsubj, also add exemption_year
                        updated_student_pk_list = update_hasexemption_in_studsubj_batch(
                            tobe_updated_studsubj_pk_list=studsubj_pk_list_of_created_exem_grades,
                            examyear=sel_examyear,
                            request=request)

                        updated_grade_pk_list, updated_studsubj_pk_list = update_grade_batch(tobe_updated_dict, sel_db_field, request)
                        if logging_on:
                            logger.debug('updated_grade_pk_list: ' + str(updated_grade_pk_list))
                            logger.debug('updated_studsubj_pk_list: ' + str(updated_studsubj_pk_list))

                        if updated_grade_pk_list:
                            updated_grade_rows = grade_view.create_grade_rows(
                                sel_examyear=sel_examyear,
                                sel_schoolbase=sel_school.base,
                                sel_depbase=sel_department.base,
                                sel_lvlbase=None,
                                sel_examperiod=sel_examperiod,
                                request=request,
                                grade_pk_list=updated_grade_pk_list
                            )

                            if updated_grade_rows:
                                update_wrap['updated_grade_rows'] = updated_grade_rows

# - return html with number of students, existing, new and erros
                    count_existing = count_total
                    count_new = 0
                    update_wrap['is_test'] = is_test
                    update_wrap['table'] = 'grade'
                    update_wrap['result'] = create_testresult_grade_html(is_test, count_dict)
                    update_wrap['log_list'] = log_list

        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UploadImportGradeView


def create_exemption_grades(sel_examperiod, tobe_updated_dict, request):  # PR2022-02-16
    # --- if examperiod is exemption:
    #   check for empty grades in tobe_updated_dict
    #       create exemption_grade when empty and
    #       put pk back in tobe_updated_tuple
    #       set studsubj.has_exemption = True

    logging_on = s.LOGGING_ON

    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- create_exemption_grades ----- ')
    """
    tobe_updated_dict: { studsubj_pk: value_dict}
    tobe_updated_dict: { 21180: {'grade_pk': None, 'studsubj_pk': 21180, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': 'NULL'}, {'grade_pk': None, 'studsubj_pk': 21181, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': "'6'"}, {'grade_pk': None, 'studsubj_pk': 21182, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': "'6'"}, {'grade_pk': None, 'studsubj_pk': 21186, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': 'NULL'}, {'grade_pk': None, 'studsubj_pk': 21187, 'output_str': "'v'", 'sesr_grade': "'v'", 'pece_grade': 'NULL', 'finalgrade': "'v'"}, {'grade_pk': None, 'studsubj_pk': 21340, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': 'NULL'}, {'grade_pk': None, 'studsubj_pk': 21341, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': "'6'"}, {'grade_pk': None, 'studsubj_pk': 21342, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': "'6'"}, {'grade_pk': None, 'studsubj_pk': 21343, 'output_str': "'4.5'", 'sesr_grade': "'4.5'", 'pece_grade': 'NULL', 'finalgrade': "'5'"}, {'grade_pk': None, 'studsubj_pk': 21347, 'output_str': "'o'", 'sesr_grade': "'o'", 'pece_grade': 'NULL', 'finalgrade': "'o'"}, {'grade_pk': None, 'studsubj_pk': 21348, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': "'6'"}, {'grade_pk': None, 'studsubj_pk': 21190, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': 'NULL'}, {'grade_pk': None, 'studsubj_pk': 21191, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': "'6'"}, {'grade_pk': None, 'studsubj_pk': 21192, 'output_str': "'5.5'", 'sesr_grade': "'5.5'", 'pece_grade': 'NULL', 'finalgrade': "'6'"}, {'grade_pk': None, 'studsubj_pk': 21193, 'output_str': "'3.8'", 'sesr_grade': "'3.8'", 'pece_grade': 'NULL', 'finalgrade': "'4'"}, 
    """

    studsubj_pk_list_of_created_exem_grades = []

    if sel_examperiod == c.EXAMPERIOD_EXEMPTION:

        if tobe_updated_dict and request.user:

            try:
                modifiedby_pk_str = str(request.user.pk)
                modifiedat_str = "'" + str(timezone.now()) + "'"

        # get studsubj_pk's from tobe_updated_dict, only when studsubj has no exemption grade yet (aka grade_pk = None)
                studsubj_pk_list = []

                for studsubj_pk, value_dict in tobe_updated_dict.items():
                    grade_pk = value_dict.get('grade_pk')
                    if logging_on:
                        logger.debug('studsubj_pk: ' + str(studsubj_pk))
                        logger.debug('grade_pk: ' + str(grade_pk))
                    if grade_pk is None:
                        if studsubj_pk not in studsubj_pk_list:
                            studsubj_pk_list.append(studsubj_pk)

                #  from https://www.postgresqltutorial.com/postgresql-insert-multiple-rows/
                value_list = []
                value_str = None
                for studsubj_pk in studsubj_pk_list:

                    value_list.append(''.join(('(',
                                               str(studsubj_pk) , ', ',
                                               str(c.EXAMPERIOD_EXEMPTION), ', ',
                                               modifiedby_pk_str, ', ',
                                               modifiedat_str,
                                               ", 0, FALSE, 0, FALSE, 0, FALSE, 0, FALSE, FALSE, FALSE, FALSE, 0",
                                               ')')))
                if value_list:
                    value_str = ', '.join(value_list)

                if value_str:
                    sql_list = [
                        "INSERT INTO students_grade (studentsubject_id, examperiod, modifiedby_id, modifiedat,",
                        "se_status, se_blocked, sr_status, sr_blocked, pe_status, pe_blocked, ce_status, ce_blocked,",
                        "pe_exam_blocked, ce_exam_blocked, tobedeleted, status",
                        ") VALUES",
                        value_str,
                        "RETURNING students_grade.id, students_grade.studentsubject_id;"
                    ]
                    sql = ' '.join(sql_list)

                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                        rows = cursor.fetchall()
                        if rows:
                            for row in rows:
                                grade_pk = row[0]
                                studsubj_pk = row[1]
                        # -  put studsubj_pk in studsubj_pk_list_of_created_exem_grades,
                        #    this is needed to set has_exemption = True in studsubj
                                studsubj_pk_list_of_created_exem_grades.append(studsubj_pk)
                        # - put grade_pk back in tobe_updated_dict, to be used in update_grade_batch
                                tobe_updated_row = tobe_updated_dict[studsubj_pk]
                                if tobe_updated_row:
                                    tobe_updated_row['grade_pk'] = grade_pk
                                studsubj_pk_list_of_created_exem_grades.append(studsubj_pk)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('studsubj_pk_list_of_created_exem_grades: ' + str(studsubj_pk_list_of_created_exem_grades))

    return studsubj_pk_list_of_created_exem_grades
# - end of create_exemption_grades


@method_decorator([login_required], name='dispatch')
class UploadImportStudentsubjectView(View):  # PR2021-07-20 PR2024-08-13

    def post(self, request):
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

# - reset language
                # PR2019-03-15 Debug: language gets lost, get request.user.lang again
                # PR2021-12-09 Debug: must come before get_selected_ey_school_dep_lvl_from_usersetting
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - not requsr_same_school
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not activated, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                permit_list, requsr_usergroups_listNIU,  requsr_allowed_sections_dictNIU, requsr_allowed_clusters_arr = acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, page)

            # to prevent you from locking out when no permits yet
                #if request.user.role == c.ROLE_128_SYSTEM:
                    #if 'permit_crud' not in permit_list:
                        #permit_list.append('permit_crud')

                has_permit = 'permit_crud' in permit_list

                if logging_on:
                    logger.debug('    importtable: ' + str(importtable) + ' ' + str(type(importtable)))
                    logger.debug('    page: ' + str(page) + ' ' + str(type(page)))
                    logger.debug('    request.user.role: ' + str(request.user.role) + ' ' + str(type(request.user.role)))
                    logger.debug('    permit_list: ' + str(permit_list) + ' ' + str(type(permit_list)))
                    logger.debug('has_permit: ' + str(has_permit) + ' ' + str(type(has_permit)))

                if not has_permit:
                    err_html = _("You don't have permission to perform this action.")
                    update_dict['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))
                elif not may_edit:
                    err_html = '<br>'.join(msg_list)
                    update_dict['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))

                else:

# - get info from upload_dict
                    #PR2021-07-20 only 'idnumber' is lookupfield.
                    lookup_field = upload_dict.get('lookup_field')
                    data_list = upload_dict.get('data_list')
                    filename = upload_dict.get('filename', '')
                    is_test = upload_dict.get('test', False)

                    if logging_on:
                        logger.debug('    is_test: ' + str(is_test))
                        logger.debug('    lookup_field: ' + str(lookup_field))
                        logger.debug('    filename: ' + str(filename))
                        if data_list:
                            logger.debug('length data_list: ' + str(len(data_list)))

                    updated_rows = []
                    log_list = []

                    count_total, count_existing, count_new, count_diff_dep, count_error, count_bisexam, count_pws_has_changed = 0, 0, 0, 0, 0, 0, 0

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
                        double_idnumberlist = stud_val.get_double_idnumberlist_from_uploadfile(data_list)

        # - get a dict per scheme of this departent only. nested keys are scheme_id, subjbase_id, sjtpbase_id
                        mapped_subjectbase_pk_dict = map_subjectbase_pk_to_schemeitem_pk(sel_department.pk)
                        """
                        mapped_subjectbase_pk_dict = {scheme_id: {subjbase_id: {sjtpbase_id: {si_id: 4371...
                        mapped_subjectbase_pk_dict: {
                            175: {'scheme_name': 'Vsbo - PBL - ec', 
                                113: {'subjbase_id': 113, 'subj_code': 'ne', 'subj_name_nl': 'Nederlands', 
                                    'default_sjtpbase_sequence': 1, 'default_sjtpbase_id': 31, 
                                        31: {'si_id': 4371, 'sjtpbase_id': 31, 'sjtp_name': 'Gemeenschappelijk deel', 
                                            'sjtp_abbrev': 'Gemeensch.', 'sjtp_has_prac': False, 'sjtp_has_pws': False, 
                                                'sjtpbase_sequence': 1}},  
                        """

                        # - get a dict with key idnumber and as value a dict with key: subjbase_pk and value: subject_code
                        # function creates a dict with as key idnumber and as value a dict with key: subjbase_pk and value: subject_code
                        # output: dict: { idnumber: {student_id: id, subjectbase_pk: subject_code, ...}, ... }
                        # PR2024-08-20 debug: studsubj are not imported at this moment, so exempptions were not added
                        students_dict_with_subjbase_pk_list, linked_student_pk_list, other_student_pk_list = \
                            get_students_dict_with_subjbase_pk_list(sel_school, sel_department)

                        # get info of other_students that are in 'linked' fields (=other_student_pk_list)
                        other_student_pok_dict = get_other_student_pok_dict(
                            sel_examyear=sel_examyear,
                            sel_department=sel_department,
                            other_student_pk_list=other_student_pk_list
                        )

                        if logging_on:
                            logger.debug('    school_name: ' + str(school_name))
                            logger.debug('    double_idnumberlist: ' + str(double_idnumberlist))

                        tobe_inserted_studentsubject_dict = {}
                        tobe_inserted_or_updated_exemption_grade_dict = {}
                        tobe_updated_studsubj_dict = {}

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++ loop through data_list - each data_dict contains info of all subjects of one student
                        for data_dict in data_list:
                            if logging_on:
                                logger.debug('++++++ loop through data_list +++++++++++++++')

    # skip empty rows
                            has_values = False
                            if data_dict.get(lookup_field):
                                has_values = True
                            elif data_dict.get('subjects'):
                                has_values = True

                            if has_values:

    # - upload studentsubject
                                studsubj_rows, has_error, is_existing_student, is_diff_dep_student, pws_has_changed = \
                                    upload_studentsubject_from_datalist(
                                        upload_data_dict=data_dict,
                                        sel_examyear=sel_examyear,
                                        sel_school=sel_school,
                                        sel_department=sel_department,
                                        is_test=is_test,
                                        double_idnumberlist=double_idnumberlist,
                                        mapped_subjectbase_pk_dict=mapped_subjectbase_pk_dict,
                                        students_dict_with_subjbase_pk_list=students_dict_with_subjbase_pk_list,
                                        linked_student_pk_list=linked_student_pk_list,
                                        other_student_pok_dict=other_student_pok_dict,
                                        tobe_inserted_or_updated_exemption_grade_dict=tobe_inserted_or_updated_exemption_grade_dict,
                                        tobe_updated_studsubj_dict=tobe_updated_studsubj_dict,
                                        log_list=log_list,
                                        request=request
                                    )

                                if not is_test and studsubj_rows:
                                    updated_rows.extend(studsubj_rows)

                                count_total += 1
                                if has_error:
                                    count_error += 1
                                elif is_diff_dep_student:
                                    count_diff_dep += 1
                                elif is_existing_student:
                                    count_existing += 1
                                else:
                                    count_new += 1
                                if pws_has_changed:
                                    count_pws_has_changed += 1
                                # count_existing not in use
                                # if has_error:
                                #   count_bisexam += 1

# +++++ end of loop through data_list
                        # PR2024-08-18 not in use yet, tobe used whe changin to bacht insert instance of savin model instance
                        #if tobe_inserted_studentsubject_dict:
                        #    if logging_on:
                        #        logger.debug(' ###########   tobe_inserted_studentsubject_dict: ' + str(tobe_inserted_studentsubject_dict))

                        #    batch_insert_or_update_studsubj(tobe_inserted_studentsubject_dict, request)

                        if logging_on:
                            logger.debug(' ###########   tobe_inserted_exemption_grade_dict: ' + str(tobe_inserted_or_updated_exemption_grade_dict))
                        if not is_test and tobe_inserted_or_updated_exemption_grade_dict:
                            updated_grade_pk_list, updated_studsubj_pk_list = batch_insert_or_update_exemption_grade(tobe_inserted_or_updated_exemption_grade_dict, request)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # - return html with number of students, existing, new and errors
                    result_html = create_result_html(
                        importtable=importtable,
                        is_test=is_test,
                        count_total=count_total,
                        count_error=count_error,
                        count_new=count_new,
                        count_existing=count_existing,
                        count_diff_dep=count_diff_dep,
                        count_pws_has_changed=count_pws_has_changed,
                        is_user=False
                    )
                    update_dict = { 'is_test': is_test,
                                    'table': 'studsubj',
                                    'result': result_html,
                                    'log_list': log_list}
                    # was: if not is_test and updated_rows:
                    #    update_dict['updated_studsubj_rows'] = updated_rows
                    if not is_test:
                        update_dict['updated_studsubj_rows'] = "tobedownloaded"

        return HttpResponse(json.dumps(update_dict, cls=af.LazyEncoder))
# - end of UploadImportStudentsubjectView


@method_decorator([login_required], name='dispatch')
class UploadImportStudentView(View):
    # PR2020-12-05 PR2021-02-23  PR2021-07-17 PR2022-08-21  PR2023-01-16  PR2024-08-06
    # function updates mapped fields, no_header and worksheetname in table Schoolsetting
    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UploadImportStudentView ============= ')

        update_wrap = {'table': 'student'}

        if request.user and request.user.country and request.user.schoolbase:

            upload_json = request.POST.get('upload')
            if upload_json:
                upload_dict = json.loads(upload_json)

                # upload_dict: {'sel_examyear_pk': 58, 'sel_schoolbase_pk': 11, 'sel_depbase_pk': 1, 'sel_depbase_code': 'Vsbo', 'sel_school_abbrev': '---',
                # 'importtable': 'import_student', 'filename': 'StJozef_2021_Kandidaten.xlsx',
                # 'awpColdef_list': ['examnumber', 'lastname', 'firstname', 'prefix', 'gender', 'idnumber', 'birthdate', 'birthcountry', 'birthcity', 'classname', 'level', 'sector'], 'test': True, 'data_list': [{'

                importtable = upload_dict.get('importtable')
                page = importtable.replace('import', 'page')

                # PPR2023-01-16 was:
                #   permit_list, requsr_usergroups_listNIU,  requsr_allowed_sections_dictNIU, requsr_allowed_clusters_arr = acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, page)
                #   has_permit = 'permit_crud' in permit_list
                has_permit = acc_prm.get_permit_crud_of_this_page(page, request)

                if logging_on:
                    logger.debug('    request.user.role: ' + str(request.user.role))
                    logger.debug('    has_permit: ' + str(has_permit))
                    #logger.debug('upload_dict: ' + str(upload_dict))

                if not has_permit:
                    msg_html = acc_prm.err_html_no_permit()  # default: 'to perform this action')
                    update_wrap['result'] = msg_html
                else:

        # - Reset language
                    # PR2019-03-15 Debug: language gets lost, get request.user.lang again
                    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                    activate(user_lang)

        # - get selected examyear, school and department from usersettings
                    sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                        acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

        # - get info from upload_dict
                    is_test = upload_dict.get('test', False)
                    awpColdef_list = upload_dict.get('awpColdef_list')
                    data_list = upload_dict.get('data_list')
                    filename = upload_dict.get('filename', '')

                    if logging_on:
                        logger.debug('    is_test:        ' + str(is_test))
                        logger.debug('    awpColdef_list: ' + str(awpColdef_list))
                        logger.debug('    len(data_list): ' + str(len(data_list)))
                        logger.debug('    sel_school:     ' + str(sel_school))
                        logger.debug('    sel_department: ' + str(sel_department))
                        for row in data_list:
                            logger.debug('   data_list row: ' + str(row))

                    update_wrap['is_test'] = is_test

                    updated_rows = []
                    count_total, count_existing, count_new, count_diff_dep, count_error, count_bisexam = 0, 0, 0, 0, 0, 0

                    if awpColdef_list and data_list and sel_school and sel_department:
                        # these are used for creating studentlog records

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

        # - get double_idnumber_list, a list of idnumbers/lastname/firstname that occur multiple times in data_list
                        double_idnumber_list = stud_val.get_double_idnumberlist_from_uploadfile(data_list)

        # - get id_number_list, the list of idnumbers of this school
                        # idnumber_list and examnumber_list will be filled in upload_student_from_datalist
                        # without a row the reference to these lists get lost. Cost me 2 hours to figure this out. PR2022-08-22
                        student_pk_list, idnumber_list, examnumber_list = [], [], []

                        # PR2024-08-05 student_pk_list is used to return student_rows and check similarities
                        updated_fields = []

                        # PR2024-08-05 append_dict is used to add 'created' to student_row, to make new row green
                        # append_dict[student_instance.pk] = {'created': True}
                        append_dict = {}

        # - get list of diplomanumber and gradelistnumber, that occur multiple times in data_list
                        # PR2023-08-12 not in use from 2023
                        # was: double_diplomanumber_list, double_gradelistnumber_list = \
                        # was:     stud_val.get_double_diplomanumber_gradelistnumber_from_uploadfile(data_list)

        # - get diplomanumber_list, gradelistnumber_list, the list of examnumbers of this school
                        # PR2023-08-12 not in use from 2023
                        # new values will be added to the value_list in upload_student_from_datalist
                        # was: diplomanumber_list = stud_val.get_diplomanumberlist_gradelistnumberlist_from_database('diplomanumber', sel_school)
                        # was: gradelistnumber_list = stud_val.get_diplomanumberlist_gradelistnumberlist_from_database('gradelistnumber', sel_school)

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# +++++ loop through data_list
                        for data_dict in data_list:
                            # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html
                            # for key, val in student.items():
                            # #logger.debug( str(key) +': ' + val + '" found in "' + str(student) + '"')

                            """
                            data_dict = {
                                'rowindex': 10, 
                                'department': 2, 'profiel': 10, 
                                'examnumber': '101', 
                                'lastname': 'Apostel', 'firstname': 'Deshawn Devanté Stan-Lee', 'prefix': None, 
                                'gender': 'M', 'idnumber': '2004042808', 'birthdate': None, 'birthcountry': 'Nederland', 
                                'birthcity': 'Dordrecht', 'classname': '5'
                                }
                            
                            awpColdef_list: [
                                'department', 'level', 'sector', 'examnumber', 'lastname', 'firstname', 'prefix',
                                'gender', 'idnumber', 'extrafacilities', 'birthdate', 'birthcountry', 'birthcity', 'classname']
                            """

    # skip empty rows
                            has_values = False
                            for field in awpColdef_list:
                                value = data_dict.get(field)
                                if value is not None:
                                    has_values = True

                            if has_values:
    # - upload student
                                is_existing, is_new_student, is_diff_dep_student, has_error, might_be_bisexam = \
                                    upload_student_from_datalist(
                                        data_dict=data_dict,
                                        sel_examyear=sel_examyear,
                                        sel_school=sel_school,
                                        sel_department=sel_department,
                                        is_test=is_test,
                                        append_dict=append_dict,
                                        student_pk_list=student_pk_list,
                                        updated_fields=updated_fields,
                                        double_idnumber_list=double_idnumber_list,
                                        idnumber_list=idnumber_list,
                                        examnumber_list=examnumber_list,
                                        log_list=log_list,
                                        request=request
                                    )

                                count_total += 1

                                if has_error:
                                    count_error += 1
                                elif is_diff_dep_student:
                                    count_diff_dep += 1
                                elif is_existing:
                                    count_existing += 1
                                elif is_new_student:
                                    count_new += 1

                                # if has_error:
                                #   count_bisexam += 1
# +++++ end of loop through data_list

                        if student_pk_list:
                            if not is_test:

                                if logging_on:
                                    logger.debug('--- savetolog_student -')
                                    logger.debug('    updated_fields: ' + str(updated_fields))
                                    logger.debug('    student_pk_list: ' + str(student_pk_list))

                                awpr_log.savetolog_student(student_pk_list, 'i', request, updated_fields)

            # +++ link identical students
                                has_automatically_linked_students = stud_val.link_identical_students(request, sel_examyear, sel_school, sel_department)

                                # PR2024-08-20 this gives message
                                update_wrap['has_automatically_linked_students'] = has_automatically_linked_students

             # +++ check if any unlinked students
                                has_unlinked_similarities = stud_val.check_unlinked_student_similarities(
                                    sel_examyear=sel_examyear,
                                    sel_schoolbase=sel_school.base,
                                    sel_depbase=sel_department.base,
                                    student_pk_list=student_pk_list
                                )
                                # PR2024-08-05 don't use has_unlinked_similarities, it will open MLINKSTUD
                                #update_dict['has_unlinked_similarities'] = has_unlinked_similarities
                                update_wrap['import_has_unlinked_similarities'] = has_unlinked_similarities


                            updated_rows, error_dictNIU = stud_view.create_student_rows(
                                request=request,
                                sel_examyear=sel_school.examyear,
                                sel_schoolbase=sel_school.base,
                                sel_depbase=sel_department.base,
                                append_dict=append_dict,
                                student_pk_list=student_pk_list
                            )

                            if updated_rows:
                                update_wrap['updated_student_rows'] = updated_rows

                        update_wrap['log_list'] = log_list

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # - return html with number of students, existing, new and errors
                    update_wrap['result'] = create_result_html(
                        importtable=importtable,
                        is_test=is_test,
                        count_total=count_total,
                        count_error=count_error,
                        count_new=count_new,
                        count_existing=count_existing,
                        count_diff_dep=count_diff_dep,
                        count_pws_has_changed=0,
                        is_user=False
                    )

                    if not is_test and updated_rows:
                        update_wrap['updated_student_rows'] = updated_rows

        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UploadImportStudentView


# ========  upload_student_from_datalist  =======
def upload_student_from_datalist(data_dict, sel_examyear, sel_school, sel_department, is_test, append_dict,
            student_pk_list, updated_fields,
            double_idnumber_list, idnumber_list, examnumber_list, log_list, request):

    #  PR2019-12-17 PR2020-06-03 PR2021-06-19 PR2022-06-26 PR2022-08-21 PR2023-01-16 PR2023-08-12 PR2024-08-06
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- upload_student_from_datalist  --------------------')
        logger.debug('    data_dict: ' + str(data_dict))
        logger.debug('    is_test: ' + str(is_test))
        """
        data_dict = {
            'rowindex': 10, 
            'department': 2, 'profiel': 10, 
            'examnumber': '101', 
            'lastname': 'Apostel', 'firstname': 'Deshawn Devanté Stan-Lee', 'prefix': None, 
            'gender': 'M', 'idnumber': '2004042808', 'birthdate': None, 'birthcountry': 'Nederland', 
            'birthcity': 'Dordrecht', 'classname': '5'
            }
    
        awpColdef_list: [
            'department', 'level', 'sector', 'examnumber', 'lastname', 'firstname', 'prefix',
             'gender', 'idnumber', 'birthdate', 'birthcountry', 'birthcity', 'classname']
        """

    # - required fields are: base, school, department, lastname, firstname
    # the lookup field 'idnumber' is not required in model, but is required for upload
    # note: 'department' =  2 contains depbase_pk, not department_pk

    # awpColdef_list:  idnumber,  lastname, firstname, prefix, gender, examnumber, birthdate, birthcountry, birthcity
    #                   classname, (iseveningstudent), bis_exam, department, level, sector, profiel

    error_list = []
    err_fields = []
    update_list = []
    is_existing_student, is_new_student, is_diff_dep_student, has_error, might_be_bisexam = False, False, False, False, False

# - get variables from data_dict (data_dict is the dict with the upload information)
    id_number = data_dict.get('idnumber', '')
    last_name = data_dict.get('lastname', '')
    first_name = data_dict.get('firstname', '')
    prefix = data_dict.get('prefix', '')
    student_depbase_pk = data_dict.get('department')
    student_lvlbase_pk = data_dict.get('level')

    student_sctbase_pk = None
    if 'sector' in data_dict:
        student_sctbase_pk = data_dict.get('sector')
    elif 'profiel' in data_dict:
        student_sctbase_pk = data_dict.get('profiel')

    if logging_on:
        logger.debug('    student_depbase_pk: ' + str(student_depbase_pk))
        logger.debug('    student_lvlbase_pk: ' + str(student_lvlbase_pk))
        logger.debug('    student_sctbase_pk: ' + str(student_sctbase_pk))

# - NIU: base_pk only has value when user has ticked off 'same_student' after test_upload
    # instead of creating a new student_base, the base_pk will be used and 'islinked' will be set True
    # base_pk = data_dict.get('base_pk')

# - skip when student is from different department
    # PR2022-06-26 debug: Havo student was added to Vsbo in ATC. Must filter out students from different departments
    # only when student_depbase_pk has value (student_depbase_pk is None when school has only 1 department)
    if student_depbase_pk and student_depbase_pk != sel_department.base_id:
        is_diff_dep_student = True
        error_list.append(gettext("This candidate belongs to a different department."))

    # don't add error message when student is from diff department
    idnumber_nodots, msg_err_list, birthdate_dteobjNIU = stud_val.get_idnumber_nodots_stripped_lower(id_number)
    if msg_err_list and not is_diff_dep_student:
        has_error = True
        error_list.extend(msg_err_list)

    lastname_stripped, err_txt = stud_val.get_string_convert_type_and_strip(_('Last name'), last_name, True) # True = blank_not_allowed
    if err_txt and not is_diff_dep_student:
        has_error = True
        error_list.append(str(err_txt))

    firstname_stripped, err_txt = stud_val.get_string_convert_type_and_strip(_('First name'), first_name, True) # True = blank_not_allowed
    if err_txt and not is_diff_dep_student:
        has_error = True
        error_list.append(str(err_txt))

    prefix_stripped, err_txt = stud_val.get_string_convert_type_and_strip(_('Prefix'), prefix, False) # False = blank_allowed
    if err_txt and not is_diff_dep_student:
        has_error = True
        error_list.append(str(err_txt))

    full_name = stud_val.get_prefix_lastname_comma_firstname(lastname_stripped, firstname_stripped, prefix_stripped)

    if logging_on :
        logger.debug('    idnumber_nodots: ' + str(idnumber_nodots))
        logger.debug('    full_name: ' + str(full_name))
        logger.debug('    student_depbase_pk: ' + str(student_depbase_pk))
        logger.debug('    error_list: ' + str(error_list))

# - check for double occurrence in upload file
    if not has_error and not is_diff_dep_student:
        has_error = stud_val.validate_double_entries_in_uploadfile(
            caption=gettext('ID-number'),
            lookup_value=idnumber_nodots,
            double_entrieslist=double_idnumber_list,
            error_list=error_list
        )

    # PR2023-08-12 double_diplomanumber_list#55 and double_gradelistnumber_list are not in use from 2023
        # if not has_error and not is_diff_dep_student:
            #     has_error = stud_val.validate_double_entries_in_uploadfile(
            #         caption=str(_('Diploma number')),
            #         lookup_value=data_dict.get('diplomanumber'),
            #         double_entrieslist=double_diplomanumber_list,
            #         error_list=error_list
        #     )
        # if not has_error and not is_diff_dep_student:
            #     has_error = stud_val.validate_double_entries_in_uploadfile(
            #         caption=str(_('Gradelist number')),
            #     lookup_value=data_dict.get('gradelistnumber'),
            #     double_entrieslist=double_gradelistnumber_list,
            #     error_list=error_list
        #  )

# - validate length of name firstname prefix
    if not has_error and not is_diff_dep_student:
        has_error = stud_val.validate_student_name_length(lastname_stripped, firstname_stripped, prefix_stripped, error_list)

    is_new_student, error_create, changes_are_saved, error_save = False, False, False, False

    if not has_error and not is_diff_dep_student:

# - replace idnumber by idnumber_nodots_stripped_lower
        data_dict['idnumber'] = idnumber_nodots

# - lookup student in database, only in this school and this examyear
        # when importing: don't give error when found, but return found student  error_when_found
        # either student, not_found or has_error is trueish

       # either student_instance, not_found or err_list is trueish
        student_instance, not_foundNIU, err_list = \
            stud_val.lookup_student_by_idnumber_nodots(
                school=sel_school,
                department=sel_department,
                idnumber_nodots=idnumber_nodots,
                upload_fullname=full_name,
                found_is_error=False
            )

        if logging_on:
            logger.debug('    lookup student_instance: ' + (str(student_instance)))
            logger.debug('    err_list:    ' + str(err_list))

        if err_list:
            has_error = True
            error_list.extend(err_list)

        else:

    # - check if birthdate is a valid date
            # birthdate has format of Excel ordinal
            birthdate_ordinal = data_dict.get('birthdate')
            if logging_on and False:
                logger.debug('birthdate_ordinal: ' + str(birthdate_ordinal) + ' ' + str(type(birthdate_ordinal)))

            birthdate_iso = af.get_dateiso_from_excel_ordinal(birthdate_ordinal, error_list)
            if birthdate_iso is None:
                birthdate_iso = af.get_birthdateiso_from_idnumber(idnumber_nodots)

        # - replace birthdate with birthdate_iso in data_dict
            # PR2021-08-12 debug: must also replace 0 with None, otherwise error occurs in update_student_instance

            data_dict['birthdate'] = birthdate_iso

            if student_instance:
                is_existing_student = True

                if logging_on:
                    logger.debug('    is_existing_student: ' + (str(is_existing_student)))
            else:
                if logging_on:
                    logger.debug('    create new student ')

    # +++ create new student when student not found in database
                #base = None
                #is_linked = False

                # NIU: check if student exists in other year is replaced to exemption.
                # here it is not in use
                # base_pk only has vaue when user has ticked of 'same_student' after test_upload
                # instead of creating a new student_base, the base_pk will be used and 'islinked' will be set True

                #if base_pk:
                #    base = stud_mod.Studentbase.objects.filter( pk=base_pk)

        # - create base record. Don't save when is_test
                # skip_save = is_test
                # note: error_list is list of strings,
                #  messages is list of dicts with format: {'field': fldName, header': header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html}

                # PR2022-08-21 replacing values with import when student already exists is not working properly.
                #  Turned off for now (found_is_error=True) PR2022-08-21
                #  Turned on again PR2022-09-02 - no issues yet

                # TODO also: return message on import modal not giving info '22 candidates are skipped' etc

        # - create student record
                student_instance, l_mode, updated_flds, error_list = stud_view.create_student_instance(
                    examyear=sel_examyear,
                    school=sel_school,
                    department=sel_department,
                    idnumber_nodots=idnumber_nodots,
                    lastname_stripped=lastname_stripped,
                    firstname_stripped=firstname_stripped,
                    prefix_stripped=prefix_stripped,
                    full_name=full_name,
                    lvlbase_pk=student_lvlbase_pk,
                    sctbase_pk=student_sctbase_pk,
                    request=request,
                    skip_save=is_test,
                    is_import=True
                )
                if l_mode:
                    for fld in updated_flds:
                        if fld not in updated_fields:
                            updated_fields.append(fld)

                if logging_on:
                    student_pk = student_instance.pk if student_instance else 'None'
                    logger.debug('student_instance: ' + str(student_instance))
                    logger.debug('student_pk:       ' + str(student_pk))
                    logger.debug('error_list:       ' + str(error_list))

                if student_instance is None:
        # - give error msg when creating student failed - is already done in create_student
                    error_create = True

                else:
                    is_new_student = True

                    # when is_test, student_instance.pk = None
                    if student_instance.pk:
                        append_dict[student_instance.pk] = {'created':  True}

    # -- check for doubles, only when is new student
                    #double_dict = validate_students_doubles(request.user.country, idnumber_nodots,
                    #                                lastname_stripped,
                    #                                firstname_stripped, birthdate_iso)
                    #if logging_on:
                    #    logger.debug('double_dict: ' + str(double_dict))
                    #if double_dict:
                    #    might_be_bisexam = True
                    #    bisexam_dict[row_index] = double_dict
                    #    if logging_on:
                    #        logger.debug('double_dict: ' + str(double_dict))
                    #        #logger.debug('bisexam_dict: ' + str(bisexam_dict))

    # - update fields, both in new and existing students
            if student_instance:
                data_dict.pop('rowindex')
                # PR2024-08-14 debug: error in function create_student_rows:
                # column "none" does not exist at SELECT UNNEST(ARRAY [10744, None, 1074
                # must filter out None values in student_pk_list
                # solved by adding if student_instance.pk
                if student_instance.pk and student_instance.pk not in student_pk_list:
                    student_pk_list.append(student_instance.pk)

                # idnumber_list and examnumber_list will be filled in upload_student_from_datalist
                # without a row the reference to these lists get lost. Cost me 2 hours to figure this out. PR2022-08-22

                # err_fields is only used in update student
                changes_are_saved, updated_flds, err_fields, err_list, error_save = \
                    stud_view.update_student_instance(
                        instance=student_instance,
                        sel_examyear=sel_examyear,
                        sel_school=sel_school,
                        sel_department=sel_department,
                        upload_dict=data_dict,
                        idnumber_list=idnumber_list,
                        examnumber_list=examnumber_list,
                        log_list=update_list,
                        request=request,
                        skip_save=is_test,
                        skip_log=True,  # use log batch instead
                        is_import=True
                    )
                if updated_flds:
                    for fld in updated_flds:
                        if fld not in updated_fields:
                            updated_fields.append(fld)
                if err_list:
                    error_list.extend(err_list)

            if logging_on:
                logger.debug('changes_are_saved: ' + str(changes_are_saved))
                logger.debug('error_list: ' + str(error_list))
                logger.debug('err_fields: ' + str(err_fields))

# create log for this student
    student_header = ''.join(((idnumber_nodots + c.STRING_SPACE_10)[:10], c.STRING_SPACE_05, full_name)) if idnumber_nodots else full_name
    if has_error or error_create or is_diff_dep_student:
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

                if logging_on:
                    logger.debug('    err: ' + str(err))

    if update_list:
        for update_txt in update_list:
            if update_txt:
                log_list.append('- '.join((c.STRING_SPACE_15, update_txt)))

    if changes_are_saved:
        if not is_new_student:
            changed_txt = _('The changes will be saved.') if is_test else _('The changes have been saved.')
            log_list.append('- '.join((c.STRING_SPACE_15, str(changed_txt))))
        if err_fields:
            changed_txt = _('Some fields have errors. They will not be saved.') \
                if is_test else _('Some fields have errors. They have not been saved.')
            log_list.append('- '.join((c.STRING_SPACE_15, str(changed_txt))))

    if error_save:
        changed_txt = _('The changes will not be saved.') if is_test else _('The changes have not been saved.')
        log_list.append('- '.join((c.STRING_SPACE_15, str(changed_txt))))

    return is_existing_student, is_new_student, is_diff_dep_student, has_error, might_be_bisexam
# --- end of upload_student_from_datalist


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
        # add 'id' at the end, after saving the student. Pk doesn't have value until instance is saved
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

            elif field == 'extrafacilities':
                # - get new value, convert to boolean, TRue when has value
                new_value = data_dict.get(field)
                new_value_bool = not not new_value

            # - get saved_value
                saved_value = getattr(student, field)
                if new_value_bool != saved_value:
                    # put new value in student instance
                    setattr(student, field, new_value_bool)
                    field_dict['updated'] = True
                    save_instance = True
            # create field_dict and log
                    if is_existing_student:
                        old_value_str = was_str + ( str(saved_value) if saved_value else blank_str)
                        field_dict['info'] = field_caption + ' ' + old_value_str
                        update_str = ((str(new_value) if new_value else blank_str) + c.STRING_SPACE_30)[:25] + old_value_str
                        log_list.append(caption_txt + update_str)

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

# - Reset language
            # PR2019-03-15 Debug: language gets lost, get request.user.lang again
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            if request.POST['upload']:
                upload_dict = json.loads(request.POST['upload'])

                importtable = upload_dict.get('importtable')
                page = importtable.replace('import', 'page')

                permit_list, requsr_usergroups_listNIU,  requsr_allowed_sections_dictNIU, requsr_allowed_clusters_arr = acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, page)

# - get permit
            # to prevent you from locking out when no permits yet
                if request.user.role == c.ROLE_128_SYSTEM:
                    has_permit = True
                else:
                    has_permit = 'permit_userpage' in permit_list

                if logging_on:
                    logger.debug('request.user.role: ' + str(request.user.role))
                    logger.debug('permit_list: ' + str(permit_list))
                    logger.debug('has_permit: ' + str(has_permit))

                if not has_permit:
                    msg_html = acc_prm.err_html_no_permit()  # default: 'to perform this action')
                    update_dict['result'] = msg_html
                else:


        # - get selected examyear from usersettings
                    sel_examyear_instance = acc_prm.get_sel_examyear_from_requsr(request)
                    sel_examyear_instance, error_list = acc_view.get_selected_examyear_from_usersetting(
                        request=request,
                        allow_not_published=False
                    )
                    if error_list:
                        error_list.append(gettext('You cannot make changes.'))
                        err_html = '<br>'.join(error_list)
                        update_dict['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))

                    else:

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
                                            sel_examyear_instance=sel_examyear_instance,
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
             # - return html with number of students, existing, new and errors
                        result_html = create_result_html(
                            importtable=importtable,
                            is_test=is_test,
                            count_total=count_total,
                            count_error=count_error,
                            count_new=count_new,
                            count_existing=count_existing,
                            count_diff_dep=0,
                            count_pws_has_changed=0,
                            is_user=True
                        )
                        update_dict = { 'is_test': is_test,
                                        'table': 'user',
                                        'result': result_html,
                                        'log_list': log_list}
                        if not is_test and updated_rows:
                            update_dict['updated_user_rows'] = updated_rows

        return HttpResponse(json.dumps(update_dict, cls=af.LazyEncoder))
# - end of UploadImportUsernameView


# ========  upload_username_from_datalist  ======= # PR2021-08-04 PR2022-03-19 PR2023-01-29 PR2023-04-06
def upload_username_from_datalist(sel_examyear_instance, data_dict, double_username_list, double_email_list, log_list, is_test, user_lang, request):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- upload_username_from_datalist  --------------------')
        logger.debug('sel_examyear_instance: ' + str(sel_examyear_instance))
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
    function_str = data_dict.get('function')
    function_first_letter_lc = function_str[0].lower() if function_str else None
    usergroups_list = ['read']

    if function_first_letter_lc:
        if function_first_letter_lc in ('v', 'p'): # 'Voorzitter', 'Chairperson'
            usergroups_list.extend(['archive', 'auth1', 'download', 'msgreceive', 'msgsend'])
        elif function_first_letter_lc == 's': # 'Secretaris', 'Secretary'
            usergroups_list.extend(['archive', 'auth2', 'download', 'msgreceive', 'msgsend'])
        elif function_first_letter_lc == 'e':  # 'Examiner'
            usergroups_list.append('auth3')
        elif function_first_letter_lc == 'g': # 'Gecommitteerde',
            usergroups_list.append('auth4')
        elif function_first_letter_lc == 'c': # 'Chairperson', 'Corrector'
            if len(function_str) > 1:
                function_second_letter_lc = function_str[1].lower()
                if function_second_letter_lc == 'h':  # 'Chairperson'
                    usergroups_list.extend(['archive', 'auth1', 'download', 'msgreceive', 'msgsend'])
                elif function_second_letter_lc == 'o':  # 'Corrector'
                    usergroups_list.append('auth4')

# - sort the list before saving, to be able to compare new and saved usergroups
    usergroups_list.sort()

# - convert to json
    usergroups_str = json.dumps(usergroups_list)

# - when school uploads users: get school_code from req_user instead of from data_dict
    if request.user.is_role_school:
        school_code = request.user.schoolbase.code

    if logging_on:
        logger.debug('schoolcode: ' + str(school_code))
        logger.debug('username_with_underscore: ' + str(username_with_underscore))
        logger.debug('last_name:  ' + str(last_name))
        logger.debug('email:      ' + str(email))
        logger.debug('usergroups_list: ' + str(usergroups_list))

# - check for double occurrence in upload file
    has_error = False
    has_username_error = stud_val.validate_double_schoolcode_username_in_uploadfile(school_code, username_with_underscore, double_username_list, error_list)
    if has_username_error:
        has_error = True

    has_email_error = stud_val.validate_double_schoolcode_email_in_uploadfile(school_code, email, double_email_list, error_list)
    if has_email_error:
        has_error = True

    if not has_error:
# - validate length of fields school_code and username
        err_txt = stud_val.validate_length(_('The school code'), school_code, c.MAX_LENGTH_SCHOOLCODE, False)
        if err_txt:
            has_error = True
            error_list.append(str(err_txt))

        err_txt = stud_val.validate_length(_('The username'), username_with_underscore, c.USERNAME_SLICED_MAX_LENGTH, False)
        if err_txt:
            has_error = True
            error_list.append(str(err_txt))

    if logging_on:
        logger.debug('error_list: ' + str(error_list))

    schoolbase = None
    is_new_user = False
    is_existing_user = False
    new_user_pk = None
    if not has_error:

# - lookup schoolbase and user in database
        # only one of is_new_user, is_existing_user or err_txt is trueish
        schoolbase, is_new_user, is_existing_user, err_txt = lookup_user(school_code, username_with_underscore, request)
        if err_txt:
            has_error = True
            error_list.append(str(err_txt))
        if logging_on:
            logger.debug('schoolbase: ' + str(schoolbase))
            logger.debug('is_new_user: ' + str(is_new_user))
            logger.debug('is_existing_user: ' + str(is_existing_user))
            logger.debug('err_txt: ' + str(err_txt))

    if not has_error:

# - validate length of last_name and unique at school
        if is_new_user:
            err_txt = awpr_val.validate_unique_user_lastname(schoolbase, last_name, None, True)
            if err_txt:
                has_error = True
                error_list.append(err_txt)

# - validate length and format of the email_address
            err_txt = awpr_val.validate_email_address(email)
            if err_txt:
                has_error = True
                error_list.append(err_txt)
            else:
# - validate unique email_address at school
                err_txt = awpr_val.validate_unique_useremail(email, request.user.country, schoolbase, None, True)
                if err_txt:
                    has_error = True
                    error_list.append(err_txt)

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
                    # PR2023-01-29 usergroups is moved to table UserAllowed
                    # was: usergroups=usergroups,
                    is_active=True,
                    activated=False,
                    lang=user_lang,
                    modified_by=request.user,
                    modified_at=now_utc
                )
                if not is_test:
                    new_user.save()
                    new_user_pk = new_user.pk

    # add userdata record PR2023-07-18
                    now_utc = timezone.now()
                    new_user_allowed = acc_mod.Userdata(
                        user=new_user,
                        modifiedby=request.user,
                        modifiedat=now_utc
                    )
                    new_user_allowed.save()

    # add user_allowed record with usergroups PR2023-01-29
                    new_user_allowed = acc_mod.UserAllowed(
                        user=new_user,
                        examyear=sel_examyear_instance,
                        usergroups=usergroups_str,
                        modifiedby=request.user,
                        modifiedat=now_utc
                    )
                    new_user_allowed.save()

            except Exception as e:
                has_error = True
                is_new_user = False
                new_user_pk = None

                logger.error(getattr(e, 'message', str(e)))
                err_txt = ''.join((str(_('An error occurred')), ': ', str(e)))
                error_list.append(err_txt)
                error_list.append(gettext("User account '%(val)s' can not be created.") % {'val': username_with_underscore})

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
        updated_rows = acc_view.create_user_rowsNEW(
            sel_examyear=sel_examyear_instance,
            request=request,
            user_pk=new_user_pk
        )

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
    err_txt = None

# - lookup schoolbase
    # err_txt already given when schoolbase is blank or too long ( in validate_student_name_length)
    if school_code:
        schoolbase = sch_mod.Schoolbase.objects.get_or_none(
            code__iexact=school_code.lower(),
            country=request.user.country
        )
    if schoolbase is None:
        err_txt = _("%(cpt)s '%(val)s' not found.") % {'cpt': _('School with code'), 'val': school_code}
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
                err_txt = _("Multiple users with username '%(val)s' exist at this school.") \
                          % {'val': username_with_underscore}

    if logging_on:
        logger.debug('----------- lookup_user ----------- ')
        logger.debug('--- schoolbase: ' + str(schoolbase))
        logger.debug('--- err_txt:    ' + str(err_txt))
        logger.debug('----------- end of lookup_user ----------- ')

    return schoolbase, is_new_user, is_existing_user, err_txt
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

        else:
            birthdate_iso = birthdate_dte.isoformat()

    if logging_on:
        logger.debug('birthdate_iso: ' + str(birthdate_iso))

    return birthdate_iso


def create_result_html(importtable, is_test, count_total, count_error, count_new, count_existing, count_diff_dep, count_pws_has_changed, is_user):
    # PR2021-06-18 PR2021-08-05 PR2022-03-18 PR2022-06-26 PR2024-08-08
    # function returns a html string with number of students, existing, new and erros
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

        if count_diff_dep:
            txt_plur = _('belong to a different department and will be skipped') if is_test else _('belong to a different department and are skipped')
            txt_sing = _('belongs to a different department and will be skipped') if is_test else _('belongs to a different department and is skipped')
            result_html += ''.join(("<li>",
                                    str(_("%(count)s %(cnd)s %(skip)s.")
                                        % {'count': count_diff_dep,
                                           'cnd': caption_plur if count_diff_dep > 1 else caption_sing,
                                           'skip': txt_plur if count_diff_dep > 1 else txt_sing}),
                                    '</li>'))
        if count_error:
            txt_plur = _('have errors and will be skipped') if is_test else _('have errors and are skipped')
            txt_sing = _('has an error and will be skipped') if is_test else _('has an error and is skipped')
            result_html += ''.join(("<li>",
                                    str(_("%(count)s %(cnd)s %(skip)s.")
                                        % {'count': count_error,
                                           'cnd': caption_plur if count_error > 1 else caption_sing,
                                           'skip': txt_plur if count_error > 1 else txt_sing}),
                                    '</li>'))

        if count_pws_has_changed:
            have_txt = _('has') if count_pws_has_changed == 1 else _('have')
            willbe_txt = pgettext_lazy('singular', 'will be') if is_test == 1 else _('has been')
            txt = _('%(have)s assignment info that %(willbe)s changed') % {'have': have_txt, 'willbe': willbe_txt }
            result_html += ''.join(("<li>",
                                    str(_("%(count)s %(cnd)s %(nw)s.")
                                        % {'count': count_pws_has_changed,
                                           'cnd': caption_plur if count_pws_has_changed > 1 else caption_sing,
                                           'nw': txt}),
                                    "</li>"))
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
# - end of create_result_html


def create_testresult_grade_html(is_test, count_dict, is_user=False):  # PR2021-06-18 PR2021-08-05
    # function returns an html string with number of students, existing, new and erros
    title = _('Test results') if is_test else _('Upload results')


    count_total = count_dict.get('stud_count', 0)


    result_html = ''.join(("<h6 class='mx-2 mt-2 mb-0'>", str(title), '</h6>'))
    if not count_total:
        result_html += ''.join(("<p>",
                                str(_("The uploaded file has no candidates.")),
                                "</p>"))
    else:
        candidate_txt = get_candidate_txt(count_total)
        result_html += ''.join(("<p>",
                                str(_("The uploaded file has %(count)s %(cnd)s:")
                                    % {'count': count_total,
                                       'cnd':candidate_txt}),
                                "</p>"))
        result_html += "<ul class='mb-0'>"

        count_stud_not_found = count_dict.get('stud_not_found', 0)
        count_stud_with_error = count_dict.get('stud_with_error', 0)
        count_no_subjects = count_dict.get('no_subjects', 0)
        count_notfound_subjects = count_dict.get('notfound_subjects', 0)
        count_subjects_with_error = count_dict.get('subjects_with_error', 0)
        count_grades_with_error = count_dict.get('grades_with_error', 0)
        count_changed_values = count_dict.get('changed_values', 0)

        if count_stud_not_found:
            candidate_txt = get_candidate_txt(count_stud_not_found)
            found_txt = _('has not been found in AWP') if count_stud_not_found == 1 else _('have not been found in AWP')
            skipped_txt = get_skipped_txt(count_stud_not_found, is_test)
            result_html += ' '.join(("<li>", str(count_stud_not_found), str(candidate_txt), str(found_txt), str(_('and')), str(skipped_txt), '</li>'))

        if count_stud_with_error:
            candidate_txt = get_candidate_txt(count_stud_with_error)
            error_txt = _('has an error') if count_stud_with_error == 1 else _('have errors')
            skipped_txt = get_skipped_txt(count_stud_with_error, is_test)
            result_html += ' '.join(("<li>", str(count_stud_with_error), str(candidate_txt), str(error_txt), str(_('and')), str(skipped_txt), '</li>'))

        if count_no_subjects:
            candidate_txt = get_candidate_txt(count_no_subjects)
            error_txt = _('has no subjects') if count_no_subjects == 1 else _('have no subjects')
            skipped_txt = get_skipped_txt(count_no_subjects, is_test)
            result_html += ' '.join(("<li>", str(count_no_subjects), str(candidate_txt), str(error_txt), str(_('and')), str(skipped_txt), '</li>'))

        if count_notfound_subjects:
            candidate_txt = get_candidate_txt(count_notfound_subjects)
            have_txt = _('has') if count_notfound_subjects == 1 else _('have')
            not_found_txt = _('subjects that this candidate does not have in AWP. These subjects')
            skipped_txt = get_skipped_txt(0, is_test)
            result_html += ' '.join(("<li>", str(count_notfound_subjects), str(candidate_txt), str(have_txt), str(not_found_txt), str(skipped_txt), '</li>'))

        if count_subjects_with_error:
            candidate_txt = get_candidate_txt(count_subjects_with_error)
            have_txt = _('has') if count_subjects_with_error == 1 else _('have')
            not_found_txt = _('subjects with errors. These subjects')
            skipped_txt = get_skipped_txt(0, is_test)
            result_html += ' '.join(("<li>", str(count_subjects_with_error), str(candidate_txt), str(have_txt), str(not_found_txt), str(skipped_txt), '</li>'))

        if count_grades_with_error:
            candidate_txt = get_candidate_txt(count_grades_with_error)
            have_txt = _('has') if count_grades_with_error == 1 else _('have')
            not_found_txt = _('grades with errors. These grades')
            skipped_txt = get_skipped_txt(0, is_test)
            result_html += ' '.join(("<li>", str(count_grades_with_error), str(candidate_txt), str(have_txt), str(not_found_txt), str(skipped_txt), '</li>'))

        if not count_changed_values:
            count_cand_txt = str(_('There are no candidates'))
        elif count_changed_values == 1:
            count_cand_txt = str(_('There is 1 candidate'))
        else:
            count_cand_txt = str(_('There are %(count)s candidates') % {'count': count_changed_values})
        added_or_changed_txt = get_added_or_changed_txt(is_test)
        result_html += ' '.join(("<li>", count_cand_txt, str(_('with grades that')), str(added_or_changed_txt), '</li>'))

        result_html += "</ul>"
        result_html += ' '.join(( '<p>', str(_("Click")),
                                        "<a href='#' class='awp_href' onclick='MIMP_OpenLogfile()'>",
                                        str(_("here")),
                                        "</a>",
                                        str(_("to download the logfile with the details.")),
                                        "</p>"
                                        ))

    return result_html
# - end of create_testresult_grade_html


def get_candidate_txt(count):  # PR2022-02-09
    return _('candidate') if count == 1 else  _('candidates')


def get_skipped_txt(count, is_test):  # PR2022-02-09
    return (pgettext_lazy('sing', 'will be skipped.') if count == 1 else
                   pgettext_lazy('plur', 'will be skipped.')) if is_test else \
                    (_('is skipped.') if count == 1 else _('are skipped.'))


def get_added_or_changed_txt( is_test):  # PR2022-02-09
    return (_('will be added or changed.')) if is_test else \
                    ( _('are added or changed.'))


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


def validate_student_exists_thisschool_thisschoolyear(school, department, idnumber_nodots):  # PR2021-06-14
    # - check if idnumber_nodots already exists in this school, this examyear

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ============= validate_student_exists_thisschool_thisschoolyear ============= ')
        logger.debug('idnumber_nodots: ' + str(idnumber_nodots))

    students = stud_mod.Student.objects.filter(
        idnumber__iexact=idnumber_nodots,
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
        err_str = str(_("ID-number '%(val)s' exists multiple times ") % {'val': idnumber_nodots})
        if found_in_diff_dep:
            if found_in_this_dep:
                err_str = str(_("in multiple departments of your school."))
            else:
                err_str = str(_("in other departments of your school."))
        elif found_in_this_dep:
            err_str = str(_("in this department."))

    elif row_count == 1:
        if found_in_diff_dep:
            err_str = str(_("ID-number '%(val)s' already exists in a different department.") % {'val': idnumber_nodots})
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
                    msg_err = None
# a. get new_value
                    new_value = field_dict.get('value')
                    saved_value = getattr(instance, field)

# 2. save changes in field 'code', required field
                    if field in ['code', 'identifier']:
                        if new_value != saved_value:
            # validate_code_name_blank_length_exists_id checks for null, too long and exists. Puts msg_err in update_dict
                            msg_err = None #stud_val.validate_code_name_blank_length_exists(
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

# - get subject list of this school/dep with number of occurrences in scheme
            count_subjectbase_dict = count_subjectbase_in_scheme(department)

# - get subject_codes from subjects of this department
            subject_code_dict = get_mapped_subjectbase_code_dict(department)

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


def get_students_dict_with_subjbase_pk_list(school, department):
    # PR2021-07-21 PR2022-03-17 PR2024-08-14
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- get_students_dict_with_subjbase_pk_list  --------------------')
        logger.debug('school.pk: ' + str(school.pk))
        logger.debug('department.pk: ' + str(department.pk))

    # function uses idnumber as key, this way you can skip lookup student

    # students_dict_with_subjbase_pk_list contains a dict with all students of this school and department, not deleted and not tobedeleted
    # it has the key idnumber and as value a dict with keys: subjbase_pk and value: subject_code
    # output:       dict: { idnumber: {student_id: id, subjectbase_pk: subject_code, ...}, ... }
    # '2004042204': {'stud_id': 3110, 133: 'ne', 134: 'en', 135: 'mm1', 136: 'lo', 138: 'pa', 141: 'wk', 142: 'ns1', 154: 'ns2', 155: 'sws'},

    # PR2023-08-29 debug KAP Hans Vlinkervleugel: cannot uploaded subjects for certain students not showing.
    # # cause: were added to deleted students.
    # solution: add stud.deleted and stud.tobedeleted to where clause


    exemp_grade_sql = ''.join((
        "SELECT grd.id, grd.studentsubject_id, grd.deleted ",
        "FROM students_grade AS grd ",

        # PR2024-08-14 don't filter on deleted exemption, can cause double exemption grade records
        # check deleted when adding exemption
        # was: "WHERE NOT grd.deleted AND NOT grd.tobedeleted ",

        "WHERE grd.examperiod =", str(c.EXAMPERIOD_EXEMPTION), "::INT ",
        "ORDER BY grd.id desc "
        "LIMIT 1"
    ))


   # sql_keys = {'ey_id': school.examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}
    sub_sql = ''.join((
        "WITH exemp_grade AS (" + exemp_grade_sql + ") ",
        "SELECT studsubj.student_id, ",

        "ARRAY_AGG(studsubj.id ORDER BY studsubj.id) AS studsubj_id_arr, ",
        "ARRAY_AGG(studsubj.deleted ORDER BY studsubj.id) AS studsubj_deleted_arr, ",
        "ARRAY_AGG(studsubj.tobedeleted ORDER BY studsubj.id) AS studsubj_tobedeleted_arr, ",
        "ARRAY_AGG(studsubj.subj_published_id ORDER BY studsubj.id) AS subj_published_id_arr, ",

        "ARRAY_AGG(studsubj.prev_auth1by_id ORDER BY studsubj.id) AS prev_auth1by_id_arr, ",
        "ARRAY_AGG(studsubj.prev_auth2by_id ORDER BY studsubj.id) AS prev_auth2by_id_arr, ",
        "ARRAY_AGG(studsubj.prev_published_id ORDER BY studsubj.id) AS prev_published_id_arr, ",

        "ARRAY_AGG(si.id ORDER BY studsubj.id) AS schemeitem_id_arr, ",

        "ARRAY_AGG(subj.base_id ORDER BY studsubj.id) AS subjbase_id_arr, ",
        "ARRAY_AGG(subjbase.code ORDER BY studsubj.id) AS subjbase_code_arr, ",

        "ARRAY_AGG(sjtp.has_pws ORDER BY studsubj.id) AS sjtp_has_pws_arr, ",
        "ARRAY_AGG(sjtp.base_id ORDER BY studsubj.id) AS sjtpbase_id_arr, ",

        "ARRAY_AGG(exemp_grade.id ORDER BY exemp_grade.id) AS exemp_grade_id_arr, ",
        "ARRAY_AGG(exemp_grade.deleted ORDER BY exemp_grade.id) AS exemp_grade_deleted_arr ",

        "FROM students_studentsubject AS studsubj ",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id) ",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id) ",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id) ",
        "INNER JOIN subjects_subjecttype AS sjtp ON (sjtp.id = si.subjecttype_id) ",

        "LEFT JOIN exemp_grade ON (exemp_grade.studentsubject_id = studsubj.id) ",

        "GROUP BY studsubj.student_id"
    ))
    # sub_sql row: (8855, 422, 'ne', False)

    sql = ''.join((
        "WITH sub_sql AS (" + sub_sql + ") ",
        "SELECT stud.idnumber, stud.id AS stud_id, stud.bis_exam, stud.linked, ",

        "CONCAT_WS (' ', stud.prefix, CONCAT(stud.lastname, ','), stud.firstname) AS fullname, ",

        "(stud.iseveningstudent OR stud.islexstudent) AS is_evelex_student, stud.partial_exam, ",
        "stud.scheme_id, ",
        "ey.code AS ey_code, "
        
        "sb.code AS sb_code, school.name AS school_name, "
        "dep.base_id AS depbase_id, depbase.code AS depbase_code, ",
        "lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev, ",
        "sct.base_id AS sctbase_id, sct.abbrev AS sct_abbrev, ",

        "sub_sql.studsubj_id_arr, sub_sql.studsubj_deleted_arr, sub_sql.studsubj_tobedeleted_arr, ",
        "sub_sql.subj_published_id_arr, ",
        "sub_sql.prev_auth1by_id_arr, sub_sql.prev_auth2by_id_arr, sub_sql.prev_published_id_arr, ",

        "sub_sql.subjbase_id_arr, sub_sql.subjbase_code_arr, sub_sql.sjtpbase_id_arr, ",
        "sub_sql.schemeitem_id_arr, sub_sql.sjtp_has_pws_arr, ",

        "sub_sql.exemp_grade_id_arr, sub_sql.exemp_grade_deleted_arr ",

        "FROM students_student AS stud ",

        "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
        "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

        "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

        "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",

        "LEFT JOIN sub_sql ON (sub_sql.student_id = stud.id) ",

        "WHERE stud.school_id=", str(school.pk), "::INT ",
        "AND stud.department_id=", str(department.pk), "::INT ",
        "AND NOT stud.deleted AND NOT stud.tobedeleted;"
    ))

    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = af.dictfetchall(cursor)

    # PR2024-08-08 used to lookup exemption.
    # linked_student_pk_list contains student_pk of students that
    # have linked students and have bis_exam or (is_evelex_student and not partial_exam)

    # other_student_pk_list contains a list of students_pk's that are in field 'linked'

    linked_student_pk_list = []
    other_student_pk_list = []

    students_with_subjectbase_pk_dict = {}
    if rows:

# ++++++ loop through students +++++
        for row in rows:
            if logging_on:
                logger.debug('............................................')
                logger.debug('    row: ' + str(row))

            # row: ('2003031202', 9240, 'Albertus', 'Lyanne Stephany', None, 372, 'ne', False)
            idnumber = row['idnumber']

# - get student_id, add as key to student_dict if it does not exists yet
            # PR2022-05-03 debug Roland Girigori Lauffer cannot upload grade because difference in lowercase/uppercase
            # must convert id_number from database to lowercase
            if idnumber:
                idnumber_lc = idnumber.lower()

                # check for double_idnumberlist outside this function. was:
                # - don't add idnumber to list when it is found multiple times in upload list
                #if double_idnumberlist and idnumber_lc in double_idnumberlist:
                #    if logging_on:
                #        logger.debug('id_number found in double_idnumberlist: ' + str(idnumber_lc))
                # elif idnumber_lc in students_with_subjectbase_pk_dict:

                if idnumber_lc in students_with_subjectbase_pk_dict:
                    if logging_on:
                        logger.debug('idnumber_lc found in students_with_subjectbase_pk_dict: ' + str(idnumber_lc) +
                                     ' - '  + str(students_with_subjectbase_pk_dict))
                else:
                    student_pk = row['stud_id']
                    bis_exam = row.get('bis_exam', False)
                    is_evelex_student = row.get('is_evelex_student', False)
                    partial_exam = row.get('partial_exam', False)

                    linked_str = row.get('linked')
                    linked_student_pk_arr = list(map(int, linked_str.split(';'))) if linked_str else []

                    if idnumber_lc not in students_with_subjectbase_pk_dict:
                        #  students_with_subjectbase_pk_dict[idnumber_lc] = {
                        student_dict = row
                        student_dict['linked_list'] = linked_student_pk_arr

        # - linked_student_pk_list contains students with:
                        # - field 'linked' has value and
                        # - bis_exam = True
                        # - or when evening or lex-student: bis_exam not necessary, but partial exam must be false

                        # linked_student_pk_list not in use yet, will be used in batch-create

                        if linked_student_pk_arr:
                            if bis_exam or (is_evelex_student and not partial_exam):
                                if student_pk not in linked_student_pk_list:
                                    linked_student_pk_list.append(student_pk)

                # - add other_student to other_student_pk_list
                                    for other_student_pk_str in linked_student_pk_arr:
                                        other_student_pk_int = int(other_student_pk_str)
                                        if other_student_pk_int not in other_student_pk_list:
                                            other_student_pk_list.append(other_student_pk_int)

# ++++++ loop through subjects of student +++++

# - get subjectbase_pk, add as key to scheme_dict if it does not exists yet
                        # rows is ordered by sjtpbase.sequence
                        # therefore the schemeitem_subject with the lowest sequence will be added
                        # a schemeitem_subject can only occur once in the subject_dict

                        studsubj_dict = {}
                        # PR2024-08-12 debug: subjbase_id_arr is None when student as no subjects yet
                        # gives error ''NoneType' object is not iterable'
                        # solved by adding: if subjbase_id_arr
                        subjbase_id_arr = row['subjbase_id_arr']
                        if subjbase_id_arr:
                            for i, subjectbase_pk in enumerate(subjbase_id_arr):

                                sjtp_has_pws = row['sjtp_has_pws_arr'][i]

                                """
                                PR2023-08-29 KAP Hans Vlinkervleugel: error importing studsubjects, cause by key subjbase_id = None
                                from upload:  data_dict: {'idnumber': '2005102301', 'subjects': {'116': 'lo', '117': 'cav', '118': 'pa', '142': 'asw', '148': 'pws', '149': 'wa', '152': 'kv', '155': 'ec', '159': 'sptl', '165': 'netl', '167': 'entl'}}
                                from database: student_dict: {'stud_id': 9109, 116: 'lo', 117: 'cav', 118: 'pa', 142: 'asw', 'has_pws_subjbase_pk': 148, 148: 'pws', 149: 'wa', 152: 'kv', 155: 'ec', 159: 'sptl', 165: 'netl', 167: 'entl', None: '-'}
                                solved by adding 'if subjectbase_pk'
                                """

                                if subjectbase_pk and subjectbase_pk not in studsubj_dict:
                                    studsubj_dict[subjectbase_pk] = {
                                        # these fields are alreay in parent dict 'student_dict'
                                        #'idnumber': row['idnumber'],
                                        #'stud_id': row['stud_id'],
                                        #'bis_exam': row['bis_exam'],
                                        #'linked': row['linked'],
                                        #'fullname': row['fullname'],
                                        #'is_evelex_student': row['is_evelex_student'],
                                        #'partial_exam': row['partial_exam'],

                                        #'ey_code': row['ey_code'],
                                        #'sb_code': row['sb_code'], 'school_name': row['school_name'],
                                        #'depbase_id': row['depbase_id'], 'depbase_code': row['depbase_code'],
                                        #'lvlbase_id': row['lvlbase_id'], 'lvl_abbrev': row['lvl_abbrev'],
                                        #'sctbase_id': row['sctbase_id'], 'sct_abbrev': row['sct_abbrev'],

                                        'scheme_id': row['scheme_id'],
                                        'studsubj_id': row['studsubj_id_arr'][i],
                                        'studsubj_deleted': row['studsubj_deleted_arr'][i],
                                        'studsubj_tobedeleted': row['studsubj_tobedeleted_arr'][i],
                                        'subj_published_id': row['subj_published_id_arr'][i],

                                        'prev_auth1by_id': row['prev_auth1by_id_arr'][i],
                                        'prev_auth2by_id': row['prev_auth2by_id_arr'][i],
                                        'prev_published_id': row['prev_published_id_arr'][i],

                                        'subjbase_id': subjectbase_pk,
                                        'subjbase_code': row['subjbase_code_arr'][i],

                                        'sjtp_has_pws': sjtp_has_pws,
                                        'sjtpbase_id': row['sjtpbase_id_arr'][i],
                                        'schemeitem_id': row['schemeitem_id_arr'][i],

                                        # PR2024-08-14  exemp_deleted can have value None, False or True
                                        # value None means there is no exemption grade of this subject
                                        # value False means this subject has an exemption grade
                                        # value True means this subject has a deleted exemption grade
                                        'exemp_grade_id': row['exemp_grade_id_arr'][i],
                                        'exemp_grade_deleted': row['exemp_grade_deleted_arr'][i]
                                    }

                                    if sjtp_has_pws:
                                        if 'has_pws_subjbase_pk' not in student_dict:
                                            student_dict['has_pws_subjbase_pk'] = subjectbase_pk
                                        else:
                                            # when multiple subjects with has_pws found: set has_pws_subjbase_pk = None
                                            student_dict['has_pws_subjbase_pk'] = None

                    # remove arr fields from student_dict
                        arr_field_list = []
                        for field in student_dict.keys():
                            if field[-4:] == '_arr':
                                arr_field_list.append(field)

                        if  arr_field_list:
                            for field in arr_field_list:
                                student_dict.pop(field)

    # - add studsubj_dict to student_dict
                        student_dict['studsubj'] =  studsubj_dict

    # - add student_dict to students_with_subjectbase_pk_dict with key  idnumber_lc
                        students_with_subjectbase_pk_dict[idnumber_lc] = student_dict

                        if logging_on:
                            logger.debug(' ***   student_dict: ' + str(student_dict))
    """
    students_with_subjectbase_pk_dict: {
        '2005022410': {
            'idnumber': '2005022410', 'stud_id': 11093, 'bis_exam': True, 
            'fullname': ' Castillo Cabrera, Merelyn Fabiana', 
            'is_evelex_student': True, 'partial_exam': False, 'scheme_id': 181, 'ey_code': 2025, 
            'sb_code': 'CUR14', 'school_name': 'Curaçaos Avondlyceum', 
            'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvlbase_id': 4, 'lvl_abbrev': 'TKL', 'sctbase_id': 13, 'sct_abbrev': 'ec', 
            'linked_arr': [10744, 7083], 
            'has_pws_subjbase_pk': 135, 
            'studsubj': {
                113: {'studsubj_id': 95419, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 
                    'subjbase_id': 113, 'subjbase_code': 'ne', 'sjtp_has_pws': False, 'sjtpbase_id': 31, 
                    'exemp_grade_id': None, 'exemp_grade_deleted': None}, 
                135: {'studsubj_id': 95425, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 
                    'subjbase_id': 135, 'subjbase_code': 'sws', 'sjtp_has_pws': True, 'sjtpbase_id': 35, 
                    'exemp_grade_id': None, 'exemp_grade_deleted': None},       
    """
    # sort, only to make testing easier
    linked_student_pk_list.sort()
    other_student_pk_list.sort()

    if logging_on:
        logger.debug(' ***   students_with_subjectbase_pk_dict: ' + str(students_with_subjectbase_pk_dict))

    return students_with_subjectbase_pk_dict, linked_student_pk_list, other_student_pk_list
# - end of get_students_dict_with_subjbase_pk_list

############################

def get_stud_subj_schemeitem_dict(sel_examyear, sel_school, sel_department): # PR2021-12-12 PR2022-08-21

    # PR2022-08-21 notatdayschool added: show this subject only when school is evening school or lex school
    # attention: day/evening school shows notatdayschool subjects. Must be filtered out when adding subjects to day student
    skip_notatdayschool = sel_school and (sel_school.islexschool or sel_school.iseveningschool)

    scheme_si_dict = {}
    schemeitem_rows = subj_view.create_schemeitem_rows(
        sel_examyear=sel_examyear,
        append_dict={},
        depbase=sel_department.base,
        cur_dep_only=True,
        skip_notatdayschool=skip_notatdayschool
    )
    if schemeitem_rows:
        for si_row in schemeitem_rows:
            si_id = si_row.get('id')
            scheme_id = si_row.get('scheme_id')
            if scheme_id not in scheme_si_dict:
                scheme_si_dict[scheme_id] = {}
            scheme_dict = scheme_si_dict[scheme_id]
            if si_id not in scheme_dict:
                scheme_dict[si_id] = si_row
    return scheme_si_dict
# - end of get_stud_subj_schemeitem_dict


############################
def map_subjectbase_pk_to_schemeitem_pk(sel_department_pk):
    # PR2021-07-21 PR2022-03-17 PR2024-08-16
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- map_subjectbase_pk_to_schemeitem_pk  --------------------')
        logger.debug('    sel_department_pk' + str(sel_department_pk))
    # function creates a dict per scheme of subjects with the lowest sequence
    # All subjects appear once, the one with the lowest sequence is added

    # output:
    # mapped_subjectbase_pk_dict = { scheme_id: { subjectbase_pk: [schemeitem_id, subject_code, has_pws_subjbase_pk] }, ... }
    # mapped_subjectbase_pk_dict: {249: {140: [2070, 'sp', 135], 133: [2054, 'ne', None],

    # rows is ordered by sjtpbase.sequence
    # therefore the schemeitem_subject with the sjtpbase.sequence will be added
    # a schemeitem_subject can only occur once in the subject_dict

    # PR2022-08-21 notatdayschool added: show this subject only when school is evening school or lex school
    # attention: day/evening school shows notatdayschool subjects. Must be filtered out when adding subjects to day student

    def get_schemeitem_rows():
        # --- create rows of all schemeitems of this examyear PR2020-11-17 PR2021-07-01 PR2022-08-21
        # schemeitem_rows = []
        sql = ' '.join(("SELECT si.id, si.scheme_id, ",
                    "scheme.name AS scheme_name, scheme.department_id, scheme.level_id, scheme.sector_id,",

                    "si.subject_id AS subj_id, subj.name_nl AS subj_name_nl, ",
                    "subjbase.id AS subjbase_id, subjbase.code AS subj_code, ",

                    "sjtpbase.id AS sjtpbase_id, sjtpbase.code AS sjtpbase_code, sjtpbase.sequence AS sjtpbase_sequence, ",
                    "sjtp.name AS sjtp_name, sjtp.abbrev AS sjtp_abbrev, ",
                    "sjtp.has_prac AS sjtp_has_prac, sjtp.has_pws AS sjtp_has_pws, ",

                    "depbase.id AS depbase_id, depbase.code AS depbase_code, ",
                    "lvl.base_id AS lvlbase_id, sct.base_id AS sctbase_id, ",
                    "lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ",

                    "si.id AS si_id, ",
                    #"si.is_combi, si.gradetype, si.weight_se, si.weight_ce, si.multiplier, si.ete_exam, si.otherlang, ",
                    #"si.is_mandatory, si.is_mand_subj_id, ",
                    #", si.extra_count_allowed, si.extra_nocount_allowed, ",
                    "si.has_practexam ",

                    "FROM subjects_schemeitem AS si ",
                    "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id) ",

                    "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id) ",
                    "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id) ",

                    "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id) ",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id) ",

                    "INNER JOIN subjects_subjecttype AS sjtp ON (sjtp.id = si.subjecttype_id) ",
                    "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = sjtp.base_id) ",

                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id) ",
                    "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id) ",

                    "WHERE dep.id = ", str(sel_department_pk), "::INT;",
                    ))

        with connection.cursor() as cursor:
            cursor.execute(sql)
            schemeitem_rows = af.dictfetchall(cursor)

        return schemeitem_rows
# --- end of create_schemeitem_rows

    mapped_subjectbase_pk_dict = {}

    schemeitem_rows = get_schemeitem_rows()

    if schemeitem_rows:
        for row in schemeitem_rows:

# - get scheme_id, add as key to schemeitems_dict if it does not exist yet
            scheme_id = row['scheme_id']
            if scheme_id not in mapped_subjectbase_pk_dict:
                mapped_subjectbase_pk_dict[scheme_id] = {
                    'scheme_name': row['scheme_name']
                }
            scheme_dict = mapped_subjectbase_pk_dict[scheme_id]

# - get subjbase_id, add as key to scheme_dict if it does not exist yet
            # rows is ordered by sjtpbase.sequence
            # therefore the schemeitem_subject with the lowest sequence will be added
            # a schemeitem_subject can only occur once in the subject_dict
            subjbase_id = row['subjbase_id']
            if subjbase_id not in scheme_dict:
                scheme_dict[subjbase_id] = {
                    'subjbase_id': subjbase_id,
                    'subj_code': row['subj_code'],
                    'subj_name_nl': row['subj_name_nl'],
                    'default_sjtpbase_sequence': None,
                    'default_sjtpbase_id': None
                }
            subject_dict = scheme_dict[subjbase_id]

            sjtpbase_id = row['sjtpbase_id']
            if sjtpbase_id not in subject_dict:
                # default_sjtpbase_sequence is used in importing sudsubj, beccause sjtp is not imported the sjtp with the lowest sequence will be used
                sjtpbase_sequence = row['sjtpbase_sequence']
                if sjtpbase_sequence is not None:
                    default_sjtpbase_sequence = subject_dict['default_sjtpbase_sequence']
                    if default_sjtpbase_sequence is None or sjtpbase_sequence < default_sjtpbase_sequence:
                        subject_dict['default_sjtpbase_sequence'] = sjtpbase_sequence
                        subject_dict['default_sjtpbase_id'] = sjtpbase_id

                subject_dict[sjtpbase_id] = {
                    'si_id': row['si_id'],
                    'sjtpbase_id': sjtpbase_id,
                    'sjtp_name': row['sjtp_name'],
                    'sjtp_abbrev': row['sjtp_abbrev'],
                    'sjtp_has_prac': row['sjtp_has_prac'],
                    'sjtp_has_pws': row['sjtp_has_pws'],
                    'sjtpbase_sequence': sjtpbase_sequence
                }

    if logging_on:
        logger.debug('mapped_subjectbase_pk_dict' + str(mapped_subjectbase_pk_dict))
    """
    mapped_subjectbase_pk_dict: { 
        scheme_id: { 
            subjbase_id: {
                sjtpbase_id': {si_id

    mapped_subjectbase_pk_dict{
        175: {'scheme_name': 'Vsbo - PBL - ec', 
                154: {'subjbase_id': 154, 'subj_code': 'hospbb', 'default_sjtpbase_sequence': 4, 'default_sjtpbase_id': 36,
                        726: {'si_id': 4377, 'sjtpbase_id': 36, 'sjtp_name': 'Sectorprogramma', 'sjtp_abbrev': 'Sectorprog.', 
                                'sjtp_has_prac': True, 'sjtp_has_pws': False, 'sjtpbase_sequence': 4}}, 
                117: {'subjbase_id': 117, 'subj_code': 'cav', 'default_sjtpbase_sequence': 1, 'default_sjtpbase_id': 33, 
                        723: {'si_id': 4378, 'sjtpbase_id': 33, 'sjtp_name': 'Gemeenschappelijk deel', 'sjtp_abbrev': 'Gemeensch.', 
                                'sjtp_has_prac': False, 'sjtp_has_pws': False, 'sjtpbase_sequence': 1}}, 
                114: {'subjbase_id': 114, 'subj_code': 'en', 'default_sjtpbase_sequence': 1,  'default_sjtpbase_id': 33, 
                        723: {'si_id': 4379, 'sjtpbase_id': 33, 'sjtp_name': 'Gemeenschappelijk deel', 'sjtp_abbrev': 'Gemeensch.', 
                                'sjtp_has_prac': False, 'sjtp_has_pws': False, 'sjtpbase_sequence': 1}, 
                        725: {'si_id': 4387, 'sjtpbase_id': 35, 'sjtp_name': 'Overig vak', 'sjtp_abbrev': 'Overig vak', 
                                'sjtp_has_prac': False, 'sjtp_has_pws': False, 'sjtpbase_sequence': 3}}, 
                               
    """
    return mapped_subjectbase_pk_dict
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


def upload_studentsubject_from_datalist(upload_data_dict, sel_examyear, sel_school, sel_department, is_test,
                                        double_idnumberlist, mapped_subjectbase_pk_dict,
                                        students_dict_with_subjbase_pk_list, linked_student_pk_list, other_student_pok_dict,
                                        tobe_inserted_or_updated_exemption_grade_dict,
                                        tobe_updated_studsubj_dict,
                                        log_list, request):
    # PR2021-07-21 PR2021-08-12 PR2022-03-17 PR2024-08-18
    # TODO add recalc_subj_composition PR2022-08-30
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----------------- upload_studentsubject_from_datalist  --------------------')
        logger.debug('    data_dict: ' + str(upload_data_dict))
        #logger.debug('    students_dict_with_subjbase_pk_list: ' + str(students_dict_with_subjbase_pk_list))

    """
    mapped_subjectbase_pk_dict = {scheme_id: {subjbase_id: {sjtpbase_id: {si_id: 4371...

    upload_data_dict: {
        'idnumber': '2005.02.24.10', 'pws_title': "Don't do it", 'pws_subjects': 'vak /?\\*"', 
        'subjects': {
            '113': 'ne', '114': 'en', '115': 'mm1', '118': 'pa', '120': 'sp', '133': 'ac', '135': 'sws', '155': 'ec'}}

    students_dict_with_subjbase_pk_list: {idnumber: {stud_id: id, 'studsubj': {subjbase_id: {} }
    students_dict_with_subjbase_pk_list: {
        '2005022410': {
            'idnumber': '2005022410', 'stud_id': 11094, 'bis_exam': False, 'linked': '10744;7083', 
            'fullname': ' Castillo Cabrera, Merelyn Fabiana', 
            'is_evelex_student': True, 'partial_exam': False, 
            'scheme_id': 181, 'ey_code': 2025,  'sb_code': 'CUR14', 'school_name': 'Curaçaos Avondlyceum', 
            'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvlbase_id': 4, 'lvl_abbrev': 'TKL', 'sctbase_id': 13, 'sct_abbrev': 'ec', 
            'has_pws_subjbase_pk': 135, 
            'studsubj': {
                113: {
                    'scheme_id': 181, 'studsubj_id': 95419, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 
                    'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 
                    'subjbase_id': 113, 'subjbase_code': 'ne', 
                    'sjtp_has_pws': False, 'sjtpbase_id': 31, 
                    'schemeitem_id': 4494, 
                    'exemp_grade_id': None, 'exemp_grade_deleted': None},
   
    """

    caption = _('This subject')
    this_subject_is_added_str = str(_("%(cpt)s will be added") % {'cpt': caption}) \
        if is_test else str(_("%(cpt)s is added") % {'cpt': caption})
    not_added_str = str(_("%(cpt)s will not be added.") % {'cpt': caption}) \
        if is_test else str(_("%(cpt)s is not added.") % {'cpt': caption})

    has_error = False
    pws_has_changed = False
    error_list = []
    studsubj_rows = []

    #lookup_field_caption = af.get_dict_value(c.CAPTIONS, ('student', 'idnumber'), '')
    lookup_field_caption = _('ID-number')

# - validate idnumber
    id_number = upload_data_dict.get('idnumber')
    idnumber_nodots, msg_err_list, birthdate_dteobjNIU = stud_val.get_idnumber_nodots_stripped_lower(id_number)
    if msg_err_list:
        has_error = True
        log_list.extend(msg_err_list)

# - check for double occurrence in upload file
    if not has_error:
        has_error = stud_val.validate_double_entries_in_uploadfile(
            caption=str(_('ID-number')),
            lookup_value=idnumber_nodots,
            double_entrieslist=double_idnumberlist,
            error_list=error_list
        )
        if error_list:
            log_list.extend(error_list)

    if logging_on:
        # logger.debug('students_dict_with_subjbase_pk_list: ' + str(students_dict_with_subjbase_pk_list))
        #logger.debug('    lookup_field_caption: ' + str(lookup_field_caption))
        logger.debug('    idnumber_nodots: ' + str(idnumber_nodots))
        logger.debug('    error_list: ' + str(error_list))
        logger.debug('    has_error:  ' + str(has_error))

    student_instance = None
    student_dict = None
    student_pk = None

    is_existing_student = False
    # TODO add code for is_diff_dep_student
    is_diff_dep_student = False

    has_pws_subjbase_pk = None
    has_multiple_pws_subjects = False

    if logging_on:
        #logger.debug('    students_dict_with_subjbase_pk_list: ' + str(students_dict_with_subjbase_pk_list))
        logger.debug('    linked_student_pk_list: ' + str(linked_student_pk_list))

    if not has_error:

# - lookup student in students_dict_with_subjbase_pk_list ( list only contains students of this dep, doubles in uploadlist are filtered out
        if idnumber_nodots in students_dict_with_subjbase_pk_list:
            student_dict = students_dict_with_subjbase_pk_list.get(idnumber_nodots)
            """
            student_dict: {
                'idnumber': '2005022410', 'stud_id': 11094, 'bis_exam': False, 'linked': '10744;7083', 
                'fullname': ' Castillo Cabrera, Merelyn Fabiana', 
                'is_evelex_student': True, 'partial_exam': False, 
                'scheme_id': 181, 'ey_code': 2025,  'sb_code': 'CUR14', 'school_name': 'Curaçaos Avondlyceum', 
                'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvlbase_id': 4, 'lvl_abbrev': 'TKL', 'sctbase_id': 13, 'sct_abbrev': 'ec', 
                'has_pws_subjbase_pk': 135, 
                'studsubj': {
                    113: {
                        'scheme_id': 181, 'studsubj_id': 95419, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 
                        'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 
                        'subjbase_id': 113, 'subjbase_code': 'ne', 
                        'sjtp_has_pws': False, 'sjtpbase_id': 31, 
                        'schemeitem_id': 4494, 
                        'exemp_grade_id': None, 'exemp_grade_deleted': None},
            """
            if logging_on and False:
                logger.debug('    student_dict: ' + str(student_dict))

            student_pk = student_dict.get('stud_id')
            if student_pk:
                student_instance = stud_mod.Student.objects.get_or_none(
                    pk=student_pk,
                    school=sel_school,
                    department=sel_department
                )

            if 'has_pws_subjbase_pk' in student_dict:
                value = student_dict.get('has_pws_subjbase_pk')
                if value:
                    has_pws_subjbase_pk = value
                else:
                    # if has_pws_subjbase_pk exists in student_dict and its value = None means: student has more than one subject with pws
                    has_multiple_pws_subjects = True

        if logging_on:
            logger.debug('    student_instance: ' + str(student_instance))

        if student_instance is None:
            has_error = True
            log_list.append(_("Candidate with ID-number '%(val)s' is not found.") % {'val': idnumber_nodots})

        elif student_instance.scheme is None:
            has_error = True
            log_list.append(idnumber_nodots + '  ' + student_instance.fullname + ' ' + str(student_instance.scheme))
            caption_txt = c.STRING_SPACE_05 + (c.STRING_SPACE_10)[:8]
            if student_instance.department_id is None:
                log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': _('department')}))
            if sel_department.sector_req and student_instance.sector_id is None:
                caption = _('profiel') if sel_department.has_profiel else _('sector')
                log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': caption}))
            if sel_department.level_req and student_instance.level_id is None:
                log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': _('leerweg')}))
            cpt = _('The subjects')
            if is_test:
                not_added_txt = pgettext_lazy('plural', "%(cpt)s will not be added.") % {'cpt': cpt}
            else:
                not_added_txt = pgettext_lazy('plural', "%(cpt)s have not been added.") % {'cpt': cpt}
            log_list.append(''.join((caption_txt, str(not_added_txt))))
        else:
            is_existing_student = True

    if not has_error:
        log_list.append(idnumber_nodots + '  ' + student_instance.fullname + ' ' + str(student_instance.scheme))

        import_pws_title = upload_data_dict.get('pws_title')
        import_pws_subjects = upload_data_dict.get('pws_subjects')

        # mapped_subjectbase_pk_dict = { scheme_id: { subjectbase_pk: [schemeitem_id, subject_code, has_pws] }, ... }
        # mapped_subjectbase_pk_dict: {249: {140: [2070, 'sp', False], 133: [2054, 'ne', False],
        scheme_dict = {}
        student_scheme_pk = student_instance.scheme_id
        if student_scheme_pk in mapped_subjectbase_pk_dict:
            scheme_dict = mapped_subjectbase_pk_dict.get(student_scheme_pk)

        # - use list of subjectbase_pk's of this student - to speed up search
        # - students_dict_with_subjbase_pk_list is a dict with key: student_pk and value: a dict with key: subjbase_pk and value: subject_code
        # output: students_dict_with_subjbase_pk_list: { student_id: {subjectbase_pk: subject_code, ...}, ... }
        student_subjbase_pk_dict = student_dict['studsubj']
        """
        student_subjbase_pk_dict: {
            113: {'scheme_id': 181, 'studsubj_id': 95419, 'studsubj_deleted': True, 'studsubj_tobedeleted': False, 
                'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 
                'subjbase_id': 113, 'subjbase_code': 'ne', 'sjtp_has_pws': False, 
                'sjtpbase_id': 31, 'schemeitem_id': 4494, 
                'exemp_grade_id': None, 'exemp_grade_deleted': None}, 
        """
        if logging_on and False:
            logger.debug('..... student_subjbase_pk_dict: ' + str(student_subjbase_pk_dict))
            logger.debug('      student_scheme: ' + str(student_scheme_pk) + ' ' + str(student_instance.scheme))

        # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
        # solved bij wrapping with str()

        if 'subjects' in upload_data_dict:
            # upload_subjects: {'133': 'ne', '134': 'en', '136': 'lo', '137': 'cav', '138': 'pa', '140': 'sp', '143': 'bi', '175': 'ec'}
            upload_subjects = upload_data_dict.get('subjects')
            if logging_on:
                logger.debug('      upload_subjects: ' + str(upload_subjects))
                #logger.debug('      student_subjbase_pk_dict: ' + str(student_subjbase_pk_dict))

            if upload_subjects:
                has_created_studsubj = False

# +++ loop through subjects of data_list ++++++++++++++++++++++++++++++++++++++
                for subjectbase_pk_str, subject_code in upload_subjects.items():
                    upload_subjbase_id = int(subjectbase_pk_str)
                    caption_txt = c.STRING_SPACE_05 + (subject_code + c.STRING_SPACE_10)[:8]

                    if logging_on:
                        logger.debug('      upload_subjbase_id: ' + str(upload_subjbase_id))

                    # - skip if student already has this subject, except when also importing pws title
                    # student_subjbase_pk_dict = {subjectbase_pk: subject_code, ...}
                    subjbase_dict = student_subjbase_pk_dict.get(upload_subjbase_id)

                    schemeitem_subjbase_dict = scheme_dict.get(upload_subjbase_id)
                    if logging_on:
                        logger.debug('    subjbase_dict: ' + str(subjbase_dict))
                        #logger.debug('    schemeitem_subjbase_dict: ' + str(schemeitem_subjbase_dict))
                    """
                    subjbase_dict: {
                        'scheme_id': 181, 'studsubj_id': 95419, 'studsubj_deleted': True, 'studsubj_tobedeleted': False, 
                        'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 
                        'subjbase_id': 113, 'subjbase_code': 'ne', 'sjtp_has_pws': False, 'sjtpbase_id': 31, 
                        'schemeitem_id': 4494, 'exemp_grade_id': None, 'exemp_grade_deleted': None}
                    schemeitem_subjbase_dict: {
                        'subjbase_id': 113, 'subj_code': 'ne', 'subj_name_nl': 'Nederlands', 'default_sjtpbase_sequence': 1, 
                        'default_sjtpbase_id': 31, 
                        31: {
                            'si_id': 4494, 'sjtpbase_id': 31, 'sjtp_name': 'Gemeenschappelijk deel', 'sjtp_abbrev': 'Gemeensch.', 
                            'sjtp_has_prac': False, 'sjtp_has_pws': False, 'sjtpbase_sequence': 1}}    
                    """
                    # check if student has this subject and is not deleted and not tobedeleted
                    if subjbase_dict is not None and \
                            not subjbase_dict['studsubj_deleted'] and \
                                            not subjbase_dict['studsubj_tobedeleted']:
                        log_str = ''.join(
                            (caption_txt, not_added_str, ' ', str(_("This candidate already has this subject."))))
                        log_list.append(log_str)
                        if logging_on:
                            logger.debug('..... ' + str(log_str))

                    # - skip if this subject is not found in scheme
                    # scheme_dict = { subjectbase_pk: [schemeitem_id, subject_code, has_pws] }
                    # scheme_dict = {140: [2070, 'sp', False], 133: [2054, 'ne', False], ...}
                    elif schemeitem_subjbase_dict is None:
                        log_str = ''.join((caption_txt, not_added_str, ' ',
                                           str(_("The subject does not occur in this subject scheme."))))
                        log_list.append(log_str)
                        if logging_on:
                            logger.debug('..... ' + str(log_str))
                    else:

# +++++ add subject when student does not have this subject and subject is found in scheme:

                        # - get schemeitem_sjtp_dict whith key sjtpbase_id from subjbase_dict
                        # get default schemeitem when sjtpbase_id is None (happens when importing studsubj

                        sjtpbase_id = schemeitem_subjbase_dict.get('default_sjtpbase_id')
                        schemeitem_sjtp_dict = schemeitem_subjbase_dict.get(sjtpbase_id)

                        if logging_on:
                            logger.debug('    sjtpbase_id: ' + str(sjtpbase_id))
                            logger.debug('    schemeitem_sjtp_dict: ' + str(schemeitem_sjtp_dict))
                        """
                        schemeitem_sjtp_dict: {
                            'si_id': 4494, 'sjtpbase_id': 31, 'sjtp_name': 'Gemeenschappelijk deel', 'sjtp_abbrev': 'Gemeensch.', 
                            'sjtp_has_prac': False, 'sjtp_has_pws': False, 'sjtpbase_sequence': 1}
    
                        """
                        schemeitem_pk = schemeitem_sjtp_dict.get('si_id')
                        sjtp_has_pws = schemeitem_sjtp_dict.get('sjtp_has_pws')

                        if sjtp_has_pws:
                            # has_pws_subjbase_pk has value when 1 subject with psw found
                            # has_pws_subjbase_pk is None and has_multiple_pws_subjects = True when multiple found
                            has_pws_subjbase_pk = upload_subjbase_id

         # - get schemeitem and upload_subjecttype
                        # if so. or no upload subjecttype given, add subject to student
                        schemeitem = subj_mod.Schemeitem.objects.get_or_none(pk=schemeitem_pk)

                        messages = []
                        err_list = []

# - check if lookup subjecttype is the same as the upload subjecttype
                        if schemeitem:

# - create studentsubject instance and grade instance
#       - schemeitem_pk is the subject with the lowest subjecttype sequence
                            studsubj, append_keyNIU = stud_view.create_studsubj(
                                student=student_instance,
                                schemeitem=schemeitem,
                                messages=messages,
                                error_list=err_list,
                                request=request,
                                skip_save=is_test,
                                is_import=True
                            )
                            if logging_on:
                                logger.debug('..... ' + str(studsubj))

                            if err_list:
                                log_list.append(''.join((caption_txt, ''.join(err_list))))
                                if logging_on:
                                    logger.debug('..... ' + str(err_list))

                            elif studsubj:
                                has_created_studsubj = True
                                log_str = ''.join((caption_txt, this_subject_is_added_str, ' ',
                                                   str(_('with character')),
                                                   " '" + schemeitem.subjecttype.abbrev + "'."))
                                log_list.append(log_str)
                                if logging_on:
                                    logger.debug('..... ' + str(log_str))

                 # - if linked_stud and has_pok: create exemption : set has_exemption=True and create exemption grade with pok_grades

                                # - linked_student_pk_list contains students with:
                                # - field 'linked' has value and
                                # - bis_exam = True
                                # - or when evening or lex-student: bis_exam not necessary, but partial exam must be false

                                if student_pk in linked_student_pk_list:
                                    create_exemption_sql_list(
                                        cur_student_dict=student_dict,
                                        cur_subjbase_pk=upload_subjbase_id,
                                        cur_subjbase_instance=studsubj,
                                        other_student_pok_dict=other_student_pok_dict,
                                        is_test=is_test,
                                        tobe_inserted_or_updated_exemption_grade_dict=tobe_inserted_or_updated_exemption_grade_dict,
                                        tobe_updated_studsubj_dict=tobe_updated_studsubj_dict,
                                        request=request
                                    )
                                if logging_on :
                                    logger.debug('    tobe_inserted_exemption_grade_dict: ' + str(tobe_inserted_or_updated_exemption_grade_dict))
                                    logger.debug('    tobe_updated_studsubj_dict: ' + str(tobe_updated_studsubj_dict))

                        elif err_list:
                                log_list.append(''.join((caption_txt, ''.join(err_list))))
                                if logging_on:
                                    logger.debug('..... ' + str(err_list))

# +++ end of loop through subjects of data_list ++++++++++++++++++++++++++++++++++++++

                if has_created_studsubj:
                    # PR2024-09-03 added: update_student_subj_composition
                    comp_ok_has_changed = stud_view.update_student_subj_composition(student_instance)

                    # - when studsubjects are added to student: add rows to studsubj_rows
                    # PR2021-08-13 to prevent timeout error: download studentsubject_rows in separate ajax call

                    """
                    append_dict = {'created': True}
                    rows = stud_view.create_studentsubject_rows(
                        sel_examyear=school.examyear,
                        sel_schoolbase=school.base if school else None,
                        sel_depbase=sel_department.base if sel_department else None,
                        sel_lvlbase=sel_lvlbase,
                        append_dict=append_dict,
                        student_pk=student.pk)
                    if rows:
                        studsubj_rows.extend(rows)
                    """

                else:
                    has_error = True
                    caption_txt = c.STRING_SPACE_05 + (c.STRING_SPACE_10)[:8]
                    log_str = ''.join((caption_txt, str(_("No subjects are added."))))
                    log_list.append(log_str)
                    if logging_on:
                        logger.debug('..... ' + str(log_str))

# +++ end of loop through subjects of data_list ++++++++++++++++++++++++++++++++++++++

# +++ add pws_title pws_subjects ++++++++++++++++++++++++++++++++++++++
        if import_pws_title or import_pws_subjects:

            caption_txt = c.STRING_SPACE_05 + (c.STRING_SPACE_10)[:8]

            not_added_str = str(_("Assignment info will not be added.")) \
                if is_test else str(_("Assignment info is not added."))
            if logging_on:
                logger.debug('--------- add pws_title pws_subjects -----')
                logger.debug('    has_pws_subjbase_pk: ' + str(has_pws_subjbase_pk))
                logger.debug('    has_multiple_pws_subjects: ' + str(has_multiple_pws_subjects))
                logger.debug('    import_pws_title: ' + str(import_pws_title))
                logger.debug('    import_pws_subjects: ' + str(import_pws_subjects))

            if has_multiple_pws_subjects:
                log_list.append(''.join((caption_txt, not_added_str)))
                log_list.append(''.join((caption_txt, str(_('Candidate has multiple subjects with assignment.')))))
            elif has_pws_subjbase_pk is None:
                log_list.append(''.join((caption_txt, not_added_str)))
                log_list.append(''.join((caption_txt, str(_('Candidate has no subject with assignment.')))))
            else:
                # - get student_subjects with subjecttype has_pws = True
                # check if there is none or multiple
                studsubj = stud_mod.Studentsubject.objects.get_or_none(
                    student=student,
                    schemeitem__subject__base_id=has_pws_subjbase_pk)
                if logging_on:
                    logger.debug('    studsubj: ' + str(studsubj))

                if not studsubj:
                    if is_test:
                        log_list.append(''.join((caption_txt, str(_("Assignment info will be added.")))))
                    else:
                        log_list.append(''.join((caption_txt, str(_("Assignment info is not added.")),
                                                 str(_("Subject could not be found.")))))
                else:
                    saved_pws_title = studsubj.pws_title
                    saved_pws_subjects = studsubj.pws_subjects
                    if logging_on:
                        logger.debug('  -> saved_pws_title: ' + str(saved_pws_title))
                        logger.debug('  -> saved_pws_subjects: ' + str(saved_pws_subjects))

                    # only save if value has changed, skip if upload_pws has no value
                    pws_has_changed = False
                    if import_pws_title:
                        # check length of title and pws_subjects
                        err_list = stud_val.validate_studsubj_pws_title_subjects_length('pws_title', import_pws_title)
                        if err_list:
                            for err_txt in err_list:
                                log_list.append(''.join((caption_txt, str(err_txt))))

                        elif import_pws_title != saved_pws_title:
                            studsubj.pws_title = import_pws_title
                            pws_has_changed = True

                            if logging_on:
                                logger.debug('  -> pws_title_has_changed: ' + str(pws_has_changed))

                    if import_pws_subjects:
                        err_list = stud_val.validate_studsubj_pws_title_subjects_length('pws_subjects',
                                                                                        import_pws_title)
                        if err_list:
                            for err_txt in err_list:
                                log_list.append(''.join((caption_txt, str(err_txt))))

                        elif import_pws_subjects != saved_pws_subjects:
                            studsubj.pws_subjects = import_pws_subjects
                            pws_has_changed = True
                            if logging_on:
                                logger.debug('  -> pws_subjects_has_changed: ' + str(pws_has_changed))

                    # is is_test and sws is a new subject it is not saved yet
                    if not pws_has_changed:
                        if is_test:
                            log_list.append(''.join((caption_txt, str(_("Assignment info will stay the same.")))))
                        else:
                            log_list.append(''.join((caption_txt, str(_("Assignment info is not changed.")))))
                    else:
                        if is_test:
                            log_list.append(''.join((caption_txt, str(_("Assignment info will be added.")))))
                        else:
                            studsubj.save(request=request)
                            log_list.append(''.join((caption_txt, str(_("Assignment info is added.")))))
                            updated_fields = []
                            if import_pws_title:
                                updated_fields.append(import_pws_title)
                            if import_pws_subjects:
                                updated_fields.append(import_pws_subjects)
                            awpr_log.savetolog_studentsubject(studsubj.pk, 'u', updated_fields)
                        # add field_dict to studsubj_dict
                        # studsubj_dict[field] = field_dict
        # +++ end of add pws_title pws_subjects ++++++++++++++++++++++++++++++++++++++

    return studsubj_rows, has_error, is_existing_student, is_diff_dep_student, pws_has_changed

# --- end of upload_studentsubject_from_datalist

def upload_studentsubject_from_datalist_v2NIUyet(upload_data_dict, school, department, is_test,
                                        double_idnumberlist,
                                        mapped_subjectbase_pk_dict,
                                        students_dict_with_subjbase_pk_list,
                                        linked_student_pk_list, other_student_pok_dict,
                                        tobe_inserted_studentsubject_dict,
                                        tobe_inserted_exemption_grade_dict,
                                        tobe_updated_studsubj_dict,
                                        log_list,
                                        request):
    # PR2021-07-21 PR2021-08-12 PR2022-03-17 PR2024-08-15
    # TODO add recalc_subj_composition PR2022-08-30
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----------------- upload_studentsubject_from_datalist  --------------------')
        logger.debug('    upload_data_dict: ' + str(upload_data_dict))
    """
    from upload_dict:
    upload_data_dict: {'idnumber': '2006.01.04.11', 
                'subjects': {'113': 'ne', '114': 'en', '115': 'mm1', '116': 'lo', '117': 'cav', '118': 'pa', '120': 'sp', '121': 'wk', '133': 'ac', '136': 'stg', '155': 'ec'}}
    """

    caption = _('This subject')
    this_subject_is_added_str = str(_("%(cpt)s will be added") % {'cpt': caption}) \
        if is_test else str(_("%(cpt)s is added") % {'cpt': caption})
    not_added_str = str(_("%(cpt)s will not be added.") % {'cpt': caption}) \
        if is_test else str(_("%(cpt)s is not added.") % {'cpt': caption})

    has_error = False
    pws_has_changed = False
    error_list = []
    studsubj_rows = []

    lookup_field_caption = _('ID-number')

# - validate idnumber
    id_number = upload_data_dict.get('idnumber')
    idnumber_nodots, msg_err_list, birthdate_dteobjNIU = stud_val.get_idnumber_nodots_stripped_lower(id_number)
    if msg_err_list:
        has_error = True
        log_list.extend(msg_err_list)

# - check for double occurrence in upload file
    if not has_error:
        has_error = stud_val.validate_double_entries_in_uploadfile(
            caption=str(_('ID-number')),
            lookup_value=idnumber_nodots,
            double_entrieslist=double_idnumberlist,
            error_list=error_list
        )
        if error_list:
            log_list.extend(error_list)

    if logging_on:
        logger.debug('    lookup_field_caption: ' + str(lookup_field_caption))
        logger.debug('    idnumber_nodots: ' + str(idnumber_nodots) + ' ' + str(type(idnumber_nodots)))
        logger.debug('    error_list: ' + str(error_list))
        logger.debug('    has_error: ' + str(has_error))

    is_existing_student = False
    # TODO add code for is_diff_dep_student
    is_diff_dep_student = False

    has_pws_subjbase_pk = None
    has_multiple_pws_subjects = False

    if not has_error:
        # students_dict_with_subjbase_pk_list contains a dict with all students of this school and department, not deleted and not tobedeleted
        # it has the key idnumber and as value a dict with keys: subjbase_pk and value: subject_code

# - check if student exists in students_dict_with_subjbase_pk_list
        #  list only contains students of this dep, not deleted nor tobedeleted, doubles in uploadlist are already filtered out
        # TODO return message when student is deleted of tobedeleted
        if idnumber_nodots not in students_dict_with_subjbase_pk_list:
            has_error = True
            log_list.append(_("Candidate with ID-number '%(val)s' is not found.") % {'val': str(idnumber_nodots)})

    if not has_error:
        student_dict = students_dict_with_subjbase_pk_list.get(idnumber_nodots)
        if logging_on and False:
            logger.debug('    student_dict: ' + str(student_dict))

        """
        students_with_subjectbase_pk_dict: {
            '2005022410': {
                'idnumber': '2005022410', 'stud_id': 11093, 'bis_exam': True, 
                'fullname': ' Castillo Cabrera, Merelyn Fabiana', 
                'is_evelex_student': True, 'partial_exam': False, 'scheme_id': 181, 'ey_code': 2025, 
                'sb_code': 'CUR14', 'school_name': 'Curaçaos Avondlyceum', 
                'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvlbase_id': 4, 'lvl_abbrev': 'TKL', 'sctbase_id': 13, 'sct_abbrev': 'ec', 
                'linked_arr': [10744, 7083], 
                'has_pws_subjbase_pk': 135, 
                'studsubj': {
                    113: {'studsubj_id': 95419, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 
                        'subjbase_id': 113, 'subjbase_code': 'ne', 'sjtp_has_pws': False, 'sjtpbase_id': 31, 
                        'exemp_grade_id': None, 'exemp_grade_deleted': None}, 
                    135: {'studsubj_id': 95425, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 
                        'subjbase_id': 135, 'subjbase_code': 'sws', 'sjtp_has_pws': True, 'sjtpbase_id': 35, 
                        'exemp_grade_id': None, 'exemp_grade_deleted': None},       
        """

        cur_student_pk = student_dict.get('stud_id')

        if 'has_pws_subjbase_pk' in student_dict:
            value = student_dict.get('has_pws_subjbase_pk')
            if value:
                has_pws_subjbase_pk = value
            else:
                # if has_pws_subjbase_pk exists in student_dict and its value = None means: student has more than one subject with pws
                has_multiple_pws_subjects = True

        fullname = student_dict['fullname']

        scheme_id = student_dict.get('scheme_id')
        lvlbase_id = student_dict.get('lvlbase_id')
        sctbase_id = student_dict.get('sctbase_id')

        lvl_abbrev = student_dict['lvl_abbrev'] if student_dict['lvl_abbrev'] else ''
        sct_abbrev = student_dict['sct_abbrev'] if student_dict['sct_abbrev'] else ''

        if not student_dict:
            has_error = True
            log_list.append(_("Candidate with ID-number '%(val)s' is not found.") % {'val': idnumber_nodots})

        elif scheme_id is None:
            has_error = True
            log_list.append(idnumber_nodots + '  ' + fullname)
            caption_txt = c.STRING_SPACE_05 + (c.STRING_SPACE_10)[:8]
            if department is None:
                log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': _('department')}))
            if department.sector_req and sctbase_id is None:
                caption = _('profiel') if department.has_profiel else _('sector')
                log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': caption}))
            if department.level_req and lvlbase_id is None:
                log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': _('leerweg')}))

            cpt = _('The subjects')
            if is_test:
                not_added_txt = pgettext_lazy('plural', "%(cpt)s will not be added.") % {'cpt': cpt}
            else:
                not_added_txt = pgettext_lazy('plural', "%(cpt)s have not been added.") % {'cpt':cpt}
            log_list.append(''.join((caption_txt, str(not_added_txt))))
        else:
            is_existing_student = True

        log_list.append(' '.join((
            idnumber_nodots, ' ',
            student_dict['fullname'],
            '-', student_dict['depbase_code'],
            lvl_abbrev,
            sct_abbrev
        )))

        import_pws_title = upload_data_dict.get('pws_title')
        import_pws_subjects = upload_data_dict.get('pws_subjects')

        """
        mapped_subjectbase_pk_dict: { scheme_id: { subjectbase_pk: {schemeitem_id, subject_code, sjtp_name, has_pws_subjbase_pk}
        mapped_subjectbase_pk_dict: {
            175: {118: {'schemeitem_id': 4382, 'subject_code': 'pa', 'sjtp_name': 'Gemeenschappelijk deel', 'has_pws_subjbase_pk': None}, 
                  135: {'schemeitem_id': 4527, 'subject_code': 'sws', 'sjtp_name': 'Sectorwerkstuk', 'has_pws_subjbase_pk': 135}},
        """

        scheme_dict = mapped_subjectbase_pk_dict.get(scheme_id)
        if logging_on and False:
            logger.debug('    scheme_dict: ' + str(scheme_dict))

# - use list of subjectbase_pk's of this student - to speed up search
        # - students_dict_with_subjbase_pk_list is a dict with key: student_pk and value: a dict with key: subjbase_pk and value: subject_code
        # output: students_dict_with_subjbase_pk_list: { student_id: {subjectbase_pk: subject_code, ...}, ... }
        studsubjects_dict = student_dict['studsubj']
        if logging_on:
            logger.debug('    studsubjects_dict: ' + str(studsubjects_dict))
        """
        studsubj_dict: {
            133: {'subjbase_id': 133, 'subjbase_code': 'ac', 'sjtp_has_pws': False, 'sjtpbase_id': 34}, 
            121: {'subjbase_id': 121, 'subjbase_code': 'wk', 'sjtp_has_pws': False, 'sjtpbase_id': 33},
            135: {'subjbase_id': 135, 'subjbase_code': 'sws', 'sjtp_has_pws': True, 'sjtpbase_id': 35}, 
        """

        upload_subjects = upload_data_dict.get('subjects')
        if logging_on:
            logger.debug('      upload_subjects: ' + str(upload_subjects))
        """
        upload_subjects: {'113': 'ne', '114': 'en', '115': 'mm1', '118': 'pa', '120': 'sp', '133': 'ac', '135': 'sws', '155': 'ec'}
        """
        if upload_subjects:
            has_created_studsubj = False

# +++ loop through subjects of upload_data_dict ++++++++++++++++++++++++++++++++++++++
            for subjbase_pk_str, subject_code in upload_subjects.items():
                upload_subjbase_pk_int = int(subjbase_pk_str)
                caption_txt = c.STRING_SPACE_05 + (subject_code + c.STRING_SPACE_10)[:8]
                if logging_on:
                    logger.debug('    -----')
                    logger.debug('    upload_subjbase_pk_int: ' + str(upload_subjbase_pk_int))
                    logger.debug('    caption_txt: ' + str(caption_txt))

# - skip if student already has this subject, except when also importing pws title
                # student_subjbase_pk_dict = {subjectbase_pk: subject_code, ...}
                cur_subj_dict = studsubjects_dict.get(upload_subjbase_pk_int)
                cur_studsubj_deleted = cur_subj_dict.get('studsubj_deleted', False) if cur_subj_dict else None
                cur_studsubj_tobedeleted = cur_subj_dict.get('studsubj_tobedeleted', False) if cur_subj_dict else None
                if logging_on:
                    logger.debug('    cur_subj_dict: ' + str(cur_subj_dict))
                    logger.debug('    cur_studsubj_deleted: ' + str(cur_studsubj_deleted))
                    logger.debug('    cur_studsubj_tobedeleted: ' + str(cur_studsubj_tobedeleted))

                if cur_subj_dict and not cur_studsubj_deleted and not cur_studsubj_tobedeleted:
                    log_str = ''.join((caption_txt, not_added_str, ' ', str(_("This candidate already has this subject."))))
                    log_list.append(log_str)
                    if logging_on:
                        logger.debug('..... ' + str(log_str))

# - skip if this subject is not found in scheme
                elif upload_subjbase_pk_int not in scheme_dict:
                    log_str = ''.join((caption_txt, not_added_str, ' ', str(_("The subject does not occur in this subject scheme."))))
                    log_list.append(log_str)
                    if logging_on:
                        logger.debug('..... ' + str(log_str))
                else:

# +++++ add subject when student does not have this subject and subject is found in scheme:

    # - check if lookup subjecttype is the same as the upload subjecttype - not in use

    # - add studentsubject - schemeitem_pk is the subject with the lowest subjecttype sequence
                        messages = []
                        err_list = []

                        insert_or_update_value_dict = create_studsubj_sql_v2(
                            cur_student_dict=student_dict,
                            scheme_dict=scheme_dict,
                            new_subjbase_id=upload_subjbase_pk_int,
                            new_sjtpbase_id=None,
                            new_pws_title = import_pws_title,
                            new_pws_subjects=import_pws_subjects,
                            error_list=err_list,
                            request=request,
                            skip_save=is_test,
                            is_import=True
                        )
                        if logging_on:
                            logger.debug('    insert_or_update_value_dict ' + str(insert_or_update_value_dict))

                        if insert_or_update_value_dict:
                            student_id = insert_or_update_value_dict.get('student_id')
                            schemeitem_id = insert_or_update_value_dict.get('schemeitem_id')
                            if student_id and schemeitem_id:
                                key_tuple = (student_id, schemeitem_id)
                                if key_tuple not in insert_or_update_value_dict:
                                    insert_or_update_value_dict[key_tuple] = insert_or_update_value_dict

                            has_created_studsubj = True
                            log_str = ''.join((caption_txt, this_subject_is_added_str, ' ',
                                              # str(_('with character')),  " '" + schemeitem_instance.subjecttype.abbrev + "'."
                                               ))
                            log_list.append(log_str)
                            if logging_on:
                                logger.debug('..... ' + str(log_str))

    # - if linked_stud and has_pok: create exemption : set has_exemption=True and create exemption grade with pok_grades

    # - linked_student_pk_list contains students with:
                            # - field 'linked' has value and
                            # - bis_exam = True
                            # - or when evening or lex-student: bis_exam not necessary, but partial exam must be false

                            if cur_student_pk in linked_student_pk_list:
                                create_exemption_sql_list(
                                    cur_student_dict=student_dict,
                                    cur_subjbase_pk=upload_subjbase_pk_int,
                                    other_student_pok_dict=other_student_pok_dict,
                                    is_test=is_test,
                                    tobe_inserted_or_updated_exemption_grade_dict=tobe_inserted_exemption_grade_dict,
                                    tobe_updated_studsubj_dict=tobe_updated_studsubj_dict,
                                    request=request
                                )

                        elif err_list:
                            log_list.append(''.join((caption_txt, ''.join(err_list))))
                            if logging_on:
                                logger.debug('..... ' + str(err_list))

# +++ end of loop through subjects of data_list ++++++++++++++++++++++++++++++++++++++

# - when studsubjects are added to student: add rows to studsubj_rows
            # PR2021-08-13 to prevent timeout error: download studentsubject_rows in separate ajax call
            if has_created_studsubj:
                pass
                """
                append_dict = {'created': True}
                rows = stud_view.create_studentsubject_rows(
                    sel_examyear=school.examyear,
                    sel_schoolbase=school.base if school else None,
                    sel_depbase=sel_department.base if sel_department else None,
                    sel_lvlbase=sel_lvlbase,
                    append_dict=append_dict,
                    student_pk=student.pk)
                if rows:
                    studsubj_rows.extend(rows)
                """
            else:
                has_error = True
                caption_txt = c.STRING_SPACE_05 + (c.STRING_SPACE_10)[:8]
                log_str = ''.join((caption_txt, str(_("No subjects are added."))))
                log_list.append(log_str)
                if logging_on:
                    logger.debug('..... ' + str(log_str))

# +++ end of loop ++++++++++++++++++++++++++++++++++++++


# +++ add pws_title pws_subjects ++++++++++++++++++++++++++++++++++++++
        if import_pws_title or import_pws_subjects:

            caption_txt = c.STRING_SPACE_05 + (c.STRING_SPACE_10)[:8]

            not_added_str = str(_("Assignment info will not be added.")) \
                if is_test else str(_("Assignment info is not added."))

            logger.debug('-----------> has_pws_subjbase_pk: ' + str(has_pws_subjbase_pk))
            logger.debug('-----------> has_multiple_pws_subjects: ' + str(has_multiple_pws_subjects))
            logger.debug('-----------> import_pws_title: ' + str(import_pws_title))
            logger.debug('-----------> import_pws_subjects: ' + str(import_pws_subjects))

            if has_multiple_pws_subjects:
                log_list.append(''.join( (caption_txt, not_added_str)))
                log_list.append(''.join( (caption_txt, str(_('Candidate has multiple subjects with assignment.')))))
            elif has_pws_subjbase_pk is None:
                log_list.append(''.join( (caption_txt, not_added_str)))
                log_list.append(''.join( (caption_txt, str(_('Candidate has no subject with assignment.')))))
            else:
                # - get student_subjects with subjecttype has_pws = True
                # check if there is none or multiple
                studsubj = stud_mod.Studentsubject.objects.get_or_none(
                    student_id=cur_student_pk,
                    schemeitem__subject__base_id=has_pws_subjbase_pk)
                logger.debug('-----------> studsubj: ' + str(studsubj))

                if not studsubj:
                    if is_test:
                        log_list.append(''.join((caption_txt, str(_("Assignment info will be added.")))))
                    else:
                       log_list.append(''.join((caption_txt, str(_("Assignment info is not added.")),
                                                     str(_("Subject could not be found.")))))
                else:
                    saved_pws_title = studsubj.pws_title
                    saved_pws_subjects = studsubj.pws_subjects
                    logger.debug('-----------> saved_pws_title: ' + str(saved_pws_title))
                    logger.debug('-----------> saved_pws_subjects: ' + str(saved_pws_subjects))

                    # only save if value has changed, skip if upload_pws has no value
                    pws_has_changed = False
                    if import_pws_title:
    # check length of title and pws_subjects
                        err_list = stud_val.validate_studsubj_pws_title_subjects_length('pws_title', import_pws_title)
                        if err_list:
                            for err_txt in err_list:
                                log_list.append(''.join((caption_txt, str(err_txt))))

                        elif import_pws_title != saved_pws_title:
                            studsubj.pws_title = import_pws_title
                            pws_has_changed = True
                            logger.debug('-----------> pws_title_has_changed: ' + str(pws_has_changed))

                    if import_pws_subjects:
                        err_list = stud_val.validate_studsubj_pws_title_subjects_length('pws_subjects', import_pws_title)
                        if err_list:
                            for err_txt in err_list:
                                log_list.append(''.join((caption_txt, str(err_txt))))

                        elif import_pws_subjects != saved_pws_subjects:
                            studsubj.pws_subjects = import_pws_subjects
                            pws_has_changed = True
                            logger.debug('-----------> pws_subjects_has_changed: ' + str(pws_has_changed))

            # is is_test and sws is a new subject it is not saved yet
                    if not pws_has_changed:
                        if is_test:
                            log_list.append(''.join((caption_txt, str(_("Assignment info will stay the same.")))))
                        else:
                            log_list.append(''.join( (caption_txt, str(_("Assignment info is not changed.")))))
                    else:
                        if is_test:
                            log_list.append(''.join( (caption_txt, str(_("Assignment info will be added.")))))
                        else:
                            studsubj.save(request=request)
                            log_list.append(''.join( (caption_txt, str(_("Assignment info is added.")))))
                            updated_fields = []
                            if import_pws_title:
                                updated_fields.append(import_pws_title)
                            if import_pws_subjects:
                                updated_fields.append(import_pws_subjects)

                            awpr_log.savetolog_studentsubject(studsubj.pk, 'u', updated_fields)

                        # add field_dict to studsubj_dict
                           # studsubj_dict[field] = field_dict
        # +++ end of add pws_title pws_subjects ++++++++++++++++++++++++++++++++++++++

    return studsubj_rows, has_error, is_existing_student, is_diff_dep_student, pws_has_changed
# --- end of upload_studentsubject_from_datalist


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def get_tobe_updated_gradelist_from_datalist(upload_data_dict, department, examyear, examperiod, examgradetype, is_test,
                                requsr_allowed_sections_dict, requsr_allowed_cluster_pk_list,
                               double_idnumberlist, scheme_si_dict, count_dict,
                               saved_student_subj_grade_dict, tobe_updated_dict,
                                new_exemption_pk_list, mapped_new_exemption_grade_list, log_list, request):
    # PR2021-12-09 PR202-02-16

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- get_tobe_updated_gradelist_from_datalist  --------------------')
        logger.debug('upload_data_dict: ' + str(upload_data_dict))
        logger.debug('examperiod: ' + str(examperiod))
        logger.debug('examgradetype: ' + str(examgradetype))
    """
    upload_data_dict: {'examnumber': 'A01', 'idnumber': '2003031202',
    'subjects': {'372': ['ne', '6,4'], '373': ['en', '6,7'], '374': ['mm1', '5,3'], '375': ['lo', '7,4'], '376': ['cav', '8,3'], '377': ['pa', '5,9'], '379': ['sp', '-'], '380': ['wk', '7,6'], '382': ['bi', '-'], '383': ['mm12', '-'], '390': ['zwi', '-'],
    '392': ['ac', '7,0'], '394': ['sws', '-'], '395': ['stg', 'G'], '414': ['ec', '6,8']}}

    mapped_subjectbase_pk_dict = { scheme_id: { subjectbase_pk: [schemeitem_id, subject_code] }, ... }
    mapped_subjectbase_pk_dict: {
        558: {376: [9793, 'cav'], 372: [9789, 'ne'], 373: [9790, 'en'], 374: [9791, 'mm1'], 375: [9792, 'lo'], 377: [9794, 'pa'], 379: [9798, 'sp'], 383: [9797, 'mm12'], 382: [9796, 'bi'], 380: [9795, 'wk'], 389: [9786, 'uv'], 390: [9787, 'zwi'], 395: [9788, 'stg']}, 
        556: {377: [9762, 'pa'], 379: [9772, 'sp'], 374: [9759, 'mm1'], 375: [9760, 'lo'], 372: [9757, 'ne'], 373: [9758, 'en'], 376: [9761, 'cav'], 380: [9763, 'wk'], 381: [9764, 'nask1'], 412: [9771, 'ict'], 388: [9769, 'ie'], 387: [9768, 'ecot'], 386: [9767, 'mvt'], 385: [9766, 'bw'], 384: [9765, 'mt'], 395: [9770, 'stg']}, 
        557: {372: [9773, 'ne'], 373: [9774, 'en'], 374: [9775, 'mm1'], 375: [9776, 'lo'], 376: [9777, 'cav'], 377: [9778, 'pa'], 379: [9785, 'sp'], 414: [9784, 'ec'], 380: [9780, 'wk'], 392: [9782, 'ac'], 391: [9781, 'hospks'], 395: [9783, 'stg']}, 
        559: {374: [9801, 'mm1'], 376: [9803, 'cav'], 377: [9804, 'pa'], 372: [9799, 'ne'], 373: [9800, 'en'], 375: [9802, 'lo'], 379: [9814, 'sp'], 381: [9806, 'nask1'], 380: [9805, 'wk'], 412: [9813, 'ict'], 384: [9807, 'mt'], 385: [9808, 'bw'], 386: [9809, 'mvt'], 387: [9810, 'ecot'], 388: [9811, 'ie'], 395: [9812, 'stg']}, 
        560: {374: [9817, 'mm1'], 373: [9816, 'en'], 377: [9820, 'pa'], 376: [9819, 'cav'], 375: [9818, 'lo'], 379: [9827, 'sp'], 372: [9815, 'ne'], 380: [9822, 'wk'], 414: [9826, 'ec'], 392: [9824, 'ac'], 391: [9823, 'hospks'], 395: [9825, 'stg']}, 
        561: {372: [9831, 'ne'], 373: [9832, 'en'], 374: [9833, 'mm1'], 375: [9834, 'lo'], 376: [9835, 'cav'], 377: [9836, 'pa'], 379: [9840, 'sp'], 380: [9837, 'wk'], 382: [9838, 'bi'], 383: [9839, 'mm12'], 390: [9829, 'zwi'], 389: [9828, 'uv'], 395: [9830, 'stg']}, 
        553: {372: [9702, 'ne'], 373: [9703, 'en'], 374: [9704, 'mm1'], 375: [9705, 'lo'], 376: [9706, 'cav'], 379: [9717, 'sp'], 377: [9715, 'pa'], 380: [9708, 'wk'], 381: [9716, 'nask1'], 393: [9709, 'nask2'], 383: [9711, 'mm12'], 414: [9712, 'ec'], 382: [9714, 'bi'], 412: [9718, 'ict'], 396: [9713, 'ta'], 394: [9710, 'sws']}, 
        555: {375: [9741, 'lo'], 376: [9742, 'cav'], 377: [9743, 'pa'], 379: [9754, 'sp'], 373: [9739, 'en'], 374: [9740, 'mm1'], 372: [9738, 'ne'], 380: [9745, 'wk'], 382: [9747, 'bi'], 383: [9755, 'mm12'], 381: [9746, 'nask1'], 393: [9751, 'nask2'], 414: [9753, 'ec'], 389: [9749, 'uv'], 390: [9750, 'zwi'], 394: [9752, 'sws']}, 
        554: {372: [9719, 'ne'], 373: [9720, 'en'], 374: [9721, 'mm1'], 375: [9722, 'lo'], 376: [9723, 'cav'], 377: [9724, 'pa'], 379: [9735, 'sp'], 414: [9734, 'ec'], 380: [9726, 'wk'], 381: [9727, 'nask1'], 383: [9728, 'mm12'], 393: [9731, 'nask2'], 382: [9736, 'bi'], 392: [9730, 'ac'], 391: [9729, 'hospks'], 394: [9732, 'sws']}}

    saved_student_subj_grade_dict: {
        2003012406: {'st_id': 9340, 'idnr': '2003012406', 'name': 'Weyman, Natisha F.', 'schm_id': 555, 'lvl_id': 117, 'sct_id': 266, 'egt': 'segrade', 'ep': 1, 
                376: {'sjb_id': 376, 'sjb_code': 'cav', 'gr_id': 68628, 'ss_id': 69168, 'val': '5.0', 'pescore': None, 'cescore': None, 'segrade': '4,7', 'srgrade': None, 'pegrade': None, 'cegrade': None, 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 
                373: {'sjb_id': 373, 'sjb_code': 'en', 'gr_id': 68625, 'ss_id': 69165, 'val': '6.0', 'pescore': None, 'cescore': None, 'segrade': '4,7', 'srgrade': None, 'pegrade': None, 'cegrade': None, 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 

    saved_student_dict: {'stud_id': 9240, 'name': 'Albertus, Lyanne S.', 'schm_id': 560, 'schm_name': 'Vsbo - PBL - ec', 'lvl_id': 119, 'sct_id': 265, 'egt': 'segrade', 'ep': 1, 
                380: {'sjb_id': 380, 'sjb_code': 'wk', 'ss_si_id': 9822, 'gr_id': 67386, 'ss_id': 67926, 'val': None, 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 
                376: {'sjb_id': 376, 'sjb_code': 'cav', 'ss_si_id': 9819, 'gr_id': 67384, 'ss_id': 67924, 'val': '5.6', 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 
                414: {'sjb_id': 414, 'sjb_code': 'ec', 'ss_si_id': 9826, 'gr_id': 67389, 'ss_id': 67929, 'val': '5.6', 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 
                373: {'sjb_id': 373, 'sjb_code': 'en', 'ss_si_id': 9816, 'gr_id': 67381, 'ss_id': 67921, 'val': '5.6', 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 
                375: {'sjb_id': 375, 'sjb_code': 'lo', 'ss_si_id': 9818, 'gr_id': 67383, 'ss_id': 67923, 'val': '5.6', 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 
                377: {'sjb_id': 377, 'sjb_code': 'pa', 'ss_si_id': 9820, 'gr_id': 67385, 'ss_id': 67925, 'val': '5.6', 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 
                395: {'sjb_id': 395, 'sjb_code': 'stg', 'ss_si_id': 9825, 'gr_id': 67388, 'ss_id': 67928, 'val': 'o', 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 
                392: {'sjb_id': 392, 'sjb_code': 'ac', 'ss_si_id': 9824, 'gr_id': 67387, 'ss_id': 67927, 'val': '5.6', 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 
                374: {'sjb_id': 374, 'sjb_code': 'mm1', 'ss_si_id': 9817, 'gr_id': 67382, 'ss_id': 67922, 'val': '5.6', 'publ': None, 'bl': False, 'st': 0, 'auth': False}, 
                372: {'sjb_id': 372, 'sjb_code': 'ne', 'ss_si_id': 9815, 'gr_id': 67380, 'ss_id': 67920, 'val': '5.6', 'publ': None, 'bl': False, 'st': 0, 'auth': False}} 

    scheme_si_dict: {
        553: {
            9702: {'id': 9702, 'scheme_id': 553, 'department_id': 1, 'level_id': 117, 'sector_id': 264, 'mapid': 'schemeitem_9702', 'subj_id': 2114, 'subj_name': 'Nederlandse taal', 'subjbase_id': 372, 'subj_code': 'ne', 'sjtpbase_code': 'gmd', 'sjtpbase_sequence': 1, 'sjtp_id': 5016, 'sjtp_name': 'Gemeenschappelijk deel', 'sjtp_abbrev': 'Gemeensch.', 'sjtp_has_prac': False, 'sjtp_has_pws': False, 'sjtp_min_subjects': None, 'sjtp_max_subjects': None, 'scheme_name': 'Vsbo - TKL - tech', 'scheme_fields': 'mand;comb', 'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvlbase_id': 12, 'sctbase_id': 12, 'lvl_abbrev': 'TKL', 'sct_abbrev': 'tech', 'code': 2021, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'ete_exam': False, 'otherlang': None, 'is_mandatory': True, 'is_mand_subj_id': None, 'is_combi': False, 'extra_count_allowed': False, 'extra_nocount_allowed': False, 'has_practexam': False, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'sr_allowed': False, 'max_reex': 1, 'no_thirdperiod': False, 'no_exemption_ce': False, 'modifiedby_id': 1, 'modifiedat': datetime.datetime(2021, 9, 4, 19, 55, 29, 806970, tzinfo=<UTC>), 'modby_username': 'Hans'}, 
            9703: {'id': 9703, 'scheme_id': 553, 'department_id': 1, 'level_id': 117, 'sector_id': 264, 'mapid': 'schemeitem_9703', 'subj_id': 2115, 'subj_name': 'Engelse taal', 'subjbase_id': 373, 'subj_code': 'en', 'sjtpbase_code': 'gmd', 'sjtpbase_sequence': 1, 'sjtp_id': 5016, 'sjtp_name': 'Gemeenschappelijk deel', 'sjtp_abbrev': 'Gemeensch.', 'sjtp_has_prac': False, 'sjtp_has_pws': False, 'sjtp_min_subjects': None, 'sjtp_max_subjects': None, 'scheme_name': 'Vsbo - TKL - tech', 'scheme_fields': 'mand;comb', 'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvlbase_id': 12, 'sctbase_id': 12, 'lvl_abbrev': 'TKL', 'sct_abbrev': 'tech', 'code': 2021, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'ete_exam': False, 'otherlang': None, 'is_mandatory': True, 'is_mand_subj_id': None, 'is_combi': False, 'extra_count_allowed': False, 'extra_nocount_allowed': False, 'has_practexam': False, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'sr_allowed': False, 'max_reex': 1, 'no_thirdperiod': False, 'no_exemption_ce': False, 'modifiedby_id': 1, 'modifiedat': datetime.datetime(2021, 9, 4, 19, 55, 29, 833378, tzinfo=<UTC>), 'modby_username': 'Hans'}, 
    """

    caption = _('This score') if 'score' in examgradetype else _('This grade')
    caption_plural = _('These scores') if 'score' in examgradetype else _('These grades')
    sc_gr_plural =  _('The scores') if 'score' in examgradetype else _('The grades')

    #this_subject_is_added_str = str(_("%(cpt)s will be added") % {'cpt': caption}) \
    #    if is_test else str(_("%(cpt)s is added") % {'cpt': caption})
    #not_added_str = str(_("%(cpt)s will not be added.") % {'cpt': caption}) \
   #     if is_test else str(_("%(cpt)s is not added.") % {'cpt': caption})
    #not_added_plural_str = str(pgettext_lazy('plural', "%(cpt)s will not be added.") % {'cpt': caption_plural}) \
    #    if is_test else str(pgettext_lazy('plural', "%(cpt)s are not added.") % {'cpt': caption_plural})

    has_error = False
    error_list = []

    lookup_field_caption = af.get_dict_value(c.CAPTIONS, ('student', 'idnumber'), '')

    log_list.append(c.STRING_SPACE_05)

# - validate idnumber
    id_number = upload_data_dict.get('idnumber')
    idnumber_nodots, msg_err_list, birthdate_dteobjNIU = stud_val.get_idnumber_nodots_stripped_lower(id_number)
    if msg_err_list:
        has_error = True
        log_list.extend(msg_err_list)

# - check for double occurrence in upload file
    if not has_error:
        has_error = stud_val.validate_double_entries_in_uploadfile(
            caption=str(_('ID-number')),
            lookup_value=idnumber_nodots,
            double_entrieslist=double_idnumberlist,
            error_list=error_list
        )
        if error_list:
            log_list.extend(error_list)

    stud_id = None
    stud_name = '---'
    schm_name = '-'

    saved_student_dict = {}
    scheme_dict = {}

# - lookup student in saved_student_subj_grade_dict ( list only contains students of this dep, doubles in uploadlist are filtered out
    if not has_error:
        saved_student_dict = saved_student_subj_grade_dict.get(idnumber_nodots)

        if saved_student_dict is None:
            has_error = True
            log_list.append(_("Candidate with ID-number '%(val)s' is not found.") % {'val': idnumber_nodots})

    caption_txt = c.STRING_SPACE_05 + (c.STRING_SPACE_10)[:8]
    if has_error:
        count_dict['stud_not_found'] += 1
    else:
        stud_id = saved_student_dict.get('stud_id')
        stud_name = saved_student_dict.get('name', '---')
        student_scheme_pk = saved_student_dict.get('schm_id')
        schm_name = saved_student_dict.get('schm_name', '-')

# - get scheme_dict of scheme of this student
        scheme_dict = scheme_si_dict.get(student_scheme_pk) if student_scheme_pk else None

        if scheme_dict is None:
            has_error = True
            count_dict['stud_with_error'] += 1

            log_list.append(idnumber_nodots + '  ' + stud_name)
            log_list.append(' '.join((caption_txt, str(_("The subject scheme of this candidate is not found.")))))

            lvl_id = saved_student_dict.get('lvl_id')
            sct_id = saved_student_dict.get('sct_id')

            if department.sector_req and sct_id is None:
                caption = _('profiel') if department.has_profiel else _('sector')
                log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': caption}))
            if department.level_req and lvl_id is None:
                log_list.append(caption_txt + str(_('This candidate has no %(cpt)s.') % {'cpt': _('leerweg')}))

            if is_test:
                not_added_txt = pgettext_lazy('plural', "%(cpt)s will not be added.") % {'cpt': sc_gr_plural}
            else:
                not_added_txt = pgettext_lazy('plural', "%(cpt)s have not been added.") % {'cpt': sc_gr_plural}
            log_list.append(''.join((caption_txt, str(not_added_txt))))

    if not has_error:

        log_list.append(idnumber_nodots + '  ' + stud_name + ' ' + schm_name)

        # - use list of subjectbase_pk's of this student - to speed up search
        # - students_dict_with_subjbase_pk_list is a dict with key: student_pk and value: a dict with key: subjbase_pk and value: subject_code
        # output: students_dict_with_subjbase_pk_list:
        """
        students_dict_with_subjbase_pk_list: {
            '2005022410': {
                'stud_id': 11098, 'idnumber': '2005022410', 
                'bis_exam': True, 'is_evelex_student': True, 'partial_exam': False, 
                'linked_arr': [10744, 7083], 
                'has_pws_subjbase_pk': 135, 
                'studsubj': {
                    133: {'subjbase_id': 133, 'subjbase_code': 'ac', 'sjtp_has_pws': False, 'sjtpbase_id': 34}, 
        """
        if logging_on:
            logger.debug('..... stud_name: ' + str(stud_name))
            logger.debug('      schm_name: ' + str(schm_name) + ' ' + str(type(schm_name)))
            logger.debug('      stud_id: ' + str(stud_id) + ' ' + str(type(stud_id)))

        # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
        # solved bij wrapping with str()
        upload_subjects_dict = upload_data_dict.get('subjects')

        """
        upload_subjects_dict: {'372': ['ne', '6,4'], '373': ['en', '6,7'], '374': ['mm1', '5,3'], '375': ['lo', '7,4'], 
                                '376': ['cav', '8,3'], '377': ['pa', '5,9'], '379': ['sp', '-'], '380': ['wk', '7,6'], 
                                '382': ['bi', '-'], '383': ['mm12', '-'], '390': ['zwi', '-'], '392': ['ac', '7,0'], 
                                '394': ['sws', '-'], '395': ['stg', 'G'], '414': ['ec', '6,8']}
        saved_subj_dict: {'sjb_id': 372, 'sjb_code': 'ne', 'is_extra_nocount': False, 'is_extra_counts': False, 
                            'has_exemption': False, 'has_sr': False, 'has_reex': False, 'has_reex03': False, 
                            'ss_si_id': 9815, 'gr_id': 67380, 'ss_id': 67920, 'val': '5.6', 
                            
                            'pescore': None, 'cescore': None, 'segrade': '4,7', 'srgrade': None, 'pegrade': None, 'cegrade': None, 
                            
                            'publ': False, 'bl': False, 'auth': False, 
                            'exam_id': None, 'nex_id': None, 'scalelength': None, 'cesuur': None, 'nterm': None}
        """

        if upload_subjects_dict is None:
            count_dict['no_subjects'] += 1
            caption_txt = c.STRING_SPACE_05 + (c.STRING_SPACE_10)[:8]
            log_str = '      '.join(
                (caption_txt, str(_("This candidate has no subjects in the upload file."))))
            log_list.append(log_str)
            if logging_on:
                logger.debug('..... ' + str(log_str))

        else:
            if logging_on:
                logger.debug('upload_subjects_dict: ' + str(upload_subjects_dict))

            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            has_notfound_subjects, has_subjects_with_error, has_grades_with_error, has_changed_values = False, False, False, False

# ++++++++  loop through upload_subjects_dict of upload_data_dict
            for sjbase_pk_str, grade_arr in upload_subjects_dict.items():

                subject_not_found, subject_has_error, grade_has_error, value_has_changed = \
                    import_studsubj_grade_from_datalist(request, examyear, examperiod, examgradetype, saved_student_dict, scheme_dict,
                                        requsr_allowed_sections_dict, requsr_allowed_cluster_pk_list,
                                        sjbase_pk_str, grade_arr, tobe_updated_dict, log_list, is_test)
                if subject_not_found:
                    has_notfound_subjects = True
                if subject_has_error:
                    has_subjects_with_error = True
                if grade_has_error:
                    has_grades_with_error = True
                if value_has_changed:
                    has_changed_values= True

 # +++ end of loop through subjects of data_list ++++++++++++++++++++++++++++++++++++++
            if has_notfound_subjects:
                count_dict['notfound_subjects'] += 1
            if has_subjects_with_error:
                count_dict['subjects_with_error'] += 1
            if has_grades_with_error:
                count_dict['grades_with_error'] += 1
            if has_changed_values:
                count_dict['changed_values'] += 1

# +++ end of loop ++++++++++++++++++++++++++++++++++++++

        """
        # - dont save data when it is a test run
        if not is_test:
            # - get scheme and update in student, also remove if necessary
            new_scheme = subj_mod.Scheme.objects.get_or_none(
                department=student.department,
                level=student.level,
                sector=student.sector)
            setattr(student, 'scheme', new_scheme)

            try:
                student.save(request=request)
                # studsubj_dict['id']['pk'] = student.pk
                # studsubj_dict['id']['ppk'] = student.company.pk
            except Exception as e:
                # - give error msg when creating student failed
                error_str = str(_("An error occurred. The student data is not saved."))
                # TODO
                code_text = '---'
                log_list.append(" ".join((code_text, error_str)))
                # studsubj_dict['row_error'] = error_str
        """
    return has_error
# --- end of get_tobe_updated_gradelist_from_datalist


def import_studsubj_grade_from_datalist(request, examyear, examperiod, examgradetype, saved_student_dict, scheme_dict,
                            requsr_allowed_sections_dict, requsr_allowed_cluster_pk_list,
                            sjbase_pk_str, grade_arr, tobe_updated_dict, log_list, is_test):
    # PR2021-12-10 PR2022-01-04 PR2022-02-09 PR2022-02-19
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- import_studsubj_grade_from_datalist ----- ')
        logger.debug('       examperiod:    ' + str(examperiod) + ' ' + str(type(examperiod)))
        logger.debug('       examgradetype: ' + str(examgradetype) + ' ' + str(type(examgradetype)))
        logger.debug('       sjbase_pk_str: ' + str(sjbase_pk_str) + ' ' + str(type(sjbase_pk_str)))
        logger.debug('       grade_arr:     ' + str(grade_arr) + ' ' + str(type(grade_arr)))
        # grade_arr =  ['ne', '6,4']

    """
    saved_student_dict has a left join with grade: if grade does not exist: gr_id = None
    
    subject dict of this examperiod
        464: {'sjb_id': 464, 'sjb_code': 'ec', 'is_extra_nocount': False, 'is_extra_counts': False, 
                'has_exemption': False, 'has_sr': False, 'has_reex': False, 'has_reex03': False, 
                'ss_si_id': 10093, 'gr_id': None, 'ss_id': None, 'val': None, 
                'pescore': None, 'cescore': None, 'segrade': None, 'srgrade': None, 'pegrade': None, 'cegrade': None, 
                'publ': None, 'bl': None, 'auth': None, 'exam_id': None, 
                'nex_id': None, 'scalelength': None, 'cesuur': None, 'nterm': None}, 
    """

    upload_sjbase_code = grade_arr[0] if grade_arr[0] else '-'
    grade_str = str(grade_arr[1]) if grade_arr[1] else ''

    upload_sjbase_pk_int = int(sjbase_pk_str)
    caption_txt = c.STRING_SPACE_05 + (upload_sjbase_code + c.STRING_SPACE_10)[:8]

    if logging_on:
        logger.debug('       sjbase_code:   ' + str(upload_sjbase_code) )
        logger.debug('       grade_str:     ' + str(grade_str) + ' ' + str(type(grade_str)))
        logger.debug('       sjbase_pk_int: ' + str(upload_sjbase_pk_int) + ' ' + str(type(upload_sjbase_pk_int)))

# --- lookup upload_sjbase_pk_int in saved_subj_grade_dict
    saved_studsubj_dict = saved_student_dict.get(upload_sjbase_pk_int)
    if logging_on:
        logger.debug('       saved_studsubj_dict: ' + str(saved_studsubj_dict))

    """
    saved_student_dict: {
        'stud_id': 9240, 'name': 'Albertus, Lyanne S.', 'schm_id': 560, 'schm_name': 'Vsbo - PBL - ec', 
        'lvl_id': 119, 'sct_id': 265, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 4,
        'iseveningstudent': False, 'islexstudent': False, 'partial_exam': False, 
        'isdayschool': False, 'iseveningschool': False, 'islexschool': False, 
        'egt': 'segrade', 'ep': 1, 
        372: {'sjb_id': 372, 'sjb_code': 'ne', cluster_id: 300, 'is_extra_nocount': False, 'is_extra_counts': False, 
                'has_exemption': False, 'has_sr': False, 'has_reex': False, 'has_reex03': False, 
                'ss_si_id': 9815, 'gr_id': 67380, 'ss_id': 67920, 'val': '6.4', 
                'pescore': None, 'cescore': None, 'segrade': '4,7', 'srgrade': None, 'pegrade': None, 'cegrade': None, 
                'publ': False, 'bl': False, 'auth': False, 
                'exam_id': None, 'nex_id': None, 'scalelength': None, 'cesuur': None, 'nterm': None}, 

    saved_subj_dict: {'sjb_id': 372, 'sjb_code': 'ne', cluster_id: 300, 'is_extra_nocount': False, 'is_extra_counts': False, 
                    'has_exemption': False, 'has_sr': False, 'has_reex': False, 'has_reex03': False, 
                    'ss_si_id': 9815, 'gr_id': 67380, 'ss_id': 67920, 'val': '5.6', 
                    'publ': False, 'bl': False, 'auth': False, 
                    'exam_id': None, 'nex_id': None, 'scalelength': None, 'cesuur': None, 'nterm': None}
    """

    subject_not_found = False
    subject_has_error = False
    grade_has_error = False

    value_has_changed = False

# - give error when student doesn't have this subject
    # saved_subj_grade_dict = {subjectbase_pk: subject_code, ...}
    if saved_studsubj_dict is None:
        subject_not_found = True
        log_str = '      '.join(
            (caption_txt, str(_("This candidate does not have subject '%(cpt)s'.") % {'cpt': upload_sjbase_code})))
        log_list.append(log_str)
        if logging_on:
            logger.debug('..... ' + str(log_str))
    else:
        grade_pk = saved_studsubj_dict.get('gr_id')
        studsubj_pk = saved_studsubj_dict.get('ss_id')
        if logging_on:
            logger.debug('  grade_pk: ' + str(grade_pk))
            logger.debug('  studsubj_pk: ' + str(studsubj_pk))

# --- lookup schemitem_dict of this subject
        ss_si_id = saved_studsubj_dict.get('ss_si_id')  # studsubj.schemeitem_id
        si_dict = scheme_dict.get(ss_si_id)
        if logging_on and False:
            logger.debug('  ss_si_id: ' + str(ss_si_id))
            logger.debug('  si_dict: ' + str(si_dict))

# - skip if this subject is not found in scheme - should not be possible, schemeitem is looked up with studsubj.schemeitem_id
        # scheme_dict = { subjectbase_pk: [schemeitem_id, subject_code] }
        # scheme_dict = {140: [2070, 'sp'], 133: [2054, 'ne'], ...}
        if si_dict is None:
            subject_has_error = True
            log_str = ' '.join(
                (caption_txt, str(_("Subject '%(cpt)s' does not occur in the subject scheme of this candidate.") \
                                                 % {'cpt': upload_sjbase_code})))
            log_list.append(log_str)

        else:

# - check if req_user is allowed to import this grade
            err_list = []

# - check if school department and level are allowed
            schoolbase_pk = saved_student_dict.get('schoolbase_id')
            if not acc_prm.validate_userallowed_school(requsr_allowed_sections_dict, schoolbase_pk):
                err_list.append(str(_("You don't have permission to upload %(cpt)s.") % {'cpt': _('This school').lower()}))
            else:
                depbase_pk = saved_student_dict.get('depbase_id')
                if logging_on:
                    logger.debug('  saved_student_dict: ' + str(saved_student_dict))
                    logger.debug('  depbase_pk: ' + str(depbase_pk))
                if not acc_prm.validate_userallowed_depbase(requsr_allowed_sections_dict, schoolbase_pk, depbase_pk):
                    err_list.append(str(_("You don't have permission to upload %(cpt)s.") % {'cpt': _('This department').lower()}))
                else:
                    lvlbase_pk = saved_student_dict.get('lvlbase_id')
                    if not acc_prm.validate_userallowed_lvlbase(requsr_allowed_sections_dict, schoolbase_pk, depbase_pk, lvlbase_pk):
                        err_list.append(str(_("You don't have permission to upload %(cpt)s.") % {'cpt': _('this level')}))
                    else:
                        subjbase_pk = saved_studsubj_dict.get('sjb_id')
                        if not acc_prm.validate_userallowed_subjbase(requsr_allowed_sections_dict, schoolbase_pk, depbase_pk, lvlbase_pk, subjbase_pk):
                            err_list.append(str( _("You don't have permission to upload %(cpt)s.") % {'cpt': _('this subject')}))
                        elif requsr_allowed_cluster_pk_list:
                            cluster_pk = saved_studsubj_dict.get('cluster_id')
                            if not cluster_pk or not str(cluster_pk) in requsr_allowed_cluster_pk_list:
                                err_list.append(str(_("You don't have permission to upload %(cpt)s.") % {'cpt': _('This cluster').lower()}))

# - validate import grade
            exemption_grade_tobe_created = False
            output_str = None
            if not err_list:
                outpt_str, err_lst, exemp_grade_tobe_created = \
                    grade_val.validate_import_grade(
                        student_dict=saved_student_dict,
                        studsubj_dict=saved_studsubj_dict,
                        si_dict=si_dict,
                        examyear=examyear,
                        examperiod=examperiod,
                        examgradetype=examgradetype,
                        grade_str=grade_str,
                        is_test=is_test
                    )
                if err_lst:
                    err_list.extend(err_lst)
                exemption_grade_tobe_created = exemp_grade_tobe_created
                if outpt_str:
                    output_str = outpt_str

                if logging_on:
                    logger.debug('..... output_str: ' + str(output_str))
                    logger.debug('..... err_list: ' + str(err_list))
                    logger.debug('..... exemption_grade_tobe_created: ' + str(exemption_grade_tobe_created))

# - write msg_err when error to logfile
            if err_list:
                if not exemption_grade_tobe_created:
                    grade_has_error = True
                show_subj_code = True
                for msg_err in err_list:
                    log_txt = ''.join((caption_txt, c.STRING_SPACE_05, ' ', msg_err)) if show_subj_code else \
                        '    '.join((c.STRING_SPACE_15, msg_err))
                    if show_subj_code:
                        show_subj_code = False
                    log_list.append(log_txt)

            if not grade_has_error:
                saved_value = saved_studsubj_dict.get('val')
                if logging_on:
                    logger.debug('..... saved_value: ' + str(saved_value))

# - check if value has changed
                if output_str:
                    if saved_value:
                        if output_str != saved_value:
                            value_has_changed = True
                    else:
                        value_has_changed = True
                elif saved_value:
                    value_has_changed = True

                if logging_on:
                    logger.debug('..... value_has_changed: ' + str(value_has_changed))

                if value_has_changed:

# - when value_has_changed: recalc sesr, pece and final grade PR2022-02-03
                    # examgradetypes are: 'segrade', 'srgrade', 'pescore', 'pegrade', 'cescore', 'cegrade
                    # calculaed fields are: 'sesrgrade', 'pecegrade', 'finalgrade'

                    """
                    si_dict: {'id': 10099, 'scheme_id': 249, 'department_id': 97, 'level_id': 84, 
                    'sector_id': 182, 'mapid': 'schemeitem_10099', 
                    'subj_id': 2166, 'subj_name': 'Mens en Maatschappij 1', 'subjbase_id': 424, 'subj_code': 'mm1', 
                    'sjtpbase_code': 'gmd', 'sjtpbase_sequence': 1, 'sjtp_id': 5094, 'sjtp_name': 'Gemeenschappelijk deel', 'sjtp_abbrev': 'Gemeensch.', 
                    'sjtp_has_prac': False, 'sjtp_has_pws': False,
                       'sjtp_min_subjects': None, 'sjtp_max_subjects': None, 
                       'scheme_name': 'Vsbo - TKL - z&w', 'scheme_fields': 
                       'mand;comb', 'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvlbase_id': 12, 'sctbase_id': 14, 'lvl_abbrev': 'TKL', 
                       'sct_abbrev': 'z&w', 'code': 2022, 'ey_no_practexam': False, 'ey_sr_allowed': True, 'ey_no_centralexam': False, 
                       'ey_no_thirdperiod': False, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 0, 'multiplier': 1, 'ete_exam': False, 
                       'otherlang': None, 'is_mandatory': True, 'is_mand_subj_id': None, 'is_combi': True, 'extra_count_allowed': False, 
                       'extra_nocount_allowed': False, 'has_practexam': False, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 
                       'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'sr_allowed': False, 'max_reex': 1, 'no_thirdperiod': False, 
                       'no_exemption_ce': False, 
                    
                    """
                    # PR2022-02-09
                    # values of examgradetype are:
                    #   'exemsegrade', 'exemcegrade', 'segrade', 'srgrade', 'pescore', 'pegrade',
                    #   'cescore', 'cegrade', 'reexscore', 'reexgrade', 'reex03score','reex03grade'

                    # input db_fields are: pescore, cescore, segrade, srgrade,  pegrade, cegrade
                    # calculated db_fields are: sesrgrade  pecegrade  finalgrade
                    db_field = grade_val.get_grade_db_field_from_examgradetype(examgradetype)

    #   gl_sesrgrade_str = ''.join(("'", gl_sesr, "'")) if gl_sesr else 'NULL'
                    #pescore =  output_str if examgradetype == 'pescore' else saved_studsubj_dict.get('pescore')
                    #cescore = output_str if examgradetype == 'cescore' else saved_studsubj_dict.get('cescore')
                    segrade = output_str if db_field == 'segrade' else saved_studsubj_dict.get('segrade')
                    srgrade = output_str if db_field == 'srgrade' else saved_studsubj_dict.get('srgrade')
                    pegrade = output_str if db_field == 'pegrade' else saved_studsubj_dict.get('pegrade')
                    cegrade = output_str if db_field == 'cegrade' else saved_studsubj_dict.get('cegrade')

                    has_sr = saved_studsubj_dict.get('has_sr', False)
                    exemption_year = saved_studsubj_dict.get('exem_year')

                    if logging_on and False:
                        logger.debug(' ..........  calc_sesr_pece_final_grade ')
                        logger.debug('       segrade: ' + str(segrade) + ' ' + str(type(segrade)))
                        logger.debug('       srgrade: ' + str(srgrade) + ' ' + str(type(srgrade)))
                        logger.debug('       pegrade: ' + str(pegrade) + ' ' + str(type(pegrade)))
                        logger.debug('       cegrade: ' + str(cegrade) + ' ' + str(type(cegrade)))

                    sesr_grade, pece_grade, finalgrade, delete_cegrade = \
                        calc_final.calc_sesr_pece_final_grade(
                            si_dict=si_dict,
                            examperiod=examperiod,
                            has_sr=has_sr,
                            exemption_year=exemption_year,
                            se_grade=segrade,
                            sr_grade=srgrade,
                            pe_grade=pegrade,
                            ce_grade=cegrade
                        )

                    sql_output_str = ''.join(("'", output_str, "'")) if output_str else 'NULL'
                    sql_sesr_grade_str = ''.join(("'", sesr_grade, "'")) if sesr_grade else 'NULL'
                    sql_pece_grade_str = ''.join(("'", pece_grade, "'")) if pece_grade else 'NULL'
                    sql_finalgrade_str = ''.join(("'", finalgrade, "'")) if finalgrade else 'NULL'

                    if logging_on and False:
                        logger.debug('......  grade_pk: ' + str(grade_pk))
                        logger.debug('        studsubj_pk: ' + str(studsubj_pk))
                        logger.debug('        sql_output_str: ' + str(sql_output_str))
                        logger.debug('        sql_sesr_grade_str: ' + str(sql_sesr_grade_str))
                        logger.debug('        sql_pece_grade_str: ' + str(sql_pece_grade_str))
                        logger.debug('        sql_finalgrade_str: ' + str(sql_finalgrade_str))

# - when value_has_changed: add new value to tobe_updated_dict
                    tobe_updated_dict[studsubj_pk] = {
                        'grade_pk': grade_pk,
                        'studsubj_pk': studsubj_pk,
                        'output_str': sql_output_str,
                        'sesr_grade': sql_sesr_grade_str,
                        'pece_grade': sql_pece_grade_str,
                        'finalgrade': sql_finalgrade_str}

# - when value_has_changed: update calculated fields
                output_nz = output_str.replace('.', ',') if output_str else ''
                output_spaces = (output_nz + c.STRING_SPACE_10)[:6]

                blank_str = ''.join(('<', str(_('blank')), '>'))
                saved_value_nz = (saved_value.replace('.', ',') if saved_value else blank_str) + c.STRING_SPACE_10

                has_changed_txt = gettext('has changed') if value_has_changed else gettext('unchanged')
                log_list.append(''.join((caption_txt, output_spaces, str(_('was')), ': ', saved_value_nz[:10], has_changed_txt)))

    if logging_on:
        logger.debug(' ----- end ----- ')
    return subject_not_found, subject_has_error, grade_has_error, value_has_changed
# --- end of import_studsubj_grade_from_datalist



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


def update_grade_batch(tobe_updated_dict, sel_db_field, request):  #PR2022-02-03
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- update_grade_batch  --------------------')
        #logger.debug('tobe_updated_dict: ' + str(tobe_updated_dict))

    updated_grade_pk_list = []
    updated_studsubj_pk_list = []
    if tobe_updated_dict and sel_db_field and request.user:
       # sql_keys = {'ey_id': school.examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}

        modifiedby_pk_str = str(request.user.pk)
        modifiedat_str = str(timezone.now())

        sql_keys = {'fieldname': sel_db_field}
        # also add fields sesrgrade, pecegrade, finalgrade. Those are recalc fields

        """
        # you can define the types by casting the values of the first row:
        CREATE TEMP TABLE lookup (key, val) AS
        VALUES 
            (0::bigint, -99999::int), 
            (1, 100) ;
        """
       # tobe_updated_dict = {'grade_pk': grade_pk, 'studsubj_pk': studsubj_pk, 'output_str': sql_output_str,
       #                      'sesr_grade': sql_sesr_grade_str, 'pece_grade': sql_pece_grade_str, 'finalgrade': sql_finalgrade_str})

        try:

            # fields are: [grade_id, value, sesrgrade, pecegrade, finalgrade, modifiedby_id, modifiedat]
            # datatype of cescore, pescore is Number, orthers are Text
            new_value_def = "0::INT," if 'score' in sel_db_field else "'-'::TEXT,"
            sql_list = ["CREATE TEMP TABLE gr_update (grade_id, new_value, sesrgrade, pecegrade, finalgrade) AS",
                "VALUES (0::INT,", new_value_def, "'-'::TEXT, '-'::TEXT, '-'::TEXT)"]

            for row in tobe_updated_dict.values():
                grade_pk = row.get('grade_pk')
                if grade_pk:
                    output_str = row.get('output_str', "'NULL'")
                    sesr_grade = row.get('sesr_grade', "'NULL'")
                    pece_grade = row.get('pece_grade', "'NULL'")
                    finalgrade = row.get('finalgrade', "'NULL'")

                    sql_list.append(''.join((", (", str(grade_pk), ", ", str(output_str) , ", ", str(sesr_grade) , ", ", str(pece_grade) , ", ", str(finalgrade) , ")")))
            sql_list.extend((
                "; UPDATE students_grade AS gr",
                "SET", sel_db_field, "= gr_update.new_value, ",
                "sesrgrade = gr_update.sesrgrade, pecegrade = gr_update.pecegrade, finalgrade = gr_update.finalgrade, ",
                "modifiedby_id = ", modifiedby_pk_str, ", modifiedat = '" , modifiedat_str, "'",
                "FROM gr_update",
                "WHERE gr_update.grade_id = gr.id",
                "RETURNING gr.id, gr.studentsubject_id;"
                ))

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql: ' + str(sql))
            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        updated_grade_pk_list.append(row[0])
                        # add studsubj_pk to list, to udate has_exemption later

                        if row[1] not in updated_studsubj_pk_list:
                            updated_studsubj_pk_list.append(row[1])
                # PR2023-08-15 TODO: batch savetolog

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

        return updated_grade_pk_list, updated_studsubj_pk_list
# - end of update_grade_batch


def update_hasexemption_in_studsubj_batch(tobe_updated_studsubj_pk_list, examyear, request):
    #PR2022-02-19 PR2022-04-15
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- update_hasexemption_in_studsubj_batch  --------------------')
        logger.debug('tobe_updated_studsubj_pk_list: ' + str(tobe_updated_studsubj_pk_list))

    # PR2022-02-19 only for exemption: add 'has_exemption' to studsubj
    # not for reex and reex03, they must set has_reex manually first
    if tobe_updated_studsubj_pk_list and request.user:

        try:
            modifiedby_pk_str = str(request.user.pk)
            modifiedat_str = str(timezone.now())

            # add previous examyear as exemption_year,
            # filter 'not when eveningschool or lexschool' is too complicated, because it can be different for each student.
            # therefore add to all students

            previous_exam_year = examyear.code - 1
            sql_keys = {'studsubj_pk_arr': tobe_updated_studsubj_pk_list,
                        'prev_ey': previous_exam_year}

            sql_list = [
                "UPDATE students_studentsubject ",
                "SET has_exemption = TRUE, exemption_year = %(prev_ey)s::INT, ",
                "modifiedby_id = ", modifiedby_pk_str, ", modifiedat = '" , modifiedat_str, "' ",
                "WHERE students_studentsubject.id IN ( SELECT UNNEST(%(studsubj_pk_arr)s::INT[]) ) ",
                "AND NOT students_studentsubject.has_exemption"
                "RETURNING students_studentsubject.student_id;"
                ]

            sql = ''.join(sql_list)
            if logging_on:
                logger.debug('sql: ' + str(sql))

            updated_student_pk_list = []
            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        updated_student_pk_list.append(row[0])
    # set bis_exam = TRUE in table students
            sql_keys = {'student_pk_arr': updated_student_pk_list}
            if updated_student_pk_list:
                sql_list = [
                    "UPDATE students_student AS stud",
                    "SET bis_exam = TRUE, ",
                    "modifiedby_id = ", modifiedby_pk_str, ", modifiedat = '", modifiedat_str, "' ",
                    "WHERE stud.id IN ( SELECT UNNEST(%(student_pk_arr)s::INT[]) ) ",
                    "AND NOT stud.bis_exam;",
                ]
                sql = ' '.join(sql_list)

                with connection.cursor() as cursor:
                    cursor.execute(sql, sql_keys)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of update_hasexemption_in_studsubj_batch


@method_decorator([login_required], name='dispatch')
class UploadImportNtermentableView(View):  # PR2022-02-26
    # function import n-termen table
    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= UploadImportNtermentableView ============= ')

        update_wrap = {}
        msg_list = []
        if request.user and request.user.country and request.user.schoolbase:

            if request.POST['upload']:
                upload_dict = json.loads(request.POST['upload'])

# - Reset language
                # PR2019-03-15 Debug: language gets lost, get request.user.lang again
                # PR2021-12-09 Debug: must come before get_selected_ey_school_dep_lvl_from_usersetting
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get permit
                page = 'page_exams'
                permit_list, requsr_usergroups_listNIU,  requsr_allowed_sections_dictNIU, requsr_allowed_clusters_arr = acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, page)
                has_permit = 'permit_crud' in permit_list

                if logging_on:
                    logger.debug('permit_list: ' + str(permit_list))
                    logger.debug('requsr_usergroups_listNIU: ' + str(requsr_usergroups_listNIU))
                    logger.debug('has_permit: ' + str(has_permit))

# - get selected examyear, school and department from usersettings
                # PR2022-07-01 TODO
                sel_examyear, err_list = acc_view.get_selected_examyear_from_usersetting(request)
                if err_list:
                    msg_list.extend(err_list)

                if not has_permit:
                    err_html = _("You don't have permission to perform this action.")
                    update_wrap['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))
                elif err_list:
                    err_html = '<br>'.join(msg_list)
                    update_wrap['result'] = ''.join(("<p class='border_bg_invalid p-2'>", str(err_html), "</p>"))
                else:

# - get info from upload_dict
                    filename = upload_dict.get('filename', '')
                    upload_data_list = upload_dict.get('data_list')

                    log_list = get_dnt_from_upload(sel_examyear, upload_data_list, filename, request)
                    update_wrap['dnt_log_list'] = log_list

        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of UploadImportNtermentableView


def get_dnt_from_upload(sel_examyear, upload_data_list, filename, request):
    # PR2022-06-02
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_dnt_from_upload ----- ' )

    log_list = ['Upload N-termentabel ' + filename, '']

    if sel_examyear and upload_data_list:
        fields = ('sty_id', 'opl_code', 'leerweg', 'ext_code', 'Tijdvak', 'nex_ID', 'Omschrijving', 'Schaallengte', 'N-term', 'AfnameVakID', 'Extra_vakcodes_tbv_Wolf', 'datum', 'begintijd', 'eindtijd')

        first_row = upload_data_list[0]

# create list of mapped_fields, index is same as index in upload_data_list, value is fieldname of table Ntermentable
        """
        mapped_fields: ['sty_id', 'opl_code', 'leerweg', 'ext_code', None, None, None, None, 'tijdvak', 'nex_id', 'omschrijving', 'schaallengte', 'n_term', 'afnamevakid', 'extra_vakcodes_tbv_wolf', 'datum', 'begintijd', 'eindtijd', None, None]

        """
        mapped_fields = []
        pkfield_index = None  # index of nex_ID
        name_index = None  # index of Omschrijving

        for col_index, caption in enumerate(first_row):
            db_field = None
            if caption and caption in fields:
    # replace '-' by '_
                if '-' in caption:
                    caption = caption.replace('-', '_')
    # convert upper to lower case
                db_field = caption.lower()
    # get col_index of nex_id and omschrijving
                if db_field == 'nex_id':
                    pkfield_index = col_index
                elif db_field == 'omschrijving':
                    name_index = col_index
            mapped_fields.append(db_field)

        if logging_on:
            logger.debug('     pkfield_index: ' + str(pkfield_index))
            logger.debug('     name_index: ' + str(name_index))
            logger.debug('     mapped_fields: ' + str(mapped_fields))

        # loop through rows of upload_data_list
        if pkfield_index:
            for row_index, row in enumerate(upload_data_list):
    # slip first row, contains field names
                if row_index:
                    is_added = False
                    has_changed = False

                    changed_list = []
    # get nex_id:
                    nex_id_str = row[pkfield_index]
                    exam_name = row[name_index]
                    if logging_on:
                        logger.debug('     nex_id_str: ' + str(nex_id_str) + ' ' + str(type(nex_id_str)))
                    try:
                        nex_id_int = int(nex_id_str)
                    except:
                        nex_id_int = None

                    if logging_on:
                        logger.debug('     row_index: ' + str(row_index) + ' ' + str(nex_id_str) + ' ' + str(type(nex_id_str)) + ' ' + str(nex_id_int) + ' ' + str(type(nex_id_int)) + ' ' + str(exam_name))

                    if nex_id_int:
    # get existing row
                        nt_instance = subj_mod.Ntermentable.objects.filter(
                            examyear=sel_examyear,
                            nex_id=nex_id_int
                        ).order_by('-pk').first()
    # add row if not found
                        if nt_instance is None:
                            nt_instance = subj_mod.Ntermentable(
                                examyear=sel_examyear,
                                nex_id=nex_id_int
                            )
                            is_added = True
                            header_txt = ' '.join((str(nex_id_int), str(exam_name)))
                        else:
                            header_txt = ' '.join((str(nt_instance.nex_id), str(nt_instance.omschrijving)))

                        if nt_instance:
                            if logging_on:
                                logger.debug('     --- nt_instance: ' + str(nt_instance.omschrijving))
            # loop through columns of row, only the ones that are mapped
                            for col_index, field in enumerate(mapped_fields):
                                if field and col_index != pkfield_index:
                                    value = row[col_index]
                                    saved_value = getattr(nt_instance, field)
                                    if logging_on:
                                        logger.debug('          field: ' + str(field) + ' value: ' + str(value) + 'saved_value: ' + str(saved_value))

                                    new_value = None
            # convert date format 20-5-2022 to 2022-05-20
                                    if value:
                                        if field == 'datum':
                                            new_value = af.get_date_from_arr_str_ddmmyy(value)

            # replace n-term comma by dot
                                        elif field == 'n-term':
                                            new_value = value.replace(',', '.')

                                        elif field in ('sty_id', 'tijdvak', 'schaallengte', 'afnamevakid'):
                                            new_value = int(value)
                                        else:
                                            new_value = value

                                    if new_value != saved_value:
                                        setattr(nt_instance, field, new_value)
                                        has_changed = True
                                        changed_list.append(' '.join(('  ', str(field), str(saved_value), '>', str(new_value))))

                                        if logging_on:
                                            logger.debug('     --- new_value: ' + str(new_value))
                        nt_instance.save(request=request)

                        prefix = '+ ' if is_added else '* ' if has_changed else "  "
                        log_list.append(prefix + header_txt)

                        log_list.extend(changed_list)
    if logging_on:
        for row in log_list:
            logger.debug(row)

    return log_list
# - end of get_dnt_from_upload


def get_other_student_pok_dict(sel_examyear, sel_department, other_student_pk_list):
    # PR2024-08-09
    # function creates dict with students:
    # - that have pk in other_student_pk_list
    # - same dep as current students
    # - (level will be filtered out per student)
    # - NOT deleted AND NOT tobedeleted
    # - that have pok value
    # - check on examyear will be done per student, depending on is_evelex
    # here filter on examyear < cur_examyear and examyear >= cur_examyear + 10

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_other_student_pok_dict ----- ' )
        logger.debug('    other_student_pk_list: ' + str(other_student_pk_list) )

    other_student_pok_dict = {}
    if sel_examyear and sel_department and other_student_pk_list:

        # get list of studsubj with pok

        sub_sql = ''.join((
            "SELECT studsubj.student_id, ",

            "ARRAY_AGG(studsubj.schemeitem_id ORDER BY studsubj.id) AS schemeitem_id_arr, ",
            "ARRAY_AGG(subj.base_id ORDER BY studsubj.id) AS subjbase_id_arr, ",
            "ARRAY_AGG(subjbase.code ORDER BY studsubj.id) AS subjbase_code_arr, ",

            "ARRAY_AGG(studsubj.pok_sesr ORDER BY studsubj.id) AS pok_sesr_arr, ",
            "ARRAY_AGG(studsubj.pok_pece ORDER BY studsubj.id) AS pok_pece_arr, ",
            "ARRAY_AGG(studsubj.pok_final ORDER BY studsubj.id) AS pok_final_arr ",

            "FROM students_studentsubject AS studsubj ",
            "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id) ",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id) ",
            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id) ",

            "WHERE NOT studsubj.deleted AND NOT studsubj.tobedeleted ",
            "AND studsubj.pok_final IS NOT NULL ",
            "GROUP BY studsubj.student_id "
        ))
        sql_list = [
            "WITH studsubj_arr AS (", sub_sql, ") ",
            "SELECT stud.id AS stud_id, stud.lastname, stud.firstname, ",
            "stud.result, ey.code AS ey_code, lvl.base_id AS lvlbase_id, ",
            "(stud.iseveningstudent OR stud.islexstudent) AS is_evelex_student, ",
            
            "studsubj_arr.schemeitem_id_arr, ",
            "studsubj_arr.subjbase_id_arr, ",
            "studsubj_arr.subjbase_code_arr, ",

            "studsubj_arr.pok_sesr_arr, ",
            "studsubj_arr.pok_pece_arr, ",
            "studsubj_arr.pok_final_arr ",

            "FROM students_student AS stud ",
            "INNER JOIN schools_school AS school ON (school.id = stud.school_id) ",
            "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id) ",
            "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id) ",

            "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id) ",

            "INNER JOIN studsubj_arr ON (studsubj_arr.student_id = stud.id) ",

            "WHERE NOT stud.deleted AND NOT stud.tobedeleted ",
            "AND dep.base_id = ", str(sel_department.base_id), "::INT ",
            "AND ey.code >= ", str(sel_examyear.code - 10), "::INT ",
            "AND ey.code < ", str(sel_examyear.code), "::INT ",

             "AND stud.id IN (SELECT UNNEST(ARRAY", str(other_student_pk_list), "::INT[]));",
            ]

        #if logging_on:
        #    for txt in sql_list:
        #        logger.debug('   > ' + str(txt))

        sql = ''.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql)

            for row in af.dictfetchall(cursor):

                stud_id = row['stud_id']
                if stud_id not in other_student_pok_dict:
                    other_student_pok_dict[stud_id] = {
                        'stud_id': stud_id,
                        'lastname': row['lastname'],
                        'firstname': row['firstname'],
                        'result': row['result'],
                        'ey_code': row['ey_code'],
                        'lvlbase_id': row['lvlbase_id'],
                        'is_evelex_student': row['is_evelex_student'],
                        'studsubj': {}
                    }
                stud_dict = other_student_pok_dict[stud_id]
                studsubj_dict = stud_dict['studsubj']
                for i, schemeitem_id in enumerate(row['schemeitem_id_arr']):
                    subjbase_id = row['subjbase_id_arr'][i]

                    if subjbase_id not in studsubj_dict:
                        studsubj_dict[subjbase_id] = {
                            'subjbase_id': subjbase_id,
                            'schemeitem_id': schemeitem_id,
                            'subjbase_code': row['subjbase_code_arr'][i],
                            'pok_sesr': row['pok_sesr_arr'][i],
                            'pok_pece': row['pok_pece_arr'][i],
                            'pok_final': row['pok_final_arr'][i]
                        }
                if logging_on:
                    logger.debug('    stud_dict: ' + str(stud_dict))

    return other_student_pok_dict
# end of get_other_student_pok_dict


def create_exemption_dict(student, studsubj, linked_student_pk_list, other_student_pok_dict, request):
    # PR2024-08-09
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_exemption_dict ----- ' )
        logger.debug('    student.bis_exam: ' + str(student.bis_exam))
        logger.debug('    student.linked: ' + str(student.linked))

    """
    other_student_pok_dict: {
        {5943: {
            'stud_id': 5943, 'lastname': 'Gomez', 'firstname': 'Ngioly', 'result': 2, 'ey_code': 2022, 
            'lvlbase_id': 4, 'is_evelex_student': False, 
            'studsubj': {
                115: {'subjbase_id': 115, 'schemeitem_id': 1688, 'subjbase_code': 'mm1', 'pok_sesr': '5.7', 'pok_pece': None, 'pok_final': '6'}, 
                116: {'subjbase_id': 116, 'schemeitem_id': 1689, 'subjbase_code': 'lo', 'pok_sesr': '7.5', 'pok_pece': None, 'pok_final': '8'}, 
                117: {'subjbase_id': 117, 'schemeitem_id': 1690, 'subjbase_code': 'cav', 'pok_sesr': '7.0', 'pok_pece': None, 'pok_final': '7'}, 
                135: {'subjbase_id': 135, 'schemeitem_id': 1699, 'subjbase_code': 'sws', 'pok_sesr': 'v', 'pok_pece': None, 'pok_final': 'v'}}}, 
    """

    # - linked_student_pk_list contains students with:
                    # - field 'linked' has value and
                    # - bis_exam = True
                    # - or when evening or lex-student: bis_exam not necessary, but partial exam must be false
    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
    # linked_student_pk_list not in use yet, will be used in batch-create

    if student.linked and \
            (student.bis_exam or
            ((student.iseveningstudent or student.islexstudent) and not student.partial_exam)):

    # - add exemption when dep and level are the same - dep is filtered out already, check level here
    # check examyear - when dayschool: pok examyear must be prevoios year
    # whene evelex: pok may be 10 years old
        cur_school = student.school
        cur_examyear = cur_school.examyear
        cur_department = student.department
        linked_arr = student.linked.split(';')

        if logging_on:
            logger.debug('    cur_examyear: ' + str(cur_examyear))
            logger.debug('    linked_arr: ' + str(linked_arr))

        for other_student_pk_str in linked_arr:
            other_student_pk_int = int(other_student_pk_str)
            if other_student_pk_int in other_student_pok_dict:
                other_student_dict = other_student_pok_dict[other_student_pk_int]

                if logging_on:
                    logger.debug('  other_student_dict: ' + str(other_student_dict))
                """
                other_student_dict: {'stud_id': 7468, 'lastname': 'Oleana', 'firstname': 'Gion Gregorio Egbert', 'result': 2, 'ey_code': 2023, 'lvlbase_id': 6, 'is_evelex_student': False, 'studsubj': {116: {'subjbase_id': 116, 'schemeitem_id': 2598, 'subjbase_code': 'lo', 'pok_sesr': '8.8', 'pok_pece': None, 'pok_final': '9'}, 117: {'subjbase_id': 117, 'schemeitem_id': 2603, 'subjbase_code': 'cav', 'pok_sesr': '6.9', 'pok_pece': None, 'pok_final': '7'}, 115: {'subjbase_id': 115, 'schemeitem_id': 2597, 'subjbase_code': 'mm1', 'pok_sesr': '8.1', 'pok_pece': None, 'pok_final': '8'}, 136: {'subjbase_id': 136, 'schemeitem_id': 2599, 'subjbase_code': 'stg', 'pok_sesr': 'v', 'pok_pece': None, 'pok_final': 'v'}}}
                other_studsubj_dict: {116: {'subjbase_id': 116, 'schemeitem_id': 2598, 'subjbase_code': 'lo', 'pok_sesr': '8.8', 'pok_pece': None, 'pok_final': '9'}, 117: {'subjbase_id': 117, 'schemeitem_id': 2603, 'subjbase_code': 'cav', 'pok_sesr': '6.9', 'pok_pece': None, 'pok_final': '7'}, 115: {'subjbase_id': 115, 'schemeitem_id': 2597, 'subjbase_code': 'mm1', 'pok_sesr': '8.1', 'pok_pece': None, 'pok_final': '8'}, 136: {'subjbase_id': 136, 'schemeitem_id': 2599, 'subjbase_code': 'stg', 'pok_sesr': 'v', 'pok_pece': None, 'pok_final': 'v'}}
                value_dict: {'subjbase_id': 116, 'schemeitem_id': 2598, 'subjbase_code': 'lo', 'pok_sesr': '8.8', 'pok_pece': None, 'pok_final': '9'}
                """

                other_result =  other_student_dict['result']
                other_examyear =  other_student_dict['ey_code']
                other_lvlbase_id =  other_student_dict['lvlbase_id']
                other_is_evelex_student =  other_student_dict['is_evelex_student']

                other_studsubj_dict = other_student_dict['studsubj']
                if logging_on:
                    logger.debug('    other_studsubj_dict: ' + str(other_studsubj_dict))


                for subjbase_id, value_dict in other_studsubj_dict.items():
                    schemeitem_id = value_dict['schemeitem_id']
                    subjbase_id = value_dict['subjbase_id']
                    subjbase_code = value_dict['subjbase_code']
                    pok_sesr =  value_dict['pok_sesr']
                    pok_pece = value_dict['pok_pece']
                    pok_final = value_dict['pok_final']
                    if logging_on:
                        logger.debug('    value_dict: ' + str(value_dict))
                    """
                    value_dict: {
                        'subjbase_id': 116, 
                        'schemeitem_id': 2598, 
                        'subjbase_code': 'lo', 
                        'pok_sesr': '8.8', 
                        'pok_pece': None, 
                        'pok_final': '9'}
                    """
                    #create_exemptions(cur_school, cur_department, cur_examyear, user_lang, request)
# end of create_exemption_dict

def create_exemption_sql_list(cur_student_dict, cur_subjbase_pk, cur_subjbase_instance, other_student_pok_dict, is_test,
                              tobe_inserted_or_updated_exemption_grade_dict, tobe_updated_studsubj_dict,
                              request):
    # P2024-08-20
    # function:
    #  - first loop through linked other students
    #  - then loop trough exemptions of other student
    #  - then lookup if cur_student as this subject
    #  - finally add values to tobe_inserted / tobe_updated dict
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug(' ============= create_exemption_sql_list ============= ')
        logger.debug('    cur_student_dict fullname: ' + str(cur_student_dict.get('fullname')))
        # logger.debug('    other_student_pok_dict: ' + str(other_student_pok_dict))
        logger.debug('    cur_subjbase_pk: ' + str(cur_subjbase_pk))

    """
    cur_student_dict: {
        'idnumber': '2005022410', 'stud_id': 11093, 'bis_exam': True, 
        'fullname': ' Castillo Cabrera, Merelyn Fabiana', 
        'is_evelex_student': True, 'partial_exam': False, 'scheme_id': 181, 'ey_code': 2025, 
        'sb_code': 'CUR14', 'school_name': 'Curaçaos Avondlyceum', 
        'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvlbase_id': 4, 'lvl_abbrev': 'TKL', 'sctbase_id': 13, 'sct_abbrev': 'ec', 
        'linked_arr': [10744, 7083], 
        'has_pws_subjbase_pk': 135, 
        'studsubj': {
            113: {'studsubj_id': 95419, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 
                'subjbase_id': 113, 'subjbase_code': 'ne', 'sjtp_has_pws': False, 'sjtpbase_id': 31, 
                'exemp_grade_id': None, 'exemp_grade_deleted': None}, 
            135: {'studsubj_id': 95425, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 
                'subjbase_id': 135, 'subjbase_code': 'sws', 'sjtp_has_pws': True, 'sjtpbase_id': 35, 
                'exemp_grade_id': None, 'exemp_grade_deleted': None},       
    """
    """
    from modal craeate
    student_dict: {
        'idnumber': '2005022410', 'stud_id': 11093, 'bis_exam': False, 'linked': '10744;7083', 
        'fullname': ' Castillo Cabrera, Merelyn Fabiana', 'is_evelex_student': True, 'partial_exam': False, 
        'scheme_id': 181, 'ey_code': 2025, 'sb_code': 'CUR14', 'school_name': 'Curaçaos Avondlyceum', 
        'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvlbase_id': 4, 'lvl_abbrev': 'TKL', 'sctbase_id': 13, 'sct_abbrev': 'ec', 
        'linked_list': [10744, 7083], 
        'studsubj': {}}

    """
    log_list = []

# - create log_list
    cur_school_name = cur_student_dict['school_name']
    #cur_examyear = cur_school.examyear

    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT

    today_dte = af.get_today_dateobj()
    today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

    #school_name = cur_school.base.code + ' ' + cur_school.name
    log_list.append(c.STRING_DOUBLELINE_80)
    log_list.append(
        str(_('Enter exemptions')) + ' ' + str(_('date')) + ': ' + str(today_formatted))
    log_list.append(c.STRING_DOUBLELINE_80)

    log_list.append(c.STRING_SPACE_05 + str(_("School    : %(name)s") % {'name': cur_school_name}))
    #log_list.append(
    #    c.STRING_SPACE_05 + str(_("Department: %(dep)s") % {'dep': cur_department.name}))
    #log_list.append(
    #    c.STRING_SPACE_05 + str(_("Exam year : %(ey)s") % {'ey': str(cur_examyear.code)}))

    #log_list.append(c.STRING_SPACE_05)
    # PR2024-08-13 when is_test, there is no cur_studsubj
    if other_student_pok_dict:
        append_dict = {}

        """
        other_student_pok_dict: {
            3950: {'stud_id': 3950, 'lastname': 'Noel', 'firstname': 'Malaiska', 
                    'result': 2, 'ey_code': 2022, 'lvlbase_id': 4, 'is_evelex_student': False, 
                    'studsubj': {
                        115: {'subjbase_id': 115, 'schemeitem_id': 1688, 'subjbase_code': 'mm1', 
                            'pok_sesr': '6.4', 'pok_pece': None, 'pok_final': '6'}, 
        """
        cur_fullname = cur_student_dict['fullname']
        cur_examyear_code = cur_student_dict['ey_code']
        cur_depbase_code = cur_student_dict['depbase_code']
        cur_lvlbase_id = cur_student_dict['lvlbase_id']
        cur_lvl_abbrev = cur_student_dict['lvl_abbrev'] if cur_student_dict['lvl_abbrev'] else ''
        cur_sct_abbrev = cur_student_dict['sct_abbrev'] if cur_student_dict['sct_abbrev'] else ''

        cur_linked = cur_student_dict['linked'] or []
        linked_arr = list(map(int, cur_linked.split(';')))

        cur_stud_is_evelex = cur_student_dict['is_evelex_student']

        curstud_logtxt_added = False

        if logging_on:
            #logger.debug(' cur_examyear_code:   ' + str(cur_examyear_code))
            #logger.debug(' cur_depbase_code:   ' + str(cur_depbase_code))
            #logger.debug(' cur_lvl_abbrev:   ' + str(cur_lvl_abbrev))
            #logger.debug(' cur_sct_abbrev:   ' + str(cur_sct_abbrev))
           # logger.debug(' cur_studentsubjects_dict:   ' + str(cur_studentsubjects_dict))
            logger.debug(' linked_arr:   ' + str(linked_arr))
            logger.debug(' ..........')

        if linked_arr:
            # PR2024-08-20 cur_student_dict has no stidsubj yet, because it is vreated before importing studsubj
            #cur_studentsubjects_dict = cur_student_dict['studsubj']
            """
            cur_studentsubjects_dict:   
                {116: {
                    'scheme_id': 171, 'studsubj_id': 95419, 'studsubj_deleted': True, 'studsubj_tobedeleted': False, 
                    'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 
                    'subjbase_id': 116, 'subjbase_code': 'lo', 'sjtp_has_pws': False, 
                    'sjtpbase_id': 31, 'schemeitem_id': 4271, 'exemp_grade_id': None, 'exemp_grade_deleted': None},
                     117: {'scheme_id': 171, 'studsubj_id': 95420, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 'subjbase_id': 117, 'subjbase_code': 'cav', 'sjtp_has_pws': False, 'sjtpbase_id': 31, 'schemeitem_id': 4270, 'exemp_grade_id': None, 'exemp_grade_deleted': None}, 118: {'scheme_id': 171, 'studsubj_id': 95421, 'studsubj_deleted': True, 'studsubj_tobedeleted': False, 'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 'subjbase_id': 118, 'subjbase_code': 'pa', 'sjtp_has_pws': False, 'sjtpbase_id': 31, 'schemeitem_id': 4265, 'exemp_grade_id': None, 'exemp_grade_deleted': None}, 140: {'scheme_id': 171, 'studsubj_id': 95422, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 'subjbase_id': 140, 'subjbase_code': 'ak', 'sjtp_has_pws': False, 'sjtpbase_id': 32, 'schemeitem_id': 4293, 'exemp_grade_id': None, 'exemp_grade_deleted': None}, 142: {'scheme_id': 171, 'studsubj_id': 95423, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 'subjbase_id': 142, 'subjbase_code': 'asw', 'sjtp_has_pws': False, 'sjtpbase_id': 31, 'schemeitem_id': 4269, 'exemp_grade_id': None, 'exemp_grade_deleted': None}, 145: {'scheme_id': 171, 'studsubj_id': 95424, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 'subjbase_id': 145, 'subjbase_code': 'gs', 'sjtp_has_pws': False, 'sjtpbase_id': 32, 'schemeitem_id': 4266, 'exemp_grade_id': None, 'exemp_grade_deleted': None}, 148: {'scheme_id': 171, 'studsubj_id': 95425, 'studsubj_deleted': False, 'studsubj_tobedeleted': False, 'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 'subjbase_id': 148, 'subjbase_code': 'pws', 'sjtp_has_pws': True, 'sjtpbase_id': 35, 'schemeitem_id': 4272, 'exemp_grade_id': None, 'exemp_grade_deleted': None}, 157: {'scheme_id': 171, 'studsubj_id': 95426, 'studsubj_deleted': True, 'studsubj_tobedeleted': False, 'subj_published_id': None, 'prev_auth1by_id': None, 'prev_auth2by_id': None, 'prev_published_id': None, 'subjbase_id': 157, 'subjbase_code': 'go', 'sjtp_has_pws': False, 'sjtpbase_id': 33, 'schemeitem_id': 4279, 'exemp_grade_id': None, 'exemp_grade_deleted': None}}
            """
            # get info of this studentsubject from cur_studsubj_dict, key is subjbase_pk, not studsubj_pk
            # use cur_subjbase_instance insetad
            #cur_studsubj_dict = cur_studentsubjects_dict.get(cur_subjbase_pk)
            #if logging_on:
            #    logger.debug('    cur_studsubj_dict: ' + str(cur_studsubj_dict))

            if cur_subjbase_instance:
                if logging_on:
                    logger.debug('# ++++++ loop through other_students')
                """
                other_student_pok_dict contains students that:
                # - are in other_student_pk_list (means that pk is in 'linked' field of one of students in the linked_student_pk_list
                # - are NOT stud.deleted AND NOT stud.tobedeleted ",
                # - have same dep.base_id as current student
                # - have ey.code >= cur_examyear.code - 10 AND ey.code < cur_examyear.code
                
                must filter out exam year and level in this function
                """
         # - sort linked_aarr by examyear desc to get most recent exemption
               # linked_arr_sorted = sorted(pok_list, key=lambda k: (k['lvl_name'], k['lastname'].lower(), k['firstname'].lower()))
                # first convert linked_arr to dictlist [ {'ey_code': 2023, 'stud_id': 1444)}
                # then sort by examyear descending
                linked_dictlist = []
                for other_student_pk in linked_arr:
                    other_stud_dict = other_student_pok_dict.get(other_student_pk)
                    if other_stud_dict:
                        linked_dictlist.append({
                            'ey_code': other_stud_dict['ey_code'],
                            'stud_id': other_stud_dict['stud_id']
                        })
                linked_dictlist_sorted = sorted(linked_dictlist, key=lambda k: (-k['ey_code']))

                if logging_on:
                    logger.debug('  >>>  linked_dictlist_sorted:   ' + str(linked_dictlist_sorted))
                    # >>>  linked_arr_sorted:   [{'ey_code': 2024, 'stud_id': 10744}]

    # ++++++ loop through other_students, sorted ey_code descending
                for linked_dict in linked_dictlist_sorted:
                    other_student_pk = linked_dict['stud_id']
                    if logging_on:
                        logger.debug('  >>>  other_student_pk:   ' + str(other_student_pk))
                    other_stud_dict = other_student_pok_dict.get(other_student_pk)

                    if logging_on:
                        logger.debug('    other_stud_dict:   ' + str(other_stud_dict))
                    """
                    other_stud_dict: {'stud_id': 3950, 'lastname': 'Noel', 'firstname': 'Malaiska', 
                            'result': 2, 'ey_code': 2022, 'lvlbase_id': 4, 'is_evelex_student': False, 
                            'studsubj': {
                                115: {'subjbase_id': 115, 'schemeitem_id': 1688, 'subjbase_code': 'mm1', 
                                    'pok_sesr': '6.4', 'pok_pece': None, 'pok_final': '6'}, 
                    """

                    if other_stud_dict:
                        other_examyear_code = other_stud_dict['ey_code']
                        other_lvlbase_id = other_stud_dict['lvlbase_id']
                        other_is_evelex = other_stud_dict['is_evelex_student']

                        other_failed = (other_stud_dict['result'] == c.RESULT_FAILED)


                        if logging_on:
                            logger.debug(
                                '    other_examyear_code:   ' + str(other_examyear_code))
                            #logger.debug('    other_depbase:   ' + str(other_depbase))
                            #logger.debug('    other_lvlbase_id:   ' + str(other_lvlbase_id))
                            logger.debug('    other_failed:   ' + str(other_failed))

            # is exam year correct?
                        # PR2024-08-10 note: it is still not clear when a pok is valid for ten years
                        # there are 4 possibilities:
                        # - cur_stud and other_stud are both day_student > pok valid for 1 year, for sure
                        # - cur_stud and other_stud are both evelex_student > pok valid for 10 years, for sure
                        # - cur_stud is day_student and other_stud is evelex_student > not clear, make it 1 year to be on the safe side
                        # - cur_stud is evelex_student and other_stud is day_student > not clear, make it 1 year to be on the safe side

                        # PR2024-09-24 pok may always be 10 years old when is_evelex_student
                        #   email Hans meijs 17 sep 24:
                        #   Een avondschool-kandidaat krijgt vrijstelling voor een vak wanneer:
                        #    - de kandiaat voor dat vak een Bewijs van Vrijstelling van een avondschool heeft dat niet ouder is dan 10 jaar
                        #    - of de kandidaat een Bewijs van Kennis van een dagschool heeft, niet ouder dan 10 jaar
                        #   email Nancy Josephina 17 sep 2024:
                        #       Jouw interpretatie klopt en de wijziging is op zijn plaats. Bedankt voor de informatie.
                        #       Drs. Nancy Josephina
                        # was: valid_years = 10 if cur_stud_is_evelex and other_is_evelex else 1

                        valid_years = 10 if cur_stud_is_evelex else 1
                        examyear_is_correct = (other_examyear_code < cur_examyear_code and
                                               other_examyear_code >= cur_examyear_code - valid_years)
                        if logging_on:
                            logger.debug('    examyear_is_correct:   ' + str(examyear_is_correct))

                        if examyear_is_correct:
            # - is dep and level correct?
                            # dep of other_student is always the same as dep of cur_student, is filtered out in other_student_pok_dict
                            if other_lvlbase_id == cur_lvlbase_id:
                                if logging_on:
                                    logger.debug('    BINGO: other_student  examyear_is_correct, same lvlbase ')

            # set student bis_exam = True if False
                                # not necessary, bis_exam = True is filtered out in linked_student_pk_list

                                # - create log header for this student
                                if not curstud_logtxt_added:
                                    log_list.append(' ')

                                    log_list.append(''.join((
                                        cur_fullname,
                                        ' - ' + cur_depbase_code,
                                        ' - ' + cur_lvl_abbrev if cur_lvl_abbrev else '',
                                        ' - ' + cur_sct_abbrev if cur_sct_abbrev else ''
                                    )))
                                    log_list.append(c.STRING_SPACE_05 + str(
                                        _("This candidate is marked as 'bis-candidate'.")))

                                    curstud_logtxt_added = True

                                log_list.append(''.join((c.STRING_SPACE_05,
                                                         (str(other_examyear_code) + c.STRING_SPACE_05)[:5],
                                                        # other_school,
                                                        # ' - ' + other_depbase_code,
                                                       #  ' - ' + other_lvlbase_code if other_lvlbase else '',
                                                       #  ' - ' + other_sctbase_code if other_sctbase else ''
                                                       #  ' - ' + other_result_status if other_result_status else '',
                                                         )))

                # - get subjects with pok of other student
                                # PR2024-04-23 debug: pok_validthru has no value

                                """
                                other_stud_dict: {'stud_id': 3950, 'lastname': 'Noel', 'firstname': 'Malaiska', 
                                        'result': 2, 'ey_code': 2022, 'lvlbase_id': 4, 'is_evelex_student': False, 
                                        'studsubj': {
                                            115: {'subjbase_id': 115, 'schemeitem_id': 1688, 'subjbase_code': 'mm1', 
                                                'pok_sesr': '6.4', 'pok_pece': None, 'pok_final': '6'}, 
                                """
                                other_studentsubjects_dict = other_stud_dict['studsubj']
                                if logging_on:
                                    logger.debug('other_studentsubjects_dict: ' + str(other_studentsubjects_dict))
                                    logger.debug('cur_subjbase_pk: ' + str(cur_subjbase_pk))

                                other_studsubj_dict = other_studentsubjects_dict.get(cur_subjbase_pk) if other_studentsubjects_dict else None
                                if logging_on:
                                    logger.debug('other_studsubj_dict: ' + str(other_studsubj_dict))

                                # other_subj_dict has value when other_student has exemption of this subject
                                if other_studsubj_dict:
                                    subj_code = other_studsubj_dict['subjbase_code']
                                    other_pok_sesr = other_studsubj_dict['pok_sesr']
                                    other_pok_pece = other_studsubj_dict['pok_pece']
                                    other_pok_final = other_studsubj_dict['pok_final']

                                    other_pok_sesr_str = other_pok_sesr.replace('.',',') if other_pok_sesr else '-'
                                    other_pok_pece_str = other_pok_pece.replace('.',',') if other_pok_pece else '-'
                                    other_pok_final_str = other_pok_final.replace('.',',') if other_pok_final else '-'

                                    grade_logtxt = ''.join((c.STRING_SPACE_10,
                                                            (subj_code + c.STRING_SPACE_10)[:8],
                                                            's: ', (other_pok_sesr_str + c.STRING_SPACE_05)[:5],
                                                            'c: ', (other_pok_pece_str + c.STRING_SPACE_05)[:5],
                                                            'e: ', (other_pok_final_str + c.STRING_SPACE_05)[:5]
                                                            ))
                                    if logging_on:
                                        logger.debug('    grade_logtxt: ' + str(grade_logtxt))

                        # check if cur_studsubj has already an exemption grade
                                    # PR2024-08-13 debug: because of None value of cur_studsubj <Studentsubject: Studentsubject object (None)>
                                    # the following error came: save() prohibited to prevent data loss due to unsaved related object 'studentsubject'.
                                    # adding if cur_studsubj is not None does not help,
                                    # because (cur_studsubj is None = False) and (cur_studsubj = False), although it says: Studentsubject object (None)
                                    # therefore must use: if cur_studsubj.pk

                                    # PR2024-08-14 get info from student_dict

                                    # PR2024-08-14 exemp_deleted can have value None, False or True
                                    # value None means there is no exemption grade of this subject
                                    # value False means this subject has an exemption grade
                                    # value True means this subject has a deleted exemption grade
                                    cur_studsubj_id = cur_subjbase_instance.pk

                                    #cur_exemp_grade_id = cur_studsubj_dict.get('exemp_grade_id')
                                    #cur_exemp_grade_deleted = cur_studsubj_dict.get('exemp_grade_deleted')

                                    cur_exemp_grade_id = None
                                    cur_exemp_grade_deleted = False
                                    exemption_grade = stud_mod.Grade.objects.filter(
                                        pk=cur_subjbase_instance.pk,
                                        examperiod=c.EXAMPERIOD_EXEMPTION
                                    ).order_by('-pk').first()
                                    if exemption_grade:
                                        cur_exemp_grade_id = exemption_grade.pk
                                        cur_exemp_grade_deleted = exemption_grade.deleted

                                    if logging_on:
                                        logger.debug(' ^^^^^^^^^^^^   cur_exemp_grade_deleted: ' + str(cur_exemp_grade_deleted))
                                        logger.debug('    cur_exemp_grade_id: ' + str(cur_exemp_grade_id))

                                    if not is_test:
                                        value_dict = {
                                            'grade_pk': cur_exemp_grade_id,
                                            'deleted': cur_exemp_grade_deleted,
                                            'studsubj_pk': cur_studsubj_id,
                                            'se_grade': other_pok_sesr,
                                            'ce_grade': other_pok_pece,
                                            'finalgrade': other_pok_final,
                                            'examyear': other_examyear_code,
                                            'exemption_imported': True
                                        }
                                        if logging_on:
                                            logger.debug('    value_dict: ' + str(value_dict))

                                        if cur_studsubj_id not in tobe_inserted_or_updated_exemption_grade_dict:
                                            tobe_inserted_or_updated_exemption_grade_dict[cur_studsubj_id] = value_dict

                                        if cur_studsubj_id not in tobe_updated_studsubj_dict:
                                            tobe_updated_studsubj_dict[cur_studsubj_id] = {
                                            'studsubj_id': cur_studsubj_id,
                                            'exemption_year': other_examyear_code,
                                            'has_exemption': True
                                            }

                            # - exit loop when exemption is found in other_stud_dict
                                        break
# ++++++ end of loop through other_students

    if logging_on and False:
        logger.debug('    tobe_inserted_exemption_grade_dict: ' + str(tobe_inserted_or_updated_exemption_grade_dict))
        logger.debug('    tobe_updated_studsubj_dict: ' + str(tobe_updated_studsubj_dict))
# - end of ceate_exeption


def batch_insert_or_update_exemption_grade(tobe_inserted_dict, request):
    #PR2024-08-15
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('--------&&&&&&&&&&&--------- batch_insert_or_update_exemption_grade  --------------------')
        logger.debug('tobe_inserted_dict: ' + str(tobe_inserted_dict))

    def get_item(row):
        grade_pk = row.get('grade_pk')
        studsubj_pk = row.get('studsubj_pk')
        se_grade = ''.join(("'", row.get('se_grade'), "'")) if row.get('se_grade') else "NULL"
        ce_grade = ''.join(("'", row.get('ce_grade'), "'")) if row.get('ce_grade') else "NULL"
        finalgrade = ''.join(("'", row.get('finalgrade'), "'")) if row.get('finalgrade') else "NULL"
        exemption_imported = "TRUE" if row.get('exemption_imported') else "FALSE"

        is_insert = grade_pk is None
        item = None

        if studsubj_pk or True:
            if is_insert:
                values = ', '.join((
                    str(studsubj_pk),
                    str(c.EXAMPERIOD_EXEMPTION),
                    modifiedby_pk_str, modifiedat_delim,
                    se_grade, se_grade, ce_grade, ce_grade, finalgrade,
                    exemption_imported,
                    "0, FALSE, 0, FALSE, 0, FALSE, 0, FALSE, FALSE, FALSE, FALSE, FALSE, 0",
                    ))
                item = ''.join(("(", values, ")"))
            else:
                values = ', '.join((
                    str(grade_pk),
                    se_grade, se_grade, ce_grade, ce_grade, finalgrade,
                    exemption_imported
                ))
                item = ''.join(("(", values, ")"))

        return item, is_insert
    # - end of get_item

    def get_insert_sql (value_str):
        return ''.join((
            "INSERT INTO students_grade (studentsubject_id, examperiod, modifiedby_id, modifiedat, ",
            "segrade, sesrgrade, cegrade, pecegrade, finalgrade, exemption_imported, ",
            "se_status, se_blocked, sr_status, sr_blocked, pe_status, pe_blocked, ce_status, ce_blocked, ",
            "pe_exam_blocked, ce_exam_blocked, deleted, tobedeleted, status",
            ") VALUES ",
            value_str,
            "RETURNING students_grade.id, students_grade.studentsubject_id;"
        ))

    def get_update_sql (value_str):
        return ''.join((
            "DROP TABLE IF EXISTS tmp; CREATE TEMP TABLE tmp (grade_id, segrade, sesrgrade, cegrade, pecegrade, finalgrade, exemption_imported) AS ",
            "VALUES (0::INT, '-'::TEXT, '-'::TEXT, '-'::TEXT, '-'::TEXT, '-'::TEXT, FALSE::BOOLEAN), ",
            value_str,
            "; UPDATE students_grade AS gr ",
            "SET segrade = tmp.segrade, sesrgrade = tmp.segrade, ",
            "cegrade = tmp.cegrade, pecegrade = tmp.cegrade, ",
            "finalgrade = tmp.finalgrade, ",
            "exemption_imported = tmp.exemption_imported, ",
            "modifiedby_id = ", modifiedby_pk_str, "::INT, modifiedat = ", modifiedat_delim, "::DATE ",
            "FROM tmp ",
            "WHERE tmp.grade_id = gr.id ",
            "RETURNING gr.id, gr.studentsubject_id;"
        ))

    def set_has_exemption_in_studsubj(tobe_inserted_dict):
        if logging_on:
            logger.debug(' ')
            logger.debug('    ..... set_has_exemption_in_studsubj  .....')
            logger.debug('tobe_inserted_dict: ' + str(tobe_inserted_dict))

        if tobe_inserted_dict:
            # tobe_updated_studsubj_dict: {95422: {'studsubj_id': 95422, 'exemption_year': 2024, 'has_exemption': True}, 95423: {'studsubj_id': 95423, 'exemption_year': 2024, 'has_exemption': True}, 95425: {'studsubj_id': 95425, 'exemption_year': 2024, 'has_exemption': True}, 95478: {'studsubj_id': 95478, 'exemption_year': 2024, 'has_exemption': True}, 95492: {'studsubj_id': 95492, 'exemption_year': 2024, 'has_exemption': True}, 95495: {'studsubj_id': 95495, 'exemption_year': 2024, 'has_exemption': True}, 95514: {'studsubj_id': 95514, 'exemption_year': 2024, 'has_exemption': True}}
            """
            tobe_inserted_or_updated_exemption_grade_dict[cur_studsubj_id] =  {
            'grade_pk': cur_exemp_grade_id,
            'studsubj_pk': cur_studsubj_id,
            'se_grade': other_pok_sesr,
            'ce_grade': other_pok_pece,
            'finalgrade': other_pok_final,
            'examyear': other_examyear_code,
            'exemption_imported': True
            }

            """
            sql_value_list = []
            for dct in tobe_inserted_dict.values():
                examyear = dct.get('examyear')
                examyear_str = str(examyear) if examyear else 'NULL'
                studsubj_pk = dct.get('studsubj_pk')
                if studsubj_pk:
            # - put values in TEMP TABLE
                    sql_value_list.append(''.join(("(", str(studsubj_pk), ", ", examyear_str, ")")))
            sql_value_str = ', '.join(sql_value_list)

            sql_update = ''.join((
                "DROP TABLE IF EXISTS tmp; CREATE TEMP TABLE tmp (",
                "studsubj_id, exemption_year) AS VALUES (0::INT, 0::INT), ",
                sql_value_str,
                "; UPDATE students_studentsubject AS studsubj ",
                "SET has_exemption = TRUE, exemption_year = tmp.exemption_year ",
                # "modifiedby_id = %(modby_id)s::INT, modifiedat = '", modifiedat_str, "'",
                "FROM tmp ",
                "WHERE tmp.studsubj_id = studsubj.id ",
                "RETURNING studsubj.id;"
            ))
            if logging_on:
                logger.debug('sql: ' + str(sql))

            updated_list = []
            with connection.cursor() as cursor:
                cursor.execute(sql_update)
                updated_rows = cursor.fetchall()
                if updated_rows:
                    for updated_row in updated_rows:
                        logger.debug('updated_row: ' + str(updated_row))
                        updated_list.append(updated_row[0])
            if updated_list:
                awpr_log.savetolog_studentsubject(
                    studsubj_pk_or_array=updated_list,
                    log_mode='i',
                    updated_fields=('has_exemption', 'exemption_year')
                )
# end of setexemptioninstudsubk

    modifiedby_pk_str = str(request.user.pk)
    modifiedat_delim =''.join(("'", str(timezone.now()), "'"))

    updated_grade_pk_list = []
    updated_studsubj_pk_list = []

    if tobe_inserted_dict and request.user:

        # sesrgrade is same as segrade, pecegrade is same as cegrade

        try:
            insert_list, update_list = [], []
            for row in tobe_inserted_dict.values():
                if logging_on:
                    logger.debug('  row: ' + str(row))
                """
                row: {'grade_pk': None, 'studsubj_pk': 95423, 
                        'se_grade': '7.6', 'ce_grade': '7.2', 'finalgrade': '7', 
                        'exemption_imported': True}    
                """
                value_item, is_insert = get_item((row))

                if logging_on:
                    logger.debug('value_item: ' + str(value_item))

                if value_item:
                    if is_insert:
                        insert_list.append(value_item)
                    else:
                        update_list.append(value_item)

                if logging_on:
                    logger.debug('    value_item: ' + str(value_item))

            for i, value_list in enumerate((insert_list, update_list)):
                if logging_on:
                    logger.debug('    ----------- index: ' + str(i))

                if value_list:
                    value_str = ', '.join(value_list)
                    sql_list = get_insert_sql(value_str) if i == 0 else get_update_sql(value_str)
                    sql = ''.join(sql_list)
                    if logging_on:
                        logger.debug('    sql: ' + str(sql))

                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                        rows = cursor.fetchall()
                        if logging_on:
                            logger.debug('    rows: ' + str(rows))

                        if rows:
                            for row in rows:
                                updated_grade_pk_list.append(row[0])
                                # add studsubj_pk to list, to udate has_exemption later

                                if row[1] not in updated_studsubj_pk_list:
                                    updated_studsubj_pk_list.append(row[1])

                        if updated_grade_pk_list:
                            awpr_log.copytolog_grade_v2(
                                grade_pk_list=updated_grade_pk_list,
                                log_mode='o', #  log_mode 'o' = _('Copied from previous exam year at ')
                                modifiedby_id=request.user.pk
                            )
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

 # also set has_exemption = True in student_subject

        if logging_on:
            logger.debug('    tobe_inserted_dict: ' + str(tobe_inserted_dict))

        set_has_exemption_in_studsubj(tobe_inserted_dict)

    if logging_on:
        logger.debug('updated_grade_pk_list: ' + str(updated_grade_pk_list))
        logger.debug('updated_studsubj_pk_list: ' + str(updated_studsubj_pk_list))

    return updated_grade_pk_list, updated_studsubj_pk_list
# - end of batch_insert_or_update_exemption_grade

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_studsubj_sql_v2(cur_student_dict, scheme_dict, new_subjbase_id, new_sjtpbase_id,
        new_pws_title, new_pws_subjects, error_list, request, skip_save, is_import):
    # --- create student subject # PR2024-08-16
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('   ')
        logger.debug(' ----- create_studsubj_sql_v2 ----- ')
        logger.debug('    student_dict: ' + str(cur_student_dict))
        logger.debug('    scheme_dict: ' + str(scheme_dict))
    """   
    student_dict: {'idnumber': '2005022410', 'stud_id': 11093, 'bis_exam': True, 'linked': '10744;7083', 
                'fullname': ' Castillo Cabrera, Merelyn Fabiana', 
                'is_evelex_student': True,  'partial_exam': False, 
                'scheme_id': 181, 'ey_code': 2025, 'sb_code': 'CUR14', 'school_name': 'Curaçaos Avondlyceum', 
                'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvlbase_id': 4, 'lvl_abbrev': 'TKL', 'sctbase_id': 13, 'sct_abbrev': 'ec',
                'linked': '10744;7083', 'has_pws_subjbase_pk': 135,
                'studsubj': {
                    135: {'scheme_id': 181,  'studsubj_id': 95419, 
                        'studsubj_deleted': False, 'studsubj_tobedeleted': False, 
                        'subj_published_id': None
                        'subjbase_id': 135, 'subjbase_code': 'sws', 
                         'sjtp_has_pws': True, 
                         'sjtpbase_id': 35, 'schemeitem_id': 4486, 
                         'exemp_grade_id': None, 'exemp_grade_deleted': None}}}

    new_schemeitem_subjbase_dict: {
        'subjbase_id': 113, 'subj_code': 'ne', 'default_sjtpbase_sequence': 1,  'default_sjtpbase_id': 33, 
        33: {'si_id': 4494, 'sjtp_id': 33, 'sjtp_name': 'Gemeenschappelijk deel', 'sjtp_abbrev': 'Gemeensch.', 
                'sjtp_has_prac': False, 'sjtp_has_pws': False, 'sjtpbase_sequence': 1}}

    """

    # append_key only used when adding subjects by modal, not at import
    # values of append_key are 'created' 'changed' 'restored' or None
    #  is added as key to updated_studsubj_rows with value 'True'
    # to make field green


    log_mode = None
    updated_fields = []  # used in savetolog_studentsubject

    sql_value_dict = {}
    append_key = None

    if cur_student_dict and scheme_dict and new_subjbase_id:
        cur_student_id =cur_student_dict['stud_id']

# - get subjbase_dict whith key subjbase_id from scheme_dict
        new_schemeitem_subjbase_dict = scheme_dict.get(new_subjbase_id)
        if logging_on:
            logger.debug('    new_schemeitem_subjbase_dict: ' + str(new_schemeitem_subjbase_dict))
        """
        schemeitem_subjbase_dict: {
            'subjbase_id': 113, 'subj_code': 'ne', 'subj_name_nl': 'Nederlands', 
            'default_sjtpbase_sequence': 1, 'default_sjtpbase_id': 31, 
            31: {'si_id': 4494, 'sjtpbase_id': 31, 'sjtp_name': 'Gemeenschappelijk deel', 'sjtp_abbrev': 'Gemeensch.', 
                'sjtp_has_prac': False, 'sjtp_has_pws': False, 'sjtpbase_sequence': 1}}

        """
        if new_schemeitem_subjbase_dict:
            #if schemeitem_has_pws_subjbase_pk and not has_multiple_pws_subjects:
            #    # has_pws_subjbase_pk has value when 1 subject with psw found
            #    # has_pws_subjbase_pk is None and has_multiple_pws_subjects = True when multiple found
            #    if has_pws_subjbase_pk is None:
            #        has_pws_subjbase_pk = schemeitem_has_pws_subjbase_pk
            #    elif has_pws_subjbase_pk != schemeitem_has_pws_subjbase_pk:
            #        has_pws_subjbase_pk = None
            #        has_multiple_pws_subjects = True

            subject_name = new_schemeitem_subjbase_dict.get('subj_name_nl')
            subjbase_id = new_schemeitem_subjbase_dict.get('subjbase_id')

            if logging_on:
                logger.debug('    subject_name: ' + str(subject_name))
                logger.debug('    subjbase_id: ' + str(subjbase_id))

    # - get schemeitem_sjtp_dict whith key sjtpbase_id from subjbase_dict
            # get default schemeitem when sjtpbase_id is None (happens when importing studsubj
            if new_sjtpbase_id is None:
                new_sjtpbase_id = new_schemeitem_subjbase_dict.get('default_sjtpbase_id')
            # get first available schemeitem when sjtpbase_id is None (should not be possible, sequence is NOT NULL field
            if new_sjtpbase_id is None:
                for value_dict in new_schemeitem_subjbase_dict.values():
                    new_sjtpbase_id = value_dict.get('sjtpbase_id')
                    break
            new_schemeitem_sjtp_dict = new_schemeitem_subjbase_dict.get(new_sjtpbase_id)

            if logging_on:
                logger.debug('    new_sjtpbase_id: ' + str(new_sjtpbase_id))
                logger.debug('    new_schemeitem_sjtp_dict: ' + str(new_schemeitem_sjtp_dict))

            if new_schemeitem_sjtp_dict:
                new_schemeitem_id = new_schemeitem_sjtp_dict.get('si_id')
                new_sjtp_name = new_schemeitem_sjtp_dict.get('sjtp_name')
                new_sjtp_has_pws = new_schemeitem_sjtp_dict.get('sjtp_has_pws', False)

                # only add pws_title and pws_subjects when sjtp_has_pws
                if not new_sjtp_has_pws:
                    new_pws_title = None
                    new_pws_subjects = None

                if logging_on:
                    logger.debug('    new_schemeitem_id: ' + str(new_schemeitem_id))
                    logger.debug('    new_sjtp_name: ' + str(new_sjtp_name))

    # - check if student already has this subject (should be not more than one)
                studentsubject_dicts = cur_student_dict.get('studsubj')
                cur_studsubj_dict = studentsubject_dicts.get(subjbase_id)

                if logging_on:
                    logger.debug('    subject_name: ' + str(subject_name))
                    logger.debug('    existing cur_studsubj_dict: ' + str(cur_studsubj_dict))

# +++++ if current studentsubject is None: create and save Studentsubject
                if cur_studsubj_dict is None:
                    append_key = 'created'

                    log_mode = 'i' if is_import else 'c'
                    updated_fields.append('schemeitem_id')

                    sql_value_dict = {
                        'append_key': 'created',
                        'student_id': cur_student_id,
                        'schemeitem_id': new_schemeitem_id,
                        'studsubj_id': None,
                        'pws_title': new_pws_title,
                        'pws_subjects': new_pws_subjects
                    }
                    # - also create grade of first examperiod - happens in batch_insert
                    # - and add to log

# ++++++++++ studsubj_instance exists
                else:
                    cur_studsubj_id = cur_studsubj_dict['studsubj_id']
                    cur_schemeitem_id = cur_studsubj_dict['schemeitem_id']
                    cur_studsubj_deleted = cur_studsubj_dict['studsubj_deleted']
                    cur_studsubj_tobedeleted = cur_studsubj_dict['studsubj_tobedeleted']
                    cur_subj_published_id = cur_studsubj_dict['subj_published_id']

                    cur_prev_auth1by_id = cur_studsubj_dict['prev_auth1by_id']
                    cur_prev_auth2by_id = cur_studsubj_dict['prev_auth2by_id']
                    cur_prev_published_id = cur_studsubj_dict['prev_published_id']

                    if logging_on:
                        logger.debug('    cur_studsubj_deleted: ' + str(cur_studsubj_deleted))
                        logger.debug('    cur_studsubj_tobedeleted: ' + str(cur_studsubj_tobedeleted))

    # +++ if studsubj is deleted:
                    if cur_studsubj_deleted:
                        append_key = 'undeleted'

                        sql_value_dict = {
                            'append_key': 'undeleted',
                            'student_id': cur_student_id,
                            'studsubj_id': cur_studsubj_id,
                            'schemeitem_id': new_schemeitem_id,

                            'subj_auth1by_id': None,
                            'subj_auth2by_id': None,
                            'subj_published_id': None,

                            'prev_auth1by_id': None,
                            'prev_auth2by_id': None,
                            'prev_published_id': None,

                            'deleted': False,
                            'tobedeleted': False,
                            'tobechanged': False,

                            'pws_title': new_pws_title,
                            'pws_subjects': new_pws_subjects
                        }

    # +++ if studsubj is tobedeleted:
                    elif cur_studsubj_tobedeleted:
                        if logging_on:
                            logger.debug('    cur_schemeitem_id: ' + str(cur_schemeitem_id))
                            logger.debug('    new_schemeitem_id: ' + str(new_schemeitem_id))
                            logger.debug('    is_import: ' + str(is_import))

                        append_key = 'restored'
                        log_mode = 'r'
                        updated_field = 'deleted' if cur_studsubj_deleted else 'tobedeleted'
                        updated_fields.append(updated_field)

                        # PR2024-08-14
                        # when adding subject from modal form: use schemeitem
                        # when import: the schemeitem of the deleted subject is used
                        if not is_import and new_schemeitem_id != cur_schemeitem_id:
                           #setattr(studsubj_instance, 'schemeitem', schemeitem)
                           updated_fields.append('schemeitem_id')

                        # PR2023-08-30 Hans Vlinkervleugel: gives open circle before submitting first Ex1.
                        # solved bij adding check if is_published
                        new_tobechanged = (cur_subj_published_id is not None and new_schemeitem_id != cur_schemeitem_id)

                        new_subj_auth1by_id = cur_prev_auth1by_id if new_schemeitem_id == cur_schemeitem_id else None
                        new_subj_auth2by_id = cur_prev_auth2by_id if new_schemeitem_id == cur_schemeitem_id else None
                        new_subj_published_id = cur_prev_published_id if new_schemeitem_id == cur_schemeitem_id else None

                        sql_value_dict = {
                            'append_key': 'restored',
                            'student_id': cur_student_id,
                            'studsubj_id': cur_studsubj_id,
                            'schemeitem_id': new_schemeitem_id,

                            'subj_auth1by_id': new_subj_auth1by_id,
                            'subj_auth2by_id': new_subj_auth2by_id,
                            'subj_published_id': new_subj_published_id,

                            'prev_auth1by_id': None,
                            'prev_auth2by_id': None,
                            'prev_published_id': None,

                            'deleted': False,
                            'tobedeleted': False,
                            'tobechanged': new_tobechanged,

                            'pws_title': new_pws_title,
                            'pws_subjects': new_pws_subjects
                        }

                        if logging_on:
                            logger.debug('    append_key: ' + str(append_key))
                            logger.debug('    updated_fields: ' + str(updated_fields))

                        if not skip_save:
                            # studsubj_instance.save(request=request)

                            log_mode = 'u'
                            updated_fields.extend(('tobechanged', 'deleted', 'tobedeleted'))

                            # +++++ also undelete grades
                            # PR2023-02-12 grades are only set tobedeleted or deleted when exem. reex or reex03
                            #  restore previously deleted grades with ep=1
                            # studsubj_instance = None
                            # crit = Q(studentsubject=studsubj_instance) & \
                            #       Q(examperiod=c.EXAMPERIOD_FIRST) & \
                            #       (Q(tobedeleted=True) | Q(deleted=True))
                            # grades = stud_mod.Grade.objects.filter(crit)
                            grades = None
                            if grades is not None:
                                for grade in grades:
                                    setattr(grade, 'tobedeleted', False)
                                    setattr(grade, 'deleted', False)
                                    if not skip_save:
                                        grade.save(request=request)
                                        # PR2024-06-02 was:
                                        # awpr_log.savetolog_grade(
                                        #    grade_pk=grade.pk,
                                        #    req_mode='u',
                                        #    request=request,
                                        #    updated_fields=('deleted', 'tobedeleted')
                                        # )

                                        awpr_log.copytolog_grade_v2(
                                            grade_pk_list=[grade.pk],
                                            log_mode='u',
                                            modifiedby_id=request.user.pk
                                        )


 # +++ if studsubj is not tobedeleted and not deleted:
                    else:

                        #has_error = True
                        #err_01 = str(_("%(cpt)s '%(val)s' already exists.") % {'cpt': _('Subject'), 'val': subject_name})
                        ## error_list not in use when using modal form, message is displayed in modmessages
                        #error_list.append(err_01)

                        ## this one closes modal and shows modmessage with msg_html
                        #msg_dict = {'header': _('Add subject'), 'class': 'border_bg_warning', 'msg_html': err_01}
                        #messages.append(msg_dict)

                # - change the schemeitem if it has changed
                        if cur_schemeitem_id != new_schemeitem_id:
                            append_key = 'changed'
                            #subj_published_id = getattr(studsubj_instance, 'subj_published_id')

                            # PR2023-08-30 Hans Vlinkervleugel: gives open circle before submitting first Ex1.
                            # solved bij adding check if is_published
                            new_tobechanged = (cur_subj_published_id is not None and new_schemeitem_id != cur_schemeitem_id)
                        # set schemeitem
                            #setattr(studsubj_instance, 'schemeitem', schemeitem)
                            updated_fields.append('schemeitem_id')

                        # changing the schemeitem of a studsubj removes 'published' and 'auth'

                            # in Ex1 / Ex4, the following characters are shown
                            # - tobedeleted:    red     'X'
                            # - changed:        blue    large outlined circle u"\u2B58"
                            # - published:      black   large solid circle u"\u2B24"
                            #  otherwise (new): blue    large solid circle u"\u2B24"

                            # PR2023-08-30 Hans Vlinkervleugel: gives open circle before submitting first Ex1.
                            # solved bij only making 'tobechanged' True, when studsubj is_already published
                            if new_tobechanged:
                                updated_fields.append('tobechanged')

                            sql_value_dict = {
                                'append_key': 'changed',

                                'student_id': cur_student_id,
                                'studsubj_id': cur_studsubj_id,
                                'schemeitem_id': new_schemeitem_id,

                                'subj_auth1by_id': None,
                                'subj_auth2by_id': None,
                                'subj_published_id': None,

                                'prev_auth1by_id': None,
                                'prev_auth2by_id': None,
                                'prev_published_id': None,

                                'deleted': False,
                                'tobedeleted': False,
                                'tobechanged': new_tobechanged,

                                'pws_title': new_pws_title,
                                'pws_subjects': new_pws_subjects
                            }

    if logging_on:
        logger.debug('    sql_value_dict: ' + str(sql_value_dict))

    return sql_value_dict
# - end of create_studsubj


def batch_insert_or_update_studsubj(tobe_inserted_studentsubject_dict, request):
    #PR2024-08-17
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----------------- batch_insert_or_update_studsubj  --------------------')
        logger.debug('tobe_inserted_studentsubject_dict: ' + str(tobe_inserted_studentsubject_dict))

    def get_value_item(value_dict):
        student_id = value_dict.get('student_id')
        schemeitem_id = value_dict.get('schemeitem_id')
        studsubj_id = value_dict.get('studsubj_id')
        pws_title = value_dict.get('pws_title')
        pws_subjects = value_dict.get('pws_subjects')

        is_insert = studsubj_id is None
        value_str = None

        if student_id and schemeitem_id:
            # enter boolean like this: - necessary??
            #exemption_imported = "TRUE" if row.get('exemption_imported') else "FALSE"

            # handle apostrophe in pws with quoted strings $$
            # https://www.postgresqltutorial.com/postgresql-plpgsql/dollar-quoted-string-constants/

            pws_title_str = ''.join(("$$", pws_title, "$$")) if pws_title else "NULL"
            pws_subjects_str = ''.join(("$$", pws_subjects, "$$")) if pws_subjects else "NULL"

            if is_insert:
                values = ', '.join((
                    str(student_id),
                    str(schemeitem_id),
                    modifiedby_pk_str, modifiedat_delim,
                    pws_title_str, pws_subjects_str,

                    "FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE",
                    "FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE"
                ))
                value_str = ''.join(("(", values, ")"))

            else:
                values = ', '.join((
                    str(studsubj_id),
                    pws_title_str,
                    pws_subjects_str
                ))
                item = ''.join(("(", values, ")"))

        return value_str, is_insert
    # - end of get_item

    def get_insert_sql (value_str):
        return ''.join((
            "INSERT INTO students_studentsubject (",
                "student_id, schemeitem_id, modifiedby_id, modifiedat, ",
                "pws_title, pws_subjects, ",
                "is_extra_nocount, is_extra_counts, is_thumbrule, ",
                "has_exemption, has_reex, has_reex03, has_sr, ",
                "gl_ni_ce, gl_ni_pe,  gl_ni_se, gl_ni_sr, gradelist_use_exem, ",
                "deleted, tobedeleted, tobechanged",
            ") VALUES ",
                value_str,
            "RETURNING students_studentsubject.id, students_studentsubject.student_id;"
        ))

    def get_update_sql (value_str):
        return ''.join((
            "DROP TABLE IF EXISTS tmp; CREATE TEMP TABLE tmp (grade_id, segrade, sesrgrade, cegrade, pecegrade, finalgrade, exemption_imported) AS ",
            "VALUES (0::INT, '-'::TEXT, '-'::TEXT, '-'::TEXT, '-'::TEXT, '-'::TEXT, FALSE::BOOLEAN), ",
            value_str,
            "; UPDATE students_grade AS gr ",
            "SET segrade = tmp.segrade, sesrgrade = tmp.segrade, ",
            "cegrade = tmp.cegrade, pecegrade = tmp.cegrade, ",
            "finalgrade = tmp.finalgrade, ",
            "exemption_imported = tmp.exemption_imported, ",
            "modifiedby_id = ", modifiedby_pk_str, "::INT, modifiedat = ", modifiedat_delim, "::DATE ",
            "FROM tmp ",
            "WHERE tmp.grade_id = gr.id ",
            "RETURNING gr.id, gr.studentsubject_id;"
        ))

    modifiedby_pk_str = str(request.user.pk)
    modifiedat_delim =''.join(("'", str(timezone.now()), "'"))

    updated_studsubj_pk_list = []
    updated_student_pk_list = []
    tobe_created_grade_studsubj_pk_list = []

    if tobe_inserted_studentsubject_dict and request.user:

        try:
            insert_list, update_list = [], []
            for value_dict in tobe_inserted_studentsubject_dict.values():
                if logging_on:
                    logger.debug('  value_dict: ' + str(value_dict))
                """
                value_dict: {'grade_pk': None, 'studsubj_pk': 95423, 
                        'se_grade': '7.6', 'ce_grade': '7.2', 'finalgrade': '7', 
                        'exemption_imported': True}    
                """
                value_item, is_insert = get_value_item(value_dict)

                if logging_on:
                    logger.debug('value_item: ' + str(value_item))

                if value_item:
                    if is_insert:
                        insert_list.append(value_item)
                    else:
                        update_list.append(value_item)

                if logging_on:
                    logger.debug('    value_item: ' + str(value_item))

            for i, value_list in enumerate((insert_list, update_list)):
                if logging_on:
                    logger.debug('    ----------- index: ' + str(i))

                if value_list:
                    value_str = ', '.join(value_list)
                    sql_list = get_insert_sql(value_str) if i == 0 else get_update_sql(value_str)
                    sql = ''.join(sql_list)
                    if logging_on:
                        logger.debug('    sql: ' + str(sql))

                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                        rows = cursor.fetchall()
                        if logging_on:
                            logger.debug('    rows: ' + str(rows))

                        if rows:
                            for row in rows:
                            # "RETURNING students_studentsubject.id, students_studentsubject.student_id;"
                                if is_insert:
                                    tobe_created_grade_studsubj_pk_list.append(row[0])
                                updated_studsubj_pk_list.append(row[0])
                                # add studsubj_pk to list, to udate has_exemption later

                                if row[1] not in updated_studsubj_pk_list:
                                    updated_student_pk_list.append(row[1])

                        if tobe_created_grade_studsubj_pk_list:
                            value_list = []
                            for studsubj_pk in tobe_created_grade_studsubj_pk_list:
                                values = ', '.join((
                                    str(studsubj_pk),
                                    str(c.EXAMPERIOD_FIRST),
                                    modifiedby_pk_str, modifiedat_delim
                                ))
                                value = ''.join(("(", values, ")"))
                                value_list.append(value)

                            if value_list:
                                value_str = ', '.join(value_list)

                                grade_sql = ''.join((
                                    "INSERT INTO students_grade (",
                                    "studentsubject_id, examperiod, modifiedby_id, modifiedat",
                                    ") VALUES ",
                                    value_str,
                                    "RETURNING students_grade.id;"
                                ))

                                with connection.cursor() as cursor:
                                    cursor.execute(grade_sql)
                                    grade_rows = cursor.fetchall()
                                    if logging_on:
                                        logger.debug('    grade_rows: ' + str(grade_rows))

                        #if updated_studsubj_pk_list:
                        #    awpr_log.copytolog_grade_v2(
                        #        grade_pk_list=updated_grade_pk_list,
                        #        req_mode='i',
                        #        modifiedby_id=request.user.pk
                        #    )
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('updated_studsubj_pk_list: ' + str(updated_studsubj_pk_list))
        logger.debug('updated_student_pk_list: ' + str(updated_student_pk_list))

    return updated_studsubj_pk_list
# - end of batch_insert_or_update_studsubj
