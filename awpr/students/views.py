# PR2018-09-02
from django.contrib.auth.decorators import login_required

from django.db.models.functions import Lower
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView, View

from awpr import menus as awpr_menu
from awpr import constants as c
from students import validations as v
from awpr import functions as af

from accounts import models as acc_mod
from schools import models as sch_mod
from students import models as stud_mod
from subjects import models as subj_mod

import json # PR2018-12-03
# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


# ========  Student  =====================================

@method_decorator([login_required], name='dispatch')
class StudentListView(View):  # PR2018-09-02 PR2020-10-27

    def get(self, request):
        logger.debug('  =====  StudentListView ===== ')
        # logger.debug('request: ' + str(request) + ' Type: ' + str(type(request)))

        # <PERMIT>
        # - school-user can only view his own school
        # - insp-users can only view schools from his country
        # - system-users can only view school from request_user,country

        # -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

        # set headerbar parameters PR2018-08-06
        page = 'students'
        params = awpr_menu.get_headerbar_param(request, page)

        # save this page in Usersetting, so at next login this page will open. Uses in LoggedIn
        acc_mod.Usersetting.set_jsonsetting('sel_page', {'page': page}, request.user)

        return render(request, 'students.html', params)


# ========  StudentsubjectListView  ======= # PR2020-09-29
@method_decorator([login_required], name='dispatch')
class StudentsubjectListView(View):

    def get(self, request):
        logger.debug(" =====  StudentsubjectListView  =====")
# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

        #requsr_examyear = sch_mod.Examyear.objects.get_or_none(country_id=request.user.country_id, pk=request.user.examyear_id)
        #requsr_examyear_text = str(_('Examyear')) + ' ' + str(requsr_examyear) if requsr_examyear else _('<No examyear selected>')

        #requsr_school = sch_mod.School.objects.get_or_none( examyear=request.user.examyear, base=request.user.schoolbase)
        #requsr_school_text = requsr_school.base.code + ' ' + requsr_school.name if requsr_school else _('<No school selected>')

        # set headerbar parameters PR2018-08-06
        page = 'subjects'
        params = awpr_menu.get_headerbar_param(request, page)
        # save this page in Usersetting, so at next login this page will open. Uses in LoggedIn
        acc_mod.Usersetting.set_jsonsetting('sel_page', {'page': page}, request.user)

        return render(request, 'studentsubjects.html', params)
#/////////////////////////////////////////////////////////////////

