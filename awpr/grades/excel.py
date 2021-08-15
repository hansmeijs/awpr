import tempfile
from django.core.files import File

from django.db import connection

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotFound, FileResponse
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import View

from datetime import date, datetime, timedelta

from accounts import models as acc_mod
from awpr import constants as c
from awpr import functions as af
from awpr import downloads as dl
from awpr import settings as s
from subjects import views as subj_view

import xlsxwriter
import io
import logging
logger = logging.getLogger(__name__)


@method_decorator([login_required], name='dispatch')
class StudsubjDownloadEx1View(View):  # PR2021-01-24 PR2021-08-09

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= StudsubjDownloadEx1View ============= ')
        # function creates, Ex1 xlsx file based on settings in usersetting

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

# - get text from examyearsetting
                    settings = af.get_exform_text(sel_examyear, ['exform', 'ex1'])
                    #if logging_on:
                    #    logger.debug('settings: ' + str(settings))

# +++ get mapped_subject_rows    '
                    # function gets all subjects of studsubj of this dep, not tobedeleted
                    # - creates list of subject_codes and list of subject_pk's
                    # - both sorted by subjbase.code
                    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
                    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]
                    subject_row_count, subject_pk_list, subject_code_list = \
                        create_ex1_mapped_subject_rows(sel_examyear, sel_school, sel_department)

                    if logging_on:
                        logger.debug('subject_row_count: ' + str(subject_row_count))
                        logger.debug('subject_pk_list: ' + str(subject_pk_list))
                        logger.debug('subject_code_list: ' + str(subject_code_list))

    # +++ create ex1_xlsx
                    save_to_disk = False
                    published_instance = None
                    response = create_ex1_xlsx(
                        published_instance=published_instance,
                        examyear=sel_examyear,
                        school=sel_school,
                        department=sel_department,
                        settings=settings,
                        save_to_disk=save_to_disk,
                        subject_pk_list=subject_pk_list,
                        subject_code_list=subject_code_list,
                        user_lang=user_lang)
        #except:
        #    raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of StudsubjDownloadEx1View

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////
def create_ex1_xlsx(published_instance, examyear, school, department, settings, save_to_disk,
                    subject_pk_list, subject_code_list, user_lang):  # PR2021-02-13 PR2021-08-14
    # called by create_Ex1_form, StudsubjDownloadEx1View
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex1_xlsx -----')

