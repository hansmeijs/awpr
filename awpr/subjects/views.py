# PR2018-07-20
import io

from django.contrib.auth.decorators import login_required # PR2018-04-01

from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

from django.db import connection
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from django.shortcuts import render

from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
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

        # request.POST<QueryDict: {'dep_id': ['11'], 'lvl_id': ['7'], 'sct_id': ['30']}>

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


def create_subject_rows(setting_dict, subject_pk, cur_dep_only=False):
    # --- create rows of all subjects of this examyear  PR2020-09-29 PR2020-10-30 PR2020-12-02
    logging_on = False  # s.LOGGING_ON

    sel_examyear_pk = af.get_dict_value(setting_dict, ('sel_examyear_pk',))
    sel_depbase_pk = af.get_dict_value(setting_dict, ('sel_depbase_pk',))

    if logging_on:
        logger.debug(' =============== create_subject_rows ============= ')
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
        sql_list = ["SELECT sj.id, sj.base_id, sj.examyear_id,",
            "CONCAT('subject_', sj.id::TEXT) AS mapid,",
            "sj.name, sb.code, sj.sequence, sj.depbases, sj.otherlang, sj.addedbyschool,",
            "sj.modifiedby_id, sj.modifiedat,",
            "ey.code AS examyear_code,",
            "SUBSTRING(au.username, 7) AS modby_username",
    
            "FROM subjects_subject AS sj",
            "INNER JOIN subjects_subjectbase AS sb ON (sb.id = sj.base_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = sj.examyear_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = sj.modifiedby_id)",
            
            "WHERE sj.examyear_id = %(ey_id)s::INT"
            ]
        if subject_pk:
            # when employee_pk has value: skip other filters
            sql_keys['sj_id'] = subject_pk
            sql_list.append('AND sj.id = %(sj_id)s::INT')
        else:
            if cur_dep_only:
                sql_keys['depbase_lookup'] = ''.join( ('%;', str(sel_depbase_pk), ';%') )
                sql_list.append("AND CONCAT(';', sj.depbases::TEXT, ';') LIKE %(depbase_lookup)s::TEXT")

            sql_list.append("ORDER BY sj.id")

        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            subject_rows = af.dictfetchall(cursor)

    return subject_rows
# --- end of create_subject_rows


@method_decorator([login_required], name='dispatch')
class SubjectUploadView(View):  # PR2020-10-01 PR2021-05-14 PR2021-07-18

    def post(self, request):
        logging_on = s.LOGGING_ON
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
                            deleted_ok = delete_subject(subject, updated_rows, messages, error_list, request)


# - create subject_row, also when deleting failed, not when deleted ok, in that case subject_row is added in delete_subject
                        else:
                            update_subject_instance(subject, examyear, upload_dict, error_list, request)

