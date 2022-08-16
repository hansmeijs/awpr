# PR2021-11-24
from django.contrib.auth.decorators import login_required
from django.db import connection

from django.core.files.storage import FileSystemStorage

from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotFound, FileResponse
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate
from django.views.generic import View

from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Frame

from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import downloads as dl
from awpr import settings as awpr_settings
from awpr import library as awpr_lib

from accounts import views as acc_view
from schools import models as sch_mod
from students import functions as stud_fnc
from subjects import models as subj_mod
from grades import views as gr_vw

from os import path
import io

import json
import logging
logger = logging.getLogger(__name__)


@method_decorator([login_required], name='dispatch')
class GradeDownloadPdfViewNIU(View):  # PR2021-02-0

    def post(self, request):
        logger.debug(' ============= GradeDownloadPdfView ============= ')
        # function creates, Ex2A pdf file based on settings in usersetting
        response = None
        try:
            if request.user and request.user.country and request.user.schoolbase:
                req_user = request.user

    # - reset language
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

                # - get upload_dict from request.POST
                upload_json = request.POST.get('upload', None)
                if upload_json:
                    upload_dict = json.loads(upload_json)
                    logger.debug('upload_dict' + str(upload_dict))

                    # upload_dict{'table': 'published', 'mapid': 'published_63', 'published_pk': 63}
                    # - get selected grade from upload_dict - if any
                    published_pk = upload_dict.get('published_pk')
                    logger.debug('published_pk: ' + str(published_pk))
                    published = sch_mod.Published.objects.get_or_none(pk=published_pk)
                    if published:
                        filename = getattr(published, 'filename')
                        filename = 'Ex2A - CUR12 St. Paulus Vsbo - SE 1e tv.pdf'
                        logger.debug('filename' + str(filename))
                        fs = FileSystemStorage()
                        logger.debug('fs.exists(filename)' + str(fs.exists(filename)))

                        # fs.fs.locationC: = C:\dev\awpr\awpr\static\media
                        logger.debug('fs.location' + str(fs.location))
                        logger.debug('fs.path' + str(fs.path))

                        if fs.exists(filename):
                            with fs.open(filename) as pdf:
                                response = FileResponse(pdf)

                               # response = HttpResponse(content_type='application/pdf')
                                #response['Content-Disposition'] = 'inline; filename="testpdf.pdf"'
                                # response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

                                response.write(pdf)

                                """
                                response = HttpResponse(pdf, content_type='application/pdf')
                                response['Content-Disposition'] = 'inline; filename="mypdf.pdf"'
                                #response['Content-Disposition'] = 'attachment; filename="mypdf.pdf"'
                                logger.debug('response' + str(response))
                                return response
                                """
                                logger.debug('response' + str(response))
                                return response


                        else:
                            return HttpResponseNotFound('The requested pdf was not found in our server.')

        except:
            raise Http404("Error creating Ex2A file")




@method_decorator([login_required], name='dispatch')
class GetEx3infoView(View):  # PR2021-10-06

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= GetEx3infoView ============= ')

        update_wrap = {}

# - get permit - no permit necessary

# - reset language
        #user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        #activate(user_lang)

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            # upload_dict = json.loads(upload_json)

# - get ex3 settings from usersetting
            setting_dict = acc_view.get_usersetting_dict(c.KEY_EX3, request)
            if logging_on:
                logger.debug('setting_dict: ' + str(setting_dict))
            if setting_dict:
                # setting_dict: {'sel_layout': 'class', 'lvlbase_pk_list': '[86, 85]'}
                sel_layout = setting_dict.get('sel_layout')
                if sel_layout:
                    update_wrap['sel_layout'] = sel_layout

                lvlbase_pk_list = setting_dict.get('lvlbase_pk_list')
                if lvlbase_pk_list:
                    update_wrap['lvlbase_pk_list'] = lvlbase_pk_list

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_editNIU, msg_listNIU = \
                dl.get_selected_ey_school_dep_from_usersetting(request)

# - get selected examperiod from usersettings
            sel_examperiod = None
            selected_pk_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
            if selected_pk_dict:
                sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
            if not sel_examperiod:
                sel_examperiod = 1
            update_wrap['sel_examperiod'] = sel_examperiod
            update_wrap['examperiod_caption'] = c.EXAMPERIOD_CAPTION.get(sel_examperiod)
            if logging_on:
                logger.debug('update_wrap: ' + str(update_wrap))

            subject_rows = self.get_subject_rows (sel_examyear, sel_school, sel_department, sel_examperiod)

            update_wrap['ex3_subject_rows'] = subject_rows

        # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))


    def get_subject_rows (self, examyear, school, department, examperiod):
        # PR2021-10-09
        # note: don't forget to filter deleted = false!! PR2021-03-15
        # grades that are not published are only visible when 'same_school'
        # note_icon is downloaded in separate call

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ----- get_subject_rows -----')

        sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk, 'examperiod': examperiod}

        sql_list = ["SELECT subj.id AS subj_id, subjbase.code AS subj_code, subj.name AS subj_name,",
                    # TODO add cluster
                    # "MAX(studsubj.clustername) AS max_clustername, MAX(stud.classname) AS max_classname,",
                    "MAX(stud.classname) AS max_classname,",
                    "ARRAY_AGG(DISTINCT lvl.base_id) AS lvlbase_id_arr",

                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                    "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",

                    "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                    "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                    "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                    "WHERE ey.id = %(ey_id)s::INT AND school.id = %(sch_id)s::INT AND dep.id = %(dep_id)s::INT",
                    "AND NOT grd.tobedeleted AND NOT studsubj.tobedeleted",
                    "AND grd.examperiod = %(examperiod)s::INT",

                    "GROUP BY subj.id, subjbase.code, subj.name",

                    "ORDER BY LOWER(subj.name)"
                    ]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            subject_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))
            logger.debug('sql: ' + str(sql))

        # - add full name to rows, and array of id's of auth
        """
        if subject_rows:
            for row in subject_rows:
                first_name = row.get('firstname')
                last_name = row.get('lastname')
                prefix = row.get('prefix')
                full_name = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)
                row['fullname'] = full_name if full_name else None
        """
        return subject_rows

    def get_grade_rows (self, examyear, school, department, examperiod, examtype):

        # note: don't forget to filter deleted = false!! PR2021-03-15
        # grades that are not published are only visible when 'same_school'
        # note_icon is downloaded in separate call

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ----- get_grade_rows -----')

        sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk, 'experiod': examperiod}
        sql_list = ["SELECT stud.lastname, stud.firstname, stud.prefix, stud.examnumber,",
                    "lvl.id AS level_id, lvl.base_id AS levelbase_id, lvl.abbrev AS lvl_abbrev,",
                    "subj.id AS subj_id, subjbase.code AS subj_code, subj.name AS subj_name",

                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                    "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",

                    "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                    "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                    "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                    "WHERE ey.id = %(ey_id)s::INT",
                    "AND school.id = %(sch_id)s::INT",
                    "AND dep.id = %(dep_id)s::INT",
                    "AND NOT grd.tobedeleted AND NOT studsubj.tobedeleted",
                    "AND grd.examperiod = %(experiod)s::INT",

                    "ORDER BY LOWER(subj.name), LOWER(stud.lastname), LOWER(stud.firstname)"
                    ]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            grade_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))
            logger.debug('sql: ' + str(sql))

        # - add full name to rows, and array of id's of auth
        if grade_rows:
            for row in grade_rows:
                first_name = row.get('firstname')
                last_name = row.get('lastname')
                prefix = row.get('prefix')
                full_name = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)
                row['fullname'] = full_name if full_name else None

        return grade_rows
