from django.db import connection
from django.utils import timezone

from awpr import constants as c
from schools.models import Examyear, Examyear_log, Department, Department_log, Schoolbase, School, School_log

import logging
logger = logging.getLogger(__name__)

def copy_deps_from_prev_examyear(request_user, new_examyear):
    # copy departments from previous examyear if it exists # PR2019-02-23

    if new_examyear is not None:
        prev_examyear = get_previous_examyear(new_examyear)

        if prev_examyear is not None:
            modified_by_id = request_user.id
            modified_at = timezone.now()

            cursor = connection.cursor()

# - copy departments from previous examyear
            field_list = 'name, abbrev, sequence, level_req, sector_req, level_caption, sector_caption,'
            sql_list =['INSERT INTO schools_department',
                       '(base_id, examyear_id,',
                       field_list,
                       'modified_by_id, modified_at)',
                       'SELECT base_id, %s AS new_examyear_id,',
                       field_list,
                       '%s AS modified_by_id, %s AS modified_at',
                       'FROM schools_department WHERE examyear_id = %s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                [new_examyear.id,
                 modified_by_id,
                 modified_at,
                 prev_examyear.id])
            connection.commit()

# - get latest Examyear_log row that corresponds with new_examyear.
            # The Examyear_log row is created at self.new_examyear.save in Schools.Model
            new_examyear_log = Examyear_log.objects.filter(examyear_id=new_examyear.id).order_by('-id').first()
            new_examyear_log_id = new_examyear_log.id

# - copy new departments to department_log
            # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
            sql_list =['INSERT INTO schools_department_log',
                        '(department_id, base_id, examyear_log_id,',
                        field_list,
                        'name_mod, abbrev_mod, sequence_mod,',
                        'level_req_mod, sector_req_mod, level_caption_mod, sector_caption_mod,',
                        'mode, modified_by_id, modified_at)',
                        'SELECT id, base_id, %s AS examyear_log_id,',
                        field_list,
                        'False AS name_mod, False AS abbrev_mod, False AS sequence_mod,',
                        'False AS level_req_mod, False AS sector_req_mod, False AS level_caption_mod, False AS sector_caption_mod,',
                        '%s AS mode, %s AS modified_by_id, %s AS modified_at',
                        'FROM schools_department WHERE examyear_id = %s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                [new_examyear_log_id,
                 c.MODE_C_CREATED,
                 modified_by_id,
                 modified_at,
                 new_examyear.id])
            connection.commit()


def copy_levels_from_prev_examyear(request_user, new_examyear):
    # copy levels from previous examyear if it exists # PR2019-02-23

    if new_examyear is not None:
        prev_examyear = get_previous_examyear(new_examyear)

        if prev_examyear is not None:
            modified_by_id = request_user.id
            modified_at = timezone.now()

            cursor = connection.cursor()

# - copy levels from previous examyear
            field_list = 'name, abbrev, sequence, depbase_list,'
            sql_list = ['INSERT INTO subjects_level',
                        '(base_id, examyear_id,',
                        field_list,
                        'modified_by_id, modified_at)',
                        'SELECT base_id, %s AS new_examyear_id,',
                        field_list,
                        '%s AS modified_by_id, %s AS modified_at',
                        'FROM subjects_level WHERE examyear_id = %s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                           [new_examyear.id,
                            modified_by_id,
                            modified_at,
                            prev_examyear.id])
            connection.commit()

            # - get latest Examyear_log row that corresponds with new_examyear.
            # The Examyear_log row is created at self.new_examyear.save in Schools.Model
            new_examyear_log = Examyear_log.objects.filter(examyear_id=new_examyear.id).order_by(
                '-id').first()
            new_examyear_log_id = new_examyear_log.id

            # - copy new levels to level_log
            # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
            sql_list = ['INSERT INTO subjects_level_log',
                        '(level_id, base_id, examyear_log_id,',
                        field_list,
                        'name_mod, abbrev_mod, sequence_mod, depbase_list_mod,',
                        'mode, modified_by_id, modified_at)',
                        'SELECT id, base_id, %s AS examyear_log_id,',
                        field_list,
                        'False AS name_mod, False AS abbrev_mod, False AS sequence_mod, False AS depbase_list_mod,',
                        '%s AS mode, %s AS modified_by_id, %s AS modified_at',
                        'FROM subjects_level WHERE examyear_id = %s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                           [new_examyear_log_id,
                            c.MODE_C_CREATED,
                            modified_by_id,
                            modified_at,
                            new_examyear.id])
            connection.commit()


