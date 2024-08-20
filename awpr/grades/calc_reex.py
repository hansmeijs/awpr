
# PR2021-11-19

from django.contrib.auth.decorators import login_required
from django.db import connection

from django.http import HttpResponse
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, pgettext_lazy, gettext, gettext_lazy as _
from django.views.generic import View

from timeit import default_timer as timer

from decimal import Decimal
from accounts import views as acc_view
from accounts import  permits as acc_prm

from awpr import constants as c
from awpr import settings as s
from awpr import functions as af

from grades import calculations as grade_calc
from grades import calc_results as calc_res
from students import functions as stud_fnc
from students import views as stud_view

import json

import logging
logger = logging.getLogger(__name__)


def calcreex_get_students_cascade_dict_v2(examyear, school, department, level,
            sel_classes, include_class_blank, sortby_class, student_pk_list=None):
    # PR2023-04-06 PR2023-04-22 PR2023-06-06 PR2024-06-16
    # only called by GradeDownloadShortGradelist

    # NOTE: don't forget to filter studsubj.deleted = False and grade.deleted = False!! PR2021-03-15

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- calcreex_get_students_cascade_dict_v2 -----')
        logger.debug('    student_pk_list: ' + str(student_pk_list))

#------------------------
    # fields in student_field_list and studsubj_field_list are added to student_dict in create_stud_dict
    student_field_list = ('stud_id',
                          # TOD check which one can be removed: 'ey_code', 'examyear_code'
                          'country', 'ey_code', 'examyear_code', 'examyear_txt',
                          'school_name', 'school_code', 'islexschool',
                          'dep_name', 'depbase_code', 'dep_abbrev', 'has_profiel', # is dep.has_profiel
                          'lvl_name', 'lvlbase_code', 'level_req', 'sct_name', 'sctbase_code',

                          # TODO check if id-fields are in use
                          'dep_id', 'lvl_id', 'sct_id', 'scheme_id',

                          'examnumber', 'iseveningstudent', 'islexstudent', 'bis_exam', 'partial_exam', 'withdrawn',
                          'classname',

                          'ep01_result', 'ep02_result', 'result',
                          'gl_ce_avg', 'gl_combi_avg', 'gl_final_avg',

                          # these rules are stored in scheme:
                          'rule_avg_pece_sufficient', 'rule_avg_pece_notatevlex',
                          'rule_core_sufficient', 'rule_core_notatevlex',

                          # these are calculated fields, don't get value from student record:
                          # 'exemption_count', 'sr_count', 'reex_count', 'reex03_count', 'thumbrule_count',
                          )

    studsubj_field_list = ('subject_id', 'subjbase_id', 'subj_sequence',
                           'subjbase_code', 'subj_name_nl', 'subjtype_abbrev', 'sjtpbase_code',
                           'gradetype', 'weight_se', 'weight_ce', 'multiplier', 'is_combi',

                           # note:
                           # si.thumb_rule = True means: thumbrule is allowed for this subject
                           # studsubj.is_thumbrule = True means: student has applied thumbrule for this subject

                           # from schemeitem:
                           'is_core_subject', 'is_mvt', 'is_wisk', 'sr_allowed', 'no_ce_years', 'thumb_rule',
                           'rule_grade_sufficient', 'rule_gradesuff_notatevlex',

                           # from studsubj:
                           'schemeitem_id',
                           'is_extra_nocount', 'is_extra_counts', 'exemption_year', 'is_thumbrule', 'has_sr',

                           'gl_examperiod',
                           'gl_sesrgrade', 'gl_pecegrade',
                           'gl_finalgrade', 'gl_use_exem',
                           'gl_no_input',

                           # PR2024-06-19 gl_ni_sesr and gl_ni_pece are added to put '---' in short gradelist instead of empty grade
                           'gl_ni_sesr', 'gl_ni_pece',

                           # these will be calculated, dont get them from table:
                           # 'has_exemption', 'has_sr', 'has_reex', 'has_reex03',

                           )

    def get_sql():

        # values of sel_layout are:"none", "level", "class", "cluster"
        # "none" or None: all students of subject on one form
        # "level:" seperate form for each leeerweg
        #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
        #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

        sql_list = ["SELECT stud.id AS stud_id, studsubj.id AS studsubj_id,",
                    "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, stud.classname,",
                    "stud.extrafacilities, stud.iseveningstudent, stud.islexstudent, stud.bis_exam, stud.partial_exam, stud.withdrawn,",
                    "stud.exemption_count, stud.sr_count, stud.reex_count, stud.reex03_count, stud.thumbrule_count,",

                    "stud.gl_ce_avg, stud.gl_combi_avg, stud.gl_final_avg, stud.result,",

                    "stud.ep01_result, stud.ep02_result, stud.result,",

                    "school.name AS school_name, school.islexschool,",
                    "sb.code AS school_code, depbase.code AS depbase_code,",
                    "ey.code AS examyear_code, country.name AS country,",

                    "dep.id AS dep_id, lvl.id AS lvl_id, sct.id AS sct_id, stud.scheme_id AS stud_scheme_id,",
                    "dep.name AS dep_name, dep.abbrev AS dep_abbrev, dep.level_req, dep.has_profiel,",

                    # "lvl.name AS lvl_name, sct.name AS sct_name,",
                    "lvlbase.code AS lvlbase_code, sctbase.code AS sctbase_code,",

                # these fileds are stored in studsubj_dict:
                    "subj.id AS subject_id, subj.base_id AS subjbase_id, subj.sequence AS subj_sequence,",
                    "subjbase.code AS subjbase_code, subj.name_nl AS subj_name_nl,",

                    "subjtype.abbrev AS subjtype_abbrev, sjtpbase.code AS sjtpbase_code,",

                    "si.gradetype, si.weight_se, si.weight_ce, si.multiplier, si.is_combi,",
                    "si.is_core_subject, si.is_mvt, si.is_wisk, si.sr_allowed, si.no_ce_years, si.thumb_rule,",
                    "si.rule_grade_sufficient, si.rule_gradesuff_notatevlex,",
                    "si.scheme_id AS si_scheme_id, ",

                    "scheme.rule_avg_pece_sufficient, scheme.rule_avg_pece_notatevlex,",
                    "scheme.rule_core_sufficient, scheme.rule_core_notatevlex,",

                    "studsubj.schemeitem_id,",
                    "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.exemption_year, studsubj.is_thumbrule,",
                    "studsubj.has_sr,"
                    # these will be calculated:
                    # "studsubj.has_exemption, studsubj.has_reex, studsubj.has_reex03,",
                    
                    "studsubj.gl_examperiod,",
                    "studsubj.gradelist_sesrgrade AS gl_sesrgrade, studsubj.gradelist_pecegrade AS gl_pecegrade,",
                    "studsubj.gradelist_finalgrade AS gl_finalgrade, studsubj.gradelist_use_exem AS gl_use_exem,",
                    "(studsubj.gl_ni_se OR studsubj.gl_ni_sr OR studsubj.gl_ni_pe OR studsubj.gl_ni_ce) AS gl_no_input,",

                    # PR2024-06-19 gl_ni_sesr and gl_ni_pece are added to put '---' in short gradelist instead of empty grade
                    "(studsubj.gl_ni_se OR studsubj.gl_ni_sr) AS gl_ni_sesr,",
                    "(studsubj.gl_ni_pe OR studsubj.gl_ni_ce) AS gl_ni_pece,",

                    # these are stred in dict with key = examperiod
                    "grd.examperiod,",
                    "grd.segrade, grd.srgrade, grd.pegrade, grd.cegrade,",
                    "grd.sesrgrade, grd.pecegrade, grd.finalgrade",

                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",

                    "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                    "INNER JOIN subjects_subjecttype AS subjtype ON (subjtype.id = si.subjecttype_id)",
                    "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = subjtype.base_id)",

                    "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                    "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                    "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                    "INNER JOIN schools_country AS country ON (country.id = ey.country_id)",

                    # PR2024-06-17 link scheme to schemeitem instead of student
                    # check if  stud.scheme_id is same as si.scheme_id happens in this function
                    # was: "INNER JOIN subjects_scheme AS scheme ON (scheme.id = stud.scheme_id)",
                    "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",

                    "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                    "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                    "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                    "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",
                    "LEFT JOIN subjects_sectorbase AS sctbase ON (sctbase.id = sct.base_id)",

                    "WHERE NOT stud.deleted AND NOT stud.tobedeleted",
                    "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted",
                    "AND NOT grd.deleted AND NOT grd.tobedeleted",

                    "AND ey.id = ", str(examyear.pk), "::INT ",
                    "AND school.id = ", str(school.pk), "::INT ",
                    "AND dep.id = ", str(department.pk), "::INT"
                    ]

        if student_pk_list:
            sql_list.extend(("AND stud.id IN (SELECT UNNEST(ARRAY", str(student_pk_list), "::INT[]))"))
        else:

            class_blank_clause = "stud.classname IS NULL"
            if sel_classes:
                sel_classes_clause = ''.join(
                    ("LOWER(stud.classname) IN (SELECT UNNEST(ARRAY", str(sel_classes), "::TEXT[]))"))
                if include_class_blank:
                    sql_list.extend(("AND (", sel_classes_clause, " OR ", class_blank_clause, ")"))
                else:
                    sql_list.extend(("AND ", sel_classes_clause))
            else:
                if include_class_blank:
                    sql_list.extend(("AND ", class_blank_clause))
                else:
                    sql_list.extend(("AND FALSE"))

            if level:
                sql_list.extend(("AND lvl.base_id = ", str(level.base.pk), "::INT"))

        sql_list.append("ORDER BY subj.sequence")

        sql = ' '.join(sql_list)

        if logging_on and False:
            for sql_txt in sql_list:
                logger.debug(' > ' + sql_txt)

        return sql
# - end of get_sql

    def create_new_student_dict(row):
# +++  add student_dict to students_cascade_dict if it does not exist
        stud_id = row['stud_id']
        last_name = row['lastname']
        first_name = row['firstname']
        prefix = row['prefix']
        extra_facilities = row['extrafacilities']

        if logging_on and False:
            logger.debug('    stud_id ' + stud_id)
            logger.debug('    last_name ' + last_name)

        if sortby_class:
            class_name = row['classname']
            if not class_name:
                class_name = 'zz_blank'
        else:
            class_name = 'all'

        full_name = stud_fnc.get_full_name(
            last_name=last_name,
            first_name=first_name,
            prefix=prefix,
            has_extrafacilities=extra_facilities
        )

        lastname_firstname_initials = stud_fnc.get_lastname_firstname_initials(
            last_name=last_name,
            first_name=first_name,
            prefix=prefix,
            has_extrafacilities=extra_facilities
        )
        # if logging_on:
        #    logger.debug(' +++++++ ' + str(full_name))

        student_dict = {
            'fullname': full_name,
            'lastname_firstname_initials': lastname_firstname_initials,
            'lastname': last_name,
            'firstname': first_name,
            'ep01_result': row['ep01_result'],
            'ep02_result': row['ep02_result'],
            'result': row['result'],
            'extrafacilities': extra_facilities,
            # c_ep2 etc is to count reex reex3 and exemp
            'c_ep2': 0,
            'c_ep3': 0,
            'c_ep4': 0,
            'subj_list': [], # to be replaced by subj_dict
            'subj_dict': {}
        }
        # add values of student fields to student_dict
        for field in student_field_list:
            student_dict[field] = row.get(field)

        if class_name not in classes_dict:
            classes_dict[class_name] = [(stud_id, last_name, first_name)]
            classname_list.append(class_name)
        else:
            classes_dict[class_name].append((stud_id, last_name, first_name))

        return student_dict
# - end of create_new_student_dict

    def create_new_studsubj_dict(row, student_dict):

        # - add subj_code: subject_id to student_dict['subj_list']. Used to order subjects by subj_code
        # - add has_ce, used to loop through subjects with ce
        # 'subj_list': [('entl', 33134, 1, 1), ('asw', 33134, 1, 1), ...]

        subjbase_code = row.get('subjbase_code') or '-'

        sj_dict = (
            subjbase_code,
            row['studsubj_id'],
            row['weight_se'],
            row['weight_ce'],
            row['is_combi'],
            row.get('sequence') or 9999
        )

        subj_list = student_dict['subj_list'] # to be replaced by subj_dict
        item_found = False
        for sj in subj_list:
            if subjbase_code == sj[0]:
                item_found = True
                break
        if not item_found:
            subj_list.append(sj_dict)

        subj_dict = student_dict['subj_dict']
        if subjbase_code not in subj_dict:
            subj_dict[subjbase_code] = sj_dict

        studsubj_dict = {
            'subjbase_code': subjbase_code
        }

        # put values of studsubj_field_list fields in studsubj_dict
        for field in studsubj_field_list:
            studsubj_dict[field] = row[field]

        #####################
        # - check if studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.gradelist_use_exem is True
        # if so: add 'has_extra_nocount' = True to student-dict
        # used to add footnote in gradelist
        info_list = []
        if row['is_extra_nocount']:
            info_list.append('+')
            student_dict['has_extra_nocount'] = True
        if row['is_extra_counts']:
            info_list.append('++')
            student_dict['has_extra_counts'] = True
        if row['is_thumbrule']:
            info_list.append('d')
            student_dict['has_thumbrule'] = True
        if row['gl_use_exem']:
            info_list.append('vr')
            student_dict['has_use_exem'] = True

        gl_examperiod = row['gl_examperiod']
        if gl_examperiod == c.EXAMPERIOD_SECOND:
            info_list.append('her')
            student_dict['has_use_reex'] = True
        elif gl_examperiod == c.EXAMPERIOD_THIRD:
            info_list.append('her 3e tv')
            student_dict['has_use_reex3'] = True

        # suffix contains (vr), her) etc
        suffix = None
        if info_list:
            info_txt = ', '.join(info_list)
            suffix = ''.join((' (', info_txt, ')'))
        studsubj_dict['suffix'] = suffix

        # count 'has_exemption', 'has_sr', 'has_reex', 'has_reex03'
        # count 'is_extra_nocount'
        # count 'is_extra_counts'
        # count 'is_thumbrule'
        # - add gl_pecegrade, only when weight_ce > 0 and not is_combi
        # - add multiplier to count dict (multiplier =1, except when sectorprogramma PBL)
        # - add gl_finalgrade * multiplier to c_3, add core subj to 'core4', 'core5',
        # - add subj_code and final grade to info_pece:
        # - add subj to subj_insuff when rule applies and grade is not 'v' or 'g' (finalgrade is not numeric)
        if logging_on:
            logger.debug('    ZZZ studsubj_dict: ' + str(studsubj_dict))

        return studsubj_dict
