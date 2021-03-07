from django.db import connection
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from datetime import datetime

from awpr import constants as c
from awpr import functions as af

from schools import models as sch_mod
from subjects import models as subj_mod

import logging
logger = logging.getLogger(__name__)

def copy_deps_from_prev_examyear(request_user, prev_examyear_pk, new_examyear_pk):
    # copy departments from previous examyear if it exists # PR2019-02-23

    if prev_examyear_pk and new_examyear_pk:
        modifiedby_id = request_user.id
        modifiedat = timezone.now()

        cursor = connection.cursor()

# - copy departments from previous examyear
        field_list = 'name, abbrev, sequence, level_req, sector_req, has_profiel,'
        sql_list =['INSERT INTO schools_department',
                   '(base_id, examyear_id,',
                   field_list,
                   'modifiedby_id, modifiedat)',
                   'SELECT base_id, %(new_ey_pk)s AS new_examyear_id,',
                   field_list,
                   '%(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                   'FROM schools_department WHERE examyear_id = %(prev_ey_pk)s;']
        sql = ' '.join(sql_list)
        sql_keys = {'prev_ey_pk': prev_examyear_pk,
                    'new_ey_pk': new_examyear_pk,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_keys)
        connection.commit()

# - get latest Examyear_log row that corresponds with new_examyear.
        # The Examyear_log row is created at self.new_examyear.save in Schools.Model
        new_examyear_log = sch_mod.Examyear_log.objects.filter(examyear_id=new_examyear_pk).order_by('-id').first()
        new_examyear_log_id = new_examyear_log.id

# - copy new departments to department_log
        # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
        sql_list =['INSERT INTO schools_department_log',
                    '(department_id, base_id, examyear_log_id,',
                    field_list,
                    'mode, modifiedby_id, modifiedat)',
                    'SELECT id, base_id, %(new_ey_log_pk)s AS examyear_log_id,',
                    field_list,
                    '%(mode)s AS mode, %(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM schools_department WHERE examyear_id = %(new_ey_log_pk)s;']
        sql = ' '.join(sql_list)
        sql_log_keys = {'new_ey_log_pk': new_examyear_log_id,
                    'mode':  c.MODE_C_CREATED,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql,sql_log_keys)
        connection.commit()

def copy_levels_from_prev_examyear(request_user, prev_examyear_pk, new_examyear_pk):
    # copy levels from previous examyear if it exists # PR2019-02-23 PR2020-10-06

    if prev_examyear_pk and new_examyear_pk:
        modifiedby_id = request_user.id
        modifiedat = timezone.now()

        cursor = connection.cursor()

# - copy levels from previous examyear
        field_list = 'name, abbrev, sequence, depbases,'
        sql_list = ['INSERT INTO subjects_level',
                    '(base_id, examyear_id,',
                    field_list,
                    'modifiedby_id, modifiedat)',
                    'SELECT base_id, %(new_ey_pk)s AS new_examyear_id,',
                    field_list,
                    '%(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM subjects_level WHERE examyear_id = %(prev_ey_pk)s;']
        sql = ' '.join(sql_list)
        sql_keys = {'prev_ey_pk': prev_examyear_pk,
                    'new_ey_pk': new_examyear_pk,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_keys)
        connection.commit()

        # - get latest Examyear_log row that corresponds with new_examyear.
        # The Examyear_log row is created at self.new_examyear.save in Schools.Model
        new_examyear_log = sch_mod.Examyear_log.objects.filter(examyear_id=new_examyear_pk).order_by(
            '-id').first()
        new_examyear_log_id = new_examyear_log.id

        # - copy new levels to level_log
        # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
        sql_list = ['INSERT INTO subjects_level_log',
                    '(level_id, base_id, examyear_log_id,',
                    field_list,
                    'mode, modifiedby_id, modifiedat)',
                    'SELECT id, base_id, %(new_ey_log_pk)s AS examyear_log_id,',
                    field_list,
                    '%(mode)s AS mode, %(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM subjects_level WHERE examyear_id = %(new_ey_log_pk)s;']
        sql = ' '.join(sql_list)
        sql_log_keys = {'new_ey_log_pk': new_examyear_log_id,
                    'mode':   c.MODE_C_CREATED,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_log_keys)
        connection.commit()

def copy_sectors_from_prev_examyear(request_user, prev_examyear_pk, new_examyear_pk):
    # copy sectors from previous examyear if it exists # PR2019-02-23

    if prev_examyear_pk and new_examyear_pk:
        modifiedby_id = request_user.id
        modifiedat = timezone.now()

        cursor = connection.cursor()

        # - copy sectors from previous examyear
        field_list = 'name, abbrev, sequence, depbases,'
        sql_list = ['INSERT INTO subjects_sector',
                    '(base_id, examyear_id,',
                    field_list,
                    'modifiedby_id, modifiedat)',
                    'SELECT base_id, %(new_ey_pk)s AS new_examyear_id,',
                    field_list,
                    '%(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM subjects_sector WHERE examyear_id = %(prev_ey_pk)s;']
        sql = ' '.join(sql_list)
        sql_keys = {'prev_ey_pk': prev_examyear_pk,
                    'new_ey_pk': new_examyear_pk,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql,sql_keys)
        connection.commit()

        # - get latest Examyear_log row that corresponds with new_examyear.
        # The Examyear_log row is created at self.new_examyear.save in Schools.Model
        new_examyear_log = sch_mod.Examyear_log.objects.filter(examyear_id=new_examyear_pk).order_by(
            '-id').first()
        new_examyear_log_id = new_examyear_log.id

        # - copy new sectors to sector_log
        # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
        sql_list = ['INSERT INTO subjects_sector_log',
                    '(sector_id, base_id, examyear_log_id,',
                    field_list,
                    'mode, modifiedby_id, modifiedat)',
                    'SELECT id, base_id, %(new_ey_log_pk)s AS examyear_log_id,',
                    field_list,
                    '%(mode)s AS mode, %(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM subjects_sector WHERE examyear_id = %(new_ey_log_pk)s;']
        sql = ' '.join(sql_list)
        sql_log_keys = {'new_ey_log_pk': new_examyear_log_id,
                    'mode':   c.MODE_C_CREATED,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_log_keys)
        connection.commit()


def copy_schools_from_prev_examyear(request_user, prev_examyear_pk, new_examyear_pk):
    # copy schools from previous examyear if it exists # PR2019-02-23 PR2020-10-07

    if prev_examyear_pk and new_examyear_pk:
        modifiedby_id = request_user.id
        modifiedat = timezone.now()

        cursor = connection.cursor()
        # - copy schools from previous examyear to new_examyear
        field_list = 'code, name, abbrev, article, depbases, activated, locked, activatedat, lockedat,'
        sql_list = ['INSERT INTO schools_school (',
                        'base_id, examyear_id,',
                        field_list,
                        'modifiedby_id, modifiedat',
                    ') SELECT base_id, %(new_ey_pk)s AS examyear_id,',
                        field_list,
                        '%(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM schools_school WHERE examyear_id = %(prev_ey_pk)s;']
        sql = ' '.join(sql_list)
        sql_keys = {'prev_ey_pk': prev_examyear_pk,
                    'new_ey_pk': new_examyear_pk,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_keys)
        connection.commit()

        # - get latest Examyear_log row that corresponds with new_examyear.
        # The Examyear_log row is created at self.new_examyear.save in Schools.Model
        new_examyear_log = sch_mod.Examyear_log.objects.filter(examyear_id=new_examyear_pk).order_by(
            '-id').first()
        new_examyear_log_id = new_examyear_log.id

        # - copy new subjects to subject_log
        # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
        sql_list = ['INSERT INTO schools_school_log (',
                        'school_id, base_id, examyear_log_id,',
                        field_list,
                        'mode, modifiedby_id, modifiedat',
                    ') SELECT id, base_id,'
                        '%(new_ey_log_pk)s AS examyear_log_id,',
                        field_list,
                        '%(mode)s AS mode, %(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM schools_school WHERE examyear_id = %(new_ey_log_pk)s;']
        sql = ' '.join(sql_list)
        sql_log_keys = {'new_ey_log_pk': new_examyear_log_id,
                    'mode':   c.MODE_C_CREATED,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_log_keys)
        connection.commit()


def copy_subjecttypes_from_prev_examyear(request_user, prev_examyear_pk, new_examyear_pk):
    # copy subjecttypes from previous examyear if it exists # PR2019-02-23

    if prev_examyear_pk and new_examyear_pk:
        modifiedby_id = request_user.id
        modifiedat = timezone.now()

        cursor = connection.cursor()

        # - copy subjecttypes from previous examyear
        field_list = 'name, abbrev, code, sequence, depbases, has_prac, has_pws, one_allowed,'

        sql_list = ['INSERT INTO subjects_subjecttype',
                    '(base_id, examyear_id,',
                    field_list,
                    'modifiedby_id, modifiedat)',
                    'SELECT base_id, %(new_ey_pk)s AS new_examyear_id,',
                    field_list,
                    '%(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM subjects_subjecttype WHERE examyear_id = %(prev_ey_pk)s;']
        sql = ' '.join(sql_list)
        sql_keys = {'prev_ey_pk': prev_examyear_pk,
                    'new_ey_pk': new_examyear_pk,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_keys)
        connection.commit()

        # - get latest Examyear_log row that corresponds with new_examyear.
        # The Examyear_log row is created at self.new_examyear.save in Schools.Model
        new_examyear_log = sch_mod.Examyear_log.objects.filter(examyear_id=new_examyear_pk).order_by(
            '-id').first()
        new_examyear_log_id = new_examyear_log.id

        # - copy new subjecttypes to subjecttype_log
        # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
        sql_list = ['INSERT INTO subjects_subjecttype_log',
                    '(subjecttype_id, base_id, examyear_log_id,',
                    field_list,
                    'mode, modifiedby_id, modifiedat)',
                    'SELECT id, base_id, %(new_ey_log_pk)s AS examyear_log_id,',
                    field_list,
                    '%(mode)s AS mode, %(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM subjects_subjecttype WHERE examyear_id = %(new_ey_log_pk)s;']
        sql = ' '.join(sql_list)
        sql_log_keys = {'new_ey_log_pk': new_examyear_log_id,
                    'mode':   c.MODE_C_CREATED,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_log_keys)
        connection.commit()


def copy_subjects_from_prev_examyear(request_user, prev_examyear_pk, new_examyear_pk):
    # copy subjects from previous examyear if it exists # PR2019-02-23

    if prev_examyear_pk and new_examyear_pk:
        modifiedby_id = request_user.id
        modifiedat = timezone.now()

        cursor = connection.cursor()

        # - copy subjects from previous examyear to new_examyear
        field_list = 'name, abbrev, sequence, depbases,'
        sql_list = ['INSERT INTO subjects_subject (',
                        'base_id, examyear_id,',
                        field_list,
                        'modifiedby_id, modifiedat',
                    ') SELECT base_id, %(new_ey_pk)s AS examyear_id,',
                        field_list,
                        '%(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM subjects_subject WHERE examyear_id = %(prev_ey_pk)s;']
        sql = ' '.join(sql_list)
        sql_keys = {'prev_ey_pk': prev_examyear_pk,
                    'new_ey_pk': new_examyear_pk,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_keys)
        connection.commit()

        # - get latest Examyear_log row that corresponds with new_examyear.
        # The Examyear_log row is created at self.new_examyear.save in Schools.Model
        new_examyear_log = sch_mod.Examyear_log.objects.filter(examyear_id=new_examyear_pk).order_by(
            '-id').first()
        new_examyear_log_id = new_examyear_log.id

        # - copy new subjects to subject_log
        # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
        sql_list = ['INSERT INTO subjects_subject_log (',
                        'subject_id, base_id, examyear_log_id,',
                        field_list,
                        'mode, modifiedby_id, modifiedat',
                    ') SELECT id, base_id,'
                        '%(new_ey_log_pk)s AS examyear_log_id,',
                        field_list,
                        '%(mode)s AS mode, %(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM subjects_subject WHERE examyear_id = %(new_ey_log_pk)s;']
        sql = ' '.join(sql_list)
        sql_log_keys = {'new_ey_log_pk': new_examyear_log_id,
                    'mode':   c.MODE_C_CREATED,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_log_keys)
        connection.commit()


def copy_schemes_from_prev_examyear(request_user, prev_examyear_pk, new_examyear_pk):
    # copy schemes from previous examyear if it exists # PR2019-02-23

    if prev_examyear_pk and new_examyear_pk:
        modifiedby_id = request_user.id
        modifiedat = timezone.now()

        cursor = connection.cursor()

# - copy schemes from previous examyear
        # get department_id of new_examyear, using subquery with filter base_id and examyear_id = new_examyear_pk
        # als with level_id andsector_id
        sql_list = ['INSERT INTO subjects_scheme',
                    '(department_id, level_id, sector_id, name, fields, modifiedby_id, modifiedat)',
                    'SELECT',
                    '(SELECT id FROM schools_department AS d WHERE d.base_id = dep.base_id AND d.examyear_id = %(new_ey_pk)s),',
                    '(SELECT id FROM subjects_level AS l WHERE l.base_id = lvl.base_id AND l.examyear_id = %(new_ey_pk)s),',
                    '(SELECT id FROM subjects_sector AS s WHERE s.base_id = sct.base_id AND s.examyear_id = %(new_ey_pk)s),',
                    'sch.name, sch.fields,',
                    '%(mod_by)s AS modifiedby_id, %(mod_at)s AS modifiedat',
                    'FROM subjects_scheme AS sch',
                    'INNER JOIN schools_department AS dep ON dep.id = sch.department_id',
                    'INNER JOIN subjects_level AS lvl ON lvl.id = sch.level_id',
                    'INNER JOIN subjects_sector AS sct ON sct.id = sch.sector_id',
                    'WHERE dep.examyear_id=%(prev_ey_pk)s;']
        sql = ' '.join(sql_list)
        sql_keys = {'prev_ey_pk': prev_examyear_pk,
                    'new_ey_pk': new_examyear_pk,
                    'mod_by': modifiedby_id,
                    'mod_at': modifiedat}
        cursor.execute(sql, sql_keys)
        connection.commit()

        # Fields from  subjects_scheme_log are:
            # id, scheme_id, dep_log_id, level_log_id, sector_log_id, '
            # name, fields, dep_mod, level_mod, sector_mod, name_mod, fields_mod'
            # 'mode, modifiedby_id, modifiedat'

        # PR2019-02-24
        sql_list = ['INSERT INTO Scheme_log (',
                        'scheme_id, department_log_id, level_log_id, sector_log_id,',
                        'name, fields, mode, department_mod, level_mod, sector_mod, name_mod, fields_mod,',
                        'modifiedby_id, modifiedat',
                    ') SELECT sch.id,',
                        '(SELECT id FROM Department_log WHERE base_id=dep.base_id AND examyear_id=dep.examyear_id ORDER BY id DESC LIMIT 1) AS dep_log_id,',
                        '(SELECT id FROM Level_log WHERE base_id=lvl.base_id AND examyear_id=dep.examyear_id ORDER BY id DESC LIMIT 1) AS level_log_id,',
                        '(SELECT id FROM Sector_log WHERE base_id=sct.base_id AND examyear_id=dep.examyear_id ORDER BY id DESC LIMIT 1) AS sector_log_id,',
                        'sch.name, sch.fields,',
                        '%(mode)s as mode, False AS department_mod, False AS level_mod, False AS sector_mod, False AS name_mod, False AS fields_mod,',
                        'sch.modifiedby_id, sch.modifiedat',
                    'FROM [Level] AS lvl INNER JOIN (',
                            'Sector AS sct INNER JOIN (',
                                'Department AS dep INNER JOIN Scheme AS sch',
                                'ON dep.id = sch.department_id)',
                            'ON sct.id = sch.sector_id)',
                        'ON lvl.id = sch.level_id',
                    'WHERE dep.examyear_id=%(new_ey_pk)s;']
        sql = ' '.join(sql_list)
        sql_log_keys = {'new_ey_pk': new_examyear_pk,
                    'mode':   c.MODE_C_CREATED}
        cursor.execute(sql, sql_log_keys)
        connection.commit()


def get_previous_examyear_instance(new_examyear_instance):
    # get previous examyear of this country from new_examyear, check if it exists # PR2019-02-23 PR2020-10-06
    prev_examyear_instance = None
    msg_err = None
    if new_examyear_instance is not None:
        new_examyear_int = new_examyear_instance.examyear
        prev_examyear_int = int(new_examyear_int) - 1
        prev_examyear_instance = sch_mod.Examyear.objects.get_or_none(
            country=new_examyear_instance.country,
            code=prev_examyear_int)
        if prev_examyear_instance is None:
            prev_examyear_count = sch_mod.Examyear.objects.filter(
                country=new_examyear_instance.country,
                code=prev_examyear_int).count()
            if prev_examyear_count:
                msg_err = _("Multiple instances of previous exam year %(ey_yr) were found. Please delete duplicates first.")
            else:
                msg_err = _("Previous exam year %(ey_yr) is not found. Please create the previous exam year first.")
    return prev_examyear_instance, msg_err


def get_department(old_examyear, new_examyear):
    # get previous examyear of this country from new_examyear, check if it exists # PR2019-02-23
    prev_examyear = None
    if new_examyear is not None:
        prev_examyear_int = int(new_examyear.code) - 1
        prev_examyear = sch_mod.Department.objects.filter(country=new_examyear.country, examyear=prev_examyear_int).first()
    return prev_examyear


# ===============================
def get_schoolsetting(request_item_setting, sel_examyear, sel_schoolbase, sel_depbase):  # PR2020-04-17 PR2020-12-28  PR2021-01-12
    logging_on = True
    if logging_on:
        logger.debug(' ---------------- get_schoolsetting ---------------- ')
        logger.debug('request_item_setting: ' + str(request_item_setting) + ' ' + str(type(request_item_setting)))
        logger.debug('sel_examyear: ' + str(sel_examyear))
        logger.debug('sel_schoolbase: ' + str(sel_schoolbase))
        logger.debug('sel_depbase: ' + str(sel_depbase) + ' ' + str(type(sel_depbase)))
    # only called by DatalistDownloadView
    # setting_keys are: {setting_key: "import_student"}, {setting_key: "import_subject"},, {setting_key: "import_grade"}
    setting_key = request_item_setting.get('setting_key')

    sel_examyear_pk = sel_examyear.pk if sel_examyear else None
    sel_schoolbase_pk = sel_schoolbase.pk if sel_schoolbase else None
    sel_depbase_pk = sel_depbase.pk if sel_depbase else None
    schoolsetting_dict = {'sel_examyear_pk': sel_examyear_pk,
                          'sel_schoolbase_pk': sel_schoolbase_pk,
                          'sel_depbase_pk': sel_depbase_pk}

    if setting_key:
        if setting_key in (c.KEY_IMPORT_STUDENT, c.KEY_IMPORT_STUDENTSUBJECT, c.KEY_IMPORT_SUBJECT, c.KEY_IMPORT_GRADE):
            schoolsetting_dict[setting_key] = get_stored_coldefs_dict(setting_key, sel_examyear, sel_schoolbase, sel_depbase, logging_on)
        else:
            schoolsetting_dict[setting_key] = sel_schoolbase.get_setting(setting_key)

    if logging_on:
        logger.debug('setting_key: ' + str(setting_key) + ' ' + str(type(setting_key)))
        logger.debug('schoolsetting_dict: ' + str(schoolsetting_dict))
    return schoolsetting_dict


# ===============================
def get_stored_coldefs_dict(setting_key, sel_examyear, sel_schoolbase, sel_depbase, logging_on):

    if logging_on:
        logger.debug(' ---------------- get_stored_coldefs_dict ---------------- ')
        logger.debug('setting_key: ' + str(setting_key))
        logger.debug('sel_depbase: ' + str(sel_depbase))

    # stored_settings_dict: {'worksheetname': 'Compleetlijst', 'has_header': True,
    # 'coldef': {'idnumber': 'ID', 'classname': 'KLAS', 'department': 'Vakantiedagen', 'level': 'Payrollcode', 'sector': 'Profiel'},
    # 'department': {'21': 2},
    # 'level': {'W6': 1, 'W3': 2, 'W2': 3},
    # 'sector': {'EM': 3, 'CM': 4, 'NT': 7}}

# - first get info from sel_school
    # sel_schoolbase can be different from request.user.schoolbase
    # This can be the case when role insp, admin or system has selected different school
    # only import students from the selected department
    sel_school = sch_mod.School.objects.get_or_none(base=sel_schoolbase, examyear=sel_examyear)

# - is_level_req / is_sector_req is True when _req is True in the selected department of sel_school
    is_level_req = False
    is_sector_req = False
    has_profiel = False
    sel_department = None
    if sel_school:
        # doublecheck if sel_depbase is in sel_school.depbases
        depbases_str_list = sel_school.depbases.split(';') if sel_school.depbases else None
        sel_school_depbases_list = list(map(int, depbases_str_list)) if depbases_str_list else None

        if logging_on:
            logger.debug('sel_school.depbases: ' + str(sel_school.depbases))
            logger.debug('depbases_str_list: ' + str(depbases_str_list))
            logger.debug('sel_school_depbases_list: ' + str(sel_school_depbases_list))
        if sel_depbase and sel_school_depbases_list and sel_depbase.pk in sel_school_depbases_list:
            sel_department = sch_mod.Department.objects.get_or_none(base=sel_depbase, examyear=sel_examyear)
            if sel_department:
                is_level_req = sel_department.level_req
                is_sector_req = sel_department.sector_req
                has_profiel = sel_department.has_profiel

# - get Schoolsetting from sel_schoolbase, not from request.user.schoolbase
    # (sel_schoolbase may be different from user.schoolbase when role is comm, insp, adm, system)
    stored_settings_dict = sel_schoolbase.get_schoolsetting_dict(setting_key)
    if logging_on:
        logger.debug('stored_settings_dict: ' + str(stored_settings_dict))
        logger.debug('setting_key: ' + str(setting_key))
        logger.debug('sel_school: ' + str(sel_school))
        logger.debug('sel_department: ' + str(sel_department))

    noheader = False
    worksheetname = ''
    coldef_list = []
    stored_coldef = {}

    if setting_key and sel_school and sel_department:
        if stored_settings_dict:
            noheader = stored_settings_dict.get('noheader', False)
            worksheetname = stored_settings_dict.get('worksheetname')
            stored_coldef = stored_settings_dict.get('coldef')

        default_coldef_list = c.KEY_COLDEF.get(setting_key)

        if logging_on:
            logger.debug('stored_coldef: ' + str(stored_coldef))
            logger.debug('default_coldef_list: ' + str(default_coldef_list))

        if default_coldef_list:
            for dict in default_coldef_list:
                awpColdef = dict.get('awpColdef')

# - only add level or sector when sel_department has is_level_req=True / is_sector_req=True
                # sector and profiel are 2 different items. Choose the one that is applicable
                if awpColdef == 'level':
                    add_to_list = is_level_req
                elif awpColdef == 'sector':
                    add_to_list = is_sector_req and not has_profiel
                elif awpColdef == 'profiel':
                    add_to_list = is_sector_req and has_profiel
                else:
                    add_to_list = True

# - loop through stored_coldef, add excColdef to corresponding item in coldef_list
                if add_to_list:
                    # stored_coldef: {'examnumber': 'exnr', 'classname': 'KLAS', 'level': 'Payrollcode', 'sector': 'Profiel'}
                    if stored_coldef:
                        stored_excColdef = None
                        for stored_awpColdef in stored_coldef:
                            if stored_awpColdef == awpColdef:
                                stored_excColdef = stored_coldef.get(stored_awpColdef)
                                break
                        if stored_excColdef:
                            dict['excColdef'] = stored_excColdef
                    coldef_list.append(dict)

    setting_dict = {
        'worksheetname': worksheetname,
        'noheader': noheader,
        'coldefs': coldef_list
        }

# create list of required levels and sectors with excColdef when linked
    # 'profiel' also stored in table 'sector', but is separate item in import
    for tblName in ('department', 'level', 'sector', 'profiel', 'subject', 'subjecttype'):
# - only add list of level / sector when _req is True in sel_department
        is_req = False
        if tblName == 'level':
            is_req = is_level_req
        elif tblName in ('sector', 'profiel'):
            is_req = is_sector_req
        else:
            #TODO set isreq for dep, subj, subjtype
            is_req = True

        if is_req:
            tbl_list = []
            instances = None

# - reverse the  stored_dict : convert {'ned': 4} to {4: 'ned'} to speed up search
            reversed_dict = {}
            stored_dict = stored_settings_dict.get(tblName) if stored_settings_dict else None
            if logging_on:
                logger.debug('tblName: ' + str(tblName))
                logger.debug('stored_dict: ' + str(stored_dict))

            if stored_dict:
                for excValue, awpBasePk in stored_dict.items():
                    reversed_dict[awpBasePk] = excValue

# - get all instances of tblNmae of sel_examyear
            if tblName == 'department':
                instances = sch_mod.Department.objects.filter(examyear=sel_examyear)
            elif tblName == 'level':
                instances = subj_mod.Level.objects.filter(examyear=sel_examyear)
            elif tblName in ('sector', 'profiel'):
                instances = subj_mod.Sector.objects.filter(examyear=sel_examyear)
            elif tblName == 'subject':
                instances = subj_mod.Subject.objects.filter(examyear=sel_examyear)
            elif tblName == 'subjecttype':
                instances = subj_mod.Subjecttype.objects.filter(examyear=sel_examyear)

# - loop through instances of this examyear
            for instance in instances:
                if logging_on:
                    logger.debug('instances: ' + str(instances) + ' ' + str(type(instances)))
    # - check if one of the depbases of the instance is in the list of depbases of the school
                add_to_list = False
                if sel_department:
                    if tblName == 'department':
            # if department: check if depbasePk is in school_depbasePk_list
                        if instance == sel_department:
                            add_to_list = True
                    elif instance.depbases:
            # in other tables: only add if sel_depbase.pk is in depbases
                        depbases_str_list = instance.depbases.split(';') if instance.depbases else None
                        depbases_list = list(map(int, depbases_str_list)) if depbases_str_list else None

                        if sel_depbase.pk in depbases_list:
                            if tblName == 'sector':
                                add_to_list = not has_profiel
                            elif tblName == 'profiel':
                                add_to_list = has_profiel
                            else:
                                add_to_list = True

                if add_to_list:
                    instance_basePk = instance.base.pk
                    instance_value = None
                    if tblName in ('department', 'subject'):
                        instance_value = instance.base.code if instance.base.code else None
                    elif tblName in ('level', 'sector', 'profiel', 'subjecttype'):
                        instance_value = instance.abbrev if instance.abbrev else None

                    dict = {'awpBasePk': instance_basePk, 'awpValue': instance_value}
                    if reversed_dict:
                        #  reversed_dict =  {3: 'EM', 4: 'CM', 7: 'NT'}
                        # - add excValue when this subject is linked
                        if reversed_dict and instance_basePk in reversed_dict:
                            dict['excValue'] = reversed_dict[instance_basePk]
                    tbl_list.append(dict)
            if tbl_list:
                setting_dict[tblName] = tbl_list

    if logging_on:
        logger.debug('setting_dict: ' + str(setting_dict))
        logger.debug(' ---------------- end of get_stored_coldef_dict ---------------- ')
    return setting_dict