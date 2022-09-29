# PR2021-11-15
from django.contrib.auth.decorators import login_required

from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, pgettext_lazy, gettext_lazy as _
from django.views.generic import View

# PR2019-01-04  https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise

# PR2022-02-13 From Django 4 we dont have force_text You Just have to Use force_str Instead of force_text.
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib import colors

from accounts import models as acc_mod
from awpr import menus as awpr_menu
from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import downloads as dl
from awpr import library as awpr_lib

from grades import calc_results as calc_res
from grades import exfiles as grd_exfiles

from students import functions as stud_fnc

import io
import json

import logging
logger = logging.getLogger(__name__)


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


# ========  Student  =====================================

@method_decorator([login_required], name='dispatch')
class ResultListView(View):  # PR2021-11-15

    def get(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('  =====  ResultListView ===== ')

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_result'
        params = awpr_menu.get_headerbar_param(request, page)

# - save this page in Usersetting, so at next login this page will open. Used in LoggedIn
        #         # PR2021-06-22 moved to get_headerbar_param

        return render(request, 'results.html', params)


@method_decorator([login_required], name='dispatch')
class ArchivesListView(View):  # PR2022-03-09

    def get(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' =====  ArchivesListView ===== ')

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_archive'
        params = awpr_menu.get_headerbar_param(request, page)

# - save this page in Usersetting, so at next login this page will open. Used in LoggedIn
        #         # PR2021-06-22 moved to get_headerbar_param

        return render(request, 'archives.html', params)
# - ens of ArchivesListView


@method_decorator([login_required], name='dispatch')
class GetGradelistDiplomaAuthView(View):  # PR2021-11-19

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GetGradelistDiplomaAuthView ============= ')

        update_wrap = {}
        messages = []

# - get permit
        has_permit = af.get_permit_crud_of_this_page('page_result', request)
        if True:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

      # ----- pres_secr_rows, used in results.js
                pres_secr_dict = get_pres_secr_dict(request)

                update_wrap['pres_secr_dict'] = pres_secr_dict
                if logging_on:
                    logger.debug('pres_secr_dict: ' + str(pres_secr_dict))

        # - addd messages to update_wrap
        if len(messages):
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of StudentUploadView


def get_pres_secr_dict(request):  # PR2021-11-18 PR2022-06-17
    # function creates a dict of auth1 and auth2 users
    # also retrieves the selected auth and printdate from schoolsettings

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_pres_secr_dict -----')

    auth_dict = {}
# get selected auth and printdatum from schoolsettings
    if request.user and request.user.schoolbase:
        settings_json = request.user.schoolbase.get_schoolsetting_dict(c.KEY_GRADELIST)
        stored_setting = json.loads(settings_json) if settings_json else {}
        if logging_on:
            logger.debug('    request.user.schoolbase.code: ' + str(request.user.schoolbase.code))
            logger.debug('    stored_setting: ' + str(stored_setting))
            # stored_setting: {'auth1_pk': 120, 'auth2_pk': None, 'printdate': None}

        # auth_dict: {'auth1': [{'pk': 120, 'name': 'jpd'}, {'pk': 116, 'name': 'Hans meijs'}], 'auth2': []}
        sql_keys = {'sb_id': request.user.schoolbase_id, 'c_id': request.user.country_id, 'role': c.ROLE_008_SCHOOL}
        sql_list = ["SELECT au.id, au.last_name,",
                    "(POSITION('" + c.USERGROUP_AUTH1_PRES + "' IN au.usergroups) > 0) AS auth1,",
                    "(POSITION('" + c.USERGROUP_AUTH2_SECR + "' IN au.usergroups) > 0) AS auth2",

                    "FROM accounts_user AS au",
                    "INNER JOIN schools_schoolbase AS sb ON (sb.id = au.schoolbase_id)",
                    "INNER JOIN schools_country AS c ON (c.id = au.country_id)",

                    "WHERE sb.id = %(sb_id)s::INT AND c.id = %(c_id)s::INT AND au.role = %(role)s::INT",
                    "AND ( (POSITION('" + c.USERGROUP_AUTH1_PRES + "' IN au.usergroups) > 0)",
                    "OR (POSITION('" + c.USERGROUP_AUTH2_SECR + "' IN au.usergroups) > 0 ) )"
                    "AND au.activated AND au.is_active"
                    ]
        sql = ' '.join(sql_list)
        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

        for row in rows:
            if logging_on:
                logger.debug('row: ' + str(row))
                # row: {'id': 47, 'last_name': 'Hans', 'auth1': False, 'auth2': True}
            for usergroup in ('auth1', 'auth2'):
                if row.get(usergroup, False):
                    last_name = row.get('last_name')
                    if last_name:
                        pk_int = row.get('id')
                        a_dict = {'pk': pk_int, 'name': last_name}
                        selected_auth_pk = stored_setting.get(usergroup + '_pk')
                        if selected_auth_pk and selected_auth_pk == pk_int:
                            a_dict['selected'] = True
                            auth_dict['_'.join(('sel', usergroup, 'pk'))] = selected_auth_pk

                        if usergroup not in auth_dict:
                            auth_dict[usergroup] = []

                        auth_dict[usergroup].append(a_dict)
# add printdate
        print_date = stored_setting.get('printdate')
        if print_date:
            auth_dict['printdate'] = print_date

    return auth_dict
# - -end of get_pres_secr_dict



# end of GetGradelistDiplomaAuthView


@method_decorator([login_required], name='dispatch')
class GradeDownloadShortGradelist(View):  # PR2022-06-06

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeDownloadShortGradelist ============= ')
        response = None

        req_user = request.user
        if req_user and req_user.country and req_user.schoolbase:

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)

# - get selected examperiod and sel_subject_pk from usersettings
            sel_examperiodNIU, sel_examtype_NIU, sel_subject_pk = \
                dl.get_selected_experiod_extype_subject_from_usersetting(request)

            if logging_on:
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))
                logger.debug('sel_subject_pk: ' + str(sel_subject_pk))

            if sel_school and sel_department:

                # - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)
                sel_lvlbase_pk, sel_sctbase_pk = dl.get_selected_lvlbase_sctbase_from_usersetting(request)
                if logging_on:
                    logger.debug('sel_school: ' + str(sel_school))
                    logger.debug('sel_department: ' + str(sel_department))

                if sel_school and sel_department:

                    # - get library from examyearsetting
                    library = awpr_lib.get_library(sel_examyear, ['gradelist'])

                    # +++ get grade_dictlist
                    student_list = get_gradelist_dictlist(sel_examyear, sel_school, sel_department, sel_lvlbase_pk,
                                                      sel_sctbase_pk, None)

                    # +++ get name of chairperson and secretary
                    # auth_dict = get_pres_secr_dict(request)

                    # - get arial font
                    try:
                        filepath = s.STATICFILES_FONTS_DIR + 'arial220815.ttf'
                        ttfFile = TTFont('Arial', filepath)
                        pdfmetrics.registerFont(ttfFile)
                    except Exception as e:
                        logger.error(getattr(e, 'message', str(e)))

                    # - get Palace_Script_MT font - for testing - it works 2021-10-14
                    """
                    try:
                        filepath = s.STATICFILES_FONTS_DIR + 'Palace_Script_MT.ttf'
                        ttfFile = TTFont('Palace_Script_MT', filepath)
                        pdfmetrics.registerFont(ttfFile)
                    except Exception as e:
                        logger.error(getattr(e, 'message', str(e)))
                    """
                    # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

                    # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                    # temp_file = tempfile.TemporaryFile()
                    # canvas = Canvas(temp_file)

                    buffer = io.BytesIO()
                    canvas = Canvas(buffer)

                    for student_dict in student_list:
                        # recalc result before printing the gradelist
                        draw_short_gradelist(canvas, library, student_dict, request)
                        canvas.showPage()

                    canvas.save()
                    pdf = buffer.getvalue()
                    # pdf_file = File(temp_file)

                    # was: buffer.close()

                    """
                    # TODO as test try to save file in
                    studsubjnote = stud_mod.Studentsubjectnote.objects.get_or_none(pk=47)
                    content_type='application/pdf'
                    file_name = 'test_try.pdf'
                    if studsubjnote and pdf_file:
                        instance = stud_mod.Noteattachment(
                            studentsubjectnote=studsubjnote,
                            contenttype=content_type,
                            filename=file_name,
                            file=pdf_file)
                        instance.save()
                        logger.debug('instance.saved: ' + str(instance))
                    # gives error: 'bytes' object has no attribute '_committed'
                    """

                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = 'inline; filename="testpdf.pdf"'
                    # response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

                    response.write(pdf)

            # except Exception as e:
            #     logger.error(getattr(e, 'message', str(e)))
            #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of GradeDownloadShortGradelist


@method_decorator([login_required], name='dispatch')
class DownloadGradelistDiplomaView(View):  # PR2021-11-15

    def get(self, request, lst):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= DownloadGradelistDiplomaView ============= ')
        response = None

        if request.user and request.user.country and request.user.schoolbase and lst:
            upload_dict = json.loads(lst) if lst != '-' else {}
            if logging_on:
                logger.debug('     upload_dict: ' + str(upload_dict))
                # upload_dict: {'mode': 'prelim', 'print_all': False, 'student_pk_list': [8629], 'auth1_pk': 116, 'printdate': '2021-11-18'}
            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)
            sel_lvlbase_pk, sel_sctbase_pk = dl.get_selected_lvlbase_sctbase_from_usersetting(request)
            if logging_on:
                logger.debug('     sel_school: ' + str(sel_school))
                logger.debug('     sel_department: ' + str(sel_department))

            if sel_school and sel_department:
                student_pk_list = upload_dict.get('student_pk_list')
                is_sxm = sel_examyear.country.abbrev == 'Sxm'
                if logging_on:
                    logger.debug('     sel_examyear.country.abbrev: ' + str(sel_examyear.country.abbrev))
                    logger.debug('     is_sxm: ' + str(is_sxm))

# - get info from upload_dict
        # modes are "calc_results", "prelim", "final", "diploma"
                mode = upload_dict.get('mode')
                is_prelim = mode == 'prelim'

# +++++ calc_batch_student_result ++++++++++++++++++++
                if mode != 'diploma':
                    calc_res.calc_batch_student_result(
                        sel_examyear=sel_examyear,
                        sel_school=sel_school,
                        sel_department=sel_department,
                        student_pk_list=student_pk_list,
                        sel_lvlbase_pk=sel_lvlbase_pk,
                        user_lang=user_lang
                    )

# - print 'Herexamen' instead of 'Afgewezen', only when prelim gradelist is printed
                print_reex = upload_dict.get('print_reex', False) if is_prelim else False
                if logging_on:
                    logger.debug('     mode: ' + str(mode))
                    logger.debug('     print_reex: ' + str(upload_dict.get('print_reex', False)))
                    logger.debug('     is_prelim: ' + str(is_prelim))

# - save printdate and auth in schoolsetting
                auth1_pk = upload_dict.get('auth1_pk')
                auth2_pk = upload_dict.get('auth2_pk')
                printdate = upload_dict.get('printdate')

                settings_key = c.KEY_GRADELIST
                new_setting_dict = {
                    'auth1_pk': auth1_pk,
                    'auth2_pk': auth2_pk,
                    'printdate': printdate,
                }

                if logging_on:
                    logger.debug('     upload_dict: ' + str(upload_dict))
                    logger.debug('     new_setting_dict: ' + str(new_setting_dict))

                new_setting_json = json.dumps(new_setting_dict)
                request.user.schoolbase.set_schoolsetting_dict(settings_key, new_setting_json)

# - get library from examyearsetting
                key_str = 'diploma' if mode == 'diploma' else 'gradelist'
                library = awpr_lib.get_library(sel_examyear, [key_str])

