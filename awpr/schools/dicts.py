import json

from django.db import connection

from accounts import views as acc_view
from accounts import permits as acc_prm

from awpr import constants as c
from awpr import functions as af
from awpr import settings as s
from schools import models as sch_mod

import logging
logger = logging.getLogger(__name__)


def create_mailmessage_received_rows(examyear, request, mailmessage_pk=None):
    # --- create received mail_message rows of this user, this examyear PR2021-10-28
    #       use INNER JOIN mailbox to filter messages for this user

    # PR2021-11-03 debug: since received messages cab come from other countries:
    # - dont filter on examyear.pk but on examyear.code
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_mailmessage_received_rows ============= ')
        logger.debug('examyear: ' + str(examyear))
        logger.debug('request.user.pk: ' + str(request.user.pk))

    mailmessage_rows = []

    try:

        sql_keys = {'req_usr_id': request.user.pk, 'ey_code': examyear.code, 'msg_id': mailmessage_pk}

        filter_mailmessage_pk = 'AND msg.id = %(msg_id)s::INT' if mailmessage_pk else ''
        sql_list = ["WITH att AS (SELECT att.mailmessage_id FROM schools_mailattachment AS att GROUP BY att.mailmessage_id)",
                    "SELECT msg.id, mb.id AS mailbox_id,",
                    "CONCAT('mailmessage_', msg.id::TEXT, '_', mb.id::TEXT) AS mapid,",
                    "mb.read, mb.deleted,",
                    "msg.header, msg.body, msg.recipients, msg.sentdate,",
                    "msg.sender_user_id, msg.sender_school_id, msg.modifiedby_id, msg.modifiedat,",
                    "CASE WHEN att.mailmessage_id IS NULL THEN FALSE ELSE TRUE END AS has_att,",
                    "sch.name AS sender_school_name, sch.abbrev AS sender_school_abbrev,",
                    "au.last_name AS sender_lastname",

                    "FROM schools_mailmessage AS msg",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = msg.examyear_id)",
                    "INNER JOIN schools_mailbox AS mb ON (mb.mailmessage_id = msg.id)",
                    "LEFT JOIN schools_school AS sch ON (sch.id = msg.sender_school_id)",
                    "LEFT JOIN accounts_user AS au ON (au.id = msg.sender_user_id)",
                    "LEFT JOIN att ON (att.mailmessage_id = msg.id)",

                    "WHERE ey.code = %(ey_code)s::INT",
                    "AND mb.user_id = %(req_usr_id)s::INT",
                    "AND msg.sentdate IS NOT NULL",

                    filter_mailmessage_pk,
                    "ORDER BY msg.id, mb.id NULLS FIRST"
                    ]
        sql = ' '.join(sql_list)
        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            mailmessage_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('mailmessage_rows: ' + str(mailmessage_rows))
            for qr in connection.queries:
                logger.debug('-----------------------------------------------------------------------------')
                logger.debug(str(qr))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return mailmessage_rows
# --- end of create_mailmessage_received_rows


