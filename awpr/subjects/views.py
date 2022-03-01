# PR2018-07-20
import io
from datetime import datetime

from django.contrib.auth.decorators import login_required # PR2018-04-01

from django.utils import timezone
from django.utils.functional import Promise

# PR2022-02-13 From Django 4 we dont have force_text You Just have to Use force_str Instead of force_text.
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

from django.db import connection
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from django.shortcuts import render

from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, pgettext_lazy, gettext_lazy as _
from django.views.generic import View
from reportlab.pdfgen.canvas import Canvas

from accounts import views as acc_view
from awpr import settings as s
from awpr import menus as awpr_menu
from awpr import logs as awpr_logs

from subjects import models as subj_mod

from awpr import constants as c
from awpr import functions as af
from awpr import validators as av
from awpr import downloads as dl
from awpr import printpdf

from schools import models as sch_mod
from subjects import models as sbj_mod
from students import models as stud_mod

import json  # PR2018-10-25
# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


# === Schemeitem =====================================
@method_decorator([login_required], name='dispatch')
class SchemeitemsDownloadView(View):  # PR2019-01-13
    # PR2019-01-17
    def post(self, request):
        # logger.debug(' ============= SchemeitemsDownloadView ============= ')
        # logger.debug('request.POST' + str(request.POST) )

        # request.POST<QueryDict: {'d
        #
        # ep_id': ['11'], 'lvl_id': ['7'], 'sct_id': ['30']}>

        params = {}
        if request.user is not None and request.user.examyear is not None:

        # lookup scheme by dep_id, lvl_id (if required) and sct_id (if required)
            if 'dep_id' in request.POST.keys():
                dep_id_int = int(request.POST['dep_id'])
                examyear = request.user.examyear
                department = sch_mod.Department.objects.filter(id=dep_id_int, examyear=examyear).first()
                if department:
                    dep_abbrev = department.abbrev
                    # logger.debug(dep_abbrev)

                    # lookup level (if required)
                    level = None
                    lvl_abbrev = ''
                    if department.level_req:
                        if 'lvl_id' in request.POST.keys():
                            lvl_id_int = int(request.POST['lvl_id'])
                            level = subj_mod.Level.objects.filter(id=lvl_id_int, examyear=examyear).first()
                            # if level:
                                # lvl_abbrev = level.abbrev
                    # logger.debug(lvl_abbrev)

                    # lookup sector (if required)
                    sector = None
                    sct_name = ''
                    if department.sector_req:
                        if 'sct_id' in request.POST.keys():
                            sct_id_int = int(request.POST['sct_id'])
                            sector = subj_mod.Sector.objects.filter(id=sct_id_int, examyear=examyear).first()
                            #if sector:
                                #sct_name = sector.name
                    # logger.debug(sct_name)

                    # lookup scheme by dep_id, lvl_id (if required) and sct_id (if required)
                    scheme = None
                    if level:
                        if sector:
                            logger.debug('filter by department, level and sector')
                            # filter by department, level and sector
                            # if selection contains multiple schemes: skip
                            if subj_mod.Scheme.objects.filter(
                                department=department, level=level, sector=sector
                            ).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(
                                    department=department, level=level, sector=sector
                                ).first()
                        else:
                            logger.debug('filter by department and level')
                            # filter by department and level
                            # if selection contains multiple schemes: skip
                            if subj_mod.Scheme.objects.filter(
                                    department=department, level=level
                            ).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(
                                    department=department, level=level
                                ).first()
                    else:
                        if sector:
                            # logger.debug('filter by department and sector')
                            # filter by department and sector
                            # if selection contains multiple schemes: skip

                            logger.debug('count: ' + str(subj_mod.Scheme.objects.filter(department=department, sector=sector).count()))
                            if subj_mod.Scheme.objects.filter(department=department, sector=sector).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(department=department, sector=sector).first()
                        else:
                            # logger.debug('only by department')
                            # filter only by department
                            # if selection contains multiple schemes: skip
                            if subj_mod.Scheme.objects.filter(department=department).count() == 1:
                                scheme = subj_mod.Scheme.objects.filter(department=department).first()

                    if scheme:
                        scheme_list_str = scheme.get_scheme_list_str()
                        params.update({'scheme': scheme_list_str})

                        # make list of all Subjects from this department and examyear (included in dep)
                        schemeitems = subj_mod.Schemeitem.get_schemeitem_list(scheme)
                        params.update({'schemeitems': schemeitems})

                        # make list of all Subjects from this department and examyear (included in dep)
                        subjects = subj_mod.Subject.get_subj_list(department)
                        params.update({'subjects': subjects})

                        # make list of all Subjecttypes from this department and examyear (included in dep)
                        subjecttypes = subj_mod.Subjecttype.get_subjtype_list( department)  # PR2019-01-18
                        params.update({'subjecttypes': subjecttypes})

                        # make list of all gradetypes

                        # GRADETYPE_CHOICES = ((0, 'None'), (1, 'Number'), (2, 'Good/Sufficient/Insufficient'))
                        gradetypes = []
                        for item in c.GRADETYPE_CHOICES:
                            if item[0] > 0:
                                gradetypes.append({
                                    'grtp_id': item[0],
                                    'name': item[1]
                                })
                        params.update({'gradetypes': gradetypes})

        #logger.debug('params')
        # logger.debug(params)
        return HttpResponse(json.dumps(params))


# ========  SubjectListView  ======= # PR2020-09-29  PR2021-03-25
@method_decorator([login_required], name='dispatch')
class SubjectListView(View):

    def get(self, request):
        #logger.debug(" =====  SubjectListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get sel_schoolbase from settings / request when role is insp, admin or system, from req_user otherwise
        sel_schoolbase, sel_schoolbase_saveNIU = af.get_sel_schoolbase_instance(request)

        # requsr_same_school = True when selected school is same as requsr_school PR2021-04-27
        # used on entering grades. Users can only enter grades of their own school. Syst, Adm and Insp, Comm can not neter grades
        requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase.pk)

# - get headerbar parameters
        if requsr_same_school:
            page = 'page_studsubj'
            html_page = 'studentsubjects.html'
            param = {'display_school': True, 'display_department': True}
        else:
            page = 'page_subject'
            html_page = 'subjects.html'
            param = {'display_school': False, 'display_department': False}

        params = awpr_menu.get_headerbar_param(request, page, param)

# - save this page in Usersetting, so at next login this page will open.  Used in LoggedIn
        # PR2021-06-22 moved to get_headerbar_param

        return render(request, html_page, params)


def create_subject_rows(setting_dict, skip_allowed_filter, request):
    # --- create rows of all subjects of this examyear  PR2020-09-29 PR2020-10-30 PR2020-12-02 PR2022-02-07
    logging_on = False  # s.LOGGING_ON

    sel_examyear_pk = af.get_dict_value(setting_dict, ('sel_examyear_pk',))
    sel_depbase_pk = af.get_dict_value(setting_dict, ('sel_depbase_pk',))

    if logging_on:
        logger.debug(' =============== create_subject_rows ============= ')
        logger.debug('setting_dict: ' + str(setting_dict) + ' ' + str(type(setting_dict)))
        logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk) + ' ' + str(type(sel_examyear_pk)))
        logger.debug('sel_depbase_pk: ' + str(sel_depbase_pk) + ' ' + str(type(sel_depbase_pk)))

    # lookup if sel_depbase_pk is in subject.depbases PR2020-12-19
    # use: AND %(depbase_pk)s::INT = ANY(sj.depbases)
    # ANY must be on the right side of =
    # from https://lerner.co.il/2014/05/22/looking-postgresql-arrays/
    # or
    # from https://www.postgresqltutorial.com/postgresql-like/
    # first_name LIKE '%Jen%';
    subject_rows = []
    if sel_examyear_pk:
        sql_keys = {'ey_id': sel_examyear_pk}
        sql_list = ["SELECT subj.id, subj.base_id, subj.examyear_id,",
            "CONCAT('subject_', subj.id::TEXT) AS mapid,",
            "subj.name, sb.code, subj.sequence, subj.depbases, subj.addedbyschool,",
            "subj.modifiedby_id, subj.modifiedat,",
            "ey.code AS examyear_code,",
            "SUBSTRING(au.username, 7) AS modby_username",
    
            "FROM subjects_subject AS subj",
            "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = subj.modifiedby_id)",
            
            "WHERE subj.examyear_id = %(ey_id)s::INT"
            ]

        # note: don't filter on sel_subjbase_pk, must be able to change within allowed
        sel_subjbase_pk = None

        # when setting allowed in serpage, all subject must be shown
        if not skip_allowed_filter:
            acc_view.get_userfilter_subjbase(sql_keys, sql_list, sel_subjbase_pk, request)

        #if subject_pk:
       #     # when employee_pk has value: skip other filters
        #    sql_keys['subj'] = subject_pk
        #    sql_list.append('AND subj.id = %(subj)s::INT')
        #else:
           # if cur_dep_only:
           #     sql_keys['depbase_lookup'] = ''.join( ('%;', str(sel_depbase_pk), ';%') )
            #    sql_list.append("AND CONCAT(';', subj.depbases::TEXT, ';') LIKE %(depbase_lookup)s::TEXT")

        sql_list.append("ORDER BY subj.id")

        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            subject_rows = af.dictfetchall(cursor)

    return subject_rows
# --- end of create_subject_rows


def create_cluster_rows(sel_examyear_pk, sel_schoolbase_pk, sel_depbase_pk, cluster_pk_list=None, add_field_created=False):
    # --- create rows of all clusters of this examyear this department  PR2022-01-06
    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug(' =============== create_cluster_rows ============= ')
        logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk) + ' ' + str(type(sel_examyear_pk)))
        logger.debug('sel_schoolbase_pk: ' + str(sel_schoolbase_pk) + ' ' + str(type(sel_schoolbase_pk)))
        logger.debug('add_field_created: ' + str(add_field_created))
        logger.debug('cluster_pk_list: ' + str(cluster_pk_list))

    cluster_rows = []
    if sel_examyear_pk and sel_schoolbase_pk and sel_depbase_pk:
        try:
            add_field_created_str = ", TRUE AS created" if add_field_created else ''

            sql_keys = {'ey_id': sel_examyear_pk, 'sb_id': sel_schoolbase_pk, 'db_id': sel_depbase_pk}
            sql_list = ["SELECT cl.id, cl.name, subj.id AS subject_id, subjbase.id AS subjbase_id,",
                        "subjbase.code AS subj_code, subj.name AS subj_name",
                        add_field_created_str,
                        "FROM subjects_cluster AS cl",
                        "INNER JOIN subjects_subject AS subj ON (subj.id = cl.subject_id)",
                        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                        "INNER JOIN schools_school AS sch ON (sch.id = cl.school_id)",
                        "INNER JOIN schools_department AS dep ON (dep.id = cl.department_id)",

                        "WHERE subj.examyear_id = %(ey_id)s::INT",
                        "AND sch.examyear_id = %(ey_id)s::INT",
                        "AND sch.base_id = %(sb_id)s::INT",
                        "AND dep.base_id = %(db_id)s::INT",
                        ]

            if cluster_pk_list:
                sql_keys['cluster_pk_arr'] = cluster_pk_list
                sql_list.append("AND cl.id IN ( SELECT UNNEST( %(cluster_pk_arr)s::INT[]))")

            sql_list.append("ORDER BY cl.id")

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                cluster_rows = af.dictfetchall(cursor)

                if logging_on:
                    logger.debug('sql: ' + str(sql))
                    logger.debug('cluster_rows: ' + str(cluster_rows) )

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return cluster_rows
# --- end of create_cluster_rows


@method_decorator([login_required], name='dispatch')
class SubjectUploadView(View):  # PR2020-10-01 PR2021-05-14 PR2021-07-18

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= SubjectUploadView ============= ')

        # error_list is attached to updated row, messages is attached to update_wrap
        messages = []
        update_wrap = {}

# - get permit
        has_permit = get_permit_crud_page_subject(request)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

# - get  variables
                subject_pk = upload_dict.get('subject_pk')
                mode = upload_dict.get('mode')
                is_create = (mode == 'create')
                is_delete = (mode == 'delete')

                if logging_on:
                    logger.debug('mode: ' + str(mode))
                    logger.debug('upload_dict' + str(upload_dict))

                updated_rows = []
                error_list = []
                is_created = False
                message_header = _('Subject')

# - get selected examyear from Usersetting
                selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                selected_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                examyear = None
                if selected_examyear_pk:
                    examyear = sch_mod.Examyear.objects.get_or_none(
                        id=selected_examyear_pk,
                        country=request.user.country
                    )

                if logging_on:
                    logger.debug('examyear' + str(examyear))

# - exit when no examyear or examyear is locked
                # TODO switch to get_selected_ey_school_dep_from_usersetting, it includes validation
                # note: subjects may be changed before publishing, therefore don't exit on examyear.published
                if examyear is None:
                    messages.append({'class': "border_bg_warning",
                                     'header': str(message_header),
                                     'msg_html': str(_('No exam year selected'))})
                elif examyear.locked:
                    messages.append( {'class': "border_bg_warning",
                                      'header': str(message_header),
                                      'msg_html': str(_("Exam year %(exyr)s is locked.") % {'exyr': str(examyear.code)})
                        })
                else:

# ++++ Create new subject:
                    if is_create:
                        subject = create_subject(examyear, upload_dict, messages, request)
                        if subject:
                            is_created = True
                    else:
# +++  get existing subject instance
                        subject = sbj_mod.Subject.objects.get_or_none(
                            id=subject_pk,
                            examyear=examyear
                        )
                    if logging_on:
                        logger.debug('..... subject: ' + str(subject))

                    deleted_ok = False

                    if subject:
# ++++ Delete subject
                        if is_delete:
                            deleted_ok = delete_subject(subject, updated_rows, error_list, request)

# - create subject_row, also when deleting failed, not when deleted ok, in that case subject_row is added in delete_subject
                        else:
                            update_subject_instance(subject, examyear, upload_dict, error_list, request)

# - create subject_row, also when deleting failed (when deleted ok there is no subject, subject_row is made above)
                    # PR2021-089-04 debug. gave error on subject.pk: 'NoneType' object has no attribute 'pk'
                    if not deleted_ok and subject:
                        setting_dict = {'sel_examyear_pk': examyear.pk}
                        updated_rows = create_subject_rows(
                            setting_dict=setting_dict,
                            skip_allowed_filter=True,
                            request=request
                        )
        # - add messages to subject_row (there is only 1 subject_row
                    if updated_rows:
                        row = updated_rows[0]
                        if row:
                            # TODO fix it or remove
                            # - add error_list to updated_rows[0]
                            if error_list:
                                updated_rows[0]['error'] = error_list
                            if is_created:
                                updated_rows[0]['created'] = True

                        update_wrap['updated_subject_rows'] = updated_rows

                if logging_on:
                    logger.debug('..... messages: ' + str(messages))
                    logger.debug('..... error_list: ' + str(error_list))
                if len(messages):
                    update_wrap['messages'] = messages
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of SubjectUploadView



##########################
@method_decorator([login_required], name='dispatch')
class SubjecttypebaseUploadView(View):  # PR2021-06-29

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= SubjecttypebaseUploadView ============= ')

        # error_list is attached to updated row, messages is attached to update_wrap
        messages = []
        update_wrap = {}

# - get permit
        has_permit = get_permit_crud_page_subject(request)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload')
            if upload_json:
                # upload_dict = {'mapid': 'subjecttypebase_4', 'sjtbase_pk': 4, 'abbrev': 'w'}
                # upload_dict{'create': True, 'code': 'a', 'name': 'a', 'sequence': 3, 'abbrev': '2'}
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))

# - get  variables
                sjtpbase_pk = upload_dict.get('sjtpbase_pk')
                is_create = upload_dict.get('create', False)
                is_delete = upload_dict.get('delete', False)

                updated_rows = []
                error_list = []
                is_created = False

# ++++ Create new subjecttypebase:
                if is_create:
                    subjecttypebase = create_subjecttypebase(upload_dict, messages, request)
                    if subjecttypebase:
                        is_created = True
                else:

# +++  get existing subjecttypebase
                    subjecttypebase = sbj_mod.Subjecttypebase.objects.get_or_none(
                        id=sjtpbase_pk
                    )
                if logging_on:
                    logger.debug('subjecttypebase: ' + str(subjecttypebase))

                if subjecttypebase:
# ++++ Delete subjecttype
                    if is_delete:
                        deleted_ok = delete_subjecttypebase(subjecttypebase, updated_rows, messages, request)
                        if deleted_ok:
                            subjecttypebase = None

# +++ Update subjecttype
                    elif not is_create:
                        update_subjecttypebase_instance(subjecttypebase, upload_dict, error_list, request)

# - create subjecttype_rows
                    if subjecttypebase:
                        updated_rows = create_subjecttypebase_rows(
                            sjtbase_pk=subjecttypebase.pk
                        )

    # - add error_list to subject_row (there is only 1 subject_row, or none
                    # Note: error_list is attached to updated row, messages is attached to update_wrap
                    # key 'field' is needed to restore old value when updating item
                    # 'messages' is needed when cerating goes wrong, then there is no item
                    # 'created' is needed to add item to data_rows and make tblRow green
                    if updated_rows:
                        if error_list:
                            updated_rows[0]['error'] = error_list
                        if is_created:
                            updated_rows[0]['created'] = True
                update_wrap['updated_subjecttypebase_rows'] = updated_rows

        if len(messages):
            update_wrap['messages'] = messages
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of SubjecttypebaseUploadView


def create_subjecttypebase(upload_dict, error_list, request):
    # --- create subjecttype # PR2021-06-29
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_subjecttypebase ----- ')

    msg_header = _('Create base character')

    code = upload_dict.get ('code')
    name = upload_dict.get ('name')
    abbrev = upload_dict.get ('abbrev')
    sequence = upload_dict.get ('sequence')
    if logging_on:
        logger.debug('name: ' + str(name))


    msg_list = []
    subjecttypebase = None

# - validate code and name. Function checks null, max_len, exists
    msg_html = av.validate_notblank_maxlength(code, c.MAX_LENGTH_04 , _('The code'))
    if msg_html:
        msg_list.append(msg_html)
    msg_html = av.validate_notblank_maxlength(name, c.MAX_LENGTH_NAME, _('The name'))
    if msg_html:
        msg_list.append(msg_html)
    msg_html = av.validate_notblank_maxlength(abbrev, c.MAX_LENGTH_20, _('The abbreviation'))
    if msg_html:
        msg_list.append(msg_html)
    msg_html = av.validate_notblank_maxlength(sequence, None, _('The sequence'))
    if msg_html:
        msg_list.append(msg_html)

# - check if subjecttypebase code, name, abbrev already exists
    msg_html = av.validate_subjecttypebase_code_name_abbrev_exists('code', code)
    if msg_html:
        msg_list.append(msg_html)
    msg_html = av.validate_subjecttypebase_code_name_abbrev_exists('name', name)
    if msg_html:
        msg_list.append(msg_html)
    msg_html = av.validate_subjecttypebase_code_name_abbrev_exists('abbrev', abbrev)
    if msg_html:
        msg_list.append(msg_html)
# - create and save subjecttype
    if len(msg_list) > 0:
        msg_html = '<br>'.join(msg_list)
        error_list.append({'header': str(msg_header), 'class': "border_bg_invalid", 'msg_html': msg_html})
    else:
        try:
            # Don't create base record. Only use the default subjecttypebase records
            subjecttypebase = sbj_mod.Subjecttypebase(
                code=code,
                name=name,
                abbrev=abbrev,
                sequence=sequence
            )
            subjecttypebase.save()

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            caption = _('Base character')
            msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                        str(_("%(cpt)s '%(val)s' could not be created.") % {'cpt': caption, 'val': name})))
            error_list.append({'header': str(msg_header), 'class': 'border_bg_invalid', 'msg_html': msg_html})

    if logging_on:
        logger.debug('subjecttypebase: ' + str(subjecttypebase))
        logger.debug('error_list: ' + str(error_list))

    return subjecttypebase
# - end of create_subjecttypebase


def delete_subjecttypebase(subjecttypebase, subjecttypebase_rows, messages, request):
    # --- delete subjecttype # PR2021-06-29
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_subjecttypebase ----- ')
        logger.debug('subjecttypebase: ' + str(subjecttypebase))
    # this dict will be sent back to the client when row is deleted
    subjecttypebase_row = {'pk': subjecttypebase.pk,
                       'mapid': 'subjecttypebase_' + str(subjecttypebase.pk),
                       'deleted': True}

    this_txt = _("Base character '%(tbl)s'") % {'tbl': subjecttypebase.name}
    header_txt = _("Delete base character")

# check if there are students with subjects with this subjecttypebase
    students_with_this_subjecttypebase_exist = stud_mod.Studentsubject.objects.filter(
        schemeitem__subjecttype__base=subjecttypebase
    ).exists()

    if logging_on:
        logger.debug('students_with_this_subjecttypebase_exist: ' + str(students_with_this_subjecttypebase_exist))

    if students_with_this_subjecttypebase_exist:
        deleted_ok = False
        msg_html = ''.join((str(_('There are candidates with subjects with this base character.')), '<br>',
                            str(_("%(cpt)s could not be deleted.") % {'cpt': this_txt})))
        msg_dict = {'class': 'border_bg_invalid', 'header': header_txt, 'msg_html': msg_html}
        messages.append(msg_dict)

    else:
        err_list = []  # TODO
        deleted_ok = sch_mod.delete_instance(subjecttypebase, messages, err_list, request, this_txt, header_txt)

    if deleted_ok:
   # - add deleted_row to subjecttypebase_rows
        subjecttypebase_rows.append(subjecttypebase_row)

    if logging_on:
        logger.debug('subjecttypebase_rows' + str(subjecttypebase_rows))
        logger.debug('messages' + str(messages))

    return deleted_ok
# - end of delete_subjecttypebase


def update_subjecttypebase_instance(instance, upload_dict, error_list, request):
    # --- update existing and new instance PR2021-06-29
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_subjecttypebase_instance -----')
        logger.debug('upload_dict: ' + str(upload_dict))

    if instance:
        save_changes = False

        msg_header = _('Update base character')

        for field, new_value in upload_dict.items():

            if logging_on:
                logger.debug('field: ' + str(field))
                logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))

# - save changes in field 'code'
            if field in ('code', 'name', 'abbrev'):
                saved_value = getattr(instance, field)
                if new_value != saved_value:
    # - validate abbrev checks null, max_len, exists
                    caption = _('Code') if field == 'code' else _('Abbreviation') if field == 'abbrev' else _('Name')
                    max_length = c.MAX_LENGTH_04 if field == 'code' else c.MAX_LENGTH_20 if field == 'abbrev' else c.MAX_LENGTH_NAME
                    msg_html = av.validate_notblank_maxlength(new_value, max_length, caption)
                    if msg_html is None:
                        msg_html = av.validate_subjecttypebase_code_name_abbrev_exists(field, new_value, instance)
                    if msg_html:
                        # add 'field' in error_list, to put old value back in field
                        # error_list will show mod_messages in RefreshDatarowItem
                        error_list.append({'field': field, 'header': msg_header, 'class': 'border_bg_warning', 'msg_html': msg_html})
                    else:
                        # - save field if changed and no_error
                        setattr(instance, field, new_value)
                        save_changes = True

            elif field == 'sequence':
                msg_html = None
                new_value_int = None

                if new_value:
    # - check if value is positive whole number
                    if not new_value.isdecimal():
                        msg_html = str(_("'%(val)s' is not a valid number.") % {'val': new_value})
                    else:
                        new_value_int = int(new_value)

                if msg_html:
                    # add 'field' in error_list, to put old value back in field
                    # error_list will show mod_messages in RefreshDatarowItem
                    error_list.append({'field': field,'header': msg_header,'class': 'border_bg_warning', 'msg_html': msg_html})
                else:
                    # -note: value can be None
                    saved_value = getattr(instance, field)
                    if new_value_int != saved_value:
                        setattr(instance, field, new_value_int)
                        save_changes = True
# --- end of for loop ---

# +++++ save changes
        if save_changes:
            try:
                instance.save()
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred: ')), '<br><i>', str(e), '</i><br>',
                                    str(_('The changes have not been saved.'))))
                error_list.append({'header': msg_header, 'class': 'border_bg_invalid', 'msg_html': msg_html})
            else:
                pass
# also update modified in scheme, otherwise it is difficult to find out if scheme has been changed
                # awpr_logs.save_to_log(instance, 'u', request)

# - end of update_subjecttypebase_instance



##########################
@method_decorator([login_required], name='dispatch')
class SubjecttypeUploadView(View):  # PR2021-06-23

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= SubjecttypeUploadView ============= ')

        # error_list is attached to updated row, messages is attached to update_wrap
        messages = []
        update_wrap = {}

# - get permit
        has_permit = get_permit_crud_page_subject(request)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                # upload_dict{'scheme_pk': 177,
                #       'sjtp_list': [{'sjtpbase_pk': 5, 'scheme_pk': 177, 'create': True}]}
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))

                msg_header = _('Update character')

# - get selected examyear from Usersetting
                examyear = get_sel_examyear(msg_header, messages, request)

# - exit when no examyear or examyear is locked
                # note: subjects may be changed before publishing, therefore don't exit when examyear.published = False
                if examyear:

# - get scheme instance
                    scheme_pk = upload_dict.get('scheme_pk')
                    scheme = get_scheme_instance(examyear, scheme_pk, messages, msg_header)
                    if logging_on:
                        logger.debug('scheme_pk: ' + str(scheme_pk))
                        logger.debug('scheme:    ' + str(scheme))

                    if scheme:
                        updated_rows = []

# +++++++++++ update subjecttypes of scheme from sjtp_list
                        sjtp_list = upload_dict.get('sjtp_list')
                        if sjtp_list:
                            update_sjtp_list(examyear, scheme, sjtp_list, updated_rows, messages, request)
                        else:
