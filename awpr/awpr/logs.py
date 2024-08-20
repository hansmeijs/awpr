# PR2021-06-28
# from django.contrib.auth import get_user_model

# PR2020-12-13 Deprecation warning: django.contrib.postgres.fields import JSONField  will be removed from Django 4
# instead use: django.db.models import JSONField (is added in Django 3)
# PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
# from django.contrib.postgres.fields import ArrayField #, JSONField

from django.db import connection
# from django.db.models import Model, Manager, ForeignKey, PROTECT, CASCADE, SET_NULL
# from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField, DateField, FileField
from django.utils import timezone

#import json

# PR2018-05-05 use AUTH_USER_MODEL
# from awpr.settings import AUTH_USER_MODEL
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
# from django.utils.translation import gettext_lazy as _
# from awpr import functions as af
from awpr import settings as s
# from awpr.storage_backends import PrivateMediaStorage

from schools import models as sch_mod
# from students import models as stud_mod
from subjects import models as subj_mod

import logging
logger = logging.getLogger(__name__)


def save_to_log(instance, req_mode, request):
    # PR2019-02-23 PR2020-10-23 PR2020-12-15 PR2021-05-11
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- save_to_log  -----')
        logger.debug('req_mode: ' + str(req_mode))
        logger.debug('instance: ' + str(instance))

    if instance:
        model_name = str(instance.get_model_name())
        if logging_on:
            logger.debug('model_name: ' + str(model_name))
        mode = req_mode[0:1] if req_mode else '-'

        modby_id = None
        mod_at = None

        if mode in ('c', 'd'):
            # when log create or delete: add req_user and now
            if request and request.user:
                modby_id = request.user.pk
            mod_at = timezone.now()
        else:
            # when log save: add user and modat of saved record
            if instance.modifiedby_id:
                modby_id = instance.modifiedby_id
            if instance.modifiedat:
                mod_at = instance.modifiedat
        pk_int = instance.pk

        if model_name == 'User':
            pass
            #copy_user_to_log(instance, mode, request)
        elif model_name == 'Examyear':
            pass
            #copy_examyear_to_log(mode, instance, modby_id, mod_at)
        elif model_name == 'ExfilesText':
            pass
        elif model_name == 'Department':
            copy_department_to_log(mode, instance, modby_id, mod_at)
        elif model_name == 'School':
            pass
        elif model_name == 'School_message':
            pass
        elif model_name == 'Published':
            # no log yet
            pass

        elif model_name == 'Level':
            pass
        elif model_name == 'Sector':
            pass
        elif model_name == 'Subjecttype':
            pass
        elif model_name == 'Norm':
            pass
        elif model_name == 'Scheme':
            pass
        elif model_name == 'Subject':
            pass
        elif model_name == 'Schemeitem':
            pass
        elif model_name == 'Exam':
            pass
        elif model_name == 'Package':
            pass
        elif model_name == 'Packageitem':
            pass
        elif model_name == 'Cluster':
            pass

        elif model_name == 'Student':
            pass
        elif model_name == 'Result':
            pass
        elif model_name == 'Resultnote':
            pass
        elif model_name == 'Studentsubject':
            pass
        elif model_name == 'Studentsubjectnote':
            pass
        elif model_name == 'Noteattachment':
            pass
        elif model_name == 'Grade':
            pass
# - end of save_to_log