# +++ get dict of students with list of studsubj_pk, grouped by levle_pk, with totals
    ex1_rows_dict = create_ex1_rows_dict(examyear, school, department, save_to_disk, published_instance)

    """
     ex1_rows_dict: {'total': {1050: 171, ..., 1069: 30},
      'auth1': [48], 'auth2': [57], 
      86: {'lvl_name': 'Praktisch Basisgerichte Leerweg', 
            'total': {1050: 89, ..., 1058: 56}, 
            'stud_list': [
                    {'idnr': '1998041505', 'exnr': 'V021', 'name': 'Albertus, Dinaida Lilian Jearette', 
                     'lvl': 'PBL', 'sct': 'z&w', 'cls': '4V2', 
                     'subj': [1050, 1055, 1051, 1047, 1065, 1057, 1054, 1052, 1048, 1070]},  
    """

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
        
         ex1_dict: 
        {'total': {1047: 175, ..., 1057: 7}, 
        'level_86': {'lvl_name': 'Praktisch Basisgerichte Leerweg', 
                    'total': {1047: ..., 1063: 23}, 
                    'stud_list': [
                        {'idnr': '2004101103', 'exnr': '21024', 'name': 'Balentien, Rayviendall', 'lvl': 'PBL', 'sct': 'tech', 'class': '4BH', 
                            'subj': [1047, 1048, 1049, 1050, 1051, 1052, 1055, 1056, 1060, 1070]}, 
                        {'idnr': '2002090102', 'exnr': '21025', 'name': 'Baromeo, Norshel', 'lvl': 'PBL', 'sct': 'tech', 'class': '4BH', 
                            'subj': [1047, 1048, 1049, 1050, 1051, 1052, 1055, 1056, 1060, 1070]}, ...}, 
    """

    response = None

    if settings and ex1_rows_dict:

        # PR2021-07-28 changed to file_dir = 'published/'
        # this one gives path: awpmedia / awpmedia / media / private / published
        # PR2021-08-06 create different folders for country and examyear
        # this one gives path: awpmedia / awpmedia / media / private / cur / 2022 / published
        # published_instance is None when downloading preliminary Ex1 form

        examyear_str = str(examyear.code)

        file_path = None
        if published_instance:

# ---  create file_path
            # PR2021-08-07 changed to file_dir = 'country/examyear/published/'
            # this one gives path:awpmedia/awpmedia/media/cur/2022/published
            country_abbrev = examyear.country.abbrev.lower()
            file_dir = '/'.join((country_abbrev, examyear_str, 'exfiles'))
            file_path = '/'.join((file_dir, published_instance.filename))
            file_name = published_instance.name

            if logging_on:
                logger.debug('file_dir: ' + str(file_dir))
                logger.debug('file_name: ' + str(file_name))
                logger.debug('filepath: ' + str(file_path))

# ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
        title = ' '.join( ('Ex1', str(examyear), school.base.code, today_dte.isoformat() ) )
        file_name = title + ".xlsx"
        worksheet_name = str(_('Ex1'))

# - Create an in-memory output file for the new workbook.
        # from https://docs.python.org/3/library/tempfile.html
        temp_file = tempfile.TemporaryFile()

        output = temp_file if save_to_disk else io.BytesIO()
        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        #  book = xlsxwriter.Workbook(response, {'in_memory': True})
        book = xlsxwriter.Workbook(output)
        sheet = book.add_worksheet(worksheet_name)
        if logging_on:
            logger.debug('output: ' + str(output))
            logger.debug('book: ' + str(book))
            logger.debug('sheet: ' + str(sheet))

# --- create format of Ex1 sheet
        ex1_formats = create_ex1_format_dict(book, sheet, school, department, subject_pk_list, subject_code_list)
        field_width = ex1_formats.get('field_width')
        bold_format = ex1_formats.get('bold_format')
        bold_blue = ex1_formats.get('bold_blue')
        normal_blue = ex1_formats.get('normal_blue')
        th_merge = ex1_formats.get('th_merge')
        th_exists = ex1_formats.get('th_exists')
        th_prelim  = ex1_formats.get('th_prelim')
        totalrow_merge = ex1_formats.get('totalrow_merge')
        col_count = ex1_formats.get('col_count', 0)
        first_subject_column =  ex1_formats.get('first_subject_column', 0)

# --- set column width
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
        lb_ex_key_str = ' '.join((  settings[lb_ex_key], department.abbrev, settings['in_examyear'], examyear_str))

        sheet.write(6, 0, lb_ex_key_str, bold_format)
        lb_school_key = 'school' if school.islexschool else 'school'
        sheet.write(7, 0, settings[lb_school_key], bold_format)
        sheet.write(7, 2, school.name, bold_blue)

# - put Ex1 in right upper corner
        #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        sheet.merge_range(0, col_count - 5, 1, col_count -1, 'EX.1', th_merge)

        row_index = 9
        if not save_to_disk:
            prelim_txt = '+++++  ' + str(_('Preliminary Ex1 form')) + '  +++++'
            sheet.merge_range(row_index, 0, row_index, col_count - 1, prelim_txt, th_prelim)
            row_index += 2

        #if has_published_ex1_rows(examyear, school, department):
        #    exists_txt = str(_('Attention: an Ex1 form has already been submitted. The subjects in that form are not included in this form.'))
        #    sheet.merge_range(row_index, 0, row_index, col_count - 1, exists_txt, th_exists)
        #    row_index += 1

# ---  table header row
        #for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        #    sheet.write(row_index, i, ex1_formats['field_captions'][i], ex1_formats['header_formats'][i])

# ++++++++++++++++++++++++++++
# iterate through levels, if more than 1 exist

        for key, level_dict in ex1_rows_dict.items():
            # skip ex1_rows_dict_totals
            if isinstance(key, int):
                # in subject column 'field_name' is subject_id
                lvl_name = level_dict.get('lvl_name')
                stud_list = level_dict.get('stud_list', [])
                lvl_totals = level_dict.get('total')

# ---  level header row
                row_index += 2
                #sheet.merge_range(row_index, 0, row_index, col_count - 1, lvl_name, th_level)
                for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
                    sheet.write(row_index, i, ex1_formats['field_captions'][i], ex1_formats['header_formats'][i])

                if len(stud_list):
                    for row in stud_list:

# ---  student rows
                        # row: {'idnr': '2004101103', 'exnr': '21024', 'name': 'Balentien, Rayviendall',
                        # 'lvl': 'PBL', 'sct': 'tech', 'class': '4BH', 'subj': [1047, 1048, 1049, 1050, 1051, 1052, 1055, 1056, 1060, 1070]}
                        row_index += 1
                        for i, field_name in enumerate(ex1_formats['field_names']):
                            value = ''
                            if isinstance(field_name, int):
                                # in subject column 'field_name' is subject_id
                                subj_id_list = row.get('subj', [])
                                if subj_id_list and field_name in subj_id_list:
                                    value = 'x'
                            else:
                                value = row.get(field_name, '')
                            sheet.write(row_index, i, value, ex1_formats['row_formats'][i])

# ---  level subtotal row
                # skip subtotal row in Havo/vwo,
                if department.level_req:
                    row_index += 1
                    for i, field_name in enumerate(ex1_formats['field_names']):
                        #logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
                        value = ''
                        if isinstance(field_name, int):
                            if field_name in lvl_totals:
                                value = lvl_totals.get(field_name)
                            sheet.write(row_index, i, value, ex1_formats['totalrow_formats'][i])
                            # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')
                        elif field_name == 'exnr':
                            #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                            sheet.merge_range(row_index, 0, row_index, first_subject_column -1, '???TOTAAL ' + lvl_name, totalrow_merge)
# end of iterate through levels,
# ++++++++++++++++++++++++++++

        total_dict = ex1_rows_dict.get('total', {})
# ---  table total row
        row_index += 1
        if department.level_req:
            row_index += 1
        for i, field_name in enumerate(ex1_formats['field_names']):
            #logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
            value = ''
            if isinstance(field_name, int):
                if field_name in total_dict:
                    value = total_dict.get(field_name)
                sheet.write(row_index, i, value, ex1_formats['totalrow_formats'][i])
                # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')
            elif field_name == 'exnr':
                #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                sheet.merge_range(row_index, 0, row_index, first_subject_column -1, 'TOTAAL', totalrow_merge)

# ---  table footer row
        row_index += 1
        for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
            if i == 0:
                sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', totalrow_merge)
            else:
                sheet.write(row_index, i, ex1_formats['field_captions'][i], ex1_formats['header_formats'][i])

# ---  footnote row
        row_index += 2
        first_footnote_row = row_index
        for i in range(1, 9):
            if school.islexschool and 'lex_footnote0' + str(i) in settings:
                key = 'lex_footnote0' + str(i)
            else:
                key = 'footnote0' + str(i)
            if key in settings:
                value = settings.get(key)
                if value:
                    sheet.write(row_index + i - 1, 0, value, bold_format)

# ---  digitally signed by
        auth_row = first_footnote_row
        if save_to_disk:
            sheet.write(auth_row, first_subject_column, str(_('Digitally signed by')) + ':')
            auth_row += 2
    # - President
            sheet.write(auth_row, first_subject_column, str(_('President')) + ':')
            auth1_list = ex1_rows_dict.get('auth1')
            if auth1_list:
                for auth1_pk in auth1_list:
                    auth1 = acc_mod.User.objects.get_or_none(pk=auth1_pk)
                    if auth1:
                        sheet.write(auth_row, first_subject_column + 4, auth1.last_name, normal_blue)
                        auth_row += 1
            else:
                auth_row += 1
            auth_row += 1
    # - Secretary
            sheet.write(auth_row, first_subject_column, str(_('Secretary')) + ':')
            auth2_list = ex1_rows_dict.get('auth2')
            if auth2_list:
                for auth2_pk in auth2_list:
                    auth2 = acc_mod.User.objects.get_or_none(pk=auth2_pk)
                    if auth2:
                        sheet.write(auth_row, first_subject_column + 4, auth2.last_name, normal_blue)
                        auth_row += 1
            else:
                auth_row += 1

            auth_row += 1

    # -  place, date
        sheet.write(auth_row, first_subject_column, 'Plaats:')
        sheet.write(auth_row, first_subject_column + 4, str(school.examyear.country.name),
                    normal_blue)
        sheet.write(auth_row, first_subject_column + 8, 'Datum:')
        sheet.write(auth_row, first_subject_column + 11, today_formatted, normal_blue)

        book.close()

# +++ save file to disk
        if save_to_disk:
            excel_file = File(temp_file)

            published_instance.file.save(file_path, excel_file)

            logger.debug('file_path: ' + str(file_path))
            # file_path: media/private/published/Ex2A CUR13 ATC Vsbo SE-tv1 cav 2021-04-29 10u11.pdf
            # stored in dir:
            logger.debug('published_instance.file: ' + str(published_instance.file))
        else:
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


def create_ex1_format_dict(book, sheet, school, department, subject_pk_list, subject_code_list): # PR2021-08-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex1_format_dict -----')

    sheet.hide_gridlines(2) # 2 = Hide screen and printed gridlines

    #cell_format = book.add_format({'bold': True, 'font_color': 'red'})
    bold_format = book.add_format({'bold': True})
    bold_blue = book.add_format({'font_color': 'blue', 'bold': True})
    normal_blue = book.add_format({'font_color': 'blue'})

    # th_format.set_bg_color('#d8d8d8') #   #d8d8d8;  /* light grey 218 218 218 100%
    # or: th_format = book.add_format({'bg_color': '#d8d8d8'
    th_align_center = book.add_format({'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    th_rotate = book.add_format({'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'rotation': 90})
    th_prelim = book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})

    th_merge = book.add_format({ 'bold': True, 'align': 'center', 'valign': 'vcenter'})
    th_merge.set_left()
    th_merge.set_bottom()

    th_exists = book.add_format({'bold': False, 'align': 'left', 'valign': 'vcenter'})

    row_align_left = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter','border': True})
    row_align_center = book.add_format({'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter','border': True})

    totalrow_align_center = book.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'border': True})
    totalrow_number = book.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'border': True})
    totalrow_merge = book.add_format({'font_size': 8, 'border': True, 'align': 'right', 'valign': 'vcenter'})

    # get number of columns
    # columns are (0: 'examnumber', 1: idnumber, 2: name 3: 'class' 4: level "
    # columns 5 thru 19 are subject columns. Extend number when more than 15 subjects

    is_lexschool = school.islexschool
    level_req = department.level_req
    sector_req = department.sector_req
    has_profiel = department.has_profiel

# - add standard columns: exnr, idnumber and fullname
    col_count = 3
    field_width = [10, 12, 35]

    ex1_formats = {'field_names': ['exnr', 'idnr', 'name'],
                   'field_captions': ['Ex.nr.', 'ID-nummer', 'Naam en voorletters van de kandidaat\n(in alfabetische volgorde)'],
                    'header_formats': [th_align_center, th_align_center, th_align_center],
                    'row_formats': [row_align_center, row_align_center, row_align_left],
                    'totalrow_formats': [totalrow_merge, totalrow_align_center, totalrow_align_center],
                    'bold_format': bold_format,
                   'bold_blue': bold_blue,
                   'normal_blue': normal_blue,
                   'th_merge': th_merge,
                   'th_exists': th_exists,
                   'th_prelim': th_prelim,
                   'totalrow_merge': totalrow_merge
    }

# - add column class, not when lex school
    if not is_lexschool:
        col_count += 1
        field_width.append(10)
        ex1_formats['field_names'].append('cls')
        ex1_formats['field_captions'].append('Klas')
        ex1_formats['header_formats'].append(th_align_center)
        ex1_formats['row_formats'].append(row_align_center)
        ex1_formats['totalrow_formats'].append(totalrow_align_center)

# - add column 'Leerweg' if level_req
    if level_req:  # add column if level_req
        col_count += 1
        field_width.append(5)
        ex1_formats['field_names'].append('lvl')
        ex1_formats['field_captions'].append('Leer-\nweg')
        ex1_formats['header_formats'].append(th_align_center)
        ex1_formats['row_formats'].append(row_align_center)
        ex1_formats['totalrow_formats'].append(totalrow_align_center)

# - add column 'Profiel' or 'Sector' if sector_req (is always the case)
    if sector_req:
        col_count += 1
        field_width.append(7)
        caption = 'Profiel' if has_profiel else 'Sector'
        ex1_formats['field_names'].append('sct')
        ex1_formats['field_captions'].append(caption)
        ex1_formats['header_formats'].append(th_align_center)
        ex1_formats['row_formats'].append(row_align_center)
        ex1_formats['totalrow_formats'].append(totalrow_align_center)

# - add subject columns. Amount of subject columns = length of subject_pk_list
    first_subject_column = col_count
    subject_col_count = len(subject_pk_list)
    subject_col_width = 2.86
    for x in range(0, subject_col_count):  # range(start_value, end_value, step), end_value is not included!
        field_width.append(subject_col_width)
        subject_pk = subject_pk_list[x]
        subject_code = subject_code_list[x] if subject_code_list[x] else ''
        ex1_formats['field_captions'].append(subject_code)
        ex1_formats['field_names'].append(subject_pk)
        ex1_formats['header_formats'].append(th_rotate)
        ex1_formats['row_formats'].append(row_align_center)
        ex1_formats['totalrow_formats'].append(totalrow_number)

        col_count += 1

    # - add empty subject columns if col_count is less than 15
    if subject_col_count < 15:
        for x in range(subject_col_count, 15):  # range(start_value, end_value, step), end_value is not included!
            field_width.append(subject_col_width)
            subject_code = ''
            # was: subject_pk = 0
            subject_pk = '0'
            ex1_formats['field_captions'].append(subject_code)
            ex1_formats['field_names'].append(subject_pk)
            ex1_formats['header_formats'].append(th_rotate)
            ex1_formats['row_formats'].append(row_align_center)
            ex1_formats['totalrow_formats'].append(totalrow_number)

        col_count += 1

    ex1_formats['col_count'] = col_count
    ex1_formats['first_subject_column'] = first_subject_column
    ex1_formats['field_width'] = field_width

    return ex1_formats
# - end of create_ex1_format_dict


def create_ex1_rows_dict(examyear, school, department, save_to_disk, published_instance):  # PR2021-08-15
    # this function is only called by create_ex1_xlsx
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex1_rows_dict -----')
    # function creates dictlist of all students of this examyear, school and department
    #  key 'subj_id_arr' contains list of all studentsubjects of this student, not tobedeleted
    #  skip studsubjects that are not fully approved
    level_req = department.level_req

    # dont show students without subjects when Ex-form is submitted
    exclude_students_without_subjects = save_to_disk
    inner_or_left_join_studsubj = "INNER JOIN" if exclude_students_without_subjects else "LEFT JOIN"

    # dont filter on published or approved subject when printing preliminary Ex1 (in that case save_to_disk = False


# PR2021-08-10 dont include null in  ARRAY_AGG
# from https://stackoverflow.com/questions/13122912/how-to-exclude-null-values-in-array-agg-like-in-string-agg-using-postgres

    # dont filter on published or approved subject when printing preliminary Ex1 (in that case save_to_disk = False

    # when submitting Ex1 form:
    # - exclude studsubj that are already published
    # - exclude studsubj that are not fully approved
    # - exclude deleted studsubj
    # TODO find a way to include tobedeleted in Ex form

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk, 'publ_id': published_instance.pk}

    sql_studsubj_agg_list = [
        "SELECT studsubj.student_id AS student_id,",
        "ARRAY_AGG(si.subject_id) AS subj_id_arr,",
        "ARRAY_AGG(DISTINCT studsubj.subj_auth1by_id) FILTER (WHERE studsubj.subj_auth1by_id is not null) AS subj_auth1_arr,",
        "ARRAY_AGG(DISTINCT studsubj.subj_auth2by_id) FILTER (WHERE studsubj.subj_auth2by_id is not null) AS subj_auth2_arr",
        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "WHERE NOT studsubj.tobedeleted"]
    if save_to_disk:
        # when submitting an Ex1 form published_instance is already saved, therefore published_instance.pk has a value
        # filter on published_instance.pk, so only subjects of this submit will ne added to Xe1 form
        sql_studsubj_agg_list.append("AND studsubj.subj_published_id = %(publ_id)s::INT")

    sql_studsubj_agg_list.append("GROUP BY studsubj.student_id")

    sql_studsubj_agg = ' '.join(sql_studsubj_agg_list)

    if logging_on:
        logger.debug('sql_studsubj_agg: ' + str(sql_studsubj_agg))
        with connection.cursor() as testcursor:
            testcursor.execute(sql_studsubj_agg, sql_keys)
            rows = af.dictfetchall(testcursor)
            for row in rows:
                logger.debug('row: ' + str(row))

    sql_list = ["WITH studsubj AS (" , sql_studsubj_agg, ")",
        "SELECT st.id, st.idnumber, st.examnumber, st.lastname, st.firstname, st.prefix, st.classname,",
        "st.level_id, lvl.name AS lvl_name, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,",
        "studsubj.subj_id_arr, studsubj.subj_auth1_arr, studsubj.subj_auth2_arr",
        "FROM students_student AS st",
        inner_or_left_join_studsubj, "studsubj ON (studsubj.student_id = st.id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
        "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
    ]
    if level_req:
        sql_list.append("ORDER BY LOWER(lvl.abbrev), LOWER(st.lastname), LOWER(st.firstname)")
    else:
        sql_list.append("ORDER BY LOWER(st.lastname), LOWER(st.firstname)")
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

        # logger.debug('connection.queries: ' + str(connection.queries))

    ex1_rows_dict = {'total': {}, 'auth1': [], 'auth2': []}
    ex1_total = ex1_rows_dict.get('total')
    ex1_auth1 = ex1_rows_dict.get('auth1')
    ex1_auth2 = ex1_rows_dict.get('auth2')

    for row in rows:

        #  row: {
        #  'id': 3309, 'idnumber': '2004101103', 'examnumber': '21024', 'lastname': 'Balentien', 'firstname': 'Rayviendall', 'prefix': None,
        #  'classname': '4BH', 'level_id': 86, 'sector_id': 180, 'lvl_abbrev': 'PBL', 'sct_abbrev': 'tech',
        #  'subj_id_arr': [1047, 1048, 1049, 1050, 1051, 1052, 1055, 1056, 1060, 1070]}

        # value is '0' when lvlbase_id = None (Havo/Vwo)
        level_pk = row.get('level_id')
        if level_pk is None:
            level_pk = 0

        lvl_name = ''
        if level_pk:
            lvl_name = row.get('lvl_name', '---')
        elif level_req:
            lvl_name = str(_("Candidates, whose 'leerweg' is not entered"))

        if level_pk not in ex1_rows_dict:
            ex1_rows_dict[level_pk] = {'lvl_name': lvl_name, 'total': {}, 'stud_list': []}

        level_dict = ex1_rows_dict[level_pk]
        level_total = level_dict.get('total')
        level_studlist = level_dict.get('stud_list')

        idnumber = row.get('idnumber' ,'---')
        examnumber = row.get('examnumber' ,'---')
        classname = row.get('classname' ,'')
        lvl_abbrev = row.get('lvl_abbrev' ,'---')
        sct_abbrev = row.get('sct_abbrev' ,'---')

        prefix = row.get('prefix')
        lastname = row.get('lastname', '')
        firstname = row.get('firstname', '')
        if prefix:
            lastname = ' '.join((prefix, lastname))
        fullname = ''.join((lastname, ', ', firstname))

        subj_id_arr = row.get('subj_id_arr', [])
        student_dict = {'idnr': idnumber, 'exnr': examnumber, 'name': fullname,
                        'lvl': lvl_abbrev, 'sct': sct_abbrev, 'cls': classname, 'subj': subj_id_arr}
        level_studlist.append(student_dict)

        if subj_id_arr:
            for subject_pk in subj_id_arr:
                if subject_pk not in level_total:
                    level_total[subject_pk] = 1
                else:
                    level_total[subject_pk] += 1
                if subject_pk not in ex1_total:
                    ex1_total[subject_pk] = 1
                else:
                    ex1_total[subject_pk] += 1

        subj_auth1_arr = row.get('subj_auth1_arr', [])
        if subj_auth1_arr:
            for auth1_pk in subj_auth1_arr:
                if auth1_pk not in ex1_auth1:
                    ex1_auth1.append(auth1_pk)

        subj_auth2_arr = row.get('subj_auth2_arr', [])
        if subj_auth2_arr:
            for auth2_pk in subj_auth2_arr:
                if auth2_pk not in ex1_auth2:
                    ex1_auth2.append(auth2_pk)
        if logging_on:
            logger.debug('row: ' + str(row))
            logger.debug('subj_id_arr: ' + str(subj_id_arr))

    if logging_on:
       logger.debug('-----------------------------------------------')
       #logger.debug('ex1_rows_dict: ' + str(ex1_rows_dict))

    return ex1_rows_dict
# --- end of create_ex1_rows_dict


def create_ex1_mapped_subject_rows(examyear, school, department):  # PR2021-08-08
    # function gets all subjects of studsubj of this dep, not tobedeleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]

    subject_code_list = []
    subject_pk_list = []
    sql_list = [
        "SELECT subj.id, subjbase.code",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT AND NOT studsubj.tobedeleted",
        "GROUP BY subj.id, subjbase.code",
        "ORDER BY LOWER(subjbase.code)"
    ]
    sql = ' '.join(sql_list)

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        row_count = 0
        subject_rows = cursor.fetchall()
        for subject_row in subject_rows:
            #subject_pk_dict[subject_row[0]] = index
            subject_pk_list.append(subject_row[0])
            subject_code_list.append(subject_row[1])
            row_count += 1

    return row_count, subject_pk_list, subject_code_list
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


def create_orderlist_mapped_subject_rows(examyear, examperiod_int, is_ete_exam, otherlang):  # PR2021-08-09
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug ('----- create_orderlist_mapped_subject_rows -----')
        logger.debug('examperiod_int: ' + str(examperiod_int))
        logger.debug('is_ete_exam: ' + str(is_ete_exam))
        logger.debug('otherlang: ' + str(otherlang))

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

        "WHERE ey.code = %(ey_int)s::INT AND NOT studsubj.tobedeleted",
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

    if logging_on:
        logger.debug ('----- create_orderlist_mapped_subject_rows -----')
        logger.debug('subjectbase_pk_list: ' + str(subjectbase_pk_list))
        logger.debug('subjectbase_code_list: ' + str(subjectbase_code_list))

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

        "WHERE ey.code = %(ey_int)s::INT AND NOT studsubj.tobedeleted",
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
                    scheme_rows = subj_view.create_scheme_rows(
                        examyear=sel_examyear,
                        scheme_pk=sel_scheme_pk)
                    subjecttype_rows = subj_view.create_subjecttype_rows(
                        examyear=sel_examyear,
                        scheme_pk=sel_scheme_pk,
                        orderby_sequence=True)
                    schemeitem_rows = subj_view.create_schemeitem_rows(
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
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_schemeitem_paragraph_xlsx  ----- ')
        logger.debug('row_index: ' + str(row_index))

    # get number of columns
    field_names = ['subj_name', 'subj_code', 'sjtp_abbrev', 'gradetype',
                   'weight_se', 'weight_ce',
                   'is_mandatory', 'is_mand_subj',
                   'is_combi', 'is_core_subject', 'is_mvt',
                   'extra_count_allowed', 'extra_nocount_allowed',
                   'elective_combi_allowed',
                   'has_practexam', 'has_pws',
                   'reex_se_allowed', 'max_reex',
                   'no_thirdperiod', 'no_exemption_ce',
                   'modifiedat', 'modby_username']

    col_count = len(field_names)
    if logging_on:
        logger.debug('col_count: ' + str(col_count))

    field_captions = [str(_('Subjects of this subject scheme')), str(_('Abbreviation')),
                      str(_('Subject type')), str(_('Grade type')),
                      str(_('SE weight')), str(_('CE weight')),
                      str(_('Mandatory')),  str(_("'Mandatory-if' subject")),
                      str( _('Combination subject')), str(_('Core subject')), str(_('MVT subject')),
                      str(_('Extra subject counts allowed')), str(_('Extra subject does not count allowed')),
                      str(_('Elective combi subject allowed')),
                      str(_('Has practical exam')), str(_('Has assignment')),
                      str(_('Herkansing SE allowed')), str(_('Maximum number of re-examinations')),
                      str(_('Subject has no third period')), str(_('Exemption without CE allowed')),
                      str(_('Last modified on ')), str(_('Last modified by'))]
    header_format = th_align_center

    row_formats = []
    for x in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        if 1 < x < col_count - 2:
            row_formats.append(row_align_center)
        else:
            row_formats.append(row_align_left)

    row_index += 3
    # ---  table header row
    for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        if logging_on:
            logger.debug('i: ' + str(i))
            logger.debug('field_captions[i]: ' + str(field_captions[i]))
        sheet.write(row_index, i, field_captions[i], header_format)
    if logging_on:
        logger.debug('field_captions end ')
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

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# NOT IN USE (was for msg on Ex1: 'Attention: an Ex1 form has already been submitted. The subjects in that form are not included in this form.'
def has_published_ex1_rows(examyear, school, department):  # PR2021-08-15
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- has_published_ex1_rows -----')
    # function checks if there are already published row, to give message in preliminary Ex1 form
    # PR2021-08-15
    # from https://www.postgresqltutorial.com/postgresql-exists/

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}
    sql_list = ["SELECT EXISTS("
        "SELECT 1",
        "FROM students_studentsubject AS studsubj",
        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
        "AND NOT studsubj.tobedeleted AND studsubj.subj_published_id IS NOT NULL"
        ")",
    ]
    sql = ' '.join(sql_list)
    exists = False
    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        row = cursor.fetchone()
        # row = (False,)
        if row:
            exists = row[0]
    if logging_on:
       logger.debug(' exists: ' + str(exists))

    return exists
# --- end of has_published_ex1_rows

