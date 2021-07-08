import tempfile

from django.db import connection

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotFound, FileResponse
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import View

from datetime import date, datetime, timedelta

from subjects import views as subj_vw
from schools import functions as sch_fnc
from awpr import constants as c
from awpr import functions as af
from awpr import downloads as dl
from awpr import settings as s
from students import views as stud_vw

import xlsxwriter
import io
import logging
logger = logging.getLogger(__name__)


@method_decorator([login_required], name='dispatch')
class SchemeDownloadXlsxView(View):  # PR2021-06-28

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= SchemeDownloadXlsxView ============= ')
        # function creates, Ex1 xlsx file based on settings in usersetting
        # TODO ex form prints colums twice, and totals are not correct,
        # TODO text EINDEXAMEN missing the rest, school not showing PR2021-05-30
        response = None
        #try:
        if True:
            if request.user and request.user.country and request.user.schoolbase:
                req_user = request.user

    # - reset language
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)


    # - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if sel_examyear :
    # get text from examyearsetting
                    exform_text = af.get_exform_text(sel_examyear, ['exform'])
                    if logging_on:
                        logger.debug('exform_text: ' + str(exform_text))

    # +++ get dict of subjects of these studsubj_rows
                    scheme_rows = subj_vw.create_scheme_rows(sel_examyear, None, {})
                    subjecttype_rows = subj_vw.create_subjecttype_rows(sel_examyear)
                    schemeitem_rows = subj_vw.create_schemeitem_rows(sel_examyear)
                    if schemeitem_rows:
                        response = create_scheme_xlsx(sel_examyear, scheme_rows, subjecttype_rows, schemeitem_rows, exform_text, user_lang)

        #except:
        #    raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of SchemeDownloadXlsxView


@method_decorator([login_required], name='dispatch')
class StudsubjDownloadEx1View(View):  # PR2021-01-24

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeDownloadEx2aView ============= ')
        # function creates, Ex1 xlsx file based on settings in usersetting
        # TODO ex form prints colums twice, and totals are not correct,
        # TODO text EINDEXAMEN missing the rest, school not showing PR2021-05-30
        response = None
        #try:
        if True:
            if request.user and request.user.country and request.user.schoolbase:
                req_user = request.user

    # - reset language
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

    # - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if sel_examyear and sel_school and sel_department :

    # get text from examyearsetting
                    settings = af.get_exform_text(sel_examyear, ['exform', 'ex1'])
                    if logging_on:
                        logger.debug('settings: ' + str(settings))

    # +++ get mapped_subject_rows
                    subject_row_count, subject_pk_list, subject_code_list, level_pk_list = \
                        create_ex1_mapped_subject_rows(sel_examyear, sel_school, sel_department)
                    #  subject_pk_dict: {34: 0, 29: 1, ...} ( subject_pk: index)
                    #  subject_code_list: ['bw', 'cav', ]
                    #  index = row_count

                    if logging_on:
                        logger.debug('subject_row_count: ' + str(subject_row_count))
                        logger.debug('subject_pk_list: ' + str(subject_pk_list))
                        logger.debug('subject_code_list: ' + str(subject_code_list))
                        logger.debug('level_pk_list: ' + str(level_pk_list))

    # +++ get dict of subjects of these studsubj_rows
                    studsubj_rows = create_ex1_rows(sel_examyear, sel_school, sel_department)
                    if studsubj_rows:
                        response = create_ex1_xlsx(sel_examyear, sel_school, sel_department, settings, subject_row_count, subject_pk_list, subject_code_list, studsubj_rows, user_lang)
        #except:
        #    raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def create_ex1_xlsx(examyear, school, department, settings, subject_col_count,
                    subject_pk_list, subject_code_list, studsubj_rows, user_lang):  # PR2021-02-13
    logger.debug(' ----- create_ex1_xlsx -----')
    logger.debug('settings: ' + str(settings))

    # from https://stackoverflow.com/questions/16393242/xlsxwriter-object-save-as-http-response-to-create-download-in-django
    #logger.debug('period_dict: ' + str(period_dict))

    """
        'Regel 0:   DEPARTEMENT VAN ONDERWIJS                                                                      EX.1
        'Regel 1:   Genummerde alfabetische naamlijst van de kandidaten
        'Regel 2:   Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o. van de 23ste juni 2008,
        'Regel 3:   ter uitvoering van artikel 32, vijfde lid, van de Landsverordening voortgezet onderwijs, no. 54.
        'Regel 4:
        'Regel 5:   Inzenden vóór 1 oktober (1 exemplaar)
        'Regel 6:   Eindexamen V.S.B.O., in het schooljaar  2009
        'Regel 7:   School: Milton Peters College
        'Regel 8:
        'Regel 9:  header kolommen
        
        studsubj_row: {'id': 149, 'lastname': 'Abath', 'firstname': 'Markleyson', 'prefix': None, 
                        'idnumber': '1999112405', 'examnumber': '63', 'classname': None, 
                        'lvl_abbrev': 'PBL', 'sct_abbrev': 'tech', 
                        'subj_id_arr': [3, 4, 1, 6, 10, 15, 27, 29, 31, 35, 46]}
  
    """

    response = None

    if settings and studsubj_rows:

# ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
        title = ' '.join( ('Ex1', str(examyear), school.base.code, today_dte.isoformat() ) )
        file_name = title + ".xlsx"
        worksheet_name = str(_('Ex1'))

    # create the HttpResponse object ...
        #response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        #response['Content-Disposition'] = "attachment; filename=" + file_name

# Create an in-memory output file for the new workbook.
        output = io.BytesIO()
        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        #  book = xlsxwriter.Workbook(response, {'in_memory': True})
        book = xlsxwriter.Workbook(output)

        sheet = book.add_worksheet(worksheet_name)
        sheet.hide_gridlines(2) # 2 = Hide screen and printed gridlines

        #cell_format = book.add_format({'bold': True, 'font_color': 'red'})
        bold_format = book.add_format({'bold': True})

        # th_format.set_bg_color('#d8d8d8') #   #d8d8d8;  /* light grey 218 218 218 100%
        # or: th_format = book.add_format({'bg_color': '#d8d8d8'
        th_align_center = book.add_format({'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        th_rotate = book.add_format({'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'rotation': 90})

        th_merge = book.add_format({ 'bold': True, 'align': 'center', 'valign': 'vcenter'})
        th_merge.set_left()
        th_merge.set_bottom()

        row_align_left = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter','border': True})
        row_align_center = book.add_format({'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter','border': True})

        totalrow_align_center = book.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'border': True})
        totalrow_number = book.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'border': True})
        totalrow_merge = book.add_format({'border': True, 'align': 'right', 'valign': 'vcenter'})