def create_mailmessage_draft_or_sent_rows(is_sent, examyear, request, append_dict, mailmessage_pk=None):
    # --- create received mail_message rows of this user, this examyear PR2021-10-28
    #       use INNER JOIN mailbox to filter messages for this user
    logging_on = False # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_mailmessage_draft_or_sent_rows ============= ')
        logger.debug('examyear_pk: ' + str(examyear))
        logger.debug('request.user.pk: ' + str(request.user.pk))

    mailmessage_rows = []

    try:
        sql_keys = {'req_usr_id': request.user.pk, 'ey_id': examyear.pk, 'msg_id': mailmessage_pk}

        filter_mailmessage_pk = 'AND msg.id = %(msg_id)s::INT' if mailmessage_pk else ''
        if is_sent:
            filter_draft_or_sent = "AND msg.id IN (SELECT mailmessage_id FROM schools_mailbox)"
        else:
            filter_draft_or_sent = "AND msg.id NOT IN (SELECT mailmessage_id FROM schools_mailbox)"

        sql_list = ["SELECT msg.id, CONCAT('mailmessage_', msg.id::TEXT) AS mapid,",
                    "msg.header, msg.body, msg.recipients, msg.sentdate,",
                    "msg.sender_user_id, msg.sender_school_id, msg.modifiedby_id, msg.modifiedat,",
                    "msg.id IN (SELECT mailmessage_id FROM schools_mailattachment) AS has_att,",
                    "sch.name AS sender_school_name, sch.abbrev AS sender_school_abbrev,",
                    "au.last_name AS sender_lastname",

                    "FROM schools_mailmessage AS msg",
                    "LEFT JOIN schools_school AS sch ON (sch.id = msg.sender_school_id)",
                    "LEFT JOIN accounts_user AS au ON (au.id = msg.sender_user_id)",

                    "WHERE msg.examyear_id = %(ey_id)s::INT",
                    "AND msg.sender_user_id = %(req_usr_id)s::INT",
                    filter_draft_or_sent,
                    filter_mailmessage_pk,
                    "ORDER BY msg.id"
                    ]
        sql = ' '.join(sql_list)
        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            mailmessage_rows = af.dictfetchall(cursor)

# - add messages to student_row
        if mailmessage_pk and mailmessage_rows and append_dict:
            # when mailmessage_pk has value there is only 1 row
            row = mailmessage_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

        if logging_on:
            logger.debug('mailmessage_rows: ' + str(mailmessage_rows))
            #for qr in connection.queries:
            #    logger.debug('-----------------------------------------------------------------------------')
            #    logger.debug(str(qr))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return mailmessage_rows
# --- end of create_mailmessage_draft_or_sent_rows


def create_mailinglist_rows(request, mailinglist_pk=None):
    # --- create mailinglist rows of this user this school PR2021-10-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_mailinglist_rows ============= ')
        logger.debug('request.user.pk: ' + str(request.user.pk))
        logger.debug('mailinglist_pk: ' + str(mailinglist_pk))

    mailinglist_rows = []

    try:
        filter_mailinglist_pk = 'AND ml.id = %(ml_pk)s::INT' if mailinglist_pk else ''

        sql_keys = {'req_usr_id': request.user.pk, 'sb_id': request.user.schoolbase_id, 'ml_pk': mailinglist_pk}

        sql_list = ["SELECT ml.id, CONCAT('mailinglist_', ml.id::TEXT) AS mapid, ml.name, ml.recipients, ml.user_id",

                    "FROM schools_mailinglist AS ml",
                    "WHERE (ml.schoolbase_id = %(sb_id)s::INT)",
                    "AND ( ml.user_id IS NULL OR ml.user_id = %(req_usr_id)s::INT )",
                    filter_mailinglist_pk,
                    "ORDER BY ml.id"
                    ]
        sql = ' '.join(sql_list)
        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            mailinglist_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('mailinglist_rows: ' + str(mailinglist_rows))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return mailinglist_rows
# --- end of create_mailinglist_rows


