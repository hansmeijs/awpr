# PR2018-07-20
from django.contrib.auth.decorators import login_required # PR2018-04-01
from django.core.paginator import Paginator # PR2018-07-20
from django.core.exceptions import PermissionDenied # PR2018-11-03

from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

from django.db import connection
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect #, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView

from schools import models as sch_mod
from awpr import menus as awpr_menu
from awpr import validators as av
from awpr import functions as af

from subjects import models as subj_mod

from django.contrib.auth.mixins import UserPassesTestMixin

from subjects.forms import SubjectAddForm, SubjectEditForm, \
    LevelAddForm, LevelEditForm, SectorAddForm, SectorEditForm, \
    SubjecttypeAddForm, SubjecttypeEditForm, \
    SchemeAddForm, SchemeEditForm, SchemeitemAddForm, SchemeitemEditForm

from awpr import constants as c
from awpr import downloads as d
from awpr import functions as af
from awpr import validators as av

from accounts import models as acc_mod
from schools import models as sch_mod
from subjects import models as sbj_mod

import json # PR2018-10-25
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
    def post(self, request, *args, **kwargs):
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


@method_decorator([login_required], name='dispatch')
class SchemeitemUploadView(View):  # PR2019-01-24

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= SchemeitemUploadView ============= ')

        # create mode: ssi =  {'mode': 'c', 'scheme_id': '168', 'subj_id': '314', 'wtse': '2', 'wtce': '1',
        #                       'mand': '1', 'comb': '1', 'chal': '0', 'prac': '0', 'sequ': 60}

        #  update mode: ssi = {'mode': 'u', 'ssi_id': '380', 'scheme_id': '168', 'scm_id': '168', 'subj_id': '314',
        #                       'wtse': '2', 'wtce': '0', 'mand': '1', 'comb': '1', 'chal': '0', 'prac': '0',
        #                       'name': 'Duitse taal', 'sequ': '60'}

        #  delete mode: ssi = {"mod":"d", "ssi_id":"393"}

        params = {}
        if request.user is not None and request.user.examyear is not None:
            # get sybject scheme item from  request.POST
            ssi = json.loads(request.POST['ssi'])
            logger.debug("ssi: " + str(ssi))

            # convert values
            # ssi_id only necessary when items are updated
            mode = ssi.get('mode', '')
            ssi_id = int(ssi.get('ssi_id', '0'))
            scheme_id = int(ssi.get('scheme_id', '0')) # scheme_id has always value (retrieved form scheme)
            scm_id = int(ssi.get('scm_id', '0'))  # scm_id = '' scheme_id is retrieved form schemeitem
            subj_id = int(ssi.get('subj_id', '0'))
            sjtp_id = int(ssi.get('sjtp_id', '0'))

            # check if scheme_id and scm_id are the same and ssi_id not None (only at update and remove)
            scm_id_ok = False
            record_saved = False
            if scheme_id:
                if mode == 'c':
                    scm_id_ok = True
                elif ssi_id and scm_id == scheme_id:
                    scm_id_ok = True
            logger.debug("scm_id_ok: " + str(scm_id_ok))

            if scm_id_ok:
                # check if scheme exists
                scheme = subj_mod.Scheme.objects.filter(id=scheme_id).first()
                if scheme:
                    if mode == 'd':
                        # lookup schemeitem
                        schemeitem = subj_mod.Schemeitem.objects.filter(id=ssi_id).first()
                        if schemeitem:
                            schemeitem.delete(request=self.request)
                            record_saved = True
                    else:
                        # check if subject and subjecttype exist
                        subject = subj_mod.Subject.objects.filter(id=subj_id, examyear=request.user.examyear).first()
                        subjecttype = subj_mod.Subjecttype.objects.filter(id=sjtp_id, examyear=request.user.examyear).first()

                        logger.debug('scheme: <' + str(scheme) + '> type: ' + str(type(scheme)))
                        logger.debug('subject: <' + str(subject) + '> type: ' + str(type(subject)))
                        logger.debug('subjecttype: <' + str(subjecttype) + '> type: ' + str(type(subjecttype)))

                        if subject and subjecttype:
                            logger.debug("scheme and subject and subjecttype")
                            if mode == 'c':
                                # create new schemeitem
                                schemeitem = subj_mod.Schemeitem(
                                    scheme=scheme,
                                    subject=subject,
                                    subjecttype=subjecttype
                                )
                            else:
                                # lookup schemeitem
                                schemeitem = subj_mod.Schemeitem.objects.filter(id=ssi_id).first()

                            if schemeitem:
                                # update mode or create mode
                                schemeitem.subjecttype = subjecttype

                                # ------------ import values from ssi  -----------------------------------
                                schemeitem.gradetype = int(ssi.get('grtp_id', '0'))
                                schemeitem.weight_se = int(ssi.get('wtse', '0'))
                                schemeitem.weight_ce = int(ssi.get('wtce', '0'))
                                schemeitem.is_mandatory = (ssi.get('mand', '0') == '1')
                                schemeitem.is_combi = (ssi.get('comb', '0') == '1')
                                schemeitem.elective_combi_allowed = (ssi.get('chal', '0') == '1')
                                schemeitem.has_practexam = (ssi.get('prac', '0') == '1')

                                schemeitem.save(request=self.request)

                                record_saved = True

            # renew list of all Subjects from this department and examyear (included in dep)
            schemeitems = subj_mod.Schemeitem.get_schemeitem_list(scheme)
            params.update({'schemeitems': schemeitems})

            if not record_saved:
                if mode == 'c':
                    err_code = 'err_msg02'
                elif mode == 'd':
                    err_code = 'err_msg04'
                else:
                    err_code = 'err_msg03'
                params.update({'err_code': err_code})

        logger.debug("params: " + str(params))

        # PR2019-02-04 was: return HttpResponse(json.dumps(params))

        # return HttpResponse(json.dumps(params, cls=LazyEncoder), mimetype='application/javascript')

        return HttpResponse(json.dumps(params, cls=af.LazyEncoder))