# - end of GetEx3infoView


@method_decorator([login_required], name='dispatch')
class DownloadPublishedFile(View):  # PR2021-02-07

    def post(self, request):
        logger.debug('xxxxxxxxxxxx  ============= DownloadPublishedFile ============= ')
        pk_int = 0
        logger.debug(' ============= DownloadPublishedFile ============= ')
        logger.debug('pk_int: ' + str(pk_int))
        # download published pdf file from server

        response = None
        # <PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated
        has_permit = False
        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user
            # TODO set permit properly
            has_permit = True
            if has_permit:
                # - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

                # - get upload_dict from request.POST
                upload_json = request.POST.get('upload', None)
                if upload_json:
                    upload_dict = json.loads(upload_json)
                    logger.debug('upload_dict' + str(upload_dict))
                    published_pk = upload_dict.get('published_pk')
                    if published_pk:
                        published = sch_mod.Published.objects.get_or_none(pk=published_pk)
                        logger.debug('published' + str(published))
                        if published:
                            file_name = published.filename
                            if file_name:

                                logger.debug('file_name: ' + str(file_name))
                                # file_dir = ''.join((awpr_settings.AWS_LOCATION, '/published/'))
                                file_dir = awpr_settings.STATICFILES_MEDIA_DIR
                                file_path = ''.join((file_dir, file_name))
                                logger.debug('file_path: ' + str(file_path))

                                if path.exists(file_path):
                                    logger.debug('file_path exists: ')
                                    # gives UnicodeDecodeError : 'charmap' codec can't decode byte 0x9d in position 656:
                                    # see https://stackoverflow.com/questions/9233027/unicodedecodeerror-charmap-codec-cant-decode-byte-x-in-position-y-character
                                    # and https://www.edureka.co/community/51644/python-unicodedecodeerror-codec-decode-position-invalid
                                    # was: with open(file_path, 'r') as pdf:

                                    with open(file_path, 'rb') as file_object:
                                        logger.debug("Name of the file: " + str(file_object.name))
                                        logger.debug('pdf: ' + str(file_object) + ' ' + str((type(file_object))) )
                                        read_data = file_object.read()




                                        response = HttpResponse(read_data, content_type='application/pdf')
                                        response['Content-Disposition'] = 'attachment; filename="some_file.pdf"'

                                        logger.debug('response: ' + str(response))
                                        return response

                                    #try:
                                        # fs = FileSystemStorage()
                                        #fs = default_storage
                                        #if fs.exists(file_name):
                                        #    logger.debug('file_name' + str(file_name))
                                        #    with open(file_name) as pdf:
                                       #         response = HttpResponse(pdf, content_type='application/pdf')
                                        #        response['Content-Disposition'] = "attachment; filename='" + file_name + ".pdf'"
                                        #        return response
                                       # else:
                                       #     return HttpResponseNotFound('The requested pdf was not found in our server.')
                                    #except:
                                    #    raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of DownloadPublishedFile



@method_decorator([login_required], name='dispatch')
class DownloadEx3View(View):  # PR2021-10-07

    def get(self, request, list):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= DownloadEx3View ============= ')
            if logging_on:
                logger.debug('     list: ' + str(list))

        # TODO for uploading Exs with signatures:
        # - give each Ex3 a sequence, print under Ex3 in box
        # - create table mapped_ex3 with field Ex3 sequence and field with all grade_pks of that Ex3
        # when uploading: user types Ex3 number when uploading Ex3,
        # Awp links grades of that Ex3 to the uploaded file
        # in table mapped_ex3: add column with href to the uploaded Ex3 form

        # function creates, Ex3 pdf file based on settings in list and usersetting

        response = None

        if request.user and request.user.country and request.user.schoolbase and list:
            upload_dict = json.loads(list)

            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)
            islexschool = sel_school.islexschool

# - get selected examperiod from usersettings
            sel_examperiod, sel_examtype_NIU, sel_subject_pk_NIU = dl.get_selected_experiod_extype_subject_from_usersetting(request)

            if logging_on:
                logger.debug('sel_examperiod: ' + str(sel_examperiod))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))

            if sel_examperiod and sel_school and sel_department:
                sel_layout = upload_dict.get('sel_layout')
                lvlbase_pk_list = upload_dict.get('lvlbase_pk_list', [])
                subject_list = upload_dict.get('subject_list', [])

# - save sel_layout and lvlbase_pk_list and in usersetting
                setting_dict = {'sel_layout': sel_layout, 'lvlbase_pk_list': lvlbase_pk_list}
                acc_view.set_usersetting_dict(c.KEY_EX3, setting_dict, request)

# - get exform_text from examyearsetting
                exform_text = awpr_lib.get_library(sel_examyear, ['exform', 'ex3'])

