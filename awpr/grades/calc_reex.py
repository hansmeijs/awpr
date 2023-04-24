
# PR2021-11-19

from django.contrib.auth.decorators import login_required
from django.db import connection

from django.http import HttpResponse
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, pgettext_lazy, gettext_lazy as _
from django.views.generic import View

from decimal import Decimal
from accounts import views as acc_view
from accounts import  permits as acc_prm

from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import downloads as dl

from grades import calculations as grade_calc
from grades import calc_score as calc_score
from grades import calc_results as calc_res
from students import functions as stud_fnc
from students import views as stud_view


import json

import logging
logger = logging.getLogger(__name__)


@method_decorator([login_required], name='dispatch')
class CalcReexView(View):  # PR2023-04-04

    def post(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= CalcReexView ============= ')

        update_wrap = {}
        messages = []
        msg_html = None

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = acc_prm.get_permit_of_this_page('page_result', 'calc_results', request)

        # note: this is part of get_permit_crud_of_this_page:
        #       'if has_permit and request.user and request.user.country and request.user.schoolbase:'
        if not has_permit:
            msg_html = acc_prm.err_html_no_permit(_('to calculate re-examinations'))
        else:

# - get upload_dict from request.POST
            # upload_dict = json.loads(list) if list != '-' else {}
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))

# ----- get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(
                        request=request,
                        skip_same_school_clause= request.user.role in (c.ROLE_032_INSP, c.ROLE_064_ADMIN)
                    )

# - exit when examyear or school is locked, not published etc
                if not may_edit:
                    msg_html = acc_prm.msghtml_from_msglist_with_border(msg_list, c.HTMLCLASS_border_bg_invalid)
                else:
                    sel_lvlbase_pk, sel_sctbase_pkNIU = acc_view.get_selected_lvlbase_sctbase_from_usersetting(request)
                    student_pk_list = upload_dict.get('student_pk_list')

# +++++ calc_batch_student_reex_result ++++++++++++++++++++
                    log_list, single_student_name = calc_batch_student_reex_result(
                        sel_examyear=sel_examyear,
                        sel_school=sel_school,
                        sel_department=sel_department,
                        student_pk_list=student_pk_list,
                        sel_lvlbase_pk=sel_lvlbase_pk,
                        user_lang=user_lang
                    )
                    update_wrap['log_list'] = log_list
                    update_wrap['log_student_name'] = single_student_name

                    update_wrap['updated_student_rows'], error_dict = stud_view.create_student_rows(
                        request=request,
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_school.base,
                        sel_depbase=sel_department.base,
                        append_dict={})


# - return html with log_list
        if messages:
            update_wrap['messages'] = messages
# - return html with log_list
        if msg_html:
            update_wrap['msg_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of CalcResultsView


def calc_batch_student_reex_result(sel_examyear, sel_school, sel_department, student_pk_list, sel_lvlbase_pk, user_lang):
    # PR2023-04-04
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------------  calc_batch_student_reex_result  ---------------')
        logger.debug('    sel_examyear: ' + str(sel_examyear))
        logger.debug('    sel_school: ' + str(sel_school))
        logger.debug('    sel_department: ' + str(sel_department))
        logger.debug('    student_pk_list: ' + str(student_pk_list))
        logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))

# - get_scheme_dict
    # is part of student_dict

# - get_schemeitems_dict
    # is part of student_dict

# +++  get_students_with_grades_dictlist
    student_dictlist = calcreex_get_students_with_final_grades(
        examyear=sel_examyear,
        school=sel_school,
        department=sel_department,
        student_pk_list=student_pk_list,
        lvlbase_pk=sel_lvlbase_pk
    )

# - create log_list with header
    log_list = log_list_header(sel_school, sel_department, sel_examyear, user_lang)
    sql_studsubj_list = []
    sql_student_list = []

# loop through student_dictlist - ordered list of students with grades
    for student_dict in student_dictlist:
        calcreex_student_reex_result(sel_examyear, sel_department, student_dict, log_list,
                            sql_studsubj_list, sql_student_list)

    # - save calculated fields in studsubj
    #if sql_studsubj_list:
    #    save_studsubj_batch(sql_studsubj_list)

    # - save calculated fields in student
    #if sql_student_list:
    #    save_student_batch(sql_student_list)

    if not student_dictlist:
        log_list.append(''.join((c.STRING_SPACE_05, str(_('There are no candidates.')))))

    log_list.append(c.STRING_SINGLELINE_80)

    single_student_name = student_dictlist[0].get('fullname') if len(student_dictlist) == 1 else None

    """
    '1. print header AWPlog Herexamenberekening
    strLogFileName = "AWPlog Herexamenberekening " & pblAfd.CurSchoolnaam & " " & IIf(pblAfd.CurHasMultipleAfdelingen,
                                                                                      Replace(pblAfd.CurAfkAfdeling,
                                                                                              ".",
                                                                              "",,, vbTextCompare) & " ", "") & Format(
        Date, "dd mmm yyyy") & " " & Format(Time(), "hh.mm") & " uur.txt"
    strLogPath = pblDirectoryRoot & conDirectoryLogfilesDefault & "\" & strLogFileName

    strLogMsg = " "
    Call
    AppendLogFile(strLogPath, strLogMsg, True)
    strLogMsg = "========================================================================================================================"
    Call
    AppendLogFile(strLogPath, strLogMsg, True)
    strLogMsg = "LOG Herexamenberekening " & pblAfd.CurAfkAfdeling & " - " & Now()
    Call
    AppendLogFile(strLogPath, strLogMsg, True)
    strLogMsg = "========================================================================================================================"
    Call
    AppendLogFile(strLogPath, strLogMsg, True)
    strLogMsg = " "
    Call
    AppendLogFile(strLogPath, strLogMsg, True)

    strLogMsg = "AWP heeft de herexamenvakken berekend en het cijfer dat minimaal behaald moet worden om te slagen. " & vbCrLf & _
    "Het vak met een > ervoor heeft het laagst benodigde herexamencijfer. "

    Call
    AppendLogFile(strLogPath, strLogMsg, True)
    """
    return log_list, single_student_name
# end of calc_batch_student_reex_result


def calcreex_get_students_with_final_grades(examyear, school, department, student_pk_list, lvlbase_pk=None):
    # PR2023-04-06 PR2023-04-22

    # NOTE: don't forget to filter studsubj.deleted = False and grade.deleted = False!! PR2021-03-15
    # TODO grades that are not published are only visible when 'same_school' (or not??)
    # also add grades of each period

    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- calcreex_get_students_with_final_grades -----')
        logger.debug('student_pk_list: ' + str(student_pk_list))

    # values of sel_layout are:"none", "level", "class", "cluster"
    # "none" or None: all students of subject on one form
    # "level:" seperate form for each leeerweg
    #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
    #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

    # fields in student_field_list and studsubj_field_list are added to student_dict
    student_field_list = ('stud_id', # 'lastname', 'firstname', 'prefix',
                        'examnumber', 'classname',
                        'iseveningstudent', 'islexstudent', 'islexschool', 'bis_exam', 'partial_exam', 'withdrawn',
                        'school_name', 'school_code', 'depbase_code', 'lvlbase_code', 'examyear_code',
                        'scheme_id', 'dep_abbrev', 'level_req', 'lvl_name', 'sct_name',
                        'rule_avg_pece_sufficient', 'rule_avg_pece_notatevlex',
                        'rule_core_sufficient', 'rule_core_notatevlex'
                         )

    studsubj_field_list = ('subject_id', 'schemeitem_id',
                           'is_extra_nocount', 'is_extra_counts', 'exemption_year',
                           'gl_sesrgrade', 'gl_pecegrade', 'gl_finalgrade',
                           'gl_ni_se', 'gl_ni_sr', 'gl_ni_pe', 'gl_ni_ce', 'gl_examperiod',
                           'is_extra_nocount', 'is_extra_counts', 'is_thumbrule', 'has_exemption', 'has_sr', 'has_reex', 'has_reex03',
                           'gradetype', 'weight_se', 'weight_ce',  'multiplier', 'is_combi',
                           'is_core_subject', 'rule_grade_sufficient', 'rule_gradesuff_notatevlex', 'thumb_rule', 'no_ce_years',
                           'subj_name_nl', 'subj_code', 'subjtype_abbrev'
                           )

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk,
                'student_pk_list': student_pk_list}

    sql_list = ["SELECT stud.id AS stud_id, studsubj.id AS studsubj_id,",

                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, stud.classname,",
                "stud.iseveningstudent, stud.islexstudent, stud.bis_exam, stud.partial_exam, stud.withdrawn,",
                "stud.exemption_count, stud.sr_count, stud.reex_count, stud.reex03_count, stud.thumbrule_count,",

                "school.name AS school_name, school.islexschool,",
                "sb.code AS school_code, depbase.code AS depbase_code, lvlbase.code AS lvlbase_code,",
                "ey.code AS examyear_code,",

                "dep.id AS dep_id, lvl.id AS lvl_id, sct.id AS sct_id, stud.scheme_id AS scheme_id,",
                "dep.name AS dep_name, dep.abbrev AS dep_abbrev, dep.level_req, dep.has_profiel,",
                "lvl.name AS lvl_name, sct.name AS sct_name,",

                "studsubj.schemeitem_id,",
                "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.exemption_year,",
                "studsubj.gradelist_sesrgrade AS gl_sesrgrade, studsubj.gradelist_pecegrade AS gl_pecegrade,",
                "studsubj.gradelist_finalgrade AS gl_finalgrade,",
                "studsubj.gl_ni_se, studsubj.gl_ni_sr, studsubj.gl_ni_pe, studsubj.gl_ni_ce, studsubj.gl_examperiod,"
                "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_thumbrule,",
                "studsubj.has_exemption, studsubj.has_sr, studsubj.has_reex, studsubj.has_reex03,",

                "si.gradetype, si.weight_se, si.weight_ce,  si.multiplier, si.is_combi,",
                "si.is_core_subject, si.is_mvt, si.is_wisk, si.sr_allowed, si.no_ce_years, si.thumb_rule,",
                "si.rule_grade_sufficient, si.rule_gradesuff_notatevlex,",

                "scheme.rule_avg_pece_sufficient, scheme.rule_avg_pece_notatevlex,",
                "scheme.rule_core_sufficient, scheme.rule_core_notatevlex,",

                "subj.id AS subject_id, subj.base_id AS subjbase_id, subj.name_nl AS subj_name_nl, subjbase.code AS subj_code,",
                "subjtype.abbrev AS subjtype_abbrev",

                "FROM students_studentsubject AS studsubj",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "INNER JOIN subjects_subjecttype AS subjtype ON (subjtype.id = si.subjecttype_id)",

                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

                # PR2023-04-22 link scheme to student instead of schemitem,
                # must check later if  stud.scheme_id is same as si.scheme_id
                "INNER JOIN subjects_scheme AS scheme ON (scheme.id = stud.scheme_id)",

                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",

                "WHERE NOT stud.tobedeleted AND NOT stud.deleted AND NOT studsubj.tobedeleted AND NOT studsubj.deleted",
                "AND ey.id = %(ey_id)s::INT AND school.id = %(sch_id)s::INT AND dep.id = %(dep_id)s::INT",
                "AND stud.result = " + str(c.RESULT_FAILED) + "::INT"
                ]

    if student_pk_list:
        sql_keys['student_pk_arr'] = student_pk_list
        sql_list.append("AND stud.id IN ( SELECT UNNEST( %(student_pk_arr)s::INT[]))")
    else:
        if lvlbase_pk:
            sql_keys['lvlbase_pk'] = lvlbase_pk
            sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

    sql_list.append("ORDER BY stud.lastname, stud.firstname")

    sql = ' '.join(sql_list)
    if logging_on and False:
        for sql_txt in sql_list:
            logger.debug(' > ' + sql_txt)

    grade_dictlist_sorted = []
    cascade_dict = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

        if rows:
            for row in rows:
                stud_id = row.get('stud_id')
                gl_examperiod = row.get('gl_examperiod') or 1
                is_combi = row.get('is_combi') or False
                gradetype = row.get('gradetype') or False
                is_core = row.get('is_core') or False
                is_extra_nocount = row.get('is_extra_nocount') or False
                is_thumbrule = row.get('is_thumbrule') or False

    # - multiplier =1, except when sectorprogramma PBL, then it is 2 in Cur
                multiplier = row.get('multiplier') or 1

                if stud_id not in cascade_dict:
                    full_name = stud_fnc.get_full_name(row.get('lastname'), row.get('firstname'), row.get('prefix'))

                    # stud_dict = {'fullname': full_name, 'result': [], }
                    stud_dict = {'fullname': full_name,
                                 'c_subj': 0, 'c_exemption': 0, 'c_sr': 0, 'c_reex': 0, 'c_reex03': 0,
                                 'c_extra_nocount': 0, 'c_extra_counts': 0, 'c_thumbrule': 0,
                                 # totals are stored as Decimal datatype, counts are stored as integer
                                 'c_ce': 0, 't_ce': '0', 'avg_ce': None, 'avg_ce_info': {}, 'avg_pece_detail': '',
                                 'c_final': 0, 't_final': '0', 'avg_final': None, 'avg_final_info': {}, 'avg_final_detail': '',
                                 'c_combi': 0, 't_combi': '0', 'avg_combi': None, 'combi_info': {}, 'combi_detail': '',
                                 'c3': 0, 'c4': 0, 'c5': 0, 'c6': 0, 'c7': 0,
                                 'core4': 0, 'core5': 0,
                                 'r_index': 0, 'r_info': {'combi': {}},
                                 'thumbrule_combi': False,
                                 'subj_with_ce': {},

                                 'test_r_index': 0, 'test_r_info': {'combi': {}}
                                 }