def create_mailbox_recipients_rows(examyear_pk, mailmessage_pk):
    # --- create mail_message rows of this examyear PR2021-09-11 PR2021-10-27
    #       used in draft messages - without JOIN to mailbox,
    #       filter by examyear_id, sender_user (both draft (sentdate IS NULL) and sent (sentdate has value)

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_mailbox_recipients_rows ============= ')
        logger.debug('examyear_pk: ' + str(examyear_pk))

    mailbox_recipients_rows = []

    try:
        sql_keys = {'ey_id': examyear_pk, 'msg_pk': mailmessage_pk}

        sql_list = ["SELECT msg.id, sb.code AS school_code, sch.name AS school_name,",
                    # note: ORDER BY LOWER(au.last_name) not working in ARRAY_AGG. Sort on client side instead
                    "ARRAY_AGG(DISTINCT au.last_name) AS au_lastname_arr",

                    "FROM schools_mailbox AS mb",
                    "INNER JOIN schools_mailmessage AS msg ON (msg.id = mb.mailmessage_id)",
                    "INNER JOIN accounts_user AS au ON (au.id = mb.user_id)",
                    "INNER JOIN schools_schoolbase AS sb ON (sb.id = au.schoolbase_id)",
                    "INNER JOIN schools_school AS sch ON (sch.base_id = sb.id)",

                    "WHERE sch.examyear_id = %(ey_id)s::INT",
                    "AND msg.id = %(msg_pk)s::INT",

                    "GROUP BY msg.id, sb.code, sch.name",
                    "ORDER BY LOWER(sb.code)"
                    ]
        sql = ' '.join(sql_list)
        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            mailbox_recipients_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('mailbox_recipients_rows: ' + str(mailbox_recipients_rows))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return mailbox_recipients_rows
# --- end of create_mailbox_recipients_rows


def create_mailattachment_rows(examyear, request, mailattachment_pk=None):
    # --- create mail_inbox rows of this user this examyear PR2021-09-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_mailattachment_rows ============= ')
        logger.debug('examyear: ' + str(examyear))
        logger.debug('request.user.pk: ' + str(request.user.pk))
        logger.debug('mailattachment_pk: ' + str(mailattachment_pk))

    mailattachment_rows = []
    # PR2022-05-12 debug: Mireille Peterson-Regales MC mailbox attachment not showing.
    # cause: attachments were filtered by examyear.pk, SXM has different examyear.pk from CUR
    # solved by: add INNER JOIN exam year and filter by examyear.code
    try:
        filter_mailattachment_pk = "AND mail_att.id = " + str(mailattachment_pk) if mailattachment_pk else ''

        req_usr_pk_str = ''.join((';', str(request.user.pk), ';'))

        if logging_on:
            logger.debug('req_usr_pk_str: ' + str(req_usr_pk_str))
            logger.debug('filter_mailattachment_pk: ' + str(filter_mailattachment_pk))

        sql_list = [
            "SELECT mail_att.id, msg.id AS mailmessage_id,",
            "mail_att.filename, mail_att.contenttype, mail_att.filesize,",
            "msg.sender_user_id, msg.recipients",

            "FROM schools_mailattachment AS mail_att",
            "INNER JOIN schools_mailmessage AS msg ON (msg.id = mail_att.mailmessage_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = msg.examyear_id)",

            "WHERE (ey.code = ", str(examyear.code), ")",

            # TODO change format recipients to list of all users (otherwise list may not reflex actual sender list)
            #  increase max length of recipients (max 1.000 recipients * 5 char = 5k > 10k max
            #"AND ( msg.sender_user_id = ", str(request.user.pk),
            #"OR POSITION('" + str(req_usr_pk_str) + "' IN CONCAT(';', msg.recipients, ';')) > 0 )",

            filter_mailattachment_pk,
            "ORDER BY mail_att.id"
            ]
        sql = ' '.join(sql_list)
        if logging_on:
            logger.debug('sql: ' + str(sql))

        rows = sch_mod.Mailattachment.objects.raw(sql)
        if rows:
            # - loop through rows and add url to row
            for row in rows:
                file = row.file
                url_str = file.url
                dict = {
                    'id': getattr(row, 'id'),
                    'mailmessage_id': getattr(row, 'mailmessage_id'),
                    'filename': getattr(row, 'filename'),
                    'url': url_str,
                    'contenttype': getattr(row, 'contenttype'),
                    'filesize': getattr(row, 'filesize'),
                    'sender_user_id': getattr(row, 'sender_user_id'),
                    'recipients': getattr(row, 'recipients')
                }
                mailattachment_rows.append(dict)

        if logging_on:
            # for qr in connection.queries:
            #    logger.debug('-----------------------------------------------------------------------------')
            #    logger.debug(str(qr))
            logger.debug('mailattachment_rows: ' + str(mailattachment_rows))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return mailattachment_rows