# - end of create_new_studsubj_dict

    def create_student_studsubj_dict(row):
        # PR2023-06-06 PR2024-06-16
        if logging_on:
            logger.debug(' ---------------  create_student_studsubj_dict  ---------------')
            logger.debug('    row: ' + str(row))

        stud_id = row['stud_id']
        if logging_on:
            logger.debug('    stud_id: ' + str(stud_id))

# +++  create student_dict and add it to students_cascade_dict if it does not exist
        if stud_id not in students_cascade_dict:
            students_cascade_dict[stud_id] = create_new_student_dict(row)

# +++  get student_dict  from students_cascade_dict
        student_dict = students_cascade_dict.get(stud_id)

# count exemption(c_ep4), reex(c_ep2), reex03(c_ep3)
        # PR 2022-06-09 debug: count exemp, reex, reex3
        # is safer than getting it from student row
        examperiod = row['examperiod']
        if examperiod in range(2, 5):
            key_str = 'c_ep' + str(examperiod)
            student_dict[key_str] += 1

 # - add failed student to failed_student_pk_list, to calculate reex later
        # PR2024-06-17 to be on the safe side: check ep01_result and result
        if row['ep01_result'] == c.RESULT_FAILED: #  or row['result'] == c.RESULT_FAILED:
            if stud_id not in failed_student_pk_list:
                failed_student_pk_list.append(stud_id)
# +++  end of add student_dict to students_cascade_dict

# +++  create studsubj_dict and add it to student_dict if it does not exist
        studsubj_id = row['studsubj_id']
        if studsubj_id not in student_dict:
            student_dict[studsubj_id] = create_new_studsubj_dict(row, student_dict)

        studsubj_dict = student_dict[studsubj_id]

# - add grade per examperiod to dict with examperiod (integer) as key
        studsubj_dict[row['examperiod']] = {
            'se': row['segrade'],
            'sr': row['srgrade'],
            'sesr': row['sesrgrade'],
            'pe': row['pegrade'],
            'ce': row['cegrade'],
            'pece': row['pecegrade'],
            'final': row['finalgrade']
        }

        # PR2024-06-18 check if scheme_id in table student and in table schemeitem are the same - should always be the case

        if row['stud_scheme_id'] != row['si_scheme_id']:
            student_dict['has_scheme_error'] = True

        if row['gl_no_input']:
            student_dict['no_input'] = True
        # count 'has_exemption', 'has_sr', 'has_reex', 'has_reex03'
        # count 'is_extra_nocount'
        # count 'is_extra_counts'
        # count 'is_thumbrule'
        # - add gl_pecegrade, only when weight_ce > 0 and not is_combi
        # - add multiplier to count dict (multiplier =1, except when sectorprogramma PBL)
        # - add gl_finalgrade * multiplier to c_3, add core subj to 'core4', 'core5',
        # - add subj_code and final grade to info_pece:
        # - add subj to subj_insuff when rule applies and grade is not 'v' or 'g' (finalgrade is not numeric)

        if logging_on:
            logger.debug('  YYYY studsubj_dict: ' + str(studsubj_dict))

# - end of create_student_studsubj_dict

    #---------------------

    # values of sel_layout are:"none", "level", "class", "cluster"
    # "none" or None: all students of subject on one form
    # "level:" seperate form for each leeerweg
    #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
    #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

    failed_student_pk_list = []
    grade_dictlist_sorted = []
    students_cascade_dict = {}

    classname_list = []
    classes_dict = {}

    sql = get_sql()
    starttime = timer()

    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = af.dictfetchall(cursor)

    if logging_on:
        elapsed_seconds = (timer() - starttime)
        logger.debug('   cursor.execute elapsed_milliseconds: ' + str(elapsed_seconds * 1000))
        #for row in rows:
        #    logger.debug('    row: ' + str(row))

    if rows:
        starttime = timer()
        for row in rows:
            create_student_studsubj_dict(row)

        if logging_on:
            elapsed_seconds = (timer() - starttime)
            logger.debug('   create_student_studsubj_dict elapsed_milliseconds: ' + str(elapsed_seconds * 1000))

        # convert dict to sorted dictlist
        grade_list = list(students_cascade_dict.values())

        # sort list to sorted dictlist
        # PR2021-11-15 from https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
        #if grade_list:
        #    # was: grade_dictlist_sorted = sorted(grade_list, key=lambda d: d['fullname'])
        #    grade_dictlist_sorted = sorted(grade_list, key=lambda k: (k['lastname'], k['firstname']))

    if classname_list:
        classname_list.sort()

    if logging_on:
        #logger.debug('   grade_dictlist_sorted ' + str(grade_dictlist_sorted))
        logger.debug('   classname_list ' + str(classname_list))
        logger.debug('   failed_student_pk_list ' + str(failed_student_pk_list))

    """
    students_cascade_dict: {
        9328: {'fullname': 'Ogenio, Liliana Elisabeth', 'lastname_firstname_initials': 'Ogenio, Liliana E.', 'lastname': 'Ogenio', 'firstname': 'Liliana Elisabeth', 
        'result': 0, 'extrafacilities': False, 
        'c_ep2': 1, 'c_ep3': 0, 'c_ep4': 6, 
        'subj_list': [('pa', 77565, 1, 1, False, 9999), ('wa', 77571, 1, 1, False, 9999), ('na', 77567, 1, 1, False, 9999), ('sk', 77568, 1, 1, False, 9999), 
            ('bi', 77566, 1, 1, False, 9999), ('ec', 77572, 1, 1, False, 9999), ('asw', 77569, 1, 0, True, 9999), ('cav', 77564, 1, 0, False, 9999), 
            ('lo', 77563, 1, 0, False, 9999), ('pws', 77570, 1, 0, True, 9999), ('frtl', 78454, 1, 0, True, 9999), ('entl', 77574, 1, 1, False, 9999)], 
        'subj_dict': {'pa': ('pa', 77565, 1, 1, False, 9999), 'wa': ('wa', 77571, 1, 1, False, 9999), 'na': ('na', 77567, 1, 1, False, 9999), 
            'sk': ('sk', 77568, 1, 1, False, 9999), 'bi': ('bi', 77566, 1, 1, False, 9999), 'ec': ('ec', 77572, 1, 1, False, 9999), 
            'asw': ('asw', 77569, 1, 0, True, 9999), 'cav': ('cav', 77564, 1, 0, False, 9999), 'lo': ('lo', 77563, 1, 0, False, 9999), 
            'pws': ('pws', 77570, 1, 0, True, 9999), 'frtl': ('frtl', 78454, 1, 0, True, 9999), 'entl': ('entl', 77574, 1, 1, False, 9999)}, 
        
        'stud_id': 9328, 'country': None, 'ey_code': None, 'examyear_code': 2024, 'examyear_txt': None, 'school_name': 'Kolegio Alejandro Paula', 'school_code': 'CUR16', 
        'islexschool': False, 'dep_name': 'Voorbereidend Wetenschappelijk Onderwijs', 'depbase_code': 'Vwo', 'dep_abbrev': 'V.W.O.', 
        'has_profiel': True, 'lvl_name': None, 'lvlbase_code': None, 'level_req': False, 'sct_name': None, 'sctbase_code': 'n&g',
         'dep_id': 18, 'lvl_id': None, 'sct_id': 37, 'scheme_id': 152, 'examnumber': '2005022501', 
         'iseveningstudent': False, 'islexstudent': False, 'bis_exam': True, 'partial_exam': False, 'withdrawn': False, 'classname': 'V6Az', 
         'gl_ce_avg': None, 'gl_combi_avg': '7', 'gl_final_avg': None, 
         'has_use_exem': True, 
         
         77565: {'subjbase_code': 'pa', 
                    'ep': {4: {'sesr': '8.1', 'pece': '8.1', 'final': '8.1'}, 
                            1: {'sesr': '2.3', 'pece': '2.3', 'final': '2.3'}}, 
                    'subject_id': 329, 'subjbase_id': 118, 'subj_sequence': 20, 'subj_name_nl': 'Papiamentu', 
                    'subjtype_abbrev': 'Gemeensch.', 'sjtpbase_code': 'gmd', 
                    'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 
                    'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 
                    'no_ce_years': '2020', 'thumb_rule': False, 
                    'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 
                    'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 
                    'rule_core_sufficient': True, 'rule_core_notatevlex': False, 
                    'schemeitem_id': 3787, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': 2023, 
                    'is_thumbrule': False, 'has_sr': False, 
                    'gl_examperiod': 4, 'gl_sesrgrade': '8.1', 'gl_pecegrade': '6.4', 'gl_finalgrade': '7', 
                    'gl_use_exem': True, 'gl_no_input': False}, 

    """
    return  students_cascade_dict, classname_list, classes_dict, failed_student_pk_list



# - end of calcreex_get_students_cascade_dict_v2


def calcreex_create_totals_in_stud_dict(student_dict):
    # PR2023-04-26 PR2024-06-16
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ---------------  calcreex_create_totals_in_stud_dict  ---------------')
        logger.debug('   student_dict ' + str(student_dict))

    """
    # PR224-06-13 Yvette Halley / Nancy Josephina: add rule sectorprgram as of 2025
    LANDSBESLUIT, HOUDENDE ALGEMENE MAATREGELEN, van de 11de juli 2022 tot wijziging van het Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o
    Artikel I
    B Artikel 36 komt als volgt te luiden: 1. De kandidaat die eindexamen v.s.b.o. heeft afgelegd, is geslaagd indien hij: a. voor al zijn vakken waarvoor een eindcijfer is vastgesteld, het eindcijfer 6 of hoger heeft behaald, b. voor ten hoogste één van zijn examenvakken het eindcijfer 5 heeft behaald en voor zijn overige examenvakken een 6 of hoger, of c. voor ten hoogste één van zijn examenvakken het eindcijfer 4 heeft behaald en voor zijn overige examenvakken een 6 of hoger waarvan ten minste één 7 of hoger, of d. voor twee van zijn examenvakken het eindcijfer 5 heeft behaald en voor zijn overige examenvakken een 6 of hoger waarvan ten minste één 7 of hoger, 
    >>> met dien verstande dat het eindcijfer van het sectorprogramma in de praktisch basisgerichte leerweg dan wel de praktisch kadergerichte leerweg een voldoende dient te zijn.
    """

# first reset all total fields in studentdict
    count_fields = (
        'c_subj', 'c_exemption', 'c_sr', 'c_reex', 'c_reex03','c_extra_nocount', 'c_extra_counts', 'c_thumbrule',
    # totals are stored as Decimal datatype, counts are stored as integer
        'c3', 'c4', 'c5', 'c6', 'c7',
         # 2024-06-16 added:
        'spr_insuff',
        'core4', 'core5', 'c_ce', 'c_final', 'c_combi',
        'r_index'
    )
    for field in count_fields:
        student_dict[field] = 0
    # these are decimal fields
    for field in ('t_ce', 't_final', 't_combi'):
        student_dict[field] = '0'

    for field in ('avg_ce_detail', 'avg_final_detail' ,'combi_detail', 'subj_insuff'):
        student_dict[field] = []

    for field in ('avg_ce_info', 'avg_final_info', 'combi_info', 'r_info', 'r_fail_info', 'r_nores_info'):
        student_dict[field] = {}

    for field in ('avg_ce', 'avg_final', 'avg_combi'):
        student_dict[field] = None

    for field in ('no_input', 'thumbrule_combi'):
        student_dict[field] = False

    if logging_on:
        logger.debug('')
        logger.debug(' +++++++ ' + str(student_dict.get('fullname') + ' +++++++ '))
    # don't reset subj_list

