# PR2024-06-19
import json
import os
import tempfile
from django.core.files import File

from django.db import connection

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, pgettext_lazy, gettext, gettext_lazy as _
from django.utils import timezone
from django.views.generic import View

from os.path import basename

from timeit import default_timer as timer

from accounts import models as acc_mod
from accounts import views as acc_view
from accounts import permits as acc_prm

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

from grades import calc_results as calc_res
from grades import calc_finalgrade as calc_final

import xlsxwriter
from zipfile import ZipFile
import io

import logging
logger = logging.getLogger(__name__)


@method_decorator([login_required], name='dispatch')
class DownloadMultipleResultOverviewView(View):  # PR2024-06-19
    # download ecel file with result overview of multiple examyears

    def get(self, request, lst):

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= DownloadMultipleResultOverviewView ============= ')
            logger.debug('    lst: ' + str(lst))

        response = None

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

            if sel_examyear and sel_school and sel_department:

# get first and last examyear (sel_examyear.code is integer)
                min_examyear_code = int(lst) if lst and lst !='-' else None
                max_examyear_code = sel_examyear.code
                if min_examyear_code is None or min_examyear_code > max_examyear_code:
                    min_examyear_code = max_examyear_code

# - fill list with examyears [2022, 2023, 2024]
                #examyear_list = []
                #for examyear_code in range(min_examyear_code, max_examyear_code + 1):  # range(start_value, end_value, step), end_value is not included!
                #    examyear_list.append(examyear_code)

# +++ get nested dicts of results per school, dep, level
                examyear_list, depbase_dict, lvlbase_dict, schoolbase_dict, has_gender_x, result_dict, error_dict = \
                    create_result_dict_per_school_multiple_examyears(
                        country_pk=request.user.country.pk,
                        is_role_school=request.user.is_role_school,
                        sel_schoolbase=sel_school.base,
                        max_examyear_code=max_examyear_code,
                        min_examyear_code=min_examyear_code
                    )

# +++ create result_overview_xlsx
                response = create_result_overview_multiple_examyears_xlsx(
                    examyear_list=examyear_list,
                    sel_school=sel_school,
                    is_role_school=request.user.is_role_school,
                    depbase_dict=depbase_dict,
                    lvlbase_dict=lvlbase_dict,
                    schoolbase_dict=schoolbase_dict,
                    has_gender_x=has_gender_x,
                    result_dict=result_dict,
                    user_lang=user_lang
                )

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of DownloadMultipleResultOverviewView


@method_decorator([login_required], name='dispatch')
class DownloadGradeAvgOverviewView(View):  # PR2024-06-23
    # download ecel file with result overview of multiple examyears

    def get(self, request, lst):

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= DownloadGradeAvgOverviewView ============= ')
            logger.debug('    lst: ' + str(lst))

        response = None

        if request.user and request.user.country and request.user.schoolbase:
            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

            if lst and sel_examyear and sel_school and sel_department:

                show_gender = False
# get first and last examyear (sel_examyear.code is integer)

                # when split_gender: lst = 'split2023'

                if lst[:5] == 'split':
                    show_gender = True
                    min_examyear_str = lst[5:]
                else:
                    min_examyear_str = lst

                min_examyear_code = None
                if len(min_examyear_str) == 4:
                    min_examyear_code = int(min_examyear_str)

                max_examyear_code = sel_examyear.code

                if min_examyear_code is None or min_examyear_code > max_examyear_code:
                    min_examyear_code = max_examyear_code

# +++ get nested dicts of results per school, dep, level
                examyear_list, depbase_dictlist, lvlbase_dictlist, schoolbase_dictlist, subjbase_dictlist, has_gender_x, grades_dict, error_dict = \
                    create_grade_avg_dict(
                        country_pk=request.user.country.pk,
                        is_role_school=request.user.is_role_school,
                        sel_schoolbase=sel_school.base if sel_school else None,
                        sel_depbase=sel_department.base if sel_department else None,
                        max_examyear_code=max_examyear_code,
                        min_examyear_code=min_examyear_code
                    )

# +++ create grade_avg_overview_xlsx
                response = create_grade_avg_overview_xlsx(
                    examyear_list=examyear_list,
                    sel_school=sel_school,
                    is_role_school=request.user.is_role_school,
                    depbase_dictlist=depbase_dictlist,
                    lvlbase_dictlist=lvlbase_dictlist,
                    schoolbase_dictlist=schoolbase_dictlist,
                    subjbase_dictlist=subjbase_dictlist,
                    has_gender_x=has_gender_x,
                    show_gender=show_gender,
                    grades_dict=grades_dict,
                    user_lang=user_lang
                )

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of DownloadGradeAvgOverviewView


def create_result_overview_multiple_examyears_xlsx(examyear_list, sel_school, is_role_school,
                                                   depbase_dict, lvlbase_dict, schoolbase_dict,
                                                   has_gender_x, result_dict, user_lang):
    # PR2022-06-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_result_overview_multiple_examyears_xlsx -----')

    response = None

    def get_field_dictlist():
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug('----- get_field_dictlist -----')

    # create result_list
        result_list = ('c', 'p', 'f', 'r', 'w', 'n')

        result_captions = {
            'c': gettext('Total candidates'),
            'p': gettext('Passed'),
            'f': gettext('Failed'),
            'r': gettext('Re-examination'),
            'w': gettext('Withdrawn'),
            'n': gettext('No result')
        }

    # create gender_list
        # only add 'x' when there are students with gender 'x'
        gender_list = ['m', 'v']
        if has_gender_x:
            gender_list.append('x')
        gender_list.append('t')

        gender_captions = {
            'm': 'M',
            'v': gettext('V'),
            'x': '-',
            't': 'T',
        }

        # first 2 columns are schoolcode and schoolname
        field_dictlist = []
        field_dictlist_index = 0
        field_dictlist.append(
            {'width': 8,
             'hdr1': {'caption': '', 'format': 'hdr_tableheader_alignleft'},
             'hdr2': {'format': 'hdr_tableheader_alignleft'},
             'hdr3': {'format': 'hdr_tableheader_alignleft'},
             'hdrdep': {'format': 'hdr_subtotal_alignleft'},
             'hdrlvl': {'format': 'hdr_subsubtotal_alignleft'},
             'detail': {'field': 'sb_code', 'format': 'row_value_alignleft'},
             'totgrd': {'format': 'hdr_grandtotal_alignleft'},
             'totdep': {'format': 'hdr_subtotal_alignleft'},
             'totlvl': {'format': 'hdr_subsubtotal_alignleft'},
            }
        )
        field_dictlist_index += 1
        field_dictlist.append(
            {'width': 36,
            'hdr1': {'caption': gettext('School'), 'format': 'hdr_tableheader_alignleft'},
            'hdr2': {'caption': '', 'format': 'hdr_tableheader_alignleft'},
            'hdr3': {'caption': '', 'format': 'hdr_tableheader_alignleft'},
            'hdrdep': {'caption': '', 'format': 'hdr_subtotal_alignleft'},
            'hdrlvl': {'caption': '', 'format': 'hdr_subsubtotal_alignleft'},
            'detail': {'field': 'sch_name', 'format': 'row_value_alignleft'},
            'totgrd': {'field': 'grd_code','format': 'hdr_grandtotal_alignleft'},
            'totdep': {'field': 'dep_code','format': 'hdr_subtotal_alignleft'},
            'totlvl': {'field': 'lvl_code','format': 'hdr_subsubtotal_alignleft'},
            }
        )
        field_dictlist_index += 1
    # merge field is the number of columns to span the header
        genderlist_length = len(gender_list)
        result_merge = examyear_list_len * genderlist_length

    # - Loop trough result list
        for result_index, result_code in enumerate(result_list):
            result_caption = result_captions[result_code]

    # - Loop trough exam years
            for examyear_index, examyear_code in enumerate(examyear_list):
                examyear_caption = str(examyear_code)
    # - Loop trough gender
                # gender_list = ['m', 'v', 't'] or ['m', 'v', 'x', 't']
                # total index is the last column 't'
                # save the numer of rows that must be added to the right in t_col_add
                # t_col is the index of the total column
                # used to calculate percentages
                for gender_index, gender_code in enumerate(gender_list):
                    gender_caption = gender_captions[gender_code]

                    if logging_on:
                        logger.debug('    gender_index: ' + str(gender_index) + ' gender_code: ' + str(gender_code) + ' gender_caption: ' + str(gender_caption))

                    t_col = field_dictlist_index - result_index * genderlist_length * examyear_list_len
                    field = ''.join((examyear_caption, '-', result_code, '_',gender_code))
                    field_dict = {
                        'width': 4.6,
                        't_col': t_col
                    }
                    # onlye add hdr when index = 0
                    if not examyear_index and not gender_index:
                        field_dict['hdr1'] = {'caption': result_caption, 'merge': result_merge, 'format': 'hdr_tableheader_borderleft'}
                        field_dict['hdrdep'] = {'merge': result_merge, 'format': 'hdr_subtotal'}
                        field_dict['hdrlvl'] = {'merge': result_merge, 'format': 'hdr_subsubtotal'}
                    if not gender_index:
                        field_dict['hdr2'] = {'caption': examyear_caption, 'merge': genderlist_length, 'format': 'hdr_tableheader_borderleft'}

                    field_dict['hdr3'] = {'caption': gender_caption, 'format': 'hdr_tableheader_borderleft'}

                    detail_row_format = 'row_value_borderleft' if not gender_index else 'row_value'
                    detail_row_formatperc = 'row_perc_borderleft' if not gender_index else 'row_perc'
                    field_dict['detail'] =  {'field': field, 'format': detail_row_format, 'formatperc': detail_row_formatperc}

                    totgrd_row_format = 'hdr_grandtotal_borderleft' if not gender_index else 'hdr_grandtotal'
                    totgrd_row_formatperc = 'hdr_grandtotal_perc_borderleft' if not gender_index else 'hdr_grandtotal_percentage'
                    field_dict['totgrd'] =  {'field': field, 'format': totgrd_row_format, 'formatperc': totgrd_row_formatperc}

                    totdep_row_format = 'hdr_subtotal_borderleft' if not gender_index else 'hdr_subtotal'
                    totdep_row_formatperc = 'hdr_subtotal_perc_borderleft' if not gender_index else 'hdr_subtotal_percentage'
                    field_dict['totdep'] =  {'field': field, 'format': totdep_row_format, 'formatperc': totdep_row_formatperc}

                    totlvl_row_format = 'hdr_subsubtotal_borderleft' if not gender_index else 'hdr_subsubtotal'
                    totlvl_row_formatperc = 'hdr_subsubtotal_perc_borderleft' if not gender_index else 'hdr_subsubtotal_percentage'
                    field_dict['totlvl'] =  {'field': field, 'format': totlvl_row_format, 'formatperc': totlvl_row_formatperc}

                    field_dictlist.append(field_dict)
                    field_dictlist_index += 1

        if logging_on:
            logger.debug('    field_dictlist: ')
            for field_dict in field_dictlist:
                logger.debug('    > : ' + str(field_dict))

        return field_dictlist
    # end of get_field_dictlistt

    if examyear_list and result_dict:
        examyear_list_len = len(examyear_list)

# --- create header_list (result, examyear, gender)
        header_list =  ('hdr1', 'hdr2', 'hdr3') if examyear_list_len > 1 else ('hdr1', 'hdr3')
        field_dictlist = get_field_dictlist()

# ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        # PR2024-02-27 debug: special characters in schoolname give gunicorn error. use abbrev instead of schoolname
        # was: school_name = ' '.join((sel_school.base.code, sel_school.name))
        school_name = ' '.join((sel_school.base.code, sel_school.abbrev))

        school_name = ' '.join((sel_school.base.code, sel_school.abbrev)) if is_role_school else ''

        if examyear_list_len == 1:
            examyear_range = str(examyear_list[0])
        else:
            examyear_range = ' - '.join((str(examyear_list[0]), str(examyear_list[examyear_list_len - 1])))

        title = ' '.join((gettext('Exam results'), str(school_name), examyear_range, 'dd', today_dte.isoformat()))
        file_name = title + ".xlsx"

        ws_name_num = gettext('Results')
        ws_name_perc = gettext('Percentage')

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

# - create dict with formats, used in this workbook
        formats = get_formats(book)
        for mode in ('num', 'perc'):

            worksheet_name = ws_name_perc if mode == 'perc' else ws_name_num

