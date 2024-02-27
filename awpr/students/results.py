# PR2021-11-15
import tempfile
from django.core.files import File

from django.contrib.auth.decorators import login_required

from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext, gettext_lazy as _
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
from  accounts import views as acc_view
from  accounts import  permits as acc_prm

from awpr import menus as awpr_menu
from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import downloads as dl
from awpr import library as awpr_lib

from grades import views as grade_view
from grades import calc_results as calc_res
from grades import calc_reex as calc_reex
from grades import exfiles as grd_exfiles
from grades import draw as grd_draw

from schools import models as sch_mod
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
class GetGradelistDiplomaAuthView(View):  # PR2021-11-19

    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GetGradelistDiplomaAuthView ============= ')

        update_wrap = {}
        messages = []

# - get permit
        has_permit = acc_prm.get_permit_crud_of_this_page('page_result', request)
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
# - end of GetGradelistDiplomaAuthView


def get_pres_secr_dict(request):  # PR2021-11-18 PR2022-06-17 PR2023-08-18
    # function creates a dict of auth1 and auth2 users
    # also retrieves the selected auth and printdate from schoolsettings

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_pres_secr_dict -----')

    auth_dict = {}

# get selected auth and printdatum from schoolsettings
    if request.user and request.user.schoolbase:
        sel_examyear = acc_prm.get_sel_examyear_from_requsr(request)

    # get stored schoolsettings, to get selected_auth_pk
        settings_json = request.user.schoolbase.get_schoolsetting_dict(c.KEY_GRADELIST)
        stored_setting = json.loads(settings_json) if settings_json else {}
        if logging_on:
            logger.debug('    request.user.schoolbase.code: ' + str(request.user.schoolbase.code))
            logger.debug('    stored_setting: ' + str(stored_setting))
            # stored_setting: {'auth1_pk': 120, 'auth2_pk': None, 'printdate': None}

        sql = ''.join((
            "SELECT au.id, au.last_name, ",
                    "(POSITION('" + c.USERGROUP_AUTH1_PRES + "' IN ual.usergroups) > 0) AS auth1, ",
                    "(POSITION('" + c.USERGROUP_AUTH2_SECR + "' IN ual.usergroups) > 0) AS auth2 ",

                    "FROM accounts_user AS au ",
                    "INNER JOIN accounts_userallowed AS ual ON (ual.user_id = au.id) ",

                    "WHERE au.schoolbase_id = ", str(request.user.schoolbase_id), "::INT ",
                    "AND au.country_id = ", str(request.user.country_id), "::INT ",
                    "AND ual.examyear_id = ", str(sel_examyear.pk), "::INT ",
                    "AND au.role = ", str(c.ROLE_008_SCHOOL),  "::INT ",

                    "AND ( (POSITION('" + c.USERGROUP_AUTH1_PRES + "' IN ual.usergroups) > 0) ",
                    "OR (POSITION('" + c.USERGROUP_AUTH2_SECR + "' IN ual.usergroups) > 0 ) ) "
                    "AND au.activated AND au.is_active;"
        ))

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = af.dictfetchall(cursor)

        for row in rows:
            if logging_on:
                logger.debug('row: ' + str(row))
                # row: {'id': 47, 'last_name': 'Hans', 'auth1': False, 'auth2': True}

        # loop through 'auth1' and 'auth2'
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

    # auth_dict: {'auth1': [{'pk': 120, 'name': 'jpd'}, {'pk': 116, 'name': 'Hans meijs'}], 'auth2': []}
    return auth_dict
# - -end of get_pres_secr_dict


@method_decorator([login_required], name='dispatch')
class GradeDownloadShortGradelist(View):  # PR2022-06-05

    def get(self, request, lst):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeDownloadShortGradelist ============= ')
            logger.debug('     list: ' + str(lst))
            # list: {"sel_classes":["4a1","zz_blank"],"sortby_class":true}

        response = None

        req_user = request.user
        if req_user and req_user.country and req_user.schoolbase and lst:

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

            upload_dict = json.loads(lst)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
            sel_lvlbase_pk, sel_sctbase_pk = acc_view.get_selected_lvlbase_sctbase_from_usersetting(request)
            if logging_on:
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))

            if sel_school and sel_department:

# +++ get grade_dictlist
                sortby_class = upload_dict.get('sortby_class') or False
                sel_classes = upload_dict.get('sel_classes')
                if logging_on:
                    logger.debug('sel_classes: ' + str(sel_classes))

                include_class_blank = False
                if sel_classes:
                    if 'zz_blank' in sel_classes:
                        include_class_blank = True
                        sel_classes.remove('zz_blank')

    # calc result before printing the grade list
                student_pk_list, classes_dictlist = get_shortgradelist_student_list(sel_school, sel_department, sel_level, sel_classes, include_class_blank)
                if logging_on:
                    logger.debug('    student_pk_list: ' + str(student_pk_list))
                    logger.debug('    classes_dictlist: ' + str(classes_dictlist))
                #  classes_dictlist: [{'classname': 'zz_blank', 'stud_pk_list': [3963]}]
    # calc result before printing the grade list

    # calc result before printing the grade list
                if student_pk_list:
                    calc_res.calc_batch_student_result(
                        sel_examyear=sel_examyear,
                        sel_school=sel_school,
                        sel_department=sel_department,
                        student_pk_list=student_pk_list,
                        sel_lvlbase_pk=sel_lvlbase_pk,
                        user_lang=user_lang
                    )

                   # grade_dict, classname_list, failed_student_pk_list = get_shortgradelist_dict(
                   #     school=sel_school,
                   #     department=sel_department,
                   #     level=sel_level,
                    #    sel_classes=sel_classes,
                    #    include_class_blank=include_class_blank,
                    #    sortby_class=sortby_class
                    #)

        # +++  get_students_with_grades_dictlist
                    grade_dict, classname_list, classes_dict, failed_student_pk_list = \
                        calc_reex.calcreex_get_students_cascade_dictNEW(
                            examyear=sel_examyear,
                            school=sel_school,
                            department=sel_department,
                            level=sel_level,
                            sel_classes=sel_classes,
                            include_class_blank=include_class_blank,
                            sortby_class=sortby_class,
                            student_pk_list=student_pk_list
                        )

                    if logging_on:
                        logger.debug('    classname_list: ' + str(classname_list))
                        logger.debug('    classes_dict: ' + str(classes_dict))
                        logger.debug('    failed_student_pk_list: ' + str(failed_student_pk_list))
                        logger.debug('    grade_dict: ' + str(grade_dict))

                    """
                   grade_dict =  {
                    3963: {
                    'fullname': 'Granviel, Jurmaily A.', 'lastname': 'Granviel', 'firstname': 'Jurmaily Adriana', 'result': 2,
                     
                    'stud_id': 3963, 'examnumber': 'A19', 'bis_exam': True, 'school_name': 'Ancilla Domini Vsbo', 'school_code': 'CUR01', 
                    'depbase_code': 'Vsbo', 'examyear_code': 2022, 'scheme_id': 73, 'dep_abbrev': 'V.S.B.O.', 'level_req': True, 'lvlbase_code': 'PKL', 'sctbase_code': 'ec',
                     'gl_ce_avg': '5.0', 'gl_combi_avg': '7', 'gl_final_avg': '5.9', 'has_use_reex': True,
                    
                    'subj_list': [
                        ('Lichamelijke opvoeding', 21571, 1, 0), ('Nederlandse taal', 21568, 1, 1), ('Papiamentu', 21573, 1, 1), ('Stage', 21576, 1, 0), 
                    ], 
                    
                    21571: {'subjbase_code': 'lo', 'subject_id': 116, 'schemeitem_id': 1743, 'exemption_year': 2021, 'gl_sesrgrade': '6.5', 'gl_finalgrade': '7', 'gl_examperiod': 4, 'has_exemption': True, 'gradetype': 1, 'weight_se': 1, 'multiplier': 1, 'is_combi': True, 'rule_grade_sufficient': True, 'rule_gradesuff_notatevlex': True, 'subj_name_nl': 'Lichamelijke opvoeding', 'subjtype_abbrev': 'Gemeensch.'}, 
                        }
                    
                    }
                    
                    """
        # calculate possible reex
                    write_log = True # for testing, set False in production to speed up
                    log_list = []
                    for failed_student_pk in failed_student_pk_list:
                        student_dict = grade_dict.get(failed_student_pk)
                        if logging_on and False:
                            logger.debug('    student_dict: ' + str(student_dict))

                        if student_dict:
                           calc_reex.calcreex_student_reex_result(sel_department, student_dict, write_log, log_list)

                        if logging_on and False:
                            logger.debug('   NEW grade_dict: ' + str(grade_dict))

                    if logging_on:
                        logger.debug('    log_list: ' + str(log_list))

                    pdf = grd_draw.print_shortgradelist(sel_examyear, sel_school, sel_department, classname_list, classes_dict, grade_dict, user_lang)

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
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of GradeDownloadShortGradelist

        """
        email 31 3 2023
        Ik stel voor het registratienummer op de diploma’s en cijferlijsten als volgt in te richten:
        
        23c01k999999
        Waarbij:
        •	De eerste twee cijfers zijn het jaartal
        •	De derde letter is ‘c’ voor Curaçao en ‘s’ voor Sint Maarten
        •	Het vierde en vijfde cijfer is het nummer van de schoolcode
        •	Het zesde teken geeft de afdeling en leerweg weer: b voor pbl, k voor pkl, t voor tkl, h voor Havo en v voor vwo
        •	Het getal daarna bestaat uit 6 cijfers en is een uniek nummer dat door AWP wordt gegenereerd.
        De afwisseling tussen cijfers en kleine letters verhoogt de leesbaarheid.
        
        Het registratienummer  komt in het midden onderaan het waardepapier. Het sedulanummer komt links onder, rechts onder staat het ‘batch’ nummer van het waardepapier.
        
        Om na te gaan of een diploma of cijferlijst authentiek is kun je het registratienummer opzoeken in AWP. 
        Als het nummer voorkomt in AWP wordt het opgeslagen waardepapier weergegeven. 
        
        Als het registratienummer van een waardepapier niet voorkomt in AWP of wanneer het niet overeenkomt met de opgeslagen versie, is er sprake van een vervalsing.
        
        """