def create_student_rows(setting_dict, append_dict, student_pk):
    # --- create rows of all students of this examyear / school PR2020-10-27
    logger.debug(' =============== create_student_rows ============= ')
    sel_examyear_pk = af.get_dict_value(setting_dict, ('sel_examyear_pk',))
    sel_schoolbase_pk = af.get_dict_value(setting_dict, ('sel_schoolbase_pk',))

    sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk}
    sql_list = ["SELECT st.id, st.base_id, st.school_id AS s_id,",
        "st.department_id AS dep_id, st.level_id AS lvl_id, st.sector_id AS sct_id, st.scheme_id,",
        "dep.abbrev AS dep_abbrev,",
        "dep.level_req AS lvl_req, dep.level_caption AS lvl_caption, lvl.abbrev AS lvl_abbrev,",
        "dep.sector_req AS sct_req, dep.sector_caption AS sct_caption, sct.abbrev AS sct_abbrev,",
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

    #logger.debug('sql_keys: ' + str(sql_keys))
    #logger.debug('sql: ' + str(sql))
    #logger.debug('student_rows: ' + str(student_rows))

# - add lastname_firstname_initials to rows
    if student_rows:
        for row in student_rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

    # - add messages to student_row
    if student_pk and student_rows:
        # when student_pk has value there is only 1 row
        row = student_rows[0]
        if row:
            for key, value in append_dict.items():
                row[key] = value

    return student_rows


# --- end of create_student_rows


@method_decorator([login_required], name='dispatch')
class StudentUploadView(View):  # PR2020-10-01

    def post(self, request):
        logger.debug(' ============= studentUploadView ============= ')

        update_wrap = {}
        has_permit = False
        if request.user and request.user.country and request.user.schoolbase:
            has_permit = True  # (request.user.is_perm_planner or request.user.is_perm_hrman)
        if has_permit:

            # - Reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                logger.debug('upload_dict' + str(upload_dict))

                # - get id  variables
                student_pk = upload_dict.get('student_pk')
                is_create = upload_dict.get('create', False)
                is_delete = upload_dict.get('delete', False)

                logger.debug('student_pk' + str(student_pk))
                student_rows = []
                append_dict = {}
                error_dict = {}

                sel_country = request.user.country

                # - get examyear of requsr, TODO only if examyear is published and not locked
                s_ey_pk = upload_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                sel_examyear = sch_mod.Examyear.objects.get_or_none(pk=s_ey_pk, country=sel_country)
                sel_examyear_pk = sel_examyear.pk if sel_examyear else None

                s_sb_pk = upload_dict.get(c.KEY_SEL_SCHOOLBASE_PK)
                sel_schoolbase = sch_mod.Schoolbase.objects.get_or_none(pk=s_sb_pk, country=sel_country)
                sel_schoolbase_pk = sel_schoolbase.pk if sel_schoolbase else None

                s_sb_pk = upload_dict.get(c.KEY_SEL_DEPBASE_PK)
                sel_depbase = sch_mod.Departmentbase.objects.get_or_none(pk=s_sb_pk, country=sel_country)
                sel_depbase_pk = sel_depbase.pk if sel_depbase else None

                # - get school only if school is not locked
                sel_school = sch_mod.School.objects.get_or_none(
                    base=sel_schoolbase,
                    examyear=sel_examyear,
                    locked=False
                )
                logger.debug('sel_school: ' + str(sel_school))

                sel_department = sch_mod.Department.objects.get_or_none(
                    base=sel_depbase,
                    examyear=sel_examyear
                )
                logger.debug('sel_department: ' + str(sel_department))

                if sel_school:
# - Delete student
                    if is_delete:
                        student = stud_mod.Student.objects.get_or_none(
                            id=student_pk,
                            school=sel_school
                        )
                        if student:
                            this_text = _("student '%(tbl)s' ") % {'tbl': student.name}
                            # a. check if student has grades, put msg_err in update_dict when error
                            msg_err = None  # validate_student_has_emplhours(student)
                            if msg_err:
                                error_dict['err_delete'] = msg_err
                            else:
                                # b. check if there are teammembers with this student: absence teammembers, remove student from shift teammembers
                                # delete_student_from_teammember(student, request)
                                # c. delete student
                                deleted_ok = True  # m.delete_instance(student, {}, error_dict, request, this_text)
                                # logger.debug('deleted_ok' + str(deleted_ok))
                                if deleted_ok:
                                    # - add deleted_row to absence_rows
                                    student_rows.append({'pk': student_pk,
                                                         'mapid': 'student_' + str(student_pk),
                                                         'deleted': True})
                                    student = None
                                # logger.debug('student_rows' + str(student_rows))
                    else:
                        # D. Create new student
                        if is_create:
                            student, msg_err = create_student(sel_country, sel_school, sel_department, upload_dict, request)
                            if student:
                                append_dict['created'] = True
                            elif msg_err:
                                append_dict['err_create'] = msg_err
                        # E. Get existing student
                        else:
                            student = stud_mod.Student.objects.get_or_none(id=student_pk, school=sel_school)

                    # I. add update_dict to update_wrap
                    if student:
                        logger.debug('student: ' + str(student))
                        # F. Update student, also when it is created.
                        #  Not necessary. Most fields are required. All fields are saved in create_student
                        # if student:
                        update_student(student, upload_dict, error_dict, request)

                        if error_dict:
                            append_dict['error'] = error_dict
                        setting_dict = {
                            'sel_examyear_pk': sel_school.examyear.pk,
                            'sel_schoolbase_pk': sel_school.base_id
                        }
                        student_rows = create_student_rows(
                            setting_dict=setting_dict,
                            append_dict=append_dict,
                            student_pk=student.pk
                        )

                update_wrap['updated_student_rows'] = student_rows

        # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))


@method_decorator([login_required], name='dispatch')
class StudentsubjectUploadView(View):  # PR2020-11-20

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= StudentsubjectUploadView ============= ')

        # function creates, deletes and updates studentsubject records of current student PR2020-11-21
        update_wrap = {}
        #<PERMIT> TODO
        has_permit = False
        # current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # in that case student data cannot be changed
        # check if student belongs to request.user.schoolbase
        if request.user and request.user.country and request.user.schoolbase:
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

# - get examyear from upload_dict, filter: examyear is published and not locked
                s_ey_pk = upload_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                sel_examyear = sch_mod.Examyear.objects.get_or_none(
                    pk=s_ey_pk,
                    country=request.user.country,
                    published=True,
                    locked=False
                )
                logger.debug('sel_examyear: ' + str(sel_examyear))
                # NIU sel_examyear_pk = sel_examyear.pk if sel_examyear else None

# - get schoolbase from upload_dict:
                s_sb_pk = upload_dict.get(c.KEY_SEL_SCHOOLBASE_PK)
                # TODO check if sel_schoolbase equals requsr_schoolbase: user can only make changes of his own school
                # turned off for now for testing
                # checked_sb_pk = s_sb_pk if s_sb_pk == request.user.schoolbase.pk else None
                checked_sb_pk = s_sb_pk
                sel_schoolbase = sch_mod.Schoolbase.objects.get_or_none(pk=checked_sb_pk, country=request.user.country)
                # NIU sel_schoolbase_pk = sel_schoolbase.pk if sel_schoolbase else None

                logger.debug('sel_schoolbase: ' + str(sel_schoolbase))
# - get school, filter: school is not locked
                sel_school = sch_mod.School.objects.get_or_none(
                    base=sel_schoolbase,
                    examyear=sel_examyear,
                    locked=False
                )
                logger.debug('sel_school: ' + str(sel_school))

# - get current student from upload_dict, filter: sel_school, student is not locked
                student = None
                if sel_school:
                    student_pk = upload_dict.get('student_pk')
                    student = stud_mod.Student.objects.get_or_none(
                        id=student_pk,
                        school=sel_school,
                        locked=False
                    )
                logger.debug('student: ' + str(student))

# - get list of studentsubjects from upload_dict
                studsubj_list = None
                if student:
                    studsubj_list = upload_dict.get('studsubj_list')
                if studsubj_list:
                    studsubj_rows = []
# - loop through list of uploaded studentsubjects
                    for studsubj_dict in studsubj_list:
                        # values of mode are: 'delete', 'create', 'update'
                        mode = studsubj_dict.get('mode')
                        studsubj_pk = studsubj_dict.get('studsubj_pk')
                        schemeitem_pk = studsubj_dict.get('schemeitem_pk')

                        logger.debug('---------- ')
                        logger.debug('studsubj mode: ' + str(mode))
                        logger.debug('studsubj_pk: ' + str(studsubj_pk))
                        logger.debug('schemeitem_pk: ' + str(schemeitem_pk))

                        append_dict = {}
                        error_dict = {}

# - get current studsubj - when mode is 'create': studsubj is None. It will be created at "elif mode == 'create'"
                        studsubj = stud_mod.Studentsubject.objects.get_or_none(
                            id=studsubj_pk,
                            student=student
                        )
                        logger.debug('studsubj: ' + str(studsubj))
# +++ delete studsubj
                        if mode == 'delete':
                            # if published: don't delete, but set deleted=True, so its remains in the Ex1 form
                            #               also set grades 'deleted=True
                            # if not published: delete studsubj, grades will be cascade deleted
                            if studsubj:
                                this_text = None
                                if studsubj.schemeitem:
                                    subject = studsubj.schemeitem.subject
                                    if subject and subject.name:
                                        this_text = _("Subject '%(tbl)s' ") % {'tbl': subject.name}
                                logger.debug('this_text: ' + str(this_text))

                                logger.debug('studsubj.published: ' + str(studsubj.published))

                                if studsubj.published:
                                    # if published: set deleted=True, so its remains in the Ex1 form
                                    setattr(studsubj, 'deleted', True)
                                    studsubj.save(request=request)
                                    logger.debug('studsubj.deleted: ' + str(studsubj.deleted))
                                    grades = stud_mod.Grade.objects.filter(studentsubject=studsubj)
                                    # also set grades deleted=True
                                    if grades:
                                        for grade in grades:
                                            setattr(grade, 'deleted', True)
                                            grade.save(request=request)
                                            logger.debug('grade.deleted: ' + str(grade.deleted))
                                else:

                                    deleted_ok = sch_mod.delete_instance(studsubj, error_dict, request, this_text)
                                    logger.debug('deleted_ok: ' + str(deleted_ok))
                                    if deleted_ok:
                                        # - add deleted_row to studsubj_rows
                                        studsubj_rows.append({'studsubj_id': studsubj_pk,
                                                             'mapid': 'studsubj_' + str(student.pk) + '_' + str(studsubj_pk),
                                                             'deleted': True})
                                        studsubj = None
                                        logger.debug('deleted_row: ' + str(studsubj_rows))

# +++ create new studentsubject
                        elif mode == 'create':
                            schemeitem = subj_mod.Schemeitem.objects.get_or_none(id=schemeitem_pk)
                            logger.debug('schemeitem: ' + str(schemeitem))
                            studsubj, msg_err = create_studsubj(student, schemeitem, request)
                            logger.debug('studsubj: ' + str(studsubj))
                            if studsubj:
                                append_dict['created'] = True
                            elif msg_err:
                                append_dict['err_create'] = msg_err
                            logger.debug('append_dict: ' + str(append_dict))
# +++ update existing studsubj - also when studsubj is created - studsubj is None when deleted
                        if studsubj and mode in ('create', 'update'):
                            logger.debug('studsubj and mode: ' + str(studsubj))
                            update_studsubj(studsubj, studsubj_dict, error_dict, request)

# - add update_dict to update_wrap
                        if studsubj:
                            # TODO check value of error_dict
                            if error_dict:
                                append_dict['error'] = error_dict
                            setting_dict = {
                                'sel_examyear_pk': sel_school.examyear.pk,
                                'sel_schoolbase_pk': sel_school.base_id
                            }
                            rows = create_studentsubject_rows(
                                setting_dict= setting_dict,
                                append_dict=append_dict,
                                studsubj_pk=studsubj.pk
                            )
                            if rows:
                                studsubj_row = rows[0]
                                if studsubj_row:
                                    studsubj_rows.append(studsubj_row)
                    if studsubj_rows:
                        update_wrap['updated_studsubj_rows'] = studsubj_rows

        #logger.debug('update_wrap: ' + str(update_wrap))
        # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of StudentsubjectUploadView


#######################################################
def update_studsubj(instance, upload_dict, msg_dict, request):
    # --- update existing and new instance PR2019-06-06
    # add new values to update_dict (don't reset update_dict, it has values)
    logger.debug(' ------- update_studsubj -------')
    logger.debug('upload_dict' + str(upload_dict))

    # FIELDS_STUDENTSUBJECT = ('student', 'schemeitem', 'cluster', 'is_extra_nocount','is_extra_counts', 'is_elective_combi',
    #                          'pws_title','pws_subjects', 'has_exemption', 'has_reex', 'has_reex03', 'has_pok', 'pok_status',
    #                          'modifiedby', 'modifiedat')

    #
    # FIELDS_STUDENTSUBJECT = ( student, schemeitem, cluster,
    #   is_extra_nocount, is_extra_counts, is_elective_combi, pws_title, pws_subjects,
    #   has_exemption, has_reex, has_reex03, has_pok,
    #   subj_auth1by, subj_auth2by, subjpublished, exem_auth1by, exem_auth2by, exemppublished,
    #   reex_auth1by, reex_auth2by, reexpublished, reex3_auth1by, reex3_auth2by, reex3published,
    #   pok_auth1by, pok_auth2by, pokpublished,
    #   deleted, 'modifiedby', 'modifiedat')


    # upload_dict{'mode': 'update', 'studsubj_id': 10, 'schemeitem_id': 201, 'stud_id': 29,
    #                   'is_extra_nocount': False, 'is_extra_counts': False, 'is_elective_combi': False,
    #                   'pws_title': 'oo', 'pws_subjects': 'pp'}
    save_changes = False
    for field, new_value in upload_dict.items():
# a. get new_value and saved_value

        #logger.debug('field: ' + str(field) + ' new_value: ' + str(new_value))

# 2. save changes in field 'name', 'abbrev'
        if field in ['pws_title', 'pws_subjects']:
            saved_value = getattr(instance, field)
            logger.debug('saved_value: ' + str(saved_value))
            if new_value != saved_value:
                # TODO
                msg_err = None
                if not msg_err:
                    # c. save field if changed and no_error
                    setattr(instance, field, new_value)
                    save_changes = True
                else:
                    msg_dict['err_' + field] = msg_err

# 3. save changes in fields 'namefirst', 'namelast'
        elif field in ['is_extra_nocount','is_extra_counts', 'is_elective_combi']:
            saved_value = getattr(instance, field)
            logger.debug('saved_value: ' + str(saved_value))
            if new_value != saved_value:
                setattr(instance, field, new_value)
                save_changes = True

        elif field in ['has_exemption', 'has_reex', 'has_reex03']:
            saved_value = getattr(instance, field)
            logger.debug('saved_value: ' + str(saved_value))
            if new_value != saved_value:
                setattr(instance, field, new_value)
                save_changes = True
                exam_period = None
                if field =='has_exemption':
                    exam_period = c.EXAMPERIOD_EXEMPTION
                elif field =='has_reex':
                    exam_period = c.EXAMPERIOD_SECOND
                elif field =='has_reex03':
                    exam_period = c.EXAMPERIOD_SECOND

       # - check if grade of this exam_period exists
                grade = stud_mod.Grade.objects.filter(studentsubject=instance, examperiod=exam_period).first()
                if grade:
                    if new_value:
       # - if it exists while old has_exemption etc. was False: it must be deleted row. Undelete
                        setattr(grade, 'deleted', False)
                    else:
       # - when new has_exemption etc. is False: deleted row by setting deleted=True and reset all fields
                        setattr(grade, 'deleted', True)
                        for fld in ('pescore', 'cescore', 'segrade', 'pegrade', 'cegrade', 'pecegrade', 'finalgrade',
                                    'sepublished', 'pepublished', 'cepublished'):
                            setattr(grade, fld, None)
                        for fld in ('seauth', 'peauth', 'ceauth', 'status'):
                            setattr(grade, fld, 0)
                        grade.save(request=request)
                elif new_value:
       # - if it does not exist and new has_exemption etc. is True: create new grade row
                    grade = stud_mod.Grade(
                        studentsubject=instance,
                        examperiod=c.EXAMPERIOD_EXEMPTION)
                    grade.save(request=request)
                if grade:
                    grade.save(request=request)


    #   subj_auth1by, subj_auth2by, subjpublished, exem_auth1by, exem_auth2by, exemppublished,
    #   reex_auth1by, reex_auth2by, reexpublished, reex3_auth1by, reex3_auth2by, reex3published,
    #   pok_auth1by, pok_auth2by, pokpublished,

        elif field in ('subj_auth1by', 'subj_auth2by', 'exem_auth1by', 'exem_auth2by',
                       'reex_auth1by', 'reex_auth2by', 'reex3_auth1by', 'reex3_auth2by',
                       'pok_auth1by', 'pok_auth2by'):
            logger.debug('field: ' + str(field) )
            logger.debug('new_value: ' + str(new_value))

            prefix, suffix  = field.split('_')
            logger.debug('prefix: ' + str(prefix) )
            logger.debug('suffix: ' + str(suffix) )

# - check if instance is published. Authorization of published instances cannot be changed.
            err_published, err_same_user = False, False
            fld_published = prefix + '_published'
            item_published = getattr(instance, fld_published)
            if item_published:
                err_published = True
# - check other authorization, to check if it is the same user. Only when auth is set to True
            elif new_value:
                suffix_other = 'auth2by' if suffix == 'auth1by' else 'auth1by'
                fld_other = prefix + '_' + suffix_other
                other_authby = getattr(instance, fld_other)
                logger.debug('other_authby: ' + str(other_authby) )
                logger.debug('request.user: ' + str(request.user) )
                if other_authby and other_authby == request.user:
                    err_same_user = True
            if not err_published and not err_same_user:
                if new_value:
                    setattr(instance, field, request.user)
                else:
                    setattr(instance, field, None)
                save_changes = True


            #msg_dict['err_' + prefix] = _('This item is published. You cannot change its authorization.')
            # msg_dict['err_' + prefix] = _('The same user cannot authorize both as chairman and secretary.')
    # --- end of for loop ---

# 5. save changes`
    if save_changes:
        try:
            instance.save(request=request)
            logger.debug('The changes have been saved' + str(instance))
        except:
            msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')
# --- end of update_studsubj


@method_decorator([login_required], name='dispatch')
class StudentImportView(View):  # PR2020-10-01

    def get(self, request):
        logger.debug(' ============= StudentImportView ============= ')
        param = {}
        has_permit = False
        if request.user is not None and request.user.country is not None and request.user.schoolbase is not None:
            has_permit = True  # (request.user.is_perm_planner or request.user.is_perm_hrman)
        if has_permit:
            # coldef_list = [{'tsaKey': 'student', 'caption': _('Company name')},
            #                      {'tsaKey': 'ordername', 'caption': _('Order name')},
            #                      {'tsaKey': 'orderdatefirst', 'caption': _('First date order')},
            #                      {'tsaKey': 'orderdatelast', 'caption': _('Last date order')} ]

            # get coldef_list  and caption
            coldef_list = c.COLDEF_SUBJECT
            captions_dict = c.CAPTION_IMPORT

            # get stored setting from Schoolsetting
            stored_setting = sch_mod.Schoolsetting.get_jsonsetting(c.KEY_IMPORT_SUBJECT, request.user.schoolbase)

            logger.debug('coldef_list: ' + str(coldef_list))
            logger.debug('captions_dict: ' + str(captions_dict))
            logger.debug('stored_setting: ' + str(stored_setting))

            # don't replace keyvalue when new_setting[key] = ''
            self.has_header = True
            self.worksheetname = ''
            self.codecalc = 'linked'
            if 'has_header' in stored_setting:
                self.has_header = False if Lower(stored_setting['has_header']) == 'false' else True
            if 'worksheetname' in stored_setting:
                self.worksheetname = stored_setting['worksheetname']
            if 'codecalc' in stored_setting:
                self.codecalc = stored_setting['codecalc']

            if 'coldefs' in stored_setting:
                stored_coldefs = stored_setting['coldefs']
                # skip if stored_coldefs does not exist
                if stored_coldefs:
                    # loop through coldef_list
                    for coldef in coldef_list:
                        # coldef = {'tsaKey': 'student', 'caption': 'Cliënt'}
                        # get fieldname from coldef
                        fieldname = coldef.get('tsaKey')
                        # logger.debug('fieldname: ' + str(fieldname))

                        if fieldname:  # fieldname should always be present
                            # check if fieldname exists in stored_coldefs
                            if fieldname in stored_coldefs:
                                # if so, add Excel name with key 'excKey' to coldef
                                coldef['excKey'] = stored_coldefs[fieldname]
                                # logger.debug('stored_coldefs[fieldname]: ' + str(stored_coldefs[fieldname]))

            coldefs_dict = {
                'worksheetname': self.worksheetname,
                'has_header': self.has_header,
                'codecalc': self.codecalc,
                'coldefs': coldef_list
            }
            coldefs_json = json.dumps(coldefs_dict, cls=LazyEncoder)

            captions = json.dumps(captions_dict, cls=LazyEncoder)

            param = awpr_menu.get_headerbar_param(request, {'captions': captions, 'setting': coldefs_json})

        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_student.html', param)


@method_decorator([login_required], name='dispatch')
class StudentImportUploadSetting(View):  # PR2019-03-10
    # function updates mapped fields, no_header and worksheetname in table Companysetting
    def post(self, request, *args, **kwargs):
        # logger.debug(' ============= StudentImportUploadSetting ============= ')
        # logger.debug('request.POST' + str(request.POST) )
        schoolsetting_dict = {}
        has_permit = False
        if request.user is not None and request.user.examyear is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_perm_adm_or_sys)
        if has_permit:
            if request.POST['upload']:
                new_setting_json = request.POST['upload']
                # new_setting is in json format, no need for json.loads and json.dumps
                # logger.debug('new_setting_json' + str(new_setting_json))

                new_setting_dict = json.loads(request.POST['upload'])
                settings_key = c.KEY_IMPORT_SUBJECT

                new_worksheetname = ''
                new_has_header = True
                new_code_calc = ''
                new_coldefs = {}
    #TODO get_jsonsetting returns dict
                stored_json = sch_mod.Schoolsetting.get_jsonsetting(settings_key, request.user.schoolbase)
                if stored_json:
                    stored_setting = json.loads(stored_json)
                    # logger.debug('stored_setting: ' + str(stored_setting))
                    if stored_setting:
                        new_has_header = stored_setting.get('has_header', True)
                        new_worksheetname = stored_setting.get('worksheetname', '')
                        new_code_calc = stored_setting.get('codecalc', '')
                        new_coldefs = stored_setting.get('coldefs', {})

                if new_setting_json:
                    new_setting = json.loads(new_setting_json)
                    # logger.debug('new_setting' + str(new_setting))
                    if new_setting:
                        if 'worksheetname' in new_setting:
                            new_worksheetname = new_setting.get('worksheetname', '')
                        if 'has_header' in new_setting:
                            new_has_header = new_setting.get('has_header', True)
                        if 'coldefs' in new_setting:
                            new_coldefs = new_setting.get('coldefs', {})
                    # logger.debug('new_code_calc' + str(new_code_calc))
                new_setting = {'worksheetname': new_worksheetname,
                               'has_header': new_has_header,
                               'codecalc': new_code_calc,
                               'coldefs': new_coldefs}
                new_setting_json = json.dumps(new_setting)
                # logger.debug('new_setting' + str(new_setting))
                # logger.debug('---  set_jsonsettingg  ------- ')
                # logger.debug('new_setting_json' + str(new_setting_json))
                # logger.debug(new_setting_json)
                # TODO set_jsonsetting parameter changed to dict
                sch_mod.Schoolsetting.set_jsonsetting(settings_key, new_setting_json, request.user.schoolbase)

        # only for testing
        # ----- get user_lang
        # user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        # tblName = 'student'
        # coldefs_dict = compdicts.get_stored_coldefs_dict(tblName, user_lang, request)
        # if coldefs_dict:
        #    schoolsetting_dict['coldefs'] = coldefs_dict
        # logger.debug('new_setting from saved ' + str(coldefs_dict))

        # m.Companysetting.set_setting(c.settings_key, new_setting_json, request.user.schoolbase)

        return HttpResponse(json.dumps(schoolsetting_dict, cls=LazyEncoder))