# ========  SubjectListView  ======= # PR2020-09-29  PR2021-03-25
@method_decorator([login_required], name='dispatch')
class SubjectListView(View):

    def get(self, request):
        #logger.debug(" =====  SubjectListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_subject'
        params = awpr_menu.get_headerbar_param(request, page)

# - save this page in Usersetting, so at next login this page will open. Uses in LoggedIn
        if request.user:
            request.user.set_usersetting_dict('sel_page', {'page': page})

        return render(request, 'subjects.html', params)


def create_subject_rows(setting_dict, append_dict, subject_pk):
    # --- create rows of all subjects of this examyear  PR2020-09-29 PR2020-10-30 PR2020-12-02
    #logger.debug(' =============== create_subject_rows ============= ')

    sel_examyear_pk = af.get_dict_value(setting_dict, ('sel_examyear_pk',))
    # TODO filter sel_depbase_pk
    sel_depbase_pk = af.get_dict_value(setting_dict, ('sel_depbase_pk',))

    # lookup if sel_depbase_pk is in subject.depbases PR2020-12-19
    # use: AND %(depbase_pk)s::INT = ANY(sj.depbases)
    # ANY must be on the right side of =
    # from https://lerner.co.il/2014/05/22/looking-postgresql-arrays/
    # or
    # from https://www.postgresqltutorial.com/postgresql-like/
    # first_name LIKE '%Jen%';
    subject_rows = []
    if sel_examyear_pk:
        depbase_lookup = ''.join( ('%;', str(sel_depbase_pk), ';%') )
        sql_keys = {'ey_id': sel_examyear_pk, 'depbase_pk': depbase_lookup}
        sql_list = ["""SELECT sj.id, sj.base_id, sj.examyear_id,
            CONCAT('subject_', sj.id::TEXT) AS mapid,
            sj.name, sb.code, sj.sequence, sj.depbases,
            sj.modifiedby_id, sj.modifiedat,
            ey.code AS examyear_code,
            SUBSTRING(au.username, 7) AS modby_username
    
            FROM subjects_subject AS sj 
            INNER JOIN subjects_subjectbase AS sb ON (sb.id = sj.base_id) 
            INNER JOIN schools_examyear AS ey ON (ey.id = sj.examyear_id) 
            LEFT JOIN accounts_user AS au ON (au.id = sj.modifiedby_id) 
            
            WHERE sj.examyear_id = %(ey_id)s::INT
            AND CONCAT(';', sj.depbases::TEXT, ';') LIKE %(depbase_pk)s::TEXT

            """]
#             AND CONCAT(';', sj.depbases::TEXT, ';') LIKE CONCAT(';', %(depbase_pk)s::TEXT, ';')
        if subject_pk:
            # when employee_pk has value: skip other filters
            sql_list.append('AND sj.id = %(sj_id)s::INT')
            sql_keys['sj_id'] = subject_pk
        else:
            sql_list.append('ORDER BY sb.code')

        sql = ' '.join(sql_list)

        newcursor = connection.cursor()
        newcursor.execute(sql, sql_keys)
        subject_rows = af.dictfetchall(newcursor)

        # - add messages to subject_row
        if subject_pk and subject_rows:
            # when subject_pk has value there is only 1 row
            row = subject_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    return subject_rows