def copy_sectors_from_prev_examyear(request_user, new_examyear):
    # copy sectors from previous examyear if it exists # PR2019-02-23

    if new_examyear is not None:
        prev_examyear = get_previous_examyear(new_examyear)

        if prev_examyear is not None:
            modified_by_id = request_user.id
            modified_at = timezone.now()

            cursor = connection.cursor()

            # - copy sectors from previous examyear
            field_list = 'name, abbrev, sequence, depbase_list,'
            sql_list = ['INSERT INTO subjects_sector',
                        '(base_id, examyear_id,',
                        field_list,
                        'modified_by_id, modified_at)',
                        'SELECT base_id, %s AS new_examyear_id,',
                        field_list,
                        '%s AS modified_by_id, %s AS modified_at',
                        'FROM subjects_sector WHERE examyear_id = %s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                           [new_examyear.id,
                            modified_by_id,
                            modified_at,
                            prev_examyear.id])
            connection.commit()

            # - get latest Examyear_log row that corresponds with new_examyear.
            # The Examyear_log row is created at self.new_examyear.save in Schools.Model
            new_examyear_log = Examyear_log.objects.filter(examyear_id=new_examyear.id).order_by(
                '-id').first()
            new_examyear_log_id = new_examyear_log.id

            # - copy new sectors to sector_log
            # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
            sql_list = ['INSERT INTO subjects_sector_log',
                        '(sector_id, base_id, examyear_log_id,',
                        field_list,
                        'name_mod, abbrev_mod, sequence_mod, depbase_list_mod,',
                        'mode, modified_by_id, modified_at)',
                        'SELECT id, base_id, %s AS examyear_log_id,',
                        field_list,
                        'False AS name_mod, False AS abbrev_mod, False AS sequence_mod, False AS depbase_list_mod,',
                        '%s AS mode, %s AS modified_by_id, %s AS modified_at',
                        'FROM subjects_sector WHERE examyear_id = %s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                           [new_examyear_log_id,
                            c.MODE_C_CREATED,
                            modified_by_id,
                            modified_at,
                            new_examyear.id])
            connection.commit()


def copy_subjecttypes_from_prev_examyear(request_user, new_examyear):
    # copy subjecttypes from previous examyear if it exists # PR2019-02-23

    if new_examyear is not None:
        prev_examyear = get_previous_examyear(new_examyear)

        if prev_examyear is not None:
            modified_by_id = request_user.id
            modified_at = timezone.now()

            cursor = connection.cursor()

            # - copy subjecttypes from previous examyear
            field_list = 'name, abbrev, code, sequence, depbase_list, has_prac, has_pws, one_allowed,'

            sql_list = ['INSERT INTO subjects_subjecttype',
                        '(base_id, examyear_id,',
                        field_list,
                        'modified_by_id, modified_at)',
                        'SELECT base_id, %s AS new_examyear_id,',
                        field_list,
                        '%s AS modified_by_id, %s AS modified_at',
                        'FROM subjects_subjecttype WHERE examyear_id = %s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                           [new_examyear.id,
                            modified_by_id,
                            modified_at,
                            prev_examyear.id])
            connection.commit()

            # - get latest Examyear_log row that corresponds with new_examyear.
            # The Examyear_log row is created at self.new_examyear.save in Schools.Model
            new_examyear_log = Examyear_log.objects.filter(examyear_id=new_examyear.id).order_by(
                '-id').first()
            new_examyear_log_id = new_examyear_log.id

            # - copy new subjecttypes to subjecttype_log
            # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
            sql_list = ['INSERT INTO subjects_subjecttype_log',
                        '(subjecttype_id, base_id, examyear_log_id,',
                        field_list,
                        'name_mod, abbrev_mod, code_mod, sequence_mod, depbase_list_mod,',
                        'has_prac_mod, has_pws_mod, one_allowed_mod,',
                        'mode, modified_by_id, modified_at)',
                        'SELECT id, base_id, %s AS examyear_log_id,',
                        field_list,
                        'False AS name_mod, False AS abbrev_mod, False AS code_mod, False AS sequence_mod, False AS depbase_list_mod,',
                        'False AS has_prac_mod, False AS has_pws_mod, False AS one_allowed_mod,',
                        '%s AS mode, %s AS modified_by_id, %s AS modified_at',
                        'FROM subjects_subjecttype WHERE examyear_id = %s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                           [new_examyear_log_id,
                            c.MODE_C_CREATED,
                            modified_by_id,
                            modified_at,
                            new_examyear.id])
            connection.commit()