# --- end of create_mailattachment_rows

###########################

def create_mailbox_user_rows(examyear, request):
    # --- create list of all users , for mailbox recipients PR2021-10-11 PR2021-10-23 PR2023-04-05
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_mailbox_user_rows ============= ')

    mailbox_user_list = []
    if examyear and request.user.country:
        try:
            # PR2021-10-23
            # do not filter users by country (happens on client if user set 'local only' = true)
            # do filter on examyear of school
            # do filter on user activated and is_active

            # filter on examyear.code instead of examyear.pk, to get als users of other countries
            # PR2023-04-05 filter only users with usergroup 'msgreceive'

            sql_list = ["SELECT u.id, u.last_name AS username, u.email, ",
                        "sb.code AS code, school.abbrev, c.id AS country_pk, c.abbrev AS country, ual.id AS ual_id, ual.examyear_id",

                "FROM accounts_user AS u",

                "INNER JOIN accounts_userallowed AS ual ON (ual.user_id = u.id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = ual.examyear_id)",

                "INNER JOIN schools_country AS c ON (c.id = u.country_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = u.schoolbase_id)",

                # PR2023-04-05 debug: users appeared twice, because school was not joined on examyear_id
                "INNER JOIN schools_school AS school ON (school.base_id = sb.id AND school.examyear_id = ual.examyear_id)",
                "WHERE u.activated AND u.is_active",
                # dont filter on country. was: "WHERE u.country_id = %(country_id)s::INT",
                ''.join(("AND ey.code=", str(examyear.code), "::INT")),

                # add only users to list when they have usergroup 'receive messages'
                ''.join(("AND (POSITION('", c.USERGROUP_MSGRECEIVE, "' IN ual.usergroups) > 0)")),
                # PR 2023-0405 this one works but may be slower:
                # ''.join(("AND ual.usergroups LIKE '%", c.USERGROUP_MSGRECEIVE, "%'")),

                "ORDER BY u.id"
            ]
            sql = ' '.join(sql_list)

            if logging_on:
                for sql_txt in sql_list:
                    logger.debug(' > ' + str(sql_txt))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                mailbox_user_list = af.dictfetchall(cursor)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        for mailbox_user in mailbox_user_list:
            logger.debug('mailbox_user: ' + str(mailbox_user))

    return mailbox_user_list
# - end of create_mailbox_user_rows


def create_mailbox_school_rows(examyear, request):
    # --- create list of all schools of all countries, for maling list PR2021-10-22
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_mailbox_school_rows ============= ')

    mailbox_school_list = []
    if examyear and request.user.country:
        try:
            # do not filter by country, locked or activated. All schools must be available for messages
            sql_keys = {'ey_code': examyear.code}

            sql_list = ["SELECT sb.id, sb.code AS code, sb.defaultrole,",
                        "school.name, school.article, c.id AS country_pk, c.abbrev AS country",

                        "FROM schools_school AS school",
                        "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
                        "INNER JOIN schools_country AS c ON (c.id = sb.country_id)",
                        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

                        "WHERE ey.code = %(ey_code)s::INT",
                        "ORDER BY sb.id"
                    ]
            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                mailbox_school_list = af.dictfetchall(cursor)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('mailbox_school_list: ' + str(mailbox_school_list))

    return mailbox_school_list
# - end of create_mailbox_school_rows


def create_mailbox_usergroup_rows():
    # --- create list of all usergroups, for mailing list PR2021-10-22
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('create_mailbox_usergroup_rows')

    mailbox_usergroup_list = []
    for key, value in c.MAILBOX_USERGROUPS.items():
        mailbox_usergroup_list.append({'id': key, 'name': value})

    return mailbox_usergroup_list

