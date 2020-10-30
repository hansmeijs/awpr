from django.db import connection

from awpr import functions as af
from schools import models as sch_m

import logging
logger = logging.getLogger(__name__)


def create_examyear_rows(country, append_dict, instance_pk):
    # --- create rows of all examyears of this country PR2020-10-04
    logger.debug(' =============== create_subject_rows ============= ')

    sql_keys = {'cntr_id': country.pk}
    sql_list = ["""SELECT ey.id, ey.country_id, 
        CONCAT('examyear_', ey.id::TEXT) AS mapid,
        ey.examyear, 
        ey.published,
        ey.locked,

        ey.createdat,
        ey.publishedat,
        ey.lockedat,

        ey.modifiedby_id, ey.modifiedat,
        SUBSTRING(au.username, 7) AS modby_username

        FROM schools_examyear AS ey 
        LEFT JOIN accounts_user AS au ON (au.id = ey.modifiedby_id) 

        WHERE ey.country_id = %(cntr_id)s::INT
        """]

    if instance_pk:
        # when employee_pk has value: skip other filters
        sql_list.append('AND ey.id = %(ey_id)s::INT')
        sql_keys['ey_id'] = instance_pk
    else:
        sql_list.append('ORDER BY -ey.examyear')

    sql = ' '.join(sql_list)

    newcursor = connection.cursor()
    newcursor.execute(sql, sql_keys)
    examyear_rows = sch_m.dictfetchall(newcursor)

    # - add messages to subject_row
    if instance_pk and examyear_rows:
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

    sql_schools = """ SELECT d.id, d.base_id, d.examyear_id, ey.examyear, ey.country_id, 
        CONCAT('department_', d.id::TEXT) AS mapid,
        d.name, d.abbrev, d.sequence, d.level_req, d.sector_req, d.level_caption, d.sector_caption,
        d.modifiedby_id, d.modifiedat,
        SUBSTRING(au.username, 7) AS modby_username

        FROM schools_department AS d 
        INNER JOIN schools_examyear AS ey ON (ey.id = d.examyear_id) 
        LEFT JOIN accounts_user AS au ON (au.id = d.modifiedby_id) 

        WHERE ey.id = %(ey_id)s::INT
        ORDER BY d.sequence
        """
    newcursor = connection.cursor()
    newcursor.execute(sql_schools, sql_keys)
    school_rows = sch_m.dictfetchall(newcursor)

    return school_rows
# --- end of create_employee_rows


def create_school_rows(examyear):
    # --- create rows of all schools of this examyear / country PR2020-09-18
    #     add messages to employee_row
    #logger.debug(' =============== create_employee_rows ============= ')

    sql_keys = {'ey_id': examyear.pk}

    sql_schools = """ SELECT s.id, s.base_id, s.examyear_id, ey.examyear, ey.country_id, c.name AS country,
        CONCAT('school_', s.id::TEXT) AS mapid,
        s.name, s.abbrev, s.article, s.depbases,
        sb.code AS sb_code,
        s.istemplate, s.locked,
        s.modifiedby_id, s.modifiedat,
        SUBSTRING(au.username, 7) AS modby_username

        FROM schools_school AS s 
        INNER JOIN schools_schoolbase AS sb ON (sb.id = s.base_id) 
        INNER JOIN schools_examyear AS ey ON (ey.id = s.examyear_id) 
        INNER JOIN schools_country AS c ON (c.id = ey.country_id) 
        LEFT JOIN accounts_user AS au ON (au.id = s.modifiedby_id) 

        WHERE ey.id = %(ey_id)s::INT
        ORDER BY LOWER(sb.code)
        """
    newcursor = connection.cursor()
    newcursor.execute(sql_schools, sql_keys)
    school_rows = sch_m.dictfetchall(newcursor)

    return school_rows
# --- end of create_employee_rows