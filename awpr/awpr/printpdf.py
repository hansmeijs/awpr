
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _

#from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
#from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import mm
#from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
#from reportlab.platypus import SimpleDocTemplate, Paragraph, Frame, Spacer, Image

from awpr import constants as c
from awpr import functions as af
from awpr import settings as s
from awpr import library as awpr_lib
from grades import views as grade_views
from grades import calc_score as calc_score

import logging
logger = logging.getLogger(__name__)


def draw_exam(canvas, sel_exam_instance, sel_examyear, user_lang):  # PR2021-05-07 PR2022-01-28
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('============= draw_exam ===================')
        logger.debug('sel_exam_instance: ' + str(sel_exam_instance) + ' ' + str(type(sel_exam_instance)))

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

    subject = sel_exam_instance.subject
    examperiod = sel_exam_instance.examperiod
    amount = sel_exam_instance.amount if sel_exam_instance.amount else 0
    amount_str = str(amount) if amount else '---'
    blanks = sel_exam_instance.blanks if sel_exam_instance.blanks else 0
    blanks_str = str(blanks) if blanks else '---'
    scalelength_str = str(sel_exam_instance.scalelength) if sel_exam_instance.scalelength else '-'

    """
    partex: "1;1;4;20;Praktijkexamen onderdeel A # 3;1;8;12;Minitoets 1 BLAUW onderdeel A # ...
    format of partex_str is:
        partex are divided by "#"
            each item of partex contains: partex_pk ; partex_examperiod ; partex_amount ; max_score ; partex_name #

    assignment: "1;4;20|1;;6;|2;;4;|3;;4;|4;;6; # 3;8;12|1;D;3;|2;C;2;|3;C;;|4;;1;|5;;1;|6;;1;|7;D;;|8;;2; # ...
    format of assignment_str is:
        partex are divided by "#"
            first item of partex contains partex info: partex_pk ; partex_amount ; max_score |
            other items =  | q_number ; max_char ; max_score ; min_score |

    keys: "1 # 3|1;ac|2;b|3;ab|7;d # ...
    format of keys_str is:
        partex are divided by "#"
            first item of partex contains partex_pk ; partex_amount ; max_score |
    """
    partex_str = sel_exam_instance.partex
    assignment_str = sel_exam_instance.assignment
    keys_str = sel_exam_instance.keys

# - get dep_abbrev from department
    dep_abbrev = '---'
    department = sel_exam_instance.department
    if department:
        dep_abbrev = department.abbrev

# - get level_abbrev from level
    level = sel_exam_instance.level
    if level and level.abbrev:
        dep_abbrev += ' - ' + level.abbrev

# - get version
    version = sel_exam_instance.version

    last_modified_text = af.get_modifiedby_formatted(sel_exam_instance, user_lang)

# - get form_text from examyearsetting
    form_text = awpr_lib.get_library(sel_examyear, ['exform', 'exam'])
    if logging_on:
        logger.debug('form_text: ' + str(form_text))

    minond = form_text.get('minond', '-')
    title = form_text.get('title', '-')  + str(subject.examyear.code)

    examperiod_cpt = form_text.get('Central_exam', '-') if examperiod == 1 else \
            form_text.get('Re_exam', '-') if examperiod == 2 else \
            form_text.get('Ce_Re_exam', '?') if examperiod == 12 else '-'

    educationtype = form_text.get('educationtype', '-') + ':'
    examtype = form_text.get('examtype', '-') + ':'
    subject_cpt = form_text.get('subject', '-') + ':'
    version_cpt = form_text.get('version', '-') + ':' if version else None
    number_questions = form_text.get('number_questions', '-') + ':'
    max_score = form_text.get('max_score', '-') + ':'

    filepath = s.STATICFILES_FONTS_DIR + 'arial.ttf'
    try:
        ttfFile = TTFont('Arial', filepath)
        #logger.debug('ttfFile: ' + str(ttfFile))
        pdfmetrics.registerFont(ttfFile)
    except Exception as e:
        logger.error('filepath: ' + str(filepath))
        logger.error(getattr(e, 'message', str(e)))

# create list of questions
    all_partex_assignment_keys_dict, no_key_count, no_max_score_count = get_all_partex_assignment_keys_dict(partex_str, assignment_str, keys_str)
    blanks_or_cesuur_str = ''
    if no_key_count or no_max_score_count:
        blanks_or_cesuur_cpt = form_text.get('blanks', '-') + ':'
        if no_key_count:
            blanks_or_cesuur_str = ' '.join((str(no_key_count), form_text.get('keys', '')))
            if no_max_score_count:
                blanks_or_cesuur_str += ', '
        if no_max_score_count:
            blanks_or_cesuur_str += ' '.join((str(no_max_score_count), form_text.get('max_scores', '')))

    elif sel_exam_instance.cesuur and not sel_exam_instance.blanks:
        blanks_or_cesuur_cpt = form_text.get('cesuur', '-') + ':'
        blanks_or_cesuur_str = str(sel_exam_instance.cesuur) if sel_exam_instance.cesuur else '---'
    else:
        blanks_or_cesuur_cpt = form_text.get('blanks', '-') + ':'
        blanks_or_cesuur_str = str(amount) if amount else '---'

    header_list = [
        (minond, None, None, None),
        (title, None, version_cpt, version),
        (educationtype, dep_abbrev, number_questions, amount_str),
        (examtype, examperiod_cpt, max_score, scalelength_str),
        (subject_cpt, subject.name, blanks_or_cesuur_cpt, blanks_or_cesuur_str)
    ]

    draw_exam_page(canvas, form_text, header_list, last_modified_text, all_partex_assignment_keys_dict)

# - end of draw_exam


def draw_exam_page(canvas, form_text, header_list, last_modified_text, all_partex_assignment_keys_dict,):
    # PR2021-05-10 PR2022-01-29 PR2022-04-23
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_exam_page -----')
        logger.debug('all_partex_assignment_keys_dict' + str(all_partex_assignment_keys_dict))

    """
    all_partex_assignment_keys_dict{
        1: {'amount': 4, 'max_score': 20, 'name': 'Praktijkexamen onderdeel A', 'q': {1: '6', 2: '4', 3: '4', 4: '6'}}, 
        3: {'amount': 8, 'max_score': 12, 'name': 'Minitoets 1 BLAUW onderdeel A', 'q': {1: 'D - ac - 3', 2: 'C - b - 2', 3: 'C - ab', 4: '1', 5: '1', 6: '1', 7: 'D - d', 8: '2'}}, 
        4: {'amount': 3, 'max_score': 22, 'name': 'Praktijkexamen onderdeel B', 'q': {1: '6', 2: '6', 3: '10'}}, 
        6: {'amount': 7, 'max_score': 7, 'name': 'Minitoets 2 BLAUW onderdeel B', 'q': {1: '1', 2: 'D - b', 3: '1', 4: '1', 5: '1', 6: 'D - b', 7: '1'}}, 
        7: {'amount': 1, 'max_score': 9, 'name': 'Praktijkexamen onderdeel C', 'q': {1: '9'}}, 
        9: {'amount': 7, 'max_score': 8, 'name': 'Minitoets 3 BLAUW onderdeel C', 'q': {1: 'C - b', 2: '1', 3: '1', 4: 'D - c', 5: '2', 6: 'D - a', 7: '1'}}, 
        10: {'amount': 1, 'max_score': 10, 'name': 'Praktijkexamen onderdeel D', 'q': {1: '10'}}, 
        12: {'amount': 8, 'max_score': 8, 'name': 'Minitoets 4 BLAUW onderdeel D', 'q': {1: 'D - a', 2: 'D - b', 3: 'C - a', 4: '1', 5: '1', 6: 'D - d', 7: 'D - d', 8: '1'}}}
    """