# 'subj_list': [('asw', 35314, 1, 0), ('pws', 35315, 1, 0), ('bi', 35311, 1, 1),
    subj_list = student_dict.get('subj_list') or []
    for subj_tuple in subj_list:
        # studsubject keys are integer, other keys are string type
        studsubj_pk = subj_tuple[1]
        studsubj_dict = student_dict.get(studsubj_pk)

        if logging_on:
            logger.debug('   subj_tuple ' + str(subj_tuple))
            logger.debug('   studsubj_dict ' + str(studsubj_dict))

        if studsubj_dict:
            gl_examperiod = studsubj_dict.get('gl_examperiod') or 1
            is_combi = studsubj_dict.get('is_combi') or False
            gradetype = studsubj_dict.get('gradetype') or False
            is_core_subject = studsubj_dict.get('is_core_subject') or False
            is_extra_nocount = studsubj_dict.get('is_extra_nocount') or False
            is_thumbrule = studsubj_dict.get('is_thumbrule') or False

            # rule_grade_sufficient applies when rule_grade_sufficient = True,
            # except when evelex student and rule_gradesuff_notatevlex
            # not when is_extra_nocount, not when is_thumbrule
            rule_grade_suff_applies = False
            if not is_extra_nocount and not is_thumbrule:
                if studsubj_dict.get('rule_grade_sufficient'):
                    if studsubj_dict.get('rule_gradesuff_notatevlex'):
                        if not studsubj_dict.get('iseveningstudent', False) and not studsubj_dict.get('islexstudent', False):
                            rule_grade_suff_applies = True
                    else:
                        rule_grade_suff_applies = True

        # - multiplier=1, except when sectorprogramma PBL, then it is 2, only in Cur
            multiplier = studsubj_dict.get('multiplier') or 1


        # - add multiplier to count subjects dict (multiplier=1, except when sectorprogramma PBL)
            student_dict['c_subj'] = multiplier + (student_dict.get('c_subj') or 0)

            subjbase_code = studsubj_dict.get('subjbase_code')
            subject_id = studsubj_dict.get('subject_id')
            weight_se = studsubj_dict.get('weight_se') or 0
            weight_ce = studsubj_dict.get('weight_ce') or 0

            if logging_on:
                logger.debug(' +++++++ ' + subjbase_code + ' +++++++ ' )

        # no_input is True if any of these are True: gl_ni_se OR gl_ni_sr OR gl_ni_pe OR gl_ni_ce
            if studsubj_dict.get('no_input'):
                student_dict['no_input'] = True

        # count 'has_exemption', 'has_sr', 'has_reex', 'has_reex03'
            for field in ('has_exemption', 'has_sr', 'has_reex', 'has_reex03'):
                if studsubj_dict.get(field):
                    key_str = 'c_' + field[4:]
                    student_dict[key_str] = 1 + (student_dict.get(key_str) or 0)

        # count 'is_extra_nocount'
            if studsubj_dict.get('is_extra_nocount'):
                student_dict['c_extra_nocount'] = 1 + (student_dict.get('c_extra_nocount') or 0)

        # count 'is_extra_counts'
            if studsubj_dict.get('is_extra_counts'):
                student_dict['c_extra_counts'] = 1 + (student_dict.get('c_extra_counts') or 0)

        # count 'is_thumbrule'
            # combi thumbrule counts as one, put thumbrule_combi = True in student_dict if any combi has thumbrule
            if studsubj_dict.get('is_thumbrule'):
                if is_combi:
                    student_dict['thumbrule_combi'] = True
                else:
                    student_dict['c_thumbrule'] = 1 + (student_dict.get('c_thumbrule') or 0)

        # - add gl_pecegrade, only when weight_ce > 0 and not is_combi
            if weight_ce and not is_combi:
                gl_pecegrade = studsubj_dict.get('gl_pecegrade') or '0'
                # skip ovg ce grade, (ovg should not occur in ce)
                if gl_pecegrade:
                    gl_pecegrade_nodots = gl_pecegrade.replace('.', '')
                    if gl_pecegrade_nodots.isnumeric():

            # - add multiplier to 'c_ce' (multiplier =1, except when sectorprogramma PBL)
                        student_dict['c_ce'] = multiplier + (student_dict.get('c_ce') or 0)

        # - add gl_pecegrade * multiplier to t_combi or t_final (multiplier =1, except when sectorprogramma PBL)
                        student_dict['t_ce'] = Decimal(gl_pecegrade) * Decimal(str(multiplier)) + Decimal(student_dict.get('t_ce'))

        # - add '2x','vr','h','h3' to grade
                        gl_pecegrade_str = gl_pecegrade.replace('.', ',')
                        gl_pecegrade_extension = calc_res.get_gradeinfo_extension(multiplier, gl_examperiod)
                        if gl_pecegrade_extension:
                            gl_pecegrade_str += gl_pecegrade_extension

        # - add subjbase_code and grade to avg_ce_detail:
                        student_dict['avg_ce_detail'].append(''.join((subjbase_code, ':', str(gl_pecegrade_str))))

        # - add final grade to total, only when isnumeric.
            gl_finalgrade = studsubj_dict.get('gl_finalgrade') or '0'

            # note: '5.6'.isnumeric() = False, but final grades are integers so it doesn't matter
            if gl_finalgrade.isnumeric():
                # add finalgrade to total finalgrade from dict and put new total in dict

            # - add gl_finalgrade * multiplier to t_combi or t_final (multiplier =1, except when sectorprogramma PBL)
                key_total = 't_combi' if is_combi else 't_final'
                student_dict[key_total] = Decimal(gl_finalgrade) * Decimal(str(multiplier)) + Decimal(
                    student_dict.get(key_total))

        # - add multiplier to count dict (multiplier =1, except when sectorprogramma PBL)
                key_count = 'c_combi' if is_combi else 'c_final'
                student_dict[key_count] = multiplier + (student_dict.get(key_count) or 0)

        # - add gl_finalgrade * multiplier to c_3, add core subj to 'core4', 'core5',
                calcreex_count_final_3457_core(student_dict, gl_finalgrade, gradetype,
                                               is_combi, is_core_subject, multiplier, is_extra_nocount, is_thumbrule)

        # - add final grade to info_pece:
                gl_finalgrade_str = gl_finalgrade.replace('.', ',') if gl_finalgrade else '-'

            # - add '2x','vr','h','h3' to grade
                gradeinfo_extension = calc_res.get_gradeinfo_extension(multiplier, gl_examperiod)
                if gradeinfo_extension:
                    gl_finalgrade_str += gradeinfo_extension

            # - add subjbase_code and grade to avg_final_detail or combi_detail
                key_detail = 'combi_detail' if is_combi else 'avg_final_detail'
                student_dict[key_detail].append(''.join((subjbase_code, ':', str(gl_finalgrade_str))))

            # - add subj to subj_insuff when rule applies and grade < 6  (finalgrade is numeric)
                if rule_grade_suff_applies:
                    gl_finalgrade_int = int(gl_finalgrade)
                    if gl_finalgrade_int < 6:
                        student_dict['subj_insuff'].append(studsubj_dict.get('subj_name_nl'))

        # if gl_finalgrade is not numeric:
            else:
            # - add subj to subj_insuff when rule applies and grade is not 'v' or 'g' (finalgrade is not numeric)
                if rule_grade_suff_applies:
                    if gl_finalgrade and gl_finalgrade.lower() not in ('v', 'g'):
                        student_dict['subj_insuff'].append(studsubj_dict.get('subj_name_nl'))

            if logging_on :
                logger.debug('  studsubj_dict: ' + str(studsubj_dict))
# - end of calcreex_create_totals_in_stud_dict


def calc_student_reex_result_v2(department, student_dict, write_log, log_list):
    # PR2023-04-27 PR2023-06-07 PR2024-06-16
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------------  calc_student_reex_result_v2  ---------------')
        logger.debug('    ' + str(student_dict['fullname']))

    dep_level_req = department.level_req
    depbase_code = str(department.base.code).lower()
    depbase_is_vsbo = (depbase_code == 'vsbo')

    no_input = student_dict.get('no_input', False)

# - get isevlex and full name with (evening / lex student)
    scheme_error, isevlexstudent, partial_exam, withdrawn, full_name = calcreex_get_isevlex_isreex_fullname(student_dict)

# - get result rules from scheme
    rule_avg_pece_sufficient, rule_core_sufficient = \
        calcreex_get_rules_from_scheme(student_dict, isevlexstudent)

# - student name header
    log_list_student_header(student_dict, full_name, write_log, log_list)

# - A.3c. skip when scheme not found, put err_msg in loglist
# PR2022-06-18 debug: msut give result 'no result, therefore don't skip student
    if scheme_error:
        log_list_add_scheme_notfound(dep_level_req, write_log, log_list)

# - add number of sr, reex, reex03 to log_list
    #log_list_reex_count(student_dict, write_log, log_list)

