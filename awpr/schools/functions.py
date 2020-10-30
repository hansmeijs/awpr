from django.db import connection
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from datetime import datetime

from awpr import constants as c

from schools import models as sch_mod

import json
import logging
logger = logging.getLogger(__name__)

def copy_deps_from_prev_examyear(request_user, prev_examyear_pk, new_examyear_pk):
    # copy departments from previous examyear if it exists # PR2019-02-23

    if prev_examyear_pk and new_examyear_pk:
        modifiedby_id = request_user.id
        modifiedat = timezone.now()

        cursor = connection.cursor()

# - copy departments from previous examyear
        field_list = 'name, abbrev, sequence, level_req, sector_req, level_caption, sector_caption,'
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
                    'name_mod, abbrev_mod, sequence_mod,',
                    'level_req_mod, sector_req_mod, level_caption_mod, sector_caption_mod,',
                    'mode, modifiedby_id, modifiedat)',
                    'SELECT id, base_id, %(new_ey_log_pk)s AS examyear_log_id,',
                    field_list,
                    'False AS name_mod, False AS abbrev_mod, False AS sequence_mod,',
                    'False AS level_req_mod, False AS sector_req_mod, False AS level_caption_mod, False AS sector_caption_mod,',
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

def get_todays_examyear():
    # get this year in Jan thru July, get next year in Aug thru Dec PR2020-09-29
    today = datetime.today()
    return today.year if today.month < 8 else today.year + 1


def get_previous_examyear(new_examyear_instance):
    # get previous examyear of this country from new_examyear, check if it exists # PR2019-02-23 PR2020-10-06
    prev_examyear_instance = None
    msg_err = None
    if new_examyear_instance is not None:
        new_examyear_int = new_examyear_instance.examyear
        prev_examyear_int = int(new_examyear_int) - 1
        prev_examyear_instance = sch_mod.Examyear.objects.get_or_none(
            country=new_examyear_instance.country,
            examyear=prev_examyear_int)
        if prev_examyear_instance is None:
            prev_examyear_count = sch_mod.Examyear.objects.filter(
                country=new_examyear_instance.country,
                examyear=prev_examyear_int).count()
            if prev_examyear_count:
                msg_err = _("Multiple instances of previous exam year %(ey_yr) were found. Please delete duplicates first.")
            else:
                msg_err = _("Previous exam year %(ey_yr) is not found. Please create the previous exam year first.")
    return prev_examyear_instance, msg_err

def get_department(old_examyear, new_examyear):
    # get previous examyear of this country from new_examyear, check if it exists # PR2019-02-23
    prev_examyear = None
    if new_examyear is not None:
        prev_examyear_int = int(new_examyear.examyear) - 1
        prev_examyear = sch_mod.Department.objects.filter(country=new_examyear.country, examyear=prev_examyear_int).first()
    return prev_examyear


# ===============================
def get_schoolsetting(table_dict, user_lang, request):  # PR2020-04-17
    logger.debug(' ---------------- get_schoolsetting ---------------- ')
    # only called by DatalistDownloadView
    # schoolsetting: {coldefs: "order"}
    schoolsetting_dict = {}
    if 'coldefs' in table_dict:
        tblName = table_dict.get('coldefs')
        logger.debug('tblName: ' + str(tblName) + ' ' + str(type(tblName)))
        coldefs_dict = get_stored_coldefs_dict(tblName, user_lang, request)
        if coldefs_dict:
            schoolsetting_dict['coldefs'] = coldefs_dict

    return schoolsetting_dict


# ===============================
def get_stored_coldefs_dict(tblName, user_lang, request):
    #logger.debug(' ---------------- get_stored_coldefs_dict ---------------- ')
    # coldef_list = [ {'awpKey': 'custcode', 'caption': 'Customer - Short name'}, ... ]
    # structure of stored_coldefs: {'awpKey': 'excKey', ... }
    # stored_coldefs: {'custcode': 'Order', 'orderidentifier': 'Customer', ...}

    has_header = True
    worksheetname = ''
    code_calc = ''
    stored_coldefs = {}
    settings_key =None
    if (tblName == 'subject'):
        settings_key = c.KEY_SUBJECT_MAPPED_COLDEFS

    stored_json = sch_mod.Schoolsetting.get_jsonsetting(settings_key, request.user.schoolbase)
    if stored_json:
        stored_setting = json.loads(stored_json)
        #logger.debug('stored_setting: ' + str(stored_setting))
        if stored_setting:
            has_header = stored_setting.get('has_header', True)
            worksheetname = stored_setting.get('worksheetname', '')
            if 'coldefs' in stored_setting:
                stored_coldefs = stored_setting['coldefs']
                #logger.debug('stored_coldefs: ' + str(stored_coldefs))

    coldef_list = []

    default_coldef_list = None
    if (tblName == 'subject'):
        default_coldef_list = c.COLDEF_SUBJECT

    for default_coldef_dict in default_coldef_list:
        # default_coldef_dict = {'awpKey': 'custcode', 'caption': _('Customer - Short name')
        #logger.debug('default_coldef_dict: ' + str(default_coldef_dict))
        default_awpKey = default_coldef_dict.get('awpKey')
        default_caption = default_coldef_dict.get('caption')
        dict = {'awpKey': default_awpKey, 'caption': default_caption}

# - loop through stored_coldefs, add excKey to corresponding item in coldef_list
        # stored_coldefs: {'orderdatefirst': 'datestart', 'orderdatelast': 'dateend'}
        if stored_coldefs:
            stored_excKey = None
            for stored_awpKey in stored_coldefs:
                if stored_awpKey == default_awpKey:
                    stored_excKey = stored_coldefs.get(stored_awpKey)
                    break
            if stored_excKey:
                dict['excKey'] = stored_excKey
        coldef_list.append(dict)
        #logger.debug('coldef_list: ' + str(coldef_list))

    coldefs_dict = {
        'worksheetname': worksheetname,
        'has_header': has_header,
        'coldefs': coldef_list
        }
    #logger.debug('coldefs_dict: ' + str(coldefs_dict))
    #logger.debug(' ---------------- end of get_stored_coldefs_dict ---------------- ')
    return coldefs_dict