def savetolog_user(instance, req_mode, request, updated_fields):
    # PR2023-08-10
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('  ----- savetolog_user -----')

    """
    # PR2023-08-10
     not in log: id                  | integer                  |           | not null | nextval('accounts_user_id_seq'::regclass)
     not in log: password            | character varying(128)   |           | not null |
     not in use: first_name          | character varying(150)   |           | not null |
     not in log: lang                | character varying(4)     |           |          |
     last_login          | timestamp with time zone |           |          |
     is_superuser        | boolean                  |           | not null |
     is_staff            | boolean                  |           | not null |
     is_active           | boolean                  |           | not null |
     date_joined         | timestamp with time zone |           | not null |
     username            | character varying(30)    |           | not null |
     last_name           | character varying(50)    |           | not null |
     email               | character varying(254)   |           | not null |
     role                | smallint                 |           | not null |
     activated           | boolean                  |           | not null |
     activated_at        | timestamp with time zone |           |          |
     created_at          | timestamp with time zone |           |          |
     modified_at         | timestamp with time zone |           |          |
     country_id          | integer                  |           |          |
     created_by_id       | integer                  |           |          |
     modified_by_id      | integer                  |           |          |
     schoolbase_id       | integer                  |           |          |
     activationlink_sent | timestamp with time zone |           |          |
     
    extra fields in user_log
    user_id             | integer                  |           | not null |
     mode                | character varying(1)     |           |          |
    
     created_username    | character varying(30)    |           |          |
     modified_username   | character varying(30)    |           |          |
              
    """
    if instance and request and request.user:
        try:
            mode = "'" + req_mode[:1] + "'" if req_mode else "'-'"

            modified_username = "'" + request.user.username_sliced + "'" if request.user.username_sliced else "'-'"

            copy_to_field_list = (
                'last_login', 'is_superuser', 'is_staff', 'is_active', 'date_joined',
                'username', 'last_name', 'email',
                'role', 'activated', 'activated_at', 'activationlink_sent',
                'country_id', 'schoolbase_id',
                'created_by_id', 'created_at',
                'modified_by_id', 'modified_at'
            )
            copy_to_field_str = ', '.join(copy_to_field_list)

            always_copy_fields = ('modified_by_id', 'modified_at')

            copy_from_field_list = []
            for field in copy_to_field_list:
                # - when mode is 'update': copy only updated fields
                # - always copy modified_by_id, 'modified_at
                if mode != 'u' or \
                        field in updated_fields or \
                        field in always_copy_fields:
                    value = field
                else:
                    # add default value when field has not been changed
                    value = 'FALSE' if field in ('is_superuser', 'is_staff', 'is_active', 'activated') else 'NULL'
                copy_from_field_list.append(value)
            copy_from_field_str = ', '.join(copy_from_field_list)

            sql = ' '.join((
                "INSERT INTO accounts_user_log(",
                    "user_id, mode, modified_username,",
                    copy_to_field_str,
                ") SELECT ",
                    "id,", mode, ",", modified_username, ",",
                    copy_from_field_str,

                    "FROM accounts_user AS au ",
                    "WHERE au.id=", str(instance.pk), "::INT",
                "RETURNING id;"
            ))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                if logging_on:
                    logger.debug('    rows: cursor.fetchall()')

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of savetolog_user


def savetolog_examyear(examyear_pk, req_mode, request, updated_fields):
    # PR2023-08-10
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('  ----- savetolog_examyear -----')

    """
    # PR2023-08-10
     id                      | integer                  |           | not null | nextval('schools_examyear_id_seq'::regclass)
     modifiedat              | timestamp with time zone |           | not null |
     code                    | smallint                 |           | not null |
     published               | boolean                  |           | not null |
     locked                  | boolean                  |           | not null |
     createdat               | timestamp with time zone |           |          |
     publishedat             | timestamp with time zone |           |          |
     lockedat                | timestamp with time zone |           |          |
     country_id              | integer                  |           | not null |
     modifiedby_id           | integer                  |           |          |
     no_centralexam          | boolean                  |           | not null |
     no_practexam            | boolean                  |           | not null |
     no_thirdperiod          | boolean                  |           | not null |
     sr_allowed              | boolean                  |           | not null |
     order_extra_fixed       | smallint                 |           | not null |
     order_extra_perc        | smallint                 |           | not null |
     order_round_to          | smallint                 |           | not null |
     order_tv2_divisor       | smallint                 |           | not null |
     order_tv2_max           | smallint                 |           | not null |
     order_tv2_multiplier    | smallint                 |           | not null |
     order_admin_divisor     | smallint                 |           | not null |
     order_admin_max         | smallint                 |           | not null |
     order_admin_multiplier  | smallint                 |           | not null |
     thumbrule_allowed       | boolean                  |           | not null |
     reex03_requests_blocked | boolean                  |           | not null |
     reex_requests_blocked   | boolean                  |           | not null |

    extra fields in examyear_log
    examyear_id             | integer                  |           | not null |
     mode                | character varying(1)     |           |          |

    """
    if examyear_pk and request and request.user:
        try:
            mode = "'" + req_mode[:1] + "'" if req_mode else "'-'"

            # field'codes always copied
            copy_to_field_list = (
               'country_id', 'code', 'published', 'locked',
               'createdat', 'publishedat', 'lockedat',
                'no_centralexam', 'no_practexam', 'no_thirdperiod', 'sr_allowed', 'thumbrule_allowed',
                'order_extra_fixed', 'order_extra_perc', 'order_round_to',
                'order_tv2_divisor', 'order_tv2_max', 'order_tv2_multiplier',
                'order_admin_divisor', 'order_admin_max', 'order_admin_multiplier',
                'reex03_requests_blocked', 'reex_requests_blocked',
                'modifiedby_id', 'modifiedat'
            )
            copy_to_field_str = ', '.join(copy_to_field_list)

            always_copy_fields = ('country_id', 'code', 'modifiedby_id', 'modifiedat')

            copy_from_field_list = []
            for field in copy_to_field_list:
                # - when mode is 'update': copy only updated fields
                # - always copy field 'country_id','code', 'modifiedby_id', ''modifiedat'
                if mode != 'u' or \
                        field in updated_fields or \
                        field in always_copy_fields:
                    value = field
                else:
                    # add NULL value when field has not been changed
                    value = 'NULL'
                copy_from_field_list.append(value)
            copy_from_field_str = ', '.join(copy_from_field_list)

            sql = ' '.join((
                "INSERT INTO schools_examyear_log(",
                "examyear_id, mode, ",
                copy_to_field_str,
                ") SELECT ",
                "id, ", mode, ",",
                copy_from_field_str,

                "FROM schools_examyear AS ey ",
                "WHERE ey.id=", str(examyear_pk), "::INT",
                "RETURNING id;"
            ))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                if logging_on:
                    logger.debug('    rows: cursor.fetchall()')

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of savetolog_examyear