# - keep track of reex with the lowest ranking
    min_ranking = None
    preferred_studsubj_pk = None
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# - loop through subjects with ce

    subj_list = student_dict.get('subj_list')
    # 'subj_list': [('entl', 33134, 1, 1 ), ('asw', 33135, 1, 0), ...]
    # 'subj_list': (subj_code, studsubj_pk, weight_se, weight_ce)

    subj_list_sorted = sorted(subj_list, key=lambda d: d[0])

    for subj_tuple in subj_list_sorted:
        # subj_tuple:  ('bi', 77566, 1, 1, False, 160)
        # subj_tuple:  ('bi', 77566, 1, 1, False, 160)
        weight_ce = subj_tuple[3]
        if logging_on:
            logger.debug(' ---------------------  ')
            logger.debug('     subj_tuple:  ' + str(subj_tuple))

        if weight_ce > 0:
            subj_name_nl = subj_tuple[0]
            studsubj_pk = subj_tuple[1]
            weight_se = subj_tuple[2]

            studsubj_dict = student_dict.get(studsubj_pk)
            if logging_on:
                logger.debug('     studsubj_dict:  ' + str(studsubj_dict))
            """
            studsubj_dict:  {
            'subjbase_code': 'pa', 'subject_id': 329, 'subjbase_id': 118, 'subj_sequence': 20, 'subj_name_nl': 'Papiamentu', 
            'subjtype_abbrev': 'Gemeensch.', 'sjtpbase_code': 'gmd', 
            'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 
            'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 
            'no_ce_years': '2020', 'thumb_rule': False, 
            'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 
            'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 
            'schemeitem_id': 3787, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': 2023, 
            'is_thumbrule': False, 'has_sr': False, 
            'gl_examperiod': 4, 'gl_sesrgrade': '8.1', 'gl_pecegrade': '6.4', 'gl_finalgrade': '7', 
            'gl_use_exem': True, 'gl_no_input': False, 
            4: {'se': '8.1', 'sr': None, 'sesr': '8.1', 'pe': None, 'ce': '6.4', 'pece': '6.4', 'final': '7'}, 
            1: {'se': '2.3', 'sr': None, 'sesr': '2.3', 'pe': None, 'ce': '5.2', 'pece': '5.2', 'final': '4'}}
            """
        # PR2024-06-13 Hans Vlinkervleugel: student with exemption who did not take an exam got still possible retake for that subject.
            # cause: gl_finalgrade is used to compare, but that can be the exemption grade.
            # solution: use grdes of fist examperiod, but:
            # - a student wh was sick has segrade but no cegrade. Must still be included, use ce-grade 1
            # - praktex subject may already have had a retake and a grade in exempriod 2, must be taken in account
            # TODO figure out how to deal with this
            # maybe:
            # if not use_exem > can use gl_grade
            # if use_exam: us ep01 grade, check if already reex, min grdae is exem grade

        # - skip if subject has already a reex or reex03 with a final grade
            # also skip when use_exem and student has no SE this year, means student did no exam this year
            # don't check on final grade, student might have been sick and did no CE
            gl_use_exem = studsubj_dict['gl_use_exem']

        # - PR2024-06-19 als skip when student already has a reex but without reex grade: skip

            ep01_sesrgrade, ep01_pecegrade, ep02_finalgrade , ep03_finalgrade = None, None, None, None
            if c.EXAMPERIOD_FIRST in studsubj_dict:
                ep01_sesrgrade = studsubj_dict[c.EXAMPERIOD_FIRST]['sesr']
                ep01_pecegrade = studsubj_dict[c.EXAMPERIOD_FIRST]['pece']
            if c.EXAMPERIOD_SECOND in studsubj_dict:
                ep02_finalgrade = studsubj_dict[c.EXAMPERIOD_SECOND]['final']
            if c.EXAMPERIOD_THIRD in studsubj_dict:
                ep03_finalgrade = studsubj_dict[c.EXAMPERIOD_THIRD]['final']

            has_reex_taken = ep02_finalgrade is not None or ep03_finalgrade is not None
            has_no_sesrgrade = ep01_sesrgrade is None

            if logging_on:
                logger.debug('   >>>>>  gl_use_exem: ' + str(gl_use_exem))
                logger.debug('   >>>>>  ep01_sesrgrade: ' + str(ep01_sesrgrade))
                logger.debug('   >>>>>  has_reex_taken: ' + str(has_reex_taken))
                logger.debug('   >>>>>  has_no_sesrgrade: ' + str(has_no_sesrgrade))
                logger.debug('   >>>>>  no_input: ' + str(no_input))

            if not has_reex_taken and not has_no_sesrgrade and not no_input:
        # - if exemption is used to calculate gl_grade and student has SE this year:
                # use grade of this year ep01 instead of gl_grade
                # but always print gl_grades on short gradeliist
                gl_sesrgrade = studsubj_dict['gl_sesrgrade']
                gl_pecegrade = studsubj_dict['gl_pecegrade']
                gl_finalgrade = studsubj_dict['gl_finalgrade']

                if studsubj_dict.get('gl_use_exem'):
                    if logging_on:
                        logger.debug('   ----  use grade of this year ep01 ')
                    ori_sesrgrade = ep01_sesrgrade
                    ori_pecegrade = ep01_pecegrade
                else:
        # get original values
                    ori_sesrgrade = gl_sesrgrade
                    ori_pecegrade = gl_pecegrade

                if ori_sesrgrade is not None:
                    ori_sesr_decimal = Decimal(ori_sesrgrade)

                    # in 2020 and 2021 not all subjects had central exam. Set min_grade to '1' in that case, show '-' in log
                    ori_pece_decimal = Decimal(ori_pecegrade if ori_pecegrade else '1')

                    if logging_on:
                        logger.debug('   =====  ori_sesr_decimal: ' + str(ori_sesr_decimal))
                        logger.debug('   =====  ori_pece_decimal: ' + str(ori_pece_decimal))

                    decimal_10 = Decimal('10')
                    decimal_2 = Decimal('2')
                    exit_loop = False

                # - count is an extra safety to prevent infinite loops, decuct 1 after each loop till 0
                    count = 10

                # - start the loop with max_pece = 10 and test_pece = 10 and min_pece = ori_pece
                    min_pece_decimal = ori_pece_decimal
                    max_pece_decimal = decimal_10
                    test_pece_decimal = decimal_10

                    pass_is_possible = False

        # start of while loop
                    while not exit_loop:
                        old_test_pece_decimal = test_pece_decimal

                # - calculate finalgrade
                        test_finalgrade = calcreex_calc_final_grade_number(ori_sesr_decimal, test_pece_decimal,
                                                                        False, False,
                                                                        weight_se, weight_ce)

                        if logging_on:
                            logger.debug('..........:  ')
                            logger.debug('     min_pece_decimal:  ' + str(min_pece_decimal))
                            logger.debug('     max_pece_decimal:  ' + str(max_pece_decimal))
                            logger.debug('     test_pece_decimal:  ' + str(test_pece_decimal))
                            logger.debug('     test_finalgrade:  ' + str(test_finalgrade))
                        #log_list_testgrade(subj_name_nl, str(test_pece_decimal), str(test_finalgrade), write_log, log_list)

                # - replace gl_pecegrade by test_pece and gl_finalgrade by test_finalgrade
                        studsubj_dict['gl_sesrgrade'] = str(ori_sesr_decimal)
                        studsubj_dict['gl_pecegrade'] = str(test_pece_decimal)
                        studsubj_dict['gl_finalgrade'] = test_finalgrade

                # calculate counts and totals and put them in student_dict
                        calcreex_create_totals_in_stud_dict(student_dict)

            # +++ calc_student_passedfailed:
                        # - calculates combi grade for each examperiod and add it to final and count dict in student_ep_dict
                        # - calculates passed / failed for each exam period (ep1, ep2, ep3)
                        # - puts calculated result of the last examperiod in log_list
                        has_subjects = True
                        has_passed = calcreex_student_passedfailed_v2(student_dict, rule_avg_pece_sufficient, rule_core_sufficient,
                                                  withdrawn, partial_exam, has_subjects, depbase_is_vsbo, log_list)
                        if logging_on:
                            logger.debug('    ==>  has_passed:  ' + str(has_passed) + ' ' + str(type(has_passed)))

                    # - if at rhe first attempt, when ce=10, student cannot pass, pass is not possible with this subject: exit loo
                        if not pass_is_possible:
                            if has_passed:
                                pass_is_possible = True
                            else:
                                exit_loop = True
                                if logging_on:
                                    logger.debug('    ==>  exit_loop:  ' + str(exit_loop) + ' ' + str(type(exit_loop)))

                        count -= 1
                        if count < 1:
                            exit_loop = True

                # - put back original values of this subject in dict
                        if not exit_loop:
                            if has_passed:
                                max_pece_decimal = test_pece_decimal
                                min_or_max_pece_decimal = min_pece_decimal
                            else:
                                min_pece_decimal = test_pece_decimal
                                min_or_max_pece_decimal = max_pece_decimal

                            if logging_on:
                                logger.debug('  % min_pece_decimal:  ' + str(min_pece_decimal) + ' ' + str(type(min_pece_decimal)))
                                logger.debug('  % max_pece_decimal:  ' + str(max_pece_decimal) + ' ' + str(type(max_pece_decimal)))

                # - if has_passed: check lower grade, halfway between min_pece and test_pece grade
                            new_pece_decimal_notrounded = (min_or_max_pece_decimal + test_pece_decimal) / decimal_2
                            test_pece_decimal = grade_calc.round_decimal(input_decimal=new_pece_decimal_notrounded, digits=1)

                            if logging_on:
                                logger.debug('  > test_pece_decimal:  ' + str(test_pece_decimal) + ' ' + str(type(test_pece_decimal)))
                                logger.debug('  > has_passed:         ' + str(has_passed))

                            if has_passed and test_pece_decimal == old_test_pece_decimal:

                    # - passed_ values are return values when student can pass, gives minimum grade of this subjectto pass
                                studsubj_dict['passed_pecegrade'] = str(test_pece_decimal) if test_pece_decimal else None
                                #studsubj_dict['passed_finalgrade'] = test_finalgrade

                                # calc grade_ranking diff between ori_pecegrade and test_pece_decimal
                                # lowest ranking is preferred reex
                                # value of ori_pece is taken in account: from 4 to 5 is preferred above 8 to 9

                                ranking = test_pece_decimal - ori_pece_decimal + (ori_pece_decimal / Decimal('4'))

                                if min_ranking is None or ranking.compare(min_ranking) < 0:  # a.compare(b)) returns -1 if a < b
                                    min_ranking = ranking
                                    preferred_studsubj_pk = studsubj_pk
                                log_list_conclusion(subj_name_nl, str(test_pece_decimal), write_log, log_list)
                                if logging_on:
                                    logger.debug('  > BINGO test_pece_decimal:  ' + str(test_pece_decimal) + ' ' + str(
                                        type(min_or_max_pece_decimal)))

                                exit_loop = True

                        # put back original values of gl_grade.
                        #They have been replaced by test value to calculate possible reex
                        if exit_loop:
                            studsubj_dict['gl_sesrgrade'] = gl_sesrgrade
                            studsubj_dict['gl_pecegrade'] = gl_pecegrade
                            studsubj_dict['gl_finalgrade'] = gl_finalgrade
        # end of while loop

# - end of loop through subjects with ce
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # put preferred_studsubj_pk in student_dict
    if preferred_studsubj_pk:
        student_dict['preferred_studsubj_pk'] = preferred_studsubj_pk

    #if not has_subjects and log_list is not None:
    #    log_list.append(''.join((c.STRING_SPACE_05, str(_('This candidate has no subjects.')))))


    #if logging_on:
    #    logger.debug('  >>>>>>>>> student_dict  ' + str(student_dict))

# - end of calc_student_reex_result_v2


def calcreex_calc_final_grade_number(sesr_decimal, pece_decimal, sesr_noinput, pece_noinput, weight_se, weight_ce):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calcreex_calc_final_grade_number -----')
        logger.debug('     sesr_decimal: ' + str(sesr_decimal) + ' ' + str(type(sesr_decimal)))
        logger.debug('     pece_decimal: ' + str(pece_decimal) + ' ' + str(type(pece_decimal)))
        logger.debug('     sesr_noinput: ' + str(sesr_noinput))
        logger.debug('     pece_noinput: ' + str(pece_noinput))

    """
    #'+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #'+  PeCEcijferNietAfgerond = (PEcijfer + CEcijfer) / 2                       +
    #'+  PeCEcijfer             = Int(0.5 + PeCEcijferNietAfgerond x 10) / 10     +
    #'+                                                                           +
    #'+                           (SEcijfer x SEweging) + (PeCEcijfer x CEweging) +
    #'+  EindcijferNietAfgerond = ---------------------------------------------   +
    #'+                                       (SEWeging + CEweging)               +
    #'+                                                                           +
    #'+  Eindcijfer             = Int(0.5 + EindcijferNietAfgerond)               +
    #'+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    HERKANSING - Function Calculations.CalcEindcijfer_Crc_Corona
            'PR2020-05-12 eindcijfer berekening ten tijde van Corona:
        ' - in eerste tijdvak is eindcijfer gelijk aan SE cijfer
        ' - in tweede tijdvak (herkansing) is berekening als in mail Esther:
        ' - vrijstelling berekent eindcijfer op de normale manier, doorloopt de functie CalcEindcijfer_Crc
        ' - derde tijdvak is niet van toepassing

        'mail Esther ETE 1 mei 2020:
           ' Het cijfer voor de extra her-toets wordt bepaald op één decimaal en telt voor 50% mee,
           ' het eerder behaalde SE-resultaat voor dat vak ook voor 50%.
           ' Beide cijfers worden gemiddeld en dat is het nieuwe eindcijfer.
           ' Dit geldt niet als het gemiddelde resultaat lager is dan het SE-resultaat.
           ' In dat geval is het Eindcijfer gelijk aan het eerder behaalde SE-resultaat.

        'ook de op 1 decimaal afgerond eindcijfer is een return value, voor weergave op de cijferlijst.
        'daarom crcSEcijfer_na_herkansing() als byref parameter opgenomen.

        'PR2020-05-29 debug: Lorraine Wieske JPD: SE_na_herkansing verschijnt niet op cijferlijst,
        ' aparte parameter crcSEcijfer_na_herkansing() gemaakt
    """

    final_grade = None
    if not sesr_noinput and not pece_noinput:
        weight_se_decimal = Decimal(str(weight_se))
        weight_ce_decimal = Decimal(str(weight_ce))
        if sesr_decimal and pece_decimal:
            final_decimal_notrounded = (sesr_decimal * weight_se_decimal + pece_decimal * weight_ce_decimal) \
                                       / (weight_se_decimal + weight_ce_decimal)
        elif sesr_decimal:
            final_decimal_notrounded = sesr_decimal
        elif pece_decimal:
            final_decimal_notrounded = pece_decimal
        else:
            final_decimal_notrounded = None
        if logging_on:
            logger.debug('     final_decimal_notrounded: ' + str(final_decimal_notrounded) + ' ' + str(
                type(final_decimal_notrounded)))

        if final_decimal_notrounded:
            final_decimal_rounded = final_decimal_notrounded.quantize(Decimal("1"), rounding='ROUND_HALF_UP')
            if logging_on:
                logger.debug('     final_decimal_rounded: ' + str(final_decimal_rounded) + ' ' + str(
                    type(final_decimal_rounded)))
            # final_decimal_rounded is integer , so no need for: final_grade = final_dot.replace('.', ',')
            final_grade = str(final_decimal_rounded)
        else:
            final_grade = None

    if logging_on:
        logger.debug(' >>> final_grade: ' + str(final_grade) + ' ' + str(type(final_grade)))

    return final_grade
# --- end of calcreex_calc_final_grade_number