# --- end of StudentImportUploadSetting

@method_decorator([login_required], name='dispatch')
class StudentImportUploadData(View):  # PR2018-12-04 PR2019-08-05 PR2020-06-04

    def post(self, request):
        logger.debug(' ========================== StudentImportUploadData ========================== ')
        params = {}
        has_permit = False
        is_not_locked = False
        if request.user is not None and request.user.examyear is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_perm_adm_or_sys)
            is_not_locked = not request.user.examyear.locked

        if is_not_locked and has_permit:
            # - Reset language
            # PR2019-03-15 Debug: language gets lost, get request.user.lang again
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                params = import_students(upload_dict, user_lang, request)

        return HttpResponse(json.dumps(params, cls=LazyEncoder))


# --- end of StudentImportUploadData

def import_students(upload_dict, user_lang, request):
    logger.debug(' -----  import_students ----- ')
    logger.debug('upload_dict: ' + str(upload_dict))
    # - get is_test, codecalc, dateformat, awpKey_list
    is_test = upload_dict.get('test', False)
    awpKey_list = upload_dict.get('awpKey_list')
    dateformat = upload_dict.get('dateformat', '')

    params = {}
    if awpKey_list:
        # - get lookup_field
        # lookup_field is field that determines if student alreay exist.
        # check if one of the fields 'payrollcode', 'identifier' or 'code' exists
        # first in the list is lookup_field
        lookup_field = 'code'

        # - get upload_dict from request.POST
        student_list = upload_dict.get('students')
        if student_list:

            today_dte = af.get_today_dateobj()
            today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
            double_line_str = '=' * 80
            indent_str = ' ' * 5
            space_str = ' ' * 30
            logfile = []
            logfile.append(double_line_str)
            logfile.append('  ' + str(request.user.schoolbase.code) + '  -  ' +
                           str(_('Import students')) + ' ' + str(_('date')) + ': ' + str(today_formatted))
            logfile.append(double_line_str)

            if lookup_field is None:
                info_txt = str(_('There is no field given to lookup candidates. Candidates cannot be uploaded.'))
                logfile.append(indent_str + info_txt)
            else:
                if is_test:
                    info_txt = str(_("This is a test. The candidate data are not saved."))
                else:
                    info_txt = str(_("The candidate data are saved."))
                logfile.append(indent_str + info_txt)
                lookup_caption = str(get_field_caption('student', lookup_field))
                info_txt = str(_("Candidates are looked up by the field: '%(fld)s'.") % {'fld': lookup_caption})
                logfile.append(indent_str + info_txt)
                # if dateformat:
                #    info_txt = str(_("The date format is: '%(fld)s'.") % {'fld': dateformat})
                #    logfile.append(indent_str + info_txt)
                update_list = []
                for student_dict in student_list:
                    # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html

                    update_dict = upload_student(student_list, student_dict, lookup_field,
                                                 awpKey_list, is_test, dateformat, indent_str, space_str, logfile,
                                                 request)
                    # json_dumps_err_list = json.dumps(msg_list, cls=f.LazyEncoder)
                    if update_dict:  # 'Any' returns True if any element of the iterable is true.
                        update_list.append(update_dict)

                if update_list:  # 'Any' returns True if any element of the iterable is true.
                    params['student_list'] = update_list
            if logfile:  # 'Any' returns True if any element of the iterable is true.
                params['logfile'] = logfile
                # params.append(new_student)
    return params