# +++ get ex3_grade_rows
                ex3_dict = self.get_ex3_grade_rows(sel_examyear, sel_school, sel_department, upload_dict, sel_examperiod)
                """
                ex3_dict: { 
                    2168: { 'subj_name': 'Culturele en Artistieke Vorming', 
                            'student_list': [
                                ('V021', ' Albertus, Dinaida L.J.'), 
                                ('A17', ' Angela, Jean-Drianelys N.E.'),
                                ('A06', ' Doran, Tianny L.'), 
                """

        # - get arial font
                try:
                    filepath = awpr_settings.STATICFILES_FONTS_DIR + 'arial220815.ttf'
                    ttfFile = TTFont('Arial', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

        # - get Palace_Script_MT font - for testing - it works 2021-10-14
                """
                try:
                    filepath = awpr_settings.STATICFILES_FONTS_DIR + 'Palace_Script_MT.ttf'
                    ttfFile = TTFont('Palace_Script_MT', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))
                """
                # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

                # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                #temp_file = tempfile.TemporaryFile()
                # canvas = Canvas(temp_file)

                buffer = io.BytesIO()
                canvas = Canvas(buffer)

                # PR2022-05-05 debug Oscap Panneflek Vpco lines not printing on Ex3
                # turn off setLineWidth (0)
                # canvas.setLineWidth(0)

                max_rows = 30  # was:  24
                line_height = 6.73 * mm  # was:  8 * mm

                for key, page_dict in ex3_dict.items():
                    student_list = page_dict.get('students', [])
                    if logging_on:
                        logger.debug('page_dict: ' + str(page_dict))
                        logger.debug('student_list: ' + str(student_list))

                    if student_list:
                        row_count = len(student_list)
                        pages_not_rounded = row_count / max_rows
                        pages_integer = int(pages_not_rounded)
                        pages_roundup = pages_integer + 1 if (pages_not_rounded - pages_integer) else pages_integer

                        for page_index in range(0, pages_roundup):  # range(start_value, end_value, step), end_value is not included!
                            first_row_of_page = page_index * max_rows
                            last_row_of_page_plus_one = (page_index + 1) * max_rows
                            row_range = [first_row_of_page, last_row_of_page_plus_one]
                            draw_Ex3(canvas, sel_examyear, sel_school, islexschool, sel_department, sel_examperiod, exform_text,
                                     page_dict, student_list, row_range, line_height, page_index, pages_roundup, user_lang)
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
                response['Content-Disposition'] = 'inline; filename="Ex3_voorblad.pdf"'
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
# - end of DownloadEx3View

    def get_ex3_grade_rows (self, examyear, school, department, upload_dict, examperiod):

        # note: don't forget to filter deleted = false!! PR2021-03-15
        # grades that are not published are only visible when 'same_school'
        # note_icon is downloaded in separate call

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ----- get_ex3_grade_rows -----')
            logger.debug('upload_dict: ' + str(upload_dict))

        # upload_dict: {'subject_list': [2206, 2165, 2166], 'sel_layout': 'level', 'level_list': [86, 85]}

        # values of sel_layout are:"none", "level", "class", "cluster"
        # "none" or None: all students of subject on one form
        # "level:" seperate form for each leeerweg
        #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
        #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

        lvlbase_pk_list = upload_dict.get('lvlbase_pk_list', [])
        subject_list = upload_dict.get('subject_list', [])
        sel_layout = upload_dict.get('sel_layout')

        sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk,
                    'lvlbase_pk_arr': lvlbase_pk_list, 'subj_arr': subject_list, 'experiod': examperiod}
        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))

        ex3_dict = {}

        level_filter = "AND lvl.base_id IN ( SELECT UNNEST( %(lvlbase_pk_arr)s::INT[]))" if lvlbase_pk_list else ""
        subject_filter = "AND subj.id IN ( SELECT UNNEST( %(subj_arr)s::INT[]))" if subject_list else ""

        logger.debug('subject_filter: ' + str(subject_filter))
        sql_list = ["SELECT subj.id AS subj_id, subjbase.code AS subj_code, subj.name AS subj_name,",
                    "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, ",
                    "stud.classname, cl.name AS cluster_name,",
                    "stud.level_id, lvl.name AS lvl_name",

                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                    "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",

                    "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                    "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                    "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                    "LEFT JOIN subjects_cluster AS cl ON (cl.id = studsubj.cluster_id)",

                    "WHERE ey.id = %(ey_id)s::INT AND school.id = %(sch_id)s::INT AND dep.id = %(dep_id)s::INT",
                    level_filter,
                    subject_filter,
                    "AND NOT grd.tobedeleted AND NOT studsubj.tobedeleted",
                    "AND grd.examperiod = %(experiod)s::INT",
                    "ORDER BY LOWER(subj.name), LOWER(stud.lastname), LOWER(stud.firstname)"
                    ]
        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            grade_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))
            logger.debug('sql: ' + str(sql))

# - add full name to rows, and array of id's of auth
        if grade_rows:
            for row in grade_rows:
                subj_pk = row.get('subj_id')
                subj_name = row.get('subj_name', '---')
                classname = row.get('classname', '---')
                cluster_name = row.get('cluster_name', '---')
                level_id = row.get('level_id')
                lvl_name = row.get('lvl_name', '---')
                examnumber = row.get('examnumber', '---')
                first_name = row.get('firstname')
                last_name = row.get('lastname')
                prefix = row.get('prefix')
                full_name = stud_fnc.get_lastname_firstname_initials(last_name, first_name, prefix)

                if sel_layout == "level":
                    key = (subj_pk, level_id)
                elif sel_layout == "class":
                    key = (subj_pk, classname)
                elif sel_layout == "cluster":
                    key = (subj_pk, cluster_name)
                else:
                    sel_layout = None
                    key = subj_pk
                if key not in ex3_dict:
                    ex3_dict[key] = {'subject': subj_name}
                    if sel_layout == "level":
                        ex3_dict[key][sel_layout] = lvl_name
                    elif sel_layout == "class":
                        ex3_dict[key][sel_layout] = classname
                    elif sel_layout == "cluster":
                        ex3_dict[key][sel_layout] = cluster_name
                    ex3_dict[key]['students'] = []

                student_list = ex3_dict[key].get('students', [])
                student_list.append((examnumber, full_name))

        if logging_on:
            logger.debug('ex3_dict: ' + str(ex3_dict))

        return ex3_dict

# - end of DownloadEx3View


@method_decorator([login_required], name='dispatch')
class DownloadEx3BackpageView(View):  # PR2022-02-26

    def get(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= DownloadEx3BackpageView ============= ')

        response = None

        if request.user and request.user.country and request.user.schoolbase and list:

            # - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)
            islexschool = sel_school.islexschool

            if sel_school:

# - get exform_text from examyearsetting
                exform_text = awpr_lib.get_library(sel_examyear, ['exform', 'ex3'])

        # - get arial font
                try:
                    filepath = awpr_settings.STATICFILES_FONTS_DIR + 'arial220815.ttf'
                    ttfFile = TTFont('Arial', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                buffer = io.BytesIO()
                canvas = Canvas(buffer)

                canvas.setLineWidth(0)

                draw_Ex3backpage(canvas, sel_school, islexschool, exform_text)

                canvas.save()
                pdf = buffer.getvalue()

                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="Ex3_achterblad.pdf"'

                response.write(pdf)

        #except Exception as e:
       #     logger.error(getattr(e, 'message', str(e)))
       #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of DownloadEx3View


@method_decorator([login_required], name='dispatch')
class GradeDownloadEx2aViewXXX(View):  # PR2021-01-24

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeDownloadEx2aView ============= ')
        # function creates, Ex2A pdf file based on settings in usersetting

        response = None
        #try:

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
           # TODO was:  sel_examyear, sel_school, sel_department, is_locked, \
                #examyear_published, school_activated, requsr_same_schoolNIU = \
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)

# - get selected examperiod, examtype, subject_pk from usersettings
            sel_examperiod, sel_examtype, sel_subject_pk = dl.get_selected_experiod_extype_subject_from_usersetting(request)

            if logging_on:
                logger.debug('sel_examperiod: ' + str(sel_examperiod))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))
                logger.debug('sel_subject_pk: ' + str(sel_subject_pk))

            if sel_examperiod and sel_school and sel_department and sel_subject_pk:
                sel_subject = subj_mod.Subject.objects.get_or_none(
                    pk=sel_subject_pk,
                    examyear=sel_examyear
                )
                if logging_on:
                    logger.debug('sel_subject: ' + str(sel_subject))