def calcreex_student_passedfailed_v2(student_dict, rule_avg_pece_sufficient, rule_core_sufficient, withdrawn, partial_exam,
                              has_subjects, depbase_is_vsbo, log_list):
    # PR2021-12-31 PR2022-06-04  PR2023-04-22
    # - calculate combi grade for each examperiod and add it to final and count dict in student_ep_dict
    # last_examperiod contains the grades that must pe put un the grade_list.
    # is reex03 when reex03 student, reex when reex student, firstperiod otherwise
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('  $$$$$$$$$$$$ --------- calcreex_student_passedfailed_v2 ---------------')
        #logger.debug(' $$$$$$$$$$$$    student_dict: ' + str(student_dict))

        #logger.debug('    withdrawn: ' + str(withdrawn) )
        #logger.debug('    partial_exam: ' + str(partial_exam) )
    """
    student_dict: {'fullname': 'Ogenio, Liliana Elisabeth', 'lastname_firstname_initials': 'Ogenio, Liliana E.', 'lastname': 'Ogenio', 'firstname': 'Liliana Elisabeth', 
    'ep01_result': 2, 'ep02_result': 0, 'result': 0, 
    'extrafacilities': False,
     'c_ep2': 1, 'c_ep3': 0, 'c_ep4': 6, 
     'subj_list': [('pa', 77565, 1, 1, False, 9999), ('wa', 77571, 1, 1, False, 9999), ('na', 77567, 1, 1, False, 9999), ('sk', 77568, 1, 1, False, 9999), ('bi', 77566, 1, 1, False, 9999), ('ec', 77572, 1, 1, False, 9999), ('asw', 77569, 1, 0, True, 9999), ('cav', 77564, 1, 0, False, 9999), ('lo', 77563, 1, 0, False, 9999), ('pws', 77570, 1, 0, True, 9999), ('frtl', 78454, 1, 0, True, 9999), ('entl', 77574, 1, 1, False, 9999), ('netl', 77573, 1, 1, False, 9999)], 'subj_dict': {'pa': ('pa', 77565, 1, 1, False, 9999), 'wa': ('wa', 77571, 1, 1, False, 9999), 'na': ('na', 77567, 1, 1, False, 9999), 'sk': ('sk', 77568, 1, 1, False, 9999), 'bi': ('bi', 77566, 1, 1, False, 9999), 'ec': ('ec', 77572, 1, 1, False, 9999), 'asw': ('asw', 77569, 1, 0, True, 9999), 'cav': ('cav', 77564, 1, 0, False, 9999), 'lo': ('lo', 77563, 1, 0, False, 9999), 'pws': ('pws', 77570, 1, 0, True, 9999), 'frtl': ('frtl', 78454, 1, 0, True, 9999), 'entl': ('entl', 77574, 1, 1, False, 9999), 'netl': ('netl', 77573, 1, 1, False, 9999)}, 
     'stud_id': 9328, 'country': 'Curaçao', 'ey_code': None, 'examyear_code': 2024, 'examyear_txt': None, 
     'school_name': 'Kolegio Alejandro Paula', 'school_code': 'CUR16', 'islexschool': False, 'dep_name': 'Voorbereidend Wetenschappelijk Onderwijs', 
     'depbase_code': 'Vwo', 'dep_abbrev': 'V.W.O.', 'has_profiel': True, 'lvl_name': None, 'lvlbase_code': None, 'level_req': False, 'sct_name': None, 
     'sctbase_code': 'n&g', 'dep_id': 18, 'lvl_id': None, 'sct_id': 37, 'scheme_id': 152, 'examnumber': '2005022501', 'iseveningstudent': False, 'islexstudent': False, 
     'bis_exam': True, 'partial_exam': False, 'withdrawn': False, 'classname': 'V6Az', 
     'gl_ce_avg': None, 'gl_combi_avg': '7', 'gl_final_avg': None, 'has_use_exem': True, 
     77565: {
        'subjbase_code': 'pa', 
        'ep': {4: {'sesr': '8.1', 'pece': '8.1', 'final': '8.1'}, 
               1: {'sesr': '2.3', 'pece': '2.3', 'final': '2.3'}}, 
        'subject_id': 329, 'subjbase_id': 118, 'subj_sequence': 20, 'subj_name_nl': 'Papiamentu', 'subjtype_abbrev': 'Gemeensch.', 
        'sjtpbase_code': 'gmd', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 
        'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': '2020', 'thumb_rule': False,
         'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 
         'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 
         'schemeitem_id': 3787, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': 2023, 
         'is_thumbrule': False, 'has_sr': False, 
         'gl_examperiod': 4, 'gl_sesrgrade': '8.1', 'gl_pecegrade': '6.4', 'gl_finalgrade': '7', 'gl_use_exem': True, 'gl_no_input': False}, 
     77571: {'subjbase_code': 'wa', 'ep': {1: {'sesr': '7.1', 'pece': '7.1', 'final': '7.1'}}, 'subject_id': 336, 'subjbase_id': 149, 'subj_sequence': 121, 'subj_name_nl': 'Wiskunde A', 'subjtype_abbrev': 'Profieldeel', 'sjtpbase_code': 'spd', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': True, 'is_mvt': False, 'is_wisk': True, 'sr_allowed': False, 'no_ce_years': '2020', 'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3813, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': None, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 1, 'gl_sesrgrade': '7.1', 'gl_pecegrade': '7.4', 'gl_finalgrade': '7', 'gl_use_exem': False, 'gl_no_input': False, 'passed_pecegrade': '7.1', 'passed_finalgrade': '7', 'passed_ranking': Decimal('1.85')}, 
     77567: {'subjbase_code': 'na', 'ep': {1: {'sesr': '6.9', 'pece': '6.9', 'final': '6.9'}}, 'subject_id': 342, 'subjbase_id': 138, 'subj_sequence': 140, 'subj_name_nl': 'Natuurkunde', 'subjtype_abbrev': 'Profieldeel', 'sjtpbase_code': 'spd', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': '2020', 'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3809, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': None, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 1, 'gl_sesrgrade': '6.9', 'gl_pecegrade': '4.7', 'gl_finalgrade': '6', 'gl_use_exem': False, 'gl_no_input': False, 'passed_pecegrade': '4.8', 'passed_finalgrade': '6', 'passed_ranking': Decimal('1.275')}, 
     77568: {'subjbase_code': 'sk', 'ep': {1: {'sesr': '5.4', 'pece': '5.4', 'final': '5.4'}}, 'subject_id': 343, 'subjbase_id': 139, 'subj_sequence': 150, 'subj_name_nl': 'Scheikunde', 'subjtype_abbrev': 'Profieldeel', 'sjtpbase_code': 'spd', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': '2020', 'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3810, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': None, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 1, 'gl_sesrgrade': '5.4', 'gl_pecegrade': '5.8', 'gl_finalgrade': '6', 'gl_use_exem': False, 'gl_no_input': False, 'passed_pecegrade': '5.9', 'passed_finalgrade': '6', 'passed_ranking': Decimal('1.55')}, 
     77566: {'subjbase_code': 'bi', 'ep': {1: {'sesr': '5.5', 'pece': '5.5', 'final': '5.5'}}, 'subject_id': 344, 'subjbase_id': 123, 'subj_sequence': 160, 'subj_name_nl': 'Biologie', 'subjtype_abbrev': 'Profieldeel', 'sjtpbase_code': 'spd', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': '2020', 'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3805, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': None, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 1, 'gl_sesrgrade': '5.5', 'gl_pecegrade': '4.3', 'gl_finalgrade': '5', 'gl_use_exem': False, 'gl_no_input': False, 'passed_pecegrade': '4.4', 'passed_finalgrade': '5', 'passed_ranking': Decimal('1.175')}, 
     77572: {'subjbase_code': 'ec', 'ep': {1: {'sesr': '7.5', 'pece': '7.5', 'final': '7.5'}}, 'subject_id': 345, 'subjbase_id': 155, 'subj_sequence': 210, 'subj_name_nl': 'Economie', 'subjtype_abbrev': 'Vrije deel', 'sjtpbase_code': 'vrd', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': '2020', 'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3817, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': None, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 1, 'gl_sesrgrade': '7.5', 'gl_pecegrade': '5.8', 'gl_finalgrade': '7', 'gl_use_exem': False, 'gl_no_input': False, 'passed_pecegrade': '5.9', 'passed_finalgrade': '7', 'passed_ranking': Decimal('1.55')}, 
     77569: {'subjbase_code': 'asw', 'ep': {4: {'sesr': '7.3', 'pece': '7.3', 'final': '7.3'}, 1: {'sesr': None, 'pece': None, 'final': None}}, 'subject_id': 352, 'subjbase_id': 142, 'subj_sequence': 600, 'subj_name_nl': 'Algemene sociale wetenschappen', 'subjtype_abbrev': 'Gemeensch.', 'sjtpbase_code': 'gmd', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 0, 'multiplier': 1, 'is_combi': True, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': None, 'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3799, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': 2023, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 4, 'gl_sesrgrade': '7.3', 'gl_pecegrade': None, 'gl_finalgrade': '7', 'gl_use_exem': True, 'gl_no_input': False}, 
     77564: {'subjbase_code': 'cav', 'ep': {1: {'sesr': None, 'pece': None, 'final': None}, 4: {'sesr': 'v', 'pece': 'v', 'final': 'v'}}, 'subject_id': 355, 'subjbase_id': 117, 'subj_sequence': 830, 'subj_name_nl': 'Culturele en artistieke vorming', 'subjtype_abbrev': 'Gemeensch.', 'sjtpbase_code': 'gmd', 'gradetype': 2, 'weight_se': 1, 'weight_ce': 0, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': None, 'thumb_rule': False, 'rule_grade_sufficient': True, 'rule_gradesuff_notatevlex': True, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3800, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': 2023, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 4, 'gl_sesrgrade': 'v', 'gl_pecegrade': None, 'gl_finalgrade': 'v', 'gl_use_exem': True, 'gl_no_input': False}, 
     77563: {'subjbase_code': 'lo', 'ep': {4: {'sesr': 'v', 'pece': 'v', 'final': 'v'}, 1: {'sesr': None, 'pece': None, 'final': None}}, 'subject_id': 357, 'subjbase_id': 116, 'subj_sequence': 900, 'subj_name_nl': 'Lichamelijke opvoeding', 'subjtype_abbrev': 'Gemeensch.', 'sjtpbase_code': 'gmd', 'gradetype': 2, 'weight_se': 1, 'weight_ce': 0, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': None, 'thumb_rule': False, 'rule_grade_sufficient': True, 'rule_gradesuff_notatevlex': True, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3790, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': 2023, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 4, 'gl_sesrgrade': 'v', 'gl_pecegrade': None, 'gl_finalgrade': 'v', 'gl_use_exem': True, 'gl_no_input': False}, 
     77570: {'subjbase_code': 'pws', 'ep': {4: {'sesr': '8.2', 'pece': '8.2', 'final': '8.2'}, 1: {'sesr': None, 'pece': None, 'final': None}}, 'subject_id': 371, 'subjbase_id': 148, 'subj_sequence': 4200, 'subj_name_nl': 'Profielwerkstuk', 'subjtype_abbrev': 'Werkstuk', 'sjtpbase_code': 'wst', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 0, 'multiplier': 1, 'is_combi': True, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': None, 'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3794, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': 2023, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 4, 'gl_sesrgrade': '8.2', 'gl_pecegrade': None, 'gl_finalgrade': '8', 'gl_use_exem': True, 'gl_no_input': False}, 
     78454: {'subjbase_code': 'frtl', 'ep': {4: {'sesr': '6.6', 'pece': '6.6', 'final': '6.6'}, 1: {'sesr': None, 'pece': None, 'final': None}}, 'subject_id': 375, 'subjbase_id': 160, 'subj_sequence': 5001, 'subj_name_nl': 'Franse taal en literatuur', 'subjtype_abbrev': 'Gemeensch.', 'sjtpbase_code': 'gmd', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 0, 'multiplier': 1, 'is_combi': True, 'is_core_subject': False, 'is_mvt': True, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': None, 'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3807, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': 2023, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 4, 'gl_sesrgrade': '6.6', 'gl_pecegrade': None, 'gl_finalgrade': '7', 'gl_use_exem': True, 'gl_no_input': False}, 'has_use_reex': True, 
     77574: {'subjbase_code': 'entl', 'ep': {2: {'sesr': '7.8', 'pece': '7.8', 'final': '7.8'}, 1: {'sesr': '7.8', 'pece': '7.8', 'final': '7.8'}}, 'subject_id': 378, 'subjbase_id': 167, 'subj_sequence': 9999, 'subj_name_nl': 'Engelse taal en literatuur', 'subjtype_abbrev': 'Gemeensch.', 'sjtpbase_code': 'gmd', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': True, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': '2020', 'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3816, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': None, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 2, 'gl_sesrgrade': '7.8', 'gl_pecegrade': None, 'gl_finalgrade': None, 'gl_use_exem': False, 'gl_no_input': True, 'passed_pecegrade': '1.1', 'passed_finalgrade': '4', 'passed_ranking': Decimal('0.35')}, 
     77573: {'subjbase_code': 'netl', 'ep': {1: {'sesr': '6.2', 'pece': '6.2', 'final': '6.2'}}, 'subject_id': 379, 'subjbase_id': 165, 'subj_sequence': 9999, 'subj_name_nl': 'Nederlandse taal en literatuur', 'subjtype_abbrev': 'Gemeensch.', 'sjtpbase_code': 'gmd', 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': True, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False, 'no_ce_years': '2020', 'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'schemeitem_id': 3815, 'is_extra_nocount': False, 'is_extra_counts': False, 'exemption_year': None, 'is_thumbrule': False, 'has_sr': False, 'gl_examperiod': 1, 'gl_sesrgrade': '6.2', 'gl_pecegrade': '5.5', 'gl_finalgrade': '6', 'gl_use_exem': False, 'gl_no_input': False, 'passed_pecegrade': '5.6', 'passed_finalgrade': '6', 'passed_ranking': Decimal('1.475')}, 
     'c_subj': 13, 'c_exemption': 0, 'c_sr': 0, 'c_reex': 0, 'c_reex03': 0, 'c_extra_nocount': 0, 'c_extra_counts': 0, 'c_thumbrule': 0, 
     'c3': 0, 'c4': 0, 'c5': 1, 'c6': 3, 'c7': 3, 'spr_insuff': 0, 'core4': 0, 'core5': 0, 'c_ce': 8, 'c_final': 8, 'c_combi': 3, 
     'r_index': 0, 't_ce': Decimal('39.9'), 't_final': Decimal('44'), 't_combi': Decimal('22'), 
     'avg_ce_detail': ['pa:6,4(vr)', 'wa:7,4', 'na:4,7', 'sk:5,8', 'bi:4,3', 'ec:5,8', 'entl:0(h)', 'netl:5,5'], 
     'avg_final_detail': ['pa:7(vr)', 'wa:7', 'na:6', 'sk:6', 'bi:5', 'ec:7', 'entl:0(h)', 'netl:6'], 
     'combi_detail': ['asw:7(vr)', 'pws:8(vr)', 'frtl:7(vr)'], 'subj_insuff': [], 
     'avg_ce_info': {}, 'avg_final_info': {}, 'combi_info': {}, 'r_info': {}, 'r_fail_info': {}, 'r_nores_info': {}, 
     'avg_ce': None, 'avg_final': None, 'avg_combi': None, 'no_input': False, 'thumbrule_combi': False, 
     'preferred_studsubj_pk': 77574}
    """