# add values of student fields to student_dict
                    for field in student_field_list:
                        value = row.get(field)
                        if value is not None or True:
                            stud_dict[field] = value

                    # PR 2022-06-09 debug: count exemp, reex, reex3
                    # id safer than getting it from student row
                    cascade_dict[stud_id] = stud_dict

    # - add studsubj_dict dict
                student_dict = cascade_dict.get(stud_id)
                if student_dict:
                    # put studsubjects in dict with key: 'studsubj_id'
                    studsubj_pk = row.get('studsubj_id')

                    if studsubj_pk not in student_dict:

    # - add multiplier to count dict (multiplier =1, except when sectorprogramma PBL)
                        student_dict['c_subj'] = multiplier + (student_dict.get('c_subj') or 0)

    # - add subj_code: subject_id to student_dict['subj_with_ce']. Used to loop through subjects with ce
                        subj_code = row.get('subj_code')
                        weight_ce = row.get('weight_ce')
                        if weight_ce > 0 and subj_code not in  student_dict['subj_with_ce']:
                            student_dict['subj_with_ce'][subj_code] = row.get('subject_id')

                        studsubj_dict = {}
                        for field in studsubj_field_list:

    # put values of studsubj_field_list fields in studsubj_dict
                            studsubj_dict[field] = row.get(field)

    # count 'has_exemption', 'has_sr', 'has_reex', 'has_reex03'
                            if field in ('has_exemption', 'has_sr', 'has_reex', 'has_reex03'):
                                if row.get(field):
                                    studsubj_dict[field] = True

                                    key_str = 'c_' + field[4:]
                                    student_dict[key_str] = 1 + (student_dict.get(key_str) or 0)

    # count 'is_extra_nocount'
                            elif field == 'is_extra_nocount':
                                if row.get('is_extra_nocount'):
                                    student_dict['c_extra_nocount'] = 1 + (student_dict.get('c_extra_nocount') or 0)
                                    studsubj_dict['is_extra_nocount'] = True

    # count 'is_extra_counts'
                            elif field == 'is_extra_counts':
                                if row.get('is_extra_counts'):
                                    student_dict['c_extra_counts'] = 1 + (student_dict.get('c_extra_counts') or 0)
                                    studsubj_dict['is_extra_counts'] = True

    # count 'is_thumbrule'
                            elif field == 'is_thumbrule':
                                # combi thumbrule counts as one, put thumbrule_combi = True in student_dict if any combi has thumbrule
                                if row.get('is_thumbrule'):
                                    if is_combi:
                                        student_dict['thumbrule_combi'] = True
                                    else:
                                        student_dict['c_thumbrule'] = 1 + (student_dict.get('c_thumbrule') or 0)
                                    studsubj_dict['is_thumbrule'] = True

                            elif field == 'gl_pecegrade':

     # - add gl_pecegrade, only when weight_ce > 0 and not is_combi
                                if weight_ce and not is_combi:
                                    gl_pecegrade = row.get('gl_pecegrade') or '0'
                                    # skip ovg ce grade, (ovg should not occur in ce)
                                    if gl_pecegrade.replace('.', '').isnumeric():

    # - add multiplier to 'c_ce' (multiplier =1, except when sectorprogramma PBL)
                                        student_dict['c_ce'] = multiplier + (student_dict.get('c_ce') or 0)

    # - add gl_pecegrade * multiplier to t_combi or t_final (multiplier =1, except when sectorprogramma PBL)
                                        student_dict['t_ce'] = Decimal(gl_pecegrade) * Decimal(str(multiplier)) +  Decimal(student_dict.get('t_ce'))

    # - add subj_code and grade to info_pece:
                                        gl_pecegrade_str = gl_pecegrade.replace('.', '')
                                        # - add '2x','vr','h','h3' to grade
                                        gl_pecegrade_extension = calc_res.get_gradeinfo_extension(multiplier, gl_examperiod)
                                        if gl_pecegrade_extension:
                                            gl_pecegrade_str += gl_pecegrade_extension

                                        student_dict['avg_pece_detail'] += ''.join((' ', subj_code, ':', gl_pecegrade_str))

                            elif field == 'gl_finalgrade':
                                # add final grade to total, only when isnumeric.
                                gl_finalgrade = row.get('gl_finalgrade') or '0'
                                # '5.6'.isnumeric() = False, therefore remove dot (final grade ony has integer or ovg, let it stay)
                                if gl_finalgrade.replace('.', '').isnumeric():
                                    # add finalgrade to total finalgrade from dict and put new total in dict

    # - add gl_finalgrade * multiplier to t_combi or t_final (multiplier =1, except when sectorprogramma PBL)
                                    key_total = 't_combi' if is_combi else 't_final'
                                    student_dict[key_total] = Decimal(gl_finalgrade) * Decimal(str(multiplier)) + Decimal(student_dict.get(key_total))

    # - add multiplier to count dict (multiplier =1, except when sectorprogramma PBL)
                                    key_count = 'c_combi' if is_combi else 'c_final'
                                    student_dict[key_count] = multiplier + (student_dict.get(key_count) or 0)

    # - add gl_finalgrade * multiplier to c_3
                                    calcreex_count_final_3457_core(student_dict, gl_finalgrade, gradetype,
                                           is_combi, is_core, multiplier, is_extra_nocount, is_thumbrule)

    # - add subj_code and final grade to info_pece:
                                    gl_finalgrade_str = gl_finalgrade.replace('.', ',') if gl_finalgrade else '-'

                                    # - add '2x','vr','h','h3' to grade
                                    gradeinfo_extension = calc_res.get_gradeinfo_extension(multiplier, gl_examperiod)
                                    if gradeinfo_extension:
                                        gl_finalgrade_str += gradeinfo_extension

                                    student_dict['avg_final_detail'] += ''.join((' ', subj_code, ':', str(gl_finalgrade_str)))

                        student_dict[studsubj_pk] = studsubj_dict

                        if logging_on and False:
                            logger.debug('    studsubj_dict: ' + str(studsubj_dict))

            # convert dict to sorted dictlist
            grade_list = list(cascade_dict.values())

            # sort list to sorted dictlist
            # PR2021-11-15 from https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
            if grade_list:
                grade_dictlist_sorted = sorted(grade_list, key=lambda d: d['fullname'])

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return grade_dictlist_sorted
# - end of calcreex_get_students_with_final_grades


def calcreex_student_reex_result(examyear, department, student_dict, log_list, sql_studsubj_list, sql_student_list):
    # PR2023-04-22
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------------  calcreex_student_reex_result  ---------------')


    """
    student_dict: {'fullname': 'Fonseca, Timothy Justin', 
    student_dict: {'fullname': 'Fonseca, Timothy Justin', 
        'c_subj': 9, 'c_exemption': 0, 'c_sr': 0, 'c_reex': 2, 'c_reex03': 0, 'c_extra_nocount': 0, 'c_extra_counts': 0, 'c_thumbrule': 0, 
        'c_ce': 7, 't_ce': Decimal('36.4'), 
        'avg_ce': Decimal('5.2'), 'avg_ce_info': 'Gemiddeld CE-cijfer: 5,2 (36,4/7) ', 'avg_pece_detail': ' pa:52 frtl:47 netl:54 entl:83 gs:55(h) wa:34 if:39', 
        'c_final': 8, 't_final': Decimal('41'), 'avg_final': Decimal('5.125'), 
        'avg_final_info': 'Gemiddeld eindcijfer: 5.1 (41/8) ', 
        'avg_final_detail': ' pa:5 frtl:5 asw:5 pws:6 netl:5 entl:7 gs:5(h) wa:4 if:4', 
        'c_combi': 2, 't_combi': Decimal('11'), 'avg_combi': None, 'combi_info': 'Combinatiecijfer: 6 (-/-) ', 'combi_detail': '', 
        'c3': 0, 'c4': 4, 'c5': 8, 'c6': 1, 'c7': 2, 
        'core4': 1, 'core5': 1, 
        'r_index': 2, 
        'r_info': {
            'combi': {}, 
            'cnt3457': '4 vieren.', 'core45': '1 vier en 1 vijf in kernvakken.', 
            'avgce55': 'Gemiddeld CE-cijfer is 5,2, moet onafgerond 5,5 of hoger zijn.'
        }, 
        'thumbrule_combi': False, 
        'subj_with_ce': {'pa': 118, 'frtl': 160, 'netl': 165, 'entl': 167, 'gs': 145, 'wa': 149, 'if': 146}, 
        'test_r_index': 0, 'test_r_info': {'combi': {}}, 
        'stud_id': 4960, 'examnumber': '107', 'classname': '5', 
        'iseveningstudent': False, 'islexstudent': False, 'islexschool': False, 'bis_exam': False, 'partial_exam': False, 
        'withdrawn': False, 
        'school_name': 'Abel Tasman College', 'school_code': 'CUR13', 'depbase_code': 'Havo', 'lvlbase_code': None, 
        'examyear_code': 2022, 'scheme_id': 81, 'dep_abbrev': 'H.A.V.O.', 
        'level_req': False, 'lvl_name': None, 'sct_name': 'Cultuur en Maatschappij', 
        'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 
        'rule_core_sufficient': True, 'rule_core_notatevlex': False, 
        
    """

    dep_level_req = department.level_req
    depbase_code = str(department.base.code).lower()
    depbase_is_vsbo = (depbase_code == 'vsbo')

    sr_allowed = examyear.sr_allowed
    no_practexam = examyear.no_practexam
    no_centralexam = examyear.no_centralexam