# +++ get selected grade_rows
                auth_dict = {}
                setting_dict = {c.KEY_SEL_SCTBASE_PK: {c.KEY_SEL_SUBJBASE_PK: sel_subject.base_id}}

                grade_rows = gr_vw.create_grade_rows(
                    sel_examyear_pk=sel_examyear.pk,
                    sel_schoolbase_pk=sel_school.base_id,
                    sel_depbase_pk=sel_department.base_id,
                    sel_examperiod=sel_examperiod,
                    setting_dict=setting_dict,
                    request=request,
                    auth_dict=auth_dict
                    )

                # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

                # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                #temp_file = tempfile.TemporaryFile()
                # canvas = Canvas(temp_file)

                buffer = io.BytesIO()
                canvas = Canvas(buffer)

                # Start writing the PDF here
                draw_Ex2A(canvas, sel_examyear, sel_school, sel_department, sel_subject, sel_examperiod, sel_examtype, grade_rows)
                #test_pdf(canvas)
                # testParagraph_pdf(canvas)

                if logging_on:
                    logger.debug('end of draw_Ex2A')

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


def testParagraph_pdf(canvas):
    styleSheet = getSampleStyleSheet()
    logger.debug('styleSheet: ' + str(styleSheet) + ' ' + str(type(styleSheet)))
    style = styleSheet['BodyText']
    logger.debug('style: ' + str(style) + ' ' + str(type(style)))
    P = Paragraph('This is a very silly example', style)
    """
    P: Paragraph(
        'caseSensitive': 1
        'encoding': 'utf8'
        'text': 'This is a very silly example'
        'frags': [ParaFrag(__tag__='para', bold=0, fontName='Helvetica', fontSize=10, greek=0, italic=0, link=[], rise=0, text='This is a very silly example', textColor=Color(0,0,0,1), us_lines=[])]
        'style': <ParagraphStyle 'BodyText'>
        'bulletText': None
        'debug': 0
    ) #Paragraph <class 'reportlab.platypus.paragraph.Paragraph'>
    """

    logger.debug('P: ' + str(P) + ' ' + str(type(P)))
    aW = 460
    # available width and height
    aH = 800
    w,h = P.wrap(aW, aH)
    # find required space
    if w<=aW and h<=aH:
        P.drawOn(canvas,0,aH)
        aH = aH - h
        # reduce the available height


def test_pdf(canvas):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch

    # pagesize A4  = (595.27, 841.89) points, 1 point = 1/72 inch
    PAGE_HEIGHT =  841.89  #  rl_config.defaultPageSize[1]
    PAGE_WIDTH = 595.27  #rl_config.defaultPageSize[0]

    styles = getSampleStyleSheet()

    Title = "Hello world"
    pageinfo = "platypus example"
    def myFirstPage(canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Bold',16)
        canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-108, Title)
        canvas.setFont('Times-Roman',9)
        canvas.drawString(inch, 0.75 * inch, "First Page / %s" % pageinfo)
        canvas.restoreState()

    def myLaterPages(canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman',9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, pageinfo))
        canvas.restoreState()

    def go():
        doc = SimpleDocTemplate("phello.pdf")
        Story = [Spacer(1,2*inch)]
        style = styles["Normal"]
        for i in range(100):
            bogustext = ("This is Paragraph number %s.  " % i) *20
            p = Paragraph(bogustext, style)
            Story.append(p)
            Story.append(Spacer(1,0.2*inch))
        doc.build(Story, onFirstPage=myFirstPage, onLaterPages=myLaterPages)


def draw_Ex3(canvas, sel_examyear, sel_school, islexschool, sel_department, sel_examperiod, exform_text,
             page_dict, student_list, row_range, line_height, page_index, pages, user_lang):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_Ex3 -----')
        logger.debug('page_dict: ' + str(page_dict))

    # page_dict: {
    # ' subj_name': 'Economie',


    # ' class': '4A3',
    #   'cluster': None,
    #   'levvl': 'Praktisch Kadergerichte Leerweg',
    #   'student_list': [('A33', 'Alberto, Giorelle L.'),

# - set the corners of the rectangle
    top, right, bottom, left = 287 * mm, 200 * mm, 12 * mm, 10 * mm
    #width = right - left  # 190 mm
    #height = top - bottom  # 275 mm
    border = [top, right, bottom, left]
    coord = [left, top]
    col_width_list = (20, 55, 35, 18, 18, 22, 22)

# - draw border around page
    draw_page_border(canvas, border)

# - draw 'Ex.3' in upper right cormner
    draw_ex_box(canvas, border, exform_text)

    examyear_code = str(sel_examyear.code)
    school_name = sel_school.name
    dep_abbrev = sel_department.abbrev

    subj_name = page_dict.get('subject', '---')
    level_name = page_dict.get('level')
    class_name = page_dict.get('class')
    cluster_name = page_dict.get('cluster')

# get article and examen for normal / lex school
    key_article = 'lex_article' if islexschool else 'eex_article'
    key_examen = 'landsexamen' if islexschool else 'eindexamen'
    examen_txt_list = [
        exform_text.get(key_examen, '-'),
        dep_abbrev,
        exform_text.get('in_het_examenjaar', '-'),
        examyear_code
    ]
# - add exam period for second and third exam period
    if sel_examperiod > 1:
        examperiod_txt = '  -  ' + c.get_examperiod_caption(sel_examperiod)
        examen_txt_list.append(examperiod_txt)
    examen_txt = ' '.join(examen_txt_list)

# - draw page header
    text_list = [
        (exform_text.get('minond', '-'), ""),
        (exform_text.get('title', '-'), ""),
        (exform_text.get(key_article, '-'), ""),
        (exform_text.get('voor_het_vak', '-'), subj_name),
        (examen_txt, ""),
    ]
    # skip school when islexschool
    if not islexschool:
        text_list.append((exform_text.get('naam_school', '-'), school_name))

    if level_name:
        text_list.append(("Leerweg:", level_name))
    elif class_name:
        text_list.append(("Klas:", class_name))
    elif cluster_name:
        text_list.append(("Cluster:", cluster_name))

    if logging_on:
        logger.debug('text_list: ' + str(text_list))

    draw_Ex3_page_header(canvas, coord, text_list)

# - draw column header
    header_height = 17 * mm
    draw_Ex3_colum_header(canvas, border, coord, header_height, col_width_list, exform_text)

# - draw vertical lines of columns
    x = coord[0]
    y_top = coord[1]
    y_top_minus = y_top - 7 * mm
    y_bottom = bottom + 10 * mm
    coord[1] = y_top - header_height

    for index in range(0, len(col_width_list) - 1):  # range(start_value, end_value, step), end_value is not included!
        w = col_width_list[index]
        x += w * mm
        y1_mod = y_top_minus if index == 3 else y_top
        canvas.line(x, y1_mod, x, y_bottom)

# - loop through students
    x = coord[0]
    y = coord[1]

    canvas.setFont('Arial', 8, leading=None)
    # PR2022-05-05 debug Oscap Panneflek Vpco lines not printing on Ex3
    # turn off grey lines
    #  canvas.setStrokeColorRGB(0.5, 0.5, 0.5)

    for index in range(row_range[0], row_range[1]):  # range(start_value, end_value, step), end_value is not included!
        row_data = None
        if index < len(student_list):
            row_data = student_list[index]
        draw_Ex3_row(canvas, row_data, left, right, y_bottom, coord, line_height, col_width_list)

# - draw page footer
    # TODO
    # sequence is number to be added to pages to be used when uploading Ex3 forms with signatures
    sequence = 0
    draw_Ex3_page_footer(canvas, border, coord, exform_text, page_index, pages, sequence, user_lang)

# - end of draw_Ex3


def draw_page_border(canvas, border):
    # - draw border around page

    #  border = [top, right, bottom, left]
    top, right, bottom, left = border[0], border[1], border[2], border[3]
    width = right - left  # 190 mm
    height = top - bottom  # 275 mm

    canvas.rect(left, bottom, width, height)

# - end of draw_page_border_plus_exbox


def draw_ex_box(canvas, border, exform_text):
    # - draw border around page

    ex_code = exform_text.get('ex_code', '---')

    #  border = [top, right, bottom, left]
    top = border[0]
    right = border[1]

# - draw rectangle around 'EX.3' text
    # draw a rectangle
    # canvas.rect(x, y, width, height, stroke=1, fill=0)
    #canvas.rect(right - 16 * mm, top - 12 * mm, 16 * mm, 12 * mm)
    canvas.line(right - 16 * mm, top, right - 16 * mm, top - 12 * mm)
    canvas.line(right - 16 * mm, top - 12 * mm , right, top - 12 * mm )

    # add 'EX.3' in the right upper corner
    canvas.drawString(right - 13 * mm, top - 8 * mm, ex_code)
# - end of draw_ex_box


def draw_Ex3_page_header(canvas, coord, text_list):
    # loop trhrough rows of page_header

    line_count = len(text_list)
    line_height = 7 * mm
    padding_left = 4 * mm

    x = coord[0] + padding_left
    y = coord[1]

    for index in range(0, line_count):  # range(start_value, end_value, step), end_value is not included!
        y -= line_height
        label = text_list[index][0]
        text = text_list[index][1]
        logger.debug('label: ' + str(label))
        logger.debug('text: ' + str(text))

# draw label
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
        canvas.setFont('Times-Bold', 11, leading=None)
        canvas.setFillColor(colors.HexColor("#000000"))
        canvas.drawString(x, y, label)

# draw text (schoolname etc
        if text:
            canvas.setFont('Arial', 11, leading=None)
            canvas.setFillColor(colors.HexColor("#000080"))
            canvas.drawString(x + 40 * mm, y, text)

    coord[1] = y
# - end of draw_Ex3_page_header


def draw_Ex3_page_footer(canvas, border, coord, exform_text, page_index, pages, sequence, user_lang):
    # PR2021-10-08
    footer_height = 10 * mm
    padding_left = 4 * mm
    padding_bottom = 2 * mm

    #  border = [top, right, bottom, left]
    right = border[1]
    bottom = border[2]
    x = coord[0] + padding_left
    y = bottom + padding_bottom
    y_top = bottom + footer_height

# - draw horizontal lines above page footer
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.line(border[3], y_top, border[1], y_top)

    canvas.setFont('Arial', 8, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))

