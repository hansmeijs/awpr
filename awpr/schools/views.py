# PR2018-04-14
from django.contrib.auth.decorators import login_required # PR2018-04-01

from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

from django.db import connection
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect, Http404

from datetime import datetime

from django.shortcuts import render, redirect #, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView, FormView

from schools.models import Country, Country_log, Examyear, Examyear_log, Department, Department_log, Schoolbase, School, School_log

from accounts import views as acc_view

from awpr import settings as s
from awpr import functions as af
from awpr import constants as c
from awpr import validators as av
from awpr import menus as awpr_menu
from awpr import downloads as dl

from schools import functions as sf
from schools import dicts as sd
from schools import models as sch_mod
from accounts import models as acc_mod

import pytz
import json
import logging
logger = logging.getLogger(__name__)

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)

# PR2018-05-06
from django.utils.translation import activate, get_language_info, ugettext_lazy as _


def home(request):
    # PR2018-04-29
    # function get_headerbar_param sets:
    # - activates request.user.language
    # - display/select schoolyear, schoolyear list, color red when not this schoolyear
    # - display/select school, school list
    # - display user dropdown menu
    # note: schoolyear, school and user are only displayed when user.is_authenticated

    #logger.debug('  ==========  home ==========')

    # set headerbar parameters PR2018-08-06
    display_school = False
    display_department = False
    if request.user:
        display_school = True
        display_department = True
    _param = awpr_menu.get_headerbar_param(request, 'home', {
        'display_school': display_school,
        'display_department': display_department
    })
    # PR2019-02-15 go to login form if user is not authenticated
    # PR2019-02-15 temporary disabled
    #if request.user.is_authenticated:    # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.

    #logger.debug('_param: ' + str(_param))
    return render(request, 'home.html', _param)
    #else:
     #   return redirect('login')


def Loggedin(request):
    #logger.debug('  ==========  Loggedin ==========')
    # redirect to saved_href of last selected menubutton # PR2018-12-25 # PR2020-10-22 PR2021-01-25

# retrieve last opened page from, so at next login this page will open. Uses in LoggedIn
    sel_page = None
    if request and request.user:
        req_user = request.user
        #logger.debug('req_user: ' + str(req_user))
        sel_page_dict = req_user.get_usersetting_dict('sel_page')
        #logger.debug('sel_page_dict: ' + str(sel_page_dict))

        if sel_page_dict is not None:
            sel_page = sel_page_dict.get('page')
# get page_url of sel_page, rturns 'home' when not found
    page_url = awpr_menu.get_saved_page_url(sel_page, request)
    #logger.debug('page_url: ' + str(page_url))

    return HttpResponseRedirect(reverse_lazy(page_url))