@method_decorator([login_required], name='dispatch')
class DownloadGradelistDiplomaView(View):
    # PR2021-11-15 PR2023-12-04

    # PR2023-12-04 TODO cannor print final gradelist / diploma when result is not approved by Inspectorate
    # the gradelist / diploma stays then blank
    # mustt create a message to inform that the result must be approved by the Inspectorate

    def get(self, request, lst):
        logging_on = s.LOGGING_ON
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
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
            sel_lvlbase_pk, sel_sctbase_pk = acc_view.get_selected_lvlbase_sctbase_from_usersetting(request)
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
                is_diploma = mode == 'diploma'
                # PR2023-06-16 save final gradelist and diploma to disk
                save_to_disk = not is_prelim

# +++++ calc_batch_student_result ++++++++++++++++++++
                if not is_diploma:
                    calc_res.calc_batch_student_result(
                        sel_examyear=sel_examyear,
                        sel_school=sel_school,
                        sel_department=sel_department,
                        student_pk_list=student_pk_list,
                        sel_lvlbase_pk=sel_lvlbase_pk,
                        user_lang=user_lang
                    )

# - print 'Herexamen' instead of 'Afgewezen', only when prelim gradelist is printed
                # also print 'Geslaagd' when 'cijferverbetering' PR203-06-10
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
                key_str = 'diploma' if is_diploma else 'gradelist'
                library = awpr_lib.get_library(sel_examyear, [key_str])

# +++ get grade_dictlist / diploma_dictlist

# - get list of used regnumbers, to check unique regnumbers
                used_regnumber_list = self.get_used_regnumber_list(sel_school, sel_department)
                if logging_on:
                    logger.debug('     used_regnumber_list: ' + str(used_regnumber_list))