# get number of columns
        # columns are (0: 'exnumber', 1: idnumber, 2: name 3: 'class' 4: level "
        # columns 5 thru 19 are subject columns. Extend number when more than 15 subjects
        is_lexschool = school.islexschool
        level_req = department.level_req
        sector_req = department.sector_req
        has_profiel = department.has_profiel

        col_count = 3  # add column exnr, idnumber, name and class
        field_width = [10, 12, 35]
        field_names = ['examnumber', 'idnumber', 'fullname']
        field_captions = ['Ex.nr.', 'ID-nummer', 'Naam en voorletters van de kandidaat\n(in alfabetische volgorde)']
        header_formats = [th_align_center, th_align_center, th_align_center]
        row_formats = [row_align_center, row_align_center, row_align_left]
        totalrow_formats = [totalrow_merge, totalrow_align_center, totalrow_align_center]
        if not is_lexschool:  # add column class, not when lex school
            col_count += 1
            field_width.append(10)
            field_names.append('classname')
            field_captions.append('Klas')
            header_formats.append(th_align_center)
            row_formats.append(row_align_center)
            totalrow_formats.append(totalrow_align_center)
        if level_req:  # add column if level_req
            col_count += 1
            field_width.append(5)
            field_names.append('lvl_abbrev')
            field_captions.append('Leer-\nweg')
            header_formats.append(th_align_center)
            row_formats.append(row_align_center)
            totalrow_formats.append(totalrow_align_center)
        if sector_req:  # add column if sector_req ( is always the case
            col_count += 1
            field_width.append(7)
            caption = 'Profiel' if has_profiel else 'Sector'
            field_names.append('sct_abbrev')
            field_captions.append(caption)
            header_formats.append(th_align_center)
            row_formats.append(row_align_center)
            totalrow_formats.append(totalrow_align_center)

        first_subject_column = col_count
        subject_length = len(subject_code_list)
        subject_col_width = 2.14
        for x in range(0, subject_length):  # range(start_value, end_value, step), end_value is not included!
            field_width.append(subject_col_width)
            subject_code = subject_code_list[x] if subject_code_list[x] else ''
            subject_pk = subject_pk_list[x]
            field_captions.append(subject_code)
            field_names.append(subject_pk)
            header_formats.append(th_rotate)
            row_formats.append(row_align_center)
            totalrow_formats.append(totalrow_number)

            col_count += 1

        if subject_length < 15:
            for x in range(subject_length, 15):  # range(start_value, end_value, step), end_value is not included!
                field_width.append(subject_col_width)
                subject_code = ''
                subject_pk = 0
                field_captions.append(subject_code)
                field_names.append(subject_pk)
                header_formats.append(th_rotate)
                row_formats.append(row_align_center)
                totalrow_formats.append(totalrow_number)

            col_count += 1

        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

    # --- title row
        # was: sheet.write(0, 0, str(_('Report')) + ':', bold)
        sheet.write(0, 0, settings['minond'], bold_format)
        sheet.write(1, 0, settings['title'], bold_format)

        lb_rgl01_key = 'lex_lb_rgl01' if school.islexschool else 'eex_lb_rgl01'
        lb_rgl02_key = 'lex_lb_rgl02' if school.islexschool else 'eex_lb_rgl02'
        sheet.write(2, 0, settings[lb_rgl01_key], bold_format)
        sheet.write(3, 0, settings[lb_rgl02_key], bold_format)

        sheet.write(5, 0, settings['submit_before'], bold_format)
        lb_ex_key = 'lex' if school.islexschool else 'eex'
        sheet.write(6, 0, settings[lb_ex_key], bold_format)
        lb_school_key = 'school' if school.islexschool else 'school'
        sheet.write(7, 0, settings[lb_school_key], bold_format)

# - put Ex1 in right upper corner
        #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        sheet.merge_range(0, col_count - 5, 1, col_count -1, 'EX.1', th_merge)

# ---  table header row
        row_index = 9
        for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
            sheet.write(row_index, i, field_captions[i], header_formats[i])

        if len(studsubj_rows):
            totals = {}
            for row in studsubj_rows:
                logger.debug('row: ' + str(row))
                # row: {'id': 155, 'idnumber': '1998092908', 'examnumber': '109', 'lastname': 'Castillo', 'firstname': 'Shurensly', 'prefix': None, 'classname': None,
                # 'lvl_abbrev': 'PBL', 'sct_abbrev': 'tech',
                # 'subj_id_arr': [3, 1, 10, 15, 27, 29, 31, 33, 46]}
                row_index += 1
                for i, field_name in enumerate(field_names):
                    value = ''
                    if isinstance(field_name, int):
                        # in subject column 'field_name is the ph of the subject
                        subj_id_list = row.get('subj_id_arr', [])
                        if subj_id_list and field_name in subj_id_list:
                            value = 'x'
                            if field_name not in totals:
                                totals[field_name] = 1
                            else:
                                totals[field_name] += 1
                    elif field_name == 'fullname':
                        prefix = row.get('prefix')
                        lastname = row.get('lastname', '')
                        firstname = row.get('firstname', '')
                        if prefix:
                            lastname = ' '.join((prefix, lastname))
                        value = ''.join((lastname, ', ', firstname))
                    else:
                        value = row.get(field_name, '')
                    sheet.write(row_index, i, value, row_formats[i])

# ---  table total row
            row_index += 1
            for i, field_name in enumerate(field_names):
                logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
                value = ''
                if isinstance(field_name, int):
                    if field_name in totals:
                        value = totals[field_name]
                    sheet.write(row_index, i, value, totalrow_formats[i])
                    # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')
                elif field_name == 'examnumber':
                    #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                    sheet.merge_range(row_index, 0, row_index, first_subject_column -1, 'TOTAAL', totalrow_merge)

