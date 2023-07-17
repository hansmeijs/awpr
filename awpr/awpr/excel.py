import json
import os
import tempfile
from django.core.files import File

from django.db import connection

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext_lazy as _
from django.utils import timezone
from django.views.generic import View

from os.path import basename

from accounts import models as acc_mod
from accounts import views as acc_view
from  accounts import permits as acc_prm

from awpr import constants as c
from awpr import functions as af
from awpr import settings as s
from awpr import library as awpr_lib

from schools import models as sch_mod
from subjects import models as subj_mod
from subjects import views as subj_view
from subjects import calc_orderlist as subj_calc

from students import views as stud_view
from students import functions as stud_fnc

import xlsxwriter
from zipfile import ZipFile
import io

import logging
logger = logging.getLogger(__name__)


@method_decorator([login_required], name='dispatch')
class StudsubjDownloadEx1View(View):  # PR2021-01-24 PR2021-08-09 PR2023-02-21

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= StudsubjDownloadEx1View ============= ')

    # - function creates, Ex1 xlsx file based on settings in usersetting
        response = None

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

    # - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

    # - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

            if logging_on:
                logger.debug('    sel_examyear: ' + str(sel_examyear))
                logger.debug('    sel_school: ' + str(sel_school))
                logger.debug('    sel_department: ' + str(sel_department))
                logger.debug('    sel_level: ' + str(sel_level))
            if sel_examyear and sel_school and sel_department:

    # - get text from examyearsetting
                settings = awpr_lib.get_library(sel_examyear, ['exform', 'ex1'])

    # +++ create ex1_xlsx
                save_to_disk = False
                # just to prevent PyCharm warning on published_instance=published_instance
                # published_instance = None  # sch_mod.School.objects.get_or_none(pk=None)
                response, is_saved_to_disk = create_ex1_xlsx(
                    published_instance=None,
                    examyear=sel_examyear,
                    sel_school=sel_school,
                    sel_department=sel_department,
                    sel_level=sel_level,
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
            logger.debug(' ')
            logger.debug(' ============= StudsubjDownloadEx4View ============= ')
        # function creates, Ex1 xlsx file based on settings in usersetting

        response = None

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

    # - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

    # - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

    # - get saved_examperiod from Usersetting, default EXAMPERIOD_FIRST if not found
            selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
            sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
            if sel_examperiod not in (c.EXAMPERIOD_SECOND, c.EXAMPERIOD_THIRD):
                sel_examperiod = c.EXAMPERIOD_SECOND

            if sel_examyear and sel_school and sel_department:

                prefix = 'reex3_' if sel_examperiod == 3 else 'reex_' if sel_examperiod == 2 else 'subj_'

# +++ create ex4_xlsx
                save_to_disk = False
                # just to prevent PyCharm warning on published_instance=published_instance
                published_instance = sch_mod.School.objects.get_or_none(pk=None)
                response, is_saved_to_disk = create_ex4_xlsx(
                    published_instance=published_instance,
                    examyear=sel_examyear,
                    sel_school=sel_school,
                    sel_department=sel_department,
                    sel_level=sel_level,
                    examperiod=sel_examperiod,
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
def create_ex1_xlsx(published_instance, examyear, sel_school, sel_department, sel_level,
                    examperiod, prefix, settings, save_to_disk, request, user_lang):
    # PR2021-02-13 PR2021-08-14 PR2022-12-30 PR2023-02-21
    # called by StudentsubjectApproveOrSubmitEx1Ex4View.create_ex1_ex4_form, StudsubjDownloadEx1View
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex1_xlsx -----')

# +++ get mapped_subject_rows    '
    # function gets all subjects of studsubj of this dep, not deleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]
    subject_row_count, subject_pk_list, subject_code_list = \
        create_ex1_Ex4_mapped_subject_rows(examyear, examperiod, sel_school, sel_department)

    if logging_on:
        logger.debug('    subject_row_count: ' + str(subject_row_count))
        logger.debug('    subject_pk_list: ' + str(subject_pk_list))
        logger.debug('    subject_code_list: ' + str(subject_code_list))

# +++ get dict of students with list of studsubj_pk, grouped by level_pk, with totals
    ex1_rows_dict = create_ex1_ex4_rows_dict(
        examyear=examyear,
        sel_school=sel_school,
        sel_department=sel_department,
        sel_level=sel_level,
        save_to_disk=save_to_disk,
        examperiod=examperiod,
        prefix=prefix,
        published_instance=published_instance
    )

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

    """

    response = None
    is_saved_to_disk = False
    if settings and ex1_rows_dict:

        examyear_str = str(examyear.code)

        file_path = None
        if published_instance:

# ---  create file_path
            # PR2021-07-28 changed to file_dir = 'published/'
            # this one gives path: awpmedia / awpmedia / media / private / published
            # PR2021-08-06 create different folders for country and examyear
            # this one gives path: awpmedia / awpmedia / media / private / cur / 2022 / published
            # published_instance is None when downloading preliminary Ex1 form

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
        depbase_code = sel_department.base.code if sel_department else '-'
        if sel_department and sel_department.level_req and sel_level:
            depbase_code += ' ' + sel_level.base.code
        title = ' '.join(('Ex1', str(examyear), sel_school.base.code, depbase_code, today_dte.isoformat()))
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
        ex1_formats = create_ex1_ex4_format_dict(book, sheet, sel_school, sel_department, subject_pk_list, subject_code_list)
        field_width = ex1_formats.get('field_width')
        bold_format = ex1_formats.get('bold_format')
        bold_blue = ex1_formats.get('bold_blue')
        normal_blue = ex1_formats.get('normal_blue')
        th_merge_bold = ex1_formats.get('th_merge_bold')
        th_prelim = ex1_formats.get('th_prelim')
        row_align_center_black = ex1_formats['row_align_center_black']
        row_align_center_blue = ex1_formats['row_align_center_blue']
        row_align_center_red = ex1_formats['row_align_center_red']
        row_align_left_red = ex1_formats['row_align_left_red']
        totalrow_merge = ex1_formats.get('totalrow_merge')
        col_count = len(ex1_formats['field_width'])
        first_subject_column = ex1_formats.get('first_subject_column', 0)

        if logging_on:
            logger.debug('  ex1_formats: ' + str(ex1_formats))

# --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

# --- title row
        # was: sheet.write(0, 0, str(_('Report')) + ':', bold)
        sheet.write(0, 0, settings['minond'], bold_format)
        sheet.write(1, 0, settings['title'], bold_format)

        lb_rgl01_key = 'lex_lb_rgl01' if sel_school.islexschool else 'eex_lb_rgl01'
        lb_rgl02_key = 'lex_lb_rgl02' if sel_school.islexschool else 'eex_lb_rgl02'
        sheet.write(2, 0, settings[lb_rgl01_key], bold_format)
        sheet.write(3, 0, settings[lb_rgl02_key], bold_format)

        sheet.write(5, 0, settings['submit_before'], bold_format)
        lb_ex_key = 'lex' if sel_school.islexschool else 'eex'
        lb_ex_key_str = ' '.join((settings[lb_ex_key], sel_department.abbrev, settings['in_examyear'], examyear_str))

        sheet.write(6, 0, lb_ex_key_str, bold_format)
        lb_school_key = 'school' if sel_school.islexschool else 'school'
        sheet.write(7, 0, settings[lb_school_key], bold_format)
        sheet.write(7, 2, sel_school.name, bold_blue)

# - put Ex1 in right upper corner
        #  merge_range(first_row, first_col, last_row, last_col, data[, cell_format])
        sheet.merge_range(0, col_count - 5, 1, col_count - 1, 'EX.1', th_merge_bold)

        row_index = 9
        if not save_to_disk:
            prelim_txt = 'VOORLOPIG Ex1 FORMULIER'
            sheet.merge_range(row_index, 0, row_index, col_count - 1, prelim_txt, th_prelim)
            row_index += 1

        # if has_published_ex1_rows(examyear, sel_school, sel_department):
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
                if lvl_name:
                    sheet.merge_range(row_index, 0, row_index, col_count - 1, lvl_name, th_prelim)
                    row_index += 1

                for i, field_caption in enumerate(ex1_formats['field_captions']):
                    sheet.write(row_index, i, field_caption, ex1_formats['header_formats'][i])

                if len(stud_list):
                    for row in stud_list:
                        stud_tobedel = row.get('tobedel', False)

                        subj_id_arr = row.get('subj', [])
                        subj_id_publ_arr = row.get('subj_publ', [])
                        subj_id_del_arr = row.get('subj_del', [])
                        subj_id_chang_arr = row.get('subj_chang', [])

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

                                if field_name in subj_id_arr:
                                    if field_name in subj_id_del_arr:
                                        # tobedeleted studsubjects
                                        value = 'X'
                                        exc_format = row_align_center_red
                                    elif field_name in subj_id_chang_arr:
                                        # tobechanged studsubjects
                                        value = u"\u2B58" # large outlined circle
                                        exc_format = row_align_center_blue
                                    elif field_name in subj_id_publ_arr:
                                        # unchanged studsubjects
                                        value = u"\u2B24" # large solid circle
                                        exc_format = row_align_center_black
                                    else:
                                        # new studsubjects
                                        value = u"\u2B24" # large solid circle
                                        exc_format = row_align_center_blue

                            else:
                                value = row.get(field_name, '')
                                if stud_tobedel:
                                    if field_name == 'name':
                                        exc_format = row_align_left_red
                                    else:
                                        exc_format = row_align_center_red

                            sheet.write(row_index, i, value, exc_format)

        # ---  level subtotal row
                # skip subtotal row in Havo/vwo,
                if sel_department.level_req:
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
        if sel_department.level_req:
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
                        if logging_on:
                            logger.debug('    field_name: ' + str(field_name), ' ' + str(type(field_name)))
                        value = total_dict[field_name]
                sheet.write(row_index, i, value, ex1_formats['totalrow_formats'][i])
                # was: sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')

# ---  table footer row
        row_index += 1
        for i, field_name in enumerate(ex1_formats['field_names']):
            if i == 0:
                sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', totalrow_merge)
            else:
                sheet.write(row_index, i, ex1_formats['field_captions'][i], ex1_formats['header_formats'][i])

# ---  extrafacilities row:
        if ex1_rows_dict.get('extrafacilities'):
            row_index += 1
            sheet.write(row_index, 0, '*', ex1_formats.get('footer_size11_aligncenter_black'))
            sheet.write(row_index, 1, settings.get('extrafacilities'), ex1_formats.get('footer_align_left_black'))

# ---  has_subj_new:
        row_index += 1
        # large solid circle
        sheet.write(row_index, 0, u"\u2B24", ex1_formats.get('footer_align_center_blue'))
        sheet.write(row_index, 1, settings.get('bullet_new'), ex1_formats.get('footer_align_left_black'))
# ---  has_subj_chang:
        if ex1_rows_dict.get('has_subj_chang'):
            row_index += 1
            # large outlined circle
            sheet.write(row_index, 0, u"\u2B58", ex1_formats.get('footer_align_center_blue'))
            sheet.write(row_index, 1, settings.get('bullet_changed'), ex1_formats.get('footer_align_left_black'))
# ---  has_subj_publ:
        if ex1_rows_dict.get('has_subj_publ'):
            row_index += 1
            # large solid circle
            sheet.write(row_index, 0, u"\u2B24", ex1_formats.get('footer_align_center_black'))
            sheet.write(row_index, 1, settings.get('bullet_submitted'), ex1_formats.get('footer_align_left_black'))
# ---  has_subj_tobedel:
        if ex1_rows_dict.get('has_subj_tobedel'):
            row_index += 1
            sheet.write(row_index, 0, "X", ex1_formats.get('footer_size11_aligncenter_red'))
            sheet.write(row_index, 1, settings.get('bullet_deleted'), ex1_formats.get('footer_align_left_black'))

# ---  footnote row
        row_index += 2
        first_footnote_row = row_index
        for i in range(1, 9):
            if sel_school.islexschool and 'lex_footnote0' + str(i) in settings:
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
        sheet.write(auth_row, first_subject_column + 4, str(sel_school.examyear.country.name),
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
            is_saved_to_disk = True

            # file_path: media/private/published/Ex2A CUR13 ATC Vsbo SE-tv1 cav 2021-04-29 10u11.pdf
            # stored in dir:

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
    return response, is_saved_to_disk


# --- end of create_ex1_xlsx


#//////////////////////////////////////////////////////////////////////////////////////////////////////////////
def create_ex4_xlsx(published_instance, examyear, sel_school, sel_department, sel_level,
                    examperiod, prefix, save_to_disk, request, user_lang):
    # PR2021-02-13 PR2021-08-14 PR2023-05-07
    # called by StudentsubjectApproveOrSubmitEx1Ex4View and StudsubjDownloadEx4View
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex4_xlsx -----')

# +++ get mapped_subject_rows    '
    # function gets all subjects of studsubj of this dep, not deleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]
    subject_row_count, subject_pk_list, subject_code_list = \
        create_ex1_Ex4_mapped_subject_rows(examyear, examperiod, sel_school, sel_department)

    if logging_on:
        logger.debug('    subject_row_count: ' + str(subject_row_count))
        logger.debug('     subject_pk_list:  ' + str(subject_pk_list))
        logger.debug('    subject_code_list: ' + str(subject_code_list))
        logger.debug('    published_instance: ' + str(published_instance))

# +++ get dict of students with list of studsubj_pk, grouped by level_pk, with totals
    ex4_rows_dict = create_ex1_ex4_rows_dict(
        examyear=examyear,
        sel_school=sel_school,
        sel_department=sel_department,
        sel_level=sel_level,
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
   
         ex4_dict: ep 3 
        {'total': {224: 1}, 
        'auth1': [70], 
        'auth2': [703], 
        'extrafacilities': False, 
        12: {'lvl_name': 'Theoretisch Kadergerichte Leerweg', 
            'total': {224: 1}, 
            'stud_list': [{'idnr': '2006.11.21.02', 'exnr': '06', 'name': 'Rosa, Marlies Alexandra', 'tobedel': False, 'lvl': 'TKL', 'sct': 'ec', 'cls': '1y4 AC', 
                    'subj': [224], 'reex_publ': []}]}}
   
    """

    response = None
    is_saved_to_disk = False
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
                logger.debug('    file_dir: ' + str(file_dir))
                logger.debug('    file_name: ' + str(file_name))
                logger.debug('    filepath: ' + str(file_path))

# ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
        title = ' '.join( ('Ex4', str(examyear), sel_school.base.code, today_dte.isoformat() ) )
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
        ex4_formats = create_ex1_ex4_format_dict(book, sheet, sel_school, sel_department, subject_pk_list, subject_code_list)
        field_width = ex4_formats.get('field_width')
        bold_format = ex4_formats.get('bold_format')
        bold_blue = ex4_formats.get('bold_blue')
        normal_blue = ex4_formats.get('normal_blue')
        th_merge_bold = ex4_formats.get('th_merge_bold')
        th_merge_normal = ex4_formats.get('th_merge_normal')
        th_exists = ex4_formats.get('th_exists')
        row_align_center_blue = ex4_formats['row_align_center_blue']
        row_align_center_black = ex4_formats['row_align_center_black']
        th_prelim = ex4_formats.get('th_prelim')
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

        key_str = 'ex4_lex_article' if sel_school.islexschool else 'ex4_eex_article'
        sheet.write(2, 0, settings[key_str], bold_format)

        sheet.write(3, 0, settings['ex4_tevens_lijst'], bold_format)

        key_str = 'ex4_lex_submit' if sel_school.islexschool else 'ex4_eex_submit'
        sheet.write(4, 0, settings[key_str], bold_format)

        lb_ex_key = 'lex' if sel_school.islexschool else 'eex'
        lb_ex_key_str = ' '.join((  settings[lb_ex_key], sel_department.abbrev, settings['in_examyear'], examyear_str))

        sheet.write(6, 0, lb_ex_key_str, bold_format)
        lb_school_key = 'school' if sel_school.islexschool else 'school'
        sheet.write(7, 0, settings[lb_school_key], bold_format)
        sheet.write(7, 2, sel_school.name, bold_blue)

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

        #if has_published_ex1_rows(examyear, sel_school, sel_department):
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
                if lvl_name:
                    sheet.merge_range(row_index, 0, row_index, col_count - 1, lvl_name, th_prelim)
                    row_index += 1

                for i, field_caption in enumerate(ex4_formats['field_captions']):
                     sheet.write(row_index, i, field_caption, ex4_formats['header_formats'][i])


# +----  iterate through stud_list
                if len(stud_list):

                    for row in stud_list:

                        subj_id_list = row.get('subj')
                        reex_publ_list = row.get('reex_publ')
                        if logging_on:
                            logger.debug('    subj_id_list: ' + str(subj_id_list))
                            logger.debug('    reex_publ_list: ' + str(reex_publ_list))

                        if logging_on:
                            logger.debug('    row: ' + str(row))
                        """
                        row: {'idnr': '2006.11.21.02', 'exnr': '06', 'name': 'Rosa, Marlies Alexandra', 
                        'tobedel': False, 'lvl': 'TKL', 'sct': 'ec', 'cls': '1y4 AC', 'subj': [224], 'reex_publ': []}

                        """
# ---  iterate through fields of student row
                        # row: {'idnr': '2004101103', 'exnr': '21024', 'name': 'Balentien, Rayviendall',
                        #          'lvl': 'PBL', 'sct': 'tech', 'class': '4BH',
                        #          'subj': [1047, 1048, 1049, 1050, 1051, 1052, 1055, 1056, 1060, 1070]}
                        row_index += 1
                        for i, field_name in enumerate(ex4_formats['field_names']):
                            if logging_on:
                                logger.debug('    field_name: ' + str(field_name))

                            exc_format = ex4_formats['row_formats'][i]
                            value = ''
                            if isinstance(field_name, int):
                                # in subject column 'field_name' is subject_id
                                if subj_id_list and field_name in subj_id_list:
                                    #value = 'x'
                                    value = u"\u2B24"  # large solid circle

                                    # PR2023-05-06  reex_publ_list contains list of subject_id's of newly submitted reex
                                    # PR2023-05-06 put newly published reex / reex03 subjects in array, to show them blue in Ex4 form
                                    # published_id is NULL in prelim Ex4, has value published_pk_str in submitted Ex4

                                    if logging_on:
                                        logger.debug('    field_name in reex_publ_list: ' + str(field_name in reex_publ_list))

                                    if reex_publ_list and field_name in reex_publ_list:
                                        exc_format = row_align_center_black
                                    else:
                                        exc_format = row_align_center_blue

                            else:
                                value = row.get(field_name, '')

                            sheet.write(row_index, i, value, exc_format)

# ---  level subtotal row
                # skip subtotal row in Havo/vwo,
                if sel_department.level_req:
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
        if sel_department.level_req:
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
                        value = total_dict[field_name]
                sheet.write(row_index, i, value, ex4_formats['totalrow_formats'][i])
                # was: sheet.write_formula(A1, '=SUBTOTAL(3;H11:H19)')

# ---  table footer row
        row_index += 1
        for i, field_name in enumerate(ex4_formats['field_names']):
            if i == 0:
                sheet.merge_range(row_index, 0, row_index, first_subject_column - 1, '', totalrow_merge)
            else:
                sheet.write(row_index, i, ex4_formats['field_captions'][i], ex4_formats['header_formats'][i])

# ---  extrafacilities row:
        if ex4_rows_dict.get('extrafacilities'):
            row_index += 1
            sheet.write(row_index, 0, '*', ex4_formats.get('footer_size11_aligncenter_black'))
            sheet.write(row_index, 1, settings.get('extrafacilities'),
                        ex4_formats.get('footer_align_left_black'))

# ---  has_subj_new:
        row_index += 1
        # large solid circle, blue
        sheet.write(row_index, 0, u"\u2B24", ex4_formats.get('footer_align_center_blue'))
        sheet.write(row_index, 1, settings.get('bullet_reex_new'), ex4_formats.get('footer_align_left_black'))

# ---  has_reex_publ:
        if ex4_rows_dict.get('has_reex_publ'):
            row_index += 1
            # large solid circle, black
            sheet.write(row_index, 0, u"\u2B24", ex4_formats.get('footer_align_center_black'))
            sheet.write(row_index, 1, settings.get('bullet_reex_submitted'), ex4_formats.get('footer_align_left_black'))

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
            if sel_school.islexschool and 'lex_footnote0' + str(i) in settings:
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
        sheet.write(auth_row, first_subject_column + 4, str(sel_school.examyear.country.name),
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
            is_saved_to_disk = True

            # file_path: media/private/published/Ex2A CUR13 ATC Vsbo SE-tv1 cav 2021-04-29 10u11.pdf

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
    return response, is_saved_to_disk
# --- end of create_ex4_xlsx


def create_ex1_ex4_format_dict(book, sheet, sel_school, sel_department, subject_pk_list, subject_code_list): # PR2021-08-10
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex1_ex4_format_dict -----')
        logger.debug('    subject_pk_list: ' + str(subject_pk_list))

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
    row_align_center_black = book.add_format({'font_size': 8, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter','border': True})
    row_align_center_blue = book.add_format({'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter','border': True})

    # for deleted subjects in Ex1
    #row_align_center_red = book.add_format({'font_size': 8, 'font_color': 'red', 'align': 'center', 'valign': 'vcenter','border': True})
    #row_align_left_red = book.add_format({'font_size': 8, 'font_color': 'red', 'align': 'left', 'valign': 'vcenter','border': True})
    row_align_center_red = book.add_format(c.XF_ROW_ALIGN_CENTER_RED)
    row_align_left_red = book.add_format(c.XF_ROW_ALIGN_LEFT_RED)

    totalrow_align_center = book.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'border': True})
    totalrow_number = book.add_format({'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'border': True})
    totalrow_merge = book.add_format({'font_size': 8, 'border': True, 'align': 'right', 'valign': 'vcenter'})

    # get number of columns
    # columns are (0: 'examnumber', 1: idnumber, 2: name 3: 'class' 4: level "
    # columns 5 thru 19 are subject columns. Extend number when more than 15 subjects

    # for footer Ex1 form

    footer_size11_aligncenter_black = book.add_format(c.XF_FOOTER_SIZE11_ALIGNCENTER_BLACK)
    footer_align_center_black = book.add_format(c.XF_FOOTER_SIZE08_ALIGNCENTER_BLACK)
    footer_align_left_black = book.add_format(c.XF_FOOTER_SIZE11_ALIGNLEFT_BLACK)
    footer_align_center_blue = book.add_format(c.XF_FOOTER_SIZE08_ALIGNCENTER_BLUE)
    footer_align_left_blue = book.add_format(c.XF_FOOTER_SIZE11_ALIGNLEFT_BLUE)
    footer_size11_aligncenter_red = book.add_format(c.XF_FOOTER_SIZE11_ALIGNCENTER_RED)

    is_lexschool = sel_school.islexschool
    level_req = sel_department.level_req
    sector_req = sel_department.sector_req
    has_profiel = sel_department.has_profiel

# - add standard columns: exnr, idnumber and fullname
    col_count = 3
    field_width = [10, 12, 35]

    ex1_formats = {'field_names': ['exnr', 'idnr', 'name'],
                   'field_captions': ['Examen-\nnummer', 'ID-nummer', 'Naam en voorletters van de kandidaat\n(in alfabetische volgorde)'],
                    'header_formats': [th_align_center, th_align_center, th_align_center],
                    'row_formats': [row_align_center_blue, row_align_center_blue, row_align_left],
                    'totalrow_formats': [totalrow_merge, totalrow_align_center, totalrow_align_center],
                    'bold_format': bold_format,
                   'bold_blue': bold_blue,
                   'normal_blue': normal_blue,

                   'row_align_center_black': row_align_center_black,
                   'row_align_center_blue': row_align_center_blue,
                   'row_align_center_red': row_align_center_red,
                   'row_align_left_red': row_align_left_red,

                   'footer_align_center_black': footer_align_center_black,
                   'footer_size11_aligncenter_black': footer_size11_aligncenter_black,
                   'footer_align_left_black': footer_align_left_black,
                   'footer_align_center_blue': footer_align_center_blue,
                   'footer_align_left_blue': footer_align_left_blue,
                   'footer_size11_aligncenter_red': footer_size11_aligncenter_red,

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
        ex1_formats['row_formats'].append(row_align_center_blue)
        ex1_formats['totalrow_formats'].append(totalrow_align_center)

# - add column 'Learning_path' if level_req
    if level_req:  # add column if level_req
        col_count += 1
        field_width.append(5)
        ex1_formats['field_names'].append('lvl')
        ex1_formats['field_captions'].append('Leer-\nweg')
        ex1_formats['header_formats'].append(th_align_center)
        ex1_formats['row_formats'].append(row_align_center_blue)
        ex1_formats['totalrow_formats'].append(totalrow_align_center)

# - add column 'Profiel' or 'Sector' if sector_req (is always the case)
    if sector_req:
        col_count += 1
        field_width.append(7)
        caption = 'Profiel' if has_profiel else 'Sector'
        ex1_formats['field_names'].append('sct')
        ex1_formats['field_captions'].append(caption)
        ex1_formats['header_formats'].append(th_align_center)
        ex1_formats['row_formats'].append(row_align_center_blue)
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
        ex1_formats['row_formats'].append(row_align_center_blue)
        ex1_formats['totalrow_formats'].append(totalrow_number)

        if logging_on:
            logger.debug(' ----- create_ex1_ex4_format_dict -----')
            logger.debug(' >> subject_pk: ' + str(subject_pk))
            logger.debug(' >> ex1_formats[field_names]: ' + str(ex1_formats['field_names']))


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
            ex1_formats['row_formats'].append(row_align_center_blue)
            ex1_formats['totalrow_formats'].append(totalrow_number)

    ex1_formats['first_subject_column'] = first_subject_column
    ex1_formats['field_width'] = field_width

    return ex1_formats
# - end of create_ex1_ex4_format_dict


def create_ex1_ex4_rows_dict(examyear, sel_school, sel_department, sel_level,
                             save_to_disk, examperiod, prefix, published_instance):
    # PR2021-08-15 PR2022-12-15 PR2022-12-30 PR2023-02-21 PR2023-05-06
    # this function is only called by create_ex1_xlsx and create_ex4_xlsx
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_ex1_ex4_rows_dict -----')
        logger.debug('     examperiod: ' + str(examperiod))
        logger.debug('     sel_school: ' + str(sel_school))
        logger.debug('     sel_department: ' + str(sel_department))
        logger.debug('     sel_level: ' + str(sel_level))
        logger.debug('     prefix: ' + str(prefix))

    # function creates dictlist of all students of this examyear, sel_school and sel_department
    #  key 'subj_id_arr' contains list of all studentsubjects of this student, not deleted
    #  skip studsubjects that are not fully approved
    level_req = sel_department.level_req

# students without subjects must only be shown in preliminary Ex1 form
    include_students_without_subjects = not save_to_disk and examperiod == 1
    inner_or_left_join_studsubj = "LEFT JOIN" if include_students_without_subjects else "INNER JOIN"

# PR2021-08-10 dont include null in  ARRAY_AGG
# from https://stackoverflow.com/questions/13122912/how-to-exclude-null-values-in-array-agg-like-in-string-agg-using-postgres

    # don't filter on published or approved subject when printing preliminary Ex1 (in that case save_to_disk = False)

    # PR2022-12-29 new approach submitting Ex1 form:
    # - exclude subjects that are deleted
    # - include previously submitted subjects (color them black)
    # - include newly submitted subjects (color them blue, bold)
    # - include tobedeleted subjects (color them red)
    # - include tobechanged subjects (color them green)
    # - include tobedeleted students (color the student name etc red)

    # filter on sel_level, if it has value

    # when submitting Ex4 form:
    # filter on has_reex or has_reex03
    # - don't exclude studsubj that are reex published
    # - exclude studsubj that are not fully reex_approved
    # - exclude deleted studsubj
    # - include tobedeleted in Ex form

    published_pk_str = ''.join(('=', str(published_instance.pk), '::INT')) if published_instance else 'IS NULL'

    sql_keys = {'ey_id': examyear.pk, 'sch_id': sel_school.pk, 'dep_id': sel_department.pk}

    sql_studsubj_agg_list = [
        "SELECT studsubj.student_id,",
        "ARRAY_AGG(si.subject_id) AS subj_id_arr,"]
    if examperiod == 1:
        sql_studsubj_agg_list.extend((
            "ARRAY_AGG(si.subject_id) FILTER (WHERE studsubj.subj_published_id IS NOT NULL) AS subj_id_arr_publ,",
            "ARRAY_AGG(si.subject_id) FILTER (WHERE studsubj.tobedeleted) AS subj_id_arr_del,",
            "ARRAY_AGG(si.subject_id) FILTER (WHERE studsubj.tobechanged) AS subj_id_arr_chang,"
        ))

    # PR2023-05-06 put newly published reex / ereex03 subjects in array, to show them blue in Ex4 form
    # published_id is NULL in prelim Ex4, has value published_pk_str in submitted Ex4
    elif examperiod in (2, 3):
        # prefix = 'reex3_' if examperiod == 3 else 'reex_' if examperiod == 2 else 'subj_'

        # PR2023-07-12 debug: this code is not correct, I think. It filters on published_instance.pk
        # use instead filter like in ep1
        # was: sql_studsubj_agg_list.append( ''.join(("ARRAY_AGG(si.subject_id) FILTER (WHERE studsubj.", prefix , "published_id ", published_pk_str, ") AS reex_publ_arr,")))

        sql_studsubj_agg_list.append(''.join(("ARRAY_AGG(si.subject_id) FILTER (WHERE studsubj.", prefix, "published_id IS NOT NULL) AS reex_publ_arr,")))

    sql_studsubj_agg_list.extend((
        "ARRAY_AGG(DISTINCT studsubj." + prefix + "auth1by_id) FILTER (WHERE studsubj." + prefix + "auth1by_id IS NOT NULL) AS auth1_arr,",
        "ARRAY_AGG(DISTINCT studsubj." + prefix + "auth2by_id) FILTER (WHERE studsubj." + prefix + "auth2by_id IS NOT NULL) AS auth2_arr",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "WHERE NOT studsubj.deleted"
    ))

    if examperiod in (2, 3):
        field = 'has_reex03' if examperiod == 3 else 'has_reex'
        sql_studsubj_agg_list.append("AND studsubj." + field)

    if save_to_disk and examperiod == 1:
        # when submitting an Ex1 form published_instance is already saved, therefore published_instance.pk has a value
        # studsubj.subj_published_id also has a value: the id of the new published_instance
        # filter on published_instance.pk, so only subjects of this submit will be added to Ex1 form
        # was: sql_studsubj_agg_list.append("AND studsubj.subj_published_id = %(published_id)s::INT")
        pass
        # was: sql_studsubj_agg_list.append("AND studsubj." + prefix + "published_id = %(published_id)s::INT")

    sql_studsubj_agg_list.append("GROUP BY studsubj.student_id")

    sql_studsubj_agg = ' '.join(sql_studsubj_agg_list)

    if logging_on and False:
        logger.debug('sql_studsubj_agg: ' + str(sql_studsubj_agg))
        with connection.cursor() as testcursor:
            testcursor.execute(sql_studsubj_agg, sql_keys)
            rows = af.dictfetchall(testcursor)
            for row in rows:
                logger.debug('row: ' + str(row))

    sql_list = ["WITH studsubj AS (" , sql_studsubj_agg, ")",
        "SELECT st.id, st.idnumber, st.examnumber, st.lastname, st.firstname, st.prefix,",
        "st.classname, st.extrafacilities, st.tobedeleted,",
        "st.level_id, lvl.name AS lvl_name, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev,"]

    if examperiod == 1:
        sql_list.append(
            "studsubj.subj_id_arr, studsubj.subj_id_arr_publ, studsubj.subj_id_arr_del, studsubj.subj_id_arr_chang,"
        )
    elif examperiod in (2, 3):
        # reex_publ_arr contains reex3_published_id when ep = 3
        sql_list.append("studsubj.subj_id_arr, studsubj.reex_publ_arr,")

    sql_list.extend((
        "studsubj.auth1_arr, studsubj.auth2_arr",
        "FROM students_student AS st",
        inner_or_left_join_studsubj, "studsubj ON (studsubj.student_id = st.id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
        "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
        "AND NOT st.deleted"
    ))

    if level_req and sel_level:
        sql_list.append(''.join(("AND st.level_id=", str(sel_level.pk), "::INT")))

    if level_req:
        sql_list.append("ORDER BY LOWER(lvl.abbrev), LOWER(st.lastname), LOWER(st.firstname)")
    else:
        sql_list.append("ORDER BY LOWER(st.lastname), LOWER(st.firstname)")
    sql = ' '.join(sql_list)

    if logging_on and False:
        for sql_txt in sql_list:
            logger.debug(' > ' + str(sql_txt))

    ex1_ex4_rows_dict = {'total': {}, 'auth1': [], 'auth2': [], 'extrafacilities': False}
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
            """
            row: {'id': 5228, 'idnumber': '2007012902', 'examnumber': '001', 
                'lastname': 'Boekhoudt', 'firstname': 'Jeziël S', 'prefix': None, 'classname': '4', 
                'extrafacilities': False, 
                'tobedeleted': True, 
                'level_id': 4, 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 'lvl_abbrev': 'TKL', 
                'sct_abbrev': 'ec', 
                'subj_id_arr': [135, 114, 124, 155, 118, 121, 115, 133, 113], 
                'subj_id_arr_publ': None,
                 'subj_id_arr_del': [135, 114, 124, 155, 118, 121, 115, 133, 113], 
                 'subj_id_arr_chang': None, 
                 'auth1_arr': None, 
                 'auth2_arr': None}
            """

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

    # add dots to idnumber, if last 2 digits are not numeric: dont print letters, pprint '00' instead
            idnumber_withdots_no_char = stud_fnc.convert_idnumber_withdots_no_char(row.get('idnumber'))

            extrafacilities = row.get('extrafacilities', False)
            if extrafacilities:
                ex1_ex4_rows_dict['extrafacilities'] = True

            if examperiod == 1:
                if row.get('subj_id_arr_publ') and 'has_subj_publ' not in ex1_ex4_rows_dict:
                    ex1_ex4_rows_dict['has_subj_publ'] = True

                if row.get('subj_id_arr_del') and 'has_subj_tobedel' not in ex1_ex4_rows_dict:
                    ex1_ex4_rows_dict['has_subj_tobedel'] = True

                if row.get('subj_id_arr_chang') and 'has_subj_chang' not in ex1_ex4_rows_dict:
                    ex1_ex4_rows_dict['has_subj_chang'] = True

            elif examperiod in (2, 3):
                if row.get('reex_publ_arr') and 'has_reex_publ' not in ex1_ex4_rows_dict:
                    ex1_ex4_rows_dict['has_reex_publ'] = True

            fullname = stud_fnc.get_full_name(
                last_name=row.get('lastname', ''),
                first_name=row.get('firstname', ''),
                prefix=row.get('prefix'),
                has_extrafacilities=extrafacilities,
            )

            subj_id_arr = row.get('subj_id_arr') or []
            subj_id_arr_del = row.get('subj_id_arr_del') or []
            student_dict = {'idnr': idnumber_withdots_no_char,
                            'exnr': row.get('examnumber' , '---'),
                            'name': fullname,
                            'tobedel': row.get('tobedeleted', False),
                            'lvl': row.get('lvl_abbrev', '---'),
                            'sct': row.get('sct_abbrev', '---'),
                            'cls': row.get('classname', ''),
                            'subj': subj_id_arr
                            }

            if examperiod == 1:
                student_dict['subj_publ'] = row.get('subj_id_arr_publ') or []
                student_dict['subj_del'] = subj_id_arr_del
                student_dict['subj_chang'] = row.get('subj_id_arr_chang') or []
            elif examperiod in (2, 3):
                student_dict['reex_publ'] = row.get('reex_publ_arr') or []

            level_studlist.append(student_dict)

            if logging_on:
                logger.debug('     student_dict: ' + str(student_dict))
            """
            student_dict: {'idnr': '2007.01.29.02', 'exnr': '001', 'name': 'Boekhoudt, Jeziël S', 
                            'tobedel': True, 'lvl': 'TKL', 'sct': 'ec', 'class': '4', 
                            'subj': [135, 114, 124, 155, 118, 121, 115, 133, 113], 
                            'subj_publ': [], 
                            'subj_del': [135, 114, 124, 155, 118, 121, 115, 133, 113], 
                            'subj_chang': []
            }
            """
            # only count non-deleted rows
            if subj_id_arr:
                for subject_pk in subj_id_arr:
                    if subject_pk not in subj_id_arr_del:
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
 
    ex1_ex4_rows_dict: {
        'total': {224: 1}, 
        'auth1': [70], 
        'auth2': [703], 
        'extrafacilities': False, 
        12: {
            'lvl_name': 'Theoretisch Kadergerichte Leerweg', 
            'total': {224: 1}, 
            'stud_list': [
                {'idnr': '2006.11.21.02', 'exnr': '06', 'name': 'Rosa, Marlies Alexandra', 'tobedel': False, 
                'lvl': 'TKL', 'sct': 'ec', 'cls': '1y4 AC', 'subj': [224], 'reex_publ': []}]}}

 
    """
    return ex1_ex4_rows_dict
# --- end of create_ex1_ex4_rows_dict


def create_ex1_Ex4_mapped_subject_rows(examyear, examperiod, sel_school, sel_department):
    # PR2021-08-08 PR2023-02-21 PR2023-07-11
    # function gets all subjects of studsubj of this dep, not deleted
    # - creates list of subject_codes and list of subject_pk's
    # - both sorted by subjbase.code
    # subject_code_list: ['adm&co', 'bi', 'cav', ..., 'sp', 'stg', 'sws', 'wk', 'zwi']
    # subject_pk_list: [1067, 1057, 1051, ..., 1054, 1070, 1069, 1055, 1065]

    subject_code_list = []
    subject_pk_list = []

    is_reex_clause = "AND studsubj.has_reex03" if examperiod == 3 else \
        "AND studsubj.has_reex" if examperiod == 2 else \
            ""

    sql_list = [
        "SELECT subj.id, subjbase.code",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
        "AND NOT st.deleted AND NOT studsubj.deleted",
        is_reex_clause,
        "GROUP BY subj.id, subjbase.code",
        "ORDER BY LOWER(subjbase.code)"
    ]
    sql = ' '.join(sql_list)

    sql_keys = {'ey_id': examyear.pk, 'sch_id': sel_school.pk, 'dep_id': sel_department.pk}

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
            logger.debug(' ')
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
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if sel_examyear and sel_school and sel_department:
                    # - get text from examyearsetting
                    library = awpr_lib.get_library(sel_examyear, ['exform', 'ex2'])

    # - may submit Ex2 per level
                    # - get selected levelbase from usersetting
                    #sel_lvlbase_pk, sel_level = None, None
                    #selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                    #if selected_pk_dict:
                    #    sel_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)
                    #if sel_lvlbase_pk:
                    #    sel_level = subj_mod.Level.objects.get_or_none(
                    #        base_id=sel_lvlbase_pk,
                    #        examyear=sel_examyear
                    #    )
                    if logging_on:
                        logger.debug('     sel_level: ' + str(sel_level))

    # +++ create Ex2_xlsx
                    save_to_disk = False
                    # just to prevent PyCharm warning on published_instance=published_instance
                    published_instance = sch_mod.School.objects.get_or_none(pk=None)

                    response, saved_to_disk = create_ex2_ex2a_xlsx(
                        published_instance=published_instance,
                        examyear=sel_examyear,
                        school=sel_school,
                        department=sel_department,
                        level=sel_level,
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
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

    # - get selected examperiod
                sel_examperiod, sel_lvlbase_pk, sel_level = None, None, None
                selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                if selected_pk_dict:
                    sel_examperiod = selected_pk_dict.get(c.KEY_SEL_EXAMPERIOD)
                    sel_lvlbase_pk = selected_pk_dict.get(c.KEY_SEL_LVLBASE_PK)

        # - may submit Ex2 per level
                sel_level = None
                if sel_lvlbase_pk:
                    sel_level = subj_mod.Level.objects.get_or_none(
                        base_id=sel_lvlbase_pk,
                        examyear=sel_examyear
                    )
                if logging_on:
                    logger.debug('     sel_examperiod: ' + str(sel_examperiod))
                    logger.debug('     sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
                    logger.debug('     sel_level: ' + str(sel_level))

                if sel_examyear and sel_school and sel_department and sel_examperiod in (1, 2, 3):
    # - get text from examyearsetting
                    library = awpr_lib.get_library(sel_examyear, ['exform', 'ex2', 'ex2a'])

# +++ create ex2_ex2a_xlsx
                    save_to_disk = False
                    # just to prevent PyCharm warning on published_instance=published_instance
                    published_instance = sch_mod.School.objects.get_or_none(pk=None)
                    response, saved_to_disk = create_ex2_ex2a_xlsx(
                        published_instance=published_instance,
                        examyear=sel_examyear,
                        school=sel_school,
                        department=sel_department,
                        level=sel_level,
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
        logging_on = False  # s.LOGGING_ON
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
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if sel_examyear and sel_school and sel_department:

    # +++ create Ex5_xlsx
                    save_to_disk = False
                    # just to prevent PyCharm warning on published_instance=published_instance
                    published_instance = sch_mod.School.objects.get_or_none(pk=None)
                    saved_is_ok, response = create_ex5_xlsx(
                        published_instance=published_instance,
                        examyear=sel_examyear,
                        school=sel_school,
                        department=sel_department,
                        level=sel_level,
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


@method_decorator([login_required], name='dispatch')
class GradeDownloadResultOverviewView(View):  # PR2022-06-01

    def get(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= GradeDownloadResultOverviewView ============= ')

        response = None
        if True:
        #try:
            if request.user and request.user.country and request.user.schoolbase:
                req_user = request.user

    # - reset language
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

    # - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if sel_examyear and sel_school and sel_department:

    # --- get department dictlist
                    # fields are: depbase_id, depbase_code, dep_name, dep_level_req
                    department_dictlist = subj_view.create_department_dictlist(sel_examyear)

                    # --- get level_dictlist
                    level_dictlist = subj_view.create_level_dictlist(sel_examyear)

                    # +++ get subjectbase dictlist
                    # functions creates ordered dictlist of all subjectbase pk and code of this exam year of all countries
                    subjectbase_dictlist = subj_view.create_subjectbase_dictlist(sel_examyear)

                    # +++ get schoolbase dictlist
                    # functions creates ordered dictlist of all schoolbase_pk, schoolbase_code and school_name of this exam year of all countries
                    schoolbase_dictlist = subj_view.create_schoolbase_dictlist(sel_examyear, request)

                    """
                    schoolbase_dictlist: [
                        {'sbase_id': 2, 'sbase_code': 'CUR01', 'sch_name': 'Ancilla Domini Vsbo'}, 
                        {'sbase_id': 37, 'sbase_code': 'SXM03', 'sch_name': 'Sundial School'}
                        {'sbase_id': 23, 'sbase_code': 'CURETE', 'sch_article': 'het', 'sch_name': 'Expertisecentrum voor Toetsen & Examens', 'sch_abbrev': 'ETE'},
                        {'sbase_id': 39, 'sbase_code': 'SXMDOE', 'sch_article': 'de', 'sch_name': 'Division of Examinations', 'sch_abbrev': 'Division of Examinations'}] 
                        ]
                    """

                    # +++ get nested dicts of results per school, dep, level

                    result_dict_per_school, error_dict = stud_view.create_result_dict_per_school(
                        request=request,
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_school.base
                    )

    # +++ create result_overview_xlsx
                    response = create_result_overview_xlsx(
                        sel_examyear=sel_examyear,
                        sel_school=sel_school,
                        department_dictlist=department_dictlist,
                        level_dictlist=level_dictlist,
                        schoolbase_dictlist=schoolbase_dictlist,
                        result_dict_per_school=result_dict_per_school,
                        user_lang=user_lang
                    )
        #except:
        #   raise Http400("Error creating file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of GradeDownloadResultOverviewView


def create_ex2_ex2a_xlsx(published_instance, examyear, school, department, level, examperiod, library, is_ex2a, save_to_disk, request, user_lang):
    # PR2022-02-17 PR2022-06-01
    # called by GradeDownloadEx2View
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
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
    ex2_rows_dict, grades_auth_dict = create_ex2_ex2a_rows_dict(examyear, school, department, level, examperiod, is_ex2a, save_to_disk, published_instance)
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
                'exemptions': {229: {'se': '-', 'ce': '-', 'final': '-'}, 259: {'se': '-', 'ce': '-', 'final': '-'}, 247: {'se': '6,4', 'ce': '-', 'final': '6'}, 224: {'se': '-', 'ce': '-', 'final': '-'}}}, 
    
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
    saved_to_disk = False

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

# ---  create file Name and worksheet Name
        exform_name = 'Ex2A' if is_ex2a else 'Ex2'
        today_dte = af.get_today_dateobj()
        title_list = [exform_name, str(examyear), school.base.code]
        if department:
            title_list.append(department.base.code)
        if level:
            title_list.append(level.base.code)
        today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
        title_list.append(today_dte.isoformat())

        file_name = ''.join((' '.join(title_list), ".xlsx"))

        if logging_on:
            logger.debug('    file_name: ' + str(file_name))

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


# when Ex2, also print sheet with exemptions PR2023-02-05
        sheet_list = [0] if is_ex2a else [0, 1]


# +++++++++++++++++++++++++
# +++ print Ex2 page / Exemptions page
        for sheet_index in sheet_list:

            sheet_name = 'Ex2A' if is_ex2a else 'Vrijstellingen' if sheet_index else 'Ex2'
            sheet = book.add_worksheet(sheet_name)

    # --- create format of Ex2 sheet
            ex2_formats = create_ex2_format_dict(book, sheet, sheet_index, school, department, subject_pk_list, subject_code_list)
            field_width = ex2_formats.get('field_width')
            bold_format = ex2_formats.get('bold_format')
            bold_blue = ex2_formats.get('bold_blue')
            normal_blue = ex2_formats.get('normal_blue')

            row_align_center_black = ex2_formats.get('row_align_center_black')
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
                title_str = library['ex2_title_exem'] if sheet_index else library['ex2_title']
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
                    # add 'Vrijstellingen to sheet Vrijstellingen
                    if sheet_index:
                        sheet.write(row_index, 0, 'VRIJSTELLINGEN', bold_format)
                        row_index += 1

                    if lvl_name:
                        sheet.write(row_index, 0, lvl_name, bold_format)
                        row_index += 2
                    students_dict = level_dict.get('students')

    # ---  write table header
                    for i, field_caption in enumerate(ex2_formats['field_captions']):
                        sheet.write(row_index, i, field_caption, ex2_formats['header_formats'][i])

                    if logging_on and False:
                        logger.debug('  students_dict: ' + str(students_dict))
# ---  student rows
                    for key, stud_dict in students_dict.items():
                        """
                        key: 7960
                        stud_dict: {'idnr': '2006091312', 'exnr': '0024', 'cls': '4b', 'lvl': 'TKL', 'sct': 'tech', 'name': 'da Costa Gomez, Jay-C Leandro Vishnu', 'grades': {223: 'vr', 229: 'x', 264: 'x', 222: 'x', 235: 'x', 234: 'x', 247: 'x', 252: 'x', 224: 'x'}, 
                                    'exemptions': {223: '7,6-7,7>8', 224: 'x'}, 
                                    'has_exemptions': True}
                        stud_dict: {'idnr': '2007101110', 'exnr': '003', 'cls': '4', 'lvl': 'TKL', 'sct': 'ec', 'name': 'da Costa Gomez, Jaydah Alejandra Ashni', 'grades': {224: 'x', 247: 'x', 223: 'x', 225: 'x', 264: 'x', 259: 'x', 222: 'x', 229: 'x', 239: 'x'}, 
                                    'exemptions': {}} 
                        stud_dict: {'idnr': '2005052070', 'exnr': '313', 'cls': 'TieP4', 'lvl': 'PKL', 'sct': 'tech', 'stud_tobedel': False, 'name': "Dennis, O'Brian Romario", 
                                    'grades': {301: '4,8', 288: '6,4', 276: '5,2', 305: '6,8', 320: 'x', 310: '7,0', 280: '5,9', 278: '7,0', 303: '8,2', 283: '4,2'}, 
                                    'new': [301, 288, 276, 305, 320, 310, 280, 278, 303, 283], 
                                    'exemptions': {305: 'x', 320: 'x', 310: 'x', 278: 'x'}},        
                                       
                        """

        # skip in exemption sheet when students has no exemptions
                        exemptions_dict = stud_dict.get('exemptions')
                        if logging_on and False:
                            logger.debug('  key: ' + str(key))
                            logger.debug('  stud_dict: ' + str(stud_dict))

                        if not sheet_index or exemptions_dict:
                            grades_dict = exemptions_dict if sheet_index else stud_dict.get('grades')
                            new_submitted_studsubj_pk_list = stud_dict.get('new') or []
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

                                    if not new_submitted_studsubj_pk_list or field_name not in new_submitted_studsubj_pk_list:
                                        exc_format = row_align_center_black
                                    else:
                                        if value == 'x':
                                            exc_format = row_align_center_red
                                        elif value == 'vr':
                                            exc_format = row_align_center_green

                                else:
                                    value = stud_dict.get(field_name, '')

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

# --- create format of Ex2 sheet
        sheet_index = 0
        ex2_formats = create_ex2_format_dict(book, sheet, sheet_index, school, department, subject_pk_list,
                                             subject_code_list)
        bold_format = ex2_formats.get('bold_format')
        bold_blue = ex2_formats.get('bold_blue')

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
            saved_to_disk = True
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
    return response, saved_to_disk
# --- end of create_ex2_xlsx


def create_ex2_format_dict(book, sheet, sheet_index, school, department, subject_pk_list, subject_code_list):  # PR2021-08-10
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

    row_align_left = book.add_format(c.XF_ROW_ALIGN_LEFT_BLUE)
    row_align_center = book.add_format(c.XF_ROW_ALIGN_CENTER_BLUE)

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
                   'row_align_center_black':  book.add_format(c.XF_ROW_ALIGN_CENTER_BLACK),
                   'row_align_center_red': book.add_format(c.XF_ROW_ALIGN_CENTER_RED),
                   'row_align_left_red': book.add_format(c.XF_ROW_ALIGN_LEFT_RED),
                   'row_align_center_green': book.add_format(c.XF_ROW_ALIGN_CENTER_GREEN),
                   'row_align_left_green': book.add_format(c.XF_ROW_ALIGN_LEFT_GREEN),
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

    # - add column 'Learning_path' if level_req
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
    subject_col_width = 5.89 if sheet_index else 2.86
    for x in range(0, colcount_subjects):  # range(start_value, end_value, step), end_value is not included!
        field_width.append(subject_col_width)
        subject_pk = subject_pk_list[x]
        subject_code = subject_code_list[x] if subject_code_list[x] else ''
        ex2_formats['field_captions'].append(subject_code)
        ex2_formats['field_names'].append(subject_pk)
        ex2_formats['header_formats'].append(th_align_center if sheet_index else th_rotate)
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
            ex2_formats['header_formats'].append(th_align_center if sheet_index else th_rotate)
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

                   'row_align_center_red': row_align_center_red,

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
        ex5_formats['field_names'].append('class')
        ex5_formats['field_captions'].append('Klas')
        ex5_formats['header_formats'].append(th_rotate)
        ex5_formats['row_formats'].append(row_align_center)
        ex5_formats['totalrow_formats'].append(totalrow_align_center)

    # - add column 'Learning_path' if level_req
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
    ex5_formats['field_captions'].append('Gemiddelde van de eindcijfers\nvoor de examenvakken')
    ex5_formats['header_formats'].append(th_rotate)
    ex5_formats['row_formats'].append(row_align_center)
    ex5_formats['totalrow_formats'].append(totalrow_align_center)

    field_width.append(4)
    ex5_formats['field_names'].append('subjects_count')
    ex5_formats['field_captions'].append('Gemiddelde van de cijfers voor het Centraal Examen')
    ex5_formats['header_formats'].append(th_rotate)
    ex5_formats['row_formats'].append(row_align_center)
    ex5_formats['totalrow_formats'].append(totalrow_align_center)

# Uitslag van het examen
    """
    field_width.append(4)
    ex5_formats['field_names'].append('subjects_count')
    ex5_formats['field_captions'].append('@@@ Uitslag van het examen')
    ex5_formats['header_formats'].append(th_rotate)
    ex5_formats['row_formats'].append(row_align_center)
    ex5_formats['totalrow_formats'].append(totalrow_align_center)
    """

    ex5_formats['field_width'] = field_width

    return ex5_formats
# - end of create_ex5_format_dict


def create_ex2_ex2a_rows_dict(examyear, school, department, level, examperiod, is_ex2a, save_to_disk, published_instance):
    # PR2022-02-17 PR2022-03-09
    # this function is only called by create_ex2_xlsx
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- create_ex2_ex2a_rows_dict -----')
        logger.debug('    published_instance.pk: ' + str(published_instance.pk if published_instance else None))
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

    # PR2022-04-13 add exemption grades if subject has exemption
    sql_exem_list = ["SELECT grd.studentsubject_id AS exem_studsubj_id, ",
                     "grd.segrade AS exem_segrade, grd.cegrade AS exem_cegrade, grd.finalgrade AS exem_finalgrade",
                "FROM students_grade AS grd",
                "WHERE grd.examperiod = 4 AND NOT grd.tobedeleted AND NOT grd.deleted"]
    sql_grd_exem = ' '.join(sql_exem_list)

    sql_list = ["WITH grd_exem AS (" + sql_grd_exem + ") ",

                "SELECT st.id AS student_id, st.idnumber, st.examnumber, st.lastname, st.firstname, st.prefix, st.classname, ",
                "st.level_id, lvl.name AS lvl_name, lvl.abbrev AS lvl_abbrev, sct.abbrev AS sct_abbrev, ",
                "si.subject_id, cluster.name AS clustername, ",

                "grd.", grade_score, " AS grade_score, grd.", se_ce, "_auth1by_id AS auth1by_id, grd.", se_ce, "_auth2by_id AS auth2by_id, ",
                "grd.", se_ce, "_auth3by_id AS auth3by_id, grd.", se_ce, "_auth4by_id AS auth4by_id, ",

                "grd.", se_ce, "_published_id AS published_id, ",

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
                "AND grd.examperiod = %(ep)s::INT "
                "AND NOT st.deleted AND NOT studsubj.deleted AND NOT grd.deleted ",
                "AND NOT st.tobedeleted AND NOT studsubj.tobedeleted AND NOT grd.tobedeleted "
                ]

    # PR2023-05-02 show all grades on Ex2, make them black when already published, blue are new grades
    #if save_to_disk:
        # when submitting an Ex2 form published_instance is already saved, therefore published_instance.pk has a value
        # filter on published_instance.pk, so only subjects of this submit will ne added to Ex2 form
        # was: sql_studsubj_agg_list.append("AND studsubj.subj_published_id = %(published_id)s::INT")

        #sql_keys['published_id'] = published_pk
        #sql_list.append("AND grd." + se_ce + "_published_id = %(published_id)s::INT ")

    if level:
        sql_keys['lvl_id'] = level.pk
        sql_list.append("AND lvl.id = %(lvl_id)s::INT ")

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
                'stud_tobedel': row.get('stud_tobedel', False),
                'name': fullname,
                'grades': {},
                'new_dict': {},
                'new': [],
                'exemptions': {}
            }
        level_student_grades_dict = level_students[student_pk].get('grades')
        # new_dict stores grades that are not submitted yet, must be shown in blue on Ex from PR2023-05-02
        level_student_new_list = level_students[student_pk].get('new')
        level_student_exemptions_dict = level_students[student_pk].get('exemptions')

        subject_pk = row.get('subject_id')
        if subject_pk:

            if subject_pk not in level_student_grades_dict:
                grade_score = row.get('grade_score')
                has_exemption = row.get('has_exemption', False)
                exem_finalgrade = row.get('exem_finalgrade') if has_exemption else None

                published_id = row.get('published_id')

                if grade_score is not None and not grade_score == '':
                    grade_score_comma = str(grade_score).replace('.', ',')
                elif has_exemption and exem_finalgrade:
                    grade_score_comma = 'vr'
                else:
                    grade_score_comma = 'x'

                level_student_grades_dict[subject_pk] = grade_score_comma

                # new_dict stores grades that are not submitted yet, must be shown in blue on Ex from PR2023-05-02
                if published_id is None or published_pk and published_id == published_pk:
                    level_student_new_list.append(subject_pk)

                if has_exemption:
                    #level_students['has_exemptions'] = True

                    if exem_finalgrade:
                        exem_segrade = row.get('exem_segrade')
                        exem_cegrade = row.get('exem_cegrade')

                        exem_segrade_comma = str(exem_segrade).replace('.', ',') if exem_segrade else '-'
                        exem_cegrade_comma = str(exem_cegrade).replace('.', ',') if exem_cegrade else '-'
                        exem_finalgrade_comma = str(exem_finalgrade).replace('.', ',') if exem_finalgrade else 'X'
                        if exem_cegrade:
                            exem_str = ''.join((exem_segrade_comma, '-', exem_cegrade_comma, '>', exem_finalgrade_comma))
                        else:
                            # PR2023-02-20 was: exem_str = exem_finalgrade_comma
                            exem_str = ''.join((exem_segrade_comma, '>', exem_finalgrade_comma))
                    else:
                        exem_str = 'x'
                    level_student_exemptions_dict[subject_pk] = exem_str

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
                'exemptions': {229: {'se': '-', 'ce': '-', 'final': '-'}, 259: {'se': '-', 'ce': '-', 'final': '-'}, 247: {'se': '6,4', 'ce': '-', 'final': '6'}, 224: {'se': '-', 'ce': '-', 'final': '-'}}}, 

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
    if logging_on:
        logger.debug('    ex2_rows_dict: ' + str(ex2_rows_dict))

    return ex2_rows_dict, grades_auth_dict
# --- end of create_ex2_ex2a_rows_dict

#@@@@@@@@@@@@@@@@@@@@@@@

def create_ex5_rows_dict(examyear, school, department, level, examperiod, save_to_disk, published_instance):
    # PR2022-02-17 PR2022-03-09
    # this function is only called by create_ex2_xlsx
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' @@@@@@@@@@@@@@@------------ create_ex5_rows_dict -----------------')
    # function creates dictlist of all students of this examyear, school and department
    #  key 'subj_id_arr' contains list of all studentsubjects of this student, not tobedeleted
    #  skip studsubjects that are not fully approved

    # PR2021-08-10 dont include null in ARRAY_AGG
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
                     "ARRAY_AGG(grd.finalgrade) AS f,",

                    "ARRAY_AGG(grd.se_auth1by_id) AS auth1_se,",
                    "ARRAY_AGG(grd.se_auth2by_id) AS auth2_se,",
                    "ARRAY_AGG(grd.ce_auth1by_id) AS auth1_ce,",
                    "ARRAY_AGG(grd.ce_auth2by_id) AS auth2_ce",

                     "FROM students_grade AS grd",

                     "WHERE NOT grd.tobedeleted AND NOT grd.deleted",
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

                "subj.id AS subj_id, subjbase.code AS subj_code, grd_arr.e, grd_arr.s, grd_arr.c, grd_arr.f,",
                "grd_arr.auth1_se, grd_arr.auth2_se, grd_arr.auth1_ce, grd_arr.auth2_ce,",

                "studsubj.has_exemption AS exemp, studsubj.has_sr AS sr, studsubj.has_reex AS re, studsubj.has_reex03 AS re3,",
                "studsubj.gradelist_sesrgrade AS gls, studsubj.gradelist_pecegrade AS glc,",
                "studsubj.gradelist_finalgrade AS glf, studsubj.gradelist_use_exem AS usex",

                "FROM students_studentsubject AS studsubj",
                "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "INNER JOIN grd_arr ON (grd_arr.studsubj_id = studsubj.id)",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
                "WHERE st.school_id = %(sch_id)s::INT AND st.department_id = %(dep_id)s::INT",
                "AND NOT st.deleted AND NOT st.tobedeleted",
                "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted"
                ]

    if save_to_disk:
        # when submitting an Ex2 form published_instance is already saved, therefore published_instance.pk has a value
        # filter on published_instance.pk, so only subjects of this submit will be added to Ex2 form
        # was: sql_studsubj_agg_list.append("AND studsubj.subj_published_id = %(published_id)s::INT")

        sql_keys['published_id'] = published_pk
        #sql_list.append("AND grd." + se_ce + "_published_id = %(published_id)s::INT ")

    level_req = department.level_req
    if level_req and level:
        sql_list.extend(("AND lvl.base_id = ", str(level.base_id) , "::INT "))

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
    auth1_list, auth2_list = [], []

    if logging_on:
        logger.debug('==========================')

    for row in rows:
        if logging_on:
            logger.debug('>>>>>>>>>>> row: ' + str(row))
        for key_str in ('auth1_se', 'auth2_se','auth1_ce','auth2_ce'):
            auth_arr = row.get(key_str)
            if auth_arr:
                for auth in auth_arr:
                    auth_list = auth1_list if key_str in ('auth1_se', 'auth1_ce') else auth2_list
                    if auth not in auth_list:
                        auth_list.append(auth)

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

    # add dots to idnumber, if last 2 digits are not numeric: dont print letters, pprint '00' instead
            idnumber_withdots_no_char = stud_fnc.convert_idnumber_withdots_no_char(row.get('idnr'))

            level_students[student_pk] = {
                'stud': {
                    'idnr': idnumber_withdots_no_char,
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
                            subj_code = row.get('subj_code')
                            examperiod_dict[subject_pk] = {'subj': subj_code, 's': s_arr[i], 'c': c_arr[i], 'f': f_arr[i] }
                            # was:   \  if s_arr[i] or c_arr[i] or f_arr[i] else {}

    if auth1_list:
        ex5_rows_dict['auth1'] = auth1_list

    if auth2_list:
        ex5_rows_dict['auth2'] = auth2_list

    if logging_on:
        logger.debug('     ex5_rows_dict: ' + str(ex5_rows_dict))
        logger.debug('     auth1_list: ' + str(auth1_list))
        logger.debug('     auth2_list: ' + str(auth2_list))

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
        "SELECT subj.id, subjbase.code, subj.name_nl",

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


def count_number_reex_for_ex5(school, department):
    # PR2022-06-12
    # function count number of reex, to detremine how many reex column Ex5 must contain
    # value is always 1 or higher, to show at least 1 set of reex subject columns

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ============= count_number_reex_for_ex5 ============= ')

    max_number_of_reex = 1

    sql_keys = {'sch_id': school.pk, 'dep_id': department.pk}

    sql_list = ["WITH sub_sql AS (",
                    "SELECT COUNT(*)",
                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                    "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                    "WHERE stud.school_id = %(sch_id)s::INT AND stud.department_id = %(dep_id)s::INT",
                    "AND grd.examperiod =", str(c.EXAMPERIOD_SECOND),
                    "AND NOT stud.deleted AND NOT stud.tobedeleted",
                    "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted",
                    "GROUP BY stud.id",
                ")",
                "SELECT MAX(count) FROM sub_sql",
                ]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = cursor.fetchall()
        if rows:
            first_row = rows[0]
            if first_row and first_row[0]:
                max_number_of_reex = first_row[0]
    if logging_on:
        logger.debug('max_number_of_reex: ' + str(max_number_of_reex))

    if not max_number_of_reex:
        max_number_of_reex = 1

    return max_number_of_reex
# --- end of count_number_reex_for_ex5


def create_ex5_xlsx(published_instance, examyear, school, department, level, examperiod,
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

    max_number_of_reex = count_number_reex_for_ex5(school, department)

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
    ex5_rows_dict = create_ex5_rows_dict(examyear, school, department, level, examperiod, save_to_disk, published_instance)

    if logging_on and False:
        logger.debug('ex5_rows_dict: ' + str(ex5_rows_dict))

    saved_is_ok = False
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
        bold_format = book.add_format(c.XF_BOLD)
        bold_blue = book.add_format(c.XF_BOLD_FCBLUE)
        normal_blue = book.add_format(c.XF_FCBLUE)

        row_align_center = book.add_format(c.XF_ROW_ALIGN_CENTER_BLUE)
        row_align_center_green = book.add_format(c.XF_ROW_ALIGN_CENTER_GREEN)
        row_align_left_green = book.add_format(c.XF_ROW_ALIGN_LEFT_GREEN)
        th_align_center = ex5_formats.get('th_align_center')
        th_rotate = ex5_formats.get('th_rotate')

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
            #prelim_txt = f'VOORLOPIG {exform_name} FORMULIER'
            prelim_txt = 'VOORLOPIG %(cpt)s FORMULIER' % {'cpt': exform_name}
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
                row_index, max_col_index = write_ex5_table_header(book, sheet, max_number_of_reex, row_index, ex5_formats, library, th_align_center, th_rotate)
                row_index += 2

# ---  student rows
                for student_pk, student_dict in students_dict.items():
                    row_index = write_ex5_table_row(
                        examyear=examyear,
                        sheet=sheet,
                        max_number_of_reex=max_number_of_reex,
                        row_index=row_index,
                        student_pk=student_pk,
                        student_dict=student_dict,
                        ex5_formats=ex5_formats,
                        formatindex_first_subject=formatindex_first_subject,
                        formatindex_number_subjects=formatindex_number_subjects,
                        row_align_center=row_align_center,
                        row_align_center_green=row_align_center_green,
                        row_align_left_green=row_align_left_green
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
        sheet.write(auth_row, 1, str(_('Digitally signed by')) + ':')
        auth_row += 2

# - Chairperson
        sheet.write(auth_row, 1, str(_('Chairperson')) + ':')
        auth1_list = ex5_rows_dict.get('auth1')
        if auth1_list:
            for auth1_pk in auth1_list:
                auth1 = acc_mod.User.objects.get_or_none(pk=auth1_pk)
                if auth1:
                    sheet.write(auth_row, 2, auth1.last_name, normal_blue)
                    auth_row += 1
        else:
            auth_row += 1
        auth_row += 1
# - Secretary
        sheet.write(auth_row, 1, str(_('Secretary')) + ':')
        auth2_list = ex5_rows_dict.get('auth2')
        if auth2_list:
            for auth2_pk in auth2_list:
                auth2 = acc_mod.User.objects.get_or_none(pk=auth2_pk)
                if auth2:
                    sheet.write(auth_row, 2, auth2.last_name, normal_blue)
                    auth_row += 1
        else:
            auth_row += 1

        auth_row += 1

# -  place, date
        sheet.write(auth_row, 1, 'Plaats:')
        sheet.write(auth_row, 2, str(school.examyear.country.name), normal_blue)

        auth_row += 1

        sheet.write(auth_row, 1, 'Datum:')
        sheet.write(auth_row, 2, today_formatted, normal_blue)

        book.close()

# +++ save file to disk
        if save_to_disk:
            excel_file = File(temp_file)

            published_instance.file.save(file_path, excel_file)

            # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
            published_instance.save(request=request)

            saved_is_ok = True

            if logging_on:
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
    return saved_is_ok, response
# --- end of create_ex5_xlsx


def write_ex5_table_header(book, sheet, max_number_of_reex, row_index, ex5_formats, library, th_align_center, th_rotate):
    # format_index counts 1 for each subject.
    # col_index adds 3 columns per subject, is therefore different from format_index

    def add_colnr_and_increase_index(col_index):
        # add column number row, increase col_index
        sheet.write(row_index + 2, col_index, str(col_index + 1), th_align_center)
        if logging_on:
            logger.debug('---col_index: ' + str(col_index))
        return col_index + 1

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

    sheet.set_row(row_index + 1, 25)
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

    # format got lost, dont know why
    th_rotate = book.add_format(
        {'font_size': 8, 'border': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'rotation': 90})

# put rest here instead of in  loop through field_captions
    sheet.set_column(col_index, col_index, 5)
    sheet.merge_range(row_index -1, col_index, row_index - 1 , col_index + 2, 'Uitslag van het examen', th_align_center)
    sheet.merge_range(row_index, col_index, row_index + 1, col_index, 'Geslaagd', th_rotate)
    col_index = add_colnr_and_increase_index(col_index)

    sheet.set_column(col_index, col_index, 5)
    sheet.merge_range(row_index, col_index, row_index + 1, col_index, 'Toegelaten tot\neen herexamen', th_rotate)
    col_index = add_colnr_and_increase_index(col_index)

    sheet.set_column(col_index, col_index, 5)
    sheet.merge_range(row_index, col_index, row_index + 1, col_index, 'Afgewezen', th_rotate)
    col_index = add_colnr_and_increase_index(col_index)

    sheet.set_column(col_index, col_index, 4)
    sheet.merge_range(row_index -1, col_index, row_index + 1, col_index, 'pre-examen(p) of\nbis-examen(b)', th_rotate)
    col_index = add_colnr_and_increase_index(col_index)

    if logging_on:
        logger.debug('     max_number_of_reex: ' + str(max_number_of_reex))
# Uitslag na tweede tijdvak
    # show at least 1 subject column set (each set contains 3 columns: 'vak', 'c', 'e')
    max_number_of_reex = max_number_of_reex if max_number_of_reex else 1
    col_count_result_ep2 = 3 * max_number_of_reex + 4

    if logging_on:
        logger.debug('     max_number_of_reex: ' + str(max_number_of_reex))
        logger.debug('     col_count_result_ep2: ' + str(col_count_result_ep2))

    sheet.merge_range(row_index -1, col_index, row_index - 1, col_index + col_count_result_ep2 -1, 'Uitslag na het tweede tijdvak', th_align_center)

# subheader 'Vak' above reex subjects
    sheet.merge_range(row_index, col_index, row_index, col_index + 3 * max_number_of_reex - 1, 'Vak', th_align_center)

# loop through number of reex subjects
    first_reex_colindex = col_index
    subj_col_width = (4.5, 2.86, 2.86)
    for i in range(0, max_number_of_reex):
        # awrite 'Vak', 'c', 'e'  in each set of subject columns
        subj_col_index = first_reex_colindex + i * 3

        for x, caption in enumerate(('Vak', 'c', 'e')):
            sheet.write(row_index + 1, subj_col_index + x, caption, th_align_center)

            sheet.set_column(col_index, col_index, subj_col_width[x])
            col_index = add_colnr_and_increase_index(col_index)

    sheet.set_column(col_index, col_index, 7)
    sheet.merge_range(row_index, col_index, row_index + 1, col_index , 'Gemiddelde van de eindcijfers\nna het herexamen', th_rotate)
    col_index = add_colnr_and_increase_index(col_index)

    sheet.set_column(col_index, col_index, 7)
    sheet.merge_range(row_index, col_index, row_index + 1, col_index , 'Gemiddelde\nvan de CE-cijfers\nna het herexamen', th_rotate)
    col_index = add_colnr_and_increase_index(col_index)

    sheet.set_column(col_index, col_index, 3)
    sheet.merge_range(row_index, col_index, row_index + 1, col_index , 'Geslaagd', th_rotate)
    col_index = add_colnr_and_increase_index(col_index)

    sheet.set_column(col_index, col_index, 3)
    sheet.merge_range(row_index, col_index, row_index + 1, col_index , 'Afgewezen', th_rotate)
    col_index = add_colnr_and_increase_index(col_index)

# Teruggetrokken
    sheet.set_column(col_index, col_index, 5)
    sheet.merge_range(row_index -1, col_index, row_index + 1, col_index, 'Teruggetrokken', th_rotate)
    col_index = add_colnr_and_increase_index(col_index)

# - Registratienummer
        # PR2023-06-21 don't print Registratienummer as of examyear 2023
    #sheet.set_column(col_index, col_index, 15)
    #sheet.merge_range(row_index - 1, col_index, row_index + 1, col_index, 'Registratienummer', th_align_center)
    #col_index = add_colnr_and_increase_index(col_index)

# - Diplomanummer
        # PR2023-06-21 don't print Diplomanummer as of examyear 2023
    #sheet.set_column(col_index, col_index, 11)
    #sheet.merge_range(row_index - 1, col_index, row_index + 1, col_index, 'Diplomanummer', th_rotate)
    #col_index = add_colnr_and_increase_index(col_index)

# - Cijferlijstnummer
        # PR2023-06-21 don't print Cijferlijstnummer as of examyear 2023
    #sheet.set_column(col_index, col_index, 11)
    #sheet.merge_range(row_index - 1, col_index, row_index + 1, col_index, 'Cijferlijstnummer', th_rotate)
    #col_index = add_colnr_and_increase_index(col_index)

# - Opmerkingen
    sheet.set_column(col_index, col_index, 17)
    sheet.merge_range(row_index - 1, col_index, row_index + 1, col_index, 'Opmerkingen\n(bij pre- en bis- examen de dit jaar geexamineerde vakken vermelden)', th_align_center)
    col_index = add_colnr_and_increase_index(col_index)

    return row_index, col_index
# - end of write_ex5_table_header


def write_ex5_table_row(examyear, sheet, max_number_of_reex, row_index, student_pk, student_dict, ex5_formats,
        formatindex_first_subject, formatindex_number_subjects,
                        row_align_center, row_align_center_green, row_align_left_green):

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('------------------- write_ex5_table_row ---------------------')
        logger.debug('student_pk: ' + str(student_pk) + ' ' + str(type(student_pk)))
        logger.debug('student_dict: ' + str(student_dict))

    if isinstance(student_pk, int):
        """
stud_info_dict: {
'idnr': '20030903xx', 'exnr': '201', 'gender': 'M', 'class': '6', 'lvl': None, 'sct': 'e&m', 
'name': 'Baan, Merijn Evert Julian', 'regnr': 'CUR131220201-', 'dipnr': None, 'glnr': None, 'evest': False, 'lexst': False, 'bisst': False, 
'partst': False, 'wdr': False, 
'ep01_ce_avg': '5.3', 'ep01_combi_avg': '8', 'ep01_final_avg': '6.0', 'ep01_result': 2, 
'ep02_ce_avg': '5.5', 'ep02_combi_avg': '8', 'ep02_final_avg': '6.1', 'ep02_result': 2, 
'gl_ce_avg': '5.5', 'gl_combi_avg': '8', 'gl_final_avg': '6.1', 'result': 2}
stubjects_dict: {142: {'gls': '6.2', 'glf': '6'}, 144: {'gls': '5.9', 'glc': '4.7', 'glf': '5'}, 148: {'gls': '9.1', 'glf': '9'}, 149: {'re': True, 'gls': '5.6', 'glc': '4.8', 'glf': '5'}, 155: {'re': True, 'gls': '5.2', 'glc': '6.1', 'glf': '6'}, 167: {'gls': '6.3', 'glc': '6.6', 'glf': '6'}, 165: {'gls': '7.6', 'glc': '5.5', 'glf': '7'}, 158: {'gls': '5.0', 'glc': '4.2', 'glf': '5'}, 140: {'gls': '7.3', 'glc': '6.6', 'glf': '7'}, 145: {'gls': '7.3', 'glc': '5.5', 'glf': '6'}, 118: {'gls': '5.3', 'glc': '3.4', 'glf': '4'}}
ep01_dict: {142: {'subj': 'asw', 's': '6.2', 'c': None, 'f': '6'}, 144: {'subj': 'du', 's': '5.9', 'c': '4.7', 'f': '5'}, 148: {'subj': 'pws', 's': '9.1', 'c': None, 'f': '9'}, 149: {'subj': 'wa', 's': '5.6', 'c': '4.5', 'f': '5'}, 155: {'subj': 'ec', 's': '5.2', 'c': '4.9', 'f': '5'}, 167: {'subj': 'entl', 's': '6.3', 'c': '6.6', 'f': '6'}, 165: {'subj': 'netl', 's': '7.6', 'c': '5.5', 'f': '7'}, 158: {'subj': 'bec', 's': '5.0', 'c': '4.2', 'f': '5'}, 140: {'subj': 'ak', 's': '7.3', 'c': '6.6', 'f': '7'}, 145: {'subj': 'gs', 's': '7.3', 'c': '5.5', 'f': '6'}, 118: {'subj': 'pa', 's': '5.3', 'c': '3.4', 'f': '4'}}
ep02_dict: {149: {'subj': 'wa', 's': '5.6', 'c': '4.8', 'f': '5'}, 155: {'subj': 'ec', 's': '5.2', 'c': '6.1', 'f': '6'}}
    
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
        is_reex_kand = False
        exemp_count = 0

        if logging_on:
            logger.debug('     stud_info_dict: ' + str(stud_info_dict))
            logger.debug('     stubjects_dict: ' + str(stubjects_dict))
            logger.debug('     examperiod_dict: ' + str(examperiod_dict))
            logger.debug('     ep01_dict: ' + str(ep01_dict))
            logger.debug('     ep02_dict: ' + str(ep02_dict))
            logger.debug('     ep03_dict: ' + str(ep03_dict))
            logger.debug('     ep04_dict: ' + str(ep04_dict))

# +++ loop through field_names
        for format_index, field_name in enumerate(ex5_formats['field_names']):
            if logging_on and False:
                logger.debug(str(format_index) + ' field_name: ' + str(field_name) + ' ' + str(type(field_name)))

            row_format = ex5_formats['row_formats'][format_index]

            if format_index < formatindex_first_subject:
                # write student info
                value_str = stud_info_dict.get(field_name) or None
                sheet.write(row_index, col_index, value_str, row_format)
                col_index += 1

            elif format_index < formatindex_number_subjects:
                # field_name contains subject_pk in subject columns
                # subj_dict can be empty, when no exemp, reex or gl garde
                subj_dict = stubjects_dict.get(field_name)
                # stubjects_dict: {152: {'exemp': True, 'usex': True, 'gls': '6.6', 'glf': '7'},

                row_format = ex5_formats['row_formats'][format_index]
                if subj_dict is None:
    # - enter empty cell with border when no subject
                    for x in range(0, 3):
                        sheet.write(row_index, col_index, None, row_format)
                        col_index += 1
                else:
                    has_exemp = subj_dict.get('exemp', False)
                    if has_exemp:
                        exemp_count += 1
                    # row_format = row_align_center_green if has_exemp else row_align_center
                    usex = subj_dict.get('usex', False)
                    # has_sr = subj_dict.get('sr', False)
                    has_reex = subj_dict.get('re', False)
                    if has_reex:
                        is_reex_kand = True
                    has_reex03 = subj_dict.get('re3', False)
                    if has_reex03:
                        is_reex03_kand = True
                    gls = subj_dict.get('gls')
                    glc = subj_dict.get('glc')
                    glf = subj_dict.get('glf')

                    """
                    ep01_dict: {120: {'s': '8.0', 'c': None, 'f': None}, 113: {'s': '5.9', 'c': None, 'f': None}, 114: {'s': '8.0', 'c': None, 'f': None}, 115: {'s': '5.4', 'c': None, 'f': '5'}, 116: {'s': '7.0', 'c': None, 'f': '7'}, 118: {'s': '7.6', 'c': None, 'f': None}, 133: {'s': '6.4', 'c': None, 'f': None}, 136: {'s': 'g', 'c': None, 'f': 'g'}, 155: {'s': '6.1', 'c': None, 'f': None}, 117: {'s': '6.1', 'c': None, 'f': '6'}}

                    """
                    if has_exemp and usex:
                        row_format = row_align_center_green

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

# average final grades
        sheet.write(row_index, col_index, stud_info_dict.get('ep01_final_avg'), row_align_center)
        col_index += 1
# average ce grade
        sheet.write(row_index, col_index, stud_info_dict.get('ep01_ce_avg'), row_align_center)
        col_index += 1
# passed
        ep01_result = stud_info_dict.get('ep01_result') or 0
        sheet.write(row_index, col_index, 'x' if ep01_result == c.RESULT_PASSED else None, row_align_center)
        col_index += 1
# reex
        sheet.write(row_index, col_index, 'x' if is_reex_kand else None, row_align_center)
        col_index += 1
# failed - not  when is_reex_kand
        sheet.write(row_index, col_index, 'x' if ep01_result == c.RESULT_FAILED and not is_reex_kand else None, row_align_center)
        col_index += 1
# bis_exam
        sheet.write(row_index, col_index, 'x' if stud_info_dict.get('bisst') else None, row_align_center)
        col_index += 1

        """
        ep01_dict: {142: {'subj': 'asw', 's': '6.2', 'c': None, 'f': '6'}, 144: {'subj': 'du', 's': '5.9', 'c': None, 'f': None}, 148: {'subj': 'pws', 's': '9.1', 'c': None, 'f': '9'}, 149: {'subj': 'wa', 's': '5.6', 'c': '4.5', 'f': '5'}, 155: {'subj': 'ec', 's': '5.2', 'c': '4.9', 'f': '5'}, 167: {'subj': 'entl', 's': '6.3', 'c': '6.6', 'f': '6'}, 165: {'subj': 'netl', 's': '7.6', 'c': '5.5', 'f': '7'}, 158: {'subj': 'bec', 's': '5.0', 'c': '4.2', 'f': '5'}, 140: {'subj': 'ak', 's': '7.3', 'c': '6.6', 'f': '7'}, 145: {'subj': 'gs', 's': '7.3', 'c': '5.5', 'f': '6'}, 118: {'subj': 'pa', 's': '5.3', 'c': '3.4', 'f': '4'}}
        ep02_dict: {149: {'subj': 'wa', 's': '5.6', 'c': None, 'f': None}, 155: {'subj': 'ec', 's': '5.2', 'c': None, 'f': None}}  
        """
# reexaminations.
    # create sorted list of reex subjects
        subj_code_dict = {}
        subj_code_list = []
        if ep02_dict:
            for subject_pk, subj_dict in ep02_dict.items():
                subj_code = subj_dict.get('subj')
                if subj_code:
                    subj_code_dict[subj_code] = subject_pk
                    subj_code_list.append(subj_code)
            subj_code_list.sort()

        if logging_on:
            logger.debug('     reex subj_code_list: ' + str(subj_code_list))
            logger.debug('     reex max_number_of_reex: ' + str(max_number_of_reex))
# loop through max number of reex subjects
        first_reex_col_index = col_index
        for x in range(0, max_number_of_reex):
            first_subj_col_index = first_reex_col_index + x * 3
            subj_code = None
            c_value = None
            f_value = None
            if x < len(subj_code_list):
                subject_pk = subj_code_dict.get(subj_code_list[x])
                if subject_pk:
                    ep2_subj_dict = ep02_dict.get(subject_pk)
                    if ep2_subj_dict:
                        first_subj_col_index = first_reex_col_index + x * 3
                        subj_code = ep2_subj_dict.get('subj') or '-'
                        c_value = ep2_subj_dict.get('c')
                        f_value = ep2_subj_dict.get('f')
                        if c_value:
                            c_value = c_value.replace('.', ',')

            sheet.write(row_index, first_subj_col_index, subj_code, row_align_center)
            sheet.write(row_index, first_subj_col_index + 1, c_value, row_align_center)
            sheet.write(row_index, first_subj_col_index + 2, f_value, row_align_center)

        col_index += 3 * max_number_of_reex

# average final grades
        sheet.write(row_index, col_index, stud_info_dict.get('ep02_final_avg'), row_align_center)
        col_index += 1
# average ce grade
        sheet.write(row_index, col_index, stud_info_dict.get('ep02_ce_avg'), row_align_center)
        col_index += 1
# passed after reex and reex03
        # use result, not ep02_result. result includdes 3rg exam period
        result = stud_info_dict.get('result') or 0
        sheet.write(row_index, col_index, 'x' if result == c.RESULT_PASSED else None, row_align_center)
        col_index += 1
# failed after reex
        sheet.write(row_index, col_index, 'x' if result == c.RESULT_FAILED else None, row_align_center)
        col_index += 1
# withdrawn
        sheet.write(row_index, col_index, 'x' if stud_info_dict.get('wdr') else None, row_align_center)
        col_index += 1
# Registratienummer
        # PR2023-06-21 don't print regnumber as of examyear 2023, regnumber is genereted when printing dp or gl
        #regnumber = stud_info_dict.get('regnr') if examyear.code < 2023 else ''
        #sheet.write(row_index, col_index, regnumber, row_align_center)
        #col_index += 1
# Diplomanummer
        # PR2023-06-21 don't print Diplomanummer as of examyear 2023
        #dipnr = stud_info_dict.get('dipnr') if examyear.code < 2023 else ''
        #sheet.write(row_index, col_index, dipnr, row_align_center)
        #col_index += 1
# Cijferlijstnummer
        # PR2023-06-21 don't print Cijferlijstnummer as of examyear 2023
        #glnr = stud_info_dict.get('glnr') if examyear.code < 2023 else ''
        #sheet.write(row_index, col_index, glnr, row_align_center)
        #col_index += 1

# Opmerkingen
        sheet.write(row_index, col_index, 'Vrijstelling' if exemp_count else None,
                    row_align_left_green if exemp_count else row_align_center)

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
                acc_view.get_selected_examyear_examperiod_from_usersetting(request)
            # in orderlist sel_examperiod is always first period
            sel_examperiod = c.EXAMPERIOD_FIRST
            if sel_examyear_instance:
                response = create_orderlist_per_school_xlsx(sel_examyear_instance, sel_examperiod, list, user_lang, request)

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

# - get selected examyear from usersettings
            # exams are only ordered (nl: besteld) in first exam period
            sel_examyear_instance, sel_examperiodNIU = \
                acc_view.get_selected_examyear_examperiod_from_usersetting(request)
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

def create_orderlist_per_school_xlsx(sel_examyear_instance, sel_examperiod, list, user_lang, request):  # PR2021-07-07 PR2021-08-20
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_orderlist_per_school_xlsx -----')
        # row: {'school_id': 78, 'schbase_code': 'CUR13', 'school_name': 'Abel Tasman College', 'dep_id': 97, 'depbase_code': 'Vsbo',
        #           'lvl_id': 63, 'lvl_abbrev': 'TKL', 'subj_id': 998, 'subjbase_code': 'ne', 'subj_name': 'Nederlandse taal', '
        #           subj_published_arr': [None], 'lang': 'ne', 'count': 7}

# - get text from examyearsetting
    settings = awpr_lib.get_library(sel_examyear_instance, ['exform', 'ex1'])

# - get depbase dictlist
    department_dictlist = subj_view.create_department_dictlist(sel_examyear_instance)

# - get lvlbase dictlist
    level_dictlist = subj_view.create_level_dictlist(sel_examyear_instance)

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
        schoolbase_pk_list = [schoolbase_pk] if schoolbase_pk else None
        count_dict, receipt_dict = subj_calc.create_studsubj_count_dict(
            sel_examyear_instance=sel_examyear_instance,
            sel_examperiod=sel_examperiod,
            request=request,
            schoolbase_pk_list=schoolbase_pk_list
        )

        total_dict = count_dict.get('total')

        if logging_on:
            logger.debug('...........school_name: ' + str(school_name))
            logger.debug('count_dict: ' + str(count_dict))
            logger.debug('total_dict: ' + str(total_dict))
            """
            count_dict: {
                'total': {0: [0, 0, 0]}, 
                'DUO': {
                    'total': {0: [0, 0, 0]}, 
                    'nl': {
                        'total': {}, 
                        None: {'c': None, 
                                0: {'c': None, 
                                    'total': {0: [0, 0, 0]}, 
                                    'admin_total': {}, 
                                    34: {'c': 'SXMDOE', 
                                         0: [0, 0, 0]}}}}}
                }

                total_dict: {0: [0, 0, 0]}
            """

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
                sheet, count_dict, department_dictlist, level_dictlist,
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

# --- get department_dictlist, filtered by dep.examyear_id, ordered by sequence
    # fields are: depbase_id, depbase_code, dep_name, dep_level_req
    department_dictlist = subj_view.create_department_dictlist(sel_examyear_instance)
    """
    department_dictlist: [
        {'depbase_id': 1, 'depbase_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_level_req': True}, 
        {'depbase_id': 2, 'depbase_code': 'Havo', 'dep_name': 'Hoger Algemeen Voortgezet Onderwijs', 'dep_level_req': False}, 
        {'depbase_id': 3, 'depbase_code': 'Vwo', 'dep_name': 'Voorbereidend Wetenschappelijk Onderwijs', 'dep_level_req': False}]
    """

# --- get lvlbase dictlist, ordered by sequence
    level_dictlist = subj_view.create_level_dictlist(sel_examyear_instance)
    """
    level_dictlist: [
        {'lvlbase_id': 6, 'lvlbase_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg'}, 
        {'lvlbase_id': 5, 'lvlbase_code': 'PKL', 'lvl_name': 'Praktisch Kadergerichte Leerweg'}, 
        {'lvlbase_id': 4, 'lvlbase_code': 'TKL', 'lvl_name': 'Theoretisch Kadergerichte Leerweg'}, 
        {'lvlbase_id': 0, 'lvlbase_code': '', 'lvl_name': ''}]
    """

# +++ get subjectbase dictlist
    # functions creates a dictlist of all subjectbase pk and code of this exam year of all countries, ordered by code
    # NOTE: examyear are filtered by examyear.code (integer field). This way subjects from SXM and CUR are added to list

    subjectbase_dictlist = subj_view.create_subjectbase_dictlist(sel_examyear_instance)
    """
    subjectbase_dictlist: [
        {'id': 133, 'code': 'ac'}, 
        {'id': 140, 'code': 'ak'}, 
        {'id': 166, 'code': 'am'},    
    """

# +++ get schoolbase dictlist
    # functions creates ordered dictlist of all schoolbase_pk, schoolbase_code and school_name
    #  of this exam year of all countries (only SXM when requsr=sxm), ordered by code

    # NOTE: schools are filtered by examyear.code (integer field). This way schools from SXM and CUR are added to list
    # when req_usr = cur: schools of cur and sxm are included
    # when req_usr = sxm: only sxm schools are included
    schoolbase_dictlist = subj_view.create_schoolbase_dictlist(sel_examyear_instance, request)

    #if logging_on:
    #    logger.debug('schoolbase_dictlist: ' + str(schoolbase_dictlist))
    """
    schoolbase_dictlist:  [
        {'sbase_id': 2, 'sbase_code': 'CUR01', 'depbases': '1', 'sch_otherlang': None, 'sch_article': 'de', 'sch_name': 'Ancilla Domini Vsbo', 'sch_abbrev': 'Ancilla Domini', 'defaultrole': 8}, 
        {'sbase_id': 23, 'sbase_code': 'CURETE', 'depbases': '1;2;3', 'sch_otherlang': None, 'sch_article': 'het', 'sch_name': 'Expertisecentrum voor Toetsen & Examens', 'sch_abbrev': 'ETE', 'defaultrole': 64}, 
        {'sbase_id': 30, 'sbase_code': 'SXM01', 'depbases': '1;2;3', 'sch_otherlang': 'en', 'sch_article': 'het', 'sch_name': 'Milton Peters College', 'sch_abbrev': 'MPC', 'defaultrole': 8}, 
        {'sbase_id': 34, 'sbase_code': 'SXMDOE', 'depbases': '1;2;3', 'sch_otherlang': 'en', 'sch_article': 'de', 'sch_name': 'Division of Examinations', 'sch_abbrev': 'Division of Examinations', 'defaultrole': 64}]
    """

# +++ get nested dicts of subjects per school, dep, level, lang, ete_exam
    sel_examperiod = c.EXAMPERIOD_FIRST
    count_dict, receipt_dict = subj_calc.create_studsubj_count_dict(
        sel_examyear_instance=sel_examyear_instance,
        sel_examperiod=sel_examperiod,
        request=request
    )

    if logging_on and False:
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
                    sheet.hide_zero()

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
                            sheet, ete_duo_dict, is_herexamens, department_dictlist, level_dictlist, schoolbase_dictlist,
                            row_index, col_count, first_subject_column, list, title, field_names, field_captions,
                            formats, col_header_formats, detail_row_formats,
                            totalrow_formats)
                    else:
                        write_orderlist_summary(
                            sheet, ete_duo_dict, is_herexamens, department_dictlist, level_dictlist, schoolbase_dictlist,
                            row_index, col_count, first_subject_column, list, title, field_names, field_captions,
                            formats, col_header_formats, detail_row_formats,
                            totalrow_formats
                        )

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


def write_orderlist_summary(sheet, ete_duo_dict, is_herexamens, department_dictlist, level_dictlist, schoolbase_dictlist,
                                 row_index, col_count, first_subject_column, list, title, field_names, field_captions,
                                 formats, col_header_formats, detail_row_formats, totalrow_formats):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- write_orderlist_summary -----')
        logger.debug('ete_duo_dict: ' + str(ete_duo_dict))

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
    write_total_row(sheet, ete_duo_dict, row_index, field_names, first_subject_column,
                    is_herexamens, formats['totalrow_merge'], totalrow_formats)

# +++++++++++++ loop through language  ++++++++++++++++++++++++++++
    for lang in ('nl', 'pa', 'en'):
        if logging_on:
            logger.debug('lang: ' + str(lang))

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
            write_total_row(sheet, lang_dict, row_index, field_names, first_subject_column,
                            is_herexamens, formats['totalrow_merge'], totalrow_formats)

# +++++++++++++++++++++ loop through departent  ++++++++++++++++++++++++++++
            for department_dict in department_dictlist:
                # fields are: depbase_id, depbase_code, dep_name, dep_level_req
                depbase_pk = department_dict.get('depbase_id')
                dep_code = department_dict.get('depbase_code')
                # department_dict: {'depbase_pk': 3, 'name': 'Voorbereidend Wetenschappelijk Onderwijs', 'code': 'Vwo', 'level_req': False}
                if depbase_pk in lang_dict:
                    dep_dict = lang_dict.get(depbase_pk)

        # ++++++++++++ loop through levels  ++++++++++++++++++++++++++++
                    for lvlbase_dict in level_dictlist:
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
                            if logging_on:
                                logger.debug('    level_dict: ' + str(level_dict))

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


def write_orderlist_with_details(sheet, ete_duo_dict, is_herexamens, department_dictlist, level_dictlist, schoolbase_dictlist,
                                 row_index, col_count, first_subject_column, list, title, field_names, field_captions,
                                 formats, col_header_formats, detail_row_formats, totalrow_formats):
    logging_on =  False  # s.LOGGING_ON

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
    for lang in ('nl', 'pa', 'en'):

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
                    for lvlbase_dict in level_dictlist:
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


def write_orderlist_per_school(sheet, count_dict, department_dictlist, level_dictlist,
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
            for lang in ('nl', 'pa', 'en'):
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
                            for lvlbase_dict in level_dictlist:
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
                                    if logging_on:
                                        logger.debug('    level_dict: ' + str(level_dict))

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
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- write_summary_row -----')
        logger.debug('    is_herexamens: ' + str(is_herexamens))
        logger.debug('    field_names: ' + str(field_names))
        logger.debug('    item_dict: ' + str(item_dict))

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
    logging_on = False  # s.LOGGING_ON
    if logging_on :
        logger.debug('item_dict: ' + str(item_dict))
    # PR2022-08-14 debug: error: 'NoneType' object has no attribute 'get', solved by adding if 'total' in item_dict
    if 'total' in item_dict:
        item_dict_total = item_dict.get('total')
        if logging_on :
            logger.debug('item_dict_total: ' + str(item_dict_total))

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
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  write_total_row_with_formula  -----')

    if subtotal_total_row_index:

        totalrow_merge = formats['totalrow_merge']
        border_left_bottom = formats['border_left_bottom']
        border_bottom = formats['border_bottom']

        """
        field_names: ['schoolbase_code', 'school_name', 123, 155, 114, 132, 124, 113, 121, 131, 'rowtotal']
        """

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
                    # PR2022-10-12 debug: gave circular reference error when there are no subjects (then i = 2)
                    # soled by adding if i > 2
                    start_col_index = 1 if i == 2 else 2
                    upper_cell_ref = subj_view.xl_rowcol_to_cell(subtotal_total_row_index, start_col_index)
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


def create_result_overview_row_formats(formats):
    # form https://stackoverflow.com/questions/16819222/how-to-return-dictionary-keys-as-a-list-in-python
    # subject_count = len([*ete_duo_dict_total])
    # ete_duo_dict_total contains a dict with keys = subjectbase_pk and value = count of subjects

    col_count = 22  # schoolbase_code', 1: school_name
    col_width = [
        8, 8, 8, 15,
        4, 4, 4,
        4, 4, 4,
        4, 4, 4,
        4, 4, 4,
        4, 4, 4,
        4, 4, 4
    ]
    field_names = [
        'db_code', 'lvl_code', 'sb_code', 'sch_name',
        'count_m', 'count_v', 'count_t',
        'res_pass_m', 'res_pass_v', 'res_pass_t',
        'res_reex_m', 'res_reex_v', 'res_reex_t',
        'res_fail_m', 'res_fail_v', 'res_fail_t',
        'res_wdr_m', 'res_wdr_v', 'res_wdr_t',
        'res_nores_m', 'res_nores_v', 'res_nores_t'
    ]
    col_count = len(field_names)
    field_captions = [ 'db_code', 'lvl_code', 'sb_code', 'sch_name',
        'count_m', 'count_v', 'count_t',
        'res_pass_m', 'res_pass_v', 'res_pass_t',
        'res_reex_m', 'res_reex_v', 'res_reex_t',
        'res_fail_m', 'res_fail_v', 'res_fail_t',
        'res_wdr_m', 'res_wdr_v', 'res_wdr_t',
        'res_nores_m', 'res_nores_v', 'res_nores_t'
    ]
    col_header_formats = [formats['border_left_bottom'], formats['border_bottom']]
    detail_row_formats = [formats['detailrow_col0'], formats['detailrow_col1']]
    summary_row_formats = [formats['detailrow_col0'], formats['detailrow_col1']]
    totalrow_formats = [formats['totalrow_merge'], formats['totalrow_align_center']]
    first_subject_column = 5

# - loop through subjectbase_dictlist to get the subject code in alphabetic order,
    # add sjbase_pk to field_names, only when subject is in count_dict
    # subjectbase_dictlist: [{'id': 153, 'code': 'adm&co'}, {'id': 162, 'code': 'asw'},

    """
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
    """

    return col_count, first_subject_column, col_width, field_names, field_captions, col_header_formats, detail_row_formats, summary_row_formats, totalrow_formats
# - end of create_row_formats



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



############ DOWNLOAD USER DATA ########################## PR2023-01-31

# +++++++++++ Userdata xlsx ++++++++++++
def create_userdata_xlsx(sel_examyear, req_usr_school, req_usr_role, mapped_depcodes, mapped_lvlcodes, mapped_schoolcodes, mapped_subjectcodes, user_rows, user_lang):  #PR2023-01-31
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_userdata_xlsx -----')

    # from https://stackoverflow.com/questions/16393242/xlsxwriter-object-save-as-http-response-to-create-download-in-django
    # logger.debug('period_dict: ' + str(period_dict))

    response = None

    def write_table_header(sheet, row_index, field_captions, header_format):  # PR2022-05-18
        for col_index, field_caption in enumerate(field_captions):
            sheet.write(row_index, col_index, field_caption, header_format)

    # --- end of write_table_header

    def write_user_rows(sheet, row_index, row, field_names, row_formats, row_formats_strikeout,
                           user_lang):  # PR2022-05-18
        # ---  loop through columns

        for i, field_name in enumerate(field_names):
            if field_name == 'modifiedat':
                modified_dte = row.get(field_name, '')
                value = af.format_modified_at(modified_dte, user_lang)
            elif field_name == 'usergroups':
                function_list = []
                usergroup_list = row.get(field_name) or []
                if usergroup_list:
                    for usergroup in usergroup_list:
                        function = c.USERGROUP_CAPTION.get(usergroup)
                        if function:
                            function_list.append (function)
                value = ', '.join(function_list)

            elif field_name == 'allowed_clusters':
                cluster_list = []
                cluster_arr = row.get(field_name) or []
                if cluster_arr:
                    for cluster in cluster_arr:
                        if cluster:
                            cluster_list.append (cluster)
                value = ', '.join(cluster_list)

            elif field_name =='allowed_sections_dict':

                allowed_sections_dict = row.get(field_name, '')
                mapped_allowed_sections = {}
                if logging_on:
                    logger.debug(' @@@@@@@@@@@   allowed_sections_dict: ' + str(allowed_sections_dict) + ' ' + str(type(allowed_sections_dict)))
                if allowed_sections_dict:
                    for sb_pk, sb_dict in allowed_sections_dict.items():
                        sb_code = mapped_schoolcodes.get(int(sb_pk)) or '-'
                        if logging_on:
                            logger.debug('    sb_pk: ' + str(sb_pk) + ' ' + str(type(sb_pk)))
                            logger.debug('    sb_code: ' + str(sb_code) + ' ' + str(type(sb_code)))
                            logger.debug('    sb_dict: ' + str(sb_dict) + ' ' + str(type(sb_dict)))
                            # sb_dict: {'1': {'-9': []}, '2': {'-9': []}, '3': {'-9': []}} <class 'dict'>
                        mapped_sb_dict = {}
                        if sb_dict:
                            for db_pk, db_dict in sb_dict.items():
                                db_code = mapped_depcodes.get(int(db_pk)) or '-'
                                mapped_db_dict = {}
                                for lb_pk, lb_arr in db_dict.items():
                                    lb_code = mapped_lvlcodes.get(int(lb_pk)) or '-'
                                    mapped_lb_arr = []
                                    for subjb_pk in lb_arr:
                                        subjb_code = mapped_subjectcodes.get(int(subjb_pk)) or '-'
                                        mapped_lb_arr.append(subjb_code)
                                    mapped_lb_arr.sort()
                                    mapped_db_dict[lb_code] = mapped_lb_arr
                                mapped_sb_dict[db_code] = mapped_db_dict

                        mapped_allowed_sections[sb_code] = mapped_sb_dict
                if logging_on:
                    logger.debug(' +++++++++   mapped_allowed_sections: ' + str(mapped_allowed_sections) + ' ' + str(type(mapped_allowed_sections)))

                value = str(mapped_allowed_sections)

            else:
                value = str(row.get(field_name, ''))

            formats = row_formats if row.get('activated', False) else row_formats_strikeout

            sheet.write(row_index, i, value, formats[i])
# --- end of write_user_rows


    if user_rows:

        # ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

        requsr_school_name = ' '.join((req_usr_school.base.code, req_usr_school.name))
        title = ' '.join((str(_('Users')), str(requsr_school_name), str(sel_examyear), 'dd', today_dte.isoformat()))
        file_name = title + ".xlsx"
        worksheet_name = str(_('Users'))

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
        # th_align_center.set_font_strikeout(True)

        th_merge_bold = book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        th_merge_bold.set_left()
        th_merge_bold.set_bottom()

        row_align_left = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter', 'border': True})
        row_align_center = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True})
        row_date_format = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'num_format': 'd mmmm yyyy', 'align': 'left', 'valign': 'vcenter',
             'border': True})

        row_align_left_strikeout = book.add_format(
            {'font_size': 8, 'font_color': 'red', 'valign': 'vcenter', 'border': True, 'font_strikeout': True})
        row_align_center_strikeout = book.add_format(
            {'font_size': 8, 'font_color': 'red', 'align': 'center', 'valign': 'vcenter', 'border': True,
             'font_strikeout': True})
        row_date_format_strikeout = book.add_format(
            {'font_size': 8, 'font_color': 'red', 'num_format': 'd mmmm yyyy', 'align': 'left', 'valign': 'vcenter',
             'border': True, 'font_strikeout': True})

        # get number of columns
        field_names = ['sb_code', 'school_name',
                       'username', 'last_name', 'email', 'telephone', 'schoolbase', 'activated',
                       'usergroups', 'allowed_sections_dict', 'allowed_clusters',
                       'modifiedat', 'modby_name']

        school_code = _('School code') if req_usr_role <= c.ROLE_008_SCHOOL else _('Code')
        school_name = _('School name') if req_usr_role <= c.ROLE_008_SCHOOL else _('Organization')

        field_captions = [str(school_code), str(school_name),
                          str(_('Username')), str(_('Name')), str(_('Email address')), str(_('Telephone')),
                          str(_('School')), str(_('Activated')),
                          str(_('User groups')), str(_('Allowed sections')), str(_('Allowed clusters')),
                          str(_('Last modified on ')), str(_('Last modified by'))]

        field_width = [12, 25,
                       12, 25, 25, 12,
                       15, 15,
                       45, 45, 25,
                       15, 15
                       ]

        header_format = th_align_center
        row_formats = [row_align_center, row_align_left,
                       row_align_left, row_align_left, row_align_left, row_align_left,
                       row_align_left, row_align_center,
                       row_align_left, row_align_left, row_align_left,
                       row_align_left, row_align_left
                       ]

        row_formats_strikeout = [row_align_center_strikeout, row_align_left_strikeout,
                                 row_align_left_strikeout, row_align_left_strikeout, row_align_left_strikeout, row_align_left_strikeout,
                                 row_align_left_strikeout, row_align_center_strikeout,
                                 row_align_left_strikeout, row_align_left_strikeout, row_align_left_strikeout,
                                 row_align_left_strikeout, row_align_left_strikeout
                                 ]

        # --- set column width
        for i, width in enumerate(field_width):
            sheet.set_column(i, i, width)

        row_index = 0

        # --- title row
        title = str(_('List of users'))
        sheet.write(row_index, 0, title, bold_format)
        row_index += 2
        sheet.write(row_index, 0, str(_('Exam year')) + ':', bold_format)
        sheet.write(row_index, 1, str(sel_examyear.code), titel_data)
        row_index += 1
        sheet.write(row_index, 0, str(_('School code')) + ':', bold_format)
        sheet.write(row_index, 1, str(req_usr_school.base.code), titel_data)
        row_index += 1
        sheet.write(row_index, 0, str(_('School')) + ':', bold_format)
        sheet.write(row_index, 1, str(req_usr_school.name), titel_data)

# --- write_table_header
        row_index += 2
        write_table_header(sheet, row_index, field_captions, header_format)

        # ---  write_user_rows
        for row in user_rows:
            row_index += 1
            write_user_rows(sheet, row_index, row, field_names, row_formats, row_formats_strikeout, user_lang)

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

# --- end of create_userdata_xlsx


############ DOWNLOAD STUDENT DATA ########################## PR2022-05-18
@method_decorator([login_required], name='dispatch')
class StudentDownloadXlsxView(View):  # PR2022-05-18 PR2023-01-30

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
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

                if logging_on:
                    logger.debug('    sel_examyear: ' + str(sel_examyear))
                    logger.debug('    sel_school: ' + str(sel_school))
                    logger.debug('    sel_school: ' + str(sel_school))

                if sel_examyear and sel_school and sel_department:

                    response = create_student_xlsx(sel_examyear, sel_school, sel_department, user_lang)

                    if logging_on:
                        logger.debug('    response: ' + str(response))

        #except Exception as e:
        #    logger.error(getattr(e, 'message', str(e)))

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of StudentDownloadXlsxView


# +++++++++++ Student xlsx ++++++++++++
def create_student_xlsx(sel_examyear, sel_school, sel_department, user_lang):  # PR2022-05-18 PR2023-01-30
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_student_xlsx -----')

    # from https://stackoverflow.com/questions/16393242/xlsxwriter-object-save-as-http-response-to-create-download-in-django
    # logger.debug('period_dict: ' + str(period_dict))

    response = None

    def get_student_rows():
        # --- create rows of all students of this examyear / school  / department PR2020-10-27 PR2022-01-03 PR2022-05-18 PR2023-01-30
        # - show only students that are not deleted
        if logging_on:
            logger.debug(' ----- get_student_rows -----')

        sub_list = ["SELECT studsubj.student_id FROM students_studentsubject AS studsubj",
                    "WHERE studsubj.subj_published_id IS NOT NULL",
                    "AND NOT studsubj.deleted",
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

                    "stud.classname, stud.examnumber, stud.regnumber, stud.tobedeleted,",
                    "CASE WHEN stud.iseveningstudent THEN 'x' ELSE NULL END AS iseveningstudent,",
                    "CASE WHEN stud.islexstudent THEN 'x' ELSE NULL END AS islexstudent,",
                    "CASE WHEN stud.bis_exam THEN 'x' ELSE NULL END AS bis_exam,",
                    "CASE WHEN stud.partial_exam THEN 'x' ELSE NULL END AS partial_exam,",
                    "CASE WHEN stud.extrafacilities THEN 'x' ELSE NULL END AS extra_facilities,",

                    "stud.modifiedby_id, stud.modifiedat,",
                    "au.last_name AS modby_name",

                    "FROM students_student AS stud",

                    # PR2023-01-30 was:
                    # "INNER JOIN studsubj ON (studsubj.student_id = stud.id)",

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
                    "AND dep.id = %(dep_id)s::INT",

                    #PR2022-06-13 to filter students with birthcountry Curacao, born before 10-10-10
                    #"AND (POSITION('" + "ura" + "' IN stud.birthcountry) > 0)",
                    #"AND stud.birthdate < '2010-10-10'",
                    
                    "AND NOT stud.deleted",
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

    def write_student_header(sheet, row_index, field_captions, header_format):  # PR2022-05-18
        for col_index, field_caption in enumerate(field_captions):
            sheet.write(row_index, col_index, field_caption, header_format)
    # --- end of write_student_header

    def write_student_rows(sheet, row_index, row, field_names, row_formats, row_formats_strikeout, user_lang):  # PR2022-05-18
        # ---  loop through columns

        for i, field_name in enumerate(field_names):
            if field_name == 'modifiedat':
                modified_dte = row.get(field_name, '')
                value = af.format_modified_at(modified_dte, user_lang)
            else:
                value = row.get(field_name, '')

            formats = row_formats_strikeout if row.get('tobedeleted', False) else row_formats

            sheet.write(row_index, i, value, formats[i])
    # --- end of write_student_rows

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
        #th_align_center.set_font_strikeout(True)

        th_merge_bold = book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        th_merge_bold.set_left()
        th_merge_bold.set_bottom()

        row_align_left = book.add_format({'font_size': 8, 'font_color': 'blue', 'valign': 'vcenter', 'border': True})
        row_align_center = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True})
        row_date_format = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'num_format': 'd mmmm yyyy', 'align': 'left', 'valign': 'vcenter', 'border': True})

        row_align_left_strikeout = book.add_format(
            {'font_size': 8, 'font_color': 'red', 'valign': 'vcenter', 'border': True, 'font_strikeout': True})
        row_align_center_strikeout = book.add_format(
            {'font_size': 8, 'font_color': 'red', 'align': 'center', 'valign': 'vcenter', 'border': True, 'font_strikeout': True})
        row_date_format_strikeout = book.add_format(
            {'font_size': 8, 'font_color': 'red', 'num_format': 'd mmmm yyyy', 'align': 'left', 'valign': 'vcenter',
             'border': True, 'font_strikeout': True})