# - column 0 'Examennummer en naam dienen in overeenstemming te zijn met formulier EX.1.'
    canvas.drawString(x, y, exform_text.get('footer_01', '-'))  # 'col_00_00': 'Examennr.'

    today_dte = af.get_today_dateobj()
    today_formatted = af.format_DMY_from_dte(today_dte, user_lang, True)  # True = month_abbrev
    canvas.drawRightString(right - padding_bottom, y, today_formatted)

    if pages > 1:
        page_txt = ' '.join(('Pagina', str(page_index + 1), 'van', str(pages)))
        canvas.drawString(right - 60 * mm, y, page_txt)

    # TODO add number to pages to be used when uploading Ex3 fiorms wit h signatures
    #canvas.drawRightString(right - 2 * mm, bottom - 4 * mm, str(sequence))


# - end of draw_Ex3_page_footer


def draw_Ex3_colum_header(canvas, border, coord, header_height, col_width_list, exform_text):

    line_height = 4 * mm

    #  border = [top, right, bottom, left]
    top, right, bottom, left = border[0], border[1], border[2], border[3]
    x = coord[0]
    y = coord[1] - 4 * mm
    coord[1] = y

# - draw horizontal lines above and below column header
    canvas.line(left, y, right, y)

    y1 = y - header_height
    canvas.line(left, y1, right, y1)

    canvas.setFont('Arial', 8, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))

    y_txt1 = y - line_height - 1 * mm
    y_txt2 = y_txt1 - line_height
    y_txt3 = y_txt2 - line_height

# - column 0 'Examennr.'
    col_index = 0
    x_center = x + col_width_list[col_index] * mm / 2
    canvas.drawCentredString(x_center, y_txt1, exform_text.get('col_00_00', '-'))  # 'col_00_00': 'Examennr.'
    canvas.drawCentredString(x_center, y_txt2, exform_text.get('col_00_01', '-'))  # ''col_00_01': '1)'

# - column 1 'Naam en voorletters van de kandidaat',
    col_index += 1
    x += col_width_list[col_index - 1] * mm
    x_center = x + col_width_list[col_index] * mm / 2
    canvas.drawCentredString(x_center, y_txt1,
                             exform_text.get('col_01_00', '-'))  # 'col_01_00': 'Naam en voorletters van de kandidaat',
    canvas.drawCentredString(x_center, y_txt2,
                             exform_text.get('col_01_01', '-'))  # 'col_01_01': '(in alfabetische volgorde)',

# - column 2 'Naam en voorletters van de kandidaat',
    col_index += 1
    x += col_width_list[col_index - 1] * mm
    x_center = x + col_width_list[col_index] * mm / 2
    canvas.drawCentredString(x_center, y_txt1, exform_text.get('col_02_00', '-'))  # 'col_02_00': 'Handtekening kandidaat'
    canvas.drawCentredString(x_center, y_txt2, exform_text.get('col_02_01', '-'))  # 'col_02_01': '(bij aanvang)',



# - column 3 'Aantal ingeleverde bladen',
    col_index += 1
    x += col_width_list[col_index - 1] * mm
    x_center = x + (col_width_list[col_index] + col_width_list[col_index + 1]) * mm / 2
    x_right = x + (col_width_list[col_index] + col_width_list[col_index + 1]) * mm
    canvas.drawCentredString(x_center, y_txt1, exform_text.get('col_03_00', '-'))  # 'col_03_00': 'Aantal ingeleverde bladen'

    # horizontal line under text
    canvas.line(x, y_txt1 - 2 * mm, x_right, y_txt1 - 2 * mm)

# - column 3 'uitwerkbladen',
    x_center = x + col_width_list[col_index] * mm / 2
    canvas.drawCentredString(x_center, y_txt2 - 2 * mm, exform_text.get('col_03_01', '-'))  # 'col_03_01': 'uitwerk-',
    canvas.drawCentredString(x_center, y_txt3 - 2 * mm, exform_text.get('col_03_02', '-'))  # 'col_03_02': 'bladen',