# === EXAMYEAR =====================================
@method_decorator([login_required], name='dispatch')
class ExamyearListView(View):
    # PR2018-08-06 PR2018-05-10 PR2018-03-02 PR2020-10-04 PR2021-03-25

    def get(self, request):
        logger.debug(" =====  ExamyearListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_examyear'
        # don't show dep and school on page examyear
        # Note: set display_school / display_dep also in download_setting
        display_school = (request and request.user and request.user.role <= c.ROLE_008_SCHOOL)
        display_department = False
        param = {'display_school': display_school, 'display_dep': display_department}
        headerbar_param = awpr_menu.get_headerbar_param(request, page, param)

# - save this page in Usersetting, so at next login this page will open. Uses in LoggedIn
        if request and request.user:
            request.user.set_usersetting_dict('sel_page', {'page': page})

        logger.debug("headerbar_param: " + str(headerbar_param))

        return render(request, 'examyears.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class ExamyearUploadView(UpdateView):  # PR2020-10-04

    def post(self, request, *args, **kwargs):
        logging_on = s.LOGGING_ON

        update_wrap = {}
        examyear_rows = []

        if request.user is not None and request.user.country is not None:
            req_user = request.user
            permit_list, requsr_usergroups_list = acc_view.get_userpermit_list('page_examyear', req_user)
            has_permit = 'crud_examyear' in permit_list

        # - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if has_permit and upload_json:
                upload_dict = json.loads(upload_json)

                append_dict = {}
                msg_list = []

# - get mode
                mode = upload_dict.get('mode')

# - get country of requsr, only if country is not locked
                country = None
                if request.user.country and not request.user.country.locked:
                    country = request.user.country
                if logging_on:
                    logger.debug(' ')
                    logger.debug(' ============= ExamyearUploadView ============= ')
                    logger.debug('upload_dict' + str(upload_dict))
                    logger.debug('country: ' + str(country))
                    logger.debug('mode:    ' + str(mode))

                if country:
# - get current examyear - when mode is 'create': examyear is None. It will be created at "elif mode == 'create'"
                    # only if examyear.country equals request.user.country
                    examyear_id = upload_dict.get('examyear_pk')
                    examyear = sch_mod.Examyear.objects.get_or_none(
                        id=examyear_id,
                        country=country
                    )
                    if logging_on:
                        logger.debug('examyear: ' + str(examyear))

# +++ delete examyear
                    if mode == 'delete':
                        if examyear:
                            this_text = _("Exam year '%(tbl)s' ") % {'tbl': str(examyear.code)}
        # - check if examyear is closed or schools have activated or locked it
                            msg_err = av.validate_delete_examyear(examyear)
                            if msg_err:
                                msg_list.append(msg_err)
                                if logging_on:
                                    logger.debug('msg_err: ' + str(msg_err))

                            else:
                                if logging_on:
                                    logger.debug('delete examyear: ' + str(examyear))
                                examyear_pk = examyear.pk
                                deleted_ok = sch_mod.delete_instance(examyear, msg_list, request, this_text)
                                if logging_on:
                                    logger.debug('deleted_ok' + str(deleted_ok))

                                if deleted_ok:
                                    # - add deleted_row to examyear_rows
                                    examyear_rows.append({'pk': examyear_pk,
                                                         'mapid': 'examyear_' + str(examyear_pk),
                                                         'deleted': True})
                                    instance = None
                                if logging_on:
                                    logger.debug('examyear_rows' + str(examyear_rows))
# +++ create new examyear
                    elif mode == 'create':
     # - validate unique examyear_code_int
                        examyear_code_int = upload_dict.get('examyear_code')
                        msg_err = av.validate_unique_examyear(examyear_code_int, request)
                        if msg_err:
                            msg_list.append(msg_err)
                            if logging_on:
                                logger.debug('msg_err: ' + str(msg_err))
                        else:
     # - create new examyear
                            examyear, msg_err = create_examyear(country, examyear_code_int, request)
                            if examyear:
                                append_dict['created'] = True
    # - copy all tables from last examyear existing examyear
                                msg_err = copy_tables_from_last_year(examyear, request)
                            if msg_err:
                                msg_list.append(msg_err)
                                if logging_on:
                                    logger.debug('msg_err: ' + str(msg_err))

# +++ update examyear, skip when it is created. All fields are saved in create_examyear
                    if examyear and mode != 'create':
                        update_examyear(examyear, upload_dict, msg_list, request)

                    if msg_list:
                        append_dict['error'] = msg_list
# - add update_dict to update_wrap
                    if examyear:
                        examyear_rows = sd.create_examyear_rows(
                            country=country,
                            append_dict=append_dict,
                            examyear_pk=examyear.pk
                        )
                    else:
                        # examyear is None when error on creating examyear. Return msg_err still
                        if append_dict:
                            examyear_rows = [append_dict]
        update_wrap['updated_examyear_rows'] = examyear_rows

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_examyear(country, examyear_code_int, request):
    # --- create examyear # PR2019-07-30 PR2020-10-05
    logger.debug(' ----- create_examyear ----- ')
    logger.debug('examyear_code_int: ' + str(examyear_code_int) + ' ' + str(type(examyear_code_int)))

    instance = None
    msg_err = None
    if country and examyear_code_int:

# - create and save examyear
        try:
            instance = sch_mod.Examyear(
                country=request.user.country,
                code=examyear_code_int,
                #published=False,
                #locked=False,
                createdat=timezone.now()
                #publishedat=None,
                #lockedat=None,
            )
            instance.save(request=request)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            caption = _('Exam year')
            name = str(examyear_code_int) if examyear_code_int else '---'
            msg_err = str(_('An error occurred.')) + ' ' + \
                      str(_("%(caption)s '%(val)s' could not be created.") % {'caption': caption, 'val': name})

    return instance, msg_err


#######################################################
def update_examyear(instance, upload_dict, msg_list, request):
    # --- update existing and new instance PR2019-06-06
    # add new values to update_dict (don't reset update_dict, it has values)
    logger.debug(' ------- update_examyear -------')
    logger.debug('upload_dict: ' + str(upload_dict))
    logger.debug('instance: ' + str(instance))

    # FIELDS_EXAMYEAR = ('country', 'examyear', 'published', 'locked',
    #                   'createdat', 'publishedat', 'lockedat', 'modifiedby', 'modifiedat')
    # upload_dict: {'table': 'examyear', 'country_pk': 1, 'examyear_pk': 58, 'mapid': 'examyear_58', 'mode': 'update', 'published': True}

    if instance:
        try:
            save_changes = False
            for field in ('examyear', 'published', 'locked'):
                logger.debug('field: ' + str(field))

# --- get new_value from  upload_dict  if it exists
                if field in upload_dict:
                    new_value = upload_dict.get(field)
                    saved_value = getattr(instance, field)

                    logger.debug('new_value: ' + str(new_value))
                    logger.debug('saved_value: ' + str(saved_value))

# --- update field 'examyear', required field
                    if field == 'examyear':
                        if new_value != saved_value:
                            msg_err = av.validate_unique_examyear(new_value, request)
                            # validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                            if not msg_err:
                                # c. save field if changed and no_error
                                setattr(instance, field, new_value)
                                save_changes = True
                            else:
                                msg_list.append(msg_err)

# --- update fieldpython manage.py runserver
                    # 'published', 'locked'
                    elif field in ('published', 'locked'):
                        if new_value is None:
                            new_value = False
                        #logger.debug('inactive saved_value]: ' + str(saved_value) + ' ' + str(type(saved_value)))
                        if new_value != saved_value:
                            setattr(instance, field, new_value)
                            save_changes = True
                            # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
                            new_date = timezone.now()
                            date_field = field + 'at'
                            setattr(instance, date_field, new_date)
# --- end of for loop ---

# --- save changes
            if save_changes:
                    instance.save(request=request)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            msg_list.append(str(_('An error occurred. The changes have not been saved.')))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def copy_tables_from_last_year(new_examyear_instance, request):
    # --- copy_tables_from_last_year # PR2019-07-30 PR2020-10-05 PR2021-04-25

    logger.debug(' ------- copy_tables_from_last_year -------')
    logger.debug('new_examyear_instance: ' + str(new_examyear_instance) + ' ' + str(type(new_examyear_instance)))

    prev_examyear_instance, msg_err = sf.get_previous_examyear_instance(new_examyear_instance)
    if new_examyear_instance and prev_examyear_instance:

        sf.copy_exfilestext_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance)
        mapped_deps = sf.copy_deps_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance)
        mapped_schools = sf.copy_schools_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance)
        # School_message
        # Published
        # PrivateDocument
        # Entrylist
        # Schoolsetting
        mapped_levels = sf.copy_levels_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance)
        mapped_sectors = sf.copy_sectors_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance)
        mapped_subjecttypes = sf.copy_subjecttypes_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance)
        # Norm
        mapped_schemes = sf.copy_schemes_from_prev_examyear(request, prev_examyear_instance, mapped_deps, mapped_levels, mapped_sectors)
        mapped_subjects = sf.copy_subjects_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance)
        mapped_schemeitems = sf.copy_schemeitems_from_prev_examyear(request, prev_examyear_instance, mapped_schemes, mapped_subjects, mapped_subjecttypes)
        # Exam
        # Package
        # Packageitem
        # Cluster
        # Birthcountry
        # Birthplace
        # Student
        # Result
        # Resultnote
        # Studentsubject
        # Studentsubjectnote
        # Noteattachment
        # Grade
        #
    # TODO copy  packages
    #logger.debug(' ----- create_examyear ----- ')
    return msg_err