# get number of columns
        field_names = ['sb_code', 'school_name', 'db_code', 'lvlbase_code', 'sctbase_code',
                       'examnumber', 'lastname', 'firstname', 'prefix', 'gender', 'idnumber',
                       'birthdate', 'birthcountry', 'birthcity',
                       'classname', 'regnumber',  'bis_exam',
                       'iseveningstudent', 'islexstudent', 'partial_exam', 'extra_facilities',
                       'modifiedat', 'modby_name']

        field_captions = [str(_('School code')), str(_('School name')), str(_('Department')), str(_('Level')), str(_('Sector / Profiel')),
                          str(_('Exam number')), str(_('Last name')), str(_('First name')), str(_('Prefix')), str(_('Gender')), str(_('ID-number')),
                          str(_('Date of birth')), str(_('Country of birth')), str(_('Place of birth')),
                          str(_('Class')), str(_('Registration number')), str(_('Bis exam')),
                          str(_('Evening student')), str(_('Landsexamen')), str(_('Partial exam')), str(_('Extra facilities')),
                          str(_('Last modified on ')), str(_('Last modified by'))]

        field_width = [12, 25, 9, 9, 12,
                       12, 20, 25, 9, 6, 12,
                       15, 15, 12,
                       9, 15, 12,
                       12, 12, 12, 12,
                       15, 15
                       ]

        header_format = th_align_center
        row_formats = [row_align_center, row_align_left, row_align_center, row_align_center, row_align_center,
                       row_align_center, row_align_left,  row_align_left, row_align_left, row_align_center, row_align_center,
                       row_date_format, row_align_left, row_align_left,
                       row_align_center, row_align_center, row_align_center,
                       row_align_center, row_align_center, row_align_center, row_align_center,
                       row_align_left, row_align_left
                       ]

        row_formats_strikeout = [row_align_center_strikeout, row_align_left_strikeout, row_align_center_strikeout, row_align_center_strikeout, row_align_center_strikeout,
                       row_align_center_strikeout, row_align_left_strikeout, row_align_left_strikeout, row_align_left_strikeout, row_align_center_strikeout, row_align_center_strikeout,
                       row_date_format_strikeout, row_align_left_strikeout, row_align_left_strikeout,
                       row_align_center_strikeout, row_align_center_strikeout, row_align_center_strikeout,
                       row_align_center_strikeout, row_align_center_strikeout, row_align_center_strikeout, row_align_center_strikeout,
                       row_align_left_strikeout, row_align_left_strikeout
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
            write_student_rows(sheet, row_index, row, field_names, row_formats, row_formats_strikeout, user_lang)

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
                    acc_view.get_selected_examyear_scheme_pk_from_usersetting(request)

                # TODO set sel_scheme_pk not working properly, set None for now. Add modconfirm on page, add list arg to url
                sel_scheme_pk = None

                if sel_examyear_instance :

    # +++ get dict of subjects of these studsubj_rows
                    scheme_rows = subj_view.create_scheme_rows(
                        examyear=sel_examyear_instance,
                        scheme_pk=sel_scheme_pk)
                    subjecttype_rows = subj_view.create_subjecttype_rows(
                        examyear=sel_examyear_instance,
                        append_dict={},
                        scheme_pk=sel_scheme_pk,
                        orderby_sequence=True)
                    schemeitem_rows = subj_view.create_schemeitem_rows(
                        sel_examyear=sel_examyear_instance,
                        append_dict={},
                        scheme_pk=sel_scheme_pk,
                        skip_notatdayschool=True, # subjects with notatdayschool must be included in excel sheet PR2022-08-21
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
                       12, 12, 12, 12,
                       15, 12, 15, 15, 15,
                       12, 12, 12, 12, 12, 15, 15,
                       12, 12, 12, 12, 12, 15, 15
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
                   'min_studyloadhours', 'min_subjects', 'max_subjects',
                   'min_mvt', 'max_mvt', 'min_wisk', 'max_wisk',
                   'min_combi', 'max_combi', 'max_reex',
                   'rule_avg_pece_sufficient', 'rule_avg_pece_notatevlex', 'rule_core_sufficient', 'rule_core_notatevlex',
                   'modifiedat', 'modby_username']
    field_captions = [str(_('Subject scheme')), str(_('Department')), str(_('Level')), str(_('Sector / Profile')),
                      str(_('Minimum studyload hours')), str(_('Minimum number of subjects')), str(_('Maximum number of subjects')),
                      str(_('Minimum number of MVT subjects')), str(_('Maximum number of MVT subjects')),
                      str(_('Minimum number of math subjects')), str(_('Maximum number of math subjects')),
                      str(_('Minimum number of combination subjects')), str(_('Maximum number of combination subjects')),
                      str(_('Maximum number of re-examinations')),

                      str(_('Average CE grade rule')), str(_('Average CE grade rule not at eveningschool')),
                      str(_('Final grade must be sufficient')), str(_('Final grade rule not at eveningschool')),

                      str(_('Last modified on ')), str(_('Last modified by'))
                      ]

    header_format = th_align_center
    row_formats = [row_align_left, row_align_center, row_align_center, row_align_center,
                   row_align_center, row_align_center, row_align_center,
                   row_align_center, row_align_center, row_align_center, row_align_center,
                   row_align_center, row_align_center, row_align_center, row_align_center,
                   row_align_center, row_align_center, row_align_center, row_align_center,
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

                if isinstance(value, bool):
                    value = 'x' if value else ''

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
                    'has_prac','has_pws',
                   'modifiedat', 'modby_username']
    field_captions = [str(_('Character')), str(_('Abbreviation')),
                      str(_('Minimum number of subjects')),
                      str(_('Maximum number of subjects')),
                      str(_("Minimum extra subject, doesn't count")),
                      str(_("Maximum extra subject, doesn't count")),
                      str(_("Minimum extra subject, counts")),
                      str(_("Maximum extra subject, counts")),
                      str(_('Has practical exam')),
                      str(_('Has assignment')),
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
                        if isinstance(value, bool):
                            value = 'x' if value else ''

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
    field_names = [
        'subj_name_nl', 'subj_code', 'sjtp_abbrev', 'gradetype',
        'studyloadhours', 'notatdayschool', 'weight_se', 'weight_ce', 'multiplier', 'is_mandatory', 'is_mand_subj',
        'is_combi', 'is_core_subject', 'is_mvt', 'is_wisk',
        'extra_count_allowed', 'extra_nocount_allowed', 'has_practexam', 'sr_allowed',
        'rule_grade_sufficient', 'rule_gradesuff_notatevlex,',
        'thumb_rule', "no_ce_years", 'otherlang', 'ete_exam',
        'modifiedat', 'modby_username'
    ]

    col_count = len(field_names)
    if logging_on:
        logger.debug('col_count: ' + str(col_count))

    field_captions = [
        str(_('Subjects of this subject scheme')), str(_('Abbreviation')), str(_('Subject type')), str(_('Grade type')),
        str(_('Studyload hours')),str(_('Subject not at dayschool')), str(_('SE weight')), str(_('CE weight')), str(_('Multiplier')), str(_('Mandatory')), str(_("Mandatory if candidate has this subject")),
        str(_('Combination subject')), str(_('Core subject')), str(_('MVT subject')), str(_('Math subject')),
        str(_('Extra subject counts allowed')), str(_('Extra subject does not count allowed')), str(_('Has practical exam')), str(_('Re-examination school exam allowed')),
        str(_('Final grade must be sufficient')), str(_('Final grade rule not at eveningschool')),
        str(_('Thumb rule applies')), str(_('Exam years without CE')), str(_('Other languages')), str(_('ETE exam')),
        str(_('Last modified on')), str(_('Last modified by'))
    ]

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

# ---  loop through schemeitem_rows
    if len(schemeitem_rows):
        for row in schemeitem_rows:
            if logging_on:
                logger.debug('row: ' + str(row))

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
                        if logging_on and False:
                            logger.debug('field_name: ' + str(field_name) + '  value: ' + str(value) + '  ' + str(type(value)))

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

####################################################

def create_result_overview_xlsx(sel_examyear, sel_school, department_dictlist, level_dictlist, schoolbase_dictlist, result_dict_per_school, user_lang):
    # PR2022-06-11
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_result_overview_xlsx -----')

    response = None

    if result_dict_per_school:

# ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        school_name = ' '.join((sel_school.base.code, sel_school.name))
        title = ' '.join((str(_('Results')), str(school_name), str(sel_examyear), 'dd', today_dte.isoformat()))
        file_name = title + ".xlsx"
        worksheet_name = str(_('Results'))

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

# +++++ create worksheet +++++
        sheet = book.add_worksheet(worksheet_name)
        sheet.hide_gridlines(2)  # 2 = Hide screen and printed gridlines
        sheet.hide_zero()
        sheet.freeze_panes(5, 0)

# create dict with formats, used in this workbook
        formats = {
            'bold_format': book.add_format(c.XF_BOLD),
            'row_align_center': book.add_format(c.XF_ROW_ALIGN_CENTER_BLUE),
            'row_align_left': book.add_format(c.XF_ROW_ALIGN_LEFT_BLUE),

            'hdr_tableheader': book.add_format(c.XF_TABLEHEADER),
            'hdr_tableheader_alignleft': book.add_format(c.XF_TABLEHEADER_ALIGNLEFT),
            'hdr_tableheader_borderleft': book.add_format(c.XF_TABLEHEADER_BORDERLEFT),

            'hdr_grandtotal': book.add_format(c.XF_HDR_GRANDTOTAL),
            'hdr_grandtotal_alignleft': book.add_format(c.XF_HDR_GRANDTOTAL_ALIGNLEFT),
            'hdr_grandtotal_percentage': book.add_format(c.XF_HDR_GRANDTOTAL_PERCENTAGE),
            'hdr_grandtotal_borderleft': book.add_format(c.XF_HDR_GRANDTOTAL_BORDERLEFT),
            'hdr_grandtotal_perc_borderleft': book.add_format(c.XF_HDR_GRANDTOTAL_PERCENTAGE_BORDERLEFT),

            'hdr_subtotal': book.add_format(c.XF_HDR_SUBTOTAL),
            'hdr_subtotal_alignleft': book.add_format(c.XF_HDR_SUBTOTAL_ALIGNLEFT),
            'hdr_subtotal_percentage': book.add_format(c.XF_HDR_SUBTOTAL_PERCENTAGE),
            'hdr_subtotal_borderleft': book.add_format(c.XF_HDR_SUBTOTAL_BORDERLEFT),
            'hdr_subtotal_perc_borderleft': book.add_format(c.XF_HDR_SUBTOTAL_PERCENTAGE_BORDERLEFT),

            'hdr_subsubtotal': book.add_format(c.XF_HDR_SUBSUBTOTAL),
            'hdr_subsubtotal_alignleft': book.add_format(c.XF_HDR_SUBSUBTOTAL_ALIGNLEFT),
            'hdr_subsubtotal_percentage': book.add_format(c.XF_HDR_SUBSUBTOTAL_PERCENTAGE),
            'hdr_subsubtotal_borderleft': book.add_format(c.XF_HDR_SUBSUBTOTAL_BORDERLEFT),
            'hdr_subsubtotal_perc_borderleft': book.add_format(c.XF_HDR_SUBSUBTOTAL_PERCENTAGE_BORDERLEFT),

            'row_value': book.add_format(c.XF_ROW_VALUE),
            'row_value_alignleft': book.add_format(c.XF_ROW_VALUE_ALIGNLEFT),
            'row_perc': book.add_format(c.XF_ROW_PERCENTAGE),
            'row_value_borderleft': book.add_format(c.XF_ROW_VALUE_BORDERLEFT),
            'row_perc_borderleft': book.add_format(c.XF_ROW_PERCENTAGE_BORDERLEFT),

            'th_align_center': book.add_format(c.XF_HDR_ALC_TOPBOTTOM),
            'th_align_left': book.add_format(c.XF_HDR_ALL_TOPBOTTOM)
        }

        titel_data = book.add_format({'font_size': 11, 'font_color': 'blue', 'valign': 'vcenter'})

        th_merge_bold = book.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        th_merge_bold.set_left()
        th_merge_bold.set_bottom()

        row_date_format = book.add_format(
            {'font_size': 8, 'font_color': 'blue', 'num_format': 'd mmmm yyyy', 'align': 'left', 'valign': 'vcenter',
             'border': True})

        # get number of columns
        field_names = ['sb_code', 'sch_name',
                       'c_m', 'c_v', 'c_t',
                       'r_p_m', 'r_p_v', 'r_p_t',
                       'r_r_m', 'r_r_v', 'r_r_t',
                       'r_f_m', 'r_f_v', 'r_f_t',
                       'r_w_m', 'r_w_v', 'r_w_t',
                       'r_n_m', 'r_n_v', 'r_n_t'
                       ]
        field_captions = ['', str(_('School')),
                          str(_('Total candidates')), '', '',
                          str(_('Passed')),  '', '',
                          str(_('Re-examination')), '', '',
                          str(_('Failed')), '', '',
                          str(_('Withdrawn')), '', '',
                          str(_('No result')), '', ''
                          ]

        subheader_captions = [str(_('V')), 'T', 'M']

        field_width = [8, 36,
                       4.6, 4.6, 4.6,
                       4.6, 4.6, 4.6,
                       4.6, 4.6, 4.6,
                       4.6, 4.6, 4.6,
                       4.6, 4.6, 4.6,
                       4.6, 4.6, 4.6,
                       8, 8, 36,
                       4.6, 4.6, 4.6,
                       4.6, 4.6, 4.6,
                       4.6, 4.6, 4.6,
                       4.6, 4.6, 4.6,
                       4.6, 4.6, 4.6]

        write_resultlist_details(sheet, sel_examyear, department_dictlist, level_dictlist, schoolbase_dictlist, result_dict_per_school,
                                field_names, field_captions, field_width, subheader_captions, formats, user_lang)

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
# - end of write_resultlist


def write_resultlist_details(sheet, sel_examyear, department_dictlist, level_dictlist, schoolbase_dictlist, result_dict_per_school,
                             field_names, field_captions, field_width, subheader_captions, formats, user_lang):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- write_resultlist_details -----')
        logger.debug(' ----- write_resultlist_details -----')
    """
    result_dict: {
        1: {'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 
                4: {'lvl_id': 4, 'lvl_code': 'TKL', 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 
                    13: {'sch_code': None, 'sch_name': 'Abel Tasman College', 
                        'res': {'c_m': 4, 'c_v': 6, 'c_t': 10, 
                                'r_p_m': 2, 'r_p_v': 6, 'r_p_t': 8, 
                                'r_f_m': 0, 'r_f_v': 0, 'r_f_t': 0,
                                'r_r_m': 1, 'r_r_v': 0, 'r_r_t': 1, 
                                'r_n_m': 1, 'r_n_v': 0, 'r_n_t': 1, 
                                'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0}}}}, 
        2: {'db_id': 2, 'db_code': 'Havo', 'dep_name': 'Hoger Algemeen Voortgezet Onderwijs', 
                0: {'lvl_id': 0, 'lvl_code': None, 'lvl_name': None, 
                    13: {'sch_code': None, 'sch_name': 'Abel Tasman College', 
                        'res': {'c_m': 12, 'c_v': 9, 'c_t': 21, 'r_p_m': 6, 'r_p_v': 5, 'r_p_t': 11, 'r_f_m': 0, 'r_f_v': 2, 'r_f_t': 2, 'r_r_m': 6, 'r_r_v': 2, 'r_r_t': 8, 'r_n_m': 0, 'r_n_v': 0, 'r_n_t': 0, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0}}}}, 
        3: {'db_id': 3, 'db_code': 'Vwo', 'dep_name': 'Voorbereidend Wetenschappelijk Onderwijs', 
                0: {'lvl_id': 0, 'lvl_code': None, 'lvl_name': None, 
                    13: {'sch_code': None, 'sch_name': 'Abel Tasman College', 
                    'res': {'c_m': 2, 'c_v': 5, 'c_t': 7, 'r_p_m': 1, 'r_p_v': 2, 'r_p_t': 3, 'r_f_m': 0, 'r_f_v': 0, 'r_f_t': 0, 'r_r_m': 1, 'r_r_v': 3, 'r_r_t': 4, 'r_n_m': 0, 'r_n_v': 0, 'r_n_t': 0, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0}}}}}
    """

# write_result_header_row
    def write_result_header_row(sheet, row_index, formats):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' -----  write_result_header_row  -----')
            logger.debug('field_captions: ' + str(field_captions))

        format_value = formats['hdr_tableheader']
        format_alignleft = formats['hdr_tableheader_alignleft']
        format_value_bl = formats['hdr_tableheader_borderleft']

# --- write_column_header and write_column_subheader
        sheet.set_row(row_index, 26)
        for col_index, field_caption in enumerate(field_captions):
            # passed_m is stored in index 5 (has modulo 2), percentage passed_m in col_index 23 (has modulo 2)
            # modulo operator >>> 5 % 3 = 2
            header_merge = col_index % 3 == 2

            if logging_on:
                logger.debug('col_index: ' + str(col_index))
                logger.debug('    header_merge: ' + str(header_merge))
                logger.debug('    field_caption: ' + str(field_caption))
                logger.debug('    format_value_bl: ' + str(format_value_bl))


            if col_index <= 1:
                sheet.write(row_index, col_index, field_caption, format_alignleft)
                sheet.write(row_index + 1, col_index, '', format_alignleft)

                sheet.write(row_index, col_index + 21, field_caption, format_alignleft)
                sheet.write(row_index + 1, col_index + 21, '', format_alignleft)

            elif 1 < col_index < 20:
                col_index_perc = col_index + 18
                if header_merge:
                    sheet.merge_range(row_index, col_index, row_index, col_index + 2, field_caption, format_value_bl)
                    if col_index > 4:
                        sheet.merge_range(row_index, col_index_perc, row_index, col_index_perc + 2, field_caption, format_value_bl)

                # modulo index % 3 is used to lookup caption, M = modulo 2, therefore M comes last in subheader_captions
                # subheader_captions = [str(_('V')), 'T', 'M']
                modulo = col_index % 3
                subheader_caption = subheader_captions[modulo]
                sheet.write(row_index + 1, col_index, subheader_caption, format_value_bl)
                if col_index > 4:
                    sheet.write(row_index + 1, col_index_perc, subheader_caption, format_value_bl)
    # - end of write_result_header_row

    def write_result_total_row(sheet, row_index, first_total_row_index, formats, mode, dep_lvl_code=None, sb_code = None, sch_name = None):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' -----  write_result_total_row  -----')
            #logger.debug('formats: ' + str(formats))

        if mode == 'grand':
            format_key_value = 'hdr_grandtotal'
            format_key_alignleft = 'hdr_grandtotal_alignleft'
            format_key_perc = 'hdr_grandtotal_percentage'
            format_key_value_bl = 'hdr_grandtotal_borderleft'
            format_key_perc_bl = 'hdr_grandtotal_perc_borderleft'
        elif mode == 'dep':
            format_key_value = 'hdr_subtotal'
            format_key_alignleft = 'hdr_subtotal_alignleft'
            format_key_perc = 'hdr_subtotal_percentage'
            format_key_value_bl = 'hdr_subtotal_borderleft'
            format_key_perc_bl = 'hdr_subtotal_perc_borderleft'
        elif mode == 'level':
            format_key_value = 'hdr_subsubtotal'
            format_key_alignleft = 'hdr_subsubtotal_alignleft'
            format_key_perc = 'hdr_subsubtotal_percentage'
            format_key_value_bl = 'hdr_subsubtotal_borderleft'
            format_key_perc_bl = 'hdr_subsubtotal_perc_borderleft'
        else:
            format_key_value = 'row_value'
            format_key_alignleft = 'row_value_alignleft'
            format_key_perc = 'row_perc'
            format_key_value_bl = 'row_value_borderleft'
            format_key_perc_bl = 'row_perc_borderleft'

        format_value = formats[format_key_value]
        format_alignleft = formats[format_key_alignleft]
        format_perc = formats[format_key_perc]
        format_value_bl = formats[format_key_value_bl]
        format_perc_bl = formats[format_key_perc_bl]

        for i, field_name in enumerate(field_names):
            code, name = None, None
            if mode == 'school':
                code = schoolbase_dict.get('sbase_code', '---')
                name = schoolbase_dict.get('sch_name', '---')
                write_value_cell(sheet, i, row_index, field_name, format_value, format_alignleft,
                               format_value_bl)
            else:
                name = str(_('TOTAL'))
                if dep_lvl_code:
                    name += ' ' + dep_lvl_code.upper()
                write_sum_cell(sheet, i, row_index, first_total_row_index, format_value, format_alignleft, format_value_bl, code, name)

            write_percentage_cell(sheet, i, row_index, format_perc, format_alignleft, format_perc_bl, code, name)
    # - end of write_result_total_row

    def write_value_cell(sheet, col_index, row_index, field_name, format_value, format_alignleft, format_value_bl):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' -----  write_value_cell  -----')
            logger.debug('col_index: ' + str(col_index))

        if field_name == 'db_code':
            sheet.write(row_index, col_index, dep_dict.get('depbase_code', '---'), format_alignleft)
        elif field_name == 'lvl_code':
            sheet.write(row_index, col_index, lvlbase_dict.get('lvlbase_code', '---'), format_alignleft)
        elif field_name == 'sb_code':
            sheet.write(row_index, col_index, schoolbase_dict.get('sbase_code', '---'), format_alignleft)
        elif field_name == 'sch_name':
            sheet.write(row_index, col_index, schoolbase_dict.get(field_name, '---'), format_alignleft)
        else:
            modulo = col_index % 3
            frm_val = format_value_bl if modulo == 2 else format_value
            value = sbase_result_dict.get(field_name)
            value_int = 0
            if value and isinstance(value, int):
                value_int = value
            sheet.write(row_index, col_index, value_int, frm_val)
    # - end of write_value_cell

    def write_sum_cell(sheet, col_index, row_index, first_total_row_index, format_value, format_alignleft, format_value_bl, code, name):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' -----  write_sum_cell  -----')
            logger.debug('col_index: ' + str(col_index))

        if col_index == 0:
            code_str = code if code else ''
            sheet.write(row_index, col_index, code_str, format_alignleft)
        elif col_index == 1:
            name_str = name if name else ''
            sheet.write(row_index, col_index, name_str, format_alignleft)
        else:
            # passed_m is stored in index 5 (has modulo 2), percentage passed_m in col_index 23 (has modulo 2)
            # modulo operator >>> 5 % 3 = 2
            modulo = col_index % 3
            frm_val = format_value_bl if modulo == 2 else format_value

            upper_cell_ref = subj_view.xl_rowcol_to_cell(first_total_row_index, col_index)
            lower_cell_ref = subj_view.xl_rowcol_to_cell(row_index - 1, col_index)
            this_cell_ref = subj_view.xl_rowcol_to_cell(row_index, col_index)

            formula = ''.join(('SUBTOTAL(9,', upper_cell_ref, ':', lower_cell_ref, ')'))
            sheet.write_formula(this_cell_ref, formula, frm_val)
    # - end of write_sum_cell

    def write_percentage_cell(sheet, col_index, row_index, format_perc, format_alignleft, format_perc_bl, code = None, name = None):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' -----  write_value_percentage_cell  -----')

        col_index_perc = col_index + 18

        # number of M, V. T is stored in col_index 2, 3, 4
        count_m_ref = subj_view.xl_rowcol_to_cell(row_index, 2)
        count_v_ref = subj_view.xl_rowcol_to_cell(row_index, 3)
        count_t_ref = subj_view.xl_rowcol_to_cell(row_index, 4)
        sum_cell_ref = subj_view.xl_rowcol_to_cell(row_index, col_index)
        if logging_on:
            logger.debug('col_index: ' + str(col_index))
            logger.debug('count_m_ref: ' + str(count_m_ref))
            logger.debug('count_v_ref: ' + str(count_v_ref))
            logger.debug('count_t_ref: ' + str(count_t_ref))
            logger.debug('sum_cell_ref: ' + str(sum_cell_ref))

        # passed_m is stored in index 5 (has modulo 2), percentage passed_m in col_index 23 (has modulo 2)
        # modulo operator >>> 5 % 3 = 2
        modulo = col_index % 3
        frm_perc = format_perc_bl if modulo == 2 else format_perc

        # put percentage in next set of columns
        count_ref = count_m_ref if modulo == 2 else count_v_ref if modulo == 0 else count_t_ref
        this_cell_ref = subj_view.xl_rowcol_to_cell(row_index, col_index_perc)

        if col_index == 3:
            code_str = code if code else ''
            sheet.write(row_index, col_index_perc, code_str, format_alignleft)
        elif col_index == 4:
            name_str = name if name else ''
            sheet.write(row_index, col_index_perc, name_str, format_alignleft)

        elif 4 < col_index < 20:
            # check for None and 0 values
            # =IF(OR(ISBLANK($D39);$D39=0);0;G39/$D39)
            formula = ''.join(('IF(OR(ISBLANK($', count_ref, '),$', count_ref, '=0),0,', sum_cell_ref, '/$', count_ref, ')'))
            sheet.write_formula(this_cell_ref, formula, frm_perc)

            if logging_on:
                logger.debug('this_cell_ref: ' + str(this_cell_ref))
                logger.debug('formula: ' + str(formula))
    # - end of write_value_percentage_cell