# +++++ create worksheet +++++
            sheet = book.add_worksheet(worksheet_name)
            sheet.hide_gridlines(2)  # 2 = Hide screen and printed gridlines
            sheet.hide_zero()
            sheet.freeze_panes(7, 2)

            write_resultlist(sheet, mode, examyear_range, depbase_dict, lvlbase_dict, schoolbase_dict, result_dict,
                                    field_dictlist, header_list, formats, ws_name_num, ws_name_perc, user_lang)

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
# - end of create_result_overview_multiple_examyears_xlsx


#@@@@@@@@@@@@@@@@@@@@@@@@

def create_grade_avg_overview_xlsx(examyear_list, sel_school, is_role_school,
                                   depbase_dictlist, lvlbase_dictlist, schoolbase_dictlist, subjbase_dictlist,
                                   has_gender_x, show_gender, grades_dict, user_lang):

    # PR2022-06-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_grade_avg_overview_xlsx -----')

    response = None

    def get_avg_field_dictlist():
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('----- get_avg_field_dictlist -----')

    # create gender_list
        # only add 'x' when there are students with gender 'x'
        gender_list = []
        if show_gender:
            gender_list.extend(('m', 'v'))
            if has_gender_x:
                gender_list.append('x')
        gender_list.append('t')

        gender_captions = {
            'm': 'M',
            'v': str(pgettext_lazy('female','F')),
            'x': '-',
            't': 'T'
        }

    # create grade header _list
        grade_list = ('count', 'sesr', 'pece', 'final')
        gradelist_length = len(grade_list)

        grade_captions = {
            'count': 't',
            'sesr': 's',
            'pece': 'c',
            'final': str(pgettext_lazy('final grade','f'))
        }

    # first 2 columns are schoolcode and schoolname
        field_dictlist = []
        field_dictlist_index = 0
        field_dictlist.append(
            {'width': 8,
             'hdr1': {'caption': '', 'format': 'hdr_tableheader_alignleft'},
             'hdr2': {'format': 'hdr_subtotal_alignleft'},
             'hdr3': {'format': 'hdr_subsubtotal_alignleft'},
             'hdr4': {'format': 'hdr_subsubtotal_alignleft'},
             'hdrdep': {'format': 'hdr_subtotal_alignleft'},
             'hdrlvl': {'format': 'hdr_subsubtotal_alignleft'},
             'detail': {'field': 'sb_code', 'format': 'row_value_alignleft'},
             'totgrd': {'format': 'hdr_grandtotal_alignleft'},
             'totdep': {'format': 'hdr_subtotal_alignleft'},
             'totlvl': {'format': 'hdr_subsubtotal_alignleft'},
            }
        )
        field_dictlist_index += 1
        field_dictlist.append(
            {'width': 36,
            'hdr1': {'caption': gettext('School'), 'format': 'hdr_tableheader_alignleft'},
            'hdr2': {'caption': '', 'format': 'hdr_subtotal_alignleft'},
            'hdr3': {'caption': '', 'format': 'hdr_subsubtotal_alignleft'},
            'hdr4': {'caption': '', 'format': 'hdr_subsubtotal_alignleft'},
            'hdrdep': {'caption': '', 'format': 'hdr_subtotal_alignleft'},
            'hdrlvl': {'caption': '', 'format': 'hdr_subsubtotal_alignleft'},
            'detail': {'field': 'sch_name', 'format': 'row_value_alignleft'},
            'totgrd': {'field': 'grd_code','format': 'hdr_grandtotal_alignleft'},
            'totdep': {'field': 'dep_code','format': 'hdr_subtotal_alignleft'},
            'totlvl': {'field': 'lvl_code','format': 'hdr_subsubtotal_alignleft'},
            }
        )
        field_dictlist_index += 1
    # merge field is the number of columns to span the header
        genderlist_length = len(gender_list)
        subject_merge = examyear_list_len * genderlist_length * gradelist_length
        examyear_merge =  genderlist_length * gradelist_length
        gender_merge = gradelist_length

# - Loop trough subject list
        for subject_index, subjbase_dict in enumerate(subjbase_dictlist):
            #  subjbase_dict: = {'subjbase_id': subjbase_id, 'subjbase_code': row['subjbase_code'], 'subj_name_nl': row['subj_name_nl']}
            subjbase_id = subjbase_dict['subjbase_id']
            subject_caption = subjbase_dict['subj_name_nl']

    # - Loop trough exam years
            for examyear_index, examyear_code in enumerate(examyear_list):
                examyear_caption = str(examyear_code)
    # - Loop trough gender
                # gender_list = ['m', 'v', 't'] or ['m', 'v', 'x', 't']
                # total index is the last column 't'
                # save the numer of rows that must be added to the right in t_col_add
                # t_col is the index of the total column

                for gender_index, gender_code in enumerate(gender_list):
                    gender_caption = gender_captions[gender_code]
                    for grade_index, grade_code in enumerate(grade_list):
                        grade_caption = grade_captions[grade_code]
                        t_col = field_dictlist_index - grade_index
                        field = ''.join((examyear_caption, '-', str(subject_index), '_', gender_code, '_', grade_code))
                        field_dict = {
                            'width': 4.6,
                            't_col': t_col,
                            'examyear_code': examyear_code,
                            'subjbase_id': subjbase_id,
                            'gender_code': gender_code,
                            'grade_code': grade_code
                        }
                        # onlye add hdr when index = 0
                        if not examyear_index and not gender_index and not grade_index:
                            field_dict['hdr1'] = {'caption': subject_caption, 'merge': subject_merge, 'format': 'hdr_tableheader_borderleft'}
                            field_dict['hdrdep'] = {'merge': subject_merge, 'format': 'hdr_subtotal'}
                        if not gender_index and not grade_index:
                            field_dict['hdr2'] = {'caption': examyear_caption, 'merge': examyear_merge, 'format': 'hdr_subtotal_borderleft'}
                        if not grade_index:
                            field_dict['hdr3'] = {'caption': gender_caption, 'merge': gender_merge, 'format': 'hdr_subsubtotal_borderleft'}
                            field_dict['hdrlvl'] = {'merge': gender_merge, 'format': 'hdr_subsubtotal_borderleft'}
                        field_dict['hdr4'] = {'caption': grade_caption, 'format': 'hdr_grade_borderleft'}

                        detail_row_format = 'row_value_borderleft' if not grade_index else 'row_value_borderleft_gray'
                        detail_row_format_avg = 'row_avg_borderleft' if not grade_index else 'row_avg_borderleft_gray'
                        field_dict['detail'] =  {'field': field, 'format': detail_row_format, 'format_avg': detail_row_format_avg}

                        totgrd_row_format = 'hdr_grandtotal_borderleft' if not grade_index else 'hdr_grandtotal_borderleft_gray'
                        field_dict['totgrd'] =  {'field': field, 'format': totgrd_row_format}

                        totdep_row_format = 'hdr_subtotal_borderleft' if not grade_index else 'hdr_subtotal_borderleft_gray'
                        totdep_row_format_avg = 'row_avg_borderleft' if not grade_index else 'row_avg_borderleft_gray'
                        field_dict['totdep'] =  {'field': field, 'format': totdep_row_format}

                        totlvl_row_format = 'hdr_subsubtotal_borderleft' if not grade_index else 'hdr_subsubtotal_borderleft_gray'
                        totlvl_row_format_avg = 'hdr_subsubtotal_borderleft' if not grade_index else 'ftr_subsubtotal_avg_borderleft_gray'
                        field_dict['totlvl'] =  {'field': field, 'format': totlvl_row_format, 'format_avg': totlvl_row_format_avg}

                        field_dictlist.append(field_dict)
                        field_dictlist_index += 1

        if logging_on:
            logger.debug('    field_dictlist: ')
            for field_dict in field_dictlist:
                logger.debug('    > : ' + str(field_dict))
            """
            {'width': 4.6, 't_col': 4, 
            'hdr3': {'caption': '-', 'format': 'hdr_tableheader_borderleft'}, 
            'detail': {'field': '2024-116_x', 'format': 'row_value', 'formatperc': 'row_perc'}, 
            'totgrd': {'field': '2024-116_x', 'format': 'hdr_grandtotal', 'formatperc': 'hdr_grandtotal_percentage'}, 
            'totdep': {'field': '2024-116_x', 'format': 'hdr_subtotal', 'formatperc': 'hdr_subtotal_percentage'}, 
            'totlvl': {'field': '2024-116_x', 'format': 'hdr_subsubtotal', 'formatperc': 'hdr_subsubtotal_percentage'}}
            """

        return field_dictlist
    # end of get_avg_field_dictlist

    if examyear_list and grades_dict:
        examyear_list_len = len(examyear_list)

# --- create header_list (subject, examyear, gender, avg_grade)
        header_list =  ['hdr1']
        if examyear_list_len > 1:
            header_list.append('hdr2')
        if show_gender:
            header_list.append('hdr3')
        header_list.append('hdr4')

        field_dictlist = get_avg_field_dictlist()

        ws_name_tot = gettext('Total')
        ws_name_avg = gettext('average').capitalize()

# ---  create file Name and worksheet Name
        today_dte = af.get_today_dateobj()
        # PR2024-02-27 debug: special characters in schoolname give gunicorn error. use abbrev instead of schoolname
        # was: school_name = ' '.join((sel_school.base.code, sel_school.name))

        no_special_char_found = af.has_no_special_char(sel_school.name)
        if logging_on:
            logger.debug('no_special_char_found: ' + str(no_special_char_found) + ' ' + str(sel_school.name))

        school_name = ' '.join((sel_school.base.code, sel_school.abbrev)) if is_role_school else ''

        if examyear_list_len == 1:
            examyear_range = str(examyear_list[0])
        else:
            examyear_range = ' - '.join((str(examyear_list[0]), str(examyear_list[examyear_list_len - 1])))

        title = ' '.join((gettext('Grade average'), str(school_name), examyear_range, 'dd', today_dte.isoformat()))
        file_name = title + ".xlsx"

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

# - create dict with formats, used in this workbook
        formats = get_formats(book)
        for mode in ('avg', 'tot'):

            worksheet_name = ws_name_tot if mode == 'tot' else ws_name_avg

# +++++ create worksheet +++++
            sheet = book.add_worksheet(worksheet_name)
            sheet.hide_gridlines(2)  # 2 = Hide screen and printed gridlines
            sheet.hide_zero()
            sheet.freeze_panes(8, 2)

            write_grade_avg_list(sheet, mode, ws_name_tot, examyear_range, depbase_dictlist, lvlbase_dictlist, schoolbase_dictlist, subjbase_dictlist, grades_dict,
                                    field_dictlist, header_list, formats, user_lang)

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
# - end of create_grade_avg_overview_xlsx


#@@@@@@@@@@@@@@@@@