def lookup_student(studentbase, request):  # PR2019-12-17 PR2020-10-20
    #logger.debug('----------- lookup_student ----------- ')

    student = None
    multiple_students_found = False

# - search student by studentbase and request.user.examyear
    if studentbase:
        # check if student exists multiple times
        row_count = stud_mod.Student.objects.filter(base=studentbase, examyear=request.user.examyear).count()
        if row_count > 1:
            multiple_students_found = True
        elif row_count == 1:
            # get student when only one found
            student = stud_mod.Student.objects.get_or_none(base=studentbase, examyear=request.user.examyear)

    return student, multiple_students_found



def get_field_caption(table, field):
    caption = ''
    if table == 'student':
        if field == 'code':
            caption = _('Abbreviation')
        elif field == 'name':
            caption = _('Student name')
        elif field == 'sequence':
            caption = _('Sequence')
        elif field == 'depbases':
            caption = _('Departments')
    return caption


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_student(country, school, department, upload_dict, request):
    # --- create student # PR2019-07-30 PR2020-10-11  PR2020-12-14
    logger.debug(' ----- create_student ----- ')

    student = None
    msg_err = None

    logger.debug('school: ' + str(school))

    if school:

# - get value of 'abbrev'
        lastname = af.get_dict_value(upload_dict, ('lastname', 'value'))
        firstname = af.get_dict_value(upload_dict, ('firstname', 'value'))

        if lastname and firstname:
# - validate abbrev checks null, max len and exists
            """
            msg_err = validate_code_name_identifier(
                table='student',
                field='code',
                new_value=code,
                is_absence=False,
                parent=parent,
                update_dict={},
                msg_dict={},
                request=request,
                this_pk=None)
            """
            msg_err = None
# - create and save student
            if not msg_err:

                try:
                    # First create base record. base.id is used in Student. Create also saves new record
                    base = stud_mod.Studentbase.objects.create(country=country)

                    student = stud_mod.Student(
                        base=base,
                        school=school,
                        lastname=lastname,
                        firstname=firstname,
                        department=department
                    )
                    student.save(request=request)
                except:
                    name = lastname + ', ' + firstname
                    msg_err = str(_("An error occurred. Student '%(val)s' could not be added.") % {'val': name})

    logger.debug('student: ' + str(student))
    logger.debug('msg_err: ' + str(msg_err))
    return student, msg_err


#######################################################
def update_student(instance, upload_dict, msg_dict, request):
    # --- update existing and new instance PR2019-06-06
    # add new values to update_dict (don't reset update_dict, it has values)
    logger.debug(' ------- update_student -------')
    logger.debug('upload_dict' + str(upload_dict))

    if instance:
        #
        # FIELDS_STUDENT = ('base', 'school', 'department', 'level', 'sector', 'scheme', 'package',
        #                   'lastname', 'firstname', 'prefix', 'gender', 'idnumber', 'birthdate', 'birthcountry', 'birthcity',
        #                   'classname', 'examnumber', 'regnumber', 'diplomanumber', 'gradelistnumber',
        #                   'iseveningstudent', 'hasdyslexia',
        #                   'locked', 'has_reex', 'bis_exam', 'withdrawn', 'modifiedby', 'modifiedat')
        update_scheme = False
        save_changes = False
        for field in c.FIELDS_STUDENT:

# --- get field_dict from  upload_dict  if it exists
            field_dict = upload_dict[field] if field in upload_dict else {}
            if field_dict:
                logger.debug('field' + str(field))
                logger.debug('field_dict' + str(field_dict))
                if 'update' in field_dict:
# a. get new_value and saved_value
                    new_value = field_dict.get('value')
                    saved_value = getattr(instance, field)
                    logger.debug('new_value' + str(new_value))
                    logger.debug('saved_value' + str(saved_value))

# - save changes in fields 'namefirst', 'namelast'
                    if field in ['lastname', 'firstname']:
                        if new_value != saved_value:
                            name_first = None
                            name_last = None
                            if field == 'firstname':
                                name_first = new_value
                                name_last = getattr(instance, 'lastname')
                            elif field == 'lastname':
                                name_first = getattr(instance, 'firstname')
                                name_last = new_value
                            # check if student namefirst / namelast combination already exists
                            """
                            has_error = validate_namelast_namefirst(
                                namelast=name_last,
                                namefirst=name_first,
                                company=request.user.company,
                                update_field=field,
                                msg_dict=msg_dict,
                                this_pk=instance.pk)
                            """
                            has_error = False
                            if not has_error:
                                setattr(instance, field, new_value)
                                save_changes = True

                    # 2. save changes in field 'name', 'abbrev'
                    elif field in ('prefix', 'gender', 'idnumber',
                                 'birthdate', 'birthcountry', 'birthcity',
                                'classname', 'examnumber', 'regnumber', 'diplomanumber', 'gradelistnumber'):
                        if new_value != saved_value:
            # validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                            msg_err = None
                            if not msg_err:
                                # c. save field if changed and no_error
                                setattr(instance, field, new_value)
                                save_changes = True
                            else:
                                msg_dict['err_' + field] = msg_err

# 3. save changes in depbases
                    elif field == 'department':
                        logger.debug('field' + str(field))
                        logger.debug('new_value' + str(new_value) + ' ' + str(type(new_value)))
                        logger.debug('saved_value' + str(saved_value) + ' ' + str(type(saved_value)))
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
                            update_scheme = True
                    elif field =='level':
                        logger.debug('field' + str(field))
                        logger.debug('new_value' + str(new_value) + ' ' + str(type(new_value)))
                        logger.debug('saved_value' + str(saved_value) + ' ' + str(type(saved_value)))
                        if new_value != saved_value:
                            level = subj_mod.Level.objects.get_or_none(pk=new_value)
                            setattr(instance, field, level)
                            save_changes = True
                            update_scheme = True
                    elif field == 'sector':
                        logger.debug('field' + str(field))
                        logger.debug('new_value' + str(new_value) + ' ' + str(type(new_value)))
                        logger.debug('saved_value' + str(saved_value) + ' ' + str(type(saved_value)))
                        if new_value != saved_value:
                            sector = subj_mod.Sector.objects.get_or_none(pk=new_value)
                            setattr(instance, field, sector)
                            save_changes = True
                            update_scheme = True
# 4. save changes in field 'inactive'
                    elif field == 'inactive':
                        #logger.debug('inactive new_value]: ' + str(new_value) + ' ' + str(type(new_value)))
                        saved_value = getattr(instance, field)
                        #logger.debug('inactive saved_value]: ' + str(saved_value) + ' ' + str(type(saved_value)))
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
                    else:
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
# --- end of for loop ---
        if update_scheme:
            department = getattr(instance, 'department')
            level = getattr(instance, 'level')
            sector = getattr(instance, 'sector')
            scheme = subj_mod.Scheme.objects.get_or_none(
                department=department,
                level=level,
                sector=sector)
            setattr(instance, 'scheme', scheme)