# - get isevlex and full name with (evening / lex student)
    scheme_error, isevlexstudent, partial_exam, withdrawn, full_name = calcreex_get_isevlex_isreex_fullname(student_dict)

# - get result rules from scheme and schemeitem
    rule_avg_pece_sufficient, rule_core_sufficient = \
        calcreex_get_rules_from_scheme(student_dict, isevlexstudent)

    """
    'A. Validate
        'a. exit if no student_id >> done in getting students
        'b. exit if locked >> done by may_edit in CalcResultsView.
        'c. exit if no scheme  >> done in this function
        TODO exit if student is tobedeleted
    """

# - student name header
    if log_list is not None:
        log_list_student_header(student_dict, full_name, log_list)

# - A.3c. skip when scheme not found, put err_msg in loglist
# PR2022-06-18 debug: msut give result 'no result, therefore don't skip student
    skip_student = False
    if scheme_error:
        skip_student = True
        if log_list is not None:
            log_list_add_scheme_notfound(dep_level_req, log_list)


    # student_dict is created in get_students_with_grades_dictlist
    # it also counts the number of grade_rows of exempttion, reex and reex_03 and puts it in 'c_ep4', 'c_ep2' and 'c_ep3'
    # later these will be saved stored in table student, fields exemption_count, reex_count and reex03_count
    exemption_count = student_dict.get('c_exem', 0)
    sr_count = student_dict.get('c_sr', 0)
    reex_count = student_dict.get('c_reex', 0)
    reex03_count = student_dict.get('c_reex03', 0)

    c_extra_nocount = student_dict.get('c_extra_nocount', 0)
    c_extra_counts = student_dict.get('c_extra_counts', 0)

    thumbrule_count = student_dict.get('c_thumbrule') or 0
    thumbrule_combi = student_dict.get('thumbrule_combi') or False

    if logging_on:
        logger.debug('    exemption_count: ' + str(exemption_count))
        logger.debug('    reex_count: ' + str(reex_count))

# - add number of sr, reex, reex03 to log_list
    # TODO add extra_nocount
    if log_list is not None:
        calc_res.log_list_reex_count(exemption_count, sr_count, reex_count, reex03_count, thumbrule_count, thumbrule_combi, log_list)


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# - loop through studsubjects from student
    has_subjects = False
    for studsubj_pk, studsubj_dict in student_dict.items():

    # - get info from schemeitems_dict
        # skip keys 'fullname' etc, only get studsubj_dict when key is integer, then it is a studsubj_pk
        if isinstance(studsubj_pk, int):
            has_subjects = True

# - get schemeitem_dict of this studsubj_dict
        # info of schemeitem is part of studsubj_dict

# - calc studsubj result
            calcreex_studsubj_result(studsubj_dict, student_dict, isevlexstudent, sr_allowed, no_practexam, log_list)

            # - put the max values that will appear on the gradelist back in studsubj, also max_use_exem
            #   done in calc_studsubj_result
            #   get_sql_studsubj_values(studsubj_pk, gl_sesr, gl_pece, gl_final, gl_use_exem, gl_ni_se, gl_ni_sr, gl_ni_pe, gl_ni_ce, gl_examperiod)

    if logging_on:
        logger.debug('    end of loop through studsubjects')
        logger.debug('    sql_studsubj_list: ' + str(sql_studsubj_list))

# - end of loop through studsubjects
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

# +++ calc_student_passedfailed:
    # - calculates combi grade for each examperiod and add it to final and count dict in student_ep_dict
    # - calculates passed / failed for each exam period (ep1, ep2, ep3)
    # - puts calculated result of the last examperiod in log_list

    calcreex_student_passedfailed(student_dict, rule_avg_pece_sufficient, rule_core_sufficient,
                              withdrawn, partial_exam, has_subjects, depbase_is_vsbo, log_list, sql_student_list)

    if logging_on:
        logger.debug('     sql_student_list: ' + str(sql_student_list))

    if not has_subjects and log_list is not None:
        log_list.append(''.join((c.STRING_SPACE_05, str(_('This candidate has no subjects.')))))
# - end of calcreex_student_reex_result


###############################
def calcreex_student_passedfailed(student_dict, rule_avg_pece_sufficient, rule_core_sufficient, withdrawn, partial_exam,
                              has_subjects, depbase_is_vsbo, log_list, sql_student_list):
    # PR2021-12-31 PR2022-06-04  PR2023-04-22
    # - calculate combi grade for each examperiod and add it to final and count dict in student_ep_dict
    # last_examperiod contains the grades that must pe put un the grade_list.
    # is reex03 when reex03 student, reex when reex student, firstperiod otherwise
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('--------- calcreex_student_passedfailed ---------------')
        logger.debug('>>>>>>>>>>>> student_dict: ' + str(student_dict))

    if logging_on:
        logger.debug('    withdrawn: ' + str(withdrawn) )
        logger.debug('    partial_exam: ' + str(partial_exam) )

# +++ calculate passed / failed for each exam period (ep1, ep2, ep3)
    # and put result back in student_ep_dict
    # - if no result because of no input: skip calculating result

    if withdrawn:
        student_dict['r_index'] = c.RESULT_WITHDRAWN
        if logging_on:
            logger.debug('     withdrawn: ' + str(withdrawn))
    elif partial_exam:
        # PR2022-06-10 Richard Westerink ATC: partial exam student has always 'No result' on gradelist
        student_dict['r_index'] = c.RESULT_NORESULT
    elif not has_subjects:
        student_dict['r_index'] = c.RESULT_NORESULT
    else:
        calcreex_combi_and_add_to_totals(student_dict)

        calcreex_pece_avg(student_dict)

        calcreex_final_avg(student_dict)

        result_no_input = calcreex_passfailed_noinput(student_dict)
        # student_dict['r_index'] = c.RESULT_NORESULT gets value in calcreex_passfailed_noinput
        if logging_on:
            logger.debug('     result_no_input: ' + str(result_no_input))

# - if no_input: create dict with key 'noresult' if it does not exist
        if not result_no_input:
            has_failed = False
            # calcreex_rule_issufficient is already called in subj loop
            # student_dict['r_index'] = c.RESULT_FAILED gets value in calc_passfailed
            if depbase_is_vsbo:
                has_failed_count6 = calcreex_passfailed_count6_vsbo(student_dict)
            else:
                has_failed_count6 = calcreex_passfailed_count6_havovwo(student_dict)
            if has_failed_count6:
                has_failed = True
            if logging_on:
                logger.debug('     has_failed_count6: ' + str(has_failed_count6))

            if rule_core_sufficient:

                # where is checked if notatevlex is included in rule_core_sufficient?
                # this happens in function get_rules_from_schemeitem:
                # it sets rule_core_sufficient to False when isevlexstudent = True and notatevlex = True

                failed_core = calc_passfailed_core_rule(student_dict)
                if failed_core:
                    has_failed = True
                if logging_on:
                    logger.debug('     failed_core: ' + str(failed_core))

            if rule_avg_pece_sufficient:

                # where is checked if notatevlex is included in rule_avg_pece_sufficient?
                # this happens in function get_rules_from_schemeitem:
                # it sets rule_core_sufficient to False when isevlexstudent = True and notatevlex = True

                failed_pece_avg = calc_passfailed_pece_avg_rule(student_dict)
                if failed_pece_avg:
                    has_failed = True
                if logging_on:
                    logger.debug('     failed_pece_avg: ' + str(failed_pece_avg))

            if not has_failed:
                student_dict['r_index'] = c.RESULT_PASSED

    if logging_on:
        logger.debug('student_dict: ' + str(student_dict))

    if logging_on:
        logger.debug('--------- end of loop through calc examperiods ')

    # put calculated result of the last examperiod in log_list
    # if is_reex_student: last_examperiod = 2, is_reex03_student: last_examperiod = 3, last_examperiod = 1 otherwise


    result_info_list, result_info_log_list = calcreex_add_result_to_log(student_dict,
                                                                    rule_avg_pece_sufficient, rule_core_sufficient, partial_exam)
    log_list.extend(result_info_log_list)

# - put result and grade info in sql_student_values
    sql_student_values = calcreex_get_sql_student_values(student_dict, result_info_list)

    if sql_student_values:
        sql_student_list.append(sql_student_values)
# - calcreex_student_passedfailed


