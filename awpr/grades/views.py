# PR2020-12-03
from django.contrib.auth.decorators import login_required

from django.db.models.functions import Lower
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView, View

from awpr import functions as f
from awpr import constants as c
from students import validations as v
from awpr import menus as awpr_menu
from awpr import functions as af

from accounts import models as acc_mod
from schools import models as sch_mod
from students import models as stud_mod
from students import views as stud_view
from subjects import models as subj_mod

import json # PR2018-12-03
# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

# ========  Student  =====================================

@method_decorator([login_required], name='dispatch')
class GradeListView(View):  # PR2020-12-03

    def get(self, request):
        #logger.debug('  =====  GradeListView ===== ')
        # logger.debug('request: ' + str(request) + ' Type: ' + str(type(request)))

        # <PERMIT>
        # - school-user can only view his own school
        # - insp-users can only view schools from his country
        # - system-users can only view school from request_user,country
        schools = None  # User.objects.filter(False) gives error: 'bool' object is not iterable
        menu_items = []
        if request.user is not None and request.user.examyear is not None:
            # logger.debug('request.user: ' + str(request.user) + ' Type: ' + str(type(request.user)))
            if request.user.examyear:
                if request.user.is_role_insp_or_admin_or_system:
                    # examyear has field country, therefore filter country is not necessary
                    schools = sch_mod.School.objects.filter(examyear=request.user.examyear)
                elif request.user.schoolbase is not None:
                    schools = sch_mod.School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear)

        # -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

        # set headerbar parameters PR2018-08-06
        page = 'grades'
        params = awpr_menu.get_headerbar_param(
            request=request,
            page=page
        )

        # save this page in Usersetting, so at next login this page will open. Uses in LoggedIn
        acc_mod.Usersetting.set_jsonsetting('sel_page', {'page': page}, request.user)

        return render(request, 'grades.html', params)


#/////////////////////////////////////////////////////////////////
"""
def create_grade_rows(setting_dict, append_dict, student_pk):
    # --- create rows of all students of this examyear / school PR2020-10-27
    # logger.debug(' =============== create_grade_rows ============= ')

    sel_examyear_pk = setting_dict.get('sel_examyear_pk')
    sel_schoolbase_pk = setting_dict.get('sel_schoolbase_pk')
    sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk}

    sql_list = ["SELECT st.id, st.base_id, st.school_id AS s_id,",
        "st.department_id AS dep_id, st.level_id AS lvl_id, st.sector_id AS sct_id, st.scheme_id,",
        "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",
        "CONCAT('student_', st.id::TEXT) AS mapid,",
        "st.lastname, st.firstname, st.prefix, st.gender,",
        "st.idnumber, st.birthdate, st.birthcountry, st.birthcity,",
        "st.classname, st.examnumber, st.regnumber, st.diplomanumber, st.gradelistnumber,",
        "st.iseveningstudent, st.locked, st.has_reex, st.bis_exam, st.withdrawn,",
        "st.modifiedby_id, st.modifiedat,",
        "SUBSTRING(au.username, 7) AS modby_username",
        "FROM students_student AS st",
        "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
        "LEFT JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
        "LEFT JOIN accounts_user AS au ON (au.id = st.modifiedby_id)",
        "WHERE sch.base_id = %(sb_id)s::INT AND sch.examyear_id = %(ey_id)s::INT "]

    if student_pk:
        # when student_pk has value: skip other filters
        sql_list.append('AND st.id = %(st_id)s::INT')
        sql_keys['st_id'] = student_pk
    else:
        sql_list.append('ORDER BY LOWER(st.lastname), LOWER(st.firstname)')
    sql = ' '.join(sql_list)

    newcursor = connection.cursor()
    newcursor.execute(sql, sql_keys)
    student_rows = sch_mod.dictfetchall(newcursor)

# - add lastname_firstname_initials to rows
    if student_rows:
        for row in student_rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = stud_view.lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

    # - add messages to student_row
    if student_pk and student_rows:
        # when student_pk has value there is only 1 row
        row = student_rows[0]
        if row:
            for key, value in append_dict.items():
                row[key] = value

    return student_rows

# --- end of create_grade_rows
"""