# ---  table footer row
            row_index += 1
            for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
                if i == 0:
                    sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', totalrow_merge)
                else:
                    sheet.write(row_index, i, field_captions[i], header_formats[i])

# ---  footnote row
            row_index += 2
            sheet.write(row_index, 0, settings['footnote01'], bold_format)
            row_index += 1
            sheet.write(row_index, 0, settings['footnote02'], bold_format)
            row_index += 1
            sheet.write(row_index, 0, settings['footnote03'], bold_format)
            row_index += 3
            sheet.write(row_index, 0, settings['footnote04'], bold_format)
            row_index += 1
            sheet.write(row_index, 0, settings['footnote05'], bold_format)
            row_index += 1
            sheet.write(row_index, 0, settings['footnote06'], bold_format)
            row_index += 1
        book.close()

    # Rewind the buffer.
        output.seek(0)

    # Set up the Http response.
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    # response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # response['Content-Disposition'] = "attachment; filename=" + file_name
    return response
# --- end of create_ex1_xlsx


def create_ex1_rows(examyear, school, department):
    level_req = department.level_req

    sql_studsubj_agg_list = [
        "SELECT studsubj.student_id AS student_id,",
        "ARRAY_AGG(si.subject_id) AS subj_id_arr",
        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "GROUP BY studsubj.student_id"]
    sql_studsubj_agg = ' '.join(sql_studsubj_agg_list)

    sql_list = [
        "SELECT st.id, st.idnumber, st.examnumber, st.lastname, st.firstname, st.prefix, st.classname,",
        "st.level_id, st.sector_id, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, studsubj.subj_id_arr",
        "FROM students_student AS st",
        "INNER JOIN (" + sql_studsubj_agg + ") AS studsubj ON (studsubj.student_id = st.id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
        "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
    ]
    if level_req:
        sql_list.append("ORDER BY LOWER(lvl.abbrev), LOWER(st.lastname), LOWER(st.firstname)")
    else:
        sql_list.append("ORDER BY LOWER(st.lastname), LOWER(st.firstname)")
    sql = ' '.join(sql_list)

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    return rows
# --- end of create_ex1_rows


def create_ex1_mapped_subject_rows(examyear, school, department):
    # function returns:
    #  subject_pk_dict: {34: 0, 29: 1, 4: 2, 36: 3, 31: 4, 27: 5, 33: 6, 35: 7, 1: 8, 15: 9, 3: 10}
    #  subject_code_list: ['bw', 'cav', 'en', 'inst', 'lo', 'mm1', 'mt', 'mvt', 'ne', 'ns1', 'pa']
    #  level_pk_list: [1]
    #  index = row_count

    subject_pk_dict = {}
    subject_code_list = []
    subject_pk_list = []
    level_pk_list = []
    sql_list = [
        "SELECT subj.id, subjbase.code, st.level_id",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
        "GROUP BY subj.id, subjbase.code, st.level_id",
        "ORDER BY LOWER(subjbase.code)"
    ]
    sql = ' '.join(sql_list)

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        index = 0
        subject_rows = cursor.fetchall()
        for subject_row in subject_rows:
            subject_pk_dict[subject_row[0]] = index
            subject_pk_list.append(subject_row[0])
            subject_code_list.append(subject_row[1])
            if subject_row[2] and subject_row[2] not in level_pk_list:
                level_pk_list.append(subject_row[2])
            index += 1

    return index, subject_pk_list, subject_code_list, level_pk_list
# --- end of create_ex1_mapped_subject_rows

# +++++++++++ Scheme list ++++++++++++