# - create subject_row, also when deleting failed (when deleted ok there is no subject, subject_row is made above)
                    if not deleted_ok:
                        setting_dict = {'sel_examyear_pk': examyear.pk}
                        updated_rows = create_subject_rows(
                            setting_dict=setting_dict,
                            subject_pk=subject.pk
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

# - end of SubjectUploadView


##########################
@method_decorator([login_required], name='dispatch')
class SubjecttypebaseUploadView(View):  # PR2021-06-29

    def post(self, request):
        logging_on = s.LOGGING_ON
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
    logging_on = s.LOGGING_ON
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
            # Don't create base record. Only use the default base records
            subjecttypebase = sbj_mod.Subjecttypebase(
                country=request.user.country,
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
    logging_on = s.LOGGING_ON
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
    logging_on = s.LOGGING_ON
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
        logging_on = s.LOGGING_ON
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


# - end of update_si_list

def get_permit_crud_page_subject(request):
    # --- get crud permit for page subject # PR2021-06-26
    logging_on = s.LOGGING_ON

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
    return examyear


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
            id=sjtpbase_pk,
            country=request.user.country
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
                deleted_list = []
                append_dict = {}

# - get variables from upload_dict
                # don't get it from usersettings, get it from upload_dict instead
                mode = upload_dict.get('mode')
                examyear_pk = upload_dict.get('examyear_pk')
                depbase_pk = upload_dict.get('depbase_pk')
                levelbase_pk = upload_dict.get('levelbase_pk')

                exam_pk = upload_dict.get('exam_pk')
                subject_pk = upload_dict.get('subject_pk')

# - check if examyear exists and equals selected examyear from Usersetting
                selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                selected_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                examyear = None
                if examyear_pk == selected_examyear_pk:
                    examyear = sch_mod.Examyear.objects.get_or_none(id=examyear_pk, country=req_usr.country)

                # note: exams can be changed before publishing examyear, therefore don't filter on examyear.published
                if examyear and not examyear.locked:

# - get subject
                    subject = subj_mod.Subject.objects.get_or_none(
                        pk=subject_pk,
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
                            base_id=levelbase_pk,
                            examyear=examyear
                        )
                        if logging_on:
                            logger.debug('department:     ' + str(department))
                            logger.debug('level:     ' + str(level))
                        examperiod_int = upload_dict.get('examperiod')
                        examtype = upload_dict.get('examtype')
                        exam, msg_err = create_exam_instance(subject, department, level, examperiod_int, examtype, request)

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
                            if deleted_row:
                                deleted_list.append(deleted_row)
                        else:

    # +++++ Update instance, also when it is created, not when is_delete
                            update_exam_instance(exam, upload_dict, error_list, examyear, request)

    # 6. create list of updated exam
                    selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                    s_depbase_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)

                    setting_dict = {'sel_examyear_pk': examyear.pk,
                                    'sel_depbase_pk': depbase_pk,
                                    'exam_pk': exam.pk}
                    exam_rows = create_exam_rows(setting_dict, append_dict)
                    if deleted_list:
                        exam_rows.extend(deleted_list)
                    if exam_rows:
                        update_wrap['updated_exam_rows'] = exam_rows
        if err_html:
            update_wrap['err_html'] = err_html
# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamUploadView


@method_decorator([login_required], name='dispatch')
class ExamApproveView(View):  # PR2021-04-04

    def post(self, request):
        logging_on = True
        if logging_on:
            logger.debug('')
            logger.debug(' ============= ExamApproveView ============= ')
        # function creates, deletes and updates grade records of current studentsubject PR2020-11-21
        update_wrap = {}

        # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of ExamApproveView


def create_exam_instance(subject, department, level, examperiod_int, examtype, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --- create_exam_instance --- ')
        logger.debug('subject: ' + str(subject))
        logger.debug('department: ' + str(department))
        logger.debug('level: ' + str(level))
        logger.debug('examperiod_int: ' + str(examperiod_int))
        logger.debug('examtype: ' + str(examtype))

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
            examtype=examtype
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


def delete_exam_instance(instance, error_list, request):  #  PR2021-04-05

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --- delete_exam_instance --- ')
        logger.debug('instance: ' + str(instance))
# - create deleted_row
    deleted_row = {'pk': instance.pk,
                    'mapid': 'exam_' + str(instance.pk),
                    'deleted': True}
    if logging_on:
        logger.debug('deleted_row: ' + str(deleted_row))
# - delete instance
    #try:
    if True:
        instance.delete(request=request)
    #except Exception as e:
    #    deleted_row = None
   #     logger.error(getattr(e, 'message', str(e)))
    #    error_list.append(_('This item could not be created.'))

    if logging_on:
        logger.debug('deleted_row: ' + str(deleted_row))
        logger.debug('error_list: ' + str(error_list))
    return deleted_row
# - end of delete_exam_instance

def update_exam_instance(instance, upload_dict, error_list, examyear, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --------- update_exam_instance -------------')
        logger.debug('upload_dict: ' + str(upload_dict))

    if instance:
        save_changes = False
        for field, new_value in upload_dict.items():
            if logging_on:
                logger.debug('field: ' + str(field))
                logger.debug('new_value: ' + str(new_value) + ' ' + str(type(new_value)))

# --- skip fields that don't contain new values
            if field in ('mode', 'examyear_pk', 'subject_pk', 'exam_pk', 'examperiod_int', 'examtype'):
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

            elif field in ('assignment', 'keys', 'amount', 'version', 'blanks'):
                old_value = getattr(instance, field)
                if new_value != old_value:
                    setattr(instance, field, new_value)
                    save_changes = True

            elif field in ('auth1by', 'auth2by'):
                pass
            elif field == 'published':
                pass

# - save orderhour
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


def create_exam_rows(setting_dict, append_dict, cur_dep_only=False):
    # --- create rows of all exams of this examyear  PR2021-04-05
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_exam_rows ============= ')
        logger.debug('setting_dict: ' + str(setting_dict))

    sel_examyear_pk = setting_dict.get('sel_examyear_pk')
    sel_examperiod = setting_dict.get('sel_examperiod')
    sel_depbase_pk = setting_dict.get('sel_depbase_pk')
    sel_lvlbase_pk = setting_dict.get('sel_lvlbase_pk')
    exam_pk = setting_dict.get('exam_pk')

    if logging_on:
        logger.debug('exam_pk: ' + str(exam_pk))
        logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk))
        logger.debug('sel_examperiod:  ' + str(sel_examperiod))
        logger.debug('sel_depbase_pk:  ' + str(sel_depbase_pk))
        logger.debug('sel_lvlbase_pk:  ' + str(sel_lvlbase_pk))

    sql_keys = {'ey_id': sel_examyear_pk, 'depbase_id': sel_depbase_pk}

    sql_list = [
        "SELECT ex.id, ex.subject_id, subj.base_id AS subj_base_id, subj.examyear_id AS subj_examyear_id,",
        "CONCAT('exam_', ex.id::TEXT) AS mapid,",
        "CONCAT(subj.name,",
        "CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' ', lvl.abbrev) END,",
        "CASE WHEN ex.version IS NULL THEN NULL ELSE CONCAT(' (', ex.version, ')') END ) AS exam_name,",

        "ex.examperiod, ex.examtype, ex.department_id, depbase.code AS depbase_code,",
        "ex.level_id, lvl.base_id AS levelbase_id, lvl.abbrev AS lvl_abbrev,",
        "ex.version, ex.assignment, ex.keys, ex.amount, ex.blanks,",
        "ex.status, ex.auth1by_id, ex.auth2by_id, ex.locked,",
        "ex.modifiedby_id, ex.modifiedat,",
        "sb.code AS subj_base_code, subj.name AS subj_name,",
        "ey.code AS ey_code, ey.locked AS ey_locked,",
        "SUBSTRING(au.username, 7) AS modby_username",

        "FROM subjects_exam AS ex",
        "INNER JOIN subjects_subject AS subj ON (subj.id = ex.subject_id)",
        "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

        "INNER JOIN schools_department AS dep ON (dep.id = ex.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = ex.level_id)",

        "LEFT JOIN accounts_user AS au ON (au.id = ex.modifiedby_id)",
        "WHERE ey.id = %(ey_id)s::INT AND depbase.id = %(depbase_id)s::INT"
    ]
    if exam_pk:
        sql_keys ['ex_id'] = exam_pk
        sql_list.append('AND ex.id = %(ex_id)s::INT')
    else:
        if sel_lvlbase_pk:
            # cannot filter on levelbase_pk because of LEFT JOIN subjects_level
            level = subj_mod.Level.objects.get_or_none(
                base_id=sel_lvlbase_pk,
                examyear_id=sel_examyear_pk
            )
            if level:
                sql_keys ['lvl_id'] = level.pk
                sql_list.append("AND lvl.id = %(lvl_id)s::INT")

        if sel_examperiod:
            sql_keys ['ex_per'] = sel_examperiod
            sql_list.append("AND ex.examperiod = %(ex_per)s::INT")
        sql_list.append("ORDER BY LOWER(sb.code)")

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        exam_rows = af.dictfetchall(cursor)

        # - add messages to exam_row
        if exam_pk and exam_rows:
            # when exam_pk has value there is only 1 row
            row = exam_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    #if logging_on:
        #logger.debug('exam_rows: ' + str(exam_rows))

    return exam_rows
# --- end of create_exam_rows


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
                    country=request.user.country,
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
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def lookup_subjectbase(lookup_value, request):  # PR2020-10-20
    logger.debug('----------- lookup_subjectbase ----------- ')
    # function searches for existing subjectbase
    logger.debug('lookup_value: ' + str(lookup_value) + ' ' + str(type(lookup_value)))

    subjectbase = None
    multiple_found = False

# check if 'code' exists multiple times in Subjectbase
    row_count = subj_mod.Subjectbase.objects.filter(code__iexact=lookup_value, country=request.user.country).count()
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

def delete_subject(subject, subject_rows, msg_list, error_list, request):
    # --- delete subject # PR2021-05-14 PR2021-07-18

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- delete_subject ----- ')
        logger.debug('subject: ' + str(subject))

    deleted_ok = False

# - create subject_row - to be returned after successfull delete
    subject_row = {'id': subject.pk,
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
        error_list.append(' '.join((err_txt1, err_txt2)))

        msg_html = '<br>'.join((err_txt1, err_txt2))
        msg_list.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': msg_html})

    else:
        deleted_ok = sch_mod.delete_instance(subject, msg_list, error_list, request, this_txt, header_txt)

    if deleted_ok:
# - add deleted_row to subject_rows
        subject_rows.append(subject_row)

# - check if this subject also exists in other examyears.
        subjects = subj_mod.Subject.objects.filter(base_id=base_pk).first()
        # If not: delete also subject_base
        if subjects is None:
            subject_base = subj_mod.Subjectbase.objects.get_or_none(id=base_pk)
            if subject_base:
                subject_base.delete()

    if logging_on:
        logger.debug('subject_rows' + str(subject_rows))
        logger.debug('msg_list' + str(msg_list))
        logger.debug('error_list' + str(error_list))

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
                    country=examyear.country,
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
    logging_on = s.LOGGING_ON
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

# - save changes in field 'otherlang'
            elif field == 'otherlang':
                saved_value = getattr(instance, field)
                if new_value != saved_value:
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
    logging_on = s.LOGGING_ON
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
    logging_on = s.LOGGING_ON
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

            if field in ("gradetype", "weight_se", "weight_ce", "is_mandatory", "is_mand_subj", "is_combi",
                         "extra_count_allowed",  "extra_nocount_allowed",  "elective_combi_allowed",
                         "has_practexam", "has_pws", "is_core_subject", "is_mvt", "is_wisk", "ete_exam",
                         "reex_se_allowed", "max_reex",  "no_thirdperiod",  "no_exemption_ce"):

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
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred: ')), '<br><i>', str(e), '</i><br>',
                            str(_('The changes have not been saved.'))))
                error_list.append({'header': msg_header_txt, 'class': "border_bg_invalid", 'msg_html': msg_html})