@method_decorator([login_required], name='dispatch')
class GradeUploadView(View):  # PR2020-12-16

    def post(self, request):
        logger.debug(' ============= GradeUploadView ============= ')
        # function creates, deletes and updates studentsubject records of current student PR2020-11-21
        update_wrap = {}
        has_permit = False
        requsr_school = None

        #<PERMIT>
        # current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # in that case student data cannot be changed
        # check if student belongs to request.user.schoolbase
        if request.user and request.user.country and request.user.schoolbase:
            if request.user.role in (c.ROLE_04_TEACHER, c.ROLE_08_SCHOOL, c.ROLE_64_SYSTEM):
                permits_tuple = request.user.permits_tuple
                if c.PERMIT_02_EDIT in permits_tuple or c.PERMIT_64_SYSTEM in permits_tuple:
                    has_permit = True
        if has_permit:

        # Validations: PR2020-11-21
        # - changes can only be made when student_school equals requsr_school
        #   (insp, admin and system can view records of other schools, but cannot change them)
        # - changes can only be made when: student notlocked, school.activated and not locked, examyear.published and not locked
        # - TODO check for double subjects, double subjects are ot allowed
        # - TODO when deleting: return warning when subject grades have values

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                logger.debug('upload_dict' + str(upload_dict))

    # - get sel_examyear, only if examyear is published and not locked
                s_ey_pk = upload_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                sel_examyear = sch_mod.Examyear.objects.get_or_none(
                    pk=s_ey_pk,
                    country=request.user.country,
                    published=True,
                    locked=False
                )
                # NIU sel_examyear_pk = sel_examyear.pk if sel_examyear else None

    # - get schoolbase, only if its is the same as requsr_schoolbase
                s_sb_pk = upload_dict.get(c.KEY_SEL_SCHOOLBASE_PK)
                # TODO skip if sel_schoolbase different from request.user.schoolbase - trun off for now, for testing
                checked_sb_pk = s_sb_pk if s_sb_pk == request.user.schoolbase.pk else None
                checked_sb_pk = s_sb_pk
                sel_schoolbase = sch_mod.Schoolbase.objects.get_or_none(pk=checked_sb_pk, country=request.user.country)
                # NIU sel_schoolbase_pk = sel_schoolbase.pk if sel_schoolbase else None

    # - get school only if school is not locked and school is activated
                sel_school = sch_mod.School.objects.get_or_none(
                    base=sel_schoolbase,
                    examyear=sel_examyear,
                    activated=True,
                    locked=False
                )

    # - get current student, only school is the same as the requsr_school, only if student is not locked
                student = None
                if sel_school:
                    student_pk = upload_dict.get('student_pk')
                    student = stud_mod.Student.objects.get_or_none(
                        id=student_pk,
                        school=sel_school,
                        locked=False
                    )
                logger.debug('student: ' + str(student))

                if student:
# - get current studentsubject, only school is the same as the requsr_school, only if student is not locked

                    mode = upload_dict.get('mode')
                    grade_pk = upload_dict.get('grade_pk')
                    studsubj_pk = upload_dict.get('studsubj_pk')
                    examperiod_pk = upload_dict.get('examperiod_pk')

                    append_dict = {}
                    error_dict = {}

                    studentsubject = stud_mod.Studentsubject.objects.get_or_none(
                        id=studsubj_pk,
                        student=student
                    )
                    logger.debug('studentsubject: ' + str(studentsubject))

# - get current grade - when mode is 'create': studsubj is None. It will be created at "elif mode == 'create'"
                    grade = stud_mod.Grade.objects.get_or_none(
                        id=grade_pk,
                        studentsubject =studentsubject,
                        examperiod=examperiod_pk
                    )
                    logger.debug('grade: ' + str(grade))

# +++ update existing studsubj - also when studsubj is created - studsubj is None when deleted
                    if grade and mode == 'update':
                        update_grade(grade, upload_dict, error_dict, request)

# - add update_dict to update_wrap
                    grade_rows = []
                    if grade:
                        # TODO check value of error_dict
                        if error_dict:
                            append_dict['error'] = error_dict

                        rows = create_grade_rows(
                            setting_dict=upload_dict,
                            append_dict=append_dict,
                            subject_pk=None,
                            student_pk=None,
                            grade_pk=grade.pk
                        )
                        if rows:
                            studsubj_row = rows[0]
                            if studsubj_row:
                                grade_rows.append(studsubj_row)
                    if grade_rows:
                        update_wrap['updated_grade_rows'] = grade_rows

        logger.debug('update_wrap: ' + str(update_wrap))
        # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=f.LazyEncoder))
# --- end of GradeUploadView



#######################################################
def update_grade(instance, upload_dict, msg_dict, request):
    # --- update existing grade PR2020-12-16
    # add new values to update_dict (don't reset update_dict, it has values)
    logger.debug(' ------- update_grade -------')
    logger.debug('upload_dict' + str(upload_dict))
    # upload_dict{'id': {'pk': 6, 'table': 'grade', 'student_pk': 5, 'studsubj_pk': 10, 'examperiod': 1,
    #                   'mode': 'update', 'mapid': 'grade_6'},
    #             'segrade': 'ww'}

    # FIELDS_GRADE =('studentsubject', 'examperiod', 'pescore', 'cescore',
    #                  'segrade', 'pegrade', 'cegrade', 'pecegrade', 'finalgrade',
    #                  'sepublished', 'pepublished', 'cepublished',
    #                  'modifiedby', 'modifiedat')

    save_changes = False
    for field, new_value in upload_dict.items():
        if field in ('pescore', 'cescore', 'segrade', 'pegrade', 'cegrade', 'pecegrade'):

# a. get saved_value
            saved_value = getattr(instance, field)

            logger.debug('field' + str(field))
            logger.debug('new_value' + str(new_value))
            logger.debug('saved_value' + str(saved_value))

# 2. save changes in field 'name', 'abbrev'

            if new_value != saved_value:
# validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                """
                msg_err = validate_code_name_identifier(
                    table='student',
                    field=field,
                    new_value=new_value, parent=parent,
                    is_absence=False,
                    update_dict={},
                    msg_dict={},
                    request=request,
                    this_pk=instance.pk)
                """
                msg_err = None
                if not msg_err:
                    # c. save field if changed and no_error
                    setattr(instance, field, new_value)
                    save_changes = True
                else:
                    msg_dict['err_' + field] = msg_err

# 3. save changes in fields 'namefirst', 'namelast'
        elif field in ('sepublished', 'pepublished', 'cepublished'):
            saved_value = getattr(instance, field)
            if new_value != saved_value:
                setattr(instance, field, new_value)
                save_changes = True

# --- end of for loop ---

# 5. save changes`
    if save_changes:
        instance.save(request=request)
        logger.debug('The changes have been saved' + str(instance))
        """
        try:
            instance.save(request=request)
            logger.debug('The changes have been saved' + str(instance))
        except:
            msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')
        """
# --- end of update_grade


def create_grade_rows(setting_dict, append_dict, subject_pk=None, student_pk=None, grade_pk=None):
    # --- create rows of all students of this examyear / school PR2020-12-14
    logger.debug(' =============== create_grade_rows ============= ')

    sel_examyear_pk = f.get_dict_value(setting_dict, ('sel_examyear_pk',))
    sel_schoolbase_pk = f.get_dict_value(setting_dict, ('sel_schoolbase_pk',))
    sel_depbase_pk = f.get_dict_value(setting_dict, ('sel_depbase_pk',))

    sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk, 'depbase_id': sel_depbase_pk}

    sql_list = ["SELECT grade.id,  studsubj.id AS studsubj_id, studsubj.schemeitem_id, studsubj.cluster_id,",
        "CONCAT('grade_', grade.id::TEXT) AS mapid, 'grade' AS table,",

        "stud.id AS student_id, stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
        "stud.iseveningstudent, ey.locked AS ey_locked, school.locked AS school_locked, stud.locked AS stud_locked,",
        "school.islexschool,",
        "ey.no_practexam, ey.no_centralexam, ey.combi_reex_allowed, ey.no_exemption_ce, ey.no_thirdperiod,",
        "grade.examperiod, grade.pescore, grade.cescore, grade.segrade, grade.pegrade, grade.cegrade,",
        "grade.pecegrade, grade.finalgrade,",
        "CASE WHEN grade.se_published_id IS NULL THEN FALSE ELSE TRUE END AS ispublished_se,",
        "CASE WHEN grade.pe_published_id IS NULL THEN FALSE ELSE TRUE END AS ispublished_pe,",
        "CASE WHEN grade.ce_published_id IS NULL THEN FALSE ELSE TRUE END AS ispublished_ce,",
        "norm.scalelength_ce, norm.scalelength_reex, norm.scalelength_pe,",
        "si.subject_id, si.subjecttype_id, si.gradetype,",
        "si.gradetype, si.weight_se, si.weight_ce, si.is_mandatory, si.is_combi, si.extra_count_allowed,",
        "si.extra_nocount_allowed, si.elective_combi_allowed, si.has_practexam,",
        "subj.name AS subj_name, subjbase.code AS subj_code",

        "FROM students_grade AS grade",
        "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grade.studentsubject_id)",

        "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
        "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
        "LEFT JOIN subjects_norm AS norm ON (norm.id = si.norm_id)",
        "WHERE ey.id = %(ey_id)s::INT",
        "AND school.base_id = %(sb_id)s::INT",
        "AND dep.base_id = %(depbase_id)s::INT"
        ]

    if grade_pk:
        # when grade_pk has value: skip other filters
        sql_keys['grade_id'] = grade_pk
        sql_list.append('AND grade.id = %(grade_id)s::INT')
    elif student_pk:
        # when student_pk has value: skip other filters
        sql_keys['student_id'] = student_pk
        sql_list.append('AND stud.id = %(student_id)s::INT')
        sql_list.append('ORDER BY LOWER(subj.name)')
    elif subject_pk:
        # when student_pk has value: skip other filters
        sql_keys['subj_id'] = subject_pk
        sql_list.append('AND subj.id = %(subj_id)s::INT')
        sql_list.append('ORDER BY LOWER(stud.lastname), LOWER(stud.firstname)')
    else:
        sql_list.append('ORDER BY LOWER(stud.lastname), LOWER(stud.firstname), subjbase.code')

    sql = ' '.join(sql_list)

    logger.debug('sql_keys: ' + str(sql_keys) )

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        grade_rows = sch_mod.dictfetchall(cursor)

# - add full name to rows
    if grade_rows:
        for row in grade_rows:
            logger.debug('row: ' + str(row) )
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = stud_view.lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

# - add messages to student_row, only when only 1 row added (then studsubj_pk has value)
        if grade_pk:
            # when student_pk has value there is only 1 row
            row = grade_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    return grade_rows
# --- end of create_grade_rows