def write_resultlist(sheet, mode, examyear_range, depbase_dictlist, level_dictlist, schoolbase_dictlist,
                             result_dict, field_dictlist, header_list, formats, ws_name_num, ws_name_perc, user_lang):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- write_resultlist -----')
        logger.debug('    field_dictlist len: ' + str(len(field_dictlist)))

    def write_detail_row(sheet, mode, row_index, formats, schoolbase_dict, sbase_result_dict, ws_name_num, ws_name_perc):
        logging_on = False  #s.LOGGING_ON
        if logging_on:
            logger.debug(' -----  write_detail_row  -----')
            logger.debug('    schoolbase_dict: ' + str(schoolbase_dict))
            logger.debug('    sbase_result_dict: ' + str(sbase_result_dict))
        """
        schoolbase_dict: {'sb_id': 2, 'sb_code': 'CUR01', 'sch_name': 'Ancilla Domini Vsbo 2024'}
        sbase_result_dict: {'sb_code': 'CUR01', 2024: {'c_m': 7, 'c_v': 20, 'c_x': 0, 'c_t': 27, 'p_m': 3, 'p_v': 10, 'p_x': 0, 'p_t': 13, 'f_m': 3, 'f_v': 6, 'f_x': 0, 'f_t': 9, 'r_m': 1, 'r_v': 3, 'r_x': 0, 'r_t': 4, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 1, 'n_x': 0, 'n_t': 1}, 2023: {'c_m': 9, 'c_v': 24, 'c_x': 0, 'c_t': 33, 'p_m': 6, 'p_v': 19, 'p_x': 0, 'p_t': 25, 'f_m': 3, 'f_v': 5, 'f_x': 0, 'f_t': 8, 'r_m': 0, 'r_v': 0, 'r_x': 0, 'r_t': 0, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 0, 'n_x': 0, 'n_t': 0}, 2022: {'c_m': 11, 'c_v': 19, 'c_x': 0, 'c_t': 30, 'p_m': 10, 'p_v': 16, 'p_x': 0, 'p_t': 26, 'f_m': 1, 'f_v': 3, 'f_x': 0, 'f_t': 4, 'r_m': 0, 'r_v': 0, 'r_x': 0, 'r_t': 0, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 0, 'n_x': 0, 'n_t': 0}}
        det_field_dict: {'field': 'c_2022_v', 'format': 'test'}
        """

        for col_index, field_dict in enumerate(field_dictlist):

            if logging_on:
                logger.debug('    field_dict: ' + str(field_dict))

            if 'detail' in field_dict:
                det_dict = field_dict['detail']

                if logging_on:
                    logger.debug('    det_dict: ' + str(det_dict))
                """
                 'detail': {'field': '2022-c_m', 'format': 'row_value_borderleft', 'formatperc': 'row_perc_borderleft'}, 
                """
                format_key = det_dict['format'] if 'format' in det_dict else 'row_value'
                field_format = formats[format_key] if format_key in formats else ''

                format_key_perc = det_dict['formatperc'] if 'formatperc' in det_dict else 'row_value'
                field_format_perc = formats[format_key_perc] if format_key_perc in formats else ''

                field_name = det_dict['field'] if 'field' in det_dict else ''

                if field_name in ('sb_code', 'sch_name') and field_name in schoolbase_dict:
                    value = schoolbase_dict[field_name]
                    sheet.write(row_index, col_index, value, field_format)
                else:
                    value = None
                    field_arr = field_name.split('-')
                    examyear = int(field_arr[0])
                    result_field = field_arr[1]
                    if examyear in sbase_result_dict:
                        examyear_result_dict = sbase_result_dict[examyear]
                        if examyear_result_dict:
                            if result_field in examyear_result_dict:
                                value = examyear_result_dict[result_field]
                    if logging_on:
                        logger.debug('    value: ' + str(value))

                    # for mode in ('num', 'perc'):
                    t_col = field_dict['t_col']
                    if mode != 'perc' or col_index == t_col:
                        sheet.write(row_index, col_index, value, field_format)
                    else:
                        formula = ''
                        this_cell_ref = subj_view.xl_rowcol_to_cell(row_index, col_index)
                        if 't_col' in field_dict:
                            t_col = field_dict['t_col']

                            if logging_on:
                                logger.debug('    ws_name_num: ' + str(ws_name_num) + ' ws_name_perc: ' + str(ws_name_perc))
                                logger.debug('    t_col: ' + str(t_col))
                                logger.debug('    det_dict: ' + str(det_dict))

                            count_ref = subj_view.xl_rowcol_to_cell(row_index, t_col)
                            sum_cell_ref = this_cell_ref
                            if logging_on:
                                logger.debug('    count_ref: ' + str(count_ref))
                                logger.debug('    sum_cell_ref: ' + str(sum_cell_ref))
                                logger.debug('    this_cell_ref: ' + str(this_cell_ref))

                            # check for None and 0 values
                            # =IF(OR(ISBLANK($D39);$D39=0);0;G39/$D39)
                            # =IF(OR(ISBLANK(Uitslagen!$D11);Uitslagen!$D11=0);0;Uitslagen!F11/Uitslagen!$D11)
                            formula = ''.join(("IF(OR(ISBLANK(", ws_name_num, "!$", count_ref,
                                               "),", ws_name_num, "!$", count_ref,
                                               "=0),0,", ws_name_num, "!", sum_cell_ref,
                                               "/", ws_name_num, "!$", count_ref, ")"
                                               ))

                            if logging_on:
                                logger.debug('    formula: ' + str(formula))
                        sheet.write_formula(this_cell_ref, formula, field_format_perc)
                #write_value_cell(sheet, i, row_index, caption, format_value, format_alignleft, format_value_bl)

            #write_percentage_cell(sheet, i, row_index, format_perc, format_alignleft, format_perc_bl, code, name)
    # - end of write_detail_row

    def write_total_row(sheet, mode, row_index, first_total_row_index, field_dict_key, code=None):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' -----  write_total_row  -----')
            logger.debug('    field_dict_key: ' + str(field_dict_key))
            logger.debug('    code: ' + str(code))

        for col_index, field_dict in enumerate(field_dictlist):

            fld_dict = field_dict.get(field_dict_key)
            if logging_on:
                logger.debug('     fld_dict: ' + str(fld_dict))
                logger.debug('     field_dict: ' + str(field_dict))
            """
            fld_dict: {'field': '2024-r_m', 'format': 'hdr_subsubtotal_borderleft', 'formatperc': 'hdr_subsubtotal_perc_borderleft'}
            field_dict: {'width': 4.6, 't_col': 2, 
                        'hdr1': {'caption': 'Herexamen', 'merge': 4, 'format': 'hdr_tableheader_borderleft'}, 
                        'hdr2': {'caption': '2024', 'merge': 4, 'format': 'hdr_tableheader_borderleft'}, 
                        'hdr3': {'caption': 'M', 'format': 'hdr_tableheader_borderleft'}, 
                        'hdrdep': {'merge': 4, 'format': 'hdr_subtotal'}, 
                        'hdrlvl': {'merge': 4, 'format': 'hdr_subsubtotal'}, 
                        'detail': {'field': '2024-r_m', 'format': 'row_value_borderleft', 'formatperc': 'row_perc_borderleft'}, 
                        'totgrd': {'field': '2024-r_m', 'format': 'hdr_grandtotal_borderleft', 'formatperc': 'hdr_grandtotal_perc_borderleft'}, 
                        'totdep': {'field': '2024-r_m', 'format': 'hdr_subtotal_borderleft', 'formatperc': 'hdr_subtotal_perc_borderleft'}, 
                        'totlvl': {'field': '2024-r_m', 'format': 'hdr_subsubtotal_borderleft', 'formatperc': 'hdr_subsubtotal_perc_borderleft'}}
            """

            if fld_dict:
                format_key = fld_dict['format'] if 'format' in fld_dict else 'row_value'
                field_format = formats[format_key] if format_key in formats else ''
                if logging_on:
                    logger.debug('     format_key: ' + str(format_key))

                if col_index == 1:
                    name = gettext('TOTAL')
                    if code:
                        name += '  ' + code.upper()

                    name_str = name if name else ''
                    sheet.write(row_index, col_index, name_str, field_format)
                else:

                    this_cell_ref = subj_view.xl_rowcol_to_cell(row_index, col_index)
                    t_col = field_dict.get('t_col')

                    if mode != 'perc' or t_col is None or col_index == t_col:

                        upper_cell_ref = subj_view.xl_rowcol_to_cell(first_total_row_index, col_index)
                        lower_cell_ref = subj_view.xl_rowcol_to_cell(row_index - 1, col_index)

                        formula = ''.join(('SUBTOTAL(9,', upper_cell_ref, ':', lower_cell_ref, ')'))

                        sheet.write_formula(this_cell_ref, formula, field_format)

                    else:
                        if logging_on:
                            logger.debug('    t_col: ' + str(t_col))

                        format_key = fld_dict['format'] if 'format' in fld_dict else 'row_value'
                        field_format = formats[format_key] if format_key in formats else ''

                        format_key_perc = fld_dict['formatperc'] if 'formatperc' in fld_dict else 'row_value'
                        field_format_perc = formats[format_key_perc] if format_key_perc in formats else ''

                        count_ref = subj_view.xl_rowcol_to_cell(row_index, t_col)
                        sum_cell_ref = this_cell_ref
                        if logging_on:
                            logger.debug('    count_ref: ' + str(count_ref))
                            logger.debug('    sum_cell_ref: ' + str(sum_cell_ref))
                            logger.debug('    this_cell_ref: ' + str(this_cell_ref))

                        # check for None and 0 values
                        # =IF(OR(ISBLANK(Uitslagen!$C11),Uitslagen!$C11=0),0,Uitslagen!G11/Uitslagen!$C11)
                        formula = ''.join(("IF(OR(ISBLANK(", ws_name_num, "!$", count_ref,
                                           "),", ws_name_num, "!$", count_ref,
                                           "=0),0,", ws_name_num, "!", sum_cell_ref,
                                           "/", ws_name_num, "!$", count_ref, ")"
                                           ))

                        if logging_on:
                            logger.debug('    formula: ' + str(formula))
                        sheet.write_formula(this_cell_ref, formula, field_format_perc)

    # - end of write_total_row

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
    for i, field_dict in enumerate(field_dictlist):
        sheet.set_column(i, i, field_dict['width'])

    row_index = 0

# --- title row
    title = ' '.join((gettext('Exam results'), examyear_range))
    sheet.write(row_index, 1, title, formats['bold_format'])
    row_index += 1


    if len(schoolbase_dictlist) == 1:
        schoolbase_dict = schoolbase_dictlist[0]
        schoolname = schoolbase_dict.get('sch_name')
        sheet.write(row_index, 1, schoolname, formats['bold_format_blue'])
        row_index += 1

    today_dte = af.get_today_dateobj()
    today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
    title = ''.join((gettext('Date'), ': ', today_formatted))
    sheet.write(row_index, 1, title, formats['bold_format'])
    row_index += 2

    write_header01_row(sheet, field_dictlist, formats, header_list, row_index)

# --- write_column_header and write_column_subheader
    # write_result_header_row(sheet, row_index, formats)
    row_index += 2
    grandtotal_first_row_index = row_index

# +++++++++++++++++++++ loop through departments  ++++++++++++++++++++++++++++
    for dep_dict in depbase_dictlist:
        # fields are: depbase_id, depbase_code, dep_name, dep_level_req
        """
        depbase_dict: {1: {'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_seq': 1, 'dep_lvl_req': True}}
        """
        db_id = dep_dict['db_id']
        depbase_code = dep_dict['db_code']
        dep_name = dep_dict['dep_name']
        dep_lvl_req = dep_dict['dep_lvl_req']

        if logging_on:
            logger.debug('    dep_dict: ' + str(dep_dict))

        # dep_dict: {'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_seq': 1, 'dep_lvl_req': True}

# lookup dep in result_dict_per_school
        if db_id in result_dict:
            depbase_result_dict = result_dict[db_id]

    # ---  department title row
            row_index += 2
            write_header_dep_lvl_row(sheet, field_dictlist, formats, 'hdrdep', dep_name, row_index)

            depbase_first_row_index = row_index

    # ++++++++++++ loop through levels  ++++++++++++++++++++++++++++
            for lvlbase_dict in level_dictlist:
                # fields are lvlbase_id, lvl_code, lvl_name",

                lvlbase_pk = lvlbase_dict.get('lvlbase_id') or 0
                lvl_code = lvlbase_dict.get('lvl_code') or '---'
                lvl_name = lvlbase_dict.get('lvl_name') or str(_('Learning path is not entered'))

     # lookup level in depbase_result_dict
                if lvlbase_pk in depbase_result_dict:
                    lvlbase_result_dict = depbase_result_dict.get(lvlbase_pk)

        # ---  level title row
                    # skip when Havo / Vwo
                    if dep_lvl_req:
                        row_index += 2
                        write_header_dep_lvl_row(sheet, field_dictlist, formats, 'hdrlvl', lvl_name, row_index)

                    lvlbase_first_row_index = row_index

    # ++++++++++++ loop through schools  ++++++++++++++++++++++++++++
                    for schoolbase_dict in schoolbase_dictlist:
                        if logging_on:
                            logger.debug('    schoolbase_dict: ' + str(schoolbase_dict))
                        """
                        schoolbase_dict: {'sb_id': 2, 'sb_code': 'CUR01', 'sch_name': 'Ancilla Domini Vsbo 2024'}
                        """
                        schoolbase_pk = schoolbase_dict.get('sb_id')
                        if logging_on:
                            logger.debug('    schoolbase_pk: ' + str(schoolbase_pk))
                            logger.debug('    lvlbase_result_dict: ' + str(lvlbase_result_dict))

                        if schoolbase_pk in lvlbase_result_dict:
                            # PR2022-06-17 defaultrole = school is filtered out in create_results_per_school_rows
                            # was: defaultrole = schoolbase_dict.get('defaultrole', 0)
                            row_index += 1

                            sbase_result_dict = lvlbase_result_dict.get(schoolbase_pk)
                            if logging_on:
                                logger.debug('    sbase_result_dict: ' + str(sbase_result_dict))

                            if lvlbase_first_row_index is None:
                                lvlbase_first_row_index = row_index

                            if logging_on:
                                logger.debug(    'sbase_result_dict: ' + str(sbase_result_dict))

                            write_detail_row(sheet, mode, row_index, formats, schoolbase_dict, sbase_result_dict, ws_name_num, ws_name_perc)

    # ++++++++++++ end of loop through schools  ++++++++++++++++++++++++++++
                    if dep_lvl_req:
                        # add 1 extra row t subtotal range, to prevent leaving out last row in calculation when manually added extra rows
                        if lvlbase_first_row_index:
                            row_index += 1
                            if logging_on:
                                logger.debug('    end of loop through schools row_index: ' + str(row_index))
                            write_total_row(sheet, mode, row_index, lvlbase_first_row_index, 'totlvl', lvl_code)

            #write_total_row(sheet, row_index, first_total_row_index, field_dict_key, code=None, name=None):

            # --- write departent total row
            if depbase_first_row_index:
                row_index += 2 if dep_lvl_req else 1
                if logging_on:
                    logger.debug('write departent total row: ' + str(row_index))
                write_total_row(sheet, mode, row_index, depbase_first_row_index, 'totdep', depbase_code)