# === School =====================================
@method_decorator([login_required], name='dispatch')
class SchoolListView(View):  # PR2018-08-25 PR2020-10-21 PR2021-03-25

    def get(self, request):
        #logger.debug('  =====  SchoolListView ===== ')

# - get headerbar parameters
        page = 'page_school'
        params = awpr_menu.get_headerbar_param(request, page)

# - save this page in Usersetting, so at next login this page will open. Uses in LoggedIn
        if request and request.user:
            request.user.set_usersetting_dict('sel_page', {'page': page})

        return render(request, 'schools.html', params)


@method_decorator([login_required], name='dispatch')
class SchoolUploadView(View):  # PR2020-10-22 PR2021-03-27

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= SchoolUploadView ============= ')

        update_wrap = {}

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

            permit_list, requsr_usergroups_list = acc_view.get_userpermit_list('page_school', req_user)
            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))

            permit_create = 'create_school' in permit_list
            permit_edit = 'edit_school' in permit_list
            permit_delete ='delete_school' in permit_list

            if permit_create or permit_edit or permit_delete:
    # -  get user_lang
                requsr_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(requsr_lang)

    # --- get upload_dict from request.POST
                upload_json = request.POST.get('upload', None)
                if upload_json:
                    upload_dict = json.loads(upload_json)

    # --- get variables from upload_dict PR2020-12-25
                    examyear_pk = upload_dict.get('examyear_pk')
                    school_pk = upload_dict.get('school_pk')
                    is_create = upload_dict.get('create', False)
                    is_delete = upload_dict.get('delete', False)

                    school_rows = []
                    append_dict = {}
                    error_dict = {}

                    if logging_on:
                        logger.debug('upload_dict' + str(upload_dict))
                        logger.debug('school_pk: ' + str(school_pk))
                        logger.debug('is_create: ' + str(is_create))
                        logger.debug('is_delete: ' + str(is_delete))

    # --- get examyear (examyear is parent of school)
                    examyear = sch_mod.Examyear.objects.get_or_none(pk=examyear_pk)
                    if examyear is None:
                        msg_err = _("Exam year not found.")
                        if logging_on :
                            logger.debug('msg_err: ' + str(msg_err))
                    else:
                        school = None
