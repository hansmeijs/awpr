# PR2021-06-28
from django.contrib.auth import get_user_model

# PR2020-12-13 Deprecation warning: django.contrib.postgres.fields import JSONField  will be removed from Django 4
# instead use: django.db.models import JSONField (is added in Django 3)
# PR2021-01-25 don't use ArrayField, JSONField, because they are not compatible with MSSQL
from django.contrib.postgres.fields import ArrayField #, JSONField

from django.db import connection
from django.db.models import Model, Manager, ForeignKey, PROTECT, CASCADE, SET_NULL
from django.db.models import CharField, IntegerField, PositiveSmallIntegerField, BooleanField, DateTimeField, DateField, FileField
from django.utils import timezone

import json

# PR2018-05-05 use AUTH_USER_MODEL
from awpr.settings import AUTH_USER_MODEL
from django.utils.translation import ugettext_lazy as _
from awpr import constants as c
from awpr import settings as s
from awpr.storage_backends import PrivateMediaStorage

from schools import models as sch_mod
from students import models as stud_mod
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

        if model_name == 'Examyear':
            copy_examyear_to_log(mode, instance, modby_id, mod_at)
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


def copy_examyear_to_log(mode, instance, modby_id, mod_at):
    # fields update PR2021-12-13
    try:
        examyear_log = sch_mod.Examyear_log(
            examyear_id=instance.id,
            # no log exists for country
            country_id=instance.country_id,

            code=instance.code,
            published=instance.published,
            locked=instance.locked,

            no_practexam=instance.no_practexam,
            sr_allowed=instance.sr_allowed,
            no_centralexam=instance.no_centralexam,
            no_thirdperiod=instance.no_thirdperiod,

            createdat=instance.createdat,
            publishedat=instance.publishedat,
            lockedat=instance.lockedat,

            order_extra_fixed=instance.order_extra_fixed,
            order_extra_perc=instance.order_extra_perc,
            order_round_to=instance.order_round_to,

            order_tv2_divisor=instance.order_tv2_divisor,
            order_tv2_multiplier=instance.order_tv2_multiplier,
            order_tv2_max=instance.order_tv2_max,

            order_admin_divisor=instance.order_admin_divisor,
            order_admin_multiplier=instance.order_admin_multiplier,
            order_admin_max=instance.order_admin_max,

            modifiedby_id=modby_id,
            modifiedat=mod_at,
            mode=mode
        )
        examyear_log.save()
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))


def copy_department_to_log(mode, instance, modby_id, mod_at):  # PR2021-04-25 PR2021-06-28
    # fields checked and correct PR2021-12-13
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- copy_department_to_log  -----')
        logger.debug('mode: ' + str(mode))
        logger.debug('instance: ' + str(instance) + ' ' + str(type(instance)))
        logger.debug('modby_id: ' + str(modby_id) + ' ' + str(type(modby_id)))
        logger.debug('mod_at: ' + str(mod_at) + ' ' + str(type(mod_at)))

# - get most recent examyear_log (with highest id)  PR20201-06-28
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

    # get most recent department_log, level_log, sector_log (with highest id)
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


def copy_grade_to_log(mode, instance, modby_id, mod_at):  # PR2021-12-13
    # ISN
    # fields updated PR2021-12-13
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- copy_grade_to_log  -----')  # PR2021-06-28
        logger.debug('mode: ' + str(mode))
        logger.debug('instance: ' + str(instance) + ' ' + str(type(instance)))
        logger.debug('modby_id: ' + str(modby_id) + ' ' + str(type(modby_id)))
        logger.debug('mod_at: ' + str(mod_at) + ' ' + str(type(mod_at)))

    # get most recent studentsubject_log, exam_log (with highest id)
    studentsubject_log_pk = get_studentsubject_log_pk(instance.studentsubject_id)
    exam_log_pk = get_exam_log_pk(instance.exam_id)
    if studentsubject_log_pk:
        try:
            grade_log = stud_mod.Grade_log(
                grade_id=instance.id,

                studentsubject_log_id=studentsubject_log_pk,
                exam_log_id=exam_log_pk,

                examperiod=instance.examperiod,
                pescore=instance.pescore,
                cescore=instance.cescore,
                segrade=instance.segrade,
                srgrade=instance.srgrade,
                sesrgrade=instance.sesrgrade,
                pegrade=instance.pegrade,
                cegrade=instance.cegrade,
                pecegrade=instance.pecegrade,
                finalgrade=instance.finalgrade,
                
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
                rule_avg_pece_notatevlex=instance.rule_avg_pece_notatevlex,
                # PR2021-11-27  NOT IN USE: mustbe_avg_pece_sufficient not at evening or lex school
                rule_core_sufficient=instance.rule_core_sufficient,
                rule_core_notatevlex=instance.rule_core_notatevlex,
                # PR2021-11-27  NOT IN USE: mustbe_avg_pece_sufficient not at evening or lex school

                modifiedby_id=modby_id,
                modifiedat=mod_at,
                mode=mode
            )
            grade_log.save()

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

