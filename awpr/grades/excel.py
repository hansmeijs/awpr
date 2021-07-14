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
            sel_examyear, sel_examperiod = \
                dl.get_selected_examyear_examperiod_from_usersetting(request)
            if logging_on:
                logger.debug('sel_examyear: ' + str(sel_examyear))
                logger.debug('sel_examperiod: ' + str(sel_examperiod) + ' ' + str(type(sel_examperiod)))

            if sel_examyear:

                # list: ete/duo
                is_ete_exam = True if list == 'ete' else False

# get text from examyearsetting
                settings = af.get_exform_text(sel_examyear, ['exform', 'ex1'])

                # TODO create 3 worksheets, one for each lang or pu them in one worksheet

                otherlang = None
# +++ get mapped_subject_rows
                subjectbase_pk_list, subjectbase_code_list = \
                    create_orderlist_mapped_subject_rows(sel_examyear, sel_examperiod, is_ete_exam, otherlang)
                if logging_on:
                    logger.debug('subjectbase_pk_list: ' + str(subjectbase_pk_list))
                    logger.debug('subjectbase_code_list: ' + str(subjectbase_code_list))
                    # index = 0 is first column with subject
                    # subjectbase_pk_list: [126, 89, 91]
                    # subjectbase_code_list: ['ec', 'pa', 'sp']


# +++ get dict of subjects of these studsubj_rows
                orderlist_rows = create_orderlist_rows(sel_examyear, sel_examperiod, is_ete_exam, otherlang)
                if orderlist_rows:
                    response = create_orderlist_xlsx(orderlist_rows, sel_examyear.code, settings, subjectbase_pk_list, subjectbase_code_list, is_ete_exam, user_lang)

        if response is None:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER') ) )
            response = HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        return response
# - end of OrderlistDownloadView


def create_orderlist_mapped_subject_rows(examyear, examperiod_int, is_ete_exam, otherlang):
    # PR2021-07-08 functions creates mapped dict and lists of all subjects
    # function returns:
    #  subject_pk_dict: {34: 0, 29: 1, }  (subj_pk: index)
    #  subject_code_list: ['bw', 'cav', 'en', 'inst', 'lo', 'mm1', 'mt', 'mvt', 'ne', 'ns1', 'pa']
    #  subject_name_list: ['Bouw', ...]
    #  index = row_count

    ete_clause = 'TRUE' if  is_ete_exam else 'FALSE'
    otherlang_clause = ''
    if otherlang:
        otherlang_clause = "AND subj.otherlang = '" + otherlang + "'"

    subjectbase_pk_list = []
    subjectbase_code_list = []

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('-----  create_orderlist_rows  -----')

    if is_ete_exam:
        ete_clause = "AND subj.etenorm"
    else:
        ete_clause = "AND NOT subj.etenorm"

    examperiod_clause = ''
    if examperiod_int == c.EXAMPERIOD_SECOND:
        examperiod_clause = "AND studsubj.has_reex"
    elif examperiod_int == c.EXAMPERIOD_THIRD:
        examperiod_clause = "AND studsubj.has_reex03"

    otherlang_clause = ''
    if otherlang:
        otherlang_clause = "AND subj.otherlang = '" + otherlang + "'"

    # Note: use examyear.code (integer field) to filter on examyear. This way schools from SXM and CUR are added to list
    sql_keys = {'ey_int': examyear.code}
    sql_list = [
        "SELECT subjbase.id, subjbase.code ",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
        "INNER JOIN schools_schoolbase AS sbase ON (sbase.id = school.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",

        "WHERE ey.code = %(ey_int)s::INT AND NOT studsubj.deleted",
        ete_clause,
        examperiod_clause,
        otherlang_clause,
        "GROUP BY subjbase.id, subjbase.code"]

    sql_list.append("ORDER BY LOWER(subjbase.code)")
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        subject_rows = cursor.fetchall()

        for subject_row in subject_rows:
            subjectbase_pk_list.append(subject_row[0])
            subjectbase_code_list.append(subject_row[1])

    return subjectbase_pk_list, subjectbase_code_list