def calcreex_passfailed_noinput(student_dict):  # PR2021-12-27 PR2022-01-04 PR2022-05-26
    # examperiod = ep1, ep2, ep3
    # noinput_dict: {1: {'sr': ['ne'], 'ce': ['ne', 'ec']}, 2: {'ce': ['ac']}, 3: {'ce': ['ac']}}
    #  - function returns 'no_input',
    #  - puts result_index = 0 in student_dict['r_index']
    #  -  puts info in student_dict['noin_info']
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('@@@@@@@@@@@@@@ -----  calcreex_passfailed_noinput  -----')
        logger.debug('     student_dict: ' + str(student_dict))
    """
    student_dict: {
        'ep': 1, 
        'final': {'sum': 48, 'cnt': 8, 'info': ' ne:5 pa:7(vr) en:6 wk:6 nask1:5 nask2:6 ta:7 combi:6', 'avg': '6.0', 
                    'result': 'Gemiddeld eindcijfer: 6.0 (48/8) '}, 
        'combi': {'sum': 19, 'cnt': 3, 'info': ' mm1:5 cav:8(vr) lo:6(vr)', 'final': 6, 
                    'result': 'Combinatiecijfer: 6 (19/3) '}, 
        'pece': {'sumX10': 372, 'cnt': 6, 'info': ' ne:4,1 en:6,2 wk:5,6 nask1:5,8 nask2:6,9 ta:8,6',  'avg': None, 
                    'result': 'Gemiddeld CE-cijfer: 6,2 (37,2/6) '}, 
        'count': {'c3': 0, 'c4': 0, 'c5': 2, 'c6': 4, 'c7': 2, 'core4': 0, 'core5': 0}}

    """
    no_input = False
    noinput_list = []

    noin_dict = student_dict.get('noin')
    if logging_on:
        logger.debug('noin_dict: ' + str(noin_dict))
        logger.debug('ni: ' + str(student_dict.get('ni')))
    """
    noin_dict: {
        'sr': ['ne', 'ac'], 
        'ce': ['ne'], 
        'vr': {'en': ['se', 'ce'], 'ec': ['se', 'ce'], 'mm12': ['se'], 'cav': ['se']}, 
        'se': ['mm1']}
    """

    if noin_dict:
        no_input = True

        # loop through tuple to get lines in right ord
        for key in ('vr', 'se', 'sr', 'ce', 'pe', 'h2', 'h3'):
            value = noin_dict.get(key)
            if value:
                if logging_on:
                    logger.debug( 'key: ' + str(key))
                    logger.debug( 'value: ' + str(value))

                # keys 'vr', 'pe', 'se', 'sr' 'ce', h2', 'h3' 'are used to create separate lines in noinput info
                caption = _('Exemption') if key == 'vr' else \
                                _('Practical exam') if key == 'pe' else \
                                _('School exam') if key == 'se' else \
                                _('Re-examination school exam') if key == 'sr' else \
                                _('Central exam') if key == 'ce' else \
                                _('Re-examination') if key == 'h2' else \
                                _('Re-examination 3rd period') if key == 'h3' else '-'
                noin_info_str = str(caption) + ': '

                if key == 'vr':
                    for subj_code, subvalue in value.items():
                        if logging_on:
                            logger.debug('     value:     ' + str(value))
                            # value:     {'en': ['se', 'ce'], 'ec': ['se', 'ce'], 'mm12': ['se'], 'cav': ['se']}
                            logger.debug('     subj_code: ' + str(subj_code))
                            logger.debug('     subvalue:  ' + str(subvalue))
                        et_list = ','.join(subvalue)

                        noin_info_str += ''.join((subj_code, '(', et_list, ') '))
                    noin_info_str += str(_('Not entered')).lower()

                else:
                    noin_info_str += ','.join(value)
                    noin_info_str += ' ' + str(_('Not entered')).lower()

                if logging_on:
                    logger.debug('     noin_info_str: ' + str(noin_info_str))

                noinput_list.append(noin_info_str)

    if no_input:
        student_dict['r_index'] = c.RESULT_NORESULT

        if 'noin_info' not in student_dict:
            student_dict['noin_info'] = []
        if noinput_list:
            student_dict['noin_info'].extend(noinput_list)

        if logging_on:
            logger.debug('     student_dict: ' + str(student_dict))

    return no_input
# - end of calcreex_passfailed_noinput


def calcreex_passfailed_count6_vsbo(student_dict):  #  PR2021-12-24 PR2022-05-26 PR2023-04-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calcreex_passfailed_count6_vsbo  -----')

    """
    'PR: slagingsregeling Vsbo
    '1a een kandidaat is geslaagd als voor al zijn vakken een eindcijfer 6 of hoger is behaald
    '1b een kandidaat is geslaagd als voor ten hoogste 1 vak een 5 heeft behaald en voor de overige vakken een 6 of hoger is behaald
    '1c een kandidaat is geslaagd als voor ten hoogste 1 vak een 4 is behaald en voor de overige vakken een 6 of hoger waarvan tenminste 1 een 7 of hoger
    '1d een kandidaat is geslaagd als voor 2 vakken een 5 is behaald en voor de overige vakken een 6 of hoger waarvan tenminste 1 een 7 of hoger
    """

    c3 = student_dict.get('c3', 0)
    c4 = student_dict.get('c4', 0)
    c5 = student_dict.get('c5', 0)
    # NIU c6 = count_dict.get('c6', 0)
    c7 = student_dict.get('c7', 0)

    has_failed = False

    if c3:  # 1 of meer drieën of lager
        has_failed = True
        three_str = ' '.join((str(c3), str( _('three or lower') if c3 == 1 else _('threes or lower'))))
        result_info = ''.join((three_str, '.'))

    else:
        # kandidaat geen drieën of lager, alleen vieren of hoger
        four_str = ' '.join((str(c4), str( _('four') if c4 == 1 else _('fours'))))
        five_str = ' '.join((str(c5), str( _('five') if c5 == 1 else _('fives'))))
        seven_str = ' '.join((str(c7) if c7 else str(pgettext_lazy('geen', 'no')), str( _('seven or higher') if c7 == 1 else _('sevens or higher'))))

        if c4 > 1:  # meer dan 1 vier
            has_failed = True
            result_info = ''.join((four_str, '.'))

        elif c4 == 1:
            # 'kandidaat heeft 1 vier, de rest vijven of hoger

            if c5:  # kandidaat heeft 1 vier en 1 of meer vijven
                has_failed = True
                result_info = ''.join((four_str, str(_(' and ')), five_str, '.'))
            else:  # 'kandidaat heeft 1 vier en geen vijf
                if not c7:
                    has_failed = True
                result_info = ''.join((four_str, str(_(' and ')), seven_str, '.')) # '1 four and no sevens or higher.'

        else:
            # 'kandidaat heeft geen vier, alleen vijven of hoger
            if c5 > 2:
                # '3 of meer vijven
                has_failed = True
                result_info = ''.join((five_str, '.'))

            elif c5 == 2:
                # kandidaat heeft 2 vijven, rest zessen of hoger
                if not c7:  # geen zevens en hoger
                    has_failed = True
                result_info = ''.join((five_str, str(_(' and ')), seven_str, '.')) # '2 fives and no sevens or higher.'

            elif c5 == 1:
                # kandidaat heeft 1 vijf, rest zessen of hoger
                result_info = ''.join((five_str, str(_(' and ')), str(_('for the other subjects a 6 or higher.'))))

            else:
                # kandidaat heeft geen vijf, rest zessen of hoger
                result_info = str(_('For all subjects a 6 or higher.'))

    r_info_dict = student_dict.get('r_info')
    r_info_dict['cnt3457'] = result_info

    if has_failed:
        student_dict['r_index'] = c.RESULT_FAILED

    return has_failed
# end of calcreex_passfailed_count6_vsbo


def calcreex_passfailed_count6_havovwo(student_dict):  #  PR2021-11-30  PR2022-05-26 PR2023-04-23
    # add result to combi_dict result:
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calcreex_passfailed_count6_havovwo  -----')

    c3 = student_dict.get('c3', 0)
    c4 = student_dict.get('c4', 0)
    c5 = student_dict.get('c5', 0)
    # NIU: c6 = count_dict.get('c6', 0)
    c7 = student_dict.get('c7', 0)

    avg_final_decimal = student_dict['avg_final']
    avg_final_str = ''
    avgfinal_lt_6 = True
    if avg_final_decimal:
        avgfinal_lt_6 = (avg_final_decimal.compare(Decimal(6)) < 0)
        # PR2022-05-29 debug: replace dot after Decimal(avgfinal_str), otherwise you get error ConversionSyntax
        avg_final_str = str(avg_final_decimal).replace('.', ',')

    has_failed = False
    result_info = ''
    if c3:  # 1 of meer drieën of lager
        has_failed = True
        three_str = ' '.join((str(c3), str( _('three or lower') if c3 == 1 else _('threes or lower'))))
        result_info = ''.join((three_str, '.'))

    else:
        # kandidaat geen drieën of lager, alleen vieren of hoger
        four_str = ' '.join((str(c4), str( _('four') if c4 == 1 else _('fours'))))
        five_str = ' '.join((str(c5), str( _('five') if c5 == 1 else _('fives'))))
        seven_str = ' '.join((str(c7) if c7 else 'no', str( _('seven or higher') if c7 == 1 else _('sevens or higher'))))

        if c4 > 1:  # meer dan 1 vier
            has_failed = True
            result_info = ''.join((four_str, '.'))

        elif c4 == 1:
            # 'kandidaat heeft 1 vier, de rest vijven of hoger
            result_info = ''.join((four_str, str(_(' and ')), five_str))
            if c5 > 1:
                # '1 vier en 2 of meer vijven
                has_failed = True
            elif c5 == 1:
                # een vier en een vijf: geslaagd als gemiddeld een 6 of hoger is behaald
                if avgfinal_lt_6:
                    has_failed = True
                result_info += ''.join((', ', str(_('average final grade is ')), avg_final_str))
            else: # 1 vier geen vijven
                # geslaagd als gemiddeld een 6 of hoger is behaald
                if avgfinal_lt_6:
                    has_failed = True
                result_info += ''.join((', ', str(_('average final grade is ')), avg_final_str))

        else:
            # 'kandidaat heeft geen vieren, alleen vijven of hoger
            if c5 > 2:
                # '3 of meer vijven
                has_failed = True
                result_info = five_str
            elif c5 == 2: # 2 vijven, rest zessen of hoger
                # geslaagd als gemiddeld een 6 of hoger is behaald
                if avgfinal_lt_6:
                    has_failed = True
                result_info += ''.join((five_str,', ', str(_('average final grade is ')), avg_final_str))
            elif c5 == 1:
                # 'kandidaat heeft 1 vijf, rest zessen of hoger
                # 'PR 17 jun 10 NB: gemiddeld een 6 of hoger is hier NIET van toepassing
                result_info = ' '.join((five_str, str(_('and for the other subjects a 6 or higher.'))))
            else:
                # kandidaat heeft geen vijf, rest zessen of hoger
                result_info = str(_('For all subjects a 6 or higher.'))

    # TODO add herexamen
    #result_dict['caption'] = str(c.RESULT_CAPTION[result_id])

    if has_failed:
        student_dict['r_index'] = c.RESULT_FAILED

# - put result_info in key 'r_info' of student_dict
    student_dict['r_info']['cnt3457'] = result_info

    return has_failed
# end of calcreex_passfailed_count6_havovwo


def calc_passfailed_core_rule(student_dict):  # PR2021-12-24  PR2022-05-28 PR2023-04-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calc_passfailed_core_rule  -----')
# 'count': {'c3': 0, 'c4': 1, 'c5': 1, 'c6': 2, 'c7': 2, 'core4': 0, 'core5': 0}
    # TODO skip core rule when in scheme 'core rule not applicable' How is this implemented ??? PR2022-08-21
    """
    in kernvak geen vieren en niet meer dan 1 vijf 'PR2015-10-31
    """
    core4 = student_dict.get('core4', 0)
    core5 = student_dict.get('core5', 0)

    if logging_on:
        logger.debug( '     core4: ' + str(core4) + ' ' + str(type(core4)))
        logger.debug( '     core5: ' + str(core5) + ' ' + str(type(core5)))

    has_failed = False
    result_info = ''
    if core4:
        result_info = ' '.join((str(core4), str(_('four') if core4 == 1 else _('fours'))))
    if core5:
        if result_info:
            result_info += str(_(' and '))
        result_info += ' '.join((str(core5), str(_('five') if core5 == 1 else _('fives'))))

    if core4 or core5 > 1:
        has_failed = True
        result_info += ''.join(( str(_(' in ')), str(_('core subjects')), '.'))


