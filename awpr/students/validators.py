# PR2019-02-17

from django.db import connection
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import pgettext_lazy, gettext_lazy as _

from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont
import math

from awpr import constants as c
from awpr import functions as af
from awpr import settings as s

from schools import models as school_mod
from students import models as stud_mod
from subjects import models as subj_mod

import logging
logger = logging.getLogger(__name__)


def get_multiple_occurrences(sel_examyear, sel_schoolbase, sel_depbase):  # PR2021-09-05
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------- get_multiple_occurrences ----------- ')
        logger.debug('--- sel_examyear: ' + str(sel_examyear))
        logger.debug('--- sel_schoolbase: ' + str(sel_schoolbase))
        logger.debug('--- sel_depbase: ' + str(sel_depbase))

    dictlist = []
    if sel_examyear and sel_schoolbase and sel_depbase:

# - get students with multiple occurrences
        # to speed up seach: get list of idnumbers of this schoolbase that occurs multiple times in database,
        # in this_year + last_year, for evening and lex school: last 10 years
        firstinrange_examyear_int, student_idnumber_list = \
            get_idnumbers_with_multiple_occurrence(sel_examyear, sel_schoolbase, sel_depbase)
        if logging_on:
            logger.debug('firstinrange_examyear_int: ' + str(firstinrange_examyear_int))

        if student_idnumber_list:
            for student_idnumber in student_idnumber_list:
                student_dict = lookup_multiple_occurrences(firstinrange_examyear_int, sel_examyear, sel_schoolbase, sel_depbase, student_idnumber)
                if student_dict:
                    dictlist.append(student_dict)
    if logging_on:
        logger.debug('dictlist: ' + str(dictlist))

    return dictlist
# - end of get_multiple_occurrences


def lookup_multiple_occurrences(firstinrange_examyear_int, sel_examyear, sel_schoolbase, sel_depbase, student_idnumber):  # PR2021-09-05
    # function looks up matching students in previous year(s)

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------- lookup_multiple_occurrences ----------- ')
        logger.debug('--- student: ' + str(student_idnumber))

    # first scheck if this student exists in this school, last year
    student_dict = {}
    if student_idnumber:
        idnumber_lower = student_idnumber.lower()

        cur_stud_dict = get_cur_stud_dict(idnumber_lower, sel_examyear, sel_schoolbase, sel_depbase)
        if cur_stud_dict:
            student_pk = cur_stud_dict.get('student_id')
            student_dict['cur_stud'] = cur_stud_dict

