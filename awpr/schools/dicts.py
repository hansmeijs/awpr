from django.db import connection

from awpr import constants as c
from awpr import functions as af
from awpr import settings as s
from schools import models as sch_mod

import logging
logger = logging.getLogger(__name__)


def create_mailbox_rows(examyear_pk, request, mailbox_pk=None):
    # --- create mail_inbox rows of this user this examyear PR2021-09-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_mailbox_rows ============= ')
        logger.debug('examyear_pk: ' + str(examyear_pk))
        logger.debug('request.user.pk: ' + str(request.user.pk))

    mailbox_rows = []

    try:
        filter_mailbox_pk = 'AND mailbox.id = %(mb_pk)s::INT' if mailbox_pk else ''

        sql_keys = {'req_usr_id': request.user.pk, 'ey_id': examyear_pk, 'mb_pk': mailbox_pk}

        sql_list = ["SELECT mailbox.id, CONCAT('mailbox_', mailbox.id::TEXT) AS mapid, msg.id AS mailmessage_id,",
                    "mailbox.read, mailbox.deleted, mailbox.issentmail, mailbox.isreceivedmail,",
                    "msg.header, msg.body, msg.mailto_user, msg.mailcc_user, msg.status, msg.modifiedby_id, msg.modifiedat, ",
                    "sch.name AS sender_school_name, sch.abbrev AS sender_school_abbrev,",
                    "au.last_name AS sender_lastname",

                    "FROM schools_mailbox AS mailbox",
                    "INNER JOIN schools_mailmessage AS msg ON (msg.id = mailbox.mailmessage_id)",
                    "LEFT JOIN schools_school AS sch ON (sch.id = msg.sender_school_id)",
                    "LEFT JOIN accounts_user AS au ON (au.id = msg.sender_user_id)",

                    "WHERE msg.examyear_id = %(ey_id)s::INT AND mailbox.user_id = %(req_usr_id)s::INT",
                    filter_mailbox_pk,
                    "ORDER BY mailbox.id"
                    ]
        sql = ' '.join(sql_list)
        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            mailbox_rows = af.dictfetchall(cursor)
        if logging_on:
            logger.debug('mailbox_rows: ' + str(mailbox_rows))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return mailbox_rows
# --- end of create_mailbox_rows

###########################

def create_mailbox_user_rows(examyear_pk, request):
    # --- create list of all users , for mailbox recipients PR2021-10-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_mailbox_user_rows ============= ')

    mailbox_user_list = []
    if examyear_pk and request.user.country:
        try:

            sql_keys = {'country_id': request.user.country.pk, 'ey_id': examyear_pk}

            sql_list = ["SELECT u.id, u.last_name, u.email, sb.code AS school_code, school.abbrev AS school_abbrev",

                "FROM accounts_user AS u",
                "INNER JOIN schools_country AS c ON (c.id = u.country_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = u.schoolbase_id)",
                "INNER JOIN schools_school AS school ON (school.base_id = sb.id)",

                "WHERE u.country_id = %(country_id)s::INT",
                "AND school.examyear_id = %(ey_id)s::INT",
                "AND  u.activated AND u.is_active",
                "ORDER BY LOWER(sb.code), LOWER(u.last_name)"
            ]
            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                mailbox_user_list = af.dictfetchall(cursor)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('mailbox_user_list: ' + str(mailbox_user_list))

    return mailbox_user_list
# - end of create_mailbox_user_rows

#############################




def create_examyear_rows(req_usr, append_dict, examyear_pk, get_all_countries=False):
    # --- create rows of all examyears of this country PR2020-10-04 PR2021-09-24
    #logger.debug(' =============== create_examyear_rows ============= ')

    # when role = school: show examyear plus school.isactivated
    country_filter = "WHERE TRUE" if get_all_countries else "WHERE ey.country_id = %(cntr_id)s::INT"
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
        sql_list = ["SELECT ey.id AS examyear_id, ey.country_id, cntr.name AS country,",
                    "CONCAT('examyear_', ey.id::TEXT) AS mapid,",
            "ey.code AS examyear_code, ey.published, ey.locked, ey.createdat, ey.publishedat, ey.lockedat,",
            "ey.no_practexam, ey.sr_allowed, ey.no_centralexam, ey.no_thirdperiod,",
            "ey.order_extra_fixed, ey.order_extra_perc, ey.order_round_to,",
            "ey.order_tv2_divisor, ey.order_tv2_multiplier, ey.order_tv2_max,",
            "ey.order_admin_divisor, ey.order_admin_multiplier, ey.order_admin_max,",
            "ey.modifiedby_id, ey.modifiedat, SUBSTRING(au.username, 7) AS modby_username",
            "FROM schools_examyear AS ey",
            "INNER JOIN schools_country AS cntr ON (cntr.id = ey.country_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = ey.modifiedby_id)",
            country_filter
        ]

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

        sql_list = ["SELECT lvl.id, lvl.base_id, lvlbase.code AS lvlbase_code, lvl.examyear_id, ey.code AS examyear_code, ey.country_id,",
            "CONCAT('level_', lvl.id::TEXT) AS mapid,",
            "lvl.name, lvl.abbrev, lvl.sequence, lvl.depbases,",
            "lvl.modifiedby_id, lvl.modifiedat, SUBSTRING(au.username, 7) AS modby_username",

            "FROM subjects_level AS lvl ",
            "INNER JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

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
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_sector_rows ============= ')
        logger.debug('cur_dep_only: ' + str(cur_dep_only))
        logger.debug('depbase: ' + str(depbase))
        logger.debug('examyear: ' + str(examyear.code))
        logger.debug('country: ' + str(examyear.country))

    rows =[]
    if examyear:
        sql_keys = {'ey_id': examyear.pk}
        sql_list = ["SELECT sct.id, sct.base_id, sctbase.code AS sctbase_code, sct.examyear_id, ey.code AS examyear_code, ey.country_id,",
                    "CONCAT('sector_', sct.id::TEXT) AS mapid,",
                    "sct.name, sct.abbrev, sct.sequence, sct.depbases,",
                    "sct.modifiedby_id, sct.modifiedat, SUBSTRING(au.username, 7) AS modby_username",

                    "FROM subjects_sector AS sct ",
                    "INNER JOIN subjects_sectorbase AS sctbase ON (sctbase.id = sct.base_id)",
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
        "sch.name, sch.abbrev, sch.article, sb.code AS sb_code, sch.depbases, sch.otherlang, sch.no_order,",
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