# --- set column width
    for i, width in enumerate(field_width):
        sheet.set_column(i, i, width)

    row_index = 0

# --- title row
    title = ' '.join((str(_('Exam results')), str(sel_examyear.code)))
    sheet.write(row_index, 1, title, formats['bold_format'])
    row_index += 1

    today_dte = af.get_today_dateobj()
    today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
    title = ''.join((str(_('Date')), ': ', today_formatted))
    sheet.write(row_index, 1, title, formats['bold_format'])
    row_index += 2


# --- write_column_header and write_column_subheader
    write_result_header_row(sheet, row_index, formats)
    row_index += 2
    grandtotal_first_row_index = row_index

# +++++++++++++++++++++ loop through departent  ++++++++++++++++++++++++++++
    for dep_dict in department_dictlist:
        # fields are: depbase_id, depbase_code, dep_name, dep_level_req
        """
        dep_dict: {'depbase_id': 1, 'depbase_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_level_req': True}
        """
        depbase_pk = dep_dict.get('depbase_id')
        dep_name = dep_dict.get('dep_name')
        depbase_code = dep_dict.get('depbase_code')
        level_req = dep_dict.get('dep_level_req', False)
        if logging_on and False:
            logger.debug('dep_dict: ' + str(dep_dict))

# lookup dep in result_dict_per_school
        if depbase_pk in result_dict_per_school:
            depbase_result_dict = result_dict_per_school.get(depbase_pk)
            if logging_on and False:
                logger.debug('depbase_result_dict: ' + str(depbase_result_dict))
            """
            depbase_result_dict {'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 
                4: {'lvlbase_id': 4, 'lvl_code': 'TKL', 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 
                    13: {'sch_code': None, 'sch_name': 'Abel Tasman College', 
                        'res': {'c_m': 4, 'c_v': 6, 'c_t': 10, 'r_p_m': 2, 'r_p_v': 6, 'r_p_t': 8, 'r_f_m': 0, 'r_f_v': 0, 'r_f_t': 0, 'r_r_m': 1, 'r_r_v': 0, 'r_r_t': 1, 'r_n_m': 1, 'r_n_v': 0, 'r_n_t': 1, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0}}}}, 
            """
            logger.debug('depbase_pk in result_dict_per_school row_index: ' + str(row_index))
    # ---  department title row
            row_index += 2
            sheet.merge_range(row_index, 0, row_index, 19, dep_name, formats['hdr_subtotal'])
            sheet.merge_range(row_index, 21, row_index, 37, dep_name, formats['hdr_subtotal'])

            logger.debug('department title row: ' + str(row_index))

    # ---  departent column header row
            depbase_first_row_index = row_index
            logger.debug('depbase_first_row_index: ' + str(row_index))

    # ++++++++++++ loop through levels  ++++++++++++++++++++++++++++
            for lvlbase_dict in level_dictlist:
                # fields are lvlbase_id, lvlbase_code, lvl_name",
                """
                lvlbase_dict: {'lvlbase_id': 6, 'lvlbase_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg'}
                lvlbase_dict: {'lvlbase_id': 0, 'lvlbase_code': '', 'lvl_name': ''}

                """
                if logging_on and False:
                    logger.debug('lvlbase_dict: ' + str(lvlbase_dict))

                lvlbase_pk = lvlbase_dict.get('lvlbase_id') or 0
                lvl_name = lvlbase_dict.get('lvl_name') or str(_('Learning path is not entered'))
                lvlbase_code = lvlbase_dict.get('lvlbase_code')  or '---'

     # lookup level in depbase_result_dict
                if lvlbase_pk in depbase_result_dict:
                    lvlbase_result_dict = depbase_result_dict.get(lvlbase_pk)

                    if logging_on and False:
                        logger.debug('lvlbase_result_dict: ' + str(lvlbase_result_dict))
                    """
                    lvlbase_result_dict {
                        'lvlbase_id': 4, 'lvl_code': 'TKL', 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 
                        13: {'sb_id': 13,'sch_code': None, 'sch_name': 'Abel Tasman College', 
                                'res': {'c_m': 4, 'c_v': 6, 'c_t': 10, 'r_p_m': 2, 'r_p_v': 6, 'r_p_t': 8, 'r_f_m': 0, 'r_f_v': 0, 'r_f_t': 0, 'r_r_m': 1, 'r_r_v': 0, 'r_r_t': 1, 'r_n_m': 1, 'r_n_v': 0, 'r_n_t': 1, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0}}}}, 
                    """

        # ---  level title row
                    # skip when Havo / Vwo
                    if level_req:
                        row_index += 2
                        sheet.merge_range(row_index, 0, row_index, 19, lvl_name, formats['hdr_subsubtotal'])
                        sheet.merge_range(row_index, 21, row_index, 37, lvl_name, formats['hdr_subsubtotal'])

                    logger.debug('level title row: ' + str(row_index))
        # ---  level column header row
                       # row_index += 1
                        #for i in range(0, col_count):
                        #    sheet.write(row_index, i, field_captions[i], col_header_formats[i])

        # ---  level total row  > moved to the end
                        #row_index += 1

                    lvlbase_first_row_index = row_index

    # ++++++++++++ loop through schools  ++++++++++++++++++++++++++++
                    for schoolbase_dict in schoolbase_dictlist:
                        if logging_on and False:
                            logger.debug('schoolbase_dict: ' + str(schoolbase_dict))
                        """
                        schoolbase_dict: {'sbase_id': 13, 'sbase_code': 'CUR13', 'sch_article': 'het', 'sch_name': 'Abel Tasman College', 'sch_abbrev': 'ATC', 'defaultrole': 8}
                        """
                        schoolbase_pk = schoolbase_dict.get('sbase_id')
                        if schoolbase_pk in lvlbase_result_dict:
                            # PR2022-06-17 defaultrole = school is filtered out in create_results_per_school_rows
                            # was: defaultrole = schoolbase_dict.get('defaultrole', 0)
                            row_index += 1

                            sbase_result_dict = lvlbase_result_dict.get(schoolbase_pk)
                            if lvlbase_first_row_index is None:
                                lvlbase_first_row_index = row_index

                            if logging_on and False:
                                logger.debug('sbase_result_dict: ' + str(sbase_result_dict))
                            sb_code = schoolbase_dict.get('sbase_code', '---')
                            sch_name = schoolbase_dict.get('sch_name', '---')
                            write_result_total_row(sheet, row_index, 0, formats, 'school',
                                                       None, sb_code, sch_name)

    # ++++++++++++ end of loop through schools  ++++++++++++++++++++++++++++
                    if level_req:
                        # add 1 extra row t subtotal range, to prevent leaving out last row in calculation when manually added extra rows
                        if lvlbase_first_row_index:
                            row_index += 1
                            logger.debug('end of loop through schools: ' + str(row_index))
                            write_result_total_row(sheet, row_index, lvlbase_first_row_index, formats, 'level', lvlbase_code)
                            logger.debug('write_result_total_row: ' + str(row_index))

