from django.db import connection

from awpr import constants as c
from awpr import functions as af
from awpr import settings as s
from schools import models as sch_mod

import logging
logger = logging.getLogger(__name__)


def create_examyear_rows(req_usr, append_dict, examyear_pk):
    # --- create rows of all examyears of this country PR2020-10-04
    #logger.debug(' =============== create_examyear_rows ============= ')

    # when role = school: show examyear plus school.isactivated

    sql_keys = {}
    if req_usr.role <= c.ROLE_008_SCHOOL:
        sql_keys['sb_id'] = req_usr.schoolbase.pk
        sql_list = ["SELECT sch.id AS school_id, ey.country_id, sch.examyear_id, CONCAT('examyear_', ey.id::TEXT) AS mapid,",
            "ey.code AS examyear_code, sch.name, sch.activated, sch.activatedat, sch.locked, sch.lockedat,",
            "sch.modifiedby_id, sch.modifiedat, SUBSTRING(au.username, 7) AS modby_username",
            "FROM schools_school AS sch",
            "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = sch.modifiedby_id)",
            "WHERE sch.base_id = %(sb_id)s::INT"]
    else:
        sql_keys['cntr_id'] = req_usr.country.pk
        sql_list = ["SELECT ey.id AS examyear_id, ey.country_id, CONCAT('examyear_', ey.id::TEXT) AS mapid,",
            "ey.code AS examyear_code,  ey.published, ey.locked, ey.createdat, ey.publishedat, ey.lockedat,",
            "ey.modifiedby_id, ey.modifiedat, SUBSTRING(au.username, 7) AS modby_username",
            "FROM schools_examyear AS ey",
            "LEFT JOIN accounts_user AS au ON (au.id = ey.modifiedby_id)",
            "WHERE ey.country_id = %(cntr_id)s::INT"]

    if examyear_pk:
        # when examyear_pk has value: skip other filters
        sql_list.append('AND ey.id = %(ey_id)s::INT')
        sql_keys['ey_id'] = examyear_pk
    else:
        sql_list.append('ORDER BY -ey.code')

    sql = ' '.join(sql_list)

    newcursor = connection.cursor()
    newcursor.execute(sql, sql_keys)
    examyear_rows = af.dictfetchall(newcursor)

# - add messages to examyear_row
    if examyear_pk and examyear_rows:
        # when examyear_pk has value there is only 1 row
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
        "dep.name, dep.abbrev, dep.sequence, dep.level_req AS lvl_req, dep.sector_req AS sct_req, dep.has_profiel,",
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
        rows = af.dictfetchall(cursor)

    return rows
# --- end of create_department_rows

def create_level_rows(examyear, depbase, cur_dep_only):
    # --- create rows of all levels of this examyear / country PR2020-12-11 PR2021-03-08  PR2021-06-24
    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_level_rows ============= ')
        logger.debug('examyear: ' + str(examyear))
        logger.debug('depbase: ' + str(depbase))
        logger.debug('cur_dep_only: ' + str(cur_dep_only))

    rows =[]
    if examyear:
        sql_keys = {'ey_id': examyear.pk}

        sql_list = ["SELECT lvl.id, lvl.base_id, lvl.examyear_id, ey.code AS examyear_code, ey.country_id,",
            "CONCAT('level_', lvl.id::TEXT) AS mapid,",
            "lvl.name, lvl.abbrev, lvl.sequence, lvl.depbases,",
            "lvl.modifiedby_id, lvl.modifiedat, SUBSTRING(au.username, 7) AS modby_username",

            "FROM subjects_level AS lvl ",
            "INNER JOIN schools_examyear AS ey ON (ey.id = lvl.examyear_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = lvl.modifiedby_id)",

            "WHERE ey.id = %(ey_id)s::INT"
            ]

        if cur_dep_only:
            depbase_lookup = None
            if depbase:
                department = sch_mod.Department.objects.get_or_none(
                    examyear=examyear,
                    base=depbase
                )
                if department:
                    if department.level_req:
                        depbase_lookup = ''.join( ('%;', str(depbase.pk), ';%') )


                if logging_on:
                    logger.debug('department: ' + str(department))
                    logger.debug('depbase_lookup: ' + str(depbase_lookup))

            if depbase_lookup:
                sql_keys['depbase_pk'] = depbase_lookup
                sql_list.append("AND CONCAT(';', lvl.depbases::TEXT, ';') LIKE %(depbase_pk)s::TEXT")
            else:
                sql_list.append("AND FALSE")
        sql_list.append("ORDER BY lvl.sequence")
        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

            if logging_on:
                logger.debug('rows: ' + str(rows))
                #logger.debug('connection.queries: ' + str(connection.queries))
        """
        'sql': "SELECT lvl.id, lvl.base_id, lvl.examyear_id, ey.code AS examyear_code, ey.country_id, 
                CONCAT('level_', lvl.id::TEXT) AS mapid, lvl.name, lvl.abbrev, lvl.sequence, lvl.depbases, lvl.modifiedby_id, lvl.modifiedat, 
                SUBSTRING(au.username, 7) AS modby_username 
                FROM subjects_level AS lvl  
                INNER JOIN schools_examyear AS ey ON (ey.id = lvl.examyear_id) 
                LEFT JOIN accounts_user AS au ON (au.id = lvl.modifiedby_id) 
                WHERE ey.id = 62::INT AND CONCAT(';', lvl.depbases::TEXT, ';') LIKE '%;1;%'::TEXT 
                ORDER BY lvl.sequence", 'time': '0.000'}]
        """
    return rows