# +++ calculate passed / failed for each exam period (ep1, ep2, ep3)
    # and put result back in student_ep_dict
    # - if no result because of no input: skip calculating result
    has_passed = False
    if withdrawn:
        student_dict['r_index'] = c.RESULT_WITHDRAWN
        if logging_on:
            logger.debug('     withdrawn: ' + str(withdrawn))
        student_dict['r_nores_info'] = gettext('This candidate has withdrawn.')
    elif partial_exam:
        # PR2022-06-10 Richard Westerink ATC: partial exam student has always 'No result' on gradelist
        student_dict['r_nores_info'] = gettext('This is a partial exam.')
        student_dict['r_index'] = c.RESULT_NORESULT
    elif not has_subjects:
        student_dict['r_index'] = c.RESULT_NORESULT
        student_dict['r_nores_info'] = gettext('This candidate has no subjects.')
    elif student_dict.get('no_input'):
        student_dict['r_index'] = c.RESULT_NORESULT
        student_dict['r_nores_info'] = gettext('One or more grades are not entered.')
    else:
        calcreex_combi_and_add_to_totals(student_dict)

        calcreex_avg_pece(student_dict)

        calcreex_avg_final(student_dict)

        has_failed = False

        # calcreex_rule_issufficient is already called in subj loop
        # student_dict['r_index'] = c.RESULT_FAILED gets value in calc_passfailed
        if depbase_is_vsbo:
            has_failed_cnt3457 = calcreex_passfailed_count6_vsbo(student_dict)
        else:
            has_failed_cnt3457 = calcreex_passfailed_count6_havovwo(student_dict)
        if has_failed_cnt3457:
            has_failed = True
        if logging_on:
            logger.debug('     has_failed_cnt3457: ' + str(has_failed_cnt3457))

        failed_insuff = calcreex_rule_issufficient(student_dict)
        if failed_insuff:
            has_failed = True

        failed_core = calc_passfailed_core_rule(student_dict, rule_core_sufficient)
        if failed_core:
            has_failed = True

        if logging_on:
            logger.debug('     failed_core: ' + str(failed_core))
            logger.debug('    student_dict r_info: ' + str(student_dict['r_info']))

        failed_avg_pece = calc_passfailed_avg_pece_rule(student_dict, rule_avg_pece_sufficient)
        if failed_avg_pece:
            has_failed = True

        if logging_on:
            logger.debug('     failed_avg_pece: ' + str(failed_avg_pece))
            logger.debug('    student_dict r_info: ' + str(student_dict['r_info']))

        # - if has_failed: create dict with key 'failed' if it does not exist
        if has_failed:
            r_index = c.RESULT_FAILED
        else:
            r_index =c.RESULT_PASSED
            has_passed = True

        student_dict['r_index'] = r_index

        if logging_on:
            logger.debug('    student_dict r_index: ' + str(student_dict['r_index']))

    if logging_on and False:
        logger.debug('student_dict: ' + str(student_dict))

    # put calculated result of the last examperiod in log_list
    # if is_reex_student: last_examperiod = 2, is_reex03_student: last_examperiod = 3, last_examperiod = 1 otherwise

    #result_info_list, result_info_log_list = calcreex_add_result_to_log(student_dict, partial_exam)
    #log_list.extend(result_info_log_list)

    return has_passed
# - calcreex_student_passedfailed_v2


def calcreex_passfailed_noinput(student_dict):  #  PR2023-04-27
    # examperiod = ep1, ep2, ep3
    # noinput_dict: {1: {'sr': ['ne'], 'ce': ['ne', 'ec']}, 2: {'ce': ['ac']}, 3: {'ce': ['ac']}}
    #  - function returns 'no_input',
    #  - puts result_index = 0 in student_dict['r_index']
    #  -  puts info in student_dict['noin_info']


    return  True if student_dict.get('no_input') else False

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

    has_failed_cnt3457 = False

    if c3:  # 1 of meer drieën of lager
        has_failed_cnt3457 = True
        three_str = ' '.join((str(c3), str( _('three or lower') if c3 == 1 else _('threes or lower'))))
        result_info = ''.join((three_str, '.'))

    else:
        # kandidaat geen drieën of lager, alleen vieren of hoger
        four_str = ' '.join((str(c4), str( _('four') if c4 == 1 else _('fours'))))
        five_str = ' '.join((str(c5), str( _('five') if c5 == 1 else _('fives'))))
        seven_str = ' '.join((str(c7) if c7 else str(pgettext_lazy('geen', 'no')), str( _('seven or higher') if c7 == 1 else _('sevens or higher'))))

        if c4 > 1:  # meer dan 1 vier
            has_failed_cnt3457 = True
            result_info = ''.join((four_str, '.'))

        elif c4 == 1:
            # 'kandidaat heeft 1 vier, de rest vijven of hoger

            if c5:  # kandidaat heeft 1 vier en 1 of meer vijven
                has_failed_cnt3457 = True
                result_info = ''.join((four_str, str(_(' and ')), five_str, '.'))
            else:  # 'kandidaat heeft 1 vier en geen vijf
                if not c7:
                    has_failed_cnt3457 = True
                result_info = ''.join((four_str, str(_(' and ')), seven_str, '.')) # '1 four and no sevens or higher.'

        else:
            # 'kandidaat heeft geen vier, alleen vijven of hoger
            if c5 > 2:
                # '3 of meer vijven
                has_failed_cnt3457 = True
                result_info = ''.join((five_str, '.'))

            elif c5 == 2:
                # kandidaat heeft 2 vijven, rest zessen of hoger
                if not c7:  # geen zevens en hoger
                    has_failed_cnt3457 = True
                result_info = ''.join((five_str, str(_(' and ')), seven_str, '.')) # '2 fives and no sevens or higher.'

            elif c5 == 1:
                # kandidaat heeft 1 vijf, rest zessen of hoger
                result_info = ''.join((five_str, str(_(' and ')), str(_('for the other subjects a 6 or higher.'))))

            else:
                # kandidaat heeft geen vijf, rest zessen of hoger
                result_info = str(_('For all subjects a 6 or higher.'))

    student_dict['r_info']['cnt3457'] = result_info

    if logging_on:
        logger.debug('     r_info cnt3457 vsbo: ' + str(result_info))
    return has_failed_cnt3457
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

    has_failed_cnt3457 = False
    result_info = ''
    if c3:  # 1 of meer drieën of lager
        has_failed_cnt3457 = True
        three_str = ' '.join((str(c3), str( _('three or lower') if c3 == 1 else _('threes or lower'))))
        result_info = ''.join((three_str, '.'))

    else:
        # kandidaat geen drieën of lager, alleen vieren of hoger
        four_str = ' '.join((str(c4), str( _('four') if c4 == 1 else _('fours'))))
        five_str = ' '.join((str(c5), str( _('five') if c5 == 1 else _('fives'))))
        seven_str = ' '.join((str(c7) if c7 else 'no', str( _('seven or higher') if c7 == 1 else _('sevens or higher'))))

        if c4 > 1:  # meer dan 1 vier
            has_failed_cnt3457 = True
            result_info = ''.join((four_str, '.'))
        elif c4 == 1:
            # 'kandidaat heeft 1 vier, de rest vijven of hoger
            result_info = ''.join((four_str, str(_(' and ')), five_str))
            if c5 > 1:
                # '1 vier en 2 of meer vijven
                has_failed_cnt3457 = True
                result_info += '.'
            elif c5 == 1:
                # een vier en een vijf: geslaagd als gemiddeld een 6 of hoger is behaald
                if avgfinal_lt_6:
                    has_failed_cnt3457 = True
                result_info += ''.join((', ', str(_('average final grade is ')), avg_final_str, '.'))
            else: # 1 vier geen vijven
                # geslaagd als gemiddeld een 6 of hoger is behaald
                if avgfinal_lt_6:
                    has_failed_cnt3457 = True
                result_info += ''.join((', ', str(_('average final grade is ')), avg_final_str, '.'))

        else:
            # 'kandidaat heeft geen vieren, alleen vijven of hoger
            if c5 > 2:
                # '3 of meer vijven
                has_failed_cnt3457 = True
                result_info = five_str
            elif c5 == 2: # 2 vijven, rest zessen of hoger
                # geslaagd als gemiddeld een 6 of hoger is behaald
                if avgfinal_lt_6:
                    has_failed_cnt3457 = True
                result_info += ''.join((five_str,', ', str(_('average final grade is ')), avg_final_str))
            elif c5 == 1:
                # 'kandidaat heeft 1 vijf, rest zessen of hoger
                # 'PR 17 jun 10 NB: gemiddeld een 6 of hoger is hier NIET van toepassing
                result_info = ' '.join((five_str, str(_('and for the other subjects a 6 or higher.'))))
            else:
                # kandidaat heeft geen vijf, rest zessen of hoger
                result_info = str(_('For all subjects a 6 or higher.'))

    if has_failed_cnt3457:
         student_dict['r_fail_info']['cnt3457'] = result_info


    # TODO add herexamen
    #result_dict['caption'] = str(c.RESULT_CAPTION[result_id])

# - put result_info in key 'r_info' of student_dict
    student_dict['r_info']['cnt3457'] = result_info

    if logging_on:
        logger.debug('     r_info cnt3457 havovwo: ' + str(result_info))

    return has_failed_cnt3457
# end of calcreex_passfailed_count6_havovwo


def calc_passfailed_core_rule(student_dict, rule_core_sufficient):  # PR2021-12-24  PR2022-05-28 PR2023-04-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calc_passfailed_core_rule  -----')
        logger.debug('    rule_core_sufficient: ' + str(rule_core_sufficient))
        logger.debug('    student_dict: ' + str(student_dict))

# 'count': {'c3': 0, 'c4': 1, 'c5': 1, 'c6': 2, 'c7': 2, 'core4': 0, 'core5': 0}
    # TODO skip core rule when in scheme 'core rule not applicable' How is this implemented ??? PR2022-08-21
    """
    in kernvak geen vieren en niet meer dan 1 vijf 'PR2015-10-31
    """

    # where is checked if notatevlex is included in rule_core_sufficient?
    # this happens in function get_rules_from_schemeitem:
    # it sets rule_core_sufficient to False when isevlexstudent = True and notatevlex = True
    failed_core = False
    if rule_core_sufficient:

        core_subjects = gettext('core subjects')

        core4 = student_dict.get('core4', 0)
        core5 = student_dict.get('core5', 0)

        if logging_on:
            logger.debug( '     core4: ' + str(core4) + ' ' + str(type(core4)))
            logger.debug( '     core5: ' + str(core5) + ' ' + str(type(core5)))

        result_info = ''
        if core4:
            result_info = ' '.join((str(core4), str(_('four') if core4 == 1 else _('fours'))))
        if core5:
            if result_info:
                result_info += str(_(' and '))
            result_info += ' '.join((str(core5), str(_('five') if core5 == 1 else _('fives'))))

        if core4 or core5 > 1:
            failed_core = True
            result_info += ''.join(( str(_(' in ')), core_subjects, '.'))


    # - add info to passed_dict
        else:
            if core5:
                result_info = ''.join(('1 ', str(_('five'))))
            #else:
            #    result_info = str(_('No fail marks')) # "Geen onvoldoendes"
                result_info += ''.join((str(_(' in ')), core_subjects, '.'))

        if logging_on:
            logger.debug( '     result_info: ' + str(result_info))

        if failed_core:
            student_dict['r_fail_info']['core45'] = result_info

    # - put result_info in key 'r_info' of student_dict
        student_dict['r_info']['core45'] = result_info

    if logging_on:
        logger.debug( '     failed_core: ' + str(failed_core))
    return failed_core
# end of calc_passfailed_core_rule


def calc_passfailed_avg_pece_rule(student_dict, rule_avg_pece_sufficient):  # PR2021-12-24 PR2022-05-26 PR2023-04-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calc_passfailed_avg_pece_rule  -----')
        logger.debug( '     rule_avg_pece_sufficient: ' + str(rule_avg_pece_sufficient))

    # where is checked if notatevlex is included in rule_avg_pece_sufficient?
    # this happens in function get_rules_from_schemeitem:
    # it sets rule_core_sufficient to False when isevlexstudent = True and notatevlex = True

    failed_avg_pece = False
    if rule_avg_pece_sufficient:

        avg_ce_decimal = student_dict.get('avg_ce')
        if avg_ce_decimal:
            display_arr = str(avg_ce_decimal).split('.')
            if len(display_arr) == 1:
                display_arr.append('0')
            avg_ce_display = ','.join((display_arr[0], display_arr[1][:1]))
            result_info = ''.join((str(_('Average CE grade')), str(_(' is ')), avg_ce_display))

            avg_decimal_A = avg_ce_decimal
            avg_55_B = Decimal('5.5')

            # a.compare(b) == -1 means a < b
            if avg_decimal_A.compare(avg_55_B) == -1:  # a.compare(b) == -1 means a < b
                failed_avg_pece = True
                result_info += str(_(', must be unrounded 5,5 or higher.'))
            else:
                result_info += '.'

            if failed_avg_pece:
                student_dict['r_fail_info']['avgce55'] = result_info

            # - put result_info in key 'r_info' of student_dict
            student_dict['r_info']['avgce55'] = result_info

            if logging_on:
                logger.debug( '     r_info avgce55: ' + str(result_info))
                logger.debug( '     r_fail_info: ' + str(student_dict['r_fail_info']))

    return failed_avg_pece
# end of calc_passfailed_avg_pece_rule


