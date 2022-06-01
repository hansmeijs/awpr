import os
import tempfile
from django.core.files import File

from django.db import connection

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect  # , Http404, HttpResponseNotFound, FileResponse
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext_lazy as _
from django.utils import timezone
from django.views.generic import View

from os.path import basename

from accounts import models as acc_mod
from accounts import  views as acc_view
from awpr import constants as c
from awpr import functions as af
from awpr import downloads as dl
from awpr import settings as s
from awpr import library as awpr_lib

from schools import models as sch_mod
from subjects import views as subj_view

import xlsxwriter
from zipfile import ZipFile
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

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

            # - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)

            if sel_examyear and sel_school and sel_department:
                # - get text from examyearsetting
                settings = awpr_lib.get_library(sel_examyear, ['exform', 'ex1'])

                # +++ create ex1_xlsx
                save_to_disk = False
                # just to prevent PyCharm warning on published_instance=published_instance
                published_instance = sch_mod.School.objects.get_or_none(pk=None)
                response = create_ex1_xlsx(
                    published_instance=published_instance,
                    examyear=sel_examyear,
                    school=sel_school,
                    department=sel_department,
                    examperiod=c.EXAMPERIOD_FIRST,
                    prefix='subj_',
                    settings=settings,
                    save_to_disk=save_to_disk,
                    request=request,
                    user_lang=user_lang)

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# - end of StudsubjDownloadEx1View


@method_decorator([login_required], name='dispatch')
class StudsubjDownloadEx4View(View):  # PR2022-05-27

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= StudsubjDownloadEx4View ============= ')
        # function creates, Ex1 xlsx file based on settings in usersetting

        response = None

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

            # - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)

            if sel_examyear and sel_school and sel_department:
                # TODO add third period
                examperiod = c.EXAMPERIOD_SECOND
                prefix = 'reex3_' if examperiod == 3 else 'reex_' if examperiod == 2 else 'subj_'

# +++ create ex4_xlsx
                save_to_disk = False
                # just to prevent PyCharm warning on published_instance=published_instance
                published_instance = sch_mod.School.objects.get_or_none(pk=None)
                response = create_ex4_xlsx(
                    published_instance=published_instance,
                    examyear=sel_examyear,
                    school=sel_school,
                    department=sel_department,
                    examperiod=examperiod,
                    prefix=prefix,
                    save_to_disk=save_to_disk,
                    request=request,
                    user_lang=user_lang)

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of StudsubjDownloadEx4View


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////
def create_ex1_xlsx(published_instance, examyear, school, department, examperiod, prefix, settings, save_to_disk, request,
                    user_lang):  # PR2021-02-13 PR2021-08-14
    # called by StudentsubjectApproveOrSubmitEx1Ex4View.create_ex1_ex4_form, StudsubjDownloadEx1View
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex1_xlsx -----')

    # +++ get mapped_subject_rows    '
    # function gets all subjects of studsubj of this dep, not tobedeleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]
    subject_row_count, subject_pk_list, subject_code_list = \
        create_ex1_Ex4_mapped_subject_rows(examyear, school, department)

    if logging_on:
        logger.debug('subject_row_count: ' + str(subject_row_count))
        logger.debug('subject_pk_list: ' + str(subject_pk_list))
        logger.debug('subject_code_list: ' + str(subject_code_list))

    # +++ get dict of students with list of studsubj_pk, grouped by level_pk, with totals
    ex1_rows_dict = create_ex1_ex4_rows_dict(
        examyear=examyear,
        school=school,
        department=department,
        save_to_disk=save_to_disk,
        examperiod=examperiod,
        prefix=prefix,
        published_instance=published_instance
    )

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
    # logger.debug('period_dict: ' + str(period_dict))

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
            requsr_school = sch_mod.School.objects.get_or_none(
                base=request.user.schoolbase,
                examyear=examyear
            )
            requsr_schoolcode = requsr_school.base.code if requsr_school.base.code else '---'
            country_abbrev = examyear.country.abbrev.lower()
            file_dir = '/'.join((country_abbrev, examyear_str, requsr_schoolcode, 'exfiles'))
            file_path = '/'.join((file_dir, published_instance.filename))
            file_name = published_instance.name

            if logging_on:
                logger.debug('file_dir: ' + str(file_dir))
                logger.debug('file_name: ' + str(file_name))
                logger.debug('filepath: ' + str(file_path))

        # ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
        title = ' '.join(('Ex1', str(examyear), school.base.code, today_dte.isoformat()))
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
        ex1_formats = create_ex1_ex4_format_dict(book, sheet, school, department, subject_pk_list, subject_code_list)
        field_width = ex1_formats.get('field_width')
        bold_format = ex1_formats.get('bold_format')
        bold_blue = ex1_formats.get('bold_blue')
        normal_blue = ex1_formats.get('normal_blue')
        th_merge_bold = ex1_formats.get('th_merge_bold')
        th_exists = ex1_formats.get('th_exists')
        th_prelim = ex1_formats.get('th_prelim')
        totalrow_merge = ex1_formats.get('totalrow_merge')
        col_count = len(ex1_formats['field_width'])
        first_subject_column = ex1_formats.get('first_subject_column', 0)

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
        lb_ex_key_str = ' '.join((settings[lb_ex_key], department.abbrev, settings['in_examyear'], examyear_str))

        sheet.write(6, 0, lb_ex_key_str, bold_format)
        lb_school_key = 'school' if school.islexschool else 'school'
        sheet.write(7, 0, settings[lb_school_key], bold_format)
        sheet.write(7, 2, school.name, bold_blue)

        # - put Ex1 in right upper corner
        #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        sheet.merge_range(0, col_count - 5, 1, col_count - 1, 'EX.1', th_merge_bold)

        row_index = 9
        if not save_to_disk:
            prelim_txt = 'VOORLOPIG Ex1 FORMULIER'
            sheet.merge_range(row_index, 0, row_index, col_count - 1, prelim_txt, th_prelim)
            row_index += 1

        # if has_published_ex1_rows(examyear, school, department):
        #    exists_txt = str(_('Attention: an Ex1 form has already been submitted. The subjects in that form are not included in this form.'))
        #    sheet.merge_range(row_index, 0, row_index, col_count - 1, exists_txt, th_exists)
        #    row_index += 1

        # ---  table header row
        # for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
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
                # sheet.merge_range(row_index, 0, row_index, col_count - 1, lvl_name, th_level)    first_subject_column = col_count

                for i, field_caption in enumerate(ex1_formats['field_captions']):
                    sheet.write(row_index, i, field_caption, ex1_formats['header_formats'][i])

                if len(stud_list):
                    for row in stud_list:

                        # ---  student rows
                        # row: {'idnr': '2004101103', 'exnr': '21024', 'name': 'Balentien, Rayviendall',
                        # 'lvl': 'PBL', 'sct': 'tech', 'class': '4BH', 'subj': [1047, 1048, 1049, 1050, 1051, 1052, 1055, 1056, 1060, 1070]}
                        row_index += 1
                        for i, field_name in enumerate(ex1_formats['field_names']):
                            exc_format = ex1_formats['row_formats'][i]
                            value = ''
                            if isinstance(field_name, int):
                                # in subject column 'field_name' is subject_id
                                # subj_id_list = row.get('subj', [])
                                # if subj_id_list and field_name in subj_id_list:
                                #    value = 'x'

                                subj_nondel_list = row.get('subj_nondel', [])
                                if subj_nondel_list and field_name in subj_nondel_list:
                                    value = 'x'
                                    # PR2022-03-05 tobedeleted is deprecated. Was:
                                    # value = 'o'
                                # subj_del_list = row.get('subj_del', [])
                                # if subj_del_list and field_name in subj_del_list:
                                #    value = 'x'
                                #    exc_format = ex1_formats['row_align_center_red']
                            else:
                                value = row.get(field_name, '')
                            sheet.write(row_index, i, value, exc_format)

                # ---  level subtotal row
                # skip subtotal row in Havo/vwo,
                if department.level_req:
                    row_index += 1
                    for i, field_name in enumerate(ex1_formats['field_names']):
                        value = ''
                        if field_name == 'exnr':
                            #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                            sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, 'TOTAAL ' + lvl_name,
                                              totalrow_merge)
                        else:
                            if isinstance(field_name, int):
                                if field_name in lvl_totals:
                                    value = lvl_totals.get(field_name)
                            sheet.write(row_index, i, value, ex1_formats['totalrow_formats'][i])
                            # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')

        # end of iterate through levels,
        # ++++++++++++++++++++++++++++

        total_dict = ex1_rows_dict.get('total') or {}
        # ---  table total row
        row_index += 1
        if department.level_req:
            row_index += 1
        for i, field_name in enumerate(ex1_formats['field_names']):
            # logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
            value = ''
            if field_name == 'exnr':
                #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, 'TOTAAL', totalrow_merge)
            else:
                if isinstance(field_name, int):
                    if field_name in total_dict:
                        value = total_dict.get(field_name)
                sheet.write(row_index, i, value, ex1_formats['totalrow_formats'][i])
                # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')

# ---  table footer row
        row_index += 1
        for i, field_name in enumerate(ex1_formats['field_names']):
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
        # PR2022-05-31 also show signatures on preliminary Ex1 form
        auth_row = first_footnote_row
        if save_to_disk or True:
            sheet.write(auth_row, first_subject_column, str(_('Digitally signed by')) + ':')
            auth_row += 2
            # - Chairperson
            sheet.write(auth_row, first_subject_column, str(_('Chairperson')) + ':')
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

            # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
            published_instance.save(request=request)

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


#//////////////////////////////////////////////////////////////////////////////////////////////////////////////
def create_ex4_xlsx(published_instance, examyear, school, department, examperiod, prefix, save_to_disk, request, user_lang):  # PR2021-02-13 PR2021-08-14
    # called by StudsubjDownloadEx4View
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex4_xlsx -----')

# +++ get mapped_subject_rows    '
    # function gets all subjects of studsubj of this dep, not tobedeleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]
    subject_row_count, subject_pk_list, subject_code_list = \
        create_ex1_Ex4_mapped_subject_rows(examyear, school, department, True)  # is_reex=True

    if logging_on:
        logger.debug('subject_row_count: ' + str(subject_row_count))
        logger.debug('subject_pk_list: ' + str(subject_pk_list))
        logger.debug('subject_code_list: ' + str(subject_code_list))