# --- write grand total row
    row_index += 2
    write_total_row(sheet, mode, row_index, grandtotal_first_row_index, 'totgrd')

# - end of write_resultlist


#@@@@@@@@@@@@@@@@@

def write_grade_avg_list(sheet, mode, ws_name_tot, examyear_range, depbase_dictlist, level_dictlist, schoolbase_dictlist, subjbase_dictlist,
                             grades_dict, field_dictlist, header_list, formats, user_lang):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- write_grade_avg_list -----')
        logger.debug('    field_dictlist len: ' + str(len(field_dictlist)))

    def write_avg_detail_row(sheet, mode, row_index, formats, schoolbase_dict, schoolbase_grade_dict):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' -----  write_detail_row  -----')
            logger.debug('    mode: ' + str(mode))
            #logger.debug('    schoolbase_grade_dict: ' + str(schoolbase_grade_dict))
        """
        schoolbase_dict: {'sb_id': 2, 'sb_code': 'CUR01', 'sch_name': 'Ancilla Domini Vsbo 2024'}
        sbase_result_dict: {'sb_code': 'CUR01', 2024: {'c_m': 7, 'c_v': 20, 'c_x': 0, 'c_t': 27, 'p_m': 3, 'p_v': 10, 'p_x': 0, 'p_t': 13, 'f_m': 3, 'f_v': 6, 'f_x': 0, 'f_t': 9, 'r_m': 1, 'r_v': 3, 'r_x': 0, 'r_t': 4, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 1, 'n_x': 0, 'n_t': 1}, 2023: {'c_m': 9, 'c_v': 24, 'c_x': 0, 'c_t': 33, 'p_m': 6, 'p_v': 19, 'p_x': 0, 'p_t': 25, 'f_m': 3, 'f_v': 5, 'f_x': 0, 'f_t': 8, 'r_m': 0, 'r_v': 0, 'r_x': 0, 'r_t': 0, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 0, 'n_x': 0, 'n_t': 0}, 2022: {'c_m': 11, 'c_v': 19, 'c_x': 0, 'c_t': 30, 'p_m': 10, 'p_v': 16, 'p_x': 0, 'p_t': 26, 'f_m': 1, 'f_v': 3, 'f_x': 0, 'f_t': 4, 'r_m': 0, 'r_v': 0, 'r_x': 0, 'r_t': 0, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 0, 'n_x': 0, 'n_t': 0}}
        det_field_dict: {'field': 'c_2022_v', 'format': 'test'}
        
        grades_dict: 
            {1: {'db_code': 'Vsbo', 'count': 2224, 'sesr': Decimal('13316.4'), 'pece': Decimal('7675.2'), 'final': Decimal('12995'), 
                6: {'lvl_code': 'PBL', 'count': 590, 'sesr': Decimal('3415.6'), 'pece': Decimal('2018.2'), 'final': Decimal('3425'), 
                    2: {'sb_code': 'CUR01', 'count': 590, 'sesr': Decimal('3415.6'), 'pece': Decimal('2018.2'), 'final': Decimal('3425'), 
                        133: {'subjbase_code': 'ac', 'count': 28, 'sesr': Decimal('162.2'), 'pece': Decimal('156.8'), 'final': Decimal('159'), 
                            2024: {'t': {'count': 15, 'sesr': Decimal('85.2'), 'pece': Decimal('80.2'), 'final': Decimal('83')}, 
                                'm': {'count': 5, 'sesr': Decimal('28.7'), 'pece': Decimal('27.5'), 'final': Decimal('28')}, 
                                'v': {'count': 10, 'sesr': Decimal('56.5'), 'pece': Decimal('52.7'), 'final': Decimal('55')}}, 
                            2023: {'t': {'count': 13, 'sesr': Decimal('77.0'), 'pece': Decimal('76.6'), 'final': Decimal('76')},

        field_dict: {'width': 3, 't_col': 2, 'examyear_code': 2023, 'subjbase_id': 133, 'gender_code': 'm', 'grade_code': 't', 
                    'hdr1': {'caption': 'Administratie & Commercie', 'merge': 32, 'format': 'hdr_tableheader_borderleft'}, 
                    'hdrdep': {'merge': 32, 'format': 'hdr_subtotal'}, 
                    'hdr2': {'caption': '2023', 'merge': 16, 'format': 'hdr_subtotal_borderleft'}, 
                    'hdr3': {'caption': 'M', 'merge': 4, 'format': 'hdr_subsubtotal_borderleft'}, 
                    'hdrlvl': {'merge': 4, 'format': 'hdr_subsubtotal_borderleft'}, 
                    'hdr4': {'caption': 't', 'format': 'hdr_grade_borderleft'}, 
                    'detail': {'field': '2023-0_m_t', 
                                'format': 'row_value_borderleft'}, 
                                'totgrd': {'field': '2023-0_m_t', 'format': 'hdr_grandtotal_borderleft'}, 
                                'totdep': {'field': '2023-0_m_t', 'format': 'hdr_subtotal_borderleft'}, 
                                'totlvl': {'field': '2023-0_m_t', 'format': 'hdr_subsubtotal_borderleft'}}
        """

        for col_index, field_dict in enumerate(field_dictlist):

            if logging_on:
                logger.debug('    col_index: ' + str(col_index))
                logger.debug('    field_dict: ' + str(field_dict))

            if 'detail' in field_dict:
                det_dict = field_dict['detail']
                t_col = field_dict.get('t_col')
                if logging_on:
                    logger.debug('    det_dict: ' + str(det_dict))

                if logging_on:
                    logger.debug('    det_dict: ' + str(det_dict))
                """
                 'detail': {'field': '2022-c_m', 'format': 'row_value_borderleft', 'formatperc': 'row_perc_borderleft'}, 
                """

                this_cell_ref = subj_view.xl_rowcol_to_cell(row_index, col_index)
                sum_cell_ref = '!'.join((ws_name_tot, subj_view.xl_rowcol_to_cell(row_index, col_index, True, True)))


                format_key = det_dict['format'] if 'format' in det_dict else 'row_value'
                field_format = formats[format_key] if format_key in formats else ''

                format_key_avg = det_dict['format_avg'] if 'format_avg' in det_dict else 'row_value'
                field_format_avg = formats[format_key_avg] if format_key_avg in formats else ''

                field_name = det_dict['field'] if 'field' in det_dict else ''

                if logging_on:
                    logger.debug('    this_cell_ref: ' + str(this_cell_ref))
                    logger.debug('    sum_cell_ref: ' + str(sum_cell_ref))
                    logger.debug('    format_key_avg: ' + str(format_key_avg))

                if field_name in ('sb_code', 'sch_name') and field_name in schoolbase_dict:
                    value = schoolbase_dict[field_name]
                    sheet.write(row_index, col_index, value, field_format)

                elif mode == 'tot':
                    value = None
                    subjbase_id = field_dict.get('subjbase_id')
                    if subjbase_id in schoolbase_grade_dict:
                        subjbase_grade_dict = schoolbase_grade_dict[subjbase_id]
                        examyear_code = field_dict.get('examyear_code')
                        if examyear_code in subjbase_grade_dict:
                            examyear_grade_dict = subjbase_grade_dict[examyear_code]
                            if examyear_grade_dict:
                                gender_code = field_dict.get('gender_code')
                                if gender_code in examyear_grade_dict:
                                    gender_grade_dict = examyear_grade_dict[gender_code]
                                    grade_code = field_dict.get('grade_code')
                                    if grade_code in gender_grade_dict:
                                        value = gender_grade_dict[grade_code]

                    sheet.write(row_index, col_index, value, field_format)

                elif t_col == col_index:
                    # check for None and 0 values
                    # =IF(OR(ISBLANK($D39);$D39=0);0;G39/$D39)
                    # =IF(OR(ISBLANK(Uitslagen!$D11);Uitslagen!$D11=0);0;Uitslagen!F11/Uitslagen!$D11)
                    formula = ''.join(("=", sum_cell_ref))

                    if logging_on:
                        logger.debug('    formula: ' + str(formula))
                    sheet.write_formula(this_cell_ref, formula, field_format)
                else:
                    formula = ''
                    if t_col:
                        count_cell_ref = '!'.join(
                        (ws_name_tot, subj_view.xl_rowcol_to_cell(row_index, t_col, True, True)))

                        if logging_on:
                            logger.debug('    t_col: ' + str(t_col))
                            logger.debug('    det_dict: ' + str(det_dict))


                        # check for None and 0 values
                        # =IF(OR(ISBLANK($D39);$D39=0);0;G39/$D39)
                        # =IF(OR(ISBLANK(Uitslagen!$D11);Uitslagen!$D11=0);0;Uitslagen!F11/Uitslagen!$D11)
                        formula = ''.join(("=IF(OR(ISBLANK(", count_cell_ref, "),", count_cell_ref, "=0),0,",
                                           sum_cell_ref, "/", count_cell_ref, ")"
                                           ))

                    if logging_on:
                        logger.debug('    formula: ' + str(formula))

                    sheet.write_formula(this_cell_ref, formula, field_format_avg)
                #write_value_cell(sheet, i, row_index, caption, format_value, format_alignleft, format_value_bl)

            #write_percentage_cell(sheet, i, row_index, format_perc, format_alignleft, format_perc_bl, code, name)
    # - end of write_detail_row

    def write_avg_total_row(sheet, mode, row_index, first_total_row_index, field_dict_key, code=None):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' -----  write_total_row  -----')
            logger.debug('    field_dict_key: ' + str(field_dict_key))
            logger.debug('    code: ' + str(code))

        for col_index, field_dict in enumerate(field_dictlist):
            # values of field_dict_key are: 'totdep', 'totlvl', 'totgrd'
            fld_dict = field_dict.get(field_dict_key)
            if logging_on:
                logger.debug('     fld_dict: ' + str(fld_dict))
                logger.debug('     field_dict: ' + str(field_dict))
            """
            fld_dict: {'field': '2024-r_m', 'format': 'hdr_subsubtotal_borderleft', 'formatperc': 'hdr_subsubtotal_perc_borderleft'}
            field_dict: {'width': 4.6, 't_col': 2, 
                        'hdr1': {'caption': 'Herexamen', 'merge': 4, 'format': 'hdr_tableheader_borderleft'}, 
                        'hdr2': {'caption': '2024', 'merge': 4, 'format': 'hdr_tableheader_borderleft'}, 
                        'hdr3': {'caption': 'M', 'format': 'hdr_tableheader_borderleft'}, 
                        'hdrdep': {'merge': 4, 'format': 'hdr_subtotal'}, 
                        'hdrlvl': {'merge': 4, 'format': 'hdr_subsubtotal'}, 
                        'detail': {'field': '2024-r_m', 'format': 'row_value_borderleft', 'formatperc': 'row_perc_borderleft'}, 
                        'totgrd': {'field': '2024-r_m', 'format': 'hdr_grandtotal_borderleft', 'formatperc': 'hdr_grandtotal_perc_borderleft'}, 
                        'totdep': {'field': '2024-r_m', 'format': 'hdr_subtotal_borderleft', 'formatperc': 'hdr_subtotal_perc_borderleft'}, 
                        'totlvl': {'field': '2024-r_m', 'format': 'hdr_subsubtotal_borderleft', 'formatperc': 'hdr_subsubtotal_perc_borderleft'}}
            """

            if fld_dict:
                t_col = field_dict.get('t_col')

                format_key = fld_dict['format'] if 'format' in fld_dict else 'row_value'
                field_format = formats[format_key] if format_key in formats else ''

                format_key_avg = fld_dict['format_avg'] if 'format_avg' in fld_dict else format_key
                field_format_avg = formats[format_key_avg] if format_key_avg in formats else ''

                if logging_on:
                    logger.debug('     format_key: ' + str(format_key))
                    logger.debug('     format_key_avg: ' + str(format_key_avg))

                this_cell_ref = subj_view.xl_rowcol_to_cell(row_index, col_index)
                sum_cell_ref = '!'.join((ws_name_tot, subj_view.xl_rowcol_to_cell(row_index, col_index, True, True)))

                if col_index <= 1:
                    name = None
                    if col_index == 1:
                        name = gettext('Total').upper() if mode == 'tot' else gettext('Average grades').upper()
                        if code:
                            name += '  ' + code.upper()

                    name_str = name if name else ''

                    sheet.write(row_index, col_index, name_str, field_format)

                elif mode == 'tot':
                    format_key = fld_dict['format'] if 'format' in fld_dict else 'row_value'
                    field_format = formats[format_key] if format_key in formats else ''
                    if logging_on:
                        logger.debug('     format_key: ' + str(format_key))

                    upper_cell_ref = subj_view.xl_rowcol_to_cell(first_total_row_index, col_index)
                    lower_cell_ref = subj_view.xl_rowcol_to_cell(row_index - 1, col_index)

                    formula = ''.join(('SUBTOTAL(9,', upper_cell_ref, ':', lower_cell_ref, ')'))

                    sheet.write_formula(this_cell_ref, formula, field_format)

                elif t_col == col_index:
                    # check for None and 0 values
                    # =IF(OR(ISBLANK($D39);$D39=0);0;G39/$D39)
                    # =IF(OR(ISBLANK(Uitslagen!$D11);Uitslagen!$D11=0);0;Uitslagen!F11/Uitslagen!$D11)
                    formula = ''.join(("=", sum_cell_ref))

                    if logging_on:
                        logger.debug('    formula: ' + str(formula))
                    sheet.write_formula(this_cell_ref, formula, field_format)
                else:
                    formula = ''
                    if t_col:
                        count_cell_ref = '!'.join(
                            (ws_name_tot, subj_view.xl_rowcol_to_cell(row_index, t_col, True, True)))

                        if logging_on:
                            logger.debug('    t_col: ' + str(t_col))

                        # check for None and 0 values
                        # =IF(OR(ISBLANK($D39);$D39=0);0;G39/$D39)
                        # =IF(OR(ISBLANK(Uitslagen!$D11);Uitslagen!$D11=0);0;Uitslagen!F11/Uitslagen!$D11)
                        formula = ''.join(("=IF(OR(ISBLANK(", count_cell_ref, "),", count_cell_ref, "=0),0,",
                                           sum_cell_ref, "/", count_cell_ref, ")"
                                           ))

                    if logging_on:
                        logger.debug('    formula: ' + str(formula))

                    sheet.write_formula(this_cell_ref, formula, field_format_avg)
                # write_value_cell(sheet, i, row_index, caption, format_value, format_alignleft, format_value_bl)

    # - end of write_total_row