def calcreex_add_result_to_log(student_dict, partial_exam):
    # PR2021-11-29 PR2022-06-05 PR2023-04-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calcreex_add_result_to_log  -----')

    r_info = student_dict.get('r_info')
    r_fail_info = student_dict['r_fail_info']
    r_nores_info = student_dict['r_nores_info']

    if logging_on:
        logger.debug( '    r_info: ' + str(r_info))
        logger.debug( '    r_fail_info: ' + str(r_fail_info))

    result_info_list = []
    result_info_log_list = []

    if student_dict['c_reex03']:
        result_str = ''.join((str(_('Result')), ' ', str(_('after')), ' ', str(_('Re-examination 3rd period')).lower(), ': '))
    elif student_dict['c_reex']:
        result_str = ''.join((str(_('Result')), ' ', str(_('after')), ' ', str(_('Re-examination')).lower(), ': '))
    else:
        result_str = ''.join((str(_('Result')), ': '))

    result_index = student_dict.get('r_index')
    result_caption = str(c.RESULT_CAPTION[result_index]).upper()
    result_str += result_caption

    result_info_log_list.append(' ')
    if result_index == c.RESULT_WITHDRAWN:

        #result_str += str(_('Withdrawn')).upper()
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)

    elif result_index == c.RESULT_NORESULT:
        #result_str += str(_('No result')).upper()
        if partial_exam:
            result_str += ''.join((' (', str(_('partial exam')).lower(), ')'))
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)

        if r_nores_info:
            result_info_list.append(r_nores_info)
            result_info_log_list.append(''.join((c.STRING_SPACE_05, r_nores_info)))

    else:
        #result_str += str(_('Failed')).upper()
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)

        cnt3457_dict = r_info.get('cnt3457')
        if logging_on:
            logger.debug( 'cnt3457_dict: ' + str(cnt3457_dict))
        if cnt3457_dict:
            result_info_list.append(str(cnt3457_dict))
            result_info_log_list.append(''.join((c.STRING_SPACE_05, str(cnt3457_dict))))

        core45_dict = r_info.get('core45')
        if logging_on:
            logger.debug( 'core45_dict: ' + str(core45_dict))
        if core45_dict:
            result_info_list.append(str(core45_dict))
            result_info_log_list.append(''.join((c.STRING_SPACE_05, str(core45_dict))))

        avgce55_dict = student_dict.get('avgce55')
        if logging_on:
            logger.debug( 'avgce55_dict: ' + str(avgce55_dict))
        if avgce55_dict:
            result_info_list.append(str(avgce55_dict))
            result_info_log_list.append(''.join((c.STRING_SPACE_05, str(avgce55_dict))))

        insuff_list = r_info.get('insuff')
        if logging_on:
            logger.debug( 'insuff_list: ' + str(insuff_list))
        if insuff_list:
            # 'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.']}
            for info in insuff_list:
                result_info_list.append(str(info))
                result_info_log_list.append(''.join((c.STRING_SPACE_05, info)))

# - add line with combi grade
        combi_dict = student_dict['combi_info']
        if combi_dict:
            result_info_log_list.append(('').join((c.STRING_SPACE_05, combi_dict)))

# - add line with final grade
        avg_final_info = student_dict['avg_final_info']
        if avg_final_info:
            result_info_log_list.append(('').join((c.STRING_SPACE_05, avg_final_info)))

# - add line with average pece grade
        avg_ce_info = student_dict.get('avg_ce_info')
        if avg_ce_info:
            result_info_log_list.append(''.join((c.STRING_SPACE_05, avg_ce_info)))

    if logging_on:
        logger.debug( '    result_info_list: ' + str(result_info_list))
        logger.debug( '    result_info_log_list: ' + str(result_info_log_list))

    return result_info_list, result_info_log_list
# - end of calcreex_add_result_to_log


def calcreex_count_final_3457_core(student_dict, finalgrade, gradetype, is_combi, is_core_subject, multiplier,
                               is_extra_nocount, is_thumbrule):
#PR2023-04-23
# - calc only when gradetype is number
# - skip count 3457 when subject is 'is_combi (combi grade is checked at the end by calc_combi_and_add_to_totals)
    #  - note: core is not skipped when is_combi

# - skip when subject is 'is_extra_nocount' or 'is_thumbrule'

# - student_dict contains keys 'c3', 'c4', 'c5', 'c6', 'c7', 'core4', 'core5'
# - values are integers, these keys are added in calcreex_get_students_with_final_grades

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' -----  calcreex_count_final_3457_core  -----')
        logger.debug('    is_core_subject: ' + str(is_core_subject))
        logger.debug('    finalgrade: ' + str(finalgrade) + str(type(finalgrade)))

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
                #   was: skip count when is combi, except when final_grade_int <= 3
                #   was: if not is_combi or final_grade_int == 3:

                if not is_combi:
                    key_str = 'c' + str(final_grade_int)
                    student_dict[key_str] += multiplier

    # count core4 and core 5, also when core subject is combi
                # don't skip core when is combi
                if is_core_subject:
                    if 3 < final_grade_int < 6:
                        key_str = 'core' + str(final_grade_int)
                        student_dict[key_str] += multiplier
                        if logging_on:
                            logger.debug(' ')
                            logger.debug(' -----  calcreex_count_final_3457_core  -----')
                            logger.debug('    student_dict[' + key_str + ']: ' + str(student_dict[key_str]))
# - end of calcreex_count_final_3457_core


def calcreex_combi_and_add_to_totals(student_dict):  # PR2021-12-22 PR2023-04-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calcreex_combi_and_add_to_totals  -----')

    # calulate avergae combi grade and put it back in student_dict

    # values of 'c_combi' and 't_combi' are stored in student_dict in function calcreex_get_students_with_final_grades,
    # while iterating through studsubjects

    # skip calculating combi grade when no combi subjects - correct? PR2021-11-30

    combi_count_int = student_dict.get('c_combi')
    if combi_count_int:
        combi_count_str = str(combi_count_int)
        combi_count_decimal = Decimal(combi_count_str)

        combi_sum_decimal = student_dict.get('t_combi') or Decimal('0')

        combi_avg_decimal_not_rounded = combi_sum_decimal / combi_count_decimal

# - final combi grade will be rounded to integer
        combi_avg_decimal_rounded = grade_calc.round_decimal(combi_avg_decimal_not_rounded, 0)

# - put combi_avg_decimal_rounded student_dict
        student_dict['avg_combi'] = combi_avg_decimal_rounded

        combi_avg_int = int(str(combi_avg_decimal_rounded))
        combi_avg_str = str(combi_avg_int) if combi_avg_int else '-'

# - add 1 to count of final grades
        student_dict['c_final'] = 1 + (student_dict.get('c_final') or 0)

# - add combi_final_int to sum of final grades
        if combi_avg_int:
            student_dict['t_final'] = combi_avg_decimal_rounded + Decimal(student_dict.get('t_final'))

# - put combi_final_int to avg_final_detail
        # this happens in calcreex_avg_final, in that way combi can be added at the end after sorting avg_final_detail

# - create combi_info
        combi_info = ''.join((
            str(_('Combination grade')), ': ',
            combi_avg_str,
            ' (',
            str(combi_sum_decimal) if combi_sum_decimal else '-',
            '/',
            str(combi_count_int) if combi_count_int else '-',
            ') '
        ))

# - get combi_detail from student_dict
        combi_detail = student_dict['combi_detail']

# - sort combi_detail
        combi_detail_sorted = sorted(combi_detail)

# - add detail_str to combi_info
        combi_detail_str = ', '.join(combi_detail_sorted)
        combi_info += ''.join(('{', combi_detail_str, '}'))

# - put  combi_info in student_dict
        student_dict['combi_info'] = combi_info
        if logging_on:
            logger.debug('   combi_info: ' + str(student_dict['combi_info']))

# - add combi grade to calcreex_count_final_3457_core
        is_thumbrule = False

        # note: here is_combi is False. When True it skips counting, this is used when for combi subjects
        calcreex_count_final_3457_core(
            student_dict=student_dict,
            finalgrade=combi_avg_int,
            gradetype=c.GRADETYPE_01_NUMBER,
            is_combi=False,
            is_core_subject=False,
            multiplier=1,
            is_extra_nocount=False,  # is_extra_nocount is not True when combi subject
            is_thumbrule=is_thumbrule
        )
# - end of calcreex_combi_and_add_to_totals


def calcreex_avg_pece(student_dict):  # PR2021-12-23 PR2023-04-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calcreex_avg_pece  -----')

    # see https://www.examenblad.nl/veel-gevraagd/hoe-moeten-cijfers-worden-afgerond/2013
    # Een gemiddelde van 5,48333 is lager dan 5,5.

    """
    student_dict: { 
        'c_ce': 7, 't_ce': Decimal('36.4'), 'avg_ce': Decimal('5.2'), 
        'avg_ce_info': 'Gemiddeld CE-cijfer: 5,2 (36,4/7) ',
        'avg_ce_detail': ['entl:8,3', 'gs:5,5(h)', 'wa:3,4', 'if:3,9', 'frtl:4,7', 'netl:5,4', 'pa:5,2'],
    """

    pece_count_int = student_dict.get('c_ce') or 0
    if pece_count_int > 0:
        pece_count_str = str(pece_count_int)
        pece_count_decimal = Decimal(pece_count_str)

        pece_sum_decimal = student_dict.get('t_ce') or Decimal('0')
        pece_sum_str = str(pece_sum_decimal).replace('.', ',')

        # PR20220-05-27 DO NOT ROUND !!!
        #   Een gemiddelde van 5,48333 is lager dan 5,5.

        # was:
        # - round to one digit after dot
        #   pece_avg_decimal_rounded = grade_calc.round_decimal(pece_avg_decimal_not_rounded, 1)
        #   pece_avg_rounded_dot = str(pece_avg_decimal_rounded)
        #   pece_avg_rounded_comma = pece_avg_rounded_dot.replace('.', ',')

# - pece_avg is not rounded, unlike final_avg that will be rounded with 1 digit
        pece_avg_decimal = pece_sum_decimal / pece_count_decimal

# - put pece_avg_decimal in student_dict
        student_dict['avg_ce'] = pece_avg_decimal

# - create avg_ce_info
        # to break pece_avg at 1 digit: split it first
        display_arr = str(pece_avg_decimal).split('.')
        if len(display_arr) == 1:
            display_arr.append('0')
        avg_ce_display = ','.join((display_arr[0], display_arr[1][:1]))

        avg_ce_info = ''.join((
            str(_('Average CE grade')), ': ',
            avg_ce_display if avg_ce_display else '-',
            ' (', pece_sum_str if pece_sum_str else '-',
            '/', pece_count_str if pece_count_str else '-',
            ') '
        ))

# - get avg_ce_detail from student_dict
        avg_ce_detail = student_dict['avg_ce_detail'] or []

# - sort avg_ce_detail
        avg_ce_detail_sorted = sorted(avg_ce_detail)

# - add detail_str to avg_final_info
        avg_ce_info += ''.join(('{', ', '.join(avg_ce_detail_sorted), '}'))

# - put avg_ce_info in student_dict
        student_dict['avg_ce_info'] = avg_ce_info
        if logging_on:
            logger.debug('    avg_ce_info: ' + str(student_dict['avg_ce_info']))
# - end of calcreex_avg_pece


def calcreex_avg_final(student_dict):  # PR2021-12-23 PR2023-04-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calcreex_avg_final  -----')

    # calulate avergae final grade and put it back in student_dict

    """
    student_dict: {
        'c_final': 0, 't_final': '0', 'avg_final': None, 'avg_final_info': {},
        'avg_final_detail': ['entl:7', 'gs:5(h)', 'wa:4', 'if:4', 'frtl:5', 'netl:5', 'pa:5'], 
    """

    final_count_int = student_dict.get('c_final')
    if final_count_int:
        final_count_str = str(final_count_int)
        final_count_decimal = Decimal(final_count_str)

        final_sum_decimal = student_dict.get('t_final') or Decimal('0')
        final_sum_str = str(final_sum_decimal)

# - final_avg will be rounded with 1 digit (unlike calcreex_avg_pece that is not rounded)
        final_avg_decimal = final_sum_decimal / final_count_decimal
        final_rounded_str = str(grade_calc.round_decimal(input_decimal=final_avg_decimal, digits=1))

# - put final_avg_decimal in student_dict
        student_dict['avg_final'] = final_avg_decimal

# - create avg_final_info
        avg_final_info = ''.join((
            str(_('Average final grade')), ': ',
            final_rounded_str if final_rounded_str else '-',
            ' (',
            final_sum_str if final_sum_str else '-',
            '/',
            final_count_str if final_count_str else '-',
            ')'))

# - get avg_final_detail from student_dict
        avg_final_detail = student_dict['avg_final_detail'] or []

# - sort avg_final_detail
        avg_final_detail_sorted = sorted(avg_final_detail)

# - get the combi grade from student_dict
        avg_combi_txt = ''.join(('combi:', str(student_dict['avg_combi'])))

# - add the combi grade at the end of the list
        avg_final_detail_sorted.append(avg_combi_txt)

# - add detail_str to avg_final_info
        avg_final_detail_str = ', '.join(avg_final_detail_sorted)
        avg_final_info += ''.join((' {', avg_final_detail_str, '}' ))

# - put  avg_final_info in student_dict
        student_dict['avg_final_info'] = avg_final_info
        if logging_on:
            logger.debug('   avg_final_info: ' + str(student_dict['avg_final_info']))
# - end of calcreex_avg_final