def copy_subjects_from_prev_examyear(request_user, new_examyear):
    # copy subjects from previous examyear if it exists # PR2019-02-23

    if new_examyear is not None:
        prev_examyear = get_previous_examyear(new_examyear)

        if prev_examyear is not None:
            modified_by_id = request_user.id
            modified_at = timezone.now()

            cursor = connection.cursor()

            # - copy subjects from previous examyear to new_examyear
            field_list = 'name, abbrev, sequence, depbase_list,'
            sql_list = ['INSERT INTO subjects_subject (',
                            'base_id, examyear_id,',
                            field_list,
                            'modified_by_id, modified_at',
                        ') SELECT base_id, %s AS examyear_id,',
                            field_list,
                            '%s AS modified_by_id, %s AS modified_at',
                        'FROM subjects_subject WHERE examyear_id = %s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                           [new_examyear.id,
                            modified_by_id,
                            modified_at,
                            prev_examyear.id])
            connection.commit()

            # - get latest Examyear_log row that corresponds with new_examyear.
            # The Examyear_log row is created at self.new_examyear.save in Schools.Model
            new_examyear_log = Examyear_log.objects.filter(examyear_id=new_examyear.id).order_by(
                '-id').first()
            new_examyear_log_id = new_examyear_log.id

            # - copy new subjects to subject_log
            # PR2019-02-23 debug: add False AS name_mod etc in sql, they don't get default value at commit
            sql_list = ['INSERT INTO subjects_subject_log (',
                            'subject_id, base_id, examyear_log_id,',
                            field_list,
                            'name_mod, abbrev_mod, sequence_mod, depbase_list_mod,',
                            'mode, modified_by_id, modified_at',
                        ') SELECT id, base_id,'
                            '%s AS examyear_log_id,',
                            field_list,
                            'False AS name_mod, False AS abbrev_mod, False AS sequence_mod, False AS depbase_list_mod,',
                            '%s AS mode, %s AS modified_by_id, %s AS modified_at',
                        'FROM subjects_subject WHERE examyear_id = %s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                           [new_examyear_log_id,
                            c.MODE_C_CREATED,
                            modified_by_id,
                            modified_at,
                            new_examyear.id])
            connection.commit()


def copy_schemes_from_prev_examyear(request_user, new_examyear):
    # copy schemes from previous examyear if it exists # PR2019-02-23

    if new_examyear is not None:
        prev_examyear = get_previous_examyear(new_examyear)

        if prev_examyear is not None:
            modified_by_id = request_user.id
            modified_at = timezone.now()

            cursor = connection.cursor()