# +++ Create new school
                        if is_create:
                            if permit_create:

                                school, msg_err = create_school(examyear, upload_dict, request)

                                if school:
                                    append_dict['created'] = True
                                elif msg_err:
                                    error_dict['err_create'] = msg_err

                                if logging_on:
                                    logger.debug('school: ' + str(school))

    # +++ Delete school
                        elif is_delete:
                            if permit_delete:
                                school = sch_mod.School.objects.get_or_none(id=school_pk)

                                if logging_on:
                                    logger.debug('school: ' + str(school))

                                if school:
                                    this_text = _("School '%(tbl)s' ") % {'tbl': school.name}
                                    #logger.debug('this_text: ' + str(this_text))
                            # a. check if school has child rows, put msg_err in update_dict when error
                                    msg_err = None #validate_employee_has_emplhours(employee)
                                    if msg_err:
                                        error_dict['err_delete'] = msg_err
                                    else:
                            # b. check if there are teammembers with this employee: absence teammembers, remove employee from shift teammembers
                                        # delete_employee_from_teammember(employee, request)
                            # c. delete school
                                        deleted_ok = sch_mod.delete_instance(school, error_dict, request, this_text)
                                        #logger.debug('deleted_ok' + str(deleted_ok))
                                        if deleted_ok:
                             # - add deleted_row to school_rows
                                            school_rows.append({'pk': school_pk,
                                                                'table': 'school',
                                                                 'mapid': 'school_' + str(school_pk),
                                                                 'deleted': True})
                                            school = None
                                        #logger.debug('school_rows' + str(school_rows))

    # --- get existing school
                        else:
                            school = sch_mod.School.objects.get_or_none(id=school_pk)

                        if school:
                            if permit_create or permit_edit:
    # --- Update school, also when it is created. When deleted: school is None
                            #  Not necessary when created. Most fields are required. All fields are saved in create_school

                                update_school(school, upload_dict, error_dict, request)

                                #logger.debug('error_dict' + str(error_dict))
    # --- add update_dict to update_wrap
                                if error_dict:
                                    append_dict['error'] = error_dict

                                permit_dict = {
                                    'requsr_role': req_user.role,
                                    'requsr_schoolbase_pk': req_user.schoolbase_id
                                }
                                school_rows = sd.create_school_rows(
                                    examyear=examyear,
                                    permit_dict=permit_dict,
                                    append_dict=append_dict,
                                    school_pk=school.pk
                                )

                        update_wrap['updated_school_rows'] = school_rows

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=LazyEncoder))


@method_decorator([login_required], name='dispatch')
class SchoolImportView(View):  # PR2020-10-01

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

            param = awpr_menu.get_headerbar_param(request, 'school_import', {'captions': captions, 'setting': coldefs_json})

        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'subjectimport.html', param)


@method_decorator([login_required], name='dispatch')
class SchoolImportUploadSetting(View):   # PR2019-03-10
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

        return HttpResponse(json.dumps(schoolsetting_dict, cls=LazyEncoder))
# --- end of SubjectImportUploadSetting

@method_decorator([login_required], name='dispatch')
class SchoolImportUploadData(View):  # PR2018-12-04 PR2019-08-05 PR2020-06-04

    def post(self, request):
        #logger.debug(' ========================== SchoolImportUploadData ========================== ')
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
                params = import_schools(upload_dict, user_lang, request)

        return HttpResponse(json.dumps(params, cls=LazyEncoder))

# --- end of SubjectImportUploadData


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


@method_decorator([login_required], name='dispatch')
class SchoolAwpUploadView(View):  # PR2021-05-03

    def post(self, request):
        logging_on = s.LOGGING_ON

        files = request.FILES
        file = files.get('file')
        if logging_on:
            logger.debug(' ============= SchoolAwpUploadView ============= ')
            logger.debug('files: ' + str(files) + ' ' + str(type(files)))
            logger.debug('file: ' + str(file) + ' ' + str(type(file)))

        # function creates, deletes and updates studentsubject records of current student PR2020-11-21
        update_wrap = {}

        #<PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated
        has_permit = False
        if request.user and request.user.country and request.user.schoolbase:
            has_permit = True # (request.user.role > c.ROLE_002_STUDENT and request.user.is_group_edit)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                logger.debug('upload_dict: ' + str(upload_dict))

                # - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, is_locked, \
                examyear_published, school_activated, is_requsr_school = \
                    dl.get_selected_examyear_school_dep_from_usersetting(request)

                file_type = upload_dict.get('file_type')
                file_name = upload_dict.get('file_name')
                file_size = upload_dict.get('file_size')