# --- write departent total row
            if depbase_first_row_index:
                row_index += 2 if level_req else 1
                logger.debug('write departent total row: ' + str(row_index))
                write_result_total_row(sheet, row_index, depbase_first_row_index, formats, 'dep', depbase_code)
                logger.debug('write_result_total_row: ' + str(row_index))

# --- write grand total row
    row_index += 2
    write_result_total_row(sheet, row_index, grandtotal_first_row_index, formats, 'grand', None)

# - end of write_resultlist_details



# from https://github.com/jmcnamara/XlsxWriter/blob/main/xlsxwriter/utility.py PR2021-08-30

def xl_rowcol_to_cell(row, col, row_abs=False, col_abs=False):
    """
    Convert a zero indexed row and column cell reference to a A1 style string.
    Args:
       row:     The cell row.    Int.
       col:     The cell column. Int.
       row_abs: Optional flag to make the row absolute.    Bool.
       col_abs: Optional flag to make the column absolute. Bool.
    Returns:
        A1 style string.
    """
    if row < 0:
        return None

    if col < 0:
        return None

    row += 1  # Change to 1-index.
    row_abs = '$' if row_abs else ''

    col_str = xl_col_to_name(col, col_abs)

    return col_str + row_abs + str(row)


def xl_col_to_name(col, col_abs=False):
    """
    Convert a zero indexed column cell reference to a string.
    Args:
       col:     The cell column. Int.
       col_abs: Optional flag to make the column absolute. Bool.
    Returns:
        Column style string.
    """
    col_num = col
    if col_num < 0:
        return None

    col_num += 1  # Change to 1-index.
    col_str = ''
    col_abs = '$' if col_abs else ''

    while col_num:
        # Set remainder from 1 .. 26
        remainder = col_num % 26

        if remainder == 0:
            remainder = 26

        # Convert the remainder to a character.
        col_letter = chr(ord('A') + remainder - 1)

        # Accumulate the column letters, right to left.
        col_str = col_letter + col_str

        # Get the next order of magnitude.
        col_num = int((col_num - 1) / 26)

    return col_abs + col_str