# 5. save changes
        if save_changes:
            try:
                instance.save(request=request)
            except:
                msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def upload_student(student_list, student_dict, lookup_field, awpKey_list,
                   is_test, dateformat, indent_str, space_str, logfile, request):  # PR2019-12-17 PR2020-10-21
    logger.debug('----------------- import student  --------------------')
    logger.debug(str(student_dict))
    # awpKeys are: 'code', 'name', 'sequence', 'depbases'

    # - get index and lookup info from student_dict
    row_index = student_dict.get('rowindex', -1)
    new_code = student_dict.get('code')
    new_name = student_dict.get('name')
    new_sequence = student_dict.get('sequence')
    new_depbases = student_dict.get('depbases')

    # - create update_dict
    update_dict = {'id': {'table': 'student', 'rowindex': row_index}}

    # - give row_error when lookup went wrong
    # multiple_found and value_too_long return the lookup_value of the error field

    lookup_field_caption = str(get_field_caption('student', lookup_field))
    lookup_field_capitalized = '-'
    if lookup_field_caption:
        lookup_field_capitalized = lookup_field_caption.capitalize()
    is_skipped_str = str(_("is skipped."))
    skipped_str = str(_("Skipped."))
    logfile.append(indent_str)
    msg_err = None
    log_str = ''

    studentbase = None
    student = None

    # check if lookup_value has value ( lookup_field = 'code')
    lookup_value = student_dict.get(lookup_field)
    if not lookup_value:
        log_str = str(_("No value for lookup field: '%(fld)s'.") % {'fld': lookup_field_caption})
        msg_err = ' '.join((skipped_str, log_str))

    # check if lookup_value is not too long
    elif len(lookup_value) > c.MAX_LENGTH_SCHOOLCODE:
        value_too_long_str = str(_("Value '%(val)s' is too long.") % {'val': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_SCHOOLCODE})
        log_str = value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))

    # check if new_name has value
    elif new_name is None:
        field_caption = str(get_field_caption('student', 'name'))
        log_str = str(_("No value for required field: '%(fld)s'.") % {'fld': field_caption})
        msg_err = ' '.join((skipped_str, log_str))

    # check if student name  is not too long
    elif len(new_name) > c.MAX_LENGTH_NAME:
        value_too_long_str = str(_("Value '%(val)s' is too long.") % {'val': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_NAME})
        log_str = value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))
    else:

        # - check if lookup_value occurs mutiple times in Excel file
        excel_list_multiple_found = False
        excel_list_count = 0
        for dict in student_list:
            value = dict.get(lookup_field)
            if value and value == lookup_value:
                excel_list_count += 1
            if excel_list_count > 1:
                excel_list_multiple_found = True
                break
        if excel_list_multiple_found:
            log_str = str(_("%(fld)s '%(val)s' is not unique in Excel file.") % {'fld': lookup_field_capitalized,
                                                                                 'val': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

    if msg_err is None:

        # - check if studentbase with this code exists in request.user.country. studentbase has value when only one found
        # lookup_value = student_dict.get(lookup_field)
        studentbase, multiple_found = lookup_studentbase(lookup_value, request)
        if multiple_found:
            log_str = str(_("Value '%(fld)s' is found multiple times.") % {'fld': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

        # - check if student with this studentbase exists in request.user.examyear. student has value when only one found
        multiple_students_found = False
        if studentbase:
            student, multiple_students_found = lookup_student(studentbase, request)
        if multiple_students_found:
            log_str = str(_("Value '%(fld)s' is found multiple times in this exam year.") % {'fld': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

    code_text = (new_code + space_str)[:30]

    # - if error: put msg_err in update_dict and logfile
    if msg_err:
        update_dict['row_error'] = msg_err
        update_dict[lookup_field] = {'error': msg_err}
        logfile.append(code_text + is_skipped_str)
        logfile.append(' ' * 30 + log_str)
    else:

        # - create new studentbase when studentbase not found in database
        if studentbase is None:
            try:
                studentbase = stud_mod.Studentbase(
                    country=request.user.country,
                    code=new_code
                )
                if studentbase:
                    studentbase.save()
            except:
                # - give error msg when creating studentbase failed
                error_str = str(_("An error occurred. The student is not added."))
                logfile.append(" ".join((code_text, error_str)))
                update_dict['row_error'] = error_str

        if studentbase:

            # - create new student when student not found in database
            is_existing_student = False
            save_instance = False

            if student is None:
                try:
                    student = stud_mod.Student(
                        base=studentbase,
                        examyear=request.user.examyear,
                        name=new_name
                    )
                    if student:
                        student.save(request=request)
                        update_dict['id']['created'] = True
                        logfile.append(code_text + str(_('is added.')))
                except:
                    # - give error msg when creating student failed
                    error_str = str(_("An error occurred. The student is not added."))
                    logfile.append(" ".join((code_text, error_str)))
                    update_dict['row_error'] = error_str
            else:
                is_existing_student = True
                logfile.append(code_text + str(_('already exists.')))

            if student:
                #TODO check if student.locked, school.activated , school.locked, examyear.published, examyear.locked
                # add 'id' at the end, after saving the student. Pk doent have value until instance is saved
                # update_dict['id']['pk'] = student.pk
                # update_dict['id']['ppk'] = student.company.pk
                # if student:
                #    update_dict['id']['created'] = True

                # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
                # solved bij wrapping with str()

                blank_str = '<' + str(_('blank')) + '>'
                was_str = str(_('was') + ': ')
                # FIELDS_SUBJECT = ('base', 'examyear', 'name', 'abbrev', 'sequence', 'depbases', 'modifiedby', 'modifiedat')
                for field in ('name', 'abbrev', 'sequence', 'depbases'):
                    # --- get field_dict from  upload_dict  if it exists
                    if field in awpKey_list:
                        # ('field: ' + str(field))
                        field_dict = {}
                        field_caption = str(get_field_caption('student', field))
                        caption_txt = (indent_str + field_caption + space_str)[:30]

                        if field in ('code', 'name', 'namefirst', 'email', 'address', 'city', 'country'):
                            if field == 'code':
                                # new_code is created in this function and already checked for max_len
                                new_value = new_code
                            else:
                                new_value = student_dict.get(field)
                            # check length of new_value
                            max_len = c.MAX_LENGTH_NAME \
                                if field in ('namelast', 'namefirst', 'email', 'address', 'city', 'country') \
                                else c.MAX_LENGTH_CODE

                            if max_len and new_value and len(new_value) > max_len:
                                msg_err = str(_("'%(val)s' is too long. Maximum is %(max)s characters'.") % {
                                    'val': new_value, 'max': max_len})
                                field_dict['error'] = msg_err
                            else:
                                # - replace '' by None
                                if not new_value:
                                    new_value = None
                                field_dict['value'] = new_value
                                if not is_existing_student:
                                    logfile.append(caption_txt + (new_value or blank_str))
                                # - get saved_value
                                saved_value = getattr(student, field)
                                if new_value != saved_value:
                                    # put new value in student instance
                                    setattr(student, field, new_value)
                                    field_dict['updated'] = True
                                    save_instance = True
                                    # create field_dict and log
                                    if is_existing_student:
                                        old_value_str = was_str + (saved_value or blank_str)
                                        field_dict['info'] = field_caption + ' ' + old_value_str
                                        update_str = ((new_value or blank_str) + space_str)[:25] + old_value_str
                                        logfile.append(caption_txt + update_str)

                        # add field_dict to update_dict
                        update_dict[field] = field_dict

                # dont save data when it is a test run
                if not is_test and save_instance:
                    student.save(request=request)
                    update_dict['id']['pk'] = student.pk
                    update_dict['id']['ppk'] = student.company.pk
                    # wagerate wagecode
                    # priceratejson additionjson
                    try:
                        student.save(request=request)
                        update_dict['id']['pk'] = student.pk
                        update_dict['id']['ppk'] = student.company.pk
                    except:
                        # - give error msg when creating student failed
                        error_str = str(_("An error occurred. The student data is not saved."))
                        logfile.append(" ".join((code_text, error_str)))
                        update_dict['row_error'] = error_str

    return update_dict


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_studsubj(student, schemeitem, request):
    # --- create student subject # PR2020-11-21
    logger.debug(' ----- create_studsubj ----- ')

    studsubj = None
    msg_err = None

    if student and schemeitem:
        # - TODO check if student already has this subject, if subject is allowed
        msg_err = None
# - create and save student
        if not msg_err:
            try:
                #a = 1 / 0
                studsubj = stud_mod.Studentsubject(
                    student=student,
                    schemeitem=schemeitem
                )
                studsubj.save(request=request)
                # also create grade of first examperiod
                grade = stud_mod.Grade(
                    studentsubject=studsubj,
                    examperiod=c.EXAMPERIOD_FIRST
                )
                grade.save(request=request)
            except:
                name = schemeitem.subject.name if schemeitem.subject and schemeitem.subject.name else '---'
                msg_err = str(_("An error occurred. Subject '%(val)s' could not be added.") % {'val': name})

    return studsubj, msg_err


#/////////////////////////////////////////////////////////////////

def create_studentsubject_rows(setting_dict, append_dict, student_pk=None, studsubj_pk=None):
    # --- create rows of all students of this examyear / school PR2020-10-27
    #logger.debug(' =============== create_student_rows ============= ')
    #logger.debug('append_dict', append_dict)
    # create list of students of this school / examyear, possibly with filter student_pk or studsubj_pk
    # with left join of studentsubjects with deleted=False
    sel_examyear_pk = af.get_dict_value(setting_dict, ('sel_examyear_pk',))
    sel_schoolbase_pk = af.get_dict_value(setting_dict, ('sel_schoolbase_pk',))

    sql_studsubj_list = ["SELECT studsubj.id AS studsubj_id, studsubj.student_id,",
        "studsubj.cluster_id, si.id AS schemeitem_id, si.scheme_id AS scheme_id,",
        "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_elective_combi,",
        "studsubj.pws_title, studsubj.pws_subjects,",
        "studsubj.has_exemption, studsubj.has_reex, studsubj.has_reex03, studsubj.has_pok,",

        "si.subject_id, si.subjecttype_id, si.gradetype,",
        "subjbase.code AS subj_code, subj.name AS subj_name,",
        "si.weight_se AS si_se, si.weight_ce AS si_ce,",
        "si.is_mandatory, si.is_combi, si.extra_count_allowed, si.extra_nocount_allowed,",
        "si.elective_combi_allowed, si.has_practexam,",

        "sjt.abbrev AS sjt_abbrev, sjt.has_prac AS sjt_has_prac,",
        "sjt.has_pws AS sjt_has_pws, sjt.one_allowed AS sjt_one_allowed,",

        "studsubj.subj_auth1by_id AS subj_auth1_id, SUBSTRING(subj_auth1.username, 7) AS subj_auth1_usr, subj_auth1.modified_at AS subj_auth1_modat,",
        "studsubj.subj_auth2by_id AS subj_auth2_id, SUBSTRING(subj_auth2.username, 7) AS subj_auth2_usr, subj_auth2.modified_at AS subj_auth2_modat,",
        "studsubj.subj_published_id AS subj_publ_id, subj_published.modifiedat AS subj_publ_modat,",

        "studsubj.exem_auth1by_id AS exem_auth1_id, SUBSTRING(exem_auth1.username, 7) AS exem_auth1_usr, exem_auth1.modified_at AS exem_auth1_modat,",
        "studsubj.exem_auth2by_id AS exem_auth2_id, SUBSTRING(exem_auth2.username, 7) AS exem_auth2_usr, exem_auth2.modified_at AS exem_auth2_modat,",
        "studsubj.exem_published_id AS exem_publ_id, exem_published.modifiedat AS exem_publ_modat,",

        "studsubj.reex_auth1by_id AS reex_auth1_id, SUBSTRING(reex_auth1.username, 7) AS reex_auth1_usr, reex_auth1.modified_at AS reex_auth1_modat,",
        "studsubj.reex_auth2by_id AS reex_auth2_id, SUBSTRING(reex_auth2.username, 7) AS reex_auth2_usr, reex_auth2.modified_at AS reex_auth2_modat,",
        "studsubj.reex_published_id AS reex_publ_id, reex_published.modifiedat AS reex_publ_modat,",

        "studsubj.reex3_auth1by_id AS reex3_auth1_id, SUBSTRING(reex3_auth1.username, 7) AS reex3_auth1_usr, reex3_auth1.modified_at AS reex3_auth1_modat,",
        "studsubj.reex3_auth2by_id AS reex3_auth2_id, SUBSTRING(reex3_auth2.username, 7) AS reex3_auth2_usr, reex3_auth2.modified_at AS reex3_auth2_modat,",
        "studsubj.reex3_published_id AS reex3_publ_id, reex3_published.modifiedat AS reex3_publ_modat,",

        "studsubj.pok_auth1by_id AS pok_auth1_id, SUBSTRING(pok_auth1.username, 7) AS pok_auth1_usr, pok_auth1.modified_at AS pok_auth1_modat,",
        "studsubj.pok_auth2by_id AS pok_auth2_id, SUBSTRING(pok_auth2.username, 7) AS pok_auth2_usr, pok_auth2.modified_at AS pok_auth2_modat,",
        "studsubj.pok_published_id AS pok_publ_id, pok_published.modifiedat AS pok_publ_modat,",

        "studsubj.deleted, studsubj.modifiedby_id, studsubj.modifiedat,",
        "SUBSTRING(au.username, 7) AS modby_username",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
        "LEFT JOIN subjects_subjecttype AS sjt ON (sjt.id = si.subjecttype_id)",

        "LEFT JOIN accounts_user AS au ON (au.id = studsubj.modifiedby_id)",

        "LEFT JOIN accounts_user AS subj_auth1 ON (subj_auth1.id = studsubj.subj_auth1by_id)",
        "LEFT JOIN accounts_user AS subj_auth2 ON (subj_auth2.id = studsubj.subj_auth2by_id)",
        "LEFT JOIN students_published AS subj_published ON (subj_published.id = studsubj.subj_published_id)",

        "LEFT JOIN accounts_user AS exem_auth1 ON (exem_auth1.id = studsubj.exem_auth1by_id)",
        "LEFT JOIN accounts_user AS exem_auth2 ON (exem_auth2.id = studsubj.exem_auth2by_id)",
        "LEFT JOIN students_published AS exem_published ON (exem_published.id = studsubj.exem_published_id)",

        "LEFT JOIN accounts_user AS reex_auth1 ON (reex_auth1.id = studsubj.reex_auth1by_id)",
        "LEFT JOIN accounts_user AS reex_auth2 ON (reex_auth2.id = studsubj.reex_auth2by_id)",
        "LEFT JOIN students_published AS reex_published ON (reex_published.id = studsubj.reex_published_id)",

        "LEFT JOIN accounts_user AS reex3_auth1 ON (reex3_auth1.id = studsubj.reex3_auth1by_id)",
        "LEFT JOIN accounts_user AS reex3_auth2 ON (reex3_auth2.id = studsubj.reex3_auth2by_id)",
        "LEFT JOIN students_published AS reex3_published ON (reex3_published.id = studsubj.reex3_published_id)",

        "LEFT JOIN accounts_user AS pok_auth1 ON (pok_auth1.id = studsubj.pok_auth1by_id)",
        "LEFT JOIN accounts_user AS pok_auth2 ON (pok_auth2.id = studsubj.pok_auth2by_id)",
        "LEFT JOIN students_published AS pok_published ON (pok_published.id = studsubj.pok_published_id)",

        "WHERE NOT studsubj.deleted"]

    sql_studsubjects = ' '.join(sql_studsubj_list)
    #  "LEFT JOIN (" + sql_studsubjects + ") AS studsubj ON (studsubj.student_id = st.id)",

    sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk}
    sql_list = ["SELECT studsubj.studsubj_id, studsubj.schemeitem_id, studsubj.cluster_id,",
        "CONCAT('studsubj_', st.id::TEXT, '_', studsubj.studsubj_id::TEXT) AS mapid, 'studsubj' AS table,",
        "st.id AS stud_id, st.lastname, st.firstname, st.prefix, st.examnumber,",
        "st.scheme_id, st.iseveningstudent, st.locked, st.has_reex, st.bis_exam, st.withdrawn,",
        "studsubj.subject_id AS subj_id, studsubj.subj_code, studsubj.subj_name, studsubj.sjt_abbrev,",
        "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",

        "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_elective_combi,",
        "studsubj.pws_title, studsubj.pws_subjects,",
        "studsubj.has_exemption, studsubj.has_reex, studsubj.has_reex03, studsubj.has_pok,",

        "studsubj.is_mandatory, studsubj.is_combi, studsubj.extra_count_allowed, studsubj.extra_nocount_allowed, studsubj.elective_combi_allowed,",
        "studsubj.sjt_has_prac, studsubj.sjt_has_pws, studsubj.sjt_one_allowed,",

        "studsubj.subj_auth1_id, studsubj.subj_auth1_usr, studsubj.subj_auth1_modat,",
        "studsubj.subj_auth2_id, studsubj.subj_auth2_usr, studsubj.subj_auth2_modat,",
        "studsubj.subj_publ_id, studsubj.subj_publ_modat,",

        "studsubj.exem_auth1_id, studsubj.exem_auth1_usr, studsubj.exem_auth1_modat,",
        "studsubj.exem_auth2_id, studsubj.exem_auth2_usr, studsubj.exem_auth2_modat,",
        "studsubj.exem_publ_id, studsubj.exem_publ_modat,",

        "studsubj.reex_auth1_id, studsubj.reex_auth1_usr, studsubj.reex_auth1_modat,",
        "studsubj.reex_auth2_id, studsubj.reex_auth2_usr, studsubj.reex_auth2_modat,",
        "studsubj.reex_publ_id, studsubj.reex_publ_modat,",

        "studsubj.reex3_auth1_id, studsubj.reex3_auth1_usr, studsubj.reex3_auth1_modat,",
        "studsubj.reex3_auth2_id, studsubj.reex3_auth2_usr, studsubj.reex3_auth2_modat,",
        "studsubj.reex3_publ_id, studsubj.reex3_publ_modat,",

        "studsubj.pok_auth1_id, studsubj.pok_auth1_usr, studsubj.pok_auth1_modat,",
        "studsubj.pok_auth2_id, studsubj.pok_auth2_usr, studsubj.pok_auth2_modat,",
        "studsubj.pok_publ_id, studsubj.pok_publ_modat,",

        "studsubj.deleted, studsubj.modifiedat, studsubj.modby_username",
        "FROM students_student AS st",
        "LEFT JOIN (" + sql_studsubjects + ") AS studsubj ON (studsubj.student_id = st.id)",
        "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
        "LEFT JOIN subjects_scheme AS scheme ON (scheme.id = st.scheme_id)",
        "LEFT JOIN subjects_package AS package ON (package.id = st.package_id)",
        "WHERE school.base_id = %(sb_id)s::INT AND school.examyear_id = %(ey_id)s::INT "]

    if studsubj_pk:
        # when studsubj_pk has value: skip other filters
        sql_list.append('AND studsubj.studsubj_id = %(studsubj_id)s::INT')
        sql_keys['studsubj_id'] = studsubj_pk
    elif student_pk:
        # when student_pk has value: skip other filters
        sql_keys['st_id'] = student_pk
        sql_list.append('AND st.id = %(st_id)s::INT')
        sql_list.append('ORDER BY studsubj.subj_abbrev')
    else:
        sql_list.append('ORDER BY LOWER(st.lastname), LOWER(st.firstname), studsubj.subj_code')

    sql = ' '.join(sql_list)

    newcursor = connection.cursor()
    newcursor.execute(sql, sql_keys)
    student_rows = sch_mod.dictfetchall(newcursor)

# - full name to rows
    if student_rows:
        for row in student_rows:
            first_name = row.get('firstname')
            last_name = row.get('lastname')
            prefix = row.get('prefix')
            full_name = lastname_firstname_initials(last_name, first_name, prefix)
            row['fullname'] = full_name if full_name else None

# - add messages to student_row, only when only 1 row added (then studsubj_pk has value)
        if studsubj_pk:
            # when student_pk has value there is only 1 row
            row = student_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    return student_rows
# --- end of create_studentsubject_rows

# oooooooooooooo Functions  Student name ooooooooooooooooooooooooooooooooooooooooooooooooooo

def lastname_firstname_initials(last_name, first_name, prefix):
    full_name = last_name.strip()
    firstnames = ''
    if first_name:
        firstnames_arr = first_name.split()
        if len(firstnames_arr) == 0:
            firstnames = first_name.strip()  # 'PR 13 apr 13 Trim toegevoegd
        else:
            skip = False
            for item in firstnames_arr:
                if not skip:
                    firstnames = firstnames + item + ' '  # write first firstname in full
                    skip = True
                else:
                    if item:
                        #PR2017-02-18 VB debug. bij dubbele spatie in voornaam krijg je lege err(x)
                        firstnames = firstnames + item[:1] # write of the next firstnames only the first letter
    if firstnames:
        full_name = full_name + ', ' + firstnames
    if prefix: # put prefix at the front
        full_name = prefix.strip() + ' ' + full_name
    full_name = full_name.strip()
    return full_name

    
def SplitPrefix(name, is_firstname):
    # PR2020-11-15 from AWP PR2016-04-01 aparte functie van gemaakt
    # Functie splits tussenvoegsel voor Achternaam (IsPrefix=True) of achter Voornamen (IsPrefix=False)

    found = False

    remainder = ''
    prefix = ''

    prefixes = ("voor den", "van den", "van der", "van de", "van 't", "de la",
                "del", "den", "der", "dos", "ten", "ter", "van",
                "al", "d'", "da", "de", "do", "el", "l'", "la", "le", "te")


    # search in reverse order of prefix length: check "van den" first,
    # when you check 'van' first, 'van den' will not be reached
    # when booIsPrefix: put space after prefix, but also check "d'" and "l'" without space after prefix
    # when not booIsPrefix: put space before prefix

    prefixes_without_space = ("d'", " l'")

    name_stripped = name.strip()  # 'PR 13 apr 13 Trim toegevoegd
    if name_stripped:
        name_len = len(name_stripped)
        for value in prefixes:
            search_prefix = ' ' + value if is_firstname else value + ' '
            search_len = len(search_prefix)
            if name_len >= search_len:
                if is_firstname:
                    # check for prefix at end of firstname
                    lookup_str = name_stripped[0:search_len]
                else:
                    # check for prefix in front of lastname
                    lookup_str = name_stripped[-name_len]
                if lookup_str == search_prefix:
                    found = True
                    prefix = lookup_str.strip()
                    if is_firstname:
                        remainder = name_stripped[len].strip()
                    else:
                        remainder_len = name_len - search_len
                        remainder = name_stripped[0:remainder_len].strip()
                    break
    # Voornamen met tussenvoegsel erachter
        #van groot naar klein, anders wordt 'van den' niet bereikt, maar 'den' ingevuld

    return found, prefix, remainder # found returns True when name is split
# End of SplitPrefix


# oooooooooooooo End of Functions Student name ooooooooooooooooooooooooooooooooooooooooooooooooooo


def get_mapped_coldefs_student(request_user):  # PR2018-12-01
    # function creates dict of fieldnames of table Student
    # It is used in ImportSudent to map Excel fieldnames to AWP fieldnames
    # mapped_coldefs: {
    #     "worksheetname": "Compleetlijst",
    #     "no_header": 0,
    #     "mapped_coldef_list": [{"awpKey": "idnumber", "caption": "ID nummer", "excKey": "ID"},
    #                            {"awpKey": "lastname", "caption": "Achternaam", "excKey": "ANAAM"}, ....]

    logger.debug('==============get_mapped_coldefs_student ============= ' )

    # get mapped excelColDef from table Schoolsetting
    mapped_coldefs = {}
    if request_user is not None:
        if request_user.examyear is not None and request_user.schoolbase is not None and request_user.depbase is not None:

            # get list of level base_id and abbrev of this school, examyear and department
            level_abbrev_list = Level.get_abbrev_list(request_user)

            # get saved settings from schoolsettings
            no_header, worksheetname, setting_columns, setting_levels, setting_sectors = get_student_mapped_coldefs(request_user)
            # setting_columns: {'gender': 'MV', 'birthdate': 'GEB_DAT', 'birthcountry': 'geboorte_land',
            #                   'birthcity': 'geboorte_plaats', 'sector': 'Profiel', 'classname': 'KLAS'}
            # setting_sectors: {'29': 'em', '30': 'ng', '31': 'cm'}

# add excKey to coldef if found in setting_columns
            column_list = get_student_column_list(request_user)
            # column_list is list of default student coldef keys and captions
            # column_list = [{"awpKey": "idnumber", "caption": "ID nummer"},
            #                {"awpKey": "fullname", "caption": "Volledige naam"}, ...]
            for coldef in column_list:
                awpKey = coldef.get('awpKey')
                # awpKey: 'idnumber'
                if awpKey: # awpKey should always be present
                    if setting_columns:
                        # lookup awpKey 'idnumber' in setting_columns, return None if not found
                        # setting_columns: {'idnumber': 'ID', ...}
                        excKey = setting_columns.get(awpKey)
                        # excKey: 'ID'
                        if excKey:
                        # if 'idnumber' found in setting_columns, add {'excKey': 'ID'} to coldef
                            coldef['excKey'] = excKey
            # column_list: [{'awpKey': 'idnumber', 'caption': 'ID nummer', 'excKey': 'ID'},

            # level_list is list of levels of this school, dep and examyear
            # level_list =  [{'base_id': 7, 'abbrev': 'TKL'},
            #                {'base_id': 8, 'abbrev': 'PKL'},
            #                {'base_id': 9, 'abbrev': 'PBL'}]
            level_list = Level.get_abbrev_list(request_user)
            logger.debug('level_list: ' + str(level_list) + ' type: ' + str(type(level_list)))

            mapped_level_list = []
            for level in level_list:
                base_id_str = str(level.get('base_id',''))
                abbrev = level.get('abbrev')
                level_dict = {}
                if base_id_str and abbrev:
                    level_dict['awpKey'] = base_id_str
                    level_dict['caption'] = abbrev
                    # check if base_id_str of this level is stored in setting_levels
                    # setting_levels: {'29': 'em', '30': 'ng', '31': 'cm'}
                    if base_id_str in setting_levels:
                        excKey = setting_levels[base_id_str]
                        if excKey:
                            level_dict['excKey'] = excKey
                if level_dict:
                    mapped_level_list.append(level_dict)
            logger.debug('mapped_level_list: ' + str(mapped_level_list) + ' type: ' + str(type(mapped_level_list)))


            # sector_list is list of sectors of this school, dep and examyear
            # sector_list =  [{'base_id': 29, 'abbrev': 'ec'},
            #                 {'base_id': 30, 'abbrev': 'tech'},
            #                 {'base_id': 31, 'abbrev': 'z&w'}]
            sector_list = Sector.get_abbrev_list(request_user)
            mapped_sector_list = []
            for sector in sector_list:
                base_id_str = str(sector.get('base_id',''))
                abbrev = sector.get('abbrev')
                sector_dict = {}
                if base_id_str and abbrev:
                    sector_dict['awpKey'] = base_id_str
                    sector_dict['caption'] = abbrev
                    # check if base_id_str of this sector is stored in setting_sectors
                    # setting_sectors: {'29': 'em', '30': 'ng', '31': 'cm'}
                    if base_id_str in setting_sectors:
                        excKey = setting_sectors[base_id_str]
                        if excKey:
                            sector_dict['excKey'] = excKey
                if sector_dict:
                    mapped_sector_list.append(sector_dict)
            #logger.debug('mapped_sector_list: ' + str(mapped_sector_list) + ' type: ' + str(type(mapped_sector_list)))

            mapped_coldefs = {
                "worksheetname": worksheetname,
                "no_header": no_header,
                "mapped_coldef_list": column_list
            }
            if mapped_level_list:
                mapped_coldefs['mapped_level_list'] = mapped_level_list
            if mapped_sector_list:
                mapped_coldefs['mapped_sector_list'] = mapped_sector_list

            logger.debug('mapped_coldefs: ' + str(mapped_coldefs) + ' type: ' + str(type(mapped_coldefs)))
            mapped_coldefs = json.dumps(mapped_coldefs)
    return mapped_coldefs

# ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo

def get_student_column_list(request_user):
    # function creates dict of fieldnames of table Student
    # It is used in ImportSudent to map Excel fieldnames to AWP fieldnames
    # mapped_coldefs: {
    #     "worksheetname": "Compleetlijst",
    #     "no_header": 0,
    #     "mapped_coldef_list": [{"awpKey": "idnumber", "caption": "ID nummer", "excKey": "ID"},
    #                            {"awpKey": "lastname", "caption": "Achternaam", "excKey": "ANAAM"}, ....]

    # logger.debug('==============get_mapped_coldefs_student ============= ' )

    # caption Sector/Profiel depends on department
    sector_caption = Sector.get_caption(request_user)
    skip_level = True
    if request_user.depbase:
        dep = request_user.department
        if dep.abbrev == "Vsbo":
            skip_level = False

    if request_user.lang == 'nl':
        coldef_list = [
            {"awpKey": "idnumber", "caption": "ID nummer"},
            {"awpKey": "fullname", "caption": "Volledige naam"},
            {"awpKey": "lastname", "caption": "Achternaam"},
            {"awpKey": "firstname", "caption": "Voornamen"},
            {"awpKey": "prefix", "caption": "Voorvoegsel"},
            {"awpKey": "gender", "caption": "Geslacht"},
            {"awpKey": "birthdate", "caption": "Geboortedatum"},
            {"awpKey": "birthcountry", "caption": "Geboorteland"},
            {"awpKey": "birthcity", "caption": "Geboorteplaats"},
        ]
    else:
        coldef_list = [
            {"awpKey": "idnumber", "caption": "ID number"},
            {"awpKey": "fullname", "caption": "Full name"},
            {"awpKey": "lastname", "caption": "Last name"},
            {"awpKey": "firstname", "caption": "First name"},
            {"awpKey": "prefix", "caption": "Prefix"},
            {"awpKey": "gender", "caption": "Gender"},
            {"awpKey": "birthdate", "caption": "Birthdate"},
            {"awpKey": "birthcountry", "caption": "Birth country"},
            {"awpKey": "birthcity", "caption": "Birth place"},
        ]

    if not skip_level:
        coldef_list.append({"awpKey": "level", "caption": "Leerweg"})
    coldef_list.append({"awpKey": "sector", "caption": sector_caption})

    if request_user.lang == 'nl':
        coldef_list.extend((
            {"awpKey": "classname", "caption": "Klas"},
            {"awpKey": "examnumber", "caption": "Examennummer"}
        ))
    else:
        coldef_list.extend((
            {"awpKey": "classname", "caption": "Class"},
            {"awpKey": "examnumber", "caption": "Exam number"}
        ))

    return coldef_list

def get_student_mapped_coldefs(request_user):
    logger.debug(        '---  get_student_mapped_coldefs  ------- ' + str(request_user))
    # get mapped excelColDef from table Schoolsetting

    no_header = False
    worksheetname = ''
    setting_columns = {}
    setting_levels = {}
    setting_sectors = {}

    if request_user is not None:
        if request_user.schoolbase is not None:
            logger.debug('request_user.schoolbase: ' + str(request_user.schoolbase) + ' type: ' + str(type(request_user.schoolbase)))
            setting = sch_mod.Schoolsetting.objects.filter(
                schoolbase=request_user.schoolbase,
                key_str=c.KEY_IMPORT_STUDENT
            ).first()

            if setting:
                no_header = int(setting.bool01)

                # setting_columns: {'firstname': 'Voornamen', 'classname': 'STAMKLAS'} type: <class 'dict'>
                if setting.char01:
                    try:
                        setting_columns = json.loads(setting.char01)
                    except:
                        pass

                if setting.char02:
                    worksheetname = setting.char02

                if setting.char03:
                    try:
                        setting_levels = json.loads(setting.char03)
                    except:
                        pass
                if setting.char04:
                    try:
                        setting_sectors = json.loads(setting.char04)
                    except:
                        pass
            logger.debug('setting_columns: ' + str(setting_columns) + ' type: ' + str(type(setting_columns)))
    return  no_header, worksheetname, setting_columns, setting_levels, setting_sectors


def get_mapped_levels_sectors(request_user):  # PR2019-01-01
    # function creates dict of fieldnames of table Student
    # It is used in ImportSudent to map Excel fieldnames to AWP fieldnames
    #     "settings_level_list": [{"awpLevel": "TKL", "excelLevel": ["tkl", "t.k.l."]"},
    #                            {"awpLevel": "PBL", "excelLevel": [], ....]

    logger.debug('==============get_mapped_levels_student ============= ' )
    level_abbrev_list = Level.get_abbrev_list(request_user)
    sector_abbrev_list = Sector.get_abbrev_list(request_user)
    # sector_abbrev_list =  [{'base_id': 29, 'abbrev': 'ec'},
    #                        {'base_id': 30, 'abbrev': 'tech'},
    #                        {'base_id': 31, 'abbrev': 'z&w'}]

    # get mapped levels and mapped sectors from table Schoolsetting
    """
    TODO: settings_level_list and settings_sector_list not defined PR2019-02-11
    mapped_level_list = []
    # iterate through list of levels: [{"base_id": 1, "caption": TKL}, {"base_id": 2, "caption": PKL}, {"base_id": 3, "caption": PBL}]
    for level_abbrev in level_abbrev_list:
        level_dict = {'awpKey': str(level_abbrev.get('base_id')), 'caption': level_abbrev.get('abbrev')}
    # check if this awpLevel is stored in settings_level_list
        for settings_dict in settings_level_list:
            # settings_dict = {"id": 2, "caption": "pkl"},
            if 'awpKey' in settings_dict:
                if settings_dict['awpKey'] == level_dict['awpKey']:
    # check if this awpLevel has excKey
                    if "excKey" in settings_dict:
    # if so: add to  awpLevel is stored in settings_level_list
                        level_dict['excKey'] = settings_dict['excKey']
                        break
        mapped_level_list.append(level_dict)

    mapped_sector_list = []
    # iterate through list of sectors ["eco", "techn", "z&w"]
    for sector_abbrev in sector_abbrev_list:
        sector_dict = {'awpKey': str(sector_abbrev.get('base_id')), 'caption': sector_abbrev.get('abbrev')}
    # check if this awpSector is stored in settings_sector_list
        for settings_dict in settings_sector_list:
            # dict = {"awpSct": "tkl", "excKey": ["tkl", "t.k.l."]"},
            if 'awpKey' in settings_dict:
                if settings_dict['awpKey'] == sector_dict['awpKey']:
    # check if this awpSector has excKey
                    if "excKey" in dict:
    # if so: add to  awpSector is stored in settings_sector_list
                        sector_dict['excKey'] = settings_dict['excKey']
                        break
        mapped_sector_list.append(sector_dict)

    logger.debug('mapped_sector_list: ' + str(mapped_sector_list))
    logger.debug('mapped_level_list: ' + str(mapped_level_list))
    return mapped_level_list, mapped_sector_list

    """
# ooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo


#  =========== Ajax requests  ===========
# PR2018-09-03 from https://simpleisbetterthancomplex.com/tutorial/2018/01/29/how-to-implement-dependent-or-chained-dropdown-list-with-django.html
def load_cities(request):
    # logger.debug('load_cities request: ' + str(request) + ' Type: ' + str(type(request)))
    # load_cities request: <WSGIRequest: GET '/student/ajax/load_cities/?birthcountry_id=16'> Type: WSGIRequest
    birthcountry_id = request.GET.get('birthcountry_id')
    # logger.debug('load_cities country_id ' + str(birthcountry_id) + ' Type: ' + str(type(birthcountry_id)))

    # create list of tuples
    # items = [(0, '---')]
    # for _city in Birthcity.objects.filter(birthcountry_id=birthcountry_id).order_by('name'):
    #     items.append((_city.id, _city.name))
    # see: https: // www.journaldev.com / 15891 / python - zip - function

    # create list of dicts
    items =[] # [{'id': 0, 'name': '---'}]
    keys = ['id', 'name']
    for _city in Birthcity.objects.filter(birthcountry_id=birthcountry_id).order_by('name'):
        values = [_city.id, _city.name]
        items.append(dict(zip(keys, values)))

    logger.debug('load_cities items: ' + str(items) + ' Type: ' + str(type(items)))
    # was: cities: < QuerySet[ < Birthcity: Anderlecht >, ... , < Birthcity: Wilrijk >] > Type: <class 'QuerySet'>
    # items: [{'id': 13, 'name': 'Anderlecht'}, ... , {'id': 27, 'name': 'Wilrijk'}]Type: <class 'list'>

    return render(request, 'dropdown_list_options.html', {'items': items})


"""

      $(document).ready(function(){
        $("#id_birthcountry").change(function () {
          var url = $("#StudentAddForm").attr("data-cities-url");  // get the url of the `load_cities` view
          var birthcountryId = $(this).val();  // get the selected country ID from the HTML input

          $.ajax({                       // initialize an AJAX request
            url: url,                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
            data: {
              'birthcountry': birthcountryId       // add the country id to the GET parameters
            },
            success: function (data) {   // `data` is the return of the `load_cities` view function
              $("#id_birthcity").html(data);  // replace the contents of the city input with the data that came from the server
            }

        });
      });
"""

"""

      $(document).ready(function(){
      // from http://jsfiddle.net/CZcvM/

        var sel = $('#testing'),
            opts =[],
            debug = $('#debug');

      debug.append(typeof sel);
      var opt_array = sel.attr('options');
      //for(var i = 0, len = opt_array.length; i < len; ++i)
      for (var a in opt_array)
      {
          debug.append(a + ':' + opt_array[a] + "<br>");
          //opts.push(opt_array[a]);
      }
      //delete the first option
      function remove()
      {
          $('#testing option:first').remove();
      }

      function restore()
      {
          sel.options.length = 0;
          for(var i = 0, len = opts.length; i < len; ++i)
          {
              //debug.append(a + ':' + opts[a] + '<br>');
              sel.options.add(opts[i]);
          }
      }
      */
      $('#remove').click(remove);
      $('#restore').click(restore);








        $("#testbutton").click(function(){
            $(this).css("background-color", "pink");

            var temp = "myXXValue";

            // Create New Option.
            var newOption = $("<option>");

            newOption.attr("value", temp).text(temp);
            $("#showtext").html(newOption.value);

            // Append that to the DropDownList.
            $('#carselect').append(newOption);

            // Select the Option.
            // $("#carselect" > [value=" + temp + "]").attr("selected", "true");


            $("#showtext").html(temp);

        });
                 // $("p").hover(function(){
                 //        $(this).css("background-color", "yellow");
                 //        }, function(){
                 //        $(this).css("background-color", "pink");
                 //    });
      });
     </script>


"""