# - copy schemes from previous examyear
            # get department_id of new_examyear, using subquery with filter base_id and examyear_id = new_examyear.id
            # als with level_id andsector_id
            sql_list = ['INSERT INTO Scheme',
                        '(department_id, level_id, sector_id, name, fields, modified_by_id, modified_at)',
                        'SELECT',
                        '(SELECT id FROM [Department] WHERE base_id = dep.base_id AND examyear_id = %s) AS new_dep_id,',
                        '(SELECT id FROM [Level] WHERE base_id = lvl.base_id AND examyear_id = %s) AS new_lvl_id,',
                        '(SELECT id FROM [Sector] WHERE base_id = sct.base_id AND examyear_id = %s) AS new_sct_id,',
                        'name, fields',
                        '%s AS modified_by_id, %s AS modified_at',
                        'FROM Level AS lvl',
                            'INNER JOIN (Sector AS sct',
                                'INNER JOIN (Department AS dep',
                                    'INNER JOIN Scheme',
                                    'ON dep.id = Scheme.department_id)',
                                'ON sct.id = Scheme.sector_id)',
                            'ON lvl.id = Scheme.level_id',
                        'WHERE dep.examyear_id=%s;']
            sql = ' '.join(sql_list)
            cursor.execute(sql,
                           [new_examyear.id,
                            new_examyear.id,
                            new_examyear.id,
                            modified_by_id,
                            modified_at,
                            prev_examyear.id])
            connection.commit()

            # Fields from  subjects_scheme_log are:
                # id, scheme_id, dep_log_id, level_log_id, sector_log_id, '
                # name, fields, dep_mod, level_mod, sector_mod, name_mod, fields_mod'
                # 'mode, modified_by_id, modified_at'

            # PR2019-02-24
            sql_list = ['INSERT INTO Scheme_log (',
                            'scheme_id, department_log_id, level_log_id, sector_log_id,',
                            'name, fields, mode, department_mod, level_mod, sector_mod, name_mod, fields_mod,',
                            'modified_by_id, modified_at',
                        ') SELECT sch.id,',
                            '(SELECT id FROM Department_log WHERE base_id=dep.base_id AND examyear_id=dep.examyear_id ORDER BY id DESC LIMIT 1) AS dep_log_id,',
                            '(SELECT id FROM Level_log WHERE base_id=lvl.base_id AND examyear_id=dep.examyear_id ORDER BY id DESC LIMIT 1) AS level_log_id,',
                            '(SELECT id FROM Sector_log WHERE base_id=sct.base_id AND examyear_id=dep.examyear_id ORDER BY id DESC LIMIT 1) AS sector_log_id,',
                            'sch.name, sch.fields,',
                            '%s as mode, False AS department_mod, False AS level_mod, False AS sector_mod, False AS name_mod, False AS fields_mod,',
                            'sch.modified_by_id, sch.modified_at',
                        'FROM [Level] AS lvl INNER JOIN (',
                                'Sector AS sct INNER JOIN (',
                                    'Department AS dep INNER JOIN Scheme AS sch',
                                    'ON dep.id = sch.department_id)',
                                'ON sct.id = sch.sector_id)',
                            'ON lvl.id = sch.level_id',
                        'WHERE dep.examyear_id=%s;']
            sql = ' '.join(sql_list)
            cursor = connection.cursor()
            cursor.execute(sql, [c.MODE_L_COPIED,
                                 new_examyear.id])
            connection.commit()



def get_previous_examyear(new_examyear):
    # get previous examyear of this country from new_examyear, check if it exists # PR2019-02-23
    prev_examyear = None
    if new_examyear is not None:
        prev_examyear_int = int(new_examyear.examyear) - 1
        prev_examyear = Examyear.objects.filter(country=new_examyear.country, examyear=prev_examyear_int).first()
    return prev_examyear

def get_department(old_examyear, new_examyear):
    # get previous examyear of this country from new_examyear, check if it exists # PR2019-02-23
    prev_examyear = None
    if new_examyear is not None:
        prev_examyear_int = int(new_examyear.examyear) - 1
        prev_examyear = Department.objects.filter(country=new_examyear.country, examyear=prev_examyear_int).first()
    return prev_examyear