# +++++++++++ update single sjtp
    # - get  variables
                            subjecttype_pk = upload_dict.get('subjecttype_pk')
                            is_delete = upload_dict.get('delete', False)

# if upload_dict does not have sjtp_list: it is single sjtp update - create, delete or update changes

# ++++ Create new subjecttype:
            # is done in sjtp_list
                            error_list = []

# +++  get existing subjecttype
                            subjecttype = sbj_mod.Subjecttype.objects.get_or_none(
                                id=subjecttype_pk,
                                scheme=scheme
                            )
                            if logging_on:
                                logger.debug(' subjecttype: ' + str(subjecttype))
                                logger.debug(' is_delete: ' + str(is_delete))

                            if subjecttype:
# ++++ Delete subjecttype
                                if is_delete:
                                    # delete_subjecttype will set subjecttype to None if deleted_ok
                                    deleted_row = delete_subjecttype(subjecttype, messages, request)
                                    # deleted_row has value when deleted = OK, will be returned to client
                                    if deleted_row:
                                        updated_rows.append(deleted_row)

# +++ Update subjecttype
                                else:
                                    update_subjecttype_instance(subjecttype, scheme, upload_dict, error_list, request)
            # - create subjecttype_rows
                                    updated_rows = create_subjecttype_rows(
                                        examyear=examyear,
                                        sjtp_pk=subjecttype.pk
                                    )

            # - add error_list to subject_row (there is only 1 subject_row, or none
                            # Note: error_list is attached to updated row, messages is attached to update_wrap
                            if error_list and updated_rows:
                                row = updated_rows[0]
                                if row:
                                    if error_list:
                                         row['error'] = error_list

                        update_wrap['updated_subjecttype_rows'] = updated_rows
        if len(messages):
            update_wrap['messages'] = messages
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of SubjecttypeUploadView

##########################

@method_decorator([login_required], name='dispatch')
class SchemeUploadView(View):  # PR2021-06-27

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= SchemeUploadView ============= ')

# error_list is attached to updated row, messages is attached to update_wrap
        msg_dictlist = []
        updated_fields = []
        update_wrap = {}

# - get permit
        has_permit = get_permit_crud_page_subject(request)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload')
            if upload_json:
                upload_dict = json.loads(upload_json)

                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))

# - get  variables
                scheme_pk = upload_dict.get('scheme_pk')

                updated_rows = []
                error_list = []

                msg_header = _('Update subject scheme')

# - get selected examyear from Usersetting
                examyear = get_sel_examyear(msg_header, msg_dictlist, request)

# - exit when no examyear or examyear is locked
                # note: subjects may be changed before publishing, therefore don't exit when examyear.published = False
                if examyear:

# ++++ Create new scheme
                # not in use

# +++  get existing scheme
                    scheme = get_scheme_instance(examyear, scheme_pk, msg_dictlist, msg_header)
                    if logging_on:
                        logger.debug('scheme: ' + str(scheme))

                    if scheme:
# ++++ Delete scheme
                # not in use
# +++ Update scheme
                        update_scheme_instance(scheme, examyear, upload_dict, updated_rows, error_list, request)

# - create scheme_rows
                        updated_rows = create_scheme_rows(
                            examyear=examyear,
                            scheme_pk=scheme.pk
                        )

                        # - add error_list to subject_row (there is only 1 subject_row, or none
                        # Note: error_list is attached to updated row, msg_dictlist is attached to update_wrap
                        # key 'field' is needed to restore old value when updating item
                        # 'msg_dictlist' is needed when cerating goes wrong, then there is no item
                        # 'created' is needed to add item to data_rows and make tblRow green
                        if updated_rows:
                            if error_list:
                                updated_rows[0]['error'] = error_list

                update_wrap['updated_scheme_rows'] = updated_rows

            # - add msg_dictlist to update_wrap, if any
                if len(msg_dictlist):
                    update_wrap['messages'] = msg_dictlist
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of SchemeUploadView


##########################

@method_decorator([login_required], name='dispatch')
class SchemeitemUploadView(View):  # PR2021-06-25

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= SchemeitemUploadView ============= ')

        update_wrap = {}

# - get permit
        has_permit = get_permit_crud_page_subject(request)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                # upload_dict{'scheme_pk': 177, 'si_list': [{'subj_pk': 755, 'sjtp_pk': 200, 'create': True}, {'subj_pk': 759, 'sjtp_pk': 202, 'create': True}]}

                messages = []

# - get  variables
                message_header = _('Update subject scheme')

                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))

                error_list = []

# - get selected examyear from Usersetting
                examyear = get_sel_examyear(message_header, messages, request)

# - exit when no examyear or examyear is locked
                # note: subjects may be changed before publishing, therefore don't exit when examyear.published = False
                if examyear:

# - get scheme instance
                    scheme_pk = upload_dict.get('scheme_pk')
                    scheme = get_scheme_instance(examyear, scheme_pk, messages, message_header)
                    if scheme:
                        updated_rows = []

# +++ update subjects of scheme from si_list
                        si_list = upload_dict.get('si_list')
                        if si_list:
                            update_si_list(examyear, scheme, si_list, updated_rows, messages, error_list, request)

# +++ if upload_dict does not have si_list: it is single schemeitem update
                        else:

# +++ update value of a single schemeitem
                            si_pk = upload_dict.get('si_pk')
                            schemeitem = get_schemeitem_instance(scheme, si_pk, logging_on)
                            if schemeitem:
                                update_schemeitem_instance(schemeitem, examyear, upload_dict, updated_rows, error_list, request)
       # - create schemeitem_rows
                                updated_rows = create_schemeitem_rows(
                                    examyear=examyear,
                                    schemeitem_pk=schemeitem.pk
                                )
                        update_wrap['updated_schemeitem_rows'] = updated_rows

            # - add messages to update_wrap, if any
                if len(messages):
                    update_wrap['messages'] = messages
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of SchemeitemUploadView


def get_permit_crud_page_subject(request):
    # --- get crud permit for page subject # PR2021-06-26
    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug(' ----- get_permit_crud_page_subject ----- ')

    has_permit = False
    if request.user and request.user.country:
        permit_list = request.user.permit_list('page_subject')
        if permit_list:
            has_permit = 'permit_crud' in permit_list
        if logging_on:
            logger.debug('permit_list: ' + str(permit_list))
            logger.debug('has_permit: ' + str(has_permit))

    return has_permit


def get_sel_examyear(message_header, msg_dictlist, request):
    # --- get selected examyear from usersetting # PR2021-06-26
    # - get selected examyear from Usersetting
    # return None when examyear is locked, give msg_err
    # function is only used for updating subjects etx
    # in SchemeUploadView, SchemeitemUploadView and SubjecttypeUploadView
    selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
    selected_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
    examyear = None
    if selected_examyear_pk:
        examyear = sch_mod.Examyear.objects.get_or_none(
            id=selected_examyear_pk,
            country=request.user.country
        )

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_sel_examyear ----- ')
        logger.debug('examyear: ' + str(examyear))

    # - exit when no examyear or examyear is locked
    # note: subjects may be changed before publishing, therefore don't exit when examyear.published = False
    if examyear is None:
        msg_dictlist.append({'class': "border_bg_warning",
                         'header': str(message_header),
                         'msg_html': str(_('No exam year selected'))})
    elif examyear.locked:
        msg_dictlist.append({'class': "border_bg_warning",
                         'header': str(message_header),
                         'msg_html': str(_("Exam year %(exyr)s is locked.") % {'exyr': str(examyear.code)})})
        examyear = None

    return examyear
# - end of get_sel_examyear


def get_scheme_instance(examyear, scheme_pk, error_list, msg_header):
    # --- get scheme instance # PR2021-06-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_scheme_instance ----- ')
        logger.debug('examyear: ' + str(examyear))
        logger.debug('scheme_pk: ' + str(scheme_pk))

    scheme = None
    if scheme_pk:
        scheme = sbj_mod.Scheme.objects.get_or_none(
            id=scheme_pk,
            department__examyear=examyear
        )
    if logging_on:
        logger.debug('scheme: ' + str(scheme))

    if scheme is None:
        error_list.append({'header': str(msg_header),
                           'class': "border_bg_invalid",
                           'msg_html': str(_('Subject scheme not found.'))})
    return scheme


def get_schemeitem_instance(scheme, si_pk, logging_on):
    # --- get schemeitem instance # PR2021-06-26
    schemeitem = None
    if si_pk:
        schemeitem = sbj_mod.Schemeitem.objects.get_or_none(
            id=si_pk,
            scheme=scheme
        )
    return schemeitem


def get_subjecttypebase_instance(sjtpbase_pk, error_list, message_header, logging_on, request):
    # --- get subjecttypebase instance # PR2021-06-26
    subjecttypebase = None

    if sjtpbase_pk:
        subjecttypebase = sbj_mod.Subjecttypebase.objects.get_or_none(
            id=sjtpbase_pk
        )

    if logging_on:
        logger.debug('subjecttypebase: ' + str(subjecttypebase))

    if subjecttypebase is None:
        error_list.append({'header': str(message_header),
                           'class': "border_bg_invalid",
                           'msg_html': str(_('Base subject type not found.'))})

    return subjecttypebase


#############################


# ========  EXAMS  =====================================
@method_decorator([login_required], name='dispatch')
class ExamListView(View):  # PR2021-04-04

    def get(self, request):
        logging_on = False  # s.LOGGING_ON

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get sel_schoolbase from settings / request when role is insp, admin or system, from req_user otherwise
        sel_schoolbase, sel_schoolbase_saveNIU = af.get_sel_schoolbase_instance(request)

# requsr_same_school = True when selected school is same as requsr_school PR2021-04-27
        # used on entering grades. Users can only enter grades of their own school. Syst, Adm and Insp, Comm can not neter grades
        requsr_same_school = (request.user.role == c.ROLE_008_SCHOOL and request.user.schoolbase.pk == sel_schoolbase.pk)

# - set headerbar parameters
        page = 'page_exams'
        # show school only when requsr_same_school
        param = {'display_school': requsr_same_school, 'display_department': True}
        params = awpr_menu.get_headerbar_param(request, page, param)

        if logging_on:
            logger.debug('  =====  ExamListView ===== ')
            logger.debug('params: ' + str(params))

# - save this page in Usersetting, so at next login this page will open.  Used in LoggedIn
        #         # PR2021-06-22 moved to get_headerbar_param

        return render(request, 'exams.html', params)
# - end of ExamListView

# ============= ExamUploadView ============= PR2021-04-04

@method_decorator([login_required], name='dispatch')
class ExamUploadView(View):

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamUploadView ============= ')

        req_usr = request.user
        update_wrap = {}
        err_html = ''

# - reset language
        user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

# - add edit permit
        has_permit = False
        if req_usr and req_usr.country:
            permit_list = req_usr.permit_list('page_exams')
            if permit_list:
                has_permit = 'permit_crud' in permit_list
            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

        if not has_permit:
            err_html = str(_("You don't have permission to perform this action."))
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))

                error_list = []
                append_dict = {}
                deleted_row = None

# - get variables from upload_dict
                # upload_dict{'table': 'exam', 'mode': 'update', 'field': 'authby', 'auth_index': 2, 'auth_bool_at_index': True, 'exam_pk': 138}

                # don't get it from usersettings, get it from upload_dict instead
                mode = upload_dict.get('mode')
                examyear_pk = upload_dict.get('examyear_pk')
                depbase_pk = upload_dict.get('depbase_pk')
                lvlbase_pk = upload_dict.get('lvlbase_pk')

                exam_pk = upload_dict.get('exam_pk')
                # PR2022-02-20 debug: exam uses subject_pk, not subjbase_pk
                subject_pk = upload_dict.get('subject_pk')

# - check if examyear exists and equals selected examyear from Usersetting
                selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                selected_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                examyear = None
                if examyear_pk == selected_examyear_pk:
                    examyear = sch_mod.Examyear.objects.get_or_none(
                        id=examyear_pk,
                        country=req_usr.country
                    )

                # note: exams can be changed before publishing examyear, therefore don't filter on examyear.published
                if examyear and not examyear.locked:

# - get subject
                    subject = subj_mod.Subject.objects.get_or_none(
                        id=subject_pk,
                        examyear=examyear
                    )
                    if logging_on:
                        logger.debug('subject:     ' + str(subject))

# +++++ Create new instance if is_create:
                    if mode == 'create':
                        department = sch_mod.Department.objects.get_or_none(
                            base_id=depbase_pk,
                            examyear=examyear
                        )
                        level = subj_mod.Level.objects.get_or_none(
                            base_id=lvlbase_pk,
                            examyear=examyear
                        )
                        if logging_on:
                            logger.debug('department:     ' + str(department))
                            logger.debug('level:     ' + str(level))
                        examperiod_int = upload_dict.get('examperiod')
                        ete_exam = True
                        exam, msg_err = create_exam_instance(subject, department, level, examperiod_int, ete_exam, request)

                        if exam:
                            append_dict['created'] = True
                        elif msg_err:
                            append_dict['err_create'] = msg_err

                        if logging_on:
                            logger.debug('created exam: ' + str(exam))
                            logger.debug('append_dict: ' + str(append_dict))

                    else:
# - else: get existing exam instance
                        exam = subj_mod.Exam.objects.get_or_none(
                            id=exam_pk,
                            subject=subject
                        )
                    if logging_on:
                        logger.debug('exam: ' + str(exam))

                    if exam:
# +++++ Delete instance if is_delete
                        if mode == 'delete':
                            deleted_row = delete_exam_instance(exam, error_list, request)
                        else:

# +++++ Update instance, also when it is created, not when is_delete
                            update_exam_instance(exam, upload_dict, error_list, examyear, request)

    # 6. create list of updated exam
                    if deleted_row:
                        updated_exam_rows = [deleted_row]
                    else:
                        updated_exam_rows = create_exam_rows(
                            req_usr=req_usr,
                            sel_examyear_pk=examyear.pk,
                            sel_depbase_pk=depbase_pk,
                            append_dict=append_dict,
                            exam_pk_list=[exam.pk]
                        )

                    if updated_exam_rows:
                        update_wrap['updated_exam_rows'] = updated_exam_rows
        if err_html:
            update_wrap['err_html'] = err_html
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamUploadView

@method_decorator([login_required], name='dispatch')
class ExamApproveOrPublishView(View):  # PR2021-04-04 PR2022-01-31 PR2022-02-23

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamApproveOrPublishView ============= ')

# function sets auth and publish of exam records - submitting grade_exams happens in ExamApproveOrSubmitGradeExamView
        update_wrap = {}
        requsr_auth = None
        msg_html = None

# - get permit
        # <PERMIT>
        # only users with role = admin and perm_approve_exam or publish_exam can approve or submit
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated

        has_permit_approve, has_permit_publish = False, False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.is_role_admin and req_usr.schoolbase:

            permit_list = req_usr.permit_list('page_exams')
            if permit_list:
                requsr_usergroup_list = req_usr.usergroup_list
                # msg_err is made on client side. Here: just skip if user has no or multiple functions

                is_auth1 = 'auth1' in requsr_usergroup_list
                is_auth2 = 'auth2' in requsr_usergroup_list
                if is_auth1 + is_auth2 == 1:
                    if is_auth1:
                        requsr_auth = 'auth1'
                    elif is_auth2:
                        requsr_auth = 'auth2'
                if requsr_auth:
                    has_permit_approve = 'permit_approve_exam' in permit_list
                    has_permit_publish = 'permit_publish_exam' in permit_list

# - check if user is admin or school
                    is_role_admin = req_usr.is_role_admin
                    is_role_same_school = req_usr.is_role_school
                if logging_on:
                    logger.debug('permit_list: ' + str(permit_list))

        if has_permit_approve or has_permit_publish:

# -  get user_lang
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

# ----- get selected examyear and department from usersettings
                msg_list = []
                sel_examyear, sel_department, sel_schoolNIU, sel_examperiod = \
                    dl.get_selected_examyear_examperiod_dep_school_from_usersetting(request)
                dl.message_examyear_missing_notpublished_locked(sel_examyear, msg_list)

                if msg_list:
                    msg_html = ''.join(("<div class='p-2 border_bg_warning'>", '<br>'.join(msg_list), '</>'))
                else:
# - get selected mode. Modes are 'approve_test', 'approve_save', 'approve_reset', 'submit_test' 'submit_save' , 'publish_test' 'publish_submit'
                    mode = upload_dict.get('mode')
                    is_approve = True if 'approve_' in mode else False
                    is_submit = True if 'submit_' in mode else False
                    is_reset = True if '_reset' in mode else False
                    is_test = True if '_test' in mode else False

# - check if user is admin or same_school
                    is_role_admin = req_usr.is_role_admin

                    if logging_on:
                        logger.debug('upload_dict' + str(upload_dict))
                        logger.debug('mode: ' + str(mode))
                        logger.debug('is_approve: ' + str(is_approve))
                        logger.debug('is_submit: ' + str(is_submit))
                        logger.debug('is_test: ' + str(is_test))

# - when mode = submit_submit: check verificationcode.
                    verification_is_ok = True
                    if (is_submit) and not is_test:
                        verification_is_ok, verif_msg_html = check_verifcode_local(upload_dict, request)
                        if verif_msg_html:
                            msg_html = verif_msg_html
                        if verification_is_ok:
                            update_wrap['verification_is_ok'] = True

                    if verification_is_ok:
                        # also filter on sel_lvlbase_pk, sel_subject_pk when is_submit
                        sel_lvlbase_pk, sel_subject_pk = None, None
                        selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                        if selected_dict:
                            sel_lvlbase_pk = selected_dict.get(c.KEY_SEL_LVLBASE_PK)
                            sel_subject_pk = selected_dict.get(c.KEY_SEL_SUBJECT_PK)
                        if logging_on:
                            logger.debug('selected_dict: ' + str(selected_dict))

# +++ get selected exam_rows
                        sel_examperiod = sel_examperiod if sel_examperiod in (1, 2) else None
                        # exclude published rows??
                        # when published_id has value it means that admin has published the exam, so it is visible for the schools.
                        # submitting the exams by schools happens with grade.ce_exam_published_id, because answers are stored in grade

                        crit = Q(subject__examyear=sel_examyear) & \
                               Q(department=sel_department)
                        # examperiod=12 means both first and second examperiod are selected
                        if sel_examperiod in (1, 2):
                            crit.add(Q(examperiod=sel_examperiod) | Q(examperiod=12), crit.connector)

                        if sel_lvlbase_pk:
                            crit.add(Q(level__base_id=sel_lvlbase_pk), crit.connector)
                        if sel_subject_pk:
                            crit.add(Q(subject_id=sel_subject_pk), crit.connector)

                        exams = subj_mod.Exam.objects.filter(crit).order_by('subject__base__code')

                        if logging_on:
                            logger.debug('sel_examperiod:  ' + str(sel_examperiod))
                            logger.debug('sel_department:  ' + str(sel_department))
                            logger.debug('sel_lvlbase_pk:   ' + str(sel_lvlbase_pk))
                            logger.debug('sel_subject_pk: ' + str(sel_subject_pk))

                            row_count = subj_mod.Exam.objects.filter(crit).count()
                            logger.debug('row_count:      ' + str(row_count))

                        updated_exam_pk_list = []
                        count_dict = {'count': 0,
                                    'already_published': 0,
                                    'has_blanks': 0,
                                    'double_approved': 0,
                                    'committed': 0,
                                    'saved': 0,
                                    'saved_error': 0,
                                    'reset': 0,
                                    'already_approved': 0,
                                    'auth_missing': 0,
                                    'test_is_ok': False,
                                    'updated_grd_count': 0
                                    }
                        if exams is not None:

# +++++ loop through exams
                            if exams:
                                for exam in exams:
                                    if is_approve:
                                        approve_exam(exam, requsr_auth, is_test, is_reset, count_dict, updated_exam_pk_list, request)

                                    elif is_submit:

        # +++ create new published_instance for each exam. Only save it when it is not a test
                                        # file_name will be added after creating exam-form
                                        published_instance = None
                                        published_instance_pk = None

                                        if not is_test:
                                            now_arr = upload_dict.get('now_arr')
                                            published_instance = create_exam_published_instance(
                                                exam=exam,
                                                now_arr=now_arr,
                                                request=request)  # PR2021-07-27
                                            if published_instance:
                                                published_instance_pk = published_instance.pk

                                            if logging_on:
                                                logger.debug('published_instance_pk' + str(published_instance_pk))

                                        publish_exam(exam, is_test, published_instance, count_dict, request)

                                # - add rows to exam_rows, to be sent back to page
                                    # to increase speed, dont create return rows but refresh page after finishing this request

                        # +++++  end of loop through  exams
                                update_wrap['approve_count_dict'] = count_dict

# - create msg_html with info of rows
                        msg_html = create_exam_approve_msg_list(count_dict, requsr_auth, is_approve, is_test)
        # get updated_rows
                        if not is_test and updated_exam_pk_list:
                            rows = create_exam_rows(
                                req_usr=req_usr,
                                sel_examyear_pk=sel_examyear.pk,
                                sel_depbase_pk=sel_department.base_id,
                                append_dict={},
                                exam_pk_list=updated_exam_pk_list)
                            if rows:
                                update_wrap['updated_exam_rows'] = rows

                            # +++++ create Ex1 form

                        if is_test:
                            committed = count_dict.get('committed', 0)
                            if committed:
                                update_wrap['test_is_ok'] = True

# - add  msg_html to update_wrap
        update_wrap['approve_msg_html'] = msg_html

        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamApproveOrPublishView


@method_decorator([login_required], name='dispatch')
class ExamApproveOrSubmitGradeExamView(View):  # PR2021-04-04 PR2022-01-31

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamApproveOrSubmitGradeExamView ============= ')

# function sets auth and publish of exam records
        update_wrap = {}
        requsr_auth = None
        msg_html = None

# - get permit
        # <PERMIT>
        # only users with role = admin and perm_approve_exam or publish_exam can approve or submit
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated

        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:

            permit_list = req_usr.permit_list('page_exams')
            if permit_list:
                requsr_usergroup_list = req_usr.usergroup_list
                # msg_err is made on client side. Here: just skip if user has no or multiple functions

                is_auth1 = 'auth1' in requsr_usergroup_list
                is_auth2 = 'auth2' in requsr_usergroup_list
                if is_auth1 + is_auth2 == 1:
                    if is_auth1:
                        requsr_auth = 'auth1'
                    elif is_auth2:
                        requsr_auth = 'auth2'
                if requsr_auth:
                    has_permit = 'permit_approve_exam' in permit_list

# - check if user is admin or school
                    is_role_admin = req_usr.is_role_admin
                    is_role_same_school = req_usr.is_role_school
                if logging_on:
                    logger.debug('permit_list: ' + str(permit_list))
                    logger.debug('has_permit: ' + str(has_permit))

        if has_permit:

# -  get user_lang
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

# ----- get selected examyear and department from usersettings. Sel_school will be retrieved from req_usr.schoolbase
                msg_list = []
                sel_examyear, sel_department, sel_schoolNIU, sel_examperiod = \
                    dl.get_selected_examyear_examperiod_dep_school_from_usersetting(request)
                dl.message_examyear_missing_notpublished_locked(sel_examyear, msg_list)

                if msg_list:
                    msg_html = ''.join(("<div class='p-2 border_bg_warning'>", '<br>'.join(msg_list), '</>'))
                else:
# - get selected mode. Modes are 'approve_test', 'approve_save', 'approve_reset', 'submit_test' 'submit_save' , 'publish_test' 'publish_submit'
                    mode = upload_dict.get('mode')
                    is_approve = True if 'approve_' in mode else False
                    is_submit = True if 'submit_' in mode else False
                    is_reset = True if '_reset' in mode else False
                    is_test = True if '_test' in mode else False

                    sel_school = sch_mod.School.objects.get_or_none(
                        examyear=sel_examyear,
                        base=req_usr.schoolbase
                    )


# - check if user is admin or same_school
                    is_role_admin = req_usr.is_role_admin
                    is_role_same_school = req_usr.is_role_school and sel_school and req_usr.schoolbase and req_usr.schoolbase.pk == sel_school.base_id

                    if logging_on:
                        logger.debug('upload_dict' + str(upload_dict))
                        logger.debug('mode: ' + str(mode))
                        logger.debug('is_approve: ' + str(is_approve))
                        logger.debug('is_test: ' + str(is_test))
                        logger.debug('sel_examyear: ' + str(sel_examyear))
                        logger.debug('sel_department: ' + str(sel_department))
                        logger.debug('sel_school: ' + str(sel_school))
                        logger.debug('sel_examperiod: ' + str(sel_examperiod))
                        logger.debug('req_usr.schoolbase: ' + str(req_usr.schoolbase))
                        logger.debug('is_role_admin: ' + str(is_role_admin))
                        logger.debug('is_role_same_school: ' + str(is_role_same_school))

# - when mode = submit_submit: check verificationcode.
                    verification_is_ok = True
                    if (is_submit) and not is_test:
                        verification_is_ok, verif_msg_html = check_verifcode_local(upload_dict, request)
                        if verif_msg_html:
                            msg_html = verif_msg_html
                        if verification_is_ok:
                            update_wrap['verification_is_ok'] = True

                    if verification_is_ok:
                        # also filter on sel_lvlbase_pk, sel_subject_pk when is_submit
                        sel_lvlbase_pk, sel_subject_pk = None, None
                        selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                        if selected_dict:
                            sel_lvlbase_pk = selected_dict.get(c.KEY_SEL_LVLBASE_PK)
                            sel_subject_pk = selected_dict.get(c.KEY_SEL_SUBJECT_PK)
                        if logging_on:
                            logger.debug('selected_dict: ' + str(selected_dict))