# --- set column width
    for i, field_dict in enumerate(field_dictlist):
        sheet.set_column(i, i, field_dict['width'])

    row_index = 0

# --- title row
    title = ' '.join((gettext('Grade average'), examyear_range))
    sheet.write(row_index, 1, title, formats['bold_format'])
    row_index += 1

    if len(schoolbase_dictlist) == 1:
        schoolbase_dict = schoolbase_dictlist[0]
        schoolname = schoolbase_dict.get('sch_name')
        sheet.write(row_index, 1, schoolname, formats['bold_format_blue'])
        row_index += 1

    today_dte = af.get_today_dateobj()
    today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
    title = ''.join((gettext('Date'), ': ', today_formatted))
    sheet.write(row_index, 1, title, formats['bold_format'])
    row_index += 2

    write_header01_row(sheet, field_dictlist, formats, header_list, row_index)

# --- write_column_header and write_column_subheader
    # write_result_header_row(sheet, row_index, formats)
    row_index += 3
    grandtotal_first_row_index = row_index + 2

# +++++++++++++++++++++ loop through departments  ++++++++++++++++++++++++++++
    for dep_dict in depbase_dictlist:
        # fields are: depbase_id, depbase_code, dep_name, dep_level_req
        """
        depbase_dict: {1: {'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_seq': 1, 'dep_lvl_req': True}}
        """
        depbase_pk = dep_dict['db_id']
        depbase_code = dep_dict['db_code']
        dep_name = dep_dict['dep_name']
        dep_lvl_req = dep_dict['dep_lvl_req']

        if logging_on:
            logger.debug('    dep_dict: ' + str(dep_dict))

        # dep_dict: {'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_seq': 1, 'dep_lvl_req': True}

# lookup dep in grade_dict_per_school
        if depbase_pk in grades_dict:
            depbase_grade_dict = grades_dict[depbase_pk]

    # ---  department title row
            row_index += 2
            write_header_dep_lvl_row(sheet, field_dictlist, formats, 'hdrdep', dep_name, row_index)

            depbase_first_row_index = row_index

    # ++++++++++++ loop through levels  ++++++++++++++++++++++++++++
            for lvlbase_dict in level_dictlist:
                # fields are lvlbase_id, lvl_code, lvl_name",

                lvlbase_pk = lvlbase_dict.get('lvlbase_id') or 0
                lvl_code = lvlbase_dict.get('lvl_code') or '---'
                lvl_name = lvlbase_dict.get('lvl_name') or str(_('Learning path is not entered'))

     # lookup level in depbase_grade_dict
                if lvlbase_pk in depbase_grade_dict:
                    lvlbase_grade_dict = depbase_grade_dict.get(lvlbase_pk)

        # ---  level title row
                    # skip when Havo / Vwo
                    if dep_lvl_req:
                        row_index += 2
                        write_header_dep_lvl_row(sheet, field_dictlist, formats, 'hdrlvl', lvl_name, row_index)

                    lvlbase_first_row_index = row_index

    # ++++++++++++ loop through schools  ++++++++++++++++++++++++++++
                    for schoolbase_dict in schoolbase_dictlist:
                        if logging_on:
                            logger.debug('    schoolbase_dict: ' + str(schoolbase_dict))
                        """
                        schoolbase_dict: {'sb_id': 2, 'sb_code': 'CUR01', 'sch_name': 'Ancilla Domini Vsbo 2024'}
                        """
                        schoolbase_pk = schoolbase_dict.get('sb_id')
                        if logging_on:
                            logger.debug('    schoolbase_pk: ' + str(schoolbase_pk))
                            #logger.debug('    lvlbase_grade_dict: ' + str(lvlbase_grade_dict))

                        if schoolbase_pk in lvlbase_grade_dict:
                            # PR2022-06-17 defaultrole = school is filtered out in create_results_per_school_rows
                            # was: defaultrole = schoolbase_dict.get('defaultrole', 0)
                            row_index += 1

                            schoolbase_grade_dict = lvlbase_grade_dict.get(schoolbase_pk)

                            if lvlbase_first_row_index is None:
                                lvlbase_first_row_index = row_index

                            write_avg_detail_row(sheet, mode, row_index, formats, schoolbase_dict, schoolbase_grade_dict)

    # ++++++++++++ end of loop through schools  ++++++++++++++++++++++++++++
                    if dep_lvl_req:
                        # add 1 extra row t subtotal range, to prevent leaving out last row in calculation when manually added extra rows
                        if lvlbase_first_row_index:
                            row_index += 1
                            if logging_on:
                                logger.debug('    end of loop through schools row_index: ' + str(row_index))
                            write_avg_total_row(sheet, mode, row_index, lvlbase_first_row_index, 'totlvl', lvl_code)

            #write_total_row(sheet, row_index, first_total_row_index, field_dict_key, code=None, name=None):

            # --- write departent total row
            if depbase_first_row_index:
                row_index += 2 if dep_lvl_req else 1
                if logging_on:
                    logger.debug('write departent total row: ' + str(row_index))
                write_avg_total_row(sheet, mode, row_index, depbase_first_row_index, 'totdep', depbase_code)

# --- write grand total row
    row_index += 2
    write_avg_total_row(sheet, mode, row_index, grandtotal_first_row_index, 'totgrd')

# - end of write_grade_avg_list