# +++ get grade_dictlist / diploma_dictlist
                if is_diploma:
                    student_list = get_diploma_dictlist(sel_examyear, sel_school, sel_department, sel_lvlbase_pk,
                                                          sel_sctbase_pk,
                                                          student_pk_list, used_regnumber_list)
                else:
                    student_list = get_gradelist_dictlist(sel_examyear, sel_school,
                                                          sel_department, sel_lvlbase_pk, sel_sctbase_pk, is_prelim,
                                                  student_pk_list, used_regnumber_list)
                if logging_on:
                    logger.debug('     student_list: ' + str(student_list))
 # +++ get name of chairperson and secretary
                # auth_dict = get_pres_secr_dict(request)

        # - get fonts
                af.register_font_arial()
                af.register_font_garamond()
                af.register_font_palace_script()

                auth1_name = acc_prm.get_auth_name(auth1_pk, c.USERGROUP_AUTH1_PRES, sel_examyear, request)
                auth2_name = acc_prm.get_auth_name(auth2_pk, c.USERGROUP_AUTH2_SECR, sel_examyear, request)

                if logging_on:
                    logger.debug('     auth1_name: ' + str(auth1_name))
                    logger.debug('     auth2_name: ' + str(auth2_name))

                # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

                # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                # temp_file = tempfile.TemporaryFile()
                # canvas = Canvas(temp_file)

    # - Create an in-memory output file for the new pdf to be downloaded (may have multiple students)
                buffer = io.BytesIO()
                canvas = Canvas(buffer)

                for student_dict in student_list:

                    if logging_on:
                        logger.debug('     student_dict: ' + str(student_dict))

        # print file to be downloaded, will not saved
                    if is_diploma:
                        if is_sxm:
                            grd_draw.draw_diploma_sxm(canvas, library, student_dict, auth1_name, auth2_name, printdate, sel_examyear.code)
                        else:
                            grd_draw.draw_diploma_cur(canvas, library, student_dict, auth1_name, auth2_name, printdate, sel_examyear.code)

                    else:
                        if is_sxm:
                            grd_draw.draw_gradelist_sxm(canvas, library, student_dict, is_prelim, print_reex, auth1_name, auth2_name, printdate, sel_examyear, request)
                        else:
                            grd_draw.draw_gradelist_cur(canvas, library, student_dict, is_prelim, print_reex, auth1_name, auth2_name, printdate, sel_examyear, request)

                    canvas.showPage()

                    if logging_on:
                        logger.debug('save_to_disk: ' + str(save_to_disk))

        # +++  print and save pdf for each sudent separately
                    if save_to_disk:
                # - create new published_instance.
                        now_arr = upload_dict.get('now_arr')
                        published_instance = grade_view.create_published_instance_gradelist_diploma(
                            sel_examyear=sel_examyear,
                            sel_school=sel_school,
                            sel_department=sel_department,
                            lvlbase_code=student_dict.get('lvlbase_code'),
                            student_pk=student_dict.get('stud_id'),
                            lastname_initials=student_dict.get('lastname_initials'),
                            regnumber=student_dict.get('regnumber') or '',
                            save_to_disk=save_to_disk,
                            is_diploma=is_diploma,
                            now_arr=now_arr,
                            request=request
                        )
                        published_pk = published_instance.pk if published_instance else None

                        if logging_on:
                            logger.debug('published_pk: ' + str(published_pk))
                            logger.debug('published_instance.filename: ' + str(published_instance.filename))

                        examyear_str = str(sel_examyear.code)
                        school_code = sel_school.base.code if sel_school.base.code else '---'
                        country_abbrev = sel_examyear.country.abbrev.lower()
                        file_dir = '/'.join((country_abbrev, examyear_str, school_code, 'diploma'))
                        file_path = '/'.join((file_dir, published_instance.filename))

                        if logging_on:
                            logger.debug('    file_dir: ' + str(file_dir))
                            logger.debug('    filepath: ' + str(file_path))

                        ########################

           # - create separate file for each student when printing final diploma or gradelist
                        # from https://docs.python.org/3/library/tempfile.html
                        #temp_file = tempfile.TemporaryFile()
                        #canvas_tobesaved = Canvas(temp_file)

                        buffer_tobesaved = io.BytesIO()
                        canvas_tobesaved = Canvas(buffer_tobesaved)

                        if is_diploma:
                            if is_sxm:
                                grd_draw.draw_diploma_sxm(canvas_tobesaved, library, student_dict, auth1_name, auth2_name,
                                                          printdate, sel_examyear.code)
                            else:
                                grd_draw.draw_diploma_cur(canvas_tobesaved, library, student_dict, auth1_name, auth2_name,
                                                          printdate, sel_examyear.code)

                        else:
                            if is_sxm:
                                if logging_on:
                                    logger.debug('    draw_gradelist_sxm: ' + str(is_sxm))
                                grd_draw.draw_gradelist_sxm(canvas_tobesaved, library, student_dict, is_prelim,
                                                            print_reex, auth1_name, auth2_name, printdate, sel_examyear, request)
                            else:
                                grd_draw.draw_gradelist_cur(canvas_tobesaved, library, student_dict, is_prelim,
                                                            print_reex, auth1_name, auth2_name, printdate, sel_examyear, request)

                        canvas_tobesaved.showPage()

                        # PR2023-06-19 do't forget to save the canvas first! It took me 2 hours to find out
                        canvas_tobesaved.save()

                # Rewind the buffer.
                        # seek(0) sets the pointer position at 0.
                        buffer_tobesaved.seek(0)
                        pdf_file = File(buffer_tobesaved, published_instance.filename)

                        published_instance.file.save(file_path, pdf_file)

                        # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
                        published_instance.save(request=request)

                canvas.save()

                # PR2023-06-22 INTERNAL SERVER ERROR when downloading a document with special characters
                # UnicodeEncodeError  gunicorn.util in to_bytestring
                # the document saved on server is ok > change code of response like in saved version
                # was:

                # found it, thanks to https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string
                # problem is not in the buffer or pdf, but gunicorn does not accept special characters
                # solution: don't add student name in  file_name

                file_name = 'Diploma' if mode == 'diploma' else 'Cijferlijst'
                # PR2023-06-22
                #if len(student_list) == 1:
                #    file_name += ' van ' + student_list[0].get('fullname')
                now_formatted = af.get_now_formatted_from_now_arr(upload_dict.get('now_arr'))
                if now_formatted:
                    file_name += ' ' + now_formatted
                file_name += '.pdf'

                if logging_on:
                    logger.debug('    file_name: ' + str(file_name))

                # seek(0) sets the pointer position at 0.
                buffer.seek(0)
                # this does not work:
                #  pdf = File(buffer, file_name)

                pdf = buffer.getvalue()

                response = HttpResponse(content_type='application/pdf')
                # PR2023-06-22 try attachment instead of inline > doesnt tsolve the problem
                # response['Content-Disposition'] = 'attachment; filename="' + file_name + '"'

                response['Content-Disposition'] = 'inline; filename="' + file_name + '"'

                response.write(pdf)
                if logging_on:
                    logger.debug('    response.write(pdf')
###################################
        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


    def get_used_regnumber_list(self, sel_school, sel_department):
        # PR2023-06-18
        used_regnumber_list = []
        try:
            # don't filter on deleted students
            sql = ' '.join(("SELECT dpgl.regnumber",
                            "FROM students_diplomagradelist AS dpgl",
                            "INNER JOIN students_student AS stud ON (stud.id = dpgl.student_id)",
                            "WHERE stud.school_id = ", str(sel_school.pk) , "::INT",
                            "AND stud.department_id = ", str(sel_department.pk) , "::INT"
                            ))
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()

            for row in rows:
                used_regnumber_list.append(row[0])

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

        return used_regnumber_list


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
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)
            sel_lvlbase_pk, sel_sctbase_pk = acc_view.get_selected_lvlbase_sctbase_from_usersetting(request)
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

                proof_of_knowledge_dict = calc_res.get_proof_of_knowledge_dict(
                    examyear=sel_examyear,
                    school=sel_school,
                    department=sel_department,
                    lvlbase_pk=sel_lvlbase_pk,
                    student_pk_list=student_pk_list
                )
                if proof_of_knowledge_dict:

        # - get arial font
                    af.register_font_arial()

                    auth1_name = acc_prm.get_auth_name(auth1_pk, c.USERGROUP_AUTH1_PRES, sel_examyear, request)

                    buffer = io.BytesIO()
                    canvas = Canvas(buffer)

                    for student_dict in proof_of_knowledge_dict.values():
                        grd_draw.draw_pok(canvas, library, student_dict, auth1_name, printdate, sel_examyear.code)

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

                    # PR2023-08-18 Sentry INTERNAL SERVER ERROR when downloading a document with special characters
                    # UnicodeEncodeError  gunicorn.util in to_bytestring

                    # found it, thanks to https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string
                    # problem is not in the buffer or pdf, but gunicorn does not accept special characters
                    # solution: don't add student name in file_name
                    # was:
                        #if len(proof_of_knowledge_dict) == 1:
                        #    for pok_dict in  proof_of_knowledge_dict.values():
                        #        file_name += ' ' + pok_dict.get('full_name')
                        #        break
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