# 9. return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=LazyEncoder))
# - end of SchoolAwpUploadView

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def create_school(examyear, upload_dict, request):
    # --- create school # PR2019-07-30 PR2020-10-22
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_school ----- ')

    school = None
    msg_err = None

    if examyear:
# - get value of 'abbrev'
        code = upload_dict.get('code')
        abbrev = upload_dict.get('abbrev')
        name = upload_dict.get('name')
        article = upload_dict.get('article')
        depbases = upload_dict.get('depbases')

        if logging_on:
            logger.debug('code: ' + str(code))
            logger.debug('abbrev: ' + str(abbrev))
            logger.debug('name: ' + str(name))
            logger.debug('article: ' + str(article))
            logger.debug('depbases: ' + str(depbases) + str(type(depbases)))

        msg_err = None
        if abbrev and name and code:
            lookup_value = code
# - validate if code already exists
            schoolbase, school, msg_err_multiple_found = lookup_schoolbase(lookup_value, request)
            if msg_err_multiple_found is None:
                if schoolbase is not None:
                    if school is not None:
                        msg_err = _("School code '%(fld)s' already exists.") % {'fld': lookup_value}
                    else:
                        msg_err = _("School code '%(fld)s' already exists in other exam years.") % {'fld': lookup_value}
# - if schoolbase exitsts but child school does not exist this examyear: add school

            if logging_on:
                logger.debug('schoolbase: ' + str(schoolbase))
                if msg_err:
                    logger.debug('msg_err: ' + str(msg_err))

# - create and save school
            if msg_err is None:
                try:
                    # First create base record. base.id is used in School. Create also saves new record
                    schoolbase = sch_mod.Schoolbase.objects.create(
                        country=request.user.country,
                        code=code
                    )
                    if logging_on:
                        logger.debug('schoolbase: ' + str(schoolbase))

                    school = sch_mod.School(
                        base=schoolbase,
                        examyear=examyear,
                        name=name,
                        abbrev=abbrev,
                        article=article,
                        depbases=depbases
                    )
                    school.save(request=request)
                    if logging_on:
                        logger.debug('schoolbase: ' + str(schoolbase))
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))
                else:
                    msg_err = str(_("An error occurred. School '%(val)s' could not be added.") % {'val': name})

    return school, msg_err


#######################################################
def update_school(instance, upload_dict, msg_dict, request):
    # --- update existing and new instance PR2019-06-06
    # add new values to update_dict (don't reset update_dict, it has values)
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_school -------')
        logger.debug('upload_dict' + str(upload_dict))

    # upload_dict = {id: {table: "school", ppk: 1, pk: 1, mapid: "school_1"},
    #                depbases: {value: Array(1), update: true} }

    if instance:
        save_changes = False
        save_parent = False
        schoolbase = instance.base
        for field, new_value in upload_dict.items():
            if field in ('code', 'name', 'abbrev', 'article', 'depbases', 'activated', 'locked'):
                if field == 'code':
                    saved_value = getattr(schoolbase, field)
                else:
                    saved_value = getattr(instance, field)

                if field == 'code':
                    if new_value != saved_value:
                        # TODO validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                        #msg_err = av.validate_code_name_identifier()
                        setattr(schoolbase, field, new_value)
                        save_parent = True

                elif field in ['name', 'abbrev', 'article']:
                    if new_value != saved_value:
                        # TODO validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                        # msg_err = validate_code_name_identifier(
                        msg_err = None
                        if not msg_err:
                            setattr(instance, field, new_value)
                            save_changes = True
                        else:
                            msg_dict['err_' + field] = msg_err

    # 3. save changes in depbases
                elif field == 'depbases':
                    # depbases is string:  "1;2;3", sorted, otherwise "1;2;3" and "3;1;2" will not be equal
                    new_value = '' if new_value is None else new_value
                    saved_value = '' if saved_value is None else saved_value
                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True

    # 4. save changes in field 'inactive'
                elif field in ['activated', 'locked']:
                    new_value = False if new_value is None else new_value

                    #logger.debug('inactive saved_value]: ' + str(saved_value) + ' ' + str(type(saved_value)))
                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True

                        # set time modified if new_value = True, remove time modified when new_value = False
                        mod_at_field = None
                        if field == 'activated':
                            mod_at_field = 'activatedat'
                        elif  field == 'locked':
                            mod_at_field = 'lockedat'
                        if mod_at_field:
                            mod_at = timezone.now() if new_value else None
                            setattr(instance, mod_at_field, mod_at)

                if logging_on:
                    logger.debug('----- field:  ' + str(field))
                    logger.debug('new_value:    ' + str(new_value) + ' ' + str(type(new_value)))
                    logger.debug('saved_value:  ' + str(saved_value) + ' ' + str(type(saved_value)))
                    logger.debug('save_changes: ' + str(save_changes))
                    logger.debug('save_parent:  ' + str(save_parent))