#/////////////////////////////////////////////////////////////////
def create_results_per_school_rows(country_pk, is_role_school, sel_schoolbase, max_examyear_code, min_examyear_code=None):
    # --- create rows of all students of this examyear range / school PR2024-06-19
    # - show only students that are not sdeleted and not tobedeleted ad not partial_exam
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_results_per_school_rows -----')

    # result_dict = {}
    result_rows = []
    error_dict = {} # PR2021-11-17 new way of err msg, like in TSA

    if country_pk and max_examyear_code:
        if min_examyear_code > max_examyear_code:
            min_examyear_code = None
        try:

            if logging_on:
                logger.debug(' examyear range: ' + str(min_examyear_code) + ' - ' + str(max_examyear_code))
                logger.debug('sel_schoolbase: ' + str(sel_schoolbase))

            subsql_list = ["SELECT st.id AS stud_id,",
                           "(LOWER(st.gender) = 'm')::INT AS m,",
                           "(LOWER(st.gender) = 'v')::INT AS v,",
                           #"(LOWER(st.gender) = 'x')::INT AS x,",
                           "((st.gender IS NULL) OR (LOWER(st.gender) != 'm' AND LOWER(st.gender) != 'v')  )::INT AS x,",

        # partal exam and tobedeleted are filtered out PR2023-06-14 debug: also st.deleted added
        # return withdrawn if result is withdrawn
                "CASE WHEN result = 4 THEN 4 ELSE",
        # return passed if any result is passed, also when reex_count > 0
                    "CASE WHEN st.ep01_result = 1 OR ep02_result = 1 OR result = 1 THEN 1 ELSE",
        # return failed if result is failed
                        "CASE WHEN (result = 2) THEN 2 ELSE",
        # return reex if reex_count > 0, not passed and not failed
        # return no result if not passed and not failed and no reex
                            "CASE WHEN st.reex_count > 0 OR st.reex03_count > 0 THEN 3 ELSE 0 END",
                        "END",
                    "END",
                "END AS resultcalc",
                "FROM students_student AS st",
                "WHERE NOT st.partial_exam",
                "AND NOT st.deleted AND NOT st.tobedeleted"
            ]
            sub_sql = ' '.join(subsql_list)
            #PR2024-06-21 debug: eror: '<' not supported between instances of 'NoneType' and 'int'
            # caused by sorted function
            # solved by givingdefault va\lrue when None
            sql_list = ["WITH subsql AS (" + sub_sql + ")",
                "SELECT ey.code AS ey_code, ",
                        "db.id AS db_id, db.code AS db_code, dep.name AS dep_name, dep.level_req AS dep_lvl_req,",
                        "COALESCE(dep.sequence, 999) AS dep_seq,",

                        "lvlbase.id AS lvlbase_id, lvlbase.code AS lvl_code, lvl.name AS lvl_name, ",
                        "COALESCE(lvl.sequence, 999) AS lvl_seq,",

                        "sb.id AS sb_id, sb.code as sb_code, sch.name as sch_name, ",

                "SUM(subsql.m) AS c_m,",
                "SUM(subsql.v) AS c_v,",
                "SUM(subsql.x) AS c_x,",
                "COUNT(*) AS c_t,",

                "SUM((subsql.resultcalc = 1 AND subsql.m = 1)::INT) AS p_m,",
                "SUM((subsql.resultcalc = 1 AND subsql.v = 1)::INT) AS p_v,",
                "SUM((subsql.resultcalc = 1 AND subsql.x = 1)::INT) AS p_x,",
                "SUM((subsql.resultcalc = 1)::INT) AS p_t,",

                "SUM((subsql.resultcalc = 2 AND subsql.m = 1)::INT) AS f_m,",
                "SUM((subsql.resultcalc = 2 AND subsql.v = 1)::INT) AS f_v,",
                "SUM((subsql.resultcalc = 2 AND subsql.x = 1)::INT) AS f_x,",
                "SUM((subsql.resultcalc = 2)::INT) AS f_t,",

                "SUM((subsql.resultcalc = 3 AND subsql.m = 1)::INT) AS r_m,",
                "SUM((subsql.resultcalc = 3 AND subsql.v = 1)::INT) AS r_v,",
                "SUM((subsql.resultcalc = 3 AND subsql.x = 1)::INT) AS r_x,",
                "SUM((subsql.resultcalc = 3)::INT) AS r_t,",

                "SUM((subsql.resultcalc = 4 AND subsql.m = 1)::INT) AS w_m,",
                "SUM((subsql.resultcalc = 4 AND subsql.v = 1)::INT) AS w_v,",
                "SUM((subsql.resultcalc = 4 AND subsql.x = 1)::INT) AS w_x,",
                "SUM((subsql.resultcalc = 4)::INT) AS w_t,",

                "SUM((subsql.resultcalc = 0 AND subsql.m = 1)::INT) AS n_m,",
                "SUM((subsql.resultcalc = 0 AND subsql.v = 1)::INT) AS n_v,",
                "SUM((subsql.resultcalc = 0 AND subsql.x = 1)::INT) AS n_x,",
                "SUM((subsql.resultcalc = 0)::INT) AS n_t",

                "FROM students_student AS st",
                "INNER JOIN subsql ON (subsql.stud_id = st.id)",

                "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
                "INNER JOIN schools_departmentbase AS db ON (db.id = dep.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
                "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                ''.join(("WHERE ey.country_id = ", str(country_pk), "::INT"))
            ]
            if min_examyear_code is None:
                sql_list.append(''.join(("AND ey.code = ", str(max_examyear_code), "::INT")))
            else:
                sql_list.append(''.join(("AND ey.code >= ", str(min_examyear_code), "::INT ",
                         "AND ey.code <= ", str(max_examyear_code), "::INT")))

            if is_role_school:
                sel_schoolbase_pk = sel_schoolbase.pk if sel_schoolbase else 0
                sql_list.append( ''.join(("AND sb.id = ", str(sel_schoolbase_pk), "::INT ")))

            sql_list.extend((
                "GROUP BY ey.code, db.id, dep.sequence, db.code, dep.name, dep.sequence, dep.level_req,",
                "lvlbase.id, lvl.sequence, lvlbase.code, lvl.name, lvl.sequence,",
                "sb.id, sb.code, sch.name",

                # PR2024-06-20 ORDER BY ey_code DESC,
                # This way the latest name of school, lvl and dep will be stored in the school_dict etc
                "ORDER BY dep.sequence, lvl.sequence, sb.code, ey_code DESC"
            ))
            sql = ' '.join(sql_list)

            if logging_on:
                for sql_txt in sql_list:
                    logger.debug('    > : ' + str(sql_txt))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                result_rows = af.dictfetchall(cursor)

                if logging_on:
                    for row in result_rows:
                        logger.debug('    row: ' + str(row))

        except Exception as e:
            # - return msg_err when instance not created
            #  msg format: [ { class: "border_bg_invalid", header: 'Update this', msg_html: "An eror occurred." }]
            logger.error(getattr(e, 'message', str(e)))
            # &emsp; add 4 'hard' spaces
            msg_html = '<br>'.join((str(_('An error occurred')) + ':','&emsp;<i>' + str(e) + '</i>'))
            error_dict = {'class': 'border_bg_invalid', 'msg_html': msg_html}

        """
        row: {'ey_code': 2024, 'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvlbase_id': 6, 'lvl_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 'sb_id': 2, 'sch_name': 'Ancilla Domini Vsbo', 'sb_code': 'CUR01', 'c_m': 7, 'c_v': 20, 'c_t': 27, 'r_p_m': 3, 'r_p_v': 10, 'r_p_t': 13, 'r_f_m': 3, 'r_f_v': 6, 'r_f_t': 9, 'r_r_m': 1, 'r_r_v': 3, 'r_r_t': 4, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0, 'r_n_m': 0, 'r_n_v': 1, 'r_n_t': 1}
        row: {'ey_code': 2023, 'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvlbase_id': 6, 'lvl_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 'sb_id': 2, 'sch_name': 'Ancilla Domini Vsbo', 'sb_code': 'CUR01', 'c_m': 9, 'c_v': 24, 'c_t': 33, 'r_p_m': 6, 'r_p_v': 19, 'r_p_t': 25, 'r_f_m': 3, 'r_f_v': 5, 'r_f_t': 8, 'r_r_m': 0, 'r_r_v': 0, 'r_r_t': 0, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0, 'r_n_m': 0, 'r_n_v': 0, 'r_n_t': 0}
        row: {'ey_code': 2022, 'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvlbase_id': 6, 'lvl_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 'sb_id': 2, 'sch_name': 'Ancilla Domini Vsbo', 'sb_code': 'CUR01', 'c_m': 11, 'c_v': 19, 'c_t': 30, 'r_p_m': 10, 'r_p_v': 16, 'r_p_t': 26, 'r_f_m': 1, 'r_f_v': 3, 'r_f_t': 4, 'r_r_m': 0, 'r_r_v': 0, 'r_r_t': 0, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0, 'r_n_m': 0, 'r_n_v': 0, 'r_n_t': 0}
            
        """

    return result_rows, error_dict
# --- end of create_results_per_school_rows


def create_result_dict_per_school_multiple_examyears(country_pk, is_role_school, sel_schoolbase, max_examyear_code, min_examyear_code):
    # --- create rows of all students of this examyear / school PR2022-06-17
    # - show only students that are not tobedeleted
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_result_dict_per_school_multiple_examyears -----')
    # store sch_name of newest examyear is stored in_dict, it might have changed. Print the sch_name of the last examyear

    field_list = []
    # 'c': count, 'p': passed, 'f': failed, 'r': reex, 'w': withdrawn, 'n': no result
    for result in  ('c', 'p', 'f', 'r', 'w', 'n'):
        for gender in ('m', 'v', 'x', 't'):
            field_list.append('_'.join((result, gender)))

    result_dict = {}
    examyear_list = []
    depbase_dict = {}
    lvlbase_dict = {}
    schoolbase_dict = {}
    has_gender_x = False

    result_rows, error_dict = create_results_per_school_rows(country_pk, is_role_school, sel_schoolbase, max_examyear_code, min_examyear_code)

    if result_rows:

        for row in result_rows:
            db_id = row.get('db_id') or 0
            lb_id = row.get('lvlbase_id') or 0
            sb_id = row.get('sb_id') or 0
            ey_code = row.get('ey_code') or 0
            # depbase_dict contains depbase name etc
            if db_id not in depbase_dict:
                depbase_dict[db_id] = {'db_id': db_id, 'db_code': row['db_code'], 'dep_name': row['dep_name'], 'dep_seq': row['dep_seq'], 'dep_lvl_req': row['dep_lvl_req']}
            if db_id not in result_dict:
                result_dict[db_id] = {'db_code': row.get('db_code')}
            # db_dict is dict with key db_id in result_dict
            db_dict = result_dict[db_id]

            if lb_id not in lvlbase_dict:
                lvlbase_dict[lb_id] = {'lvlbase_id': lb_id, 'lvl_code': row['lvl_code'], 'lvl_name': row['lvl_name'], 'lvl_seq': row['lvl_seq']}
            if lb_id not in db_dict:
                db_dict[lb_id] = {'lvl_code': row['lvl_code']}
            lb_dict = db_dict[lb_id]

            if sb_id not in schoolbase_dict:
                schoolbase_dict[sb_id] = {'sb_id': sb_id, 'sb_code': row['sb_code'], 'sch_name': row['sch_name'] }
            if sb_id not in lb_dict:
                lb_dict[sb_id] = {'sb_code': row['sb_code']}
            sb_dict = lb_dict[sb_id]

            if ey_code not in examyear_list:
                examyear_list.append(ey_code)
            if ey_code not in sb_dict:
                sb_dict[ey_code] = {}
            ey_dict = sb_dict[ey_code]

            for field in field_list:
                field_value = row[field]
                ey_dict[field] = field_value

                if field == 'c_x' and field_value:
                    has_gender_x = True

    examyear_list.sort()

    # convert dict to sorted dictlist
    depbase_dictlist = sorted(list(depbase_dict.values()), key=lambda k: (k['dep_seq'])) if depbase_dict else []
    lvlbase_dictliist = sorted(list(lvlbase_dict.values()), key=lambda k: (k['lvl_seq'])) if lvlbase_dict else []
    schoolbase_dictliist = sorted(list(schoolbase_dict.values()), key=lambda k: (k['sb_code'])) if schoolbase_dict else []


    if logging_on:
        logger.debug('     examyear_list: ' + str(examyear_list))
        logger.debug('     depbase_dictlist: ' + str(depbase_dictlist))
        logger.debug('     lvlbase_dictliist: ' + str(lvlbase_dictliist))
        logger.debug('     schoolbase_dictliist: ' + str(schoolbase_dictliist))
        logger.debug('     has_gender_x: ' + str(has_gender_x))
        logger.debug('     result_dict: ' + str(result_dict))

    """
    examyear_list: [2022, 2023, 2024]
    depbase_dictlist: [
        {'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_seq': 1, 'dep_lvl_req': True}]
    lvlbase_dictliist: [
        {'lvlbase_id': 6, 'lvl_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 'lvl_seq': 1}, 
        {'lvlbase_id': 5, 'lvl_code': 'PKL', 'lvl_name': 'Praktisch Kadergerichte Leerweg', 'lvl_seq': 2}, 
        {'lvlbase_id': 4, 'lvl_code': 'TKL', 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 'lvl_seq': 3}]
    schoolbase_dictliist: [
        {'sb_id': 2, 'sb_code': 'CUR01', 'sch_name': 'Ancilla Domini Vsbo 2024'}]
    has_gender_x: True
        
    result_dict: {
        1: {'db_code': 'Vsbo', 
            6: {'lvl_code': 'PBL', 
                2: {'sb_code': 'CUR01', 2024: {'c_m': 7, 'c_v': 20, 'c_x': 0, 'c_t': 27, 'p_m': 3, 'p_v': 10, 'p_x': 0, 'p_t': 13, 'f_m': 3, 'f_v': 6, 'f_x': 0, 'f_t': 9, 'r_m': 1, 'r_v': 3, 'r_x': 0, 'r_t': 4, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 1, 'n_x': 0, 'n_t': 1}, 2023: {'c_m': 9, 'c_v': 24, 'c_x': 0, 'c_t': 33, 'p_m': 6, 'p_v': 19, 'p_x': 0, 'p_t': 25, 'f_m': 3, 'f_v': 5, 'f_x': 0, 'f_t': 8, 'r_m': 0, 'r_v': 0, 'r_x': 0, 'r_t': 0, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 0, 'n_x': 0, 'n_t': 0}, 2022: {'c_m': 11, 'c_v': 19, 'c_x': 0, 'c_t': 30, 'p_m': 10, 'p_v': 16, 'p_x': 0, 'p_t': 26, 'f_m': 1, 'f_v': 3, 'f_x': 0, 'f_t': 4, 'r_m': 0, 'r_v': 0, 'r_x': 0, 'r_t': 0, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 0, 'n_x': 0, 'n_t': 0}}}, 
            5: {'lvl_code': 'PKL', 
                2: {'sb_code': 'CUR01', 2024: {'c_m': 2, 'c_v': 23, 'c_x': 0, 'c_t': 25, 'p_m': 0, 'p_v': 14, 'p_x': 0, 'p_t': 14, 'f_m': 1, 'f_v': 3, 'f_x': 0, 'f_t': 4, 'r_m': 1, 'r_v': 5, 'r_x': 0, 'r_t': 6, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 1, 'n_x': 0, 'n_t': 1}, 2023: {'c_m': 9, 'c_v': 35, 'c_x': 0, 'c_t': 44, 'p_m': 6, 'p_v': 25, 'p_x': 0, 'p_t': 31, 'f_m': 3, 'f_v': 10, 'f_x': 0, 'f_t': 13, 'r_m': 0, 'r_v': 0, 'r_x': 0, 'r_t': 0, 'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 'n_m': 0, 'n_v': 0, 'n_x': 0, 'n_t': 0}, 2022: {'c_m': 8, 'c_v': 31, 'c_x': 0, 'c_t': 39, 'p_m': 5, 'p_v': 23, 'p_x': 0, 'p_t': 28, 'f_m': 3, 'f_v': 7, 'f_x': 0, 'f_t': 10, 'r_m': 0, 'r_v': 0, 'r_x': 0, 'r_t': 0, 'w_m': 0, 'w_v': 1, 'w_x': 0, 'w_t': 1, 'n_m': 0, 'n_v': 0, 'n_x': 0, 'n_t': 0}}}, 
            4: {'lvl_code': 'TKL', 
                2: {'sb_code': 'CUR01', 
                    2024: {'c_m': 2, 'c_v': 24, 'c_x': 1, 'c_t': 27, 
                           'p_m': 0, 'p_v': 15, 'p_x': 1, 'p_t': 16, 
                           'f_m': 2, 'f_v': 4, 'f_x': 0, 'f_t': 6, 
                           'r_m': 0, 'r_v': 5, 'r_x': 0, 'r_t': 5, 
                           'w_m': 0, 'w_v': 0, 'w_x': 0, 'w_t': 0, 
                           'n_m': 0, 'n_v': 0, 'n_x': 0, 'n_t': 0}, 
                    2023: {'c_m': 5, 'c_v': 48, 'c_x': 0, 'c_t': 53, 

    """
    return examyear_list, depbase_dictlist, lvlbase_dictliist, schoolbase_dictliist, has_gender_x, result_dict, error_dict