# --- end of create_orderlist_subject_rows


def create_orderlist_rows(examyear, examperiod_int, is_ete_exam, otherlang):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('-----  create_orderlist_rows  -----')

    if is_ete_exam:
        ete_clause = "AND subj.etenorm"
    else:
        ete_clause = "AND NOT subj.etenorm"

    examperiod_clause = ''
    if examperiod_int == c.EXAMPERIOD_SECOND:
        examperiod_clause = "AND studsubj.has_reex"
    elif examperiod_int == c.EXAMPERIOD_THIRD:
        examperiod_clause = "AND studsubj.has_reex03"

    otherlang_clause = ''
    if otherlang:
        otherlang_clause = "AND subj.otherlang = '" + otherlang + "'"

    # Note: use examyear.code (integer field) to filter on examyear. This way schools from SXM and CUR are added to list
    sql_keys = {'ey_int': examyear.code}
    sql_list = [
        "SELECT depbase.code, lvl.abbrev, sbase.code, school.name, subjbase.id, count(*)",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
        "INNER JOIN schools_schoolbase AS sbase ON (sbase.id = school.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",

        "WHERE ey.code = %(ey_int)s::INT AND NOT studsubj.deleted",
        ete_clause,
        examperiod_clause,
        otherlang_clause,
        "GROUP BY depbase.code, lvl.abbrev, sbase.code, school.name, subjbase.id"]

    sql_list.append("ORDER BY LOWER(depbase.code), LOWER(lvl.abbrev), LOWER(sbase.code)")
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = cursor.fetchall()

    # row:  0: depbase_code, 1: lvl_abbrev, 2: schoolbase_code, 3: subjbase_code 4: count

    return rows
# --- end of create_orderlist_rows


def create_orderlist_xlsx(orderlist_rows, examyear_code, settings,
                          subjectbase_pk_list, subjectbase_code_list,
                          is_ete_exam, user_lang):  # PR2021-07-07
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
        # columns are (0: 'depbase_code', 1: lvl_abbrev, 2: schoolbase_code 3:"
        # columns 3 etc  are subject columns. Extend number when more than 15 subjects

        col_count = 4  # depbase_code', lvl_abbrev,schoolbase_code
        subject_count = len(subjectbase_code_list)

        field_width = [10, 10, 10, 25]
        field_names = ['depbase_code', 'lvl_abbrev','schoolbase_code', 'school_name']
        field_names.extend(subjectbase_pk_list)
        logger.debug('field_names: ' + str(field_names))

        field_captions = [str(_('Department')),  str(_('Level')),  str(_('School code')), str(_('School')) ]
        field_captions.extend(subjectbase_code_list)
        logger.debug('field_captions: ' + str(field_captions))



        header_formats = [th_align_center, th_align_center, th_align_center, th_align_center]
        row_formats = [row_align_center, row_align_center, row_align_center, row_align_left]
        totalrow_formats = [totalrow_merge, totalrow_align_center, totalrow_align_center, totalrow_align_center]

        first_subject_column = col_count
        subject_col_width = 4


# add attributes to subject columns
        for x in range(0, subject_count):  # range(start_value, end_value, step), end_value is not included!
            field_width.append(subject_col_width)
            header_formats.append(th_align_center)
            row_formats.append(row_align_center)
            totalrow_formats.append(totalrow_number)

        col_count += subject_count


# create index_list and total_list
        index_list = []
        total_list = []
        for x in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
            index_list.append(x)
            total_list.append(0)

        logger.debug('index_list: ' + str(index_list))
        logger.debug('total_list: ' + str(total_list))

# create mapped_dict from field_names and index list, used to lookup index of  field_name
        mapped_dict = dict(zip(field_names, index_list))
        logger.debug('mapped_dict: ' + str(mapped_dict))
        # mapped_dict: {'depbase_code': 0, 'lvl_abbrev': 1, 'schoolbase_code': 2, 126: 3, 89: 4, 91: 5}