# - end of create_mailbox_usergroup_rows


#############################
def create_examyear_rows(req_usr, append_dict, examyear_pk=None):
    #  PR2020-10-04 PR2021-09-24 PR2021-12-02 PR2022-07-31
    # --- create rows of all published examyears of this country
    # - create_examyear_rows is used in each page to switch examyears
    # - when role = school: show only published examyears of this school
    # - when role = admin: show also un-published examyears, set filter unpublished also in mod select
    # - when examyear_pk has value it is used in updated create_examyear_rows

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_examyear_rows ============= ')

    sql_keys = {'country_id': req_usr.country.pk}
    if req_usr.role <= c.ROLE_008_SCHOOL:
        sql_keys['sb_id'] = req_usr.schoolbase.pk
        sql_list = ["SELECT ey.id, ey.country_id, ey.code AS examyear_code, CONCAT('examyear_', ey.id::TEXT) AS mapid,",
            "sch.id AS school_id, sch.name, sch.locked, sch.lockedat,",
            "ey.published AS examyear_published, ey.locked AS examyear_locked,",
            "ey.thumbrule_allowed AS thumbrule_allowed,",
            "sch.modifiedby_id, sch.modifiedat, au.last_name AS modby_username",
            "FROM schools_school AS sch",
            "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = sch.modifiedby_id)",
            "WHERE ey.country_id = %(country_id)s::INT",
            "AND sch.base_id = %(sb_id)s::INT"
        ]
    else:
        sql_list = ["SELECT ey.id, ey.country_id, cntr.name AS country,",
                    "CONCAT('examyear_', ey.id::TEXT) AS mapid,",
            "ey.code AS examyear_code, ey.published, ey.locked, ey.createdat, ey.publishedat, ey.lockedat,",
            "ey.no_practexam, ey.sr_allowed, ey.no_centralexam, ey.no_thirdperiod,",
            "ey.order_extra_fixed, ey.order_extra_perc, ey.order_round_to,",
            "ey.order_tv2_divisor, ey.order_tv2_multiplier, ey.order_tv2_max,",
            "ey.order_admin_divisor, ey.order_admin_multiplier, ey.order_admin_max,",
            "ey.thumbrule_allowed AS thumbrule_allowed,",
            "ey.modifiedby_id, ey.modifiedat, au.last_name AS modby_username",
            "FROM schools_examyear AS ey",
            "INNER JOIN schools_country AS cntr ON (cntr.id = ey.country_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = ey.modifiedby_id)",
            "WHERE ey.country_id = %(country_id)s::INT"
        ]

    if examyear_pk:
        # when examyear_pk has value: skip published filter
        sql_list.append('AND ey.id = %(ey_id)s::INT')
        sql_keys['ey_id'] = examyear_pk
    elif req_usr.role < c.ROLE_064_ADMIN:
        sql_list.append("AND ey.published")

    sql_list.append('ORDER BY ey.id')

    sql = ' '.join(sql_list)

    if logging_on:
            logger.debug('    sql: ' + str(sql))

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

    if logging_on:
        for row in examyear_rows:
            logger.debug('    row: ' + str(row))
    return examyear_rows
# --- end of create_examyear_rows