# --- end of create_result_dict_per_school_multiple_examyears
#/////////////////////////////////////////////////////////////////

# /////////////////////////////////////////////////////////////////
def create_grades_avg_rows(country_pk, is_role_school, sel_schoolbase, sel_depbase, max_examyear_code,
                                   min_examyear_code=None):
    # --- create rows of all studentsubjects of this examyear range / school PR2024-06-22
    # - show only students that are not deleted and not tobedeleted ad not partial_exam
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_grades_avg_rows -----')

    def get_sql_grade(grade_field):
        return ''.join((
            "CASE WHEN studsubj.gradelist_", grade_field, " IS NULL THEN NULL ",
                "ELSE studsubj.gradelist_", grade_field, "::DECIMAL ",
            "END AS ", grade_field, ","
        ))

    grade_rows = []
    error_dict = {}  # PR2021-11-17 new way of err msg, like in TSA

    if country_pk and max_examyear_code:
        if min_examyear_code > max_examyear_code:
            min_examyear_code = None

        #try:
        if True:
            if logging_on:
                logger.debug(' examyear range: ' + str(min_examyear_code) + ' - ' + str(max_examyear_code))
                logger.debug('sel_schoolbase: ' + str(sel_schoolbase))

            subsql_list = ["SELECT studsubj.id AS studsubj_id,",
                           "CASE WHEN LOWER(st.gender) = 'm' THEN 'm' ELSE ",
                                "CASE WHEN LOWER(st.gender) = 'v' THEN 'v' ELSE 'x' END ",
                           "END AS gender, ",

                           get_sql_grade('sesrgrade'),
                           get_sql_grade('pecegrade'),
                           get_sql_grade('finalgrade'),

                           "si.gradetype",

                           "FROM students_studentsubject AS studsubj",
                           "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                           "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",

                           "WHERE NOT studsubj.deleted AND NOT studsubj.tobedeleted",
                           "AND NOT st.deleted AND NOT st.tobedeleted",

                            # do't include ovg grades (onvlodoende, voldoende , goed)
                           "AND si.gradetype = ", str(c.GRADETYPE_01_NUMBER),

                           # include partial exams.
                           # "AND NOT st.partial_exam",
                           "AND NOT studsubj.gradelist_finalgrade IS NULL",
                           ]
            sub_sql = ' '.join(subsql_list)

            # PR2024-06-21 debug: eror: '<' not supported between instances of 'NoneType' and 'int'
            # caused by sorted function
            # solved by givingdefault va\lrue when None
            sql_list = ["WITH subsql AS (" + sub_sql + ")",
                        "SELECT ey.code AS ey_code, ",
                        "db.id AS db_id, db.code AS db_code, dep.name AS dep_name, dep.level_req AS dep_lvl_req,",
                        "COALESCE(dep.sequence, 999) AS dep_seq,",

                        "lvlbase.id AS lvlbase_id, lvlbase.code AS lvl_code, lvl.name AS lvl_name, ",
                        "COALESCE(lvl.sequence, 999) AS lvl_seq,",

                        "si.gradetype,",
                        "sb.id AS sb_id, sb.code AS sb_code, sch.name AS sch_name, ",

                        "subjbase.id AS subjbase_id, subjbase.code AS subjbase_code, subj.name_nl AS subj_name_nl,",

                        "subsql.gender,"

                        "SUM(subsql.sesrgrade) AS sum_sesr,",
                        "SUM(subsql.pecegrade) AS sum_pece,",
                        "SUM(subsql.finalgrade) AS sum_final,",

                        "COUNT(*) AS count",

                        "FROM students_studentsubject AS studsubj",

                        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
                        "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
                        "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",

                        "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
                        "INNER JOIN schools_departmentbase AS db ON (db.id = dep.base_id)",
                        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
                        "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                        "INNER JOIN subsql ON (subsql.studsubj_id = studsubj.id)",

                        ''.join(("WHERE ey.country_id = ", str(country_pk), "::INT ",
                                 "AND db.id = ", str(sel_depbase.pk), "::INT")),
                        ]
            if min_examyear_code is None:
                sql_list.append(''.join(("AND ey.code = ", str(max_examyear_code), "::INT")))
            else:
                sql_list.append(''.join(("AND ey.code >= ", str(min_examyear_code), "::INT ",
                                         "AND ey.code <= ", str(max_examyear_code), "::INT")))

            if is_role_school:
                sel_schoolbase_pk = sel_schoolbase.pk if sel_schoolbase else 0
                sql_list.append(''.join(("AND sb.id = ", str(sel_schoolbase_pk), "::INT ")))

            sql_list.extend((
                "GROUP BY ey.code, ",
                "subsql.gender,"
                "db.id, db.code, dep.name, dep.level_req,  dep.sequence,",
                "lvlbase.id, lvlbase.code, lvl.name, lvl.sequence,",
                "sb.id, sb.code, sch.name, subjbase.id, subjbase.code, subj.name_nl, si.gradetype",

                # PR2024-06-20 ORDER BY ey_code DESC,
                # This way the latest name of school, lvl and dep will be stored in the school_dict etc
                "ORDER BY dep.sequence, lvl.sequence, subj.name_nl, ey_code DESC",
            ))
            sql = ' '.join(sql_list)

            if logging_on and False:
                for sql_txt in sql_list:
                    logger.debug('    > : ' + str(sql_txt))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                grade_rows = af.dictfetchall(cursor)

                if logging_on:
                    for row in grade_rows:
                        logger.debug('    row: ' + str(row))

        #except Exception as e:
            # - return msg_err when instance not created
            #  msg format: [ { class: "border_bg_invalid", header: 'Update this', msg_html: "An eror occurred." }]
        #    logger.error(getattr(e, 'message', str(e)))
            # &emsp; add 4 'hard' spaces
        #    msg_html = '<br>'.join((str(_('An error occurred')) + ':', '&emsp;<i>' + str(e) + '</i>'))
        #    error_dict = {'class': 'border_bg_invalid', 'msg_html': msg_html}

        """
        row: {'ey_code': 2024, 'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvlbase_id': 6, 'lvl_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 'sb_id': 2, 'sch_name': 'Ancilla Domini Vsbo', 'sb_code': 'CUR01', 'c_m': 7, 'c_v': 20, 'c_t': 27, 'r_p_m': 3, 'r_p_v': 10, 'r_p_t': 13, 'r_f_m': 3, 'r_f_v': 6, 'r_f_t': 9, 'r_r_m': 1, 'r_r_v': 3, 'r_r_t': 4, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0, 'r_n_m': 0, 'r_n_v': 1, 'r_n_t': 1}
        row: {'ey_code': 2023, 'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvlbase_id': 6, 'lvl_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 'sb_id': 2, 'sch_name': 'Ancilla Domini Vsbo', 'sb_code': 'CUR01', 'c_m': 9, 'c_v': 24, 'c_t': 33, 'r_p_m': 6, 'r_p_v': 19, 'r_p_t': 25, 'r_f_m': 3, 'r_f_v': 5, 'r_f_t': 8, 'r_r_m': 0, 'r_r_v': 0, 'r_r_t': 0, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0, 'r_n_m': 0, 'r_n_v': 0, 'r_n_t': 0}
        row: {'ey_code': 2022, 'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvlbase_id': 6, 'lvl_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 'sb_id': 2, 'sch_name': 'Ancilla Domini Vsbo', 'sb_code': 'CUR01', 'c_m': 11, 'c_v': 19, 'c_t': 30, 'r_p_m': 10, 'r_p_v': 16, 'r_p_t': 26, 'r_f_m': 1, 'r_f_v': 3, 'r_f_t': 4, 'r_r_m': 0, 'r_r_v': 0, 'r_r_t': 0, 'r_w_m': 0, 'r_w_v': 0, 'r_w_t': 0, 'r_n_m': 0, 'r_n_v': 0, 'r_n_t': 0}

        """
    return grade_rows, error_dict
# --- end of create_grades_avg_rows