def savetolog_student(student_pk_or_array, log_mode, request, updated_fields):
    # PR2023-08-10 PR2024-07-24 PR2024-08-06
    # called by:
    # - set_student_instance_tobedeleted
    # - create_student_instance
    # - update_student_instance
    # - add_new_examnumbers in StudentCreateExamnumbersView
    # - new_bisexam in StudentLinkStudentView

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('  ----- savetolog_student -----')
        logger.debug('    req_mode: ' + str(log_mode))
        logger.debug('    updated_fields: ' + str(updated_fields))

    if student_pk_or_array and request and request.user:

        try:
            if isinstance(student_pk_or_array, int):
                where_clause = ''.join(("WHERE stud.id=", str(student_pk_or_array), "::INT "))
            elif isinstance(student_pk_or_array, list):
                where_clause = ''.join(("WHERE stud.id IN (SELECT UNNEST(ARRAY", str(student_pk_or_array), "::INT[])) "))
            else:
                where_clause = "WHERE FALSE "

            if isinstance(updated_fields, str):
                updated_field_list = [updated_fields]
            elif isinstance(updated_fields, list):
                updated_field_list = updated_fields
            else:
                updated_field_list = []

            if logging_on:
                logger.debug('    where_clause: ' + str(where_clause))
                logger.debug('    updated_field_list: ' + str(updated_field_list))

            log_field_list = (
                'school_id', 'department_id', 'level_id', 'sector_id', 'scheme_id', 'package_id',
                'lastname', 'firstname', 'prefix', 'gender',
                'idnumber', 'birthdate', 'birthcountry', 'birthcity', 'classname', 'examnumber',
                'extrafacilities', 'iseveningstudent', 'islexstudent', 'bis_exam', 'partial_exam',
                'subj_composition_checked', 'subj_composition_ok',
                'subj_dispensation', 'subj_disp_modifiedby_id', 'subj_disp_modifiedat',
                'linked', 'notlinked', 'withdrawn',
                'result', 'result_status', 'result_info',
                'gl_status', 'gl_modifiedat', 'gl_auth1by_id',
                'tobedeleted', 'deleted',
                'modifiedby_id', 'modifiedat'
            )

            # these fields are always included: 'modifiedby_id', 'modifiedat'
            tobe_copied_field_list = ['modifiedby_id', 'modifiedat']

            for field in updated_field_list:
                if field in log_field_list and field not in tobe_copied_field_list:
                    tobe_copied_field_list.append(field)

            if logging_on:
                logger.debug('    tobe_copied_field_list: ' + str(tobe_copied_field_list))

            tobe_copied_field_str = ', '.join(tobe_copied_field_list)

            sql = ''.join((
                "INSERT INTO students_studentlog(",
                    "student_id, mode,", tobe_copied_field_str,
                ") SELECT ",
                    "id, '", log_mode, "',", tobe_copied_field_str,
                " FROM students_student AS stud ",
                where_clause,
                " RETURNING student_id, mode;"
            ))
            if logging_on:
                logger.debug('    sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                if logging_on:
                    logger.debug('    rows:' + str(cursor.fetchall()))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of savetolog_student


def savetolog_studentsubject(studsubj_pk_or_array, log_mode, updated_fields):
    # PR2023-08-14 PR2024-07-30
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('  ----- savetolog_studentsubject -----')
        logger.debug('    log_mode: ' + str(log_mode))
        logger.debug('    updated_fields: ' + str(updated_fields))


    #  PR2024-04-02 Sentry error: null value in column "gradelist_use_exem" violates not-null constraint
    #   cause: forgot to add non-null field gradelist_use_exem to field_list
    # PR2024-05-30 TODO make gradelist_use_exem nullable, remove from default fieldlist

    if studsubj_pk_or_array:
        try:

            if isinstance(studsubj_pk_or_array, int):
                where_clause = ''.join(("WHERE studsubj.id = ", str(studsubj_pk_or_array), "::INT;"))
            elif isinstance(studsubj_pk_or_array, list):
                where_clause = ''.join(("WHERE studsubj.id IN (SELECT UNNEST(ARRAY", str(studsubj_pk_or_array), "::INT[]));"))
            else:
                where_clause = "WHERE FALSE;"

            if isinstance(updated_fields, str):
                updated_field_list = [updated_fields]
            elif isinstance(updated_fields, list):
                updated_field_list = updated_fields
            else:
                updated_field_list = []

            mode = "'" + log_mode[:1] + "'" if log_mode else "'-'"

            log_field_list = (
                # NIU: 'student_id', 'subject_id',
                'schemeitem_id', 'cluster_id', 'ete_cluster_id',
                'is_extra_nocount', 'is_extra_counts', 'is_thumbrule',
                'pws_title', 'pws_subjects',
                'has_exemption', 'has_sr', 'has_reex', 'has_reex03', 'exemption_year',
                'pok_validthru', 'pok_sesr', 'pok_pece', 'pok_final',
                'subj_auth1by_id', 'subj_auth2by_id', 'subj_published_id',
                'tobechanged', 'tobedeleted', 'deleted',

                #  PR2024-04-02 fields added:
                'sr_published_id', 'reex_published_id', 'reex3_published_id', 'pok_published_id',
                'gradelist_sesrgrade', 'gradelist_pecegrade', 'gradelist_finalgrade', 'gradelist_use_exem',

                'modifiedby_id', 'modifiedat'
            )

            # these fields are always included: 'modifiedby_id', 'modifiedat'
            tobe_copied_field_list = ['modifiedby_id', 'modifiedat']

            # PR2024-06-02 TODO in log file all fields must be set null=True , also boolean fields
            # gradelist_use_exem = BooleanField(null=True)
            # till that is done: add gradelist_use_exem as requited field
            tobe_copied_field_list.append('gradelist_use_exem')

            for field in updated_field_list:
                if field in log_field_list and field not in tobe_copied_field_list:
                    tobe_copied_field_list.append(field)

            if logging_on:
                logger.debug('    tobe_copied_field_list: ' + str(tobe_copied_field_list))

            tobe_copied_field_str = ', '.join(tobe_copied_field_list)

            sql = ''.join((
                "INSERT INTO students_studentsubjectlog(",
                    "studentsubject_id, mode,", tobe_copied_field_str,
                ") SELECT ",
                    "id, '", log_mode, "',", tobe_copied_field_str,
                " FROM students_studentsubject AS studsubj ",
                where_clause
            ))

            with connection.cursor() as cursor:
                cursor.execute(sql)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of savetolog_studentsubject


def savetolog_grade(grade_pk_or_array, log_mode, request, updated_fields):
    # PR2023-08-15 PR2024-02-24
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('  ----- savetolog_grade -----')
        logger.debug('    req_mode: ' + str(log_mode))
        logger.debug('    updated_fields: ' + str(updated_fields))

    if grade_pk_or_array and request and request.user:
        try:
            if isinstance(grade_pk_or_array, int):
                where_clause = ''.join(("= ", str(grade_pk_or_array), "::INT;"))
            elif isinstance(grade_pk_or_array, list):
                where_clause = ''.join(("IN (SELECT UNNEST(ARRAY", str(grade_pk_or_array), "::INT[])) "))
            else:
                where_clause = "WHERE FALSE;"

            mode = "'" + log_mode[:1] + "'" if log_mode else "'-'"
            field_list = (
                'studentsubject_id',
                'pescore', 'cescore', 'segrade', 'srgrade', 'sesrgrade',
                'pegrade', 'cegrade', 'pecegrade', 'finalgrade', 'exemption_imported',
                'deleted', 'status',

                # PR2024-02-27 TODO add:
                # 'se_published_id', 'se_blocked' ,
                # 'sr_published_id', 'sr_blocked'
                # 'pe_published_id', 'pe_blocked'
                # 'ce_published_id', 'ce_blocked'

                'modifiedby_id', 'modifiedat'
            )

            # PR2024-05-03 Sentry error: null value in column "gradelist_use_exem" violates not-null constraint
            # solved by adding 'gradelist_use_exem' to tobe_copied_field_list
            # PR2024-05-30 not true: table gradelog does not have a field 'gradelist_use_exem', removed from list

            # these fields are always included:
            tobe_copied_field_list = ['examperiod', 'status', 'modifiedby_id', 'modifiedat']  # was: , 'gradelist_use_exem']

            for field in field_list:
                # - when mode is 'update': copy only updated fields and required fields

                if field not in tobe_copied_field_list:
                    is_create_or_import = mode in ("'c'", "'i'")

            # copy all fields when mode = 'create' or 'import'
                    if is_create_or_import:
                        tobe_copied_field_list.append(field)

            # otherwise: copy updated_fields in tobe_copied_field_list
                    elif field in updated_fields:
                        tobe_copied_field_list.append(field)

            tobe_copied_field_str = ', '.join(tobe_copied_field_list)

            sql = ' '.join((
                "INSERT INTO students_gradelog(",
                "grade_id, mode,", tobe_copied_field_str,
                ") SELECT",
                "id,", mode, ",", tobe_copied_field_str,
                "FROM students_grade AS grade",
                "WHERE grade.id=", str(grade_pk), "::INT",
                "RETURNING id;"
            ))
            if logging_on:
                logger.debug('    tobe_copied_field_list: ' + str(tobe_copied_field_list))
                logger.debug('    sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                if logging_on:
                    logger.debug('    rows: ' + str(cursor.fetchall()))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of savetolog_grade
##################

def copy_department_to_log(mode, instance, modby_id, mod_at):  # PR2021-04-25 PR2021-06-28
    # fields checked and correct PR2021-12-13
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- copy_department_to_log  -----')
        logger.debug('mode: ' + str(mode))
        logger.debug('instance: ' + str(instance) + ' ' + str(type(instance)))
        logger.debug('modby_id: ' + str(modby_id) + ' ' + str(type(modby_id)))
        logger.debug('mod_at: ' + str(mod_at) + ' ' + str(type(mod_at)))

# - get most recent examyear_log (with the highest id)  PR20201-06-28
    examyear_log = get_examyear_log(instance.examyear_id)

    if examyear_log:
        try:
            department_log = sch_mod.Department_log(
                department_id=instance.id,

                base_id=instance.base_id,
                examyear_log_id=examyear_log.id,

                name=instance.name,
                abbrev=instance.abbrev,
                sequence=instance.sequence,

                level_req=instance.level_req,
                sector_req=instance.sector_req,
                has_profiel=instance.has_profiel,

                modifiedby_id=modby_id,
                modifiedat=mod_at,

                mode=mode
            )
            department_log.save()

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of copy_department_to_log


def copy_scheme_to_log(mode, instance, modby_id, mod_at):  # PR2021-06-28
    # fields updated PR2021-12-13
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- copy_scheme_to_log  -----')  # PR2021-06-28
        logger.debug('mode: ' + str(mode))
        logger.debug('instance: ' + str(instance) + ' ' + str(type(instance)))
        logger.debug('modby_id: ' + str(modby_id) + ' ' + str(type(modby_id)))
        logger.debug('mod_at: ' + str(mod_at) + ' ' + str(type(mod_at)))

    # get most recent department_log, level_log, sector_log (with the highest id)
    department_log = get_department_log(instance.department_id)
    level_log = get_level_log(instance.level_id)
    sector_log = get_sector_log(instance.sector_id)

    try:
        scheme_log = subj_mod.Scheme_log(
            scheme_id=instance.id,

            department_log=department_log.id,
            level_log=level_log.id,
            sector_log=sector_log.id,

            name=instance.name,
            fields=instance.fields,

            min_subjects=instance.min_subjects,
            max_subjects=instance.max_subjects,

            min_mvt=instance.min_mvt,
            max_mvt=instance.max_mvt,

            min_wisk=instance.min_wisk,
            max_wisk=instance.max_wisk,

            min_combi=instance.min_combi,
            max_combi=instance.max_combi,

            rule_avg_pece_sufficient=instance.rule_avg_pece_sufficient,
            rule_avg_pece_notatevlex=instance.rule_avg_pece_notatevlex,  # PR2021-11-27  NOT IN USE: mustbe_avg_pece_sufficient not at evening or lex school
            rule_core_sufficient=instance.rule_core_sufficient,
            rule_core_notatevlex=instance.rule_core_notatevlex,  # PR2021-11-27  NOT IN USE: mustbe_avg_pece_sufficient not at evening or lex school

            modifiedby_id=modby_id,
            modifiedat=mod_at,
            mode=mode
        )
        scheme_log.save()

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# - end of copy_scheme_to_log


def get_examyear_log(examyear_id):
    # get most recent examyear_log (with the highest id)  PR20201-06-28
    log = None
    try:
        log = sch_mod.Examyear_log.objects.filter(
            examyear_id=examyear_id
        ).order_by('-pk').first()
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
    return log


def get_department_log(department_id):
    # get most recent department_log (with the highest id)  PR20201-06-28
    log = None
    try:
        log = sch_mod.Department_log.objects.filter(
            department_id=department_id
        ).order_by('-pk').first()
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
    return log


def get_level_log(level_id): # PR20201-06-28
    log = None
    try:
        log = subj_mod.Level_log.objects.filter(
            level_id=level_id
        ).order_by('-pk').first()
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
    return log


def get_sector_log(sector_id): # PR20201-06-28
    log = None
    try:
        log = subj_mod.Sector_log.objects.filter(
            sector_id=sector_id
        ).order_by('-pk').first()
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
    return log


def get_exam_log_pk(exam_id): # PR2021-12-13
    log_pk = None
    try:
        log = subj_mod.Exam_log.objects.filter(
            exam_id=exam_id
        ).order_by('-pk').first().values('pk')
    # add Exam_log if it does not exist yet
        # TODO create Exam_log if it does not exist yet
        if log is None:
            pass

        if log:
            log_pk = getattr(log, 'pk')
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
    return log_pk


############################## VERSION 2 ############################### PR2024-06-02
def copytolog_grade_v2(grade_pk_list, log_mode, modifiedby_id=None):
    # PR2024-06-02
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- copytolog_grade_v2 ----- ')
        logger.debug('    grade_pk_list: ' + str(grade_pk_list))
    def where_clause(pk_list):
        sql_clause = 'AND FALSE'
        if pk_list:
            if len(pk_list) == 1:
                sql_clause = ''.join(("WHERE grd.id=", str(pk_list[0]), "::INT;"))
            else:
                sql_clause = ''.join(("WHERE grd.id IN (SELECT UNNEST(ARRAY", str(pk_list), "::INT[]));"))
        return sql_clause

    def sql_mode_value():
        mode = log_mode[:1] if log_mode else '-'
        return ''.join(("'", mode, "', "))

    def sql_modifiedvalue():
        if modifiedby_id:
            modifiedat_str = ''.join(("'", str(timezone.now()), "'"))
            sql_value = ''.join((
                str(modifiedby_id), "::INT, ",
                modifiedat_str, " ",
            ))
        else:
            sql_value = "modifiedby_id, modifiedat "
        return sql_value

    if grade_pk_list:

        try:
            field_list = ''.join((
                'examperiod, pescore, cescore, segrade, srgrade, sesrgrade, pegrade, cegrade, pecegrade, finalgrade, ',
                'exemption_imported, deleted, status, '
            ))
            # PR2024-02-27 TODO add:
            # se_published_id, sr_published_id, pe_published_id, ce_published_id
            # se_blocked, sr_blocked, pe_blocked, ce_blocked

            sql = ''.join((
                "INSERT INTO students_gradelog (grade_id, ", field_list, " mode, modifiedby_id, modifiedat) ",
                "SELECT id, ", field_list,
                sql_mode_value(),
                sql_modifiedvalue(),
                "FROM students_grade AS grd ",
                where_clause(grade_pk_list)
            ))

            with connection.cursor() as cursor:
                cursor.execute(sql)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

# - end of copytolog_grade_v2