# - end of update_schemeitem_instance

# >>>>>>>>  SCHEME >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def update_scheme_instance(instance, examyear, upload_dict, updated_rows, error_list, request):
    # --- update existing and new instance PR2021-06-27
    logging_on = s.LOGGING_ON
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

            elif field in ('min_subjects', 'max_subjects', 'min_mvt', 'max_mvt', 'min_wisk', 'max_wisk', 'min_combi', 'max_combi'):
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

                if msg_html:
                    msg_dict = {'field': field,
                                'header': msg_header_txt,
                                'class': 'border_bg_warning',
                                'msg_html': msg_html}
                    error_list.append(msg_dict)
                else:
                    # -note: value can be None
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
    logging_on = s.LOGGING_ON
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
    logging_on = s.LOGGING_ON
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
    logging_on = s.LOGGING_ON
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
                        id=new_value,
                        country=request.user.country
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
                           'min_extra_counts', 'max_extra_counts',
                           'min_elective_combi', 'max_elective_combi'
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

                        elif field == 'min_elective_combi':
                            max_elective_combi = getattr(instance, 'max_elective_combi')
                            if max_elective_combi is not None and new_value > max_elective_combi:
                                msg_html = str(_("Minimum amount of %(cpt)s cannot be greater than maximum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': max_elective_combi})
                        elif field == 'max_elective_combi':
                            min_elective_combi = getattr(instance, 'min_elective_combi')
                            if min_elective_combi is not None and new_value < min_elective_combi:
                                msg_html = str(_("Maximum amount of %(cpt)s cannot be fewer than minimum (%(val)s).") \
                                               % {'cpt': _('subjects'), 'val': min_elective_combi})

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
            "sjtp.min_extra_counts, sjtp.max_extra_counts, sjtp.min_elective_combi, sjtp.max_elective_combi,",
            "lvl.id AS lvl_id, lvl.abbrev AS lvl_abbrev, sct.id AS sct_id, sct.abbrev AS sct_abbrev,",
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
        else:
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
            "scheme.name, scheme.min_subjects, scheme.max_subjects, scheme.min_mvt, scheme.max_mvt, scheme.min_wisk, scheme.max_wisk, scheme.min_combi, scheme.max_combi,",
            "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ey.code AS ey_code,",
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

    if examyear :
        sql_keys = {'ey_id': examyear.pk}
        sql_list = ["SELECT si.id, si.scheme_id, scheme.department_id, scheme.level_id, scheme.sector_id,",
            "CONCAT('schemeitem_', si.id::TEXT) AS mapid,",
            "si.subject_id AS subj_id, subj.name AS subj_name, subjbase.id AS subjbase_id, subjbase.code AS subj_code,",
            "sjtpbase.code AS sjtpbase_code, sjtpbase.sequence AS sjtpbase_sequence,",
            "sjtp.id AS sjtp_id, sjtp.name AS sjtp_name, sjtp.abbrev AS sjtp_abbrev,",
            "sjtp.has_prac AS sjtp_has_prac, sjtp.has_pws AS sjtp_has_pws, ",
            "sjtp.min_subjects AS sjtp_min_subjects, sjtp.max_subjects AS sjtp_max_subjects, ",
            "scheme.name AS scheme_name, scheme.fields AS scheme_fields,",
            "depbase.id AS depbase_id, depbase.code AS depbase_code,",
            "lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ey.code,",

            "si.gradetype, si.weight_se, si.weight_ce, si.ete_exam, si.is_mandatory, si.is_mand_subj_id, si.is_combi,",
            "si.extra_count_allowed, si.extra_nocount_allowed, si.elective_combi_allowed, si.has_practexam,",
            "si.has_pws, si.is_core_subject, si.is_mvt, si.is_wisk,",
            "si.reex_se_allowed, si.max_reex, si.no_thirdperiod, si.no_exemption_ce,",

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
            logger.debug('sql: ' + str(sql))
        newcursor = connection.cursor()
        newcursor.execute(sql, sql_keys)
        schemeitem_rows = af.dictfetchall(newcursor)

    return schemeitem_rows
# --- end of create_schemeitem_rows


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
                printpdf.draw_exam(canvas, sel_exam_instance, user_lang)
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
class ExamDownloadExamJsonView(View):  # PR2021-05-06

    def get(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('===== ExamDownloadExamJsonView ===== ')
            logger.debug('list: ' + str(list) + ' ' + str(type(list)))

        exam_pk = None

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
            sel_examperiod, sel_examtype, sel_subject_pkNIU = dl.get_selected_examperiod_examtype_from_usersetting(request)

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

def get_assignment_keys_dict(amount, assignment, keys):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_assignment_keys_dict -----')

    # - create dict with assignments PR2021-05-08
    assignment_keys_dict = {}
    if amount and assignment:
        # assignment: 1:4|2:5|3:6|4:M
        maxchar_maxscore_dict = {}
        minscore_dict = {}
        for qa in assignment.split('|'):
            # qa_arr: ['1', '4;;']
            qa_arr = qa.split(':')
            if len(qa_arr) > 0:
                q_number = int(qa_arr[0])
                if logging_on:
                    logger.debug('qa_arr: ' + str(qa_arr) + ' ' + str(type(qa_arr)))
                if qa_arr[1]:
                    value_list = qa_arr[1].split(';')

                    value = ''
                    if value_list[1]:
                        value = value_list[1]
                    elif value_list[0]:
                        value += value_list[0]
                    if value:
                        maxchar_maxscore_dict[q_number] = value

                    if value_list[2]:
                        minscore_dict[q_number] = value_list[2]

        keys_dict = {}
        if keys:
            for qa in keys.split('|'):
                qa_arr = qa.split(':')
                if len(qa_arr) > 0:
                    keys_dict[int(qa_arr[0])] = qa_arr[1]
        if logging_on:
            logger.debug('keys_dict: ' + str(keys_dict) + ' ' + str(type(keys_dict)))

        for q_number in range(1, amount + 1):  # range(start_value, end_value, step), end_value is not included!
            if q_number in maxchar_maxscore_dict:
                value = maxchar_maxscore_dict.get(q_number, '')
                if q_number in keys_dict:
                    value += ' - ' +  keys_dict.get(q_number,'')
                if q_number in minscore_dict:
                    value += ' - min:' + minscore_dict.get(q_number,'')
                assignment_keys_dict[q_number] = value

    return assignment_keys_dict


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