def create_scheme_xlsx(examyear, scheme_rows, subjecttype_rows, schemeitem_rows, exform_text, user_lang):  # PR2021-06-28
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_scheme_xlsx -----')
        for row in scheme_rows:
            logger.debug('scheme_row: ' + str(row))
        for row in subjecttype_rows:
            logger.debug('subjecttype_row: ' + str(row))

    # from https://stackoverflow.com/questions/16393242/xlsxwriter-object-save-as-http-response-to-create-download-in-django
    # logger.debug('period_dict: ' + str(period_dict))

    """

        scheme_row: {'id': 193, 'department_id': 99, 'level_id': None, 'sector_id': 147, 'mapid': 'scheme_193', 
        'scheme_name': 'Vwo - n&t', 'minsubjects': None, 'maxsubjects': None, 'min_mvt': None, 'max_mvt': None, 
        'dep_abbrev': 'V.W.O.', 'lvl_abbrev': None, 'sct_abbrev': 'n&t', 'ey_code': 2021, 'depbase_code': 'Vwo', 
        'modifiedby_id': 41, 'modifiedat': datetime.datetime(2021, 6, 28, 15, 14, 8, 446421, tzinfo=<UTC>), 
        'modby_username': 'Ete'}

    """

    response = None

    if scheme_rows:
        # ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
        title = ' '.join(('Ex1', str(examyear), today_dte.isoformat()))
        file_name = title + ".xlsx"
        worksheet_name = str(_('Ex1'))

        # create the HttpResponse object ...
        # response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        # response['Content-Disposition'] = "attachment; filename=" + file_name

        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()
        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        #  book = xlsxwriter.Workbook(response, {'in_memory': True})
        book = xlsxwriter.Workbook(output)

        sheet = book.add_worksheet(worksheet_name)
        sheet.hide_gridlines(2)  # 2 = Hide screen and printed gridlines

        # cell_format = book.add_format({'bold': True, 'font_color': 'red'})
        bold_format = book.add_format({'bold': True})

        # th_format.set_bg_color('#d8d8d8') #   #d8d8d8;  /* light grey 218 218 218 100%
        # or: th_format = book.add_format({'bg_color': '#d8d8d8'
        th_align_center = book.add_format(
            {'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        th_rotate = book.add_format(
            {'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'rotation': 90})

        th_merge = book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        th_merge.set_left()
        th_merge.set_bottom()

        row_align_left = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter', 'border': True})
        row_align_center = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True})

        totalrow_align_center = book.add_format(
            {'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'border': True})
        totalrow_number = book.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'border': True})
        totalrow_merge = book.add_format({'border': True, 'align': 'right', 'valign': 'vcenter'})

        # get number of columns
        col_count = 3  # add column exnr, idnumber, name and class
        field_width = [10, 12, 35]
        field_names = ['examnumber', 'idnumber', 'fullname']
        field_captions = ['Ex.nr.', 'ID-nummer', 'Naam en voorletters van de kandidaat\n(in alfabetische volgorde)']
        header_formats = [th_align_center, th_align_center, th_align_center]

        # --- title row
        # was: sheet.write(0, 0, str(_('Report')) + ':', bold)
        sheet.write(0, 0, exform_text['minond'], bold_format)
        sheet.write(1, 0, exform_text['title'], bold_format)

        # ---  table header row
        row_index = 9
        for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
            sheet.write(row_index, i, field_captions[i], header_formats[i])

        if len(studsubj_rows):
            totals = {}
            for row in studsubj_rows:
                logger.debug('row: ' + str(row))
                # row: {'id': 155, 'idnumber': '1998092908', 'examnumber': '109', 'lastname': 'Castillo', 'firstname': 'Shurensly', 'prefix': None, 'classname': None,
                # 'lvl_abbrev': 'PBL', 'sct_abbrev': 'tech',
                # 'subj_id_arr': [3, 1, 10, 15, 27, 29, 31, 33, 46]}
                row_index += 1
                for i, field_name in enumerate(field_names):
                    value = ''
                    if isinstance(field_name, int):
                        # in subject column 'field_name is the ph of the subject
                        subj_id_list = row.get('subj_id_arr', [])
                        if subj_id_list and field_name in subj_id_list:
                            value = 'x'
                            if field_name not in totals:
                                totals[field_name] = 1
                            else:
                                totals[field_name] += 1
                    elif field_name == 'fullname':
                        prefix = row.get('prefix')
                        lastname = row.get('lastname', '')
                        firstname = row.get('firstname', '')
                        if prefix:
                            lastname = ' '.join((prefix, lastname))
                        value = ''.join((lastname, ', ', firstname))
                    else:
                        value = row.get(field_name, '')
                    sheet.write(row_index, i, value, row_formats[i])

            # ---  table total row
            row_index += 1
            for i, field_name in enumerate(field_names):
                logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
                value = ''
                if isinstance(field_name, int):
                    if field_name in totals:
                        value = totals[field_name]
                    sheet.write(row_index, i, value, totalrow_formats[i])
                    # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')
                elif field_name == 'examnumber':
                    #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                    sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, 'TOTAAL', totalrow_merge)

        book.close()

        # Rewind the buffer.
        output.seek(0)

        # Set up the Http response.
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    # response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # response['Content-Disposition'] = "attachment; filename=" + file_name
    return response
# --- end of create_ex1_xlsx


############ ORDER LIST ##########################

@method_decorator([login_required], name='dispatch')
class OrderlistDownloadView(View):  # PR2021-07-04

    def get(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= OrderlistDownloadView ============= ')
            logger.debug('list: ' + str(list) + ' ' + str(type(list)))
        # function creates, Ex1 xlsx file based on settings in usersetting
        # TODO ex form prints colums twice, and totals are not correct,
        # TODO text EINDEXAMEN missing the rest, school not showing PR2021-05-30
        response = None

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear,from usersettings
            sel_examyear, sel_schoolNIU, sel_departmentNIU, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)
            if logging_on:
                logger.debug('sel_examyear: ' + str(sel_examyear))

            if sel_examyear:
                is_ete_exam = True if list == 'ete' else False
# get text from examyearsetting
                settings = af.get_exform_text(sel_examyear, ['exform', 'ex1'])
                if logging_on:
                    logger.debug('settings: ' + str(settings))

# +++ get mapped_subject_rows
                subject_row_count, mapped_subject_pk_dict, subject_pk_list, subject_code_list, subject_name_list = \
                    create_orderlist_mapped_subject_rows(sel_examyear, is_ete_exam)
                if logging_on:
                    logger.debug('mapped_subject_pk_dict: ' + str(mapped_subject_pk_dict))
                    logger.debug('subject_pk_list: ' + str(subject_pk_list))
                    logger.debug('subject_code_list: ' + str(subject_code_list))
                    logger.debug('subject_name_list: ' + str(subject_name_list))
                #  subject_pk_dict: {34: 0, 29: 1, ...} ( subject_pk: index)
                #  subject_code_list: ['bw', 'cav', ]
                #  index = row_count

# +++ get dict of subjects of these studsubj_rows
                orderlist_rows = create_orderlist_rows(sel_examyear, is_ete_exam)
                if orderlist_rows:
                    response = create_orderlist_xlsx(orderlist_rows, sel_examyear.code, settings, subject_pk_list, subject_code_list, is_ete_exam, user_lang)

        if response is None:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER') ) )
            response = HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        return response
# - end of OrderlistDownloadView


def create_orderlist_xlsx(orderlist_rows, examyear_code, settings, subject_pk_list, subject_code_list, is_ete_exam, user_lang):  # PR2021-07-07
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_orderlist_xlsx -----')
        # row: {'school_id': 78, 'schbase_code': 'CUR13', 'school_name': 'Abel Tasman College', 'dep_id': 97, 'depbase_code': 'Vsbo',
        #           'lvl_id': 63, 'lvl_abbrev': 'TKL', 'subj_id': 998, 'subjbase_code': 'ne', 'subj_name': 'Nederlandse taal', '
        #           subj_published_arr': [None], 'lang': 'ne', 'count': 7}

    response = None

    if orderlist_rows:

# ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
        ete_duo = ' ETE ' if is_ete_exam else "DUO"
        title = ' '.join((str(_('Orderlist')), ete_duo, str(_('exams')), str(examyear_code)))
        file_name = title + ' dd ' + today_dte.isoformat() + ".xlsx"
        worksheet_name = str(_('Orderlist'))

    # create the HttpResponse object ...
        #response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        #response['Content-Disposition'] = "attachment; filename=" + file_name

# Create an in-memory output file for the new workbook.
        output = io.BytesIO()
        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        #  book = xlsxwriter.Workbook(response, {'in_memory': True})
        book = xlsxwriter.Workbook(output)

        sheet = book.add_worksheet(worksheet_name)
        sheet.hide_gridlines(2) # 2 = Hide screen and printed gridlines

        #cell_format = book.add_format({'bold': True, 'font_color': 'red'})
        bold_format = book.add_format({'bold': True})

        # th_format.set_bg_color('#d8d8d8') #   #d8d8d8;  /* light grey 218 218 218 100%
        # or: th_format = book.add_format({'bg_color': '#d8d8d8'
        th_align_center = book.add_format({'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        th_rotate = book.add_format({'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'rotation': 90})

        th_merge = book.add_format({ 'bold': True, 'align': 'center', 'valign': 'vcenter'})
        th_merge.set_left()
        th_merge.set_bottom()

        row_align_left = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter','border': True})
        row_align_center = book.add_format({'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter','border': True})

        totalrow_align_center = book.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'border': True})
        totalrow_number = book.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'border': True})
        totalrow_merge = book.add_format({'border': True, 'align': 'right', 'valign': 'vcenter'})