# +++ get dict of students with list of studsubj_pk, grouped by level_pk, with totals
    ex4_rows_dict = create_ex1_ex4_rows_dict(
        examyear=examyear,
        school=school,
        department=department,
        save_to_disk=save_to_disk,
        examperiod=examperiod,
        prefix=prefix,
        published_instance=published_instance
    )

    if logging_on:
        logger.debug('ex4_rows_dict: ' + str(ex4_rows_dict))

    """
     ex1_rows_dict: {'total': {1050: 171, ..., 1069: 30},
      'auth1': [48], 'auth2': [57], 
      86: {'lvl_name': 'Praktisch Basisgerichte Leerweg', 
            'total': {1050: 89, ..., 1058: 56}, 
            'stud_list': [
                    {'idnr': '1998041505', 'exnr': 'V021', 'name': 'Albertus, Dinaida Lilian Jearette', 
                     'lvl': 'PBL', 'sct': 'z&w', 'cls': '4V2', 
                     'subj': [1050, 1055, 1051, 1047, 1065, 1057, 1054, 1052, 1048, 1070]},  

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

    # - get text from examyearsetting
    settings = awpr_lib.get_library(examyear, ['exform', 'ex4'])

    if settings and ex4_rows_dict:

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
            requsr_school = sch_mod.School.objects.get_or_none(
                base=request.user.schoolbase,
                examyear=examyear
            )
            requsr_schoolcode = requsr_school.base.code if requsr_school.base.code else '---'
            country_abbrev = examyear.country.abbrev.lower()
            file_dir = '/'.join((country_abbrev, examyear_str, requsr_schoolcode, 'exfiles'))
            file_path = '/'.join((file_dir, published_instance.filename))
            file_name = published_instance.name

            if logging_on:
                logger.debug('file_dir: ' + str(file_dir))
                logger.debug('file_name: ' + str(file_name))
                logger.debug('filepath: ' + str(file_path))

# ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
        title = ' '.join( ('Ex4', str(examyear), school.base.code, today_dte.isoformat() ) )
        file_name = title + ".xlsx"
        worksheet_name = str(_('Ex4'))

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

# --- create format of Ex4 sheet
        ex4_formats = create_ex1_ex4_format_dict(book, sheet, school, department, subject_pk_list, subject_code_list)
        field_width = ex4_formats.get('field_width')
        bold_format = ex4_formats.get('bold_format')
        bold_blue = ex4_formats.get('bold_blue')
        normal_blue = ex4_formats.get('normal_blue')
        th_merge_bold = ex4_formats.get('th_merge_bold')
        th_merge_normal = ex4_formats.get('th_merge_normal')
        th_exists = ex4_formats.get('th_exists')
        th_prelim  = ex4_formats.get('th_prelim')
        totalrow_merge = ex4_formats.get('totalrow_merge')
        col_count = len(ex4_formats['field_width'])
        first_subject_column =  ex4_formats.get('first_subject_column', 0)
        th_align_center = ex4_formats.get('th_align_center')

# --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

        """
        'Regel 0:   MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT
        'Regel 1:   Lijst van kandidaten voor het herexamen.
        'Regel 2:   (Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54).
        'Regel 3:   Tevens lijst van kandidaten, die om een geldige reden verhinderd waren het examen te voltooien.
        'Regel 4:   Direct na elke uitslag inzenden naar de Onderwijs Inspectie en digitaal naar het ETE
        'Regel 5:   
        'Regel 6:   EINDEXAMEN H.A.V.O. in het examenjaar 2021
        'Regel 7:   School:
        'Regel 8:
        'Regel 9:  "Examen Nr"
        """
# --- title row
        # was: sheet.write(0, 0, str(_('Report')) + ':', bold)
        title_str =  settings['ex4_title_reex03'] if examperiod == 3 else settings['ex4_title']
        sheet.write(0, 0, settings['minond'], bold_format)
        sheet.write(1, 0, title_str, bold_format)

        key_str = 'ex4_lex_article' if school.islexschool else 'ex4_eex_article'
        sheet.write(2, 0, settings[key_str], bold_format)

        sheet.write(3, 0, settings['ex4_tevens_lijst'], bold_format)

        key_str = 'ex4_lex_submit' if school.islexschool else 'ex4_eex_submit'
        sheet.write(4, 0, settings[key_str], bold_format)

        lb_ex_key = 'lex' if school.islexschool else 'eex'
        lb_ex_key_str = ' '.join((  settings[lb_ex_key], department.abbrev, settings['in_examyear'], examyear_str))

        sheet.write(6, 0, lb_ex_key_str, bold_format)
        lb_school_key = 'school' if school.islexschool else 'school'
        sheet.write(7, 0, settings[lb_school_key], bold_format)
        sheet.write(7, 2, school.name, bold_blue)

# - put Ex4 in right upper corner
        #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        sheet.merge_range(0, col_count - 5, 1, col_count -1, 'EX.4', th_merge_bold)

        row_index = 9
        if not save_to_disk:
            prelim_txt = 'VOORLOPIG Ex4 FORMULIER'
            if examperiod == 3:
                prelim_txt += ' DERDE TIJDVAK'
            sheet.merge_range(row_index, 0, row_index, col_count - 1, prelim_txt, th_prelim)
            row_index += 1

        #if has_published_ex1_rows(examyear, school, department):
        #    exists_txt = str(_('Attention: an Ex1 form has already been submitted. The subjects in that form are not included in this form.'))
        #    sheet.merge_range(row_index, 0, row_index, col_count - 1, exists_txt, th_exists)
        #    row_index += 1

# ---  table header row
        #for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        #    sheet.write(row_index, i, ex4_formats['field_captions'][i], ex4_formats['header_formats'][i])

# ++++++++++++++++++++++++++++
# iterate through levels, if more than 1 exist

        for key, level_dict in ex4_rows_dict.items():
            # skip ex4_rows_dict_totals
            if isinstance(key, int):
                # in subject column 'field_name' is subject_id
                lvl_name = level_dict.get('lvl_name')
                stud_list = level_dict.get('stud_list', [])
                lvl_totals = level_dict.get('total')

# ---  level header row
                row_index += 2
                #sheet.merge_range(row_index, 0, row_index, col_count - 1, lvl_name, th_level)    first_subject_column = col_count

                for i, field_caption in enumerate(ex4_formats['field_captions']):
                     sheet.write(row_index, i, field_caption, ex4_formats['header_formats'][i])

                if len(stud_list):
                    for row in stud_list:

# ---  student rows
                        # row: {'idnr': '2004101103', 'exnr': '21024', 'name': 'Balentien, Rayviendall',
                        # 'lvl': 'PBL', 'sct': 'tech', 'class': '4BH', 'subj': [1047, 1048, 1049, 1050, 1051, 1052, 1055, 1056, 1060, 1070]}
                        row_index += 1
                        for i, field_name in enumerate(ex4_formats['field_names']):
                            exc_format = ex4_formats['row_formats'][i]
                            value = ''
                            if isinstance(field_name, int):
                                # in subject column 'field_name' is subject_id
                                #subj_id_list = row.get('subj', [])
                                #if subj_id_list and field_name in subj_id_list:
                                #    value = 'x'

                                subj_nondel_list = row.get('subj_nondel', [])
                                if subj_nondel_list and field_name in subj_nondel_list:
                                    value = 'x'
                                    # PR2022-03-05 tobedeleted is deprecated. Was:
                                    #value = 'o'
                                #subj_del_list = row.get('subj_del', [])
                                #if subj_del_list and field_name in subj_del_list:
                                #    value = 'x'
                                #    exc_format = ex4_formats['row_align_center_red']
                            else:
                                value = row.get(field_name, '')
                            sheet.write(row_index, i, value, exc_format)

# ---  level subtotal row
                # skip subtotal row in Havo/vwo,
                if department.level_req:
                    row_index += 1
                    for i, field_name in enumerate(ex4_formats['field_names']):
                        value = ''
                        if field_name == 'exnr':
                            #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                            sheet.merge_range(row_index, 0, row_index, first_subject_column -1, 'TOTAAL ' + lvl_name, totalrow_merge)
                        else:
                            if isinstance(field_name, int):
                                if field_name in lvl_totals:
                                    value = lvl_totals.get(field_name)
                            sheet.write(row_index, i, value, ex4_formats['totalrow_formats'][i])
                            # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')

# end of iterate through levels,
# ++++++++++++++++++++++++++++

        total_dict = ex4_rows_dict.get('total') or {}

# ---  table total row
        row_index += 1
        if department.level_req:
            row_index += 1
        for i, field_name in enumerate(ex4_formats['field_names']):
            #logger.debug('field_name: ' + str(field_name) + ' ' + str(type(field_name)))
            value = ''
            if field_name == 'exnr':
                #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
                sheet.merge_range(row_index, 0, row_index, first_subject_column -1, 'TOTAAL', totalrow_merge)
            else:
                if isinstance(field_name, int):
                    if field_name in total_dict:
                        value = total_dict.get(field_name)
                sheet.write(row_index, i, value, ex4_formats['totalrow_formats'][i])
                # sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')

# ---  table footer row
        row_index += 1
        for i, field_name in enumerate(ex4_formats['field_names']):
            if i == 0:
                sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', totalrow_merge)
            else:
                sheet.write(row_index, i, ex4_formats['field_captions'][i], ex4_formats['header_formats'][i])

# table 'verhinderd
        row_index += 2
        verhinderd_txt = ' '.join((settings['ex4_verhinderd_header01'], '\n', settings['ex4_verhinderd_header02']))
        sheet.merge_range(row_index, 0, row_index + 1, col_count -1, verhinderd_txt, th_merge_normal)
        row_index += 2
        sheet.write(row_index, 0, ex4_formats['field_captions'][0], th_merge_normal)
        sheet.merge_range(row_index, 1, row_index, first_subject_column -1, settings['ex4_verhinderd_header03'], th_merge_normal)

        for i in range(first_subject_column, col_count):
            sheet.write(row_index, i, '', th_merge_normal)

        for x in range(0, 5):
            row_index += 1
            sheet.write(row_index, 0, '', th_merge_normal)
            sheet.merge_range(row_index, 1, row_index, first_subject_column - 1, '', th_merge_normal)

            for i in range(first_subject_column, col_count):
                sheet.write(row_index, i, '', th_merge_normal)

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
        # PR2022-05-31 also show signatures on preliminary Ex4 form
        auth_row = first_footnote_row
        if save_to_disk or True:
            sheet.write(auth_row, first_subject_column, str(_('Digitally signed by')) + ':')
            auth_row += 2
    # - Chairperson
            sheet.write(auth_row, first_subject_column, str(_('Chairperson')) + ':')
            auth1_list = ex4_rows_dict.get('auth1')
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
            auth2_list = ex4_rows_dict.get('auth2')
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

            # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
            published_instance.save(request=request)

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
# --- end of create_ex4_xlsx


def create_ex1_ex4_format_dict(book, sheet, school, department, subject_pk_list, subject_code_list): # PR2021-08-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex1_ex4_format_dict -----')

    sheet.hide_gridlines(2) # 2 = Hide screen and printed gridlines

    #cell_format = book.add_format({'bold': True, 'font_color': 'red'})
    bold_format = book.add_format({'bold': True})
    bold_blue = book.add_format({'font_color': 'blue', 'bold': True})
    normal_blue = book.add_format({'font_color': 'blue'})

    # th_format.set_bg_color('#d8d8d8') #   #d8d8d8;  /* light grey 218 218 218 100%
    # or: th_format = book.add_format({'bg_color': '#d8d8d8'
    th_align_center = book.add_format({'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    th_rotate = book.add_format({'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'rotation': 90})
    th_prelim = book.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})

    th_merge_bold = book.add_format({ 'bold': True, 'align': 'center', 'valign': 'vcenter'})
    th_merge_bold.set_left()
    th_merge_bold.set_bottom()

    th_merge_normal = book.add_format({'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})

    th_exists = book.add_format({'bold': False, 'align': 'left', 'valign': 'vcenter'})

    row_align_left = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter','border': True})
    row_align_center = book.add_format({'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter','border': True})
    # for deleted subjects in Ex1
    row_align_center_red = book.add_format({'font_size': 8, 'font_color': 'red', 'align': 'center', 'valign': 'vcenter','border': True})

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
                   'field_captions': ['Examen-\nnummer', 'ID-nummer', 'Naam en voorletters van de kandidaat\n(in alfabetische volgorde)'],
                    'header_formats': [th_align_center, th_align_center, th_align_center],
                    'row_formats': [row_align_center, row_align_center, row_align_left],
                    'totalrow_formats': [totalrow_merge, totalrow_align_center, totalrow_align_center],
                    'bold_format': bold_format,
                   'bold_blue': bold_blue,
                   'normal_blue': normal_blue,
                   'row_align_center_red': row_align_center_red,
                   'th_merge_bold': th_merge_bold,
                   'th_merge_normal': th_merge_normal,
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
    colcount_subjects = len(subject_pk_list)
    subject_col_width = 2.86
    for x in range(0, colcount_subjects):  # range(start_value, end_value, step), end_value is not included!
        field_width.append(subject_col_width)
        subject_pk = subject_pk_list[x]
        subject_code = subject_code_list[x] if subject_code_list[x] else ''
        ex1_formats['field_captions'].append(subject_code)
        ex1_formats['field_names'].append(subject_pk)
        ex1_formats['header_formats'].append(th_rotate)
        ex1_formats['row_formats'].append(row_align_center)
        ex1_formats['totalrow_formats'].append(totalrow_number)

    # - add empty subject columns if col_count is less than 15
    if colcount_subjects < 15:
        for x in range(colcount_subjects, 15):  # range(start_value, end_value, step), end_value is not included!
            field_width.append(subject_col_width)
            subject_code = ''
            # was: subject_pk = 0
            subject_pk = '0'
            ex1_formats['field_captions'].append(subject_code)
            ex1_formats['field_names'].append(subject_pk)
            ex1_formats['header_formats'].append(th_rotate)
            ex1_formats['row_formats'].append(row_align_center)
            ex1_formats['totalrow_formats'].append(totalrow_number)

    ex1_formats['first_subject_column'] = first_subject_column
    ex1_formats['field_width'] = field_width

    return ex1_formats
# - end of create_ex1_ex4_format_dict


def create_ex1_ex4_rows_dict(examyear, school, department, save_to_disk, examperiod, prefix, published_instance):  # PR2021-08-15
    # this function is only called by create_ex1_xlsx
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex1_ex4_rows_dict -----')
        logger.debug('     examperiod: ' + str(examperiod))

    # function creates dictlist of all students of this examyear, school and department
    #  key 'subj_id_arr' contains list of all studentsubjects of this student, not tobedeleted
    #  skip studsubjects that are not fully approved
    level_req = department.level_req

    # only show students without subjects in preliminary Ex1 form
    include_students_without_subjects = not save_to_disk # and examperiod == 1
    inner_or_left_join_studsubj = "LEFT JOIN" if include_students_without_subjects else "INNER JOIN"

# PR2021-08-10 dont include null in  ARRAY_AGG
# from https://stackoverflow.com/questions/13122912/how-to-exclude-null-values-in-array-agg-like-in-string-agg-using-postgres

    # don't filter on published or approved subject when printing preliminary Ex1 (in that case save_to_disk = False)

    # when submitting Ex1 form:
    # - exclude studsubj that are already published
    # - exclude studsubj that are not fully approved
    # - exclude deleted studsubj

    # when submitting Ex4 form:
    # filter on has_reex or has_reex03
    # - don't exclude studsubj that are reex published
    # - exclude studsubj that are not fully reex_approved
    # - exclude deleted studsubj
    # TODO find a way to include tobedeleted in Ex form

    published_pk = published_instance.pk if published_instance else None
    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk, 'published_id': published_pk}

    sql_studsubj_agg_list = [
        "SELECT studsubj.student_id,",
        "ARRAY_AGG(si.subject_id) AS subj_id_arr,",
        "ARRAY_AGG(si.subject_id) FILTER (WHERE NOT studsubj.tobedeleted) AS subj_id_arr_nondel,",
        "ARRAY_AGG(si.subject_id) FILTER (WHERE studsubj.tobedeleted) AS subj_id_arr_del,",

        "ARRAY_AGG(DISTINCT studsubj." + prefix + "auth1by_id) FILTER (WHERE studsubj." + prefix + "auth1by_id IS NOT NULL) AS auth1_arr,",
        "ARRAY_AGG(DISTINCT studsubj." + prefix + "auth2by_id) FILTER (WHERE studsubj." + prefix + "auth2by_id IS NOT NULL) AS auth2_arr",
        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        # was: "WHERE NOT studsubj.tobedeleted"
    ]

    if examperiod == 2:
        sql_studsubj_agg_list.append("WHERE studsubj.has_reex")
    elif examperiod == 3:
        sql_studsubj_agg_list.append("WHERE studsubj.has_reex03")
    else:
        sql_studsubj_agg_list.append("WHERE TRUE")

    if save_to_disk and examperiod == 1:
        # when submitting an Ex1 form published_instance is already saved, therefore published_instance.pk has a value
        # studsubj.subj_published_id also has a value: the id of the new published_instance
        # filter on published_instance.pk, so only subjects of this submit will be added to Ex1 form
        # was: sql_studsubj_agg_list.append("AND studsubj.subj_published_id = %(published_id)s::INT")

        sql_studsubj_agg_list.append("AND studsubj." + prefix + "published_id = %(published_id)s::INT")

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
        "studsubj.subj_id_arr, studsubj.subj_id_arr_nondel, studsubj.subj_id_arr_del,",
        "studsubj.auth1_arr, studsubj.auth2_arr",

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

    if logging_on:
        logger.debug('     sql: ' + str(sql))

    ex1_ex4_rows_dict = {'total': {}, 'auth1': [], 'auth2': []}
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

        # if logging_on:
            # logger.debug('connection.queries: ' + str(connection.queries))

        ex1_ex4_total = ex1_ex4_rows_dict.get('total')
        ex1_ex4_auth1 = ex1_ex4_rows_dict.get('auth1')
        ex1_ex4_auth2 = ex1_ex4_rows_dict.get('auth2')

        for row in rows:
            # row: {'student_id': 4902,
            #       'subj_id_arr': [1047, 1055, 1050, 1067, 1048, 1069, 1049, 1089, 1052, 1054, 1051],
            #       'auth1_arr': [67],
            #       'auth2_arr': [101]}
            if logging_on:
                logger.debug('     row: ' + str(row))

            # value is '0' when level_id = None (Havo/Vwo)
            level_pk = row.get('level_id')
            if level_pk is None:
                level_pk = 0

            lvl_name = ''
            if level_pk:
                lvl_name = row.get('lvl_name', '---')
            elif level_req:
                lvl_name = str(_("Candidates, whose 'leerweg' is not entered"))

            if level_pk not in ex1_ex4_rows_dict:
                ex1_ex4_rows_dict[level_pk] = {'lvl_name': lvl_name, 'total': {}, 'stud_list': []}

            level_dict = ex1_ex4_rows_dict[level_pk]
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
            subj_id_arr_nondel = row.get('subj_id_arr_nondel', [])
            subj_id_arr_del = row.get('subj_id_arr_del', [])
            student_dict = {'idnr': idnumber, 'exnr': examnumber, 'name': fullname,
                            'lvl': lvl_abbrev, 'sct': sct_abbrev, 'cls': classname, 'subj': subj_id_arr,
                            'subj_nondel': subj_id_arr_nondel, 'subj_del': subj_id_arr_del
                            }
            level_studlist.append(student_dict)
            # only count non-deleted rows
            if subj_id_arr_nondel:
                for subject_pk in subj_id_arr_nondel:
                    if subject_pk not in level_total:
                        level_total[subject_pk] = 1
                    else:
                        level_total[subject_pk] += 1
                    if subject_pk not in ex1_ex4_total:
                        ex1_ex4_total[subject_pk] = 1
                    else:
                        ex1_ex4_total[subject_pk] += 1

            auth1_arr = row.get('auth1_arr', [])
            if auth1_arr:
                for auth1_pk in auth1_arr:
                    if auth1_pk not in ex1_ex4_auth1:
                        ex1_ex4_auth1.append(auth1_pk)

            auth2_arr = row.get('auth2_arr', [])
            if auth2_arr:
                for auth2_pk in auth2_arr:
                    if auth2_pk not in ex1_ex4_auth2:
                        ex1_ex4_auth2.append(auth2_pk)
    except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
       logger.debug('-----------------------------------------------')
       logger.debug('ex1_ex4_rows_dict: ' + str(ex1_ex4_rows_dict))

    """
    ex1_ex4_rows_dict: 
        {'total': {1048: 171, 1055: 139, 1052: 171, 1051: 171, 1050: 171, 1057: 115, 1047: 171, 1049: 55, 1065: 115, 1089: 56, 1070: 140, 1067: 56, 1058: 117, 1066: 1, 1054: 31, 1069: 30}, 
        'auth1': [48], 
        'auth2': [57], 
        86: {
            'lvl_name': 'Praktisch Basisgerichte Leerweg', 
            'total': {1048: 89, 1055: 89, 1052: 89, 1051: 89, 1050: 89, 1057: 57, 1047: 89, 1049: 34, 1065: 57, 1089: 32, 1070: 88, 1067: 32, 1058: 56}, 
            'stud_list': [
                {'idnr': '1998041505', 'exnr': 'V021', 'name': 'Albertus, Dinaida Lilian Jearette', 'lvl': 'PBL', 'sct': 'z&w', 'cls': '4V2', 
                 'subj': [1048, 1055, 1052, 1051, 1050, 1057, 1047, 1049, 1065]}, 
 
    """
    return ex1_ex4_rows_dict
# --- end of create_ex1_ex4_rows_dict


def create_ex1_Ex4_mapped_subject_rows(examyear, school, department, is_reex=False):  # PR2021-08-08
    # function gets all subjects of studsubj of this dep, not tobedeleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]

    subject_code_list = []
    subject_pk_list = []
    is_reex_clause = "AND studsubj.has_reex" if is_reex else ""

    sql_list = [
        "SELECT subj.id, subjbase.code",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
        "AND NOT st.tobedeleted AND NOT studsubj.tobedeleted",
        is_reex_clause,
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
# --- end of create_ex1_Ex4_mapped_subject_rows



#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

@method_decorator([login_required], name='dispatch')
class GradeDownloadEx2View(View):  # PR2022-02-17

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeDownloadEx2View ============= ')
        # function creates, Ex2 xlsx file based on settings in usersetting

        response = None
        # try:
        if True:
            if request.user and request.user.country and request.user.schoolbase:
                req_user = request.user

                # - reset language
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

                # - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if sel_examyear and sel_school and sel_department:
                    # - get text from examyearsetting
                    library = awpr_lib.get_library(sel_examyear, ['exform', 'ex2'])

    # +++ create Ex2_xlsx
                    save_to_disk = False
                    # just to prevent PyCharm warning on published_instance=published_instance
                    published_instance = sch_mod.School.objects.get_or_none(pk=None)
                    response = create_ex2_ex2a_xlsx(
                        published_instance=published_instance,
                        examyear=sel_examyear,
                        school=sel_school,
                        department=sel_department,
                        examperiod=c.EXAMPERIOD_FIRST,
                        library=library,
                        is_ex2a=False,
                        save_to_disk=save_to_disk,
                        request=request,
                        user_lang=user_lang)
        # except:
        #    raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of GradeDownloadEx2View

@method_decorator([login_required], name='dispatch')
class GradeDownloadEx2aView(View):  # PR2022-02-17 PR2022-05-09

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeDownloadEx2aView ============= ')
        # function creates, Ex2 xlsx file based on settings in usersetting

        response = None
        # try:
        if True:
            if request.user and request.user.country and request.user.schoolbase:
                req_user = request.user

    # - reset language
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

    # - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

    # - get selected examperiod
                sel_examperiod = None
                selected_pk_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                if selected_pk_dict:
                    sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)

                if sel_examyear and sel_school and sel_department and sel_examperiod in (1, 2, 3):
    # - get text from examyearsetting
                    library = awpr_lib.get_library(sel_examyear, ['exform', 'ex2', 'ex2a'])

# +++ create ex2_ex2a_xlsx
                    save_to_disk = False
                    # just to prevent PyCharm warning on published_instance=published_instance
                    published_instance = sch_mod.School.objects.get_or_none(pk=None)
                    response = create_ex2_ex2a_xlsx(
                        published_instance=published_instance,
                        examyear=sel_examyear,
                        school=sel_school,
                        department=sel_department,
                        examperiod=sel_examperiod,
                        library=library,
                        is_ex2a=True,
                        save_to_disk=save_to_disk,
                        request=request,
                        user_lang=user_lang)
        # except:
        #    raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of GradeDownloadEx2aView


@method_decorator([login_required], name='dispatch')
class GradeDownloadEx5View(View):  # PR2022-02-17

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeDownloadEx5View ============= ')
        # function creates, Ex2 xlsx file based on settings in usersetting

        response = None
        # try:
        if True:
            if request.user and request.user.country and request.user.schoolbase:
                req_user = request.user

                # - reset language
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

                # - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if sel_examyear and sel_school and sel_department:

    # +++ create Ex5_xlsx
                    save_to_disk = False
                    # just to prevent PyCharm warning on published_instance=published_instance
                    published_instance = sch_mod.School.objects.get_or_none(pk=None)
                    response = create_ex5_xlsx(
                        published_instance=published_instance,
                        examyear=sel_examyear,
                        school=sel_school,
                        department=sel_department,
                        examperiod=c.EXAMPERIOD_FIRST,
                        save_to_disk=save_to_disk,
                        request=request,
                        user_lang=user_lang)
        # except:
        #    raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of GradeDownloadEx5View


def create_ex2_ex2a_xlsx(published_instance, examyear, school, department, examperiod, library, is_ex2a, save_to_disk, request, user_lang):
    # PR2022-02-17 PR2022-06-01
    # called by GradeDownloadEx2View
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex2_ex2a_xlsx -----')

    # +++ get mapped_subject_rows    '
    # function gets all subjects of studsubj of this dep, not tobedeleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]
    subject_row_count, subject_pk_list, subject_code_list, subjects_dict = \
        create_exform_mapped_subject_rows(examyear, school, department, is_ex2a, False)  # is_ex5 = False)

    if logging_on:
        logger.debug('     subject_row_count: ' + str(subject_row_count))
        logger.debug('     subject_pk_list: ' + str(subject_pk_list))
        logger.debug('     subject_code_list: ' + str(subject_code_list))

# +++ get dict of students with list of studsubj_pk, grouped by level_pk, with totals
    ex2_rows_dict, grades_auth_dict = create_ex2_ex2a_rows_dict(examyear, school, department, examperiod, is_ex2a, save_to_disk, published_instance)
    if logging_on:
        logger.debug('grades_auth_dict: ' + str(grades_auth_dict))
    """
    ex2_rows_dict: {
        6: {'lvl_name': 'Praktisch Basisgerichte Leerweg', 'students': 
            'students': {
                3747: {'idnumber': '2002111708', 'examnumber': '2101', 'classname': 'B4A', 'lvl_abbrev': 'PBL', 'sct_abbrev': 'ec', 'fullname': 'Ahoua, Ahoua Bryan Blanchard ', 
                    'grades': {115: '5,5', 133: '4,4', 157: '-', 120: '-', 154: '-', 136: 'v', 114: '5,5', 113: '-', 116: '5,5', 118: '-'}}, 
                3773: {'idnumber': '2002010704', 'examnumber': '2127', 'classname': 'B4B', 'lvl_abbrev': 'PBL', 'sct_abbrev': 'tech', 'fullname': 'BouwM, Nathan Leon Tadeus ', 
                'grades': {113: '-', 121: '-', 122: '-', 118: '-', 116: '5,5', 114: '5,5', 153: '5,5', 117: '4,5', 136: 'o', 115: '5,5'}}, 
                    
    grades_auth_dict: {'auth1': ['Monique Beek'], 'auth2': ['Hans2'], 
                    'auth3': {'Hans Meijs': {121: {'class': ['4A1', '4VA2', '4VA1', '4V3'], 'cluster': []}, 
                                             136: {'class': ['4A1', '4V1', '4V2', '4VA2'], 'cluster': []}, 
    file_dir: cur/2022/CUR01/exfiles
    file_name: Ex2 CUR01 Ancilla Domini Vsbo  2022-03-09 15u24.xlsx             
               
    """

    # from https://stackoverflow.com/questions/16393242/xlsxwriter-object-save-as-http-response-to-create-download-in-django
    # logger.debug('period_dict: ' + str(period_dict))

    """
        'Regel 0:   MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT
        'Regel 1:   Verzamellijst van cijfers van schoolexamens
        'Regel 2:   Landsbesluit eindexamens V.W.O., H.A.V.O., V.S.B.O. van de 23ste juni 2008,
        'Regel 3:   ter uitvoering van artikel 32, vijfde lid, van de Landsverordening voortgezet onderwijs, no. 54.
        'Regel 4:
        'Regel 5:   Inzenden ten minste 3 dagen vóór aanvang van de centrale examens*
        'Regel 6:   EINDEXAMEN V.S.B.O. in het examenjaar 2022

        'Regel 7:   School: Milton Peters College
        'Regel 8:
        'Regel 9:  VOORLOPIG Ex2 FORMULIER
        'Regel 10:
        'Regel 11:  column header
    """

    response = None

    if library and ex2_rows_dict:

        # PR2021-07-28 changed to file_dir = 'published/'
        # this one gives path: awpmedia / awpmedia / media / private / published
        # PR2021-08-06 create different folders for country and examyear
        # this one gives path: awpmedia / awpmedia / media / private / cur / 2022 / published
        # published_instance is None when downloading preliminary Ex2 form

        examyear_str = str(examyear.code)

        file_path = None
        if published_instance:
            requsr_school = sch_mod.School.objects.get_or_none(
                base=request.user.schoolbase,
                examyear=examyear
            )
    # ---  create file_path
            # PR2021-08-07 changed to file_dir = 'country/examyear/published/'
            # this one gives path:awpmedia/awpmedia/media/cur/2022/published
            requsr_schoolcode = requsr_school.base.code if requsr_school.base.code else '---'
            country_abbrev = examyear.country.abbrev.lower()
            file_dir = '/'.join((country_abbrev, examyear_str, requsr_schoolcode, 'exfiles'))
            file_path = '/'.join((file_dir, published_instance.filename))
            file_name = published_instance.name

            if logging_on:
                logger.debug('file_dir: ' + str(file_dir))
                logger.debug('file_name: ' + str(file_name))
                logger.debug('filepath: ' + str(file_path))

    # ---  create file Name and worksheet Name
        exform_name = 'Ex2A' if is_ex2a else 'Ex2'
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
        title = ' '.join((exform_name, str(examyear), school.base.code, today_dte.isoformat()))
        file_name = title + ".xlsx"

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

# +++++++++++++++++++++++++
# +++ print Ex2 front page
        sheet = book.add_worksheet(str(_('Ex2')))

# --- create format of Ex2 sheet
        ex2_formats = create_ex2_format_dict(book, sheet, school, department, subject_pk_list, subject_code_list)
        field_width = ex2_formats.get('field_width')
        bold_format = ex2_formats.get('bold_format')
        bold_blue = ex2_formats.get('bold_blue')
        normal_blue = ex2_formats.get('normal_blue')
        row_align_center_red = ex2_formats.get('row_align_center_red')
        row_align_center_green = ex2_formats.get('row_align_center_green')
        th_merge_bold = ex2_formats.get('th_merge_bold')
        th_prelim = ex2_formats.get('th_prelim')
        totalrow_merge = ex2_formats.get('totalrow_merge')
        col_count = len(ex2_formats['field_width'])
        first_subject_column = ex2_formats.get('first_subject_column', 0)

# --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

# --- title row
        sheet.write(0, 0, library['minond'], bold_format)

        if is_ex2a:
            title_str = library['ex2a_title'] + library['ex2a_title_tv0' + str(examperiod)]

            lb_rgl01_str = library['ex2a_lex_article'] if school.islexschool else library['ex2a_eex_article']
            lb_rgl02_str = None
        else:
            title_str = library['ex2_title']
            lb_rgl01_str = library['lex_lb_rgl01'] if school.islexschool else library['eex_lb_rgl01']
            lb_rgl02_str = library['lex_lb_rgl02'] if school.islexschool else library['eex_lb_rgl02']

        sheet.write(1, 0, title_str, bold_format)
        sheet.write(2, 0, lb_rgl01_str, bold_format)
        sheet.write(3, 0, lb_rgl02_str, bold_format)

        if not is_ex2a:
            sheet.write(5, 0, library['submit_before'], bold_format)

        lb_ex_key = 'lex' if school.islexschool else 'eex'
        lb_ex_key_str = ' '.join((library[lb_ex_key], department.abbrev, library['in_examyear'], examyear_str))

        sheet.write(6, 0, lb_ex_key_str, bold_format)
        lb_school_key = 'school' if school.islexschool else 'school'
        sheet.write(7, 0, library[lb_school_key], bold_format)
        sheet.write(7, 2, school.name, bold_blue)

# - put Ex2 in right upper corner
        sheet.merge_range(0, col_count - 5, 1, col_count - 1, exform_name, th_merge_bold)

        row_index = 9
        if not save_to_disk:
            prelim_txt = ' '.join(('VOORLOPIG', exform_name, 'FORMULIER'))
            sheet.merge_range(row_index, 0, row_index, col_count - 1, prelim_txt, th_prelim)
            row_index += 1

        # if has_published_ex2_rows(examyear, school, department):
        #    exists_txt = str(_('Attention: an Ex2 form has already been submitted. The subjects in that form are not included in this form.'))
        #    sheet.merge_range(row_index, 0, row_index, col_count - 1, exists_txt, th_exists)
        #    row_index += 1

# ---  table header row
        # for i in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        #    sheet.write(row_index, i, ex2_formats['field_captions'][i], ex2_formats['header_formats'][i])

# ++++++++++++++++++++++++++++
        # iterate through levels, if more than 1 exist

        for key, level_dict in ex2_rows_dict.items():
            # skip ex2_rows_dict_totals
            if isinstance(key, int):
                # in subject column 'field_name' is subject_id

                row_index += 2

# ---  write level header if level exists
                lvl_name = level_dict.get('lvl_name')
                if lvl_name:
                    sheet.write(row_index, 0, lvl_name, bold_format)
                    row_index += 2
                students_dict = level_dict.get('students')

# ---  write table header

                for i, field_caption in enumerate(ex2_formats['field_captions']):
                    sheet.write(row_index, i, field_caption, ex2_formats['header_formats'][i])

# ---  student rows
                for key, stud_dict in students_dict.items():
                    grades_dict = stud_dict.get('grades')
                    """
                    stud_dict: {
                        idnumber': '2002111708', 'examnumber': '2101', 'classname': 'B4A', 'lvl_abbrev': 'PBL', 'sct_abbrev': 'ec', 'fullname': 'Ahoua, Ahoua Bryan Blanchard ', 
                        'grades': {115: '5,5', 133: '4,4', 157: '-', 120: '-', 154: '-', 136: 'v', 114: '5,5', 113: '-', 116: '5,5', 118: '-'}}
                        
                    ex2_formats[field_names]: ['exnr', 'idnr', 'name', 'cls', 'lvl', 'sct', 
                        133, 123, 126, 117, 155, 114, 119, 157, 154, 153, 129, 116, 115, 124, 122, 134, 113, 118, 120, 136, 135, 137, 121, 131]
                    """

                    row_index += 1
                    for i, field_name in enumerate(ex2_formats['field_names']):
                        exc_format = ex2_formats['row_formats'][i]
                        value = ''
                        if isinstance(field_name, int):
                            # in subject column 'field_name' is subject_id
                            value = grades_dict.get(field_name)
                            if value == 'x':
                                exc_format = row_align_center_red
                            elif value == 'vr':
                                exc_format = row_align_center_green

                        else:
                            value = stud_dict.get(field_name, '')
                            if logging_on and False:
                                logger.debug('field_name: ' + str(field_name))
                                logger.debug('value: ' + str(value))
                        sheet.write(row_index, i, value, exc_format)


# ---  table footer row
                row_index += 1
                for i, field_name in enumerate(ex2_formats['field_names']):
                    if i == 0:
                        sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', totalrow_merge)
                    else:
                        sheet.write(row_index, i, ex2_formats['field_captions'][i], ex2_formats['header_formats'][i])

        # end of iterate through levels,
# ++++++++++++++++++++++++++++
# ---  footnote row
        row_index += 2
        first_footnote_row = row_index
        max_index = 3 if is_ex2a else 9
        for i in range(1, max_index):
            if school.islexschool and 'lex_footnote0' + str(i) in library:
                key = 'lex_footnote0' + str(i)
            else:
                key = 'footnote0' + str(i)
            if key in library:
                value = library.get(key)
                if value:
                    sheet.write(row_index + i - 1, 0, value, bold_format)

# ---  digitally signed by
        # PR2022-05-04 Lionel Mongen saw wrong secretary on Ex2,
        # to be able to check: also add signed by on prelim Ex-form
        # was:  if save_to_disk:
        auth_row = first_footnote_row
        sheet.write(auth_row, first_subject_column, str(_('Digitally signed by')) + ':')
        auth_row += 2

 # - Chairperson
        sheet.write(auth_row, first_subject_column, str(_('Chairperson')) + ':')
        auth1_list = grades_auth_dict.get('auth1')
        if logging_on:
            logger.debug('auth1_list: ' + str(auth1_list))
        # auth1_list: ['Monique Beek', 'Hans Meijs']
        if auth1_list:
            for auth1 in auth1_list:
                if logging_on:
                    logger.debug('auth1: ' + str(auth1) + ' ' + str(type(auth1)))
                if auth1:
                    sheet.write(auth_row, first_subject_column + 4, auth1, normal_blue)
                    auth_row += 1
        else:
            auth_row += 1
        auth_row += 1

# - Secretary
        sheet.write(auth_row, first_subject_column, str(_('Secretary')) + ':')
        auth2_list = grades_auth_dict.get('auth2')
        if logging_on:
            logger.debug('auth2_list: ' + str(auth2_list))

        if auth2_list:
            for auth2 in auth2_list:
                if logging_on:
                    logger.debug('auth2: ' + str(auth2) + ' ' + str(type(auth2)))
                if auth2:
                    sheet.write(auth_row, first_subject_column + 4, auth2, normal_blue)
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

# +++++++++++++++++++++++++
# +++ print back page
        sheet = book.add_worksheet(str(_('Handtekeningen')))

# --- set column width
        field_width = (40, 40, 40, 40)
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

# --- title row
        sheet.write(0, 0, library['minond'], bold_format)
        sheet.write(1, 0, library['title'], bold_format)

        lb_ex_key = 'lex' if school.islexschool else 'eex'
        lb_ex_key_str = ' '.join((library[lb_ex_key], department.abbrev, library['in_examyear'], examyear_str))
        sheet.write(3, 0, lb_ex_key_str, bold_format)

        lb_school_key = 'school' if school.islexschool else 'school'
        sheet.write(5, 0, library[lb_school_key], bold_format)
        sheet.write(5, 1, school.name, bold_blue)

        backpage01_key = 'backpage01_ex2a' if is_ex2a else 'backpage01_lex' if school.islexschool else 'backpage01_eex'
        sheet.write(7, 0, library[backpage01_key], bold_format)
        sheet.write(8, 0, library['backpage02'], bold_format)

        row_index = 10

        # when Ex2a: also give signatures of 2nd corrector
        #PR2022-05-31 debug: dont forget comma to crete tuple, was: else (0) this gives integer
        index_tuple = (0, 1) if is_ex2a else (0,)
        for index in index_tuple:
# ---  auth header row
            auth_name_key = 'backheader01_ex2a' if index else 'backheader01'
            field_captions = (library[auth_name_key], library['backheader02'], library['backheader03'], library['backheader04'])  # , library['backheader05'])

            if logging_on:
                logger.debug('field_captions: ' + str(field_captions))
                logger.debug('grades_auth_dict: ' + str(grades_auth_dict))

            for i, field_caption in enumerate(field_captions):
                if logging_on:
                    logger.debug('field_caption: ' + str(field_caption))
                    logger.debug('row_index: ' + str(row_index))
                sheet.write(row_index, i, field_caption, ex2_formats['header_formats'][i])

            """
                grades_auth_dict: {
                    'auth1': ['Hans Meijs'], 
                    'auth2': [], 
                    'auth3': {
                        'Hans Meijs': {
                            'cav': {'class': ['B4B', 'B4A'], 'cluster': []}, 
                            'lo': {'class': ['B4A'], 'cluster': []}, 
                            'ie': {'class': ['B4A'], 'cluster': []}, 
                            'en': {'class': ['B4A'], 'cluster': []}}}}
            """

    # ---  auth rows
            auth_key = 'auth4' if index else 'auth3'
            gr_auth_dict = grades_auth_dict.get(auth_key)
            if gr_auth_dict:
                for auth_name, auth_dict in gr_auth_dict.items():
                    for subject_pk, dict in auth_dict.items():
                        row_index += 1

                        subj_name = ''
                        subject_dict = subjects_dict.get(subject_pk)
                        if subject_dict:
                            subj_name = subject_dict.get('name', '')

                        sheet.write(row_index, 0, auth_name)
                        sheet.write(row_index, 1, subj_name)

                        class_list = dict.get('class')
                        if class_list:
                            class_list.sort()
                            class_str = ', '.join(class_list)
                            sheet.write(row_index, 2, class_str)

                        cluster_list = dict.get('cluster')
                        if cluster_list:
                            cluster_list.sort()
                            cluster_str = ', '.join(cluster_list)
                            sheet.write(row_index, 3, cluster_str)

            row_index += 3
# +++++++++++++++++++++++++

        book.close()

# +++ save file to disk
        if save_to_disk:
            excel_file = File(temp_file)

            published_instance.file.save(file_path, excel_file)

            # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
            published_instance.save(request=request)

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
# --- end of create_ex2_xlsx


def create_ex2_format_dict(book, sheet, school, department, subject_pk_list, subject_code_list):  # PR2021-08-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex2_format_dict -----')

    sheet.hide_gridlines(2)  # 2 = Hide screen and printed gridlines

    # cell_format = book.add_format({'bold': True, 'font_color': 'red'})
    bold_format = book.add_format({'bold': True})
    bold_blue = book.add_format({'font_color': 'blue', 'bold': True})
    normal_blue = book.add_format({'font_color': 'blue'})

    # th_format.set_bg_color('#d8d8d8') #   #d8d8d8;  /* light grey 218 218 218 100%
    # or: th_format = book.add_format({'bg_color': '#d8d8d8'
    th_align_center = book.add_format(
        {'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    th_rotate = book.add_format(
        {'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'rotation': 90})
    th_prelim = book.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})

    th_merge_bold = book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
    th_merge_bold.set_left()
    th_merge_bold.set_bottom()

    th_exists = book.add_format({'bold': False, 'align': 'left', 'valign': 'vcenter'})

    row_align_left = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter', 'border': True})
    row_align_center = book.add_format(
        {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True})

    row_align_center_red = book.add_format(
        {'font_size': 8, 'font_color': 'red', 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': True})

    row_align_center_green = book.add_format(
        {'font_size': 8, 'font_color': '#008000', 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': True})

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

    ex2_formats = {'field_names': ['exnr', 'idnr', 'name'],
                   'field_captions': ['Ex.nr.', 'ID-nummer',
                                      'Naam en voorletters van de kandidaat\n(in alfabetische volgorde)'],
                   'header_formats': [th_align_center, th_align_center, th_align_center],
                   'row_formats': [row_align_center, row_align_center, row_align_left],
                   'totalrow_formats': [totalrow_merge, totalrow_align_center, totalrow_align_center],
                   'bold_format': bold_format,
                   'bold_blue': bold_blue,
                   'normal_blue': normal_blue,
                   'row_align_center_red': row_align_center_red,
                   'row_align_center_green': row_align_center_green,
                   'th_merge_bold': th_merge_bold,
                   'th_exists': th_exists,
                   'th_prelim': th_prelim,
                   'totalrow_merge': totalrow_merge
                   }

    # - add column class, not when lex school
    if not is_lexschool:
        col_count += 1
        field_width.append(10)
        ex2_formats['field_names'].append('cls')
        ex2_formats['field_captions'].append('Klas')
        ex2_formats['header_formats'].append(th_align_center)
        ex2_formats['row_formats'].append(row_align_center)
        ex2_formats['totalrow_formats'].append(totalrow_align_center)

    # - add column 'Leerweg' if level_req
    if level_req:  # add column if level_req
        col_count += 1
        field_width.append(5)
        ex2_formats['field_names'].append('lvl')
        ex2_formats['field_captions'].append('Leer-\nweg')
        ex2_formats['header_formats'].append(th_align_center)
        ex2_formats['row_formats'].append(row_align_center)
        ex2_formats['totalrow_formats'].append(totalrow_align_center)

    # - add column 'Profiel' or 'Sector' if sector_req (is always the case)
    if sector_req:
        col_count += 1
        field_width.append(7)
        caption = 'Profiel' if has_profiel else 'Sector'
        ex2_formats['field_names'].append('sct')
        ex2_formats['field_captions'].append(caption)
        ex2_formats['header_formats'].append(th_align_center)
        ex2_formats['row_formats'].append(row_align_center)
        ex2_formats['totalrow_formats'].append(totalrow_align_center)

    # - add subject columns. Amount of subject columns = length of subject_pk_list
    first_subject_column = col_count
    colcount_subjects = len(subject_pk_list)
    subject_col_width = 2.86
    for x in range(0, colcount_subjects):  # range(start_value, end_value, step), end_value is not included!
        field_width.append(subject_col_width)
        subject_pk = subject_pk_list[x]
        subject_code = subject_code_list[x] if subject_code_list[x] else ''
        ex2_formats['field_captions'].append(subject_code)
        ex2_formats['field_names'].append(subject_pk)
        ex2_formats['header_formats'].append(th_rotate)
        ex2_formats['row_formats'].append(row_align_center)
        ex2_formats['totalrow_formats'].append(totalrow_number)

    # - add empty subject columns if col_count is less than 15
    if colcount_subjects < 15:
        for x in range(colcount_subjects, 15):  # range(start_value, end_value, step), end_value is not included!
            field_width.append(subject_col_width)
            subject_code = ''
            # was: subject_pk = 0
            subject_pk = '0'
            ex2_formats['field_captions'].append(subject_code)
            ex2_formats['field_names'].append(subject_pk)
            ex2_formats['header_formats'].append(th_rotate)
            ex2_formats['row_formats'].append(row_align_center)
            ex2_formats['totalrow_formats'].append(totalrow_number)

    ex2_formats['first_subject_column'] = first_subject_column
    ex2_formats['field_width'] = field_width

    return ex2_formats
# - end of create_ex2_format_dict


def create_ex5_format_dict(book, sheet, school, department, subject_pk_list, subject_code_list, subjects_dict):  # PR2022-05-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex5_format_dict -----')

    sheet.hide_gridlines(2)  # 2 = Hide screen and printed gridlines

    # cell_format = book.add_format({'bold': True, 'font_color': 'red'})
    bold_format = book.add_format({'bold': True})
    bold_blue = book.add_format({'font_color': 'blue', 'bold': True})
    normal_blue = book.add_format({'font_color': 'blue'})

    # th_format.set_bg_color('#d8d8d8') #   #d8d8d8;  /* light grey 218 218 218 100%
    # or: th_format = book.add_format({'bg_color': '#d8d8d8'
    th_align_center = book.add_format(
        {'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    th_rotate = book.add_format(
        {'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'rotation': 90})
    th_prelim = book.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True})

    th_merge_small = book.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    th_merge_small.set_left() # set left border
    th_merge_small.set_bottom() # set bottom border

    th_merge_bold = book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
    th_merge_bold.set_left() # set left border
    th_merge_bold.set_bottom() # set bottom border

    th_exists = book.add_format({'bold': False, 'align': 'left', 'valign': 'vcenter'})

    row_align_left = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter', 'border': True})
    row_align_center = book.add_format(
        {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True})

    row_align_center_red = book.add_format(
        {'font_size': 8, 'font_color': 'red', 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': True})

    row_align_center_green = book.add_format(
        {'font_size': 8, 'font_color': '#008000', 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': True})

    row_bg_lightgrey = book.add_format(
        {'font_size': 8, 'border': True, 'bg_color': '#f2f2f2', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
    # format_y = wb.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C6500'})

    # row_bg_lightgrey.set_bg_color('#d8d8d8')  # #d8d8d8;  /* light grey 218 218 218 100%
    #row_bg_lightgrey.set_bg_color('#f2f2f2')  # ##f2f2f2;  /* light light grey 242 242 242 100%

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
    field_width = [6, 12, 38, 4]
    # Note: length of header_formats list must be same as length of field_captions
    ex5_formats = {'field_names': ['exnr', 'idnr', 'name', 'gender'],
                   'field_captions': ['Examennummer',
                                      'Sedulanr.',
                                      'Naam en voorletters van de kandidaat\n(Deze gegevens moeten geheel in overeenstemming zijn met die, vermeld op de lijst van geslaagde kandidaten)',
                                      'Geslacht (m of v)'
                                      ],
                   'header_formats': [th_rotate, th_align_center, th_align_center, th_rotate],
                   'row_formats': [row_align_center, row_align_center, row_align_left, row_align_center],
                   'totalrow_formats': [totalrow_merge, totalrow_align_center, totalrow_align_center, totalrow_align_center, totalrow_align_center, totalrow_align_center],
                   'bold_format': bold_format,
                   'bold_blue': bold_blue,
                   'normal_blue': normal_blue,
                   'row_align_center_red': row_align_center_red,
                   'row_align_center_green': row_align_center_green,
                   'row_bg_lightgrey': row_bg_lightgrey,
                   'th_align_center': th_align_center,
                   'th_merge_small': th_merge_small,
                   'th_merge_bold': th_merge_bold,
                   'th_exists': th_exists,
                   'th_prelim': th_prelim,
                   'totalrow_merge': totalrow_merge
                   }
    # format_index counts 1 for each subject.
    # col_index adds 3 columns per subject, is teherfore dirrenet from format_index
    format_index = 3

# - add column class, not when lex school
    if not is_lexschool:
        format_index += 1
        field_width.append(4)
        ex5_formats['field_names'].append('cls')
        ex5_formats['field_captions'].append('Klas')
        ex5_formats['header_formats'].append(th_rotate)
        ex5_formats['row_formats'].append(row_align_center)
        ex5_formats['totalrow_formats'].append(totalrow_align_center)

    # - add column 'Leerweg' if level_req
    if level_req:  # add column if level_req
        format_index += 1
        field_width.append(4)
        ex5_formats['field_names'].append('lvl')
        ex5_formats['field_captions'].append('Leerweg')
        ex5_formats['header_formats'].append(th_rotate)
        ex5_formats['row_formats'].append(row_align_center)
        ex5_formats['totalrow_formats'].append(totalrow_align_center)

    # - add column 'Profiel' or 'Sector' if sector_req (is always the case)
    if sector_req:
        format_index += 1
        field_width.append(4)
        caption = 'Profiel' if has_profiel else 'Sector'
        ex5_formats['field_names'].append('sct')
        ex5_formats['field_captions'].append(caption)
        ex5_formats['header_formats'].append(th_rotate)
        ex5_formats['row_formats'].append(row_align_center)
        ex5_formats['totalrow_formats'].append(totalrow_align_center)

    """
        Dim ExcColCount_Vakken As Integer
        Dim ExcColCount_Herexamens As Integer
        Dim ExcColCount_HerexamensTv03 As Integer 'PR2019-05-13
        Dim ExcColCount_Totaal As Integer
        
        Dim ExcColCount_Uitslag As Integer 'aantal Excel kolommen na vakken en voor herexamens (5 of 6: evt GemidCSE, eindcijfers, Geslaagd, her, Afgewezen, pre-/bis-examen
        Dim ExcColCount_TweedeTijdvakVakken As Integer
        Dim ExcColCount_TweedeTijdvakUitslag As Integer
        Dim ExcColCount_DerdeTijdvakVakken As Integer  'PR2019-05-13
        Dim ExcColCount_DerdeTijdvakUitslag As Integer  'PR2019-05-13
    
        Const ExcCol_FirstCol_Vakken As Byte = 7
        Dim ExcCol_FirstCol_TweedeTijdvak As Integer
        Dim ExcCol_FirstCol_TweedeTijdvakUitslag As Integer
        Dim ExcCol_FirstCol_DerdeTijdvak As Integer
        Dim ExcCol_FirstCol_DerdeTijdvakUitslag As Integer
        Dim ExcCol_Column_AantalVakken As Integer
        Dim ExcCol_Column_Teruggetrokken As Integer 'PR2019-05-15
    """

    # - add subject columns. 3 columns per subject, Amount of subject columns = length of subject_pk_list
    # columns index is 0-based
    formatindex_first_subject = format_index + 1
    subject_count = len(subject_pk_list)

    #  Const ExcColCount_GegevensKandidaat As Integer = 6 '6 = aantal Excel kolommen voor vakkenkolommen
    ex5_formats['formatindex_first_subject'] = formatindex_first_subject
    ex5_formats['subject_count'] = subject_count

    subject_col_width = 2.86
    for x in range(0, subject_count):  # range(start_value, end_value, step), end_value is not included!
        subject_pk = subject_pk_list[x]
        subject_dict = subjects_dict.get(subject_pk)
        subject_name = subject_dict.get('name') if subject_dict else '-'
        # each subject has column 's', 'c' and 'e', done in create_ex5_xlsx

        format_index += 1

        field_width.append(subject_col_width)
        ex5_formats['field_captions'].append(subject_name)
        ex5_formats['field_names'].append(subject_pk)
        ex5_formats['header_formats'].append(th_merge_small)
        ex5_formats['row_formats'].append(row_align_center)
        ex5_formats['totalrow_formats'].append(totalrow_number)

    field_width.append(4)
    ex5_formats['field_names'].append('subjects_count')
    ex5_formats['field_captions'].append('Aantal vakken')
    ex5_formats['header_formats'].append(th_rotate)
    ex5_formats['row_formats'].append(row_align_center)
    ex5_formats['totalrow_formats'].append(totalrow_align_center)

    field_width.append(4)
    ex5_formats['field_names'].append('subjects_count')
    ex5_formats['field_captions'].append('Totaal van de eindcijfers\nvoor de examenvakken')
    ex5_formats['header_formats'].append(th_rotate)
    ex5_formats['row_formats'].append(row_align_center)
    ex5_formats['totalrow_formats'].append(totalrow_align_center)

    field_width.append(4)
    ex5_formats['field_names'].append('subjects_count')
    ex5_formats['field_captions'].append('Gemiddelde van de cijfers voor het Centraal Examen')
    ex5_formats['header_formats'].append(th_rotate)
    ex5_formats['row_formats'].append(row_align_center)
    ex5_formats['totalrow_formats'].append(totalrow_align_center)




    ex5_formats['field_width'] = field_width

    return ex5_formats
# - end of create_ex5_format_dict


def create_ex2_ex2a_rows_dict(examyear, school, department, examperiod, is_ex2a, save_to_disk, published_instance, lvlbase_pk=None):
    # PR2022-02-17 PR2022-03-09
    # this function is only called by create_ex2_xlsx
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex2_ex2a_rows_dict -----')
    # function creates dictlist of all students of this examyear, school and department
    #  key 'subj_id_arr' contains list of all studentsubjects of this student, not tobedeleted
    #  skip studsubjects that are not fully approved
    level_req = department.level_req

    # PR2021-08-10 dont include null in  ARRAY_AGG
    # from https://stackoverflow.com/questions/13122912/how-to-exclude-null-values-in-array-agg-like-in-string-agg-using-postgres

    # don't filter on published or approved subject when printing preliminary Ex2 (in that case save_to_disk = False)

    # when submitting Ex2 form:
    # - exclude studsubj that are already published
    # - exclude studsubj that are not fully approved
    # - exclude deleted studsubj

    se_ce = 'ce' if is_ex2a else 'se'
    grade_score = 'cescore' if is_ex2a else 'segrade'

    published_pk = published_instance.pk if published_instance else None
    sql_keys = {'ey_id': examyear.pk, 'ep': examperiod, 'sch_id': school.pk, 'dep_id': department.pk, 'published_id': published_pk}

    # PR2022-04-13 add exemption grades if subject has exemption , to be used in future
    sql_exem_list = ["SELECT grd.studentsubject_id AS exem_studsubj_id, ",
                     "grd.segrade AS exem_segrade, grd.cegrade AS exem_cegrade, grd.finalgrade AS exem_finalgrade",
                "FROM students_grade AS grd",
                "WHERE grd.examperiod = 4 AND NOT grd.tobedeleted"]
    sql_grd_exem = ' '.join(sql_exem_list)

###############

    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    sql_list = ["WITH grd_exem AS (" + sql_grd_exem + ") ",

                "SELECT st.id AS student_id, st.idnumber, st.examnumber, st.lastname, st.firstname, st.prefix, st.classname, ",
                "st.level_id, lvl.name AS lvl_name, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ",
                "si.subject_id, cluster.name AS clustername, ",

                "grd.", grade_score, " AS grade_score, grd.", se_ce, "_auth1by_id AS auth1by_id, grd.", se_ce, "_auth2by_id AS auth2by_id, ",
                "grd.", se_ce, "_auth3by_id AS auth3by_id, grd.", se_ce, "_auth4by_id AS auth4by_id, ",

                "studsubj.has_exemption, grd_exem.exem_segrade, grd_exem.exem_cegrade, grd_exem.exem_finalgrade, ",

                "auth1.last_name AS auth1_usr, auth2.last_name AS auth2_usr, auth3.last_name AS auth3_usr, auth4.last_name AS auth4_usr ",

                "FROM students_grade AS grd ",
                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id) ",
                "INNER JOIN students_student AS st ON (st.id = studsubj.student_id) ",
                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id) ",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id) ",

                "LEFT JOIN grd_exem ON (grd_exem.exem_studsubj_id = studsubj.id) ",

                "LEFT JOIN subjects_cluster AS cluster ON (cluster.id = studsubj.cluster_id) ",

                "LEFT JOIN accounts_user AS auth1 ON (auth1.id = grd.", se_ce, "_auth1by_id) ",
                "LEFT JOIN accounts_user AS auth2 ON (auth2.id = grd.", se_ce, "_auth2by_id) ",
                "LEFT JOIN accounts_user AS auth3 ON (auth3.id = grd.", se_ce, "_auth3by_id) ",
                "LEFT JOIN accounts_user AS auth4 ON (auth4.id = grd.", se_ce, "_auth4by_id) ",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id) ",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id) ",
                "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT ",
                "AND grd.examperiod = %(ep)s::INT AND NOT st.tobedeleted AND NOT studsubj.tobedeleted AND NOT grd.tobedeleted "
                ]

    if save_to_disk:
        # when submitting an Ex2 form published_instance is already saved, therefore published_instance.pk has a value
        # filter on published_instance.pk, so only subjects of this submit will ne added to Ex2 form
        # was: sql_studsubj_agg_list.append("AND studsubj.subj_published_id = %(published_id)s::INT")

        sql_keys['published_id'] = published_pk
        sql_list.append("AND grd." + se_ce + "_published_id = %(published_id)s::INT ")

    if lvlbase_pk:
        sql_keys['lvlbase_id'] = lvlbase_pk
        sql_list.append("AND lvl.base_id = %(lvlbase_id)s::INT ")

    if level_req:
        sql_list.append("ORDER BY LOWER(lvl.abbrev), LOWER(st.lastname), LOWER(st.firstname)")
    else:
        sql_list.append("ORDER BY LOWER(st.lastname), LOWER(st.firstname)")
    sql = ''.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    # if logging_on:
    # logger.debug('connection.queries: ' + str(connection.queries))

    ex2_rows_dict = {}
    grades_auth_dict = {'auth1': [], 'auth2': [], 'auth3': {}, 'auth4': {}}
    grades_auth1_list = grades_auth_dict.get('auth1')
    grades_auth2_list = grades_auth_dict.get('auth2')
    grades_auth3_dict = grades_auth_dict.get('auth3')
    grades_auth4_dict = grades_auth_dict.get('auth4')

    for row in rows:

        if logging_on:
            logger.debug('row: ' + str(row))

        # value is '0' when level_id = None (Havo/Vwo)
        level_pk = row.get('level_id')
        if level_pk is None:
            level_pk = 0

        lvl_name = ''
        if level_pk:
            lvl_name = row.get('lvl_name', '---')
        elif level_req:
            lvl_name = str(_("Candidates, whose learning path is not entered"))

        if level_pk not in ex2_rows_dict:
            ex2_rows_dict[level_pk] = {'lvl_name': lvl_name, 'students': {}}

        level_dict = ex2_rows_dict[level_pk]
        level_students = level_dict.get('students')

        student_pk = row.get('student_id')
        if student_pk and student_pk not in level_students:

            prefix = row.get('prefix')
            lastname = row.get('lastname', '')
            firstname = row.get('firstname', '')
            if prefix:
                lastname = ' '.join((prefix, lastname))
            fullname = ''.join((lastname, ', ', firstname))

            level_students[student_pk] = {
                'idnr': row.get('idnumber', '---'),
                'exnr': row.get('examnumber', '---'),
                'cls': row.get('classname', ''),
                'lvl': row.get('lvl_abbrev', '---'),
                'sct': row.get('sct_abbrev', '---'),
                'name': fullname,
                'grades': {}
            }
        level_student_grades_dict = level_students[student_pk].get('grades')

        subject_pk = row.get('subject_id')
        if subject_pk:

            if subject_pk not in level_student_grades_dict:
                grade_score = row.get('grade_score')
                has_exemption = row.get('has_exemption', False)

                if grade_score is not None and not grade_score == '':
                    grade_score_comma = str(grade_score).replace('.', ',')
                elif row.get('has_exemption', False):
                    grade_score_comma = 'vr'
                else:
                    grade_score_comma = 'x'

                level_student_grades_dict[subject_pk] = grade_score_comma

                if logging_on:
                    logger.debug('     grade_score: ' + str(grade_score) + ' ' + str(type(grade_score)))
                    logger.debug('     has_exemption: ' + str(has_exemption) + ' ' + str(type(has_exemption)))
                    logger.debug('     grade_score_comma: ' + str(grade_score_comma) + ' ' + str(type(grade_score_comma)))

            auth1_usr = row.get('auth1_usr')
            if auth1_usr and auth1_usr not in grades_auth1_list:
                grades_auth1_list.append(auth1_usr)

            auth2_usr = row.get('auth2_usr')
            if auth2_usr and auth2_usr not in grades_auth2_list:
                grades_auth2_list.append(auth2_usr)

            auth3_usr = row.get('auth3_usr')
            if auth3_usr:
                if auth3_usr not in grades_auth3_dict:
                    grades_auth3_dict[auth3_usr] = {}
                grades_auth3_usr = grades_auth3_dict[auth3_usr]

                if subject_pk not in grades_auth3_usr:
                    grades_auth3_usr[subject_pk] = {'class': [], 'cluster': []}

                classname = row.get('classname')
                if classname:
                    grades_auth3_class = grades_auth3_usr[subject_pk].get('class')
                    if classname not in grades_auth3_class:
                        grades_auth3_class.append(classname)

                clustername = row.get('clustername')
                if clustername:
                    grades_auth3_cluster = grades_auth3_usr[subject_pk].get('cluster')
                    if clustername not in grades_auth3_cluster:
                        grades_auth3_cluster.append(clustername)

            auth4_usr = row.get('auth4_usr')
            if auth4_usr:
                if auth4_usr not in grades_auth4_dict:
                    grades_auth4_dict[auth4_usr] = {}
                grades_auth4_usr = grades_auth4_dict[auth4_usr]

                if subject_pk not in grades_auth4_usr:
                    grades_auth4_usr[subject_pk] = {'class': [], 'cluster': []}

                classname = row.get('classname')
                if classname:
                    grades_auth4_class = grades_auth4_usr[subject_pk].get('class')
                    if classname not in grades_auth4_class:
                        grades_auth4_class.append(classname)

                clustername = row.get('clustername')
                if clustername:
                    grades_auth4_cluster = grades_auth4_usr[subject_pk].get('cluster')
                    if clustername not in grades_auth4_cluster:
                        grades_auth4_cluster.append(clustername)

        if logging_on:
            logger.debug('level_student_grades_dict: ' + str(level_student_grades_dict))
            logger.debug('-----------------------------------------------')
            logger.debug('>>>>>>>>> grades_auth_dict: ' + str(grades_auth_dict))

    """
    https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
    to sort list of students alphabetically:
    from operator import itemgetter
    newlist = sorted(list_to_be_sorted, key=itemgetter('name')) 
    """
    """
    ex2_rows_dict: {
        6: {'lvl_name': 'Praktisch Basisgerichte Leerweg', 'students': 
            'students': {
                3747: {'idnumber': '2002111708', 'examnumber': '2101', 'classname': 'B4A', 'lvl_abbrev': 'PBL', 'sct_abbrev': 'ec', 'fullname': 'Ahoua, Ahoua Bryan Blanchard ', 
                    'grades': {115: '5,5', 133: '4,4', 157: '-', 120: '-', 154: '-', 136: 'v', 114: '5,5', 113: '-', 116: '5,5', 118: '-'}}, 
                3773: {'idnumber': '2002010704', 'examnumber': '2127', 'classname': 'B4B', 'lvl_abbrev': 'PBL', 'sct_abbrev': 'tech', 'fullname': 'BouwM, Nathan Leon Tadeus ', 
                'grades': {113: '-', 121: '-', 122: '-', 118: '-', 116: '5,5', 114: '5,5', 153: '5,5', 117: '4,5', 136: 'o', 115: '5,5'}}, 

    
    grades_auth_dict: {
        'auth1': ['Hans Meijs'], 
        'auth2': [], 
        'auth3': {
            'Hans Meijs': {
                'cav': {'class': ['B4B', 'B4A'], 'cluster': []}, 
                'lo': {'class': ['B4A'], 'cluster': []}, 
                'ie': {'class': ['B4A'], 'cluster': []}, 
                'en': {'class': ['B4A'], 'cluster': []}}}}
                                
    """
    return ex2_rows_dict, grades_auth_dict
# --- end of create_ex2_ex2a_rows_dict

#@@@@@@@@@@@@@@@@@@@@@@@

def create_ex5_rows_dict(examyear, school, department, examperiod, save_to_disk, published_instance,
                              lvlbase_pk=None):
    # PR2022-02-17 PR2022-03-09
    # this function is only called by create_ex2_xlsx
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex5_rows_dict -----')
    # function creates dictlist of all students of this examyear, school and department
    #  key 'subj_id_arr' contains list of all studentsubjects of this student, not tobedeleted
    #  skip studsubjects that are not fully approved
    level_req = department.level_req

    # PR2021-08-10 dont include null in  ARRAY_AGG
    # from https://stackoverflow.com/questions/13122912/how-to-exclude-null-values-in-array-agg-like-in-string-agg-using-postgres

    # don't filter on published or approved subject when printing preliminary Ex2 (in that case save_to_disk = False)

    # when submitting Ex2 form:
    # - exclude studsubj that are already published
    # - exclude studsubj that are not fully approved
    # - exclude deleted studsubj

    """
    https://hashrocket.com/blog/posts/faster-json-generation-with-postgresql
    https://dba.stackexchange.com/questions/224910/postgresql-how-to-generate-an-array-containing-column-name-and-column-data
    SELECT row_to_json(t) FROM (SELECT SELECT id, last, first FROM names WHERE id = '001') t
    """

    published_pk = published_instance.pk if published_instance else None
    sql_keys = {'ey_id': examyear.pk, 'ep': examperiod, 'sch_id': school.pk, 'dep_id': department.pk,
                'published_id': published_pk}

    # PR2022-04-13 add exemption grades if subject has exemption , to be used in future
    sql_grd_list = ["SELECT grd.studentsubject_id AS studsubj_id,",

                     "ARRAY_AGG(grd.examperiod) AS e,",
                     "ARRAY_AGG(grd.sesrgrade) AS s,",
                     "ARRAY_AGG(grd.pecegrade) AS c,",
                     "ARRAY_AGG(grd.finalgrade) AS f",

                     "FROM students_grade AS grd",

                     "WHERE NOT grd.tobedeleted",
                     # TODO set filter published
                     #"AND grd.se_published_id IS NOT NULL AND grd.ce_published_id IS NOT NUL",
                     "GROUP BY grd.studentsubject_id",
                     ]
    sql_grd = ' '.join(sql_grd_list)
    """
    row: {'st_id': 3826, 'idnr': '2005080604', 'exnr': '2180', gender': 'm', 'ln': 'Arion ', 'fn': 'Tichainy Jennifer', 'pref': None, 
        'class': 'T4B', 'level_id': 4, 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 'lvl_abbrev': 'TKL', 'sct_abbrev': 'z&w', 
        'regnr': 'CUR0322221803', 'dipnr': None, 'glnr': None, 'evest': False, 'lexst': False, 'bisst': False, 'partst': False, 
        'wdr': False, 'c_avg': None, 'combi_avg': None, 'f_avg': None, 'result': 0, 'subj_id': 116, 
        'e': [1, 4], 's': ['6.3', None], 'c': [None, None], 'f': ['6', None], 
        'exemp': True, 'sr': False, 're': False, 're3': False, 'gls': None, 'glc': None, 'glf': None, 'usex': True}
    """
    ###############

    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    sql_list = ["WITH grd_arr AS (" + sql_grd + ")",
                "SELECT st.id AS st_id, st.idnumber AS idnr, st.examnumber AS exnr, st.gender,",
                "st.lastname AS ln, st.firstname AS fn, st.prefix AS pref, st.classname AS class, ",
                "st.level_id, lvl.name AS lvl_name, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ",

                "st.regnumber AS regnr, st.diplomanumber AS dipnr, st.gradelistnumber AS glnr,",
                "st.iseveningstudent AS evest, st.islexstudent AS lexst, st.bis_exam AS bisst, st.partial_exam AS partst, st.withdrawn AS wdr,"
                
                "st.ep01_ce_avg, st.ep01_combi_avg, st.ep01_final_avg, st.ep01_result,"
                "st.ep02_ce_avg, st.ep02_combi_avg, st.ep02_final_avg, st.ep02_result,"
                "st.gl_ce_avg, st.gl_combi_avg, st.gl_final_avg, st.result,"

                "subj.id AS subj_id, grd_arr.e, grd_arr.s, grd_arr.c, grd_arr.f, ",

                "studsubj.has_exemption AS exemp, studsubj.has_sr AS sr, studsubj.has_reex AS re, studsubj.has_reex03 AS re3,",
                "studsubj.gradelist_sesrgrade AS gls, studsubj.gradelist_pecegrade AS glc,",
                "studsubj.gradelist_finalgrade AS glf, studsubj.gradelist_use_exem AS usex",

                "FROM students_studentsubject AS studsubj",
                "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",

                "INNER JOIN grd_arr ON (grd_arr.studsubj_id = studsubj.id)",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
                "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
                "AND NOT st.tobedeleted AND NOT studsubj.tobedeleted"
                ]

    if save_to_disk:
        # when submitting an Ex2 form published_instance is already saved, therefore published_instance.pk has a value
        # filter on published_instance.pk, so only subjects of this submit will be added to Ex2 form
        # was: sql_studsubj_agg_list.append("AND studsubj.subj_published_id = %(published_id)s::INT")

        sql_keys['published_id'] = published_pk
        #sql_list.append("AND grd." + se_ce + "_published_id = %(published_id)s::INT ")

    if lvlbase_pk:
        sql_keys['lvlbase_id'] = lvlbase_pk
        sql_list.append("AND lvl.base_id = %(lvlbase_id)s::INT ")

    if level_req:
        sql_list.append("ORDER BY LOWER(lvl.abbrev), LOWER(st.lastname), LOWER(st.firstname)")
    else:
        sql_list.append("ORDER BY LOWER(st.lastname), LOWER(st.firstname)")
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    # if logging_on:
    # logger.debug('connection.queries: ' + str(connection.queries))

    ex5_rows_dict = {}

    if logging_on:
        logger.debug('==========================')

    for row in rows:
        if logging_on and False:
            logger.debug('row: ' + str(row))

        # value is '0' when level_id = None (Havo/Vwo)
        level_pk = row.get('level_id')
        if level_pk is None:
            level_pk = 0

        lvl_name = ''
        if level_pk:
            lvl_name = row.get('lvl_name', '---')
        elif level_req:
            lvl_name = str(_("Candidates, whose learning path is not entered"))

        if level_pk not in ex5_rows_dict:
            ex5_rows_dict[level_pk] = {'lvl_name': lvl_name, 'students': {}}

        level_dict = ex5_rows_dict[level_pk]
        level_students = level_dict.get('students')

        student_pk = row.get('st_id')
        if student_pk and student_pk not in level_students:

            prefix = row.get('pref')
            lastname = row.get('ln', '')
            firstname = row.get('fn', '')
            if prefix:
                lastname = ' '.join((prefix, lastname))
            fullname = ''.join((lastname, ', ', firstname))

            level_students[student_pk] = {
                'stud': {
                    'idnr': row.get('idnr'),
                    'exnr': row.get('exnr'),
                    'gender': row.get('gender'),
                    'class': row.get('class'),
                    'lvl': row.get('lvl_abbrev'),
                    'sct': row.get('sct_abbrev'),
                    'name': fullname,
                    'regnr': row.get('regnr'),
                    'dipnr': row.get('dipnr'),
                    'glnr': row.get('glnr'),
                    'evest': row.get('evest', False),
                    'lexst': row.get('lexst', False),
                    'bisst': row.get('bisst', False),
                    'partst': row.get('partst', False),
                    'wdr': row.get('wdr', False),

                    'ep01_ce_avg': row.get('ep01_ce_avg'),
                    'ep01_combi_avg': row.get('ep01_combi_avg'),
                    'ep01_final_avg': row.get('ep01_final_avg'),
                    'ep01_result': row.get('ep01_result'),

                    'ep02_ce_avg': row.get('ep02_ce_avg'),
                    'ep02_combi_avg': row.get('ep02_combi_avg'),
                    'ep02_final_avg': row.get('ep02_final_avg'),
                    'ep02_result': row.get('ep02_result'),

                    'gl_ce_avg': row.get('gl_ce_avg'),
                    'gl_combi_avg': row.get('gl_combi_avg'),
                    'gl_final_avg': row.get('gl_final_avg'),
                    'result': row.get('result')
                },
                'subj': {},
                'ep': {}
            }
        subjects_dict = level_students[student_pk].get('subj')
        examperiods_dict = level_students[student_pk].get('ep')

        subject_pk = row.get('subj_id')
        if subject_pk:
            if subject_pk not in subjects_dict:
                subjects_dict[subject_pk] = {}
                subj_dict = subjects_dict[subject_pk]
                if row.get('exemp'):
                    subj_dict['exemp'] = True
                if row.get('usex'):
                    subj_dict['usex'] = True
                #if row.get('sr'):
                #    subj_dict['sr'] = True
                if row.get('re'):
                    subj_dict['re'] = True
                if row.get('re3'):
                    subj_dict['re3'] = True

                if row.get('gls'):
                    subj_dict['gls'] = row.get('gls')
                if row.get('glc'):
                    subj_dict['glc'] = row.get('glc')
                if row.get('glf'):
                    subj_dict['glf'] = row.get('glf')

                e_arr = row.get('e')
                if e_arr:
                    s_arr = row.get('s')
                    c_arr = row.get('c')
                    f_arr = row.get('f')

                    for i, examperiod in enumerate(e_arr):
                        if examperiod not in examperiods_dict:
                            examperiods_dict[examperiod] = {}

                        examperiod_dict = examperiods_dict[examperiod]

                        if subject_pk not in examperiod_dict:
                            examperiod_dict[subject_pk] = {'s': s_arr[i], 'c': c_arr[i], 'f': f_arr[i] } \
                                if s_arr[i] or c_arr[i] or f_arr[i] else {}

    if logging_on:
        logger.debug('ex5_rows_dict: ' + str(ex5_rows_dict))

        """                       
        ex5_rows_dict: {
            6: {'lvl_name': 'Praktisch Basisgerichte Leerweg', 
                'students':
                    3826: {
                        'stud': {'idnr': '2005080604', 'exnr': '2180', 'gender': 'V', 'class': 'T4B', 'lvl': 'TKL', 'sct': 'z&w', 
                                'name': 'Arion , Tichainy Jennifer', 'regnr': 'CUR0322221803', 'dipnr': None, 'glnr': None, 
                                'evest': False, 'lexst': False, 'bisst': False, 'partst': False, 'wdr': False, 
                                'c_avg': None, 'combi_avg': None, 'f_avg': None, 'result': 0}, 
                        'subj': {135: {'exemp': True, 'usex': True}, 113: {}, 114: {}, 115: {}, 
                                116: {'exemp': True, 'usex': True}, 117: {'exemp': True, 'usex': True}, 
                                118: {'exemp': True, 'usex': True}, 123: {}, 124: {}, 120: {}, 131: {}}, 
                        'ep': {4: {135: {}, 116: {}, 117: {}, 118: {}}, 
                                1: {135: {'s': 'g', 'c': None, 'f': 'g'}, 
                                    113: {'s': '6.6', 'c': None, 'f': None}, 
                                    114: {'s': '7.9', 'c': None, 'f': None}, 
                                    115: {'s': '5.0', 'c': None, 'f': '5'}, 
                                    116: {'s': '6.3', 'c': None, 'f': '6'}, 
                                    117: {}, 118: {}, 
                                    123: {'s': '6.3', 'c': None, 'f': None}, 
                                    124: {'s': '6.1', 'c': None, 'f': None}, 
                                    120: {'s': '6.1', 'c': None, 'f': None}, 
                                    131: {'s': '5.9', 'c': None, 'f': None}}}}, 


       """
    return ex5_rows_dict
# --- end of create_ex5_rows_dict

#@@@@@@@@@@@@@@@@@@@@@@@
def create_exform_mapped_subject_rows(examyear, school, department, is_ex2a, is_ex5):  # PR2021-08-08 PR2022-05-16
    # function gets all subjects of studsubj of this dep, not tobedeleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]

    #Pr2022-05-16 added: filter on weighing
    filter_weighing = ''
    # ex5 shows all subjects
    if not is_ex5:
        # ex2a shows only subjects with weight_ce > 0
        if is_ex2a:
            filter_weighing = 'AND si.weight_ce > 0'
        else:
        # ex2 shows only subjects with weight_se > 0 (all subjects have weight_se > 0)
            filter_weighing = 'AND si.weight_se > 0'

    subject_code_list = []
    subject_pk_list = []
    subjects_dict = {}

    sql_list = [
        "SELECT subj.id, subjbase.code, subj.name",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
        "AND NOT st.tobedeleted AND NOT studsubj.tobedeleted",
        filter_weighing,
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
            # subject_pk_dict[subject_row[0]] = index
            subject_pk_list.append(subject_row[0])
            subject_code_list.append(subject_row[1])
            subjects_dict[subject_row[0]] = {'code': subject_row[1], 'name': subject_row[2]}
            row_count += 1

    return row_count, subject_pk_list, subject_code_list, subjects_dict
# --- end of create_exform_mapped_subject_rows


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
def create_ex5_xlsx(published_instance, examyear, school, department, examperiod,
                     save_to_disk, request, user_lang):
    # PR2022-05-13
    # called by GradeDownloadEx5View
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex5_xlsx -----')

# - get text from examyearsetting
    library = awpr_lib.get_library(examyear, ['exform', 'ex5'])

# +++ get mapped_subject_rows    '
    # function gets all subjects of studsubj of this dep, not tobedeleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]
    subject_row_count, subject_pk_list, subject_code_list, subjects_dict = \
        create_exform_mapped_subject_rows(examyear, school, department, False, True) # is_ex2a = False, is_ex5 = True)

    if logging_on:
        logger.debug('subject_row_count: ' + str(subject_row_count))
        #logger.debug('library: ' + str(library))
        #logger.debug('subject_pk_list: ' + str(subject_pk_list))
        #logger.debug('subject_code_list: ' + str(subject_code_list))
        #logger.debug('subjects_dict: ' + str(subjects_dict))
    """
    subject_row_count: 21
    subject_pk_list: [133, 123, 126, 117, 155, 114, 153, 129, 116, 115, 124, 122, 134, 113, 118, 120, 136, 135, 137, 121, 131]
    subject_code_list: ['ac', 'bi', 'bw', 'cav', 'ec', 'en', 'ict', 'ie', 'lo', 'mm1', 'mm2', 'nask1', 'nask2', 'ne', 'pa', 'sp', 'stg', 'sws', 'ta', 'wk', 'zwi']
    subjects_dict: {133: {'code': 'ac', 'name': 'Administratie en commercie'}, 123: {'code': 'bi', 'name': 'Biologie'}, 
    """

# +++ get dict of students with list of studsubj_pk, grouped by level_pk, with totals
    ex5_rows_dict = create_ex5_rows_dict(examyear, school, department, examperiod, save_to_disk, published_instance)

    if logging_on and False:
        logger.debug('ex5_rows_dict: ' + str(ex5_rows_dict))

    response = None

    if library and ex5_rows_dict:

        # PR2021-07-28 changed to file_dir = 'published/'
        # this one gives path: awpmedia / awpmedia / media / private / published
        # PR2021-08-06 create different folders for country and examyear
        # this one gives path: awpmedia / awpmedia / media / private / cur / 2022 / published
        # published_instance is None when downloading preliminary Ex2 form

        examyear_str = str(examyear.code)

        file_path = None
        if published_instance:
            requsr_school = sch_mod.School.objects.get_or_none(
                base=request.user.schoolbase,
                examyear=examyear
            )

# ---  create file_path
            # PR2021-08-07 changed to file_dir = 'country/examyear/published/'
            # this one gives path:awpmedia/awpmedia/media/cur/2022/published
            requsr_schoolcode = requsr_school.base.code if requsr_school.base.code else '---'
            country_abbrev = examyear.country.abbrev.lower()
            file_dir = '/'.join((country_abbrev, examyear_str, requsr_schoolcode, 'exfiles'))
            file_path = '/'.join((file_dir, published_instance.filename))
            file_name = published_instance.name

        if logging_on:
            logger.debug('filepath: ' + str(file_path))

# ---  create file Name and worksheet Name
        exform_name = 'Ex5'
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
        title = ' '.join((exform_name, str(examyear), school.base.code, today_dte.isoformat()))
        file_name = title + ".xlsx"

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

# +++++++++++++++++++++++++
# +++ print Ex5 front page
        sheet = book.add_worksheet(str(_('Ex5')))

    # --- create format of Ex5 sheet
        ex5_formats = create_ex5_format_dict(book, sheet, school, department, subject_pk_list, subject_code_list, subjects_dict)
        field_width = ex5_formats.get('field_width')
        bold_format = ex5_formats.get('bold_format')
        bold_blue = ex5_formats.get('bold_blue')
        normal_blue = ex5_formats.get('normal_blue')
        row_align_center = ex5_formats.get('row_align_center')
        row_align_center_green = ex5_formats.get('row_align_center_green')
        row_bg_lightgrey = ex5_formats.get('row_bg_lightgrey')

        th_merge_small = ex5_formats.get('th_merge_small')
        th_merge_bold = ex5_formats.get('th_merge_bold')
        th_prelim = ex5_formats.get('th_prelim')
        th_align_center = ex5_formats.get('th_align_center')
        totalrow_merge = ex5_formats.get('totalrow_merge')
        #col_index = len(ex5_formats['field_width'])

        formatindex_first_subject = ex5_formats.get('formatindex_first_subject', 0)
        subject_count = ex5_formats.get('subject_count', 0)
        formatindex_number_subjects = formatindex_first_subject + subject_count

        # --- min ond row
        sheet.write(0, 0, library['minond'], bold_format)

    # --- title row
        title_str = library['ex5_title']
        if school.islexschool:
            lb_rgl01_str = ' '.join((library['lex_lb_rgl01'], library['lex_lb_rgl02']))
        else:
            lb_rgl01_str = ' '.join((library['eex_lb_rgl01'], library['eex_lb_rgl02']))

        sheet.write(1, 0, title_str, bold_format)
        sheet.write(2, 0, lb_rgl01_str , bold_format)

        lb_ex_key = 'lex' if school.islexschool else 'eex'
        lb_ex_key_str = ' '.join((library[lb_ex_key], department.abbrev, library['in_examyear'], examyear_str))
        sheet.write(3, 0, lb_ex_key_str, bold_format)

        lb_school_key = 'school' if school.islexschool else 'school'
        sheet.write(5, 0, library[lb_school_key], bold_format)
        sheet.write(5, 2, school.name, bold_blue)

        inzenden_key = 'lex_inzenden' if school.islexschool else 'eex_inzenden'
        sheet.write(7, 0, library[inzenden_key], bold_format)

# - put Ex5 in right upper corner
        #sheet.merge_range(0, col_index - 5, 1, col_index - 1, exform_name, th_merge_bold)

        row_index = 9

        if not save_to_disk:
            prelim_txt = f'VOORLOPIG {exform_name} FORMULIER'
            sheet.write(row_index, 0, prelim_txt, bold_format)

        # if has_published_ex2_rows(examyear, school, department):
        #    exists_txt = str(_('Attention: an Ex2 form has already been submitted. The subjects in that form are not included in this form.'))
        #    sheet.merge_range(row_index, 0, row_index, col_index - 1, exists_txt, th_exists)
        #    row_index += 1

        # ---  table header row
        # for i in range(0, col_index):  # range(start_value, end_value, step), end_value is not included!
        #    sheet.write(row_index, i, ex5_formats['field_captions'][i], ex5_formats['header_formats'][i])

# ++++++++++++++++++++++++++++
# iterate through levels - levels have headers in Ex5

        for key, level_dict in ex5_rows_dict.items():

            if isinstance(key, int):
                students_dict = level_dict.get('students')

                row_index += 2
# ---  write level header if level exists
                lvl_name = level_dict.get('lvl_name')
                if lvl_name:
                    sheet.write(row_index, 0, lvl_name, bold_format)
                    row_index += 2

# ---  write table header
                row_index = write_ex5_table_header(sheet, row_index, ex5_formats, library, th_align_center)
                row_index += 2

# ---  student rows
                for student_pk, student_dict in students_dict.items():
                    row_index = write_ex5_table_row(
                        sheet=sheet,
                        row_index=row_index,
                        student_pk=student_pk,
                        student_dict=student_dict,
                        ex5_formats=ex5_formats,
                        formatindex_first_subject=formatindex_first_subject,
                        formatindex_number_subjects=formatindex_number_subjects,
                        row_align_center=row_align_center,
                        row_align_center_green=row_align_center_green,
                        row_bg_lightgrey=row_bg_lightgrey
                    )

    # end of iterate through students
# end of iterate through levels
# ++++++++++++++++++++++++++++


    # ---  footnote row
        row_index += 2
        first_footnote_row = row_index
        max_index = 3
        for i in range(1, max_index):
            if school.islexschool and 'lex_footnote0' + str(i) in library:
                key = 'lex_footnote0' + str(i)
            else:
                key = 'footnote0' + str(i)
            if key in library:
                value = library.get(key)
                if value:
                    sheet.write(row_index + i - 1, 0, value, bold_format)

    # ---  digitally signed by
        # PR2022-05-04 Lionel Mongen saw wrong secretary on Ex2,
        # to be able to check: also add signed by on prelim Ex-form
        # was:  if save_to_disk:
        auth_row = first_footnote_row
        sheet.write(auth_row, formatindex_first_subject, str(_('Digitally signed by')) + ':')
        auth_row += 2

    # -  place, date
        sheet.write(auth_row, formatindex_first_subject, 'Plaats:')
        sheet.write(auth_row, formatindex_first_subject + 4, str(school.examyear.country.name),
                    normal_blue)
        sheet.write(auth_row, formatindex_first_subject + 8, 'Datum:')
        sheet.write(auth_row, formatindex_first_subject + 11, today_formatted, normal_blue)

        book.close()

# +++ save file to disk
        if save_to_disk:
            excel_file = File(temp_file)

            published_instance.file.save(file_path, excel_file)

            # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
            published_instance.save(request=request)

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
# --- end of create_ex5_xlsx


def write_ex5_table_header(sheet, row_index, ex5_formats, library, th_align_center):
    # format_index counts 1 for each subject.
    # col_index adds 3 columns per subject, is therefore different from format_index

    formatindex_first_subject = ex5_formats['formatindex_first_subject']
    subject_count = ex5_formats['subject_count']
    formatindex_number_subjects = formatindex_first_subject + subject_count

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('formatindex_first_subject: ' + str(formatindex_first_subject))
        logger.debug('subject_count: ' + str(subject_count))
        logger.debug('formatindex_number_subjects: ' + str(formatindex_number_subjects))

# ---  header row 'GEGEVENS OMTRENT DE KANDIDATEN'
    sheet.set_row(row_index, 20)
    sheet.merge_range(row_index, 0, row_index, formatindex_first_subject - 1, library['geg_kand'], th_align_center)
    col_last = formatindex_first_subject + 3 * subject_count - 1
    sheet.merge_range(row_index, formatindex_first_subject, row_index, col_last, library['cijf_kand'], th_align_center)
    row_index += 1

# ---  subheader row 2
    sheet.set_row(row_index, 60)
    header_formats = ex5_formats['header_formats']
    field_names = ex5_formats['field_names']
    field_width = ex5_formats['field_width']
    col_index = 0

    def add_colnr_and_increase_index(col_index):
        # add column number row, increase col_index
        sheet.write(row_index + 2, col_index, str(col_index + 1), th_align_center)
        if logging_on:
            logger.debug('---col_index: ' + str(col_index))
        return col_index + 1

# +++ loop through field_captions
    for format_index, field_caption in enumerate(ex5_formats['field_captions']):
        header_format = header_formats[format_index]
        field_name = field_names[format_index]
        width = field_width[format_index]

        # format_index starts with 0
        if logging_on:
            logger.debug('format_index: ' + str(format_index))
            logger.debug('     field_caption: ' + str(field_caption))
            logger.debug('     field_name: ' + str(field_name))
            logger.debug('     header_format: ' + str(header_format))

        if format_index < formatindex_first_subject:
            sheet.set_column(col_index, col_index, width)
            sheet.merge_range(row_index, col_index, row_index + 1, col_index, field_caption, header_format)
            # add column number row, increase col_index
            # sheet.write(row_index + 2, col_index, str(col_index + 1), th_align_center)
            # col_index += 1
            col_index = add_colnr_and_increase_index(col_index)

        elif format_index < formatindex_number_subjects:
            if logging_on:
                logger.debug('format_index < formatindex_number_subjects: ' + str(format_index))
            sheet.set_column(col_index, col_index + 2, width)
            # merge subject name columns
            sheet.merge_range(row_index, col_index, row_index, col_index + 2, field_caption, header_format)

            sheet.write(row_index + 1, col_index, 's', th_align_center)
            col_index = add_colnr_and_increase_index(col_index)

            sheet.write(row_index + 1, col_index, 'c', th_align_center)
            col_index = add_colnr_and_increase_index(col_index)

            sheet.write(row_index + 1, col_index, 'e', th_align_center)
            col_index = add_colnr_and_increase_index(col_index)

        else:
            sheet.set_column(col_index, col_index, width)
            sheet.merge_range(row_index - 1, col_index, row_index + 1, col_index, field_caption, header_format)
            col_index = add_colnr_and_increase_index(col_index)

    return row_index
# - end of write_ex5_table_header


def write_ex5_table_row(sheet, row_index, student_pk, student_dict, ex5_formats,
formatindex_first_subject, formatindex_number_subjects,
                        row_align_center, row_align_center_green, row_bg_lightgrey):

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('student_pk: ' + str(student_pk) + ' ' + str(type(student_pk)))
        logger.debug('student_dict: ' + str(student_dict))

    if isinstance(student_pk, int):
        """
        student_dict: {3747: {'stud': {'idnr': '2002111708', 'exnr': '2101', 'gender': 'M',
        """
        stud_info_dict = student_dict.get('stud')
        stubjects_dict = student_dict.get('subj')
        examperiod_dict = student_dict.get('ep')

        subj_count = str(len(stubjects_dict)) if stubjects_dict is not None else None

        ep01_dict, ep02_dict, ep03_dict, ep04_dict = {}, {}, {}, {}
        if examperiod_dict:
            ep01_dict = examperiod_dict.get(c.EXAMPERIOD_FIRST, {})
            ep02_dict = examperiod_dict.get(c.EXAMPERIOD_SECOND, {})
            ep03_dict = examperiod_dict.get(c.EXAMPERIOD_THIRD, {})
            ep04_dict = examperiod_dict.get(c.EXAMPERIOD_EXEMPTION, {})

        row_index += 1
        col_index = 0

        if logging_on:
            logger.debug('     stud_info_dict: ' + str(stud_info_dict))
            logger.debug('     stubjects_dict: ' + str(stubjects_dict))
            logger.debug('     examperiod_dict: ' + str(examperiod_dict))
            logger.debug('     ep01_dict: ' + str(ep01_dict))

# +++ loop through field_names
        for format_index, field_name in enumerate(ex5_formats['field_names']):
            if logging_on:
                logger.debug(str(format_index) + ' field_name: ' + str(field_name) + str(type(field_name)))

            if format_index < formatindex_first_subject:
                # write student info
                row_format = ex5_formats['row_formats'][format_index]
                value_str = stud_info_dict.get(field_name) or None
                sheet.write(row_index, col_index, value_str, row_format)
                col_index += 1

            elif format_index < formatindex_number_subjects:
                # field_name contains subject_pk in subject columns
                # subj_dict can be empty, when no exemp, reex or gl garde
                subj_dict = stubjects_dict.get(field_name)

                row_format = ex5_formats['row_formats'][format_index]
                if subj_dict is None:
    # - enter empty cell with border when no subject
                    for x in range(0, 3):
                        sheet.write(row_index, col_index, None, row_format)
                        col_index += 1
                else:
                    has_exemp = subj_dict.get('exemp', False)
                    # row_format = row_align_center_green if has_exemp else row_align_center
                    usex = subj_dict.get('usex', False)
                    # has_sr = subj_dict.get('sr', False)
                    has_re = subj_dict.get('re', False)
                    has_re3 = subj_dict.get('re3', False)
                    gls = subj_dict.get('gls')
                    glc = subj_dict.get('glc')
                    glf = subj_dict.get('glf')

                    """
                    ep01_dict: {120: {'s': '8.0', 'c': None, 'f': None}, 113: {'s': '5.9', 'c': None, 'f': None}, 114: {'s': '8.0', 'c': None, 'f': None}, 115: {'s': '5.4', 'c': None, 'f': '5'}, 116: {'s': '7.0', 'c': None, 'f': '7'}, 118: {'s': '7.6', 'c': None, 'f': None}, 133: {'s': '6.4', 'c': None, 'f': None}, 136: {'s': 'g', 'c': None, 'f': 'g'}, 155: {'s': '6.1', 'c': None, 'f': None}, 117: {'s': '6.1', 'c': None, 'f': '6'}}

                    """

                    #row_format = row_align_center_green if has_exemp and usex else row_align_center
                    ep_dict = ep04_dict if has_exemp and usex else ep01_dict
                    ep_subj_dict = ep_dict.get(field_name)

                    s_value, c_value, f_value = None, None, None
                    if ep_subj_dict:
                        s_value = ep_subj_dict.get('s')
                        c_value = ep_subj_dict.get('c')
                        f_value = ep_subj_dict.get('f')

                        if s_value:
                            s_value = s_value.replace('.', ',')
                        if c_value:
                            c_value = c_value.replace('.', ',')
                        if f_value:
                            f_value = f_value.replace('.', ',')

                        if logging_on and False:
                            logger.debug('   --- s_value: ' + str(s_value))

                    sheet.write(row_index , col_index, s_value, row_format)
                    col_index += 1

                    sheet.write(row_index, col_index, c_value, row_format)
                    col_index += 1

                    sheet.write(row_index, col_index, f_value, row_format)
                    col_index += 1

            elif format_index == formatindex_number_subjects:
                sheet.write(row_index, col_index, subj_count, row_format)
                col_index += 1
            else:
                sheet.write(row_index, col_index, None, row_bg_lightgrey)
                col_index += 1

    return row_index
# - end of write_ex5_table_row


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
@method_decorator([login_required], name='dispatch')
class OrderlistPerSchoolDownloadView(View):  # PR2021-09-01
    # function creates Ex1 xlsx file based on settings in usersetting

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= OrderlistPerSchoolDownloadView ============= ')

        response = None

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear,from usersettings
            # orderlist is only created in first exam period
            sel_examyear_instance, sel_examperiodNIU = \
                dl.get_selected_examyear_examperiod_from_usersetting(request)

            if sel_examyear_instance:
                response = create_orderlist_per_school_xlsx(sel_examyear_instance, list, user_lang, request)

        if response is None:
            response = HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        return response
# - end of OrderlistPerSchoolDownloadView


@method_decorator([login_required], name='dispatch')
class OrderlistDownloadView(View):  # PR2021-07-04

    def get(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= OrderlistDownloadView ============= ')
            logger.debug('list: ' + str(list) + ' ' + str(type(list)))
        # function creates, xlsx file based on settings in usersetting

        response = None

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear,from usersettings
            # exames are only ordered in first exam period
            sel_examyear_instance, sel_examperiodNIU = \
                dl.get_selected_examyear_examperiod_from_usersetting(request)
            if logging_on:
                logger.debug('sel_examyear_instance: ' + str(sel_examyear_instance))

            if sel_examyear_instance:
                response = create_orderlist_xlsx(sel_examyear_instance, list, user_lang, request)

        if response is None:
            response = HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        return response
# - end of OrderlistDownloadView


def create_orderlist_rowsNIU(examyear, examperiod_int, is_ete_exam, otherlang):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- excel.py create_orderlist_rows  -----')

    if is_ete_exam:
        ete_clause = "AND si.ete_exam"
    else:
        ete_clause = "AND NOT si.ete_exam"

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

##################################################

def create_orderlist_per_school_xlsx(sel_examyear_instance, list, user_lang, request):  # PR2021-07-07 PR2021-08-20
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_orderlist_per_school_xlsx -----')
        # row: {'school_id': 78, 'schbase_code': 'CUR13', 'school_name': 'Abel Tasman College', 'dep_id': 97, 'depbase_code': 'Vsbo',
        #           'lvl_id': 63, 'lvl_abbrev': 'TKL', 'subj_id': 998, 'subjbase_code': 'ne', 'subj_name': 'Nederlandse taal', '
        #           subj_published_arr': [None], 'lang': 'ne', 'count': 7}

# - get text from examyearsetting
    settings = awpr_lib.get_library(sel_examyear_instance, ['exform', 'ex1'])

# - get depbase dictlist
    department_dictlist = subj_view.create_departmentbase_dictlist(sel_examyear_instance)

# - get lvlbase dictlist
    lvlbase_dictlist = subj_view.create_levelbase_dictlist(sel_examyear_instance)

# - get subjectbase dictlist
    subjectbase_dictlist = subj_view.create_subjectbase_dictlist(sel_examyear_instance)

# - get schoolbase dictlist
    # functions creates ordered dictlist of all schoolbase_pk, schoolbase_code and school_name of this exam year of all countries
    # fields are: sbase_id, sbase_code, sch_name
    schoolbase_dictlist = subj_view.create_schoolbase_dictlist(sel_examyear_instance, request)

# ---  create file Name and worksheet Name
    now_formatted = af.format_modified_at(timezone.now(), user_lang, False)  # False = not month_abbrev
    today_dte = af.get_today_dateobj()
    file_name = ''.join(('Bestelling examens ', str(sel_examyear_instance.code), ' per school dd ', today_dte.isoformat(), '.xlsx'))

# Create an in-memory output file for the new workbook.
    output = io.BytesIO()
    # Even though the final file will be in memory the module uses temp
    # files during assembly for efficiency. To avoid this on servers that
    # don't allow temp files, for example the Google APP Engine, set the
    # 'in_memory' Workbook() constructor option as shown in the docs.
    #  book = xlsxwriter.Workbook(response, {'in_memory': True})
    book = xlsxwriter.Workbook(output)

# create dict with cell formats
    formats = create_formats(book)

# ++++++++++++ loop through schools  ++++++++++++++++++++++++++++
    for schoolbase_dict in schoolbase_dictlist:
        # fields are: sbase_id, sbase_code, sch_name
        schoolbase_pk = schoolbase_dict.get('sbase_id')
        schoolbase_code = schoolbase_dict.get('sbase_code')
        school_name = schoolbase_dict.get('sch_name')

# +++ get nested dicts of subjects of this  school, dep, level, lang, ete_exam
        count_dict = subj_view.create_studsubj_count_dict(sel_examyear_instance, request, schoolbase_pk)

        total_dict = count_dict.get('total')

        if logging_on:
            logger.debug('...........school_name: ' + str(school_name))
            logger.debug('count_dict: ' + str(count_dict))
            logger.debug('total_dict: ' + str(total_dict))

# - skip when school has no totals
        if total_dict:
            col_count, first_subject_column, col_width, field_names, field_captions, \
            header_formats, detail_row_formats, summary_row_formats, totalrow_formats = \
                create_row_formats(subjectbase_dictlist, total_dict, formats)

# +++++ create worksheet per school
            sheet = book.add_worksheet(schoolbase_code)
            sheet.hide_gridlines(2)  # 2 = Hide screen and printed gridlines

    # --- set column width
            for i, width in enumerate(col_width):
                sheet.set_column(i, i, width)

    # --- title row
            title = ' '.join((schoolbase_code, school_name, ' -  Bestelling examens', str(sel_examyear_instance.code)))
            sheet.write(0, 0, settings['minond'], formats['bold_format'])
            sheet.write(1, 0, now_formatted)

            sheet.write(3, 0, title, formats['bold_format'])

            row_index = 7
#########################################################################
            write_orderlist_per_school(
                sheet, count_dict, department_dictlist, lvlbase_dictlist,
                row_index, col_count, first_subject_column, title, field_names, field_captions,
                formats, detail_row_formats, totalrow_formats)
#########################################################################
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
# - end of create_orderlist_per_school_xlsx


def create_orderlist_xlsx(sel_examyear_instance, list, user_lang, request):
    # PR2021-07-07 PR2021-08-20 PR2022-05-08 'herexamen details' added
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_orderlist_xlsx -----')
        # row: {'school_id': 78, 'schbase_code': 'CUR13', 'school_name': 'Abel Tasman College', 'dep_id': 97, 'depbase_code': 'Vsbo',
        #           'lvl_id': 63, 'lvl_abbrev': 'TKL', 'subj_id': 998, 'subjbase_code': 'ne', 'subj_name': 'Nederlandse taal', '
        #           subj_published_arr': [None], 'lang': 'ne', 'count': 7}

# get text from examyearsetting
    settings = awpr_lib.get_library(sel_examyear_instance, ['exform', 'ex1'])

# --- get department dictlist
    # fields are: depbase_id, depbase_code, dep_name, dep_level_req
    department_dictlist = subj_view.create_departmentbase_dictlist(sel_examyear_instance)

# --- get lvlbase dictlist
    lvlbase_dictlist = subj_view.create_levelbase_dictlist(sel_examyear_instance)

# +++ get subjectbase dictlist
    # functions creates ordered dictlist of all subjectbase pk and code of this exam year of all countries
    subjectbase_dictlist = subj_view.create_subjectbase_dictlist(sel_examyear_instance)
    """
    subjectbase_pk_list: [
        {'id': 153, 'code': 'adm&co'}, 
        ... 
        {'id': 151, 'code': 'zwi'}]
    """

# +++ get schoolbase dictlist
    # functions creates ordered dictlist of all schoolbase_pk, schoolbase_code and school_name of this exam year of all countries
    schoolbase_dictlist = subj_view.create_schoolbase_dictlist(sel_examyear_instance, request)
    """
    schoolbase_dictlist: [
        {'sbase_id': 2, 'sbase_code': 'CUR01', 'sch_name': 'Ancilla Domini Vsbo'}, 
        ...
        {'sbase_id': 37, 'sbase_code': 'SXM03', 'sch_name': 'Sundial School'}
        {'sbase_id': 23, 'sbase_code': 'CURETE', 'sch_article': 'het', 'sch_name': 'Expertisecentrum voor Toetsen & Examens', 'sch_abbrev': 'ETE'},
        {'sbase_id': 39, 'sbase_code': 'SXMDOE', 'sch_article': 'de', 'sch_name': 'Division of Examinations', 'sch_abbrev': 'Division of Examinations'}] 
        ]
    """

# +++ get nested dicts of subjects per school, dep, level, lang, ete_exam
    count_dict = subj_view.create_studsubj_count_dict(sel_examyear_instance, request)

    if logging_on:
        logger.debug('count_dict: ' + str(count_dict))

    response = None

    if count_dict:

# ---  create file Name and worksheet Name
        now_formatted = af.format_modified_at(timezone.now(), user_lang, False)  # False = not month_abbrev

        today_dte = af.get_today_dateobj()
        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
        file_name = ''.join(('Bestellijst examens ', str(sel_examyear_instance.code), ' dd ', today_dte.isoformat(), '.xlsx'))

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

# create dict with cell formats
        formats = create_formats(book)

# ++++++++++++ loop through sheets  ++++++++++++++++++++++++++++
        for ete_duo in ('ETE', 'DUO'):
            for summary_detail in ('overzicht', 'details', 'herexamens', 'herexamen details'):
                is_herexamens = summary_detail in ('herexamens', 'herexamen details')

                if ete_duo in count_dict:
                    ete_duo_dict = count_dict.get(ete_duo)
                    ete_duo_dict_total = ete_duo_dict.get('total')

            # get number of subject columns from DEO / ETE total dict
                    # 'DUO': {'total': {137: 513, 134: 63, 156: 63, 175: 63},
                    # columns are (0: 'schoolbase_code', 1: school_name"
                    # columns 2 etc  are subject columns. Extend number when more than 15 subjects

                    col_count, first_subject_column, col_width, field_names, field_captions, \
                        col_header_formats, detail_row_formats, summary_row_formats, totalrow_formats = \
                            create_row_formats(subjectbase_dictlist, ete_duo_dict_total, formats)

# +++++ create worksheet +++++
                    sheet_name = ' '.join((ete_duo, summary_detail))
                    sheet = book.add_worksheet(sheet_name)
                    sheet.hide_gridlines(2) # 2 = Hide screen and printed gridlines

    # --- set column width
                    for i, width in enumerate(col_width):
                        sheet.set_column(i, i, width)

    # --- title row
                    exam_str = summary_detail if is_herexamens else 'examens'
                    title = ' '.join(('Bestellijst', ete_duo, exam_str, str(sel_examyear_instance.code)))
                    sheet.write(0, 0, settings['minond'], formats['bold_format'])
                    sheet.write(1, 0, now_formatted)
                    if not is_herexamens:
                        exta_txt = ' '.join (('   -  ',
                              str(sel_examyear_instance.order_extra_fixed),  str(_('extra exams plus')),
                              str(sel_examyear_instance.order_extra_perc) + '%,',  str(_('rounded up to')),
                              str(sel_examyear_instance.order_round_to) + '.'))
                        sheet.write(3, 0, str(_('Calulation of extra exams:')))
                        sheet.write(4, 0, exta_txt)
                    else:
                        tv2_txt = ' '.join (('   -  ',
                             str(sel_examyear_instance.order_tv2_multiplier), str(_('exams per')),
                             str(sel_examyear_instance.order_tv2_divisor), str(_('exams first exam period,')),
                             str(_('with a maximum of')), str(sel_examyear_instance.order_tv2_max), '.'))
                        sheet.write(3, 0, str(_('Calulation exams second exam period:')))
                        sheet.write(4, 0, tv2_txt)

                    row_index = 7
    #########################################################################
                    if summary_detail in ('details', 'herexamen details'):
                        write_orderlist_with_details(
                            sheet, ete_duo_dict, is_herexamens, department_dictlist, lvlbase_dictlist, schoolbase_dictlist,
                            row_index, col_count, first_subject_column, list, title, field_names, field_captions,
                            formats, col_header_formats, detail_row_formats,
                            totalrow_formats)
                    else:
                        write_orderlist_summary(
                            sheet, ete_duo_dict, is_herexamens, department_dictlist, lvlbase_dictlist, schoolbase_dictlist,
                            row_index, col_count, first_subject_column, list, title, field_names, field_captions,
                            formats, col_header_formats, detail_row_formats,
                            totalrow_formats)

#########################################################################
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


def write_orderlist_summary(sheet, ete_duo_dict, is_herexamens, department_dictlist, lvlbase_dictlist, schoolbase_dictlist,
                                 row_index, col_count, first_subject_column, list, title, field_names, field_captions,
                                 formats, col_header_formats, detail_row_formats, totalrow_formats):
    logging_on = False  # s.LOGGING_ON

# ---  ETE / DUO title row
    sheet.merge_range(row_index, 0, row_index, col_count - 1, title, formats['ete_duo_headerrow'])

    # ---  language column header row
    row_index += 1
    sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', col_header_formats[0])
    for i in range(first_subject_column, col_count):  # range(start_value, end_value, step), end_value is not included!
        sheet.write(row_index, i, field_captions[i], col_header_formats[i])

    # ---  ETE / DUO total row > moved to the end
    row_index += 1
    eteduo_total_row_index = row_index
    #write_total_row(sheet, ete_duo_dict, row_index, field_names, first_subject_column,
    #                is_herexamens, formats['totalrow_merge'], totalrow_formats)

# +++++++++++++ loop through language  ++++++++++++++++++++++++++++
    for lang in ('ne', 'pa', 'en'):

        if lang in ete_duo_dict:
            lang_dict = ete_duo_dict.get(lang)

# ---  language title row
            row_index += 2
            lang_full = 'ENGELSTALIGE' if lang == 'en' else 'PAPIAMENTSTALIGE' if lang == 'pa' else 'NEDERLANDSTALIGE'
            examens_txt = 'HEREXAMENS' if is_herexamens else 'EXAMENS'
            title_txt = ' '.join((lang_full,examens_txt ))
            sheet.merge_range(row_index, 0, row_index, col_count - 1, title_txt, formats['lang_headerrow'])
    # ---  language column header row
            row_index += 1
            sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', col_header_formats[0])
            for i in range(first_subject_column,
                           col_count):  # range(start_value, end_value, step), end_value is not included!
                sheet.write(row_index, i, field_captions[i], col_header_formats[i])
    # ---  language total row > moved to the end
            row_index += 1
            lang_total_row_index = row_index
           # write_total_row(sheet, lang_dict, row_index, field_names, first_subject_column,
           #                 is_herexamens, formats['totalrow_merge'], totalrow_formats)

# +++++++++++++++++++++ loop through departent  ++++++++++++++++++++++++++++
            for department_dict in department_dictlist:
                # fields are: depbase_id, depbase_code, dep_name, dep_level_req
                depbase_pk = department_dict.get('depbase_id')
                dep_code = department_dict.get('depbase_code')
                # department_dict: {'depbase_pk': 3, 'name': 'Voorbereidend Wetenschappelijk Onderwijs', 'code': 'Vwo', 'level_req': False}
                if depbase_pk in lang_dict:
                    dep_dict = lang_dict.get(depbase_pk)

        # ++++++++++++ loop through levels  ++++++++++++++++++++++++++++
                    for lvlbase_dict in lvlbase_dictlist:
                        # fields are lvlbase_id, lvlbase_code, lvl_name",
                        # lvlbase_dict: {'lvlbase_id': 12, 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 'lvlbase_code': 'TKL'}
                        lvlbase_pk = lvlbase_dict.get('lvlbase_id')
                        lvlbase_code = lvlbase_dict.get('lvlbase_code')
                        if logging_on:
                            logger.debug('lvlbase_dict: ' + str(lvlbase_dict))
                        if lvlbase_code:
                            dep_lvl_name = ' '.join((dep_code, lvlbase_code))
                        else:
                            dep_lvl_name = dep_code

                        if lvlbase_pk in dep_dict:
                            level_dict = dep_dict.get(lvlbase_pk)

                # ---  dep / level row
                            last_row_index = write_summary_row(sheet, level_dict, is_herexamens, row_index, first_subject_column, list,
                                              field_names, dep_lvl_name, detail_row_formats)
                            row_index = last_row_index
        # --- write language total row
            lang_last_row_index = row_index + 1
            write_total_row_with_formula(sheet, formats, lang_total_row_index, lang_last_row_index,
                                         field_names, totalrow_formats)

# --- write ete_duo total row
    eteduo_last_row_index = row_index + 1
    write_total_row_with_formula(sheet, formats, eteduo_total_row_index, eteduo_last_row_index,
                                 field_names, totalrow_formats)

# - end of write_orderlist_summary


def write_orderlist_with_details(sheet, ete_duo_dict, is_herexamens, department_dictlist, lvlbase_dictlist, schoolbase_dictlist,
                                 row_index, col_count, first_subject_column, list, title, field_names, field_captions,
                                 formats, col_header_formats, detail_row_formats, totalrow_formats):
    logging_on = s.LOGGING_ON

    has_separate_extra_row = False
    base_extra_tuple = ('',)
    if list == 'totals_only':
        base_extra_tuple = (' incl. extra',)
    elif list in ('extra_separate', 'per_school'):
        has_separate_extra_row = True
        base_extra_tuple = ('', ' extra')

# ---  ETE / DUO title row
    sheet.merge_range(row_index, 0, row_index, col_count - 1, title, formats['ete_duo_headerrow'])

# ---  column header row
    row_index += 1
    sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', col_header_formats[0])
    for i in range(first_subject_column, col_count):  # range(start_value, end_value, step), end_value is not included!
        sheet.write(row_index, i, field_captions[i], col_header_formats[i])

# ---  ETE / DUO total row > moved to the end
    row_index += 1
    eteduo_total_row_index = row_index

# +++++++++++++ loop through language  ++++++++++++++++++++++++++++
    for lang in ('ne', 'pa', 'en'):

        if lang in ete_duo_dict:
            lang_dict = ete_duo_dict.get(lang)

    # ---  language title row
            row_index += 2
            lang_full = 'ENGELSTALIGE EXAMENS' \
                if lang == 'en' else 'PAPIAMENTSTALIGE EXAMENS' \
                if lang == 'pa' else 'NEDERLANDSTALIGE EXAMENS'
            sheet.merge_range(row_index, 0, row_index, col_count - 1, lang_full, formats['lang_headerrow'])

    # ---  language column header row
            row_index += 1
            sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', col_header_formats[0])
            for i in range(first_subject_column, col_count):  # range(start_value, end_value, step), end_value is not included!
                sheet.write(row_index, i, field_captions[i], col_header_formats[i])

    # ---  language total row  > moved to the end
            row_index += 1
            lang_total_row_index = row_index

# +++++++++++++++++++++ loop through departent  ++++++++++++++++++++++++++++
            for department_dict in department_dictlist:
                # fields are: depbase_id, depbase_code, dep_name, dep_level_req
                depbase_pk = department_dict.get('depbase_id')
                dep_name = department_dict.get('dep_name')
                level_req = department_dict.get('dep_level_req', False)
                if depbase_pk in lang_dict:
                    dep_dict = lang_dict.get(depbase_pk)

    # ---  departent title row
                    row_index += 2
                    sheet.merge_range(row_index, 0, row_index, col_count - 1, dep_name, formats['dep_headerrow'])
    # ---  departent column header row
                    row_index += 1
                    sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', col_header_formats[0])
                    for i in range(first_subject_column, col_count):
                        sheet.write(row_index, i, field_captions[i], col_header_formats[i])
    # ---  departent total row > moved to the end
                    row_index += 1
                    depbase_total_row_index = row_index

# ++++++++++++ loop through levels  ++++++++++++++++++++++++++++
                    for lvlbase_dict in lvlbase_dictlist:
                        # fields are lvlbase_id, lvlbase_code, lvl_name",
                        # lvlbase_dict: {'lvlbase_id': 12, 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 'lvlbase_code': 'TKL'}
                        if logging_on:
                            logger.debug('lvlbase_dict: ' + str(lvlbase_dict))

                        lvlbase_pk = lvlbase_dict.get('lvlbase_id')
                        lvl_name = lvlbase_dict.get('lvl_name')
                        if lvlbase_pk in dep_dict:
                            level_dict = dep_dict.get(lvlbase_pk)

                            if logging_on:
                                logger.debug('level_dict: ' + str(level_dict))
                            """
                            level_dict: {'c': 'PBL', 
                                        'total': {
                                            'total': {440: [114, 21, 35], 464: [67, 13, 25], 442: [37, 8, 15], 423: [197, 23, 50], 430: [190, 20, 50], 432: [114, 21, 35], 438: [5, 5, 5], 429: [3, 2, 5], 435: [4, 6, 5]}, 
                                             2:      {'c': 'Sxm', 440: [52, 8, 15], 464: [30, 5, 10], 442: [30, 5, 10], 423: [82, 8, 20], 432: [52, 8, 15], 430: [82, 8, 20]}, 
                                             1:      {'c': 'Cur', 430: [108, 12, 30], 442: [7, 3, 5], 432: [62, 13, 20], 438: [5, 5, 5], 464: [37, 8, 15], 440: [62, 13, 20], 423: [115, 15, 30], 429: [3, 2, 5], 435: [4, 6, 5]}}, 
                                        35: {'c': 'SXM01', 440: [52, 8, 15], 464: [30, 5, 10], 442: [30, 5, 10], 423: [82, 8, 20], 432: [52, 8, 15], 430: [82, 8, 20]}, 
                                        2: {'c': 'CUR01', 430: [82, 8, 20], 432: [52, 8, 15], 464: [30, 5, 10], 423: [82, 8, 20], 440: [52, 8, 15]}, 
                                        4: {'c': 'CUR03', 442: [7, 3, 5], 432: [10, 5, 5], 430: [26, 4, 10], 438: [5, 5, 5], 464: [7, 3, 5], 440: [10, 5, 5], 423: [33, 7, 10], 429: [3, 2, 5], 435: [4, 6, 5]}}
                            """

                            lvlbase_total_row_index = 0
                # ---  level title row
                            # skip when Havo / Vwo
                            if level_req:
                                row_index += 2
                                sheet.merge_range(row_index, 0, row_index, col_count - 1, lvl_name, formats['lvl_headerrow'])
                # ---  level column header row
                                row_index += 1
                                for i in range(0, col_count):
                                    sheet.write(row_index, i, field_captions[i], col_header_formats[i])

                # ---  level total row  > moved to the end
                                row_index += 1
                                lvlbase_total_row_index = row_index

        # ++++++++++++ loop through schools  ++++++++++++++++++++++++++++
                            for schoolbase_dict in schoolbase_dictlist:
                                schoolbase_pk = schoolbase_dict.get('sbase_id')
                                if schoolbase_pk in level_dict:
                                    defaultrole = schoolbase_dict.get('defaultrole', 0)
                                    for x, key in enumerate(base_extra_tuple):
                                        # skip 'non_extra' row when ETE/DEX
                                        skip_non_extra_row = (has_separate_extra_row and defaultrole == c.ROLE_064_ADMIN and x == 0)
                                        if not skip_non_extra_row:
                                            row_index += 1
                                            school_dict = level_dict.get(schoolbase_pk)

                                            if logging_on:
                                                logger.debug('schoolbase_dict: ' + str(schoolbase_dict))
                                                logger.debug('school_dict: ' + str(school_dict))

                                            """
                                            schoolbase_dict: {'sbase_id': 2, 'sbase_code': 'CUR01', 'sch_name': 'Ancilla Domini Vsbo'}
                                            school_dict: {138: [88, 0, 20], 134: [88, 0, 20]}
                                            """
                                            total = 0
                                            for i, field_name in enumerate(field_names):
                                                if i == 0:
                                                    value = schoolbase_dict.get('sbase_code', '---')
                                                    sheet.write(row_index, i, value, detail_row_formats[i])
                                                elif i == 1:
                                                    value = schoolbase_dict.get('sch_name', '---') + key
                                                    sheet.write(row_index, i, value, detail_row_formats[i])
                                                elif isinstance(field_name, int):
                                                    value = None
                                                    value_arr = school_dict.get(field_name)
                                                    if value_arr:
                                                        if is_herexamens:
                                                            value = value_arr[2]
                                                        else:
                                                            if has_separate_extra_row:
                                                                value = value_arr[x]
                                                            else:
                                                                value = value_arr[0] + value_arr[1]
                                                    if value:
                                                        total += value
                                                    sheet.write(row_index, i, value, detail_row_formats[i])

                                                elif field_name == 'rowtotal':
                                                    last_column = len(field_names) - 1

                                                    upper_cell_ref = subj_view.xl_rowcol_to_cell(row_index, 2)  # cell_ref: 10,0 > A11
                                                    lower_cell_ref = subj_view.xl_rowcol_to_cell(row_index, last_column -1)  # cell_ref: 10,0 > A11

                                                    sum_cell_ref = subj_view.xl_rowcol_to_cell(row_index, last_column)  # cell_ref: 10,0 > A11

                                                    formula = ''.join(['=SUM(', upper_cell_ref, ':', lower_cell_ref, ')'])
                                                    sheet.write_formula(sum_cell_ref, formula, detail_row_formats[last_column])
                            if level_req:
                                # add 1 extra row t subtotal range, to prevent leaving out last row in calculation when manually added extra rows
                                lvlbase_last_row_index = row_index + 1
                                write_total_row_with_formula(sheet, formats,  lvlbase_total_row_index,
                                    lvlbase_last_row_index, field_names, totalrow_formats)

        # --- write departent total row
                    depbase_last_row_index = row_index + 1
                    write_total_row_with_formula(sheet, formats,depbase_total_row_index, depbase_last_row_index,
                                                 field_names, totalrow_formats)

    # --- write language total row
            lang_last_row_index = row_index + 1
            write_total_row_with_formula(sheet, formats, lang_total_row_index, lang_last_row_index,
                                         field_names, totalrow_formats)
# --- write ete_duo total row
        eteduo_last_row_index = row_index + 1
        write_total_row_with_formula(sheet, formats, eteduo_total_row_index, eteduo_last_row_index,
                                     field_names, totalrow_formats)

# - end of write_orderlist_with_details


def write_orderlist_per_school(sheet, count_dict, department_dictlist, lvlbase_dictlist,
                                 row_index, col_count, first_subject_column, title, field_names, field_captions,
                                 formats, detail_row_formats, totalrow_formats):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- write_orderlist_per_school -----')

    list = 'extra_separate'

# ---  TOTAL title row 'CUR01 Ancilla Domini Vsbo  -  Bestelling examens 2022'
    sheet.merge_range(row_index, 0, row_index, col_count - 1, title, formats['ete_duo_headerrow'])

# ---  grandtotal subject header row
    row_index += 1
    write_subject_header_row(sheet, row_index, col_count, first_subject_column, field_captions, formats)

# ---  grandtotal_row_index row > moved to the end
    row_index += 1
    grandtotal_row_index = row_index

    for ete_duo in ('ETE', 'DUO'):
        if ete_duo in count_dict:
            ete_duo_dict = count_dict.get(ete_duo)

    # ---  ETE / DUO title row
            row_index += 2
            title = ete_duo + ' EXAMENS'
            sheet.merge_range(row_index, 0, row_index, col_count - 1, title, formats['lang_headerrow'])

    # ---  ete_duo subject header row
            row_index += 1
            write_subject_header_row(sheet, row_index, col_count, first_subject_column, field_captions, formats)

    # ---  ete_duo total row > moved to the end
            row_index += 1
            eteduo_total_row_index = row_index

# +++++++++++++ loop through language  ++++++++++++++++++++++++++++
            for lang in ('ne', 'pa', 'en'):
                if lang in ete_duo_dict:
                    lang_dict = ete_duo_dict.get(lang)

     # ---  language title row
                    row_index += 2
                    lang_full = 'ENGELSTALIGE EXAMENS' \
                        if lang == 'en' else 'PAPIAMENTSTALIGE EXAMENS' \
                        if lang == 'pa' else 'NEDERLANDSTALIGE EXAMENS'
                    sheet.merge_range(row_index, 0, row_index, col_count - 1, lang_full, formats['dep_headerrow'])

    # ---  language subject header row
                    row_index += 1
                    write_subject_header_row(sheet, row_index, col_count, first_subject_column, field_captions, formats)

    # ---  language total row > moved to the end
                    row_index += 1
                    lang_total_row_index = row_index

# +++++++++++++++++++++ loop through departent  ++++++++++++++++++++++++++++
                    for department_dict in department_dictlist:
                        # fields are: depbase_id, depbase_code, dep_name, dep_level_req
                        depbase_pk = department_dict.get('depbase_id')
                        dep_code = department_dict.get('depbase_code')
                        # department_dict: {'depbase_pk': 3, 'name': 'Voorbereidend Wetenschappelijk Onderwijs', 'code': 'Vwo', 'level_req': False}
                        if depbase_pk in lang_dict:
                            dep_dict = lang_dict.get(depbase_pk)

# ++++++++++++ loop through levels  ++++++++++++++++++++++++++++
                            for lvlbase_dict in lvlbase_dictlist:
                                # fields are lvlbase_id, lvlbase_code, lvl_name",
                                # lvlbase_dict: {'lvlbase_id': 12, 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 'lvlbase_code': 'TKL'}
                                lvlbase_pk = lvlbase_dict.get('lvlbase_id')
                                lvlbase_code = lvlbase_dict.get('lvlbase_code')

                                if lvlbase_code:
                                    dep_lvl_name = ' '.join((dep_code, lvlbase_code))
                                else:
                                    dep_lvl_name = dep_code

                                if lvlbase_pk in dep_dict:
                                    level_dict = dep_dict.get(lvlbase_pk)

        # ---  dep / level row
                                    last_rowindex = write_summary_row(sheet, level_dict, False, row_index, first_subject_column,
                                                      list, field_names, dep_lvl_name, detail_row_formats)
                                    row_index = last_rowindex

        # --- write total row
                    lang_last_row_index = row_index + 1
                    write_total_row_with_formula(sheet, formats, lang_total_row_index, lang_last_row_index,
                                                 field_names, totalrow_formats)

        # --- write ete_duo total row
            eteduo_last_row_index = row_index + 1
            write_total_row_with_formula(sheet, formats, eteduo_total_row_index, eteduo_last_row_index,
                                         field_names, totalrow_formats)

# --- write grandtotal row
    grandtotal_last_row_index = row_index + 1
    write_total_row_with_formula(sheet, formats, grandtotal_row_index, grandtotal_last_row_index,
                                 field_names, totalrow_formats)
# - end of write_orderlist_per_school


def write_subject_header_row(sheet, row_index, col_count, first_subject_column, field_captions, formats):
    sheet.write(row_index, 0, None, formats['border_left_bottom'])
    sheet.write(row_index, 1, None, formats['border_bottom'])
    for i in range(first_subject_column, col_count):  # range(start_value, end_value, step), end_value is not included!
        sheet.write(row_index, i, field_captions[i], formats['th_align_center'])
# - end of write_subject_header_row

#$$$$$$$4$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
def write_summary_row(sheet, item_dict, is_herexamens, row_index, first_subject_column,
                      list, field_names, caption, detail_row_formats):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- write_summary_row -----')
        logger.debug('is_herexamens: ' + str(is_herexamens))
        logger.debug('field_names: ' + str(field_names))

    item_dict_total = item_dict.get('total')
    if logging_on:
        logger.debug('item_dict_total: ' + str(item_dict_total))

    if list == 'totals_only':
        has_separate_extra_row = False
        base_extra_tuple = (' incl. extra',)
    else:
        has_separate_extra_row = True
        base_extra_tuple = ('', ' extra')

    for x, key in enumerate(base_extra_tuple):
        if key:
            caption += key

        row_index += 1
        total = 0
        for i, field_name in enumerate(field_names):
            if i == 0:
                sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, caption, detail_row_formats[0])
                #sheet.write(row_index, i, caption, detail_row_formats[i])
            elif i == 1:
                pass
            elif isinstance(field_name, int):
                value = None
                value_arr = item_dict_total.get(field_name)

                if value_arr:
                    if is_herexamens:
                        value = value_arr[2]
                    else:
                        if has_separate_extra_row:
                            value = value_arr[x]
                        else:
                            value = value_arr[0] + value_arr[1]
                    total += value
                if value == 0:
                    value = None
                sheet.write(row_index, i, value, detail_row_formats[i])

            elif field_name == 'rowtotal':

                last_column = len(field_names) -1

                upper_cell_ref = subj_view.xl_rowcol_to_cell(row_index, 2)  # cell_ref: 10,0 > A11
                lower_cell_ref = subj_view.xl_rowcol_to_cell(row_index, last_column - 1)  # cell_ref: 10,0 > A11

                sum_cell_ref = subj_view.xl_rowcol_to_cell(row_index, last_column)  # cell_ref: 10,0 > A11

                formula = ''.join(['=SUM(', upper_cell_ref, ':', lower_cell_ref, ')'])
                sheet.write_formula(sum_cell_ref, formula, detail_row_formats[last_column])

    last_rowindex = row_index
    return last_rowindex

# - end of write_summary_row

def write_total_row(sheet, item_dict, row_index, field_names, first_subject_column, is_herexamens,
                    totalrow_merge, totalrow_formats):
    item_dict_total = item_dict.get('total')
    # {'total': {156: [101, 9, 25], [count, extra, tv2]
    total = 0
    for i, field_name in enumerate(field_names):
        if i == 0:
            # ??? sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, 'TOTAAL ', totalrow_merge)
            pass
        elif isinstance(field_name, int):
            base_plus_extra = 0
            count_arr = item_dict_total.get(field_name)
            if count_arr:
                if is_herexamens:
                    base_plus_extra = count_arr[2]
                else:
                    base_plus_extra = count_arr[0] + count_arr[1]

                total += base_plus_extra
            if base_plus_extra == 0:
                base_plus_extra = None
            sheet.write(row_index, i, base_plus_extra, totalrow_formats[i])

    last_column = len(field_names) -1
    if total == 0:
        total = None
    sheet.write(row_index, last_column, total, totalrow_formats[last_column - 1])
# - end of write_total_row


def write_total_row_with_formula(sheet, formats, subtotal_total_row_index, subtotal_last_row_index,
                                 field_names, totalrow_formats):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  write_total_row_with_formula  -----')

    if subtotal_total_row_index:

        totalrow_merge = formats['totalrow_merge']
        border_left_bottom = formats['border_left_bottom']
        border_bottom = formats['border_bottom']

        for i, field_name in enumerate(field_names):
            if i == 0:
                # PR2021-09-02 debug. Here merge_range doesn't work. Dont know why
                #sheet.merge_range(subtotal_total_row_index, 0, subtotal_total_row_index, first_subject_column - 1, 'TOTAAL ', totalrow_merge)
                #sheet.merge_range(subtotal_total_row_index, 0, subtotal_total_row_index, 1, 'TOTAAL ', totalrow_merge)
                sheet.write(subtotal_total_row_index, i, '', border_left_bottom)
            elif i == 1:
                sheet.write(subtotal_total_row_index, i, 'TOTAAL ', border_bottom)
            elif isinstance(field_name, int) or field_name == 'rowtotal':

        # use 'sum' in total column, 'subtotal' in subject columns
                if field_name == 'rowtotal':
                    upper_cell_ref = subj_view.xl_rowcol_to_cell(subtotal_total_row_index, 2)
                    lower_cell_ref = subj_view.xl_rowcol_to_cell(subtotal_total_row_index, i - 1)
                    sum = ''.join(['SUM(', upper_cell_ref, ':', lower_cell_ref, ')'])
                else:
                    upper_cell_ref = subj_view.xl_rowcol_to_cell(subtotal_total_row_index + 1, i)
                    lower_cell_ref = subj_view.xl_rowcol_to_cell(subtotal_last_row_index, i)
                    sum = ''.join(('SUBTOTAL(9,', upper_cell_ref, ':', lower_cell_ref, ')'))
        # hide zero's in subtotal
                formula = ''.join(['=IF(', sum, '=0, "", ', sum, ')'])

                sum_cell_ref = subj_view.xl_rowcol_to_cell(subtotal_total_row_index, i)
                sheet.write_formula(sum_cell_ref, formula, totalrow_formats[i])
# - end of write_total_row_with_formula


def create_row_formats(subjectbase_dictlist, ete_duo_dict_total, formats):
    # form https://stackoverflow.com/questions/16819222/how-to-return-dictionary-keys-as-a-list-in-python
    # subject_count = len([*ete_duo_dict_total])
    # ete_duo_dict_total contains a dict with keys = subjectbase_pk and value = count of subjects

    col_count = 2  # schoolbase_code', 1: school_name
    col_width = [8, 45]
    subject_col_width = 4.5
    field_names = ['schoolbase_code', 'school_name']
    field_captions = ['', '']
    col_header_formats = [formats['border_left_bottom'], formats['border_bottom']]
    detail_row_formats = [formats['detailrow_col0'], formats['detailrow_col1']]
    summary_row_formats = [formats['detailrow_col0'], formats['detailrow_col1']]
    totalrow_formats = [formats['totalrow_merge'], formats['totalrow_align_center']]
    first_subject_column = col_count

# - loop through subjectbase_dictlist to get the subject code in alphabetic order,
    # add sjbase_pk to field_names, only when subject is in count_dict
    # subjectbase_dictlist: [{'id': 153, 'code': 'adm&co'}, {'id': 162, 'code': 'asw'},
    for subjectbase_dict in subjectbase_dictlist:
        sjbase_pk = subjectbase_dict.get('id')
        sjbase_code = subjectbase_dict.get('code', '---')
        if sjbase_pk and sjbase_pk in ete_duo_dict_total:
            field_names.append(sjbase_pk)
            field_captions.append(sjbase_code)
            col_count += 1
            col_width.append(subject_col_width)
            col_header_formats.append(formats['th_align_center'])
            detail_row_formats.append(formats['row_align_center'])
            summary_row_formats.append(formats['row_align_center'])
            totalrow_formats.append(formats['totalrow_number'])
# - add total at end of list
    field_names.append('rowtotal')
    field_captions.append(str(_('Total')))
    col_count += 1
    col_width.append(6)
    col_header_formats.append(formats['th_align_center'])
    detail_row_formats.append(formats['row_total'])
    summary_row_formats.append(formats['row_total'])
    totalrow_formats.append(formats['totalrow_number'])

    return col_count, first_subject_column, col_width, field_names, field_captions, col_header_formats, detail_row_formats, summary_row_formats, totalrow_formats
# - end of create_row_formats


def create_formats(book):
    formats = {
        'bold_format': book.add_format({'bold': True}),
        'th_align_center': book.add_format(
            {'font_size': 11, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}),
        'th_rotate': book.add_format(
            {'font_size': 11, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
             'rotation': 90}),
        'th_merge_bold': book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'}),
        'detailrow_col0': book.add_format( {'font_size': 11, 'font_color': 'blue', 'valign': 'vcenter'}),
        'detailrow_col1': book.add_format( {'font_size': 11, 'font_color': 'blue', 'valign': 'vcenter'}),
        'row_align_center': book.add_format(
            {'font_size': 11, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True}),
        'row_total': book.add_format({'font_size': 11, 'align': 'center', 'valign': 'vcenter', 'border': True}),
        'totalrow_align_center': book.add_format(
            {'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter', 'border': True}),
        'totalrow_number': book.add_format(
            {'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter', 'border': True}),
        'totalrow_merge': book.add_format({'bold': True, 'border': True, 'align': 'right', 'valign': 'vcenter'}),
        'ete_duo_headerrow': book.add_format(
            {'font_size': 14, 'font_color': 'white', 'border': True, 'bold': True, 'align': 'center',
             'valign': 'vcenter'}),
        'lang_headerrow': book.add_format(
            {'font_size': 14, 'border': True, 'bold': True, 'align': 'center', 'valign': 'vcenter'}),
        'dep_headerrow': book.add_format(
            {'font_size': 14, 'border': True, 'bold': True, 'align': 'center', 'valign': 'vcenter'}),
        'lvl_headerrow': book.add_format(
            {'font_size': 14, 'border': True, 'bold': True, 'align': 'center', 'valign': 'vcenter'}),

        'border_left_bottom': book.add_format({'valign': 'vcenter'}),
        'border_bottom': book.add_format({'bold': True, 'align': 'right', 'valign': 'vcenter'}),
    }

    formats['th_merge_bold'].set_left()
    formats['th_merge_bold'].set_bottom()
    formats['ete_duo_headerrow'].set_bg_color('#6c757d')  # ##6c757d;  /* awp tab greay 1088 117 125 100%
    formats['lang_headerrow'].set_bg_color('#d8d8d8')  # #d8d8d8;  /* light grey 218 218 218 100%
    formats['dep_headerrow'].set_bg_color('#f2f2f2')  # ##f2f2f2;  /* light light grey 242 242 242 100%

    formats['border_left_bottom'].set_left()
    formats['border_left_bottom'].set_bottom()
    formats['border_bottom'].set_bottom()

    formats['detailrow_col0'].set_left()
    formats['detailrow_col0'].set_bottom()
    formats['detailrow_col1'].set_bottom()

    return formats
# - end of create_formats


############ DOWNLOAD STUDENT DATA ########################## PR2022-05-18
@method_decorator([login_required], name='dispatch')
class StudentDownloadXlsxView(View):  # PR2022-05-18

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= StudentDownloadXlsxView ============= ')
        # function xlsx file with student data
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

                if sel_examyear and sel_school and sel_department:

                    response = create_student_xlsx(sel_examyear, sel_school, sel_department, user_lang)

        #except:
        #    raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of StudentDownloadXlsxView


# +++++++++++ Scheme list ++++++++++++
def create_student_xlsx(sel_examyear, sel_school, sel_department, user_lang):  # PR2022-05-18
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_student_xlsx -----')

    # from https://stackoverflow.com/questions/16393242/xlsxwriter-object-save-as-http-response-to-create-download-in-django
    # logger.debug('period_dict: ' + str(period_dict))

    response = None

    def get_student_rows():
        # --- create rows of all students of this examyear / school PR2020-10-27 PR2022-01-03 PR2022-05-18
        # - show only students that are not tobedeleted
        if logging_on:
            logger.debug(' ----- get_student_rows -----')

        sub_list = ["SELECT studsubj.student_id FROM students_studentsubject AS studsubj",
                    "WHERE studsubj.subj_published_id IS NOT NULL",
                    "AND NOT studsubj.tobedeleted",
                    "GROUP BY studsubj.student_id"]
        sub_sql = ' '.join(sub_list)
        sql_keys = {'ey_id': sel_examyear.pk, 'school_id': sel_school.pk, 'dep_id': sel_department.pk}
        sql_list = ["WITH studsubj AS (" + sub_sql + ")",
                    "SELECT schoolbase.code as sb_code, sch.name as school_name,",
                    "depbase.code AS db_code,",
                    "dep.level_req AS lvl_req, lvlbase.code AS lvlbase_code,",
                    "dep.sector_req AS sct_req, sctbase.code AS sctbase_code,",
                    "dep.has_profiel AS dep_has_profiel,",

                    # WS stands for with separator. First argument is separator
                    #"CONCAT_WS (' ', stud.prefix, CONCAT(stud.lastname, ','), stud.firstname) AS fullname,",
                    "stud.lastname, stud.firstname, stud.prefix, stud.gender,",
                    "stud.idnumber, stud.birthdate, stud.birthcountry, stud.birthcity,",

                    "stud.classname, stud.examnumber, stud.regnumber,",
                    "CASE WHEN stud.iseveningstudent THEN 'x' ELSE NULL END AS iseveningstudent,",
                    "CASE WHEN stud.islexstudent THEN 'x' ELSE NULL END AS islexstudent,",
                    "CASE WHEN stud.bis_exam THEN 'x' ELSE NULL END AS bis_exam,",
                    "CASE WHEN stud.partial_exam THEN 'x' ELSE NULL END AS partial_exam,",

                    "stud.modifiedby_id, stud.modifiedat,",
                    "au.last_name AS modby_name",

                    "FROM students_student AS stud",

                    "INNER JOIN studsubj ON (studsubj.student_id = stud.id)",

                    "INNER JOIN schools_school AS sch ON (sch.id = stud.school_id)",
                    "INNER JOIN schools_schoolbase AS schoolbase ON (schoolbase.id = sch.base_id)",

                    "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                    "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                     # PR2022-05-18 debug: with INNER JOIN subjects_levelbase the records without level are excluded (ie Havo Vwo)
                    "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",
                    "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",
                    "LEFT JOIN subjects_sectorbase AS sctbase ON (sctbase.id = sct.base_id)",

                    "LEFT JOIN accounts_user AS au ON (au.id = stud.modifiedby_id)",
                    "WHERE sch.examyear_id = %(ey_id)s::INT",
                    "AND sch.id = %(school_id)s::INT",
                    # show students of all departments
                    #"AND dep.id = %(dep_id)s::INT",
                    "AND NOT stud.tobedeleted",
                    "ORDER BY LOWER(schoolbase.code), dep.sequence, lvl.sequence, LOWER(stud.lastname), LOWER(stud.firstname);"
                    ]

        sql = ' '.join(sql_list)
        if logging_on:
            logger.debug('sql_keys: ' + str(sql_keys))
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            student_rows = af.dictfetchall(cursor)

        if logging_on:
            logger.debug('len(student_rows: ' + str(len(student_rows)))

        if logging_on and False:
            if student_rows:
                for row in student_rows:
                    logger.debug('row: ' + str(row))

        return student_rows
    # --- end of get_student_rows

    student_rows = get_student_rows()

    if student_rows:

        # ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
        school_name = ' '.join((sel_school.base.code, sel_school.name))
        title = ' '.join((str(_('Candidates')), str(school_name), str(sel_examyear), 'dd', today_dte.isoformat()))
        file_name = title + ".xlsx"
        worksheet_name = str(_('Candidates'))

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

        bold_format = book.add_format({'bold': True})
        titel_data = book.add_format({'font_size': 11, 'font_color': 'blue', 'valign': 'vcenter'})

        th_align_center = book.add_format(
            {'font_size': 8, 'border': True, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        th_align_center.set_bottom()
        th_align_center.set_bg_color('#d8d8d8')  # #d8d8d8;  /* light grey 218 218 218 100%

        th_merge_bold = book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        th_merge_bold.set_left()
        th_merge_bold.set_bottom()

        row_align_left = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter', 'border': True})
        row_align_center = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True})
        row_date_format = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'num_format': 'd mmmm yyyy', 'align': 'left', 'valign': 'vcenter', 'border': True})


# get number of columns
        field_names = ['sb_code', 'school_name', 'db_code', 'lvlbase_code', 'sctbase_code',
                       'examnumber', 'lastname', 'firstname', 'prefix', 'gender', 'idnumber',
                       'birthdate', 'birthcountry', 'birthcity',
                       'classname', 'regnumber',  'bis_exam',
                       'iseveningstudent', 'islexstudent', 'partial_exam',
                       'modifiedat', 'modby_name']

        field_captions = [str(_('School code')), str(_('School name')), str(_('Department')), str(_('Level')), str(_('Sector / Profiel')),
                          str(_('Exam number')), str(_('Last name')), str(_('First name')), str(_('Prefix')), str(_('Gender')), str(_('ID-number')),
                          str(_('Date of birth')), str(_('Country of birth')), str(_('Place of birth')),
                          str(_('Class')), str(_('Registration number')), str(_('Bis exam')),
                          str(_('Evening student')), str(_('Landsexamen')), str(_('Partial exam')),
                          str(_('Last modified on ')), str(_('Last modified by'))]

        field_width = [12, 25, 9, 9, 12,
                       12, 20, 25, 9, 6, 12,
                       15, 15, 12,
                       9, 15, 12,
                       12, 12, 12,
                       15, 15
                       ]

        header_format = th_align_center
        row_formats = [row_align_center, row_align_left, row_align_center, row_align_center, row_align_center,
                       row_align_center, row_align_left,  row_align_left, row_align_left, row_align_center, row_align_center,
                       row_date_format, row_align_left, row_align_left,
                       row_align_center, row_align_center, row_align_center,
                       row_align_center, row_align_center, row_align_center,
                       row_align_left, row_align_left
                       ]

# --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

        row_index = 0

# --- title row
        title = str(_('List of exam candidates'))
        sheet.write(row_index, 0, title, bold_format)
        row_index += 2
        sheet.write(row_index, 0, str(_('Exam year')) + ':', bold_format)
        sheet.write(row_index, 1, str(sel_examyear.code), titel_data)
        row_index += 1
        sheet.write(row_index, 0, str(_('School code')) + ':', bold_format)
        sheet.write(row_index, 1, str(sel_school.base.code), titel_data)
        row_index += 1
        sheet.write(row_index, 0, str(_('School')) + ':', bold_format)
        sheet.write(row_index, 1, str(sel_school.name), titel_data)

# --- write_student_header
        row_index += 2
        write_student_header(sheet, row_index, field_captions, header_format)

        # ---  write_student_rows
        for row in student_rows:
            row_index += 1
            write_student_rows(sheet, row_index, row, field_names, row_formats, user_lang)

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
# --- end of create_student_xlsx


def write_student_header(sheet, row_index, field_captions, header_format):  # PR2022-05-18
    for col_index, field_caption in enumerate(field_captions):
        sheet.write(row_index, col_index, field_caption, header_format)

# --- end of write_student_header


def write_student_rows(sheet, row_index, row, field_names, row_formats, user_lang):  # PR2022-05-18
    # ---  loop through columns

    for i, field_name in enumerate(field_names):
        if field_name == 'modifiedat':
            modified_dte = row.get(field_name, '')
            value = af.format_modified_at(modified_dte, user_lang)
        else:
            value = row.get(field_name, '')
        sheet.write(row_index, i, value, row_formats[i])

# --- end of write_student_rows



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
                sel_examyear_instance, sel_scheme_pk = \
                    dl.get_selected_examyear_scheme_pk_from_usersetting(request)

                # TODO set sel_scheme_pk not working properly, set None for now
                sel_scheme_pk = None

                if sel_examyear_instance :

    # +++ get dict of subjects of these studsubj_rows
                    scheme_rows = subj_view.create_scheme_rows(
                        examyear=sel_examyear_instance,
                        scheme_pk=sel_scheme_pk)
                    subjecttype_rows = subj_view.create_subjecttype_rows(
                        examyear=sel_examyear_instance,
                        scheme_pk=sel_scheme_pk,
                        orderby_sequence=True)
                    schemeitem_rows = subj_view.create_schemeitem_rows(
                        examyear=sel_examyear_instance,
                        scheme_pk=sel_scheme_pk,
                        orderby_name=True)
                    if schemeitem_rows:
                        response = create_scheme_xlsx(sel_examyear_instance, scheme_rows, subjecttype_rows, schemeitem_rows, user_lang)

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

        th_merge_bold = book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        th_merge_bold.set_left()
        th_merge_bold.set_bottom()

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
                       12, 12, 12,
                       12, 12, 12,
                       12,15,
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
                   'modifiedat', 'modby_username']
    field_captions = [str(_('Character')), str(_('Abbreviation')),
                      str(_('Minimum amount of subjects')),
                      str(_('Maximum amount of subjects')),
                      str(_("Minimum extra subject, doesn't count")),
                      str(_("Maximum extra subject, doesn't count")),
                      str(_("Minimum extra subject, counts")),
                      str(_("Maximum extra subject, counts")),
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

                   "rule_grade_sufficient, rule_gradesuff_notatevlex,",

                   'extra_count_allowed', 'extra_nocount_allowed',
                   'has_practexam',
                   'sr_allowed', 'max_reex',
                   'no_thirdperiod', 'no_exemption_ce',
                   'otherlang',
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
                      str(_('Has practical exam')), str(_('Has assignment')),
                      str(_('Herkansing SE allowed')), str(_('Maximum number of re-examinations')),
                      str(_('Subject has no third period')), str(_('Exemption without CE allowed')),
                      str(_('Other languages')),
                      str(_('Last modified on ')), str(_('Last modified by'))]
    header_format = th_align_center

    row_formats = []
    for x in range(0, col_count):  # range(start_value, end_value, step), end_value is not included!
        if 1 < x < col_count - 3:
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

                    elif field_name == 'otherlang':
                        other_lang = row.get(field_name)
                        value = other_lang
                        # TODO
                        """
                        if other_lang:
                            if 'en' in other_lang:
                                value += str(_('English'))
                            if 'pa' in other_lang:
                                if value:
                                    value += ', '
                                value += str(_('Papiamentu'))
                        """
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


###################################################
# PR2021-09-2 from https://thispointer.com/python-how-to-create-a-zip-archive-from-multiple-files-or-directory/
def create_zipfileNIU(dirName):
    # create a ZipFile object
    zipObj = ZipFile('sample.zip', 'w')
    # Add multiple files to the zip
    zipObj.write('sample_file.csv')
    zipObj.write('test_1.log')
    zipObj.write('test_2.log')
    # close the Zip File
    zipObj.close()

# We can do the same thing with “with open” . It will automatically close the zip file when ZipFile object goes out of scope i.e.
    # Create a ZipFile Object
    with ZipFile('sample2.zip', 'w') as zipObj2:
        # Add multiple files to the zip
        zipObj2.write('sample_file.csv')
        zipObj2.write('test_1.log')
        zipObj2.write('test_2.log')

        # create a ZipFile object
        with ZipFile('sampleDir.zip', 'w') as zipObj:
            # Iterate over all the files in directory
            for folderName, subfolders, filenames in os.walk(dirName):
                for filename in filenames:
                    # create complete filepath of file in directory
                    filePath = os.path.join(folderName, filename)
                    # Add file to zip
                    zipObj.write(filePath, basename(filePath))