# create a list of partex_pk, sorted by partex names
    partexpk_list_sorted = []
    partexname_list = []
    partexname_dict = {}

    for partex_pk, partex_dict in all_partex_assignment_keys_dict.items():
        partex_name = partex_dict.get('name')
        if partex_name:
            partexname_list.append(partex_name)
            partexname_dict[partex_name] = partex_pk
    partexname_list.sort()
    for partex_name in partexname_list:
        partex_pk = partexname_dict.get(partex_name)
        partexpk_list_sorted.append(partex_pk)

    """
    partexname_dict: {'Praktijkexamen onderdeel A': 1, 'Minitoets 1 BLAUW onderdeel A': 3, 'Praktijkexamen onderdeel B': 4, 'Minitoets 2 BLAUW onderdeel B': 6, 'Praktijkexamen onderdeel C': 7, 'Minitoets 3 BLAUW onderdeel C': 9, 'Praktijkexamen onderdeel D': 10, 'Minitoets 4 BLAUW onderdeel D': 12}
    partexname_list: ['Minitoets 1 BLAUW onderdeel A', 'Minitoets 2 BLAUW onderdeel B', 'Minitoets 3 BLAUW onderdeel C', 'Minitoets 4 BLAUW onderdeel D', 'Praktijkexamen onderdeel A', 'Praktijkexamen onderdeel B', 'Praktijkexamen onderdeel C', 'Praktijkexamen onderdeel D']
    partexpk_list:   [3, 6, 9, 12, 1, 4, 7, 10]
    """

# +++ write header block
    """
    canvas.setLineWidth(.5)
    # corners of the rectangle
    top, right, bottom, left = 287 * mm, 200 * mm, 17 * mm, 10 * mm
    page_width = right - left  # 190 mm
    border = (top, right, bottom, left)
    canvas.rect(left, bottom, page_width, height)
    """

    today_dte = af.get_today_dateobj()
    today_formatted = af.format_WDMY_from_dte(today_dte, c.LANG_DEFAULT)

    # - set the corners of the rectangle
    top, right, bottom, left = 287 * mm, 200 * mm, 12 * mm, 10 * mm
    # width = right - left  # 190 mm
    # height = top - bottom  # 275 mm
    border = [top, right, bottom, left]
    coord = [left, top]
    lines_per_page = 29
    available_lines = lines_per_page
    columns_per_page = 5
    row_height = 7 * mm

# create pagenumber_text
    page_count = get_page_count(columns_per_page, lines_per_page, all_partex_assignment_keys_dict)

    page_number = 1
    pagenumber_text = ' '.join((
            str(_('Page')), str(page_number),
            'van', str(page_count) + ',',
            today_formatted
    ))
    draw_exam_page_header(canvas, border, coord, header_list, last_modified_text, pagenumber_text)

    #for partex_pk, partex_dict in all_partex_assignment_keys_dict.items():
    for partex_pk in partexpk_list_sorted:
        partex_dict = all_partex_assignment_keys_dict.get(partex_pk)
        # calculate necessary lines: 2 for partex_header, 1 for each line
        amount = int(partex_dict.get('amount', 0))
        # calculate number of rows - 5 columns per row
        columns_per_page = 5
        number_of_rows = 1 + int((amount - 1) / columns_per_page) if amount > 0 else 0
        needed_lines = 2 + number_of_rows

        if needed_lines > available_lines:
            canvas.showPage()

            coord[0] = left
            coord[1] = top # 287 * mm
            available_lines = lines_per_page
            page_number += 1
            pagenumber_text = ' '.join((
                str(_('Page')), str(page_number),
                'van', str(page_count) + ',',
                today_formatted
            ))
            draw_exam_page_header(canvas, border, coord, header_list, last_modified_text, pagenumber_text)

        draw_partex_header(canvas, border, coord, form_text, partex_dict)

        draw_questions(canvas, border, coord, row_height, form_text, partex_dict)
        available_lines -= needed_lines
# - end of draw_exam_page


def get_page_count(columns_per_page, lines_per_page, all_partex_assignment_keys_dict):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_page_count -----')
        logger.debug('all_partex_assignment_keys_dict: ' + str(all_partex_assignment_keys_dict) + ' ' + str(type(all_partex_assignment_keys_dict)))

    page_count = 1
    available_lines = lines_per_page
    for partex_pk, partex_dict in all_partex_assignment_keys_dict.items():
        # calculate necessary lines: 2 for partex_header, 1 for each line
        amount = int(partex_dict.get('amount', 0))

        # calculate number of rows - 5 columns per row
        number_of_rows = 1 + int((amount - 1) / columns_per_page) if amount > 0 else 0
        needed_lines = 2 + number_of_rows

        if logging_on:
            logger.debug('name: ' + str(partex_dict.get('name')))
            logger.debug('    amount: ' + str(amount))
            logger.debug('    number_of_rows: ' + str(number_of_rows))
            logger.debug('    needed_lines: ' + str(needed_lines))
            logger.debug('    needed_lines > available_lines: ' + str(needed_lines > available_lines))

        if needed_lines > available_lines:
            available_lines = lines_per_page
            page_count += 1

        available_lines -= needed_lines

        if logging_on:
            logger.debug('    available_lines: ' + str(available_lines))

    if logging_on:
        logger.debug('    page_count: ' + str(page_count))

    return page_count
# - end of get_page_count



def draw_exam_page_header(canvas, border, coord, text_list, last_modified_text, pagenumber_text):
    # loop through rows of page_header
    # called by draw_exam_page (2x) and draw_conversion_page

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_exam_page_header -----')
        logger.debug('text_list: ' + str(text_list))

# +++ write header block
    canvas.setLineWidth(.5)

# corners of the rectangle
    top, right, bottom, left = border[0], border[1], border[2], border[3]
    page_width = right - left  # 190 mm
    height = top - bottom  # 275 mm

    canvas.rect(left, bottom, page_width, height)

    line_count = len(text_list)
    line_height = 7 * mm
    padding_left = 4 * mm

    # coord = [left, top]
    x = coord[0] + padding_left
    y = coord[1]

    for index in range(0, line_count):  # range(start_value, end_value, step), end_value is not included!
        y -= line_height
        label = text_list[index][0]
        text = text_list[index][1]
        label2 = text_list[index][2]
        text2 = text_list[index][3]