# - add info to passed_dict
    else:
        if core5:
            result_info = ''.join(('1 ', str(_('five'))))
        else:
            result_info = str(_('No fail marks')) # "Geen onvoldoendes"
        result_info += ''.join((str(_(' in ')), str(_('core subjects')), '.'))

# - if has_failed: create dict with key 'failed' if it does not exist
    if has_failed:
        student_dict['r_index'] = c.RESULT_FAILED

# - put result_info in key 'r_info' of student_dict
    student_dict['r_info']['core45'] = result_info

    return has_failed
# end of calc_passfailed_core_rule


def calc_passfailed_pece_avg_rule(student_dict):  # PR2021-12-24 PR2022-05-26 PR2023-04-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calc_passfailed_pece_avg_rule  -----')

    has_failed = False

    avg_ce_decimal = student_dict.get('avg_ce')
    if avg_ce_decimal:
        avg_display = str(avg_ce_decimal).replace('.', ',')
        result_info = ''.join((str(_('Average CE grade')), str(_(' is ')), avg_display))

        avg_decimal_A = avg_ce_decimal
        avg_55_B = Decimal('5.5')

        # a.compare(b) == -1 means a < b
        if avg_decimal_A.compare(avg_55_B) == -1:  # a.compare(b) == -1 means a < b
            has_failed = True
            result_info += str(_(', must be unrounded 5,5 or higher.'))
        else:
            result_info += '.'

    # - if has_failed: create dict with key 'failed' if it does not exist
        if has_failed:
            student_dict['r_index'] = c.RESULT_FAILED

        # - put result_info in key 'r_info' of student_dict
        student_dict['r_info']['avgce55'] = result_info

    return has_failed
# end of calc_passfailed_pece_avg_rule


def calcreex_add_result_to_log(student_dict, rule_avg_pece_sufficient, rule_core_sufficient, partial_exam):
    # PR2021-11-29 PR2022-06-05 PR2023-04-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calcreex_add_result_to_log  -----')

    # add result to combi_dict result: PR2021-11-29
    result_info_list = []
    result_info_log_list = []

    if student_dict['c_reex03']:
        result_str = ''.join((str(_('Result')), ' ', str(_('after')), ' ', str(_('Re-examination 3rd period')).lower(), ': '))
    elif student_dict['c_reex']:
        result_str = ''.join((str(_('Result')), ' ', str(_('after')), ' ', str(_('Re-examination')).lower(), ': '))
    else:
        result_str = ''.join((str(_('Result')), ': '))

    result_info_dict = student_dict.get('r_info')

    show_details = False
    result_info_log_list.append(' ')
    result_index = student_dict.get('r_index')
    if result_index == c.RESULT_WITHDRAWN:
        result_str += str(_('Withdrawn')).upper()
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)
    elif result_index == c.RESULT_NORESULT:
        result_str += str(_('No result')).upper()
        if partial_exam:
            result_str += ''.join((' (', str(_('partial exam')).lower(), ')'))
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)
        noin_info_list = result_info_dict.get('noin_info')
        if noin_info_list:
            for noin_info in noin_info_list:
                result_info_list.append(noin_info)
                result_info_log_list.append(''.join((c.STRING_SPACE_05, noin_info)))

    elif result_index == c.RESULT_FAILED:
        show_details = True
        result_str += str(_('Failed')).upper()
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)

        cnt3457_dict = result_info_dict.get('cnt3457')
        if cnt3457_dict:
            result_info_list.append(str(cnt3457_dict))
            result_info_log_list.append(''.join((c.STRING_SPACE_05, str(cnt3457_dict))))

        if rule_core_sufficient:
            core45_dict = result_info_dict.get('core45')
            if core45_dict:
                result_info_list.append(str(core45_dict))
                result_info_log_list.append(''.join((c.STRING_SPACE_05, str(core45_dict))))

        if rule_avg_pece_sufficient:
            avgce55_dict = student_dict.get('avgce55')
            if avgce55_dict:
                result_info_list.append(str(avgce55_dict))
                result_info_log_list.append(''.join((c.STRING_SPACE_05, str(avgce55_dict))))

            insuff_list = result_info_dict.get('insuff')
            if insuff_list:
                # 'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.']}
                for info in insuff_list:
                    result_info_list.append(str(info))
                    result_info_log_list.append(''.join((c.STRING_SPACE_05, info)))

    elif result_index == c.RESULT_PASSED:
        show_details = True
        result_str += str(_('Passed')).upper()
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)

        cnt3457_dict = result_info_dict.get('cnt3457')
        if cnt3457_dict:
            result_info_log_list.append(''.join((c.STRING_SPACE_05, str(cnt3457_dict))))
        core45_dict = student_dict.get('core45')
        if core45_dict:
            result_info_log_list.append(''.join((c.STRING_SPACE_05, str(core45_dict))))
        avgce55_dict = result_info_dict.get('avgce55')
        if avgce55_dict:
            result_info_log_list.append(''.join((c.STRING_SPACE_05, str(avgce55_dict))))
        insuff_list = result_info_dict.get('insuff')
        if insuff_list:
            # 'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.']}
            for info in insuff_list:
                result_info_log_list.append(''.join((c.STRING_SPACE_05, info)))

    if show_details:
        result_info = ''

# - add line with combi grade
        combi_dict = result_info_dict['combi']
        if 'result' in combi_dict:
            result_info_log_list.append(('').join((c.STRING_SPACE_05, combi_dict['result'], '{' + combi_dict['info'][1:] + '}')))

# - add line with final grade
        # final_sum_int is negative when grades have no input, therefore use: if final_sum_int > 0
        final_sum_decimal = student_dict.get('t_final') or '0'
        final_count_int = student_dict.get('c_final') or 0

        final_count_str = str(final_count_int) if final_count_int else '-'
        final_sum_str = str(final_sum_decimal)
        if final_sum_str == '0':
            final_sum_str = '-'
        final_rounded_str = '-'

        decimal_A = final_sum_decimal
        decimal_B = Decimal('0')

        # a.compare(b) == 1 means a > b, a.compare(b) == -1 means a < b, a.compare(b) == 0 means a = b
        if decimal_A.compare(decimal_B) == 1:
            has_failed = True
            result_info += str(_(', must be unrounded 5,5 or higher.'))
        else:
            result_info += '.'

        if final_count_int and decimal_A.compare(decimal_B) == 1:
            final_avg = Decimal(final_sum_str) / Decimal(final_count_str)
            final_rounded_str = str(grade_calc.round_decimal_from_str(final_avg, digits=1))
        final_rounded_with_comma = final_rounded_str.replace('.', ',')

        final_info = '' #  final_dict.get('info', '-')
        final_info_str = final_info[1:] if final_info else '-'
        log_txt = ''.join((str(_('Average final grade')), ': ',
            final_rounded_with_comma, ' (', final_sum_str, '/', final_count_str, ') ', '{' + final_info_str + '}'
        ))
        result_info_log_list.append(('').join((c.STRING_SPACE_05, str(log_txt))))

# - add line with average pece grade
        avg_ce_info_dict = student_dict.get('avg_ce_info')
        if avg_ce_info_dict:
            result_str = avg_ce_info_dict['result'] if 'result' in avg_ce_info_dict else ''
            info_str = avg_ce_info_dict['info'][1:] if 'info' in avg_ce_info_dict else ''
            result_info_log_list.append(''.join((c.STRING_SPACE_05, result_str, '{' + info_str + '}')))

        if logging_on:
            logger.debug( 'log_txt: ' + str(log_txt))
    return result_info_list, result_info_log_list
# - end of calcreex_add_result_to_log


def calcreex_sum_pece(student_dict, gl_pecegrade, gradetype, multiplier, weight_ce, exemp_no_ce, is_extra_nocount, is_thumbrule, subj_code):  # PR2023-04-23
    # function adds CE-grade * multiplier to CE-sum, adds final-grade * multiplier to final-sum, adds multiplier to subj_count

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' -----  calcreex_sum_pece  -----')


    # calc only when :
    #  - gradetype is number
    #  - weight_ce > 0
    #  - exemption has central exam
    #  - subject is not 'is_extra_nocount'
    #  - subject is not 'is_thumbrule'

    if gradetype == c.GRADETYPE_01_NUMBER and weight_ce > 0 and not exemp_no_ce and not is_extra_nocount and not is_thumbrule:
        try:

            for key_str in ('sumX10', 'cnt', 'info'):
                if key_str not in pece_dict:
                    default_value = '' if key_str == 'info' else 0
                    pece_dict[key_str] = default_value

            if logging_on:
                logger.debug('     pece_dict: ' + str(pece_dict) + ' ' + str(type(pece_dict)))
                logger.debug('     max_ep: ' + str(max_ep) + ' ' + str(type(max_ep)))
                logger.debug('     max_pece: ' + str(max_pece) + ' ' + str(type(max_pece)))
                logger.debug('     multiplier: ' + str(multiplier) + ' ' + str(type(multiplier)))

    # - add multiplier to count dict (multiplier =1, except when sectorprogramma PBL
            pece_dict['cnt'] += multiplier

            if logging_on:
                logger.debug('     pece_dict[cnt]: ' + str(pece_dict['cnt']) + ' ' + str(type(pece_dict['cnt'])))

            max_pece_x10_int = 0
            max_pece_str = '-'
            if 'pe' in max_ni or 'ce' in max_ni:
                # make sum negatve when no_input, to show '-' as combi grade or final sum  when one of the subejcts has noinput
                max_pece_x10_int = -9999
            elif max_pece:
                max_pece_str = str(max_pece).replace('.', ',')
                max_pece_dot = max_pece.replace(',', '.')
                if '.' in max_pece_dot:
                    max_pece_dot = max_pece_dot.replace('.', '')
                else:
                    max_pece_dot += '0'
                max_pece_x10_int = int(max_pece_dot)

            if logging_on:
                logger.debug('     max_pece_x10_int: ' + str(max_pece_x10_int) + ' ' + str(type(max_pece_x10_int)))

    # - add pece_x10_int * multiplier to this_sum_int (multiplier =1, except when sectorprogramma PBL
            if max_pece_x10_int:
                pece_dict['sumX10'] += max_pece_x10_int * multiplier

    # - add subj_code and grade to info_pece:
            pece_dict['info'] += ''.join((' ', subj_code, ':', max_pece_str))

            # - add '2x','vr','h','h3' to grade
            gradeinfo_extension = calc_res.get_gradeinfo_extension(multiplier, max_ep)
            if gradeinfo_extension:
                pece_dict['info'] += gradeinfo_extension

            if logging_on:
                logger.debug('     pece_dict: ' + str(pece_dict))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of calcreex_sum_pece


def calcreex_count_final_3457_core(student_dict, finalgrade, gradetype, is_combi, is_core, multiplier,
                               is_extra_nocount, is_thumbrule):
#PR2023-04-23
# - calc only when gradetype is number
# - skip count 3457 when subject is 'is_combi (combi grade is checked at the end by calc_combi_and_add_to_totals)
    #  - note: grade '3 or less' is not skipped when is_combi
    #  - note: core is not skipped when is_combi