# get number of columns
        # columns are (0: 'exnumber', 1: idnumber, 2: name 3: 'class' 4: level "
        # columns 5 thru 19 are subject columns. Extend number when more than 15 subjects
        # columns schoolcode schoolname, dep, lvl, lang, name

        col_count = 5  # add column exnr, idnumber, name and class
        field_width = [10, 25, 8, 8, 35]
        field_names = ['sbase_code', 'school_name', 'depbase_code', 'lvl_abbrev',  'fullname']
        field_captions = [ str(_('School code')), str(_('School')), str(_('Department')), str(_('Level')),  str(_('Candidate')) ]
        header_formats = [th_align_center, th_align_center, th_align_center, th_align_center,  th_align_center]
        row_formats = [row_align_center, row_align_left, row_align_center, row_align_center,  row_align_left]
        totalrow_formats = [totalrow_merge, totalrow_align_center, totalrow_align_center,  totalrow_align_center, totalrow_align_center]

        first_subject_column = col_count
        subject_length = len(subject_code_list)
        subject_col_width = 2.14


        for x in range(0, subject_length):  # range(start_value, end_value, step), end_value is not included!
            field_width.append(subject_col_width)
            subject_code = subject_code_list[x] if subject_code_list[x] else ''
            subject_pk = subject_pk_list[x]
            field_captions.append(subject_code)
            field_names.append(subject_pk)
            header_formats.append(th_rotate)
            row_formats.append(row_align_center)
            totalrow_formats.append(totalrow_number)

            col_count += 1

        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

    # --- title row
        # was: sheet.write(0, 0, str(_('Report')) + ':', bold)
        sheet.write(0, 0, settings['minond'], bold_format)
        sheet.write(2, 0, title, bold_format)