# draw label
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
        set_font_timesbold_11_black(canvas)
        canvas.drawString(x, y, label)

# draw text (schoolname etc
        if text:
            set_font_arial_11_blue(canvas)
            canvas.drawString(x + 38 * mm, y, text)

# draw label 2
        if label2:
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
            set_font_timesbold_11_black(canvas)
            canvas.drawString(x + 114 * mm, y, label2)

# draw text 2
        if text2:
            set_font_arial_11_blue(canvas)
            canvas.drawString(x + 152 * mm, y, text2)

# - draw horizontal line at bottom of header section
    x1, x2 = left, right
    y -= 4 * mm
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.line(x1, y, x2, y)

# - draw horizontal line at top of footer section
    #y1 = bottom + 8 * mm
    # canvas.line(x1, y1, x2, y1)

    y1 = bottom + 2 * mm
    set_font_timesroman_11_black(canvas)
    canvas.drawString(x, y1, last_modified_text)

    x1 = right - 4 * mm
    canvas.drawRightString(x1 , y1, pagenumber_text)

    coord[1] = y

# - end of draw_exam_page_header


def draw_partex_header(canvas, border, coord, form_text, partex_dict):
    # loop through rows of page_header
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_partex_header -----')

    # border = [top, right, bottom, left]
    # coord = [left, top]
    top, right, bottom, left = border[0], border[1], border[2], border[3]

    line_height = 7 * mm
    padding_left = 4 * mm

    x = border[3] + padding_left
    y = coord[1]

    y -= line_height

# draw partex_name
    # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
    set_font_timesbold_11_black(canvas)
    canvas.drawString(x, y, partex_dict.get('name', '---'))

# draw label 1
    set_font_timesroman_11_black(canvas)
    canvas.drawRightString(x + 115 * mm, y, form_text.get('max_score', '-') + ':')

# draw text 1
    set_font_arial_11_blue(canvas)
    canvas.drawString(x + 120 * mm, y, str(partex_dict.get('max_score', '-')))

# draw label amount_cpt
    # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
    set_font_timesroman_11_black(canvas)
    canvas.drawRightString(x + 170 * mm, y, form_text.get('number_questions', '-') + ':')

# draw text amount
    set_font_arial_11_blue(canvas)
    canvas.drawString(x + 175 * mm, y, str(partex_dict.get('amount', '-')))

# - draw horizontal line at bottom of header section
    x1, x2 = left, right
    y -= 4 * mm
    #canvas.setStrokeColorRGB(1, 0, 0)
    canvas.line(x1, y, x2, y)

    coord[1] = y
# - end of draw_partex_header


def draw_questions(canvas, border, coord, row_height, form_text, partex_assignment_keys_dict):
    # loop through rows of page_header
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_partex_header -----')
        logger.debug('partex_assignment_keys_dict: ' + str(partex_assignment_keys_dict))

    """
    partex_assignment_keys_dict: 
        {'blanks': 0, 
        'q': {1: 'a', 2: 'b', 3: 'b', 4: '0', 5: '1', 6: 'x', 7: 'x', 8: 'x'}, 
        's': {1: 3, 2: 2, 3: 1, 5: 1, 6: 'x', 7: 'x', 8: 'x'}, 
        'name': 'Minitoets 1 BLAUW onderdeel A', 
        'amount': 8}

    """

    top, right, bottom, left = border[0], border[1], border[2], border[3]

    amount = partex_assignment_keys_dict.get('amount', 0)
    questions_dict = partex_assignment_keys_dict.get('q')
    scores_dict = partex_assignment_keys_dict.get('s')
    multiple_choice_list = partex_assignment_keys_dict.get('m')

    if logging_on:
        logger.debug('questions_dict: ' + str(questions_dict))
        logger.debug('scores_dict: ' + str(scores_dict))
        logger.debug('multiple_choice_list: ' + str(multiple_choice_list))

# calculate number of rows - 5 columns per row
    columns_per_page = 5
    number_of_rows = 1 + int( (amount - 1) / columns_per_page ) if amount > 0 else 0

    section_top = coord[1]
# +++ loop through rows of this partex
    for row_index in range(0, number_of_rows):  # range(start_value, end_value, step), end_value is not included!

        draw_question_row(canvas, border, coord, form_text, columns_per_page, number_of_rows, row_index, row_height, amount, questions_dict, scores_dict, multiple_choice_list)

    # - draw horizontal line at bottom of header section
    x1, x2 = left, right
    coord[1] -= 4 * mm
    canvas.line(x1, coord[1], x2, coord[1])

    section_bottom = coord[1]

# - vertical lines - w_list contains width of columns
    w_list = (38, 38, 38, 38)  # last col is 38 mm
    x, y1, y2 = left, section_top, section_bottom

    for w in w_list:
        x += w * mm
        canvas.line(x, y1, x, y2)
# - end of draw_questions

def draw_question_row(canvas, border, coord, form_text,
                      columns_per_page, number_of_rows, row_index, row_height, amount,
                      questions_dict, scores_dict, multiple_choice_list):
#  questions_dict = {1: '4', 2: 'D-b', 3: '6', 4: 'E-d', 5: '2', 6: '1', 7: '1', 8: '1', 9: '1'}},
    # border = [top, right, bottom, left]
    # coord = [left, top]
    top, right, bottom, left = border[0], border[1], border[2], border[3]

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_question_row -----')
        logger.debug('questions_dict: ' + str(questions_dict))
        logger.debug('scores_dict: ' + str(scores_dict))
        logger.debug('multiple_choice_list: ' + str(multiple_choice_list))

    line_height = row_height
    padding_left = 4 * mm

    col_width = 38*mm
    padding_x = 2*mm

    left = border[3] + padding_left
    y = coord[1]

    y -= line_height

# +++ loop through columns of this page
    for col_index in range(0, columns_per_page):  # range(start_value, end_value, step), end_value is not included!
        q_number = (1 + row_index) + col_index * number_of_rows
        if q_number <= amount:
            answer = None
            if q_number in questions_dict:
                answer = questions_dict[q_number]

            score = None
            if scores_dict and q_number in scores_dict:
                score = scores_dict[q_number]

            multiple_choice_suffix = '*' if multiple_choice_list and q_number in multiple_choice_list else ''

            if logging_on:
                logger.debug('score: ' + str(score) + str(type(score)))
                logger.debug('isinstance(score, int): ' + str(isinstance(score, int)))

            # lookup in questions_dict
            x_label = left + col_index * col_width
            x_data = x_label + 14 * mm
            x_score = x_data + 14 * mm
            # draw_red_cross(canvas, x_label, y)

        # draw label
            # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
            set_font_timesroman_11_black(canvas)
            canvas.drawString(x_label, y, str(q_number) + multiple_choice_suffix + ':')

        # draw text answer
            hex_color = "#000080" if answer else "#000000"
            if answer is None:
                answer = '________'
            canvas.setFillColor(colors.HexColor(hex_color))
            canvas.setFont('Arial', 11, leading=None)
            canvas.drawString(x_data, y, answer)

        # draw text score
            # score may have value 'n' or 'e'
            if score and score not in ('n', 'e'):
                set_font_timesroman_11_black(canvas)
                canvas.drawString(x_score, y, str(score))
    coord[1] = y