####################################

def get_gradelist_dictlist(examyear, school, department, sel_lvlbase_pk, sel_sctbase_pk, is_prelim, student_pk_list, used_regnumber_list):
    # PR2021-11-19 PR2023-06-10

    # NOTE: don't forget to filter deleted = false!! PR2021-03-15
    # grades that are not published are only visible when 'same_school'

    # PR2023-06-20 when not prelim: filter on gl_status = 1, i.e. approved by Inspectorate

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

    # PR2023-07-04 debug: Friedeman Hasselbaink Jacques Ferrandi: wants to print gradelist 2022.
    # has saved regnumber instead of calculated regnumber
    use_saved_regnumber = examyear.code < 2023

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk,
                'student_pk_arr': student_pk_list}
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    grade_dictlist_sorted = []
    grade_dict = {}

    sql_list = ["SELECT studsubj.id AS studsubj_id, stud.id AS stud_id,",
                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, stud.gender, stud.idnumber, stud.regnumber,",
                "stud.birthdate, stud.birthcountry, stud.birthcity, stud.bis_exam,"
                "stud.gl_ce_avg, stud.gl_combi_avg, stud.gl_final_avg, stud.result, stud.result_status,",
                "stud.gl_status, stud.ep01_result,",
                "school.name AS school_name, school.article AS school_article, school.islexschool,",
                "sb.code AS school_code, depbase.code AS depbase_code, lvlbase.code AS lvlbase_code,",
                "ey.code AS examyear_code, ey.code::TEXT AS examyear_txt, c.name AS country,",
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
                "AND NOT stud.deleted AND NOT stud.tobedeleted",
                "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted"
                ]
    if not is_prelim:
        sql_list.extend(("AND stud.gl_status =", str(c.GL_STATUS_01_APPROVED), "::INT"))

    if student_pk_list:
        #sql_keys['student_pk_arr'] = student_pk_list
        #sql_list.append("AND stud.id IN ( SELECT UNNEST( %(student_pk_arr)s::INT[]))")
        sql_list.extend(("AND stud.id IN (SELECT UNNEST(ARRAY", str(student_pk_list), "::INT[])) "))

    else:
        if sel_lvlbase_pk:
            #sql_keys['lvlbase_pk'] = sel_lvlbase_pk
            #sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")
            sql_list.extend(("AND lvl.base_id = ", str(sel_lvlbase_pk), "::INT"))

        if sel_sctbase_pk:
            #sql_keys['sctbase_pk'] = sel_sctbase_pk
            #sql_list.append("AND sct.base_id = %(sctbase_pk)s::INT")
            sql_list.extend(("AND sct.base_id = ", str(sel_sctbase_pk), "::INT"))

    sql_list.append("ORDER BY subj.sequence")

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        grade_rows = af.dictfetchall(cursor)

    if logging_on:
        logger.debug('len grade_rows: ' + str(len(grade_rows)))

    # - add full name to rows, and array of id's of auth
    if grade_rows:
        for row in grade_rows:
            stud_id = row.get('stud_id')

            if stud_id not in grade_dict:
                #full_name = stud_fnc.get_full_name(row.get('lastname'), row.get('firstname'), row.get('prefix'))
                last_name = row.get('lastname') or '---'
                first_name = row.get('firstname') or '---'
                prefix = row.get('prefix')
                full_name = stud_fnc.get_firstname_prefix_lastname(last_name, first_name, prefix)

                lastname_initials = stud_fnc.get_lastname_initials(last_name, first_name, prefix)

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
                # - calc regnumber - get it from database table Student when examyear = 2022, calculate otherwise
                if use_saved_regnumber:
                    reg_number = row.get('regnumber') or '---'
                else:
                    reg_number = stud_fnc.calc_regnumber(
                        school_code=row.get('school_code'),
                        gender=row.get('gender'),
                        examyear_str=row.get('examyear_txt'),
                        examnumber_str=row.get('examnumber'),
                        depbase_code=row.get('depbase_code'),
                        levelbase_code=row.get('lvlbase_code'),
                        bis_exam=row.get('bis_exam'),
                        used_regnumber_list=used_regnumber_list
                    )

                if logging_on:
                    logger.debug('    use_saved_regnumber: ' + str(use_saved_regnumber))
                    logger.debug('    reg_number: ' + str(reg_number))



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

                    'stud_id': stud_id,
                    'firstname': first_name,
                    'lastname': last_name,

                    'fullname': full_name,
                    'lastname_initials': lastname_initials,

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
        # was: grade_dictlist_sorted = sorted(grade_list, key=lambda d: d['sortname'])

        # PR2023-07-11 email Jean Provence-Laurence MPC VSBO-TKL: order of gradelist not same as diploma
        # cause: diploma sorts with: sql_list.append("ORDER BY LOWER(stud.lastname), LOWER(stud.firstname)")
        # gradelist sorts with:    grade_dictlist_sorted = sorted(grade_list, key=lambda k: (k['lastname'], k['firstname']))
        # solved by adding 'lower()'
        # was: grade_dictlist_sorted = sorted(grade_list, key=lambda k: (k['lastname'], k['firstname']))
        grade_dictlist_sorted = sorted(grade_list, key=lambda k: (k['lastname'].lower(), k['firstname'].lower()))

        if logging_on:
            if grade_dictlist_sorted:
                for row in grade_dictlist_sorted:
                    logger.debug('row: ' + str(row))

    return grade_dictlist_sorted