# - skip when subject is 'is_extra_nocount' or 'is_thumbrule'

# - student_dict contains keys 'c3', 'c4', 'c5', 'c6', 'c7', 'core4', 'core5'
# - values are integers, these keys are added in calcreex_get_students_with_final_grades

    if gradetype == c.GRADETYPE_01_NUMBER and not is_extra_nocount and not is_thumbrule:
        if finalgrade:
            final_grade_int = None
            if isinstance(finalgrade, int):
                final_grade_int = finalgrade
            elif isinstance(finalgrade, str):
                final_grade_int = int(finalgrade)

            if final_grade_int:
                if final_grade_int < 3:
                    final_grade_int = 3
                if 6 < final_grade_int < 11:
                    final_grade_int = 7

    # count c3, c4, c5, c6, c7
                # skip count when is combi

                # PR2022-06-11 Mail Nancy Josefina: 3 is allowed in combi subject
                # was: skip count when is combi, except when final_grade_int <= 3
                # was: if not is_combi or final_grade_int == 3:

                if not is_combi:
                    key_str = 'c' + str(final_grade_int)
                    student_dict[key_str] += multiplier

    # count core4 and core 5, also when core subject is combi
                # don't skip core when is combi
                if is_core:
                    if 3 < final_grade_int < 6:
                        key_str = 'core' + str(final_grade_int)
                        student_dict[key_str] += multiplier

# - end of calcreex_count_final_3457_core


def calcreex_combi_and_add_to_totals(student_dict):  # PR2021-12-22 PR2023-04-23
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calcreex_combi_and_add_to_totals  -----')
        logger.debug('student_dict: ' + str(student_dict))

    # values of 'c_combi' and 't_combi' are stored in student_dict in function calcreex_get_students_with_final_grades,
    # while iterating through studsubjects

    combi_count_int = student_dict.get('c_combi') or 0
    combi_sum_decimal = student_dict.get('t_combi')

    combi_count_str, combi_sum_str, combi_final_str, combi_final_int = None, None, None, None

    # skip calculating combi grade when no combi subjects - correct? PR2021-11-30
    if combi_count_int > 0:

# - calculate final combi grade
        combi_count_decimal = Decimal(str(combi_count_int))
        combi_avg_decimal_not_rounded = combi_sum_decimal / combi_count_decimal

# round to integer
        combi_avg_decimal_rounded = grade_calc.round_decimal(combi_avg_decimal_not_rounded, 0)

        combi_final_str = str(combi_avg_decimal_rounded)
        combi_final_int = int(combi_final_str)

# - add 1 to count of final grades
        student_dict['c_final'] = 1 + (student_dict.get('c_final') or 0)

# - add combi_final_int to sum of final grades
        if combi_final_int:
            student_dict['t_final'] = combi_avg_decimal_rounded + Decimal(student_dict.get('t_final'))

# add 'combi'' and combi grade to result_info detail
        result_info = ''.join((' ', 'combi', ':',
            combi_final_str if combi_final_str else '-'
            ))

# - put info in combi_info
        #     'c_combi': 0, 't_combi': '0', 'avg_combi': None, 'combi_info': {}, 'avg_combi_detail': {},
        student_dict['combi_info'] = ''.join((
            str(_('Combination grade')), ': ',
            combi_final_str if combi_final_str else '-',
            ' (',
            combi_sum_str if combi_sum_str else '-',
            '/',
            combi_count_str if combi_count_str else '-',
            ') '
        ))

        """
        'c_combi': 2, 't_combi': Decimal('11'), 'avg_combi': None, 
        'combi_info': 'Combinatiecijfer: 6 (-/-) ', 
        'combi_detail': {}
        """

# - add combi grade to calcreex_count_final_3457_core(use_studsubj_ep_dict, calc_student_ep_dict, gradetype, is_core, multiplier, log_list):
        is_thumbrule = False

        # note: here is_combi is False. When True it skips counting, this is used when for combi subjects
        calcreex_count_final_3457_core(
            student_dict=student_dict,
            finalgrade=combi_final_int,
            gradetype=c.GRADETYPE_01_NUMBER,
            is_combi=False,
            is_core=False,
            multiplier=1,
            is_extra_nocount=False,   # is_extra_nocount is not True when combi subject
            is_thumbrule=is_thumbrule
        )
# - end of calcreex_combi_and_add_to_totals


def calcreex_pece_avg(student_dict):  # PR2021-12-23 PR2023-04-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calcreex_pece_avg  -----')

    # see https://www.examenblad.nl/veel-gevraagd/hoe-moeten-cijfers-worden-afgerond/2013
    # Een gemiddelde van 5,48333 is lager dan 5,5.

    """
    student_dict: { 
        'c_ce': 7, 't_ce': Decimal('36.4'), 'avg_ce': Decimal('5.2'), 
        'avg_ce_info': 'Gemiddeld CE-cijfer: 5,2 (36,4/7) ', 'avg_ce_detail': {}, 
    """
    pece_count_int = student_dict.get('c_ce') or 0
    pece_total_decimal = student_dict.get('t_ce') or '0'

    if pece_count_int > 0:
        pece_count_str = str(pece_count_int)
        pece_count_decimal = Decimal(pece_count_str)
        pece_sum_str = str(pece_total_decimal).replace('.', ',')

        # PR20220-05-27 DO NOT ROUND !!!
        #   Een gemiddelde van 5,48333 is lager dan 5,5.

        # was:
        # - round to one digit after dot
        #   pece_avg_decimal_rounded = grade_calc.round_decimal(pece_avg_decimal_not_rounded, 1)
        #   pece_avg_rounded_dot = str(pece_avg_decimal_rounded)
        #   pece_avg_rounded_comma = pece_avg_rounded_dot.replace('.', ',')

        pece_avg_decimal = pece_total_decimal / pece_count_decimal

        pece_avg_display = str(pece_avg_decimal).replace('.', ',')

        student_dict['avg_ce'] = pece_avg_decimal
        student_dict['avg_ce_info'] = ''.join((
            str(_('Average CE grade')), ': ',
            pece_avg_display if pece_avg_display else '-',
            ' (', pece_sum_str if pece_sum_str else '-',
            '/', pece_count_str if pece_count_str else '-',
            ') '
        ))

        if logging_on:
            logger.debug('    pece_total_decimal: ' + str(pece_total_decimal) + ' ' + str(type(pece_total_decimal)))
            logger.debug('    pece_count_decimal: ' + str(pece_count_decimal) + ' ' + str(type(pece_count_decimal)))
            logger.debug('    pece_avg_decimal: ' + str(pece_avg_decimal) + ' ' + str(type(pece_avg_decimal)))
# - end of calcreex_pece_avg


def calcreex_final_avg(student_dict):  # PR2021-12-23 PR2023-04-22
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calcreex_final_avg  -----')

    # calulate avergae final grade and put it back in student_ep_dict

    """
    student_dict: {'fullname': 'Benilia, Elisha Rashida Netanya', 
        'c_subj': 10, 'c_exem': 0, 'c_sr': 0, 'c_reex': 2, 'c_reex03': 0, 'c_extra_nocount': 0, 'c_extra_counts': 0, 'c_thumbrule': 0, 
        't_ce': Decimal('34.6'), 't_final': Decimal('33'), 't_combi': Decimal('18'), 
        'c_ce': 6, 'c_final': 6, 'c_combi': 3, 
        
        
    'c_final': 0, 't_final': '0', 'avg_final': None, 'avg_final_info': {}, 'avg_final_detail': {},
    """
    # final_dict: {sum: 49, cnt: 7, info: ' ne:6 pa:9 en:6 sp:8 wk:6 ec:6 ac:8'}

    final_sum_decimal = student_dict.get('t_final')
    final_count_int = student_dict.get('c_final')

    final_count_str, final_sum_str, final_rounded_str, final_rounded_int = None, None, None, 0
    final_avg_decimal = None
    if final_count_int:
        final_count_str = str(final_count_int)
        final_sum_str = str(final_sum_decimal)

        # final_avg will be rounded with 1 digit (unlike calcreex_pece_avg that is not rounded)
        final_avg_decimal = final_sum_decimal / Decimal(final_count_str)
        final_rounded_str = str(grade_calc.round_decimal_from_str(final_avg_decimal, digits=1))

    # put avg_final in student_dict
    student_dict['avg_final'] = final_avg_decimal
    student_dict['avg_final_info'] = ''.join((
        str(_('Average final grade')), ': ',
        final_rounded_str if final_rounded_str else '-',
        ' (',
        final_sum_str if final_sum_str else '-',
        '/',
        final_count_str if final_count_str else '-',
        ') '))
# - end of calcreex_final_avg


def calcreex_get_rules_from_scheme(student_dict, isevlexstudent):
    # PR2021-12-19 PR2022-06-04 PR2023-04-22
    # - get result rules from scheme, values are in student_dict

    # -must check if scheme of student is correct( dep, lvl and sct are the same) (should always be the case)
    #   happens when iterating throudh studsubjects

    # - get scheme rules
    rule_avg_pece_sufficient = student_dict.get('rule_avg_pece_sufficient') or False
    rule_core_sufficient = student_dict.get('rule_core_sufficient') or False

    if rule_avg_pece_sufficient:
        # skip when student is evening / lex student and rule_avg_pece_notatevlex = True
        if isevlexstudent and student_dict.get('rule_avg_pece_notatevlex'):
            rule_avg_pece_sufficient = False

    if rule_core_sufficient:
        if isevlexstudent and student_dict.get('rule_core_notatevlex'):
            rule_core_sufficient = False

    return rule_avg_pece_sufficient, rule_core_sufficient
# - end of calcreex_get_rules_from_scheme