# --- end of create_subject_rows


@method_decorator([login_required], name='dispatch')
class SubjectUploadView(View):  # PR2020-10-01

    def post(self, request, *args, **kwargs):
        logger.debug(' ============= SubjectUploadView ============= ')

        update_wrap = {}
        has_permit = False
        if request.user is not None and request.user.country is not None and request.user.schoolbase is not None:
            has_permit = True # (request.user.is_perm_planner or request.user.is_perm_hrman)
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
                subject_pk = af.get_dict_value(upload_dict, ('id', 'pk'))
                examyear_pk = af.get_dict_value(upload_dict, ('id', 'ppk'))
                mode = af.get_dict_value(upload_dict, ('id', 'mode'))

                append_dict = {'mode': mode, 'table': 'subject'}
                error_dict = {}
                subject_rows = []
# A. check if examyear exists  (examyear is parent of subject)
                examyear = sch_mod.Examyear.objects.get_or_none(id=examyear_pk, country=request.user.country)
                logger.debug('examyear: ' + str(examyear))
                if examyear and examyear == request.user.examyear:
# C. Delete subject
                    # upload_dict = {'id': {'pk': 164, 'ppk': 37, 'table': 'subject', 'mode': 'delete', 'mapid': 'subject_164'}}
                    if mode == 'delete':
                        subject = sbj_mod.Subject.objects.get_or_none(id=subject_pk, examyear=examyear)
                        logger.debug('subject: ' + str(subject))
                        if subject:
                            this_text = _("Subject '%(tbl)s'") % {'tbl': subject.name}
                    # a. check if employee has emplhours, put msg_err in update_dict when error
                            examyear_is_locked, examyear_has_activated_schools = av.validate_locked_activated_examyear(examyear)
                            msg_err = None #validate_employee_has_emplhours(employee)
                            if examyear_is_locked:
                                append_dict['err_delete'] = str(_('Exam year %(exyr)s is closed.') % {'exyr': examyear.code} +
                                                                '\n' + _('%(item)s cannot be deleted.') % {'item': this_text})
                            elif examyear_has_activated_schools:
                                append_dict['err_delete'] = str(_('There are schools that have activated exam year %(exyr)s.') % {'exyr': examyear.code} +
                                                                '\n' + _('%(item)s cannot be deleted.') % {'item': this_text})
                            else:
                    # b. check if there are teammembers with this employee: absence teammembers, remove employee from shift teammembers
                                # delete_employee_from_teammember(employee, request)
                    # c. delete subject
                                deleted_ok = sch_mod.delete_instance(subject, append_dict, request, this_text)
                                logger.debug('deleted_ok' + str(deleted_ok))
                                if deleted_ok:
                     # - add deleted_row to absence_rows
                                    subject_rows.append({'pk': subject_pk,
                                                         'mapid': 'subject_' + str(subject_pk),
                                                         'deleted': True})
                                    subject = None
                                logger.debug('subject_rows' + str(subject_rows))
                    else:
# D. Create new subject
                        # upload_dict = {'id': {'table': 'subject', 'ppk': 37, 'mode': 'create'},
                        #               'abbrev': {'value': 'ab', 'update': True},
                        #               'sequence': {'value': 15, 'update': True},
                        #               'name': {'value': 'ab', 'update': True},
                        #                depbases': {'value': [], 'update': True}}
                        if mode == 'create':
                            subject, msg_err = create_subject(examyear, upload_dict, request)
                            if subject:
                                append_dict['created'] = True
                            elif msg_err:
                                append_dict['err_create'] = msg_err

                            logger.debug('append_dict' + str(append_dict))
# E. Get existing subject
                        else:
                            subject = sbj_mod.Subject.objects.get_or_none(id=subject_pk, examyear=examyear)

# F. Update subject, also when it is created.
                        #  Not necessary. Most fields are required. All fields are saved in create_subject
                        #if subject:
                            update_subject(subject, examyear, upload_dict, error_dict, request)