# ---  table header row
        row_index = 9
        for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
            sheet.write(row_index, i, field_captions[i], header_formats[i])

        if len(orderlist_rows):
            totals = {}
            for row in orderlist_rows:
                logger.debug('row: ' + str(row))
                # row: {'id': 155, 'idnumber': '1998092908', 'examnumber': '109', 'lastname': 'Castillo', 'firstname': 'Shurensly', 'prefix': None, 'classname': None,
                # 'lvl_abbrev': 'PBL', 'sct_abbrev': 'tech',
                # 'subj_id_arr': [3, 1, 10, 15, 27, 29, 31, 33, 46]}
                row_index += 1
                for i, field_name in enumerate(field_names):
                    value = ''
                    if isinstance(field_name, int):
                        # in subject column 'field_name is the pk of the subject
                        subj_id_list = row.get('subj_id_arr', [])
                        if subj_id_list and field_name in subj_id_list:
                            value = '1'
                            if field_name not in totals:
                                totals[field_name] = 1
                            else:
                                totals[field_name] += 1
                    elif field_name == 'fullname':
                        prefix = row.get('prefix')
                        lastname = row.get('lastname', '')
                        firstname = row.get('firstname', '')
                        if prefix:
                            lastname = ' '.join((prefix, lastname))
                        value = ''.join((lastname, ', ', firstname))
                    else:
                        value = row.get(field_name, '')
                    sheet.write(row_index, i, value, row_formats[i])

# ---  table total row
            row_index += 1
            for i, field_name in enumerate(field_names):
                logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
                value = ''
                if isinstance(field_name, int):
                    if field_name in totals:
                        value = totals[field_name]
                    sheet.write(row_index, i, value, totalrow_formats[i])
                    # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')
                elif field_name == 'examnumber':
                    #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                    sheet.merge_range(row_index, 0, row_index, first_subject_column -1, 'TOTAAL', totalrow_merge)

