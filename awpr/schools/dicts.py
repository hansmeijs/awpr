from django.db import connection

from awpr import constants as ac
from schools import models as sch_m

import logging
logger = logging.getLogger(__name__)


def create_examyear_rows(country, append_dict, examyear_pk):
    # --- create rows of all examyears of this country PR2020-10-04
    #logger.debug(' =============== create_examyear_rows ============= ')

    sql_keys = {'cntr_id': country.pk}
    sql_list = ["SELECT ey.id AS examyear_id, ey.country_id,  CONCAT('examyear_', ey.id::TEXT) AS mapid,",
        "ey.code AS examyear_code,  ey.published, ey.locked, ey.createdat, ey.publishedat, ey.lockedat,",
        "ey.modifiedby_id, ey.modifiedat, SUBSTRING(au.username, 7) AS modby_username",
        "FROM schools_examyear AS ey",
        "LEFT JOIN accounts_user AS au ON (au.id = ey.modifiedby_id)",
        "WHERE ey.country_id = %(cntr_id)s::INT"]

    if examyear_pk:
        # when employee_pk has value: skip other filters
        sql_list.append('AND ey.id = %(ey_id)s::INT')
        sql_keys['ey_id'] = examyear_pk
    else:
        sql_list.append('ORDER BY -ey.code')

    sql = ' '.join(sql_list)

    newcursor = connection.cursor()
    newcursor.execute(sql, sql_keys)
    examyear_rows = sch_m.dictfetchall(newcursor)

    # - add messages to subject_row
    if examyear_pk and examyear_rows:
        # when subject_pk has value there is only 1 row
        row = examyear_rows[0]
        if row:
            for key, value in append_dict.items():
                row[key] = value

    return examyear_rows


# --- end of create_examyear_rows


def create_department_rows(examyear):
    # --- create rows of all departments of this examyear / country PR2020-09-30
    #logger.debug(' =============== create_department_rows ============= ')

    sql_keys = {'ey_id': examyear.pk}

    sql_list = ["SELECT dep.id, dep.base_id, dep.examyear_id, ey.code AS examyear_code, ey.country_id,",
        "CONCAT('department_', dep.id::TEXT) AS mapid, depbase.code AS base_code,",
        "dep.name, dep.abbrev, dep.sequence, dep.level_req AS lvl_req, dep.sector_req AS sct_req, dep.level_caption AS lvl_caption, dep.sector_caption AS sct_caption,",
        "dep.modifiedby_id, dep.modifiedat, SUBSTRING(au.username, 7) AS modby_username",

        "FROM schools_department AS dep",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
        "LEFT JOIN accounts_user AS au ON (au.id = dep.modifiedby_id)",

        "WHERE ey.id = %(ey_id)s::INT",
        "ORDER BY dep.sequence"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = sch_m.dictfetchall(cursor)

    return rows
# --- end of create_department_rows

def create_level_rows(examyear):
    # --- create rows of all levels of this examyear / country PR2020-12-11
    #logger.debug(' =============== create_level_rows ============= ')

    sql_keys = {'ey_id': examyear.pk}

    sql_list = ["SELECT lvl.id, lvl.base_id, lvl.examyear_id, ey.code AS examyear_code, ey.country_id,",
        "CONCAT('level_', lvl.id::TEXT) AS mapid,",
        "lvl.name, lvl.abbrev, lvl.sequence, lvl.depbases,",
        "lvl.modifiedby_id, lvl.modifiedat, SUBSTRING(au.username, 7) AS modby_username",

        "FROM subjects_level AS lvl ",
        "INNER JOIN schools_examyear AS ey ON (ey.id = lvl.examyear_id)",
        "LEFT JOIN accounts_user AS au ON (au.id = lvl.modifiedby_id)",

        "WHERE ey.id = %(ey_id)s::INT",
        "ORDER BY lvl.sequence"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = sch_m.dictfetchall(cursor)

    return rows
# --- end of create_level_rows


def create_sector_rows(examyear):
    # --- create rows of all sectors of this examyear / country PR2020-12-11
    #logger.debug(' =============== create_sector_rows ============= ')

    sql_keys = {'ey_id': examyear.pk}

    sql_list = ["SELECT sct.id, sct.base_id, sct.examyear_id, ey.code AS examyear_code, ey.country_id,",
        "CONCAT('sector_', sct.id::TEXT) AS mapid,",
        "sct.name, sct.abbrev, sct.sequence, sct.depbases,",
        "sct.modifiedby_id, sct.modifiedat, SUBSTRING(au.username, 7) AS modby_username",

        "FROM subjects_sector AS sct ",
        "INNER JOIN schools_examyear AS ey ON (ey.id = sct.examyear_id)",
        "LEFT JOIN accounts_user AS au ON (au.id = sct.modifiedby_id)",

        "WHERE ey.id = %(ey_id)s::INT",
        "ORDER BY sct.sequence"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = sch_m.dictfetchall(cursor)

    return rows
# --- end of create_sector_rows

def create_school_rows(examyear, setting_dict):
    # --- create rows of all schools of this examyear / country PR2020-09-18
    #     add messages to employee_row
    #logger.debug(' =============== create_employee_rows ============= ')

    #<PERMIT> PR2021-01-01  PR2021-01-26
    # - when role_school: show only the requsr_school
    # - else: show only schools with defaultrole <= requsr_role
    requsr_role_system = setting_dict.get('requsr_role_system', False)
    requsr_role_admin = setting_dict.get('requsr_role_admin', False)

    requsr_schoolbase_pk =  setting_dict.get('requsr_schoolbase_pk')

    requsr_role = setting_dict.get('requsr_role', 0)

    sql_keys = {'ey_id': examyear.pk, 'max_role': requsr_role}

    sql_list = ["SELECT s.id, s.base_id, s.examyear_id, ey.code AS examyear_code, ey.country_id, c.name AS country,",
        "CONCAT('school_', s.id::TEXT) AS mapid, sb.defaultrole,",
        "s.name, s.abbrev, s.article, s.depbases, sb.code AS sb_code, s.locked, s.depbases,",
        "s.modifiedby_id, s.modifiedat, SUBSTRING(au.username, 7) AS modby_username",

        "FROM schools_school AS s",
        "INNER JOIN schools_schoolbase AS sb ON (sb.id = s.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = s.examyear_id)",
        "INNER JOIN schools_country AS c ON (c.id = ey.country_id)",
        "LEFT JOIN accounts_user AS au ON (au.id = s.modifiedby_id)",

        "WHERE ey.id = %(ey_id)s::INT",
        "AND sb.defaultrole <= %(max_role)s::INT"]

    if requsr_role >= ac.ROLE_16_INSP :
        sql_list.append("ORDER BY LOWER(sb.code)")
    else:
        sql_keys['sb_id'] = requsr_schoolbase_pk
        sql_list.append("AND sb.id = %(sb_id)s::INT")

    sql = ' '.join(sql_list)
    newcursor = connection.cursor()
    newcursor.execute(sql, sql_keys)
    school_rows = sch_m.dictfetchall(newcursor)

    return school_rows
# --- end of create_employee_rows