def calcreex_studsubj_result(studsubj_dict, student_dict, isevlexstudent, sr_allowed, no_practexam, log_list):
    # PR2021-12-30 PR2022-01-02 PR2023-04-22
    # called by calc_student_result and update_and_save_gradelist_fields_in_studsubj_student

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('  ++++++++++++  calcreex_studsubj_result  ++++++++++++')
        #logger.debug('  studsubj_dict: ' + str(studsubj_dict))
    """
    studsubj_dict: {
        'subject_id': 123, 'schemeitem_id': 1763, 
        'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': None, 
        'gl_sesrgrade': '4.7', 'gl_pecegrade': '4.9', 'gl_finalgrade': '5', 
        'gl_ni_se': False, 'gl_ni_sr': False, 'gl_ni_pe': False, 'gl_ni_ce': False,
         'gl_examperiod': 1, 'is_thumbrule': False, 'has_exemption': False, 'has_sr': False, 'has_reex': True, 'has_reex03': False, 
        'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 
        'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'thumb_rule': False, 'no_ce_years': '2020', 
        'subj_name_nl': 'Biologie', 'subj_code': 'bi', 'subjtype_abbrev': 'Sectordeel'
    }
    """
    subj_code = studsubj_dict.get('subj_code', '-')
    subj_name_nl = studsubj_dict.get('subj_name_nl', '-')
    gradetype = studsubj_dict.get('gradetype')
    multiplier = studsubj_dict.get('multiplier', 1)
    weight_se = studsubj_dict.get('weight_se', 0)
    weight_ce = studsubj_dict.get('weight_ce', 0)
    is_combi = studsubj_dict.get('is_combi', False)
    is_core = studsubj_dict.get('is_core_subject', False)

    gl_finalgrade = studsubj_dict.get('gl_finalgrade')
    gl_pecegrade = studsubj_dict.get('gl_pecegrade')

    rule_grade_sufficient = studsubj_dict.get('rule_grade_sufficient', False)
    rule_gradesuff_notatevlex = studsubj_dict.get('rule_gradesuff_notatevlex', False)

    # si.thumb_rule = True means: thumbrule is allowed for this subject
    # studsubj.is_thumbrule = True means: student has applied thumbrule for this subject
    thumb_rule_allowed = studsubj_dict.get('thumb_rule', False)

    # Practical exam does not exist any more. Set has_practexam = False PR2022-05-26
    # was: has_practexam = si_dict.get('has_practexam', False)
    has_practexam = False

    # - put subject name + combi, core if appl. in log_list
    subj_name_str = subj_name_nl
    if is_combi or is_core:
        subj_name_str += ' ('
        if is_combi:
            subj_name_str += str(_('Combination subject'))
        if is_combi and is_core:
            subj_name_str += ', '
        if is_core:
            subj_name_str += str(_('Core subject'))
        subj_name_str += ')'

    if log_list is not None:
        log_list.append(subj_name_str)

    # PR2022-06-09 debug: value of has_reex etc is not always correct
    # it is safer to loop through ep_list to calculate values of has_reex etc
    # then has_reex can be stored in student
    # here field 'has_reex' of studsubj is used,

    is_extra_nocount = studsubj_dict.get('is_extra_nocount', False)
    if is_extra_nocount:
        if log_list is not None:
            log_list.append(''.join((c.STRING_SPACE_05, str(_('Extra subject, does not count for the result.')))))

    is_thumbrule = False
    if thumb_rule_allowed:
        is_thumbrule = studsubj_dict.get('is_thumbrule', False)
        if is_thumbrule:
            if log_list is not None:
                log_list.append(
                    ''.join((c.STRING_SPACE_05, str(_('Thumb rule applies, subject does not count for the result.')))))

    has_sr = studsubj_dict.get('has_sr') or False
    has_exemption = studsubj_dict.get('has_exemption') or False
    has_reex = studsubj_dict.get('has_reex') or False
    has_reex03 = studsubj_dict.get('has_reex03') or False

    exemp_no_ce = False
    if has_exemption:
        # table 'schemeitem' contains field 'no_ce_years' with string with years without ce: "2020;2021"
        # table 'studsubj' contains field 'exemption_year' with year of the exemption

        exemption_year = studsubj_dict.get('exemption_year')
        no_ce_years = studsubj_dict.get('no_ce_years')
        exemp_no_ce = calc_res.calc_exemp_noce(exemption_year, no_ce_years)

    if logging_on:
        logger.debug(' ')
        logger.debug(' =====================  ' + str(subj_name_nl) + '   =====================')
        logger.debug('     has_exemption: ' + str(has_exemption))
        logger.debug('     has_reex:      ' + str(has_reex))
        logger.debug('     has_reex03:      ' + str(has_reex03))
        logger.debug('     is_thumbrule:  ' + str(is_thumbrule))

    # gl_examperiod contains the examperiod that is stored in studsubj, to be shown on gradelist
    gl_examperiod = studsubj_dict.get('gl_examperiod')

    log_subj_grade_str = log_list_subject_grade(studsubj_dict, gl_examperiod, multiplier,
                                            weight_se, weight_ce, has_practexam, sr_allowed, no_practexam)

    prefix =  '     '
    log_list.append(''.join((prefix, log_subj_grade_str)))

# - calculate count of each final grade
    calcreex_count_final_3457_core(student_dict, gl_finalgrade, gradetype, is_combi, is_core, multiplier, is_extra_nocount, is_thumbrule)

# - calculate CE-sum with subject_count
    calcreex_sum_pece(student_dict, gl_pecegrade, gradetype, multiplier, weight_ce, exemp_no_ce, is_extra_nocount, is_thumbrule, subj_code)

    # - after adding max_grades: check result requirements
    # when failed: 'failed' info is added to student_ep_dict
    # 'failed': {'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.'],
    calcreex_rule_issufficient(student_dict, gl_finalgrade,
                           isevlexstudent, is_extra_nocount, thumb_rule_allowed,
                           rule_grade_sufficient, rule_gradesuff_notatevlex, subj_name_nl)


    # - put the max values that will appear on the gradelist back in studsubj, also max_use_exem, gl_ni_se etc
    max_examperiod_dict = studsubj_dict.get('gl_examperiod')
    if logging_on:
        logger.debug('    studsubj_dict: ' + str(studsubj_dict))
        logger.debug('    max_examperiod_dict: ' + str(max_examperiod_dict))
# - end of calcreex_studsubj_result


def calcreex_get_sql_student_values(student_dict, result_info_list):  # PR2021-12-30

    # function puts result and grade info in return list sql_student_values

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------- calcreex_get_sql_student_values ----------- ')

    def get_sql_value_str(value):
        return ''.join(("'", str(value), "'")) if value else 'NULL'

    def get_sql_value_int(value):
        return str(value) if value else '0'

    sql_student_values = []
    try:
        student_id = student_dict.get('stud_id')
        exemption_count_str = get_sql_value_int(student_dict.get('c_ep4'))
        sr_count_str = get_sql_value_int(student_dict.get('sr_count_str'))
        reex_count_str = get_sql_value_int(student_dict.get('c_ep2'))
        reex03_count_str = get_sql_value_int(student_dict.get('c_ep3'))

        # combi thumbrule counts as one, thumbrule_combi = True in student_dict if any combi has thumbrule
        c_thumbrule = student_dict.get('c_thumbrule') or 0
        if student_dict.get('thumbrule_combi'):
            c_thumbrule += 1
        thumbrule_count_str = get_sql_value_int(c_thumbrule)
        # TODO add field subj_count to model
        # subject_count = get_sql_value_int(student_dict.get('c_subj'))

        if logging_on:
            logger.debug('     exemption_count_str: ' + str(exemption_count_str))
            logger.debug('     reex_count_str: ' + str(reex_count_str))
            logger.debug('     thumbrule_count_str: ' + str(thumbrule_count_str))

        last_ep_key = student_dict.get('last_ep')
        last_ep_dict = student_dict.get(last_ep_key)

        if logging_on:
            logger.debug('?????????????!@@ last_ep_dict: ' + str(last_ep_dict))

        gl_ce_avg = af.get_dict_value(last_ep_dict, ('pece', 'avg'))
        gl_combi_avg = af.get_dict_value(last_ep_dict, ('combi', 'final'))
        gl_final_avg = af.get_dict_value(last_ep_dict, ('final', 'avg'))
        result_index = last_ep_dict.get('result_index') or 0

        """
        last_ep_dict: {'ep': 1, 
        'final': {'sum': 41, 'cnt': 7, 'info': ' ec:4 en:6 fr:5 ne:7 sp:6 wk:6 combi:7', 'avg': '5.9', 
        'result': 'Gemiddeld eindcijfer: 5.9 (41/7) '}, 
        'combi': {'sum': 21, 'cnt': 3, 'info': ' cav:7 lo:8 mm1:6', 'final': 7, 
        'result': 'Combinatiecijfer: 7 (21/3) '}, 
        'pece': {'sumX10': 300, 'cnt': 6, 'info': ' ec:1,3 en:6,4 fr:3,5 ne:7,5 sp:5,4 wk:5,9', 'avg': '5.0', 
        'result': 'Gemiddeld CE-cijfer: 5,0 (30/6) '}, 
        'count': {'c3': 0, 'c4': 1, 'c5': 1, 'c6': 3, 'c7': 2, 'core4': 0, 'core5': 0}, 
        'result_index': 2, 
        'failed': {'cnt3457': '1 vier en 1 vijf.', 'avgce55': 'Gemiddeld CE-cijfer is 5,0, moet onafgerond 5,5 of hoger zijn.'}}

        """

        gl_ce_avg_str = ''.join(("'", str(gl_ce_avg), "'")) if gl_ce_avg else 'NULL'
        gl_combi_avg_str = ''.join(("'", str(gl_combi_avg), "'")) if gl_combi_avg else 'NULL'
        gl_final_avg_str = ''.join(("'", str(gl_final_avg), "'")) if gl_final_avg else 'NULL'

        result_index_str = str(result_index) if result_index else '0'
        result_status_str = ''.join(("'", c.RESULT_CAPTION[result_index], "'")) if c.RESULT_CAPTION[
            result_index] else 'NULL'

        result_info = '|'.join(result_info_list) if result_info_list else None
        result_info_str = ''.join(("'", result_info, "'")) if result_info else 'NULL'

        e1_ce_avg_str, e1_combi_avg_str, e1_final_avg_str, e1_result_index_str = 'NULL', 'NULL', 'NULL', '0'
        ep1_dict = student_dict.get('ep1')
        if ep1_dict:
            e1_ce_avg = af.get_dict_value(ep1_dict, ('pece', 'avg'))
            e1_combi_avg = af.get_dict_value(ep1_dict, ('combi', 'final'))
            e1_final_avg = af.get_dict_value(ep1_dict, ('final', 'avg'))
            e1_result_index = ep1_dict.get('result_index')

            e1_ce_avg_str = ''.join(("'", str(e1_ce_avg), "'")) if e1_ce_avg else 'NULL'
            e1_combi_avg_str = ''.join(("'", str(e1_combi_avg), "'")) if e1_combi_avg else 'NULL'
            e1_final_avg_str = ''.join(("'", str(e1_final_avg), "'")) if e1_final_avg else 'NULL'
            e1_result_index_str = str(e1_result_index) if e1_result_index else '0'

        e2_ce_avg_str, e2_combi_avg_str, e2_final_avg_str, e2_result_index_str = 'NULL', 'NULL', 'NULL', '0'
        ep2_dict = student_dict.get('ep2')
        if ep2_dict:
            e2_ce_avg = af.get_dict_value(ep2_dict, ('pece', 'avg'))
            e2_combi_avg = af.get_dict_value(ep2_dict, ('combi', 'final'))
            e2_final_avg = af.get_dict_value(ep2_dict, ('final', 'avg'))
            e2_result_index = ep2_dict.get('result_index')

            e2_ce_avg_str = ''.join(("'", str(e2_ce_avg), "'")) if e2_ce_avg else 'NULL'
            e2_combi_avg_str = ''.join(("'", str(e2_combi_avg), "'")) if e2_combi_avg else 'NULL'
            e2_final_avg_str = ''.join(("'", str(e2_final_avg), "'")) if e2_final_avg else 'NULL'
            e2_result_index_str = str(e2_result_index) if e2_result_index else '0'

        """
        sql_student_values = [ str(student_id),
            gl_ce_avg_str, gl_combi_avg_str, gl_final_avg_str, result_index_str,  result_status_str,  result_info_str,
            e1_ce_avg_str, e1_combi_avg_str, e1_final_avg_str, e1_result_index_str,
            e2_ce_avg_str, e2_combi_avg_str, e2_final_avg_str, e2_result_index_str,
            exemption_count, sr_count, reex_count, reex03_count,thumbrule_count
        ]
        sql_student_values: [ '4377', 
            "'5.8'", "'7'", "'6.1'", '1', "'Geslaagd'", "'Uitslag na herexamen: GESLAAGD'", 
            "'5.0'", "'7'", "'5.9'", '2', 
            "'5.8'", "'7'", "'6.1'", '1']
        sql_student_values: ['4377', 
            "'5.0'", "'7'", "'5.9'", '2', "'Afgewezen'", "'Uitslag: AFGEWEZEN|1 vier en 1 vijf.|Gemiddeld CE-cijfer is 5,0, moet onafgerond 5,5 of hoger zijn.'", 
            "'5.0'", "'7'", "'5.9'", '2', 'NULL', 'NULL', 'NULL', '0', '0', '0', '0', '0', '0']

        """

        sql_student_values = [str(student_id),
                              gl_ce_avg_str, gl_combi_avg_str, gl_final_avg_str, result_index_str,
                              result_status_str, result_info_str,
                              e1_ce_avg_str, e1_combi_avg_str, e1_final_avg_str, e1_result_index_str,
                              e2_ce_avg_str, e2_combi_avg_str, e2_final_avg_str, e2_result_index_str,
                              exemption_count_str, sr_count_str,
                              reex_count_str, reex03_count_str, thumbrule_count_str
                              ]

        if logging_on:
            logger.debug('     sql_student_values: ' + str(sql_student_values))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return sql_student_values