# +++ get selected grade_exam_rows
                        sel_examperiod = sel_examperiod if sel_examperiod in (1, 2) else None
                        # exclude published rows??
                        # when published_id has value it means that admin has published the exam, so it is visible for the schools.
                        # submitting the exams by schools happens with grade.ce_exam_published_id, because answers are stored in grade

                        crit = Q(subject__examyear=sel_examyear) & \
                               Q(department=sel_department)

                        if sel_examperiod in (1, 2):
                            crit.add(Q(examperiod=sel_examperiod) | Q(examperiod=12), crit.connector)

                        if sel_lvlbase_pk:
                            crit.add(Q(level__base_id=sel_lvlbase_pk), crit.connector)
                        if sel_subject_pk:
                            crit.add(Q(subject_id=sel_subject_pk), crit.connector)

                        exams = subj_mod.Exam.objects.filter(crit).order_by('subject__base__code')

                        if logging_on:
                            logger.debug('sel_examperiod:  ' + str(sel_examperiod))
                            logger.debug('sel_department:  ' + str(sel_department))
                            logger.debug('sel_lvlbase_pk:   ' + str(sel_lvlbase_pk))
                            logger.debug('sel_subject_pk: ' + str(sel_subject_pk))

                            row_count = subj_mod.Exam.objects.filter(crit).count()
                            logger.debug('row_count:      ' + str(row_count))

                        updated_exam_pk_list = []
                        count_dict = {'count': 0,
                                    'already_published': 0,
                                    'has_blanks': 0,
                                    'double_approved': 0,
                                    'committed': 0,
                                    'saved': 0,
                                    'saved_error': 0,
                                    'reset': 0,
                                    'already_approved': 0,
                                    'auth_missing': 0,
                                    'test_is_ok': False,
                                    'updated_grd_count': 0
                                    }
                        if exams is not None:

                            # +++ create new published_instance. Only save it when it is not a test
                            # file_name will be added after creating Ex-form
                            published_instance = None
                            published_instance_pk = None
                            if is_submit and not is_test:
                                now_arr = upload_dict.get('now_arr')
                                published_instance = XXXcreate_exam_published_instance(
                                    sel_school=sel_school,
                                    sel_department=sel_department,
                                    sel_examperiod=1,
                                    now_arr=now_arr,
                                    request=request)  # PR2021-07-27
                                if published_instance:
                                    published_instance_pk = published_instance.pk

                                if logging_on:
                                    logger.debug('published_instance_pk' + str(published_instance_pk))

# +++++ loop through exams
                            if exams:
                                for exam in exams:
                                    if is_approve:
                                        approve_exam(exam, requsr_auth, is_test, is_reset, count_dict, updated_exam_pk_list, request)
                                    elif is_submit:
                                        submit_grade_exam(exam, is_test, published_instance, count_dict, request)

                                # - add rows to exam_rows, to be sent back to page
                                    # to increase speed, dont create return rows but refresh page after finishing this request

                        # +++++  end of loop through  exams
                                update_wrap['approve_count_dict'] = count_dict

# - create msg_html with info of rows
                        msg_html = create_exam_approve_msg_list(count_dict, requsr_auth, is_approve, is_test)
        # get updated_rows
                        if not is_test and updated_exam_pk_list:
                            rows = create_exam_rows(
                                req_usr=req_usr,
                                sel_examyear_pk=sel_examyear.pk,
                                sel_depbase_pk=sel_department.base_id,
                                append_dict={},
                                exam_pk_list=updated_exam_pk_list)
                            if rows:
                                update_wrap['updated_exam_rows'] = rows

                            # +++++ create Ex1 form

                        if is_test:
                            committed = count_dict.get('committed', 0)
                            if committed:
                                update_wrap['test_is_ok'] = True

# - add  msg_html to update_wrap
        update_wrap['approve_msg_html'] = msg_html

        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamApproveOrSubmitGradeExamView


def get_approve_grade_exam_rows():  #PR2022-02-24
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  ----- get_approve_grade_exam_rows -----')
        logger.debug('count_dict: ' + str(count_dict))
        logger.debug('is_test: ' + str(is_test))

    # ATTENTION: ce_exam is linked with curacao subject, while SXM students are connected with sxm subjects.
    # therefore don't link grade
    sql_list = ["SELECT grd.id, grd.examperiod,"
                # "grd.pe_exam_id, grd.pe_exam_result, grd.pe_exam_auth1by_id, grd.pe_exam_auth2by_id, grd.pe_exam_published_id, grd.pe_exam_blocked,",
                "grd.ce_exam_id, grd.ce_exam_result, grd.ce_exam_auth1by_id, grd.ce_exam_auth2by_id, grd.ce_exam_published_id, grd.ce_exam_blocked,",

                "ce_exam.id AS ceex_exam_id, ce_exam.exam_name AS ceex_name,"

                "FROM students_grade AS grd",
                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS si_subj ON (si_subj.id = si.subject_id)",

                "INNER JOIN subjects_exam AS ce_exam ON (ce_exam.id = grd.ce_exam_id)",

                "INNER JOIN subjects_subject AS exam_subj ON (subj.id = exam.subject_id)",

                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                "WHERE ey.id = %(ey_id)s::INT",
                "AND school.base_id = %(sb_id)s::INT",
                "AND dep.base_id = %(depbase_id)s::INT",
                "AND NOT grd.tobedeleted AND NOT studsubj.tobedeleted AND NOT stud.tobedeleted"
                ]

# end of get_approve_grade_exam_rows

def create_exam_approve_msg_list(count_dict, requsr_auth, is_approve, is_test, is_grade_exam=False):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  ----- create_exam_approve_msg_list -----')
        logger.debug('count_dict: ' + str(count_dict))
        logger.debug('is_test: ' + str(is_test))

    exam_count = count_dict.get('count', 0)
    committed = count_dict.get('committed', 0)
    saved = count_dict.get('saved', 0)
    saved_error = count_dict.get('saved_error', 0)
    already_published = count_dict.get('already_published', 0)
    has_blanks = count_dict.get('has_blanks', 0)
    auth_missing = count_dict.get('auth_missing', 0)
    already_approved = count_dict.get('already_approved', 0)
    double_approved = count_dict.get('double_approved', 0)

    if logging_on:
        logger.debug('.....exam_count: ' + str(exam_count))
        logger.debug('.....committed: ' + str(committed))
        logger.debug('.....already_published: ' + str(already_published))
        logger.debug('.....auth_missing: ' + str(auth_missing))
        logger.debug('.....already_approved: ' + str(already_approved))
        logger.debug('.....double_approved: ' + str(double_approved))

    def get_exam_count_text(count):
        exam_str = str(_('exam') if count == 1 else _('exams'))
        count_str = str(pgettext_lazy('geen', 'no ') if not count else count)
        return ' '.join((count_str, exam_str))

    def get_exams_are_text(count):
        return ' '.join((get_exam_count_text(count), ' ', get_are_text(count)))

    def get_exams_have_text(count):
        return ' '.join((get_exam_count_text(count), ' ', get_have_txt(count)))

    def get_are_text(count):
        return str(pgettext_lazy('singular', 'is') if  count == 1 else pgettext_lazy('plural', 'are'))

    def get_will_be_text(count):
        return str(pgettext_lazy('singular', 'will be') if  count == 1 else pgettext_lazy('plural', 'will be'))

    def get_willbe_or_are_txt(is_test, count):
        return get_will_be_text(count) if is_test else get_are_text(count)

    def get_have_txt(count):
        return str(pgettext_lazy('singular', 'has') if count == 1 else pgettext_lazy('plural', 'have'))

    def get_could_txt(count):
        return str(pgettext_lazy('singular', 'could') if count == 1 else pgettext_lazy('plural', 'could'))

    def get_have_has_been_txt(count):
        return str(pgettext_lazy('singular', 'has been') if count == 1 else pgettext_lazy('plural', 'have been'))


    show_warning_msg = False
    show_msg_first_approve_by_pres_secr = False
    if is_test:
        if is_approve:
            class_str = 'border_bg_valid' if committed else 'border_bg_invalid'
        else:
            if committed:
                if (is_test and auth_missing) or (is_test and double_approved):
                    class_str = 'border_bg_warning'
                    if is_grade_exam:
                        show_warning_msg = True
                else:
                    class_str = 'border_bg_valid'
            else:
                class_str = 'border_bg_invalid'
    else:
        if saved_error:
            class_str = 'border_bg_invalid'
        elif saved:
            class_str = 'border_bg_valid'
        else:
            class_str = 'border_bg_transpaprent'

# - create first line with 'The selection contains 4 exams'
    msg_list = ["<div class='p-2 ", class_str, "'>"]
    if is_test:
        msg_list.append(''.join(("<p class='pb-2'>",
                                 str(_("The selection contains %(val)s.") % {'val': get_exam_count_text(exam_count)}),
                                 '</p>')))

# - if any exams skipped: create lines 'The following exams will be skipped' plus the reason
    if is_test and committed < exam_count:
        msg_list.append("<p class='pb-0'>" + str(_("The following exams %(willbe)s skipped")
                                                 % {'willbe': get_willbe_or_are_txt(is_test, exam_count)}) + ':</p><ul>')
        if already_published:
            if is_grade_exam:
                msg_list.append('<li>' + str(_("%(subj)s already submitted") %
                                             {'subj': get_exams_are_text(already_published)}) + ';</li>')
            else:
                msg_list.append('<li>' + str(_("%(subj)s already published") %
                                             {'subj': get_exams_are_text(already_published)}) + ';</li>')
        if has_blanks:
            msg_list.append('<li>' + str(_("%(subj)s no questions or blank questions") %
                                         {'subj': get_exams_have_text(has_blanks)}) + ';</li>')
        if auth_missing:
            msg_list.append('<li>' + str(_("%(subj)s not fully approved") %
                                         {'subj': get_exams_are_text(auth_missing)}) + ';</li>')
            show_msg_first_approve_by_pres_secr = True
        if already_approved:
            msg_list.append('<li>' + get_exams_are_text(already_approved) + str(
                _(' already approved')) + ';</li>')
        if double_approved:
            other_function = str(_('president')) if requsr_auth == 'auth2' else str(_('secretary'))
            msg_list.append(''.join(('<li>', get_exams_are_text(double_approved),
                                     str(_(' already approved by you as ')), other_function, '.<br>',
                                     str(_("You cannot approve an exam both as president and as secretary.")),
                                     '</li>')))
        msg_list.append('</ul>')

# - line with text how many exams will be approved / submitted
    msg_list.append('<p>')
    if is_test:
        if is_approve:
            if not committed:
                msg_str = _("No exams will be approved.")
            else:
                msg_str = ' '.join((
                    get_exam_count_text(committed),
                    get_will_be_text(committed), str(_('approved.'))
                ))
        else:
            if not committed:
                if is_approve:
                    msg_str = _("No exams will be submitted.") if is_grade_exam else _("No exams will be published.")
                else:
                    msg_str = _("The exams cannot be submitted.") if is_grade_exam else _("The exams cannot be published.")
            else:
                approve_txt = str(_('approved.') if is_approve else _('submitted.') if is_grade_exam else _('published.'))
                msg_str = ' '.join((
                    get_exam_count_text(committed).capitalize(),
                    get_will_be_text(committed), approve_txt))
    else:
        subject_error_count_txt = get_exams_are_text(saved_error)

        # - line with text how many exams have been approved / submitted
        if is_approve:
            not_str = '' if saved else str(_('not')) + ' '
            msg_str = ''
            if not saved and not saved_error:
                msg_str = str(_("No exams have been approved."))
            else:
                if saved:
                    msg_str = str(_("%(exams)s %(havehasbeen)s approved.")
                                  % {'exams': get_exam_count_text(saved),
                                     'havehasbeen': get_have_has_been_txt(saved)})
                else:
                    msg_str = str(_("No exams have been approved."))
                if saved_error:
                    if msg_str:
                        msg_str += '<br>'
                    msg_str += str(
                        _("%(subj)s %(could)s not be approved because an error occurred.")
                        % {'subj': subject_error_count_txt, 'could': get_could_txt(saved_error)})

        else:
            not_str = '' if saved else str(_('not')) + ' '
            if is_grade_exam:
                msg_str = str(_("The exams have %(not)s been submitted.") % {'not': not_str})
            else:
                msg_str = str(_("The exams have %(not)s been published.") % {'not': not_str})
            if saved:
                msg_str += '<br>' + str(_("It contains %(exam)s.") % {'exam': get_exam_count_text(saved)})
    msg_list.append(str(msg_str))
    msg_list.append('</p>')

    # - warning if any exams are not fully approved
    if show_warning_msg and not is_approve:
        msg_list.append("<p class='pt-2'><b>")
        msg_list.append(str(_('WARNING')))
        msg_list.append(':</b> ')
        msg_list.append(str(_('There are exams that are not fully approved.')))
        msg_list.append(' ')

        if is_grade_exam:
            msg_list.append(str(_('They will not be submitted.')))
        else:
            msg_list.append(str(_('They will not be published.')))

        msg_list.append(' ')
        msg_list.append(str(_('Are you sure you want to continue?')))
        msg_list.append('</p>')

    # - add line 'both president and secretary must first approve all exams before you can submit the Ex form
    if show_msg_first_approve_by_pres_secr:
        if is_grade_exam:
            msg_txt = ''.join(('<p>', str(_(
                'The president and the secretary must approve the exams before you can submit them.')),
                               '</p>'))

# - line with text how many  subjects of stuidents have been linked to exams
    if not is_test and not is_approve and not is_grade_exam:
        if count_dict['updated_grd_count']:
            if count_dict['updated_grd_count'] == 1:
                msg_str = _("The exam has been linked to 1 subject of a candidate.")
            else:
                msg_str = _("The exams have been linked to %(count)s subjects of candidates."
                                  % {'count': count_dict['updated_grd_count']})
            msg_txt = ''.join(('<p>', str(msg_str), '</p>'))
            msg_list.append(msg_txt)

    msg_list.append('</div>')

    msg_html = ''.join(msg_list)
    return msg_html
# - end of create_exam_approve_msg_list


def approve_exam(exam, requsr_auth, is_test, is_reset, count_dict, updated_exam_pk_list, request):
    # PR2022-01-31
    # auth_bool_at_index is not used to set or rest value. Instead 'is_reset' is used to reset, set otherwise PR2021-03-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- approve_exam -----')
        logger.debug('requsr_auth:  ' + str(requsr_auth))
        logger.debug('is_reset:     ' + str(is_reset))

    if exam:
        req_user = request.user

        count_dict['count'] += 1

# - skip if this studsubj is already published
        is_published = True if getattr(exam, 'published') else False
        if logging_on:
            logger.debug('published:    ' + str(is_published))

        if is_published:
            count_dict['already_published'] += 1
        else:
            no_questions = False if getattr(exam, 'amount') else True
            has_blank_questions = True if getattr(exam, 'blanks') else False
            # dont skip this when is_reset
            if not is_reset and (no_questions or has_blank_questions):
                count_dict['has_blanks'] += 1
            else:
                requsr_authby_field = requsr_auth + 'by'

    # - skip if other_auth has already approved and other_auth is same as this auth. - may not approve if same auth has already approved
                auth1by = getattr(exam, 'auth1by')
                auth2by = getattr(exam, 'auth2by')
                if logging_on:
                    logger.debug('requsr_authby_field: ' + str(requsr_authby_field))
                    logger.debug('auth1by:      ' + str(auth1by))
                    logger.debug('auth2by:      ' + str(auth2by))

                save_changes = False

                has_old_authby_value = True if getattr(exam, requsr_authby_field) else False

    # - remove authby when is_reset
                if is_reset:
                    if has_old_authby_value:
                        setattr(exam, requsr_authby_field, None)
                        count_dict['reset'] += 1
                        save_changes = True
                        if exam.pk not in updated_exam_pk_list:
                            updated_exam_pk_list.append(exam.pk)
                else:

    # - skip if this exam is already approved
                    requsr_authby_field_already_approved = has_old_authby_value
                    if logging_on:
                        logger.debug('requsr_authby_field_already_approved: ' + str(requsr_authby_field_already_approved))

                    if requsr_authby_field_already_approved:
                        count_dict['already_approved'] += 1
                    else:

    # - skip if this author (like 'president') has already approved this studsubj
            # under a different permit (like 'secretary' or 'commissioner')

                        double_approved = False
                        if requsr_auth == 'auth1':
                            double_approved = True if auth2by and auth2by == req_user else False
                        elif requsr_auth == 'auth2':
                            double_approved = True if auth1by and auth1by == req_user else False

                        if double_approved:
                            count_dict['double_approved'] += 1
                        else:
                            setattr(exam, requsr_authby_field, req_user)

                            save_changes = True
                            if logging_on:
                                logger.debug('save_changes: ' + str(save_changes))

                        if logging_on:
                            logger.debug('     double_approved: ' + str(double_approved))
                            logger.debug('     requsr_authby_field_already_approved:    ' + str(requsr_authby_field_already_approved))
                            logger.debug('     auth1by:     ' + str(auth1by))
                            logger.debug('     auth2by:     ' + str(auth2by))
    # - set value of requsr_authby_field
                if save_changes:
                    if exam.pk not in updated_exam_pk_list:
                        updated_exam_pk_list.append(exam.pk)


                    if is_test:
                        count_dict['committed'] += 1
                    else:
    # - save changes
                        try:
                            exam.save(request=request)
                            count_dict['saved'] += 1
                        except Exception as e:
                            logger.error(getattr(e, 'message', str(e)))
                            count_dict['saved_error'] += 1

    if logging_on:
        logger.debug('count_dict: ' + str(count_dict))
# - end of approve_exam


def publish_exam(exam, is_test, published_instance, count_dict, request):  # PR2022-02-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- publish_exam -----')

    updated_grd_count = 0
    if exam:
        count_dict['count'] += 1

# - check if this exam is already published
        published = getattr(exam, 'published')
        if logging_on:
            logger.debug('published: ' + str(published))

        if published:
            count_dict['already_published'] += 1
        else:

# - check if this exam / examtype is approved by all auth
            auth1by = getattr(exam, 'auth1by')
            auth2by = getattr(exam, 'auth2by')
            auth_missing = auth1by is None or auth2by is None
            if logging_on:
                logger.debug('auth1by: ' + str(auth1by))
                logger.debug('auth2by: ' + str(auth2by))
                logger.debug('auth_missing: ' + str(auth_missing))
            if auth_missing:
                count_dict['auth_missing'] += 1
            else:

# - check if all auth are different
                double_approved = auth1by == auth2by
                if logging_on:
                    logger.debug('double_approved: ' + str(double_approved))
                if double_approved and not auth_missing:
                    count_dict['double_approved'] += 1
                else:
# - set value of published_instance and examtype_status field
                    if is_test:
                        count_dict['committed'] += 1
                    else:

                        update_exam_in_grades = False
                        try:
# - put published_id in field published
                            setattr(exam, 'published', published_instance)
# - save changes
                            exam.save(request=request)
                            count_dict['saved'] += 1
                            update_exam_in_grades = True
                        except Exception as e:
                            logger.error(getattr(e, 'message', str(e)))
                            count_dict['saved_error'] += 1

# --- add exam_pk to grades when published
                        if update_exam_in_grades:  # is_publish_exam and not is_test:

# - skip when there are more than 1 exam for this subject / dep / level / examperiod
                            crit = Q(subject=exam.subject) & \
                                   Q(department=exam.department)
                            if exam.examperiod in (1, 2):
                                crit.add(Q(examperiod=exam.examperiod), crit.connector)
                            else:
                                crit.add(Q(examperiod__lte=2), crit.connector)
                            if exam.level:
                                crit.add(Q(level=exam.level), crit.connector)

                # - add_published_exam_to_grades
                            count_exams = subj_mod.Exam.objects.filter(crit).count()
                            if count_exams == 1:
                                grd_count = add_published_exam_to_grades(exam)
                                if grd_count:
                                    count_dict['updated_grd_count'] += grd_count
# - end of publish_exam


def submit_grade_exam(exam, is_test, published_instance, count_dict, request):  # PR2022-02-04
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- submit_grade_exam -----')

    updated_grd_count = 0
    if exam:
        count_dict['count'] += 1

# - check if this exam is already published
        published = getattr(exam, 'published')
        if logging_on:
            logger.debug('published: ' + str(published))

        if published:
            count_dict['already_published'] += 1
        else:

# - check if this exam / examtype is approved by all auth
            auth1by = getattr(exam, 'auth1by')
            auth2by = getattr(exam, 'auth2by')
            auth_missing = auth1by is None or auth2by is None
            if logging_on:
                logger.debug('auth1by: ' + str(auth1by))
                logger.debug('auth2by: ' + str(auth2by))
                logger.debug('auth_missing: ' + str(auth_missing))
            if auth_missing:
                count_dict['auth_missing'] += 1
            else:

# - check if all auth are different
                double_approved = auth1by == auth2by
                if logging_on:
                    logger.debug('double_approved: ' + str(double_approved))
                if double_approved and not auth_missing:
                    count_dict['double_approved'] += 1
                else:
# - set value of published_instance and examtype_status field
                    if is_test:
                        count_dict['committed'] += 1
                    else:

                        update_exam_in_grades = False
                        try:
# - put published_id in field published
                            setattr(exam, 'published', published_instance)
# - save changes
                            exam.save(request=request)
                            count_dict['saved'] += 1
                            update_exam_in_grades = True
                        except Exception as e:
                            logger.error(getattr(e, 'message', str(e)))
                            count_dict['saved_error'] += 1

# --- add exam_pk to grades when published
                        if update_exam_in_grades:  # is_publish_exam and not is_test:
# - skip when there are more than 1 exam for this subject / dep / level / examperiod

                            crit = Q(subject=exam.subject) & \
                                   Q(department=exam.department)
                            if exam.examperiod in (1, 2):
                                crit.add(Q(examperiod=exam.examperiod), crit.connector)
                            else:
                                crit.add(Q(examperiod__lte=2), crit.connector)
                            if exam.level:
                                crit.add(Q(level=exam.level), crit.connector)

                            count_exams = subj_mod.Exam.objects.filter(crit).count()
                            if count_exams == 1:
                                grd_count = add_published_exam_to_grades(exam)
                                if grd_count:
                                    count_dict['updated_grd_count'] += grd_count
# - end of submit_grade_exam


def create_exam_published_instance(exam, now_arr, request):  # PR2022-02-23
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_exam_published_instance -----')
        logger.debug('request.user: ' + str(request.user))

    # create new published_instance and save it when it is not a test (this function is only called when it is not a test)
    # filename is added after creating file in create_ex1_xlsx
    subjbase_code = exam.subject.base.code
    depbase_code = exam.department.base.code
    lvlbase_code = ''
    if exam.level:
        lvlbase_code = exam.level.base.code
    examperiod = exam.examperiod

    # examtype used to store 'ete' or 'duo' exam

    # to be used when submitting Ex4 form
    examtype_caption = ''
    exform = 'Exam'

    if examperiod == 1:
        examtype_caption = 'ce'
    elif examperiod == 2:
        examtype_caption = 'her'
    elif examperiod == 12:
        examtype_caption = 'ce her'

    today_date = af.get_date_from_arr(now_arr)

    year_str = str(now_arr[0])
    month_str = ("00" + str(now_arr[1]))[-2:]
    date_str = ("00" + str(now_arr[2]))[-2:]
    hour_str = ("00" + str(now_arr[3]))[-2:]
    minute_str = ("00" +str( now_arr[4]))[-2:]
    now_formatted = ''.join([year_str, "-", month_str, "-", date_str, " ", hour_str, "u", minute_str])

    file_name = ' '.join((exform, examtype_caption, depbase_code, lvlbase_code + subjbase_code, now_formatted))
    # if total file_name is still too long: cut off
    if len(file_name) > c.MAX_LENGTH_FIRSTLASTNAME:
        file_name = file_name[0:c.MAX_LENGTH_FIRSTLASTNAME]

    published_instance = sch_mod.Published.objects.create(
        school=None,
        department=exam.department,
        examtype=examtype_caption,
        examperiod=exam.examperiod,
        name=file_name,
        datepublished=today_date,
        modifiedat=timezone.now,
        modifiedby=request.user
    )
    # Note: filefield 'file' gets value on creating Ex form

    published_instance.filename = file_name + '.pdf'
    # PR2021-09-06 debug: request.user is not saved in instance.save, don't know why
    published_instance.save(request=request)

    if logging_on:
        logger.debug(' request.user: ' + str(request.user))
        logger.debug('published_instance.saved: ' + str(published_instance))
        logger.debug('published_instance.pk: ' + str(published_instance.pk))
        logger.debug('published_instance.modifiedby: ' + str(published_instance.modifiedby))

    return published_instance
# - end of create_exam_published_instance


def add_published_exam_to_grades(exam):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --- add_published_exam_to_grades --- ')

    # als add exam to stdudents of SXM, therefore use subjbase and examyear insrtead of subhject
    subjbase_pk = exam.subject.base_id
    examyear_code = exam.subject.examyear.code
    depbase_pk = exam.department.base_id
    lvlbase_pk = exam.level.base_id
    examperiod = exam.examperiod
    ce_exam_pk = exam.pk

    if logging_on:
        logger.debug('exam.subject.name: ' + str(exam.subject.name))
        logger.debug('subjbase_pk: ' + str(subjbase_pk))
        logger.debug('examyear_code: ' + str(examyear_code))
        logger.debug('depbase_pk: ' + str(depbase_pk))
        logger.debug('lvlbase_pk: ' + str(lvlbase_pk))
        logger.debug('examperiod: ' + str(examperiod))
        logger.debug('ce_exam_pk: ' + str(ce_exam_pk))

    updated_grd_count = 0
    try:

# skip if there are multiple exams

        # Note: exams must also be assigned to students of SXM. Therefore don't filter on examyer.pk but on examyear.code
        sql_keys = {'ey_code': examyear_code, 'db_pk': depbase_pk, 'lb_pk': lvlbase_pk,
                    'subjbase_pk': subjbase_pk, 'ep': examperiod,  'ce_exam_pk': ce_exam_pk}

        lvlbase_join = "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)" if lvlbase_pk else ''
        lvlbase_clause = "AND lvl.base_id = %(lb_pk)s::INT" if lvlbase_pk else ''
        ep_clause = "AND grd.examperiod = %(ep)s::INT" if examperiod in (1, 2) else "AND (grd.examperiod = 1 OR exam.examperiod = 2)"
        sql_list = [
            "WITH sub_sql AS ( SELECT grd.id AS grd_id",

            "FROM students_grade AS grd",
            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
            "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
            lvlbase_join,

            "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id )",

            "WHERE ey.code = %(ey_code)s::INT",
            "AND dep.base_id = %(db_pk)s::INT",
            "AND subj.base_id = %(subjbase_pk)s::INT",
            "AND grd.ce_exam_id IS NULL",
            ep_clause,
            lvlbase_clause,
            "AND NOT grd.tobedeleted AND NOT studsubj.tobedeleted AND NOT stud.tobedeleted )",

            "UPDATE students_grade",
            "SET ce_exam_id = %(ce_exam_pk)s::INT",
            "FROM sub_sql",
            "WHERE id = sub_sql.grd_id",
            "RETURNING id;"
        ]

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = cursor.fetchall()

            if logging_on:
                logger.debug('rows: ' + str(rows))

            if rows:
                updated_grd_count += len(rows)
                if logging_on:
                    logger.debug('updated_grd_count: ' + str(updated_grd_count))

        # for testing only:
        if logging_on and False:
            for qr in connection.queries:
                logger.debug('-----------------------------------------------------------------------------')
                logger.debug(str(qr))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return updated_grd_count
# end of add_published_exam_to_grades


def create_exam_instance(subject, department, level, examperiod_int, ete_exam, request):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' --- create_exam_instance --- ')
        logger.debug('subject: ' + str(subject))
        logger.debug('department: ' + str(department))
        logger.debug('level: ' + str(level))
        logger.debug('examperiod_int: ' + str(examperiod_int))

    exam = None
    msg_err = None
# - create exam
    try:
        #a = 1 / 0 # to create error
        exam = subj_mod.Exam(
            subject=subject,
            department=department,
            level=level,
            examperiod=examperiod_int,
            ete_exam=ete_exam
            # NIU (null not allowed): examtype=examtype
        )
        exam.save(request=request)
        if logging_on:
            logger.debug('exam: ' + str(exam))

    except Exception as e:
# - create error when exam is  not created
        logger.error(getattr(e, 'message', str(e)))
        msg_err = ("An error occurred. This exam could not be created.")
        if logging_on:
            logger.debug('msg_err: ' + str(msg_err))

    return exam, msg_err
# - end of create_exam_instance


def delete_exam_instance(instance, error_list, request):  #  PR2021-04-05 PR2022-01-22
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' --- delete_exam_instance --- ')
        logger.debug('instance: ' + str(instance))

# - create deleted_row
    deleted_row = {'id': instance.pk,
                    'mapid': 'exam_' + str(instance.pk),
                    'deleted': True}
    if logging_on:
        logger.debug('deleted_row: ' + str(deleted_row))

# - delete instance
    try:
        instance.delete(request=request)
    except Exception as e:
        deleted_row = None
        logger.error(getattr(e, 'message', str(e)))
        error_list.append(_('This exam could not be deleted.'))

    if logging_on:
        logger.debug('deleted_row: ' + str(deleted_row))
        logger.debug('error_list: ' + str(error_list))
    return deleted_row
# - end of delete_exam_instance


def update_exam_instance(instance, upload_dict, error_list, examyear, request): #  PR2021-04-05 PR2022-01-24
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --------- update_exam_instance -------------')
        logger.debug('upload_dict: ' + str(upload_dict))
        # upload_dict: {'table': 'exam', 'mode': 'update', 'examyear_pk': 1, 'depbase_pk': 1, 'lvlbase_pk': 13,
        # 'exam_pk': 138, 'subject_pk': 2137, 'field': 'authby', 'auth_index': 2, 'auth_bool_at_index': True}
    if instance:
        save_changes = False
        for field, new_value in upload_dict.items():

# --- skip fields that don't contain new values
            if field in ('mode', 'examyear_pk', 'subject_pk', 'exam_pk', 'examtype'):
                pass

# ---   save changes in field 'depbases', 'levelbases', 'sectorbases'
            elif field in ('depbases', 'levelbases', 'sectorbases'):
                old_value = getattr(instance, field)
                uploaded_field_arr = []
                if field == 'depbases':
                    uploaded_field_arr = new_value.split(';') if new_value else []
                elif field == 'levelbases':
                    uploaded_field_arr = new_value.split(';') if new_value else []
                elif field == 'sectorbases':
                    uploaded_field_arr = new_value.split(';') if new_value else []

                checked_field_arr = []
                checked_field_str = None
                if uploaded_field_arr:
                    for base_pk_str in uploaded_field_arr:
                        base_pk_int = int(base_pk_str)
                        base_instance = None
                        if field == 'depbases':
                            base_instance = sch_mod.Department.objects.get_or_none(base=base_pk_int,examyear=examyear)
                        elif field == 'levelbases':
                            base_instance = subj_mod.Level.objects.get_or_none(base=base_pk_int,examyear=examyear)
                        elif field == 'sectorbases':
                            base_instance = subj_mod.Sector.objects.get_or_none(base=base_pk_int,examyear=examyear)
                        if base_instance:
                            checked_field_arr.append(base_pk_str)
                    if checked_field_arr:
                        checked_field_arr.sort()
                        checked_field_str = ';'.join(checked_field_arr)
                if checked_field_str != old_value:
                    setattr(instance, field, new_value)
                    save_changes = True

            elif field in ('partex', 'assignment', 'keys', 'version', 'examperiod',
                           'amount', 'blanks', 'scalelength', 'nex_id', 'cesuur', 'nterm', 'examdate' ):
                # save None instead of  '' or 0
                if not new_value:
                    new_value = None
                old_value = getattr(instance, field)
                if new_value != old_value:
                    setattr(instance, field, new_value)
                    save_changes = True

            elif field == 'has_partex':
                if not new_value:
                    new_value = False
                old_value = getattr(instance, field, False)
                if new_value != old_value:
                    setattr(instance, field, new_value)
                    save_changes = True

            elif field == 'auth_index':
                auth_index = upload_dict.get(field)
                auth_bool_at_index = upload_dict.get('auth_bool_at_index', False)
                fldName = 'auth1by' if auth_index == 1 else 'auth2by' if auth_index == 2 else None

                if logging_on:
                    logger.debug('auth_index: ' + str(auth_index))
                    logger.debug('auth_bool_at_index: ' + str(auth_bool_at_index))
                    logger.debug('fldName: ' + str(fldName))

                if fldName:
                    new_value = request.user if auth_bool_at_index else None
                    if logging_on:
                        logger.debug('new_value: ' + str(auth_index))

                    setattr(instance, fldName, new_value)
                    save_changes = True

            elif field == 'published':
                pass

# - save instance
        if save_changes:
            try:
                instance.save(request=request)
                if logging_on:
                    logger.debug('instance saved: ' + str(instance))

# - save to log after saving emplhour and orderhour, also when emplhour is_created
                #m.save_to_emplhourlog(emplhour.pk, request, False) # is_deleted=False

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_err = _('An error occurred. This exam could not be updated.')
                error_list.append(msg_err)
# - end of update_exam_instance


def create_exam_rows(req_usr, sel_examyear_pk, sel_depbase_pk, append_dict, setting_dict=None, exam_pk_list=None):
    # --- create rows of all exams of this examyear  PR2021-04-05  PR2022-01-23 PR2022-02-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_exam_rows ============= ')

# - only show published exams when user is school
    sql_keys = {'ey_id': sel_examyear_pk, 'depbase_id': sel_depbase_pk}

    sql_list = [
        "SELECT ex.id, ex.subject_id, subj.base_id AS subjbase_id, subj.examyear_id AS subj_examyear_id,",
        "CONCAT('exam_', ex.id::TEXT) AS mapid,",
        "CONCAT(subj.name,",
        "CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' - ', lvl.abbrev) END,",
        "CASE WHEN ex.version IS NULL OR ex.version = '' THEN NULL ELSE CONCAT(' - ', ex.version) END ) AS exam_name,",

        "ex.ete_exam, ex.examperiod, ex.department_id, depbase.id AS depbase_id, depbase.code AS depbase_code,",
        "ex.level_id, lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev,",
        "ex.version, ex.has_partex, ex.partex, ex.assignment, ex.keys, ex.amount, ex.blanks,",
        "ex.nex_id, ex.scalelength, ex.cesuur, ex.nterm,",  # ex.examdate,",

        "ex.status, ex.auth1by_id, ex.auth2by_id, ex.published_id, ex.locked, ex.modifiedat,",
        "sb.code AS subj_base_code, subj.name AS subj_name,",
        "ey.id AS ey_id, ey.code AS ey_code, ey.locked AS ey_locked,",
        "au.last_name AS modby_username,",

        "auth1.last_name AS auth1_usr, auth2.last_name AS auth2_usr, publ.modifiedat AS publ_modat",

        "FROM subjects_exam AS ex",
        "INNER JOIN subjects_subject AS subj ON (subj.id = ex.subject_id)",
        "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

        "INNER JOIN schools_department AS dep ON (dep.id = ex.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = ex.level_id)",

        "LEFT JOIN accounts_user AS auth1 ON (auth1.id = ex.auth1by_id)",
        "LEFT JOIN accounts_user AS auth2 ON (auth2.id = ex.auth2by_id)",
        "LEFT JOIN schools_published AS publ ON (publ.id = ex.published_id)",

        "LEFT JOIN accounts_user AS au ON (au.id = ex.modifiedby_id)",
        "WHERE ey.id = %(ey_id)s::INT AND depbase.id = %(depbase_id)s::INT"
    ]

# - only show exams that are not published when user is_role_admin
    if not req_usr.is_role_admin:
        sql_list.append("AND ex.published_id IS NOT NULL")

    if exam_pk_list:
        sql_keys['pk_arr'] = exam_pk_list
        sql_list.append("AND ex.id IN ( SELECT UNNEST( %(pk_arr)s::INT[]))")

    elif setting_dict:
        sel_examperiod = setting_dict.get(c.KEY_SEL_EXAMPERIOD)
        if sel_examperiod in(1, 2):
            # examperiod = 12 means ce and reex
            sql_keys['ep'] = sel_examperiod
            sql_list.append("AND (ex.examperiod = %(ep)s::INT OR ex.examperiod = 12)")

        sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)
        if sel_lvlbase_pk:
            sql_keys['lvlbase_pk'] = sel_lvlbase_pk
            sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

    sql_list.append("ORDER BY ex.id")

    sql = ' '.join(sql_list)
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        exam_rows = af.dictfetchall(cursor)

# - add messages to first exam_row, only when exam_pk exists
        if exam_pk_list and len(exam_pk_list) == 1 and exam_rows:
            # when exam_pk has value there is only 1 row
            row = exam_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    if logging_on:
        logger.debug('exam_rows: ' + str(exam_rows))

    return exam_rows
# --- end of create_exam_rows


def create_duo_exam_rows(req_usr, sel_examyear_pk, sel_depbase_pk, append_dict, setting_dict=None, exam_pk_list=None):
    # --- create rows of all exams of this examyear  PR2021-04-05  PR2022-01-23 PR2022-02-23
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_duo_exam_rows ============= ')

# - only show published exams when user is school
    sql_keys = {'ey_id': sel_examyear_pk, 'depbase_id': sel_depbase_pk}
    sql_list = [
        "SELECT subj.id, subj.base_id AS subjbase_id,",
        "sb.code AS subj_base_code, subj.name AS subj_name,",
        "lvl.id AS lvl_id, lvl.abbrev AS lvl_abbrev",

        "FROM subjects_schemeitem AS si",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

        "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",

        "WHERE ey.id = %(ey_id)s::INT AND depbase.id = %(depbase_id)s::INT",
        "AND NOT si.ete_exam"
    ]

    if setting_dict:
        sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)
        if sel_lvlbase_pk:
            sql_keys['lvlbase_pk'] = sel_lvlbase_pk
            sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

    sql_list.append("GROUP BY subj.id, subj.base_id, sb.code, subj.name, lvl.id, lvl.abbrev")
    sql_list.append("ORDER BY subj.id, lvl.id")

    sql = ' '.join(sql_list)
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))
        logger.debug('sql: ' + str(sql))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        duo_exam_rows = af.dictfetchall(cursor)

# - add messages to first exam_row, only when exam_pk exists
        if exam_pk_list and len(exam_pk_list) == 1 and duo_exam_rows:
            # when exam_pk has value there is only 1 row
            row = duo_exam_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    if logging_on:
        logger.debug('duo_exam_rows: ' + str(duo_exam_rows))

    return duo_exam_rows
# --- end of create_duo_exam_rows


def create_ntermentable_rows(sel_examyear_pk, sel_depbase, setting_dict):
    # --- create rows of all exams of this examyear  PR2021-04-05  PR2022-01-23 PR2022-02-23
    logging_on = False  #  s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_ntermentable_rows ============= ')
    # sty_id 1 = vwo, 2 = havo, 3 = vmbo
    sty_id = None
    if sel_depbase.code == 'Vsbo':
        sty_id = 3
    elif sel_depbase.code == 'Havo':
        sty_id = 2
    elif sel_depbase.code == 'Vwo':
        sty_id = 1
    # - only show published exams when user is school
    sql_keys = {'ey_id': sel_examyear_pk, 'sty_id': sty_id}

    sql_list = [
        "SELECT nt.id, nt.nex_id, nt.sty_id, nt.opl_code, nt.leerweg, nt.ext_code, nt.tijdvak,"
        "nt.omschrijving, nt.schaallengte, nt.n_term, nt.afnamevakid, nt.extra_vakcodes_tbv_wolf,",
        "nt.datum, nt.begintijd, nt.eindtijd",

        "FROM subjects_ntermentable AS nt",
        "INNER JOIN schools_examyear AS ey ON (ey.id = nt.examyear_id)",
        "WHERE ey.id = %(ey_id)s::INT AND nt.sty_id = %(sty_id)s::INT"
    ]

    if setting_dict:
        sel_examperiod = setting_dict.get(c.KEY_SEL_EXAMPERIOD)
        if sel_examperiod == 1:
            sql_list.append("AND nt.tijdvak = 1")
        elif sel_examperiod == 2:
            sql_list.append("AND (nt.tijdvak = 2 OR nt.tijdvak = 3)")

        sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)
        if sel_lvlbase_pk:
            sel_level_abbrev = setting_dict.get('sel_level_abbrev')
            if sel_level_abbrev == 'TKL':
                sql_list.append("AND nt.leerweg = 'GL/TL'")
            elif sel_level_abbrev == 'PKL':
                sql_list.append("AND nt.leerweg = 'KB'")
            elif sel_level_abbrev == 'PBL':
                sql_list.append("AND nt.leerweg = 'BB'")

    sql_list.append("ORDER BY nt.id")
    sql = ' '.join(sql_list)
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        ntermentable_rows = af.dictfetchall(cursor)

    return ntermentable_rows
# --- end of create_exam_rows


def calc_total():
    # --- creates possible sums of list with max_scores and occurrencies
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== calc_total ============= ')

    maxscore_list = [(18, 2), (34, 1), (27, 4)]
    if logging_on:
        logger.debug('maxscore_list: ' + str(maxscore_list))

    # use list to get reference instead of value
    used_score_str = ""
    total_score_dict = {}
    total_score = 0
    list_index = len(maxscore_list) -1

    calc_recursive(maxscore_list, total_score_dict, used_score_str, total_score, list_index)


    if logging_on:
        logger.debug('total_score_list: ' + str(total_score_dict))

    return total_score_dict
# --- end of calc_total


def calc_recursive(maxscore_list, total_score_dict, used_score_str, total_score, list_index):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calc_recursive  ----- list_index: ' + str(list_index))
        logger.debug('total_score: ' + str(total_score))
        logger.debug('used_score_str: ' + str(used_score_str))

    if list_index >= 0:
        tuple_at_index = maxscore_list[list_index]
        max_score = tuple_at_index[0]
        occurrencies = tuple_at_index[1]
        if logging_on:
            logger.debug('     max_score: ' + str(max_score) + ' occurrencies: ' + str(occurrencies))

        new_listindex = list_index - 1
        this_used_score_str = used_score_str
        # loop through amount of occurrencies
        for multiplier in range(0, occurrencies + 1, 1):  # range(start_value, end_value, step), end_value is not included!
            new_total_score = total_score + max_score * multiplier
            if multiplier:
                new_used_score_str = ';'.join((this_used_score_str, str(max_score)))
            else:
                new_used_score_str = this_used_score_str
            if logging_on:
                logger.debug('..... for multiplier = ' + str(multiplier))
                logger.debug('     new_total_score: ' + str(new_total_score))

            calc_recursive(maxscore_list, total_score_dict, new_used_score_str, new_total_score, new_listindex)

            if logging_on:
                logger.debug('..... end of for multiplier = ' + str(multiplier))
    else:
        if total_score:
            used_score_arr = []
            if used_score_str:
                used_score_str = used_score_str[1:]
                arr = used_score_str.split(';')
                if len(arr):
                    for score_str in arr:
                        used_score_arr.append(int(score_str))
                    used_score_arr.sort()

            total_score_dict[total_score] = used_score_arr

        if logging_on:
            logger.debug('     end of recurrencies ')
            logger.debug('     total_score_dict: ' + str(total_score_dict))
            logger.debug('-----  end of calc_recursive')
# - end of calc_recursive

@method_decorator([login_required], name='dispatch')
class SubjectImportView(View):  # PR2020-10-01

    def get(self, request):
        param = {}
        has_permit = False
        if request.user is not None and request.user.country is not None and request.user.schoolbase is not None:
            has_permit = True # (request.user.is_perm_planner or request.user.is_perm_hrman)
        if has_permit:
            # coldef_list = [{'tsaKey': 'employee', 'caption': _('Company name')},
            #                      {'tsaKey': 'ordername', 'caption': _('Order name')},
            #                      {'tsaKey': 'orderdatefirst', 'caption': _('First date order')},
            #                      {'tsaKey': 'orderdatelast', 'caption': _('Last date order')} ]

    # get coldef_list  and caption
            coldef_list = c.COLDEF_SUBJECT
            captions_dict = c.CAPTION_IMPORT

            # get mapped coldefs from table Companysetting
            # get stored setting from Companysetting

            settings_json = request.user.schoolbase.get_schoolsetting_dict(c.KEY_IMPORT_SUBJECT)
            stored_setting = json.loads(settings_json) if settings_json else {}

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
                        # coldef = {'tsaKey': 'employee', 'caption': 'Cliënt'}
                        # get fieldname from coldef
                        fieldname = coldef.get('tsaKey')
                        #logger.debug('fieldname: ' + str(fieldname))

                        if fieldname:  # fieldname should always be present
                            # check if fieldname exists in stored_coldefs
                            if fieldname in stored_coldefs:
                                # if so, add Excel name with key 'excKey' to coldef
                                coldef['excKey'] = stored_coldefs[fieldname]
                                #logger.debug('stored_coldefs[fieldname]: ' + str(stored_coldefs[fieldname]))

            coldefs_dict = {
                'worksheetname': self.worksheetname,
                'has_header': self.has_header,
                'codecalc': self.codecalc,
                'coldefs': coldef_list
            }
            coldefs_json = json.dumps(coldefs_dict, cls=LazyEncoder)

            captions = json.dumps(captions_dict, cls=LazyEncoder)

            param = awpr_menu.get_headerbar_param(request,'subject_import', {'captions': captions, 'setting': coldefs_json})

        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'subjectimport.html', param)


@method_decorator([login_required], name='dispatch')
class SubjectImportUploadSetting(View):   # PR2019-03-10
    # function updates mapped fields, no_header and worksheetname in table Companysetting
    def post(self, request, *args, **kwargs):
        #logger.debug(' ============= SubjectImportUploadSetting ============= ')
        #logger.debug('request.POST' + str(request.POST) )
        schoolsetting_dict = {}
        has_permit = False
        if request.user is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_group_system)
        if has_permit:
            if request.POST['upload']:
                new_setting_json = request.POST['upload']
                # new_setting is in json format, no need for json.loads and json.dumps
                #logger.debug('new_setting_json' + str(new_setting_json))

                new_setting_dict = json.loads(request.POST['upload'])
                settings_key = c.KEY_IMPORT_SUBJECT

                new_worksheetname = ''
                new_has_header = True
                new_code_calc = ''
                new_coldefs = {}
    #TODO get_jsonsetting returns dict
                stored_json = request.user.schoolbase.get_schoolsetting_dict(settings_key)
                if stored_json:
                    stored_setting = json.loads(stored_json)
                    #logger.debug('stored_setting: ' + str(stored_setting))
                    if stored_setting:
                        new_has_header = stored_setting.get('has_header', True)
                        new_worksheetname = stored_setting.get('worksheetname', '')
                        new_code_calc = stored_setting.get('codecalc', '')
                        new_coldefs = stored_setting.get('coldefs', {})

                if new_setting_json:
                    new_setting = json.loads(new_setting_json)
                    #logger.debug('new_setting' + str(new_setting))
                    if new_setting:
                        if 'worksheetname' in new_setting:
                            new_worksheetname = new_setting.get('worksheetname', '')
                        if 'has_header' in new_setting:
                            new_has_header = new_setting.get('has_header', True)
                        if 'coldefs' in new_setting:
                            new_coldefs = new_setting.get('coldefs', {})
                    #logger.debug('new_code_calc' + str(new_code_calc))
                new_setting = {'worksheetname': new_worksheetname,
                               'has_header': new_has_header,
                               'codecalc': new_code_calc,
                               'coldefs': new_coldefs}
                new_setting_json = json.dumps(new_setting)
                request.user.schoolbase.set_schoolsetting_dict(settings_key, new_setting_json)

    # only for testing
                # ----- get user_lang
                #user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                #tblName = 'employee'
                #coldefs_dict = compdicts.get_stored_coldefs_dict(tblName, user_lang, request)
                #if coldefs_dict:
                #    schoolsetting_dict['coldefs'] = coldefs_dict
                #logger.debug('new_setting from saved ' + str(coldefs_dict))

                #m.Companysetting.set_setting(c.settings_key, new_setting_json, request.user.schoolbase)

        return HttpResponse(json.dumps(schoolsetting_dict, cls=LazyEncoder))
# --- end of SubjectImportUploadSetting

@method_decorator([login_required], name='dispatch')
class SubjectImportUploadData(View):  # PR2018-12-04 PR2019-08-05 PR2020-06-04

    def post(self, request):
        logger.debug(' ========================== SubjectImportUploadData ========================== ')
        params = {}
        has_permit = False
        is_not_locked = False
        if request.user is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_group_system)
            # TODO change request.user.examyear to sel_examyear
            is_not_locked = not request.user.examyear.locked

        if is_not_locked and has_permit:
            # - Reset language
            # PR2019-03-15 Debug: language gets lost, get request.user.lang again
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                params = import_subjects(upload_dict, user_lang, request)

        return HttpResponse(json.dumps(params, cls=LazyEncoder))

# --- end of SubjectImportUploadData

def import_subjects(upload_dict, user_lang, request):

    logger.debug(' -----  import_subjects ----- ')
    logger.debug('upload_dict: ' + str(upload_dict))
# - get is_test, codecalc, dateformat, awpKey_list
    is_test = upload_dict.get('test', False)
    awpKey_list = upload_dict.get('awpKey_list')
    dateformat = upload_dict.get('dateformat', '')

    params = {}
    if awpKey_list:
# - get lookup_field
        # lookup_field is field that determines if employee alreay exist.
        # check if one of the fields 'payrollcode', 'identifier' or 'code' exists
        # first in the list is lookup_field
        lookup_field = 'code'

# - get upload_dict from request.POST
        subject_list = upload_dict.get('subjects')
        if subject_list:

            today_dte = af.get_today_dateobj()
            today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
            double_line_str = '=' * 80
            indent_str = ' ' * 5
            space_str = ' ' * 30
            logfile = []
            logfile.append(double_line_str)
            logfile.append( '  ' + str(request.user.schoolbase.code) + '  -  ' +
                            str(_('Import subjects')) + ' ' + str(_('date')) + ': ' + str(today_formatted))
            logfile.append(double_line_str)

            if lookup_field is None:
                info_txt = str(_('There is no field given to lookup subjects. Subjects cannot be uploaded.'))
                logfile.append(indent_str + info_txt)
            else:
                if is_test:
                    info_txt = str(_("This is a test. The subject data are not saved."))
                else:
                    info_txt = str(_("The subject data are saved."))
                logfile.append(indent_str + info_txt)
                lookup_caption = str(get_field_caption('subject', lookup_field))
                info_txt = str(_("Subjects are looked up by the field: '%(fld)s'.") % {'fld': lookup_caption})
                logfile.append(indent_str + info_txt)
                #if dateformat:
                #    info_txt = str(_("The date format is: '%(fld)s'.") % {'fld': dateformat})
                #    logfile.append(indent_str + info_txt)
                update_list = []
                for subject_dict in subject_list:
                    # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html

                    update_dict = upload_subject(subject_list, subject_dict, lookup_field,
                                                 awpKey_list, is_test, dateformat, indent_str, space_str, logfile, request)
                    # json_dumps_err_list = json.dumps(msg_list, cls=f.LazyEncoder)
                    if update_dict:  # 'Any' returns True if any element of the iterable is true.
                        update_list.append(update_dict)

                if update_list:  # 'Any' returns True if any element of the iterable is true.
                    params['subject_list'] = update_list
            if logfile:  # 'Any' returns True if any element of the iterable is true.
                params['logfile'] = logfile
                        # params.append(new_employee)
    return params


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def upload_subject(subject_list, subject_dict, lookup_field, awpKey_list,
                   is_test, dateformat, indent_str, space_str, logfile, request):  # PR2019-12-17 PR2020-10-21
    logger.debug('----------------- import subject  --------------------')
    logger.debug(str(subject_dict))
    # awpKeys are: 'code', 'name', 'sequence', 'depbases'