def create_grade_avg_dict(country_pk, is_role_school, sel_schoolbase, sel_depbase,
                          max_examyear_code, min_examyear_code):
    # --- create rows of all students of this examyear / school PR2022-06-17
    # - show only students that are not tobedeleted
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_grade_avg_dict -----')
    # store sch_name of newest examyear is stored in_dict, it might have changed. Print the sch_name of the last examyear

    starttime = timer()
    def add_to_total(total_dict, count , sesr, pece, final):
        if count:
            total_dict['count'] += count
        if sesr:
            total_dict['sesr'] += sesr
        if pece:
            total_dict['pece'] += pece
        if final:
            total_dict['final'] += final

    examyear_list = []
    grades_dict = {}
    depbase_dict = {}
    lvlbase_dict = {}
    schoolbase_dict = {}
    subjbase_dict = {}

    has_gender_x = False

    grade_rows, error_dict = create_grades_avg_rows(country_pk, is_role_school, sel_schoolbase, sel_depbase,
                                                             max_examyear_code, min_examyear_code)

    if grade_rows:

        for row in grade_rows:
            db_id = row.get('db_id') or 0
            lb_id = row.get('lvlbase_id') or 0
            sb_id = row.get('sb_id') or 0
            ey_code = row.get('ey_code') or 0
            subjbase_id = row.get('subjbase_id') or 0
            gender = row['gender']

            count = row['count']
            sesr = row['sum_sesr']
            pece = row['sum_pece']
            final = row['sum_final']

            # depbase_dict contains depbase name etc
            if db_id not in depbase_dict:
                depbase_dict[db_id] = {'db_id': db_id, 'db_code': row['db_code'], 'dep_name': row['dep_name'],
                                       'dep_seq': row['dep_seq'], 'dep_lvl_req': row['dep_lvl_req']}
            # db_dict is dict with key db_id in grades_dict
            if db_id not in grades_dict:
                grades_dict[db_id] = {'db_code': row['db_code']}  # , 'count': 0, 'sesr': 0, 'pece': 0,'final': 0}
            db_dict = grades_dict[db_id]

           #add_to_total(db_dict, count, sesr, pece, final)

            if lb_id not in lvlbase_dict:
                lvlbase_dict[lb_id] = {'lvlbase_id': lb_id, 'lvl_code': row['lvl_code'], 'lvl_name': row['lvl_name'],
                                       'lvl_seq': row['lvl_seq']}
            if lb_id not in db_dict:
                db_dict[lb_id] = {'lvl_code': row['lvl_code']}  # , 'count': 0, 'sesr': 0, 'pece': 0,'final': 0}
            lb_dict = db_dict[lb_id]

            #add_to_total(lb_dict, count, sesr, pece, final)

            if sb_id not in schoolbase_dict:
                schoolbase_dict[sb_id] = {'sb_id': sb_id, 'sb_code': row['sb_code'], 'sch_name': row['sch_name']}
            if sb_id not in lb_dict:
                lb_dict[sb_id] = {'sb_code': row['sb_code']}  # , 'count': 0, 'sesr': 0, 'pece': 0,'final': 0}
            sb_dict = lb_dict[sb_id]

            #add_to_total(sb_dict, count, sesr, pece, final)

            if subjbase_id not in subjbase_dict:
                subjbase_dict[subjbase_id] = {'subjbase_id': subjbase_id, 'subjbase_code': row['subjbase_code'], 'subj_name_nl': row['subj_name_nl']}

            if subjbase_id not in sb_dict:
                sb_dict[subjbase_id] = {'subjbase_code': row['subjbase_code']}  # , 'count': 0, 'sesr': 0, 'pece': 0,'final': 0}
            sjb_dict = sb_dict[subjbase_id]

            #add_to_total(sjb_dict, count, sesr, pece, final)

            if ey_code not in examyear_list:
                examyear_list.append(ey_code)
            if ey_code not in sjb_dict:
                sjb_dict[ey_code] = {'t': {'count': 0, 'sesr': 0, 'pece': 0, 'final': 0}}
            ey_dict = sjb_dict[ey_code]

            if gender == 'x':
                has_gender_x = True

            ey_dict[gender] = {
                'count': count,
                'sesr': sesr,
                'pece': pece,
                'final': final
            }

            add_to_total(ey_dict['t'], count, sesr, pece, final)

    examyear_list.sort()

    # convert dict to sorted dictlist
    depbase_dictlist = sorted(list(depbase_dict.values()), key=lambda k: (k['dep_seq'])) if depbase_dict else []
    lvlbase_dictlist = sorted(list(lvlbase_dict.values()), key=lambda k: (k['lvl_seq'])) if lvlbase_dict else []
    schoolbase_dictlist = sorted(list(schoolbase_dict.values()),
                                  key=lambda k: (k['sb_code'])) if schoolbase_dict else []


    if logging_on and False:
        logger.debug('     schoolbase_dict: ' + str(schoolbase_dict))
        logger.debug('     subjbase_dict: ' + str(subjbase_dict))
    subjbase_dictlist = sorted(list(subjbase_dict.values()),
                                  key=lambda k: (k['subj_name_nl'])) if subjbase_dict else []

    if logging_on and False:
        logger.debug('     examyear_list: ' + str(examyear_list))
        logger.debug('     depbase_dictlist: ' + str(depbase_dictlist))
        logger.debug('     lvlbase_dictlist: ' + str(lvlbase_dictlist))
        logger.debug('     schoolbase_dictlist: ' + str(schoolbase_dictlist))
        logger.debug('     subjbase_dictlist: ' + str(subjbase_dictlist))
        logger.debug('     has_gender_x: ' + str(has_gender_x))
        logger.debug('     grades_dict: ' + str(grades_dict))

    """
    examyear_list: [2024]
    depbase_dictlist: [{'db_id': 1, 'db_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_seq': 1, 'dep_lvl_req': True}]
    lvlbase_dictlist: [{'lvlbase_id': 6, 'lvl_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 'lvl_seq': 1}]
    schoolbase_dictlist: [{'sb_id': 2, 'sb_code': 'CUR01', 'sch_name': 'Ancilla Domini Vsbo 2024'}]
    subject_dictlist: [
        {'subj_id': 365, 'subjbase_code': 'ac', 'subj_name_nl': 'Administratie & Commercie'}, 
        {'subj_id': 344, 'subjbase_code': 'bi', 'subj_name_nl': 'Biologie'}, 
        {'subj_id': 355, 'subjbase_code': 'cav', 'subj_name_nl': 'Culturele en artistieke vorming'}, 
        {'subj_id': 345, 'subjbase_code': 'ec', 'subj_name_nl': 'Economie'}, 
        {'subj_id': 330, 'subjbase_code': 'en', 'subj_name_nl': 'Engels'}]
    has_gender_x: False

    grades_dict: {
        1: {'db_code': 'Vsbo', 'count': 818, 'sesr': Decimal('4885.1'), 'pece': Decimal('2754.9'), 'final': Decimal('4779'), 
            6: {'lvl_code': 'PBL', 'count': 260, 'sesr': Decimal('1486.5'), 'pece': Decimal('863.9'), 'final': Decimal('1495'), 
                2: {'sb_code': 'CUR01', 'count': 260, 'sesr': Decimal('1486.5'), 'pece': Decimal('863.9'), 'final': Decimal('1495'), 
                    133: {'subjbase_code': 'ac', 'count': 15, 'sesr': Decimal('85.2'), 'pece': Decimal('80.2'), 'final': Decimal('83'), 
                        2024: {'t': {'count': 15, 'sesr': Decimal('85.2'), 'pece': Decimal('80.2'), 'final': Decimal('83')}, 
                                'm': {'count': 5, 'sesr': Decimal('28.7'), 'pece': Decimal('27.5'), 'final': Decimal('28')}, 
                                'v': {'count': 10, 'sesr': Decimal('56.5'), 'pece': Decimal('52.7'), 'final': Decimal('55')}}}, 
                    123: {'subjbase_code': 'bi', 'count': 12, 'sesr': Decimal('72.1'), 'pece': Decimal('64.1'), 'final': Decimal('69'),

    """
    if logging_on:
        elapsed_seconds = timer() - starttime
        logger.debug('   elapsed_seconds: ' + str(elapsed_seconds))

    return examyear_list, depbase_dictlist, lvlbase_dictlist, schoolbase_dictlist, subjbase_dictlist, has_gender_x, grades_dict, error_dict
# --- end of create_grade_avg_dict
# /////////////////////////////////////////////////////////////////

def get_formats(book):
    # create dict with formats, used in this workbook
    return {
        'bold_format': book.add_format(c.XF_BOLD),
        'bold_format_blue': book.add_format(c.XF_BOLD_FCBLUE),

        #'row_align_center': book.add_format(c.XF_ROW_ALIGN_CENTER_BLUE),
        #'row_align_left': book.add_format(c.XF_ROW_ALIGN_LEFT_BLUE),

        'hdr_tableheader_alignleft': book.add_format(c.XF_TABLEHEADER_ALIGNLEFT),
        'hdr_tableheader_borderleft': book.add_format(c.XF_TABLEHEADER_BORDERLEFT),

        'hdr_grandtotal': book.add_format(c.XF_HDR_GRANDTOTAL),
        'hdr_grandtotal_alignleft': book.add_format(c.XF_HDR_GRANDTOTAL_ALIGNLEFT),
        'hdr_grandtotal_percentage': book.add_format(c.XF_HDR_GRANDTOTAL_PERCENTAGE),
        'hdr_grandtotal_borderleft': book.add_format(c.XF_HDR_GRANDTOTAL_BORDERLEFT),
        'hdr_grandtotal_borderleft_gray': book.add_format(c.XF_HDR_GRANDTOTAL_BORDERLEFT_GRAY),
        'hdr_grandtotal_perc_borderleft': book.add_format(c.XF_HDR_GRANDTOTAL_PERCENTAGE_BORDERLEFT),

        'hdr_subtotal': book.add_format(c.XF_HDR_SUBTOTAL),
        'hdr_subtotal_alignleft': book.add_format(c.XF_HDR_SUBTOTAL_ALIGNLEFT),
        'hdr_subtotal_percentage': book.add_format(c.XF_HDR_SUBTOTAL_PERCENTAGE),
        'hdr_subtotal_borderleft': book.add_format(c.XF_HDR_SUBTOTAL_BORDERLEFT),
        'hdr_subtotal_borderleft_gray': book.add_format(c.XF_HDR_SUBTOTAL_BORDERLEFT_GRAY),
        'hdr_subtotal_perc_borderleft': book.add_format(c.XF_HDR_SUBTOTAL_PERCENTAGE_BORDERLEFT),

        'hdr_subsubtotal': book.add_format(c.XF_HDR_SUBSUBTOTAL),
        'hdr_subsubtotal_alignleft': book.add_format(c.XF_HDR_SUBSUBTOTAL_ALIGNLEFT),
        'hdr_subsubtotal_percentage': book.add_format(c.XF_HDR_SUBSUBTOTAL_PERC),
        'hdr_subsubtotal_borderleft': book.add_format(c.XF_HDR_SUBSUBTOTAL_BORDERLEFT),
        'hdr_subsubtotal_borderleft_gray': book.add_format(c.XF_HDR_SUBSUBTOTAL_BORDERLEFT_GRAY),
        'hdr_subsubtotal_perc_borderleft': book.add_format(c.XF_HDR_SUBSUBTOTAL_PERC_BORDERLEFT),
        'ftr_subsubtotal_avg_borderleft_gray': book.add_format(c.XF_FTR_SUBSUBTOTAL_AVG_BORDERLEFT_GRAY),

        #'hdr_grade': book.add_format(c.XF_HDR_GRADE),
        'hdr_grade_borderleft': book.add_format(c.XF_HDR_GRADE_BORDERLEFT),

        'row_value': book.add_format(c.XF_ROW_VALUE),
        'row_value_alignleft': book.add_format(c.XF_ROW_VALUE_ALIGNLEFT),
        'row_perc': book.add_format(c.XF_ROW_PERCENTAGE),
        'row_value_borderleft': book.add_format(c.XF_ROW_VALUE_BORDERLEFT),
        'row_value_borderleft_gray': book.add_format(c.XF_ROW_VALUE_BORDERLEFT_GRAY),
        'row_perc_borderleft': book.add_format(c.XF_ROW_PERCENTAGE_BORDERLEFT),

        'row_avg_borderleft': book.add_format(c.XF_ROW_AVERAGE_BORDERLEFT),
        'row_avg_borderleft_gray': book.add_format(c.XF_ROW_AVERAGE_BORDERLEFT_GRAY),


    #'th_align_center': book.add_format(c.XF_HDR_ALC_TOPBOTTOM),
        #'th_align_left': book.add_format(c.XF_HDR_ALL_TOPBOTTOM)
    }
# end of get_formats


def write_header01_row(sheet, field_dictlist, formats, header_list, row_index):
    # Code School	Totaal aantal kandidaten			Geslaagd			Herexamen			Afgewezen			Teruggetrokken			Geen uitslag
    sheet.set_row(row_index, 26)

    for col_index, field_dict in enumerate(field_dictlist):
        #   'hdr1': {'caption': result_caption, 'format': 'test'},
        for hdr_index, hdr_key in enumerate(header_list):
            hdr_row_index = row_index + hdr_index
            if hdr_key in field_dict:
                hdr_dict = field_dict[hdr_key]
                if hdr_dict:
                    field_caption = hdr_dict['caption'] if 'caption' in hdr_dict else ''
                    field_merge =  hdr_dict['merge'] if 'merge' in hdr_dict else 0
                    format_key = hdr_dict['format'] if 'format' in hdr_dict else ''
                    field_format = formats[format_key] if format_key in formats else ''
                    if field_merge:
                        sheet.merge_range(hdr_row_index, col_index, hdr_row_index,
                                          col_index + field_merge - 1, field_caption, field_format)
                    else:
                        sheet.write(hdr_row_index, col_index, field_caption, field_format)
# end of write_header01_row

def write_header_dep_lvl_row(sheet, field_dictlist, formats, hdr_key, caption, row_index):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  write_header_dep_lvl_row  -----')
        logger.debug('    hdr_key: ' + str(hdr_key))
        logger.debug('    caption: ' + str(caption))

    for col_index, field_dict in enumerate(field_dictlist):
        if hdr_key in field_dict:
            hdr_dict = field_dict[hdr_key]
            if logging_on:
                logger.debug('    hdr_dict: ' + str(hdr_dict))

            if hdr_dict:
                field_caption = caption if 'caption' in hdr_dict else ''
                field_merge =  hdr_dict['merge'] if 'merge' in hdr_dict else 0
                format_key = hdr_dict['format'] if 'format' in hdr_dict else ''
                if logging_on:
                    logger.debug('    format_key: ' + str(format_key))

                field_format = formats[format_key] if format_key in formats else ''
                if field_merge:
                    sheet.merge_range(row_index, col_index, row_index,
                                      col_index + field_merge - 1, field_caption, field_format)
                else:
                    sheet.write(row_index, col_index, field_caption, field_format)
# end of write_header01_row