# get other occurrences of this student within period, from all countries
            sql_keys = {'first_ey': firstinrange_examyear_int, 'cur_ey': sel_examyear.code,
                        'st_id': student_pk, 'idnumber': idnumber_lower}
            sql_list = ["SELECT st.id AS student_id, st.base_id, st.lastname, st.firstname, st.prefix, st.result_info, st.linked, st.notlinked,",
                        "CONCAT_WS (' ', st.prefix, CONCAT(st.lastname, ','), st.firstname) AS fullname,",
                        "CONCAT(depbase.code, ' ', lvl.abbrev, CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE ' ' END, sct.abbrev) AS deplvlsct,",
                        "ey.code AS examyear, sch.name AS school_name, depbase.code AS depbase_code,",
                        "lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev",
                        "FROM students_student AS st",
                        "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                        "INNER JOIN schools_schoolbase AS schbase ON (schbase.id = sch.base_id)",
                        "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
                        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
                        "INNER JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",
                        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
                        "INNER JOIN subjects_sectorbase AS sctbase ON (sctbase.id = sct.base_id)",
                        "WHERE ey.code <= %(cur_ey)s::INT",
                        "AND LOWER(st.idnumber) = %(idnumber)s::TEXT",
                        "AND NOT st.id = %(st_id)s::INT",
                        "AND NOT st.tobedeleted"
                        ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                student_dict['other_stud'] = af.dictfetchall(cursor)

    if logging_on:
        logger.debug('student_dict: ' + str(student_dict))

    return student_dict
# - end of lookup_multiple_occurrences


def get_cur_stud_dict(idnumber_lower, sel_examyear, sel_schoolbase, sel_depbase):  # PR2021-09-17

    student_dict = None
    if idnumber_lower:
        # get student with this idnumber of this school and dep
        sql_keys = {'idnumber': idnumber_lower, 'ey_pk': sel_examyear.pk,
                    'sbase_id': sel_schoolbase.pk, 'depbase_id': sel_depbase.pk}
        sql_list = [
            "SELECT st.id AS student_id, st.base_id, st.idnumber, st.linked, st.notlinked,",
            "CONCAT_WS (' ', st.prefix, CONCAT(st.lastname, ','), st.firstname) AS fullname,",
            "depbase.code AS depbase_code, lvlbase.code AS lvlbase_code, sctbase.code AS sctbase_code",
    
            "FROM students_student AS st",
            "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

            "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
            "INNER JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
            "INNER JOIN subjects_sectorbase AS sctbase ON (sctbase.id = sct.base_id)",

            "WHERE ey.id = %(ey_pk)s::INT",
            "AND sch.base_id = %(sbase_id)s::INT",
            "AND LOWER(st.idnumber) = %(idnumber)s::TEXT",
            "AND NOT st.tobedeleted"
            ]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            student_dict = af.dictfetchone(cursor)

    return student_dict
# - end of


def get_idnumbers_with_multiple_occurrence(sel_examyear, sel_schoolbase, sel_depbase):  # PR2021-09-05
    # to speed up seach: get list of students of this schoolbase with idnumber that occurs multiple times in database,
    # in this_year + last_year, for evening and lex school: last 10 years
    # from all countries

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------- get_idnumbers_with_multiple_occurrence ----------- ')
        logger.debug('--- sel_examyear: ' + str(sel_examyear))
        logger.debug('--- sel_schoolbase: ' + str(sel_schoolbase))
        logger.debug('--- sel_depbase: ' + str(sel_depbase))
    # first scheck if this student exists in this school, last year
    firstinrange_examyear_int = None
    student_idnumber_list = []
    if sel_examyear and sel_schoolbase and sel_depbase:
        # - get selected school
        sel_school = school_mod.School.objects.get_or_none(
            base=sel_schoolbase,
            examyear=sel_examyear)
        if sel_school:
            if logging_on:
                logger.debug('sel_schoolbase: ' + str(sel_schoolbase))
                logger.debug('sel_schoolbase.pk: ' + str(sel_schoolbase.pk))

            current_examyear_int = sel_examyear.code
            # bewijs van vrijstelling is valid for 10 years when evening or lex school
            if sel_school.iseveningschool or sel_school.islexschool:
                firstinrange_examyear_int = current_examyear_int - 10 if current_examyear_int else None
            else:
                firstinrange_examyear_int = current_examyear_int - 1 if current_examyear_int else None

            sql_keys = {'sbase_id': sel_schoolbase.pk, 'last_ey': firstinrange_examyear_int, 'cur_ey': current_examyear_int}
            sql_list = ["SELECT st.idnumber, count(*),",
                        "ARRAY_AGG(DISTINCT sch.base_id)",
                        "FROM students_student AS st",
                        "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                        "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                        "WHERE ey.code >= %(last_ey)s::INT AND ey.code <= %(cur_ey)s::INT",
                        "AND NOT st.tobedeleted",
                        "GROUP BY st.idnumber",
                        "HAVING count(*) > 1",
                        "AND ARRAY_POSITION(ARRAY_AGG(DISTINCT sch.base_id), %(sbase_id)s::INT) > 0",
                        ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                for row in cursor.fetchall():
                    student_idnumber_list.append(row[0])
    return firstinrange_examyear_int, student_idnumber_list
# - end of get_idnumbers_with_multiple_occurrence


# ########################### validate students ##############################

def lookup_student_by_idnumber_nodots(school, department, idnumber_nodots, upload_fullname,
                   error_list, found_is_error=False):
    # PR2019-12-17 PR2020-12-06 PR2020-12-31  PR2021-02-27  PR2021-06-19  PR2021-07-21  PR2021-09-22
    # called before creating new student, by upload_student_from_datalist and create_student
    # function searches for existing student by idnumber, only in this school and this examyear
    # if student exists in other schools is checked by StudentLinkStudentView
    # gives error if multiple found, or found in different department, returns student if found in this department

    # this one is not used for uploading subjects and grade - they lookup idnumber in students_dict_with_subjbase_pk_list

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------- lookup_student_by_idnumber_nodots ----------- ')
        logger.debug('--- school:           ' + str(school))
        logger.debug('--- department:       ' + str(department))
        logger.debug('--- idnumber_nodots: ' + str(idnumber_nodots))
        logger.debug('--- upload_fullname: ' + str(upload_fullname))

    student = None
    not_found = False
    err_str = None

    # msg_err already given when id is blank or too long ( in stud_val.get_idnumber_nodots_stripped_lower)
    if idnumber_nodots:
        msg_keys = {'cpt': str(_('ID-number')), 'val': idnumber_nodots, 'name': upload_fullname}

# - count how many students exist with this idnumber in this school (all departments)
        # get all students from this school with this idnumber
        # idnumber can have letters, therefore compare case insensitive
        rows = stud_mod.Student.objects.filter(
            idnumber__iexact=idnumber_nodots,
            school=school
        )
        if logging_on:
            for row in rows:
                logger.debug('row: ' + str(row))

# - if no students found:
        if len(rows) == 0:
            not_found = True

        elif len(rows) == 1:

# - if one student found: get this student and check if it is in this department
            row = rows[0]

# - return student when student only occurs once and is in this department
            if row.department_id == department.pk:
                # return error when creating single student
                if found_is_error:
                    err_str = str(_("%(cpt)s '%(val)s' already exists.") % msg_keys)
                else:
                    # return student when importing, to update student infoPR2021-08-23
                    student = row
            else:

# - return error when student occurs in different department (not when eveningschool or lexschool)
                # in evening school student can do exam in two different departments at the same time
                # info from Richard Westerink, confirmed by Nancy Josephina August 2021
                if not school.iseveningschool and not school.islexschool:
                    err_str = str(_("%(cpt)s '%(val)s' already exists in a different department.") % msg_keys)
                else:
                    not_found = True

# - if two students found: (only when eveningschool or lexschool)
        elif (len(rows) == 2) and (school.iseveningschool or school.islexschool):
            # in evening school student can do exam in two different departments at the same time
            # info from Richard Westerink, confirmed by Nancy Josephina August 2021

    # - check which department both students have
            # - if one student exists in this department: return thisstudent
            # - if both students exists in this department: return error
            # - if both students exists in other departments: return error

            student = None
            for row in rows:
                if row.department_id == department.pk:
                    if student is None:
                        student = row
                    else:
                        student = None

    # - return error if both students exist in this this or other department: return error
            if student is None:
                err_str = get_error_multiple_students(rows, department, msg_keys)
            elif found_is_error:
                err_str = str(_("%(cpt)s '%(val)s' already exists.") % msg_keys)

# - return error if multiple students found (2 or more in dayschool, 3 or more in eveningschool or lexschool)
        else:
            err_str = get_error_multiple_students(rows, department, msg_keys)

        if logging_on:
            logger.debug('student: ' + str(student))
            logger.debug('not_found: ' + str(not_found))
            logger.debug('err_str: ' + str(err_str))
            logger.debug('----------- end of lookup_student_by_idnumber_nodots ---- ')

    return student, not_found, err_str
# --- end of lookup_student_by_idnumber_nodots


def get_error_multiple_students(rows, department, msg_keys):  # PR2021-09-22
    # - check which department both students have
    # - if one student exists in this department: return thisstudent
    # - if both students exists in this department: return error
    # - if both students exists in other departments: return error

    found_in_this_dep, found_in_diff_dep = False, False
    for row in rows:
        if row.department_id == department.pk:
            found_in_this_dep = True
        else:
            found_in_diff_dep = True

    err_str = str(_("%(cpt)s '%(val)s' exists multiple times this year ") % msg_keys)
    if found_in_diff_dep:
        if found_in_this_dep:
            err_str += str(_("in multiple departments of your school."))
        else:
            err_str += str(_("in other departments of your school."))
    elif found_in_this_dep:
        err_str += str(_("in this department."))

    return err_str
# --- end of get_error_multiple_students


# ========  get_prefix_lastname_comma_firstname  ======= PR2021-06-19
def get_prefix_lastname_comma_firstname(lastname_stripped, firstname_stripped, prefix_stripped):
    full_name = '---'

    if lastname_stripped:
        full_name = lastname_stripped
    if prefix_stripped:  # put prefix before last_name
        full_name = prefix_stripped + ' ' + full_name
    if firstname_stripped:  # put first_name after last_name
        full_name += ', ' + firstname_stripped

    return full_name


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def validate_examnumber_exists(student, examnumber):  # PR2021-08-11
    # - function checks if this examnumber already exists in this school and department
    # returns has_error when examnumber found in other students

# - filter school and department, exclude this student
    has_error = stud_mod.Student.objects.filter(
        school=student.school,
        department=student.department,
        examnumber__iexact=examnumber
    ).exclude(pk=student.pk).exists()

    return has_error
# - end of validate_examnumber_exists
##########################


# ========  validate_studentsubjects  ======= PR2021-08-17

def validate_studentsubjects_TEST(student, studsubj_dictlist_with_tobedeleted):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  validate_studentsubjects_TEST  -----')
        logger.debug('student: ' + str(student))
        logger.debug('studsubj_dictlist_with_tobedeleted: ' + str(studsubj_dictlist_with_tobedeleted))

    # PR2021-09-29 debug: 'tobedeleted' subjects must be filtered out
    # PR2021-12-27 debug: also subjects with 'is_extra_nocount' must be filtered out
    studsubj_dictlist = []
    if studsubj_dictlist_with_tobedeleted:
        for studsubj_dict in studsubj_dictlist_with_tobedeleted:
            tobedeleted = studsubj_dict.get('tobedeleted', False)
            if not tobedeleted:
                is_extra_nocount = studsubj_dict.get('is_extra_nocount', False)
                if not is_extra_nocount:
                    studsubj_dictlist.append(studsubj_dict)

    try:
        msg_list = []

        if student:
            stud_scheme = student.scheme
            if logging_on:
                logger.debug('stud_scheme: ' + str(stud_scheme))

    # - no student.scheme
            if stud_scheme is None:
                dep_missing, level_missing, sector_missing, has_profiel = False, False, False, False

                department = student.department
                if department is None:
                    dep_missing = True
                else:
                    has_profiel = department.has_profiel
                    level_missing = department.level_req and student.level is None
                    sector_missing = department.sector_req and student.sector is None

                not_entered_str = ''
                if dep_missing:
                    not_entered_str = _('The department is not entered.')
                else:
                    if level_missing and sector_missing:
                        if has_profiel:
                            not_entered_str = _("The 'leerweg' and 'profiel' are not entered.")
                        else:
                            not_entered_str = _("The 'leerweg' and 'sector' are not entered.")
                    elif level_missing:
                        not_entered_str = _("The 'leerweg' is not entered.")
                    elif sector_missing:
                        if has_profiel:
                            not_entered_str = _("The 'profiel' is not entered.")
                        else:
                            not_entered_str = _("The sector is not entered.")
                msg_list.append(str(not_entered_str) + '<br>' + str(_("Go to the page <i>Candidates</i> and enter the missing information of the candidate.")))
                if logging_on:
                    logger.debug('msg_list: ' + str(msg_list))

# - return warning when no subjects found
            elif studsubj_dictlist is None:
                msg_list = ["<div class='p-2 border_bg_warning'><p>", str(_('This candidate has no subjects.')), "</p></div>"]
            else:

    # ++++++++++++++++++++++++++++++++
    # - get min max subjects and mvt from scheme
                scheme_dict = get_scheme_si_sjtp_dict(stud_scheme)
    # ++++++++++++++++++++++++++++++++
    # - get info from studsubjects
                doubles_pk_list = []
                doubles_code_list = []
                studsubj_dict = get_studsubj_dict_from_modal(stud_scheme, student, studsubj_dictlist, doubles_pk_list, msg_list)
                doubles_pk_len = len(doubles_pk_list)
                if doubles_pk_len:
                    subject_code_dict = scheme_dict.get('subj_code')
                    for pk_int in doubles_pk_list:
                        doubles_code_list.append(subject_code_dict.get(pk_int, '-'))
                    display_str = convert_code_list_to_display_str(doubles_code_list)
                    if doubles_pk_len == 1:
                        msg_list.append(''.join(
                            ("<li>",
                             str(_("The subject %(list)s occurs twice and must be deleted.") % {'list': display_str}),
                             "<br>",
                             str(_("It will be disregarded in the rest of the validation.")),
                             "</li>")))
                    else:
                        msg_list.append(''.join((
                            "<li>",
                            str(_("The subjects %(list)s occur multiple times and must be deleted.") % {'list': display_str}),
                            "<br>",
                            str(_("They will be disregarded in the rest of the validation.")),
                            "</li>")))

                if logging_on:
                    logger.debug('............................... ')
                    logger.debug('scheme_dict: ' + str(scheme_dict))
                    logger.debug('studsubj_dict: ' + str(studsubj_dict))
                    logger.debug('msg_list: ' + str(msg_list))

                """
                studsubj_dict: {
                    'subject_list': [113, 114, 115, 116, 118, 133, 136, 120, 157, 154], 
                    'doubles_list': [], 
                    'sjtp_dict': {
                        249: {'min': 6, 'max': 6, 'name': 'Gemeenschappelijk deel', 
                                'subj_list': [113, 114, 115, 116, 118], 'nocount_list': [], 'counts_list': []}, 
                        296: {'min': 1, 'max': 1, 'name': 'Sectorprogramma', 
                                'subj_list': [133, 154], 'nocount_list': [], 'counts_list': []}, 
                        316: {'min': 1, 'max': 1, 'name': 'Stage', 
                                'subj_list': [136], 'nocount_list': [], 'counts_list': []}, 
                        266: {'min': 2, 'max': 2, 'name': 'Sectordeel', 
                                'subj_list': [120], 'nocount_list': [], 'counts_list': []}, 
                        283: {'min': 0, 'max': 1, 'name': 'Overig vak', 
                                'subj_list': [157], 'nocount_list': [], 'counts_list': []}
                        }, 
                    'mand_list': [113, 115, 116, 118, 136], 
                    'mand_subj_list': [], 
                    'combi_list': [115, 116], 
                    'mvt_list': [114, 120], 
                    'wisk_list': [], 
                    'core_list': [], 
                    'sufficient_list': [], 
                    'notatevlex_list': []}
                """

    # ++++++++++++++++++++++++++++++++
    # - get eveninstudent or lex student
                is_evening_or_lex_student = get_evening_or_lex_student(student)

    # -------------------------------
    # - check required subjects
                validate_required_subjects(is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)

    # - check total amount of subjects
                validate_amount_subjects('subject', is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)

    # - check amount of mvt and combi subjects
                validate_amount_subjects('mvt', is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)
                validate_amount_subjects('wisk', is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)
                validate_amount_subjects('combi', is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)

    # - check amount of subjects per subjecttype
                validate_amount_subjecttype_subjects(is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)
                if len(msg_list):
                    msg_str = ''.join(("<div class='p-2 border_bg_warning'><h6>", str(_('The composition of the subjects is not correct')), ':</h6>', "<ul class='msg_bullet'>"))
                    msg_list.insert(0, msg_str)
                    msg_list.append("</ul></div>")
                else:
                    msg_list = ["<div class='p-2 border_bg_valid'><p>", str(_('AWP has not found any errors in the composition of the subjects.')), "</p></div>"]
                if logging_on:
                    logger.debug('msg_list: ' + str(msg_list))

                """
                studsubj_dictlist_with_tobedeleted: [
                    {'mode': 'delete', 'student_pk': 3747, 'studsubj_pk': 21188, 'schemeitem_pk': 1793, 'is_extra_nocount': False, 'is_extra_counts': False, 'pws_title': None, 'pws_subjects': None}, 
                    {'mode': 'delete', 'student_pk': 3747, 'studsubj_pk': 23033, 'schemeitem_pk': 1786, 'is_extra_nocount': False, 'is_extra_counts': False, 'pws_title': None, 'pws_subjects': None}, 
                    {'mode': 'create', 'student_pk': 3747, 'studsubj_pk': None, 'schemeitem_pk': 2162, 'is_extra_nocount': False, 'is_extra_counts': False, 'pws_title': None, 'pws_subjects': None}, 
                    {'mode': 'create', 'student_pk': 3747, 'studsubj_pk': None, 'schemeitem_pk': 2153, 'is_extra_nocount': False, 'is_extra_counts': False, 'pws_title': None, 'pws_subjects': None}]}
                """

    # - return warning when subject is deleted or subjtype has changed
                deleted_list, changed_list, submitted_list = [], [], []
                for studsubj_dict in studsubj_dictlist_with_tobedeleted:
                    studsubj_pk = studsubj_dict.get('studsubj_pk')
                    tobedeleted = studsubj_dict.get('tobedeleted')
                    tobechanged = studsubj_dict.get('tobechanged')

                    if logging_on:
                        logger.debug('............................... ')
                        logger.debug('studsubj_dict: ' + str(studsubj_dict))
                        logger.debug('studsubj_pk: ' + str(studsubj_pk))
                        logger.debug('tobedeleted: ' + str(tobedeleted))
                        logger.debug('tobechanged: ' + str(tobechanged))

                # check if subject has already been submitted
                # PR2022-02-15 don't check on submitted studsubj or submitted grades
                    # - this will give problems when a school wants to delete subject with submitted grades
                    if (studsubj_pk) and (tobedeleted or tobechanged):
                        is_published = False

                        #if tobedeleted:
                        #    # check if studsubj has submitted grades
                        #    has_error, published = validate_submitted_locked_grades(
                        #        studsubj_pk=studsubj_pk
                        #    )
                        #    if published:
                        #        is_published = True

                        sb_code = '-'
                        studsubj = stud_mod.Studentsubject.objects.get_or_none(pk=studsubj_pk)
                        if studsubj:
                            sb_code = studsubj.schemeitem.subject.base.code

                        if tobedeleted:
                            deleted_list.append(sb_code)
                            # was:
                            #if is_published:
                            #    submitted_list.append(sb_code)
                            #else:
                            #    deleted_list.append(sb_code)
                        elif tobechanged:
                            changed_list.append(sb_code)

                deleted_count = len(deleted_list)
                changed_count = len(changed_list)
                submitted_count = len(submitted_list)
                if deleted_count or changed_count:
                    msg_list.append("<div class='p-2 border_bg_warning'><h6>" + str(_('ATTENTION')) + '</h6><p>')

                    if submitted_count:
                        submitted_list.sort()
                        subj_str = ''
                        for x in range(0, submitted_count):  # range(start_value, end_value, step), end_value is not included!
                            if x == 0:
                                join_str = ''
                            elif x == (submitted_count - 1):
                                join_str = str(_(' and '))
                            else:
                                join_str = ', '
                            subj_str += ''.join((join_str, "'", submitted_list[x], "'"))
                        if submitted_count == 1:
                            cpt1 = _('this subject')
                            cpt2 = _('it has submitted grades')
                        else:
                            cpt1 = _('these subjects')
                            cpt2 =_('they have submitted grades')
                        msg_list.append(
                            str(_("You cannot delete %(cpt1)s, because  %(cpt2)s.") \
                                % {'cpt1': cpt1, 'cpt2': cpt2}) + '</p></div>')

                    if deleted_count:
                        deleted_list.sort()
                        subj_str = ''
                        for x in range(0, deleted_count):  # range(start_value, end_value, step), end_value is not included!
                            if x == 0:
                                join_str = ''
                            elif x == (deleted_count - 1):
                                join_str = str(_(' and '))
                            else:
                                join_str = ', '
                            subj_str += ''.join((join_str, "'", deleted_list[x], "'"))
                        if deleted_count == 1:
                            msg_str = str(_("The subject %(subj_str)s will be deleted.") % {'subj_str': subj_str})
                        else:
                            msg_str = str(_("The subjects %(subj_str)s will be deleted.") % {'subj_str': subj_str})
                        msg_list.append(msg_str + '<br>')

                    if changed_count:
                        changed_list.sort()
                        subj_str = ''
                        for x in range(0, changed_count):  # range(start_value, end_value, step), end_value is not included!
                            if x == 0:
                                join_str = ''
                            elif x == (changed_count - 1):
                                join_str = str(_(' and '))
                            else:
                                join_str = ', '
                            subj_str += ''.join((join_str, "'", changed_list[x], "'"))
                        if changed_count == 1:
                            msg_str = str(_("The character of subject %(subj_str)s will be changed.") % {'subj_str': subj_str})
                        else:
                            msg_str = str(_("The character of subjects %(subj_str)s will be changed.") % {'subj_str': subj_str})
                        msg_list.append(msg_str + '<br>')

        msg_html = ''.join(msg_list)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

        msg_html = ' '.join(("<div class='p-2 border_bg_invalid'><p>",
                    str(_('An error occurred.')), str(_('AWP has not checked the composition of the subjects.')),"</p></div>"))

    if logging_on:
        logger.debug('msg_html: ' + str(msg_html))
    return msg_html
# --- end of validate_studentsubjects_TEST


def get_evening_or_lex_student(student):  # PR 2021-09-08
    # - get eveninstudent or lex student
    # PR 2021-09-08 debug tel Lionel Mongen CAL: validation still chekcs for required subjects
    # reason: CAL iseveningschool, but students were not set iseveningstudent
    # and validation onkly checked for iseveningstudent / islexstudent
    # solved by checking validation on iseveningstudent only when school is both dayschool and evveningschool,
    # check on eveningschool when only eveningschool
    if student.school.isdayschool:
        is_evening_or_lex_student = (student.school.iseveningschool and student.iseveningstudent) or \
                                    (student.school.islexschool and student.islexstudent)
    else:
        # when mot a dayschool: alle students are iseveningstudent / islexstudent
        is_evening_or_lex_student = student.school.iseveningschool or student.school.islexschool
    return is_evening_or_lex_student

##########################


# ========  validate_submitted_locked_grades  ======= PR2021-09-03 PR2022-02-15 PR2022-03-05
def validate_submitted_locked_grades(student_pk=None, studsubj_pk=None, examperiod=None):
    # PR2022-02-15 don't check on submitted studsubj, only on submitted grades
    # PR2022-03-05 used in remove bis_exam in student page
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- validate_submitted_locked_grades ----- ')
        logger.debug('student_pk: ' + str(student_pk))

    has_error, has_published = False, False

    try:
        sql_keys = {'st_id': student_pk}
        sql_list = [
            "SELECT grd.id",

            "FROM students_grade AS grd",
            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
            "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",

            "WHERE NOT st.tobedeleted AND NOT studsubj.tobedeleted AND NOT grd.tobedeleted",
            "AND (grd.se_published_id IS NOT NULL OR",
                "grd.sr_published_id IS NOT NULL OR",
                "grd.pe_published_id IS NOT NULL OR",
                "grd.ce_published_id IS NOT NULL OR",
                "grd.pe_exam_published_id IS NOT NULL OR",
                "grd.ce_exam_published_id IS NOT NULL)",
        ]
        if examperiod:
            sql_keys['ep'] = examperiod
            sql_list.append("AND (grd.examperiod = %(ep)s::INT)")

        if studsubj_pk:
            sql_keys['studsubj_id'] = studsubj_pk
            sql_list.append("AND (studsubj.id = %(studsubj_id)s::INT)")
        elif student_pk:
            sql_keys['st_id'] = student_pk
            sql_list.append("AND (st.id = %(st_id)s::INT)")

        sql_list.append("LIMIT 1;")
        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('sql_list: ' + str(sql_list))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = cursor.fetchall()
            if len(rows):
                has_published = True

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        has_error = True

    if logging_on:
        logger.debug('has_error: ' + str(has_error))
        logger.debug('has_published: ' + str(has_published))
    return has_error, has_published
# - end of validate_submitted_locked_grades


# ========  validate_studentsubjects  ======= PR2021-07-24
def validate_studentsubjects_no_msg(student):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  validate_studentsubjects  -----')
        logger.debug('student: ' + str(student))

# - store info of schemeitem in si_dict

    if student:
        stud_scheme = student.scheme
        if logging_on:
            logger.debug('stud_scheme: ' + str(stud_scheme))

        if stud_scheme is None:
            return True
        else:

# ++++++++++++++++++++++++++++++++
# - get min max subjects and mvt from scheme
            scheme_dict = get_scheme_si_sjtp_dict(stud_scheme)
# ++++++++++++++++++++++++++++++++
# - get info from studsubjects
            doubles_pk_list = []
            msg_list = []
            studsubj_dict = get_studsubj_dict(stud_scheme, student, doubles_pk_list, msg_list)
            if msg_list:
                return True
            if doubles_pk_list:
                return True

# ++++++++++++++++++++++++++++++++
# - get eveninstudent or lex student
            is_evening_or_lex_student = get_evening_or_lex_student(student)

# -------------------------------
# - check required subjects - not when is_evening_or_lex_student
            validate_required_subjects(is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)
            if msg_list:
                return True
# - check total amount of subjects
            validate_amount_subjects('subject', is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)
            if msg_list:
                return True

# - check amount of mvt and combi subjects
            validate_amount_subjects('mvt', is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)
            if msg_list:
                return True
            validate_amount_subjects('wisk', is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)
            if msg_list:
                return True
            validate_amount_subjects('combi', is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)
            if msg_list:
                return True

# - check amount of subjects per subjecttype
            validate_amount_subjecttype_subjects(is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list)
            if msg_list:
                return True

    return False
# --- end of validate_studentsubjects


def validate_required_subjects(is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list):
    # - validate amount of subjects PR2021-07-10

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  validate_required_subjects  -----')

# - skip when is_evening_or_lex_student
    if not is_evening_or_lex_student:
        scheme_mand_list = scheme_dict.get('mand_list', [])
        studsubj_mand_list = studsubj_dict.get('mand_list', [])

        subject_code_dict = scheme_dict.get('subj_code')

        if logging_on:
            logger.debug('scheme_dict: ' + str(scheme_dict))
            logger.debug('studsubj_dict: ' + str(studsubj_dict))
            logger.debug('scheme_mand_list: ' + str(scheme_mand_list))
            logger.debug('studsubj_mand_list: ' + str(studsubj_mand_list))
            logger.debug('subject_code_dict: ' + str(subject_code_dict))

        missing_mand_list = []
        if len(scheme_mand_list):
            for i, req_pk in enumerate(scheme_mand_list):
                if req_pk not in studsubj_mand_list:
                    req_code = subject_code_dict[req_pk]
                    missing_mand_list.append(req_code)

        msg_txt = None
        missing_req_len = len(missing_mand_list)
        if missing_req_len:
            if missing_req_len == 1:
                req_code = missing_mand_list[0]
                msg_txt = _("The required subject '%(code)s' is missing.") % {'code': req_code}
            else:
                req_code_list = convert_code_list_to_display_str(missing_mand_list)
                msg_txt = _("The required subjects %(code)s are missing.") % {'code': req_code_list}

        if msg_txt:
            msg_html = ''.join(('<li>', msg_txt, '</li>'))
            msg_list.append(msg_html)

        if logging_on:
            logger.debug('msg_txt: ' + str(msg_txt))


def convert_code_list_to_display_str(code_list):
    # function converts ['wk', 'en' 'pa'] in  "'en', 'pa' and 'wk'" PR2021-07-20
    display_str = ''
    if code_list:
        list_len = len(code_list)
        code_list.sort()
        for x in range(0, list_len):  # range(start_value, end_value, step), end_value is not included!
            if x == 0:
                join_str = ''
            elif x == (list_len - 1):
                join_str = str(_(' and '))
            else:
                join_str = ', '
            display_str += ''.join((join_str, "'", code_list[x], "'"))

    return display_str


def validate_amount_subjecttype_subjects(is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list):
    # - validate amount of subjects PR2021-07-11

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  validate_amount_subjecttype_subjects  -----')

    scheme_sjtp_dict = scheme_dict.get('sjtp_dict')
    studsubj_sjtp_dict = studsubj_dict.get('sjtp_dict')
    if scheme_sjtp_dict:
        for scheme_sjtp_dict_pk, scheme_item_dict in scheme_sjtp_dict.items():
            if logging_on:
                logger.debug('scheme_item_dict: ' + str(scheme_item_dict))
            # scheme_item_dict: {'name': 'Gemeensch.', 'min_subjects': 2, 'max_subjects': 4,
            # 'min_extra_nocount': 2, 'max_extra_nocount': 4, 'min_extra_counts': 2, 'max_extra_counts': 4,


            sjtp_name = scheme_item_dict.get('name', '')
            min_subjects = scheme_item_dict.get('min_subjects')
            max_subjects = scheme_item_dict.get('max_subjects')

            min_extra_nocount = scheme_item_dict.get('min_extra_nocount')
            max_extra_nocount = scheme_item_dict.get('max_extra_nocount')

            min_extra_counts = scheme_item_dict.get('min_extra_counts')
            max_extra_counts = scheme_item_dict.get('max_extra_counts')

            if logging_on:
                logger.debug('----------------: ' + str(sjtp_name))
                logger.debug('min_subjects: ' + str(min_subjects))
                logger.debug('max_subjects: ' + str(max_subjects))

            subject_count = 0
            if scheme_sjtp_dict_pk in studsubj_sjtp_dict:
                studsubj_item_dict = studsubj_sjtp_dict.get(scheme_sjtp_dict_pk)
                # studsubj_item_dict: {'min': 2, 'max': 4, 'name': 'Gemeensch.',
                #                       'subj_list': [1026, 999, 998, 1002, 1027],
                #                       'nocount_list': [], 'counts_list': [],
                subj_list = studsubj_item_dict.get('subj_list')
                nocount_list = studsubj_item_dict.get('nocount_list', [])
                counts_list = studsubj_item_dict.get('counts_list', [])
                subject_count = len(subj_list)

                if logging_on:
                    logger.debug('----------------: ' + str(sjtp_name))
                    logger.debug('studsubj_item_dict: ' + str(studsubj_item_dict))

                    logger.debug('subj_list: ' + str(subj_list))
                    logger.debug('nocount_list: ' + str(nocount_list))
                    logger.debug('counts_list: ' + str(counts_list))
                    logger.debug('subject_count: ' + str(subject_count))

            caption = _('subject')
            captions = _('subjects')

            validate_minmax_count('sjtp', is_evening_or_lex_student, scheme_dict, subject_count, caption, captions, sjtp_name, min_subjects, max_subjects, msg_list)
# - end of validate_amount_subjecttype_subjects


def validate_amount_subjects(field, is_evening_or_lex_student, scheme_dict, studsubj_dict, msg_list):
    # - validate amount of subjects PR2021-07-10
    # - skip validate minimum subjects when is_evening_or_lex_student
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  validate_amount_subjects  -----')
        logger.debug('field: ' + str(field))

    caption, captions = '', ''

    msg_html = None
    min_subj_key, max_subj_key, subject_list_key = '', '', ''
    if field == 'subject':
        min_subj_key = 'min_subj'
        max_subj_key = 'max_subj'
        subject_list_key = 'subject_list'
        caption = _('subject')
        captions = _('subjects')
    elif field == 'mvt':
        min_subj_key = 'min_mvt'
        max_subj_key = 'max_mvt'
        subject_list_key = 'mvt_list'
        caption = _('MVT subject')
        captions = _('MVT subjects')
    elif field == 'wisk':
        min_subj_key = 'min_wisk'
        max_subj_key = 'max_wisk'
        subject_list_key = 'wisk_list'
        caption = str((_('Wiskunde subject'))).lower()
        captions = str(_('Wiskunde subjects')).lower()
    elif field == 'core':
        min_subj_key = 'min_core'
        max_subj_key = 'max_core'
        subject_list_key = 'core_list'
        caption = _('core subject')
        captions = _('core subjects')
    elif field == 'combi':
        min_subj_key = 'min_combi'
        max_subj_key = 'max_combi'
        subject_list_key = 'combi_list'
        caption = _('combination subject')
        captions = _('combination subjects')

    min_subj = scheme_dict.get(min_subj_key)
    max_subj = scheme_dict.get(max_subj_key)
    studsubj_list = studsubj_dict.get(subject_list_key)

    subject_count = len(studsubj_list) if studsubj_list else 0

    if subject_count == 0:
        msg_count = _('There are no %(cpt)s.') % {'cpt': captions}
    elif subject_count == 1:
        msg_count = _('There is 1 %(cpt)s.') % {'cpt': caption}
    else:
        msg_count = _('There are %(val)s %(cpt)s.') % {'cpt': captions, 'val': subject_count}

    if logging_on:
        logger.debug('msg_count: ' + str(msg_count))
        logger.debug('studsubj_list: ' + str(studsubj_list))

    msg_txt, msg_available = '', ''
    if min_subj and max_subj and min_subj == max_subj:
        if subject_count != min_subj:
            msg_txt = _("The amount of %(cpt)s must be %(max)s.") % {'cpt': captions, 'max': max_subj}
    elif min_subj or max_subj:
        minmax_txt = None
        minmax_val = None
        if min_subj and subject_count < min_subj:
            if not is_evening_or_lex_student:
                minmax_txt = pgettext_lazy('NL_minimale', 'minimum')
                minmax_val = min_subj
                # - add available list , not when field = 'subject'
                if field != 'subject':
                    scheme_pk_list = scheme_dict.get(subject_list_key)
                    subject_code_dict = scheme_dict.get('subj_code')

                    available_list = []
                    if logging_on:
                        logger.debug('scheme_pk_list: ' + str(scheme_pk_list))

                    for subj_pk in scheme_pk_list:
                        if logging_on:
                            logger.debug('subj_pk: ' + str(subj_pk))

                        code = subject_code_dict[subj_pk]
                        if code not in available_list:
                            available_list.append(code)

                    if logging_on:
                        logger.debug('available_list: ' + str(available_list))

                    available_len = len(available_list)
                    if available_len:
                        if available_len == 1:
                            msg_available = _("The %(cpt)s is: '%(list)s'.") % {'cpt': caption, 'list': available_list[0]}
                        else:
                            available_list.sort()
                            available_str = ''
                            for i, val in enumerate(available_list):
                                available_str += "'" + val + "'"
                                if i:
                                    if i == available_len - 1:
                                        available_str += str(_(' and ')) + "'" + val + "'"
                                    else:
                                        available_str += ", '" + val + "'"
                                else:
                                    available_str = "'" + val + "'"

                            if logging_on:
                                logger.debug('available_list.sort: ' + str(available_list))
                            list_str = ''
                            for x in range(0, available_len):  # range(start_value, end_value, step), end_value is not included!
                                if x == 0:
                                    join_str = ''
                                elif x == (available_len - 1):
                                    join_str = str(_(' and '))
                                else:
                                    join_str = ', '
                                list_str += ''.join((join_str, "'", available_list[x], "'"))
                            msg_available = _("The %(cpt)s are: %(list)s.") % {'cpt': captions, 'list': list_str}
                            if logging_on:
                                logger.debug('list_str: ' + str(list_str))
                                logger.debug('msg_available: ' + str(msg_available))

        if max_subj and subject_count > max_subj:
            minmax_txt = pgettext_lazy('NL_maximale', 'maximum')
            minmax_val = max_subj

        if minmax_txt:
            msg_txt = _("The %(minmax_txt)s amount of %(cpt)s is %(minmax_val)s.") \
                      % {'cpt': captions, 'minmax_txt': minmax_txt, 'minmax_val': minmax_val}

            #msg_available += _("<br>Available MVT subjects are: %(list)s.") % {'list': 'min_mvt'}
    if msg_txt:
        msg_html = ''.join(('<li>', msg_count, ' ', msg_txt, ' ', msg_available, '</li>'))
        msg_list.append(msg_html)

    if logging_on:
        logger.debug('msg_txt: ' + str(msg_txt))
        logger.debug('msg_list: ' + str(msg_html))
# - validate_amount_subjects


def validate_minmax_count(field, is_evening_or_lex_student, scheme_dict, subject_count, caption, captions, sjtp_name, min_subj, max_subj, msg_list):

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  validate_minmax_count  -----')
        logger.debug('subject_count: ' + str(subject_count))

    if subject_count == 0:
        msg_count = _('There are no %(cpt)s') % {'cpt': captions}
    elif subject_count == 1:
        msg_count = _('There is 1 %(cpt)s') % {'cpt': caption}
    else:
        msg_count = _('There are %(val)s %(cpt)s') % {'cpt': captions, 'val': subject_count}

    if sjtp_name:
        msg_count = ''.join((str(msg_count), str(_(' with character ')), "'", sjtp_name, "'"))

    msg_count += '.'
    if logging_on:
        logger.debug('msg_count: ' + str(msg_count))

    msg_txt, msg_available = '', ''
    # note: min_subj and max_subj can be None (no restrictions) or zero (amount = 0)
    if min_subj is not None and max_subj is not None and min_subj == max_subj:
        if subject_count != min_subj:
            msg_txt = _("The amount of %(cpt)s must be %(max)s.") % {'cpt': captions, 'max': max_subj}
    elif min_subj is not None or max_subj is not None:
        minmax_txt = None
        minmax_val = None
        if min_subj is not None and subject_count < min_subj:
            if not is_evening_or_lex_student:
                minmax_txt = pgettext_lazy('NL_minimale', 'minimum')
                minmax_val = min_subj
                # - add available list , not when field = 'subject'
                if field != 'subject':
                    subject_code_dict = scheme_dict.get('subj_code')
                    available_list = []
                    for subj_pk, subject_code in subject_code_dict.items():
                        if logging_on:
                            logger.debug('subj_pk: ' + str(subj_pk))
                            logger.debug('subject_code: ' + str(subject_code))

                        if subject_code not in available_list:
                            available_list.append(subject_code)

                    if logging_on:
                        logger.debug('available_list: ' + str(available_list))

                    available_len = len(available_list)
                    if available_len:
                        if available_len == 1:
                            msg_available = _("The %(cpt)s is: '%(list)s'.") % {'cpt': caption, 'list': available_list}
                        else:
                            available_list.sort()
                            if logging_on:
                                logger.debug('available_list.sort: ' + str(available_list))
                            list_str = ''
                            for x in range(0, available_len):  # range(start_value, end_value, step), end_value is not included!
                                if x == 0:
                                    join_str = ''
                                elif x == (available_len - 1):
                                    join_str = str(_(' and '))
                                else:
                                    join_str = ', '
                                list_str += ''.join((join_str, "'", available_list[x], "'"))
                            msg_available = _("The %(cpt)s are: %(list)s.") % {'cpt': captions, 'list': list_str}
                            if logging_on:
                                logger.debug('list_str: ' + str(list_str))
                                logger.debug('msg_available: ' + str(msg_available))

        if max_subj is not None and subject_count > max_subj:
            minmax_txt = pgettext_lazy('NL_maximale', 'maximum')
            minmax_val = max_subj

        if minmax_txt:
            msg_txt = _("The %(minmax_txt)s amount of %(cpt)s is %(minmax_val)s.") \
                      % {'cpt': captions, 'minmax_txt': minmax_txt, 'minmax_val': minmax_val}

            #msg_available += _("<br>Available MVT subjects are: %(list)s.") % {'list': 'min_mvt'}
    if msg_txt:
        msg_html = ''.join(('<li>', msg_count, ' ', msg_txt, ' ', msg_available, '</li>'))
        msg_list.append(msg_html)
# - end of validate_minmax_count


def get_scheme_si_sjtp_dict(scheme):
# - get info from scheme, subjecttypes and schemeitems PR2021-07-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_scheme_si_sjtp_dict  -----')
        logger.debug('scheme: ' + str(scheme))

# - get min max subjects and mvt from scheme
    schemename = getattr(scheme, 'name')
    min_subj = getattr(scheme, 'min_subjects')
    max_subj = getattr(scheme, 'max_subjects')
    min_mvt = getattr(scheme, 'min_mvt')
    max_mvt = getattr(scheme, 'max_mvt')
    min_wisk = getattr(scheme, 'min_wisk')
    max_wisk = getattr(scheme, 'max_wisk')
    min_combi = getattr(scheme, 'min_combi')
    max_combi = getattr(scheme, 'max_combi')

# - get info from subjecttypes
    sjtp_dict = {}
    sjtps = subj_mod.Subjecttype.objects.filter(scheme=scheme)
    for sjtp in sjtps:
        sjtp_pk = sjtp.pk
        if sjtp_pk not in sjtp_dict:
            sjtp_dict[sjtp_pk] = {'name': sjtp.name,
                'min_subjects': sjtp.min_subjects,
                'max_subjects': sjtp.max_subjects,

                'min_extra_nocount': sjtp.min_extra_nocount,
                'max_extra_nocount': sjtp.max_extra_nocount,

                'min_extra_counts': sjtp.min_extra_counts,
                'max_extra_counts': sjtp.max_extra_counts
            }

# - get info from schemeitems
    mand_list = []
    mand_subj_list = []
    combi_list = []
    mvt_list = []
    wisk_list = []
    core_list = []
    sufficient_list = []
    notatevlex_list = []

    subject_code = {}

    sis = subj_mod.Schemeitem.objects.filter(scheme=scheme)
    for si in sis:
        subj_pk = si.subject.pk
        subj_code = si.subject.base.code
        subject_code[subj_pk] = subj_code

        if si.is_mandatory:
            mand_list.append(subj_pk)
        if si.is_mand_subj:
            mand_subj_list.append(subj_pk)
        if si.is_combi:
            combi_list.append(subj_pk)
        if si.is_mvt:
            mvt_list.append(subj_pk)
        if si.is_wisk:
            wisk_list.append(subj_pk)
        if si.is_core_subject:
            core_list.append(subj_pk)

        if si.rule_grade_sufficient:  # PR2021-11-23
            sufficient_list.append(subj_pk)
        if si.rule_gradesuff_notatevlex:  # PR2021-11-23
            notatevlex_list.append(subj_pk)

    scheme_dict = {
        'schemename': schemename,
        'min_subj': min_subj,
        'max_subj': max_subj,
        'min_mvt': min_mvt,
        'max_mvt': max_mvt,
        'min_wisk': min_wisk,
        'max_wisk': max_wisk,
        'min_combi': min_combi,
        'max_combi': max_combi,

        'sjtp_dict': sjtp_dict,

        'mand_list': mand_list,
        'mand_subj_list': mand_subj_list,
        'combi_list': combi_list,
        'mvt_list': mvt_list,
        'wisk_list': wisk_list,
        'core_list': core_list,
        'sufficient_list': sufficient_list,
        'notatevlex_list': notatevlex_list,

        'subj_code': subject_code
    }
    return scheme_dict
# - end of get_scheme_si_sjtp_dict


def get_studsubj_dict_from_modal(stud_scheme, student, si_dictlist, doubles_list, msg_list):
    # - get info from student subjects PR2021-08-17
    # si_dictlist contains studentsubject values from studsubj modal, not from the database
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_studsubj_dict_from_modal  -----')
        logger.debug('scheme: ' + str(student))
        logger.debug('si_dictlist: ' + str(si_dictlist))

    subject_list = []
    sjtp_dict = {}

    mand_list = []
    mand_subj_list = []
    combi_list = []
    mvt_list = []
    wisk_list = []
    core_list = []

    sufficient_list = []  # PR2021-11-23
    notatevlex_list = []

    if not si_dictlist:
        msg_list.append(str(_("This candidate has no subjects.")))
    else:
        for si_dict in si_dictlist:
            # si_dict = {schemeitem_id: 2089, is_extra_counts: false, is_extra_nocount: false,}
            schemeitem = None
            schemeitem_pk = si_dict.get('schemeitem_id')
            is_extra_nocount = si_dict.get('is_extra_nocount', False)
            is_extra_counts = si_dict.get('is_extra_counts', False)
            if schemeitem_pk:
                schemeitem = subj_mod.Schemeitem.objects.get_or_none(pk=schemeitem_pk)
            get_schemitem_info(stud_scheme, schemeitem, is_extra_nocount, is_extra_counts,
                                   subject_list, doubles_list, sjtp_dict, mand_list, mand_subj_list, combi_list,
                                   mvt_list, wisk_list, core_list, sufficient_list, notatevlex_list, msg_list)

    studsubj_dict = {
        'subject_list': subject_list,
        'doubles_list': doubles_list,
        'sjtp_dict': sjtp_dict,
        'mand_list': mand_list,
        'mand_subj_list': mand_subj_list,
        'combi_list': combi_list,
        'mvt_list': mvt_list,
        'wisk_list': wisk_list,
        'core_list': core_list,
        'sufficient_list': sufficient_list,
        'notatevlex_list': notatevlex_list
    }

    if logging_on:
        logger.debug('studsubj_dict: ' + str(studsubj_dict))
    return studsubj_dict
# - end of get_studsubj_dict_from_modal


def get_studsubj_dict(stud_scheme, student, doubles_list, msg_list):  #  PR2021-07-10 PR2021-12-30
    # - get info from student subjects
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_studsubj_dict  -----')
        logger.debug('scheme: ' + str(student))

    subject_list = []
    sjtp_dict = {}

    mand_list = []
    mand_subj_list = []
    combi_list = []
    mvt_list = []
    wisk_list = []
    core_list = []

    sufficient_list = []  # PR2021-11-23
    notatevlex_list = []

# - create dict with studentsubject values that are used in validator
    # PR2021-12-27 debug: also skip subjects with 'is_extra_nocount'
    rows = stud_mod.Studentsubject.objects.filter(
        student=student,
        tobedeleted=False,
        is_extra_nocount=False
    )
    if rows is None:
        msg_list.append(_("This candidate has no subjects."))
    else:
        for studsubj in rows:
            get_schemitem_info(stud_scheme, studsubj.schemeitem,
                                   studsubj.is_extra_nocount, studsubj.is_extra_counts,
                                   subject_list, doubles_list, sjtp_dict, mand_list, mand_subj_list, combi_list,
                                   mvt_list, wisk_list, core_list, sufficient_list, notatevlex_list, msg_list)

    studsubj_dict = {
        'subject_list': subject_list,
        'doubles_list': doubles_list,
        'sjtp_dict': sjtp_dict,
        'mand_list': mand_list,
        'mand_subj_list': mand_subj_list,
        'combi_list': combi_list,
        'mvt_list': mvt_list,
        'wisk_list': wisk_list,
        'core_list': core_list,
        'sufficient_list': sufficient_list,
        'notatevlex_list': notatevlex_list
    }

    if logging_on:
        logger.debug('studsubj_dict: ' + str(studsubj_dict))
    return studsubj_dict
# - end of get_studsubj_dict


def get_schemitem_info(stud_scheme, schemeitem,
                       studsubj_is_extra_nocount, studsubj_is_extra_counts,
                       subject_list, doubles_list, sjtp_dict, mand_list, mand_subj_list, combi_list,
                       mvt_list, wisk_list, core_list, sufficient_list, notatevlex_list, msg_list):
    # - get info from schemitem PR2021-08-17
    logging_on = False  # s.LOGGING_ON
    if schemeitem.scheme_id != stud_scheme.pk:
        value = schemeitem.subject.base.code
        msg_str = '<li>' + str(_("Subject '%(val)s' does not occur in this subject scheme.") % {'val': value}) + '</li>'
        if logging_on:
            logger.debug('msg_str: ' + str(msg_str))
        msg_list.append(msg_str)
    else:

# - put subject.pk in subject_list, or in doubles_list when already exists
        subj_pk = schemeitem.subject.pk

        # if subject already exists: skip double from other checks (double should not be possible)
        if subj_pk in subject_list:
            doubles_list.append(subj_pk)
        else:
            subject_list.append(subj_pk)

# add subject to subjecttype list
            subjecttype = schemeitem.subjecttype
            sjtp_pk = subjecttype.pk
            if sjtp_pk not in sjtp_dict:
                sjtp_dict[sjtp_pk] = {
                    'min': subjecttype.min_subjects,
                    'max': subjecttype.max_subjects,
                    'name': subjecttype.name,
                    'subj_list': [],
                    'nocount_list': [],
                    'counts_list': []
                }
            item_dict = sjtp_dict.get(sjtp_pk)

            subj_list = item_dict.get('subj_list')
            subj_list.append(subj_pk)

            if studsubj_is_extra_nocount:
                nocount_list = item_dict.get('nocount_list')
                nocount_list.append(subj_pk)
            if studsubj_is_extra_counts:
                counts_list = item_dict.get('counts_list')
                counts_list.append(subj_pk)

            if schemeitem.is_mandatory:
                mand_list.append(subj_pk)
            if schemeitem.is_mand_subj:
                mand_subj_list.append(subj_pk)
            if schemeitem.is_combi:
                combi_list.append(subj_pk)
            if schemeitem.is_mvt:
                mvt_list.append(subj_pk)
            if schemeitem.is_wisk:
                wisk_list.append(subj_pk)
            if schemeitem.is_core_subject:
                core_list.append(subj_pk)
            if schemeitem.rule_grade_sufficient:  # PR2021-11-23
                sufficient_list.append(subj_pk)
            if schemeitem.rule_gradesuff_notatevlex:  # PR2021-11-23
                notatevlex_list.append(subj_pk)

# - end of get_schemitem_info


#######################################################################################
# ++++++++++++ Validations  +++++++++++++++++++++++++

# ========  get_examnumberlist_from_database  ======= PR2021-07-19
# NOT IN USE, switched to excel number format

def get_dateformat_from_uploadfileNIU(data_list, date_field):
    # function returns logging_on, that is used in datefield of  uploadfile
    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  get_dateformat_from_uploadfile  -----')
        logger.debug('date_field: ' + str(date_field))

# - get_min_max_dateparts():
    max_0, max_1, max_2 = 0, 0, 0
    for data_dict in data_list:
        date_string = data_dict.get(date_field)
        if date_string:
            if '/' in date_string:
                date_string = date_string.replace('/', '-')

            if logging_on:
                logger.debug('---- ' )
                logger.debug('date_string: ' + str(date_string))

            if '-' in date_string:
                arr = date_string.split('-')
                if logging_on:
                    logger.debug('arr: ' + str(arr))

                if len(arr) == 3:
                    int_0, int_1, int_2 = None, None, None
                    if arr[0] and arr[0].isdecimal():
                        int_0 = int(arr[0])
                    if arr[1] and arr[1].isdecimal():
                        int_1 = int(arr[1])
                    if arr[2] and arr[2].isdecimal():
                        int_2 = int(arr[2])

                    if logging_on:
                        logger.debug('int_0: ' + str(int_0) + ' int_1: ' + str(int_1) + ' int_2: ' + str(int_2))

                    if int_0 is not None and int_1 is not None and int_2 is not None:
                        if int_0 > max_0:
                            max_0 = int_0
                        if int_1 > max_1:
                            max_1 = int_1
                        if int_2 > max_2:
                            max_2 = int_2

                    if logging_on:
                        logger.debug('max_0: ' + str(max_0) + ' max_1: ' + str(max_1) + ' max_2: ' + str(max_2))


    if logging_on:
        logger.debug('final max_0: ' + str(max_0) + ' max_1: ' + str(max_1) + ' max_2: ' + str(max_2))

# - get position of year (either pos 0 or pos 2)
    year_pos = None
    if max_0 > 31 and max_1 <= 31 and max_2 <= 31:
        year_pos = 0
    elif max_2 > 31 and max_0 <= 31 and max_1 <= 31:
        year_pos = 2

# - get position of day
    day_pos = None
    if year_pos == 0:
        if max_1 > 12 and max_2 <= 12:
            day_pos = 1
        elif max_2 > 12 and max_1 <= 12:
            day_pos = 2
    elif year_pos == 2:
        if max_0 > 12 and max_1 <= 12:
            day_pos = 0
        elif max_1 > 12 and max_0 <= 12:
            day_pos = 1

    if logging_on:
        logger.debug('year_pos: ' + str(year_pos) + ' day_pos: ' + str(day_pos))

# - format
    dateformat = ''
    if year_pos is not None and day_pos is not None:
        if year_pos == 0:
            if day_pos == 1:
                dateformat = 'yyyy-dd-mm'
            elif day_pos == 2:
                dateformat = 'yyyy-mm-dd'
        elif year_pos == 2:
            if day_pos == 0:
                dateformat = 'dd-mm-yyyy'
            elif day_pos == 1:
                dateformat = 'mm-dd-yyyy'

    if logging_on:
        logger.debug('dateformat: ' + str(dateformat))

    return dateformat
# - end of get_dateformat_from_uploadfile


# ========  get_idnumberlist_from_database  ======= PR2021-07-19 PR2022-06-20
def get_idnumberlist_from_database(sel_school):
    # get list of idnumbers of this school, used with import student and update student
    # idnumber_list contains tuples with (id, idnumber)
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_idnumberlist_from_database -----')
        logger.debug('sel_school: ' + str(sel_school))

    idnumber_list = []
    if sel_school:
        sql_keys = {'sch_id': sel_school.pk}
        sql_list = ["SELECT st.id, st.idnumber",
            "FROM students_student AS st",
            "WHERE st.school_id = %(sch_id)s::INT",
            "AND st.idnumber IS NOT NULL",
            "AND NOT st.tobedeleted",
            "ORDER BY st.idnumber"]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            idnumber_list = cursor.fetchall()

    if logging_on:
        logger.debug('idnumber_list: ' + str(idnumber_list))

    return idnumber_list
# - end of get_idnumberlist_from_database


# ========  get_examnumberlist_from_database  =======
def get_examnumberlist_from_database(sel_school, sel_department):
    # PR2021-07-19 PR2022-06-26
    # get list of examnumbers of this school and this department, used with import student  and update student
    # list contains tuples with (id, examnumber) id is needed to skip value of  this student
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_examnumberlist_from_database -----')
        logger.debug('sel_school: ' + str(sel_school))
        logger.debug('sel_department: ' + str(sel_department))

    examnumber_list = []
    if sel_school and sel_department:
        sql_keys = {'sch_id': sel_school.pk, 'dep_id': sel_department.pk}
        sql_list = ["SELECT st.id, st.examnumber",
            "FROM students_student AS st",
            "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
            "AND st.examnumber IS NOT NULL",
            "AND NOT st.tobedeleted",
            "ORDER BY st.examnumber"]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            examnumber_list = cursor.fetchall()

    if logging_on:
        logger.debug('examnumber_list: ' + str(examnumber_list))
    return examnumber_list
# - end of get_examnumberlist_from_database


# ========  get_diplomanumberlist_gradelistnumberlist_from_database  =======
def get_diplomanumberlist_gradelistnumberlist_from_database(field, sel_school):
    # PR2022-06-26
    # get list of diplomanumbers and gradelistnumbers of this school, used with import student and update student
    # list contains tuples with (id, value) id is needed to skip value of  this student

    value_list = []
    if sel_school:
        sql_keys = {'sch_id': sel_school.pk}
        sql_list = ["SELECT stud.id, stud.", field, " ",
            "FROM students_student AS stud ",
            "WHERE stud.school_id = %(sch_id)s::INT ",
            "AND stud.", field, " IS NOT NULL ",
            "AND NOT stud.tobedeleted"]
        sql = ''.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            value_list = cursor.fetchall()

    return value_list
# - end of get_diplomanumberlist_gradelistnumberlist_from_database
"""
TODO replace by functio that also detects dipl nr in other schools

# ========  get_diplomanumberlist_gradelistnumberlist_from_database  =======
def validate_diplomanumberlist_gradelistnumberlist_exists(field, value, sel_school):
    # PR2022-06-26
    # get list of diplomanumbers and gradelistnumbers of this school, used with import student and update student
    # list contains tuples with (id, value) id is needed to skip value of  this student

    value_list = []
    if sel_school and value:
        sql_keys = {'ey_id': sel_school.examyear.pk, 'val': value.strip()}
        sql_list = ["SELECT stud.id, ,
            "FROM students_student AS stud ",
            "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
            "INNER JOIN schools_schoolbase AS sbase ON (sbase.id = school.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

            "WHERE school.examyear_id = %(ey_id)s::INT",
            "AND TRIM(stud.", field, ") ILIKE %(val)s::TEXT",  # ILIKE is case insensitive
            "AND NOT stud.tobedeleted"

            "WHERE stud.school_id = %(sch_id)s::INT ",
            "AND stud.", field, " IS NOT NULL ",
            "AND NOT stud.tobedeleted"]
        sql = ''.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            value_list = cursor.fetchall()

    return value_list
# - end of get_diplomanumberlist_gradelistnumberlist_from_database



"""

# ========  get_double_schoolcode_usernamelist_from_uploadfile  ======= PR2021-08-04
def get_double_schoolcode_usernamelist_from_uploadfile(data_list):
    # function returns list of (schoolcode, username) tuples that occur multiple times in data_list

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  get_double_schoolcode_usernamelist_from_uploadfile  -----')

    double_username_list, double_email_list = [], []
    # user_list is list of of (schoolcode, username) tuples  of all users in data_list.
    # email_list is list of of (schoolcode, email) tuples  of all users in data_list.
    username_list, email_list = [], []
    for data_dict in data_list:
        datadict_schoolcode = data_dict.get('schoolcode')
        datadict_schoolcode_stripped = datadict_schoolcode.strip() if datadict_schoolcode else None
        datadict_schoolcode_lc = datadict_schoolcode_stripped.lower() if datadict_schoolcode_stripped else ''

        datadict_username = data_dict.get('username')
        datadict_username_stripped = datadict_username.strip() if datadict_username else None
        datadict_username_underscore = datadict_username_stripped.replace(' ', '_') if datadict_username_stripped else None
        datadict_username_lc = datadict_username_underscore.lower() if datadict_username_underscore else ''

        datadict_email = data_dict.get('email')
        datadict_email_stripped = datadict_email.strip() if datadict_email else None
        datadict_email_lc = datadict_email_stripped.lower() if datadict_email_stripped else ''

        if logging_on:
            logger.debug('datadict_schoolcode_lc: ' + str(datadict_schoolcode_lc))
            logger.debug('datadict_username_lc: ' + str(datadict_username_lc))
            logger.debug('datadict_email_lc: ' + str(datadict_email_lc))

# ---------------------------------------------------------

    # check if schoolcode + username already exists in username_list
        search_tuple = (datadict_schoolcode_lc, datadict_username_lc)
    # add to username_list if it is not in that list yet
        if not found_in_tuple_list(username_list, search_tuple):
            username_list.append(search_tuple)
    # if not found_in_double_username_list: add to  found_in_double_username_list
        elif not found_in_tuple_list(double_username_list, search_tuple):
            double_username_list.append(search_tuple)

# ---------------------------------------------------------
    # check if schoolcode + email already exists in username_list
        search_tuple = (datadict_schoolcode_lc, datadict_email_lc)
        # add to username_list if it is not in that list yet
        if not found_in_tuple_list(email_list, search_tuple):
            email_list.append(search_tuple)
        # if not found_in_double_username_list: add to  found_in_double_username_list
        elif not found_in_tuple_list(double_email_list, search_tuple):
            double_email_list.append(search_tuple)

# ---------------------------------------------------------
    if logging_on:
        logger.debug('username_list: ' + str(username_list))
        logger.debug('email_list: ' + str(email_list))
        logger.debug('double_username_list: ' + str(double_username_list))
        logger.debug('double_email_list: ' + str(double_email_list))

    return double_username_list, double_email_list
# - end of get_double_schoolcode_usernamelist_from_uploadfile


def found_in_tuple_list(tuple_list, search_tuple): # PR2021-08-05
    found = False
    if tuple_list:
        for item_tuple in tuple_list:
            if search_tuple[0] == item_tuple[0] and search_tuple[1] == item_tuple[1]:
                found = True
                break
    return found


# ========  validate_double_schoolcode_username_in_uploadfile  ======= PR2021-07-17
def validate_double_schoolcode_username_in_uploadfile(schoolcode, username, double_entrieslist, error_list):
    has_error = False
    if schoolcode and username and double_entrieslist:
        search_tuple = (schoolcode.lower(), username.lower())
        if found_in_tuple_list(double_entrieslist, search_tuple):
            has_error = True
            error_list.append(_("This schoolcode + user is found multiple times in this upload file.") )
    return has_error
# - end of validate_double_schoolcode_username_in_uploadfile


# ========  validate_double_schoolcode_username_in_uploadfile  ======= PR2021-07-17
def validate_double_schoolcode_email_in_uploadfile(schoolcode, email, double_entrieslist, error_list):
    has_error = False
    if schoolcode and email and double_entrieslist:
        search_tuple = (schoolcode.lower() , email.lower())
        if found_in_tuple_list(double_entrieslist, search_tuple):
            has_error = True
            error_list.append(_("This schoolcode + email address is found multiple times in this upload file."))
    return has_error
# - end of validate_double_schoolcode_username_in_uploadfile


# ========  get_double_diplomanumber_gradelistnumber_from_uploadfile  ======= PR2022-06-26
def get_double_diplomanumber_gradelistnumber_from_uploadfile(data_list):
    # function returns list of diplomanumber and gradelistnumber, that occur multiple times in data_list

    diplomanumber_list = []
    gradelistnumber_list = []
    double_diplomanumber_list = []
    double_gradelistnumber_list = []

    for data_dict in data_list:
        diplomanumber = data_dict.get('diplomanumber')

        if diplomanumber:
            if not isinstance(diplomanumber, str):
                diplomanumber = str(diplomanumber)

            if diplomanumber not in diplomanumber_list:
                diplomanumber_list.append(diplomanumber)
            elif diplomanumber not in double_diplomanumber_list:
                double_diplomanumber_list.append(diplomanumber)

        gradelistnumber = data_dict.get('gradelistnumber')
        if gradelistnumber:
            if not isinstance(gradelistnumber, str):
                gradelistnumber = str(gradelistnumber)

            if gradelistnumber not in gradelistnumber_list:
                gradelistnumber_list.append(gradelistnumber)
            elif diplomanumber not in double_gradelistnumber_list:
                double_gradelistnumber_list.append(gradelistnumber)

    return double_diplomanumber_list, double_gradelistnumber_list
# - end of get_double_diplomanumber_gradelistnumber_from_uploadfile


# ========  get_double_idnumberlist_from_uploadfile  ======= PR2021-06-14 PR2021-07-17 PR2022-01-04
def get_double_idnumberlist_from_uploadfile(data_list):
    # function returns list of valid idnumbers, that occur multiple times in data_list

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  get_double_idnumberlist_from_uploadfile  -----')

    double_entrieslist = []
    # student_list is list of idnumbers of all students in data_list.
    student_list = []
    for data_dict in data_list:
        id_number = data_dict.get('idnumber')
        if logging_on:
            logger.debug('id_number: ' + str(id_number) + ' ' + str(type(id_number)))
            logger.debug('isinstance(id_number, int): ' + str(isinstance(id_number, int)))

        idnumber_nodots_stripped, msg_errNIU, birthdate_dteobjNIU = get_idnumber_nodots_stripped_lower(id_number)
        if logging_on:
            logger.debug('idnumber_nodots_stripped: ' + str(idnumber_nodots_stripped) + ' ' + str(type(idnumber_nodots_stripped)))

        # PR2022-01-04 debug: when idnumber is not valid, idnumber_nodots_stripped = ''. Skip check in that case
        if idnumber_nodots_stripped:
            found = False
            if student_list:
                for student_id in student_list:
                    if student_id == idnumber_nodots_stripped:
                        if logging_on:
                            logger.debug('student_id == idnumber_nodots_stripped: ' + str(student_id) + ' ' + str(type(student_id)))
                        found = True
                        if idnumber_nodots_stripped not in double_entrieslist:
                            double_entrieslist.append(idnumber_nodots_stripped)
                        break
            if not found:
                student_list.append(idnumber_nodots_stripped)

        if logging_on:
            logger.debug('>>> student_list: ' + str(student_list))
            logger.debug('>>> double_entrieslist: ' + str(double_entrieslist))
    return double_entrieslist
# - end of get_double_idnumberlist_from_uploadfile


def get_idnumber_nodots_stripped_lower(id_number):
    # PR2021-07-20  PR2021-09-10
    logger_on = False  # s.LOGGING_ON
    if logger_on:
        logger.debug('  -----  get_idnumber_nodots_stripped_lower  -----')
        logger.debug('id_number: ' + str(id_number) + ' ' + str(type(id_number)))

    idnumber_nodots_stripped_lower = ''
    birthdate_dteobj = None
    msg_err = None
    if id_number:
        try:
            if isinstance(id_number, int):
                id_number = str(id_number)

            id_number_str = id_number.replace('.', '')
            if id_number_str:
                id_number_str = id_number_str.strip()
                if logger_on:
                    logger.debug('id_number_str: <' + str(id_number_str) + '> ' + str(type(id_number_str)))
                if id_number_str:
                    id_number_str = id_number_str.lower()

                    is_ok = False
                    if id_number_str:
                        if len(id_number_str) == 10: # PR2019-02-18 debug: object of type 'NoneType' has no len(), added: if id_str
                            date_str = id_number_str[:8]
                            if date_str.isnumeric():

                        # ---   convert to date
                                date_iso = date_str[:4] + "-" + date_str[4:6] + "-" + date_str[6:8]
                                birthdate_dteobj = af.get_date_from_ISO(date_iso)

                                if birthdate_dteobj :
                                    is_ok = True

                    if logger_on:
                        logger.debug('is_ok: ' + str(is_ok) )
                    if is_ok:
                        idnumber_nodots_stripped_lower = id_number_str
                    else:
                        msg_err = _("ID number '%(val)s' is not valid.") % {'val': id_number}
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            msg_err = _("ID number '%(val)s' is not valid.") % {'val': id_number}
    else:
        msg_err = _("ID number is not entered.")

    if logger_on:
        logger.debug('    msg_err: ' + str(msg_err))
        logger.debug('    idnumber_nodots_stripped_lower: ' + str(idnumber_nodots_stripped_lower) + ' ' + str(type(idnumber_nodots_stripped_lower)))
        logger.debug('    birthdate_dteobj: ' + str(birthdate_dteobj)+ ' ' + str(type(birthdate_dteobj)))
    return idnumber_nodots_stripped_lower, msg_err, birthdate_dteobj
# - end of get_idnumber_nodots_stripped_lower


def get_string_convert_type_and_strip(caption, value, blank_not_allowed):
    # function converts non-string types to string and strips it from spaces PR2021-11-07
    value_stripped = ''
    msg_err = None
    if value:
        try:
            if not isinstance(value, str):
                value = str(value)

            value_stripped = value.strip()

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            msg_err = _("%(cpt)s '%(val)s' is not a valid field type.") % {'cpt': caption, 'val': str(value)}

    elif blank_not_allowed:
        msg_err = _("%(cpt)s cannot be blank.")% {'cpt': caption, 'val': str(value)}

    return value_stripped, msg_err
# - end of get_string_checked_for_type_and_stripped




# ========  get_double_entrieslist_with_firstlastname_from_uploadfileNIU  ======= PR2021-06-14 PR2021-07-16
# NOT IN USE

def get_double_entrieslist_with_firstlastname_from_uploadfileNIU(data_list):
    # function returns list of student tuples with (idnumber, lastname, firstname) that occur multiple times in data_list

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  get_double_entrieslist_with_firstlastname_from_uploadfileNIU  -----')

    double_entrieslist = []
    # student_list is list of all students in data_list. It has format: tuple (idnumber, lastname, firstsname)
    student_list = []
    for data_dict in data_list:
        id_number = data_dict.get('idnumber')
        idnumber_nodots_stripped = id_number.replace('.', '').strip()  if id_number else ''

        last_name = data_dict.get('lastname')
        last_name_stripped = last_name.strip() if last_name else ''

        first_name = data_dict.get('firstname')
        first_name_stripped = first_name.strip() if first_name else ''

        student_tuple = (idnumber_nodots_stripped, last_name_stripped, first_name_stripped)

        found = False
        if student_list:
            for item in student_list:
                if item == student_tuple:
                    found = True
                    if student_tuple not in double_entrieslist:
                        double_entrieslist.append(student_tuple)
                    break
        if not found:
            student_list.append(student_tuple)

        if logging_on:
            logger.debug('student_tuple: ' + str(student_tuple))
            logger.debug('student_list: ' + str(student_list))
            logger.debug('double_entrieslist: ' + str(double_entrieslist))
    return double_entrieslist


# ========  validate_double_entries_in_uploadfile  ======= PR2021-07-17 PR2022-06-25
def validate_double_entries_in_uploadfile(caption, lookup_value, double_entrieslist, error_list):
    has_error = False
    if lookup_value and double_entrieslist:
        if lookup_value in double_entrieslist:
            has_error = True
            error_list.append(str(_("%(cpt)s '%(val)s' is found multiple times in this upload file.") \
                      % {'cpt': caption, 'val': lookup_value}))
    return has_error


# ========  validate_student_name_length  ======= PR2021-06-19 PR2021-09-10
def validate_student_name_length(lastname_stripped, firstname_stripped, prefix_stripped, error_list):

    has_error = False

    if not lastname_stripped:
        has_error = True
        error_list.append(_('%(cpt)s cannot be blank.') % {'cpt': _("The last name")})
    elif len(lastname_stripped) > c.MAX_LENGTH_FIRSTLASTNAME:
        has_error = True
        error_list.append(_("%(fld)s '%(val)s' is too long, maximum %(max)s characters.") \
                    % {'fld': _("The last name"), 'val': lastname_stripped, 'max': c.MAX_LENGTH_FIRSTLASTNAME})

    if not firstname_stripped:
        has_error = True
        error_list.append(_('%(cpt)s cannot be blank.') % {'cpt': _("The first name")})
    elif len(firstname_stripped) > c.MAX_LENGTH_FIRSTLASTNAME:
        has_error = True
        error_list.append(_("%(fld)s '%(val)s' is too long, maximum %(max)s characters.") \
                    % {'fld': _("The first name"), 'val': firstname_stripped, 'max': c.MAX_LENGTH_FIRSTLASTNAME})

    if len(prefix_stripped) > c.MAX_LENGTH_10:
        has_error = True
        error_list.append(_("%(fld)s '%(val)s' is too long, maximum %(max)s characters.") \
                          % {'fld': _("The prefix"), 'val': prefix_stripped, 'max': c.MAX_LENGTH_10})

    return has_error
# - end of validate_student_name_length


# ========  validate_length  ======= PR2021-08-05

def validate_length(caption, input_value, max_length, blank_allowed):
    #  PR2021-08-05 PR2022-06-29
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------- validate_length ----------- ')

    msg_err = None
    if not input_value:
        if not blank_allowed:
            msg_err = _('%(cpt)s cannot be blank.') % {'cpt': caption}

    elif max_length and len(input_value) > max_length:
        msg_err = _("%(cpt)s '%(val)s' is too long, maximum %(max)s characters.") \
                    % {'cpt': caption, 'val': input_value, 'max': max_length}

    if logging_on:
        logger.debug('msg_err: ' + str(msg_err))

    return msg_err
# - end of validate_length


def validate_gender(value):
    # validate gender, convert to string 'M' or 'V' PR2019-02-18
    clean_gender = c.GENDER_NONE
    msg_text = None
    if value:
        valid = False
        if len(value) == 1:
            value_upper = value.upper()
            if value_upper == 'M': # was if value_upper in ('M', 'F',):
                clean_gender = c.GENDER_MALE
                valid = True
            elif value_upper in ('V', 'F',):
                clean_gender = c.GENDER_FEMALE
                valid = True
        if not valid:
            msg_text = _('Gender \'"%s"\' is not allowed.' % value)
    return clean_gender, msg_text


# Not in use, maybe can be used for warning

# don't check if the amount of re-examinations equals or exceeds the maximum
#   students that have been sick may do multiple reex
#   was: if not err_list:

def validate_reex_count(studsubj_instance, si_dict):  # PR2021-12-19
    err_list = []
    max_reex = si_dict.get('scheme_max_reex', 1)



    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- validate_reex_count -------')
        logger.debug('max_reex: ' + str(max_reex))

    # Note: Students that have been sick may do more reex
    # instead of blocking, give flag when reex amount exceeds

    reex_count = stud_mod.Studentsubject.objects.filter(
        student=studsubj_instance.student,
        has_reex=True
    ).count()

    if reex_count >= max_reex:
        is_are = _('is') if max_reex == 1 else _('are')
        caption = _('Re-examination') if max_reex == 1 else _('Re-examinations')
        err_list.append(_("The candidate already has %(val)s %(cpt)s, only %(max)s %(is_are)s allowed.") \
                    % {'val': str(reex_count), 'cpt': str(caption).lower(), 'is_are': is_are, 'max': str(max_reex)})

    return err_list
# function checks if the amount of re-examination equals or exceeds the maximum


def validate_studsubj_sr_allowed(si_dict):  # PR2021-12-25
    err_list = []

    if not si_dict.get('ey_sr_allowed', False):
        err_list.append(str(_('Re-examinations of the school exam are not allowed this exam year.')))
    elif not si_dict.get('sr_allowed', False):
        err_list.append(str(_('Re-examinations of the school exam are not allowed for this subject.')))
    elif not si_dict.get('weight_se', 0):
        caption = _('Re-examination school exam')
        err_list.append(str(_('The %(se_ce_cpt)s weighing of this subject is zero.') % {'se_ce_cpt': 'SE'}))
        err_list.append(str(_('You cannot enter a %(item_str)s.') % {'item_str': str(caption).lower()}))

    return err_list
# --- end of validate_studsubj_sr_allowed


def validate_studsubj_pws_title_subjects_length(field, value):
    # PR2022-06-25
    # check if title or subjects of assignments fits on gradelist
    # uses reportlab stringWidth to calculate width of tekst in points, convert to mm (1 point = 1/72 inch)
    err_list = []
    if field == 'pws_title':
        max_width_mm = c.GRADELIST_PWS_TITLE_MAX_LENGTH_MM
        caption = 'the title'
    elif field == 'pws_subjects':
        max_width_mm = c.GRADELIST_PWS_TITLE_MAX_LENGTH_MM
        caption = 'the subjects'
    else:
        max_width_mm = None
        caption = ''

    if value and max_width_mm:
        value_strip = value.strip()
        if value_strip:
            value_width = stringWidth(value_strip, 'Times-Roman', 10)
            value_width_roundup_mm = math.ceil(value_width / 72 * 25.4)

            if value_width_roundup_mm > max_width_mm:
                err_list.append(str(_('The length of %(cpt)s of the assignment is %(val)s mm.')
                                    % {'cpt': caption, 'val': str(value_width_roundup_mm)}))
                err_list.append(str(_('The maximum length is %(max)s mm.') % {'max': str(max_width_mm)}))

    return err_list
# --- end of validate_studsubj_pws_title_subjects_length


def validate_studsubj_add_reex_reex03_allowed(field, si_dict):  # PR2021-12-18
    err_list = []
    if field in ['has_reex', 'has_reex03']:
        if si_dict.get('no_centralexam', False):
            err_list.append(str(_('This exam year has no central exams.')))
        else:
            if field == 'has_reex03' and si_dict.get('ey_no_thirdperiod', False):
                err_list.append(str(_('This exam year has no third exam period.')))
            elif field == 'has_reex03' and si_dict.get('no_thirdperiod', False):
                err_list.append(str(_('This subject has no third exam period.')))
            elif not si_dict.get('weight_ce', 0):
                #caption = _('Re-examination 3rd period') if field == 'has_reex03' else _('Re-examination')
                #err_list.append(
                #    str(_('The %(se_ce_cpt)s weighing of this subject is zero.') % {'se_ce_cpt': 'CE'}))
                #err_list.append(str(_('You cannot enter a %(item_str)s.') % {'item_str': str(caption).lower()}))
                err_list.append(str(_('This subject has no central exam.')))

    return err_list
# --- end of validate_studsubj_add_reex_reex03_allowed


def validate_thumbrule_allowed(studsubj_instance):  # PR2022-06-07
    # from letter minister MinOnd 22 feb 2022:
    # thumbrule is allowed:
    # - in only 1 subject
    # - only Havo Vwo
    # - not in core subjects
    # - only when they did the full exam (i.e. no exemptions)
    # - combi grade can have thumbrule, not individual exams

    # SXM

    # Option for all final exam students not to include the final mark of one subject when
    # determining the final results (duimregel). This subject may not be a core subject.

    # WARNING : calc_result uses schemeitem.thumb_rule + studsubj.is_thumbrule
    # must also set thumb_rule in schemeitem

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- validate_thumbrule_allowed -------')
        logger.debug('studsubj_instance: ' + str(studsubj_instance))
    err_list = []
# sxm has different rules
    is_sxm_student = studsubj_instance.student.school.examyear.country.abbrev = 'Sxm'
    if is_sxm_student:
# check if there is already a subject with thumbrule
        has_thumbrule_nocombi = stud_mod.Studentsubject.objects.filter(
            student=studsubj_instance.student,
            is_thumbrule=True,
            schemeitem__is_combi=False,
            tobedeleted=False
        ).exists()
        has_thumbrule_combi = stud_mod.Studentsubject.objects.filter(
            student=studsubj_instance.student,
            is_thumbrule=True,
            schemeitem__is_combi=True,
            tobedeleted=False
        ).exists()
        if has_thumbrule_nocombi or has_thumbrule_combi:
            err_list.append(str(_('This candidate already has a subject with the thumb rule.')))
            err_list.append(str(_('The thumbrule can only be applied to one subject.')))
    else:
# - only when Havo / Vwo
        depbase_code = studsubj_instance.student.department.base.code
        if depbase_code != 'Havo' and depbase_code != 'Vwo':
            err_list.append(str(_('Thumb rule is not applicable in Vsbo.')))
    # - not in core subjects
        elif studsubj_instance.schemeitem.is_core_subject:
            err_list.append(str(_('Thumb rule is not applicable to core subjects.')))
        else:
    # - not when there are exemptions
            # PR2022-06-15 this is removed from the final MB
            # was:
            #has_exemptions = stud_mod.Studentsubject.objects.filter(
            #    student=studsubj_instance.student,
            #    has_exemption=True,
            #    tobedeleted=False
            #).exists()
            #if has_exemptions:
            #    err_list.append(str(_('Thumb rule is only applicable when the candidate has taken a full exam.')))
            #    err_list.append(str(_('This candidate has exemptions, therefore the thumbrule cannot be applied.')))
            #else:

# check if there is already a subject with thumbrule
            has_thumbrule_nocombi = stud_mod.Studentsubject.objects.filter(
                student=studsubj_instance.student,
                is_thumbrule=True,
                schemeitem__is_combi=False,
                tobedeleted=False
            ).exists()
            has_thumbrule_combi = stud_mod.Studentsubject.objects.filter(
                student=studsubj_instance.student,
                is_thumbrule=True,
                schemeitem__is_combi=True,
                tobedeleted=False
            ).exists()
            if has_thumbrule_nocombi or has_thumbrule_combi:
                err_list.append(str(_('This candidate already has a subject with the thumb rule.')))
                err_list.append(str(_('The thumbrule can only be applied to one subject.')))

    return err_list
# --- end of validate_thumbrule_allowed


def validate_extra_nocount_allowed(studsubj_instance):  # PR2022-06-08

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- validate_thumbrule_allowed -------')
        logger.debug('studsubj_instance: ' + str(studsubj_instance))
    err_list = []
    # when sxm has different rules
    # id_sxm_student = studsubj_instance.student.school.examyear.country.abbrev = 'Sxm'
    depbase_code = studsubj_instance.student.department.base.code
    if depbase_code != 'Vsbo':
# - only when Vsbo
# PR2022-06-09 Ricahrd Westerink: also for havo Vwo, is correct: was in old AWP also allowed
        pass
        # was: err_list.append(str(_('This option is not applicable in %(cpt)s.') %{'cpt': depbase_code}))
# - only in TKL
    elif not studsubj_instance.student.level:
        err_list.append(str(_('Candidate has no learning path.')))
# - only in TKL
    elif studsubj_instance.student.level.abbrev != 'TKL':
        err_list.append(str(_('This option is not applicable in %(cpt)s.') %{'cpt': studsubj_instance.student.level.abbrev}))
# - not when mandatory subject
    elif studsubj_instance.schemeitem.is_mand_subj:
        err_list.append(str(_('This is a mandatory subject.')))
        err_list.append(str(_('This option is not allowed when a subject is mandatory.')))

# - only for subjects in 'vrije deel / overig vak'
    # TODO PR2022-06-09 Kevin Weert: restrictie Overig vak tijdelijk weggehaald, totdat je kunt switchen van karakter zonder cijfers kwijt te raken
    #elif not studsubj_instance.schemeitem.subjecttype:
    #    err_list.append(str(_("Subject has no 'Character'.")))
    #elif not studsubj_instance.schemeitem.subjecttype.base.code == 'vrd':
    #    err_list.append(str(_("This subject has the character '%(cpt)s'.") %{'cpt': studsubj_instance.schemeitem.subjecttype.base.name}))
    #    err_list.append(str(_("This option is only allowed when a subject has the character 'Overig vak'.")))
    else:
# - only one allowed
        has_extra_nocount = stud_mod.Studentsubject.objects.filter(
            student=studsubj_instance.student,
            is_extra_nocount=True,
            tobedeleted=False)
        if has_extra_nocount:
            err_list.append(str(_('Only one subject can be set as extra subject that does not count towards the result.')))

    return err_list
# --- end of validate_extra_nocount_allowed