# - get index and lookup info from subject_dict
    row_index = subject_dict.get('rowindex', -1)
    new_code = subject_dict.get('code')
    new_name = subject_dict.get('name')
    new_sequence = subject_dict.get('sequence')
    new_depbases = subject_dict.get('depbases')

# - create update_dict
    update_dict = {'id': {'table': 'subject', 'rowindex': row_index}}

# - give row_error when lookup went wrong
    # multiple_found and value_too_long return the lookup_value of the error field

    lookup_field_caption = str(get_field_caption('subject', lookup_field))
    lookup_field_capitalized = '-'
    if lookup_field_caption:
        lookup_field_capitalized = lookup_field_caption.capitalize()
    is_skipped_str = str(_("is skipped."))
    skipped_str = str(_("Skipped."))
    logfile.append(indent_str)
    msg_err = None
    log_str = ''

    subjectbase = None
    subject = None

# check if lookup_value has value ( lookup_field = 'code')
    lookup_value = subject_dict.get(lookup_field)
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
        field_caption = str(get_field_caption('subject', 'name'))
        log_str = str(_("No value for required field: '%(fld)s'.") % {'fld': field_caption})
        msg_err = ' '.join((skipped_str, log_str))

# check if subject name  is not too long
    elif len(new_name) > c.MAX_LENGTH_NAME:
        value_too_long_str = str(_("Value '%(val)s' is too long.") % {'val': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_NAME})
        log_str = value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))
    else:

# - check if lookup_value occurs mutiple times in Excel file
        excel_list_multiple_found = False
        excel_list_count = 0
        for dict in subject_list:
            value = dict.get(lookup_field)
            if value and value == lookup_value:
                excel_list_count += 1
            if excel_list_count > 1:
                excel_list_multiple_found = True
                break
        if excel_list_multiple_found:
            log_str = str(_("%(fld)s '%(val)s' is not unique in Excel file.") % {'fld': lookup_field_capitalized, 'val': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

    if msg_err is None:

# - check if subjectbase with this code exists in request.user.country. subjectbase has value when only one found
        # lookup_value = subject_dict.get(lookup_field)
        subjectbase, multiple_found = lookup_subjectbase(lookup_value, request)
        if multiple_found:
            log_str = str(_("Value '%(fld)s' is found multiple times.") % {'fld': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

# - check if subject with this subjectbase exists in request.user.examyear. subject has value when only one found
        multiple_subjects_found = False
        if subjectbase:
            subject, multiple_subjects_found = lookup_subject(subjectbase, request)
        if multiple_subjects_found:
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

# - create new subjectbase when subjectbase not found in database
        if subjectbase is None:
            try:
                subjectbase = subj_mod.Subjectbase(
                    code=new_code
                )
                if subjectbase:
                    subjectbase.save()
            except:
# - give error msg when creating subjectbase failed
                error_str = str(_("An error occurred. The subject is not added."))
                logfile.append(" ".join((code_text, error_str )))
                update_dict['row_error'] = error_str

        if subjectbase :

# - create new subject when subject not found in database
            is_existing_subject = False
            save_instance = False

            if subject is None:
                try: # TODO change request.user.examyear to sel_examyear
                    subject = subj_mod.Subject(
                        base=subjectbase,
                        examyear=request.user.examyear,
                        name=new_name
                    )
                    if subject:
                        subject.save(request=request)
                        update_dict['id']['created'] = True
                        logfile.append(code_text + str(_('is added.')))
                except:
    # - give error msg when creating subject failed
                    error_str = str(_("An error occurred. The subject is not added."))
                    logfile.append(" ".join((code_text, error_str )))
                    update_dict['row_error'] = error_str
            else:
                is_existing_subject = True
                logfile.append(code_text + str(_('already exists.')))

            if subject:
                # add 'id' at the end, after saving the subject. Pk doent have value until instance is saved
                #update_dict['id']['pk'] = subject.pk
                #update_dict['id']['ppk'] = subject.company.pk
                #if subject:
                #    update_dict['id']['created'] = True

                # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
                # solved bij wrapping with str()

                blank_str = '<' + str(_('blank')) + '>'
                was_str = str(_('was') + ': ')
                # FIELDS_SUBJECT = ('base', 'examyear', 'name', 'abbrev', 'sequence', 'depbases', 'modifiedby', 'modifiedat')
                for field in ('name', 'abbrev', 'sequence', 'depbases'):
                    # --- get field_dict from  upload_dict  if it exists
                    if field in awpKey_list:
                        #('field: ' + str(field))
                        field_dict = {}
                        field_caption = str(get_field_caption('subject', field))
                        caption_txt = (indent_str + field_caption + space_str)[:30]

                        if field in ('code', 'name', 'namefirst', 'email', 'address', 'city', 'country'):
                            if field == 'code':
                                # new_code is created in this function and already checked for max_len
                                new_value = new_code
                            else:
                                new_value = subject_dict.get(field)
                # check length of new_value
                            max_len = c.MAX_LENGTH_NAME \
                                if field in ('namelast', 'namefirst', 'email', 'address', 'city', 'country') \
                                else c.MAX_LENGTH_SCHOOLCODE

                            if max_len and new_value and len(new_value) > max_len:
                                msg_err = str(_("'%(val)s' is too long. Maximum is %(max)s characters'.") % {
                                    'val': new_value, 'max': max_len})
                                field_dict['error'] = msg_err
                            else:
                    # - replace '' by None
                                if not new_value:
                                    new_value = None
                                field_dict['value'] = new_value
                                if not is_existing_subject:
                                    logfile.append(caption_txt + (new_value or blank_str))
                    # - get saved_value
                                saved_value = getattr(subject, field)
                                if new_value != saved_value:
                    # put new value in subject instance
                                    setattr(subject, field, new_value)
                                    field_dict['updated'] = True
                                    save_instance = True
                    # create field_dict and log
                                    if is_existing_subject:
                                        old_value_str = was_str + (saved_value or blank_str)
                                        field_dict['info'] = field_caption + ' ' + old_value_str
                                        update_str = ((new_value or blank_str) + space_str)[:25] + old_value_str
                                        logfile.append(caption_txt + update_str)

                # add field_dict to update_dict
                        update_dict[field] = field_dict

               # dont save data when it is a test run
               # if not is_test and save_instance:
                    #employee.save(request=request)
                    #update_dict['id']['pk'] = employee.pk
                    #update_dict['id']['ppk'] = employee.company.pk
                    # wagerate wagecode
                    # priceratejson additionjson
                   # try:
                        #employee.save(request=request)


                        #update_dict['id']['pk'] = employee.pk
                        #update_dict['id']['ppk'] = employee.company.pk
                   # except:
        # - give error msg when creating employee failed
                   #     error_str = str(_("An error occurred. The subject data is not saved."))
                   #     logfile.append(" ".join((code_text, error_str)))
                  #      update_dict['row_error'] = error_str

    return update_dict
# --- end of upload_subject


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def lookup_subjectbase(lookup_value, request):  # PR2020-10-20
    logger.debug('----------- lookup_subjectbase ----------- ')
    # function searches for existing subjectbase
    logger.debug('lookup_value: ' + str(lookup_value) + ' ' + str(type(lookup_value)))

    subjectbase = None
    multiple_found = False

# check if 'code' exists multiple times in Subjectbase
    row_count = subj_mod.Subjectbase.objects.filter(
        code__iexact=lookup_value
    ).count()

    if row_count > 1:
        multiple_found = True
    elif row_count == 1:
# get subjectbase when only one found # TODO change request.user.examyear to sel_examyear
        subjectbase = subj_mod.Subject.objects.get_or_none(code__iexact=lookup_value, examyear=request.user.examyear)
    # TODO skip for now, remove this line
    multiple_found = False
    return subjectbase, multiple_found


def lookup_subject(subjectbase, request):  # PR2019-12-17 PR2020-10-20
    #logger.debug('----------- lookup_subject ----------- ')

    subject = None
    multiple_subjects_found = False

# - search subject by subjectbase and request.user.examyear
    if subjectbase:
        # check if subject exists multiple times # TODO change request.user.examyear to sel_examyear
        row_count = subj_mod.Subject.objects.filter(base=subjectbase, examyear=request.user.examyear).count()
        if row_count > 1:
            multiple_subjects_found = True
        elif row_count == 1:
            # get subject when only one found # TODO change request.user.examyear to sel_examyear
            subject = subj_mod.Subject.objects.get_or_none(base=subjectbase, examyear=request.user.examyear)

    return subject, multiple_subjects_found



def get_field_caption(table, field):
    caption = ''
    if table == 'subject':
        if field == 'code':
            caption = _('Abbreviation')
        elif field == 'name':
            caption = _('Subject name')
        elif field == 'sequence':
            caption = _('Sequence')
        elif field == 'depbases':
            caption = _('Departments')
    return caption


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def delete_subject(subject, updated_rows, err_list, request):
    # --- delete subject # PR2021-05-14 PR2021-07-18 PR2022-02-16

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_subject ----- ')
        logger.debug('subject: ' + str(subject))

    deleted_ok = False

# - create updated_row - to be returned after successfull delete
    updated_row = {'id': subject.pk,
                   'mapid': 'subject_' + str(subject.pk),
                   'deleted': True}
    base_pk = subject.base.pk

    this_txt = _("Subject '%(tbl)s'") % {'tbl': subject.name}
    header_txt = _("Delete subject")

# - check if there are students with this subject
    students_with_this_subject_exist = stud_mod.Studentsubject.objects.filter(
        schemeitem__subject=subject).exists()

    if logging_on:
        logger.debug('students_with_this_subject_exist: ' + str(students_with_this_subject_exist))

    if students_with_this_subject_exist:
        err_txt1 = str(_('There are candidates with this subject.'))
        err_txt2 = str(_("%(cpt)s could not be deleted.") % {'cpt': this_txt})
        err_list.append(' '.join((err_txt1, err_txt2)))

    else:
        deleted_ok = sch_mod.delete_instance(subject, [], err_list, request, this_txt, header_txt)

    if deleted_ok:
# - add deleted_row to updated_rows
        updated_rows.append(updated_row)

# - check if this subject also exists in other examyears.
        subjects = subj_mod.Subject.objects.filter(base_id=base_pk).first()
        # If not: delete also subject_base
        if subjects is None:
            subject_base = subj_mod.Subjectbase.objects.get_or_none(id=base_pk)
            if subject_base:
                subject_base.delete()

    if logging_on:
        logger.debug('updated_rows' + str(updated_rows))
        logger.debug('err_list' + str(err_list))

    return deleted_ok
# - end of delete_subject


def create_subject(examyear, upload_dict, messages, request):
    # --- create subject # PR2019-07-30 PR2020-10-11 PR2021-05-13 PR2021-06-22
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_subject ----- ')
        logger.debug('examyear: ' + str(examyear))
        logger.debug('upload_dict: ' + str(upload_dict))

    subject = None
    caption = _('Create subject')

    if examyear:
# - get values
        code = upload_dict.get('code')
        name = upload_dict.get ('name')
        sequence = upload_dict.get ('sequence', 9999)
        depbases = upload_dict.get('depbases')
        if logging_on:
            logger.debug('code: ' + str(code))
            logger.debug('name: ' + str(name))
            logger.debug('sequence: ' + str(sequence))
            logger.debug('depbases: ' + str(depbases) + str(type(depbases)))

        msg_list = []
# - validate code and name. Function checks null, max_len, exists
        msg_err = av.validate_notblank_maxlength(code, c.MAX_LENGTH_SCHOOLCODE, _('The abbreviation'))
        if msg_err:
            msg_list.append(msg_err)
        msg_err = av.validate_notblank_maxlength(name, c.MAX_LENGTH_NAME, _('The name'))
        if msg_err:
            msg_list.append(msg_err)
# - check if subject code already exists
        msg_err = av.validate_subject_code_exists(code, subject)
        if msg_err:
            msg_list.append(msg_err)
# - check if subject name already exists
        msg_err = av.validate_subject_name_exists(name, subject)
        if msg_err:
            msg_list.append(msg_err)

# - create and save subject
        if len(msg_list) > 0:
            msg_html = '<br>'.join(msg_list)
            messages.append({'header': str(caption), 'class': "border_bg_invalid", 'msg_html': msg_html})
        else:
            try:
                # First create base record. base.id is used in Subject. Create also saves new record
                base = sbj_mod.Subjectbase.objects.create(
                    code=code
                )

                subject = sbj_mod.Subject(
                    base=base,
                    examyear=examyear,
                    name=name,
                    sequence=sequence,
                    depbases=depbases
                )
                subject.save(request=request)

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                                    str(_("%(cpt)s '%(val)s'could not be added.") % {'cpt': _('Subject'), 'val': name})))
                messages.append(
                    {'class': "border_bg_invalid", 'header': str(_('Create subject')), 'msg_html': msg_html})

    if logging_on:
        logger.debug('subject: ' + str(subject))
        logger.debug('messages: ' + str(messages))

    return subject
# - end of create_subject


def update_subject_instance(instance, examyear, upload_dict, error_list, request):
    # --- update existing and new instance PR2019-06-06 PR2021-05-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_subject_instance -----')
        logger.debug('upload_dict: ' + str(upload_dict))

    if instance:
        save_changes = False
        save_changes_in_base = False

        caption = _('Subject')
        for field, new_value in upload_dict.items():
            if logging_on:
                logger.debug('field: ' + str(field))
                logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))

# - save changes in field 'code'
            if field == 'code':
                base = instance.base
                saved_value = getattr(base, field)
                if logging_on:
                    logger.debug('saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))

                if new_value != saved_value:
                    if logging_on:
                        logger.debug('new_value != saved_value')
    # - validate abbrev checks null, max_len, exists
                    #  msg_err = { 'field': 'code', msg_list: [text1, text2] }, (for use in imput modals)
                    msg_html = av.validate_subject_code_exists(
                        code=new_value,
                        cur_subject=instance
                    )
                    if msg_html:
                        error_list.append({'header': str(caption), 'class': 'alert-danger', 'msg_html': msg_html})
                    else:
     # - save field if changed and no_error
                        setattr(base, field, new_value)
                        save_changes_in_base = True

# - save changes in field 'name'
            elif field == 'name':
                saved_value = getattr(instance, field)
                if new_value != saved_value:
    # - validate abbrev checks null, max_len, exists
                    msg_html = av.validate_subject_name_exists(
                        name=new_value,
                        examyear=examyear,
                        cur_subject=instance
                    )
                    if msg_html:
                        error_list.append({'msg_html': msg_html, 'class': 'alert-danger'})
                    else:
                        # - save field if changed and no_error
                        setattr(instance, field, new_value)
                        save_changes = True

# 3. save changes in depbases
            elif field == 'depbases':
                saved_value = getattr(instance, field)
                uploaded_field_arr = new_value.split(';') if new_value else []

                checked_field_arr = []
                checked_field_str = None
                if uploaded_field_arr:
                    for base_pk_str in uploaded_field_arr:
                        base_pk_int = int(base_pk_str)
                        base_instance = sch_mod.Department.objects.get_or_none(
                            base=base_pk_int,
                            examyear=examyear
                        )
                        if base_instance:
                            checked_field_arr.append(base_pk_str)

                    if checked_field_arr:
                        checked_field_arr.sort()
                        checked_field_str = ';'.join(checked_field_arr)
                if checked_field_str != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

            elif field in ('sequence', 'addedbyschool'):
                saved_value = getattr(instance, field)
                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True
# --- end of for loop ---

# 5. save changes
        if save_changes or save_changes_in_base:
            try:
                if save_changes_in_base:
                    # also save instance when base has changed, to update modifiedat and modifiedby
                    instance.base.save()
                instance.save(request=request)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                header_txt = _('Update subject')
                msg_list = [_('An error occurred: ') + str(e),
                            _('The changes have not been saved.')]
                msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i>',
                                    str(_('The changes have not been saved.'))))
                error_list.append({'header': str(header_txt), 'class': 'border_bg_invalid', 'msg_html': msg_html})
                # error_list = [ { 'header': 'Header text', 'field': 'code', msg_html: 'line1 <br> line2',
                #                'class': 'border_bg_invalid')


# >>>>>>>  SCHEMEITEM >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def create_schemeitem(examyear, scheme, subj_pk, sjtp_pk, messages, request):
    # --- create schemeitem # PR2021-06-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_schemeitem ----- ')

    schemeitem = None

    has_error = False
    message_header = str(_('Create subject scheme subject'))
    subject = subj_mod.Subject.objects.get_or_none(
        pk=subj_pk,
        examyear=examyear
    )
    if subject is None:
        has_error = True
        messages.append({'class': "border_bg_invalid",
                         'header': message_header,
                         'msg_list': [str(_('Subject not found.'))]})

    subjecttype = subj_mod.Subjecttype.objects.get_or_none(
        pk=sjtp_pk,
        scheme=scheme
    )
    if subjecttype is None:
        has_error = True
        messages.append({'header': message_header,
                         'class': "border_bg_invalid",
                         'msg_html': str(_('Subject type not found.'))})
    if not has_error:
# - create and save schemeitem
        try:
            schemeitem = sbj_mod.Schemeitem(
                scheme=scheme,
                subject = subject,
                subjecttype = subjecttype
            )
            schemeitem.save(request=request)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            msg_html = [': '.join((str(_('An error occurred')),str(e))),
                        str(_("Subject scheme subject '%(val)s' could not be created.") % {'val': subject.name})]

            messages.append(
                {'class': "border_bg_invalid", 'header': message_header, 'msg_html': msg_html})

    if logging_on:
        logger.debug('schemeitem: ' + str(schemeitem))
        logger.debug('messages: ' + str(messages))

    return schemeitem

# - end of create_schemeitem


def delete_schemeitem(schemeitem, messages, request):
    # --- delete schemeitem # PR2021-06-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_schemeitem ----- ')
        logger.debug('subject: ' + str(schemeitem))

    deleted_row = None
    # get info from row before deleting it
    row_tobe_deleted = {'pk': schemeitem.pk,
                       'mapid': 'schemeitem_' + str(schemeitem.pk),
                        'subj_name': schemeitem.subject.name,
                       'deleted': True}
    subject_name = schemeitem.subject.name
    this_txt = _("Subject '%(tbl)s' of subject scheme '%(tbl)s'") % {'tbl': subject_name}
    header_txt = _("Delete subject from subject scheme")

# check if there are students with subjects with this schemeitem
    students_with_this_schemeitem_exist = stud_mod.Studentsubject.objects.filter(
        schemeitem=schemeitem
    ).exists()

    if logging_on:
        logger.debug('students_with_this_schemeitem_exist: ' + str(students_with_this_schemeitem_exist))

    students_with_this_schemeitem_exist = False
    if students_with_this_schemeitem_exist:
        deleted_ok = False
        msg_list = [
            _('There are candidates with subjects with this schemeitem.'),
            _("%(cpt)s could not be deleted.") % {'cpt': this_txt}
        ]
        msg_dict = {'class': "border_bg_invalid", 'header': header_txt, 'msg_list': msg_list}
        messages.append(msg_dict)

    else:
        err_list = []  # TODO
        scheme_pk = schemeitem.pk
        deleted_ok = sch_mod.delete_instance(schemeitem, messages, err_list, request, this_txt, header_txt)

   # - create deleted_row, to be returned to client
        # if deleting failed, schemeitem still exists and wil be returned to client, together with error message
        if deleted_ok:
            deleted_row = row_tobe_deleted

    if logging_on:
        logger.debug('messages' + str(messages))

    return deleted_ok, deleted_row
# - end of delete_schemeitem


def update_si_list(examyear, scheme, si_list, updated_rows, messages, error_list, request):
    # --- delete schemeitem # PR2021-06-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_si_list ----- ')
        logger.debug('si_list: ' + str(si_list))

# ++++ loop through list of schemeitems:
    for si_dict in si_list:
        schemeitem = None
        is_create = si_dict.get('create')
        is_delete = si_dict.get('delete')
        is_created = False

        if is_create:
            subj_pk = si_dict.get('subj_pk')
            sjtp_pk = si_dict.get('sjtp_pk')
            schemeitem = create_schemeitem(examyear, scheme, subj_pk, sjtp_pk, messages, request)
            if schemeitem:
                is_created = True

        elif is_delete:

# ++++ Delete schemeitem
# - get existing scheme item
            si_pk = si_dict.get('si_pk')
            schemeitem = sbj_mod.Schemeitem.objects.get_or_none(
                id=si_pk,
                scheme=scheme
            )

            deleted_ok, deleted_row = delete_schemeitem(schemeitem, messages, request)
            if deleted_ok:
                schemeitem = None
                updated_rows.append(deleted_row)

# - create schemeitem_rows[0], also when deleting failed (when deleted ok there is no subject, subject_row is made above)
        if schemeitem:
            schemeitem_rows = create_schemeitem_rows(
                examyear=examyear,
                schemeitem_pk=schemeitem.pk
            )

# - add messages to row (there is only 1 row
            if schemeitem_rows:
                schemeitem_row = schemeitem_rows[0]

                # - add error_list to subject_rows[0]
                if error_list:
                    # structure of error_list: [ { 'field': 'code', msg_list ['line 1', 'line 2'] } ]
                    # or general error:        [ { 'class': 'alert-danger', msg_list ['line 1', 'line 2'] } ]
                    schemeitem_row['error'] = error_list
                if is_created:
                    schemeitem_row['created'] = True

                updated_rows.append(schemeitem_row)
# - end of update_si_list


def update_schemeitem_instance(instance, examyear, upload_dict, updated_rows, error_list, request):
    # --- update existing and new instance PR2021-06-26
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_schemeitem_instance -----')
        logger.debug('upload_dict: ' + str(upload_dict))

    if instance:
        save_changes = False
        msg_header_txt = _("Update subject of subject scheme")

        for field, new_value in upload_dict.items():

            if field in ('gradetype', 'weight_se', 'weight_ce', 'multiplier', 'is_mandatory', 'is_mand_subj', 'is_combi',
                         'extra_count_allowed', 'extra_nocount_allowed',
                         'has_practexam', 'is_core_subject', 'is_mvt', 'is_wisk',

                         # not in use: "rule_final_vsbo", "rule_finalvsbo_notatevlex",
                         # not in use: "rule_final_havovwo", "rule_finalhavovwo_notatevlex",
                         "rule_avg_pece_sufficient", "rule_avg_pece_notatevlex",
                         "rule_grade_sufficient", "rule_gradesuff_notatevlex",
                         "rule_core_sufficient", "rule_core_notatevlex",

                         'ete_exam', 'otherlang',
                         'sr_allowed', 'max_reex', 'no_thirdperiod', 'no_exemption_ce'):

                saved_value = getattr(instance, field)
                if logging_on:
                    logger.debug('field: ' + str(field))
                    logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))
                    logger.debug('saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))

                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

                    if logging_on:
                        logger.debug('save_changes: ' + str(save_changes))
# --- end of for loop ---

# +++++ save changes
        if save_changes:
            try:
                instance.save(request=request)
                if logging_on:
                    otherlang = getattr(instance, 'otherlang')
                    logger.debug('instance: ' + str(instance))
                    logger.debug('otherlang: ' + str(otherlang))
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred: ')), '<br><i>', str(e), '</i><br>',
                            str(_('The changes have not been saved.'))))
                error_list.append({'header': msg_header_txt, 'class': "border_bg_invalid", 'msg_html': msg_html})

# - end of update_schemeitem_instance

# >>>>>>>>  SCHEME >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def update_scheme_instance(instance, examyear, upload_dict, updated_rows, error_list, request):
    # --- update existing and new instance PR2021-06-27 PR2021-11-28
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_scheme_instance -----')
        logger.debug('upload_dict: ' + str(upload_dict))

    if instance:
        save_changes_in_base = False
        save_changes = False

        msg_header_txt = _('Update subject scheme')

        for field, new_value in upload_dict.items():

            if logging_on:
                logger.debug('field: ' + str(field))
                logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))