#---------------------------------------





###################################################
# PR2021-09-2 from https://thispointer.com/python-how-to-create-a-zip-archive-from-multiple-files-or-directory/

def xl_book_add_format(book, font_size=11, font_color='black', font_bold=False, bg_color=None, h_align='left', v_align='vcenter',
        border=False, border_top=None, border_bottom=None, border_left=None, border_right=None,
        text_wrap=False, num_format=None):
    # PR2023-07-11

    xl_format = {
        'font_size': font_size,
        'font_color': font_color,
        'align':  h_align,
        'valign': v_align
    }

    if font_bold:
        xl_format['bold'] = True
    if bg_color:
        xl_format['bg_color'] = bg_color

    if text_wrap:
        xl_format['text_wrap'] = True

    if border:
        xl_format['border'] = True
    if border_top:
        xl_format['top'] = border_top
    if border_bottom:
        xl_format['bottom'] = border_bottom
    if border_left:
        xl_format['left'] = border_left
    if border_right:
        xl_format['right'] = border_right

    if num_format:
        if num_format == 'num_dig_0':
            xl_format['num_format'] = '#,##0'
        elif num_format == 'num_dig_2':
            xl_format['num_format'] = '#,##0.00'
        elif num_format == 'perc_dig_0':
            xl_format['num_format'] = '0%',
        elif num_format == 'perc_dig_2':
            xl_format['num_format'] = '0.00%',
        else:
            xl_format['num_format'] = num_format

    return book.add_format(xl_format)
# - end of xl_book_add_format


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