# --- end of for loop ---

# 5. save changes
        if save_parent:
            try:
                schoolbase = instance.base
                schoolbase.save()
                if logging_on:
                    logger.debug('parent changes saved')
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')
        if save_changes:
            try:
                instance.save(request=request)
                if logging_on:
                    logger.debug('instance changes saved')
            except:
                msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



def import_schools(upload_dict, user_lang, request):

    #logger.debug(' -----  import_schools ----- ')
    #logger.debug('upload_dict: ' + str(upload_dict))
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
        school_list = upload_dict.get('schools')
        if school_list:

            today_dte = af.get_today_dateobj()
            today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
            double_line_str = '=' * 80
            indent_str = ' ' * 5
            space_str = ' ' * 30
            logfile = []
            logfile.append(double_line_str)
            logfile.append( '  ' + str(request.user.schoolbase.code) + '  -  ' +
                            str(_('Import schools')) + ' ' + str(_('date')) + ': ' + str(today_formatted))
            logfile.append(double_line_str)

            if lookup_field is None:
                info_txt = str(_('There is no field given to lookup schools. Schools cannot be uploaded.'))
                logfile.append(indent_str + info_txt)
            else:
                if is_test:
                    info_txt = str(_("This is a test. The school data are not saved."))
                else:
                    info_txt = str(_("The school data are saved."))
                logfile.append(indent_str + info_txt)
                lookup_caption = str(get_field_caption('school', lookup_field))
                info_txt = str(_("Schools are looked up by the field: '%(fld)s'.") % {'fld': lookup_caption})
                logfile.append(indent_str + info_txt)
                #if dateformat:
                #    info_txt = str(_("The date format is: '%(fld)s'.") % {'fld': dateformat})
                #    logfile.append(indent_str + info_txt)
                update_list = []
                for school_dict in school_list:
                    # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html

                    update_dict = upload_school(school_list, school_dict, lookup_field,
                                                 awpKey_list, is_test, dateformat, indent_str, space_str, logfile, request)
                    # json_dumps_err_list = json.dumps(msg_list, cls=f.LazyEncoder)
                    if update_dict:  # 'Any' returns True if any element of the iterable is true.
                        update_list.append(update_dict)

                if update_list:  # 'Any' returns True if any element of the iterable is true.
                    params['school_list'] = update_list
            if logfile:  # 'Any' returns True if any element of the iterable is true.
                params['logfile'] = logfile
                        # params.append(new_employee)
    return params


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def upload_school(school_list, school_dict, lookup_field, awpKey_list,
                   is_test, dateformat, indent_str, space_str, logfile, request):  # PR2019-12-17 PR2020-10-21
    #logger.debug('----------------- import school  --------------------')
    #logger.debug(str(school_dict))
    # awpKeys are: 'code', 'name', 'sequence', 'depbases'

# - get index and lookup info from school_dict
    row_index = school_dict.get('rowindex', -1)
    new_code = school_dict.get('code')
    new_name = school_dict.get('name')
    new_sequence = school_dict.get('sequence')
    new_depbases = school_dict.get('depbases')

# - create update_dict
    update_dict = {'id': {'table': 'school', 'rowindex': row_index}}

# - give row_error when lookup went wrong
    # multiple_found and value_too_long return the lookup_value of the error field

    lookup_field_caption = str(get_field_caption('school', lookup_field))
    lookup_field_capitalized = '-'
    if lookup_field_caption:
        lookup_field_capitalized = lookup_field_caption.capitalize()
    is_skipped_str = str(_("is skipped."))
    skipped_str = str(_("Skipped."))
    logfile.append(indent_str)
    msg_err = None
    log_str = ''

    schoolbase = None
    school = None

# check if lookup_value has value ( lookup_field = 'code')
    lookup_value = school_dict.get(lookup_field)
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
        field_caption = str(get_field_caption('school', 'name'))
        log_str = str(_("No value for required field: '%(fld)s'.") % {'fld': field_caption})
        msg_err = ' '.join((skipped_str, log_str))

# check if school name  is not too long
    elif len(new_name) > c.MAX_LENGTH_NAME:
        value_too_long_str = str(_("Value '%(val)s' is too long.") % {'val': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_NAME})
        log_str = value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))
    else:

# - check if lookup_value occurs mutiple times in Excel file
        excel_list_multiple_found = False
        excel_list_count = 0
        for dict in school_list:
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