# ---  table footer row
            row_index += 1
            for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
                if i == 0:
                    sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', totalrow_merge)
                else:
                    sheet.write(row_index, i, field_captions[i], header_formats[i])

# ---  footnote row
            """
            row_index += 2
            sheet.write(row_index, 0, settings['footnote01'], bold_format)
            row_index += 1
            sheet.write(row_index, 0, settings['footnote02'], bold_format)
            row_index += 1
            sheet.write(row_index, 0, settings['footnote03'], bold_format)
            row_index += 3
            sheet.write(row_index, 0, settings['footnote04'], bold_format)
            row_index += 1
            sheet.write(row_index, 0, settings['footnote05'], bold_format)
            row_index += 1
            sheet.write(row_index, 0, settings['footnote06'], bold_format)
            row_index += 1
            """
        book.close()

    # Rewind the buffer.
        output.seek(0)

    # Set up the Http response.
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    # response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # response['Content-Disposition'] = "attachment; filename=" + file_name
    return response
# - end of create_orderlist_xlsx


def create_orderlist_mapped_subject_rows(examyear, is_ete_exam):
    # PR2021-07-08 functions creates mapped dict and lists of all subjects
    # function returns:
    #  subject_pk_dict: {34: 0, 29: 1, }  (subj_pk: index)
    #  subject_code_list: ['bw', 'cav', 'en', 'inst', 'lo', 'mm1', 'mt', 'mvt', 'ne', 'ns1', 'pa']
    #  subject_name_list: ['Bouw', ...]
    #  index = row_count

    ete_clause = 'TRUE' if  is_ete_exam else 'FALSE'

    mapped_subject_pk_dict = {}
    subject_pk_list = []
    subject_code_list = []
    subject_name_list = []

    sql_keys = {'ey_id': examyear.pk}
    sql_list = [
        "SELECT subj.id, subjbase.code, subj.name",

        "FROM subjects_schemeitem AS si",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",

        "WHERE ey.id = %(ey_id)s::INT",
        "AND subj.etenorm = " + ete_clause,
        "GROUP BY subj.id, subjbase.code, subj.name",
        "ORDER BY LOWER(subj.name)"
    ]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        index = 0
        subject_rows = cursor.fetchall()
        for subject_row in subject_rows:
            mapped_subject_pk_dict[subject_row[0]] = index
            subject_pk_list.append(subject_row[0])
            subject_code_list.append(subject_row[1])
            subject_name_list.append(subject_row[2])

            index += 1

    return index, mapped_subject_pk_dict, subject_pk_list, subject_code_list, subject_name_list
# --- end of create_orderlist_subject_rows


def create_orderlist_rows(examyear, is_ete_exam):

    ete_clause = 'TRUE' if  is_ete_exam else 'FALSE'
    sql_studsubj_agg_list = [
        "SELECT studsubj.student_id AS student_id,",
        "ARRAY_AGG(si.subject_id) AS subj_id_arr",
        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "WHERE subj.etenorm = " + ete_clause,
        "GROUP BY studsubj.student_id"]
    sql_studsubj_agg = ' '.join(sql_studsubj_agg_list)
    # Note: use examyear.code (integer field) to filter on examyear. This way schools from SXM and CUR are added to list
    sql_keys = {'ey_int': examyear.code , 'ete': is_ete_exam}
    sql_list = [
        "SELECT st.id, st.idnumber, st.examnumber, st.lastname, st.firstname, st.prefix, st.classname,",
        "sbase.code AS sbase_code, school.name AS school_name, depbase.code AS depbase_code,",
        "st.level_id, st.sector_id, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, studsubj.subj_id_arr",

        "FROM students_student AS st",
        "INNER JOIN (" + sql_studsubj_agg + ") AS studsubj ON (studsubj.student_id = st.id)",
        "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
        "INNER JOIN schools_schoolbase AS sbase ON (sbase.id = school.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",

        "WHERE ey.code = %(ey_int)s::INT"
    ]
    sql_list.append("ORDER BY LOWER(st.lastname), LOWER(st.firstname)")
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    return rows
# --- end of create_orderlist_rows