# I. add update_dict to update_wrap
                    logger.debug('subject' + str(subject))
                    logger.debug('subject_rows' + str(subject_rows))
                    if subject:
                        if error_dict:
                            append_dict['error'] = error_dict

                        subject_rows = create_subject_rows(
                            examyear_pk=examyear.pk,
                            append_dict=append_dict,
                            subject_pk=subject.pk
                        )
                    if subject_rows:
                        update_wrap['updated_subject_rows'] = subject_rows

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))


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
        if request.user is not None and request.user.examyear is not None and request.user.schoolbase is not None:
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
        if request.user is not None and request.user.examyear is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_group_system)
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
                try:
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
                        error_str = str(_("An error occurred. The subject data is not saved."))
                        logfile.append(" ".join((code_text, error_str)))
                        update_dict['row_error'] = error_str

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
# get subjectbase when only one found
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
        # check if subject exists multiple times
        row_count = subj_mod.Subject.objects.filter(base=subjectbase, examyear=request.user.examyear).count()
        if row_count > 1:
            multiple_subjects_found = True
        elif row_count == 1:
            # get subject when only one found
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
def create_subject(examyear, upload_dict, request):
    # --- create subject # PR2019-07-30 PR2020-10-11
    logger.debug(' ----- create_subject ----- ')

    subject = None
    msg_err = None

    logger.debug('examyear: ' + str(examyear))
    if examyear:

# - get values
        code = af.get_dict_value(upload_dict, ('code', 'value'))
        name = af.get_dict_value(upload_dict, ('name', 'value'))
        sequence = af.get_dict_value(upload_dict, ('sequence', 'value'), 9999)
        depbases = af.get_dict_value(upload_dict, ('depbases', 'value'))
        logger.debug('code: ' + str(code))
        logger.debug('name: ' + str(name))
        logger.debug('sequence: ' + str(sequence))
        logger.debug('depbases: ' + str(depbases) + str(type(depbases)))
        if code and name:
# - validate abbrev checks null, max_len, exists and is_lokced
            msg_err = av.validate_subject_code(
                code=code,
                cur_subject=None
            )

# - create and save subject
            if not msg_err:

               # try:
                    # First create base record. base.id is used in Subject. Create also saves new record
                base = sbj_mod.Subjectbase.objects.create(
                    country=examyear.country,
                    code=code
                )
                logger.debug('base: ' + str(base))

                subject = sbj_mod.Subject(
                    base=base,
                    examyear=examyear,
                    name=name,
                    sequence=sequence,
                    depbases=depbases
                )
                subject.save(request=request)
                logger.debug('subject: ' + str(subject))
                #except:
                #    msg_err = str(_("An error occurred. Subject '%(val)s' could not be added.") % {'val': name})

    logger.debug('subject: ' + str(subject))
    logger.debug('msg_err: ' + str(msg_err))
    return subject, msg_err


#######################################################
def update_subject(instance, parent, upload_dict, msg_dict, request):
    # --- update existing and new instance PR2019-06-06
    # add new values to update_dict (don't reset update_dict, it has values)
    #logger.debug(' ------- update_subject -------')
    #logger.debug('upload_dict' + str(upload_dict))

    if instance:
        # FIELDS_SUBJECT = ('base', 'examyear', 'name', 'abbrev','sequence', 'depbases', 'modifiedby', 'modifiedat')
        save_changes = False
        for field in c.FIELDS_SUBJECT:

# --- get field_dict from  upload_dict  if it exists
            field_dict = upload_dict[field] if field in upload_dict else {}
            if field_dict:
                if 'update' in field_dict:
# a. get new_value and saved_value
                    new_value = field_dict.get('value')
                    saved_value = getattr(instance, field)