# - check if schoolbase with this code exists in request.user.country. schoolbase has value when only one found
        # lookup_value = school_dict.get(lookup_field)
        schoolbase, multiple_found = lookup_schoolbase(lookup_value, request)
        if multiple_found:
            log_str = str(_("Value '%(fld)s' is found multiple times.") % {'fld': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

# - check if school with this schoolbase exists in request.user.examyear. school has value when only one found
        multiple_schools_found = False
        if schoolbase:
            school, multiple_schools_found = lookup_school(schoolbase, request)
        if multiple_schools_found:
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

# - create new schoolbase when schoolbase not found in database
        if schoolbase is None:
            try:
                schoolbase = sch_mod.Schoolbase(
                    country=request.user.country,
                    code=new_code
                )
                if schoolbase:
                    schoolbase.save()
            except:
# - give error msg when creating schoolbase failed
                error_str = str(_("An error occurred. The school is not added."))
                logfile.append(" ".join((code_text, error_str )))
                update_dict['row_error'] = error_str

        if schoolbase :
# - create new school when school not found in database
            is_existing_school = False
            save_instance = False

            if school is None:
                try: # TODO change request.user.examyear to sel_examyear
                    school = sch_mod.School(
                        base=schoolbase,
                        examyear=request.user.examyear,
                        name=new_name
                    )
                    if school:
                        school.save(request=request)
                        update_dict['id']['created'] = True
                        logfile.append(code_text + str(_('is added.')))
                except:
    # - give error msg when creating school failed
                    error_str = str(_("An error occurred. The school is not added."))
                    logfile.append(" ".join((code_text, error_str )))
                    update_dict['row_error'] = error_str
            else:
                is_existing_school = True
                logfile.append(code_text + str(_('already exists.')))

            if school:
                # add 'id' at the end, after saving the school. Pk doent have value until instance is saved
                #update_dict['id']['pk'] = school.pk
                #update_dict['id']['ppk'] = school.company.pk
                #if school:
                #    update_dict['id']['created'] = True

                # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
                # solved bij wrapping with str()

                blank_str = '<' + str(_('blank')) + '>'
                was_str = str(_('was') + ': ')
                # FIELDS_schoolS = ('base', 'examyear', 'name', 'abbrev', 'sequence', 'depbases', 'modifiedby', 'modifiedat')
                for field in ('name', 'abbrev', 'sequence', 'depbases'):
                    # --- get field_dict from  upload_dict  if it exists
                    if field in awpKey_list:
                        #('field: ' + str(field))
                        field_dict = {}
                        field_caption = str(get_field_caption('school', field))
                        caption_txt = (indent_str + field_caption + space_str)[:30]

                        if field in ('code', 'name', 'namefirst', 'email', 'address', 'city', 'country'):
                            if field == 'code':
                                # new_code is created in this function and already checked for max_len
                                new_value = new_code
                            else:
                                new_value = school_dict.get(field)
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
                                if not is_existing_school:
                                    logfile.append(caption_txt + (new_value or blank_str))
                    # - get saved_value
                                saved_value = getattr(school, field)
                                if new_value != saved_value:
                    # put new value in school instance
                                    setattr(school, field, new_value)
                                    field_dict['updated'] = True
                                    save_instance = True
                    # create field_dict and log
                                    if is_existing_school:
                                        old_value_str = was_str + (saved_value or blank_str)
                                        field_dict['info'] = field_caption + ' ' + old_value_str
                                        update_str = ((new_value or blank_str) + space_str)[:25] + old_value_str
                                        logfile.append(caption_txt + update_str)

                # add field_dict to update_dict
                        update_dict[field] = field_dict

               # dont save data when it is a test run
                if not is_test and save_instance:
                    employee.save(request=request)
                    update_dict['id']['pk'] = employee.pk
                    update_dict['id']['ppk'] = employee.company.pk
                    # wagerate wagecode
                    # priceratejson additionjson
                    try:
                        employee.save(request=request)
                        update_dict['id']['pk'] = employee.pk
                        update_dict['id']['ppk'] = employee.company.pk
                    except:
        # - give error msg when creating employee failed
                        error_str = str(_("An error occurred. The school data is not saved."))
                        logfile.append(" ".join((code_text, error_str)))
                        update_dict['row_error'] = error_str

    return update_dict
# --- end of upload_school

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def lookup_schoolbase(lookup_value, request, this_pk=None):  # PR2020-10-22
    #logger.debug('----------- lookup_schoolbase ----------- ')
    #logger.debug('lookup_value: ' + str(lookup_value) + ' ' + str(type(lookup_value)))

    # function searches for existing schoolbase
    schoolbase = None
    school = None
    msg_err_multiple_found = None
    if lookup_value and request:
# --- check if 'code' exists multiple times in Schoolbase with filter country
        crit = Q(country=request.user.country) & \
               Q(code__iexact=lookup_value)
# --- exclude this record
        if this_pk:
            crit.add(~Q(pk=this_pk), crit.connector)
        row_count = sch_mod.Schoolbase.objects.filter(crit).count()
        if row_count > 1:
            msg_err_multiple_found = _("Value '%(fld)s' is found multiple times.") % {'fld': lookup_value}
        elif row_count == 1:
    # get schoolbase when only one found (get_or_none does not work with Q, is not necessary, use first() instead)
            schoolbase = sch_mod.Schoolbase.objects.filter(crit).first()
            if schoolbase:
    # --- if 1 found: check if it has school this examyear
                # TODO change request.user.examyear to sel_examyear
                crit = Q(base=schoolbase) & Q(examyear=request.user.examyear)
                school_count = sch_mod.School.objects.filter(crit).count()
                if school_count > 1:
                    msg_err_multiple_found = _("Value '%(fld)s' is found multiple times in this exam year.") % {'fld': lookup_value}
                elif row_count == 1:
    # get school when only one found (get_or_none does not work with Q, is not necessary, use first() instead)
                    school = sch_mod.School.objects.filter(crit).first()

    return schoolbase, school, msg_err_multiple_found


def lookup_school(schoolbase, request):  # PR2019-12-17 PR2020-10-20
    #logger.debug('----------- lookup_school ----------- ')

    school = None
    multiple_schools_found = False

# - search school by schoolbase and request.user.examyear
    # TODO change request.user.examyear to sel_examyear
    if schoolbase:
        # check if school exists multiple times
        row_count = sch_mod.School.objects.filter(base=schoolbase, examyear=request.user.examyear).count()
        if row_count > 1:
            multiple_schools_found = True
        elif row_count == 1:
            # get school when only one found
            school = sch_mod.School.objects.get_or_none(base=schoolbase, examyear=request.user.examyear)

    return school, multiple_schools_found


def get_field_caption(table, field):
    caption = ''
    if table == 'school':
        if field == 'code':
            caption = _('Short name')
        elif field == 'name':
            caption = _('School name')
        elif field == 'sequence':
            caption = _('Sequence')
        elif field == 'depbases':
            caption = _('Departments')
    return caption

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# ++++++++++++++++++   VALIDATORS     ++++++++++++++++++++++++++++++++++++++

class Validate_examyear(object):

    @staticmethod  # PR2018-08-14
    def examyear_does_not_exist_in_country(user_country, new_examyear_int):
        # This validation is used when user wants to add a new examyear (only systenm and insp users can add new examyear)
        # It checks if new examyear exists in user.country. Name of examyear is Int type.
        # returns True if examyear.code does not exist in user.country, otherwise False
        _does_not_exist = True
        if user_country is not None:
            if new_examyear_int is not None:
                if not Examyear.objects.filter(country=user_country, code=new_examyear_int).exists():
                    _does_not_exist = True
        return _does_not_exist

    @staticmethod  # PR2018-08-14
    def get_examyear_in_selected_country(country_selected, user_examyear_int):
        # This validation is used when user wants to change user.country (only systenm users can change user.country)
        # It checks if user.examyear exists in selected_country. Returns examyear in selected_country if it exists, otherwise None
        # If it exists: selected_country is OK, if not: delete user.examyear
        if country_selected is None:
            # if country is None: selected_country NOT OK, exit code is outside this function
            _examyear_country_selected = None
        else:
            if user_examyear_int is None:
                # if examyear is None: selected_country OK (examyear is None, no need to delete)
                _examyear_country_selected = None
            else:
                if Examyear.objects.filter(code=user_examyear_int, country=country_selected).exists():
                    # examyear exists in selected_country: selected_country OK
                    _examyear_country_selected = Examyear.objects.filter(code=user_examyear_int, country=country_selected).get()
                    #logger.debug('get_examyear_in_selected_country _examyear_country_selected: ' + str(_examyear_country_selected) + ' type: ' + str(type(_examyear_country_selected)))
                else:
                    # examyear does not exist in country: select country NOT OK: delete user.examyear
                    _examyear_country_selected = None
        return _examyear_country_selected


    def examyear_exists_in_this_country(cls, country, examyear):
        # PR2018-08-13
        # This validation is used when user wants to add a new examyear (only systenm and insp users can add new examyear)
        # It checks if new examyear exists in user.country.
        # If it exists: new examyear cannot be added, if not: OK

        # except_for_this_examyear not necessray because examyear cannot be changed

        if country is None:
            # if country is None: new examyear cannot be added
            _isOK = False
        else:
            if examyear is None:
                # if examyear is None: new examyear cannot be added
                _isOK = False
            else:
                if Examyear.objects.filter(examyear=examyear, country=country).exists():
                    # examyear exists in country: new examyear cannot be added
                    _isOK = False
                else:
                    # examyear does not exist in country: add examyear OK, new examyear can be added
                    _isOK = True
        return _isOK