# - save changes in field 'name'
            if field == 'name':
                saved_value = getattr(instance, field)
                if new_value != saved_value:
                    # - validate abbrev checks null, max_len, exists
                    has_error = av.validate_scheme_name_exists(new_value, examyear, error_list, instance)
                    if not has_error:
                        # - save field if changed and no_error
                        setattr(instance, field, new_value)
                        save_changes = True

            elif field in ('rule_avg_pece_sufficient', 'rule_avg_pece_notatevlex',
                            'rule_core_sufficient', 'rule_core_notatevlex'):
                saved_value = getattr(instance, field)
                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

            elif field in ('min_subjects', 'max_subjects', 'min_mvt', 'max_mvt',
                           'min_wisk', 'max_wisk', 'min_combi', 'max_combi', 'max_reex'):
                msg_html = None
                new_value_int = None

                if logging_on:
                    logger.debug('..........field: ' + str(field))

                if new_value:
                    # - check if value is positive whole number
                    if not new_value.isdecimal():
                        msg_html = str(_("'%(val)s' is not a valid number.") % {'val': new_value})
                    else:
                        new_value_int = int(new_value)
                        if logging_on:
                            logger.debug('new_value_int: <' + str(new_value_int) + '> ' + str(type(new_value_int)))
                        if field in ('min_subjects', 'min_mvt', 'min_wisk', 'min_combi'):
                            max_field = 'max_mvt' if field == 'min_mvt' else 'max_wisk' if field == 'min_wisk' else 'max_combi' if field == 'min_combi' else 'max_subjects'
                            max_subjects = getattr(instance, max_field)

                            if logging_on:
                                logger.debug('max_subjects: <' + str(max_subjects) + '> ' + str(type(max_subjects)))

                            if max_subjects and new_value_int > max_subjects:
                                msg_html = str(
                                    _("Minimum amount of subjects cannot be greater than maximum (%(val)s).") % {
                                        'val': max_subjects})
                        elif field in ('max_subjects', 'max_mvt', 'max_wisk', 'max_combi'):
                            min_field = 'min_mvt' if field == 'max_mvt' else 'min_wisk' if field == 'max_wisk' else 'min_combi' if field == 'max_combi' else 'min_subjects'
                            min_subjects = getattr(instance, min_field)

                            if logging_on:
                                logger.debug('min_subjects: <' + str(min_subjects) + '> ' + str(type(min_subjects)))

                            if min_subjects and new_value_int < min_subjects:
                                msg_html = str(
                                    _("Maximum amount of subjects cannot be fewer than minimum (%(val)s).") % {
                                        'val': min_subjects})
                        elif field == 'max_reex':
                            if not new_value_int:
                                msg_html = str(_('%(cpt)s cannot be blank.') % {'cpt': _("Maximum number of re-examinations")})
                            elif new_value_int < 0:
                                msg_html = str(_("Maximum number of re-examinations must be a positive whole number."))

                if msg_html:
                    msg_dict = {'field': field,
                                'header': msg_header_txt,
                                'class': 'border_bg_warning',
                                'msg_html': msg_html}
                    error_list.append(msg_dict)
                else:
                    # -note: value can be None, not when max_reex
                    saved_value = getattr(instance, field)
                    if logging_on:
                        logger.debug('saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))
                    if new_value_int != saved_value:
                        setattr(instance, field, new_value_int)
                        save_changes = True
                    if logging_on:
                        logger.debug('..........save_changes: ' + str(save_changes))
        # --- end of for loop ---

        # 5. save changes
        if save_changes or save_changes_in_base:
            try:
                if save_changes_in_base:
                    # also save instance when base has changed, to update modifiedat and modifiedby
                    instance.base.save()
                instance.save(request=request)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred: ')), str(e), '<br>',
                                    str(_('The changes have not been saved.'))))
                error_list.append({'header': msg_header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html})
            else:
# - create schemeitem_rows[0]
                scheme_rows = create_scheme_rows(
                    examyear=examyear,
                    scheme_pk=instance.pk
                )
                if scheme_rows:
                    updated_rows.append(scheme_rows[0])

# - end of update_scheme_instance




# >>>>>>>  SUBJECTTYPE >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def update_sjtp_list(examyear, scheme, sjtp_list, updated_rows, messages, request):
    # --- update_sjtp_list # PR2021-06-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_sjtp_list ----- ')
        logger.debug('sjtp_list: ' + str(sjtp_list))

    msg_header = _('Update character')
# ++++ loop through list of subjecttypes:
    for sjtp_dict in sjtp_list:
        subjecttype = None
        is_create = sjtp_dict.get('create')
        is_delete = sjtp_dict.get('delete')
        is_created = False

        if is_create:
            sjtpbase_pk = sjtp_dict.get('sjtpbase_pk')
            subjecttype = create_subjecttype(sjtpbase_pk, scheme, sjtp_dict, messages, msg_header, request)
            if subjecttype:
                is_created = True

        elif is_delete:

# ++++ Delete subjecttype
# - get existing subjecttype
            sjtp_pk = sjtp_dict.get('sjtp_pk')
            subjecttype = sbj_mod.Subjecttype.objects.get_or_none(
                id=sjtp_pk,
                scheme=scheme
            )
            # delete_subjecttype will set subjecttype to None if deleted_ok
            deleted_row = delete_subjecttype(subjecttype, messages, request)
            if deleted_row:
                updated_rows.append(deleted_row)

        if logging_on:
            logger.debug('subjecttype: ' + str(subjecttype))

# - create schemeitem_rows[0], also when deleting failed (when deleted ok there is no subject, subject_row is made above)
        if subjecttype:
            subjecttype_rows = create_subjecttype_rows(
                examyear=examyear,
                sjtp_pk=subjecttype.pk,
                cur_dep_only=False
            )
            if logging_on:
                logger.debug('subjecttype_rows: ' + str(subjecttype_rows))

# - messages will be attached to update_wrap, not to updated_rows
            if subjecttype_rows:
                subjecttype_row = subjecttype_rows[0]
                if is_created:
                    subjecttype_row['created'] = True

                updated_rows.append(subjecttype_row)
                if logging_on:
                    logger.debug('updated_rows: ' + str(updated_rows))
# - end of update_sjtp_list


def create_subjecttype(sjtpbase_pk, scheme, upload_dict, messages, msg_header, request):
    # --- create subjecttype # PR2021-06-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_subjecttype ----- ')

    subjecttype = None
    sjtpbase = None
    msg_header = _('Create character')

    if scheme:
# - get sjtpbase
        sjtpbase = get_subjecttypebase_instance(sjtpbase_pk, messages,
                                        msg_header, logging_on, request)
        if sjtpbase is None:
            msg_html = str(_("Base character not found."))
            msg_dict = {'header': str(msg_header), 'class': 'border_bg_invalid', 'msg_html': msg_html}
            messages.append(msg_dict)
        else:
    # - get values
                name = upload_dict.get ('name')
                if logging_on:
                    logger.debug('name: ' + str(name))

                msg_list = []
                has_error = False
        # - validate code and name. Function checks null, max_len, exists
                msg_html = av.validate_notblank_maxlength(name, c.MAX_LENGTH_NAME, _('The name'))
                if msg_html:
                    msg_list.append(msg_html)

        # - check if subjecttype name already exists

                msg_html = av.validate_subjecttype_name_abbrev_exists('name', name, scheme, subjecttype)
                if msg_html:
                    msg_list.append(msg_html)

        # - create and save subjecttype
                if len(msg_list) > 0:
                    msg_html = '<br>'.join(msg_list)
                    messages.append({'header': str(msg_header), 'class': "border_bg_invalid", 'msg_html': msg_html})
                else:
                    try:
                        # Don't create base record. Only use the default base records
                        subjecttype = sbj_mod.Subjecttype(
                            base=sjtpbase,
                            scheme=scheme,
                            name=name
                        )
                        subjecttype.save(request=request)

                    except Exception as e:
                        logger.error(getattr(e, 'message', str(e)))
                        caption = _('Character')
                        msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                                    str(_("%(cpt)s '%(val)s' could not be created.") % {'cpt': caption, 'val': name})))
                        messages.append({'header': str(msg_header), 'class': 'border_bg_invalid', 'msg_html': msg_html})

    if logging_on:
        logger.debug('subjecttype: ' + str(subjecttype))
        logger.debug('messages: ' + str(messages))

    return subjecttype
# - end of create_subjecttype


def delete_subjecttype(subjecttype, messages, request):
    # --- delete subjecttype # PR2021-06-23 PR2021-07-13
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_subjecttype ----- ')
        logger.debug('subjecttype: ' + str(subjecttype))

    subjecttype_pk = subjecttype.pk
    deleted_row = None
    this_txt = _("Character '%(tbl)s'") % {'tbl': subjecttype.name}
    header_txt = _("Delete character")

# check if there are students with subjects with this subjecttype
    students_with_this_subjecttype_exist = stud_mod.Studentsubject.objects.filter(
        schemeitem__subjecttype=subjecttype
    ).exists()

    if logging_on:
        logger.debug('students_with_this_subjecttype_exist: ' + str(students_with_this_subjecttype_exist))

    if students_with_this_subjecttype_exist:
        deleted_ok = False
        msg_html = ''.join((str(_('There are candidates with subjects with this character.')), '<br>',
                            str(_("%(cpt)s could not be deleted.") % {'cpt': this_txt})))
        msg_dict = {'class': 'border_bg_invalid', 'header': header_txt, 'msg_html': msg_html}
        messages.append(msg_dict)

    else:
        # delete_instance will set subjecttype to None if deleted_ok
        err_list = []  # TODO
        deleted_ok = sch_mod.delete_instance(subjecttype, messages, err_list, request, this_txt, header_txt)

    if deleted_ok:
    # - check if this subjecttype base has other child subjecttypes, delet if none found
        # PR2021-06-27 debug: Don't delete base subjecttypes without children: they may be used another time

   # - deleted_row gets value when deleted = ok, to be returnes to client
        deleted_row = {'pk': subjecttype_pk,
                       'mapid': 'subjecttype_' + str(subjecttype_pk),
                       'deleted': True}

    if logging_on:
        logger.debug('deleted_row' + str(deleted_row))
        logger.debug('messages' + str(messages))

    return deleted_row
# - end of delete_subjecttype


def update_subjecttype_instance(instance, scheme, upload_dict, error_list, request):
    # --- update existing and new instance PR2021-06-23
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_subjecttype_instance -----')
        logger.debug('upload_dict: ' + str(upload_dict))

    if instance:
        save_changes_in_base = False
        save_changes = False

        msg_header = _('Update character')

        for field, new_value in upload_dict.items():

            if logging_on:
                logger.debug('field: ' + str(field))
                logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))

# - save changes in field 'code'
            if field == 'sjtpbase_pk':
                base = None
                if new_value:
                    base = sbj_mod.Subjecttypebase.objects.get_or_none(
                        id=new_value
                    )
                if logging_on:
                    logger.debug('new_subjecttypebase: ' + str(base) + ' ' + str(type(base)))

                if base.pk != instance.base.pk:
                    if logging_on:
                        logger.debug('new_value != saved_value')
    # - validate abbrev checks null, max_len, exists
                    #  msg_err = { 'field': 'code', msg_list: [text1, text2] }, (for use in imput modals)
     # - save field if changed and no_error
                    setattr(base, field, new_value)
                    save_changes_in_base = True

# - save changes in field 'name'
            elif field in ('name', 'abbrev'):
                saved_value = getattr(instance, field)
                if new_value != saved_value:
    # - validate abbrev checks null, max_len, exists
                    msg_html = av.validate_subjecttype_name_abbrev_exists(field, new_value, scheme, instance)
                    if msg_html:
                        # add 'field' in error_list, to put old value back in field
                        # error_list will show mod_messages in RefreshDatarowItem
                        error_list.append({'field': field, 'header': msg_header, 'class': 'border_bg_warning', 'msg_html': msg_html})
                    else:
                        # - save field if changed and no_error
                        setattr(instance, field, new_value)
                        save_changes = True

            elif field in ('min_subjects', 'max_subjects',
                           'min_extra_nocount', 'max_extra_nocount',
                           'min_extra_counts', 'max_extra_counts'
                           ):
                msg_html = None

                if logging_on:
                    logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))
                    logger.debug('new_value.isdecimal: ' + str(new_value.isdecimal()))