def create_department_rows(examyear, sel_school, sel_schoolbase, skip_allowed_filter, request):
    # --- create rows of all departments of this examyear / country PR2020-09-30 PR2022-08-03 PR2023-01-09
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_department_rows ============= ')
        logger.debug('    examyear: ' + str(examyear))
        logger.debug('    sel_schoolbase: ' + str(sel_schoolbase))

    sql_keys = {'ey_id': examyear.pk}

    sql_list = ["SELECT dep.id, dep.base_id, dep.examyear_id, ey.code AS examyear_code, ey.country_id,",
        "CONCAT('department_', dep.id::TEXT) AS mapid, depbase.code AS base_code,",
        "dep.name, dep.abbrev, dep.sequence, dep.level_req AS lvl_req, dep.sector_req AS sct_req, dep.has_profiel,",
        "dep.modifiedby_id, dep.modifiedat, au.last_name AS modby_username",

        "FROM schools_department AS dep",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
        "LEFT JOIN accounts_user AS au ON (au.id = dep.modifiedby_id)",

        "WHERE ey.id = %(ey_id)s::INT"
    ]

    # PR2023-03-25 always add school_dep filter when role is school
    if request.user.role == c.ROLE_008_SCHOOL:
        if sel_school.depbases:
            school_depbases_list = list(map(int, sel_school.depbases.split(';')))
            sql_list.append(''.join(("AND dep.base_id IN (SELECT UNNEST(ARRAY", str(school_depbases_list), "::INT[]))")))

    allowed_depbase_sql_clause, allowed_depbase_sql_key_dict = acc_prm.get_sqlclause_allowed_depbase_from_request(
        request=request,
        depbase_pk=None,
        sel_schoolbase_pk=sel_schoolbase.pk if sel_schoolbase else None,
        skip_allowed_filter=skip_allowed_filter
    )

    if logging_on:
        logger.debug('    allowed_depbase_sql_clause: ' + str(allowed_depbase_sql_clause))
        logger.debug('    allowed_depbase_sql_key_dict: ' + str(allowed_depbase_sql_key_dict))

    if allowed_depbase_sql_clause:
        sql_list.append(allowed_depbase_sql_clause)
    if allowed_depbase_sql_key_dict:
        sql_keys.update(allowed_depbase_sql_key_dict)

    if logging_on:
        logger.debug('    sql_keys: ' + str(sql_keys))

    sql_list.append("ORDER BY dep.id")
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    if logging_on:
        for row in rows:
            logger.debug('    row: ' + str(row))

    return rows
# --- end of create_department_rows


def create_level_rows(request, examyear, sel_schoolbase, sel_depbase, cur_dep_only, skip_allowed_filter):
    # --- create rows of all levels of this examyear / country PR2020-12-11 PR2021-03-08  PR2021-06-24
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_level_rows ============= ')
        logger.debug('    examyear:       ' + str(examyear))
        logger.debug('    sel_schoolbase: ' + str(sel_schoolbase))
        logger.debug('    sel_depbase:    ' + str(sel_depbase))
        logger.debug('    cur_dep_only:   ' + str(cur_dep_only))

    rows =[]
    if examyear:
        sql_keys = {'ey_id': examyear.pk}

        sql_list = ["SELECT lvl.id, lvl.base_id, lvlbase.code AS lvlbase_code, lvl.examyear_id, ey.code AS examyear_code, ey.country_id,",
            "CONCAT('level_', lvl.id::TEXT) AS mapid,",
            "lvl.name, lvl.abbrev, lvl.sequence, lvl.depbases,",
            "lvl.modifiedby_id, lvl.modifiedat, au.last_name AS modby_username",

            "FROM subjects_level AS lvl ",
            "INNER JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

            "INNER JOIN schools_examyear AS ey ON (ey.id = lvl.examyear_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = lvl.modifiedby_id)",

            "WHERE ey.id = %(ey_id)s::INT"
            ]

        if cur_dep_only:
            depbase_lookup = None
            if sel_depbase:
                department = sch_mod.Department.objects.get_or_none(
                    examyear=examyear,
                    base=sel_depbase
                )
                if department:
                    if department.level_req:
                        depbase_lookup = ''.join( ('%;', str(sel_depbase.pk), ';%') )
                if logging_on:
                    logger.debug('department: ' + str(department))
                    logger.debug('depbase_lookup: ' + str(depbase_lookup))

            if depbase_lookup:
                sql_keys['depbase_pk'] = depbase_lookup
                sql_list.append("AND CONCAT(';', lvl.depbases::TEXT, ';') LIKE %(depbase_pk)s::TEXT")
            else:
                sql_list.append("AND FALSE")

        acc_view.get_userfilter_allowed_lvlbase(
            request=request,
            sql_keys=sql_keys,
            sql_list=sql_list,
            skip_allowed_filter=skip_allowed_filter,
            lvlbase_pk=None,
            sel_schoolbase_pk=sel_schoolbase.pk if sel_schoolbase else None,
            sel_depbase_pk=sel_depbase.pk if sel_depbase else None
        )

        sql_list.append("ORDER BY lvl.id")

        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

            if logging_on:
                logger.debug('rows: ' + str(rows))

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
                    "sct.modifiedby_id, sct.modifiedat, au.last_name AS modby_username",

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

        sql_list.append("ORDER BY sct.id")

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