# - end of draw_question_row


def set_font_arial_11_blue(canvas):
    canvas.setFont('Arial', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000080"))


def set_font_timesroman_11_black(canvas):
    canvas.setFont('Times-Roman', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))


def set_font_timesbold_11_black(canvas):
    canvas.setFont('Times-Bold', 11, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

def draw_pdf_upload_log(canvas, sel_exam_instance, user_lang):  # PR2021-07-16
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_exam -----')
        logger.debug('sel_exam_instance: ' + str(sel_exam_instance) + ' ' + str(type(sel_exam_instance)))

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

    subject = sel_exam_instance.subject
    examyear = subject.examyear
    examperiod = sel_exam_instance.examperiod
    examtype = sel_exam_instance.examtype

    amount = sel_exam_instance.amount if sel_exam_instance.amount else 0
    amount_str = str(amount) if amount else '---'

    blanks_str = str(sel_exam_instance.blanks) if sel_exam_instance.blanks else '-'

    examyear_code = str(examyear.code)

    subject_name = subject.name
    examperiod_caption = c.get_examperiod_caption(examperiod)
    examtype_caption = c.get_examtype_caption(examtype)

# create list of questions
    assignment_keys_dict = get_all_partex_assignment_keys_dict(
        partex_str=sel_exam_instance.partex,
        assignment_str=sel_exam_instance.assignment,
        keys_str=sel_exam_instance.keys
    )
    if logging_on:
        logger.debug('assignment_keys_dict: ' + str(assignment_keys_dict) + ' ' + str(type(assignment_keys_dict)))

# - get dep_abbrev from department
    dep_abbrev = '---'
    department = sel_exam_instance.department
    if department:
        dep_abbrev = department.abbrev

# - get level_abbrev from level
    level_abbrev = None
    level = sel_exam_instance.level
    if level and level.abbrev:
        dep_abbrev += ' - ' + level.abbrev

# - get version
    version = sel_exam_instance.version

    last_modified_text = af.get_modifiedby_formatted(sel_exam_instance, user_lang)

# NIU: sector_abbrevs = get_sector_abbrevs(sel_exam_instance, examyear)

    header_list = ("MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT",
                 "Examenvragen voor het examenjaar " + examyear_code)

    data_list = [( str(_('Education type')) + ':', dep_abbrev) ]
    data_list.append( (str(_('Exam type')) + ':', ' '.join( (examtype_caption, examperiod_caption) ) ) )
    data_list.append((str(_('Subject')) + ':', subject_name) )
    if version:
        data_list.append( (str(_('Version')) + ':', version) )
    question_list = [ ( str(_('Number of questions')) + ':', amount_str ),
                      ( str(_('Blanks')) + ':', blanks_str )
                    ]
    filepath = s.STATICFILES_FONTS_DIR + 'arial.ttf'
    try:
        ttfFile = TTFont('Arial', filepath)
        #logger.debug('ttfFile: ' + str(ttfFile))
        pdfmetrics.registerFont(ttfFile)
    except Exception as e:
        logger.error('filepath: ' + str(filepath))
        logger.error(getattr(e, 'message', str(e)))

# +++ loop through pages (max pages = 2
    max_rows_per_page = 25
    max_questions_per_page = max_rows_per_page * 5
    page_count = 1
    if amount:
        page_count = 1 + int( (amount - 1) / max_questions_per_page )

    if logging_on:
        logger.debug('amount: ' + str(amount))
        logger.debug('page_count: ' + str(page_count))

    for page_number in range(1, 6):  # range(start_value, end_value, step), end_value is not included!

# create 2 frames per column: 1 for label and 1 for values
        first_q_number_on_page = (page_number -1) * max_questions_per_page
        if logging_on:
            logger.debug('first_q_number_on_page: ' + str(first_q_number_on_page))

        if first_q_number_on_page < amount:
            # go to new page
            if page_number > 1:
                canvas.showPage()
            #write_page(canvas, header_list, data_list, question_list, assignment_keys_dict,
            #           amount, page_number, page_count, max_rows_per_page, last_modified_text)
# - end of draw_exam


def get_all_partex_assignment_keys_dict(partex_str, assignment_str, keys_str):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_all_partex_assignment_keys_dict -----')
        logger.debug('partex_str: ' + str(partex_str))
        logger.debug('assignment_str: ' + str(assignment_str))
        logger.debug('keys_str: ' + str(keys_str))

    """
    partex: "1;1;4;20;Praktijkexamen onderdeel A # 3;1;8;12;Minitoets 1 BLAUW onderdeel A # ...
    format of partex_str is:
        partex are divided by "#"
            each item of partex contains: partex_pk ; partex_examperiod ; partex_amount ; max_score ; partex_name #

    assignment: "1;4;20|1;;6;|2;;4;|3;;4;|4;;6; # 3;8;12|1;D;3;|2;C;2;|3;C;;|4;;1;|5;;1;|6;;1;|7;D;;|8;;2; # ...
    format of assignment_str is:
        partex are divided by "#"
            first item of partex contains partex info: partex_pk ; partex_amount ; max_score |
            other items =  | q_number ; max_char ; max_score ; min_score |

    keys: "1 # 3|1;ac|2;b|3;ab|7;d # ...
    format of keys_str is:
        partex are divided by "#"
            first item of partex contains partex_pk ; partex_amount ; max_score |
    """

# - create dict with assignments PR2021-05-08
    all_assignment_dict, no_key_count, no_max_score_count = grade_views.get_allassignment_dict_from_string(assignment_str, keys_str)

#  create dict from partex
    all_partex_assignment_keys_dict = {}
    p_partex_dict = {}
    if partex_str:
        for pp in partex_str.split('#'):
            if pp:
                pp_arr = pp.split(';')
                # each partex contains partex_pk, partex_examperiod, partex_amount, max_score, partex_name
                partex_pk = int(pp_arr[0])
                partex_dict = {
                    'amount': int(pp_arr[2]),
                    'max_score': int(pp_arr[3]),
                    'name': pp_arr[4],
                }
                if partex_pk in all_assignment_dict:
                    partex_dict['q'] = all_assignment_dict[partex_pk]

                all_partex_assignment_keys_dict[partex_pk] = partex_dict

    if logging_on:
        logger.debug( 'all_partex_assignment_keys_dict: ' + str(all_partex_assignment_keys_dict) + ' ' + str(type(all_partex_assignment_keys_dict)))

    """
all_partex_assignment_keys_list: {
    1: {'amount': 31, 'max_score': 24, 'name': 'Praktijktoets blauw', 
            'q': {1: '4', 2: 'D - b', 3: '6', 4: 'E - d', 5: '2', 6: '1', 7: '1', 8: '1', 9: '1', 10: '5'}}, 
    2: {'amount': 31, 'max_score': 12, 'name': 'Minitoets rood', 
            'q': {1: '2', 2: 'D - a', 3: 'B - b', 4: 'E - c', 5: '6'}}, 
    3: {'amount': 41, 'max_score': 13, 'name': 'Minitoets groen', 
            'q': {1: '2', 2: 'C - ab', 3: 'D - d', 4: '3', 5: 'E - a', 6: '2', 7: '2'}}, 
    4: {'amount': 99, 'max_score': 0, 'name': 'Deelexamen 4', 'q': {}}
}
    """
    return all_partex_assignment_keys_dict, no_key_count, no_max_score_count
# - end of get_all_partex_assignment_keys_dict


def draw_grade_exam(canvas, sel_grade_instance, sel_exam_instance, sel_examyear, user_lang):  # PR2022-01-29
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_grade_exam -----')
        logger.debug('sel_exam_instance: ' + str(sel_exam_instance) + ' ' + str(type(sel_exam_instance)))

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

    subject = sel_exam_instance.subject
    # get examperiod from grade, not from exam, because in exam examperiod can have value '12'
    examperiod = sel_grade_instance.examperiod

# create list of results
    all_result_dict, total_amount, max_score, total_score, total_blanks, has_errors = \
        grade_views.get_assignment_with_results_dict(
            partex_str=sel_exam_instance.partex,
            assignment_str=sel_exam_instance.assignment,
            keys_str=sel_exam_instance.keys,
            result_str=sel_grade_instance.ce_exam_result
        )
    if logging_on:
        logger.debug('----- draw_grade_exam -----')
        logger.debug('     sel_exam_instance: ' + str(sel_exam_instance) + ' ' + str(type(sel_exam_instance)))
        logger.debug('     all_result_dict: ' + str(all_result_dict) + ' ' + str(type(all_result_dict)))
        logger.debug('     max_score: ' + str(max_score) + ' ' + str(type(max_score)))
        logger.debug('     total_score: ' + str(total_score) + ' ' + str(type(total_score)))
        logger.debug('     total_blanks: ' + str(total_blanks) + ' ' + str(type(total_blanks)))
        logger.debug('     has_errors: ' + str(has_errors) + ' ' + str(type(has_errors)))

# - get dep_abbrev from department
    dep_abbrev = '---'
    department = sel_exam_instance.department
    if department:
        dep_abbrev = department.abbrev

# - get level_abbrev from level
    level = sel_exam_instance.level
    if level and level.abbrev:
        dep_abbrev += ' - ' + level.abbrev

# - get version
    version = sel_exam_instance.version

    last_modified_text = af.get_modifiedby_formatted(sel_grade_instance, user_lang)

# - get form_text from examyearsetting
    form_text = awpr_lib.get_library(sel_examyear, ['exform', 'exam'])

    minond = form_text.get('minond', '-')
    title_key = 'title_ep1' if examperiod == 1 else 'title_ep2' if examperiod == 2 else '---'
    title = form_text.get(title_key, '-') + str(subject.examyear.code)

    school_cpt = form_text.get('school', '-') + ':'
    candidate_cpt = form_text.get('candidate', '-') + ':'
    subject_cpt = form_text.get('subject', '-') + ':'
    version_cpt = form_text.get('version', '-') + ':' if version else None

    exam_number_cpt = form_text.get('exam_number', '-') + ':'
    educationtype_cpt = form_text.get('educationtype', '-') + ':'
    school = sel_grade_instance.studentsubject.student.school.name
    full_name = sel_grade_instance.studentsubject.student.fullname
    exam_number = sel_grade_instance.studentsubject.student.examnumber

    # was: total_score_str = "---"
    #       if 'total_score' in all_result_dict:
    #           total_score_str = str(all_result_dict.get('total_score'))
    total_score_cpt, total_score_str = '-', '---'
    if total_score:
        total_score_str = str(total_score) if total_score else '---'
        total_score_cpt = form_text.get('total_score', '-') + ':'
    elif total_blanks:
        total_score_str = str(total_blanks) if total_blanks else '---'
        total_score_cpt = form_text.get('blanks', '-') + ':'

    max_score_str = str(max_score) if max_score else '---'
    max_score_cpt = form_text.get('max_score', '-') + ':'

    total_amount_str = str(total_amount) if total_amount else '---'
    total_amount_cpt = form_text.get('number_questions', '-') + ':'

    header_list = [
        (minond, None, None, None),
        (title, None, version_cpt, version),
        (school_cpt, school, educationtype_cpt, dep_abbrev),
        (candidate_cpt, full_name, total_amount_cpt, total_amount_str),
        (exam_number_cpt, exam_number, max_score_cpt, max_score_str),
        (subject_cpt, subject.name, total_score_cpt, total_score_str)
    ]

    filepath = s.STATICFILES_FONTS_DIR + 'arial.ttf'
    try:
        ttfFile = TTFont('Arial', filepath)
        #logger.debug('ttfFile: ' + str(ttfFile))
        pdfmetrics.registerFont(ttfFile)
    except Exception as e:
        logger.error('filepath: ' + str(filepath))
        logger.error(getattr(e, 'message', str(e)))

    draw_grade_exam_page(canvas, form_text, header_list, last_modified_text, all_result_dict)

# - end of draw_grade_exam


def draw_grade_exam_page(canvas, form_text, header_list, last_modified_text, all_result_dict):
    # PR2022-01-29 PR2022-04-27
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_grade_exam_page -----')
        logger.debug('all_result_dict: ' + str(all_result_dict))

# +++ write header block
    """
    canvas.setLineWidth(.5)
    # corners of the rectangle
    top, right, bottom, left = 287 * mm, 200 * mm, 17 * mm, 10 * mm
    page_width = right - left  # 190 mm
    border = (top, right, bottom, left)
    canvas.rect(left, bottom, page_width, height)
    """

    today_dte = af.get_today_dateobj()
    today_formatted = af.format_WDMY_from_dte(today_dte, c.LANG_DEFAULT)

    # - set the corners of the rectangle
    top, right, bottom, left = 287 * mm, 200 * mm, 12 * mm, 10 * mm
    # width = right - left  # 190 mm
    # height = top - bottom  # 275 mm
    border = [top, right, bottom, left]
    coord = [left, top]
    lines_per_page = 29
    available_lines = lines_per_page

    row_height = 7 * mm

# create pagenumber_text
    page_count = 1 # get_page_count(columns_per_page, lines_per_page, all_result_dict)

    page_number = 1
    pagenumber_text = ' '.join((
            str(_('Page')), str(page_number),
            'van', str(page_count) + ',',
            today_formatted
    ))
    draw_grade_exam_page_header(canvas, border, coord, header_list, last_modified_text, pagenumber_text)

    all_result_partex_dict = all_result_dict.get('partex')

# create a list of partex_pk, sorted by partex names - TODO improve code if possible
    partexpk_list_sorted = []
    partexname_list = []
    partexname_dict = {}

    if all_result_partex_dict:
        for partex_pk, partex_dict in all_result_partex_dict.items():
            partex_name = partex_dict.get('name')
            if partex_name:
                partexname_list.append(partex_name)
                partexname_dict[partex_name] = partex_pk
        partexname_list.sort()

    if partexname_list:
        for partex_name in partexname_list:
            partex_pk = partexname_dict.get(partex_name)
            partexpk_list_sorted.append(partex_pk)

    partex_count = len(partexpk_list_sorted)

    # was: for partex_pk, partex_dict in all_result_partex_dict.items():
    for partex_pk in partexpk_list_sorted:
        partex_dict = all_result_partex_dict.get(partex_pk)
        if logging_on:
            logger.debug('partex_dict: ' + str(partex_dict))

        # calculate necessary lines: 2 for partex_header, 1 for each line
        amount = int(partex_dict.get('amount', 0))
        if logging_on:
            logger.debug('amount: ' + str(amount))
        # calculate number of rows - 5 columns per row
        columns_per_page = 5
        number_of_rows = 1 + int((amount - 1) / columns_per_page) if amount > 0 else 0
        needed_lines = 2 + number_of_rows

        if logging_on:
            logger.debug('needed_lines: ' + str(needed_lines))
        if needed_lines > available_lines:
            canvas.showPage()

            coord[0] = left
            coord[1] = top # 287 * mm
            available_lines = lines_per_page
            page_number += 1
            pagenumber_text = ' '.join((
                str(_('Page')), str(page_number),
                'van', str(page_count) + ',',
                today_formatted
            ))
            draw_grade_exam_page_header(canvas, border, coord, header_list, last_modified_text, pagenumber_text)

        if partex_count > 1:
            draw_grade_partex_header(canvas, border, coord, form_text, partex_dict, partex_count)

        draw_questions(canvas, border, coord, row_height, form_text, partex_dict)

        available_lines -= needed_lines
# - end of draw_grade_exam_page


def draw_grade_exam_page_header(canvas, border, coord, text_list, last_modified_text, pagenumber_text):
    # loop trhrough rows of page_header
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_grade_exam_page_header -----')
        logger.debug('text_list: ' + str(text_list))

# +++ write header block
    canvas.setLineWidth(.5)

# corners of the rectangle
    top, right, bottom, left = border[0], border[1], border[2], border[3]
    page_width = right - left  # 190 mm
    height = top - bottom  # 275 mm

    canvas.rect(left, bottom, page_width, height)

    line_count = len(text_list)
    line_height = 7 * mm
    padding_left = 4 * mm

    # coord = [left, top]
    x = coord[0] + padding_left
    y = coord[1]

    for index in range(0, line_count):  # range(start_value, end_value, step), end_value is not included!
        y -= line_height
        label = text_list[index][0]
        text = text_list[index][1]
        label2 = text_list[index][2]
        text2 = text_list[index][3]

# draw label
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
        set_font_timesbold_11_black(canvas)
        canvas.drawString(x, y, label)

# draw text (schoolname etc
        if text:
            set_font_arial_11_blue(canvas)
            canvas.drawString(x + 38 * mm, y, text)

# draw label 2
        if label2:
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
            set_font_timesbold_11_black(canvas)
            canvas.drawString(x + 114 * mm, y, label2)

# draw text 2
        if text2:
            set_font_arial_11_blue(canvas)
            canvas.drawString(x + 152 * mm, y, text2)

# - draw horizontal line at bottom of header section
    x1, x2 = left, right
    y -= 4 * mm
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.line(x1, y, x2, y)

# - draw horizontal line at top of footer section
    #y1 = bottom + 8 * mm
    # canvas.line(x1, y1, x2, y1)

    y1 = bottom + 2 * mm
    set_font_timesroman_11_black(canvas)
    canvas.drawString(x, y1, last_modified_text)

    x1 = right - 4 * mm
    canvas.drawRightString(x1 , y1, pagenumber_text)

    coord[1] = y
# - end of draw_grade_exam_page_header


def draw_grade_partex_header(canvas, border, coord, form_text, partex_dict, partex_count):
    # loop through rows of page_header PR2022-04-27

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_grade_partex_header -----')
        logger.debug('partex_dict: ' + str(partex_dict))
        #logger.debug('form_text: ' + str(form_text))
    """
    partex_dict: 
        {'blanks': 0, 
            'q': {1: 'a', 2: 'a', 3: 'b', 4: '0', 5: '1', 6: 'x', 7: 'x', 8: 'x'}, 
            's': {1: 3, 3: 1, 5: 1, 6: 'x', 7: 'x', 8: 'x'}, 
        'name': 'Minitoets 1 BLAUW onderdeel A', 
        'amount': 8, 
        'score': 5}

    """
    # border = [top, right, bottom, left]
    # coord = [left, top]
    top, right, bottom, left = border[0], border[1], border[2], border[3]

    line_height = 7 * mm
    padding_left = 4 * mm

    x = border[3] + padding_left
    y = coord[1]

    y -= line_height

# draw partex_name - skip when there is only 1 aprtex

    if partex_count > 1:
    # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
        set_font_timesbold_11_black(canvas)
        canvas.drawString(x, y, partex_dict.get('name', '---'))

# draw label 1 - skip when there is only 1 aprtex
        blanks = partex_dict.get('blanks', 0)
        if blanks:
            set_font_timesroman_11_black(canvas)
            canvas.drawString(x + 114 * mm, y, form_text.get('blanks', '-') + ':')

    # draw text 1
            set_font_arial_11_blue(canvas)
            canvas.drawRightString(x + 144 * mm, y, str(blanks))
        else:
            score = partex_dict.get('score', 0)
            set_font_timesroman_11_black(canvas)
            canvas.drawString(x + 114 * mm, y, str(_('Score')) + ':')

            # draw text 1
            set_font_arial_11_blue(canvas)
            canvas.drawRightString(x + 144 * mm, y, str(score))

# draw label amount_cpt
    # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
    set_font_timesroman_11_black(canvas)
    canvas.drawString(x + 152 * mm, y, form_text.get('number_questions', '-') + ':')

# draw text amount
    set_font_arial_11_blue(canvas)
    canvas.drawRightString(x + 183 * mm, y, str(partex_dict.get('amount', '-')))

# - draw horizontal line at bottom of header section
    x1, x2 = left, right
    y -= 4 * mm
    #canvas.setStrokeColorRGB(1, 0, 0)
    canvas.line(x1, y, x2, y)

    coord[1] = y
# - end of draw_grade_partex_header


def draw_conversion_table(canvas, sel_exam_instance, sel_examyear, user_lang):  # PR2022-05-08
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_conversion_table -----')
        logger.debug('sel_exam_instance: ' + str(sel_exam_instance) + ' ' + str(type(sel_exam_instance)))

    is_ete_exam = sel_exam_instance.ete_exam
    subject = sel_exam_instance.subject
    examperiod = sel_exam_instance.examperiod
    amount_int = sel_exam_instance.amount if sel_exam_instance.amount else 0
    cesuur_int, nterm_str, nexid_str, version_nexid_txt = 0, '', '', ''

    if is_ete_exam:
        cesuur_int = sel_exam_instance.cesuur if sel_exam_instance.cesuur is not None else 0
        if sel_exam_instance.cesuur:
            cesuur_nterm_str = ' / '.join((str(sel_exam_instance.cesuur - 1), str(sel_exam_instance.cesuur)))
        else:
            cesuur_nterm_str = '---'
        version_nexid_txt = sel_exam_instance.version
    else:
        cesuur_nterm_str = sel_exam_instance.nterm if sel_exam_instance.nterm else ''
        nexid_str = str(sel_exam_instance.nex_id) if sel_exam_instance.nex_id else '-'
        version_nexid_txt = str(sel_exam_instance.nex_id) if sel_exam_instance.nex_id else ''

    scalelength_int = sel_exam_instance.scalelength
    scalelength_str = str(scalelength_int) if scalelength_int else '-'

# - get dep_abbrev from department
    dep_abbrev = '---'
    department = sel_exam_instance.department
    if department:
        dep_abbrev = department.abbrev

# - get level_abbrev from level
    level = sel_exam_instance.level
    if level and level.abbrev:
        dep_abbrev += ' - ' + level.abbrev

# - get version
    version = sel_exam_instance.version
    # dont print last_modified_by
    skip_modifiedby = True
    last_modified_text = af.get_modifiedby_formatted(sel_exam_instance, user_lang, skip_modifiedby)

# - get form_text from examyearsetting
    form_text = awpr_lib.get_library(sel_examyear, ['exform', 'exam'])
    logger.debug('form_text: ' + str(form_text))

    minond = form_text.get('minond', '-')
    if is_ete_exam:
        title = form_text.get('title_scoretable_ete', '-') + str(subject.examyear.code)
    else:
        title = form_text.get('title_scoretable_duo', '-') + str(subject.examyear.code)

    examperiod_cpt = form_text.get('Central_exam', '-') if examperiod == 1 else \
            form_text.get('Re_exam', '-') if examperiod == 2 else '-'

    educationtype = form_text.get('educationtype', '-') + ':'
    examtype = form_text.get('examtype', '-') + ':'
    subject_cpt = form_text.get('subject', '-') + ':'

    if is_ete_exam:
        max_score = form_text.get('max_score', '-') + ':'
        cesuur_nterm_lbl = form_text.get('cesuur', '-') + ':'
        version_nexid_lbl = form_text.get('version', '-') + ':' if version else None
    else:
        max_score = form_text.get('scalelength', '-') + ':'
        cesuur_nterm_lbl = form_text.get('n_term', '-') + ':'
        version_nexid_lbl = form_text.get('nex_id', '-') + ':' if nexid_str else None

    header_list = [
        (minond, None, None, None),
        (title, None, None, None),
        (educationtype, dep_abbrev, version_nexid_lbl, version_nexid_txt),
        (examtype, examperiod_cpt, max_score, scalelength_str),
        (subject_cpt, subject.name, cesuur_nterm_lbl, cesuur_nterm_str)
    ]

    filepath = s.STATICFILES_FONTS_DIR + 'arial.ttf'
    try:
        ttfFile = TTFont('Arial', filepath)
        #logger.debug('ttfFile: ' + str(ttfFile))
        pdfmetrics.registerFont(ttfFile)
    except Exception as e:
        logger.error('filepath: ' + str(filepath))
        logger.error(getattr(e, 'message', str(e)))

# create list of with score and grades
    score_grade_dict = {}
    for score_int in range(0, scalelength_int + 1):  # range(start_value, end_value, step), end_value is not included!
        if is_ete_exam:
            grade_str = calc_score.calc_grade_from_score_ete(score_int, scalelength_int, cesuur_int)
        else:
            grade_str = calc_score.calc_grade_from_score_duo(score_int, scalelength_int, cesuur_int)
        grade_with_comma = grade_str.replace('.', ',') if grade_str else '-'
        score_grade_dict[score_int] = grade_with_comma

    draw_conversion_page(canvas, form_text, scalelength_int, cesuur_int, header_list, last_modified_text, score_grade_dict)

# - end of draw_conversion_table


def draw_conversion_page(canvas, form_text, scalelength_int, cesuur_int, header_list, last_modified_text, score_grade_dict):
    # PR2022-05-08
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_conversion_page -----')

# +++ write header block
    """
    canvas.setLineWidth(.5)
    # corners of the rectangle
    top, right, bottom, left = 287 * mm, 200 * mm, 17 * mm, 10 * mm
    page_width = right - left  # 190 mm
    border = (top, right, bottom, left)
    canvas.rect(left, bottom, page_width, height)
    """

    today_dte = af.get_today_dateobj()
    today_formatted = af.format_WDMY_from_dte(today_dte, c.LANG_DEFAULT)

    # - set the corners of the rectangle
    top, right, bottom, left = 287 * mm, 200 * mm, 12 * mm, 10 * mm
    # width = right - left  # 190 mm
    # height = top - bottom  # 275 mm
    border = [top, right, bottom, left]
    coord = [left, top]
    lines_per_page = 30
    columns_per_page = 5
    row_height = 7 * mm

# create pagenumber_text
    number_of_rows, page_count = get_conversion_page_count(columns_per_page, lines_per_page, scalelength_int)

    if logging_on:
        logger.debug('    scalelength_int: ' + str(scalelength_int))
        logger.debug('    columns_per_page: ' + str(columns_per_page))
        logger.debug('    number_of_rows: ' + str(number_of_rows))
        logger.debug('    lines_per_page: ' + str(lines_per_page))
        logger.debug('    page_count: ' + str(page_count))
        logger.debug('    cesuur_int: ' + str(cesuur_int))

    page_number = 0

    row_index_on_this_page = 0
    number_of_rows_on_this_page = 0
    first_score_on_page = 0

    new_page = True
    skip_show_page = True
    for row_number_minus1 in range(0, number_of_rows):  # range(start_value, end_value, step), end_value is not included!

        if logging_on:
            logger.debug('---- row_number_minus1: ' + str(row_number_minus1))

        #if page_row > lines_per_page and False:
        if new_page:
            # skip new page at first page
            if skip_show_page:
                skip_show_page = False
            else:
                canvas.showPage()

            new_page = False

            # calculate number of rows on this page
            row_index_on_this_page = 0
            page_number += 1

            already_printed_rows = (page_number -1) * lines_per_page
            tobe_printed_rows = number_of_rows - already_printed_rows
            number_of_rows_on_this_page = tobe_printed_rows if tobe_printed_rows < lines_per_page else  lines_per_page
            first_score_on_page = already_printed_rows * columns_per_page

            if logging_on:
                logger.debug('---- already_printed_rows: ' + str(already_printed_rows))
                logger.debug('---- tobe_printed_rows: ' + str(tobe_printed_rows))
                logger.debug('---- number_of_rows_on_this_page: ' + str(number_of_rows_on_this_page))

            draw_conversion_page_header(canvas, border, coord, left, top, header_list,
                                        page_number, page_count, last_modified_text, today_formatted)

            draw_conversion_question_header_row(canvas, border, coord, columns_per_page, row_height)

        if cesuur_int:

            if logging_on:
                logger.debug('    page_number: ' + str(page_number))

            draw_conversion_question_row(canvas, border, coord, columns_per_page,
                                         row_index_on_this_page, number_of_rows_on_this_page, first_score_on_page,
                                        row_height, scalelength_int, cesuur_int, score_grade_dict)

            row_index_on_this_page += 1
            if row_index_on_this_page >= lines_per_page:
                new_page = True

    #available_lines -= needed_lines
# - end of draw_conversion_page


def draw_conversion_page_header(canvas, border, coord, left, top, text_list,
                                page_number, page_count, last_modified_text, today_formatted):
    # loop through rows of page_header
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_conversion_page_header -----')

    coord[0] = left
    coord[1] = top # 287 * mm

    pagenumber_text = ' '.join((
        str(_('Page')), str(page_number),
        'van', str(page_count) + ',',
        today_formatted
    ))

# +++ write header block
    canvas.setLineWidth(.5)

# corners of the rectangle
    top, right, bottom, left = border[0], border[1], border[2], border[3]
    page_width = right - left  # 190 mm
    height = top - bottom  # 275 mm

    canvas.rect(left, bottom, page_width, height)

    line_count = len(text_list)
    line_height = 7 * mm
    padding_left = 4 * mm

    # coord = [left, top]
    x = coord[0] + padding_left
    y = coord[1]

    for index in range(0, line_count):  # range(start_value, end_value, step), end_value is not included!
        y -= line_height
        label = text_list[index][0]
        text = text_list[index][1]
        label2 = text_list[index][2]
        text2 = text_list[index][3]

# draw label
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
        set_font_timesbold_11_black(canvas)
        canvas.drawString(x, y, label)

# draw text (schoolname etc
        if text:
            set_font_arial_11_blue(canvas)
            canvas.drawString(x + 38 * mm, y, text)

# draw label 2
        if label2:
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
            set_font_timesbold_11_black(canvas)
            canvas.drawString(x + 114 * mm, y, label2)

# draw text 2
        if text2:
            set_font_arial_11_blue(canvas)
            canvas.drawString(x + 152 * mm, y, text2)

# - draw horizontal line at bottom of header section
    x1, x2 = left, right
    y -= 4 * mm
    canvas.line(x1, y, x2, y)

# - vertical lines
    y_top_footer = bottom + 8 * mm
    y_txt_footer = bottom + 2 * mm
    w = 38 * mm
    for i in range(1, 5):  # range(start_value, end_value, step), end_value is not included!
        col_x = i * w + left
        canvas.line(col_x, y, col_x, y_top_footer)

# - draw horizontal line at top of footer section
    canvas.line(x1, y_top_footer, x2, y_top_footer)

    set_font_timesroman_11_black(canvas)
    canvas.drawString(x, y_txt_footer, last_modified_text)

    x1 = right - 4 * mm
    canvas.drawRightString(x1, y_txt_footer, pagenumber_text)

    coord[1] = y
# - end of draw_conversion_page_header


def draw_conversion_question_header_row(canvas, border, coord, columns_per_page, row_height):

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_conversion_question_row -----')

    line_height = row_height
    padding_left = 6 * mm

    col_width = 38 * mm

    left = border[3] + padding_left
    y = coord[1]

    y -= line_height

# +++ loop through columns of this page
    for col_index in range(0, columns_per_page):  # range(start_value, end_value, step), end_value is not included!
        score_lbl = _('Score')
        grade_lbl = _('Grade')

        x_label = left + col_index * col_width
        x_data = x_label + 14 * mm

    # draw label
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
        set_font_timesroman_11_black(canvas)
        canvas.drawString(x_label, y, str(score_lbl))

    # draw text answer
        canvas.drawString(x_data, y, str(grade_lbl))

    coord[1] = y
# - end of draw_conversion_question_header_row


def draw_conversion_question_row(canvas, border, coord, columns_per_page,
                                 row_index_on_this_page, number_of_rows_on_this_page, first_score_on_page,
                                 row_height, scalelength_int, cesuur_int, score_grade_dict):
    #  questions_dict = {1: '4', 2: 'D-b', 3: '6', 4: 'E-d', 5: '2', 6: '1', 7: '1', 8: '1', 9: '1'}},

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_conversion_question_row -----')
        logger.debug('     row_index_on_this_page: ' + str(row_index_on_this_page))
        logger.debug('     number_of_rows_on_this_page: ' + str(number_of_rows_on_this_page))
        logger.debug('     first first_score_on_page: ' + str(first_score_on_page))

    line_height = row_height
    padding_left = 8 * mm

    col_width = 38*mm

    left = border[3] + padding_left
    y = coord[1]

    y -= line_height
    # create more lien spacing between score 10 and 11 etc
    if row_index_on_this_page and int(row_index_on_this_page / 10) == row_index_on_this_page / 10:
        y -= line_height / 2

# +++ loop through columns of this page
    for col_index in range(0, columns_per_page):  # range(start_value, end_value, step), end_value is not included!
        score_int = first_score_on_page + row_index_on_this_page + col_index * number_of_rows_on_this_page

        if score_int <= scalelength_int:
            grade = score_grade_dict[score_int] if score_int in score_grade_dict else ''

            cesuur_suffix = '*' if score_int == cesuur_int else ''

            # lookup in questions_dict
            x_label = left + col_index * col_width
            x_data = x_label + 14 * mm
            # draw_red_cross(canvas, x_label, y)

        # draw label
            # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
            set_font_timesroman_11_black(canvas)
            canvas.drawString(x_label, y, str(score_int) + cesuur_suffix)

        # draw text answer
            hex_color = "#000080"
            canvas.setFillColor(colors.HexColor(hex_color))
            canvas.setFont('Arial', 11, leading=None)
            canvas.drawString(x_data, y, grade)

    coord[1] = y
# - end of draw_conversion_question_row


def get_conversion_page_count(columns_per_page, lines_per_page, scalelength_int):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_page_count -----')

    # calculate number of rows - 5 columns per row

    #number_of_rows = 1 + int((scalelength_int - 1) / columns_per_page) if scalelength_int > 0 else 0
    # there are scalelength_int + 1 grades to be printed ( 0 thru scalelength_int)
    number_of_rows = 1 + int((scalelength_int + 1) / columns_per_page)

    page_count = 1 + int((number_of_rows - 1) / (lines_per_page))

    if logging_on:
        logger.debug('    scalelength_int: ' + str(scalelength_int))
        logger.debug('    columns_per_page: ' + str(columns_per_page))
        logger.debug('    number_of_rows: ' + str(number_of_rows))
        logger.debug('    lines_per_page: ' + str(lines_per_page))
        logger.debug('    page_count: ' + str(page_count))

    return number_of_rows, page_count
# - end of get_conversion_page_count


############################################

def draw_red_cross(canvas, x, y):
    # draw red cross, for outlining while designing
    canvas.setStrokeColorRGB(1, 0, 0)
    canvas.line(x, y + 5 * mm, x, y - 5 * mm)
    canvas.line(x - 5 * mm, y , x + 5 * mm, y )