# 2. save changes in field 'name', 'abbrev'
                    if field in ['name', 'abbrev']:
                        if new_value != saved_value:
            # validate_code_name_id checks for null, too long and exists. Puts msg_err in update_dict
                            """
                            msg_err = validate_code_name_identifier(
                                table='subject',
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
                    elif field in ['namefirst', 'namelast']:
                        if new_value != saved_value:
                            name_first = None
                            name_last = None
                            if field == 'namefirst':
                                name_first = new_value
                                name_last = getattr(instance, 'namelast')
                            elif field == 'namelast':
                                name_first = getattr(instance, 'namefirst')
                                name_last = new_value
                            # check if subject namefirst / namelast combination already exists
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

# 3. save changes in depbases
                    elif field == 'depbases':
                        # save new value when it has different length
                        len_new = len(new_value) if new_value else 0
                        len_saved = len(saved_value) if saved_value else 0
                        if len_new != len_saved:
                            setattr(instance, field, new_value)
                            save_changes = True
                        elif len_new:
                        # compare items in sorted list when len>0 (givers error otherwise)
                            new_value_sorted = sorted(new_value)
                            saved_value_sorted = sorted(saved_value)
                            if new_value_sorted != saved_value_sorted:
                                setattr(instance, field, new_value_sorted)
                                save_changes = True

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

# 5. save changes
        if save_changes:
            try:
                instance.save(request=request)
            except:
                msg_dict['err_update'] = _('An error occurred. The changes have not been saved.')

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#  =========== Ajax requests  ===========


def create_scheme_rows(setting_dict, append_dict, scheme_pk):
    # --- create rows of all schemes of this examyear PR2020-11-16
    # logger.debug(' =============== create_scheme_rows ============= ')
    scheme_rows = []
    examyear_pk = setting_dict.get('sel_examyear_pk')
    depbase_pk = setting_dict.get('sel_depbase_pk')
    if examyear_pk:
        sql_keys = {'ey_id': examyear_pk}
        sql_list = ["SELECT scheme.id, scheme.department_id, scheme.level_id, scheme.sector_id,",
            "CONCAT('scheme_', scheme.id::TEXT) AS mapid,",
            "scheme.name, scheme.fields,",
            "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ey.code,",
            "scheme.modifiedby_id, scheme.modifiedat,",
            "SUBSTRING(au.username, 7) AS modby_username",

            "FROM subjects_scheme AS scheme",
            "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = scheme.modifiedby_id)",

            "WHERE dep.examyear_id = %(ey_id)s::INT"]

        if scheme_pk:
            sql_keys['scheme_id'] = scheme_pk
            sql_list.append('AND scheme.id = %(scheme_id)s::INT')
        else:
            if depbase_pk:
                sql_keys['db_id'] = depbase_pk
                sql_list.append('AND dep.base_id = %(db_id)s::INT')
            sql_list.append('ORDER BY scheme.name')

        sql = ' '.join(sql_list)

        newcursor = connection.cursor()
        newcursor.execute(sql, sql_keys)
        scheme_rows = af.dictfetchall(newcursor)

        # - add messages to subject_row
        if scheme_pk and scheme_rows:
            # when subject_pk has value there is only 1 row
            row = scheme_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    return scheme_rows
# --- end of create_scheme_rows


def create_schemeitem_rows(setting_dict, append_dict, scheme_pk):
    # --- create rows of all schemeitems of this examyear PR2020-11-17
    logger.debug(' =============== create_schemeitem_rows ============= ')
    schemeitem_rows = []
    examyear_pk = setting_dict.get('sel_examyear_pk')
    depbase_pk = setting_dict.get('sel_depbase_pk')
    if examyear_pk and depbase_pk:
        sql_keys = {'ey_id': examyear_pk, 'db_id': depbase_pk}
        sql_list = ["SELECT si.id, si.scheme_id, scheme.department_id, scheme.level_id, scheme.sector_id,",
            "CONCAT('schemeitem_', si.id::TEXT) AS mapid,",
            "si.subject_id AS subj_id, subj.name AS subj_name, subjbase.code AS subj_code,",
            "si.subjecttype_id AS sjt_id, subjtype.name AS sjt_name, subjtype.abbrev AS sjt_abbrev, subjtype.sequence AS sjt_sequence,",
            "subjtype.has_prac AS sjt_has_prac, subjtype.has_pws AS sjt_has_pws, subjtype.one_allowed AS sjt_one_allowed,",
            "scheme.name, scheme.fields,",
            "dep.abbrev AS dep_abbrev, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ey.code,",

            "si.gradetype, si.weight_se, si.weight_ce, si.is_mandatory, si.is_combi,",
            "si.extra_count_allowed, si.extra_nocount_allowed, si.elective_combi_allowed, si.has_practexam,",

            "si.modifiedby_id, si.modifiedat,",
            "SUBSTRING(au.username, 7) AS modby_username",

            "FROM subjects_schemeitem AS si",
            "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
            "INNER JOIN subjects_subjecttype AS subjtype ON (subjtype.id = si.subjecttype_id)",
            "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
            "LEFT JOIN subjects_sector AS sct ON (sct.id = scheme.sector_id)",
            "LEFT JOIN accounts_user AS au ON (au.id = si.modifiedby_id)",

            "WHERE dep.examyear_id = %(ey_id)s::INT",
            "AND dep.base_id = %(db_id)s::INT"]

        if scheme_pk:
            # when employee_pk has value: skip other filters
            sql_list.append('AND scheme.id = %(scheme_id)s::INT')
            sql_keys['scheme_id'] = scheme_pk
        else:
            sql_list.append('ORDER BY subjbase.code, subjtype.sequence')

        sql = ' '.join(sql_list)

        newcursor = connection.cursor()
        newcursor.execute(sql, sql_keys)
        schemeitem_rows = af.dictfetchall(newcursor)

    return schemeitem_rows
# --- end of create_schemeitem_rows