# --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

    # --- title row
        # was: sheet.write(0, 0, str(_('Report')) + ':', bold)
        sheet.write(0, 0, settings['minond'], bold_format)
        sheet.write(2, 0, title, bold_format)

# ---  table header row
        row_index = 5
        for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
            sheet.write(row_index, i, field_captions[i], header_formats[i])

        # field_names: ['depbase_code', 'lvl_abbrev', 'schoolbase_code', 126, 89, 91]
        if len(orderlist_rows):

# ---  data rows
            for row in orderlist_rows:
                logger.debug('row: ' + str(row))
                # row:  0: depbase_code, 1: lvl_abbrev, 2: schoolbase_code, 3: subjbase_pk 4: count
                # row: ('Havo', None, 'CUR13', 89, 17)
                row_index += 1
                for i, field_name in enumerate(field_names):
                    value = ''
                    if isinstance(field_name, int):
                        subjbase_pk = row[4]
                        if field_name ==  subjbase_pk:
                            value = row[5]
                            total_list[i] += value
                    elif field_name == 'depbase_code':
                        value = row[0]
                    elif field_name == 'lvl_abbrev':
                        value = row[1]
                    elif field_name == 'schoolbase_code':
                        value = row[2]
                    elif field_name == 'school_name':
                        value = row[3]
                    sheet.write(row_index, i, value, row_formats[i])

# ---  table total row
            row_index += 1
            for i, field_name in enumerate(field_names):
                logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
                value = ''
                if isinstance(field_name, int):
                    value = total_list[i]
                    sheet.write(row_index, i, value, totalrow_formats[i])
                    # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')
                elif field_name == 'depbase_code':
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


############ SCHEME LIST ##########################
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@method_decorator([login_required], name='dispatch')
class SchemeDownloadXlsxView(View):  # PR2021-07-13

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
                sel_examyear, sel_scheme_pk = \
                    dl.get_selected_examyear_scheme_pk_from_usersetting(request)

                if sel_examyear :

    # +++ get dict of subjects of these studsubj_rows
                    scheme_rows = subj_vw.create_scheme_rows(
                        examyear=sel_examyear,
                        scheme_pk=sel_scheme_pk)
                    subjecttype_rows = subj_vw.create_subjecttype_rows(
                        examyear=sel_examyear,
                        scheme_pk=sel_scheme_pk,
                        orderby_sequence=True)
                    schemeitem_rows = subj_vw.create_schemeitem_rows(
                        examyear=sel_examyear,
                        scheme_pk=sel_scheme_pk,
                        orderby_name=True)
                    if schemeitem_rows:
                        response = create_scheme_xlsx(sel_examyear, scheme_rows, subjecttype_rows, schemeitem_rows, user_lang)

        #except:
        #    raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of SchemeDownloadXlsxView