# - check if value is positive whole number
                if new_value == '':
                    new_value = None

                if new_value is not None:
                    if not new_value.isdecimal():
                        msg_html = str(_("'%(val)s' is not a valid number.") % {'val': new_value})
                    else:
                        # TODO simplify code, also check for min max subjects when checking min_extra_nocount etc
                        new_value = int(new_value)
                        if field == 'min_subjects':
                            max_subjects = getattr(instance, 'max_subjects')
                            if max_subjects is not None and new_value > max_subjects:
                                msg_html = str(_("Minimum amount of %(cpt)s cannot be greater than maximum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': max_subjects})
                        elif field == 'max_subjects':
                            min_subjects = getattr(instance, 'min_subjects')
                            if min_subjects is not None and new_value < min_subjects:
                                msg_html = str(_("Maximum amount of %(cpt)s cannot be fewer than minimum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': min_subjects})

                        elif field == 'min_extra_nocount':
                            max_extra_nocount = getattr(instance, 'max_extra_nocount')
                            if max_extra_nocount is not None and new_value > max_extra_nocount:
                                msg_html = str(_("Minimum amount of %(cpt)s cannot be greater than maximum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': max_extra_nocount})
                        elif field == 'max_extra_nocount':
                            min_extra_nocount = getattr(instance, 'min_extra_nocount')
                            if min_extra_nocount is not None and new_value < min_extra_nocount:
                                msg_html = str(_("Maximum amount of %(cpt)s cannot be fewer than minimum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': min_extra_nocount})

                        elif field == 'min_extra_counts':
                            max_extra_counts = getattr(instance, 'max_extra_counts')
                            if max_extra_counts is not None and new_value > max_extra_counts:
                                msg_html = str(_("Minimum amount of %(cpt)s cannot be greater than maximum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': max_extra_counts})
                        elif field == 'max_extra_counts':
                            min_extra_counts = getattr(instance, 'min_extra_counts')
                            if min_extra_counts is not None and new_value < min_extra_counts:
                                msg_html = str(_("Maximum amount of %(cpt)s cannot be fewer than minimum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': min_extra_counts})

                if msg_html:
                    if logging_on:
                        logger.debug('msg_html: <' + str(msg_html) + '> ' + str(type(msg_html)))
                    # add 'field' in error_list, to put old value back in field
                    # error_list will show mod_messages in RefreshDatarowItem
                    error_list.append({'field': field,'header': msg_header,'class': 'border_bg_warning', 'msg_html': msg_html})
                else:
                    # -note: value can be None
                    saved_value = getattr(instance, field)
                    if logging_on:
                        logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))
                        logger.debug('saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))
                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True

            elif field == 'has_pws':
                saved_value = getattr(instance, field)
                if logging_on:
                    logger.debug('field: ' + str(field))
                    logger.debug('new_value: <' + str(new_value) + '> ' + str(type(new_value)))
                    logger.debug('saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))

                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# --- end of for loop ---

# +++++ save changes
        if save_changes or save_changes_in_base:
            try:
                if save_changes_in_base:
                    # also save instance when base has changed, to update modifiedat and modifiedby
                    instance.base.save()
                instance.save(request=request)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred: ')), '<br><i>', str(e), '</i><br>',
                                    str(_('The changes have not been saved.'))))
                error_list.append({'header': msg_header, 'class': 'border_bg_invalid', 'msg_html': msg_html})
            else:
# also update modified in scheme, otherwise it is difficult to find out if scheme has been changed
                try:
                    scheme = instance.scheme
                    scheme.save(request=request)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                awpr_logs.save_to_log(instance, 'u', request)

# - end of update_subjecttype_instance


def create_subjecttype_rows(examyear, scheme_pk=None, depbase=None, cur_dep_only=False, sjtp_pk=None, orderby_sequence=False):
    # --- create rows of all subjecttypes of this examyear / country  PR2021-06-24
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_subjecttype_rows ============= ')
        logger.debug('cur_dep_only: ' + str(cur_dep_only))
        logger.debug('examyear: ' + str(examyear))
        logger.debug('scheme_pk: ' + str(scheme_pk))
        logger.debug('depbase: ' + str(depbase))
        logger.debug('sjtp_pk: ' + str(sjtp_pk))

    subjecttype_rows =[]
    if examyear:
        sql_keys = {'ey_id': examyear.pk}
        sql_list = ["SELECT sjtp.id, sjtp.base_id, CONCAT('subjecttype_', sjtp.id::TEXT) AS mapid,",
            "sjtpbase.id AS sjtpbase_id, sjtpbase.code AS sjtpbase_code, sjtpbase.name AS sjtpbase_name,",
            "sjtpbase.sequence AS sjtpbase_sequence, sjtp.name, sjtp.abbrev,",
            "sjtp.min_subjects, sjtp.max_subjects, sjtp.min_extra_nocount, sjtp.max_extra_nocount,",
            "sjtp.min_extra_counts, sjtp.max_extra_counts, sjtp.has_pws,",
            "lvl.id AS lvl_id, lvl.abbrev AS lvl_abbrev, sct.id AS sct_id, sct.abbrev AS sct_abbrev,",
            "dep.base_id AS depbase_id, lvl.base_id AS lvlbase_id, sct.base_id AS sctbase_id,",
            "ey.code AS ey_code,",
            "dep.id AS department_id, depbase.code AS depbase_code, scheme.id AS scheme_id, scheme.name AS scheme_name,",
            "sjtp.modifiedby_id, sjtp.modifiedat, SUBSTRING(au.username, 7) AS modby_username",

            "FROM subjects_subjecttype AS sjtp",
            "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = sjtp.base_id)",
            "INNER JOIN subjects_scheme AS scheme ON (scheme.id = sjtp.scheme_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",

            "LEFT JOIN accounts_user AS au ON (au.id = sjtp.modifiedby_id)",

            "WHERE ey.id = %(ey_id)s::INT"]

        if sjtp_pk:
            sql_keys['sjtp_pk'] = sjtp_pk
            sql_list.append("AND sjtp.id = %(sjtp_pk)s::INT")

        elif scheme_pk:
            sql_keys['scheme_pk'] = scheme_pk
            sql_list.append("AND scheme.id = %(scheme_pk)s::INT")

        elif cur_dep_only:
            depbase_lookup = None
            if depbase:
                department = sch_mod.Department.objects.get_or_none(examyear=examyear, base=depbase)
                if department:
                    depbase_lookup = ''.join( ('%;', str(depbase.pk), ';%') )
            if logging_on:
                logger.debug('depbase_lookup: ' + str(depbase_lookup))

            if depbase_lookup:
                sql_keys['depbase_pk'] = depbase_lookup
                sql_list.append("AND CONCAT(';', sct.depbases::TEXT, ';') LIKE %(depbase_pk)s::TEXT")
            else:
                sql_list.append("AND FALSE")

        if orderby_sequence:
            sql_list.append("ORDER BY sjtpbase.sequence")

        sql_list.append("ORDER BY sjtp.id")

        sql = ' '.join(sql_list)
        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            subjecttype_rows = af.dictfetchall(cursor)

    return subjecttype_rows
# --- end of create_subjecttype_rows


def create_subjecttypebase_rows(sjtbase_pk=None):
    # --- create rows of all subjecttypes of this examyear / country  PR2021-06-22
    #logger.debug(' =============== create_subjecttypebase_rows ============= ')
    rows =[]

    sql_keys = {}

    sql_list = ["SELECT sjtbase.id, CONCAT('subjecttypebase_', sjtbase.id::TEXT) AS mapid,",
        "sjtbase.code, sjtbase.name, sjtbase.abbrev, sjtbase.sequence",
        "FROM subjects_subjecttypebase AS sjtbase"]

    if sjtbase_pk:
        sql_keys['sjtbase_pk'] = sjtbase_pk
        sql_list.append("WHERE sjtbase.id = %(sjtbase_pk)s::INT")

    sql_list.append("ORDER BY sjtbase.id")

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    return rows
# --- end of create_subjecttypebase_rows




# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


def create_scheme_rows(examyear, scheme_pk=None, cur_dep_only=False, depbase=None):
    # --- create rows of all schemes of this examyear PR2020-11-16 PR2021-06-24
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_scheme_rows ============= ')
        logger.debug('cur_dep_only: ' + str(cur_dep_only))
        logger.debug('scheme_pk: ' + str(scheme_pk))

    scheme_rows = []
    if examyear:
        sql_keys = {'ey_id': examyear.pk}
        sql_list = ["SELECT scheme.id, scheme.department_id, scheme.level_id, scheme.sector_id,",
            "CONCAT('scheme_', scheme.id::TEXT) AS mapid,",
            "scheme.name, scheme.min_subjects, scheme.max_subjects, scheme.min_mvt, scheme.max_mvt, ",
            "scheme.min_wisk, scheme.max_wisk, scheme.min_combi, scheme.max_combi, scheme.max_reex,",

            "scheme.rule_avg_pece_sufficient, scheme.rule_avg_pece_notatevlex,",
            "scheme.rule_core_sufficient, scheme.rule_core_notatevlex,",

            "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ey.code AS ey_code,",
            "dep.base_id AS depbase_id, lvl.base_id AS lvlbase_id, sct.base_id AS sctbase_id,",
            "depbase.code AS depbase_code,"
            "scheme.modifiedby_id, scheme.modifiedat,",
            "SUBSTRING(au.username, 7) AS modby_username",

            "FROM subjects_scheme AS scheme",
            "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = scheme.modifiedby_id)",

            "WHERE dep.examyear_id = %(ey_id)s::INT"]

        if scheme_pk:
            sql_keys['scheme_id'] = scheme_pk
            sql_list.append('AND scheme.id = %(scheme_id)s::INT')
        elif cur_dep_only:
            if depbase:
                sql_keys['db_id'] = depbase.pk
                sql_list.append('AND dep.base_id = %(db_id)s::INT')
            else:
                sql_list.append("AND FALSE")

        sql_list.append("ORDER BY scheme.id")

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

    return rows
# --- end of create_scheme_rows


def create_schemeitem_rows(examyear, schemeitem_pk=None, scheme_pk=None,
                           cur_dep_only=False, depbase=None, orderby_name=False, orderby_sjtpbase_sequence=False):
    # --- create rows of all schemeitems of this examyear PR2020-11-17 PR2021-07-01

    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug(' =============== create_schemeitem_rows ============= ')
        logger.debug('examyear: ' + str(examyear) + ' ' + str(type(examyear)))
        logger.debug('schemeitem: ' + str(schemeitem_pk) + ' ' + str(type(schemeitem_pk)))
        logger.debug('depbase: ' + str(depbase) + ' ' + str(type(depbase)))

    schemeitem_rows = []
    try:
        if examyear :
            sql_keys = {'ey_id': examyear.pk}
            sql_list = ["SELECT si.id, si.scheme_id, scheme.department_id, scheme.level_id, scheme.sector_id,",
                "CONCAT('schemeitem_', si.id::TEXT) AS mapid,",
                "si.subject_id AS subj_id, subj.name AS subj_name, subjbase.id AS subjbase_id, subjbase.code AS subj_code,",
                "sjtpbase.code AS sjtpbase_code, sjtpbase.sequence AS sjtpbase_sequence,",
                "sjtp.id AS sjtp_id, sjtp.name AS sjtp_name, sjtp.abbrev AS sjtp_abbrev,",
                "sjtp.has_prac AS sjtp_has_prac, sjtp.has_pws AS sjtp_has_pws,",
                "sjtp.min_subjects AS sjtp_min_subjects, sjtp.max_subjects AS sjtp_max_subjects, ",
                "scheme.name AS scheme_name, scheme.fields AS scheme_fields,",
                "depbase.id AS depbase_id, depbase.code AS depbase_code,",
                "lvl.base_id AS lvlbase_id, sct.base_id AS sctbase_id,",
                "lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",

                "ey.code, ey.no_practexam AS ey_no_practexam, ey.sr_allowed AS ey_sr_allowed,"
                "ey.no_centralexam AS ey_no_centralexam, ey.no_thirdperiod AS ey_no_thirdperiod,",

                "si.gradetype, si.weight_se, si.weight_ce, si.multiplier, si.ete_exam, si.otherlang,",
                "si.is_mandatory, si.is_mand_subj_id,",
                "si.is_combi, si.extra_count_allowed, si.extra_nocount_allowed,",
                "si.has_practexam, si.is_core_subject, si.is_mvt, si.is_wisk,",

                "si.rule_grade_sufficient, si.rule_gradesuff_notatevlex,",
                "si.sr_allowed, si.max_reex, si.no_thirdperiod, si.no_exemption_ce,",

                "si.modifiedby_id, si.modifiedat,",
                "SUBSTRING(au.username, 7) AS modby_username",

                "FROM subjects_schemeitem AS si",
                "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                "INNER JOIN subjects_subjecttype AS sjtp ON (sjtp.id = si.subjecttype_id)",
                "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = sjtp.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",
                "LEFT JOIN accounts_user AS au ON (au.id = si.modifiedby_id)",

                "WHERE dep.examyear_id = %(ey_id)s::INT"]

            if schemeitem_pk:
                # when schemeitem_pk has value: skip other filters
                sql_keys['si_pk'] = schemeitem_pk
                sql_list.append('AND si.id = %(si_pk)s::INT')

            elif scheme_pk:
                sql_keys['scheme_pk'] = scheme_pk
                sql_list.append("AND scheme.id = %(scheme_pk)s::INT")

            elif cur_dep_only:
                if depbase:
                    sql_keys['depbase_pk'] = depbase.pk
                    sql_list.append('AND depbase.id = %(depbase_pk)s::INT')
                else:
                    sql_list.append("AND FALSE")

            if orderby_name:
                sql_list.append('ORDER BY LOWER(scheme.name), LOWER(subj.name)')
            elif orderby_sjtpbase_sequence:
                sql_list.append('ORDER BY sjtpbase.sequence')
            else:
                sql_list.append('ORDER BY si.id')

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('orderby_name: ' + str(orderby_name) )
                logger.debug('orderby_sjtpbase_sequence: ' + str(orderby_sjtpbase_sequence) )
                logger.debug('sql_keys: ' + str(sql_keys) )
                logger.debug('sql: ' + str(sql) )

            newcursor = connection.cursor()
            newcursor.execute(sql, sql_keys)
            schemeitem_rows = af.dictfetchall(newcursor)

            if logging_on:
                logger.debug('schemeitem_rows: ' + str(schemeitem_rows) )

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return schemeitem_rows
# --- end of create_schemeitem_rows

#################

def get_scheme_si_dict(examyear_pk, depbase_pk, scheme_pk=None, schemeitem_pk=None):
    # PR2021-12-13
    # --- create dict with all schemitems of this examyear, this department
    # used to validate studsubj and grades, not to make changes
    # lookup key = schemeitem_pk
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== get_scheme_si_dict ============= ')
        logger.debug('examyear_pk:   ' + str(examyear_pk) + ' ' + str(type(examyear_pk)))
        logger.debug('depbase_pk:    ' + str(depbase_pk) + ' ' + str(type(depbase_pk)))
        logger.debug('scheme_pk:     ' + str(scheme_pk) + ' ' + str(type(scheme_pk)))
        logger.debug('schemeitem_pk: ' + str(schemeitem_pk) + ' ' + str(type(schemeitem_pk)))

    schemeitem_dict = {}
    try:
        if examyear_pk and depbase_pk:
            sql_keys = {'ey_id': examyear_pk, 'depbase_pk': depbase_pk}
            sql_list = ["SELECT si.id, subj.name AS subj_name, subjbase.code AS subj_code,",
                "sjtpbase.code AS sjtpbase_code,",

                "scheme.name AS scheme_name, scheme.max_reex AS scheme_max_reex,",
                # TODO check if these will be used
                #"scheme.min_subjects AS sch_min_subjects, scheme.max_subjects AS sch_max_subjects,",
                #"scheme.min_extra_nocount AS sch_min_extra_nocount, scheme.max_extra_nocount AS sch_max_extra_nocount,",
                #"scheme.min_extra_counts AS sch_min_extra_counts, scheme.max_extra_counts AS sch_max_extra_counts,",

                "sjtp.name AS sjtp_name, sjtp.abbrev AS sjtp_abbrev,",
                "sjtp.has_prac AS sjtp_has_prac, sjtp.has_pws AS sjtp_has_pws,",
                # TODO check if these will be used
                #"sjtp.min_subjects AS sjtp_min_subjects, sjtp.max_subjects AS sjtp_max_subjects,",
                #"sjtp.min_extra_nocount AS sjtp_min_extra_nocount, sjtp.max_extra_nocount AS sjtp_max_extra_nocount,",
                #"sjtp.min_extra_counts AS sjtp_min_extra_counts, sjtp.max_extra_counts AS sjtp_max_extra_counts,",

                "ey.code AS ey_code, ey.no_practexam AS ey_no_practexam, ey.sr_allowed AS ey_sr_allowed,"
                "ey.no_centralexam AS ey_no_centralexam, ey.no_thirdperiod AS ey_no_thirdperiod,",

                "depbase.code AS depbase_code, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",
                "dep.level_req, dep.sector_req, dep.has_profiel,",
                "si.ete_exam, si.otherlang,",
                "si.gradetype, si.weight_se, si.weight_ce, si.multiplier,",
                "si.is_mandatory, si.is_mand_subj_id,",
                "si.is_combi, si.extra_count_allowed, si.extra_nocount_allowed,",
                "si.has_practexam, si.is_core_subject, si.is_mvt, si.is_wisk,",

                "si.rule_grade_sufficient, si.rule_gradesuff_notatevlex,",

                "si.sr_allowed, si.max_reex, si.no_thirdperiod, si.no_exemption_ce",

                "FROM subjects_schemeitem AS si",
                "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                "INNER JOIN subjects_subjecttype AS sjtp ON (sjtp.id = si.subjecttype_id)",
                "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = sjtp.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",

                "WHERE dep.examyear_id = %(ey_id)s::INT",
                "AND depbase.id = %(depbase_pk)s::INT"
                ]
            if schemeitem_pk:
                sql_keys['si_id'] = schemeitem_pk
                sql_list.append("AND si.id = %(si_id)s::INT")
            elif scheme_pk:
                sql_keys['schm.id'] = scheme_pk
                sql_list.append("AND scheme.id = %(schm.id)s::INT")
            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = af.dictfetchall(cursor)

            for row in rows:
                si_pk = row.get('id')
                if si_pk:
                    schemeitem_dict[si_pk] = row

                if logging_on:
                    logger.debug('row: ' + str(row))

        if logging_on:
            logger.debug('schemeitem_dict: ' + str(schemeitem_dict))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return schemeitem_dict
# --- end of get_scheme_si_dict


###################
@method_decorator([login_required], name='dispatch')
class ExamDownloadExamView(View):  # PR2021-05-06

    def get(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('===== ExamDownloadExamView ===== ')
            logger.debug('list: ' + str(list) + ' ' + str(type(list)))

        # function creates, Exam pdf file

        response = None
        exam_pk = None
        #try:

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

# - reset language
            # PR2021-05-08 debug: without activate text will not be translated
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get order_pk_list from parameter 'list
            if list:
                # list: 10 <class 'str'>
                exam_pk = int(list)

                #list_dict = json.loads(list)
                #logger.debug('list_dict: ' + str(list_dict))

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

            if logging_on:
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))
                logger.debug('exam_pk: ' + str(exam_pk))

            if sel_examyear and exam_pk:
                sel_exam_instance = subj_mod.Exam.objects.get_or_none(
                    pk=exam_pk,
                    subject__examyear=sel_examyear)
                if logging_on:
                    logger.debug('sel_exam_instance: ' + str(sel_exam_instance))

                # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

                # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                #temp_file = tempfile.TemporaryFile()
                # canvas = Canvas(temp_file)

                buffer = io.BytesIO()
                canvas = Canvas(buffer)

                # Start writing the PDF here
                printpdf.draw_exam(canvas, sel_exam_instance, sel_examyear, user_lang)
                #test_pdf(canvas)
                # testParagraph_pdf(canvas)

                if logging_on:
                    logger.debug('end of draw_exam')

                canvas.showPage()
                canvas.save()

                pdf = buffer.getvalue()
                # pdf_file = File(temp_file)

                # was: buffer.close()

                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="testpdf.pdf"'
                #response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

                response.write(pdf)

        #except Exception as e:
       #     logger.error(getattr(e, 'message', str(e)))
       #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of ExamDownloadExamView

@method_decorator([login_required], name='dispatch')
class ExamDownloadGradeExamView(View):  # PR2022-01-29

    def get(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('===== ExamDownloadGradeExamView ===== ')
            logger.debug('list: ' + str(list) + ' ' + str(type(list)))

        # function creates, Exam pdf file with answers

        response = None
        grade_pk = None
        #try:

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

# - reset language
            # PR2021-05-08 debug: without activate text will not be translated
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get order_pk_list from parameter 'list
            if list:
                # list: 10 <class 'str'>
                grade_pk = int(list)

                #list_dict = json.loads(list)
                #logger.debug('list_dict: ' + str(list_dict))

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

            if logging_on:
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))
                logger.debug('grade_pk: ' + str(grade_pk))

            if sel_examyear and grade_pk:

                sel_grade_instance = stud_mod.Grade.objects.get_or_none(
                    pk=grade_pk,
                    studentsubject__student__school__base_id=sel_school.base_id)
                if logging_on:
                    logger.debug('sel_grade_instance: ' + str(sel_grade_instance))

                # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3
                sel_ce_exam_instance = None
                if sel_grade_instance:
                    sel_ce_exam_instance = sel_grade_instance.ce_exam
                if logging_on:
                    logger.debug('sel_ce_exam_instance: ' + str(sel_ce_exam_instance))

                if sel_ce_exam_instance:
                    # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                    #temp_file = tempfile.TemporaryFile()
                    # canvas = Canvas(temp_file)

                    buffer = io.BytesIO()
                    canvas = Canvas(buffer)

                    # Start writing the PDF here
                    printpdf.draw_grade_exam(canvas, sel_grade_instance, sel_ce_exam_instance, sel_examyear, user_lang)
                    #test_pdf(canvas)
                    # testParagraph_pdf(canvas)

                    if logging_on:
                        logger.debug('end of draw_exam')

                    canvas.showPage()
                    canvas.save()

                    pdf = buffer.getvalue()
                    # pdf_file = File(temp_file)

                    # was: buffer.close()

                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = 'inline; filename="testpdf.pdf"'
                    #response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

                    response.write(pdf)

        #except Exception as e:
       #     logger.error(getattr(e, 'message', str(e)))
       #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of ExamDownloadGradeExamView



@method_decorator([login_required], name='dispatch')
class ExamDownloadExamJsonView(View):  # PR2021-05-06

    def get(self, request, list):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('===== ExamDownloadExamJsonView ===== ')
            logger.debug('list: ' + str(list) + ' ' + str(type(list)))

        response = None

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

            # - get exam_pk from parameter 'list'
            if list:
                # list: 10 <class 'str'>
                exam_pk = int(list)
            exam_pk = None
# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, is_locked, \
                examyear_published, school_activated, requsr_same_schoolNIU = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

# - get selected examperiod, examtype, subject_pk from usersettings
            sel_examperiod, sel_examtype, sel_subject_pkNIU = dl.get_selected_experiod_extype_subjbase_from_usersetting(request)

            if logging_on:
                logger.debug('sel_examperiod: ' + str(sel_examperiod))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))
                logger.debug('exam_pk: ' + str(exam_pk))

            if sel_examperiod:
                examenlijst = []

                # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
                crit = Q(subject__examyear=sel_examyear)
                # - exclude this subject base in case it is an existing subject
                if exam_pk:
                    crit.add(Q(pk=exam_pk), crit.connector)
                exam_instances = subj_mod.Exam.objects.filter(crit)

                if exam_instances:
                    for exam_instance in exam_instances:
                        exam_dict = {}
                        subject = exam_instance.subject
                        examyear = subject.examyear

                        exam_dict['code'] = subject.base.code
                        exam_dict['vak'] = subject.name

                # - create string with department abbrev
                        exam_dict['afdeling'] = exam_instance.department.base.code

                # - create string with level abbrevs
                        if exam_instance.level:
                            exam_dict['leerweg'] = exam_instance.level.abbrev

                        exam_dict['examensoort'] = c.get_examtype_caption(exam_instance.examtype)
                        exam_dict['aantal vragen'] = exam_instance.amount if exam_instance.amount else 0
                        exam_dict['opgaven'] = get_assignment_list(exam_instance)
                        exam_dict['kandidaten'] = get_answers_list(exam_instance)

                        examenlijst.append(exam_dict)

                examens_dict = {
                    'examenjaar': sel_examyear.code,
                    'tijdvak': c.get_examperiod_caption(sel_examperiod),
                    'examens': examenlijst
                }

                response = HttpResponse(json.dumps(examens_dict), content_type="application/json")
                response['Content-Disposition'] = 'exam_dict; filename="testjson.json"'
                #response['Content-Disposition'] = 'inline; filename="testjson.pdf"'

        # except Exception as e:
        #     logger.error(getattr(e, 'message', str(e)))
        #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        #return JsonResponse({'test': 'json'})

# - end of ExamDownloadExamJsonView


def get_assignment_list(sel_exam_instance):
    # - create list with assignments PR2021-05-08  PR2021-05-24

    amount = getattr(sel_exam_instance, 'amount')

    assignment_list = []

    if amount:
        assignment_dict = {}
        assignment = getattr(sel_exam_instance, 'assignment')
        if assignment:
            for qa in assignment.split('|'):
                qa_arr = qa.split(':')
                if len(qa_arr) > 0:
                    if qa_arr[1]:
                        q_nr = int(qa_arr[0])
                        value_list = qa_arr[1].split(';')
                        assignment_dict[q_nr] = {
                            'max_score': value_list[0] if value_list[0] else '',
                            'max_char': value_list[1] if value_list[1] else '',
                            'min_score': value_list[2] if value_list[2] else ''
                        }

        keys_dict = {}
        keys = getattr(sel_exam_instance, 'keys')
        if keys:
            for qk in keys.split('|'):
                qk_arr = qk.split(':')
                if len(qk_arr) > 0:
                    if qk_arr[1]:
                        qk_nr = int(qk_arr[0])
                        value_list = qk_arr[1].split(';')
                        keys_dict[qk_nr] = {
                            'keys': value_list[0] if value_list[0] else ''
                        }

        for q_number in range(1, amount + 1):  # range(start_value, end_value, step), end_value is not included!
            if q_number in assignment_dict:
                exam_dict = {'nr': q_number}
                max_score = af.get_dict_value(assignment_dict, (q_number, 'max_score'), '')
                max_score_int = int(max_score) if max_score else 0
                max_char = af.get_dict_value(assignment_dict, (q_number, 'max_char'), '')
                is_multiple_choice = True if max_char else False

                if is_multiple_choice:
                    asc_code = ord(max_char.lower())
                    alternatives = asc_code - 96

                    keys = af.get_dict_value(keys_dict, (q_number, 'keys'), '')
                    logger.debug('keys: ' + str(keys) + ' ' + str(type(keys)))
                    key_list = list(keys)
                    logger.debug('key_list: ' + str(key_list) + ' ' + str(type(key_list)))
                    key_int_list = []
                    for key_str in key_list:
                        logger.debug('key_str: ' + str(key_str) + ' ' + str(type(key_str)))
                        asc_code = ord(key_str.lower())
                        logger.debug('asc_code: ' + str(asc_code) + ' ' + str(type(asc_code)))
                        key_int = asc_code - 96

                        logger.debug('alternatives: ' + str(alternatives) + ' ' + str(type(alternatives)))
                        if key_int < 1 or key_int > alternatives:
                            key_int = -1
                        logger.debug('key_int: ' + str(key_int) + ' ' + str(type(key_int)))
                        key_int_list.append(key_int)
                        logger.debug('key_int_list: ' + str(key_int_list) + ' ' + str(type(key_int_list)))

                    exam_dict['opgavetype'] = 'Meerkeuze'
                    exam_dict['alternatieven'] = alternatives
                    exam_dict['sleutel'] = key_int_list
                else:
                    exam_dict['opgavetype'] = 'Open'
                    exam_dict['maximum score'] = max_score_int

                assignment_list.append(exam_dict)

    return assignment_list


def get_answers_list(sel_exam_instance):
    # - create dict with answers PR2021-05-08  PR2021-05-24

    answer_dict = {}
    answer_list = []

    amount = getattr(sel_exam_instance, 'amount')
    if amount:
        grades = stud_mod.Grade.objects.filter(exam=sel_exam_instance)
        if grades:
            for grade in grades:
                if grade.answers:
                    school_code = grade.studentsubject.student.school.base.code

                    a_dict = {}
                    for qa in grade.answers.split('|'):
                        qa_arr = qa.split(':')
                        if len(qa_arr) > 0:
                            if qa_arr[1]:
                                q_nr = int(qa_arr[0])
                                value_str = qa_arr[1]
                                a_dict[q_nr] = value_str
                    logger.debug('a_dict: ' + str(a_dict) + ' ' + str(type(a_dict)))

                    a_list = []
                    for q_number in range(1, amount + 1):  # range(start_value, end_value, step), end_value is not included!
                        value_int = 0
                        if q_number in a_dict:
                            value_str = a_dict.get(q_number)
                            if value_str:
                                is_multiple_choice = True if not value_str.isnumeric() else False
                                if is_multiple_choice:
                                    value_lc = value_str.lower()
                                    if value_lc == 'x':
                                        value_int = -1
                                    else:
                                        logger.debug('value_str: ' + str(value_str) + ' ' + str(type(value_str)))
                                        asc_code = ord(value_lc)
                                        logger.debug('asc_code: ' + str(asc_code) + ' ' + str(type(asc_code)))
                                        value_int = asc_code - 96
                                else:
                                    value_int = int(value_str)
                        a_list.append(value_int)

                    answer_list.append({'school': school_code, 'responses': a_list} )

    return answer_list


def get_department_codes(sel_exam_instance, examyear):
    # - create string with depbase codes PR2021-05-09
    dep_codes = ''
    depbases = sel_exam_instance.depbases
    if depbases:
        arr = depbases.split(';')
        if arr:
            for pk_str in arr:
                if pk_str:
                    pk_int = int(pk_str)
                    department = sch_mod.Department.objects.get_or_none(
                        base_id=pk_int,
                        examyear=examyear
                    )
                    if department:
                        if dep_codes:
                            dep_codes += ', '
                        dep_codes += department.base.code
    return dep_codes


# NIU, may be used for other instances with depbases
def get_department_abbrevs(sel_exam_instance, examyear):
    # - create string with depbase abbrevs PR2021-05-08
    dep_abbrevs = ''
    depbases = sel_exam_instance.depbases
    if depbases:
        arr = depbases.split(';')
        if arr:
            for pk_str in arr:
                if pk_str:
                    pk_int = int(pk_str)
                    department = sch_mod.Department.objects.get_or_none(
                        base_id=pk_int,
                        examyear=examyear
                    )
                    if department:
                        if dep_abbrevs:
                            dep_abbrevs += ', '
                        dep_abbrevs += department.abbrev
    return dep_abbrevs


def get_level_abbrevs(exam_instance, examyear):
    # - create string with level abbrevs PR2021-05-08
    level_names = ''
    levelbases = exam_instance.levelbases
    if levelbases:
        arr = levelbases.split(';')
        if arr:
            for pk_str in arr:
                if pk_str:
                    pk_int = int(pk_str)
                    level = subj_mod.Level.objects.get_or_none(
                        base_id=pk_int,
                        examyear=examyear
                    )
                    if level:
                        if level_names:
                            level_names += ', '
                        level_names += level.abbrev
    return level_names


def check_verifcode_local(upload_dict, request ):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('  ----- check_verifcode_local -----')

    form_name = upload_dict.get('form')
    verif_key = upload_dict.get('verificationkey')
    verif_code = upload_dict.get('verificationcode')
    if logging_on:
        logger.debug('verif_key: ' + str(verif_key))
        logger.debug('verif_code: ' + str(verif_code))

    is_ok, is_expired = False, False
    msg_html, msg_txt = None, None

    if form_name and verif_key and verif_code:
        key_code = '_'.join((verif_key, verif_code))
    # - get saved key_code
        saved_dict = acc_view.get_usersetting_dict(c.KEY_VERIFICATIONCODE, request)
        if logging_on:
            logger.debug('key_code: ' + str(key_code))
            logger.debug('saved_dict: ' + str(saved_dict))

        if saved_dict:
    # - check if code is expired:
            saved_expirationtime = saved_dict.get('expirationtime')
            if logging_on:
                logger.debug('saved_expirationtime: ' + str(saved_expirationtime))
            # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
            now_iso = datetime.now().isoformat()
            if logging_on:
                logger.debug('saved_expirationtime: ' + str(saved_expirationtime))
                logger.debug('now_iso: ' + str(now_iso))
            if now_iso > saved_expirationtime:
                is_expired = True
                msg_txt = _("The verificationcode has expired.")
            else:
    # - check if code is correct:
                saved_form = saved_dict.get('form')
                saved_key_code = saved_dict.get('key_code')
                if logging_on:
                    logger.debug('saved_form: ' + str(saved_form))
                    logger.debug('saved_key_code: ' + str(saved_key_code))

                if saved_form == form_name and key_code == saved_key_code:
                    is_ok = True
                else:
                    msg_txt = _("The verificationcode you have entered is not correct.")

    # - delete setting when expired or ok
            if is_ok or is_expired:
                acc_view.set_usersetting_dict(c.KEY_VERIFICATIONCODE, None, request)

    if logging_on:
        logger.debug('is_ok: ' + str(is_ok))
        logger.debug('is_expired: ' + str(is_expired))
    if msg_txt:
        msg_html = ''.join(("<div class='p-2 border_bg_invalid'>",
                            "<p class='pb-2'>",
                            str(msg_txt),
                            '</p>'))

    return is_ok, msg_html
# - end of check_verifcode_local
##########################################################

def create_departmentbase_dictlist(examyear_instance):  # PR2021-09-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_departmentbase_dictlist -----')

    # PR2021-08-20 functions creates ordered dictlist of all departments of this exam year of all countries
    # NOTE: use examyear.code (integer field) to filter on examyear. This way depbases from SXM and CUR are added to list
    # PR2021-09-02 debug: filter on examyear.code returned each depbase twice. Select ey_pk, same depbase is uses in Cur and SXM
    sql_keys = {'ey_pk': examyear_instance.pk}
    sql_list = [
        "SELECT depbase.id AS depbase_id, depbase.code AS depbase_code, dep.name AS dep_name, dep.level_req AS dep_level_req ",

        "FROM schools_department AS dep",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",

        "WHERE ey.id = %(ey_pk)s::INT",
        "ORDER BY dep.sequence"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        dictlist = af.dictfetchall(cursor)

    if logging_on:
        logger.debug('dictlist: ' + str(dictlist))

    return dictlist
# --- end of create_departmentbase_dictlist


def create_levelbase_dictlist(examyear_instance):  # PR2021-09-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_levelbase_dictlist -----')

    # PR2021-09-01 functions creates ordered dictlist of all levels of this exam year of all countries
    # NOTE: use examyear.code (integer field) to filter on examyear. This way lvlbases from SXM and CUR are added to list
    # also add row with pk = 0 for Havo / Vwo

    # PR2021-09-02 debug: filter on examyear.code returned each depbase twice. Select ey_pk, same depbase is uses in Cur and SXM

    # fields are lvlbase_id, lvlbase_code, lvl_name",
    sql_keys = {'ey_pk': examyear_instance.pk}
    sql_list = [
        "SELECT lvlbase.id AS lvlbase_id, lvlbase.code AS lvlbase_code, lvl.name AS lvl_name ",

        "FROM subjects_level AS lvl",
        "INNER JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = lvl.examyear_id)",

        "WHERE ey.id = %(ey_pk)s::INT",
        "ORDER BY lvl.sequence"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        dictlist = af.dictfetchall(cursor)

    # add row with pk = 0 for Havo / Vwo
    dictlist.append({'lvlbase_id': 0, 'lvlbase_code': '', 'lvl_name': ''})

    if logging_on:
        logger.debug('dictlist: ' + str(dictlist))

    return dictlist
# --- end of create_levelbase_dictlist


def create_schoolbase_dictlist(examyear, request):  # PR2021-08-20 PR2021-10-14
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug ('----- create_schoolbase_dictlist -----')

    # PR2021-08-20 functions creates ordered dictlist of all schoolbase_pk, schoolbase_code and school_name
    # - of this exam year, of all countries
    # - country: when req_usr country = curacao: include all schools (inluding SXM schools)
    #           when req_usr country = sxm: include only SXM schools

    # - skip schools of other organizations than schools
    # - also add admin organization (ETE, DOE), for extra for ETE, DOE
    # NOTE: use examyear.code (integer field) to filter on examyear. This way schoolbases from SXM and CUR are added to list

    # called by: create_orderlist_xlsx, create_orderlist_per_school_xlsx and OrderlistsPublishView

    if request.user.country.abbrev.lower() == 'sxm':
        show_sxm_schools_only = "AND ey.country_id = %(requsr_country_id)s::INT"
    else:
        show_sxm_schools_only = ''

    sql_keys = {'ey_code_int': examyear.code, 'requsr_country_id': request.user.country.pk}
    sql_list = [
        "SELECT sbase.id AS sbase_id, sbase.code AS sbase_code, sch.article AS sch_article, sch.name AS sch_name, sch.abbrev AS sch_abbrev, sbase.defaultrole",

        "FROM schools_school AS sch",
        "INNER JOIN schools_schoolbase AS sbase ON (sbase.id = sch.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",

        "WHERE ey.code = %(ey_code_int)s::INT",
        "AND (sbase.defaultrole =", str(c.ROLE_008_SCHOOL), "OR sbase.defaultrole =", str(c.ROLE_064_ADMIN), ")",
        show_sxm_schools_only,
        "ORDER BY LOWER(sbase.code)"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        dictlist = af.dictfetchall(cursor)

    if logging_on:
        logger.debug('schoolbase_dictlist: ' + str(dictlist))

    return dictlist
# --- end of create_schoolbase_dictlist


def create_subjectbase_dictlist(examyear):  # PR2021-08-20
    logging_on = False  # s.LOGGING_ON

    # PR2021-08-20 functions creates ordered dictlist of all subjectbase pk and code of this exam year of all countries
    # NOTE: use examyear.code (integer field) to filter on examyear. This way subjects from SXM and CUR are added to list

    sql_keys = {'ey_int': examyear.code}
    sql_list = [
        "SELECT subjbase.id, subjbase.code ",

        "FROM subjects_subject AS subj",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

        "WHERE ey.code = %(ey_int)s::INT",
        "GROUP BY subjbase.id, subjbase.code",
        "ORDER BY LOWER(subjbase.code)"]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        subjectbase_dictlist = af.dictfetchall(cursor)

    if logging_on:
        logger.debug ('----- create_subjectbase_dictlist -----')
        logger.debug('subjectbase_dictlist: ' + str(subjectbase_dictlist))

    return subjectbase_dictlist
# --- end of create_subjectbase_dictlist


# /////////////////////////////////////////////////////////////////
def create_studsubj_count_dict(sel_examyear_instance, request, prm_schoolbase_pk=None):  # PR2021-08-19 PR2021-09-24
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_studsubj_count_dict ----- ')

    #  create nested dict with subjects count per exam, lang, dep, lvl, school and subjbase_id
    #  all schools of CUR and SXM only submitted subjects, not deleted # PR2021-08-19
    #  add extra for ETE and DOE PR2021-09-25
    # called by: create_orderlist_xlsx, create_orderlist_per_school_xlsx, OrderlistsPublishView

# - get schoolbase_id of ETE and DOE

    # key = country_id, value = row_dict
    mapped_admin_dict = {}
    sql_keys = {'ey_code_int': sel_examyear_instance.code, 'default_role': c.ROLE_064_ADMIN }
    sql_list = ["SELECT sb.country_id, sch.base_id AS sb_id, sb.code AS c,",
                "ey.order_extra_fixed, ey.order_extra_perc, ey.order_round_to,",
                "ey.order_tv2_divisor, ey.order_tv2_multiplier, ey.order_tv2_max,",
                "ey.order_admin_divisor, ey.order_admin_multiplier, ey.order_admin_max",

                "FROM schools_school AS sch",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                "WHERE ey.code = %(ey_code_int)s::INT",
                "AND sb.defaultrole = %(default_role)s::INT"
                ]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)
        for row in rows:
            country_id = row.get('country_id')
            if country_id not in mapped_admin_dict:
                mapped_admin_dict[country_id] = row

    if logging_on:
        logger.debug('mapped_admin_dict: ' + str(mapped_admin_dict) + ' ' + str(type(mapped_admin_dict)))
        # mapped_admin_dict: {39: {'c': 'SXMDOE'}, 23: {'c': 'CURETE'}} <class 'dict'>

    # - when print orderlist ETE: skip DUO of SXM school
    # - when print orderlist SXM: skip all CUR schools, skip all ETE exams
    #  when print per school: show all
    skip_ete_or_duo = ''
    requsr_country_pk = request.user.country.pk

    if request.user.country.abbrev.lower() == 'cur':
    # when print orderlist ETE
        # - when request,user = ETE: add all ETE-exams and DUO-exams of CUR schools, but skip DUO-exams of SXM schools
        # -  WHERE is_ete_exam OR (NOT is_ete_exam AND country = requsr_country)
        skip_ete_or_duo = "AND ( (si.ete_exam) OR (NOT si.ete_exam AND ey.country_id = %(requsr_country_id)s::INT ))"
    elif request.user.country.abbrev.lower() == 'sxm':
    # when print orderlist DOE
        # - when request,user = SXM: show only SXM schools, show ETE exams and DUO exams
        # -  WHERE country = requsr_country
        skip_ete_or_duo = "AND (ey.country_id = %(requsr_country_id)s::INT )"

    sql_keys = {'ey_code_int': sel_examyear_instance.code, 'requsr_country_id': requsr_country_pk}
    sql_studsubj_agg_list = [
        "SELECT st.school_id, ey.country_id as ey_country_id, dep.base_id AS depbase_id, lvl.base_id AS lvlbase_id,",
        "sch.otherlang AS sch_otherlang,",

        "lvl.abbrev AS lvl_abbrev,",  # for testing only, must also delete from group_by
        "subj.name AS subj_name,",  # for testing only, must also delete from group_by

        #PR2021-10-12 subj.otherlang replaced by si.otherlang
        # was: "subj.base_id AS subjbase_id, si.ete_exam, subj.otherlang AS subj_otherlang, count(*) AS subj_count",
        "subj.base_id AS subjbase_id, si.ete_exam, si.otherlang AS si_otherlang, count(*) AS subj_count",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",

# - show only exams that are not deleted
        "WHERE NOT studsubj.tobedeleted",
# - show only published exams
        "AND studsubj.subj_published_id IS NOT NULL",
# - show only exams that have a central exam
        "AND NOT si.weight_ce = 0",
# - skip DUO exams for SXM schools
        skip_ete_or_duo,

        # PR2021-10-12 subj.otherlang replaced by si.otherlang
        #  was: "GROUP BY st.school_id, ey.country_id, dep.base_id, lvl.base_id, lvl.abbrev, sch.otherlang, subj.base_id, si.ete_exam, subj.otherlang"
        "GROUP BY st.school_id, ey.country_id, dep.base_id, lvl.base_id,",
        "lvl.abbrev, subj.name,", # for testing only, must also delete from group_by
        "sch.otherlang, subj.base_id, si.ete_exam, si.otherlang"
    ]
    sql_studsubj_agg = ' '.join(sql_studsubj_agg_list)

    sql_list = ["WITH studsubj AS (", sql_studsubj_agg, ")",
                "SELECT studsubj.subjbase_id, studsubj.ete_exam,",

                # PR2021-10-12 subj.otherlang replaced by si.otherlang
                #  was:
                # "CASE WHEN studsubj.subj_otherlang IS NULL OR studsubj.sch_otherlang IS NULL THEN 'ne' ELSE",
                # "CASE WHEN POSITION(studsubj.sch_otherlang IN studsubj.subj_otherlang) > 0 ",
                # "THEN studsubj.sch_otherlang ELSE 'ne' END END AS lang,",
                "CASE WHEN studsubj.si_otherlang IS NULL OR studsubj.sch_otherlang IS NULL THEN 'ne' ELSE",
                "CASE WHEN POSITION(studsubj.sch_otherlang IN studsubj.si_otherlang) > 0 ",
                "THEN studsubj.sch_otherlang ELSE 'ne' END END AS lang,",

                "cntr.id AS country_id,",  # PR2021-09-24 added, for extra exams ETE and DoE
                "sb.code AS sb_code, studsubj.lvl_abbrev, studsubj.subj_name,",  # for testing only
                "sch.base_id AS schoolbase_id, studsubj.depbase_id, studsubj.lvlbase_id, studsubj.subj_count",

                "FROM schools_school AS sch",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",
                "INNER JOIN schools_country AS cntr ON (cntr.id = sb.country_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                "INNER JOIN studsubj ON (studsubj.school_id = sch.id)",
# - show only exams of this exam year
                "WHERE ey.code = %(ey_code_int)s::INT"
                ]

# - filter on parameter schoolbase_pk when it has value
    if prm_schoolbase_pk:
        sql_keys['sb_pk'] = prm_schoolbase_pk
        sql_list.append("AND sb.id = %(sb_pk)s::INT")

    sql = ' '.join(sql_list)

    #if logging_on:
        #logger.debug('sql_keys: ' + str(sql_keys))
        #logger.debug('sql: ' + str(sql))
        #logger.debug('connection.queries: ' + str(connection.queries))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)
    if logging_on:
        logger.debug('rows: ' + str(rows))

    count_dict = {'total': {}}

    for row in rows:
        if logging_on:
            logger.debug('row: ' + str(row))

        row_sb_code = row.get('sb_code', '-')  # for testing only

        # admin_id is schoolbase_id of school of ETE / DOE
        admin_id, admin_code = None, None
        order_extra_fixed, order_extra_perc, order_round_to = None, None, None
        order_tv2_divisor, order_tv2_multiplier, order_tv2_max = None, None, None

        country_id = row.get('country_id')
        if country_id in mapped_admin_dict:
            mapped_country_dict = mapped_admin_dict[country_id]
            admin_id = mapped_country_dict.get('sb_id')
            admin_code = mapped_country_dict.get('c')

            order_extra_fixed = mapped_country_dict.get('order_extra_fixed')
            order_extra_perc = mapped_country_dict.get('order_extra_perc')
            order_round_to = mapped_country_dict.get('order_round_to')

            order_tv2_divisor = mapped_country_dict.get('order_tv2_divisor')
            order_tv2_multiplier = mapped_country_dict.get('order_tv2_multiplier')
            order_tv2_max = mapped_country_dict.get('order_tv2_max')

        if logging_on:
            #logger.debug('mapped_country_dict: ' + str(mapped_country_dict))
            logger.debug('admin_code: ' + str(admin_code))
            #logger.debug('order_extra_fixed: ' + str(order_extra_fixed))
            #logger.debug('order_extra_perc: ' + str(order_extra_perc))
            logger.debug('order_round_to: ' + str(order_round_to))

        exam = 'ETE' if row.get('ete_exam', False) else 'DUO'
        if exam not in count_dict:
            count_dict[exam] = {'total': {}}
        exam_dict = count_dict[exam]

        lang = row.get('lang', 'ne')
        if lang not in exam_dict:
            # lang_dict has no key 'total'
            exam_dict[lang] = {}
        lang_dict = exam_dict[lang]

        depbase_pk = row.get('depbase_id')
        if depbase_pk not in lang_dict:
            # depbase_dict has no key 'total'
            lang_dict[depbase_pk] = {}
        depbase_dict = lang_dict[depbase_pk]

        # value is '0' when lvlbase_id = None (Havo/Vwo)
        lvlbase_pk = row.get('lvlbase_id', 0)
        if lvlbase_pk is None:
            lvlbase_pk = 0
        lvl_abbrev = row.get('lvl_abbrev', '-')
        if lvlbase_pk not in depbase_dict:
            depbase_dict[lvlbase_pk] = {'c': lvl_abbrev, 'total': {}, 'country': {}}
        lvlbase_dict = depbase_dict[lvlbase_pk]

        row_sb_pk = row.get('schoolbase_id')
        if row_sb_pk not in lvlbase_dict:
            lvlbase_dict[row_sb_pk] = {'c': row_sb_code}
        schoolbase_dict = lvlbase_dict[row_sb_pk]

# +++ count extra exams and examns tv2 per school / subject
        subjbase_pk = row.get('subjbase_id')
        subj_count = row.get('subj_count', 0)

        extra_count = 0
        tv2_count = 0
        if subj_count:
            extra_count = calc_extra_exams(subj_count, order_extra_fixed, order_extra_perc, order_round_to)
            tv2_count = calc_exams_tv02(subj_count, order_tv2_divisor, order_tv2_multiplier, order_tv2_max)

        if logging_on:
            logger.debug('.........................................')
            logger.debug('........schoolbase_pk: ' + str(row_sb_pk) + ' ' + str(row_sb_code))
            logger.debug('........lvlbase_pk: ' + str(lvlbase_pk) + ' ' + str(lvl_abbrev))
            logger.debug('........subjbase_pk: ' + str(subjbase_pk))
            logger.debug('........subj_count: ' + str(subj_count))
            logger.debug('.......extra_count: ' + str(extra_count))
            logger.debug('.........tv2_count: ' + str(tv2_count))

# +++ add to totals
        if subjbase_pk not in schoolbase_dict:
            schoolbase_dict[subjbase_pk] = [subj_count, extra_count, tv2_count]
        else:
            schoolbase_dict[subjbase_pk][0] += subj_count
            schoolbase_dict[subjbase_pk][1] += extra_count
            schoolbase_dict[subjbase_pk][2] += tv2_count

        if logging_on:
            logger.debug('schoolbase_dict: ' + str(schoolbase_dict))

        lvlbase_total = lvlbase_dict.get('total')
        if subjbase_pk not in lvlbase_total:
            lvlbase_total[subjbase_pk] = [subj_count, extra_count, tv2_count]
        else:
            lvlbase_total[subjbase_pk][0] += subj_count
            lvlbase_total[subjbase_pk][1] += extra_count
            lvlbase_total[subjbase_pk][2] += tv2_count

    # skip admin_total when calculate per school > when schoolbase_pk has value
        if prm_schoolbase_pk is None:
            lvlbase_country = lvlbase_dict.get('country')
            if admin_id not in lvlbase_country:
                lvlbase_country[admin_id] = {'c': admin_code}
            admin_total = lvlbase_country[admin_id]

            if subjbase_pk not in admin_total:
                admin_total[subjbase_pk] = [subj_count, extra_count, tv2_count]
            else:
                admin_total[subjbase_pk][0] += subj_count
                admin_total[subjbase_pk][1] += extra_count
                admin_total[subjbase_pk][2] += tv2_count

            if logging_on:
                logger.debug(' - - - - ')
                logger.debug('........admin_total: ' + str(admin_total))

        exam_total = exam_dict.get('total')
        if subjbase_pk not in exam_total:
            exam_total[subjbase_pk] = [subj_count, extra_count, tv2_count]
        else:
            exam_total[subjbase_pk][0] += subj_count
            exam_total[subjbase_pk][1] += extra_count
            exam_total[subjbase_pk][2] += tv2_count

        examyear_total = count_dict.get('total')
        if subjbase_pk not in examyear_total:
            examyear_total[subjbase_pk] = [subj_count, extra_count, tv2_count]
        else:
            examyear_total[subjbase_pk][0] += subj_count
            examyear_total[subjbase_pk][1] += extra_count
            examyear_total[subjbase_pk][2] += tv2_count

# +++ after adding schools: calculate extra for ETE and DEX:
    # skip when calculate per school > when schoolbase_pk has value
    if prm_schoolbase_pk is None:
        if logging_on:
            logger.debug('schoolbase_pk is None')

        for exam, exam_dict in count_dict.items():
            if exam != 'total':
                if logging_on:
                    logger.debug('exam: ' + str(exam) + ' ' + str(type(exam)))

                for lang, lang_dict in exam_dict.items():
                    if lang != 'total':
                        if logging_on:
                            logger.debug('lang: ' + str(lang) + ' ' + str(type(lang)))

                        for depbase_pk, depbase_dict in lang_dict.items():
                            if isinstance(depbase_pk, int):
                                for lvlbase_pk, lvlbase_dict in depbase_dict.items():
                                    if isinstance(lvlbase_pk, int):
                                        if logging_on:
                                            logger.debug('lvlbase_pk: ' + str(lvlbase_pk) + ' ' + str(type(lvlbase_pk)))
                                            logger.debug('lvlbase_dict: ' + str(lvlbase_dict) + ' ' + str(type(lvlbase_dict)))

                                        lvlbase_country_dict = lvlbase_dict.get('country')
                                        lvlbase_total_dict = lvlbase_dict.get('total')
                                        exam_total_dict = exam_dict.get('total')
                                        examyear_total_dict = count_dict.get('total')

                                        if lvlbase_country_dict:
                                            if logging_on:
                                                logger.debug('lvlbase_country_dict: ' + str(lvlbase_country_dict) + ' ' + str(type(lvlbase_country_dict)))
                                                # 'lvlbase_country_dict': {39: {'c': 'SXMDOE', 430: [82, 8, 20], 440: [52, 8, 15]},
                                                #             23: {'c': 'CURETE', 430: [108, 12, 30], 440: [62, 13, 20], 435: [4, 6, 5]}},

                                            #  country_id: 1
                                            # mapped_country_dict: { 'country_id': 1, 'sb_id': 23, 'c': 'CURETE',
                                            # 'order_extra_fixed': 2, 'order_extra_perc': 5, 'order_round_to': 5,
                                            # 'order_tv2_divisor': 25, 'order_tv2_multiplier': 6, 'order_tv2_max': 25,
                                            # 'order_admin_divisor': 30, 'order_admin_multiplier': 7, 'order_admin_max': 25}

                            # - get admin_pk from mapped_country_dict with key: country_id
                                            # admin_pk is schoolbase_id of school of ETE / DEX
                                            for country_id, mapped_country_dict in mapped_admin_dict.items():
                                                admin_pk = mapped_country_dict.get('sb_id')
                                                admin_code = mapped_country_dict.get('c')
                                                order_admin_divisor = mapped_country_dict.get('order_admin_divisor')
                                                order_admin_multiplier = mapped_country_dict.get('order_admin_multiplier')
                                                order_admin_max = mapped_country_dict.get('order_admin_max')

                            # - lookup 'country_admin_dict' in lvlbase_country_dict, with key: admin_pk
                                                # country_admin_dict contains subject_count of all subjects of this admin, this level
                                                if admin_pk in lvlbase_country_dict:
                                                    country_admin_dict = lvlbase_country_dict.get(admin_pk)
                                                    if logging_on:
                                                        logger.debug('country_id: ' + str(country_id) + ' ' + str(type(country_id)))
                                                        logger.debug(
                                                            'mapped_country_dict: ' + str(mapped_country_dict) + ' ' + str(
                                                                type(mapped_country_dict)))
                                                        logger.debug('admin_pk: ' + str(admin_pk) + ' ' + str(type(admin_pk)))
                                                        logger.debug('admin_code: ' + str(admin_code) + ' ' + str(type(admin_code)))

                            # - add extra row 'lvlbase_admin_dict' for ETE / DOE in lvlbase_dict, if not exists yet
                                                    if admin_pk not in lvlbase_dict:
                                                        lvlbase_dict[admin_pk] = {'c': admin_code}
                                                    lvlbase_admin_dict = lvlbase_dict[admin_pk]

                                                    if logging_on:
                                                        logger.debug('lvlbase_admin_dict: ' + str(lvlbase_admin_dict) + ' ' + str(type(lvlbase_admin_dict)))
                                                        #  lvlbase_admin_dict = {'c': 'CURETE', 430: [0, 25, 0], 440: [0, 21, 0], 435: [0, 7, 0]}}

                            # - loop through subjects in country_admin_dict
                                                    for subjbase_pk, count_list in country_admin_dict.items():
                                                        if isinstance(subjbase_pk, int):
                            # - caculate extra exams for ETE / DEX
                                                            sj_count = count_list[0]
                                                            tv2_count = count_list[2]

                                                            admin_extra_count = calc_exams_tv02(sj_count, order_admin_divisor, order_admin_multiplier, order_admin_max)
                                                            # TODO tv2 calc for extra ETE / DEZ
                                                            # TODO esparate varables for extra tv2 ETE/DEX
                                                            admin_tv2_count = calc_exams_tv02(tv2_count, order_admin_divisor, order_admin_multiplier, order_admin_max)
                                                            if logging_on:
                                                                logger.debug('admin_extra_count: ' + str(admin_extra_count) + ' ' + str(type(admin_extra_count)))
                                                                logger.debug('admin_tv2_count: ' + str(admin_tv2_count) + ' ' + str(type(admin_tv2_count)))

                            # - add extra exams to lvlbase_admin_dict
                                                            # index 0 contains sj_count, but admins don't have exams, omly extra and tv2 extra
                                                            lvlbase_admin_dict[subjbase_pk] = [0, admin_extra_count, admin_tv2_count ]

                            # - also add admin_extra_count to total row of lvlbase_total_dict, exam_total_dict and examyear_total_dict
                                                            if subjbase_pk in lvlbase_total_dict:
                                                                # Note: admin has no exams: total_dict[subjbase_pk][0] += 0
                                                                lvlbase_total_dict[subjbase_pk][1] += admin_extra_count
                                                                lvlbase_total_dict[subjbase_pk][2] += admin_tv2_count

                                                            if subjbase_pk in exam_total_dict:
                                                                # Note: admin has no exams: total_dict[subjbase_pk][0] += 0
                                                                exam_total_dict[subjbase_pk][1] += admin_extra_count
                                                                exam_total_dict[subjbase_pk][2] += admin_tv2_count

                                                            if subjbase_pk in examyear_total_dict:
                                                                # Note: admin has no exams: total_dict[subjbase_pk][0] += 0
                                                                examyear_total_dict[subjbase_pk][1] += admin_extra_count
                                                                examyear_total_dict[subjbase_pk][2] += admin_tv2_count

                                                    if logging_on:
                                                        logger.debug('lvlbase_admin_dict: ' + str( lvlbase_admin_dict) + ' ' + str(type(lvlbase_admin_dict)))

    if logging_on:
        logger.debug('schoolbase_pk is NOT None')

        """
        lvlbase_pk: 13 <class 'int'>
        lvlbase_dict: {'c': 'PKL', 
                       'total': {'total': {427: [102, 8, 30]}, 
                            1: {'c': 'Cur', 427: [51, 4, 15]}, 
                            2: {'c': 'Sxm', 427: [51, 4, 15]}
                            }, 
                        2: {'c': 'CUR01', 427: [51, 4, 15]}, 
                        35: {'c': 'SXM01', 427: [51, 4, 15]}} 
        """

        """
        examyear_dict_sample = {'total': {137: 513, 134: 63, 156: 63, 175: 63},
            'DUO': {'total': {137: 513, 134: 63, 156: 63, 175: 63},  # exam_dict: { 'total': {}, lang_dict: {}
                'ne': {'total': {137: 513, 134: 63, 156: 63, 175: 63},  # lang_dict: { 'total': {}, depbase_dict: {}
                    1: {'total': {137: 513, 134: 63, 156: 63, 175: 63},  # depbase_dict: { 'total': {}, lvlbase_dict: {}
                        12: {'total': {137: 90},  # lvlbase_dict: { 'total': {}, schoolbase_pk: {}
                             2: {137: [90, 5]}  #  schoolbase_pk: { subjbase_pk: [ subj_count, extra_count, tv2_count]
                             },
                        13: {'total': {134: 63, 137: 156, 156: 63, 175: 63},
                             2: {134: 63, 137: 156, 156: 63, 175: 63}
                             },
                        14: {'total': {137: 267},
                             2: {137: [267, 10]}
                             }
                    }
                }
            }
        }

    lvlbase_dict = {'c': 'PBL',
            'total': {430: [190, 66, 50], 440: [114, 56, 35], 435: [4, 13, 5]},
            'country': {
                39: {'c': 'SXMDOE', 430: [82, 8, 20], 440: [52, 8, 15]},
                23: {'c': 'CURETE', 430: [108, 12, 30], 440: [62, 13, 20], 435: [4, 6, 5]}},
            35: {'c': 'SXM01', 430: [82, 8, 20], 440: [52, 8, 15]},
             2: {'c': 'CUR01', 430: [82, 8, 20], 440: [52, 8, 15]},
             4: {'c': 'CUR03', 430: [26, 4, 10], 440: [10, 5, 5], 435: [4, 6, 5]},
            39: {'c': 'SXMDOE', 430: [0, 21, 0], 440: [0, 14, 0]},
            23: {'c': 'CURETE', 430: [0, 25, 0], 440: [0, 21, 0], 435: [0, 7, 0]}}

"""

    if logging_on:
        logger.debug('studsubj_count_dict: ' + str(count_dict))

    return count_dict
# --- end of create_studsubj_count_dict


def calc_extra_exams(subj_count, extra_fixed, extra_perc, round_to):  # PR2021-09-25
    # - function counts extra exams and examns tv2 per school / subject
    # - Note: values of extra_fixed, extra_perc, round_to are from table examyear,
    #         thus can be different for CUR and SXM schools

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- calc_extra_exams -------')
        logger.debug('subj_count:  ' + str(subj_count))
        logger.debug('extra_fixed: ' + str(extra_fixed))
        logger.debug('extra_perc:  ' + str(extra_perc))
        logger.debug('round_to:  ' + str(round_to))

    extra_count = 0
    if subj_count:
        total_not_rounded = subj_count + extra_fixed + (subj_count * extra_perc / 100)
        total_divided = total_not_rounded / round_to
        total_integer = int(total_divided)
        # total_frac = (total_divided - total_integer)
        total_roundup = total_integer + 1 if (total_divided - total_integer) else total_integer
        # total_roundup = total_frac_roundup * order_round_to
        extra_count = total_roundup * round_to - subj_count

        if logging_on:
            logger.debug('subj_count:  ' + str(subj_count))
            logger.debug('total_not_rounded: ' + str(total_not_rounded))
            logger.debug('total_divided:  ' + str(total_divided))
            logger.debug('total_integer:  ' + str(total_integer))
            logger.debug('total_frac: ' + str(total_divided - total_integer))
            logger.debug('total_roundup: ' + str(total_roundup))
            logger.debug('total_roundup:   ' + str(total_roundup))
            logger.debug('extra_count:   ' + str(extra_count))
            logger.debug('..........: ')

    return extra_count
# - end of calc_extra_exams


def calc_exams_tv02(subj_count, divisor, multiplier, max_exams):  # PR2021-09-25
    # - count examns tv2 per school / subject:
    # - 'multiplier' tv02-examns per 'divisor' tv01-examns, roundup to 'multiplier', with max of 'max_exams'
    # - Note: values of divisor, multiplier, max_exams are from table examyear,
    #         thus can be different for CUR and SXM schools

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- calc_exams_tv02 -------')
        logger.debug('subj_count:  ' + str(subj_count))
        logger.debug('divisor: ' + str(divisor))
        logger.debug('multiplier:  ' + str(multiplier))
        logger.debug('max_exams:  ' + str(max_exams))

    tv2_count = 0
    if subj_count:
        try:
            # PR2021-10-12 debug: gave ZeroDivisionError. "if divisor else 0" added.
            total_divided = subj_count / divisor if divisor else 0
            total_integer = int(total_divided)
            # total_frac = (total_divided - total_integer)
            total_roundup = total_integer + 1 if (total_divided - total_integer) else total_integer
            # total_roundup = total_frac_roundup * order_round_to
            tv2_count = total_roundup * multiplier

            if tv2_count > max_exams:
                tv2_count = max_exams

            if logging_on:
                logger.debug('subj_count:  ' + str(subj_count))
                logger.debug('total_divided:  ' + str(total_divided))
                logger.debug('total_integer:  ' + str(total_integer))
                logger.debug('total_frac: ' + str(total_divided - total_integer))
                logger.debug('total_roundup: ' + str(total_roundup))
                logger.debug('tv2_count:   ' + str(tv2_count))
                logger.debug('..........: ')

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return tv2_count
# - end of calc_exams_tv02

# from https://github.com/jmcnamara/XlsxWriter/blob/main/xlsxwriter/utility.py PR2021-08-30

def xl_rowcol_to_cell(row, col, row_abs=False, col_abs=False):
    """
    Convert a zero indexed row and column cell reference to a A1 style string.
    Args:
       row:     The cell row.    Int.
       col:     The cell column. Int.
       row_abs: Optional flag to make the row absolute.    Bool.
       col_abs: Optional flag to make the column absolute. Bool.
    Returns:
        A1 style string.
    """
    if row < 0:
        return None

    if col < 0:
        return None

    row += 1  # Change to 1-index.
    row_abs = '$' if row_abs else ''

    col_str = xl_col_to_name(col, col_abs)

    return col_str + row_abs + str(row)


def xl_col_to_name(col, col_abs=False):
    """
    Convert a zero indexed column cell reference to a string.
    Args:
       col:     The cell column. Int.
       col_abs: Optional flag to make the column absolute. Bool.
    Returns:
        Column style string.
    """
    col_num = col
    if col_num < 0:
        return None

    col_num += 1  # Change to 1-index.
    col_str = ''
    col_abs = '$' if col_abs else ''

    while col_num:
        # Set remainder from 1 .. 26
        remainder = col_num % 26

        if remainder == 0:
            remainder = 26

        # Convert the remainder to a character.
        col_letter = chr(ord('A') + remainder - 1)

        # Accumulate the column letters, right to left.
        col_str = col_letter + col_str

        # Get the next order of magnitude.
        col_num = int((col_num - 1) / 26)

    return col_abs + col_str