def create_school_rows(request, examyear, append_dict, skip_allowed_filter=False, school_pk=None):
    # --- create rows of all schools of this examyear / country
    # PR2020-09-18 PR2021-04-23 PR2022-03-13 PR2022-08-07 PR2022-12-05 PR2023-02-16

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' =============== create_school_rows ============= ')
        logger.debug('    school_pk: ' + str(school_pk) + ' ' + str(type(school_pk)))
        logger.debug('    skip_allowed_filter: ' + str(skip_allowed_filter) + ' ' + str(type(skip_allowed_filter)))

    school_rows = []

    try:
        requsr_role = request.user.role
        requsr_schoolbase_pk = request.user.schoolbase.pk

        examyear_pk = examyear.pk if examyear else None
        max_role = requsr_role
        sql_list = ["SELECT school.id, school.base_id, school.examyear_id, ey.code AS examyear_code, ey.country_id, c.name AS country,",
            "CONCAT('school_', school.id::TEXT) AS mapid, sb.defaultrole,",
            "school.name, school.abbrev, school.article, sb.code AS sb_code, school.depbases, school.otherlang,",
            "school.isdayschool, school.iseveningschool, school.islexschool, school.activated, school.activatedat, school.locked, school.lockedat,",
            "school.modifiedby_id, school.modifiedat, au.last_name AS modby_username",

            "FROM schools_school AS school",
            "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
            "INNER JOIN schools_country AS c ON (c.id = ey.country_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = school.modifiedby_id)",

            "WHERE ey.id=" + str(examyear_pk) + "::INT",
            "AND sb.defaultrole <= " + str(max_role) + "::INT"]

        schoolbase_pk = None
        if school_pk:
            # school_pk has only a value after update in SchoolUploadView
            # then one row is retrieved,  to put new values on page
            sql_list.append(''.join(("AND school.id=" , str(school_pk), "::INT")))

        elif requsr_role <= c.ROLE_008_SCHOOL:
            # schools can only view their own school
            schoolbase_pk = requsr_schoolbase_pk

        allowed_schoolbase_sql_clause = acc_prm.get_sqlclause_allowed_schoolbase_from_request(
            request=request,
            schoolbase_pk=schoolbase_pk,
            skip_allowed_filter=skip_allowed_filter
        )
        if allowed_schoolbase_sql_clause:
            sql_list.append(allowed_schoolbase_sql_clause)

        # order by id necessary to make sure that lookup function on client gets the right row
        # TODO to be deprecated when changing do dict instead of sorted dictlist PR2023-01-25
        sql_list.append("ORDER BY school.id")

        sql = ' '.join(sql_list)
        if logging_on:
            for row in sql_list:
                logger.debug(' > ' + str(row))

        with connection.cursor() as cursor:
            cursor.execute(sql)
            school_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('    len(school_rows): ' + str(len(school_rows)))

    # - add messages to school_row, only if school_pk has value
        if school_pk and school_rows and append_dict:
            # when subject_pk has value there is only 1 row
            row = school_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return school_rows
# --- end of create_school_rows