def calcreex_get_rules_from_scheme(student_dict, isevlexstudent):
    # PR2021-12-19 PR2022-06-04 PR2023-04-22
    # - get result rules from scheme, values are in student_dict

    # -must check if scheme of student is correct( dep, lvl and sct are the same) (should always be the case)
    #   happens when iterating throudh studsubjects

    # these rules are stored in scheme:
    #'rule_avg_pece_sufficient', 'rule_avg_pece_notatevlex',
    #'rule_core_sufficient', 'rule_core_notatevlex',

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


def calcreex_studsubj_result_to_log(studsubj_dict, write_log, log_list):
    # PR2021-12-30 PR2022-01-02 PR2023-04-22

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('  ++++++++++++ calcreex_studsubj_result_to_log  ++++++++++++')

    if write_log:
        subj_name_nl = studsubj_dict.get('subj_name_nl', '-')
        is_combi = studsubj_dict.get('is_combi', False)
        is_core = studsubj_dict.get('is_core_subject', False)

        # si.thumb_rule = True means: thumbrule is allowed for this subject
        # studsubj.is_thumbrule = True means: student has applied thumbrule for this subject
        thumb_rule_allowed = studsubj_dict.get('thumb_rule', False)

        # Practical exam does not exist any more. Set has_practexam = False PR2022-05-26
        # was: has_practexam = si_dict.get('has_practexam', False)

    # - put subject name + combi, core if appl. in log_list
        if write_log:
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

            log_list.append(subj_name_str)

        # PR2022-06-09 debug: value of has_reex etc is not always correct
        # it is safer to loop through ep_list to calculate values of has_reex etc
        # then has_reex can be stored in student
        # here field 'has_reex' of studsubj is used,

        is_extra_nocount = studsubj_dict.get('is_extra_nocount', False)
        if is_extra_nocount:
            log_list.append(''.join((c.STRING_SPACE_05, gettext('Extra subject, does not count for the result'), '.')))

        if thumb_rule_allowed:
            is_thumbrule = studsubj_dict.get('is_thumbrule', False)
            if is_thumbrule:
                log_list.append(''.join((c.STRING_SPACE_05, gettext('Thumb rule applies, subject does not count for the result'), '.')))

        multiplier = studsubj_dict.get('multiplier', 1)
        weight_se = studsubj_dict.get('weight_se', 0)
        weight_ce = studsubj_dict.get('weight_ce', 0)

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

        # gl_examperiod contains the examperiod that is stored in studsubj, to be shown on gradelist
        ep_str = ''
        gl_examperiod = studsubj_dict.get('gl_examperiod')
        if gl_examperiod == c.EXAMPERIOD_EXEMPTION:
            ep_str = str(_('Exemption')) + ': '
        elif gl_examperiod == c.EXAMPERIOD_SECOND:
            ep_str = str(_('Re-examination')) + ': '
        elif gl_examperiod == c.EXAMPERIOD_THIRD:
            ep_str = str(_('Re-examination 3rd period')) + ': '

        final_str = studsubj_dict.get('gl_finalgrade') or '-'
        grade_str = ''.join((' ', str(_('Final grade')), ':', final_str))
        subj_grade_str = ''.join((str(ep_str), sesr_display, pece_display, grade_str))

        if logging_on:
            logger.debug('     subj_grade_str: ' + str(subj_grade_str))

        prefix = '     '
        log_list.append(''.join((prefix, subj_grade_str)))
# - end ofcalcreex_studsubj_result_to_log


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


def calcreex_rule_issufficient(student_dict):
    # PR2021-11-23 PR2023-04-26
    # function checks if max final grade is sufficient (
    # - only when 'rule_grade_sufficient' for this subject is set True in schemeitem
    # - skip when evlex student and notatevlex = True
    # - skip when subject is 'is_extra_nocount'

    # in function calcreex_create_stud_dict a key 'subj_insuff' is added to student_dict
    # it contains the sujc_codes of the subjects that are insufficient when rule_grade_sufficient

    # rule_grade_sufficient applies when rule_grade_sufficient = True,
    # except when evelex studnet and rule_gradesuff_notatevlex
    # not when is_extra_nocount, not when is_thumbrule

    # rule 2022 Havo/VWO CUR + SXM
    # - voor de vakken cav en lo een voldoende of goed is behaald

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug( ' -----  calcreex_rule_issufficient  -----')

# - skip when subject is 'is_extra_nocount' or when thumb_rule_allowed
    has_failed = False
    subj_insuff_list = student_dict['subj_insuff']

    if subj_insuff_list:
        has_failed = True
        student_dict['r_index'] = c.RESULT_FAILED
        for subj_name_nl in subj_insuff_list:
            result_info = ''.join((subj_name_nl, str(_(' is ')), str(_('not sufficient'))))

    # - reate dict with key 'failed' if it does not exist
            r_info_dict = student_dict['r_info']
            if 'insuff' not in r_info_dict:
                r_info_dict['insuff'] = []
            r_info_dict['insuff'].append(result_info)
            """
            'r_info': {'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.'],
            r_info_dict: {'combi': {}, 'cnt3457': '3 vieren.', 'insuff': ['Culturele en artistieke vorming is onvoldoende.']}
            
            """
            if logging_on:
                logger.debug('    r_info_dict: ' + str(r_info_dict))

    return has_failed
# - end of calcreex_rule_issufficient



def log_list_header(sel_school, sel_department, sel_level, sel_examyear, user_lang, write_log, log_list):
    # PR2021-12-20 PR2023-04-27
    if write_log:
        today_formatted = af.format_WDMY_from_dte(af.get_today_dateobj(), user_lang)
        school_name = sel_school.base.code + ' ' + sel_school.name

        log_list.append( ''.join((
            gettext('Calculate possible re-examinations'), ' ' , str(sel_examyear.code),
            gettext('date'), ': ', str(today_formatted)
        )))
        log_list.append(c.STRING_DOUBLELINE_80)
        log_list.append( ''.join(((gettext('School') + c.STRING_SPACE_15)[:13], ': ', school_name)))
        log_list.append( ''.join(((gettext('Department') + c.STRING_SPACE_15)[:13], ': ', sel_department.name)))
        if sel_level:
            log_list.append( ''.join(((gettext('Learning path') + c.STRING_SPACE_15)[:13], ': ', sel_level.name)))

        log_list.append(c.STRING_DOUBLELINE_80)
        log_list.append(gettext('AWP has calculated the re-examination subjects'))
        log_list.append(gettext('and the minimum grade that must be obtained to pass.'))
        log_list.append(gettext("The subject with the '>' sign has the lowest required re-examination grade."))
        """
        
        Call AppendLogFile(strLogPath, strLogMsg, True)
        strLogMsg = "========================================================================================================================"
        Call AppendLogFile(strLogPath, strLogMsg, True)
        strLogMsg = "LOG Herexamenberekening " & pblAfd.CurAfkAfdeling & " - " & Now()
        Call AppendLogFile(strLogPath, strLogMsg, True)
        strLogMsg = "========================================================================================================================"
        Call AppendLogFile(strLogPath, strLogMsg, True)
        strLogMsg = " "
        Call AppendLogFile(strLogPath, strLogMsg, True)
        
        strLogMsg = "AWP heeft de herexamenvakken berekend en het cijfer dat minimaal behaald moet worden om te slagen. " & vbCrLf & _
                    "Het vak met een > ervoor heeft het laagst benodigde herexamencijfer. "
        Call AppendLogFile(strLogPath, strLogMsg, True)
        """

# - end of log_list_header


def log_list_student_header(student_dict, full_name, write_log, log_list):
    # PR2021-12-19 PR2023-04-27
    if write_log:
        depbase_code = student_dict.get('depbase_code') or ''
        lvlbase_code = student_dict.get('lvlbase_code') or ''
        sct_name = student_dict.get('sct_name') or ''

        log_list.extend((
            c.STRING_SINGLELINE_80,
            full_name,
            ''.join((c.STRING_SPACE_05, depbase_code, ' ', lvlbase_code, ' ', sct_name ))
        ))


def log_list_add_scheme_notfound(dep_level_req, write_log, log_list):
    # PR2021-12-19 PR2023-04-27
    # - add msg when scheme not found
    if write_log:
        msg_txt = _('Please enter the learning path and sector.') if dep_level_req else _('Please enter the profile.')

        log_list.extend((
            ''.join((c.STRING_SPACE_05, str(_('The subject scheme of this candidate could not be found.')))),
            ''.join((c.STRING_SPACE_05, str(_('The result cannot be calculated.')))),
            ''.join((c.STRING_SPACE_05, str(msg_txt)))
        ))
# - end of log_list_add_scheme_notfound


def log_list_reex_count(student_dict, write_log, log_list):
    # PR2021-12-20 PR2021-12-28 PR2022-06-03 PR2023-04-27
    #

    # - add number of sr, reex, reex03 to log_list
    # TODO add extra_nocount

    # student_dict is created in get_students_with_grades_dictlist
    # it also counts the number of grade_rows of exempttion, reex and reex_03 and puts it in 'c_ep4', 'c_ep2' and 'c_ep3'
    # later these will be saved stored in table student, fields exemption_count, reex_count and reex03_count

    if write_log:
        exemption_count = student_dict.get('c_exem', 0)
        sr_count = student_dict.get('c_sr', 0)
        reex_count = student_dict.get('c_reex', 0)
        reex03_count = student_dict.get('c_reex03', 0)

        c_extra_nocount = student_dict.get('c_extra_nocount', 0)
        c_extra_counts = student_dict.get('c_extra_counts', 0)

        thumbrule_count = student_dict.get('c_thumbrule') or 0
        thumbrule_combi = student_dict.get('thumbrule_combi') or False

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

            if c_extra_nocount:
                cpt = gettext('subject') if c_extra_nocount == 1 else gettext('subjects')
                does_dont_count = gettext('does not count') if c_extra_nocount == 1 else gettext("don't count")
                extra_nocount_txt = _("The candidate has %(val)s extra %(cpt)s, that %(count)s for the result. ") \
                                        % {'val' : str(c_extra_nocount), 'cpt' : cpt, 'count' : does_dont_count}
                log_list.append(''.join((c.STRING_SPACE_05, extra_nocount_txt)))

            if c_extra_counts:
                cpt = gettext('subject') if c_extra_counts == 1 else gettext('subjects')
                count_counts = gettext('counts') if c_extra_counts == 1 else gettext("count")
                extra_nocount_txt = _(
                    "The candidate has %(val)s extra %(cpt)s, that %(count)s for the result. ") \
                                    % {'val': str(c_extra_counts), 'cpt': cpt, 'count': count_counts}
                log_list.append(''.join((c.STRING_SPACE_05, extra_nocount_txt)))
#  end of log_list_reex_count


def log_list_testgrade(subj_code, test_pece_str, test_finalgrade, write_log, log_list):
    # PR2021-12-19 PR2023-04-27
    if write_log:
        log_list.append(' ')
        log_list.append(
            ''.join((c.STRING_SPACE_05,  subj_code, ' ce: ', test_pece_str, ' final: ', test_finalgrade ))
        )


def log_list_conclusion(subj_name_nl, test_pece_str, write_log, log_list):
    # PR2021-12-19 PR2023-04-27
    if write_log:
        log_list.append(
            ''.join((c.STRING_SPACE_05, subj_name_nl, ' ce: ', test_pece_str))
        )

"""

  strLogMsg = " "
        Call AppendLogFile(strLogPath, strLogMsg, True)
        strLogMsg = "========================================================================================================================"
        Call AppendLogFile(strLogPath, strLogMsg, True)
        strLogMsg = "LOG Herexamenberekening " & pblAfd.CurAfkAfdeling & " - " & Now()
        Call AppendLogFile(strLogPath, strLogMsg, True)
        strLogMsg = "========================================================================================================================"
        Call AppendLogFile(strLogPath, strLogMsg, True)
        strLogMsg = " "
        Call AppendLogFile(strLogPath, strLogMsg, True)
        
        strLogMsg = "AWP heeft de herexamenvakken berekend en het cijfer dat minimaal behaald moet worden om te slagen. " & vbCrLf & _
                    "Het vak met een > ervoor heeft het laagst benodigde herexamencijfer. "
        Call AppendLogFile(strLogPath, strLogMsg, True)
        
        
    '4. Zet klas in logheader PR2015-05-24 toegevoegd op verzoek HvD
            If Not IsNull(rsExk(conKand09_Klas)) Then
                If Not rsExk(conKand09_Klas) = k22_Klas_LogHeader Then
                    Call AppendLogFile(strLogPath, " ", True)
                    k22_Klas_LogHeader = rsExk(conKand09_Klas)
                    strLogMsg = "------------------------------------------------------------------------------------------------------------------------"
                    Call AppendLogFile(strLogPath, strLogMsg, True)
                    Call AppendLogFile(strLogPath, "  Klas " & k22_Klas_LogHeader, True)
                    Call AppendLogFile(strLogPath, strLogMsg, True)
                End If
            End If
        'kolommen van arrCijfers zijn 
        0: VakID, 1: afkVak, 2: Vak, 3: CEcijfer, 4: MinHerCijfer (alleen ingevuld als her mogelijk is), 5: Diff (MinHer-CE), 6: '>' = Preferred Herex, 7: Is Al HerexVak, 8: GemidHerex
       
       
            strListHerexVakkenCaption = "Geen enkel herexamen geeft uitslag geslaagd."
            No re-examination gives a pass result
       
"""