# --- end of create_level_rows


def create_sector_rows(examyear, depbase, cur_dep_only):
    # --- create rows of all sectors of this examyear / country PR2020-12-11  PR2021-03-08  PR2021-06-24
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_sector_rows ============= ')
        logger.debug('cur_dep_only: ' + str(cur_dep_only))
        logger.debug('depbase: ' + str(depbase))
        logger.debug('examyear: ' + str(examyear.code))
        logger.debug('country: ' + str(examyear.country))

    rows =[]
    if examyear:
        sql_keys = {'ey_id': examyear.pk}
        sql_list = ["SELECT sct.id, sct.base_id, sct.examyear_id, ey.code AS examyear_code, ey.country_id,",
                    "CONCAT('sector_', sct.id::TEXT) AS mapid,",
                    "sct.name, sct.abbrev, sct.sequence, sct.depbases,",
                    "sct.modifiedby_id, sct.modifiedat, SUBSTRING(au.username, 7) AS modby_username",

                    "FROM subjects_sector AS sct ",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = sct.examyear_id)",
                    "LEFT JOIN accounts_user AS au ON (au.id = sct.modifiedby_id)",

                    "WHERE ey.id = %(ey_id)s::INT"
                    ]

        if cur_dep_only:
            depbase_lookup = None
            if depbase:
                department = sch_mod.Department.objects.get_or_none(examyear=examyear, base=depbase)
                if department:
                    if department.sector_req:
                        depbase_lookup = ''.join( ('%;', str(depbase.pk), ';%') )

            if depbase_lookup:
                sql_keys['depbase_pk'] = depbase_lookup
                sql_list.append("AND CONCAT(';', sct.depbases::TEXT, ';') LIKE %(depbase_pk)s::TEXT")
            else:
                sql_list.append("AND FALSE")

        sql_list.append("ORDER BY sct.sequence")
        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('sql: ' + str(sql))
        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

            if logging_on:
                for row in rows:
                    logger.debug('row: ' + str(row))
    return rows
# --- end of create_sector_rows




def create_school_rows(examyear, permit_dict, school_pk=None):
    # --- create rows of all schools of this examyear / country PR2020-09-18 PR2021-04-23
    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_school_rows ============= ')
        logger.debug('permit_dict: ' + str(permit_dict))

    requsr_role = permit_dict.get('requsr_role', 0)
    requsr_schoolbase_pk =  permit_dict.get('requsr_schoolbase_pk')

    sql_keys = {'ey_id': examyear.pk, 'max_role': requsr_role}


    sql_list = ["SELECT sch.id, sch.base_id, sch.examyear_id, ey.code AS examyear_code, ey.country_id, c.name AS country,",
        "CONCAT('school_', sch.id::TEXT) AS mapid, sb.defaultrole,",
        "sch.name, sch.abbrev, sch.article, sb.code AS sb_code, sch.depbases, sch.otherlang,",
        "sch.isdayschool, sch.iseveningschool, sch.islexschool, sch.activated, sch.activatedat, sch.locked, sch.lockedat,",
        "sch.modifiedby_id, sch.modifiedat, SUBSTRING(au.username, 7) AS modby_username",

        "FROM schools_school AS sch",
        "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
        "INNER JOIN schools_country AS c ON (c.id = ey.country_id)",
        "LEFT JOIN accounts_user AS au ON (au.id = sch.modifiedby_id)",

        "WHERE ey.id = %(ey_id)s::INT",
        "AND sb.defaultrole <= %(max_role)s::INT"]

    if school_pk:
        # school_pk has only a value after update
        # then one row is retrieved,  to put new values on page
        sql_list.append('AND sch.id = %(sch_id)s::INT')
        sql_keys['sch_id'] = school_pk
    elif requsr_role <= c.ROLE_008_SCHOOL:
        # schools can olny view their own school
        sql_keys['sb_id'] = requsr_schoolbase_pk
        sql_list.append("AND sb.id = %(sb_id)s::INT")

    # order by id necessary to make sure that lookup function on client gets the right row
    sql_list.append("ORDER BY sch.id")
    sql = ' '.join(sql_list)
    if logging_on:
        logger.debug('sql_keys' + str(sql_keys))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        school_rows = af.dictfetchall(cursor)

    return school_rows
# --- end of create_school_rows