# - column 4 'folio bladen',
    col_index += 1
    x += col_width_list[col_index - 1] * mm
    x_center = x + col_width_list[col_index] * mm / 2
    canvas.drawCentredString(x_center, y_txt2 - 2 * mm, exform_text.get('col_04_01', '-'))  # 'col_04_01': 'folio',
    canvas.drawCentredString(x_center, y_txt3 - 2 * mm, exform_text.get('col_04_02', '-'))  # 'col_04_02': 'bladen',

# - column 5 'Tijdstip van inlevering',
    col_index += 1
    x += col_width_list[col_index - 1] * mm
    x_center = x + col_width_list[col_index] * mm / 2
    canvas.drawCentredString(x_center, y_txt1, exform_text.get('col_05_00', '-'))  # 'col_05_00': 'Tijdstip van',
    canvas.drawCentredString(x_center, y_txt2, exform_text.get('col_05_01', '-'))  # ''col_05_01', 'inlevering'

# - column 6 'Paraaf surveillant',
    col_index += 1
    x += col_width_list[col_index - 1] * mm
    x_center = x + col_width_list[col_index] * mm / 2
    canvas.drawCentredString(x_center, y_txt1, exform_text.get('col_06_00', '-'))  # 'col_06_00', 'Paraaf'
    canvas.drawCentredString(x_center, y_txt2, exform_text.get('col_06_01', '-'))  # ''col_06_01', 'surveillant'
    canvas.drawCentredString(x_center, y_txt3, exform_text.get('col_06_02', '-'))  # 'col_06_02', '(voor inlevering)'
# - end of draw_Ex3_colum_header



def draw_Ex3_row(canvas, row, left, right, y_bottom, coord, line_height, col_width_list):

    x = left
    y = coord[1] - line_height
    pl = 4 * mm
    pb = 2 * mm

    try:
        #logger.debug('y: ' + str(y) + ' ' + str(type(y)))
        #logger.debug('tab_list: ' + str(tab_list) + ' ' + str(type(tab_list)))
        # col_width = (25, 65, 17, 22, 22, 22, 17)  # last col is 17 mm
        # draw empty row when row is None, to draw lines till end of page
        if row is not None:
            examnumber = row[0] or '---'
            # canvas.drawString(tab_list[0], y, examnumber)
            # canvas.drawCentredString(x + pl + pb, y + pb, examnumber)

            # PR2022-05-02 Hans Vlinkervleugel KAP: uses id as examnumbers, outline not good
            pl_exnr = pb if len(examnumber) > 8 else pl
            canvas.drawString(x + pl_exnr, y + pb, examnumber)

            x += col_width_list[0] * mm
            fullname = row[1] or '---'
            canvas.drawString(x + pl, y + pb, fullname)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        logger.error('row: ', str(row))

    #canvas.line(left, y - 1.25 * mm, right, y - 1.25 * mm)
    # skip lines that are in the footer
    if y > y_bottom:
        canvas.line(left, y, right, y)

    coord[1] = y
    #logger.debug('end of draw_Ex2A_line:')
# - end of draw_Ex3_row


def draw_Ex3backpage(canvas, sel_school, islexschool, exform_text):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_Ex3backpage -----')


    #if logging_on:
    #    logger.debug('exform_text: ' + str(exform_text))
    dots_63 = '.' * 63
    dots_45 = '.' * 45

# - set the corners of the rectangle
    top, right, bottom, left = 287 * mm, 200 * mm, 12 * mm, 10 * mm
    #width = right - left  # 190 mm
    #height = top - bottom  # 275 mm
    border = [top, right, bottom, left]
    coord = [left, top]

    canvas.setLineWidth(0)

# - draw 'Ex.3' in upper right cormner
    draw_ex_box(canvas, border, exform_text)

# - draw page header
    # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
    canvas.setFont('Times-Bold', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))

    line_height = 6 * mm
    padding_left = 4 * mm
    padding_bottom = 2 * mm

    x = coord[0] + padding_left
    y = coord[1]
    y -= line_height
    text = exform_text.get('minond', '-')
    canvas.drawString(x, y, text)

# - PROCES-VERBAAL
    canvas.setFont('Times-Bold', 16, leading=None)
    x_center = (right + left) / 2
    y -= line_height * 3
    text = exform_text.get('proces_verbaal', '-')
    canvas.drawCentredString(x_center, y, text.upper())

# - PROCES-VERBAAL VAN TOEZICHT
    canvas.setFont('Times-Bold', 11, leading=None)
    y -= line_height * 2
    text = exform_text.get('title', '-')
    canvas.drawString(x, y, text.upper())

# - Artikel 28, Landsbesluit eindexamens
    # get article and examen for normal / lex school
    canvas.setFont('Times-Roman', 11, leading=None)
    y -= line_height
    key_article = 'lex_article' if islexschool else 'eex_article'
    text = exform_text.get(key_article, '-')
    canvas.drawString(x, y, text)

# - School
    # skip school when islexschool
    if not islexschool:
        y -= line_height  * 1.5
        canvas.drawString(x, y, exform_text.get('naam_school', '-'))
        canvas.setFont('Arial', 11, leading=None)
        canvas.setFillColor(colors.HexColor("#000080"))
        canvas.drawString(x + 40 * mm, y, sel_school.name)

# - Verloop en eventuele bijzonderheden
    canvas.setFont('Times-Roman', 11, leading=None)
    y -= line_height * 1.5
    text = exform_text.get('back_01', '-')
    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.drawString(x, y, text)

# - blank line for subject
    y -= line_height * 1.5
    text = ''.join((dots_63, dots_63, dots_63))
    canvas.drawString(x, y, text)

# - voor de groep kandidaten
    y -= line_height
    canvas.drawString(x, y, exform_text.get('back_02', '-'))

# - Indien meer dan 2 verschillende personen
    y -= line_height * 1.5
    canvas.drawString(x, y, exform_text.get('back_03', '-'))

    canvas.setStrokeColorRGB(0.5, 0.5, 0.5)

# -  ten dotted lines
    line_height = 8 * mm
    y -= line_height * 0.5
    for index in range(0, 10):  # range(start_value, end_value, step), end_value is not included!
        y -= line_height
        text = ''.join((dots_63, dots_63, dots_63))
        canvas.drawString(x, y, text)
# - ... , ...
    y -= line_height
    x_center_right = (right + x_center) / 2
    text = ''.join((dots_45, ', ', dots_45))
    canvas.drawCentredString(x_center_right, y, text)
# - (plaatsnaam)
    y -= line_height * 0.5
    x_place = (x_center_right + x_center) / 2
    canvas.drawCentredString(x_place, y, exform_text.get('back_place', '-'))
# - (datum)
    x_date = (right + x_center_right) / 2
    canvas.drawCentredString(x_date, y, exform_text.get('back_date', '-'))

# - Handtekening toezichthouders
    y -= line_height * 1.5
    canvas.drawString(x, y, exform_text.get('back_signature', '-'))