# +++ get grade_dictlist / diploma_dictlist
                if mode == 'diploma':
                    student_list = get_diploma_dictlist(sel_examyear, sel_school, sel_department, sel_lvlbase_pk,
                                                          sel_sctbase_pk,
                                                          student_pk_list)
                else:
                    student_list = get_gradelist_dictlist(sel_examyear, sel_school, sel_department, sel_lvlbase_pk, sel_sctbase_pk,
                                                  student_pk_list)

 # +++ get name of chairperson and secretary
                # auth_dict = get_pres_secr_dict(request)

        # - get arial font
                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'arial220815.ttf'
                    ttfFile = TTFont('Arial', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

        # - get Garamond font
                #try:
                #    filepath = s.STATICFILES_FONTS_DIR + 'Garamond.ttf'
                #    ttfFile = TTFont('Garamond', filepath)
                #    pdfmetrics.registerFont(ttfFile)
                #except Exception as e:
                #    logger.error(getattr(e, 'message', str(e)))

       # - get Garamond font
                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'Garamond_Bold.ttf'
                    ttfFile = TTFont('Garamond_Bold', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))
                # - get Garamond font
                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'Garamond_Regular.ttf'
                    ttfFile = TTFont('Garamond_Regular', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

        # - get Palace_Script_MT font - for testing - it works 2021-10-14
                # PR2022-09-04 Sentry error: Can't open file "/home/uaw/awpr/awpr/static/fonts/Palace_Script_MT.ttf"
                # because extension in filename is TTF instead of ttf > change filename to Palace_Script_MT.TTF
                # but loading ttfFile went ok, is apparently not case-sensitive
                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'Palace_Script_MT.TTF' # was: 'Palace_Script_MT.ttf'
                    ttfFile = TTFont('Palace_Script_MT', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'Palace_Script_MT_Semi_Bold.ttf'
                    ttfFile = TTFont('Palace_Script_MT_Semi_Bold', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

                # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                # temp_file = tempfile.TemporaryFile()
                # canvas = Canvas(temp_file)

                auth1_name, auth2_name = '---', '---'
                # get auth1_pk from upload_dict, check if user exists and has auth1 permission
                if auth1_pk:
                    auth1 = acc_mod.User.objects.get_or_none(
                        pk=auth1_pk,
                        schoolbase=request.user.schoolbase,
                        activated=True,
                        is_active=True,
                        usergroups__contains='auth1'
                    )
                    if auth1:
                        auth1_name = auth1.last_name

                # get auth1_pk from upload_dict, check if user exists and has auth1 permission
                if auth2_pk:
                    auth2 = acc_mod.User.objects.get_or_none(
                        pk=auth2_pk,
                        schoolbase=request.user.schoolbase,
                        activated=True,
                        is_active=True,
                        usergroups__contains='auth2'
                    )
                    if auth2:
                        auth2_name = auth2.last_name

                buffer = io.BytesIO()
                canvas = Canvas(buffer)

                for student_dict in student_list:
                    if mode == 'diploma':
                        if is_sxm:
                            draw_diploma_sxm(canvas, library, student_dict, auth1_name, auth2_name, printdate)
                        else:
                            draw_diploma_cur(canvas, library, student_dict, auth1_name, auth2_name, printdate)

                    else:
                        if is_sxm:
                            draw_gradelist_sxm(canvas, library, student_dict, is_prelim, is_sxm, print_reex, auth1_pk, auth2_pk, printdate, request)
                        else:
                            draw_gradelist_cur(canvas, library, student_dict, is_prelim, is_sxm, print_reex, auth1_pk, auth2_pk, printdate, request)

                    canvas.showPage()

                canvas.save()
                pdf = buffer.getvalue()
                # pdf_file = File(temp_file)

                # was: buffer.close()

                """
                # TODO as test try to save file in
                studsubjnote = stud_mod.Studentsubjectnote.objects.get_or_none(pk=47)
                content_type='application/pdf'
                file_name = 'test_try.pdf'
                if studsubjnote and pdf_file:
                    instance = stud_mod.Noteattachment(
                        studentsubjectnote=studsubjnote,
                        contenttype=content_type,
                        filename=file_name,
                        file=pdf_file)
                    instance.save()
                    logger.debug('instance.saved: ' + str(instance))
                # gives error: 'bytes' object has no attribute '_committed'
                """

                file_name = 'Diploma' if mode == 'diploma' else 'Cijferlijst'
                if len(student_list) == 1:
                    file_name += ' van ' + student_list[0].get('fullname')
                now_formatted = af.get_now_formatted_from_now_arr(upload_dict.get('now_arr'))
                if now_formatted:
                    file_name += ' ' + now_formatted
                file_name += '.pdf'

                response = HttpResponse(content_type='application/pdf')
                #response['Content-Disposition'] = 'inline; filename="testpdf.pdf"'
                response['Content-Disposition'] = 'inline; filename="' + file_name + '"'
                # response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

                response.write(pdf)

        # except Exception as e:
        #     logger.error(getattr(e, 'message', str(e)))
        #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of DownloadGradelistDiplomaView


@method_decorator([login_required], name='dispatch')
class DownloadPokView(View):  # PR2022-07-02

    def get(self, request, lst):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= DownloadPokView ============= ')
        response = None

        if request.user and request.user.country and request.user.schoolbase and lst:
            upload_dict = json.loads(lst) if lst != '-' else {}
            if logging_on:
                logger.debug('     upload_dict: ' + str(upload_dict))
                # upload_dict: {'mode': 'prelim', 'print_all': False, 'student_pk_list': [8629], 'auth1_pk': 116, 'printdate': '2021-11-18'}
            req_user = request.user

    # - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

   # - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)
            sel_lvlbase_pk, sel_sctbase_pk = dl.get_selected_lvlbase_sctbase_from_usersetting(request)
            if logging_on:
                logger.debug('     sel_school: ' + str(sel_school))
                logger.debug('     sel_department: ' + str(sel_department))

            if sel_school and sel_department:
                student_pk_list = upload_dict.get('student_pk_list')
                if logging_on:
                    logger.debug('     student_pk_list: ' + str(student_pk_list))

                auth1_pk = upload_dict.get('auth1_pk')
                auth2_pk = upload_dict.get('auth2_pk')
                printdate = upload_dict.get('printdate')

                settings_key = c.KEY_GRADELIST
                new_setting_dict = {
                    'auth1_pk': auth1_pk,
                    'auth2_pk': auth2_pk,
                    'printdate': printdate,
                }
                new_setting_json = json.dumps(new_setting_dict)
                request.user.schoolbase.set_schoolsetting_dict(settings_key, new_setting_json)

        # - get library from examyearsetting
                library = awpr_lib.get_library(sel_examyear, ['exform', 'ex6', 'gradelist'])

                proof_of_knowledge_dict = calc_res.get_proof_of_knowledge_dict(sel_examyear, sel_school, sel_department, sel_lvlbase_pk, student_pk_list)
                if proof_of_knowledge_dict:

                    # - get arial font
                    try:
                        filepath = s.STATICFILES_FONTS_DIR + 'arial220815.ttf'
                        ttfFile = TTFont('Arial', filepath)
                        pdfmetrics.registerFont(ttfFile)
                    except Exception as e:
                        logger.error(getattr(e, 'message', str(e)))

                    auth1_name = '---'
                    # get auth1_pk from upload_dict, check if user exists and has auth1 permission
                    if auth1_pk:
                        auth1 = acc_mod.User.objects.get_or_none(
                            pk=auth1_pk,
                            schoolbase=request.user.schoolbase,
                            activated=True,
                            is_active=True,
                            usergroups__contains='auth1'
                        )

                    buffer = io.BytesIO()
                    canvas = Canvas(buffer)

                    for student_dict in proof_of_knowledge_dict.values():
                        draw_pok(canvas, library, student_dict, auth1_pk, printdate, request)

                        canvas.showPage()

                    canvas.save()
                    pdf = buffer.getvalue()
                    # pdf_file = File(temp_file)

                    # was: buffer.close()

                    """
                    # TODO as test try to save file in
                    studsubjnote = stud_mod.Studentsubjectnote.objects.get_or_none(pk=47)
                    content_type='application/pdf'
                    file_name = 'test_try.pdf'
                    if studsubjnote and pdf_file:
                        instance = stud_mod.Noteattachment(
                            studentsubjectnote=studsubjnote,
                            contenttype=content_type,
                            filename=file_name,
                            file=pdf_file)
                        instance.save()
                        logger.debug('instance.saved: ' + str(instance))
                    # gives error: 'bytes' object has no attribute '_committed'
                    """

                    file_name = 'Ex6 Bewijs van vrijstelling' if sel_school.iseveningschool or sel_school.islexschool else 'Ex6 Bewijs van kennis'
                    if len(proof_of_knowledge_dict) == 1:
                        for pok_dict in  proof_of_knowledge_dict.values():
                            file_name += ' ' + pok_dict.get('full_name')
                            break
                    now_formatted = af.get_now_formatted_from_now_arr(upload_dict.get('now_arr'))
                    if now_formatted:
                        file_name += ' ' + now_formatted
                    file_name += '.pdf'
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = 'inline; filename="' + file_name + '"'
                    # response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

                    response.write(pdf)

                # except Exception as e:
                #     logger.error(getattr(e, 'message', str(e)))
                #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of DownloadPokView


def get_gradelist_dictlist(examyear, school, department, sel_lvlbase_pk, sel_sctbase_pk, student_pk_list):  # PR2021-11-19

    # NOTE: don't forget to filter deleted = false!! PR2021-03-15
    # grades that are not published are only visible when 'same_school'

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_gradelist_dictlist -----')
        logger.debug('student_pk_list: ' + str(student_pk_list))

    # upload_dict: {'subject_list': [2206, 2165, 2166], 'sel_layout': 'level', 'level_list': [86, 85]}

    # values of sel_layout are:"none", "level", "class", "cluster"
    # "none" or None: all students of subject on one form
    # "level:" seperate form for each leeerweg
    #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
    #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk,
                'student_pk_arr': student_pk_list}
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    grade_dictlist_sorted = []
    grade_dict = {}

    sql_list = ["SELECT studsubj.id AS studsubj_id, stud.id AS stud_id,",
                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, stud.gender, stud.idnumber,",
                "stud.birthdate, stud.birthcountry, stud.birthcity, stud.bis_exam,"
                "stud.gl_ce_avg, stud.gl_combi_avg, stud.gl_final_avg, stud.result, stud.result_status,",

                "school.name AS school_name, school.article AS school_article, school.islexschool,",
                "sb.code AS school_code, depbase.code AS depbase_code, lvlbase.code AS lvlbase_code,",
                "ey.code::TEXT AS examyear_txt, c.name AS country,",
                "dep.name AS dep_name, dep.abbrev AS dep_abbrev, dep.level_req, dep.has_profiel,",
                "lvl.name AS lvl_name, sct.name AS sct_name, sctbase.code AS sctbase_code,",
                "cl.name AS cluster_name, stud.classname,",
                "studsubj.gradelist_sesrgrade, studsubj.gradelist_pecegrade, studsubj.gradelist_finalgrade,",
                "studsubj.is_extra_nocount, studsubj.is_thumbrule, studsubj.is_extra_counts, studsubj.gradelist_use_exem,",

                "studsubj.pws_title, studsubj.pws_subjects,",

                "si.is_combi, (sjtpbase.code = 'stg')::BOOLEAN AS is_stg, (sjtpbase.code = 'wst')::BOOLEAN AS is_wst,",
                "subj.id AS subj_id, subj.name_nl AS subj_name, subjbase.code AS subjbase_code,",
                "sjtp.name AS sjtp_name, sjtpbase.sequence AS sjtpbase_sequence, sjtpbase.code AS sjtpbase_code",

                "FROM students_studentsubject AS studsubj",
                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "INNER JOIN schools_country AS c ON (c.id = ey.country_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",
                "LEFT JOIN subjects_sectorbase AS sctbase ON (sctbase.id = sct.base_id)",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "INNER JOIN subjects_subjecttype AS sjtp ON (sjtp.id = si.subjecttype_id)",
                "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = sjtp.base_id)",

                "LEFT JOIN subjects_cluster AS cl ON (cl.id = studsubj.cluster_id)",

                "WHERE ey.id = %(ey_id)s::INT AND school.id = %(sch_id)s::INT AND dep.id = %(dep_id)s::INT",
                "AND NOT stud.tobedeleted AND NOT studsubj.tobedeleted"
                ]

    if student_pk_list:
        sql_keys['student_pk_arr'] = student_pk_list
        sql_list.append("AND stud.id IN ( SELECT UNNEST( %(student_pk_arr)s::INT[]))")
    else:
        if sel_lvlbase_pk:
            sql_keys['lvlbase_pk'] = sel_lvlbase_pk
            sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")
        if sel_sctbase_pk:
            sql_keys['sctbase_pk'] = sel_sctbase_pk
            sql_list.append("AND sct.base_id = %(sctbase_pk)s::INT")

    sql_list.append("ORDER BY subj.sequence")

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        grade_rows = af.dictfetchall(cursor)

    # - add full name to rows, and array of id's of auth
    if grade_rows:
        for row in grade_rows:
            stud_id = row.get('stud_id')
            if logging_on:
                logger.debug('row: ' + str(row))

            if stud_id not in grade_dict:
                #full_name = stud_fnc.get_full_name(row.get('lastname'), row.get('firstname'), row.get('prefix'))
                last_name = row.get('lastname') or '---'
                first_name = row.get('firstname') or '---'
                prefix = row.get('prefix')
                full_name = stud_fnc.get_firstname_prefix_lastname(last_name, first_name, prefix)
                sort_name = stud_fnc.get_full_name(last_name, first_name, prefix)
                birth_date = row.get('birthdate', '')
                birth_date_formatted = af.format_DMY_from_dte(birth_date, 'nl', False)  # month_abbrev = False

                birth_country = row.get('birthcountry')
                birth_city = row.get('birthcity')

                birth_place = ''
                if birth_country:
                    if birth_city:
                        birth_place = ', '.join((birth_city, birth_country))
                    else:
                        birth_place = birth_country
                elif birth_city:
                    birth_place = birth_city

        # add dots to idnumber, if last 2 digits are not numeric: dont print letters, pprint '00' instead
                idnumber_withdots_no_char = stud_fnc.convert_idnumber_withdots_no_char(row.get('idnumber'))

        # - calc regnumber - don't get it from database table
                reg_number = stud_fnc.calc_regnumber(
                    school_code=row.get('school_code'),
                    gender=row.get('gender'),
                    examyear_str=row.get('examyear_txt'),
                    examnumber_str=row.get('examnumber'),
                    depbase_code=row.get('depbase_code'),
                    levelbase_code=row.get('lvlbase_code'),
                    bis_exam=row.get('bis_exam')
                )

                grade_dict[stud_id] = {
                    'country': row.get('country'),
                    'examyear_txt': row.get('examyear_txt'),

                    'school_name': row.get('school_name'),
                    'school_article':  row.get('school_article'),
                    'school_code':  row.get('school_code'),
                    'islexschool':  row.get('islexschool', False),

                    'dep_name':  row.get('dep_name'),
                    'depbase_code':  row.get('depbase_code'),
                    'dep_abbrev':  row.get('dep_abbrev'),

                    'lvl_name':  row.get('lvl_name'),
                    'lvlbase_code':  row.get('lvlbase_code'),
                    'level_req':  row.get('level_req', False),

                    'sct_name':  row.get('sct_name'),
                    'sctbase_code':  row.get('sctbase_code'),
                    'has_profiel':  row.get('has_profiel', False),

                    'fullname': full_name,
                    'sortname': sort_name,
                    'idnumber': idnumber_withdots_no_char,
                    'gender': row.get('gender'),
                    'birthdate': birth_date_formatted,
                    'birthplace': birth_place,
                    'regnumber':  reg_number,
                    'examnumber':  row.get('examnumber'),
                    'classname':  row.get('classname'),
                    'cluster_name':  row.get('cluster_name'),

                    'ce_avg': row.get('gl_ce_avg'),
                    'combi_avg':  row.get('gl_combi_avg'),
                    'final_avg':  row.get('gl_final_avg'),
                    'result_status':  row.get('result_status'),
                }

# - add subjecttype dict
            student_dict = grade_dict.get(stud_id)
            if student_dict:
                # put combi subjects in dict with key: 'combi', others in dict with key: subjecttype_id
                # werkstuk Havo/Vwo is combi subject, is added to list of combi subjects
                # werkstuk Vsbo TKL is not a combi subject, it is added with key 'wst', grade is shown in draw_wst
                # stage it is added with key 'stg', grade is shown in draw_stg
                is_combi = row.get('is_combi', False)
                if is_combi:
                    sjtp_sequence = 'combi'
                elif row.get('is_wst', False):
                    sjtp_sequence = 'wst'
                elif row.get('is_stg', False):
                    sjtp_sequence = 'stg'
                else:
                    sjtp_sequence = row.get('sjtpbase_sequence', 9999)

                if sjtp_sequence not in student_dict:
                    student_dict[sjtp_sequence] = {
                        'sjtp_name':  row.get('sjtp_name', '') if not is_combi else ''
                    }

                sjtp_dict = student_dict.get(sjtp_sequence)
                subj_id = row.get('subj_id')
                if subj_id not in sjtp_dict:
                    segrade = row.get('gradelist_sesrgrade').replace('.', ',') if row.get('gradelist_sesrgrade') else None
                    pecegrade = row.get('gradelist_pecegrade').replace('.', ',') if row.get('gradelist_pecegrade') else None
                    finalgrade = row.get('gradelist_finalgrade')

                    sjtp_dict[subj_id] = {
                        'sjtp_code':  row.get('sjtpbase_code'),
                        'subj_name':  row.get('subj_name'),
                        'subjbase_code':  row.get('subjbase_code'),
                        'segrade':  segrade,
                        'pecegrade': pecegrade,
                        'finalgrade': finalgrade
                    }
                subj_dict = sjtp_dict[subj_id]

                if logging_on and False:
                    logger.debug('     row: ' + str(row))
                    logger.debug('     sjtp_dict[' + str(subj_id) + ']: ' + str(sjtp_dict[subj_id]))

                """
                row: {'studsubj_id': 40093, 'stud_id': 5453, 'lastname': 'Boasman', 'firstname': 'Acemar, Hurbertho', 
                    'prefix': None, 'examnumber': '402', 'gender': 'M', 'idnumber': '2005061871', 
                    'birthdate': datetime.date(2005, 6, 18), 'birthcountry': 'Nederland', 'birthcity': 'Sint Maarten', 
                    'gl_ce_avg': None, 'gl_combi_avg': None, 'gl_final_avg': None, 'result_status': 'Geen uitslag', 
                    'school_name': 'Milton Peters College', 'school_article': 'het', 'islexschool': False, 
                    'school_code': 'SXM01', 'depbase_code': 'Vsbo', 'lvlbase_code': 'TKL', 'examyear_txt': '2022', 
                    'country': 'Sint Maarten', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 
                    'dep_abbrev': 'V.S.B.O.', 'level_req': True, 'has_profiel': False, 
                    'lvl_name': 'Theoretisch Kadergerichte Leerweg', 'sct_name': 'Techniek', 
                    'cluster_name': None, 'classname': 'VT4A', 
                    'gradelist_sesrgrade': None, 'gradelist_pecegrade': None, 'gradelist_finalgrade': None,
                     'is_extra_nocount': False, 'is_extra_counts': False, 'gradelist_use_exem': False, 
                     'pws_title': None, 'pws_subjects': None, 'is_combi': False, 'is_stg': False, 
                     'is_wst': False, 'subj_id': 168, 'subj_name': 'Nederlandse taal', 
                     'sjtp_name': 'Gemeenschappelijk deel', 'sjtpbase_sequence': 1, 'sjtpbase_code': 'gmd'}
                     
                sjtp_dict[168]: {'sjtp_code': 'gmd', 'subj_name': 'Nederlandse taal', 
                    'segrade': None, 'pecegrade': None, 'finalgrade': None}

                """

# - add  pws_title and pws_subjects to subj_dict
                pws_title = row.get('pws_title')
                if pws_title:
                    subj_dict['pws_title'] = pws_title
                pws_subjects = row.get('pws_subjects')
                if pws_subjects:
                    subj_dict['pws_subjects'] = pws_subjects

# - check if studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.gradelist_use_exem is True
                # if so: add 'has_extra_nocount' = True to student-dict
                # used to add foornote in gradelist
                if row.get('is_extra_nocount', False):
                    subj_dict['is_extra_nocount'] = True
                    student_dict['has_extra_nocount'] = True
                if row.get('is_thumbrule', False):
                    subj_dict['is_thumbrule'] = True
                    student_dict['has_thumbrule'] = True
                if row.get('is_extra_counts', False):
                    subj_dict['is_extra_counts'] = True
                    student_dict['has_extra_counts'] = True
                if row.get('gradelist_use_exem', False):
                    subj_dict['grlst_use_exem'] = True
                    student_dict['has_use_exem'] = True

# convert dict to sorted dictlist
        grade_list = list(grade_dict.values())

# sort list to sorted dictlist
        # PR2021-11-15 from https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
        #grade_dictlist_sorted = sorted(grade_list, key=lambda d: d['fullname'])
        # PR2022-06-16 Hans Vlinkervleugel gradelist sort by first name, instead of by last name. sortname added
        # was: grade_dictlist_sorted = sorted(grade_list, key=lambda d: d['fullname'])
        grade_dictlist_sorted = sorted(grade_list, key=lambda d: d['sortname'])

        if logging_on:
            if grade_dictlist_sorted:
                for row in grade_dictlist_sorted:
                    logger.debug('row: ' + str(row))

    return grade_dictlist_sorted
# - end of get_gradelist_dictlist


def get_diploma_dictlist(examyear, school, department, sel_lvlbase_pk, sel_sctbase_pk,
                           student_pk_list):  # PR2022-06-16 PR2022-06-24

    # NOTE: don't forget to filter deleted = false!! PR2021-03-15
    # PR2022-06-24 Marisela Cijntje Radulphus: cannot print diploma of passed students with reex
    # solved by: allow printing if ep01_result or ep02_result or ep01_result = passed

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_diploma_dictlist -----')
        logger.debug('student_pk_list: ' + str(student_pk_list))

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk, 'passed': c.RESULT_PASSED,
                'student_pk_arr': student_pk_list}
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    sql_list = ["SELECT stud.id AS stud_id,",
                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, stud.gender, stud.idnumber,",
                "stud.birthdate, stud.birthcountry, stud.birthcity, stud.bis_exam,",
                "stud.gl_ce_avg, stud.gl_combi_avg, stud.gl_final_avg, stud.result, stud.result_status,",
                "stud.ep01_result, stud.ep02_result, stud.result,"
                
                "school.name AS school_name, school.article AS school_article, school.islexschool,",
                "sb.code AS school_code, depbase.code AS depbase_code, lvlbase.code AS lvlbase_code,"
                "ey.code::TEXT AS examyear_txt, c.name AS country,",
                "dep.name AS dep_name, dep.abbrev AS dep_abbrev, dep.level_req, dep.has_profiel,",
                "lvl.name AS lvl_name, sct.name AS sct_name, sctbase.code AS sctbase_code,",
                "stud.classname",

                "FROM students_student AS stud",
                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "INNER JOIN schools_country AS c ON (c.id = ey.country_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",
                "LEFT JOIN subjects_sectorbase AS sctbase ON (sctbase.id = sct.base_id)",

                "WHERE ey.id = %(ey_id)s::INT AND school.id = %(sch_id)s::INT AND dep.id = %(dep_id)s::INT",
                "AND (stud.ep01_result = %(passed)s::INT OR stud.ep02_result = %(passed)s::INT OR stud.result = %(passed)s::INT)",
                "AND NOT stud.tobedeleted"
                ]

    if student_pk_list:
        sql_keys['student_pk_arr'] = student_pk_list
        sql_list.append("AND stud.id IN (SELECT UNNEST( %(student_pk_arr)s::INT[]))")
    else:
        if sel_lvlbase_pk:
            sql_keys['lvlbase_pk'] = sel_lvlbase_pk
            sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")
        if sel_sctbase_pk:
            sql_keys['sctbase_pk'] = sel_sctbase_pk
            sql_list.append("AND sct.base_id = %(sctbase_pk)s::INT")

    sql_list.append("ORDER BY stud.lastname, stud.firstname")

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    if logging_on:
        logger.debug('rows: ' + str(rows))

    diploma_list = []

    # - add full name to rows, and array of id's of auth
    if rows:
        for row in rows:
            # full_name = stud_fnc.get_full_name(row.get('lastname'), row.get('firstname'), row.get('prefix'))
            last_name = row.get('lastname') or '---'
            first_name = row.get('firstname') or '---'
            prefix = row.get('prefix')
            full_name = stud_fnc.get_firstname_prefix_lastname(last_name, first_name, prefix)

    # add dots to idnumber, if last 2 digits are not numeric: dont print letters, pprint '00' instead
            idnumber_withdots_no_char = stud_fnc.convert_idnumber_withdots_no_char(row.get('idnumber'))

    # - calc regnumber - don't get it from database table
            reg_number = stud_fnc.calc_regnumber(
                school_code=row.get('school_code'),
                gender=row.get('gender'),
                examyear_str=row.get('examyear_txt'),
                examnumber_str=row.get('examnumber'),
                depbase_code=row.get('depbase_code'),
                levelbase_code=row.get('lvlbase_code'),
                bis_exam=row.get('bis_exam')
            )

            birth_date = row.get('birthdate', '')
            birth_date_formatted = af.format_DMY_from_dte(birth_date, 'nl', False)  # month_abbrev = False

            birth_country = row.get('birthcountry')
            birth_city = row.get('birthcity')

            birth_place = ''
            if birth_country:
                if birth_city:
                    birth_place = ', '.join((birth_city, birth_country))
                else:
                    birth_place = birth_country
            elif birth_city:
                birth_place = birth_city

            diploma_list.append({
                'country': row.get('country'),
                'examyear_txt': row.get('examyear_txt'),

                'school_name': row.get('school_name'),
                'school_article': row.get('school_article'),
                'school_code': row.get('school_code'),
                'islexschool': row.get('islexschool', False),

                'dep_name': row.get('dep_name'),
                'depbase_code': row.get('depbase_code'),
                'dep_abbrev': row.get('dep_abbrev'),

                'lvl_name': row.get('lvl_name'),
                'lvlbase_code': row.get('lvlbase_code'),
                'level_req': row.get('level_req', False),

                'sct_name': row.get('sct_name'),
                'sctbase_code': row.get('sctbase_code'),
                'has_profiel': row.get('has_profiel', False),

                'fullname': full_name,
                'idnumber': idnumber_withdots_no_char,
                'gender': row.get('gender'),
                'birthdate': birth_date_formatted,

                'birth_country': birth_country,
                'birth_city': birth_city,
                'birthplace': birth_place,
                'regnumber': reg_number
            })


    if logging_on:
        for row in diploma_list:
            logger.debug('row: ' + str(row))

    return diploma_list
# - end of get_diploma_dictlist


def draw_diploma_cur(canvas, library, student_dict, auth1_name, auth2_name, printdate):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('+++++++++++++ draw_diploma_cur +++++++++++++')
        logger.debug('     student_dict: ' + str(student_dict))

    #PR 2022-06-20
    # Margins on the diploma of Curacao are:
    # PR2022-06-20 Janine Dambruck ETE: make left margin 1 mm wider, (from 18 > 19 mm)
    # and put student name evenly from 'De ondergetekenden' and 'geboren op' (distance between these 2 lines is 27 mm)
    # therefore y+pos of fullname must be 13 mm higher than line 'geboren op
    # top is base of the line 'De ondergetekenden', left = start of line 'De ondergetekenden'

    # - 72 points = 1 inch  -  1 point = 20 pixels - 1 mm = 2,8346 points
    # origin of diploma CUR = [19, 199] mm
    #   subtract y from y origin, add x to x-origin.
    #   convert mm to point when drawing

    """
    student_dict: {'country': 'Curaçao', 'examyear_txt': '2022', 'school_name': 'St. Jozef Vsbo', 'school_article': 'de', 
    'school_code': 'CUR11', 'islexschool': False, 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 
    'depbase_code': 'Vsbo', 'dep_abbrev': 'V.S.B.O.', 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 
    'lvlbase_code': 'TKL', 'level_req': True, 'sct_name': 'Techniek', 'sctbase_code': 'tech', 'has_profiel': False, 
    'fullname': 'Tanisha Jacqueline Isabel Metresili Teixeira Veloza', 'idnumber': '2005.09.06.06', 
    'gender': 'V', 'birthdate': '6 september 2005', 'birthplace': 'Willemstad, Curaçao', 'regnumber': 'CUR1122222113'}
    """

    is_lex_cur = student_dict.get('islexschool', False) and student_dict.get('country', '')[:3] == 'Cur'

    # - set the corners of the rectangle
    top = 199 * mm # was: 197 * mm
    left = 19 * mm # was:  18 * mm

    origin = [left, top]
    #draw_red_cross(canvas, origin[0], origin[1])

    tabstop = [0, 8 * mm, 22 * mm, 55 * mm, 87 * mm, 105 * mm, 115 * mm, 127 * mm]

    lineheight_5mm = 5 * mm
    lineheight_8mm = 8 * mm
    lineheight_10mm = 10 * mm

    y_pos = origin[1] - 14 * mm  # was: origin[1] - 15 * mm

    font_bold_fancy = 'Palace_Script_MT' if is_lex_cur else 'Garamond_Bold'
    font_bold = 'Garamond_Bold'
    font_normal = 'Garamond_Regular'
    size_normal = 12
    size_small = 10
    size_large = 36 if is_lex_cur else 16

# - full name
    canvas.setFont(font_bold_fancy, size_large)
    canvas.drawString(origin[0] + tabstop[1], y_pos, student_dict.get('fullname') or '---')
    y_pos -= 13 * mm  # was: lineheight_10mm

# - geboren
    canvas.setFont(font_normal, size_normal)
    canvas.drawString(origin[0], y_pos, library.get('born'))

    canvas.setFont(font_bold_fancy, size_large)
    canvas.drawString(origin[0] + tabstop[2], y_pos, student_dict.get('birthdate') or '---')
    y_pos -= lineheight_8mm

# - te
    canvas.setFont(font_normal, size_normal)
    canvas.drawString(origin[0], y_pos, library.get('born_at'))

    canvas.setFont(font_bold_fancy, size_large)
    canvas.drawString((origin[0] + tabstop[2]) , y_pos, student_dict.get('birthplace') or '---')
    y_pos -= lineheight_10mm

# - met gunstig gevolg
    canvas.setFont(font_normal, size_normal)
    key_str = 'attended_lex' if is_lex_cur else 'attended'
    text = ' '.join((library.get(key_str), student_dict.get('dep_abbrev'), library.get('conform')))
    canvas.drawString(origin[0], y_pos, text)
    y_pos -= lineheight_10mm

# - conform_sector / profiel
    canvas.setFont(font_normal, size_normal)
    key_str = 'conform_profiel' if student_dict.get('has_profiel') else 'conform_sector'
    canvas.drawString(origin[0], y_pos, library.get(key_str))

    canvas.setFont(font_bold_fancy, size_large)
    canvas.drawString(origin[0] + tabstop[2], y_pos, student_dict.get('sct_name') or '---')
    y_pos -= lineheight_8mm

# - aan
    if not is_lex_cur:
        canvas.setFont(font_normal, size_normal)
        text = library.get('at_school')
        school_article = student_dict.get('school_article')
        if school_article:
            text += ' ' + school_article
        canvas.drawString(origin[0], y_pos, text)

        canvas.setFont(font_bold_fancy, size_large)
        canvas.drawString(origin[0] + tabstop[2], y_pos, student_dict.get('school_name') or '---')
        y_pos -= lineheight_8mm

# - te
        canvas.setFont(font_normal, size_normal)
        canvas.drawString(origin[0], y_pos, library.get('at_country'))

        canvas.setFont(font_bold_fancy, size_large)
        canvas.drawString(origin[0] + tabstop[2], y_pos, student_dict.get('country') or '---')
        y_pos -= lineheight_10mm

# - welk examen werd afgenomen
    canvas.setFont(font_normal, size_normal)
    canvas.drawString(origin[0], y_pos, library.get('dpl_article01_cur'))
    y_pos -= lineheight_5mm
    canvas.drawString(origin[0], y_pos, library.get('dpl_article02_cur'))
    y_pos -= lineheight_5mm
    canvas.drawString(origin[0], y_pos, library.get('dpl_article03_cur'))
    y_pos -= lineheight_5mm
    canvas.drawString(origin[0], y_pos, library.get('dpl_article04_cur'))
    y_pos -= lineheight_10mm

# - Plaats - datum
    canvas.drawString(origin[0], y_pos, library.get('place'))
    canvas.drawString(origin[0] + tabstop[4], y_pos, library.get('date'))

    canvas.setFont(font_bold_fancy, size_large)
    canvas.drawString(origin[0] + tabstop[2], y_pos, student_dict.get('country') or '---')

    printdate_formatted = None
    if printdate:
        printdate_dte = af.get_date_from_ISO(printdate)
        printdate_formatted = af.format_DMY_from_dte(printdate_dte, 'nl', False)  # False = not month_abbrev
    if not printdate_formatted:
        printdate_formatted = '---'
    canvas.drawString(origin[0] + tabstop[5], y_pos, printdate_formatted)
    y_pos -= lineheight_10mm

# - Het Expertisecentrum voor Toetsen & Examens
    if is_lex_cur:
        canvas.setFont(font_normal, size_normal)
        canvas.drawString(origin[0], y_pos, library.get('ete'))
        y_pos -= lineheight_10mm

# - De voorzitter - De secretaris
    canvas.setFont(font_normal, size_normal)
    canvas.drawString(origin[0], y_pos, library.get('chairperson'))
    canvas.drawString(origin[0] + tabstop[4], y_pos, library.get('secretary'))
    y_pos -= (2 * lineheight_10mm) + lineheight_5mm

# - Voorzitter - Secretaris
    canvas.setFont(font_bold, size_normal)
    canvas.drawString(origin[0], y_pos, auth1_name or '---')
    canvas.drawString(origin[0] + tabstop[4], y_pos, auth2_name or '---')
    y_pos -= lineheight_10mm

# - Handtekening van de geslaagde:
    canvas.setFont(font_normal, size_normal)
    canvas.drawString(origin[0] + tabstop[3], y_pos, library.get('signature'))

# - Registratienr - Id.nr.:
    canvas.setFont(font_normal, size_small)
    y_pos = 22 * mm
    canvas.drawString(origin[0], y_pos, library.get('reg_nr'))
    canvas.drawString(origin[0] + tabstop[6], y_pos, library.get('id_nr'))

    canvas.setFont(font_bold, size_small)
    canvas.drawString(origin[0] + tabstop[2], y_pos, student_dict.get('regnumber') or '-')
    canvas.drawString(origin[0] + tabstop[7], y_pos, student_dict.get('idnumber') or '-')

    #draw_red_cross(canvas, origin[0], y_pos)
    #draw_red_cross(canvas, right, y_pos)
# - end of draw_diploma_cur


def draw_diploma_sxm(canvas, library, student_dict, auth1_name, auth2_name, printdate):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('+++++++++++++ draw_diploma_sxm +++++++++++++')
        logger.debug('     student_dict: ' + str(student_dict))

    #PR 2022-06-20
    # Position of fields taken form old AWP

    # - 72 points = 1 inch  -  1 point = 20 pixels - 1 mm = 2,8346 points
    # origin of diploma CUR = [19, 199] mm
    #   subtract y from y origin, add x to x-origin.
    #   convert mm to point when drawing

    """
    student_dict: {'country': 'Curaçao', 'examyear_txt': '2022', 'school_name': 'St. Jozef Vsbo', 'school_article': 'de', 
    'school_code': 'CUR11', 'islexschool': False, 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 
    'depbase_code': 'Vsbo', 'dep_abbrev': 'V.S.B.O.', 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 
    'lvlbase_code': 'TKL', 'level_req': True, 'sct_name': 'Techniek', 'sctbase_code': 'tech', 'has_profiel': False, 
    'fullname': 'Tanisha Jacqueline Isabel Metresili Teixeira Veloza', 'idnumber': '2005.09.06.06', 
    'gender': 'V', 'birthdate': '6 september 2005', 'birthplace': 'Willemstad, Curaçao', 'regnumber': 'CUR1122222113'}
    """

# - set the corners of the rectangle
    # - 72 points = 1 inch   -  1 point = 20 pixels  - 1 mm = 2,8346 points
    # only when prelim gradelist. rectangle is 180 mm wide and 270 mm high, 12 mm from bottom, 15 mm from left
    top = 191 * mm
    left = 23 * mm

    origin = [left, top]

    if logging_on:
        logger.debug(' ')
        logger.debug('+++++++++++++ draw_diploma_sxm +++++++++++++')
        logger.debug('     student_dict: ' + str(student_dict))

    y_pos = origin[1]

    font_bold = 'Garamond_Bold'
    size_normal = 12
    size_small = 10
    size_large = 16

# - full name
    canvas.setFont(font_bold, size_large)
    canvas.drawString(left + 14 * mm, y_pos, student_dict.get('fullname') or '---')

# - birthdate - birthplace
    y_pos -= 17 * mm
    canvas.setFont(font_bold, size_large)
    canvas.drawString(left + 28 * mm, y_pos, student_dict.get('birthdate') or '---')

    birthplace = student_dict.get('birthplace') or ''
    if len(birthplace) <= 25:
        if birthplace:
            canvas.drawString(left + 98 * mm, y_pos, birthplace)
    else:
    # put birthcountry on separate line when totl char > 25
        birth_country = student_dict.get('birth_country')
        birth_city = student_dict.get('birth_city')
        if birth_country:
            if birth_city:
                canvas.drawString(left + 98 * mm, y_pos, birth_city + ',')
                canvas.drawString(left + 98 * mm, y_pos - 8 * mm, birth_country)
            else:
                canvas.drawString(left + 98 * mm, y_pos, birth_country)
        elif birth_city:
                canvas.drawString(left + 98 * mm, y_pos, birth_city)

# - sector / profiel
    y_pos -= 22 * mm
    canvas.setFont(font_bold, size_large)
    canvas.drawString(left + 47 * mm, y_pos, student_dict.get('sct_name') or '---')

# - aan
    y_pos -= 10 * mm
    canvas.setFont(font_bold, size_large)
    canvas.drawString(left + 20 * mm, y_pos, student_dict.get('school_name') or '---')

# - te
    y_pos -= 10 * mm
    canvas.setFont(font_bold, size_large)
    canvas.drawString(left + 17 * mm, y_pos, student_dict.get('country') or '---')

# - Plaats - datum
    y_pos -= 43 * mm
    canvas.setFont(font_bold, size_large)
    canvas.drawString(left + 25 * mm, y_pos, student_dict.get('country') or '---')

    printdate_formatted = None
    if printdate:
        printdate_dte = af.get_date_from_ISO(printdate)
        printdate_formatted = af.format_DMY_from_dte(printdate_dte, 'nl', False)  # False = not month_abbrev
    if not printdate_formatted:
        printdate_formatted = '---'
    canvas.drawString(left + 112 * mm, y_pos, printdate_formatted)

# - Voorzitter - Secretaris
    y_pos -= 29 * mm
    canvas.setFont(font_bold, size_normal)
    canvas.drawCentredString(left + 44 * mm, y_pos, auth1_name or '---')
    canvas.drawCentredString(left + 129 * mm, y_pos, auth2_name or '---')

# - Registratienr - Id.nr.:
    # PR2022-06-28 mail Joan Kartokromo: Op de diploma's zal ik de regel met het registratienummer en id-nummer 1 mm lager plaatsen.
    # was:  canvas.drawString(left + 38 * mm, 31 * mm, student_dict.get('regnumber') or '-') >> changed to 30 mm
    canvas.setFont(font_bold, size_small)
    canvas.drawString(left + 38 * mm, 30 * mm, student_dict.get('regnumber') or '-')
    canvas.drawString(left + 134 * mm, 30 * mm, student_dict.get('idnumber') or '-')
# - end of draw_diploma_sxm


def draw_gradelist_sxm(canvas, library, student_dict, is_prelim, is_sxm, print_reex, auth1_pk, auth2_pk, printdate, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('+++++++++++++ draw_gradelist_sxm +++++++++++++')
        logger.debug('     auth1_pk: ' + str(auth1_pk) + '' + str(type(auth1_pk)))
        logger.debug('     student_dict: ' + str(student_dict))
        logger.debug('     is_prelim: ' + str(is_prelim))
        logger.debug('     is_sxm: ' + str(is_sxm))

    auth1_name = '---'
    if auth1_pk:
        auth1 = acc_mod.User.objects.get_or_none(
            pk=auth1_pk,
            schoolbase=request.user.schoolbase,
            activated=True,
            is_active=True,
            usergroups__contains='auth1'
        )
        if auth1:
            auth1_name = auth1.last_name

        if logging_on:
            logger.debug('     auth1: ' + str(auth1))
            logger.debug('     auth1_name: ' + str(auth1_name))
            logger.debug('     auth1.usergroups: ' + str(auth1.usergroups))

    auth2_name = '---'
    if auth2_pk:
        auth2 = acc_mod.User.objects.get_or_none(
            pk=auth2_pk,
            schoolbase=request.user.schoolbase,
            activated=True,
            is_active=True,
            usergroups__contains='auth2'
        )
        if auth2:
            auth2_name = auth2.last_name

    is_lexschool = student_dict.get('islexschool', False)

    has_profiel = student_dict.get('has_profiel', False)
    reg_number = student_dict.get('regnumber')

# - set the corners of the rectangle
    # - 72 points = 1 inch   -  1 point = 20 pixels  - 1 mm = 2,8346 points
    # only when prelim gradelist. rectangle is 180 mm wide and 270 mm high, 15 mm from bottom, 15 mm from left

    # PR2022-06-28 mail Joan Kartokromo:
    # Bij de cijferlijst van Vsbo zal ik tussen 'Theoretisch Kadergerichte Leerweg' en 'De ondergetekenden verklaren dat'
    # eenzelfde regelafstand aanhouden als tussen de naam en de regel  'De ondergetekenden verklaren dat'.
    # make top 6 mm lower than before.
    # was:  top = (261 if is_sxm else 282) * mm
    # Ik zal de onderste regel met  het registratienummer en id-nummer iets naar boven halen, zodat ze niet door het kader geprint worden.
    # was bottom = 15 * mm  > bottom = 18 * mm

    is_vsbo = False
    dep_abbrev = student_dict.get('dep_abbrev')
    if dep_abbrev:
        is_vsbo = dep_abbrev.replace('.', '').lower() == 'vsbo'

    top = (255 if is_vsbo else 261) * mm
    bottom = 18 * mm
    left = 15 * mm
    right = 195 * mm

    border = [top, right, bottom, left]

    coord = [left, top]
    if logging_on:
        logger.debug('     is_vsbo: ' + str(is_vsbo))
        logger.debug('     bottom: ' + str(bottom))
        logger.debug('     left: ' + str(left))
        logger.debug('     coord: ' + str(coord))
        logger.debug('     1 * mm: ' + str(1 * mm))

    canvas.setLineWidth(0.5)
    canvas.setStrokeColorRGB(0.5, 0.5, 0.5)

    col_tab_list = (10, 90, 110, 130, 150, 170, 180)

# - draw border around page
    if is_prelim:
        draw_page_border(canvas, border)
# - draw page header
    draw_gradelist_page_header(
        canvas=canvas,
        coord=coord,
        col_tab_list=col_tab_list,
        library=library,
        student_dict=student_dict,
        is_prelim=is_prelim,
        is_sxm=is_sxm,
        is_lexschool=is_lexschool
    )

# - draw column header
    draw_gradelist_colum_header(canvas, coord, col_tab_list, library, is_lexschool)

# - loop through subjecttypes
    # combi, stage and werkstuk have text keys, rest has integer key
    for sequence in range(0, 10):  # range(start_value, end_value, step), end_value is not included!
        # sjtp_dict = {'sjtp_code': 'combi', 'sjtp_name': '', 2168: {'subj_name': 'Culturele en Artistieke Vorming',
        sjtp_dict = student_dict.get(sequence)
        if sjtp_dict:
            draw_gradelist_sjtp_header(canvas, coord, col_tab_list, library, sjtp_dict, student_dict)
            if logging_on:
                logger.debug('     sjtp_dict: ' + str(sjtp_dict))

            for key, subj_dict in sjtp_dict.items():

                if isinstance(key, int):
                    draw_gradelist_subject_row(canvas, coord, col_tab_list, subj_dict)

    """
    sjtp_dict: {
        'sjtp_name': 'Gemeenschappelijk deel', 
        113: {'sjtp_code': 'gmd', 'subj_name': 'Nederlandse taal', 'segrade': '5.9', 'pecegrade': None, 'finalgrade': None}, 
        118: {'sjtp_code': 'gmd', 'subj_name': 'Papiamentu', 'segrade': '7.6', 'pecegrade': None, 'finalgrade': None}, 
        114: {'sjtp_code': 'gmd', 'subj_name': 'Engelse taal', 'segrade': '8.0', 'pecegrade': None, 'finalgrade': None}}
    """

# - get combi subjects
    # also check if combi contains werkstuk
    combi_dict = student_dict.get('combi')
    wst_subj_dict = {}

    if combi_dict:
        draw_gradelist_sjtp_header(canvas, coord, col_tab_list, library, combi_dict, student_dict, True)
        for key, subj_dict in combi_dict.items():
            if isinstance(key, int):
                sjtp_code = subj_dict.get('sjtp_code')
                if sjtp_code == 'wst':
                    wst_subj_dict = subj_dict
                    wst_subj_dict['is_combi'] = True

                draw_gradelist_subject_row(canvas, coord, col_tab_list, subj_dict, True)

# - get werkstuk rows
    # if wst not found in combi (in Havo Vwo), lookup with key 'wst' ( in Vsbo)
    if not wst_subj_dict:
        wst_dict = student_dict.get('wst')
        if wst_dict:
            # there can only be one werkstuk
            for key, subj_dict in wst_dict.items():
                if isinstance(key, int):
                    wst_subj_dict = subj_dict
                    wst_subj_dict['is_combi'] = False
                    break
    if wst_subj_dict:
        draw_gradelist_werkstuk_row(canvas, coord, col_tab_list, library, wst_subj_dict, has_profiel)

# - get stage rows
    stg_dict = student_dict.get('stg')
    if stg_dict:
        stg_subj_dict = {}
        # there can only be one stage
        for key, subj_dict in stg_dict.items():
            if isinstance(key, int):
                stg_subj_dict = subj_dict
                break
        if stg_subj_dict:
            draw_gradelist_stage_row(canvas, coord, col_tab_list, stg_subj_dict)

# - draw 'Gemiddelde der cijfers' row
    draw_gradelist_avg_final_row(canvas, coord, col_tab_list, library, student_dict)

# - draw 'Uitslag op grond van de resultaten:' row
    draw_gradelist_result_row(canvas, coord, col_tab_list, library, student_dict, print_reex)

# - draw page footer
    draw_gradelist_footnote_row(canvas, coord, col_tab_list, library, student_dict, is_lexschool)

# - draw page signatures
    draw_gradelist_signature_row(canvas, border, coord, col_tab_list, is_sxm, library, student_dict, auth1_name, auth2_name, printdate, reg_number)
# - end of draw_gradelist_sxm


def draw_gradelist_cur(canvas, library, student_dict, is_prelim, is_sxm, print_reex, auth1_pk, auth2_pk, printdate, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('+++++++++++++ draw_gradelist +++++++++++++')
        logger.debug('     auth1_pk: ' + str(auth1_pk) + '' + str(type(auth1_pk)))
        logger.debug('     student_dict: ' + str(student_dict))
        logger.debug('     is_prelim: ' + str(is_prelim))
        logger.debug('     is_sxm: ' + str(is_sxm))

    auth1_name = '---'
    if auth1_pk:
        auth1 = acc_mod.User.objects.get_or_none(
            pk=auth1_pk,
            schoolbase=request.user.schoolbase,
            activated=True,
            is_active=True,
            usergroups__contains='auth1'
        )
        if auth1:
            auth1_name = auth1.last_name

        if logging_on:
            logger.debug('     auth1: ' + str(auth1))
            logger.debug('     auth1_name: ' + str(auth1_name))
            logger.debug('     auth1.usergroups: ' + str(auth1.usergroups))

    auth2_name = '---'
    if auth2_pk:
        auth2 = acc_mod.User.objects.get_or_none(
            pk=auth2_pk,
            schoolbase=request.user.schoolbase,
            activated=True,
            is_active=True,
            usergroups__contains='auth2'
        )
        if auth2:
            auth2_name = auth2.last_name

    is_lexschool = student_dict.get('islexschool', False)

    has_profiel = student_dict.get('has_profiel', False)
    reg_number = student_dict.get('regnumber')

# - set the corners of the rectangle
    # - 72 points = 1 inch   -  1 point = 20 pixels  - 1 mm = 2,8346 points
    # only when prelim gradelist. rectangle is 180 mm wide and 270 mm high, 15 mm from bottom, 15 mm from left
    top = (261 if is_sxm else 282) * mm
    bottom = 15 * mm
    left = 15 * mm
    right = 195 * mm

    border = [top, right, bottom, left]

    coord = [left, top]
    if logging_on:
        logger.debug('     bottom: ' + str(bottom))
        logger.debug('     left: ' + str(left))
        logger.debug('     coord: ' + str(coord))
        logger.debug('     1 * mm: ' + str(1 * mm))

    canvas.setLineWidth(0.5)
    canvas.setStrokeColorRGB(0.5, 0.5, 0.5)

    col_tab_list = (10, 90, 110, 130, 150, 170, 180)

# - draw border around page
    if is_prelim:
        draw_page_border(canvas, border)
# - draw page header
    draw_gradelist_page_header(
        canvas=canvas,
        coord=coord,
        col_tab_list=col_tab_list,
        library=library,
        student_dict=student_dict,
        is_prelim=is_prelim,
        is_sxm=is_sxm,
        is_lexschool=is_lexschool
    )

# - draw column header
    draw_gradelist_colum_header(canvas, coord, col_tab_list, library, is_lexschool)

# - loop through subjecttypes
    # combi, stage and werkstuk have text keys, rest has integer key
    for sequence in range(0, 10):  # range(start_value, end_value, step), end_value is not included!
        # sjtp_dict = {'sjtp_code': 'combi', 'sjtp_name': '', 2168: {'subj_name': 'Culturele en Artistieke Vorming',
        sjtp_dict = student_dict.get(sequence)
        if sjtp_dict:
            draw_gradelist_sjtp_header(canvas, coord, col_tab_list, library, sjtp_dict, student_dict)
            if logging_on:
                logger.debug('     sjtp_dict: ' + str(sjtp_dict))

            for key, subj_dict in sjtp_dict.items():

                if isinstance(key, int):
                    draw_gradelist_subject_row(canvas, coord, col_tab_list, subj_dict)

    """
    sjtp_dict: {
        'sjtp_name': 'Gemeenschappelijk deel', 
        113: {'sjtp_code': 'gmd', 'subj_name': 'Nederlandse taal', 'segrade': '5.9', 'pecegrade': None, 'finalgrade': None}, 
        118: {'sjtp_code': 'gmd', 'subj_name': 'Papiamentu', 'segrade': '7.6', 'pecegrade': None, 'finalgrade': None}, 
        114: {'sjtp_code': 'gmd', 'subj_name': 'Engelse taal', 'segrade': '8.0', 'pecegrade': None, 'finalgrade': None}}
    """

# - get combi subjects
    # also check if combi contains werkstuk
    combi_dict = student_dict.get('combi')
    wst_subj_dict = {}

    if combi_dict:
        draw_gradelist_sjtp_header(canvas, coord, col_tab_list, library, combi_dict, student_dict, True)
        for key, subj_dict in combi_dict.items():
            if isinstance(key, int):
                sjtp_code = subj_dict.get('sjtp_code')
                if sjtp_code == 'wst':
                    wst_subj_dict = subj_dict
                    wst_subj_dict['is_combi'] = True

                draw_gradelist_subject_row(canvas, coord, col_tab_list, subj_dict, True)

# - get werkstuk rows
    # if wst not found in combi (in Havo Vwo), lookup with key 'wst' ( in Vsbo)
    if not wst_subj_dict:
        wst_dict = student_dict.get('wst')
        if wst_dict:
            # there can only be one werkstuk
            for key, subj_dict in wst_dict.items():
                if isinstance(key, int):
                    wst_subj_dict = subj_dict
                    wst_subj_dict['is_combi'] = False
                    break
    if wst_subj_dict:
        draw_gradelist_werkstuk_row(canvas, coord, col_tab_list, library, wst_subj_dict, has_profiel)

# - get stage rows
    stg_dict = student_dict.get('stg')
    if stg_dict:
        stg_subj_dict = {}
        # there can only be one stage
        for key, subj_dict in stg_dict.items():
            if isinstance(key, int):
                stg_subj_dict = subj_dict
                break
        if stg_subj_dict:
            draw_gradelist_stage_row(canvas, coord, col_tab_list, stg_subj_dict)

# - draw 'Gemiddelde der cijfers' row
    draw_gradelist_avg_final_row(canvas, coord, col_tab_list, library, student_dict)

# - draw 'Uitslag op grond van de resultaten:' row
    draw_gradelist_result_row(canvas, coord, col_tab_list, library, student_dict, print_reex)

# - draw page footer
    draw_gradelist_footnote_row(canvas, coord, col_tab_list, library, student_dict, is_lexschool)

# - draw page signatures
    draw_gradelist_signature_row(canvas, border, coord, col_tab_list, is_sxm, library, student_dict, auth1_name, auth2_name, printdate, reg_number)
# - end of draw_gradelist_cur


def draw_page_border(canvas, border):
    # - draw border around page

    #  border = [top, right, bottom, left]
    top, right, bottom, left = border[0], border[1], border[2], border[3]
    width = right - left  # 190 mm
    height = top - bottom  # 275 mm

    canvas.rect(left, bottom, width, height)

    #draw_red_cross(canvas, left, bottom)
# - end of draw_page_border


def draw_gradelist_page_header(canvas, coord, col_tab_list, library, student_dict, is_prelim, is_sxm, is_lexschool):
    # loop through rows of page_header
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- draw_gradelist_page_header -----')
        logger.debug('     is_sxm: ' + str(is_sxm))

    examyear_code = student_dict.get('examyear_txt', '---')
    school_name = student_dict.get('school_name', '---')
    school_article = student_dict.get('school_article', '---')
    country = student_dict.get('country', '---')
    dep_abbrev = student_dict.get('dep_abbrev', '---')
    dep_name = student_dict.get('dep_name', '---')

    full_name = student_dict.get('fullname', '---')
    birth_date = student_dict.get('birthdate') or '---'
    birth_place = student_dict.get('birthplace') or '---'
    in_the_examyear_txt = ' '.join((
        library.get('in_the_examyear', '-'),
        examyear_code,
        library.get('attended_the_exam', '-'),
        library.get('het_landsexamen', '-') if is_lexschool else library.get('het_eindexamen', '-'),
        dep_abbrev,
        library.get('conform', '-'),
    ))
    level_req = student_dict.get('level_req', False)
    key_str = 'de_sector' if level_req else 'het_profiel'
    sector_profiel_label = library.get(key_str) or '-'
    leerweg_label = library.get('leerweg') or '-'

    sector_profiel_txt = student_dict.get('sct_name') or '---'
    leerweg_txt = student_dict.get('lvl_name') or '---'

    aan_article_txt = ' '.join((library.get('at_school', '-'), school_article))

# get different 'Landsbesluit' text for sxm and cur
    eex_article_list = []
    for x in range(1, 5):
        key_str = 'eex_article0' + str(x) + ('_sxm' if is_sxm else '_cur')
        eex_article_txt = library.get(key_str)
        if logging_on:
            logger.debug('     key_str: ' + str(key_str))
            logger.debug('     eex_article_txt: ' + str(eex_article_txt))
        if eex_article_txt:
            eex_article_list.append(eex_article_txt)

    if logging_on:
        logger.debug('     eex_article_list: ' + str(eex_article_list))

# VOORLOPIGE CIJFERLIJST - print only when is_prelim, but do add line when not printing
    line_height = 10
    txt_list = [{'txt': library.get('preliminary', '---'), 'font': 'Times-Roman', 'size': 16, 'align': 'c',
         'x': coord[0] + (col_tab_list[0] + col_tab_list[5]) / 2 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 0, False, None, txt_list, not is_prelim)

    txt_list = [{'txt': dep_name, 'font': 'Times-Bold', 'size': 16, 'align': 'c',
         'x': coord[0] + (col_tab_list[0] + col_tab_list[5]) / 2 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 0, False, None, txt_list, not is_prelim)

    dont_print_leerweg = not level_req or not is_prelim
    txt_list = [{'txt': leerweg_txt, 'font': 'Times-Bold', 'size': 14, 'align': 'c',
         'x': coord[0] + (col_tab_list[0] + col_tab_list[5]) / 2 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 0, False, None, txt_list, dont_print_leerweg)

    txt_list = [{'txt': library.get('undersigned', '---'), 'size': 11, 'x': 25 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 0, False, None, txt_list)

# full_name
    line_height = 7 if is_sxm else 10
    txt_list = [{'txt': full_name, 'font': 'Times-Bold', 'size': 14, 'x': 25 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 0, False, None, txt_list)

# born_on born_at
    txt_list = [
        {'txt': library.get('born_on', '---'), 'size': 11, 'x': 25 * mm},
        {'txt': birth_date, 'font': 'Times-Bold', 'size': 11, 'x': 45 * mm},
        {'txt': library.get('born_at', '---'), 'size': 11, 'x': 80 * mm},
        {'txt': birth_place, 'font': 'Times-Bold', 'size': 11, 'x': 87 * mm} ]
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 0, False, None, txt_list)

# in_the_examyear
    line_height = 5 if is_sxm else 6
    txt_list = [{'txt': in_the_examyear_txt, 'size': 11, 'x': 25 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 0, False, None, txt_list)

# sector_profiel
    txt_list = [
        {'txt': sector_profiel_label, 'size': 11, 'x': 25 * mm},
        {'txt': sector_profiel_txt, 'font': 'Times-Bold', 'size': 11, 'x': 45 * mm} ]
    if level_req:
        txt_list.extend([
            {'txt': leerweg_label, 'size': 11, 'x': 95 * mm},
            {'txt': leerweg_txt, 'font': 'Times-Bold', 'size': 11, 'padding': 0, 'x': 115 * mm} ])
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 0, False, None, txt_list)

# aan_article
    txt_list = [
        {'txt': aan_article_txt,'size': 11, 'x': 25 * mm},
        {'txt': school_name, 'font': 'Times-Bold', 'size': 11, 'x': 45 * mm},
        {'txt': library.get('at_country', '-'), 'size': 11, 'x': 135 * mm},
        {'txt': country, 'font': 'Times-Bold', 'size': 11, 'x': 145 * mm}]
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 0, False, None, txt_list)

# De kandidaat heeft examen afgelegd in de onderstaande vakken volgens de voorschriften gegeven bij en
    # first line has height 6, rest is 5
    eex_article_lineheight = 5 if is_sxm else 6
    for eex_article_txt in eex_article_list:
        txt_list = [{'txt': eex_article_txt, 'x': 25 * mm}]
        draw_text_one_line(canvas, coord, col_tab_list, eex_article_lineheight, 0, False, None, txt_list)
        eex_article_lineheight = 4 if is_sxm else 5
# - end of draw_gradelist_page_header


def draw_gradelist_colum_header(canvas, coord, col_tab_list, library, is_lexschool):
    #     col_tab_list = (10, 90, 110, 130, 150, 170, 180)

    header_height = 13 * mm

    x = coord[0]
    y = coord[1] - 5 * mm
    coord[1] = y

# - draw horizontal lines above and below column header
    left = coord[0] + col_tab_list[0] * mm
    right = coord[0] + col_tab_list[5] * mm
    canvas.line(left, y, right, y)

    y1 = y - header_height
    canvas.line(left, y1, right, y1)


# - draw vertical lines of columns
    y_top = coord[1]
    y_top_minus = y_top - 5 * mm  # line height - 1 mm
    y_bottom = y_top - header_height

    for index in range(0, len(col_tab_list) - 1):  # range(start_value, end_value, step), end_value is not included!
        line_x = coord[0] + col_tab_list[index] * mm
        y1_mod = y_top_minus if index in (2, 4) else y_top
        canvas.line(line_x, y1_mod, line_x, y_bottom)

# - draw horizontal line  below 'CIjfers voor' and 'Eindcijfers'
    left = coord[0] + col_tab_list[1] * mm
    canvas.line(left, y_top_minus, right, y_top_minus)
    #canvas.setFont('Arial', 8, leading=None)
    #canvas.setFillColor(colors.HexColor("#000000"))

   # line_height = 4 * mm
    #y_txt1 = y - line_height - 1 * mm

    # - draw page header
    col_01_01_key = 'col_01_01_lex' if is_lexschool else 'col_01_01_eex'
    col_01_01_txt = library.get(col_01_01_key, '-')
    txt_list = [
        {'txt': library.get('col_00_00', '-'), 'padding': 4, 'x': x + col_tab_list[0] * mm, 'offset_bottom': 1.25, 'line_height': 5},
        {'txt': library.get('col_01_00', '-'), 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[3]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
        {'txt': library.get('col_03_00', '-'), 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[5]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
        ]
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, False, None, txt_list)
    txt_list = [
        {'txt': col_01_01_txt, 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[2]) / 2 * mm, 'offset_bottom': 1, 'line_height': 5},
        {'txt': library.get('col_02_01', '-'), 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
        {'txt': library.get('col_03_01', '-'), 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
        {'txt': library.get('col_04_01', '-'), 'align': 'c', 'x': x + (col_tab_list[4] + col_tab_list[5]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0}]

    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, False, None, txt_list)
    txt_list = [
        {'txt': library.get('col_01_02', '-'), 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[2]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 3},
        {'txt': library.get('col_02_02', '-'), 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
    ]
    draw_text_one_line(canvas, coord, col_tab_list, 3, 1.25, False, None, txt_list)
# - end of draw_gradelist_colum_header


def draw_gradelist_sjtp_header(canvas, coord, col_tab_list, library, sjtp_dict, student_dict, is_combi=False):
    #     col_tab_list = (10, 90, 110, 130, 150, 170, 180)

    header_height = 5 * mm

    x = coord[0]
    y = coord[1]

# - draw recangle and fill background
    left = x + col_tab_list[0] * mm
    right = coord[0] + col_tab_list[5] * mm
    width = (col_tab_list[5] - col_tab_list[0]) * mm

    y1 = y - header_height

    canvas.setFillColor(colors.HexColor("#f0f0f0"))
    canvas.rect(left, y1, width, header_height, stroke=0, fill=1) # canvas.rect(left, bottom, page_width, height)
    canvas.setFillColor(colors.HexColor("#000000"))

# also draw upper line - otherwise it will be covered by fill rectangle
    canvas.setStrokeColorRGB(.5, .5, .5)
    canvas.line(left, y, right, y)

# - draw sjtp text
    if is_combi:
        sjtp_name = library.get('combi_grade', '---')
    else:
        sjtp_name = sjtp_dict.get('sjtp_name', '---')

    combi_grade, combi_grade_in_letters = get_final_grade(student_dict, 'combi_avg')

    font_str = 'Times-Roman' if is_combi else 'Times-Bold'
    txt_list = [ {'txt': sjtp_name, 'font': font_str, 'padding': 4, 'x': x + col_tab_list[0] * mm}]

    vertical_lines = (0, 3, 4, 5) if is_combi else (0, 5)
    if is_combi:
        txt_list.extend([
            {'txt': combi_grade, 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm},
            {'txt': combi_grade_in_letters, 'align': 'c', 'x': x + (col_tab_list[4] + col_tab_list[5]) / 2 * mm}
        ])

    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_sjtp_header


def draw_gradelist_subject_row(canvas, coord, col_tab_list, subj_dict, is_combi=False):
    #     col_tab_list = (10, 90, 110, 130, 150, 170, 180)

    x = coord[0]
    """
    'PR2020-05-18 Corona:
    ' functie wordt nu ook gebruikt om vrst weer te geven achter vak als Vrijstelling wordt gebruikt in eindcijfer
    ' - bij vrijstelling "(vrst)" achter vak plaatsen, Hier geplaatst, zodat het ook op de cijferlijst terecht komt
    ' - suffix (h) en (h3) niet weergeven op Cijferlijst, wordt bereikt door IsHerTv02 en IsHerTv03 weg te laten uit parameters
    
    'PR2020-05-08 Corona bij vrijstelling "(vrst)" achter vak plaatsen, Hier geplaatst, zodat het ook op de cijferlijst terecht komt
    
    'PR2020-07-10 verzoek Esther: geen Vrst weergeven op LEX cijferlijst als het officieel geen vrst is.
        ' deze berekening wordt te ingewikkeld, dan maar gewoon uischakelen.
        'BewijsVanKennisOK = CalcBewijsVanKennis(strVakText, strSEcijfer, strCEcijfer, strEINDcijfer, _
        '                             lngCijferTypeID, crcSEweging, crcCEweging, _
        '                             booIsCombiOfKeuzeCombi, kv_IsHerVak(), kv_MaxTv())
    If Not pblAfd.IsLandsexamen Then
        strVakText = strVakText & " (Vr)"
    End If
    
    """

    subj_name = subj_dict.get('subj_name', '---')
    if is_combi:
        subj_name += " *"
    if subj_dict.get('is_extra_nocount', False) or subj_dict.get('is_thumbrule', False):
        subj_name += " +"
    if subj_dict.get('is_extra_counts', False):
        subj_name += " ++"
    if subj_dict.get('grlst_use_exem', False):
        subj_name += " (vr)"

    finalgrade, finalgrade_in_letters = get_final_grade(subj_dict, 'finalgrade')

# - draw subject_row
    txt_list = [
        {'txt': subj_name, 'font': 'Times-Roman', 'padding': 4, 'x': x + col_tab_list[0] * mm},
        {'txt': subj_dict.get('segrade', '---'), 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[2]) / 2 * mm},
        {'txt': subj_dict.get('pecegrade', '---'), 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm},
        {'txt': finalgrade, 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm},
        {'txt': finalgrade_in_letters, 'align': 'c', 'x': x + (col_tab_list[4] + col_tab_list[5]) / 2 * mm}
    ]
    logger.debug('     txt_list: ' + str(txt_list))

    vertical_lines = (0, 1, 2, 3, 4,  5)
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_subject_row


def draw_gradelist_werkstuk_row(canvas, coord, col_tab_list, library, subj_dict, has_profiel):

    x = coord[0]

# - draw subject_row
    # draw grade of werkstuk, only if it is not part of the combi grade
    is_combi = subj_dict.get('is_combi', False)
    if not is_combi:
        label_key = 'pws' if has_profiel else 'sws'
        label_txt = library.get(label_key, '---')
        finalgrade, finalgrade_in_letters = get_final_grade(subj_dict, 'finalgrade')

        txt_list = (
            {'txt': label_txt, 'font': 'Times-Roman', 'padding': 4, 'x': x + col_tab_list[0] * mm},
            {'txt': finalgrade_in_letters, 'align': 'c', 'x': x + (col_tab_list[4] + col_tab_list[5]) / 2 * mm}
        )
        vertical_lines = (0, 3, 4, 5)
        draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)

# - draw subject_row
    # when title has more than 44 char, shift title 22 mm to left
    title_key = 'lbl_title_pws' if has_profiel else 'lbl_title_sws'

    pws_title = subj_dict.get('pws_title') or ''
    if pws_title:
        pws_title = pws_title.strip()
    pws_subjects = subj_dict.get('pws_subjects') or ''
    if pws_subjects:
        pws_subjects = pws_subjects.strip()

    #logger.debug('pws_title: >' + str(pws_title) + '< ' + str(len(pws_title)) )

    if len(pws_title) > 44:
        pos_x_title = x + (col_tab_list[1] - 20) * mm
    else:
        pos_x_title = x + col_tab_list[1] * mm

    txt_list = (
        {'txt': library.get(title_key, '---'), 'font': 'Times-Roman', 'padding': 4, 'x': x + col_tab_list[0] * mm},
        {'txt': pws_title, 'font': 'Times-Italic', 'padding': 4, 'x': pos_x_title}
    )
    vertical_lines = (0, 5)
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)

    subjects_key = 'lbl_subjects_pws' if has_profiel else 'lbl_subjects_sws'
    txt_list = (
        {'txt': library.get(subjects_key, '---'), 'font': 'Times-Roman', 'padding': 4, 'x': x + col_tab_list[0] * mm},
        {'txt': pws_subjects, 'font': 'Times-Italic', 'padding': 4, 'x': x + col_tab_list[1] * mm}
    )
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_werkstuk_row


def draw_gradelist_stage_row(canvas, coord, col_tab_list, subj_dict):
    finalgrade, finalgrade_in_letters = get_final_grade(subj_dict, 'finalgrade')

    txt_list = [
        {'txt': subj_dict.get('subj_name', '---'), 'font': 'Times-Roman', 'padding': 4, 'x': coord[0] + col_tab_list[0] * mm},
        {'txt': finalgrade_in_letters, 'align': 'c', 'x': coord[0] + (col_tab_list[4] + col_tab_list[5]) / 2 * mm}
    ]
    vertical_lines = (0, 3, 4, 5)
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_stage_row


def draw_gradelist_avg_final_row(canvas, coord, col_tab_list, library, student_dict):
    # PR2021-11-16 PR2022-06-09
    # draw row 'Gemiddelde der cijfers', only when ce_avg or endgrade_avg have value PR2021-11-16
    # values are stored in student_dict, not in subj_dict

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- draw_gradelist_avg_final_row -----')
        logger.debug('     student_dict: ' + str(student_dict))

    ce_avg = student_dict.get('ce_avg')
    final_avg = student_dict.get('final_avg')
    if logging_on:
        logger.debug('ce_avg: ' + str(ce_avg))
        logger.debug('final_avg: ' + str(final_avg))

    if ce_avg or final_avg:
        txt_list = [ {'txt': library.get('avg_grade', '---'), 'font': 'Times-Roman', 'padding': 4, 'x': coord[0] + col_tab_list[0] * mm}]
        if ce_avg:
            txt_list.append({'txt': ce_avg, 'align': 'c', 'x': coord[0] + (col_tab_list[2] + col_tab_list[3]) / 2 * mm})
        if final_avg:
            txt_list.append({'txt': final_avg, 'align': 'c', 'x': coord[0] + (col_tab_list[3] + col_tab_list[4]) / 2 * mm})
        vertical_lines = [0, 3, 5]
        if ce_avg:
            vertical_lines.append(2)
        if final_avg:
            vertical_lines.append(4)

        draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_avg_final_row


def draw_gradelist_result_row(canvas, coord, col_tab_list, library, student_dict, print_reex):
    label = library.get('result', '---')
    result_status = student_dict.get('result_status', '---')
    result = student_dict.get('result', 0)
    #TODO add result (integer) to student_dict
    if print_reex and result_status == 'Afgewezen':
        result_status = 'Herexamen'

    logger.debug('print_reex: ' + str(print_reex))
    logger.debug('result: ' + str(result))
    logger.debug('result_status: ' + str(result_status))

    txt_list = [
        {'txt':label, 'font': 'Times-Bold', 'padding': 4, 'x': coord[0] + col_tab_list[0] * mm},
        {'txt': result_status, 'font': 'Times-Bold', 'padding': 3, 'align': 'r', 'x': coord[0] + col_tab_list[5] * mm}
    ]
    vertical_lines = (0, 5)
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_gradelist_stage_row


def draw_gradelist_footnote_row(canvas, coord, col_tab_list, library, student_dict, is_lexschool):
    """
    'PR2020-05-08 Corona: voetnoot toegevoegd, overleg Esther, Rubya Nancy 2020-005-08
    'PR2020-07-10 verzoek Esther: geen Vrst weergeven op LEX cijferlijst als het officieel geen vrst is.
    """
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug((' ----- draw_gradelist_footnote_row -----'))
        #logger.debug(('student_dict: ' + str(student_dict)))
        logger.debug('has_extra_nocount: ' + str(student_dict.get('has_extra_nocount', False)))
        logger.debug('has_extra_counts: ' + str(student_dict.get('has_extra_counts', False)))

    # check if student has subjects with is_extra_nocount or has_thumbruleor is_extra_counts or gradelist_use_exem
    footnote = ''
    if student_dict.get('has_extra_nocount', False) or student_dict.get('has_thumbrule', False):
        footnote += library.get('footnote_extra_nocount') or ''
    if student_dict.get('has_extra_counts', False):
        footnote += library.get('footnote_extra_counts') or ''
    if student_dict.get('has_use_exem', False) and not is_lexschool:
        footnote += library.get('footnote_exem') or ''

    if logging_on:
        logger.debug('footnote: ' + str(footnote))

    if footnote:
        txt_list = [
            {'txt':footnote, 'font': 'Times-Roman',  'size': 8, 'padding': 4, 'x': coord[0] + col_tab_list[0] * mm}
        ]
        if logging_on:
            logger.debug('txt_list: ' + str(txt_list))
        vertical_lines = ()
        draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, False, vertical_lines, txt_list)
# - end of draw_gradelist_footnote_row


def draw_gradelist_signature_row(canvas, border, coord, col_tab_list, is_sxm, library, student_dict, auth1_name, auth2_name, printdate, reg_number):
    """
    'PR2020-05-24 na email correspondentie Esther: 'De voorzitter / directeur' gewijzigd in 'De voorzitter'
    """
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug((' ----- draw_gradelist_signature_row -----'))
        #logger.debug(('student_dict: ' + str(student_dict)))
        logger.debug('auth1_name: ' + str(auth1_name))
        logger.debug('auth2_name: ' + str(auth2_name))
        logger.debug('printdate: ' + str(printdate))

    #border = [top, right, bottom, left]
    bottom = border[2]

    # when cur: bottom = 15 mm, when sxm: bottom = 18 mm

# - place, date
    # printdate is retrieved from upload_dict and saved in school_settings
    printdate_formatted = None
    if printdate:
        printdate_dte = af.get_date_from_ISO(printdate)
        printdate_formatted = af.format_DMY_from_dte(printdate_dte, 'nl', False)  # False = not month_abbrev
    if not printdate_formatted:
        printdate_formatted = '---'

    x = coord[0]

    txt_list = [
        {'txt': library.get('place', '---'), 'font': 'Times-Roman', 'size': 10, 'padding': 4, 'x': x + col_tab_list[0] * mm},
        {'txt': student_dict.get('country', '---'), 'font': 'Times-Bold', 'size': 10, 'padding': 18, 'x': x + col_tab_list[0] * mm},
        {'txt': library.get('date', '---'), 'font': 'Times-Roman', 'size': 10, 'padding': 4, 'x': x + col_tab_list[1] * mm},
        {'txt': printdate_formatted, 'font': 'Times-Bold', 'size': 10, 'padding': 18, 'x': x + col_tab_list[1] * mm},
    ]
    line_height = 7
    draw_text_one_line(canvas, coord, col_tab_list, line_height, 1.25, False, None, txt_list)

# - draw name of chairperson and secretary
    # - place the text of the name of the chairperson / secretary 40 mm under  the line chairperson / secretary
    # but no lower than maximum

    txt_list = [
        {'txt': auth1_name, 'font': 'Times-Bold', 'size': 10, 'padding': 4,
         'x': x + col_tab_list[0] * mm}
    ]

    # pok has no auth2_name, skip when auth2_name has no value
    if auth2_name:
        txt_list.append(
            {'txt': auth2_name, 'font': 'Times-Bold', 'size': 10, 'padding': 4,
            'x': x + col_tab_list[1] * mm}
        )

    line_height = 30
    pos_y_auth = coord[1] - line_height * mm
    # let signature never go lower than just above regnr line

    # when cur: bottom = 15 mm, when sxm: bottom = 18 mm
    min_pos_y_auth = 28 * mm if is_sxm else 25 * mm
    if pos_y_auth < min_pos_y_auth:
        pos_y_auth = min_pos_y_auth
    coord_auth = [coord[0], pos_y_auth]
    draw_text_one_line(canvas, coord_auth, col_tab_list, 0, 1.25, False, None, txt_list)

# - draw label 'chairperson' and 'secretary' under the name
    pos_y_auth_label = pos_y_auth - 4 * mm
    coord_auth_label = [coord[0], pos_y_auth_label]
    txt_list = [
        {'txt': library.get('chairperson', '---'), 'font': 'Times-Roman', 'size': 10, 'padding': 4,
         'x': x + col_tab_list[0] * mm},
    ]
    # pok has no auth2_name, skip when auth2_name has no value
    if auth2_name:
        txt_list.append(
            {'txt': library.get('secretary', '---'), 'font': 'Times-Roman', 'size': 10, 'padding': 4,
             'x': x + col_tab_list[1] * mm}
        )
    draw_text_one_line(canvas, coord_auth_label, col_tab_list, 0, 1.25, False, None, txt_list)

    if logging_on:
        logger.debug('coord: ' + str(coord))
        logger.debug('coord_auth: ' + str(coord_auth))
        logger.debug('bottom: ' + str(bottom))

# - regnumber and idnumber are just above lower line of rectangle
    id_number = student_dict.get('idnumber') or '---'
    txt_list = [
        {'txt': reg_number, 'font': 'Times-Roman', 'size': 8, 'padding': 4,
         'x': x + col_tab_list[0] * mm},
        {'txt': id_number, 'font': 'Times-Roman', 'size': 8, 'padding': 4,
         'x': x + col_tab_list[1] * mm},
    ]
    coord_regnr = [coord[0], bottom]

    draw_text_one_line(canvas, coord_regnr, col_tab_list, 0, 1.25, False, None, txt_list)
# - end of draw_gradelist_signature_row


def draw_text_one_line(canvas, coord, col_tab_list, line_height, offset_bottom,
                       draw_line_below, vertical_lines, text_list, dont_print=False):
    # function creates one line with text for each item in list PR2021-11-16
    # x-coord[0] is not in use
    # coord[1] decreses with line_height

    # still call this function when dont_print, to keep track of y_pos

    y_pos_line = coord[1] - line_height * mm
    y_pos_txt = y_pos_line + offset_bottom * mm

    if not dont_print:
        for text_dict in text_list:
            #  text_dict = {'txt': '-', 'font', 'Times-Roman', 'size', 10 'color', '#000000' 'align', 'l' 'padding': 4, 'x': x 4 * mm,},
    # - get info from text_dict
            text = text_dict.get('txt')
            if text:
                font_type = text_dict.get('font', 'Times-Roman')
                font_size = text_dict.get('size', 10)
                font_hexcolor = text_dict.get('color', '#000000')
                text_align = text_dict.get('align', 'l')
                padding = text_dict.get('padding', 0) * mm

                x_pos = text_dict.get('x', 0)

                # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
                canvas.setFont(font_type, font_size, leading=None)
                canvas.setFillColor(colors.HexColor(font_hexcolor))
                if text_align == 'c':
                    x_pos_txt = x_pos
                    canvas.drawCentredString(x_pos_txt, y_pos_txt, text)
                elif text_align == 'r':
                    x_pos_txt = x_pos - padding
                    canvas.drawRightString(x_pos_txt, y_pos_txt, text)
                else:
                    x_pos_txt = x_pos + padding
                    canvas.drawString(x_pos_txt, y_pos_txt, text)

                #draw_red_cross(canvas, x_pos_txt, y_pos_txt)

        # - draw line at bottom of row
        if draw_line_below:
            canvas.setStrokeColorRGB(.5, .5, .5)
            left = coord[0] + col_tab_list[0] * mm
            right = coord[0] + col_tab_list[5] * mm
            canvas.line(left, y_pos_line, right, y_pos_line)

    # - draw vertical lines of columns
        if vertical_lines:
            canvas.setStrokeColorRGB(.5, .5, .5)
            for index in vertical_lines:
                y_top = coord[1]
                y_bottom = y_pos_line

                line_x = coord[0] + col_tab_list[index] * mm
                canvas.line(line_x, y_top, line_x, y_bottom)

    coord[1] = y_pos_line
# - end of draw_text_one_line


# def draw_red_cross(canvas, x, y):
    # draw red cross, for outlining while designing

    #canvas.setStrokeColorRGB(1, 0, 0)
    #canvas.line(x, y + 5 * mm, x, y - 5 * mm)
    #canvas.line(x - 5 * mm, y , x + 5 * mm, y )


def get_final_grade(subj_dict, key_str):
    # PR2021-11-19
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  key_str  -----')
        logger.debug('subj_dict: ' + str(subj_dict))
        logger.debug('key_str: ' + str(key_str))

    finalgrade, finalgrade_in_letters = None, None
    final_grade = subj_dict.get(key_str)

    if logging_on:
        logger.debug('final_grade: ' + str(final_grade))

    if final_grade:
        finalgrade = final_grade.lower()
        finalgrade_in_letters = c.GRADE_IN_LETTERS.get(final_grade)

    if not finalgrade:
        finalgrade = '---'
    if not finalgrade_in_letters:
        finalgrade_in_letters = '---'

    if logging_on:
        logger.debug('finalgrade: ' + str(finalgrade))
        logger.debug('finalgrade_in_letters: ' + str(finalgrade_in_letters))
    return finalgrade, finalgrade_in_letters
# - end of get_final_grade

#############################################

def draw_short_gradelist(canvas, library, student_dict, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_gradelist -----')
        logger.debug('student_dict: ' + str(student_dict))

    is_lexschool = student_dict.get('islexschool', False)
    has_profiel = student_dict.get('has_profiel', False)

    # - set the corners of the rectangle
    # - 72 points = 1 inch   -  1 point = 20 pixels  - 1 mm = 2,8346 points
    # only when prelim gradelist. rectangle is 180 mm wide and 270 mm high, 12 mm from bottom, 15 mm from left
    top, right, bottom, left = 282 * mm, 195 * mm, 12 * mm, 15 * mm
    # width = right - left  # 190 mm
    # height = top - bottom  # 275 mm
    border = [top, right, bottom, left]
    coord = [left, top]

    canvas.setLineWidth(0.5)
    canvas.setStrokeColorRGB(0.5, 0.5, 0.5)
    col_tab_list = (10, 25, 40, 55, 70)

# - draw border around page
    draw_page_border(canvas, border)

# - draw page header
    draw_shortlist_page_header(canvas, coord, col_tab_list, library, student_dict)

# - draw column header
    draw_short_list_colum_header(canvas, coord, col_tab_list, library, is_lexschool)

# - loop through subjecttypes

    # combi, stage and werkstuk have text keys, rest has integer key
    for sequence in range(0, 10):  # range(start_value, end_value, step), end_value is not included!
        # sjtp_dict = {'sjtp_code': 'combi', 'sjtp_name': '', 2168: {'subj_name': 'Culturele en Artistieke Vorming',
        sjtp_dict = student_dict.get(sequence)
        if sjtp_dict:
            for key, subj_dict in sjtp_dict.items():
                if isinstance(key, int):
                    draw_shortlist_subject_row(canvas, coord, col_tab_list, subj_dict)

# - get combi subjects
    # also check if combi contains werkstuk
    combi_dict = student_dict.get('combi')
    wst_subj_dict = {}

    if combi_dict:
        #draw_shortlist_combi_header(canvas, coord, col_tab_list, library, combi_dict, student_dict, True)

        for key, subj_dict in combi_dict.items():
            if isinstance(key, int):
                sjtp_code = subj_dict.get('sjtp_code')
                if sjtp_code == 'wst':
                    wst_subj_dict = subj_dict
                    wst_subj_dict['is_combi'] = True

                #draw_gradelist_subject_row(canvas, coord, col_tab_list, subj_dict, True)

# - get werkstuk rows
    # if wst not found in combi (in Havo Vwo), lookup with key 'wst' ( in Vsbo)
    if not wst_subj_dict:
        wst_dict = student_dict.get('wst')
        if wst_dict:
            # there can only be one werkstuk
            for key, subj_dict in wst_dict.items():
                if isinstance(key, int):
                    wst_subj_dict = subj_dict
                    wst_subj_dict['is_combi'] = False
                    break
    #if wst_subj_dict:
    #    draw_gradelist_werkstuk_row(canvas, coord, col_tab_list, library, wst_subj_dict, has_profiel)

# - get stage rows
    stg_dict = student_dict.get('stg')
    if stg_dict:
        stg_subj_dict = {}
        # there can only be one stage
        for key, subj_dict in stg_dict.items():
            if isinstance(key, int):
                stg_subj_dict = subj_dict
                break
        #if stg_subj_dict:
        #    draw_gradelist_stage_row(canvas, coord, col_tab_list, stg_subj_dict)

# - draw 'Gemiddelde der cijfers' row
    #draw_gradelist_avg_final_row(canvas, coord, col_tab_list, library, student_dict)

# - draw 'Uitslag op grond van de resultaten:' row
    print_reex = False
    #draw_gradelist_result_row(canvas, coord, col_tab_list, library, student_dict, print_reex)
# - end of draw_short_gradelist


def draw_shortlist_page_header(canvas, coord, col_tab_list, library, student_dict):
    # loop through rows of page_header

    x = coord[0]

    #school_name = student_dict.get('school_name', '---')
    #txt_list = [{'txt': school_name, 'font': 'Times-Bold', 'size': 11, 'x': x}]
    #draw_shortlist_one_line(canvas, coord, col_tab_list, 6, 0, False, None, txt_list)

    # draw_shortlist_one_line(canvas, coord, col_tab_list, line_height, offset_bottom, draw_line_below, vertical_lines, text_list, dont_print=False)
    full_name = student_dict.get('fullname', '---')
    txt_list = [{'txt': full_name, 'font': 'Times-Bold', 'size': 11, 'x': x}]
    draw_shortlist_one_line(canvas, coord, col_tab_list, 6, 0, False, None, txt_list)

    level_req = student_dict.get('level_req', False)
    depbase_code = student_dict.get('depbase_code', '---')
    sctbase_code = student_dict.get('sctbase_code') or '---'
    txt_list = [ {'txt': depbase_code, 'size': 11, 'x': x}]
    if level_req:
        lvlbase_code = student_dict.get('lvlbase_code') or '---'
        txt_list.append({'txt': lvlbase_code, 'size': 11, 'x': x + 15 * mm})
        txt_list.append({'txt': sctbase_code, 'size': 11, 'x': x + 30 * mm})
    else:
        txt_list.append({'txt': sctbase_code, 'size': 11, 'x': x + 15 * mm})
    draw_shortlist_one_line(canvas, coord, col_tab_list, 6, 0, False, None, txt_list)
# - end of draw_gradelist_page_header


def draw_short_list_colum_header(canvas, coord, col_tab_list, library, is_lexschool):
    #     col_tab_list = (10, 90, 110, 130, 150, 170, 180)

    header_height = 13 * mm
    x = coord[0]
    y = coord[1] - 5 * mm
    coord[1] = y

# - draw horizontal lines above and below column header
    left = coord[0] + col_tab_list[0] * mm
    right = coord[0] + col_tab_list[4] * mm
    canvas.line(left, y, right, y)

    y1 = y - header_height
    canvas.line(left, y1, right, y1)

# - draw vertical lines of columns
    y_top = coord[1]
    y_top_minus = y_top - 5 * mm  # line height - 1 mm
    y_bottom = y_top - header_height
    """
    for index in range(0, len(col_tab_list) - 1):  # range(start_value, end_value, step), end_value is not included!
        line_x = coord[0] + col_tab_list[index] * mm
        y1_mod = y_top_minus if index in (2, 4) else y_top
        canvas.line(line_x, y1_mod, line_x, y_bottom)
    """

    # - draw subject_row
    txt_list = [
        {'txt': str(_('Subject')), 'font': 'Times-Roman', 'padding': 4, 'x': x + col_tab_list[0] * mm},
        {'txt': 's', 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[2]) / 2 * mm},
        {'txt': 'c', 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm},
        {'txt': 'e', 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm}
    ]
    vertical_lines = (0, 1, 2)
    draw_shortlist_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)




# - end of draw_short_list_colum_header


def draw_shortlist_combi_header(canvas, coord, col_tab_list, library, sjtp_dict, student_dict, is_combi=False):
    #     col_tab_list = (10, 90, 110, 130, 150, 170, 180)

    header_height = 5 * mm

    x = coord[0]
    y = coord[1]

# - draw recangle and fill background
    left = x + col_tab_list[0] * mm
    right = coord[0] + col_tab_list[4] * mm
    width = (col_tab_list[4] - col_tab_list[0]) * mm

    y1 = y - header_height

    canvas.setFillColor(colors.HexColor("#f0f0f0"))
    canvas.rect(left, y1, width, header_height, stroke=0, fill=1) # canvas.rect(left, bottom, page_width, height)
    canvas.setFillColor(colors.HexColor("#000000"))

# also draw upper line - otherwise it will be covered by fill rectangle
    canvas.setStrokeColorRGB(.5, .5, .5)
    canvas.line(left, y, right, y)

# - draw sjtp text
    if is_combi:
        sjtp_name = library.get('combi_grade', '---')
    else:
        sjtp_name = sjtp_dict.get('sjtp_name', '---')

    combi_grade, combi_grade_in_letters = get_final_grade(student_dict, 'combi_avg')

    font_str = 'Times-Roman' if is_combi else 'Times-Bold'
    txt_list = [ {'txt': sjtp_name, 'font': font_str, 'padding': 4, 'x': x + col_tab_list[0] * mm}]

    vertical_lines = (0, 3, 4, 5) if is_combi else (0, 5)
    if is_combi:
        txt_list.extend([
            {'txt': combi_grade, 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm}
        ])

    draw_shortlist_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_shortlist_combi_header


def draw_shortlist_subject_row(canvas, coord, col_tab_list, subj_dict, is_combi=False):
    #     col_tab_list = (10, 90, 110, 130, 150, 170, 180)

    x = coord[0]

    subj_name = subj_dict.get('subjbase_code', '---')
    if is_combi:
        subj_name += " *"
    if subj_dict.get('is_extra_nocount', False):
        subj_name += " +"
    if subj_dict.get('is_extra_counts', False):
        subj_name += " ++"
    if subj_dict.get('grlst_use_exem', False):
        subj_name += " (vr)"

    finalgrade, finalgrade_in_letters = get_final_grade(subj_dict, 'finalgrade')

# - draw subject_row
    txt_list = [
        {'txt': subj_name, 'font': 'Times-Roman', 'padding': 4, 'x': x + col_tab_list[0] * mm},
        {'txt': subj_dict.get('segrade', '---'), 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[2]) / 2 * mm},
        {'txt': subj_dict.get('pecegrade', '---'), 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm},
        {'txt': finalgrade, 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm}
    ]
    vertical_lines = (0, 1, 2)
    draw_shortlist_one_line(canvas, coord, col_tab_list, 5, 1.25, True, vertical_lines, txt_list)
# - end of draw_shortlist_subject_row


def draw_shortlist_one_line(canvas, coord, col_tab_list, line_height, offset_bottom,
                       draw_line_below, vertical_lines, text_list, dont_print=False):
    # function creates one line with text for each item in list PR2021-11-16
    # x-coord[0] is not in use
    # coord[1] decreses with line_height

    # still call this function when dont_print, to keep track of y_pos

    y_pos_line = coord[1] - line_height * mm
    y_pos_txt = y_pos_line + offset_bottom * mm

    if not dont_print:
        for text_dict in text_list:
    # - get info from text_dict
            text = text_dict.get('txt')
            if text:
                font_type = text_dict.get('font', 'Times-Roman')
                font_size = text_dict.get('size', 10)
                font_hexcolor = text_dict.get('color', '#000000')
                text_align = text_dict.get('align', 'l')

                x_pos = text_dict.get('x', 0)

                # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
                canvas.setFont(font_type, font_size, leading=None)
                canvas.setFillColor(colors.HexColor(font_hexcolor))
                if text_align == 'c':
                    x_pos_txt = x_pos
                    canvas.drawCentredString(x_pos_txt, y_pos_txt, text)
                elif text_align == 'r':
                    x_pos_txt = x_pos - text_dict.get('padding', 0) * mm
                    canvas.drawRightString(x_pos_txt, y_pos_txt, text)
                else:
                    x_pos_txt = x_pos + text_dict.get('padding', 0) * mm
                    canvas.drawString(x_pos_txt, y_pos_txt, text)

                #draw_red_cross(canvas, x_pos_txt, y_pos_txt)

        # - draw line at bottom of row
        if draw_line_below:
            canvas.setStrokeColorRGB(.5, .5, .5)
            left = coord[0] + col_tab_list[0] * mm
            right = coord[0] + col_tab_list[4] * mm
            canvas.line(left, y_pos_line, right, y_pos_line)

    # - draw vertical lines of columns
        if vertical_lines:
            canvas.setStrokeColorRGB(.5, .5, .5)
            for index in vertical_lines:
                y_top = coord[1]
                y_bottom = y_pos_line

                line_x = coord[0] + col_tab_list[index] * mm
                canvas.line(line_x, y_top, line_x, y_bottom)

    coord[1] = y_pos_line
# - end of draw_shortlist_one_line

#############################################

def draw_pok(canvas, library, student_dict, auth1_pk, printdate, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('+++++++++++++ draw_pok +++++++++++++')
        logger.debug('     auth1_pk: ' + str(auth1_pk) + '' + str(type(auth1_pk)))
        logger.debug('     student_dict: ' + str(student_dict))

    auth1_name = '---'
    if auth1_pk:
        auth1 = acc_mod.User.objects.get_or_none(
            pk=auth1_pk,
            schoolbase=request.user.schoolbase,
            activated=True,
            is_active=True,
            usergroups__contains='auth1'
        )
        if auth1:
            auth1_name = auth1.last_name

        if logging_on:
            logger.debug('     auth1: ' + str(auth1))
            logger.debug('     auth1_name: ' + str(auth1_name))
            logger.debug('     auth1.usergroups: ' + str(auth1.usergroups))

    is_eveningstudent = student_dict.get('iseveningstudent') or False
    is_lexstudent = student_dict.get('islexstudent') or False
    reg_number = student_dict.get('regnumber')
    is_sxm = student_dict.get('country_abbrev') == 'Sxm'

# - set the corners of the rectangle
    # - 72 points = 1 inch   -  1 point = 20 pixels  - 1 mm = 2,8346 points
    # only when prelim gradelist. rectangle is 180 mm wide and 270 mm high, 15 mm from bottom, 15 mm from left
    top = 282 * mm
    bottom = 15 * mm
    left = 15 * mm
    right = 195 * mm

    border = [top, right, bottom, left]

    coord = [left, top]
    if logging_on:
        logger.debug('     bottom: ' + str(bottom))
        logger.debug('     left: ' + str(left))
        logger.debug('     coord: ' + str(coord))
        logger.debug('     1 * mm: ' + str(1 * mm))

    canvas.setLineWidth(0.5)
    canvas.setStrokeColorRGB(0.5, 0.5, 0.5)

    col_tab_list = (4, 84, 104, 124, 144, 164, 174)

# - draw page header
    draw_pok_page_header(
        canvas=canvas,
        border=border,
        coord=coord,
        library=library,
        student_dict=student_dict,
        is_sxm=is_sxm,
        is_eveningstudent=is_eveningstudent,
        is_lexstudent=is_lexstudent
    )

# - draw column header
    draw_gradelist_colum_header(canvas, coord, col_tab_list, library, is_lexstudent)

# - loop through subjects
    # subjects_dict = [{'subj_name': 'Algemene sociale wetenschappen', 'sesr_grade': '6.3', 'pece_grade': None, 'final_grade': '6'}
    subject_list = student_dict.get('subjects')
    for subj_dict in subject_list:
        draw_gradelist_subject_row(canvas, coord, col_tab_list, subj_dict)

# - draw page footer
    draw_gradelist_footnote_row(canvas, coord, col_tab_list, library, student_dict, is_lexstudent)

# - draw page signatures
    draw_gradelist_signature_row(canvas, border, coord, col_tab_list, is_sxm, library, student_dict, auth1_name, None, printdate, reg_number)
# - end of draw_pok


def draw_pok_page_header(canvas, border, coord, library, student_dict, is_sxm, is_eveningstudent, is_lexstudent):
    # loop through rows of page_header
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- draw_pok_page_header -----')
        logger.debug('     student_dict: ' + str(student_dict))
        logger.debug('     library: ' + str(library))

    line_height = 7 * mm
    padding_left = 4 * mm

    x = coord[0] + padding_left
    y = coord[1] - 8 * mm

# - draw 'Ex.6' in upper right cormner
    grd_exfiles.draw_ex_box(canvas, border, library)

# draw MinOnd
    canvas.setFont('Times-Bold', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.drawString(x, y, library.get('minond', '-'))
    y -= 10 * mm

# draw Pok / Pex
    key_str = 'ex6_pex' if is_eveningstudent or is_lexstudent else 'ex6_pok'
    canvas.drawString(x, y, library.get(key_str, '-'))
    y -= line_height

# draw 'Landsbesluit', different text for sxm and cur  and eex and lex ex6_article_sxm_lex
    canvas.setFont('Times-Roman', 11, leading=None)
    key_str = '_'.join(('ex6', 'article', ('sxm' if is_sxm else 'cur'), ('lex' if is_lexstudent else 'eex')))
    eex_article_txt = library.get(key_str, '-')
    canvas.drawString(x, y, eex_article_txt)
    y -= 10 * mm

# draw 'De voorzitter van de examencommissie van' + school name
    txt = ' '.join((
        library.get('ex6_voorzitter', '-'),
        student_dict.get('school_article', ''),
    ))
    txt_width = pdfmetrics.stringWidth(txt + '  ', 'Times-Roman', 11)
    canvas.drawString(x, y, txt)

    canvas.setFont('Arial', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000080"))
    canvas.drawString(x + txt_width, y, student_dict.get('school_name', '---'))
    y -= line_height

# draw country, examyear
    te_label = library.get('ex6_te', '')
    te_label_width = pdfmetrics.stringWidth(te_label + '  ', 'Times-Roman', 11)
    country_name = student_dict.get('country', '---')
    country_name_width = pdfmetrics.stringWidth(country_name, 'Arial', 11)
    examyear_label = ',  ' + library.get('ex6_examyear', '-')
    examyear_label_width = pdfmetrics.stringWidth(examyear_label + '  ', 'Times-Roman', 11)
    examyear_txt = student_dict.get('examyear_txt', '---')
    examyear_txt_width = pdfmetrics.stringWidth(examyear_txt + '  ', 'Arial', 11)
    belast_label = library.get('ex6_belast', '-')

    canvas.setFont('Times-Roman', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))

    canvas.drawString(x, y, te_label)
    canvas.drawString(x + te_label_width + country_name_width, y, examyear_label)
    canvas.drawString(x + te_label_width + country_name_width+ examyear_label_width + examyear_txt_width, y, belast_label)

    canvas.setFont('Arial', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000080"))
    canvas.drawString(x + te_label_width, y, country_name)
    canvas.drawString(x + te_label_width + country_name_width + examyear_label_width, y, student_dict.get('examyear_txt', '---'))
    y -= line_height

# draw het_eindexamen, department, aan_deze_school, verklaart_dat
    key_str = 'ex6_landsexamen' if is_lexstudent else 'ex6_eindexamen'
    eindexamen = library.get(key_str, '-')
    dep_name = student_dict.get('dep_name', '---')

    key_str = 'ex6_instelling' if is_lexstudent else 'ex6_school'
    school_instelling = library.get(key_str, '-')
    txt_str = ''.join((
        eindexamen, ' ',
        dep_name, ' ',
        library.get('ex6_aan_deze', '-'),
        school_instelling,
        library.get('ex6_verklaart_dat', '-')
    ))

    canvas.setFont('Times-Roman', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.drawString(x, y, txt_str)
    y -= 10 * mm

# draw fullname
    canvas.setFont('Arial', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000080"))
    canvas.drawString(x + 5 * mm, y, student_dict.get('full_name', '---'))
    y -= 10 * mm

# draw geboren_op, geboren_te
    txt_str = ' '.join((
        library.get('ex6_geboren_op', '-'),
        student_dict.get('birth_date_formatted') or '---',
        te_label,
        student_dict.get('birth_place') or '---'
    ))
    canvas.setFont('Times-Roman', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.drawString(x, y, txt_str)

    y -= line_height

# draw ex6_bovengenoemde  instelling
    key_str = 'ex6_het_landsexamen' if is_lexstudent else 'ex6_het_eindexamen'
    aan_bovengenoemde_school = ''.join((
        library.get('ex6_bovengenoemde', '-'),
        school_instelling,
        library.get(key_str, '-')))
    canvas.setFont('Times-Roman', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.drawString(x, y, aan_bovengenoemde_school)
    y -= line_height

# draw dep_name
    canvas.setFont('Arial', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000080"))
    canvas.drawString(x + 5 * mm, y, dep_name)
    y -= line_height

# draw level, if exists
    lvl_name = student_dict.get('lvl_name', '---')
    if lvl_name:
        canvas.drawString(x + 5 * mm, y, lvl_name)
        y -= line_height

# draw heeft_afgelegd
    gender = student_dict.get('gender')
    hij_zij_str = None
    if gender:
        if gender.lower() == 'm':
            hij_zij_str = library.get('ex6_hij')
        elif gender.lower() == 'v':
            hij_zij_str = library.get('ex6_zij')
            gender_key = 'ex6_zij'
    if not hij_zij_str:
        hij_zij_str = '/'.join((library.get('ex6_hij', '-'),library.get('ex6_zij', '-')))

    txt_str =' '.join((
            library.get('ex6_afgelegd', '-'),
            hij_zij_str,
            library.get('ex6_volgend_jaar', '-'),
            school_instelling,
            library.get('ex6_geen_examen', '-')
    ))
    canvas.setFont('Times-Roman', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.drawString(x, y, txt_str)
    y -= line_height

# draw hieronder_vermelde_vakken
    canvas.drawString(x, y, library.get('ex6_hieronder_vermelde', '-'))
    y -= line_height

    coord[1] = y

# - end of draw_pok_page_header


def draw_pok_colum_headerNIU(canvas, coord, col_tab_list, library, is_lexschool):
    #     col_tab_list = (10, 90, 110, 130, 150, 170, 180)

    header_height = 15 * mm

    x = coord[0]
    y = coord[1] - 5 * mm
    coord[1] = y

# - draw horizontal lines above and below column header
    left = coord[0] + col_tab_list[0] * mm
    right = coord[0] + col_tab_list[4] * mm
    canvas.line(left, y, right, y)

    y1 = y - header_height
    canvas.line(left, y1, right, y1)


# - draw vertical lines of columns
    y_top = coord[1]
    y_top_minus = y_top - 5 * mm  # line height - 1 mm
    y_bottom = y_top - header_height

    for index in range(0, len(col_tab_list)):  # range(start_value, end_value, step), end_value is not included!
        line_x = coord[0] + col_tab_list[index] * mm
        y1_mod = y_top_minus if index == 2 else y_top
        canvas.line(line_x, y1_mod, line_x, y_bottom)

# - draw horizontal line  below 'Cijfers voor' and 'Eindcijfers'
    left = coord[0] + col_tab_list[1] * mm
    canvas.line(left, y_top_minus, right, y_top_minus)
    #canvas.setFont('Arial', 8, leading=None)
    #canvas.setFillColor(colors.HexColor("#000000"))

   # line_height = 4 * mm
    #y_txt1 = y - line_height - 1 * mm

    # - draw page header
    commissie_school_txt = library.get('ex6_Commissie' if is_lexschool else 'ex6_School', '-')
    examen_txt = library.get('ex6_examen', '-')

    txt_list = [
        {'txt': library.get('ex6_examen_afgelegd', '-'), 'padding': 4, 'x': x + col_tab_list[0] * mm, 'offset_bottom': 1.25, 'line_height': 5},
        {'txt': library.get('ex6_Cijfers_voor', '-'), 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[3]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0},
        {'txt': library.get('ex6_Eindcijfers', '-'), 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0}
    ]
    # draw_text_one_line(canvas, coord, col_tab_list, line_height, offset_bottom, draw_line_below, vertical_lines, text_list, dont_print=False)
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, False, None, txt_list)

    txt_list = [
        {'txt': commissie_school_txt, 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[2]) / 2 * mm, 'offset_bottom': 1, 'line_height': 5},
        {'txt': library.get('ex6_Centraal', '-'), 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0}
    ]
    draw_text_one_line(canvas, coord, col_tab_list, 5, 1.25, False, None, txt_list)

    txt_list = [
        {'txt': examen_txt, 'align': 'c', 'x': x + (col_tab_list[1] + col_tab_list[2]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 4},
        {'txt': examen_txt, 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm, 'offset_bottom': 1.25, 'line_height': 0}
    ]
    draw_text_one_line(canvas, coord, col_tab_list, 4, 1.25, False, None, txt_list)
# - end of draw_pok_colum_header