# - end of copy_grade_to_log


def get_examyear_log(examyear_id):
    # get most recent examyear_log (with highest id)  PR20201-06-28
    log = None
    try:
        log = sch_mod.Examyear_log.objects.filter(
            examyear_id=examyear_id
        ).order_by('-pk').first()
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
    return log


def get_department_log(department_id):
    # get most recent department_log (with highest id)  PR20201-06-28
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


def get_studentsubject_log_pk(studentsubject_id): # PR2021-12-13
    log_pk = None
    try:
        log = stud_mod.Studentsubject_log.objects.filter(
            studentsubject_id=studentsubject_id
        ).order_by('-pk').first().values('pk')

    # add Studentsubject_log if it does not exist yet
        # TODO create Studentsubject_log if it does not exist yet
        if log is None:
            pass

        if log:
            log_pk = getattr(log, 'pk')
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
    return log_pk


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

"""
Old save_to_log with SQL, not in use PR2021-04-25
fields updated PR2021-12-13
elif model_name == 'Grade':
    # this one not working, cannot get filter pc.id with LIMIT 1 in query, get info from pricecodelist instead
    sub_ssl_list = ["SELECT id, studentsubject_id AS studsubj_id,",
                    "FROM studentsubject_log",
                    "ORDER BY id DESC NULLS LAST LIMIT 1"]
    sub_ssl = ' '.join(sub_ssl_list)
    # note: multiple WITH clause syntax:WITH cte1 AS (SELECT...), cte2 AS (SELECT...) SELECT * FROM ...
    sql_keys = {'grade_id': pk_int,  'mode': mode, 'modby_id': modby_id, 'mod_at': mod_at}
    sql_list = ["WITH sub_ssl AS (" + sub_ssl + ")",
                "INSERT INTO students_grade_log (id,",
                    "grade_id, studentsubject_log_id, exam_id, examperiod,",
                    
                    "pescore, cescore, segrade, srgrade, sesrgrade,",
                    "pegrade, cegrade, pecegrade, finalgrade,",
                    
                    "sepublished_id, sr_published_id, pepublished_id, cepublished_id,",
                    "seblocked, srblocked, peblocked, ceblocked,",
                    
                    "answers, blanks, answers_published_id,",
                    
                    "mode, modifiedby_id, modifiedat)",
                    
                "SELECT nextval('students_grade_log_id_seq'),",
                    "grade_id, sub_ssl.id, exam_id, examperiod, ",
                    
                    "pescore, cescore, segrade, srgrade, sesrgrade,",
                    "pegrade, cegrade, pecegrade, finalgrade,",
                    
                    "sepublished_id, sr_published_id, pepublished_id, cepublished_id,",
                    "seblocked, srblocked, peblocked, ceblocked,",
                    
                    "answers, blanks, answers_published_id,",
                    
                    "%(mode)s::TEXT, %(modby_id)s::INT, %(mod_at)s::DATE",
                "FROM students_grade AS grade",
                "INNER JOIN sub_ssl ON (sub_ssl.studsubj_id = grade.studentsubject_id)",
                "WHERE (grade.id = %(grade_id)s::INT"]

    sql_list = ["SELECT nextval('students_grade_log_id_seq') AS sgl_id,",
                    "grade.id, grade.examperiod,",
                    "%(mode)s::TEXT AS mode, %(modby_id)s::INT AS modby_id, %(mod_at)s::DATE AS mod_at",
                "FROM students_grade AS grade",
                "WHERE id = %(grade_id)s::INT"]
    sql = ' '.join(sql_list)
    #logger.debug('sql_keys: ' + str(sql_keys))
    #logger.debug('sql: ' + str(sql))

    #logger.debug('---------------------- ')
    with connection.cursor() as cursor:
        #logger.debug('================= ')
        cursor.execute(sql, sql_keys)
        #for qr in connection.queries:
            #logger.debug('-----------------------------------------------------------------------------')
            #logger.debug(str(qr))

        #logger.debug('---------------------- ')
        #rows = dictfetchall(cursor)
        #logger.debug('---------------------- ')
        #for row in rows:
            #logger.debug('row: ' + str(row))


"""