# -  five dotted lines with 'Toezicht van...
    dots_40 = '.' * 38
    y -= line_height * 0.5
    for index in range(0, 5):  # range(start_value, end_value, step), end_value is not included!
        y -= line_height
        text = '  '.join((dots_63, exform_text.get('back_from', '-'), dots_40, exform_text.get('back_till', '-'), dots_40, exform_text.get('back_hour', '-')))
        canvas.drawString(x, y, text)


# - draw page footer
    y = bottom + padding_bottom
    canvas.setFont('Times-Roman', 10, leading=None)
    canvas.drawString(x, y, exform_text.get('backfooter_01', ''))

# - end of draw_Ex3backpage


def draw_red_cross(canvas, x, y):
    # draw red cross, for outlining while designing
    canvas.setStrokeColorRGB(1, 0, 0)
    canvas.line(x, y + 5 * mm, x, y - 5 * mm)
    canvas.line(x - 5 * mm, y , x + 5 * mm, y )


def draw_Ex2A(canvas, sel_examyear, sel_school, sel_department, sel_subject, sel_examperiod, sel_examtype, grade_rows):
    #logger.debug('----- draw_Ex2A -----')
    # pagesize A4  = (595.27, 841.89) points, 1 point = 1/72 inch
    # move the origin up and to the left
    # c.translate(inch,inch)


    #filepath = awpr_settings.STATICFILES_FONTS_DIR + 'Garamond.ttf'


    #filepath = awpr_settings.STATICFILES_FONTS_DIR + 'Palace_Script_MT.ttf'
    #logger.debug('filepath: ' + str(filepath))
    #pdfmetrics.registerFont(TTFont('Palace_Script_MT', filepath))

    #c.setFont('Palace_Script_MT', 36)
    #c.drawString(10, 650, "Some text encoded in UTF-8")
    #c.drawString(10, 600, "In the Palace_Script_MT TT Font!")

    # choose some colors
    #c.setStrokeColorRGB(0.2,0.5,0.3)
    #c.setFillColorRGB(1,0,1)

    # draw a rectangle
    # canvas.rect(x, y, width, height, stroke=1, fill=0)

    canvas.setLineWidth(.5)
    # corners of the rectangle
    top, right, bottom, left = 287*mm, 200*mm, 12*mm, 10*mm
    width = right - left  # 190 mm
    height = top - bottom # 275 mm
    border = [top, right, bottom, left]
    canvas.rect(left, bottom, width, height)

    # - draw rectangle around Ex2A
    canvas.rect(right - 16 * mm, top - 12 * mm, 16 * mm, 12 * mm)

# - draw horizontal lines
    x1, x2, y = left, right, top - 45*mm
    canvas.line(x1, y, x2, y)

    x1, x2, y = left, right, top - 62*mm
    canvas.line(x1, y,x2, y)

    # verrtical lines
    x_list = (25, 65, 17, 22, 22, 22, 17) # last col is 17 mm
    x, y1, y2 = left, top - 45*mm, bottom + 40*mm

    """
        ______
      | 
     16 
     
    """

    tab_list = [left + 12 * mm,
                left + 29 * mm,
                left + 97 * mm,
                left + 116 * mm,
                left + 138 * mm,
                left + 160 * mm,
                left + 177 * mm
                ]

    for w in x_list:
        x += w*mm
        canvas.line(x, y1, x, y2)

    #logger.debug('tab_list: ' + str(tab_list) + ' ' + str(type(tab_list)))
    # canvas.setFont(psfontname, size, leading = None)
    examyear_code = str(sel_examyear.code)
    school_name = sel_school.name
    dep_abbrev = sel_department.abbrev
    subject_name = sel_subject.name
    examperiod_caption = c.get_examperiod_caption(sel_examperiod)
    examtype_caption = c.get_examtype_caption(sel_examtype)

    filepath = awpr_settings.STATICFILES_FONTS_DIR + 'arial220815.ttf'
    #logger.debug('filepath: ' + str(filepath))

    try:
        ttfFile = TTFont('Arial', filepath)
        #logger.debug('ttfFile: ' + str(ttfFile))
        pdfmetrics.registerFont(ttfFile)
    except Exception as e:
        logger.error('filepath: ' + str(filepath))
        logger.error(getattr(e, 'message', str(e)))

    canvas.setFont('Times-Bold', 11, leading=None)

    text_list = ("MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT",
                 "Lijst van cijfers",
                 "(Artikel 20 Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)",
                 "voor het vak:",
                 "EINDEXAMEN " + dep_abbrev + " in het examenjaar " + examyear_code,
                 "Naam van de school:")
    x, y = left + 5 * mm, top
    canvas.drawString(right - 13*mm, y - 8*mm, "EX.2a")
    l_b_coord = [x,y - 50*mm]

    #draw_page_header(canvas, border, text_list, school_name, subject_name)

    canvas.setFont('Arial', 8, leading=None)
    x, y = left + 2*mm, top - 50*mm
    canvas.drawString(x, y, 'Examennummer')
    canvas.drawString(x, y - 4 * mm, 'van de kandidaat')
    canvas.drawString(x + 10*mm, y - 10*mm, '1)')

    x += 30*mm
    canvas.drawString(x, y, 'Naam en voorletters van de kandidaat')
    canvas.drawString(x + 7*mm, y - 4*mm, '(in alfabetische volgorde)')
    # canvas.drawString(x + 20*mm, y - 10*mm, '2)')
    # calculate center: x + dx/2
    canvas.drawCentredString(x + 20*mm, y - 10*mm, '2)')

    x += 61*mm
    canvas.drawString(x, y, 'Cijfer SE')
    canvas.drawString(x + 4*mm, y - 10*mm, '3)')

    x += 19*mm
    canvas.drawString(x, y, 'Cijfer PE')
    canvas.drawString(x + 6*mm, y - 10*mm, '4)')

    x += 22*mm
    canvas.drawString(x, y, 'Cijfer CE')
    canvas.drawString(x + 6*mm, y - 10*mm, '5)')

    x += 22*mm
    canvas.drawString(x, y, 'Cijfer Herex')
    canvas.drawString(x + 6*mm, y - 10*mm, '6)')

    x += 20*mm
    canvas.drawString(x, y, 'Eindcijfer')
    canvas.drawString(x + 4*mm, y - 10*mm, '7)')

    y -= 16 * mm
    canvas.setStrokeColorRGB(0.5, 0.5, 0.5)

    if grade_rows:
        coord = [x, y]
        for row in grade_rows:
            draw_Ex2A_line(canvas, row, left, right, coord, tab_list)
# - end of draw_Ex2A