# --- end of get_sql_student_values


def calcreex_get_isevlex_isreex_fullname(student_dict):  # PR2021-12-19  PR2021-12-29 PR2022-06-05
    # - get from student_dict: isevlexstudent, reex_count, reex03_count and full name with (evening / lex student)

    full_name = student_dict.get('fullname', '---')
    iseveningstudent = student_dict.get('iseveningstudent') or False
    islexstudent = student_dict.get('islexstudent') or False
    partial_exam = student_dict.get('partial_exam') or False

    scheme_error = False
    isevlexstudent = False
    ev_lex_part_list = []

    scheme_id = student_dict.get('scheme_id')
    scheme_error = scheme_id is None

    if iseveningstudent:
        isevlexstudent = True
        ev_lex_part_list.append(str(_('evening school candidate')))
    if islexstudent:
        isevlexstudent = True
        ev_lex_part_list.append(str(_('landsexamen candidate')))
    if partial_exam:
        if iseveningstudent:
            ev_lex_part_list.append(str(_('partial exam')))
        else:
            ev_lex_part_list.append(str(_('additional exam')))

    if ev_lex_part_list:
        ev_lex_part_str = ', '.join(ev_lex_part_list)
        full_name += ''.join((' (', ev_lex_part_str, ')'))

    withdrawn = student_dict.get('withdrawn', False)

    return scheme_error, isevlexstudent, partial_exam, withdrawn, full_name
# - end of calcreex_get_isevlex_isreex_fullname


def calcreex_rule_issufficient(student_dict, gl_finalgrade, isevlexstudent,
                           is_extra_nocount, thumb_rule_allowed, rule_grade_sufficient, rule_gradesuff_notatevlex, subj_name):  # PR2021-11-23
    # function checks if max final grade is sufficient (
    # - only when 'rule_grade_sufficient' for this subject is set True in schemeitem
    # - skip when evlex student and notatevlex = True
    # - skip when subject is 'is_extra_nocount'

    # rule 2022 Havo/VWO CUR + SXM
    # - voor de vakken cav en lo een voldoende of goed is behaald

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug( ' -----  calcreex_rule_issufficient  -----')

# - skip when subject is 'is_extra_nocount' or when thumb_rule_allowed
    if not is_extra_nocount or thumb_rule_allowed:
        try:
            has_failed = False

# - skip when 'rule_grade_sufficient' for this subject is not set True in schemeitem
            if rule_grade_sufficient:

# - skip when evlex student and notatevlex = True
                if not isevlexstudent or not rule_gradesuff_notatevlex:

# - check if subject is sufficient
                    gl_finalgrade = use_studsubj_ep_dict.get('max_final')
                    if gl_finalgrade:
                        if gl_finalgrade.isnumeric():
                            gl_finalgrade_int = int(gl_finalgrade)
                            if gl_finalgrade_int < 6:
                                has_failed = True
                        else:
                            if gl_finalgrade and gl_finalgrade.lower() not in ('v', 'g'):
                                has_failed = True

# - if not: create dict with key 'insuff' if it does not exist
                    if has_failed:

                        gl_finalgrade_str = str(_('not sufficient')) if gl_finalgrade else ''.join(('<', str(_('Not entered')).lower(), '>'))
                        result_info = ''.join((subj_name, str(_(' is ')), gl_finalgrade_str))

        # - if has_failed: create dict with key 'failed' if it does not exist
                        if 'failed' not in student_ep_dict:
                            student_ep_dict['failed'] = {}
                        failed_dict = student_ep_dict.get('failed')

                        if 'insuff' not in failed_dict:
                            failed_dict['insuff'] = []
                        failed_dict['insuff'].append(result_info)
            """
            'failed': {'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.'],
            """
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of calcreex_rule_issufficient




def log_list_header(sel_school, sel_department, sel_examyear, user_lang):  # PR2021-12-20
# - create log_list
    today_dte = af.get_today_dateobj()
    today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

    school_name = sel_school.base.code + ' ' + sel_school.name
    log_list = [c.STRING_DOUBLELINE_80,
                str(_('Calculate results')) + ' ' + str(_('date')) + ': ' + str(today_formatted),
                c.STRING_DOUBLELINE_80]
    log_list.append(c.STRING_SPACE_05 + str(_("School    : %(name)s") % {'name': school_name}))
    log_list.append(c.STRING_SPACE_05 + str(_("Department: %(dep)s") % {'dep': sel_department.name}))
    log_list.append(c.STRING_SPACE_05 + str(_("Exam year : %(ey)s") % {'ey': str(sel_examyear.code)}))

    log_list.append(c.STRING_SPACE_05)

    return log_list
# - end of log_list_header


def log_list_student_header(student_dict, full_name, log_list):  # PR2021-12-19

    log_list.append(c.STRING_SINGLELINE_80)
    log_list.append(full_name)
    depbase_code = student_dict.get('depbase_code') or ''
    lvlbase_code = student_dict.get('lvlbase_code') or ''
    sct_name = student_dict.get('sct_name') or ''
    log_list.append( ''.join((c.STRING_SPACE_05, depbase_code, ' ', lvlbase_code, ' ', sct_name )))


def log_list_subject_grade (studsubj_dict, examperiod, multiplier, weight_se, weight_ce, has_practexam, sr_allowed, no_practexam):
    # PR2021-12-20 PR2022-06-05

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------- log_list_subject_grade ----------')
        logger.debug('    studsubj_dict: ' + str(studsubj_dict))

    multiplier_str = ''.join(('(', str(multiplier), 'x)')) if multiplier != 1 else ''
    weight_se_str = ''.join(('(x', str(weight_se), ')')) if weight_se != 1 else ''

    sesr_str = studsubj_dict.get('gl_sesrgrade') or '-'

    pece_str = studsubj_dict.get('gl_pecegrade') or '-'

# when has_sr: sr_str has either value or 'noinput
    if weight_se <= 0:
        sesr_display = ''
    else:
        sesr_str = sesr_str.replace('.', ',')
        sesr_display = ''.join(('SE:', sesr_str, multiplier_str, weight_se_str))

    if weight_ce <= 0:
        pece_display = ''
    else:
        pece_str = pece_str.replace('.', ',')
        pece_display = ''.join((' CE:', pece_str))

    ep_str = ''
    if examperiod == c.EXAMPERIOD_EXEMPTION:
        ep_str = str(_('Exemption')) + ': '
    elif examperiod == c.EXAMPERIOD_SECOND:
        ep_str = str(_('Re-examination')) + ': '
    elif examperiod == c.EXAMPERIOD_THIRD:
        ep_str = str(_('Re-examination 3rd period')) + ': '

    final_str = studsubj_dict.get('gl_finalgrade') or '-'
    grade_str = ''.join((' ', str(_('Final grade')), ':', final_str))

    if logging_on:
        logger.debug('     ep_str: ' + str(ep_str))
        logger.debug('     sesr_display: ' + str(sesr_display))
        logger.debug('     pece_display: ' + str(pece_display))
        logger.debug('     grade_str: ' + str(grade_str))

    subj_grade_str = ''.join((str(ep_str), sesr_display, pece_display, grade_str))
    return subj_grade_str
# - end of log_list_subject_grade

def log_list_add_scheme_notfound(dep_level_req, log_list):  # PR2021-12-19
    # - add msg when scheme not found
    log_list.append(''.join((c.STRING_SPACE_05, str(_('The subject scheme of this candidate could not be found.')))))
    log_list.append(''.join((c.STRING_SPACE_05, str(_('The result cannot be calculated.')))))
    msg_txt = _('Please enter the learning path and sector.') if dep_level_req else _('Please enter the profile.')
    log_list.append(('').join((c.STRING_SPACE_05, str(msg_txt))))
# - end of log_list_add_scheme_notfound


def log_list_reex_count(exemption_count, sr_count, reex_count, reex03_count, thumbrule_count, thumbrule_combi, log_list):
    # PR2021-12-20 PR2021-12-28 PR2022-06-03
    if exemption_count or sr_count or reex_count or reex03_count:
        if exemption_count:
            cpt = str(_('Exemption') if exemption_count == 1 else _('Exemptions')).lower()
            log_list.append(''.join((c.STRING_SPACE_05, str(_('has')), ' ', str(exemption_count), ' ', cpt)))
        elif sr_count:
            cpt = str(_('Re-examination school exam') if sr_count == 1 else _('Re-examinations school exam')).lower()
            log_list.append(''.join((c.STRING_SPACE_05, str(_('has')), ' ', str(sr_count), ' ', cpt)))
        if reex_count:
            cpt = str(_('Re-examination') if reex_count == 1 else _('Re-examinations')).lower()
            log_list.append(''.join((c.STRING_SPACE_05, str(_('has')), ' ', str(reex_count), ' ', cpt)))
        if reex03_count:
            cpt = str(_('Re-examination 3rd period') if reex03_count == 1 else _('Re-examinations 3rd period')).lower()
            log_list.append(''.join((c.STRING_SPACE_05, str(_('has')), ' ', str(reex03_count), ' ', cpt)))
        if thumbrule_count:
            cpt = str(_('thumb rule is applied') if thumbrule_count == 1 else _('thumb rules are applied'))
            log_list.append(''.join((c.STRING_SPACE_05, str(thumbrule_count), ' ', cpt)))
        if thumbrule_combi:
            log_list.append(''.join((c.STRING_SPACE_05,str(_('The thumb rule is applied to the combination subjects.')))))