# - end of get_gradelist_dictlist


def get_diploma_dictlist(examyear, school, department, sel_lvlbase_pk, sel_sctbase_pk,
                           student_pk_list, used_regnumber_list):
    # PR2022-06-16 PR2022-06-24 PR2023-06-10

    # NOTE: don't forget to filter deleted = false!! PR2021-03-15
    # PR2022-06-24 Marisela Cijntje Radulphus: cannot print diploma of passed students with reex
    # solved by: allow printing if ep01_result or ep02_result or ep01_result = passed

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_diploma_dictlist -----')
        logger.debug('student_pk_list: ' + str(student_pk_list))

    # PR2023-07-04 debug: Friedeman Hasselbaink Jacques Ferrandi: wants to print gradelist 2022.
    # has saved regnumber instead of calculated regnumber
    use_saved_regnumber = examyear.code < 2023

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk, 'passed': c.RESULT_PASSED,
                'student_pk_arr': student_pk_list}
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    sql_list = ["SELECT stud.id AS stud_id,",
                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, stud.gender, stud.idnumber, stud.regnumber,",
                "stud.birthdate, stud.birthcountry, stud.birthcity, stud.bis_exam,",
                "stud.gl_ce_avg, stud.gl_combi_avg, stud.gl_final_avg, stud.result, stud.result_status,",
                "stud.ep01_result, stud.ep02_result, stud.result,"
                "stud.gl_status,"
                "school.name AS school_name, school.article AS school_article, school.islexschool,",
                "sb.code AS school_code, depbase.code AS depbase_code, lvlbase.code AS lvlbase_code,"
                "ey.code AS examyear_code, ey.code::TEXT AS examyear_txt, c.name AS country,",
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
                "AND NOT stud.deleted AND NOT stud.tobedeleted",
                # PR2023-06-20 only print diploma when Inspectorate has approved gl_result
                "AND stud.gl_status =", str(c.GL_STATUS_01_APPROVED), "::INT"
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

    sql_list.append("ORDER BY LOWER(stud.lastname), LOWER(stud.firstname)")

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

            lastname_initials = stud_fnc.get_lastname_initials(last_name, first_name, prefix)

    # add dots to idnumber, if last 2 digits are not numeric: dont print letters, pprint '00' instead
            idnumber_withdots_no_char = stud_fnc.convert_idnumber_withdots_no_char(row.get('idnumber'))

    # - calc regnumber - get it from database table Student when examyear = 2022, calculate otherwise
            if use_saved_regnumber:
                reg_number = row.get('regnumber') or '---'
            else:
                reg_number = stud_fnc.calc_regnumber(
                    school_code=row.get('school_code'),
                    gender=row.get('gender'),
                    examyear_str=row.get('examyear_txt'),
                    examnumber_str=row.get('examnumber'),
                    depbase_code=row.get('depbase_code'),
                    levelbase_code=row.get('lvlbase_code'),
                    bis_exam=row.get('bis_exam'),
                    used_regnumber_list=used_regnumber_list
                )

            if logging_on:
                logger.debug(' ----- get_diploma_dictlist -----')
                logger.debug('    examyear.code: ' + str(examyear.code))
                logger.debug('    use_saved_regnumber: ' + str(use_saved_regnumber))
                logger.debug('    reg_number: ' + str(reg_number))
                logger.debug('    row.get(regnumber): ' + str(row.get('regnumber')))

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

                'stud_id': row.get('stud_id'),
                'fullname': full_name,
                'lastname_initials': lastname_initials,
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



def get_shortgradelist_student_list(school, department, level, sel_classes, include_class_blank):
    # PR2023-06-05
    # get list of selected students, to calc result before printing the shortgradelist

    sql_list = ["SELECT stud.id AS stud_id, stud.classname",

                "FROM students_studentsubject AS studsubj",
                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",

                "WHERE stud.school_id = ", str(school.pk), "::INT ",
                "AND dep.id = ", str(department.pk), "::INT",

                "AND NOT stud.deleted AND NOT stud.tobedeleted",
                "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted"
                ]

    class_blank_clause = "stud.classname IS NULL"
    if sel_classes:
        sel_classes_clause = ''.join(("LOWER(stud.classname) IN (SELECT UNNEST(ARRAY", str(sel_classes), "::TEXT[]))"))
        if include_class_blank:
            sql_list.extend(("AND (", sel_classes_clause, " OR ", class_blank_clause, ")"))
        else:
            sql_list.extend(("AND ", sel_classes_clause))
    else:
        if include_class_blank:
            sql_list.extend(("AND ", class_blank_clause))
        else:
            sql_list.extend(("AND FALSE"))

    if level:
        sql_list.extend(("AND lvl.base_id = ", str(level.base.pk), "::INT"))

    sql_list.append("GROUP BY stud.id, stud.classname")
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()
    student_pk_list = []
    classes_dict = {}
    if rows:
        for row in rows:
            student_pk_list.append(row[0])
            class_name = row[1] if row[1] else 'zz_blank'
            if class_name not in classes_dict:
                classes_dict[class_name] = {'classname': class_name, 'stud_pk_list': [row[0]]}
            else:
                classes_dict[class_name]['stud_pk_list'].append(row[0])

    # convert dict to sorted dictlist
    classes_dictlist = sorted(list(classes_dict.values()), key=lambda k: (k['classname'])) if classes_dict else []

    return student_pk_list, classes_dictlist
# - end of get_shortgradelist_student_list


def get_shortgradelist_dict(school, department, level, sel_classes, include_class_blank, sortby_class):
    # PR2023-06-05


    # NOTE: don't forget to filter deleted = false!! PR2021-03-15

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_gradelist_dictlist -----')
        logger.debug('sel_classes: ' + str(sel_classes) + ' ' + str(type(sel_classes)))
        logger.debug('include_class_blank: ' + str(include_class_blank))
        logger.debug('sortby_class: ' + str(sortby_class))

    # upload_dict: {'subject_list': [2206, 2165, 2166], 'sel_layout': 'level', 'level_list': [86, 85]}

    # values of sel_layout are:"none", "level", "class", "cluster"
    # "none" or None: all students of subject on one form
    # "level:" seperate form for each leeerweg
    #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
    #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

    #sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}
    #if logging_on:
    #    logger.debug('sql_keys: ' + str(sql_keys))

    sql_list = ["SELECT studsubj.id AS studsubj_id, stud.id AS stud_id,",
                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
                "stud.classname, stud.bis_exam,"
                
                "stud.extrafacilities, stud.iseveningstudent, stud.islexstudent, stud.partial_exam,"

                "stud.gl_ce_avg, stud.gl_combi_avg, stud.gl_final_avg, stud.result,",

                "depbase.code AS depbase_code, dep.level_req, lvlbase.code AS lvlbase_code, sctbase.code AS sctbase_code,",

                "studsubj.gradelist_sesrgrade, studsubj.gradelist_pecegrade, studsubj.gradelist_finalgrade,",
                "studsubj.is_extra_nocount, studsubj.is_thumbrule, studsubj.is_extra_counts,",
                "studsubj.gradelist_use_exem, studsubj.gl_examperiod,",

                "subj.id AS subj_id, subjbase.code AS subjbase_code, subj.sequence, si.is_combi",

                "FROM students_studentsubject AS studsubj",
                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",

                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",
                "LEFT JOIN subjects_sectorbase AS sctbase ON (sctbase.id = sct.base_id)",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "WHERE stud.school_id = ", str(school.pk), "::INT ",
                "AND dep.id = ", str(department.pk), "::INT",

                "AND NOT stud.deleted AND NOT stud.tobedeleted",
                "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted"
                ]

    class_blank_clause = "stud.classname IS NULL"
    if sel_classes:
        sel_classes_clause = ''.join(("LOWER(stud.classname) IN (SELECT UNNEST(ARRAY", str(sel_classes), "::TEXT[]))"))
        if include_class_blank:
            sql_list.extend(("AND (", sel_classes_clause, " OR ", class_blank_clause, ")"))
        else:
            sql_list.extend(("AND ", sel_classes_clause))
    else:
        if include_class_blank:
            sql_list.extend(("AND ", class_blank_clause))
        else:
            sql_list.extend(("AND FALSE"))

    if level:
        sql_list.extend(("AND lvl.base_id = ", str(level.base.pk), "::INT"))

    sql_list.append("ORDER BY subj.sequence")

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql)
        grade_rows = af.dictfetchall(cursor)
        if logging_on:
            logger.debug('len grade_rows: ' + str(len(grade_rows)))

    grade_dict = {}
    classname_list = []
    failed_student_pk_list = []
    if grade_rows:
        for row in grade_rows:

            if logging_on:
                logger.debug('row: ' + str(row))
            try:
                stud_id = row.get('stud_id')
                row_classname = row.get('classname')

                if not sortby_class:
                    classname = 'all'
                elif row_classname is None:
                    classname = ''.join(('<', gettext('not entered'), '>'))
                else:
                    classname = row_classname.lower()

                if classname not in grade_dict:
                    grade_dict[classname] = {}
                    classname_list.append(classname)

                class_dict = grade_dict[classname]

                if stud_id not in class_dict:
                    last_name = row.get('lastname') or '---'
                    first_name = row.get('firstname') or '---'
                    prefix = row.get('prefix')
                    full_name = stud_fnc.get_lastname_firstname_initials(
                        last_name=last_name,
                        first_name=first_name,
                        prefix=prefix,
                        has_extrafacilities=False
                    )
                    #sort_name = (last_name.lower() + c.STRING_SPACE_30)[:30] + first_name.lower()

                    result = row.get('result') or 0
                    class_dict[stud_id] = {
                        'depbase_code': row.get('depbase_code'),
                        'lvlbase_code': row.get('lvlbase_code'),
                        'level_req': row.get('level_req', False),

                        'sctbase_code': row.get('sctbase_code'),
                        'classname': row_classname,

                        #'firstname': first_name,
                        #'lastname': last_name,

                        'fullname': full_name,
                        #'sortname': sort_name,

                        'examnumber': row.get('examnumber'),

                        'bis_exam': row.get('bis_exam'),
                        'extrafacilities': row.get('extrafacilities'),
                        'iseveningstudent': row.get('iseveningstudent'),
                        'islexstudent': row.get('islexstudent'),
                        'partial_exam': row.get('partial_exam'),

                        'ce_avg': row.get('gl_ce_avg'),
                        'combi_avg': row.get('gl_combi_avg'),
                        'final_avg': row.get('gl_final_avg'),

                        'result': result
                    }
                    if result == c.RESULT_FAILED:
                        failed_student_pk_list.append(stud_id)

                    student_list = class_dict.get('student_list')
                    if student_list:
                        #student_list.append({'id': stud_id, 'sortname': sort_name})
                        student_list.append({'id': stud_id,  'firstname': first_name, 'lastname': last_name})
                    else:
                        #class_dict['student_list'] = [{'id': stud_id, 'sortname': sort_name}]
                        class_dict['student_list'] = [{'id': stud_id, 'firstname': first_name, 'lastname': last_name}]

                # - add subjecttype dict
                student_dict = class_dict.get(stud_id)
                if student_dict:
                    # put combi subjects in dict with key: 'combi', others in dict with key: subjecttype_id
                    # werkstuk Havo/Vwo is combi subject, is added to list of combi subjects
                    # werkstuk Vsbo TKL is not a combi subject, it is added with key 'wst', grade is shown in draw_wst
                    # stage it is added with key 'stg', grade is shown in draw_stg
                    is_combi = row.get('is_combi', False)
                    if is_combi:
                        sjtp_sequence = 'combi'
                    else:
                        sjtp_sequence = 'nocombi'

                    if sjtp_sequence not in student_dict:
                        student_dict[sjtp_sequence] = {
                            'combi_avg': row.get('gl_combi_avg')
                        }

                    sjtp_dict = student_dict.get(sjtp_sequence)
                    subj_id = row.get('subj_id')
                    if subj_id not in sjtp_dict:
                        segrade = row.get('gradelist_sesrgrade').replace('.', ',') if row.get(
                            'gradelist_sesrgrade') else None
                        pecegrade = row.get('gradelist_pecegrade').replace('.', ',') if row.get(
                            'gradelist_pecegrade') else None
                        finalgrade = row.get('gradelist_finalgrade')

                        sjtp_dict[subj_id] = {
                            'segrade': segrade,
                            'pecegrade': pecegrade,
                            'finalgrade': finalgrade
                        }
                    subj_dict = sjtp_dict[subj_id]

            # - check if studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.gradelist_use_exem is True
                    # if so: add 'has_extra_nocount' = True to student-dict
                    # used to add foornote in gradelist
                    info_list = []
                    if row.get('is_extra_nocount', False):
                        info_list.append('+')
                        student_dict['has_extra_nocount'] = True
                    if row.get('is_extra_counts', False):
                        info_list.append('++')
                        student_dict['has_extra_counts'] = True
                    if row.get('is_thumbrule', False):
                        info_list.append('d')
                        student_dict['has_thumbrule'] = True

                    if row.get('gradelist_use_exem', False):
                        info_list.append('vr')
                        student_dict['has_use_exem'] = True

                    gl_examperiod = row.get('gl_examperiod', 0)
                    if gl_examperiod == c.EXAMPERIOD_SECOND:
                        info_list.append('her')
                        student_dict['has_use_reex'] = True
                    elif gl_examperiod == c.EXAMPERIOD_THIRD:
                        info_list.append('her 3e tv')
                        student_dict['has_use_reex3'] = True

                    subjbase_code = row.get('subjbase_code') or '-'
                    if info_list:
                        info_txt = ', '.join(info_list)
                        subjbase_code += ''.join((' (', info_txt, ')'))
                    subj_dict['subjbase_code'] = subjbase_code
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
    classname_list.sort()

    if logging_on:
        # logger.debug('    grade_dict: ' + str(grade_dict))
        logger.debug('    classname_list: ' + str(classname_list))
        logger.debug('    failed_student_pk_list: ' + str(failed_student_pk_list))

    return grade_dict, classname_list, failed_student_pk_list
# - end of get_shortgradelist_dict


def draw_red_cross(canvas, x, y):
    # draw red cross, for outlining while designing
    canvas.setStrokeColorRGB(1, 0, 0)
    canvas.line(x, y + 5 * mm, x, y - 5 * mm)
    canvas.line(x - 5 * mm, y , x + 5 * mm, y )