def draw_Ex2A_line(canvas, row, left, right, coord, tab_list):
    y = coord[1]
    try:
        #logger.debug('y: ' + str(y) + ' ' + str(type(y)))
        #logger.debug('tab_list: ' + str(tab_list) + ' ' + str(type(tab_list)))
        # col_width = (25, 65, 17, 22, 22, 22, 17)  # last col is 17 mm


        #logger.debug('left: ' + str(left))
        #logger.debug('tab_list: ' + str(tab_list[0]))

        examnumber = row['examnumber'] or '---'
        # canvas.drawString(tab_list[0], y, examnumber)
        canvas.drawCentredString(tab_list[0], y, examnumber)

        fullname = row['fullname'] or '---'
        canvas.drawString(tab_list[1], y, fullname)

        segrade = row['segrade'] or '---'
        canvas.drawString(tab_list[2], y, segrade)

        pegrade = row['pegrade'] or '---'
        canvas.drawString(tab_list[3], y, pegrade)

        cegrade = row['cegrade'] or '---'
        canvas.drawString(tab_list[4], y, cegrade)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        logger.error('row: ', str(row))

    canvas.line(left, y - 1.25 * mm, right, y - 1.25 * mm)
    coord[1] = y - 5 * mm
    #logger.debug('end of draw_Ex2A_line:')


def draw_page_headerOLD_NIU(canvas, border, label_list, text_list, school_name, subject_name):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_page_header -----')
        logger.debug('text_list: ' + str(text_list))
        """
        text_list: ('MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT', 
                    'Proces-verbaal van toezicht', 
                    '(Artikel 28 Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)', 
                    'voor het vak:', 
                    'EINDEXAMEN V.S.B.O. in het examenjaar 2022', 
                    'Naam van de school:')
        """

    # border = [top, right, bottom, left]
    # width = right - left  # 190 mm
    # height = top - bottom  # 275 mm

    left = border[3]
    width = border[1] - border[3]
    height = 48 * mm
    bottom = border[0] - height
    # canvas.setFillColorRGB(0, 0, 0.5) #  =.HexColor("#000080"),
    # add some flowables

    styleLabel = ParagraphStyle(name="ex_header", alignment=TA_LEFT, fontName="Times-Bold", fontSize=11,
                                   leading=7*mm, leftIndent=2*mm, rightIndent=2*mm)

    #logger.debug('styleLabel: ' + str(styleLabel) + ' ' + str(type(styleLabel)))
    story_label = []
    story_text = []
    for row_index, label in enumerate(label_list):
        text = text_list[row_index]
        story_label.append(Paragraph(label, styleLabel))
        story_text.append(Paragraph(text, styleLabel))

    # Frame(x1, y1, width,height, leftPadding=6, bottomPadding=6, rightPadding=6, topPadding=6, id=None, showBoundary=0)
    # (x1,y1) = lower left hand corner at coordinate (x1,y1)
    # If showBoundary is non-zero then the boundary of the frame will getdrawn at run time.
    f = Frame(left, bottom, width, height, showBoundary=0)
    f.addFromList(story_label, canvas)
    color_blue = colors.HexColor("#000080")
    #color_blue = colors.cornflowerblue

    #logger.debug('color_blue: ' + str(color_blue) + ' ' + str(type(color_blue)))
    styleData = ParagraphStyle(name="ex_data", alignment=TA_LEFT, fontName="Arial", fontSize=11,
                                   textColor=colors.HexColor("#000080"),
                                   leading=14*mm, leftIndent = 4*mm, rightIndent = 4*mm)
    #logger.debug('styleData: ' + str(styleData) + ' ' + str(type(styleData)))

    #logger.debug('subject_name: ' + str(subject_name) + ' ' + str(type(subject_name)))
    #logger.debug('school_name: ' + str(school_name) + ' ' + str(type(school_name)))
    line1 = Paragraph(subject_name, styleData)
    #logger.debug('line1: ' + str(line1) + ' ' + str(type(line1)))
    line2 = Paragraph(school_name, styleData)
    #logger.debug('line2: ' + str(line2) + ' ' + str(type(line2)))
    story2 = [line1, line2]
    #logger.debug('story2: ' + str(story2) + ' ' + str(type(story2)))

    left = left + 40*mm
    bottom = bottom - 13*mm
    width = 80*mm
    height = 40*mm
    f2 = Frame(left, bottom, width, height, showBoundary=0)
    f2.addFromList(story2, canvas)
    #logger.debug('addFromList: ' + str(f2) + ' ' + str(type(f2)))

# - end of draw_page_header

def testing():
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'

    buffer = io.BytesIO()

    p = Canvas(buffer)
    p.setFont('Helvetica-Bold', 36)

    p.setPageSize((400, 400))
    p.drawString(100, 100, "Hello world.")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


"""
class ParagraphStyle(PropertySet):    
defaults = {
    'fontName':_baseFontName, 'fontSize':10, 
    'leading':12, 
    'leftIndent':0, 'rightIndent':0, 'firstLineIndent':0, 
    'alignment':TA_LEFT, 
    'spaceBefore':0, 'spaceAfter':0, 
    'bulletFontName':_baseFontName, 'bulletFontSize':10, 'bulletIndent':0, 
    'textColor': black, 'backColor':None, 
    'wordWrap':None, 
    'borderWidth': 0, 'borderPadding': 0, 'borderColor': None, 'borderRadius': None, 
    'allowWidows': 1, 'allowOrphans': 0, 
    'textTransform':None, 
    'endDots':None, 
    'splitLongWords':1, 
    'underlineWidth': _baseUnderlineWidth, 
    'bulletAnchor': 'start', 
    'justifyLastLine': 0,  'justifyBreaks': 0, 
    'spaceShrinkage': _spaceShrinkage, 
    'strikeWidth': _baseStrikeWidth, '#stroke width
    'underlineOffset': _baseUnderlineOffset, '#fraction of fontsize to offset underlines 
    underlineGap': _baseUnderlineGap, '  #gap for double/triple underline        
    'strikeOffset': _baseStrikeOffset,  #fraction of fontsize to offset strikethrough
    'strikeGap': _baseStrikeGap,        #gap for double/triple strike        
    'linkUnderline': _platypus_link_underline,       
     #'underlineColor':  None,        
     #'strikeColor': None,        
     'hyphenationLang': _hyphenationLang, 
     'uriWasteReduce': _uriWasteReduce,        
     'embeddedHyphenation': _embeddedHyphenation,
    }

    # pagesize A4  = (595.27, 841.89) points, 1 point = 1/72 inch
    # move the origin up and to the left
    # c.translate(inch,inch)

    # filepath = awpr_settings.STATICFILES_FONTS_DIR + 'Garamond.ttf'

    # filepath = awpr_settings.STATICFILES_FONTS_DIR + 'Palace_Script_MT.ttf'
    # logger.debug('filepath: ' + str(filepath))
    # pdfmetrics.registerFont(TTFont('Palace_Script_MT', filepath))

    # c.setFont('Palace_Script_MT', 36)
    # c.drawString(10, 650, "Some text encoded in UTF-8")
    # c.drawString(10, 600, "In the Palace_Script_MT TT Font!")

    # choose some colors
    # c.setStrokeColorRGB(0.2,0.5,0.3)
    # c.setFillColorRGB(1,0,1)

    # draw a rectangle
    # canvas.rect(x, y, width, height, stroke=1, fill=0)

    #canvas.setLineWidth(.5)
    #canvas.setLineWidth(.1)


"""