# +++++++++++ Scheme list ++++++++++++
def create_scheme_xlsx(examyear, scheme_rows, subjecttype_rows, schemeitem_rows, user_lang):  # PR2021-06-28
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_scheme_xlsx -----')

    # from https://stackoverflow.com/questions/16393242/xlsxwriter-object-save-as-http-response-to-create-download-in-django
    # logger.debug('period_dict: ' + str(period_dict))

    response = None

    if scheme_rows:
        # ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
        title = ''.join((str(_('Subject schemes')), ' ', str(examyear), ' dd ', today_dte.isoformat()))
        file_name = title + ".xlsx"
        worksheet_name = str(_('Subject schemes'))

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
            {'font_size': 8, 'border': True, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        th_align_center.set_bottom()
        th_align_center.set_bg_color('#d8d8d8')  # #d8d8d8;  /* light grey 218 218 218 100%

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

        field_width = [25, 12, 12, 12,
                       12, 12, 12, 12, 12, 12,
                       15, 15,
                       12, 12, 12, 12, 12, 12, 12,
                       15, 15
                       ]

# --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

        row_index = 0

# --- title row
        title = ''.join((str(_('Subject schemes')), ' ', str(examyear)))
        sheet.write(row_index, 0, title, bold_format)

        row_index += 3
        for scheme_row in scheme_rows:
            scheme_pk = scheme_row.get('id')

    # ---  table subject scheme
            row_index = create_scheme_paragraph_xlsx(row_index, sheet, scheme_row, bold_format,
                                         th_align_center, row_align_left, row_align_center, user_lang)

    # ---  table subject type
            row_index = create_subjecttype_paragraph_xlsx(row_index, sheet, subjecttype_rows, scheme_pk,
                                         th_align_center, row_align_left, row_align_center, user_lang)

    # ---  table scheitems
            row_index = create_schemeitem_paragraph_xlsx(row_index, sheet, schemeitem_rows, scheme_pk,
                                              th_align_center, row_align_left, row_align_center, user_lang)
        book.close()

# - Rewind the buffer.
        output.seek(0)

# - Set up the Http response.
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
    # response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # response['Content-Disposition'] = "attachment; filename=" + file_name
    return response
# --- end of create_scheme_xlsx


def create_scheme_paragraph_xlsx(row_index, sheet, row, bold_format,
                                 th_align_center, row_align_left, row_align_center, user_lang):  # PR2021-07-13

    # get number of columns
    field_names = ['name', 'dep_abbrev', 'lvl_abbrev', 'sct_abbrev',
                   'min_subjects', 'max_subjects',
                   'min_mvt', 'max_mvt',
                   'min_combi', 'max_combi',
                   'modifiedat', 'modby_username']
    field_captions = [str(_('Subject scheme')), str(_('Department')), str(_('Level')), str(_('Sector / Profiel')),
                      str(_('Minimum amount of subjects')), str(_('Maximum amount of subjects')),
                      str(_('Minimum amount of MVT subjects')), str(_('Maximum amount of MVT subjects')),
                      str(_('Minimum amount of combination subjects')),
                      str(_('Maximum amount of combination subjects')),
                      str(_('Last modified on ')), str(_('Last modified by'))]
    header_format = th_align_center
    row_formats = [row_align_left, row_align_center, row_align_center, row_align_center,
                   row_align_center, row_align_center,
                   row_align_center, row_align_center,
                   row_align_center, row_align_center,
                   row_align_left, row_align_left
                   ]

    col_count = len(field_names)

    row_index += 3
    # --- title row
    title = row.get('name', '')
    sheet.write(row_index, 0, title, bold_format)

    row_index += 2

    # ---  table header row
    for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        sheet.write(row_index, i, field_captions[i], header_format)

    # ---  loop through scheme rows
    if row:
        row_index += 1
        for i, field_name in enumerate(field_names):
            if field_name == 'modifiedat':
                modified_dte = row.get(field_name, '')
                value = af.format_modified_at(modified_dte, user_lang)
            else:
                value = row.get(field_name, '')
            sheet.write(row_index, i, value, row_formats[i])

    return row_index
# --- end of create_scheme_paragraph_xlsx


def create_subjecttype_paragraph_xlsx(row_index, sheet, subjecttype_rows, scheme_pk,
                                 th_align_center, row_align_left, row_align_center, user_lang):  # PR2021-07-13

    # get number of columns
    field_names = ['name', 'abbrev',
                   'min_subjects', 'max_subjects',
                   'min_extra_nocount', 'max_extra_nocount',
                   'min_extra_counts', 'max_extra_counts',
                   'min_elective_combi', 'max_elective_combi',
                   'modifiedat', 'modby_username']
    field_captions = [str(_('Character')), str(_('Abbreviation')),
                      str(_('Minimum amount of subjects')),
                      str(_('Maximum amount of subjects')),
                      str(_("Minimum extra subject, doesn't count")),
                      str(_("Maximum extra subject, doesn't count")),
                      str(_("Minimum extra subject, counts")),
                      str(_("Maximum extra subject, counts")),
                      str(_("Minimum elective combi subject")),
                      str(_("Maximum elective combi subject")),
                      str(_('Last modified on ')), str(_('Last modified by'))]
    header_format = th_align_center
    row_formats = [row_align_left, row_align_center,
                   row_align_center, row_align_center,
                   row_align_center, row_align_center,
                   row_align_center, row_align_center,
                   row_align_center, row_align_center,
                   row_align_left, row_align_left
                   ]

    col_count = len(field_names)

    row_index += 3
    # ---  table header row
    for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        sheet.write(row_index, i, field_captions[i], header_format)

    # ---  loop through scheme rows
    if len(subjecttype_rows):
        for row in subjecttype_rows:
            scheme_id = row.get('scheme_id')
            if scheme_id == scheme_pk:
                row_index += 1
                for i, field_name in enumerate(field_names):
                    if field_name == 'modifiedat':
                        modified_dte = row.get(field_name, '')
                        value = af.format_modified_at(modified_dte, user_lang)
                    else:
                        value = row.get(field_name, '')
                    sheet.write(row_index, i, value, row_formats[i])

    return row_index
# --- end of create_subjecttype_paragraph_xlsx


def create_schemeitem_paragraph_xlsx(row_index, sheet, schemeitem_rows, scheme_pk,
                                 th_align_center, row_align_left, row_align_center, user_lang):  # PR2021-07-13

    # get number of columns
    field_names = ['subj_name', 'subj_code', 'sjtp_abbrev', 'gradetype',
                   'weight_se', 'weight_ce',
                   'is_mandatory',
                   'is_combi', 'is_core_subject', 'is_mvt',
                   'extra_count_allowed', 'extra_nocount_allowed',
                   'elective_combi_allowed',
                   'has_practexam',

                   'has_pws',
                   'reex_se_allowed', 'max_reex',
                   'no_thirdperiod', 'no_exemption_ce',

                   'modifiedat', 'modby_username']

    col_count = len(field_names)

    field_captions = [str(_('Subjects of this subject scheme')),
                      str(_('Abbreviation')),
                      str(_('Subject type')),
                      str(_('Grade type')),
                      str(_('SE weight')), str(_('CE weight')),
                      str(_('Mandatory')),
                      str( _('Combination subject')),
                      str(_('Core subject')),
                      str(_('MVT subject')),
                      str(_('Extra subject counts allowed')), str(_('Extra subject does not count allowed')),
                      str(_('Elective combi subject allowed')),
                      str(_('Has practical exam')),
                      str(_('Has assignment')),
                      str(_('Herkansing SE allowed')),
                      str(_('Maximum number of re-examinations')),
                      str(_('Subject has no third period')),
                      str(_('Exemption without CE allowed')),
                      str(_('Last modified on ')), str(_('Last modified by'))]
    header_format = th_align_center

    row_formats = []
    for x in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        if 1 < x <  col_count - 2:
            row_formats.append(row_align_center)
        else:
            row_formats.append(row_align_left)

    row_index += 3
    # ---  table header row
    for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        sheet.write(row_index, i, field_captions[i], header_format)

    # ---  loop through scheme rows
    if len(schemeitem_rows):
        for row in schemeitem_rows:
            scheme_id = row.get('scheme_id')
            if scheme_id == scheme_pk:
                row_index += 1
                for i, field_name in enumerate(field_names):
                    if field_name == 'modifiedat':
                        modified_dte = row.get(field_name, '')
                        value = af.format_modified_at(modified_dte, user_lang)
                    elif field_name == 'gradetype':
                        gradetype = row.get(field_name)
                        if gradetype == 1:
                            value = str(_('Number'))
                        elif gradetype == 2:
                            value = 'o/v/g'
                        else:
                            value = ''
                    else:
                        value = row.get(field_name, '')
                        if isinstance(value, bool):
                            value = 'x' if value else ''

                    sheet.write(row_index, i, value, row_formats[i])

    return row_index
# --- end of create_subjecttype_paragraph_xlsx
